---
title: "CPython Runtime Internals (Free-Threading, Subinterpreters, JIT)"
description: "> Reference file — part of the programming-languages hub. Authored via /dr (deep-research). Cross-refs: python-patterns (modern Python idioms) and nodejs-concurrency-internals (the parallel runtime-co"
---

<!-- hub-reference-banner -->
> **Reference file — part of the `programming-languages` hub.** Authored via `/dr` (deep-research). Cross-refs: `python-patterns` (modern Python idioms) and `nodejs-concurrency-internals` (the parallel runtime-concurrency-internals reference for Node/libuv).

# CPython Runtime Internals — Free-Threading, Subinterpreters, and the JIT

Deep reference for the 2023–2026 CPython runtime overhaul. Three PEPs reshape how the interpreter executes, all touching the same machinery (eval loop, reference counting, per-interpreter state):

| PEP | Feature | First shipped | Status @ 3.14 |
|-----|---------|---------------|----------------|
| **703** | Free-threaded (no-GIL) build | 3.13 (experimental) | **Supported, opt-in** (per PEP 779) |
| **734** | `concurrent.interpreters` stdlib module (on PEP 684 per-interpreter GIL) | 3.14 | Final |
| **744** | Copy-and-patch JIT (tier 2) | 3.13 (experimental) | Still experimental, off by default |

These are three answers to "how do I use more than one core / go faster in Python." Free-threading removes the lock; subinterpreters give each thread its own lock + isolated heap; the JIT speeds up single-threaded execution. They compose.

## 1. Shared runtime execution model (foundation)
The eval loop is tiered: **Tier 1** = specializing adaptive interpreter (PEP 659, 3.11+) rewrites hot bytecodes in place into type-specialized forms while profiling. **Tier 2** = micro-op (uop) IR (3.13+, `-X uops`/`PYTHON_UOPS=1`). **Tier 3** = JIT machine code (PEP 744). Runtime state lives in C globals, `_PyRuntimeState`, and per-interpreter `PyInterpreterState`; each thread has a `PyThreadState`. **Immortal objects (PEP 683, 3.12)** — small ints/None/True/False/interned strings/code constants have refcounts that are never modified and are never freed; this is the enabling primitive for *both* subinterpreters (shareable immutable singletons) and free-threading (no refcount contention).

## 2. PEP 703 — Free-threaded (no-GIL) build
**Status:** 3.13 experimental; 3.14 **supported but not default** (PEP 779, "phase II"). **Internals:** biased reference counting (fast path for thread-owned objects, atomic slow path for shared); deferred reference counting (module objects/functions/descriptors/`threading.local` — cleanup deferred to GC); per-thread reference counting (heap types, code objects, module `__dict__`, merged at safe points); immortalization of code constants + `sys.intern()`ed strings (3.14); `mimalloc` replaces `pymalloc`; lock-free structures use **QSBR**; per-object locks + **`PyMutex`** (1-byte lock) keep list/dict/set ops atomic; stop-the-world GC pauses; non-GC object header 16→32 bytes (AMD64). **Cost:** ~1% single-thread overhead on macOS aarch64, up to ~8% on x86-64 Linux. **Build/detect:** `./configure --disable-gil`; `python -VV` shows "free-threading build"; `sys._is_gil_enabled()`; `sysconfig.get_config_var("Py_GIL_DISABLED")`. **Runtime GIL control:** `-X gil=0|1` / `PYTHON_GIL=0|1`. **Behavioral:** `sys.flags.thread_inherit_context` and `context_aware_warnings` default True; reading another thread's `frame.f_locals` is unsafe; sharing one iterator across threads can drop/dup elements.

## 3. C-extension free-threading compatibility
An extension that doesn't declare support **auto-re-enables the GIL at import with a warning** — silently negating no-GIL process-wide. Multi-phase init (PEP 489): add slot `{Py_mod_gil, Py_MOD_GIL_NOT_USED}`. Single-phase init (`PyModule_Create`): `#ifdef Py_GIL_DISABLED` then `PyUnstable_Module_SetGIL(module, Py_MOD_GIL_NOT_USED);`. Free-threaded wheels use the **`cp314t`** ABI tag. NumPy/Cython/pybind11/PyO3 ship FT-aware paths (track: py-free-threading.github.io/tracking/, hugovk.github.io/free-threaded-wheels/). Test with a tiny `sys.setswitchinterval(...)` and ThreadSanitizer.

