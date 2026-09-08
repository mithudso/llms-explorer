---
title: "CPython Performance Profiling and Acceleration"
description: "> Hub reference under programming-languages. Created via /dr (2026-06-01). Sources: official Python docs (profile/pstats), project docs/GitHub (py-spy, Scalene, memray, pytest-memray, Cython), the Sca"
---

# CPython Performance Profiling and Acceleration

> Hub reference under `programming-languages`. Created via `/dr` (2026-06-01). Sources: official Python docs (profile/pstats), project docs/GitHub (py-spy, Scalene, memray, pytest-memray, Cython), the Scalene arXiv paper, pyperf docs.

Performance work in Python is two phases, in this order: **measure** (profile and benchmark to find the real bottleneck) then **accelerate** (fix it, native last). The most-violated rule is to optimize before profiling; the second is to trust measurements that the profiler's own overhead has distorted. Pick the tool by the *question* you are asking.

## Pick the profiler by the question

| Question | Tool | Why |
| --- | --- | --- |
| "Which functions/call-paths cost the most?" | **cProfile + pstats** | Built-in, deterministic call graph, exact ncalls/tottime/cumtime. |
| "What is a *running/production* process doing?" | **py-spy** (or Austin) | Samples another process's memory; no code changes, negligible overhead. |
| "Is this hotspot Python, native, or I/O — and which line?" | **Scalene** | Line-level; separates Python vs native vs system vs GPU time. |
| "What is allocating memory (incl. C extensions)?" | **memray** | Tracks every allocation, Python + native + interpreter. |
| "Which line of this hot function is slow?" | **line_profiler / kernprof** | Per-line CPU timing inside `@profile` functions. |
| "Is A faster than B, reliably?" | **pyperf / timeit / pytest-benchmark** | Statistically rigorous benchmarks. |

## 1. Deterministic profiling — cProfile / profile / pstats
Monitors **every** call/return/exception with precise timing. Use the C-extension `cProfile` (low overhead); `profile` is the pure-Python, hookable, much slower twin (used for calibration).

```bash
python -m cProfile -o out.prof -s cumtime script.py
```
```python
import cProfile, pstats
from pstats import SortKey
with cProfile.Profile() as pr:        # context manager (3.8+)
    run_workload()
pstats.Stats(pr).strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats(15)
```
Columns: **ncalls** (call count); **tottime** (in-function, excludes subcalls — sort to find hot loops); **cumtime** (cumulative incl. subcalls — find expensive chains); two **percall**. SortKey enum (3.7+): CALLS, CUMULATIVE, FILENAME, LINE, NAME, NFL, PCALLS, STDNAME, TIME. Stats: `add()` (merge), `print_callers/callees()`, `get_stats_profile()` (3.9+). Calibration: `bias = profile.Profile().calibrate(10000)`. Visualize with **snakeviz** / **gprof2dot** / tuna. Tradeoff: per-call overhead distorts many-tiny-call workloads — use sampling for production.

## 2. Statistical / sampling profilers — py-spy, Austin
**py-spy** (Rust, benfred; rbspy lineage) profiles a process you can't/won't instrument, including production. Separate process reading target memory (process_vm_readv / vm_read / ReadProcessMemory) — zero code changes, very low overhead.
```bash
py-spy record -o profile.svg --pid 12345
py-spy record -o p.json --format speedscope -- python prog.py
py-spy top --pid 12345
py-spy dump --pid 12345        # all thread stacks (find a hang)
```
Flags: `--rate`, `--duration`, **`--native`** (C/C++/Cython frames), **`--gil`** (only GIL-holding threads), `--subprocesses`, `--idle`, `--nonblocking`. Output: flamegraph SVG (default), speedscope, raw. Permissions: spawning is unprivileged; **attaching** needs sudo/ptrace on Linux (ptrace_scope), root on macOS, SYS_PTRACE in Docker/K8s. **Austin** is a sibling C frame-stack sampler for the same flamegraph/speedscope pipeline.

## 3. Scalene — line-level CPU+GPU+memory, native separation
plasma-umass profiler that **separates Python vs native (C/C++) vs system (I/O) time** plus GPU + memory at per-line granularity — instantly answers "is this even optimizable in Python?" (mostly *system* time = I/O-bound; mostly *native* = inside a C library).
```bash
scalene run prog.py            # → scalene-profile.json
scalene view --html            # or --cli/--standalone/--json
```
Flags: `--cpu-only`/`--gpu`/`--memory`, `--reduced-profile`, `--profile-only/-exclude`, thresholds. Target with `@profile` or `scalene_profiler.start()/stop()`. **Copy volume (MB/s)** flags costly silent C↔Python / CPU↔GPU copies. Low overhead via sampling + signal handlers + native stack stitching (~10–20%). AI suggestions (⚡/💥) via Bedrock/Azure/OpenAI/Ollama; experimental `--memory-leak-detector`.

