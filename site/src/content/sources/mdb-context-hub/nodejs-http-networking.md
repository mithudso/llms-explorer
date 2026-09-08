---
title: "Node.js HTTP & Networking"
description: "This reference is the networking + HTTP core of Node plus the modern HTTP client:"
---

# Node.js HTTP & Networking

## Overview

This reference is the **networking + HTTP core of Node** plus the **modern HTTP client**:
the layered stack from raw TCP/UDP sockets up through HTTP/1.1, HTTP/2, TLS, and the
`fetch`/undici client. It is the "talk to the network correctly and keep the sockets
healthy" companion to three siblings that own neighbouring layers:

- **`nodejs-backend-frameworks`** owns the *framework* layer (Express/Fastify/NestJS/Hono,
  routing, middleware, framework selection). This file is the primitives those frameworks
  are built on — `http.Server`, the Agent, timeouts, TLS.
- **`nodejs-concurrency-internals`** owns the libuv **event-loop phase model** and **stream
  backpressure** (`highWaterMark`, `pipe` vs `pipeline` flow control). This file *uses*
  streams (request/response bodies are streams) but defers the backpressure mechanics there.
- **`http-security-headers`** owns CSP/HSTS/CORS and mTLS *hardening posture*. This file
  covers the TLS *plumbing* (SNI, ALPN, session resumption); the security headers go there.

The mental model has four layers: **net/dgram** (TCP/UDP sockets) → **tls** (encryption,
SNI, ALPN) → **http / http2 / https** (framing) → **fetch/undici** (the high-level pooled,
retrying client). Most production incidents here are **timeout** and **socket-pool** problems,
not protocol problems — so the timeout knobs and Agent/Pool sizing get the most attention below.

## Core concepts

### 1. `node:http` — server lifecycle, IncomingMessage/ServerResponse, request & Agent

`http.createServer([options][, requestListener])` returns an `http.Server`. The lifecycle is
event-driven, and the events you actually wire up are:

- **`'request'`** `(req, res)` — the normal path; `req` is an **`IncomingMessage`** (a readable
  stream: `req.method`, `req.url`, `req.headers`, `req.on('data'|'end')`), `res` is a
  **`ServerResponse`** (a writable stream: `res.writeHead(status, headers)`, `res.setHeader`,
  `res.getHeader`, `res.flushHeaders()`, `res.write`, `res.end`).
- **`'connection'`** `(socket)` — a new TCP socket (pre-parse); **`'clientError'`** `(err, socket)`
  — malformed request or header overflow. The default `clientError` handler replies `400 Bad
  Request`, or **`431`** on `HPE_HEADER_OVERFLOW`; override it but always check `socket.writable`
  and ignore `ECONNRESET`.
- **`'upgrade'`** `(req, socket, head)` — protocol upgrade (WebSocket handshake lives here).

**Client side:** `http.request(options|url[, callback])` returns a writable
`ClientRequest`; `http.get` is the same but auto-`end()`s and is GET-only. Key options:
`hostname`/`host`, `port` (default 80), `method` (default `GET`), `path`, `headers`, `agent`,
`timeout`. Header size is capped by **`--max-http-header-size`** (default **16 KiB**), readable as
`http.maxHeaderSize`.

**The `http.Agent`** manages the socket pool for outbound requests (the default is
`http.globalAgent`, which historically has **`keepAlive: false`**). Construct your own to reuse
connections. Options and defaults:

| Option | Default | Meaning |
| --- | --- | --- |
| `keepAlive` | `false` | Reuse sockets across requests (set `true` in production clients). |
| `keepAliveMsecs` | `1000` | Initial delay for TCP keep-alive probes on kept sockets. |
| `maxSockets` | `Infinity` | Max concurrent sockets **per origin**. `Infinity` is a footgun — bound it. |
| `maxFreeSockets` | `256` | Max idle kept-alive sockets per origin. |
| `maxTotalSockets` | `Infinity` | Max sockets across **all** origins. |
| `scheduling` | `'lifo'` | `'lifo'` reuses the hottest socket (better for keep-alive expiry); `'fifo'` round-robins. Default became `'lifo'` in v15.6. |

### 2. `node:http` — server & socket timeouts (the anti-slowloris knobs)