## 4. PEP 734 — Multiple interpreters in the stdlib (subinterpreters)
Subinterpreters exist via C API since 1.5 (1997); **PEP 684** (3.12) gave each its own GIL by isolating runtime state into `PyInterpreterState`; **PEP 734** (3.14, final) exposes them in Python (predecessor draft: **PEP 554**; module renamed `interpreters` → **`concurrent.interpreters`**). Parallelism by isolation: N interpreters → N cores without no-GIL thread-safety hazards.
```python
from concurrent import interpreters
interp = interpreters.create()          # -> Interpreter
interp.id; interp.is_running()
interp.prepare_main(x=10)               # bind globals
interp.exec("print(x)"); interp.call(fn); t = interp.call_in_thread(fn)
interp.close()
interpreters.get_current(); interpreters.list_all()
q = interpreters.create_queue()         # put/get/put_nowait/get_nowait/empty/full/qsize
```
**Sharing:** nearly anything picklable crosses (copied via pickle); `memoryview`/buffer-protocol objects share the buffer directly. Synchronize by passing tokens through queues, not shared mutable objects. **Exceptions:** `exec()` → `ExecutionFailed` (`.type/.msg/.snapshot`); `call()` propagates directly; plus `InterpreterError`, `InterpreterNotFoundError`, `QueueEmpty`, `QueueFull`. **Pool:** `concurrent.futures.InterpreterPoolExecutor`. **Probe:** `sys.implementation.supports_isolated_interpreters`. **Caveats:** heavier startup than a thread; not all C extensions are subinterpreter-safe (process-global C state).

## 5. PEP 744 — Copy-and-patch JIT
Compiles hot **tier-2 micro-op** sequences to native code. New/experimental in 3.13, off by default through 3.14. **Technique:** at build time LLVM (Clang, needs `musttail`) compiles each micro-op into a machine-code **stencil** dumped to a header; at runtime the JIT copies each stencil almost verbatim and patches operands (tiny JIT latency). **Build/run:** `./configure --enable-experimental-jit` (values `yes|no|interpreter|yes-off`; `yes-off` = build but run interpreter mode); `PYTHON_JIT=1`. Build-time LLVM dep adds ~3–60 s; no runtime dep, no API/ABI change. **Reality (3.13/3.14):** ~on par with the specializing interpreter, **10–20% memory overhead** — a foundation, not yet a free win. Tier-1 platforms: x86-64 + aarch64 on Linux/macOS/Windows. **Non-experimental criteria (PEP 744):** ≈5% speedup on a popular platform, deployable with minimal disruption, Steering Council sign-off.

## 6. Choosing a parallelism strategy
- CPU-bound, shared mutable state, threads → **free-threading (703)** (you own the locking; FT-incompatible C ext re-enables the GIL).
- CPU-bound, little sharing, want isolation → **subinterpreters (734)** (per-interpreter GIL → multi-core; pass data via queues).
- Hard isolation / crash containment → **multiprocessing**.
- I/O-bound → **asyncio/threads** (GIL releases on I/O).
- Single-thread speed → **JIT (744)** + specializing interpreter (modest today).

## Anti-patterns
- Shipping a C extension without `Py_mod_gil`/`PyUnstable_Module_SetGIL` → silent process-wide GIL re-enable.
- Assuming no-GIL ⇒ thread-safe code: container *ops* are atomic, but multi-step invariants still need your own `threading.Lock`; cross-thread iterator sharing is unsafe.
- Reading another thread's running `frame.f_locals` on the FT build — may crash.
- Treating subinterpreters as cheap threads — use `InterpreterPoolExecutor`.
- Expecting a big JIT win today (≈parity, +10–20% memory).
- Sharing mutable objects between subinterpreters — use the queue.

## Troubleshooting
- "GIL was re-enabled at runtime" → an imported C ext lacks `Py_mod_gil`; check `sys._is_gil_enabled()`, find/fix the offender.
- Objects not freed promptly (FT) → deferred/QSBR; `gc.collect()` or tune `MIMALLOC_PURGE_DELAY=0` (perf cost).
- Subinterpreter import crash → extension keeps process-global C state.
- JIT no speedup → expected at 3.13/3.14; verify it's built (`--enable-experimental-jit`) and on (`PYTHON_JIT=1`).

## References
- PEP 703 https://peps.python.org/pep-0703/ · PEP 779 https://peps.python.org/pep-0779/
- Free-threading HOWTO https://docs.python.org/3/howto/free-threading-python.html
- C-API extension support https://docs.python.org/3/howto/free-threading-extensions.html
- Free-Threading Guide https://py-free-threading.github.io/
- PEP 734 https://peps.python.org/pep-0734/ · PEP 684 https://peps.python.org/pep-0684/ · PEP 554 https://peps.python.org/pep-0554/ · PEP 683 https://peps.python.org/pep-0683/
- Per-interpreter GIL (LWN) https://lwn.net/Articles/941090/
- PEP 744 https://peps.python.org/pep-0744/ · pydevtools JIT https://pydevtools.com/handbook/explanation/what-is-cpythons-jit-compiler/ · Following up on the JIT (LWN) https://lwn.net/Articles/1029307/