## 4. memray — allocation-level memory profiling (Bloomberg)
Tracks allocations in **Python, native extensions, and the interpreter** by intercepting allocators. **Linux/macOS only (no Windows).**
```bash
memray run [--native] [--follow-fork] [--trace-python-allocators] script.py   # → capture.bin
memray run --live script.py
memray flamegraph capture.bin     # default reporter (also: table, tree, summary, stats)
memray flamegraph --leaks capture.bin      # allocations never freed
memray flamegraph --temporal capture.bin   # over-time
```
`--native` adds C/C++ frames (essential for numpy/pandas). **pytest-memray:** `--memray` + `@pytest.mark.limit_memory("100 MB")`. Default = high-watermark (peak); `--leaks`/`--temporal` switch modes.

## 5. line_profiler / kernprof — per-line CPU
```bash
kernprof -l -v script.py        # @profile-decorated functions; → script.py.lprof
```
Reports Hits / Time / Per Hit / % Time per source line. **py-heat** = heatmap. Real overhead — scope to the one function under investigation.

## 6. Benchmarking — measure the fix, not the noise
- **timeit** — micro-snippets (`python -m timeit "..."`); weak isolation.
- **pyperf** (PSF) — rigorous: multi-process, warmup (skips first value), mean±stdev, keeps GC, `pyperf system tune` to suppress outliers. Use for any "A vs B" claim that matters.
- **pytest-benchmark** — benchmarks in the test suite, regression tracking; pair with CI perf budgets.

## 7. Flame-graph interpretation
- **Width = cost** (time, or bytes for memray). X-axis is **not** time order in a classic flame graph — it's grouped/sorted stacks.
- **Self time** (frame's own bar minus children) vs **cumulative** (whole stack width). Wide frame + narrow children = work is here; wide children = cost is below.
- **speedscope** views: Time Order, Left Heavy (best for biggest contributors), Sandwich. py-spy `--gil` shows real on-CPU Python.

## 8. The native-acceleration ladder (native is the LAST resort)
1. **Algorithm / data structure** — biggest wins (O(n²)→O(n log n), set/dict membership, generators).
2. **Builtins / vectorization** — push loops into C (comprehensions, str.join, itertools, **NumPy** vectorized ops).
3. **Concurrency** — asyncio/threads for I/O; processes (or free-threaded 3.13t+) for CPU-bound.
4. **Native compilation** of the proven hotspot:

| Tool | Model | Best for | Caveat |
| --- | --- | --- | --- |
| **Numba** `@njit` | LLVM JIT at runtime, infers types | Numerical/NumPy loops, `prange`, `@vectorize` | First-call compile cost. |
| **Cython** | Python superset → C; `cdef`, typed memoryviews, `nogil`, `prange()` (OpenMP) | CPU-bound numeric code shipped as a compiled wheel | Build step; needs types to be fast; parallel blocks must be nogil. |
| **mypyc** | Type-annotated Python → C extension | Codebases already type-hinted (mypy/black) | Gains scale with annotation coverage. |
| **PyO3/Rust** (+maturin) | Rust → native module | New high-perf code, memory safety, GIL release | Rust + bindings learning curve. |
| **ctypes/cffi** | Call existing C lib | Wrapping a pre-built native lib | No speedup unless most time is in the C. |

Cython: use **typed memoryviews** (`double[:, ::1]`) for fast array access (unlocks nogil); `prange(..., nogil=True)` for OpenMP; run **`cython -a`** and drive yellow (Python-object) lines white. Pure-Python mode keeps source runnable as plain `.py`.

## Anti-patterns and gotchas
- **Optimizing before profiling** — intuition about Python hotspots is usually wrong.
- **Trusting overhead-distorted numbers** — cProfile inflates many-small-call code; line_profiler inflates the line under test. Cross-check with py-spy/Scalene before a rewrite.
- **Optimizing the wrong layer** — system-time (I/O) or native-time (C library) lines won't get faster from Python changes; Scalene's split catches this.
- **Micro-benchmarking without warmup/isolation** — use pyperf for decisions.
- **Reaching for native too early** — exhaust algorithm/vectorization/concurrency first.
- **Wall-clock vs CPU time** — a sleep/network-bound function isn't a JIT candidate.
- **Forgetting `--native`** — hides the C-extension frames where cost often lives (numpy/pandas/torch).
- **memray on Windows** — unsupported; use py-spy or tracemalloc there.

## References (2026-06-01)
- Python docs — Profilers: https://docs.python.org/3/library/profile.html • pstats: https://docs.python.org/3/library/pstats.html
- py-spy: https://github.com/benfred/py-spy
- Scalene: https://github.com/plasma-umass/scalene • arXiv: https://arxiv.org/pdf/2212.07597
- memray: https://github.com/bloomberg/memray • https://bloomberg.github.io/memray/ • pytest-memray: https://github.com/bloomberg/pytest-memray
- Cython parallelism: https://cython.readthedocs.io/en/latest/src/userguide/parallelism.html • memoryviews: https://docs.cython.org/en/latest/src/userguide/memoryviews.html
- pyperf: https://pyperf.readthedocs.io/
- Cython/Numba/PyO3 comparison (Witt): https://wittgeo.medium.com/boost-python-performance-with-cython-numba-and-pyo3-486d59d8c2c6
