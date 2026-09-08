---
title: "Node.js Production Diagnostics & Profiling"
description: "This reference is about measuring a real Node.js process — locating where CPU"
---

# Node.js Production Diagnostics & Profiling

## Overview

This reference is about **measuring a real Node.js process** — locating where CPU
time is spent, where memory is retained, and how to instrument code paths with
near-zero overhead in production. It is the "find the bottleneck" companion to two
sibling references that own the *explanatory* and *tuning* layers:

- **`v8-engine-internals`** — owns GC mechanics and heap **tuning** (`--max-old-space-size`,
  semi-space sizing, deopt reasons). This file uses heap *snapshots* to find leaks;
  it does **not** re-explain generational GC.
- **`nodejs-concurrency-internals`** — owns the libuv event-loop **phase model**,
  microtask ordering, and stream backpressure. This file *measures* event-loop lag
  (`monitorEventLoopDelay`, `eventLoopUtilization`); it does not re-derive the phases.
- **`javascript-node-html-css-debugging-expert`** — owns interactive breakpoint/step
  debugging and browser HTML/CSS DevTools. This file is about **profiling**, not stepping.

The mental model: **Doctor → Flame/CPU profile → Heap snapshot.** First classify the
symptom (CPU-bound, I/O-bound, GC-bound, event-loop-blocked), then reach for the tool
that resolves that class. Guessing without a profile is the cardinal anti-pattern.

## Core concepts

### 1. The Inspector / Chrome DevTools Protocol (CDP)

Node embeds the **V8 Inspector**, which speaks the **Chrome DevTools Protocol over a
WebSocket**. Every richer tool (Chrome DevTools, VS Code, clinic, programmatic
profiling) is a CDP client underneath.

- `--inspect[=[host:]port]` activates the inspector (default `127.0.0.1:9229`; port `0`
  = random). `--inspect-brk` breaks at the first line of the user script; `--inspect-wait`
  (v22.2+) blocks until a client attaches. `--inspect-port` + `SIGUSR1` lets you attach
  to an already-running process.
- **Security**: the inspector is a full code-execution channel. Never bind it to a public
  interface (`0.0.0.0`) without a firewall — `--inspect` on a public IP is remote code
  execution. Default to localhost and tunnel over SSH.
- The WebSocket URL is discoverable at `http://host:port/json/list` or via
  `inspector.url()`. `--inspect-publish-uid` controls where it's published.
- Open `chrome://inspect` (or `edge://inspect`) → the target appears under "Remote Target"
  → "inspect" gives a full DevTools UI (Performance + Memory tabs) wired to the Node process.

### 2. Programmatic profiling via `node:inspector`

You don't need an external client — drive the protocol in-process for self-profiling
(e.g., profile only a hot window, or on a signal). The promises API is cleanest:

```js
import { Session } from 'node:inspector/promises';
import fs from 'node:fs';

const session = new Session();
session.connect();
await session.post('Profiler.enable');
await session.post('Profiler.start');
// ... run the workload you want to profile ...
const { profile } = await session.post('Profiler.stop');
fs.writeFileSync('./hotpath.cpuprofile', JSON.stringify(profile)); // open in DevTools
```

- **`Profiler.*`** domain → CPU profiles (`.cpuprofile`). **`HeapProfiler.*`** domain →
  heap snapshots (`.heapsnapshot`) and allocation sampling; snapshot chunks arrive via the
  `HeapProfiler.addHeapSnapshotChunk` event. Do **not** pass `reportProgress: true` to
  `HeapProfiler.takeHeapSnapshot`.
- `inspector.open(port, host, wait)` activates the inspector at runtime and (v20.6+)
  returns a `Disposable` so `using` auto-closes it. `inspector.waitForDebugger()` blocks
  until a client sends `Runtime.runIfWaitingForDebugger`.
- In worker threads use `session.connectToMainThread()`; setting breakpoints on a
  same-thread session is unsupported.

### 3. The V8 profilers as CLI flags (no client needed)

For batch jobs, CI, or servers you can't attach to, the flags write artifacts to disk:

| Flag | Produces | Notes |
| --- | --- | --- |
| `--cpu-prof` | `.cpuprofile` at exit | `--cpu-prof-dir`, `--cpu-prof-name` (`${pid}` placeholder), `--cpu-prof-interval` µs (default 1000). Stable since v22.4. |
| `--heap-prof` | `.heapprofile` (allocation sampling) at exit | `--heap-prof-dir/-name/-interval` (bytes, default 512 KiB). |
| `--prof` | `isolate-*.log` (raw V8 tick log) | Post-process with `node --prof-process isolate-*.log > processed.txt` — the classic tick processor; summarizes by Summary / Bottom-up / ticks in C++/JS/GC. |

`--diagnostic-dir` sets the base directory for all of the above. `NODE_OPTIONS` can carry
the flags (`NODE_OPTIONS='--cpu-prof' node app.js`) when you can't edit the launch command.

### 4. Heap snapshots & the memory-leak hunting workflow

A heap snapshot is a full graph of live objects and their retainers. Capture one:

