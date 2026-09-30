---
title: "Local Model Performance: An Unverified Reported MLX, RTX 5080 eGPU and Ollama Comparison"
description: "An unverified reported comparison of MLX, RTX 5080 eGPU and Ollama performance, retained for review. Matching public run artifacts have not been identified for its comparative throughput ranges; the included Qwen2-beta-14B transcript does not validate them."
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

1. **Large Unified Memory Pools (Apple Silicon M-Series)**: High capacity (64 GB–128 GB) with moderate shared memory bandwidth (~400 GB/s on M5 Max).
2. **High-Bandwidth Discrete Accelerators (RTX 5080 eGPU)**: Ultra-high memory bandwidth (~1000 GB/s GDDR7), bounded by a rigid physical capacity ceiling (16 GB VRAM) and an external PCIe transport bus (~7.0 GB/s over Thunderbolt 5).

Understanding when to run a model on Apple Silicon's unified memory via **MLX** versus offloading to a dedicated **eGPU GDDR7 pool** via native CUDA/Tinygrad or running general-purpose **Ollama GGUF** runtimes requires rigorous performance evaluation.

This post preserves reported comparisons from deep research (`/dr`), Concept Family Explorer (`cfe`), and Rabbithole analysis covering model sizing, memory residency, prompt ingestion latency (TTFT), and auto-regressive generation throughput (TPS). The evidence notice above applies to the comparisons and recommendations below.

---

## 1. The Core Bottleneck: The Memory Bandwidth Ceiling

During auto-regressive decoding, a language model evaluates tokens sequentially. For each generated token, the inference engine must stream every parameter weight from memory into the arithmetic compute units:

$$\text{Theoretical Peak TPS} = \frac{\text{Memory Bandwidth (GB/s)}}{\text{Model Weight Footprint (GB)}}$$

This simple physical invariant dictates the performance ceiling across local hardware architectures.

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
Attempting to run a 35B parameter model (e.g. `qwen3.6:35b-mlx` at ~22 GB) by streaming weights layer-by-layer across the Thunderbolt 5 interconnect results in catastrophic performance collapse:

$$\text{Streaming TPS} = \frac{7.0 \text{ GB/s}}{21.9 \text{ GB}} \approx 0.32 \text{ tokens/sec}$$

**Key Architectural Rule**: Weights must reside entirely inside the local device memory pool. Partial layer streaming across an external PCIe/Thunderbolt bus is impractical for interactive auto-regressive generation.

---

## 2. In-Depth Model Profiling

### 2.1 Qwen 3.6 35B (`qwen3.6:35b-mlx`) on Apple Silicon Unified Memory
- **Weight Footprint (NVFP4 / 4-bit)**: ~21.9 GB
- **KV Cache Allocation**:
  - At 8,192 context: ~1.1 GB (16-bit)
  - At 32,768 context: ~4.5 GB (16-bit)
  - At 65,536 context: ~9.0 GB (16-bit)
- **Total Working Footprint**: 26.4 GB to 30.9 GB
- **Residency Feasibility**:
  - **Apple M5 Max 64 GB**: **Fits with high headroom**. Leaves ~33 GB for macOS system memory and application workspaces.
  - **RTX 5080 16 GB**: **Physically impossible**. Model weights alone exceed total VRAM by 5.9 GB.
- **Throughput on M5 Max**:
  - Theoretical limit: $\frac{400 \text{ GB/s}}{21.9 \text{ GB}} = 18.26 \text{ tokens/sec}$
  - Unverified reported generation: **15.5 – 17.2 tokens/sec** (~90% bus saturation).

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
MLX avoids all memory copying. Memory allocated by Python arrays maps directly to Metal GPU execution buffers. Lazy evaluation chains operations into fused Metal compute shaders.

### 2. Ollama / llama.cpp
Ollama packages models as GGUF files. GGUF maps tensors from disk into virtual address space via `mmap()`. On macOS, llama.cpp offloads tensor operations to Metal via `ggml-metal`. Dynamic context reallocation can introduce intermittent latency spikes if context length is not pre-allocated via `num_ctx`.

### 3. Tinygrad eGPU Accelerator
Tinygrad compiles model computation graphs into direct NVIDIA GPU assembly (PTX) or raw driver command streams. When paired with the RTX 5080 over Thunderbolt 5, it executes fully resident in GDDR7, avoiding host operating system scheduling noise.

---

## 4. The Evaluation Metrics Framework

Comprehensive local LLM evaluation requires measuring four orthogonal dimensions:

1. **Time to First Token (TTFT)**:
   - Measures prompt evaluation latency.
   - Compute-bound: determined by parallel FLOPs on tensor cores during prompt matrix multiplication.
2. **Tokens Per Second (TPS)**:
   - Measures sequential auto-regressive generation throughput.
   - Memory bandwidth-bound: determined by memory bus throughput divided by model parameter size.
3. **Inter-Token Latency Variance (Jitter)**:
   - Measures stutter between sequential tokens.
   - Caused by dynamic KV cache expansion, garbage collection pauses, or memory page compaction.
4. **Wired Memory Saturation**:
   - Tracking resident set size (RSS) and macOS wired memory to prevent kernel swapping.

---

## 5. Benchmarking with the Harness Tools

We have packaged automated benchmarking and memory profiling scripts for reproducible evaluations:

### 1. Running the Benchmark Suite
The benchmark suite measures TTFT, prompt evaluation speed, token generation throughput, and total wall-clock duration:

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
The memory profiler instruments system unified memory, wired pages, and discrete GPU residency:

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

- **[benchmark_suite.py](/downloads/benchmarks/benchmark_suite.py)**: End-to-end benchmark harness measuring TTFT, TPS, prompt evaluation latency, and generation speed across Ollama and OpenAI-compatible endpoints.
- **[memory_profiler.py](/downloads/benchmarks/memory_profiler.py)**: Hardware profiler querying Apple Silicon unified memory states, wired pages, and GPU residency.
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
