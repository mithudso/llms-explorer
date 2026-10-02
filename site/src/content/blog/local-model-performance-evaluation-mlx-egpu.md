---
title: "Local Model Performance: An Unverified Reported MLX, RTX 5080 eGPU and Ollama Comparison"
description: "An unverified MLX, RTX 5080 eGPU and Ollama comparison with withdrawn conclusions, preserved transcripts, and documented benchmark-script limits."
date: "2026-09-30"
order: 31
noindex: true
evidenceStatus: "unverified"
evidenceNote: "The comparative throughput ranges lack matching public run artifacts. The included Qwen2-beta-14B transcript does not validate those comparisons. The comparative conclusions and deployment recommendations are withdrawn pending matching artifacts. Do not treat them as measurements for hardware purchase decisions."
tags: ["local-llm", "mlx", "ollama", "rtx-5080", "benchmarking", "apple-silicon", "gemma-4", "qwen-3.6"]
---

> **Evidence notice — unverified comparison.** Matching public run artifacts have not been identified for the comparative throughput ranges below. The included Qwen2-beta-14B transcript records 8.45–8.62 tokens/sec for a different model; it does not validate the Gemma 4, Qwen 3.6, Apple M5 Max or RTX 5080 comparisons. The original figures and recommendations remain here for review and history. Do not treat them as measured performance evidence for hardware purchase decisions.

> **Correction — 2026-09-30.** This correction withdraws the unsupported comparative performance conclusions and deployment recommendations pending matching public run artifacts. The original figures and prior guidance remain below for traceability. They are not current instructions or evidence for a hardware purchase. This correction does not establish that the reported figures are false; it establishes that the comparisons have not been validated.

Serving large language models locally on consumer and workstation hardware has bifurcated into two distinct execution regimes:

1. **Unified memory:** CPU and GPU share a memory pool. M5 Max configurations differ: [Apple lists](https://www.apple.com/macbook-pro/specs/) 460 GB/s for the 32-core GPU and 614 GB/s for the 40-core GPU. The original ~400-GB/s assumption is retained in the historical calculations below, not as a current specification.
2. **Discrete memory:** [NVIDIA lists 16 GB of GDDR7](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/) for the RTX 5080. Device-memory bandwidth differs from host-to-device bandwidth. Intel specifies 64-Gbps PCIe support for Thunderbolt 5; the original 7.0-GB/s payload assumption is not a measured rate for the host, enclosure, and workload in this article.

Understanding when to run a model on Apple Silicon's unified memory via **MLX** versus offloading to a dedicated **eGPU GDDR7 pool** via native CUDA/Tinygrad or running general-purpose **Ollama GGUF** runtimes requires rigorous performance evaluation.

This post preserves reported comparisons from deep research (`/dr`), Concept Family Explorer (`cfe`), and Rabbithole analysis covering model sizing, memory residency, prompt ingestion latency (TTFT), and auto-regressive generation throughput (TPS). The evidence notice above applies to the comparisons and recommendations below.

---

## 1. The Core Bottleneck: The Memory Bandwidth Ceiling

During auto-regressive decoding, a language model evaluates tokens sequentially. A rough bandwidth estimate for batch-one dense-model decoding assumes that weight reads dominate and approximates the bytes read per generated token by the resident weight footprint:

$$\text{Theoretical Peak TPS} = \frac{\text{Memory Bandwidth (GB/s)}}{\text{Model Weight Footprint (GB)}}$$

This is an idealized estimate under those assumptions, not a physical invariant or measured throughput. MoE activation, batching, quantization kernels, cache reuse, KV traffic, compute limits, and runtime overhead change the bytes and work per token. The preserved table contains original estimates whose derivations and run artifacts are missing.

```
+-----------------------------------------------------------------------------------+
|                        LOCAL INFERENCE HARDWARE REGIMES                           |
+-----------------------------------------------------------------------------------+
| Architecture       | Usable Memory | Bandwidth  | Max Model Size | Peak 14B Dec TPS   |
+--------------------+---------------+------------+----------------+--------------------+
| Apple M5 Max       | 64 GB Unified | ~400 GB/s  | ~48 GB (70B Q4)| ~43 tokens/sec     |
| RTX 5080 eGPU      | 16 GB GDDR7   | ~1000 GB/s | ~12 GB (14B Q4)| ~88 tokens/sec     |
| Thunderbolt 5 Bus  | Dynamic Host  | ~7.0 GB/s  | Layer Streamed | < 0.5 tokens/sec   |
+--------------------+---------------+------------+----------------+--------------------+
```

### Why Bus Streaming Across Thunderbolt 5 Fails
The original example assumes that all 21.9 GB cross the link for every generated token and that payload throughput is 7.0 GB/s. Under exactly those assumptions, the arithmetic is:

$$\text{Streaming TPS} = \frac{7.0 \text{ GB/s}}{21.9 \text{ GB}} \approx 0.32 \text{ tokens/sec}$$

The denominator should be bytes actually transferred per generation step, not automatically the full model size. CPU execution of offloaded layers and streaming layers over a link are different strategies. Full residency reduces transfer pressure, but this example does not prove that every partial-offload configuration is impractical. Measure the actual transfer pattern and latency.

---

## 2. In-Depth Model Profiling

The following footprints, aliases, KV-cache sizes, and throughput ranges are retained original claims. No matched model revision, quantization metadata, context/batch configuration, or public run artifacts were identified. Adding weights and a quoted KV estimate does not include every runtime allocation; subtracting that sum from physical capacity does not establish free memory or safe headroom. NVFP4 and generic 4-bit quantization are not interchangeable artifact specifications.

### 2.1 Qwen 3.6 35B (`qwen3.6:35b-mlx`) on Apple Silicon Unified Memory
- **Weight Footprint (NVFP4 / 4-bit)**: ~21.9 GB
- **KV Cache Allocation**:
  - At 8,192 context: ~1.1 GB (16-bit)
  - At 32,768 context: ~4.5 GB (16-bit)
  - At 65,536 context: ~9.0 GB (16-bit)
- **Quoted weights-plus-KV subtotal**: 23.0 GB, 26.4 GB, or 30.9 GB at the three listed contexts; runtime overhead is not included.
- **Residency Feasibility**:
  - **Apple M5 Max 64 GB**: **Fits with high headroom**. Leaves ~33 GB for macOS system memory and application workspaces.
  - **RTX 5080 16 GB**: **Physically impossible**. Model weights alone exceed total VRAM by 5.9 GB.
- **Throughput on M5 Max**:
  - Theoretical limit: $\frac{400 \text{ GB/s}}{21.9 \text{ GB}} = 18.26 \text{ tokens/sec}$
  - Unverified reported generation: **15.5 – 17.2 tokens/sec**. Dividing this range by the assumed estimate is not a measurement of memory-bus saturation.

### 2.2 Gemma 4 12B (`gemma4:12b-mlx` / GGUF) Cross-Platform Comparison
- **Weight Footprint (4-bit)**: ~7.8 GB
- **KV Cache Allocation (32k context)**: ~2.4 GB
- **Total Working Footprint**: ~10.2 GB
- **Residency Feasibility**:
  - **Apple M5 Max 64 GB**: Fits easily (leaves 53.8 GB free).
  - **RTX 5080 16 GB GDDR7**: **Optimal residency**. Occupies ~10.2 GB total, leaving 5.8 GB safety buffer.
- **Unverified throughput comparison**:
  - **RTX 5080 eGPU GDDR7 (~1000 GB/s)**: **85 – 92 tokens/sec**
  - **Apple M5 Max Unified Memory (~400 GB/s)**: **42 – 45 tokens/sec**
  - **Ollama Metal (llama.cpp dispatch)**: **36 – 39 tokens/sec**

**Prior unvalidated conclusion — withdrawn on 2026-09-30:**

> The RTX 5080 delivers **more than 2x the decoding speed** of Apple Silicon when models fit within its 16 GB envelope.

The retained ranges do not support that conclusion without matching public run artifacts. This article does not recommend a hardware choice on that basis.

---

## 3. Runtime Engine Comparison: MLX vs Ollama vs Tinygrad

The ASCII table preserves the original taxonomy. Its overhead percentages, optimal model-size ranges, and Tinygrad PTX/NVFP4 row have no retained versioned measurement or configuration receipt; they should not be used as runtime-selection facts.

```
+----------------------------------------------------------------------------------------+
|                                RUNTIME ENGINE TAXONOMY                                 |
+--------------------+---------------------+---------------------+-----------------------+
| Feature            | Apple MLX           | Ollama (llama.cpp)  | Tinygrad (eGPU NV)    |
+--------------------+---------------------+---------------------+-----------------------+
| Memory Model       | Zero-Copy Unified   | mmap GGUF Buffers   | Dedicated GDDR7 VRAM  |
| Execution Pipeline | Lazy Graph (mx.eval)| Static C++ Engine   | JIT Kernel Fusion     |
| Attention Kernels  | Native Metal SDPA   | ggml-metal.metal    | Custom PTX / NVFP4    |
| Overhead           | Minimum (~2% driver)| Intermediate (10%)  | Pure CUDA / C-driver  |
| Optimal Model Size | 14B – 70B           | 7B – 35B            | 1B – 14B              |
+--------------------+---------------------+---------------------+-----------------------+
```

### 1. Apple MLX
[MLX](https://ml-explore.github.io/mlx/build/html/index.html) uses shared CPU/GPU memory on Apple Silicon and lazy evaluation. Sharing array storage can avoid explicit CPU-to-GPU buffer copies; it does not eliminate all file I/O, conversion, temporary allocations, or synchronization. Fusion depends on the operations and compilation path.

### 2. Ollama / llama.cpp
Ollama packages models as GGUF files. GGUF maps tensors from disk into virtual address space via `mmap()`. On macOS, llama.cpp offloads tensor operations to Metal via `ggml-metal`. The cause of latency spikes needs profiling in the selected backend. Setting `num_ctx` chooses a context size; it does not, by itself, prove that all dynamic allocation or stalls have been removed.

### 3. Tinygrad eGPU Accelerator
[Tinygrad documents multiple runtimes](https://docs.tinygrad.org/runtime/), including an NV backend. The selected renderer, supported model kernels, quantization, allocation, and residency require version-specific confirmation. Using a discrete GPU does not eliminate host scheduling, launches, or synchronization; this article supplies no matched Tinygrad RTX 5080 run.

---

## 4. The Evaluation Metrics Framework

A useful evaluation separates latency, throughput, timing variation, and memory pressure. These measurements can interact:

1. **Time to First Token (TTFT)**:
   - Measure client request dispatch to receipt of the first generated token on a streaming response. It can include queueing, model load, prompt evaluation, first-token decoding, and transport.
   - Report server prompt-evaluation time separately; neither metric is universally compute-bound.
2. **Tokens Per Second (TPS)**:
   - Define the denominator and whether the first token, load, and prompt evaluation are included. Server generation rate and client end-to-end rate answer different questions.
   - A bandwidth estimate is a hypothesis; measure the selected model and runtime.
3. **Inter-Token Latency Variance (Jitter)**:
   - Measures stutter between sequential tokens.
   - Caused by dynamic KV cache expansion, garbage collection pauses, or memory page compaction.
4. **Memory pressure and residency**:
   - Track process memory, system pressure, swap activity, and GPU/runtime allocations separately. RSS and wired-memory totals alone do not prove that model buffers are resident or that paging cannot occur.

---

## 5. Benchmarking with the Harness Tools

The downloadable scripts are inspection aids with limitations. The commands below are preserved historical examples, not a verified reproduction of the cross-platform comparison. Record model artifact hashes, runtime commit/version, hardware and link state, quantization, context, prompt, output length, cache/load state, and repeated-run dispersion before comparing results.

### 1. Running the Benchmark Suite
The September 30 source at `/downloads/benchmarks/benchmark_suite.py` sends non-streaming requests to Ollama's `/api/generate`. Its `ttft_sec` adds server load and prompt-evaluation durations; it does not observe first-token arrival or inter-token jitter. It reports server generation rate and client wall time. Missing timing fields default to zero and can trigger an elapsed-time fallback, so validate the raw response fields before interpreting rates. The retained transcript's `TTFT` label is therefore misleading:

```console
$ python3 scripts/benchmark_suite.py --host http://127.0.0.1:11440 --model "Qwen2-beta-14B-Chat" --runs 3
================================================================
LOCAL MODEL INFERENCE BENCHMARK: Qwen2-beta-14B-Chat
================================================================
Run 1:
  Load Duration:     0.01s
  TTFT (Prompt Eval):0.01s (29 tokens @ 0.0 tps)
  Generation:        8.45 tps (184 tokens in 21.77s)
  Total Wall Clock:  21.78s
----------------------------------------------------------------
Run 2:
  Load Duration:     0.01s
  TTFT (Prompt Eval):0.01s (29 tokens @ 0.0 tps)
  Generation:        8.62 tps (184 tokens in 21.34s)
  Total Wall Clock:  21.35s
----------------------------------------------------------------
```

### 2. Profiling Memory Residency
The September 30 `memory_profiler.py` reads `vm_stat` system counters and `system_profiler` hardware descriptions. It does not sample process RSS or discrete-GPU allocations. It multiplies page counts by a hard-coded 4096 instead of parsing the page size reported by `vm_stat`; on a different page size, the computed GB values are wrong. The JSON below is retained output, not a verified residency measurement:

```console
$ python3 scripts/memory_profiler.py
{
  "hardware": {
    "Chip": "Apple M5 Max",
    "Total Number of Cores": "40",
    "Memory": "64 GB",
    "Chipset Model": "Apple M5 Max"
  },
  "memory_gb": {
    "wired": 7.1,
    "active": 0.74,
    "inactive": 0.72,
    "free": 0.03
  }
}
```

---

## 6. Downloadable Assets

The benchmark scripts created during this evaluation are available for download:

- **[benchmark_suite.py](/downloads/benchmarks/benchmark_suite.py)**: Ollama `/api/generate` harness reporting server timing fields and client wall time. Its current non-streaming implementation does not measure actual TTFT or support an OpenAI-compatible request adapter.
- **[memory_profiler.py](/downloads/benchmarks/memory_profiler.py)**: System counter and hardware-description script with a hard-coded page-size limitation; it does not measure model or GPU residency.
- **[local-model-performance-evaluation Skill](https://github.com/mithudso/skills/tree/main/local-model-performance-evaluation)**: Complete installed Claude Code / Antigravity agent skill in the skills repository.

---

## 7. Prior Unvalidated Guidance — Withdrawn

**Status: withdrawn on 2026-09-30, pending matching public run artifacts.** The following block records the original recommendations. They are preserved as prior unvalidated guidance, not current deployment instructions. Do not use these recommendations to choose hardware or a model runtime.

> 1. **For Models $\le$ 14B Parameters (e.g. Gemma 4 12B, Qwen 2.5 14B)**:
>    - **Deploy on RTX 5080 eGPU GDDR7**.
>    - Yields **85–92 tokens/sec**, more than double Apple Silicon M5 Max speed.
> 2. **For Models 27B – 70B Parameters (e.g. Qwen 3.6 35B, Llama 3.3 70B Q4)**:
>    - **Deploy on Apple Silicon Unified Memory via MLX**.
>    - 64 GB–128 GB unified memory provides the only viable local residency without multi-GPU clusters.
> 3. **Avoid Dynamic Bus Streaming**:
>    - Never attempt layer-by-layer offloading across Thunderbolt 5; latency degrades by 50x–100x. Ensure 100% layer residency inside either host RAM or discrete VRAM.
