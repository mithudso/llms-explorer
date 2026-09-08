---
title: "Node.js Concurrency Internals"
description: "How Node.js does concurrency on a single main thread: the libuv event loop that"
---

# Node.js Concurrency Internals

How Node.js does concurrency on a single main thread: the **libuv event loop** that
orchestrates everything, the **thread pool** that absorbs blocking work, **stream
backpressure** that keeps memory bounded, and the **three parallelism models**
(`worker_threads`, `cluster`, `child_process`) for escaping the single thread. Treat the
[Node.js API docs](https://nodejs.org/api/index.html) and [libuv docs](https://docs.libuv.org/en/v1.x/)
as the source of truth for version-sensitive behavior.

This is the deep-internals companion to `references/javascript-nodejs.md` (broad language /
runtime-API reference). When a question is about *ordering, blocking, throughput, or
parallelism mechanics*, it belongs here.

## When to use this reference

- Predicting or explaining **event-loop phase ordering** (`setTimeout` vs `setImmediate`, why I/O callbacks fire where they do)
- `process.nextTick` vs Promise **microtask** draining, or diagnosing **nextTick starvation**
- "Don't block the event loop" — **event-loop lag**, ReDoS, sync APIs, **partitioning vs offloading**
- Tuning **`UV_THREADPOOL_SIZE`** or diagnosing thread-pool saturation (fs/dns/crypto/zlib)
- **Stream backpressure**: `highWaterMark`, `write()` returning `false`, `'drain'`, `pipe` vs `pipeline`
- Writing **custom `Readable`/`Writable`/`Transform`** streams correctly
- Choosing **`worker_threads` vs `cluster` vs `child_process`**
- `SharedArrayBuffer` / `Atomics` / `transferList` / structured clone between threads
- **`cluster`** scheduling (`SCHED_RR` vs `SCHED_NONE`), shared ports, worker lifecycle
- **`child_process`** `spawn`/`exec`/`execFile`/`fork`, shell command-injection, `maxBuffer`, IPC

## When NOT to use this reference

- Broad JS/Node language semantics, module systems, everyday API selection → `references/javascript-nodejs.md`
- Debugging tools, breakpoints, heap snapshots, DevTools → `references/javascript-node-html-css-debugging-expert.md`
- Production observability (OpenTelemetry, structured logging) → `nodejs-observability` / `pino-structured-logging` (devops-infra hub)
- Python `asyncio` → `references/python-patterns.md`; Go goroutines/channels → `references/go-patterns.md`

---

## 1. The libuv event loop and its phases

Node runs JavaScript on a **single main thread**. libuv drives an **event loop** that, on
each iteration ("tick" of the loop), passes through six phases **in this fixed order**, each
with its own FIFO callback queue ([Node.js Event Loop](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick), [libuv design](https://docs.libuv.org/en/v1.x/design.html)):

| # | Phase | What runs here |
|---|-------|----------------|
| 1 | **timers** | Callbacks whose `setTimeout()` / `setInterval()` threshold has elapsed |
| 2 | **pending callbacks** | A few system-level I/O callbacks deferred to the next iteration (e.g. some TCP errors like `ECONNREFUSED`) |
| 3 | **idle, prepare** | Internal libuv use only |
| 4 | **poll** | Retrieve new I/O events; run most I/O callbacks (everything except close callbacks, timers, and `setImmediate`). **This is where the loop blocks/waits.** |
| 5 | **check** | `setImmediate()` callbacks |
| 6 | **close callbacks** | `'close'` events, e.g. `socket.on('close', …)` |

After phase 6 the loop wraps back to phase 1. The loop's notion of **`now`** is sampled once
at the start of an iteration and is *not* updated again mid-iteration — a timer that becomes
due while earlier timers are still running waits until the next iteration.

### The poll phase decides how long the process sleeps

The poll phase is the heart of the loop ([Node.js Event Loop](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)):

- **Poll queue not empty** → run its callbacks synchronously until the queue drains or a system limit is hit.
- **Poll queue empty:**
  - If `setImmediate()` callbacks are scheduled → end poll, go to **check**.
  - Else → **block here waiting for I/O**, with a computed timeout equal to the nearest pending timer (so timers fire roughly on time). If no timers and no handles keep the loop alive, the process exits.

A process stays alive only while there are **active handles or requests** (open sockets,
listening servers, pending timers, active worker threads). When none remain, the loop ends
and Node exits.

### libuv is what makes I/O async

For **network I/O**, libuv uses the OS's native async primitives (epoll on Linux, kqueue on
BSD/macOS, IOCP on Windows) — no extra threads. For work the OS **cannot** do
asynchronously (notably file-system I/O, and DNS via `getaddrinfo`), libuv falls back to the
**thread pool** (Section 3) ([libuv design](https://docs.libuv.org/en/v1.x/design.html)).

---

## 2. Microtasks: process.nextTick and the Promise queue

`process.nextTick()` and the **Promise microtask queue** are **not** event-loop phases. They
are two separate queues that drain **between every callback and between every phase
transition** — they run before the loop is allowed to advance ([Node.js Event Loop](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)).

**Drain order at each checkpoint:**
1. The entire **`process.nextTick` queue** (highest priority), then
2. The entire **Promise microtask queue** (`.then` / `await` continuations, `queueMicrotask`).

Both are fully drained before the next phase callback runs.

```js
setImmediate(() => console.log('immediate'));   // check phase
Promise.resolve().then(() => console.log('promise')); // microtask
process.nextTick(() => console.log('nextTick'));      // nextTick queue
console.log('sync');
// Output: sync, nextTick, promise, immediate
```

### nextTick / microtask starvation

Because these queues drain *completely* before the loop advances, **recursively scheduling
`process.nextTick()` (or microtasks) starves the loop** — I/O, timers, and `setImmediate`
never run:

```js
function starve() { process.nextTick(starve); } // poll phase never reached again
```

Prefer `setImmediate()` when you want to yield back to the loop. Legitimate `nextTick` uses:
defer a callback so the caller's synchronous code finishes first, emit an event after a
constructor returns (so listeners can attach), or normalize an API to "always async."

### setTimeout(…, 0) vs setImmediate

- **In the main module / top level:** order is **non-deterministic** — it depends on how
  fast the process reaches the timers phase vs whether the 0-ms timer's threshold has elapsed.
- **Inside an I/O callback (poll phase):** `setImmediate` **always** fires before
  `setTimeout(…, 0)`, because the loop goes poll → check next, and only reaches timers on the
  following iteration.

```js
const fs = require('node:fs');
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));
});
// Always: immediate, then timeout
```

---

## 3. The libuv thread pool

A **global thread pool**, shared across all event loops in the process, runs work that has no
async OS primitive ([libuv threadpool](https://docs.libuv.org/en/v1.x/threadpool.html)):

- **Default size: 4 threads.** Configurable via the **`UV_THREADPOOL_SIZE`** environment
  variable, **max 1024** (raised from 128 in libuv 1.30.0). Must be set **before** the pool is
  first used (effectively at process start); libuv preallocates the threads on first use.
- **What uses it:** `fs.*` file operations, `dns.lookup()` (`getaddrinfo`/`getnameinfo`),
  `crypto` (`pbkdf2`, `randomBytes`, `scrypt`), and `zlib` compression. **Network sockets do
  NOT** — they use the OS event mechanism, not the pool.

**Saturation symptom:** with the default 4 threads, 5+ concurrent `fs`/`crypto`/`zlib`/DNS
operations queue; the 5th waits for a free thread even though the CPU is idle. Latency climbs
with no obvious CPU cause. Raise `UV_THREADPOOL_SIZE` (a common starting point is the number
of logical cores, or higher for I/O-heavy workloads) and measure.

> Pitfall: `dns.lookup()` uses the pool; the lower-level `dns.resolve*()` family uses the
> network and does **not**. A burst of `dns.lookup()` (which most connection code calls
> implicitly) can starve the pool.

---

## 4. Don't block the event loop (or the pool)

Node serves many clients with few threads, so **any synchronous CPU work on the main thread
stalls every other client** — a throughput problem and a DoS vector ([Don't Block the Event Loop](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)).

**Things that block the main thread:**
- Synchronous APIs in request paths: `fs.readFileSync`, `crypto.pbkdf2Sync`, `zlib.*Sync`, `child_process.execSync`, `JSON.parse`/`JSON.stringify` on large payloads.
- **ReDoS** — catastrophic backtracking from nested quantifiers (`/(\/.+)+$/`), overlapping alternation (`/(a|a)*/`), or backreferences; an attacker triggers exponential time. Mitigate with `indexOf`, `safe-regex`, or `node-re2` (linear-time engine), and bound input size.
- Long synchronous loops / O(n²) work per request.

**Two fixes:**
1. **Partitioning** (keep work on the loop but yield): break the loop into chunks and
   reschedule each chunk with `setImmediate()` so other callbacks interleave.
2. **Offloading** (move work off the loop): `worker_threads` for CPU-bound JS,
   `child_process` for separate programs. Use a **pool** of workers — never spawn one per
   request (fork-bomb / unbounded memory).

**Measure event-loop lag** with `perf_hooks.monitorEventLoopDelay()` (histogram) or
`performance.eventLoopUtilization()` (ELU). Don't block the **pool** either: one slow
thread-pool task (e.g. reading `/dev/random`) ties up 1 of 4 threads; partition large reads
or use streams (auto-partitioned).

---

## 5. Streams and backpressure

A stream moves data in chunks instead of buffering it all in memory. **Backpressure** is the
flow-control signal that stops a fast producer from outrunning a slow consumer; ignoring it
lets internal buffers grow without bound ([Backpressuring in Streams](https://nodejs.org/en/learn/modules/backpressuring-in-streams), [Node.js Stream API](https://nodejs.org/api/stream.html)).

**Four stream types:** `Readable` (source), `Writable` (sink), `Duplex` (both, independent
sides, e.g. a TCP socket), `Transform` (Duplex where output is a function of input, e.g.
`zlib.createGzip()`).

### highWaterMark and the write() / drain contract

Each stream has a **`highWaterMark`** buffer threshold — default **16384 bytes (16 KB)** for
byte streams, **16 objects** in `objectMode`.

- `writable.write(chunk)` returns **`true`** → keep writing.
- It returns **`false`** → the internal buffer is at/over `highWaterMark`. **Stop writing and
  wait for the `'drain'` event** before resuming. (`write()` still accepts the chunk; the
  return value is purely the backpressure signal.)

```js
// Manual writing MUST honor backpressure:
readable.on('data', (chunk) => {
  if (!writable.write(chunk)) readable.pause();
});
writable.on('drain', () => readable.resume());
```

Real impact: compressing a ~9 GB file with backpressure held memory at ~88 MB; ignoring it
ballooned to ~1.5 GB (≈17× more) with far worse GC pauses.

### Prefer pipeline() over pipe()

`pipe()` and `pipeline()` **handle backpressure automatically** (you don't manage
`drain`/`pause`/`resume`). Always prefer **`stream.pipeline()`** over manual `.pipe()` chains:
on any stream's failure it destroys *all* streams and propagates the error, where `.pipe()`
leaks file descriptors and sockets on error.

```js
const { pipeline } = require('node:stream/promises');
await pipeline(
  fs.createReadStream('in.mkv'),
  zlib.createGzip(),
  fs.createWriteStream('out.mkv.gz'),
); // throws on any stage failure, cleans up everything
```

### Custom stream rules

- **`Readable._read`:** respect `push()`'s return value — when `this.push(chunk)` returns
  `false`, stop pushing (the consumer's buffer is full). `push(null)` signals end-of-stream.
- **`Writable._write(chunk, enc, cb):`** call `cb` **exactly once** (use `return cb()` on
  every branch so it can't be called twice).
- **Batching:** `cork()` buffers writes; `uncork()` flushes them in one go. Schedule the
  `uncork()` with `process.nextTick()` so multiple synchronous `write()`s batch into a single
  flush rather than flushing per call.
- Modern alternative: build pipelines from **async iterators / async generators** as
  Transform stages — `pipeline()` accepts them and applies backpressure automatically.

---

## Web Streams API (WHATWG) & Node interop (Readable.toWeb/fromWeb, stream/consumers)

Alongside classic `node:stream` (Section 5), Node implements the **WHATWG Web Streams**
standard — the same `ReadableStream`/`WritableStream`/`TransformStream` you get in browsers,
`fetch`/`undici` response bodies, and edge runtimes (Workers, Deno). Use them for
**cross-runtime / edge-portable** code and when consuming `fetch` bodies; reach for classic
`node:stream` for Node-centric server I/O and the richer ecosystem. The three stream classes
plus `TextEncoderStream`/`TextDecoderStream`/`CompressionStream`/`DecompressionStream`/the
queuing-strategy classes are **globals** in modern Node — no import. Only `node:stream/consumers`,
`node:stream/promises`, and the `toWeb`/`fromWeb` bridge methods need importing
([Web Streams API](https://nodejs.org/api/webstreams.html), [MDN Streams concepts](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Concepts)).

### Construction (underlying source / sink / transformer)

Web Streams take a plain object describing the source/sink, optionally followed by a queuing
strategy. The hook names differ from classic `_read`/`_write` (Section 5):

```js
// ReadableStream: { start, pull, cancel }, type:'bytes' for a byte stream
const rs = new ReadableStream({
  start(controller) {},
  pull(controller) { controller.enqueue(chunk); /* controller.close() to end */ },
  cancel(reason) {},
}, new CountQueuingStrategy({ highWaterMark: 16 }));

// WritableStream: { start, write, close, abort }
const ws = new WritableStream({
  write(chunk, controller) { /* return a Promise to apply backpressure */ },
  close() {}, abort(reason) {},
}, new ByteLengthQueuingStrategy({ highWaterMark: 64 * 1024 }));

// TransformStream: { start, transform, flush } + separate writable/readable strategies
const ts = new TransformStream({ transform(chunk, controller) { controller.enqueue(chunk); } });
```

### Backpressure: the demand/pull model (vs classic write()/drain)

Same goal as Section 5 (bound memory, throttle a fast producer) but a different surface — so
**don't re-derive the classic `write()===false` + `'drain'` contract; note the delta:**

- A **queuing strategy is an object** (`new ByteLengthQueuingStrategy({highWaterMark})` for byte
  streams, `new CountQueuingStrategy({highWaterMark})` for object streams), not a numeric
  `highWaterMark` option as in classic streams. There is **no fixed default `highWaterMark`** —
  the *model*, not a magic number, is the contract (classic streams keep the 16 KB / 16-object
  defaults from Section 5).
- Backpressure is read via **`controller.desiredSize`** (= `highWaterMark` − queued size). When
  it drops to **≤ 0**, the producer is outrunning the consumer; stop enqueuing. It can go
  negative.
- The runtime calls **`pull(controller)`** only while the queue is below the high-water mark, and
  — if `pull` returns a Promise — won't call it again until that Promise settles. This is a
  **demand-driven pull** loop, whereas classic streams are push-with-a-`drain`-backstop. Apply
  backpressure on the write side by returning a Promise from the sink's `write()` (or awaiting
  `writer.ready` / reading `writer.desiredSize`).
- **`stream.pipeTo()` / `stream.pipeThrough()`** propagate backpressure end-to-end automatically
  (the Web-Streams analogue of `pipeline()`), and `tee()` forks one readable into two independent
  readables — a fan-out classic streams have no direct equivalent for.

### Default vs BYOB (byte) readers

`getReader()` yields a `ReadableStreamDefaultReader` (opaque chunks). For a `type: 'bytes'`
stream, `getReader({ mode: 'byob' })` yields a **`ReadableStreamBYOBReader`** whose
`read(view)` fills a caller-supplied `TypedArray`/`DataView` — a **zero-copy** read straight
into your buffer. (Never hand it a pooled Node `Buffer`: BYOB detaches the backing
`ArrayBuffer`.) Async iteration works too: `for await (const chunk of readable)`.

### Bridging classic ↔ Web (toWeb / fromWeb)

Static methods on the classic stream classes convert both directions — bridge a Node
file/socket stream into a Web pipeline, or wrap a `fetch` body as a classic `Readable`:

```js
import { Readable, Writable, Duplex } from 'node:stream';

const webReadable = Readable.toWeb(fs.createReadStream('in.bin'));   // classic → Web
const nodeReadable = Readable.fromWeb(response.body);               // Web (fetch) → classic
const webWritable = Writable.toWeb(fs.createWriteStream('out.bin'));
const nodeWritable = Writable.fromWeb(webWritableStream);
// Duplex.toWeb(d) → { readable, writable }; Duplex.fromWeb(pair) → Duplex (e.g. for a socket)
```

These bridges were historically flagged experimental — check the **stability index** for your
Node version and pin Node versions for production use.

### Consuming either stream world: stream/consumers & stream/promises

`node:stream/consumers` collects **either** a Web `ReadableStream`, a classic `stream.Readable`,
**or** any `AsyncIterable` into one value — no manual chunk loop:

```js
import { text, json, arrayBuffer, blob, buffer, bytes } from 'node:stream/consumers';
const obj = await json(response.body);          // Web ReadableStream → parsed JSON
const str = await text(fs.createReadStream('x')); // classic Readable → UTF-8 string
// also: arrayBuffer → ArrayBuffer, blob → Blob, buffer → Buffer, bytes → Uint8Array
```

`node:stream/promises` spans both worlds too: **`pipeline()`** accepts Web streams, classic
streams, and async iterables/generators in one chain, and **`finished()`** accepts a
`ReadableStream`/`WritableStream` as well as a classic stream. Prefer these over hand-rolled
`getReader()`/`read()` loops when you just need the collected result or a completion signal.

---

## 6. Three ways to escape the single thread

| Model | Unit | Memory | Cost | Use for |
|-------|------|--------|------|---------|
| **`worker_threads`** | Thread (own V8 isolate + event loop, same process) | Can **share** via `SharedArrayBuffer`; transfer `ArrayBuffer` | Low (in-process) | **CPU-bound JS** in parallel without blocking the main loop |
| **`cluster`** | Process (Node) sharing a server port | Isolated | Higher (full process) | **Scaling a network server** across cores |
| **`child_process`** | Process (any program) | Isolated | Higher | Running **external programs** / isolating untrusted or crash-prone work |

Rule of thumb: **CPU-bound JS → worker_threads; scaling an HTTP/TCP server → cluster; shelling
out to another program → child_process.** None of these help **I/O-bound** work — plain async
I/O on one thread is already optimal and cheaper.

---

## 7. worker_threads

Each `Worker` is a **separate V8 isolate with its own event loop and heap**, inside the same
OS process — far cheaper than a process, and able to share memory ([worker_threads](https://nodejs.org/api/worker_threads.html)).

```js
// main.js
import { Worker } from 'node:worker_threads';
const worker = new Worker(new URL('./worker.js', import.meta.url), {
  workerData: { rows: 1_000_000 },
});
worker.on('message', (result) => console.log(result));
worker.on('error', (err) => { /* uncaught worker error */ });
worker.on('exit', (code) => { /* code !== 0 → abnormal */ });
```

```js
// worker.js
import { parentPort, workerData } from 'node:worker_threads';
const result = heavyCompute(workerData.rows);
parentPort.postMessage(result);
```

**Communication:**
- `postMessage()` copies data using the **HTML structured clone algorithm** (not JSON): it
  handles `Map`/`Set`/`Date`/`RegExp`/`BigInt`/typed arrays and circular refs, but **drops
  class prototypes** (a class instance arrives as a plain object) and cannot clone functions.
- **`transferList`:** move (don't copy) ownership of an `ArrayBuffer` / `MessagePort`:
  `port.postMessage(view, [view.buffer])`. The buffer becomes **detached** (length 0) on the
  sender side, and *all* views over it become unusable — zero-copy handoff.
- **`MessageChannel` / `MessagePort`:** dedicated bidirectional channels (transfer one port to
  the worker). **`BroadcastChannel`:** one-to-many by channel name.
- **`SharedArrayBuffer` + `Atomics`:** true shared memory for high-frequency coordination.
  Use `Atomics.add/compareExchange/...` for race-free updates and `Atomics.wait` /
  `Atomics.notify` to block/wake threads.

**Caveats:** workers don't share `process.stdin/stdout/stderr` unless piped; can't
`process.chdir()` or handle process signals; `worker.unref()` lets the process exit without
waiting on the worker; `worker.terminate()` force-stops it (returns a Promise). For many small
tasks, **reuse a worker pool** (e.g. `Piscina`) rather than creating a worker per task.

---

## 8. cluster

`cluster` forks multiple **Node worker processes that all listen on the same server port**,
letting a server use every core. It is built on **`child_process.fork()`** with an IPC channel
and server-handle passing ([cluster](https://nodejs.org/api/cluster.html)).

```js
import cluster from 'node:cluster';
import http from 'node:http';
import { availableParallelism } from 'node:os';

if (cluster.isPrimary) {
  for (let i = 0; i < availableParallelism(); i++) cluster.fork();
  cluster.on('exit', (worker) => cluster.fork()); // respawn on death
} else {
  http.createServer((req, res) => res.end('ok')).listen(8000); // shared port
}
```

**Scheduling policy** (`cluster.schedulingPolicy` / `NODE_CLUSTER_SCHED_POLICY`):
- **`SCHED_RR`** (round-robin) — **default everywhere except Windows.** The primary accepts
  connections and hands them out evenly. Usually the right choice.
- **`SCHED_NONE`** — the OS distributes connections; can be badly unbalanced (e.g. most
  connections landing on a couple of workers).

**Lifecycle events** (primary): `fork`, `online`, `listening`, `message`, `disconnect`,
`exit`. Communicate via `worker.send()` / `process.on('message')`. Graceful shutdown:
`worker.disconnect()` (stop accepting, drain) then a kill-timeout fallback.

**Caveats:** workers have **separate memory** — never keep session/login state in process
memory; use a shared store (Redis) or a load balancer with **sticky sessions** for stateful
connections. `cluster.isMaster`/`setupMaster()` are deprecated → use
`isPrimary`/`setupPrimary()`. Many deployments instead run N single-process instances behind
an external balancer (or a process manager like PM2).

---

## 9. child_process

Run other programs (or other Node scripts) as separate OS processes ([child_process](https://nodejs.org/api/child_process.html)).

| Function | Shell? | Output | Best for |
|----------|--------|--------|----------|
| **`spawn(cmd, args)`** | No (default) | **Streaming** (stdout/stderr are streams) | Large/continuous output, long-running processes |
| **`exec(cmdString)`** | **Yes** | Buffered, **`maxBuffer` default 1 MB** | Quick shell one-liners (pipes, globbing) |
| **`execFile(file, args)`** | No (default) | Buffered, `maxBuffer` 1 MB | Running an executable directly, no shell |
| **`fork(modulePath)`** | No | Streaming + **IPC channel** | Spawning a **Node** child with `send()`/`'message'` |

Each has a `*Sync` variant (`spawnSync`, `execSync`, `execFileSync`) that **blocks the event
loop** — startup/CLI use only, never in a server.

**Command injection:** `exec`/`shell: true` interpolate strings through a shell, so untrusted
input enables injection (`exec(\`echo ${userInput}\`)` with `userInput = "; rm -rf /"`). Prefer
**`spawn`/`execFile` with an args array** — arguments bypass shell parsing, so metacharacters
are inert. Reach for a shell only when you genuinely need shell features, and sanitize input.

**Other essentials:**
- **`maxBuffer`** (exec/execFile): exceeding it kills the child with
  `ERR_CHILD_PROCESS_STDIO_MAXBUFFER_EXCEEDED`; raise it or switch to `spawn` for big output.
- **`stdio`** option: `'pipe'` (default; streams on the child object), `'inherit'` (share the
  parent's stdio), `'ignore'`, or `'ipc'` (message channel — what `fork` adds).
- **IPC:** `fork` (or `spawn` with an `'ipc'` stdio slot) gives `child.send(msg)` ↔
  `process.on('message')`, using structured clone.
- **`detached: true` + `subprocess.unref()`** lets a child outlive the parent (with
  `stdio: 'ignore'`). `ref()`/`unref()` toggle whether the child keeps the parent's loop alive.
- **Events:** `'spawn'` (started) → `'exit'` (process ended, stdio may still be open) →
  `'close'` (stdio fully closed; always after `'exit'`); `'error'` on spawn failure.

---

## Quick decision guide

| Symptom / goal | Answer |
|----------------|--------|
| `setTimeout(0)` vs `setImmediate` order | Indeterminate at top level; `setImmediate` first inside I/O callbacks |
| Need to run *after* current op but before I/O | `process.nextTick` (don't recurse — starvation) |
| App latency high, CPU idle, lots of fs/crypto/dns | Raise `UV_THREADPOOL_SIZE`; the pool (default 4) is saturated |
| Heavy CPU loop stalls all requests | Partition with `setImmediate`, or offload to `worker_threads` |
| Memory grows while piping data | Backpressure ignored — use `pipeline()` or honor `write()===false` + `'drain'` |
| Multi-stream flow with error safety | `stream.pipeline()`, never raw `.pipe()` chains |
| Parallelize CPU-bound JS | `worker_threads` (pool of them) |
| Use all cores for one HTTP server | `cluster` (`SCHED_RR`) or N instances behind a balancer |
| Shell out to another program | `spawn`/`execFile` + args array (never interpolate into `exec`) |
| Big subprocess output | `spawn` (streaming), not `exec` (1 MB `maxBuffer`) |

---

## References

- [Node.js — The event loop, timers, and process.nextTick()](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)
- [Node.js — Don't block the event loop (or the worker pool)](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)
- [Node.js — Backpressuring in streams](https://nodejs.org/en/learn/modules/backpressuring-in-streams)
- [Node.js Stream API](https://nodejs.org/api/stream.html)
- [Node.js Web Streams API (`node:stream/web`, `stream/consumers`, `stream/promises`)](https://nodejs.org/api/webstreams.html)
- [MDN — Streams API concepts (backpressure, queuing strategies, BYOB)](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Concepts)
- [Node.js worker_threads](https://nodejs.org/api/worker_threads.html)
- [Node.js cluster](https://nodejs.org/api/cluster.html)
- [Node.js child_process](https://nodejs.org/api/child_process.html)
- [libuv — Design overview](https://docs.libuv.org/en/v1.x/design.html)
- [libuv — Thread pool work scheduling](https://docs.libuv.org/en/v1.x/threadpool.html)
