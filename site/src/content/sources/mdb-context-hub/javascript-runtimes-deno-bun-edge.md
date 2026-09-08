---
title: "JavaScript/TypeScript Runtimes (Deno, Bun, Edge) & WinterTC Interop"
description: "PROVENANCE: Authored by /dr (deep-research-and-build) on 2026-05-31."
---

<!--
PROVENANCE: Authored by /dr (deep-research-and-build) on 2026-05-31.
HUB: programming-languages (reference spoke). NOT a standalone top-level skill.
SCOPE: Alternative/non-Node JS-TS runtimes (Deno 2.x, Bun 1.x) + edge runtimes + the
WinterTC/WinterCG cross-runtime interop standard. Cross-references the sibling
javascript-nodejs and nodejs-concurrency-internals references for Node-specific depth.
SOURCES: WinterTC ECMA-429 (min-common-api.proposal.wintertc.org), W3C WinterCG→WinterTC
transition, Deno 2 blog/docs (deno.com, docs.deno.com), Bun 1.2/1.3 blog+docs (bun.com),
Cloudflare Workers nodejs_compat docs+blog, Vercel Edge Runtime, Deno Deploy docs.
-->

# JavaScript/TypeScript Runtimes: Deno 2.x, Bun 1.x, Edge Runtimes & WinterTC Interop

A `programming-languages` hub reference covering the **non-Node JS/TS runtime landscape** and the
**cross-runtime interop standard** that ties them together. For Node.js language/runtime APIs and
event-loop internals, defer to the sibling references `javascript-nodejs.md` and
`nodejs-concurrency-internals.md` — this file assumes that foundation and focuses on what differs.

## Overview

There are now four practically-relevant server-side JS/TS execution targets:

| Runtime | Engine | Language | Killer feature | Node compat posture |
|---|---|---|---|---|
| **Node.js** | V8 | JS/TS (via loader) | Ecosystem incumbent | n/a (the baseline) |
| **Deno 2.x** | V8 | TS-native, JS | Secure-by-default, TS w/o config, JSR | Backwards-compatible w/ Node + npm |
| **Bun 1.x** | JavaScriptCore | TS-native, JS | All-in-one (runtime+pm+test+bundler), speed | Drop-in Node replacement, ~90%+ test suite |
| **Edge** (workerd / Vercel Edge / Deno Deploy) | V8 isolates | JS/TS | Sub-ms cold start, global POPs | Web-standard subset + opt-in Node compat |

The unifying thread is **WinterTC** (formerly WinterCG): the standard defining the **Minimum Common
Web Platform API** — the subset of browser/Web APIs every server runtime implements identically, so
code written to that surface is portable across all of them. Understand WinterTC first; it is the
shared branch every runtime below inherits from.

---

## Core Concept 1 — WinterTC / WinterCG & the Minimum Common Web Platform API (the shared foundation)

**History.** WinterCG (Web-interoperable Runtimes Community Group, a W3C CG founded by Cloudflare,
Vercel, Deno, Shopify and others) incubated a "minimum common API." In **January 2025** WinterCG was
wound down and the work moved to **Ecma TC55** ("WinterTC" — Technical Committee on Web-interoperable
Server Runtimes). The spec is now **ECMA-429** ("Minimum common web API"), adopted by the Ecma
General Assembly in December 2025, with **yearly snapshots**.

**What's in the Minimum Common Web Platform API** (the portable surface):
- **Fetch & data:** `fetch()`, `Headers`, `Request`, `Response`, `Blob`, `File`, `FormData`
- **Streams:** `ReadableStream`, `WritableStream`, `TransformStream` + controllers; `CompressionStream`/`DecompressionStream`
- **Encoding/text:** `TextEncoder`/`TextDecoder` (+ stream variants), `atob`/`btoa`
- **Crypto:** `crypto` (`Crypto`, `CryptoKey`, `SubtleCrypto`) — Web Crypto, not Node `crypto`
- **URL:** `URL`, `URLSearchParams`, `URLPattern`
- **Events/messaging:** `Event`, `EventTarget`, `CustomEvent`, `AbortController`/`AbortSignal`, `MessageChannel`/`MessagePort`, `MessageEvent`
- **Timers:** `setTimeout`/`setInterval`/`clear*`, `queueMicrotask`, `performance`
- **Utilities:** `structuredClone`, `console`, `navigator.userAgent`, `reportError`
- **WebAssembly:** `WebAssembly.*`
- **Global handlers:** `onerror`, `onunhandledrejection`, `onrejectionhandled`

**Explicitly NOT required:** Web Workers, the DOM (`window`, `document`), and HTML element
interfaces. (WinterTC plans future *conformance levels* — e.g. CLI/File-Systems, Graphics, Servers
with advanced networking — layered above the minimum.)

