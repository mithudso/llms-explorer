---
title: "Web Platform and Browser APIs"
description: "programming-languages hub reference for the browser-side JavaScript platform — the APIs that ship in the browser, not in the ECMAScript language (javascript-nodejs) or in Node. This is the half of 'Ja"
---

# Web Platform & Browser APIs

programming-languages hub reference for the **browser-side JavaScript platform** — the APIs that ship in the *browser*, not in the ECMAScript language (`javascript-nodejs`) or in Node. This is the half of "JavaScript" that lives between the language and the framework. Sibling to `javascript-nodejs`, `javascript-runtimes-deno-bun-edge`, and `frontend-design`.

**TRIGGER:** which browser API to use; DOM/events; the observer family; Fetch/Streams/abort; Web Components & Shadow DOM; Service Workers / offline / PWA; client-storage choice; real-time transports (WebSocket/WebRTC/WebTransport/SSE); View Transitions, Navigation API, WebGPU.
**SKIP:** JS language/runtime semantics → `javascript-nodejs`; non-Node runtimes → `javascript-runtimes-deno-bun-edge`; framework rendering (React/Vue/Svelte) → `frontend-design` / frontend-frameworks (concept-tree gap); CSS & visual design → `frontend-design`; Chrome-extension MV3 surfaces → `chrome-dev`.

## Map of the platform (by purpose)

| Area | Core APIs | Notes |
|---|---|---|
| **DOM & events** | `querySelector`, `EventTarget`, event delegation, `CustomEvent`, capture/bubble, passive listeners | Prefer delegation + `AbortController` to remove listeners in bulk |
| **Networking** | `fetch`, `Request`/`Response`, `Headers`, `AbortController`/`AbortSignal`, `ReadableStream`/`WritableStream`/`TransformStream` | Streams enable progressive parse; `AbortSignal.timeout()` for deadlines |
| **Components** | Custom Elements, **Shadow DOM**, `<template>`/`<slot>`, declarative shadow DOM, constructable stylesheets | Framework-agnostic encapsulation; SSR via declarative shadow DOM |
| **Offline / PWA** | **Service Worker** lifecycle, `Cache` API, `fetch` interception, Background Sync, Web App Manifest | SW is event-driven & killable — never assume in-memory state persists (see `chrome-dev` for MV3 parallels) |
| **Client storage** | `localStorage`/`sessionStorage`, **IndexedDB**, Cache API, **OPFS** (Origin Private File System), Storage quotas | See `dexie-indexeddb-local-first-reviewer` for IndexedDB ergonomics |
| **Observers** | `IntersectionObserver`, `ResizeObserver`, `MutationObserver`, `PerformanceObserver` | Replace scroll/resize polling; PerformanceObserver feeds Core Web Vitals |
| **Real-time** | `WebSocket`, **WebRTC** (data + media), **WebTransport** (HTTP/3), Server-Sent Events (`EventSource`) | WebTransport = low-latency, unreliable-or-reliable streams over HTTP/3; SSE for one-way server push |
| **Compute & security** | **Web Workers**, `SharedArrayBuffer`/`Atomics`, **Web Crypto** (`crypto.subtle`), `crypto.randomUUID()`, the WASM boundary | Offload CPU to workers; Web Crypto for hashing/signing/encryption — never hand-roll crypto |
| **Media & device** | Media Capture (`getUserMedia`), Web Audio, Canvas 2D, **WebGL/WebGPU**, Geolocation, Permissions, Web Bluetooth/USB/Serial | Capability-gated; check `navigator.permissions` |

## 2026 frontier (confirmed current)

- **Navigation API → Baseline Newly Available (Jan 2026)** — Chrome, Edge, Firefox 147, Safari 26.2. The modern replacement for the History API: single `navigate` event, intercept + transition, proper SPA routing. Prefer it over `history.pushState` for new SPAs.
- **View Transitions API** — same-document *and* cross-document; **element-scoped** transitions now enable targeted animations without animating the whole page.
- **WebGPU** — in production browsers; 2026 is the consistency/predictability year. Compute + 3D; the successor to WebGL.
- **HTML-in-Canvas** — render real DOM elements into a canvas (WebGL/WebGPU) while staying accessible, searchable, translatable.
- **Document Picture-in-Picture** — always-on-top window with arbitrary HTML (Firefox 151 desktop + Chromium).
- **Soft Navigations API** — brings Core Web Vitals measurement to SPA route changes.
- **`Temporal`** (language, via `javascript-nodejs`) lands alongside as the modern date/time layer these APIs increasingly assume.

## Selection guidance

1. **One-way server push?** SSE (`EventSource`) — simplest, auto-reconnect. **Bidirectional low-latency?** WebSocket. **Media or P2P?** WebRTC. **HTTP/3 streams / unreliable datagrams?** WebTransport.
2. **Client storage:** key/value tiny + sync → `localStorage`; structured/queryable/large → IndexedDB (via Dexie); HTTP responses → Cache API; real files / SQLite-in-browser → OPFS.
3. **Watching layout/visibility?** Use the matching observer, never a `scroll`/`resize` polling loop.
4. **Encapsulated, framework-free widget?** Custom Element + Shadow DOM.
5. **CPU-heavy work?** Web Worker (+ `Atomics`/`SharedArrayBuffer` for shared state); push to WASM if numeric.
6. **SPA routing (new)?** Navigation API + View Transitions, not `history.pushState` + manual diffing.

## Anti-patterns

- Polling `scroll`/`resize`/`setInterval` where an observer exists.
- Assuming a Service Worker keeps in-memory state across events — it gets terminated.
- Hand-rolling crypto instead of `crypto.subtle`; using `Math.random()` for tokens instead of `crypto.getRandomValues`/`randomUUID`.
- Blocking the main thread with heavy compute instead of a Worker.
- New SPA routing on the History API when the Navigation API is now Baseline.
- Unbounded `fetch` with no `AbortSignal.timeout()` — leaks pending requests.

## Sources

- "New to the web platform in January / May 2026" — web.dev/blog
- "Navigation API Reaches Baseline Newly Available" — InfoQ (May 2026)
- "15 updates from Google I/O 2026 (Chrome)" — developer.chrome.com/blog/chrome-at-io26
- Microsoft Edge 147-149 web platform release notes — learn.microsoft.com
- MDN Web Docs — Web APIs reference (canonical)
