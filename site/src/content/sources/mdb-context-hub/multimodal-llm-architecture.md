---
title: "Multimodal & Vision-Language Model Architecture"
description: "> Provenance: reference under the ai-agent-engineering hub. Built via /dr deep-research, 2026-05-31. Owns the 'how a text-only transformer becomes multimodal' layer — the vision/audio/video front-end"
---

# Multimodal & Vision-Language Model (VLM) Architecture

> Provenance: reference under the `ai-agent-engineering` hub. Built via /dr deep-research, 2026-05-31. Owns the "how a text-only transformer becomes multimodal" layer — the vision/audio/video front-end and how it fuses into the decoder. EXTENDS `transformer-architecture` to other modalities; the decoder block itself (attention/MoE/RoPE/norm) lives there.

This reference answers one question: **how do you turn a text-only decoder LLM into a model that can see (and hear)?** Every other model-layer reference in the hub (`transformer-architecture`, `llm-pretraining-scaling-laws`, `llm-fine-tuning-peft`, …) is about a text decoder. This one is the **front-end and fusion machinery bolted onto that decoder** so it can consume images, video, and audio.

**The one mental model: the "modality → tokens → residual stream" pipeline.** A decoder LLM only consumes a sequence of `d_model`-dimensional vectors (token embeddings) on its residual stream. So *every* modality must become a sequence of `d_model` vectors that live in the same space as text-token embeddings. Three jobs:

1. **Encode** the raw modality (pixels, audio, frames) into feature vectors — the **vision encoder** (or audio encoder).
2. **Connect / project** those features into the LLM's embedding dimension and (usually) reduce their count — the **connector / projector**.
3. **Fuse** the resulting "visual tokens" with the text tokens so the decoder attends across both — the **fusion strategy**.

Almost the entire VLM zoo is a choice of {encoder} × {connector} × {fusion} × {resolution handling} × {training stages}. The dominant recipe in 2024-2026 is simple: **a SigLIP/CLIP ViT encoder → a 2-layer MLP projector → concatenate visual tokens in front of text tokens → feed one decoder** (the "LLaVA recipe"). Everything else is a variation on, or a deliberate rejection of, that recipe. Scope: image/video/audio **understanding** + the discrete-token **generation** path (Chameleon-style); NOT diffusion/DiT image-generation internals.

## 1. Vision encoders (ViT / CLIP / SigLIP / DINOv2 / EVA)

Nearly all VLMs encode images with a **Vision Transformer (ViT)**: split the image into fixed-size patches (e.g. 14×14 px), linearly embed each patch, add position embeddings, run transformer blocks. A 336×336 image at patch-14 → 24×24 = 576 patch tokens. What matters is *how that ViT was pretrained*:

- **Contrastive image-text (CLIP).** Image + text encoders trained jointly so matching pairs have high cosine similarity (softmax **InfoNCE** over the in-batch similarity matrix). Features are *semantically aligned to language* — what a VLM wants. CLIP ViT-L/14 was the default encoder for years.
- **Sigmoid contrastive (SigLIP / SigLIP 2).** Replaces InfoNCE with a **pairwise sigmoid loss** — each image-text pair is an independent binary match/no-match, so **no global softmax over the batch**. Decouples the loss from batch size (no all-gather of the full matrix), more memory-efficient and stable, **wins at small/medium batch (4k–8k)** while both saturate ~32k. **SigLIP is now the most effective VLM front-end**, beating CLIP- and DINO-based encoders. SigLIP 2 (2025) adds multilingual + self-distillation + masked-prediction and a native-resolution "NaFlex" variant.
- **Self-supervised image-only (DINOv2).** No text; strong *dense/spatial/geometric* features (segmentation, depth) but **not language-aligned** — underperforms alone on VLM language tasks, but a popular *complement* to a contrastive encoder.
- **Masked/reconstructive (EVA, EVA-CLIP).** Masked-image modeling scaled to billion-param ViTs; high-capacity encoder in some large VLMs.

**Mixture-of-encoders:** Eagle (NVIDIA, arXiv 2408.15998) found **concatenating tokens from complementary encoders (CLIP/SigLIP semantics + DINOv2 spatial + OCR-specialized) is as good as complex fusion**, and **stronger perception measurably reduces hallucination** + helps OCR.

**Frozen vs trained:** early VLMs froze the encoder; the 2024-2026 trend trains the ViT (often from scratch, native-resolution) — Qwen2.5-VL and Pixtral train new ViTs. `transformer-architecture` owns the ViT's transformer block; this owns what makes it a vision encoder.

