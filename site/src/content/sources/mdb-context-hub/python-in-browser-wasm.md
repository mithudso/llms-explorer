---
title: "Python in the Browser & WebAssembly (Pyodide, PyScript, WASI/CPython)"
description: "'Python in the browser' means compiling a Python interpreter to WebAssembly (WASM) so it runs inside the browser's WASM VM (or a server-side WASM runtime) instead of a native OS process. There is no n"
---

# Python in the Browser & WebAssembly (Pyodide, PyScript, WASI/CPython)

## Overview

"Python in the browser" means compiling a Python interpreter to **WebAssembly (WASM)** so it runs inside the browser's WASM VM (or a server-side WASM runtime) instead of a native OS process. There is no native Python in a browser; everything routes through one of two WASM targets of CPython:

- **`wasm32-emscripten`** — CPython compiled with **Emscripten**, which emulates a POSIX-ish environment (a virtual filesystem, a JS-backed libc) on top of the browser/JS host. This is the target **Pyodide** ships, and is the one that runs *in a browser tab* or in Node.js. CPython tier-3 since 3.14 (restored Oct 2024).
- **`wasm32-wasi`** — CPython compiled against the **WASI** (WebAssembly System Interface) ABI, a capability-based syscall layer. Runs in standalone WASM runtimes (**wasmtime**, Wasmer, WasmEdge) for server-side/edge/sandboxed/plugin use, *not* the browser DOM. CPython **tier 2** since 3.13.0 (the first final release to ship it).

A third lever is the **interpreter choice**: full **Pyodide (CPython)** — large but complete, with NumPy/SciPy/pandas — versus **MicroPython** — tiny (~300 KB) and near-instant but a reduced language/stdlib. PyScript lets you pick per-page.

The defining reality of all WASM Python: **single-threaded, sandboxed, no OS.** No real threads, no raw sockets, no blocking stdin, and a multi-megabyte cold-start download for full CPython. Design around these from the start.

```
Browser tab ── Pyodide (wasm32-emscripten) ──► JS host (DOM, fetch, Web APIs) via FFI
Web Worker ── Pyodide/MicroPython ───────────► off-main-thread, keeps UI responsive
Server/edge ── CPython (wasm32-wasi) ────────► wasmtime/Wasmer, capability-gated FS/net
PyScript ──── polyscript core ───────────────► orchestrates either runtime + DOM components
```

## Core Concepts

### 1. The CPython → WASM compile pipeline (shared foundation)
Both targets cross-compile CPython. Emscripten produces a `.wasm` + a JS loader (`pyodide.js`) plus a packaged stdlib; WASI produces a `python.wasm` you feed to a runtime. WASM is **single-threaded by default**; pthreads need SharedArrayBuffer + cross-origin isolation (COOP/COEP headers) and are still not generally usable for CPython's threading model. The **PEP 11 platform tiers** govern support: WASI is **tier 2** (3.13+, PEP 816 pins WASI + WASI-SDK versions per release), Emscripten is **tier 3** (3.14+, PEP 776 defines it). Everything else (Pyodide FFI, packaging) layers on top of this.

### 2. Pyodide — the browser CPython distribution
Pyodide is **a port of CPython to Emscripten/WASM** providing three things: (a) the CPython interpreter compiled with Emscripten + a few patches; (b) a **JS⟺Python foreign function interface (FFI)**; (c) a catalog of third-party packages (NumPy, pandas, scikit-learn, etc.) precompiled to WASM. Loaded with the async `loadPyodide()`; run code with `pyodide.runPython(code)` (sync) or `pyodide.runPythonAsync(code)` (supports top-level `await` via `eval_code_async`). Hit ~1B+ JsDelivr requests in 2025; usage doubling year-over-year. Also powers **Cloudflare Python Workers** and Node.js Python embedding.

### 3. The foreign function interface (FFI) and PyProxy/JsProxy
The FFI is the heart of in-browser Python. Two translation strategies: **convert** (copy a value into a native object of the other language) or **proxy** (wrap the original). Crossing the boundary yields proxies: a Python object handed to JS becomes a **`PyProxy`**; a JS object handed to Python becomes a **`JsProxy`**. `PyProxy.toJs()` (JS) / `to_js()` (Python) does an explicit deep conversion; `create_proxy()` wraps a Python callable as a persistent JS function (e.g. for `addEventListener`). **PEP 818** is upstreaming the *core* of this FFI into CPython itself (the `js` module + proxy machinery) so it's standard, not Pyodide-private.

### 4. PyScript — the framework layer
PyScript is **not a runtime**; it's a framework built on a small core called **polyscript** that orchestrates a runtime (Pyodide *or* MicroPython) plus DOM integration. You write `<script type="py">…</script>` (Pyodide) or `<script type="mpy">…</script>` (MicroPython), configure via `<py-config>`/`<mpy-config>` or an external `pyscript.toml`/`.json`, and get components like `<py-editor>`/`<mpy-editor>` (REPL widgets) and the `pyscript` Python module (`display()`, `when`, `PyWorker`, DOM access). Pyodide is the default runtime "for the foreseeable future"; MicroPython is the lightweight option.

