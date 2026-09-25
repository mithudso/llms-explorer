---
title: "Blackwell sm_120 local-LLM inference stack on Linux: llama.cpp, Ollama, PyTorch and vLLM over a Thunderbolt eGPU"
description: "Building and choosing the local-LLM inference stack for a consumer Blackwell GPU (sm_120, RTX 5080 16 GB) on Linux — the llama.cpp CUDA build matrix, Ollama's bundled CUDA backends and GPU discovery,"
---

# Blackwell sm_120 local-LLM inference stack on Linux: llama.cpp, Ollama, PyTorch and vLLM over a Thunderbolt eGPU

Building and choosing the local-LLM inference stack for a consumer Blackwell GPU (sm_120, RTX 5080 16 GB) on Linux — the llama.cpp CUDA build matrix, Ollama's bundled CUDA backends and GPU discovery, the PyTorch wheel and vLLM status, and what a ~3 GB/s Thunderbolt tunnel costs in load time and offload traffic and how to keep everything resident in 16 GB.

---
name: blackwell-sm120-llm-inference-stack-linux
title: Local-LLM inference stack for consumer Blackwell (sm_120, RTX 5080 16 GB) on Linux
description: Build/choose the CUDA inference stack for an RTX 5080 (sm_120) on Linux, incl. a ~3 GB/s Thunderbolt eGPU. TRIGGER — llama.cpp CUDA build for sm_120 (CMAKE_CUDA_ARCHITECTURES=120 vs 120a-real, GGML_NATIVE, MXFP4 ptxas errors, cudart bundles, 12.8 vs 13.4 tarballs); Ollama cuda_v12/cuda_v13 runners, GPU discovery, OLLAMA_FLASH_ATTENTION / OLLAMA_KV_CACHE_TYPE / num_gpu; PyTorch cu126-cu132 wheels and driver floors; vLLM / TensorRT-LLM / ExLlamaV3 / bitsandbytes on SM120; TB tunnel cost (load time, MoE expert offload, multi-GPU); keeping a model resident in 16 GB. SKIP — driver branches, DKMS, nvidia module params (sibling reference); Mac eGPU; KV-cache theory → kv-cache-optimization.
verified-as-of: 2026-09-24
---

# Local-LLM inference stack for consumer Blackwell (sm_120) on Linux

**Verified-as-of 2026-09-24.** Target box: RTX 5080 16 GB in a Thunderbolt-5-capable enclosure (Razer Core X V2) on a Thunderbolt 4 host, an Intel NUC 15 Pro, Ubuntu 26.04.1, kernel 7.0.0-34, NVIDIA driver 610.57.04-open (KMD 610 / CUDA UMD 13.3), Ollama already serving via its bundled llama-server, apt CUDA libs 12.4 (apt `nvcc` is too old for sm_120). Driver branches / DKMS / module parameters are covered by the sibling reference and are not repeated here.

Tagging: `[SOURCED url]` = read from the cited page; `[INFERRED]` = derived from sourced facts plus arithmetic or well-known engine behaviour; nothing else is asserted. No version or flag below is invented.

---

## Core Concepts