- **On signal** (production): `--heapsnapshot-signal=SIGUSR2`, then `kill -USR2 <pid>`.
- **Near OOM** (catch the growth): `--heapsnapshot-near-heap-limit=<count>` (stable v25.4)
  writes a snapshot as the heap approaches the limit — pair with `--max-old-space-size`.
- **Programmatically**: `v8.writeHeapSnapshot()` or the `HeapProfiler` domain above.

**The three-snapshot technique** (the standard leak workflow in DevTools' Memory tab):
1. Snapshot at steady state (baseline).
2. Drive the suspected-leaking operation N times; force a GC; snapshot again.
3. Repeat; snapshot a third time. Use **"Comparison"** view between snapshots and the
   **"Objects allocated between snapshot 1 and 2"** filter: anything still retained after
   step 3 that grows linearly with N is the leak. Inspect the **Retainers** pane to find
   what holds it — the usual culprits are module-scope `Map`/array caches without
   eviction, event listeners never removed (`emitter.on` in a hot path), closures
   capturing large scope, and timers holding references.

### 5. `perf_hooks` — measurement, not sampling

Where profilers sample stacks, `perf_hooks` gives precise, programmatic numbers:

- **`PerformanceObserver`** with `entryTypes` (`mark`, `measure`, `function`, `gc`, `http`,
  `dns`, `net`, …) and `buffered: true` to catch entries created before `observe()`.
- **`performance.mark()` / `measure()` / `timerify(fn)`** — `timerify` wraps a function so
  each call emits a `function` timeline entry (works with async, reports on settlement).
- **`monitorEventLoopDelay({ resolution })`** → an `IntervalHistogram` sampling event-loop
  delay in ns: `enable()/disable()`, `percentile(p)`, `mean`, `max`, `stddev`, `reset()`.
  This is the right signal for "is the event loop lagging?" — a p99 in the tens of ms
  means something is blocking.
- **`performance.eventLoopUtilization()`** → `{ idle, active, utilization }`. Take two
  snapshots and diff (`eventLoopUtilization(prev)`); utilization near 1.0 means the loop is
  saturated (CPU-bound), near 0 means it's mostly waiting (I/O-bound). It is the canonical
  signal for **worker-pool / thread-pool sizing** decisions.
- **`createHistogram()`** → a `RecordableHistogram` (`record`, `recordDelta`, `percentile`)
  for your own latency distributions.

### 6. `diagnostics_channel` — production instrumentation with zero idle cost

The publish/subscribe channel built into Node for **library + production instrumentation**.
Its defining property: **`channel.hasSubscribers` is false until something subscribes**, so
guarded publishing costs almost nothing when no APM is attached.

```js
import dc from 'node:diagnostics_channel';
const ch = dc.channel('app:db:query');           // create at module top level
if (ch.hasSubscribers) ch.publish({ sql, ms });  // guard the expensive prep
dc.subscribe('app:db:query', (msg, name) => metrics.record(name, msg.ms));
```

- **`TracingChannel`** (`dc.tracingChannel(name)`) emits a coordinated set of sub-channels
  — `tracing:<name>:start | end | asyncStart | asyncEnd | error` — and wraps a unit of work
  with `traceSync`, `tracePromise`, or `traceCallback`. Subscribe to all events at once
  with `tc.subscribe({ start, end, asyncStart, asyncEnd, error })`. This is how APM vendors
  trace async operations without monkey-patching.
- **Built-in channels** ship for `http(.server/.client).*`, `http2.*`, `net.*`, `module`
  (require/import tracing), `child_process`, `worker_threads`, and console — subscribe to
  get framework-level telemetry for free. `channel.bindStore()` integrates `AsyncLocalStorage`
  for request-context propagation.

### 7. Diagnostic reports & trace events

- **Diagnostic report** (`--report-on-fatalerror`, `--report-on-signal`,
  `--report-uncaught-exception`, `--report-signal=SIGUSR2`, `process.report.writeReport()`):
  a single JSON document with the JS + native stack, heap stats, libuv handles, resource
  usage, and environment — the first artifact to grab on a crash or hang in production.
- **`--trace-event-categories='v8,node,node.async_hooks'`** emits Chrome `trace_events`
  (`trace_*.log`) loadable in `chrome://tracing` / Perfetto for a timeline across
  subsystems. Heavier than the above; use for deep timeline correlation.

## Tools & frameworks

| Tool | What it does | When to reach for it |
| --- | --- | --- |
| **clinic.js doctor** | Runs the app, collects metrics, then *diagnoses* the symptom class (CPU, GC, event-loop blocking, I/O) and recommends the next tool. | The entry point — start here when you don't yet know the bottleneck class. |
| **clinic.js flame** | Interactive CPU flame graph; wide/hot bars are functions hogging CPU (self vs total time on hover). | Doctor says "CPU." Find the hot function. |
| **clinic.js bubbleprof** | Visualizes async-operation flow + delays grouped by source. | Doctor says "I/O" / async bottleneck. |
| **0x** | Single-command CPU flame graph (`0x app.js`), any platform; pairs with a load generator. | Lightweight flame graph without the full clinic suite. |
| **autocannon** | HTTP load generator (high-throughput, latency histograms). | Generate the load under which you profile a server. |

**The canonical combo** — profile *under load*: `0x` sets a `$PORT` to the first port the
profiled process opens and forwards a signal when the load test ends, so
`0x -P 'autocannon localhost:$PORT' server.js` runs the load test, then auto-generates the
flame graph from exactly that window. (clinic does the same with `clinic flame --autocannon`.)

## Methodology — a triage workflow

1. **Reproduce under load.** A profile of an idle process is noise. Drive realistic traffic
   with `autocannon` (or your load tool).
2. **Classify with `monitorEventLoopDelay` + `eventLoopUtilization`** (or clinic doctor):
   high ELU + high event-loop delay → **CPU-bound / blocking**; low ELU + high latency →
   **I/O-bound / async**; sawtooth memory + GC pauses → **GC/leak**.
3. **CPU-bound** → `--cpu-prof` or a flame graph (0x / clinic flame). Read top-down for the
   hot path; look for an unexpectedly wide synchronous frame (sync crypto, JSON of a huge
   payload, a regex → ReDoS).
4. **I/O-bound** → clinic bubbleprof or `diagnostics_channel` HTTP/net channels; look for
   serialized awaits that should be `Promise.all`, missing connection pooling, or a chatty
   downstream.
5. **Memory growth** → heap snapshot three-snapshot diff; find the retainer.
6. **Instrument the winner** with `diagnostics_channel` / `perf_hooks` so the metric is
   permanent and you can alert on regressions — don't re-profile by hand each time.

## Practical patterns

- **Profile a window, not the whole run** — use the programmatic `Profiler.start/stop`
  around the suspect path to keep the profile small and readable.
- **On-demand production capture** — ship with `--heapsnapshot-signal=SIGUSR2` and a
  `process.on('SIGUSR2')` CPU-profile toggle so you can capture artifacts from a live pod
  without a redeploy. Pull the files and open them in local DevTools.
- **Guard every `publish`** with `hasSubscribers` so instrumentation is free when no
  collector is attached.
- **Alert on `eventLoopUtilization` and event-loop delay p99**, not just CPU% — they catch
  blocking that CPU% averages hide.

## Anti-patterns

- **Optimizing without a profile.** "I think this loop is slow" → measure first; the hot
  path is almost never where intuition points.
- **Profiling an idle / unrealistic process** — no load, or synthetic data that doesn't
  exercise the real path.
- **`console.time` everywhere as a profiler** — fine for one span, useless for finding an
  unknown bottleneck; it can't see native frames or aggregate.
- **Leaving `--inspect` bound to a public interface** — remote code execution.
- **Unguarded `channel.publish(expensiveToBuild())`** — defeats the zero-idle-cost design.
- **Treating a heap *snapshot* as GC *tuning*** — the snapshot finds the leak; sizing the
  heap (`--max-old-space-size`) is a `v8-engine-internals` concern.

## Troubleshooting

- **Can't connect Chrome DevTools** → check the WS URL (`inspector.url()` / `/json/list`),
  confirm the port isn't firewalled, and that you used `--inspect` not `--inspect-brk`
  (which pauses before your code).
- **`.cpuprofile` is empty / tiny** → the profiler window didn't overlap the workload;
  start it before driving load, stop it after.
- **Heap snapshot too big to open** → raise DevTools memory or use allocation *sampling*
  (`--heap-prof`) instead of a full snapshot for a first pass.
- **No `gc` entries from PerformanceObserver** → GC timeline entries require observing
  `entryTypes: ['gc']`; for GC *tuning* and pause analysis, see `v8-engine-internals`.
- **High event-loop delay but flat CPU** → blocking is in the libuv thread pool
  (fs/dns/crypto/zlib) saturating `UV_THREADPOOL_SIZE`; see `nodejs-concurrency-internals`.

## References

- Node.js — Inspector module (`node:inspector`, CDP, Session, Profiler/HeapProfiler): https://nodejs.org/api/inspector.html
- Node.js — CLI diagnostic flags (`--inspect`, `--cpu-prof`, `--heap-prof`, `--prof`, `--heapsnapshot-signal`, `--report-*`, `--trace-event-categories`): https://nodejs.org/api/cli.html
- Node.js — `perf_hooks` (PerformanceObserver, monitorEventLoopDelay, eventLoopUtilization, timerify, createHistogram): https://nodejs.org/api/perf_hooks.html
- Node.js — `diagnostics_channel` (channels, TracingChannel, built-in channels, bindStore): https://nodejs.org/api/diagnostics_channel.html
- clinic.js — node-clinic (doctor / flame / bubbleprof): https://github.com/clinicjs/node-clinic ; NearForm "Introducing Clinic.js": https://nearform.com/insights/introducing-node-clinic-a-performance-toolkit-for-node-js-developers/
- 0x — single-command flame graphs: https://github.com/davidmarkclements/0x ; NearForm "Tuning Node.js app performance with Autocannon and 0x": https://nearform.com/insights/tuning-node-js-app-performance-with-autocannon-and-0x/
- autocannon — HTTP load generator: https://github.com/mcollina/autocannon