**Runtime Keys** (separate WinterTC registry): standardized identifiers for runtimes used in
`package.json` `exports` conditions, `engines`, and runtime detection. Common keys: `node`, `deno`,
`bun`, `workerd`, `edge-light`, `electron`, `fastly`, `netlify`, `react-native`, `react-server`.
Keys are immutable once approved and require "proof of use." Use them to ship runtime-specific entry
points:
```json
{ "exports": { "workerd": "./dist/edge.js", "deno": "./dist/deno.js",
               "node": "./dist/node.js", "default": "./dist/default.js" } }
```
> Practical rule: write to the **Minimum Common API** by default; only branch on a Runtime Key when
> you genuinely need a runtime-specific capability. Branching is the exception, portability the rule.

---

## Core Concept 2 — Deno 2.x

Deno 2.0 shipped **October 2024** (four years after 1.0); the line is now considered stable and
production-ready, with a **Long-Term Support (LTS)** channel.

**Headline of 2.x = Node/npm backwards compatibility** (the thing that blocked adoption in 1.x):
- Understands `package.json`, `node_modules/`, and **npm workspaces** — run Deno inside existing
  ESM Node projects.
- `npm:` specifiers (`import express from "npm:express@4"`) and `node:` builtins
  (`import { createServer } from "node:http"`).
- Package-management subcommands: `deno install`, `deno add`, `deno remove` (so `deno` doubles as a
  package manager). `deno install` is reported ~15% faster than npm cold-cache, ~90% faster hot-cache.
- `nodeModulesDir: "auto" | "manual"` in `deno.json` (or `--node-modules-dir=auto|manual`) controls
  whether a real `node_modules/` is materialized.

**Defining Deno traits (still true in 2.x):**
- **Secure by default** — no file/network/env access unless granted: `--allow-net`, `--allow-read`,
  `--allow-env`, or `--allow-all`/`-A`. This is the biggest behavioral difference from Node/Bun.
  (Node has since added an *opt-in* parallel — the stable 24.x Permission Model, `node --permission`
  + `--allow-fs-read`/`--allow-net`/etc.; see the sibling reference `nodejs-typescript-and-runtime-features.md`.
  Deno's is the inverse default: deny-by-default vs Node's allow-by-default.)
- **TypeScript with zero config** — run `.ts` directly, no `tsconfig`/transpile step required.
- **Web-standard first** — `fetch`, Web Crypto, streams are globals (WinterTC alignment).
- **Built-in toolchain** — `deno fmt`, `deno lint`, `deno test`, `deno bench`, `deno compile`
  (single-file executables), `deno task` (script runner).
- **Config:** `deno.json`/`deno.jsonc` — imports map, tasks, lint/fmt config, compiler options.
- **JSR** (`jsr:` / jsr.io) — Deno's TypeScript-first registry; publishes TS source, generates docs,
  works across runtimes (also installable from npm).
- **Deno KV** — built-in key-value store (`Deno.openKv()`); on Deno Deploy it's globally distributed
  on FoundationDB. Available in Node via the `@deno/kv` npm package (SQLite-backed locally).
- **Deno Queues** — `kv.enqueue()` / `kv.listenQueue()`, at-least-once delivery.

---

## Core Concept 3 — Bun 1.x (runtime + package manager + test + bundler)

Bun is an **all-in-one toolkit** written in **Zig**, powered by **JavaScriptCore** (not V8) — the
JSC choice drives its fast startup and low memory. Positioned as a **drop-in Node.js replacement**.

**Node compatibility:** since 1.2, Bun runs the **Node.js test suite on every commit**; many core
modules (`node:http`, `node:http2`, `node:dgram`, `node:cluster`, `node:zlib`, etc.) pass **>90%** of
their tests. Bun also implemented V8 C++ APIs inside JSC so native N-API addons (e.g. `cpu-features`)
work unmodified.

**As a package manager (`bun install`)** — works in any `package.json` project:
- Up to ~25x faster than npm; supports **workspaces** (reads the `workspaces` key, single-pass install,
  de-dup), git/http/tarball deps, custom registries, `.npmrc`.
- **`bun.lock`** — text-based JSONC lockfile (default since **1.2**, replacing binary `bun.lockb`);
  reviewable in PRs, mergeable. Migrate with
  `bun install --save-text-lockfile --frozen-lockfile --lockfile-only` then delete `bun.lockb`.
- **Isolated installs** (1.3): central store in `node_modules/.bun/` with symlinks → packages only see
  declared deps (kills phantom deps). Default linker: *isolated* for new monorepos, *hoisted* for new
  single packages and pre-existing projects (backward compat).
