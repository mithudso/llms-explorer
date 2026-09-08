---
title: "On-Device & Local LLM Runtimes"
description: "The local/on-device runtime + developer-experience layer: which runtime to"
---

# On-Device & Local LLM Runtimes

The **local/on-device runtime + developer-experience layer**: which runtime to
install and how to run, serve, and size an LLM on a laptop, desktop, phone,
browser, or edge device — without a cloud API. This is the "get a model talking
on `localhost`" skill, not the quant-math skill and not the datacenter-serving
skill.

## When to use / Skip

**Use this skill when you are:**
- Choosing a local runtime (Ollama vs llama.cpp vs LM Studio vs MLX vs MLC vs
  Jan vs GPT4All vs llamafile vs KoboldCpp).
- Sizing hardware: "how much RAM/VRAM for a 7B/13B/70B?", "which quant fits 8/12/24 GB?".
- Standing up a **local OpenAI-compatible server** and pointing app code at it.
- Running a model **in the browser** (WebGPU / WebLLM / Transformers.js / Chrome
  Prompt API) or **on a phone** (MediaPipe/LiteRT-LM / ONNX Runtime GenAI /
  llama.cpp), or via OS frameworks (Apple Foundation Models, Windows Foundry Local).
- Getting **local embeddings** or **local structured output / function calling**.

**Skip — defer to the right neighbor:**
- **Quantization ALGORITHMS & format internals** — GPTQ/AWQ, GGUF k-quant math,
  imatrix, bitsandbytes/NF4 -> **`llm-compression`**. (Quant *levels* as a
  fit/quality/speed knob are HERE; *why* Q4_K_M is 4.8 bpw is THERE.)
- **Datacenter / server-grade serving** — vLLM PagedAttention, continuous/in-flight
  batching, prefill/decode disaggregation, TTFT/TPOT goodput SLOs, multi-GPU
  tensor/pipeline parallelism -> **`llm-inference-serving`**. (Single-machine local
  serving is HERE; the high-throughput engine is THERE.)
- Consuming a **hosted cloud** model / managed endpoint -> `llm-integration-reviewer`,
  `aws-ai-ml`. Picking the *best* model on quality/price -> `llm-models`.

## Why run locally

| Driver | What it buys you |
|---|---|
| **Privacy / data residency** | Prompts + documents never leave the device. The whole premise of Apple Foundation Models, Chrome Built-in AI, Windows Foundry Local. |
| **Cost** | No per-token billing — viable for high-volume, batch, or background tasks. |
| **Offline** | Works on a plane, air-gapped network, or the edge. |
| **Latency** | No network round-trip; on-device TTFT ~100 ms for a 3B on a modern NPU. |
| **Control** | No rate limits, no surprise deprecations, reproducible runs. |

The tradeoff: local models are smaller/slower per token than frontier cloud
models, and **you own the ops** (download, RAM budget, updates). Pick local when
privacy/cost/offline matters more than peak capability.

## Desktop/server runtime landscape

### Ollama — the default on-ramp
- Go daemon over a llama.cpp-derived engine. `ollama run llama3.1` pulls from the
  **model library** and serves on **`localhost:11434`**.
- **APIs:** OpenAI-compatible `/v1/chat/completions`, `/v1/completions`,
  `/v1/embeddings`, `/v1/responses` (non-stateful), tools/function-calling, JSON
  mode; plus native `/api/chat`, `/api/generate`, `/api/embed`.