### 1. `sm_120` vs `sm_120a` vs `sm_120f` — why "120" alone breaks a native llama.cpp build
- Consumer Blackwell (RTX 50xx) is compute capability 12.0. CUDA 12.8 was the first toolkit that knows `sm_120` (`compute_120`); older `nvcc` (e.g. Ubuntu's apt 12.4) fails with `Unsupported gpu architecture 'compute_120'`. [SOURCED https://github.com/ggml-org/llama.cpp/issues/20195] [SOURCED https://github.com/ggml-org/llama.cpp/issues/22696]
- The `a` suffix (`120a`) selects architecture-specific features that are **not forward-compatible**; the `f` suffix (`120f`) is the "family" variant that is forward-compatible within Blackwell. The MXFP4 tensor-core instructions (`mma … .kind::mxf4`, `.block_scale`, `.scale_vec::2X`) exist only on `120a`/`120f`, not on plain `sm_120`. Building plain `120` after MXFP4 landed yields hundreds of `ptxas … Feature '.kind::mxf4' not supported on .target 'sm_120'` errors. [SOURCED https://github.com/ggml-org/llama.cpp/issues/19662] [SOURCED https://github.com/ggml-org/llama.cpp/pull/17906]
- llama.cpp's `ggml/src/ggml-cuda/CMakeLists.txt` therefore rewrites any `12X[-real|-virtual]` entry to `12Xa…` (`"Replacing 120-real in CMAKE_CUDA_ARCHITECTURES_NATIVE with 120a-real"`) and, for non-native builds with toolkit ≥ 12.8, appends `120a-real` (and `121a-real` at ≥ 12.9). The comment notes `120f-virtual` would work but needs CMake ≥ 3.31.8 (<4.0) or ≥ 4.0.2 because of a CMake regex bug. [SOURCED https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-cuda/CMakeLists.txt]
- Consequence: a `GGML_NATIVE=ON` build on the RTX 5080 produces `120a-real` SASS only — no PTX — so it cannot run on a future (Rubin) GPU, and it cannot be JIT-ed by a driver. [SOURCED issue 19662 comments by llama.cpp maintainers]

### 2. Toolkit ↔ driver floors and CUDA minor-version compatibility
| CUDA toolkit | Minimum Linux driver | Source |
|---|---|---|
| 12.4 GA | ≥ 550.54.14 | [SOURCED https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html] |
| 12.8 GA | ≥ 570.26 | same |
| 12.9 GA | ≥ 575.51.03 | same |
| 13.0 | R580 (≥ 580.65.06) | same + [SOURCED https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html] |
| 13.1 | R590 | same |
| 13.2 | R595 | same |
| 13.3 | R610 | same |
| 13.4 (current, 13.4 Update 1) | R615 | same |

- Minor-version compatibility: any CUDA 13.x-built application runs on driver ≥ 580; CUDA 12.x-built applications run on ≥ 525 (newer drivers are backward compatible). The exception: "Applications that compile device code to PTX will not work on older drivers" — a PTX-only binary must be JIT-compiled by a driver that understands that PTX ISA. [SOURCED https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html]
- On this box (driver 610 = R610 = CUDA 13.3 branch): a **CUDA 12.8-built** llama.cpp/Ollama runner runs unconditionally; a **CUDA 13.0–13.3-built** one runs unconditionally; a **CUDA 13.4-built** binary with SASS for `120a-real` runs under minor-version compatibility, but anything in that binary that is *PTX-only for a 13.4-era ISA* would need R615. `[INFERRED]` from the two rows above.
- NVIDIA no longer bundles the driver with the toolkit on Linux from CUDA 13.4 onward. [SOURCED CUDA 13.4 release notes]

### 3. Real vs virtual architectures decide first-load latency and driver dependence
- `XX-real` = SASS (native GPU machine code) for that exact GPU; `XX-virtual` = PTX (portable intermediate ISA), JIT-compiled to SASS by the driver on first run; no suffix = both. [SOURCED llama.cpp ggml-cuda CMakeLists comment]
- Ollama's **cuda_v12** runner (built with CUDA 12.8) is compiled for `50-virtual;52-virtual;60;61;70;75;80;86;89;90;90a;100;120` (Linux) — `120` = SASS + PTX. Its **cuda_v13** runner (built with CUDA 13.0) is compiled *entirely virtual*: `75-virtual;80-virtual;86-virtual;87-virtual;89-virtual;90-virtual;90a-virtual;100-virtual;103-virtual;110-virtual;120-virtual;121-virtual`. [SOURCED https://raw.githubusercontent.com/ollama/ollama/main/llama/server/CMakePresets.json] [SOURCED https://raw.githubusercontent.com/ollama/ollama/main/Dockerfile — `CUDA12VERSION=12.8`, `CUDA13VERSION=13.0`]
- So when Ollama picks cuda_v13 on the 5080, the driver JIT-compiles PTX for sm_120 on first load (the driver caches the result in `~/.nv/ComputeCache`); the cuda_v12 runner has native sm_120 SASS. `[INFERRED]` from the preset lists; the JIT cache location is standard NVIDIA behaviour.

### 4. Where the Thunderbolt tunnel is on the critical path — and where it is not
- Once weights are resident in VRAM, decode touches the link only for the per-token activations/logits: worst case ≈ 128 256 vocab × 4 B ≈ 513 KB per generated token, i.e. ~51 MB/s at 100 tok/s ≈ 1.3 % of a ~4 GB/s (theoretical) TB4 link, or ~1.7 % at the ~3 GB/s realised on this box. The throughput ceiling is VRAM bandwidth ÷ resident bytes, identical inside or outside an enclosure. [SOURCED https://localaimaster.com/blog/egpu-local-ai-benchmarks]
- The link governs (a) **model load time** (`seconds ≥ GB ÷ GB/s`), (b) anything that streams CPU-resident weights to the GPU per batch, and (c) multi-GPU traffic. [SOURCED same] Reported whole-system penalties: RTX 5080 in a TB4 enclosure ≈ 85 % of internal-PCIe token throughput on a Llama 3.1 70B Q4 workload, ≈ 95 % on TB5 (TB = Thunderbolt; Framework 16 + Razer Core X V2, Ubuntu 24.04; methodology not published in detail). [SOURCED https://botmonster.com/self-hosting/best-egpu-enclosures-linux-2026/] A separate RTX 4090 measurement reported TB3 eGPU 38.5 % lower tok/s than PCIe 4.0 x16 (page not retrievable at verification time; treat as anecdotal). `[INFERRED]` that the gap is dominated by prefill/batched paths and CPU-offload streaming rather than pure decode.

### 5. 16 GB residency budget
- Usable VRAM on an RTX 5080 is ~15.92 GiB; the interesting question on a 16 GB card "is rarely 'does it fit in VRAM'" but which tensors stay in host RAM and how efficiently they stream over PCIe. [SOURCED https://github.com/BFinn/5080-llm-configs]
- Budget = weights + KV cache + compute/scratch buffers (scale with `-ub`/batch) + CUDA context (~hundreds of MB) + any desktop compositor. KV per token = 2 × n_layer × n_kv_heads × head_dim × bytes/elem; `q8_0` halves it, `q4_0` quarters it (Ollama: "q8_0 … approximately 1/2 the memory of f16 with a very small loss in precision"; "q4_0 … approximately 1/4 … small-medium loss"). [SOURCED https://raw.githubusercontent.com/ollama/ollama/main/docs/faq.mdx]
- Flash attention is a prerequisite for KV quantization in Ollama and makes the attention scratch buffer O(1) in context length instead of O(n²). [SOURCED same FAQ] `[INFERRED]` for the scratch-buffer statement (standard FA behaviour).

### 6. MoE expert offload keeps the *hot* set on the GPU
- `--n-cpu-moe N` keeps the routed-expert FFN weights of the first N layers in system RAM; attention, KV cache, router, shared experts and norms stay on the GPU. `--override-tensor "\.ffn_.*_exps\.weight=CPU"` (`-ot`) is the general regex form. [SOURCED https://openclawdc.com/blog/llama-cpp-moe-offload-flags-explained/] [SOURCED https://gist.github.com/DocShotgun/a02a4c0c0a57e43ff4f038b46ca66ae0]
- Because only ~3–4 B of a 20–35 B MoE are active per token, CPU-side expert compute costs far less than dense-layer offload; the limiter becomes host RAM bandwidth (e.g. 33.6 GB/s measured on a DDR5-3600 desktop). [SOURCED 5080-llm-configs repo, URL in Sources] `[INFERRED]` that on the NUC the equivalent number is the NUC's own DDR5 SODIMM bandwidth, not the TB tunnel, for decode.

---

## Compatibility Matrix

| Stack (version verified) | Min CUDA to build / run | sm_120 status | Install path on this box | Known issues |
|---|---|---|---|---|
| **llama.cpp** b11170 (2026-09-24 nightly tag; the tagged `v0.5.0` release carries only `nightly-tag.txt`) | Build: toolkit ≥ 12.8 (`nvcc`). Run: cuda-12.8 tarball needs driver ≥ 570.26; cuda-13.4 tarball ≥ 580 via minor-version compat (R615 for full 13.4 feature set) | **Native.** `120a-real` SASS; MXFP4 tensor-core kernels (PR #17906, +1.2–1.3× pp on MXFP4 MoE); FA (FlashAttention) on | Prebuilt: `llama-b11170-bin-ubuntu-cuda-12.8-x64.tar.gz` (170 MB) or `…-cuda-13.4-x64.tar.gz` (150 MB) + matching `cudart-llama-b11170-bin-ubuntu-cuda-{12.8,13.4}-x64.tar.gz` (594 / 440 MB). Or build from source with a 12.8+/13.x toolkit (see recipe) | #19662 (plain `120` → ptxas mxf4 errors; open), #18398 (`compute_120a` unsupported on an old nvcc), FA dynamic-smem ceiling on sm_120 (see Ollama #18276) |
| **Ollama** v0.33.x (0.33.0 2026-08-21) | Driver ≥ 550 (docs); cuda_v13 runner implies ≥ 580; cuda_v12 runner (CUDA 12.8) ≥ 570 | **Supported.** "Ollama is now compiled for NVIDIA Blackwell" (v0.5.13, 2025-02-27); "Support for CUDA 13" (v0.11.11, 2025-09-11); docs list CC 12.0 GeForce RTX 50xx | Official installer ships `/usr/local/lib/ollama/cuda_v12/` and `cuda_v13/`; discovery bootstraps each dir and picks one; `OLLAMA_LLM_LIBRARY=cuda_v12` forces | #13163 (0.12.11, RTX 5070 Ti, driver 580.95: cuda_v13 loaded then `total vram="0 B"` CPU fallback), #12136 (driver 580.65.06/CUDA 13.0: `no nvidia devices detected by library …libcuda.so.580.65.06`), #18276 (qwen3moe + auto-FA crash at warmup on sm_120; `OLLAMA_FLASH_ATTENTION=0` works around), suspend/resume needs `rmmod nvidia_uvm && modprobe nvidia_uvm` |
| **PyTorch** 2.14.0 (2026-09-02) | cu130 wheel → driver ≥ 580; cu132 → ≥ 595 (R595 = CUDA 13.2); cu126 → ≥ 560; (cu128 → ≥ 570, wheel discontinued) | **Supported in cu130/cu132** (arch list "Turing 7.5, Ampere 8.0/8.6, Hopper 9.0, Blackwell 10.0, 12.0"). **Not in cu126** (Maxwell→Hopper only). First stable with sm_120 binaries: 2.7.0 (cu128) | `pip install torch` (PyPI = cu130 since 2.11); `--index-url https://download.pytorch.org/whl/cu132` for experimental 13.2; runtime comes from `nvidia-*` pip packages, apt CUDA 12.4 is irrelevant | cu128 removed from the build matrix in 2.12 (week of 2026-04-06); `torch.compile`/Triton historically needed a Triton whose bundled `ptxas` knows sm_120 (`Value 'sm_120' is not defined for option 'gpu-name'`); a reported gap in `libnvptxcompiler.so` in CUDA 12.8/12.9 pip runtime packages broke PTX JIT on a 5080 (HF forum report) |
| **vLLM** v0.30.0 (2026-09-22) | PyPI wheel = CUDA 13.0 (driver ≥ 580); `+cu129` wheel also published (docs page still says 12.9 default — docs lag the release) | **Partial → improving.** SM120-specific: `B12X_ATTN` causal paged-attention backend for SM120/121, W4A4 NVFP4 now default over weight-only kernels on SM120/121 (#55170), DeepGEMM fork with SM120 paged-MQA ports, SM12x blockwise FP8. Requires CC ≥ 7.5 | `pip install vllm` (cu130) or `uv pip install vllm --torch-backend=auto`; Docker `vllm/vllm-openai:v0.30.0` (`-cu129` tag for 12.9) | On 0.24 a ModelOpt NVFP4 checkpoint on a 5090 fell back to Marlin W4A16 with a misleading "no native FP4" warning (#47749); Nemotron NVFP4 MoE "No NvFp4 MoE backend" (#35065); SM120 uses SM80-style `mma.sync`, not SM100 `tcgen05` — SM100 kernels crash on SM120; FlashInfer Triton GEMM configs exceed SM120's 99 KiB (101 376 B) shared-memory limit (FlashInfer PR #5517) |
| **FlashInfer** 0.6.x | cu128/cu130 wheels (see vLLM) | Partial: FA2 tensor-core path and XQA NVFP4-KV decode are SM120-enabled; trtllm-gen FMHA sm120 still a feature request (#5290) | pulled in by vLLM | smem-limit launch failures; ongoing SM120 tracking issues (#5209, #5290) |
| **bitsandbytes** 0.50.1 (2026-08-13) | CUDA 12.8+ wheels carry sm_100/sm_120 since 0.45.3; CUDA 13 CI since 0.49.0; CUDA 13.2 wheels since 0.50.0 | Supported (4-bit fused dequant+GEMM kernels in 0.50.0) | `pip install bitsandbytes` matching the torch CUDA major | none Blackwell-specific found beyond the version floor |
| **TensorRT-LLM** (1.x line) | Container-based; CUDA 13.x | **Works, thinly documented.** Support matrix lists "NVIDIA Blackwell Architecture" without naming RTX 50 or FP4; FP4 GEMM on GeForce Blackwell was gated in 0.19.0 and enabled from 0.20.0rc3 (issue #5018); community RTX 5090 FP4 deployments (discussion #8334) and C++ runtime patches for 30B NVFP4 MoE on v1.2.0rc4 exist | NGC container only; heavy (tens of GB) — on a 16 GB card only small NVFP4 models fit | multimodal reported not working on 5090 (#8334); no official RTX 50 statement; TensorRT-for-RTX (a separate product) explicitly targets CC 12.0/12.1 |
| **ExLlamaV3** v1.5.1 (2026-09-20) | torch ≥ 2.6, CUDA ≥ 12.4; wheels `+cu128.torch2.8…2.11` and `+cu132.torch2.11…2.13` | Wheels are built with 12.8/13.2 toolkits (which support sm_120); attention/cache/recurrent kernels are Triton, so a Blackwell-aware Triton is required. README makes no explicit Blackwell statement `[INFERRED]` | `pip install exllamav3 --extra-index-url` per release page, pick the wheel matching your torch | none documented; torch 2.7 wheels retired in 1.4.9 |

Sources for this table: llama.cpp GitHub release API (b11166–b11171) and issues 19662/18398/20195; Ollama release API (v0.5.13, v0.11.11, v0.33.0), CMakePresets.json, Dockerfile, docs.ollama.com/gpu, issues 13163/12136/18276; PyTorch release v2.14.0 notes, dev-discuss posts 3325 and 3337; vLLM v0.30.0 release notes, docs installation/gpu, issues 47749/35065; FlashInfer issues 5290/5209 and PR 5517; bitsandbytes releases 0.49.0/0.50.0/0.50.1; TensorRT-LLM issue 5018, discussion 8334, support-matrix page; ExLlamaV3 release API. Full URLs in *Sources*.

---

## llama.cpp Build

### Option A — prebuilt (fastest, no nvcc needed)
```bash
# pick ONE CUDA line and keep binary + cudart from the SAME build number and CUDA version
B=b11170
curl -LO https://github.com/ggml-org/llama.cpp/releases/download/$B/llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz
curl -LO https://github.com/ggml-org/llama.cpp/releases/download/$B/cudart-llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz
mkdir -p ~/llama-cuda && tar -C ~/llama-cuda -xzf llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz \
                       && tar -C ~/llama-cuda -xzf cudart-llama-$B-bin-ubuntu-cuda-12.8-x64.tar.gz
# the cudart tarball supplies libcudart.so.12 / libcublas.so.12 / libcublasLt.so.12 next to the binaries,
# so the apt CUDA 12.4 libs are never used
```
Asset names as published on 2026-09-24: `llama-b11170-bin-ubuntu-cuda-12.8-x64.tar.gz`, `llama-b11170-bin-ubuntu-cuda-13.4-x64.tar.gz`, `cudart-llama-b11170-bin-ubuntu-cuda-12.8-x64.tar.gz`, `cudart-llama-b11170-bin-ubuntu-cuda-13.4-x64.tar.gz` (Windows: `cuda-12.4` and `cuda-13.4`). [SOURCED https://api.github.com/repos/ggml-org/llama.cpp/releases]
- Which one on driver 610? **12.8** is the zero-risk choice (any 12.x-built app runs on ≥ 525; the toolkit floor is 570.26). **13.4** runs under minor-version compat on ≥ 580 as long as the sm_120 code is SASS (`120a-real`, which the non-native CMake default produces); it is the one to pick if you want the newest cuBLAS. `[INFERRED]` — the official CI's exact `CMAKE_CUDA_ARCHITECTURES` for the Ubuntu CUDA jobs was not read; the non-native default in CMakeLists (toolkit ≥ 12.8 ⇒ `…;89-real;90-virtual;120a-real`) is what applies when CI sets `GGML_NATIVE=OFF`.
- One 2026-03 comment on issue 19662 claimed "Pre-built binaries don't include SM120 yet"; the Ubuntu CUDA assets did not exist then (issue #16205 requested them). The current asset list shows they now do. [SOURCED issue 19662 comment 2026-03-13; release API 2026-09-24]

### Option B — from source (needed for `GGML_CUDA_FA_QUANTS`, NCCL, custom flags)
Prerequisite: a CUDA **toolkit ≥ 12.8** (12.8 is the floor for `sm_120`; 13.x is fine on driver 610). Do **not** use the apt `nvidia-cuda-toolkit` 12.4 — install the toolkit from NVIDIA's repo or the runfile with `--toolkit` only (driver handling is in the sibling reference).
```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
cmake -B build \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
  -DCMAKE_CUDA_ARCHITECTURES="120a-real" \
  -DGGML_NATIVE=ON \
  -DGGML_CUDA_FA_QUANTS=all \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j"$(nproc)" --target llama-server llama-cli llama-bench llama-gguf-split
```
- `CMAKE_CUDA_ARCHITECTURES`: if omitted, `GGML_NATIVE=ON` (default) + toolkit ≥ 11.6 + CMake ≥ 3.24 gives `native`, and CMake's detected `120-real` is rewritten to `120a-real` — **but only if the GPU is attached at configure time**; with no GPU present the native list is "garbage" and the build must be re-run with an explicit list. Explicit `120a-real` (or `120a`) is the community-confirmed form; plain `120` compiles nothing MXFP4-related on the current tree (issue 19662). [SOURCED ggml-cuda CMakeLists; issue 19662 comments dated 2026-03-13 and 2026-05-04]
- `GGML_NATIVE=OFF` builds a portable arch set (`…;86-real;89-real;90-virtual;120a-real`) — use it if the binary must also run on a non-Blackwell box. [SOURCED docs/build.md; CMakeLists]
- `GGML_CUDA_FA_QUANTS=all` compiles FlashAttention kernels for every K/V quant pair (needed for `-ctk q4_0`/`q8_0` combos); `GGML_CUDA_FA_ALL_QUANTS` is a deprecated alias. `GGML_CUDA_FORCE_MMQ` / `GGML_CUDA_FORCE_CUBLAS` (default off) pick custom quantized MMQ vs FP16 cuBLAS. `GGML_CUDA_NO_VMM` disables the virtual-memory-management pool. [SOURCED https://raw.githubusercontent.com/ggml-org/llama.cpp/master/docs/build.md; CMakeLists]
- `LLAMA_CUDA` is deprecated in favour of `GGML_CUDA`. [SOURCED issue 19662 CMake output]
- Look for these two lines in the configure log to confirm a correct Blackwell build:
  `-- Replacing 120-real in CMAKE_CUDA_ARCHITECTURES_NATIVE with 120a-real`
  `-- Using CMAKE_CUDA_ARCHITECTURES=120a-real CMAKE_CUDA_ARCHITECTURES_NATIVE=120a-real` [SOURCED issue 19662]
- `CUDA 13.x` builds drop `50/61/70-virtual` from the non-native default (Maxwell/Pascal/Volta are gone from CUDA 13). [SOURCED CMakeLists]

### Runtime sanity
```bash
~/llama-cuda/llama-bench -m model.gguf -ngl 99 -fa 1 -p 512 -n 128
# expect ggml_cuda_init: found 1 CUDA devices: Device 0: NVIDIA GeForce RTX 5080, compute capability 12.0
```
Reference points from the community CUDA benchmark thread (7B Q4_0, `pp512`/`tg128`): RTX 5080 8297→9488 pp, 182→185 tg (pairs read as FA off → on `[INFERRED]`); RTX 5090 14073/290 → 14970/300; RTX 4090 11993/186 → 14771/189. [SOURCED https://github.com/ggml-org/llama.cpp/discussions/15013]

---

## Ollama

### How the bundled runners are chosen
- The Linux install ships `lib/ollama/cuda_v12/` (CUDA 12.8, arches incl. `120` real+PTX) and `lib/ollama/cuda_v13/` (CUDA 13.0, all `-virtual` incl. `120-virtual`). [SOURCED CMakePresets.json; Dockerfile]
- `discover/runner.go` enumerates each `*ggml-*` library dir, runs a bootstrap discovery pass per dir (30 s timeout), applies `filterOldCUDADriver` only to the `cuda_v12` dir, then a second pass "to weed out devices that aren't supported by a given library". `OLLAMA_LLM_LIBRARY` skips every other dir ("skipping available library at user's request"). [SOURCED https://raw.githubusercontent.com/ollama/ollama/main/discover/runner.go]
- Library preference is cuda_v13 > cuda_v12 > cuda_v11 when several qualify (third-party wiki summary of the sorter; not read in the Go source). `[INFERRED]` — on driver 610 both qualify, so expect `cuda_v13` unless overridden.
- Docs: "Ollama supports Nvidia GPUs with compute capability 5.0+ and driver version 550 and newer"; CC 12.0 "GeForce RTX 50xx" is listed; `CUDA_VISIBLE_DEVICES` accepts UUIDs (more reliable than ordinals). NVML is not mentioned in the docs — discovery goes through the ggml CUDA backend (`libcuda`), which is why #12136 reports `no nvidia devices detected by library …/libcuda.so.580.65.06`. [SOURCED https://docs.ollama.com/gpu; issue 12136]

### Env knobs (from `envconfig/config.go`, default in parentheses)
| Variable | Default | Effect |
|---|---|---|
| `OLLAMA_FLASH_ATTENTION` | auto (FA is enabled "automatically when the selected backend and devices support it"); `1` forces on, `0` forces off | attention scratch stays flat with context; prerequisite for KV quantization |
| `OLLAMA_KV_CACHE_TYPE` | `f16` | `q8_0` ≈ ½ KV memory, "very small loss"; `q4_0` ≈ ¼, "small-medium loss … more noticeable at higher context"; **global**, applies to all models |
| `OLLAMA_CONTEXT_LENGTH` | `0` = auto ("4k/32k/256k based on VRAM" per code; FAQ says 4096) | default `num_ctx` |
| `OLLAMA_KEEP_ALIVE` | `5m` | negative value keeps the model loaded forever (avoids a TB reload every idle period) |
| `OLLAMA_GPU_OVERHEAD` | `0` bytes | reserve VRAM per GPU for other processes |
| `OLLAMA_MAX_LOADED_MODELS` / `OLLAMA_NUM_PARALLEL` / `OLLAMA_MAX_QUEUE` | `0` / `1` / `512` | scheduler limits |
| `OLLAMA_SCHED_SPREAD` | `false` | force spreading across all GPUs |
| `OLLAMA_LLM_LIBRARY` | unset | force `cuda_v12`, `cuda_v13`, `vulkan`, `cpu_avx2`… |
| `OLLAMA_VULKAN` | `true` | disable to stop Vulkan probing the same GPU |
| `OLLAMA_DEBUG` | `0` | `1` for discovery/load logs |
| `CUDA_VISIBLE_DEVICES` | unset | device visibility |
[SOURCED https://raw.githubusercontent.com/ollama/ollama/main/envconfig/config.go; https://raw.githubusercontent.com/ollama/ollama/main/docs/faq.mdx]

- **`OLLAMA_NUM_GPU` is not an upstream environment variable.** `envconfig/config.go` does not define it; `num_gpu` is a per-request/Modelfile *option* (`NumGPU int json:"num_gpu"`, default `-1` = "set dynamically"). Set it via `PARAMETER num_gpu 999` in a Modelfile or `"options":{"num_gpu":999}` in the API to force all layers onto the GPU. Guides that mention `OLLAMA_NUM_GPU` come from the IPEX-LLM fork. [SOURCED https://raw.githubusercontent.com/ollama/ollama/main/api/types.go; envconfig/config.go]

### Verification checklist (run as the user; nothing here changes state)
1. `ollama --version` → ≥ 0.11.11 for a cuda_v13 runner; ≥ 0.5.13 for any Blackwell SASS. [SOURCED release notes]
2. `journalctl -u ollama --since -10m | grep -E 'load_backend|inference compute|total vram|library='` → expect `load_backend: loaded CUDA backend from /usr/local/lib/ollama/cuda_v13/libggml-cuda.so` (or `cuda_v12`) and an `inference compute` line with `library=cuda` and `compute=12.0`; **failure signature** is `library=cpu` plus `"total vram"="0 B"` / `entering low vram mode`. [SOURCED issue 13163 log lines]
3. `nvidia-smi --query-gpu=name,memory.used,driver_version --format=csv` while a model is loaded → memory.used ≈ model size + KV.
4. `ollama ps` → `100% GPU`, not `48%/52% CPU/GPU`. [SOURCED FAQ]
5. If discovery fails after suspend/resume: `sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm`. [SOURCED docs.ollama.com/gpu]
6. A/B the runner: `OLLAMA_LLM_LIBRARY=cuda_v12 ollama serve` vs `cuda_v13`; on a Blackwell CPU-fallback (#13163 pattern) the v12 runner with real sm_120 SASS is the first thing to try. `[INFERRED]`
7. MoE model + FA crash at warmup (`CUDA error: shared object initialization failed` at `fattn-mma-f16.cuh`) → `OLLAMA_FLASH_ATTENTION=0` (global) until fixed; the kernel asked for more dynamic shared memory than sm_120 allows. [SOURCED https://github.com/ollama/ollama/issues/18276]
8. Confirm KV quantization took effect: the load log prints the cache type; if FA is off the setting is silently ignored. [SOURCED FAQ ("cache is only quantized when flash attention is enabled")]
9. Set `OLLAMA_KEEP_ALIVE=-1` in the systemd override so the ~4 s TB reload (see Thunderbolt Bandwidth Costs) doesn't recur after every 5-minute idle.

---

## PyTorch & vLLM

### PyTorch wheel matrix (2.14.0)
| Wheel | Arch list | Driver floor | Status |
|---|---|---|---|
| `cu126` | 5.0, 6.0, 7.0, 7.5, 8.0, 8.6, 9.0 — **no 12.0** | ≥ 560 | legacy |
| `cu128` | had 12.0 (first stable sm_120 binaries in 2.7.0) | ≥ 570 | **removed** from the matrix in 2.12 (April 2026) |
| `cu130` | 7.5, 8.0, 8.6, 9.0, 10.0, **12.0** | ≥ 580 | PyPI default since 2.11 |
| `cu132` | 7.5, 8.0, 8.6, 9.0, 10.0, **12.0** | R595+ (CUDA 13.2 branch) | experimental since 2.12 |
[SOURCED https://dev-discuss.pytorch.org/t/transitioning-pypi-cuda-wheels-to-cuda-13-0-as-the-stable-release-2-11/3325; https://dev-discuss.pytorch.org/t/introducing-cuda-13-2-and-deprecating-cuda-12-8-release-2-12/3337; https://github.com/pytorch/pytorch/issues/159207; CUDA release-notes driver table]
- `pip install torch` → cu130 and the `nvidia-*` runtime wheels (cudart, cublas, cudnn 9.24, nccl 2.30.7…) — the apt CUDA 12.4 install is not consulted; only the **driver** floor matters. 2.14.0 also added a cuBLASLt grouped-GEMM backend "on Hopper and Blackwell GPUs with CUDA 13.3 or newer" and sm_107 (Rubin) awareness with CUDA 13.4. [SOURCED https://api.github.com/repos/pytorch/pytorch/releases/latest]
- `torch.compile` on sm_120: Inductor emits Triton; the bundled Triton must ship a `ptxas` that knows sm_120 (historic error `Value 'sm_120' is not defined for option 'gpu-name'`), and PTX JIT needs `libnvptxcompiler`/nvJitLink from the CUDA runtime wheels (a 2025 forum report found it missing in the 12.8/12.9 pip packages on a 5080). With cu130/cu132 wheels and a current Triton this is expected to work; verify with a one-line `torch.compile` smoke test rather than assuming. `[INFERRED]` — sourced only at the level of forum reports. [SOURCED https://discuss.pytorch.org/t/rtx-5070-ti-blackwell-pytorch-nightly-triton-still-getting-sm-120-is-not-defined-for-option-gpu-name-error/220460]
- Ignore 2025-era search hits saying "stable PyTorch supports only up to sm_90" — true before 2.7.0, false now.

### vLLM 0.30.0 on a 16 GB SM120 card
- Install: `pip install vllm` (CUDA 13.0 wheel) or the `+cu129` wheel from the GitHub release; Docker `vllm/vllm-openai:v0.30.0` (`-cu129` variant). Docs' "compiled with CUDA 12.9 by default" predates the 0.30 release notes. [SOURCED https://api.github.com/repos/vllm-project/vllm/releases/latest; https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html]
- SM120 paths that exist today: `--attention-backend B12X_ATTN` (causal paged attention for SM120/121); W4A4 NVFP4 is the new default over weight-only kernels on SM120/121; NVFP4 KV cache on consumer Blackwell (FlashInfer FA2 dequantizes FP4 KV to BF16 in-kernel; XQA NVFP4-KV decode is SM120-exclusive). [SOURCED vLLM v0.30.0 notes; https://github.com/vllm-project/vllm/pull/50288; https://github.com/vllm-project/vllm/pull/46329]
- Pitfalls: SM120 executes SM80-era `mma.sync`, not SM100 `tcgen05.mma` — kernels compiled for SM100 fail or crash on SM120; FlashInfer/Triton GEMM configs that need > 99 KiB shared memory fail at launch (RTX 5090 limit 101 376 B); ModelOpt "mixed NVFP4" checkpoints could silently fall to Marlin W4A16 in 0.24 (#47749, tracked with #31085/#44022/#46268). [SOURCED PR 50288 description; FlashInfer PR 5517; vLLM issue 47749]
- 16 GB reality: vLLM pre-reserves `--gpu-memory-utilization` (0.9 default) of VRAM at startup for weights + paged KV, so it cannot coexist with a loaded Ollama model; stop Ollama (or set `OLLAMA_MAX_LOADED_MODELS`/`KEEP_ALIVE=0`) before serving with vLLM, and expect only ≤ 8B BF16 or ≤ ~14B W4 models to leave room for KV. `[INFERRED]` from vLLM's documented allocator behaviour.
- bitsandbytes 0.50.x: sm_120 wheels since 0.45.3; fused 4-bit dequant+GEMM in 0.50.0 ("up to 4x faster at batch sizes 2–64"); CUDA 13.2 wheels since 0.50.0. [SOURCED bitsandbytes release API]

### TensorRT-LLM / ExLlamaV3 (short)
- TensorRT-LLM: FP4 GEMM on GeForce Blackwell unlocked at 0.20.0rc3 (#5018); RTX 5090 FP4 serving (`nvidia/Qwen3-30B-A3B-FP4`) reported working via NGC container + OpenAI-compatible API, multimodal not; C++ runtime patches were needed for 30B NVFP4 MoE on v1.2.0rc4. The official support matrix names only "NVIDIA Blackwell Architecture". On 16 GB this is a niche option. [SOURCED https://github.com/NVIDIA/TensorRT-LLM/issues/5018; https://github.com/NVIDIA/TensorRT-LLM/discussions/8334; https://github.com/JohnTDI-cpu/trtllm-nvfp4-blackwell-fix; https://nvidia.github.io/TensorRT-LLM/reference/support-matrix.html]
- ExLlamaV3 1.5.1: wheels `+cu128.torch{2.8,2.9,2.10,2.11}` and `+cu132.torch{2.11,2.12,2.13}`; needs torch ≥ 2.6 and CUDA ≥ 12.4; attention/cache kernels are Triton. Pair `cu132` with torch 2.12/2.13 cu132 for the newest path, or `cu128` with torch 2.11 if you keep a cu128 torch pinned. [SOURCED https://api.github.com/repos/turboderp-org/exllamav3/releases; https://github.com/turboderp-org/exllamav3]

---

## Thunderbolt Bandwidth Costs

Assumptions: TB4 tunnel realised ≈ **3 GB/s** on this box (figure supplied by the box owner, not measured here; theoretical PCIe 3.0 x4 ≈ 4 GB/s), vs ≈ 25 GB/s realised on internal PCIe 4.0 x16 (31.5 GB/s theoretical). Formulae from [SOURCED https://localaimaster.com/blog/egpu-local-ai-benchmarks]; numbers below are arithmetic on those formulae plus published model sizes — `[INFERRED]` unless noted.

| Operation | Bytes crossing the tunnel | Time @ 3 GB/s (TB4) | Time @ 25 GB/s (x16) | Verdict |
|---|---|---|---|---|
| Load 8B Q4_K_M (4.8 GB) | 4.8 GB, once | ≥ 1.6 s | ≥ 0.2 s | noticeable only if reloaded often |
| Load gpt-oss-20b MXFP4 (~12.1 GB) | ~12 GB, once | ≥ 4 s | ≥ 0.5 s | set `OLLAMA_KEEP_ALIVE=-1` |
| Load Qwen3.5-35B-A3B UD-IQ3_S (13.6 GB) | 13.6 GB, once | ≥ 4.5 s | ≥ 0.55 s | same |
| Decode, all weights resident | ≤ 513 KB/token (worst case, fp32 logits of a 128 K vocab) → 51 MB/s @ 100 tok/s | ~1.7 % of link | ~0.2 % | **not link-bound** [SOURCED localaimaster] |
| Prefill, all weights resident | token embeddings in, logits out; KV stays on GPU | negligible | negligible | not link-bound; RTX 5080 pp512 ≈ 9.5 k tok/s (7B Q4_0) |
| Decode with `--n-cpu-moe N` | per offloaded layer per token ≈ 2 × n_embd × 2 B of activations (e.g. Qwen3-30B-A3B n_embd 2048 → ~8 KB/layer, ~0.4 MB/token for all 48 layers) | < 1 % of link | — | limiter is **host DDR5 bandwidth** and CPU FLOPs, not TB |
| Prefill with `--n-cpu-moe N` at large `-ub` | llama.cpp may stream CPU-resident expert weights to the GPU per micro-batch for batched matmul; worst case = all offloaded expert bytes per ubatch (e.g. 8 GB of experts → ≥ 2.7 s per ubatch) | seconds per ubatch | 0.3 s | **link-bound**; the only common path where TB really hurts. Mitigate with smaller `-ub`, fewer offloaded layers, or accept slower prefill `[INFERRED]` — the 5080-llm-configs repo notes "PCIe streaming efficiency" is the real question on a 16 GB 5080 |
| Two eGPUs on one TB controller, `-sm layer` | activations at each layer boundary (KB/token) | small | — | fine for decode; both GPUs share 40 Gbps |
| Two eGPUs, `-sm row` / tensor-parallel | all-reduce per layer (MB/token) | link-bound | — | avoid over TB |
| KV cache | never leaves the GPU for GPU layers | 0 | 0 | — |
| Model swap (two models alternating under `OLLAMA_MAX_LOADED_MODELS=1`) | full reload each swap | ≥ 4 s per swap for 12 GB | — | raise `OLLAMA_MAX_LOADED_MODELS` only if both fit |

Whole-system reference points (not decomposed): RTX 5080 TB4 ≈ 85 % of internal throughput, TB5 ≈ 95 % on a 70B Q4 workload that is itself partly CPU-offloaded on a 16 GB card — consistent with the offload-prefill row above. [SOURCED botmonster] Disk is often the real load bottleneck: a cold GGUF read from NVMe (3–7 GB/s) is on the same order as the tunnel; a page-cache-warm second load is tunnel-bound. `[INFERRED]`

---

## 16 GB Residency

Goal: weights + KV + scratch ≤ ~15 GiB so nothing spills to CPU and nothing re-crosses the tunnel after load.

**Model classes that stay resident on a 16 GB RTX 5080 (published measurements):**
| Model / quant | Weights | Context that fit | Speed | Source |
|---|---|---|---|---|
| gpt-oss-20b MXFP4 (ggml-org GGUF) | ~12 GB | `--ctx-size 32768 -ub 4096 -b 4096` on 16 GB (llama.cpp guide) | ~89 tok/s est. on 5080 | [SOURCED https://github.com/ggml-org/llama.cpp/discussions/15396; modelfit.io] |
| Qwen3.5-35B-A3B UD-IQ3_S | 13.6 GB | ~100 K (RTX 4080 16 GB) | 136–138 tok/s at 19–64 K | [SOURCED https://www.glukhov.org/llm-performance/benchmarks/best-llm-on-16gb-vram-gpu/] |
| Qwen3.5-27B UD-IQ3_XXS (dense) | 11.5 GB | 128 K (9.6 tok/s there); 45 tok/s ≤ 32 K | — | same |
| Qwen3.8-27B UD-IQ3_S (dense, vision) | 12 GB | 98 304 | 95–96 tok/s decode w/ speculative, 1 756 tok/s prefill | [SOURCED 5080-llm-configs repo, URL in Sources] |
| 14B Q4_K_M | ~8.4 GB | 32 K f16 KV comfortably | ~58 tok/s | [SOURCED modelfit.io/gpu/rtx-5080] |
| 8B Q4_K_M | ~4.8 GB | 64 K+ | ~45 tok/s (Llama 3.1 8B, localscore) | [SOURCED https://www.localscore.ai/accelerator/489] |

**llama.cpp flags that keep it resident**
```bash
llama-server -m model.gguf -ngl 99 -fa on -c 32768 -ctk q8_0 -ctv q8_0 -ub 512 -b 2048 --jinja
# MoE that does not fit: keep attention/router/KV on GPU, experts partly on CPU
llama-server -m qwen3-30b-a3b-Q4_K_M.gguf -ngl 99 --n-cpu-moe 12 -fa on -c 32768 -ctk q8_0 -ctv q8_0
```
- Raise `--n-cpu-moe` in small steps until the load succeeds, then walk it back down for speed; `-ot "\.ffn_.*_exps\.weight=CPU"` is the fully-offloaded form. [SOURCED openclawdc.com; MoE-flags gist]
- `-ub` sets the compute-buffer size; on a TB link a smaller `-ub` also shrinks the per-ubatch weight streaming when experts are offloaded (see bandwidth table). `[INFERRED]`
- `-ctk/-ctv q8_0` need a build with the matching FA quant kernels (`GGML_CUDA_FA_QUANTS=all` or the default set that includes q8_0). [SOURCED docs/build.md]
- Bench with `llama-bench -ngl 99 -fa 1 -ctk q8_0 -ctv q8_0 -p 512,2048 -n 128` and confirm `nvidia-smi` shows no growth after the first request.

**Ollama equivalents**
```ini
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_CONTEXT_LENGTH=32768"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
```
plus `PARAMETER num_gpu 999` (Modelfile) or `"options":{"num_gpu":999,"num_ctx":32768}` (API) when Ollama's automatic estimate under-offloads; verify with `ollama ps` → `100% GPU`. If Ollama insists on splitting, lower `num_ctx` or the KV type before touching `num_gpu`. [SOURCED FAQ; api/types.go] Ollama's own MoE offload is automatic (it has no `--n-cpu-moe` knob); for fine-grained expert placement use llama-server directly. `[INFERRED]` from the absence of such an option in `envconfig` and `api/types.go`.

**Rules of thumb** `[INFERRED]`
- Weights ≤ 11–12 GB → 32 K f16 KV fits for ≤ 14B dense; ≤ 13.5 GB → needs q8_0 KV or ≤ 16 K.
- Reserve ~0.5–1 GB for CUDA context + compositor; add `OLLAMA_GPU_OVERHEAD` if another CUDA process (e.g. a torch job) must coexist.
- Never run vLLM and a loaded Ollama model on the same 16 GB card.

---

## Anti-patterns

1. **`-DCMAKE_CUDA_ARCHITECTURES=120`** on a current tree → `ptxas … '.kind::mxf4' not supported on .target 'sm_120'`; use `120a-real` (or let `native` rewrite it). `-DGGML_CUDA_MXFP4=OFF` does not prevent the template instantiation. [SOURCED issue 19662]
2. **apt `nvcc` 12.4** → `Unsupported gpu architecture 'compute_120'`; the floor is toolkit 12.8. [SOURCED issue 20195]
3. **`GGML_NATIVE=ON` with the eGPU unplugged/asleep at configure time** → CMake's native list is "garbage" and the build targets nothing useful; configure with the GPU attached or pass the arch list explicitly. [SOURCED CMakeLists comment]
4. **Mixing a `cuda-13.4` binary with the `cuda-12.8` cudart bundle** (or with the apt 12.4 libs) → `libcudart.so.13` not found or symbol errors; keep build number and CUDA major identical. [SOURCED release asset naming] `[INFERRED]` for the failure mode.
5. **Old-toolkit-built binary + new PTX**: a PTX-only build (Ollama `cuda_v13` is all `-virtual`) depends on the driver's JIT; on a *lower* driver than the PTX ISA it fails. On driver 610 this is fine for CUDA 13.0 PTX, but not for a 13.4-era PTX-only artefact. [SOURCED minor-version compatibility doc; CMakePresets]
6. **`OLLAMA_NUM_GPU=…`** — not an upstream variable; it does nothing (issue #11437 documents the resulting confusion). Use `num_gpu` as an option. [SOURCED envconfig; api/types.go]
7. **`OLLAMA_KV_CACHE_TYPE=q8_0` with FA off** → silently ignored, KV stays f16 and the model spills. [SOURCED FAQ]
8. **Leaving FlashAttention on (auto or forced `=1`) for a qwen3moe-class model on sm_120** → warmup crash (`shared object initialization failed`, dynamic shared memory ceiling). Set `OLLAMA_FLASH_ATTENTION=0` (global, so it also disables KV quantization) or wait for the fix. [SOURCED issue 18276]
9. **`pip install torch --index-url …/cu126`** on Blackwell → `sm_120 is not compatible with the current PyTorch installation`; cu126 has no 12.0 SASS. Use cu130 (default) or cu132. [SOURCED dev-discuss 3337]
10. **Assuming SM100 kernels/flags apply to SM120** (`tcgen05`, datacenter NVFP4 MoE backends) → compile or runtime failure; consumer Blackwell is `mma.sync` + 99 KiB smem. [SOURCED vLLM PR 50288; FlashInfer PR 5517]
11. **Large `-ub` with heavy `--n-cpu-moe` over a TB link** → prefill becomes a weight-streaming exercise at 3 GB/s; shrink `-ub` or offload fewer layers. `[INFERRED]`
12. **Default `OLLAMA_KEEP_ALIVE=5m` on an eGPU** → a 12 GB model re-crosses the tunnel after every idle gap (≥ 4 s each time). Set `-1`. `[INFERRED]` from the load-time formula.
13. **Trusting 2025 search snippets** ("no prebuilt SM120 binaries", "stable torch stops at sm_90", "vLLM lacks 5090 support") — all superseded; check the dated sources above.
14. **Running vLLM beside a loaded Ollama model on 16 GB** → allocator collision; vLLM reserves 90 % by default. `[INFERRED]`

---

## Sources

llama.cpp
- https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-cuda/CMakeLists.txt — arch defaults, 12X→12Xa rewrite, real/virtual semantics, "120 == Blackwell, needs CUDA v12.8"
- https://raw.githubusercontent.com/ggml-org/llama.cpp/master/docs/build.md — `GGML_CUDA`, `GGML_NATIVE`, `GGML_CUDA_FA_QUANTS`, `GGML_CUDA_FORCE_MMQ/CUBLAS`
- https://github.com/ggml-org/llama.cpp/issues/19662 — MXFP4 ptxas errors on `sm_120`, `120a-real` fix, configure-log signature (opened 2026-02-16, open)
- https://github.com/ggml-org/llama.cpp/pull/17906 — native MXFP4 for Blackwell (merged 2025-12-24), 120a/120f, perf numbers; follow-ups #18361, #18736
- https://github.com/ggml-org/llama.cpp/issues/18398 — `compute_120a` unsupported after #17906 (closed stale)
- https://github.com/ggml-org/llama.cpp/issues/20195 and https://github.com/ggml-org/llama.cpp/issues/22696 — `compute_120` needs toolkit ≥ 12.8
- https://api.github.com/repos/ggml-org/llama.cpp/releases — b11166–b11171 asset list (`…ubuntu-cuda-12.8-x64`, `…ubuntu-cuda-13.4-x64`, `cudart-…`), 2026-09-24
- https://github.com/ggml-org/llama.cpp/issues/16205 — original request for Ubuntu CUDA release assets
- https://github.com/ggml-org/llama.cpp/discussions/15013 — RTX 5080/5090/4090 pp512/tg128 numbers
- https://github.com/ggml-org/llama.cpp/discussions/15396 — gpt-oss run guide, 16 GB flags
- https://gist.github.com/DocShotgun/a02a4c0c0a57e43ff4f038b46ca66ae0 and https://openclawdc.com/blog/llama-cpp-moe-offload-flags-explained/ — `--n-cpu-moe`, `-ot` regex

Ollama
- https://raw.githubusercontent.com/ollama/ollama/main/llama/server/CMakePresets.json — cuda_v12 / cuda_v13 arch lists
- https://raw.githubusercontent.com/ollama/ollama/main/Dockerfile — `CUDA12VERSION=12.8`, `CUDA13VERSION=13.0`
- https://raw.githubusercontent.com/ollama/ollama/main/discover/runner.go — bootstrap discovery, `OLLAMA_LLM_LIBRARY`, `filterOldCUDADriver`
- https://raw.githubusercontent.com/ollama/ollama/main/envconfig/config.go — env variable definitions/defaults
- https://raw.githubusercontent.com/ollama/ollama/main/api/types.go — `NumGPU json:"num_gpu"`, default -1
- https://raw.githubusercontent.com/ollama/ollama/main/docs/faq.mdx and https://docs.ollama.com/faq — FA auto/`1`/`0`, KV cache types, `ollama ps`
- https://docs.ollama.com/gpu — CC 5.0+, driver 550+, CC 12.0 RTX 50xx listed, UVM reload workaround
- https://api.github.com/repos/ollama/ollama/releases — v0.5.13 "compiled for NVIDIA Blackwell", v0.11.11 "Support for CUDA 13", v0.33.0
- https://github.com/ollama/ollama/issues/13163, https://github.com/ollama/ollama/issues/12136, https://github.com/ollama/ollama/issues/18276, https://github.com/ollama/ollama/issues/11437

NVIDIA CUDA
- https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html — toolkit↔driver table (12.0…13.4), driver no longer bundled on Linux from 13.4
- https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html — 13.0 ≥ 580.65.06
- https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html — 12.x ≥ 525, 13.x ≥ 580, PTX caveat

PyTorch / vLLM / FlashInfer / bitsandbytes / TRT-LLM / ExLlamaV3
- https://dev-discuss.pytorch.org/t/transitioning-pypi-cuda-wheels-to-cuda-13-0-as-the-stable-release-2-11/3325 (2026-03-11)
- https://dev-discuss.pytorch.org/t/introducing-cuda-13-2-and-deprecating-cuda-12-8-release-2-12/3337 — per-wheel arch lists, cu128 removal
- https://api.github.com/repos/pytorch/pytorch/releases/latest — v2.14.0 (2026-09-02) notes
- https://github.com/pytorch/pytorch/issues/159207 — sm_120 support history (2.7.0 first stable)
- https://discuss.pytorch.org/t/rtx-5070-ti-blackwell-pytorch-nightly-triton-still-getting-sm-120-is-not-defined-for-option-gpu-name-error/220460
- https://discuss.huggingface.co/t/ptx-jit-broken-on-rtx-5080-blackwell-sm-120-missing-libnvptxcompiler-so-in-cuda-12-8-12-9/161827 (title only; page 403 at verification)
- https://api.github.com/repos/vllm-project/vllm/releases/latest — v0.30.0 (2026-09-22): CUDA 13.0 PyPI, cu129 wheels, `B12X_ATTN`, NVFP4 W4A4 default on SM120/121
- https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html — CC ≥ 7.5, wheel variants
- https://github.com/vllm-project/vllm/pull/50288, https://github.com/vllm-project/vllm/pull/46329, https://github.com/vllm-project/vllm/issues/47749, https://github.com/vllm-project/vllm/issues/35065, https://github.com/vllm-project/vllm/issues/31085
- https://github.com/flashinfer-ai/flashinfer/pull/5517, https://github.com/flashinfer-ai/flashinfer/issues/5290, https://github.com/flashinfer-ai/flashinfer/issues/5209
- https://api.github.com/repos/bitsandbytes-foundation/bitsandbytes/releases — 0.49.0, 0.50.0, 0.50.1
- https://github.com/NVIDIA/TensorRT-LLM/issues/5018, https://github.com/NVIDIA/TensorRT-LLM/discussions/8334, https://github.com/JohnTDI-cpu/trtllm-nvfp4-blackwell-fix, https://nvidia.github.io/TensorRT-LLM/reference/support-matrix.html
- https://api.github.com/repos/turboderp-org/exllamav3/releases and https://github.com/turboderp-org/exllamav3

Thunderbolt / 16 GB
- https://localaimaster.com/blog/egpu-local-ai-benchmarks — link bandwidth table, load-time formula, per-token traffic arithmetic (explicitly theoretical)
- https://botmonster.com/self-hosting/best-egpu-enclosures-linux-2026/ — RTX 5080 TB4 ≈ 85 %, TB5 ≈ 95 % of internal
- https://github.com/BFinn/5080-llm-configs — measured 16 GB RTX 5080 configs
- https://www.glukhov.org/llm-performance/benchmarks/best-llm-on-16gb-vram-gpu/ — 16 GB model/context/speed table
- https://www.localscore.ai/accelerator/489, https://modelfit.io/gpu/rtx-5080/ — 5080 tok/s reference points