- Commands: `bun add/remove/update`, `bun outdated`, `bun publish`, `bun patch`, `bun run --filter`.

**Built-in runtime APIs (the `Bun.*` namespace + `bun:` modules):**
- `Bun.serve()` — HTTP/WebSocket server with static routes (~40% faster than dynamic handlers);
  Express runs ~3x faster on Bun than Node.
- `bun:sqlite` — native SQLite (`query.as(Class)` for ORM-less mapping).
- `Bun.sql` — native PostgreSQL client, tagged-template parameterized queries, pooling (~50% faster
  than popular Node Postgres libs); also `Bun.redis`.
- `Bun.s3` — built-in S3 client (~5x faster downloads than `@aws-sdk/client-s3`), presigned URLs,
  multipart `writer()`, integrates with `fetch()`/`Bun.serve()`.
- `Bun.file()` (`.delete()`, `.stat()`, S3-backed), `Bun.udpSocket()`, `Bun.color()`.

**Test runner (`bun test`):** Jest-compatible expect, JUnit XML + LCOV for CI, inline snapshots
(`toMatchInlineSnapshot()`), `test.only()` w/o flags.

**Bundler/build:** HTML imports, built-in CSS parser (LightningCSS-derived), bytecode caching (~2x
faster startup), cross-compilation (build Windows/macOS binaries on Linux), `bun build --compile`.

---

## Core Concept 4 — Edge Runtimes (workerd / Vercel Edge / Deno Deploy)

Edge runtimes run JS in **V8 isolates** (lightweight contexts, not containers) distributed across
global POPs — **sub-millisecond cold starts**, no per-request VM boot. The execution model is a
handler: `Request → Response`. They expose the **WinterTC Minimum Common API**, *not* full Node.

**Hard constraints to design around:**
- **Stateless** — no durable in-memory state between requests; persistence needs external stores
  (KV, D1, Durable Objects, databases-over-HTTP).
- **Tight CPU/memory budgets** — e.g. memory commonly capped ~128 MB, CPU time tens of ms (provider-
  and plan-specific; Cloudflare offers higher CPU limits on paid tiers).
- **No raw filesystem / no long-running event loop / no Node `net` server** by default.
- TCP/raw-socket and many npm packages that assume Node internals won't work unless a compat shim is on.

**Providers:**
- **Cloudflare Workers (workerd)** — V8 isolates, 330+ POPs. **`nodejs_compat`** is an umbrella
  compatibility flag enabling Node APIs incrementally (granular sub-flags exist). Unsupported APIs are
  polyfilled by **Wrangler via `unenv`** when `nodejs_compat` is on and the **compatibility date** is
  ≥ `2024-09-23`. 2025 added real implementations gated by compat date: `node:net`/`node:dns`/
  `node:timers` (Jan 2025), `node:fs` + Web FS (`enable_nodejs_fs_module`, auto ≥ `2025-09-15`),
  `node:os` (≥ `2025-09-15`), `node:console` (≥ `2025-09-21`), `node:vm` stub (≥ `2025-10-01`).
  Storage/compute primitives: KV, R2, D1, Durable Objects, Queues, Cron Triggers.
- **Vercel Edge Functions / Edge Runtime** — V8 + a **subset of Node APIs** ("Edge Runtime"),
  WinterCG/WinterTC-compliant; open-source `edge-runtime` package emulates it locally. Fast cold
  starts; many npm packages work if they stick to the Web-standard subset.
- **Deno Deploy** — multi-tenant V8 **isolate cloud**; TS-first, native ESM, no bundler step. Now
  supports **`npm:` specifiers and `node:` builtins** (run existing Node apps like `node:http` at the
  edge). Primitives: **Deno KV** (FoundationDB-backed, globally replicated), **Deno Queues**.
  **Subhosting** = run *your users'* untrusted code securely in isolates (multi-tenant PaaS). Dec 2025:
  detects Deno/npm **workspace/monorepo** configs to deploy from subdirectories. (Note the
  "Deploy Classic" → new Deno Deploy migration path.)

**Compatibility-date discipline (Cloudflare):** the `compatibility_date` (+ optional
`compatibility_flags`) pins runtime behavior. Bumping the date can flip on new Node modules or change
defaults — treat it as a deliberate, tested upgrade, not a passive value.

---

## Core Concept 5 — Choosing & migrating between runtimes

**Decision guide:**
- **Maximum ecosystem certainty / existing large app** → Node.js (the baseline; see `javascript-nodejs.md`).
- **TS-first, security sandboxing, batteries-included tooling, JSR** → **Deno 2.x**.
- **Raw speed + single-tool DX (install/run/test/bundle), heavy local I/O (SQLite/Postgres/S3)** → **Bun 1.x**.
- **Global low-latency, request/response, sub-ms cold start, no servers to manage** → **Edge**.