These four properties are the most operationally important thing in the module. Misconfigured,
they cause hung requests, leaked sockets, and the infamous **502 behind a load balancer**:

- **`server.headersTimeout`** (default **60000 ms**) — max time to receive the *complete* request
  headers. Defeats slowloris header-dribbling.
- **`server.requestTimeout`** (default **300000 ms** / 5 min) — max time from socket connect to the
  full request being received. Defeats slow-body attacks.
- **`server.keepAliveTimeout`** (default **5000 ms**) — how long an idle keep-alive socket stays
  open between requests. **Must be larger than the upstream load-balancer / proxy idle timeout**,
  or the LB reuses a socket Node just closed → `ECONNRESET` surfaces as a 502. (AWS ALB idle is 60s;
  set Node's `keepAliveTimeout` above that.)
- **`server.maxRequestsPerSocket`** (default unlimited) — close a keep-alive socket after N requests.
- `server.timeout` (legacy socket inactivity timeout) and `server.setTimeout()` still exist but the
  three above are the modern, attack-aware controls.

### 3. `node:http2` — secure/insecure servers, sessions, streams, ALPN, compatibility API

- **`http2.createServer()`** = cleartext **h2c** (rarely used by browsers); **`http2.createSecureServer({ key, cert })`** = **h2 over TLS** and the one browsers speak — it advertises **ALPN `'h2'`** automatically. `allowHTTP1: true` lets a secure server fall back to HTTP/1.1 for non-h2 clients.
- **Streams, not connections.** A single TCP connection (`Http2Session`) multiplexes many
  **`Http2Stream`**s. Server side: `server.on('stream', (stream, headers) => { stream.respond({ ':status': 200 }); stream.end(body); })`. Client: **`http2.connect(authority)`** returns a `ClientHttp2Session`; `session.request(headers)` returns a `ClientHttp2Stream` that emits `'response'`.
- Pseudo-headers (`:method`, `:path`, `:scheme`, `:authority`, `:status`) replace the request line.
  `session.settings()` tunes **`initialWindowSize`** (default 65535), **`maxConcurrentStreams`**,
  `enablePush`. Sessions emit `'goaway'` (graceful shutdown) and `'frameError'`.
- **Server push (`stream.pushStream`) is deprecated** — RFC 9113 removed it and Chrome/modern
  browsers no longer support it. Prefer **`103 Early Hints`** (`res.writeEarlyHints`) for preloading.
  Stream **priority** signaling is likewise deprecated.
- **Compatibility API:** `Http2ServerRequest`/`Http2ServerResponse` mimic `http`'s
  `IncomingMessage`/`ServerResponse` so Express-style `(req, res)` handlers run on h2 with minimal
  change. `respondWithFile`/`respondWithFD` stream a file/FD directly.

### 4. `node:https` + `node:tls` — secure context, SNI, ALPN, session resumption

**`node:https`** is HTTP semantics carried over `node:tls`: `https.createServer(options, listener)`
and `https.request` take the same shape as their `http` counterparts **plus** TLS options. There is a
dedicated **`https.Agent`**, which additionally keeps a **client-side TLS session cache** (keyed by
host) so reconnections can resume the TLS session and skip a round trip — a meaningful win for a
keep-alive-light, many-origins client (`maxCachedSessions` bounds it).

The real depth is **`node:tls`**:

- **`tls.createSecureContext({ key, cert, ca, pfx, passphrase, minVersion, maxVersion, ciphers })`** —
  the reusable cert/key bundle. `ca` overrides the default trust store; `minVersion: 'TLSv1.2'` is the
  sane floor.
- **SNI (one server, many certs):** server option **`SNICallback(servername, cb)`** or
  **`server.addContext('*.example.com', ctx)`** picks the cert by requested hostname. Client:
  **`servername`** sets the SNI hostname.
- **ALPN:** **`ALPNProtocols: ['h2', 'http/1.1']`** on server and client negotiates the protocol; read
  the result from **`socket.alpnProtocol`** (`false` if none). This is exactly how h2-vs-h1.1 is chosen.
- **Session resumption** (skip the full handshake on reconnect), two mechanisms:
  **session IDs** (server caches state; `'newSession'`/`'resumeSession'` events) and **TLS tickets**
  (server encrypts state into a ticket the client returns; no server cache, and **`ticketKeys`** /
  `getTicketKeys`/`setTicketKeys` let a fleet share keys behind a load balancer). Client saves the
  `'session'` event buffer and passes it back as `session:` to `tls.connect`. `sessionTimeout` bounds it.

### 5. `node:net` — the TCP connection model, allowHalfOpen, Nagle, keep-alive

`node:net` is the TCP/IPC layer everything above sits on. `net.createServer([opts][, listener])`
emits **`'connection'`** `(socket)`; `net.connect`/`net.createConnection` open a client
**`net.Socket`** (a `Duplex` stream emitting `'data'`, `'end'`, `'close'`, `'error'`, `'timeout'`,
`'ready'`). The socket controls you reach for:

- **`socket.setNoDelay(true)`** disables **Nagle's algorithm** (send small writes immediately instead
  of coalescing) — important for low-latency request/response and chatty protocols.