- **Modelfile** = build blueprint: `FROM`, `PARAMETER` (e.g. `num_ctx 8192`,
  `temperature`), `SYSTEM`, `TEMPLATE` (Go template), `ADAPTER` (LoRA). Build with
  `ollama create mymodel -f Modelfile`. Setting context size for the OpenAI API
  *requires* a Modelfile with `PARAMETER num_ctx N` (the `/v1` API can't set it).
- **Structured outputs** (since late 2024): pass a JSON schema to `format`
  (use Pydantic `model_json_schema()` / Zod `zodToJsonSchema()`; set `temperature 0`).
- **Tool calling** with Llama 3.1/3.2, Mistral, Qwen2.5, gpt-oss; streaming tool calls.
- **2025:** new multimodal engine (vision first-class); **native desktop GUI app**
  (macOS/Windows) shipped 2025-07-30; drag-drop PDFs/images.

### llama.cpp — the engine under everything
- C/C++ inference engine; powers Ollama, LM Studio, llamafile, KoboldCpp.
- Consumes **GGUF** (the dominant local quant format; 100k+ GGUF repos on HF).
- **`llama-server`** exposes `POST /v1/chat/completions`, `/v1/completions`,
  `/v1/embeddings`, Anthropic-style `/v1/messages` (with `--jinja`), and a built-in
  web UI (`--no-ui` to disable).
- **Constrained generation:** **GBNF** grammars via the `grammar` param;
  `json_schema` + `response_format` on the chat endpoint.
- **Key flags:** `--model`, `--ctx-size N`, `--n-gpu-layers N` (offload N layers to
  GPU/Metal — the central partial-offload knob), `--host`, `--port`, `--embeddings`,
  `--cache-type-k q8_0` (quantize the KV cache). Python wrapper: `llama-cpp-python`
  ships the same OpenAI server.

### LM Studio — GUI + SDK + MLX backend
- Polished desktop app to discover/download/run models; **local OpenAI-compatible
  server** (Developer tab, REST + `lms` CLI + TS/Python SDKs).
- Ships an **Apple MLX backend** (since v0.3.4) — MLX-accelerated inference on Mac
  behind the same UI/API. JSON-schema structured output supported.

### Apple MLX / MLX-LM — Apple Silicon native
- MLX = Apple's array framework exploiting **unified memory** (CPU+GPU share one pool).
- **`mlx-lm`** Python pkg: `mlx_lm.generate`, `mlx_lm.chat`,
  `mlx_lm.convert --model … -q` (quantize, e.g. 4-bit), and
  **`mlx_lm.server --model … --port 8080`** -> OpenAI-compatible `/v1`.
- `mlx-community` on HF hosts thousands of pre-converted models. **Mac-only**
  (M-series); not Intel Macs.

### MLC-LLM — universal deploy via ML compilation
- Compiler (Apache TVM Unity) -> **MLCEngine**, an OpenAI-compatible engine across
  **REST / Python / JS / iOS / Android**.
- `mlc_llm compile … -o model.wasm` for the browser; native libs for phones.
  **WebLLM is its web backend.** Use when you need one model artifact deployed to
  many targets.

### Long tail (one line each)
- **llamafile** (Mozilla): llama.cpp + **Cosmopolitan Libc** -> a single
  Actually-Portable-Executable running on 6 OSes, no install, weights embedded.
- **GPT4All** (Nomic): zero-setup desktop app, **CPU-friendly**, **LocalDocs**
  RAG-over-files.
- **Jan**: open-source "ChatGPT replacement" UI with **hybrid** local/cloud switching.
- **KoboldCpp**: llama.cpp fork + KoboldAI UI + OpenAI-compatible API; story/roleplay focus.
- **Open WebUI / AnythingLLM / LocalAI**: front-ends/gateways on top of Ollama or any
  `/v1` server (RAG UI, multi-backend). LocalAI also fronts multiple backends/formats.

## Browser & edge runtimes

- **WebLLM** (MLC): high-performance **in-browser** engine, **WebGPU**-accelerated,
  **OpenAI-compatible** JS API (`CreateMLCEngine`), Web Worker support, runs fully
  client-side. `npm i @mlc-ai/web-llm` or CDN. Best for local chat with streaming.
- **Transformers.js v3** (HuggingFace): Python-Transformers API in JS over **ONNX
  Runtime Web** -> **WebGPU** (3-10x the WASM fallback). Best for HF pipelines and
  **in-browser embeddings / RAG**.
- **Chrome Built-in AI / Gemini Nano (Prompt API):** the browser ships **Gemini Nano**.
  **Prompt API is stable for web pages as of Chrome 148** (extensions-only through
  ~138); **Summarizer** stable since 138; **Translator** + **Language Detector**
  stable in 148; **Writer/Rewriter** in origin trial; multimodal input in the Early
  Preview Program. Full GA targeted ~Chrome 150 / end of 2026. No model download for
  the developer — the browser manages weights.
- **Apple Foundation Models framework** (WWDC25, iOS/macOS 26): Swift API to Apple
  Intelligence's **~3B on-device model** (KV-cache sharing + 2-bit QAT). **Guided
  generation** = constrained decoding via the **`@Generable`** macro on Swift
  structs/enums (OS daemon runs constrained + speculative decoding); plus **tool
  calling**. On-device, private, free to the app.
- **Windows AI Foundry / Foundry Local** (Build 2025; evolution of Windows Copilot
  Runtime): **Windows ML** (GA 2025-09) = on-device runtime across CPU/GPU/**NPU**
  (AMD/Intel/NVIDIA/Qualcomm). **Foundry Local** auto-detects hardware, lists
  compatible models, and exposes an **OpenAI-compatible** local endpoint; ships
  Phi-class SLMs (~3.8B) tuned for Copilot+ PC NPUs.

## Mobile runtimes

- **llama.cpp on iOS/Android**: ARM + Metal builds power most third-party local-LLM
  apps (e.g. PocketPal); GGUF models via Swift/Kotlin wrappers.
- **Google MediaPipe LLM Inference**: cross-platform on-device API (Gemma 3n
  E2B/E4B, Phi-2…) using `.task` files; multimodal on Android. **2025 change: the
  Android/iOS implementations are DEPRECATED -> migrate to LiteRT-LM.** The **Web**
  target is not deprecated.
- **ONNX Runtime GenAI** (Microsoft): generative layer over ONNX Runtime; execution
  providers CPU/CUDA/**DirectML**/**QNN**/OpenVINO/WebGPU. Runs Phi-3.5-mini and
  Llama-3.2-3B on **Qualcomm NPUs** (PC + mobile); ~100 ms TTFT (128-token prompt,
  Snapdragon 8 Elite). Pairs with **Qualcomm AI Hub** for precompiled QNN binaries.

## Hardware sizing & quant-level selection

Total memory ≈ **model weights + KV cache + ~0.5-1 GB runtime overhead**.

**Weights = params(B) × bytes-per-weight**, set by the **quant level**:

| Level | ≈ bytes/wt | 7B | 13B | 70B | Quality vs FP16 | Use when |
|---|---|---|---|---|---|---|
| FP16 | 2.0 | ~14 GB | ~26 GB | ~140 GB | baseline | training / max fidelity |
| Q8_0 | ~1.0 | ~8 GB | ~14 GB | ~70 GB | ~99% (near-lossless) | quality-critical, RAM to spare |
| Q6_K | ~0.75 | ~6 GB | ~11 GB | ~54 GB | ~97% | reasoning/code, 20+ GB |
| Q5_K_M | ~0.65 | ~5 GB | ~9 GB | ~47 GB | ~97-98% | 12-16 GB sweet spot |
| **Q4_K_M** | **~0.5-0.55** | **~4-5 GB** | **~8 GB** | **~40 GB** | **~92-95%** | **default; 8-10 GB chat** |
| Q3_K_M | ~0.4 | ~3.5 GB | ~6.5 GB | ~33 GB | noticeably worse | only if desperate |

**Quick formula:** `memory_GB ≈ params_B × bytes_per_weight × 1.2`.
Selection rule (in priority order): **(1) fit your RAM/VRAM ceiling, (2) quality,
(3) speed.** Q4_K_M is the community default; bump to Q5/Q6 for code & reasoning
(they punish aggressive quant); Q8_0 when fidelity matters and it fits. Avoid Q2.
*(How k-quants pack bits / imatrix calibration -> `llm-compression`.)*

**KV cache — the silent long-context killer.** It grows **linearly with context**.
A 70B at 4K ctx ≈ ~2 GB KV; at 128K ctx ≈ ~64 GB **for the cache alone** before
weights. Mitigate with **KV-cache quantization** (`--cache-type-k q8_0`) and
**GQA** (Llama 3.1 8B: 8 KV heads vs 32 query heads -> ~4x smaller cache).

**VRAM-tier cheat sheet (Q4_K_M, ~4K ctx):**
| VRAM/RAM | Comfortably runs |
|---|---|
| 8 GB | 7-8B (RTX 3070/4060, many laptops) |
| 12 GB | 13B (RTX 3060 12 GB) |
| 24 GB | 32-34B; 70B only with partial CPU offload (RTX 3090/4090) |
| 48 GB | 70B Q4 (RTX 6000 Ada / dual 24 GB) |
| 128 GB+ unified (Mac) | 70B+ at higher quant; very large MoE |

When weights exceed VRAM, use **partial offload**: llama.cpp `--n-gpu-layers N`
(GPU layers, rest on CPU) — graceful but slower.

**Apple Silicon vs consumer NVIDIA (the durable frame).** Two philosophies:
- **Apple unified memory** — one large pool (up to 128-512 GB on Max/Ultra), but
  **bandwidth-bound** (~546 GB/s on M4 Max). *Lets large models load that a 24 GB
  card can't hold at all.*
- **NVIDIA discrete VRAM** — faster (~1008 GB/s on RTX 4090), **~2x+ faster per
  token when the model fits**, but **24 GB is a hard wall** — spill to system RAM
  and throughput collapses.

**Takeaway: NVIDIA for speed at sizes that fit; Apple to *run* models that don't
fit a consumer GPU.** Indicative single-stream decode: dense **70B-Q4 ~8-15 tok/s
on an M4 Max** (faster at short context). Treat headline "2,000+ tok/s" figures
with care — those are MoE (few active params) and/or prefill/batched, not dense
decode. For multi-user throughput on one box you eventually outgrow these
single-stream runtimes -> **`llm-inference-serving`**.

## Integration patterns

**Point any OpenAI client at a local server** — same SDK, local `base_url`, dummy key:
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")  # or :8080 (mlx/llama.cpp), :1234 (LM Studio)
resp = client.chat.completions.create(
    model="llama3.1", messages=[{"role": "user", "content": "Hi"}])
```

**Structured output (Ollama, JSON schema):**
```python
from ollama import chat
from pydantic import BaseModel
class Country(BaseModel):
    name: str; capital: str
out = chat(model="llama3.1",
           messages=[{"role": "user", "content": "Tell me about Canada."}],
           format=Country.model_json_schema(), options={"temperature": 0})
Country.model_validate_json(out.message.content)
```

**Grammar-constrained output (llama.cpp GBNF):** pass a `.gbnf` to `llama-server`'s
`grammar` param to force, e.g., valid JSON or a fixed enum — useful when a model
lacks native structured-output support.

**Local embeddings:**
```bash
curl http://localhost:11434/v1/embeddings -d '{"model":"nomic-embed-text","input":"hello"}'
# llama.cpp:  llama-server -m embed.gguf --embeddings   ->  POST /v1/embeddings
```

**In-browser (WebLLM):**
```js
import { CreateMLCEngine } from "@mlc-ai/web-llm";
const engine = await CreateMLCEngine("Llama-3.2-3B-Instruct-q4f16_1-MLC");
const r = await engine.chat.completions.create({ messages:[{role:"user",content:"Hi"}] });
```

**Apple guided generation (Swift):**
```swift
@Generable struct Recipe { let title: String; let steps: [String] }
let session = LanguageModelSession()
let recipe = try await session.respond(to: "A quick pasta recipe", generating: Recipe.self)
```

## Anti-patterns & failure modes

- **Picking quant by name, not by fit.** Always size first (`params × bytes × 1.2`
  + KV). A 70B-Q4 (~40 GB) will *not* fit a 24 GB card without offload.
- **Forgetting the KV cache at long context.** Long-context jobs OOM from the cache,
  not the weights — quantize the KV cache or cut context.
- **Defaulting to Q4 for code/reasoning.** Those workloads degrade visibly; prefer
  Q5/Q6 if you have headroom.
- **Setting context on Ollama's `/v1` API and wondering why it's ignored.** Bake
  `num_ctx` into a Modelfile; the OpenAI-compat layer can't set it.
- **Exposing a local server beyond loopback.** llama.cpp/Ollama default to localhost;
  binding `--host 0.0.0.0` puts an unauthenticated LLM on your LAN. Gate it.
- **Reaching for a local single-stream runtime to serve many users.** Concurrency,
  batching, autoscaling -> `llm-inference-serving` (vLLM/SGLang/TGI), not Ollama.
- **Assuming WebGPU/Built-in AI everywhere.** WebGPU + Chrome Built-in AI gate on
  browser version, OS, and hardware; always feature-detect and fall back.
- **Shipping a now-deprecated mobile path.** MediaPipe LLM on Android/iOS is
  deprecated -> LiteRT-LM; don't start new mobile work on it.
- **Trusting unconditional throughput numbers.** Verify model (dense vs MoE),
  context length, and decode-vs-prefill before quoting tok/s.

## 2025-2026 frontier

- **OpenAI-compat is the lingua franca.** Ollama, llama.cpp, LM Studio, MLX-LM,
  MLC, Foundry Local all expose `/v1` — local<->cloud swap is a `base_url` change.
- **NPUs go mainstream.** Copilot+ PCs (Windows ML/Foundry Local), Snapdragon
  (ONNX Runtime GenAI + QNN), and Apple's Neural-Engine-assisted stack push small
  models onto dedicated low-power silicon.
- **OS-native on-device models.** Apple Foundation Models (~3B, `@Generable`),
  Chrome Gemini Nano (Prompt API), Windows Phi-Silicon — "free," private, zero-download
  models built into the platform.
- **Small-but-capable models.** Gemma 3n (E2B/E4B), Llama 3.2 1B/3B, Qwen2.5,
  Phi-class, gpt-oss — the 1-4B tier is now genuinely useful on-device.
- **Local serving borrows datacenter tricks.** Projects like **vLLM-MLX** bring
  continuous batching / paged-KV to Apple Silicon — when you outgrow single-stream
  local serving, that's the bridge to **`llm-inference-serving`**.
- **Browser inference matures.** WebGPU is broadly shipping; WebLLM + Transformers.js
  make zero-install, fully-private web AI practical for sub-4B models.

## Sources
1. Ollama — OpenAI compatibility / Modelfile / structured outputs / API / multimodal: https://docs.ollama.com/api/openai-compatibility , /modelfile , /capabilities/structured-outputs , https://github.com/ollama/ollama/blob/main/docs/api.md , https://ollama.com/blog/multimodal-models
2. llama.cpp — `llama-server` README: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
3. LM Studio — Local server docs + MLX (v0.3.4): https://lmstudio.ai/docs/developer/core/server , https://lmstudio.ai/blog/lmstudio-v0.3.4
4. Apple MLX-LM: https://github.com/ml-explore/mlx-lm
5. MLC-LLM + WebLLM: https://llm.mlc.ai/docs/get_started/introduction , https://github.com/mlc-ai/web-llm
6. Chrome Built-in AI / Prompt API + I/O '25 status: https://developer.chrome.com/docs/ai/prompt-api , https://developer.chrome.com/blog/ai-api-updates-io25
7. Apple Foundation Models framework + 2025 updates: https://developer.apple.com/documentation/FoundationModels , https://machinelearning.apple.com/research/apple-foundation-models-2025-updates
8. Microsoft Foundry on Windows + Windows ML GA: https://learn.microsoft.com/en-us/windows/ai/overview , https://blogs.windows.com/windowsdeveloper/2025/09/23/windows-ml-is-generally-available...
9. Google AI Edge — MediaPipe LLM Inference (LiteRT-LM migration): https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference
10. Microsoft ONNX Runtime GenAI + Snapdragon/QNN: https://github.com/microsoft/onnxruntime-genai , https://onnxruntime.ai/docs/genai/tutorials/snapdragon.html
11. Mozilla llamafile: https://github.com/mozilla-ai/llamafile
12. GGUF VRAM/memory calculators + quant guide (sizing corroboration): https://ggufvram.radicchio.page/ , https://llmhardware.io/guides/llm-quantization-guide
13. Apple Silicon vs RTX local-LLM benchmarks: https://www.sitepoint.com/mac-m3-max-vs-rtx-4090-local-llm-benchmark/ , https://github.com/XiongjieDai/GPU-Benchmarks-on-LLM-Inference

> Boundary note: quant-algorithm/format internals (GPTQ/AWQ, GGUF k-quant math, imatrix) defer to `llm-compression`; datacenter/multi-GPU serving (vLLM, batching, disaggregation) to `llm-inference-serving`. Quant *levels* (Q4/Q5/Q8) appear here only as a fit/quality knob. Not related: `dexie-indexeddb` (browser storage) and `mongodb-atlas-device-sdk` (Realm sync) — different domains despite "local/device" keyword overlap.