## 2. The connector / projector (MLP vs Q-Former vs cross-attention)

The encoder emits ~576 vectors of dim `d_vis`; the decoder wants `d_model` vectors, ideally fewer (image tokens are expensive KV). The connector does dimension-matching + token-count reduction:

- **Linear / MLP projection (the LLaVA recipe — default).** LLaVA used a linear matrix; LLaVA-1.5 a **2-layer MLP** (GELU). Maps each feature to `d_model`, appended as-is — *no reduction*, 576 → 576 tokens. Simplest, most-copied, works well. Qwen2.5-VL uses an MLP merger that also merges adjacent patches; InternVL uses an MLP after **pixel-shuffle** (448×448 tile 1024 → 256 tokens).
- **Query-based resampler — Q-Former (BLIP-2) / Perceiver Resampler (Flamingo).** Fixed **learnable query vectors** cross-attend to frozen image features and emit a *fixed small* token count. **BLIP-2's Q-Former**: 32 queries → **32 tokens**, bridging a **frozen** encoder + **frozen** LLM (only the Q-Former trains). **Flamingo's Perceiver Resampler**: variable/multi-frame grid → fixed token count. Trade-off: slashes tokens but the bottleneck loses detail — for OCR the field swung *back* to MLP + more tokens + tiling.
- **Gated cross-attention into the decoder (Flamingo, Llama-3.2-Vision).** Insert **new cross-attention layers between self-attention layers**; text queries attend to visual K/V. Flamingo gates each with **`tanh(α)`, α a learnable scalar init 0** — at init a no-op, so the pretrained LLM is unchanged and "opens up" during training (keeps the LLM frozen, stable). Llama-3.2-Vision: ViT-H/14 + adapter + **cross-attention layers into a frozen Llama-3.1**.

**Pick:** MLP-concat = simplest, best detail, most tokens. Resampler = fixed small budget, good for many-image/video/frozen. Cross-attention = keep the LLM frozen, bolt vision on the side.

## 3. Fusion strategy (unified/early-fusion vs cross-attention vs late fusion)

The most important architectural axis — *distinct* from the connector:

- **Unified / decoder-only / channel-concat (dominant).** Project to `d_model`, **concatenate visual tokens into the sequence**: `[<img tokens> <text tokens>]`; the *single* decoder runs full self-attention over both. LLaVA/Qwen-VL/InternVL/Pixtral. Pros: minimal new params, deep every-layer interaction. Cons: image tokens eat context + KV; high-res blows up the sequence (→ tiling). Still **two encoders feeding a shared decoder**, not a single tokenizer (contrast §4).
- **Cross-attention injection (mid fusion, Flamingo/Llama-3.2).** Visual tokens are NOT in the input sequence; new cross-attention layers let text attend to vision. Pros: the text sequence/KV is unchanged — keep the LLM **frozen**, image tokens don't eat the text budget. Cons: more params, interaction only at inserted layers. Meta used it to avoid degrading text-only Llama-3.1.
- **Late fusion (shallow, retrieval).** Encode each modality independently, combine at the end (pooled-embedding similarity, as in CLIP-for-retrieval). Right for multimodal RAG (→ `rag-architecture`), too shallow for generative reasoning.

**Mental model:** unified-concat fuses at the *input* (shares all layers); cross-attention fuses in the *middle* (frozen-LLM friendly); late fusion fuses at the *output* (retrieval, not generation). 2024-2026 consensus = unified-concat with a trained decoder; cross-attention persists where a frozen base LLM matters.

## 4. Native any-to-any & image tokenization (Chameleon, VQ-VAE/VQGAN, Fuyu)

A radical design **drops the separate encoder + connector** by turning images into **discrete tokens from a vocabulary**, like text BPE — one transformer, one vocabulary, can **generate** images too:

- **Discrete image tokenization (VQ-VAE/VQGAN).** A vector-quantized autoencoder (trained separately) maps an image to a grid of latents, each snapped to the nearest **codebook** entry (e.g. 8,192 codes); indices are integer tokens. **Chameleon** (Meta, arXiv 2405.09818) tokenizes a 512×512 image to **1,024 VQ tokens** from an 8,192-code codebook, in the **same vocabulary + embedding table as BPE text tokens**.
- **Early-fusion mixed-modal (Chameleon).** Image and text are the same kind of token, so one decoder trains over interleaved `[text, image, …]` from scratch — no encoder, no projector. Reads and **generates** in any order (true any-to-any image+text). Cost: hard to train at scale (needs QK-norm / norm-placement stabilizers), and discrete tokens cap visual fidelity.
- **Patch-as-token, no encoder, continuous (Fuyu, Adept).** No vision encoder, not discretized — patches pass through a *single linear projection* into the decoder as continuous "tokens"; the decoder does all visual processing. Handles arbitrary resolution trivially; asks the LLM to learn vision from scratch.
- **Native omni frontier.** GPT-4o, Gemini are **natively multimodal** (trained end-to-end across modalities, architectures undisclosed). Documented native paths are discrete-token (Chameleon) + patch-as-token (Fuyu); InternVL's "native multimodal pretraining" interleaves multimodal data *during* pretraining.

**When it matters:** if you need ONE model to understand **and generate** images, the discrete-token/native path is the only single-model option; understanding-only is simpler + higher-fidelity via encoder+MLP.

## 5. High-resolution & dynamic tiling (AnyRes, InternVL tiles, NaViT)

A vanilla CLIP/SigLIP ViT runs at fixed low resolution (224/336) — fails on documents, dense text, charts. Three solutions:

- **AnyRes / tiling (LLaVA-NeXT, InternVL).** Split the image into a **grid of tiles** at native resolution, encode each separately, **plus a downsized thumbnail** for global context, concatenate all tile tokens. LLaVA-NeXT picks a grid from `{2×2, 1×{2,3,4}, {2,3,4}×1}`. InternVL: 1–12 tiles of 448×448 by aspect ratio at train, **zero-shot to ~40 tiles (≈4K) at test**, each pixel-shuffled to 256 tokens. Dominant + simplest; cost is token count.
- **Native-resolution packing — NaViT ("Patch n' Pack", arXiv 2307.06304).** Process each image at native resolution/aspect by borrowing **example packing** from NLP: patches from multiple differently-sized images in one sequence (**masked attention** so images don't cross-attend) + **factorized position embeddings**. No resize/crop loss, no padding waste. Drop-in replacement for fixed-res CLIP.
- **Native dynamic-resolution ViT from scratch (Qwen2-VL/2.5-VL, Pixtral).** Train the ViT to accept variable resolution natively. Qwen2.5-VL adds **2-D RoPE + window attention** (images to multiples of 28, patch stride 14); Pixtral ingests natural resolution/aspect. The cleaner long-term answer.

**Arc:** fixed-336 CLIP → tile a fixed encoder (AnyRes) → train a native-resolution ViT.

## 6. Audio, video, speech (Whisper encoders, audio tokens, frame sampling, omni)

The encode→connect→fuse pipeline generalizes:

- **Audio understanding (Whisper-style).** Waveform → **mel-spectrogram** (~128 channels) → **Whisper-derived encoder** (Whisper-large-v3 common — Qwen2.5-Omni, InteractiveOmni) → audio tokens projected into the LLM like visual tokens. Reuses a strong ASR encoder as the perception module.
- **Speech generation (audio tokens + decoder).** To *speak*, emit **discrete audio tokens** decoded to a waveform. **Qwen2.5-Omni** (arXiv 2503.20215) uses **Thinker-Talker**: the Thinker LLM emits text; a separate Talker consumes the Thinker's text + hidden states and emits audio tokens — streams text + speech concurrently without interference.
- **Video (frame sampling + temporal encoding).** Sample frames (Qwen2.5-Omni ~25 fps/40 ms; many VLMs 1–2 fps or N frames), encode each, compress per-frame tokens (resampler/merging), add **temporal position** (M-RoPE). Qwen2.5-VL adds **absolute time encoding** for second-level localization over hour-long video. Central tension: the **token budget** (more frames = quadratic cost → resamplers + frame-rate tuning).
- **Native omni:** GPT-4o + Gemini are natively multimodal across text/vision/audio (GPT-4o does native end-to-end audio, not Whisper→LLM→TTS).

## 7. Multimodal position encoding (2-D RoPE, M-RoPE)

A text RoPE (→ `transformer-architecture` for the base mechanism) encodes a **1-D** position — wrong for an image (row, column) and video (+ time):

- **2-D RoPE in the vision encoder.** From-scratch ViTs (Qwen2.5-VL, Pixtral) apply a **2-D rotary embedding** to patches so attention knows each patch's spatial (h, w) position — needed once resolution/aspect vary (no fixed learned table for arbitrary grids).
- **M-RoPE in the decoder (Qwen2-VL, arXiv 2409.12191).** **Decomposes the rotary embedding into three components — temporal, height, width** — so one scheme encodes 1-D text, 2-D image, 3-D video positions concurrently. Text uses all three identically (→ standard 1-D RoPE); image varies h/w at fixed time; video advances time across frames. Also **helps length extrapolation** (an image's position ids span a 2-D region, keeping numeric ids small). Common in unified-fusion VLMs (Qwen2.5-VL/Qwen3-VL).

**Why:** get this wrong and the model reads an image but can't reason about *where* ("is the cat left of the dog?", "top-right table cell?"). M-RoPE is the cheap fix for spatial grounding.

## 8. VLM training stages (projector-align → visual instruction tuning → multimodal preference/DPO)

The canonical **multi-stage recipe** (LLaVA) — about *which component is frozen/trained per stage*, not LoRA mechanics (→ `llm-fine-tuning-peft`) or preference-loss math (→ `llm-alignment-post-training`):

1. **Stage 1 — projector / feature alignment.** **Freeze encoder + LLM, train only the connector** on image-caption pairs (LLaVA: CC3M subset). Teaches the projector to map visual features into the LLM's space. Cheap, fast.
2. **Stage 2 — visual instruction tuning (the "SFT" of VLMs).** **Unfreeze the LLM** (often projector; sometimes encoder) and train on multimodal instruction data — (image, instruction, response) triples (VQA, OCR, reasoning, grounding). LLaVA *generated* this data by prompting text-only GPT-4 with captions/boxes. Turns a captioner into an instruction-follower. Modern recipes add an encoder high-res stage; "native multimodal pretraining" folds multimodal data into base pretraining.
3. **Stage 3 — multimodal preference / alignment (hallucination reduction).** RLHF or **DPO** with *multimodal* preference data to cut **hallucination** (#1 VLM failure) + improve helpfulness. **LLaVA-RLHF / Fact-RLHF** (arXiv 2309.14525): ~10k human prefs over which response is *more hallucinated*, **Factually-Augmented RLHF** feeds the reward model ground-truth (captions/boxes) so it isn't fooled by fluent-but-wrong answers; improves MMHal-Bench. Trend → **mDPO** + self-rewarding (M3PO). The multimodal wrinkle: **a naive text-only DPO can ignore the image** — mDPO adds image-contrastive terms to force visual conditioning.

**Why staged:** Stage 1 protects pretrained weights while the random projector finds its footing; Stage 2 builds capability; Stage 3 buys trustworthiness. Skip Stage 1 → destabilize; skip Stage 3 → capable but hallucination-prone.

## 9. The VLM landscape (architectural map, mid-2026)

Read as *what front-end + connector + fusion + resolution each uses* (→ `llm-models` for selection/pricing):

| Model | Vision front-end | Connector | Fusion | Resolution | Notable |
| --- | --- | --- | --- | --- | --- |
| CLIP / SigLIP / SigLIP 2 | (these *are* encoders) | — | late (retrieval) | fixed (SigLIP2 NaFlex native) | SigLIP now preferred over CLIP for VLMs |
| Flamingo (2022) | frozen CLIP-style | Perceiver Resampler | gated cross-attention | fixed | Originated `tanh(α)`-gated cross-attn |
| BLIP-2 (2023) | frozen ViT | Q-Former (32→32) | unified-concat (frozen LLM) | fixed | Frozen-encoder + frozen-LLM bridge |
| LLaVA / 1.5 / NeXT | CLIP ViT-L/14 | linear → 2-layer MLP | unified-concat | 336 → AnyRes tiling | Defined the dominant recipe + instruction tuning |
| Qwen2-VL / 2.5-VL / 3-VL | native-res ViT from scratch (2-D RoPE, window attn) | MLP merger | unified-concat + M-RoPE | native dynamic | Variable res, hour-long video + absolute time |
| InternVL (1.5/2.5/3) | InternViT (large) | MLP after pixel-shuffle (¼) | unified-concat | dynamic tiling (1–12 → ~40, 4K) | "ViT-MLP-LLM"; v3 native MM pretraining |
| Llama-3.2-Vision (2024) | ViT-H/14 | MLP/adapter | gated cross-attention into frozen Llama-3.1 | tiling | Cross-attn to preserve text-only quality |
| Pixtral 12B (2024) | new encoder from scratch, native | MLP | unified-concat | native | Beats larger models; OCR strength |
| Chameleon (2024) | none (VQ-VAE tokens) | none (shared vocab) | early-fusion, single tokenizer | fixed (512→1024 tok) | True any-to-any image+text generation |
| Fuyu (Adept) | none (linear patch proj) | linear | unified-concat (patches as tokens) | arbitrary | No encoder; decoder does all vision |
| Qwen2.5-Omni | Whisper-v3 audio + ViT | projectors | unified-concat + Thinker-Talker | dynamic | Audio in + streaming speech out |
| GPT-4o / Gemini | undisclosed, natively multimodal | — | native | native | Reference points for "native" |

**Arc:** Flamingo (cross-attn, frozen) → BLIP-2 (Q-Former, frozen everything) → **LLaVA (MLP-concat, the recipe that won)** → tiling for high-res → **native-resolution from-scratch encoders (Qwen2.5-VL, Pixtral)** for understanding, and **Chameleon/native-omni** for any-to-any generation.

## 10. Multimodal evaluation & hallucination (MMMU, MMBench, DocVQA, MathVista, POPE/MMHal)

Standard 2024-2026 suite (OpenVLM Leaderboard, run via **VLMEvalKit**, arXiv 2407.11691):

- **MMMU** (CVPR 2024) — college-level, **30 subjects**, domain knowledge + figure/chart reading. The headline "is this VLM smart" exam; far from saturated.
- **MMBench** — bilingual EN/CN, perception/reasoning/knowledge across fine-grained dimensions; circular-eval / answer-shuffling to reduce guessing.
- **DocVQA** — QA over **document images** (forms, tables, scans). The OCR / high-res stress test.
- **MathVista** — **math reasoning in visual contexts** (charts, plots, geometry, IQ figures); IQTest/FunctionQA/PaperQA.
- **Hallucination — POPE, H-POPE, MMHal-Bench.** **POPE** (Polling-based Object Probing) asks yes/no "is there a <object>?" and shows VLMs **confirm frequently-co-occurring objects that aren't present** (a chair when there's a table). H-POPE → attributes. MMHal-Bench scores open-ended hallucination. *Better perception (resolution, mixture-of-encoders) reduces it* (Eagle).

**Hygiene:** benchmark **contamination** inflates scores; many are **multiple-choice** so report protocol (shuffling, MCQ vs free-form). Offline *general* harness mechanics (HELM/MMLU/LLM-as-judge) → `da-analytical-methods` (`references/da-7-machine-learning.md`); VLM-specific benchmarks + hallucination evals are here.

## Practical patterns

- **Default image-understanding build:** SigLIP(2) ViT → 2-layer MLP → unified-concat → AnyRes tiling → 3-stage training (align → instruction-tune → mDPO). The reliable recipe; deviate only for a reason.
- **Keep a frozen great text LLM:** gated cross-attention (Flamingo/Llama-3.2).
- **Many images / video / tight token budget:** resampler (Q-Former/Perceiver) or token-merging/pixel-shuffle; tune frame rate explicitly.
- **Generate images/audio too:** discrete-token/native (Chameleon; Thinker-Talker for speech) — accept harder training + lower fidelity.
- **OCR/documents/charts:** prioritize **resolution** (native-res ViT or many tiles, keep tokens — don't use a 32-token resampler); consider a mixture of encoders.
- **Fighting hallucination:** improve perception first, then Stage-3 mDPO/Fact-RLHF; evaluate with POPE + MMHal, not just MMMU.

## Anti-patterns

- **Over-compressing visual tokens for detail tasks** (a 32-token Q-Former can't read a dense table).
- **Reusing fixed-336 CLIP for documents** (loses small text — tile or use native-resolution).
- **Pure-DINO as the *sole* front-end** (strong spatial, weak language alignment — pair with a contrastive encoder).
- **Skipping Stage-1 projector alignment** (random projector + unfrozen LLM destabilizes).
- **Text-only DPO on a VLM expecting less hallucination** (the loss can be met without using the image — use image-aware signals: Fact-RLHF, mDPO).
- **Treating image tokens as free** (high-res images are hundreds-to-thousands of tokens; dominate context + serving cost → `llm-inference-serving`).
- **Benchmarking only on MMMU** (always add a hallucination probe POPE/MMHal + an OCR test DocVQA).

## Troubleshooting

- **Captions fine but can't read in-image text** → resolution. Add AnyRes tiling or native-resolution; verify no downscale to 336.
- **Can't reason about spatial relations** → position encoding. Ensure 2-D RoPE in the encoder + M-RoPE in the decoder; check visual tokens aren't collapsed to 1-D positions.
- **Invents objects/attributes** → hallucination. Improve perception, add Stage-3 image-aware preference optimization, eval with POPE/H-POPE/MMHal.
- **Diverges when unfreezing everything** → run Stage-1 projector alignment first; for unified-from-scratch (Chameleon) use QK-norm / norm-placement stabilizers + careful LR.
- **Video OOMs / too slow** → token budget. Lower frame rate/count, add a resampler or token-merging, pixel-shuffle per-frame tokens.
- **Added vision, text-only quality dropped** → unified-concat fine-tuning erodes text skills; use cross-attention into a frozen LLM (Llama-3.2), or mix text-only data back into instruction tuning.

## Cross-references (ai-agent-engineering hub)

- **Text decoder block** (attention/MoE/RMSNorm/residual stream, *text* RoPE/ALiBi/YaRN, FlashAttention as architecture) → `transformer-architecture`. This reference **extends** it to other modalities (same decoder + vision/audio front-end + M-RoPE).
- **Visual-instruction-tuning LoRA/QLoRA mechanics** → `llm-fine-tuning-peft`. Training *stages* here; *adapter mechanics* there.
- **Preference-optimization algorithm internals** (DPO/PPO/DPO-variant family, reward modeling) → `llm-alignment-post-training`. *Multimodal* preference / Fact-RLHF / mDPO as a stage here; the algorithm there.
- **Serving a VLM** (vLLM/SGLang multimodal, paged KV for image tokens) → `llm-inference-serving`.
- **CLIP/SigLIP as a retrieval index, multimodal RAG** → `rag-architecture`, `ai-datastores`. Here CLIP/SigLIP are the generative front-end, not a retrieval embedder.
- **Pretraining objectives / scaling laws** for the base text model → `llm-pretraining-scaling-laws`.
- **Which VLM to pick** (capabilities/pricing/limits) → `llm-models`.

## References (2024-2026 primary papers + model cards)

- CLIP — Radford et al., OpenAI 2021 (contrastive image-text encoder).
- SigLIP — Zhai et al., Google 2023, arXiv 2303.15343; SigLIP 2 — DeepMind 2025 (multilingual + self-distillation + NaFlex).
- Surveys — arXiv 2501.02189 (SOTA Large VLMs), arXiv 2504.09724 (Efficient VLMs), arXiv 2510.09586 (26K-paper survey), Jina AI vision-encoder survey.
- Flamingo — Alayrac et al., DeepMind 2022 (Perceiver Resampler + tanh-gated cross-attention).
- BLIP-2 — Li et al., Salesforce 2023 (Q-Former, 32 queries).
- LLaVA / 1.5 — Liu et al., NeurIPS 2023; LLaVA-NeXT — llava-vl.github.io 2024 (AnyRes).
- LLaVA-RLHF / Fact-RLHF — Sun et al., arXiv 2309.14525.
- Chameleon — Meta, arXiv 2405.09818 (VQ-VAE discrete tokens, shared vocab, any-to-any).
- Fuyu — Adept, Fuyu-8B model card (linear patch projection, no encoder).
- NaViT — Dehghani et al., Google, arXiv 2307.06304 (native-resolution packing).
- Qwen2-VL — Wang et al., arXiv 2409.12191 (M-RoPE); Qwen2.5-VL — arXiv 2502.13923 (native-res ViT, window attn, absolute time); Qwen3-VL — arXiv 2511.21631.
- Qwen2.5-Omni — arXiv 2503.20215 (Whisper-v3 audio, Thinker-Talker speech).
- InternVL — InternVL 1.5 (internvl.github.io) + InternVL 2.5 arXiv 2412.05271 (ViT-MLP-LLM, pixel-shuffle, dynamic tiling).
- Pixtral 12B — Mistral, arXiv 2410.07073 (from-scratch native-resolution encoder).
- Llama-3.2-Vision — Meta 2024 (cross-attention adapter into frozen Llama-3.1).
- Eagle — NVIDIA, arXiv 2408.15998 (token-concat ≈ complex fusion; perception reduces hallucination).
- Benchmarks — MMMU (CVPR 2024), MathVista, DocVQA, MMBench, POPE + H-POPE (arXiv 2411.04077), MMHal-Bench, VLMEvalKit (arXiv 2407.11691) + OpenVLM Leaderboard.
- GPT-4o / Gemini — OpenAI / Google model cards (natively-multimodal "omni"; architectures undisclosed).