### 5. MicroPython vs Pyodide (the size/capability tradeoff)
- **Pyodide (CPython):** ~11 MB+ runtime download (full distribution effectively ~15 MB; big packages like pandas/SciPy add more), slow cold start, but real CPython with the C-extension scientific stack and `micropip`/PyPI.
- **MicroPython:** ~300 KB total, **loads instantly and runs in <100 ms**, ideal for mobile/constrained/educational/visualization use. No `micropip`/PyPI; uses `mip` + `micropython-lib`. A reduced language and stdlib.
- Choose MicroPython when startup latency and footprint dominate; choose Pyodide when you need the real CPython ecosystem.

### 6. Packaging for WASM Python (PEP 783 / PyEmscripten ABI)
Historically you could not put WASM wheels on PyPI; you used anaconda.org or jsdelivr. **PEP 783 (accepted)** defines a `pyodide_${YEAR}_${PATCH}_wasm32` platform tag (the **PyEmscripten** ABI) so binary wheels can ship on PyPI. Key rule: **one ABI per Python version** — wheels built for one Pyodide build work across all Pyodide versions sharing that Python version. Build with `pyodide build`/`pyodide-build` or `cibuildwheel`; no Docker needed (just Linux + matching Python/Node/Emscripten). Pure-Python wheels install via **`micropip.install()`**; Pyodide-built C-extension packages also load via `pyodide.loadPackage()` (lower overhead, more limited).

### 7. The WASI/CPython target (server-side & sandboxed)
WASI CPython runs *outside* the browser in a WASM runtime (**wasmtime** is the officially recommended one). Use cases: sandboxed plugin execution, edge functions, embedding Python as a guest with host-provided functions, and capability-secure execution (the runtime grants explicit FS/socket capabilities; nothing is ambient). Cross-compile via `Tools/wasm/` / `Platforms/WASI` in the CPython tree (configure for the build Python, then the host WASI Python with the WASI-SDK). You can even drive a WASI CPython from a host and extend it with host functions. **PEP 816** governs which WASI/WASI-SDK versions a CPython release targets.

## Tools / Frameworks

| Tool | Layer | Use it for |
|---|---|---|
| **Pyodide** | CPython on Emscripten/WASM | Full Python in a browser tab / Node / Cloudflare Workers; scientific stack |
| **PyScript** | Framework over polyscript | Declarative `<script type="py">` apps, DOM components, runtime switching |
| **polyscript** | PyScript's core | Low-level runtime orchestration (used by PyScript) |
| **MicroPython (WASM)** | Lightweight interpreter | Instant-start, small-footprint browser Python |
| **micropip** | Python pkg installer (Pyodide) | Install pure-Python/Pyodide wheels from PyPI/URL at runtime |
| **pyodide-build / cibuildwheel** | Build toolchain | Produce PEP 783 `pyodide_*` wheels |
| **wasmtime** | WASI runtime | Run `wasm32-wasi` CPython server-side/sandboxed |
| **WASI SDK / Emscripten SDK** | Compilers | Cross-compile CPython to the respective WASM target |

## Methodology — choosing & wiring an approach

1. **Where does it run?** Browser DOM → Emscripten (Pyodide/PyScript). Server/edge/plugin/sandbox → WASI + wasmtime.
2. **How much Python do you need?** Scientific stack / real CPython → Pyodide. Tiny + instant → MicroPython.
3. **Hand-rolled or framework?** Direct JS control / embedding → Pyodide JS API. Declarative HTML app → PyScript.
4. **Keep the UI alive:** run the interpreter in a **Web Worker** so heavy compute / package loads don't block the main thread.
5. **Plan the FFI boundary:** decide convert-vs-proxy per value, and own PyProxy/JsProxy lifetimes (destroy explicitly).
6. **Package strategy:** prefer PyPI wheels via `micropip`; for C extensions ensure a PEP 783 `pyodide_*` wheel or a Pyodide-built package exists.

## Practical Patterns

**Bootstrap Pyodide and run code (browser/Node):**
```js
const pyodide = await loadPyodide();              // async; loads the WASM + stdlib
await pyodide.loadPackage("numpy");                // load a Pyodide-built package
await pyodide.runPythonAsync(`
    import numpy as np
    np.arange(5).sum()
`);                                                 // top-level await supported
```

**Install a pure-Python PyPI wheel at runtime:**
```js
await pyodide.loadPackage("micropip");
const micropip = pyodide.pyimport("micropip");
await micropip.install("snowballstemmer");          // from PyPI / JsDelivr / URL
```