- **`socket.setKeepAlive(true, delay)`** enables TCP-level keep-alive probes (detect dead peers).
- **`socket.setTimeout(ms)`** fires `'timeout'` on inactivity (it does **not** auto-close — you must
  `socket.destroy()` in the handler).
- **`allowHalfOpen`** (default `false`): when the remote sends FIN (readable `'end'`), Node by default
  also ends the writable side; set `true` to keep writing after the peer is done reading.
  `pauseOnConnect` lets you hand a socket to another process before data flows. `net.BlockList`
  (`addAddress`/`addRange`/`addSubnet`) does IP allow/deny lists. *(Backpressure mechanics of the
  socket stream live in `nodejs-concurrency-internals`.)*

### 6. `node:dgram` — UDP sockets (brief)

Connectionless UDP. **`dgram.createSocket('udp4'|'udp6')`** → a socket you **`bind([port])`** and read
via the **`'message'`** `(msg, rinfo)` event; **`socket.send(msg, port, address)`** to transmit (no
connection, no delivery guarantee). **`socket.connect(port, address)`** pins a default remote so you
can `send(msg)` without re-specifying it. Multicast: **`addMembership`/`dropMembership`**,
`setMulticastTTL`, `setMulticastLoopback`; broadcast: `setBroadcast(true)`. Used for DNS, mDNS/SSDP
discovery, metrics (StatsD), and as the substrate under QUIC/HTTP-3.

### 7. The global `fetch` **is** undici — Dispatcher, Client, Pool, Agent

Node's global **`fetch`/`Request`/`Response`/`Headers`** (stable since v21) is implemented by
**undici**, Node's from-scratch HTTP/1.1 client. Understanding undici *is* understanding `fetch`'s
performance.

- **`Dispatcher`** is the base abstraction; everything is a dispatcher with a `.dispatch()` (and the
  higher-level **`request`/`stream`/`pipeline`/`connect`/`upgrade`** methods). The concrete types:
  - **`Client`** — a single keep-alive connection to one origin.
  - **`Pool`** — a pool of `Client`s to one origin (option **`connections`**); this is what gives you
    parallelism to a single host.
  - **`BalancedPool`** — spreads load across **multiple** upstream origins.
  - **`Agent`** — the default dispatcher: opens a `Pool` per origin on demand (this backs `fetch`).
- **`undici.request(url, opts)`** returns `{ statusCode, headers, body }` where `body` is a stream with
  convenience readers (`body.json()`, `body.text()`); it's lower-overhead than `fetch` when you don't
  need the WHATWG semantics. `undici.stream`/`pipeline` are for zero-copy piping.
- **`setGlobalDispatcher(dispatcher)`** / `getGlobalDispatcher()` swap the dispatcher that **global
  `fetch` uses** — the supported way to set client-wide pool size, timeouts, TLS (`connect` options),
  or a proxy for all `fetch` calls in a process.
- **Interceptors** compose behaviour onto a dispatcher: **`dispatcher.compose(interceptor, ...)`** with
  built-ins for **redirect**, **retry**, **dns**, and **cache** (the modern replacement for the older
  `maxRedirections` option style). **`RetryAgent`** wraps a dispatcher with a `RetryHandler` (backoff,
  idempotent-method retries). **`ProxyAgent`** / **`EnvHttpProxyAgent`** route through an HTTP(S) proxy
  (the latter reads `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`). **`MockAgent`** + `setGlobalDispatcher`
  intercepts requests in tests without a real network.

