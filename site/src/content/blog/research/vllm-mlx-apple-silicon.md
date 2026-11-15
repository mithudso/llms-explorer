---
title: "A dated vLLM and MLX comparison on Apple Silicon"
description: "A dated vLLM and MLX comparison on Apple Silicon. An edited historical research report with its original evidence limits retained."
date: "2026-11-15"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# vLLM vs mlx-lm on M5 Max, and eGPU usability (2026-10-09)

Historical single-host benchmark: **2026-10-09**. Publication review inspected saved summaries. eGPU inspection was detection only; no experiment was rerun. These results do not qualify today’s runtime or device.

Host: MacBook Pro M5 Max, 64 GB unified memory, macOS 27.2.
Models (MLX 4-bit, same weights for both runtimes):
- `mlx-community/Qwen3-4B-Instruct-2507-4bit` (dense, 2.3 GB)
- `mlx-community/Qwen3.5-9B-4bit` (hybrid, 6.0 GB)
- `mlx-community/Qwen3.6-27B-4bit` (hybrid, 16.1 GB)

Method: greedy decoding with EOS ignored, 256 new tokens, batch 1, median of 3 runs. Batch-8 runs use 8 prompts of 512 tokens. Script: `bench.py`. Raw results: `results-*.json`. vLLM ran in-process (`VLLM_ENABLE_V1_MULTIPROCESSING=0`) so that `time -l` measures the engine.

## Versions

- mlx-lm 0.32.0 / mlx 0.32.3 in `.venv-mlx` (this dir).
- vLLM 0.31.0+cpu + vllm-metal 0.31.0.dev20261009 (dev channel, MLX 0.32.1 backend) in `the separate vLLM environment`, installed by the official `install.sh` (copy in `dl/`).

## Speed

Decode tok/s (batch 1), for 128 / 1024 / 4096-token prompts:

| Model | mlx-lm | vLLM |
|---|---|---|
| Qwen3-4B   | 147 / 170 / 148 | 90 / 103 / 94 |
| Qwen3.5-9B | 100 / 99 / 97   | 97 / 93 / 93  |
| Qwen3.6-27B | 33 / 33 / 31   | 30 / 28 / 32  |

Prefill tok/s (prompt tokens ÷ time to first token), for 128 / 1024 / 4096-token prompts:

| Model | mlx-lm | vLLM |
|---|---|---|
| Qwen3-4B   | 2601 / 5579 / 4699 | 1818 / 2234 / 1850 |
| Qwen3.5-9B | 1778 / 3049 / 2834 | 2044 / 2642 / 2221 |
| Qwen3.6-27B | 603 / 899 / 753   | 646 / 579 / 647    |

Batch-8 aggregate throughput, and startup:

| Model | mlx-lm batch-8 | vLLM batch-8 | mlx-lm load | vLLM engine init |
|---|---|---|---|---|
| Qwen3-4B   | 425 tok/s | 209 tok/s | 0.8 s | 5.1 s  |
| Qwen3.5-9B | 251 tok/s | 240 tok/s | 1.2 s | 16.4 s |
| Qwen3.6-27B | 78 tok/s | 68 tok/s  | 2.6 s | 26.3 s |

## Memory

| Model | mlx-lm MLX peak | mlx-lm footprint | vLLM MLX peak | vLLM footprint | vLLM `gpu_memory_utilization` |
|---|---|---|---|---|---|
| Qwen3-4B   | 3.4 GiB  | 4.7 GB  | 9.9 GiB  | 5.5 GB  | 0.2 |
| Qwen3.5-9B | 7.6 GiB  | 9.2 GB  | 14.4 GiB | 25.7 GB | 0.4 |
| Qwen3.6-27B | 20.2 GiB | 23.1 GB | 19.9 GiB | 33.0 GB | 0.5 |

- mlx-lm grows its KV cache on demand. Its memory is roughly weights plus the working set.
- vLLM preallocates a paged KV pool sized by `gpu_memory_utilization`. The setting is a fraction of all 68.7 GB, not of free memory.
- If the setting is too low, vLLM refuses to start. Qwen3.5-9B at 0.25 failed with: `ValueError: To serve at least one request with the model's max seq len (8192), (0.31 GiB KV cache is needed, which is larger than the available KV cache memory (0.04 GiB)`. The 9B model needed about 19 GB before any KV cache. vllm-metal loads it through mlx-vlm with the vision tower and profiles an 8k-token prefill.
- Process footprint (`/usr/bin/time -l`) and MLX allocator peak disagree, because Metal-wired buffers are counted differently. Compare within one column.

## eGPU (RTX 5080): neither tested build exposed CUDA on this macOS host

Evidence: `egpu-detection.json`. This was a detection-only test. At study time a separate macuda llama-server owned the card and a fault marker was present, so this experiment did not open the device.

- **mlx-lm:** `mx.cuda.is_available()` = False. The MLX CUDA backend (`mlx-cuda-13`) ships wheels only for Linux and Windows. On macOS MLX runs on Metal (the M5 Max GPU) only.
- **vLLM:** the macOS PyTorch 2.13 build has no CUDA (`torch.backends.cuda.is_built()` = False). vLLM's CUDA platform therefore can't load. On macOS vLLM resolves to `MetalPlatform` (vllm-metal → MLX → Apple GPU) or CPU.
- The study’s macuda configuration (TinyGPU userspace CUDA) supported llama.cpp and stable-diffusion.cpp; it did not provide the PyTorch/vLLM path tested here. This is a dated configuration observation.

The original study records prior llama.cpp/macuda eGPU client timings. They were not reproduced in this detection-only experiment and are historical reference figures with GGUF Q4_K_M at 32k context, so they are a different quant and only roughly comparable:
- Qwen3-4B-Instruct-2507: about 196–205 tok/s decode.
- Qwen3.5-9B: about 117 tok/s decode.
- No 27B eGPU figure is recorded.

## Verdict

- **mlx-lm led most tested throughput cases on this host.** The 27B/4096-token decode case favored vLLM (32 versus 31 tok/s). Reported loading/initialization times were roughly 6–14× shorter for mlx-lm, though those stages need not perform identical work. The memory columns favor mlx-lm at 4B and 9B.
- **The gap shrinks as models grow.** On the 4B dense model vLLM is about 40% slower. On the 9B model vLLM decode is within about 7%; on 27B it ranges from about 15% slower to 3% faster. The runtimes use MLX-based execution, but their MLX versions differ and this experiment did not isolate the cause of the gaps. vLLM's 9B prefill was slightly faster at 128 tokens.
- **Evaluate vllm-metal separately when its serving features are required.** This throughput test does not measure API usability or continuous batching. The tested memory pool requires explicit sizing.
- **The prior eGPU timings do not establish a matched winner.** They used different quantization and context settings (4B about 200 tok/s, 9B about 117 tok/s). The study records a 16.1 GB MLX 27B artifact, a 16 GB card and a separately configured IQ2_XXS 27B server; those facts do not prove whether a different GGUF representation fits or performs on that card. No 27B eGPU timing was measured. The M5 Max’s tested 4-bit 27B decoded at about 31–33 tok/s.

## Run notes

- The in-process vLLM benchmark can crash during teardown before printing its summary. The results JSON is written first, so read the file.
- During the 9B runs other services held about 30 GB: a VM, two Ollama llama-servers and Metal-wired memory. Memory was freer for the 27B runs.