**FFI: persistent callback + explicit cleanup:**
```js
const proxy = pyodide.runPython("lambda evt: print('clicked', evt.type)");
const handler = proxy.create_proxy ? proxy : pyodide.ffi.create_proxy(proxy);
document.body.addEventListener("click", handler);
// later, when removed: handler.destroy(); proxy.destroy();  // avoid the leak
```

**PyScript app with external config + worker:**
```html
<script type="py" src="./main.py" config="./pyscript.toml" worker></script>
```
```toml
# pyscript.toml
packages = ["pandas"]              # micropip names (Pyodide only)
[files]
"./data.csv" = "data.csv"          # mount a file into the virtual FS
```

**Run CPython under WASI with wasmtime (server-side):**
```bash
wasmtime run --dir=. python.wasm -- script.py     # --dir grants FS capability explicitly
```

## Anti-Patterns

- **Assuming threads/multiprocessing work.** Pyodide has **no threading or multiprocessing**; packages using them need patching to disable it. Don't port a thread-pool design unchanged.
- **Expecting raw sockets / blocking network.** No raw socket access; only HTTP(S), subject to CORS; no synchronous networking on the main thread. The `socket` module is present but always non-blocking and needs a server-side WebSocket-to-TCP proxy.
- **Leaking PyProxy/JsProxy.** A return-value `PyProxy` must be `destroy()`-ed or it leaks; a JS→Python→JS reference loop never gets GC'd. Don't rely solely on `FinalizationRegistry`.
- **Blocking the main thread.** Loading Pyodide + big packages on the UI thread freezes the page. Use a Web Worker.
- **Shipping full Pyodide for trivial logic.** Don't download 15 MB to run 10 lines — use MicroPython, or lazy-load Pyodide only when needed.
- **Treating files as persistent.** The Emscripten virtual FS is in-memory; files vanish on refresh/close unless you persist them out (IndexedDB/server).
- **Putting raw WASM wheels on PyPI pre-PEP-783, or mixing ABIs.** Use the `pyodide_*` tag and respect one-ABI-per-Python-version.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Page freezes during load/compute | Interpreter on main thread → move to Web Worker |
| `ModuleNotFoundError` after `micropip.install` | Package has C extensions with no Pyodide/PEP-783 wheel; try `loadPackage`, find a Pyodide-built build, or pick a pure-Python alt |
| Memory grows / tab eventually crashes | Un-destroyed PyProxy/JsProxy or reference loops; call `.destroy()`, break loops; also bounded by browser memory |
| `threading`/`multiprocessing` errors | Unsupported in Pyodide; disable/patch the threaded path |
| Network call fails (CORS / "not allowed") | Browser sandbox + CORS; only HTTP(S); use `pyodide.http`/`fetch` and a proxy for TCP |
| Streaming download falls back to full body | Streaming needs a Web Worker on a **cross-origin-isolated** site (COOP/COEP) |
| Huge first-load latency | Full CPython cold start; switch to MicroPython, lazy-load, or cache the runtime |
| WASI build can't read files | wasmtime grants no ambient FS; pass `--dir` to grant the capability |

## References

- Pyodide — official site & docs (architecture, JS API, type conversions, packaging): https://pyodide.org/ ; usage: https://pyodide.org/en/stable/usage/ ; WASM constraints: https://pyodide.org/en/stable/usage/wasm-constraints.html ; PyEmscripten ABI: https://pyodide.org/en/stable/development/abi.html
- Pyodide GitHub: https://github.com/pyodide/pyodide ; blog (0.26/0.28 releases): https://blog.pyodide.org/
- PEP 818 — Adding the Core of the Pyodide FFI to Python: https://peps.python.org/pep-0818/
- PEP 783 — Emscripten Packaging (accepted; `pyodide_*` wheel tag): https://peps.python.org/pep-0783/
- PEP 776 — Emscripten Support (tier-3 target def): https://peps.python.org/pep-0776/
- PEP 816 — WASI Support (WASI/WASI-SDK version policy): https://peps.python.org/pep-0816/
- PyScript docs — configuration, workers, FFI, features: https://docs.pyscript.net/2025.3.1/user-guide/ ; polyscript: https://pyscript.github.io/polyscript/
- Anaconda — PyScript + MicroPython runtime (size/startup numbers): https://www.anaconda.com/blog/pyscript-updates-bytecode-alliance-pyodide-and-micropython
- CPython WASI platform dir & build helpers: https://github.com/python/cpython/tree/main/Platforms/WASI ; Tools/wasm README: https://fossies.org/linux/Python/Tools/wasm/README.md
- Cloudflare — Python Workers via Pyodide/WASM: https://blog.cloudflare.com/python-workers/
- Running CPython on WASI with wasmtime + host functions: https://www.manjusaka.blog/posts/2024/10/02/how-to-extend-the-wasi-python-by-using-host-function-en/