### 8. undici keep-alive & timeout options (the client-side mirror of §2)

`Client`/`Pool` constructor options and their **current** defaults (verify against your undici
version — these changed historically):

- **`pipelining`** — default **off** (effectively 1 in-flight per connection); HTTP/1.1 pipelining is
  off because of head-of-line blocking. Set higher only against servers you control.
- **`keepAliveTimeout`** — default **4 s**; **`keepAliveMaxTimeout`** — default **10 min** (caps how far
  a server `keep-alive` hint can extend it); `keepAliveTimeoutThreshold` trims a safety margin.
- **`headersTimeout`** — default **30 s** (wait for response headers); **`bodyTimeout`** — default
  **30 s** (max gap between body chunks). A connection-establishment timeout (~10 s) is configured as a
  **Connector** option (`connect: { timeout }`), not a top-level Client default.
- `connect: { ... }` carries TLS options (`ca`, `rejectUnauthorized`, `servername`, ALPN) for HTTPS
  origins; `maxRequestsPerClient` recycles a connection after N requests.

## Tools & frameworks

| Tool / API | What it is | When to reach for it |
| --- | --- | --- |
| **`node:http` / `http.Server`** | Core HTTP/1.1 server + client; the `http.Agent` socket pool. | Any HTTP/1.1 work; the base under every framework. |
| **`node:http2`** | Multiplexed HTTP/2 (h2/h2c), compatibility API. | gRPC-style multiplexing, many small assets, h2 from browsers. |
| **`node:tls` / `node:https`** | TLS plumbing — SNI, ALPN, session resumption — and HTTP-over-TLS. | Terminating TLS in-process, multi-cert hosting, ALPN negotiation. |
| **`node:net`** | Raw TCP / IPC sockets. | Custom wire protocols, proxies, low-latency `setNoDelay` paths. |
| **`node:dgram`** | UDP datagram sockets, multicast. | DNS, discovery (mDNS/SSDP), StatsD metrics, QUIC substrate. |
| **global `fetch` / undici** | WHATWG `fetch` (= undici) and the `Client`/`Pool`/`Agent` client. | Outbound HTTP from a Node service; pooled, retrying, proxied clients. |
| **`undici.MockAgent`** | In-process network mocking via `setGlobalDispatcher`. | Unit-testing code that calls `fetch`/undici without real sockets. |

## Methodology / practical patterns

1. **Always set client keep-alive.** A bare `http.request` with the default `globalAgent`
   (`keepAlive: false`) opens and tears down a TCP+TLS connection per request. Use a shared
   `new http.Agent({ keepAlive: true, maxSockets: <bounded> })`, or for `fetch` call
   `setGlobalDispatcher(new Agent({ connections: N }))` once at startup.
2. **Order the timeout sandwich correctly:** Node `server.keepAliveTimeout` **>** upstream LB idle
   timeout, and give `headersTimeout`/`requestTimeout` finite values so a stuck client can't pin a
   socket forever. Mirror it on the client with undici `headersTimeout`/`bodyTimeout`.
3. **Bound `maxSockets`/`connections`.** `Infinity` (the default) means a downstream slowdown lets
   pending requests open unbounded sockets → fd exhaustion. Size the pool to the downstream's capacity.
4. **Pick the protocol deliberately:** HTTP/2 (`createSecureServer` + ALPN `'h2'`) for many concurrent
   streams to one origin; HTTP/1.1 + a `Pool` of `connections` when the server isn't h2. Don't enable
   HTTP/1.1 `pipelining` on the open internet.
5. **Reuse a `SecureContext`** across connections instead of re-reading PEM per request; enable session
   resumption (tickets + shared `ticketKeys` behind an LB) to cut handshake round-trips.
6. **Test with `MockAgent`**, not a live network: `const mock = new MockAgent(); setGlobalDispatcher(mock); mock.get(origin).intercept({ path }).reply(200, body)`.

## Anti-patterns

- **No timeouts anywhere.** A `fetch`/`http.request` with no `bodyTimeout`/`headersTimeout` to a slow
  peer hangs forever and holds a socket; a server with the defaults removed is a slowloris target.