**Portability strategy (works everywhere):**
1. Code to the **Minimum Common Web Platform API** (fetch/streams/Web Crypto/URL/TextEncoder).
2. Prefer ESM; use `package.json` `exports` with **Runtime Keys** only for genuine per-runtime branches.
3. Keep Node-specific built-ins (`fs`, `net`, native addons) behind an abstraction so edge targets can
   swap them for a Web-standard or platform primitive.
4. Verify with each runtime's compat tracking (Bun's Node test-suite pass rate; Cloudflare's
   `nodejs_compat` + compat-date matrix; Deno's `node:`/`npm:` support).

---

## Practical Patterns

- **One server, three runtimes:** a handler exporting `default { fetch(req) { return new Response(...) } }`
  is the portable shape — it runs on Deno (`Deno.serve`), Bun (`Bun.serve`/default export), and edge
  (workerd/Vercel) with minimal glue.
- **Deno running a Node app:** add `package.json`, set `nodeModulesDir: "auto"` in `deno.json`, use
  `deno install` then `deno run -A npm:...` — no rewrite needed for ESM projects.
- **Bun as a faster CI package manager only:** drop `bun install` into a Node project (commit
  `bun.lock`), keep running the app on Node — Bun-as-pm is decoupled from Bun-as-runtime.
- **Edge + state:** never hold state in module scope expecting persistence; route durable state to KV/
  D1/Durable Objects (Cloudflare) or Deno KV/Queues (Deno Deploy).

## Anti-Patterns

- **Assuming "Node-compatible" = 100%.** Bun ~90%+ on *supported* modules; Cloudflare's coverage is
  gated by compat date/flags; Deno supports `node:`/`npm:` but not every native edge case. Test, don't assume.
- **Using Node `crypto`/`Buffer`/`fs` in edge code** that targets the Web-standard subset — reach for
  Web Crypto (`crypto.subtle`), `Uint8Array`/`Blob`, and platform storage instead.
- **Leaving Cloudflare `compatibility_date` stale (or bumping it blind).** Stale = you miss fixes/new
  modules; blind bump = behavior changes silently. Pin and upgrade deliberately.
- **Committing `bun.lockb` (binary) in 2025+.** Migrate to text `bun.lock` for reviewable diffs.
- **Relying on phantom dependencies** under Bun's hoisted linker — use isolated installs in monorepos.
- **Shipping a Deno script that silently needs broad perms** — scope `--allow-*` tightly; `-A` defeats
  the security model.

## Troubleshooting

- *npm package fails on edge* → it likely imports a Node built-in; enable `nodejs_compat` + check
  compat date (Cloudflare), or refactor to the Web-standard subset.
- *Deno "Requires net access" / permission error* → add the matching `--allow-net`/`--allow-read` flag.
- *Bun behaves differently from Node on a module* → check Bun's Node compatibility tracker for that
  `node:` module's pass rate; file/upstream if it's a gap.
- *Cold start still slow on "edge"* → confirm you're on an isolate runtime (workerd/V8 isolates), not a
  container-backed serverless function masquerading as edge.
- *Lockfile merge conflicts in Bun* → you're on binary `bun.lockb`; migrate to text `bun.lock`.

## References

- WinterTC Minimum Common Web Platform API (ECMA-429): https://min-common-api.proposal.wintertc.org/
- WinterTC FAQ / TC55: https://wintertc.org/faq
- W3C: Goodbye WinterCG, welcome WinterTC (Jan 2025): https://www.w3.org/community/wintercg/2025/01/10/goodbye-wintercg-welcome-wintertc/
- WinterTC Runtime Keys proposal: https://runtime-keys.proposal.wintercg.org/
- Announcing Deno 2: https://deno.com/blog/v2.0
- Deno Node & npm compatibility docs: https://docs.deno.com/runtime/fundamentals/node/
- Native npm support on Deno Deploy: https://deno.com/blog/npm-on-deno-deploy
- Deno KV via npm: https://deno.com/blog/kv-npm
- Bun (GitHub): https://github.com/oven-sh/bun
- Bun 1.2 release: https://bun.com/blog/bun-v1.2
- Bun text lockfile: https://bun.com/blog/bun-lock-text-lockfile
- Bun package manager / install docs: https://bun.com/docs/pm/cli/install
- Cloudflare Workers Node.js compatibility: https://developers.cloudflare.com/workers/runtime-apis/nodejs/
- Cloudflare compatibility flags: https://developers.cloudflare.com/workers/configuration/compatibility-flags/
- A year of Node.js compat in Workers (2025): https://blog.cloudflare.com/nodejs-workers-2025/
- Vercel Edge Runtime: https://edge-runtime.vercel.app/