- **`keepAliveTimeout` below the LB idle timeout** → the LB reuses a socket Node already closed →
  `ECONNRESET` → intermittent **502s** that look random. The #1 Node-behind-ALB bug.
- **`maxSockets: Infinity` / unbounded `connections`** → socket & file-descriptor exhaustion under load
  (`EMFILE`), often mistaken for a memory leak.
- **A fresh `Agent`/`Pool`/`Client` per request** → you've thrown away pooling entirely; create it once
  and share it.
- **Enabling HTTP/1.1 pipelining to arbitrary servers** → head-of-line blocking and corruption with
  non-compliant intermediaries; that's why undici ships it off.
- **Relying on HTTP/2 server push** → removed from browsers and deprecated in RFC 9113; use `103 Early
  Hints` instead.
- **Disabling `rejectUnauthorized` to "fix" a TLS error** → silently disables cert validation (MITM).
  Fix the trust chain via `ca:` instead.

## Troubleshooting

- **Intermittent 502 / `ECONNRESET` behind a proxy** → raise `server.keepAliveTimeout` above the
  upstream idle timeout; confirm with `curl -v` keep-alive reuse.
- **`fetch` is slow / opens too many connections** → you're on the default per-origin pool; install a
  tuned `Agent` via `setGlobalDispatcher` and check `keepAlive` is in effect.
- **`socket hang up` / `UND_ERR_HEADERS_TIMEOUT` / `UND_ERR_BODY_TIMEOUT`** → the server didn't respond
  within undici's 30 s header/body timeout; raise the relevant option or fix the upstream.
- **`EMFILE: too many open files`** → unbounded `maxSockets`/`connections` (or leaked sockets that never
  `end`); bound the pool and `ulimit -n`.
- **`HPE_HEADER_OVERFLOW` / `431`** → headers exceed `--max-http-header-size` (16 KiB); raise the flag or
  shrink cookies/headers.
- **HTTP/2 client gets HTTP/1.1** → ALPN didn't negotiate `'h2'`; check `ALPNProtocols` on both ends and
  read `socket.alpnProtocol` to confirm.
- **TLS handshake slow under load** → no session resumption; wire up tickets/`ticketKeys` and reuse a
  single `SecureContext`. (Event-loop lag while throughput is fine is a different problem — profile the
  loop; see `nodejs-concurrency-internals`.)

## References

- Node.js — `node:http` (Server, IncomingMessage/ServerResponse, http.request/get, http.Agent, headersTimeout/requestTimeout/keepAliveTimeout/maxRequestsPerSocket, clientError, maxHeaderSize): https://nodejs.org/api/http.html
- Node.js — CLI options (`--max-http-header-size`): https://nodejs.org/api/cli.html
- Node.js — `node:http2` (createServer/createSecureServer, http2.connect, Http2Session/Http2Stream, pushStream deprecation, ALPN, settings, compatibility API): https://nodejs.org/api/http2.html
- Node.js — `node:tls` (createSecureContext, SNICallback/addContext, ALPNProtocols/alpnProtocol, session resumption — IDs vs tickets, ticketKeys, sessionTimeout): https://nodejs.org/api/tls.html
- Node.js — `node:https` (createServer/request, https.Agent + TLS session cache): https://nodejs.org/api/https.html
- Node.js — `node:net` (createServer, net.Socket, allowHalfOpen, setNoDelay/Nagle, setKeepAlive, setTimeout, BlockList): https://nodejs.org/api/net.html
- Node.js — `node:dgram` (UDP createSocket, send/bind, 'message', multicast addMembership, connected UDP): https://nodejs.org/api/dgram.html
- Node.js — global `fetch` / WHATWG fetch backed by undici: https://nodejs.org/api/globals.html#fetch
- undici — Dispatcher/Client/Pool/BalancedPool/Agent, request/stream/pipeline, setGlobalDispatcher, interceptors, RetryAgent/ProxyAgent/EnvHttpProxyAgent/MockAgent: https://undici.nodejs.org/
- undici — Client API options & defaults (pipelining, keepAliveTimeout 4s, keepAliveMaxTimeout 10min, headersTimeout 30s, bodyTimeout 30s): https://github.com/nodejs/undici/blob/main/docs/docs/api/Client.md
