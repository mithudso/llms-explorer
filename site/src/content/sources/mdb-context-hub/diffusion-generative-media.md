---
title: "Diffusion & Generative-Media Models"
description: "The model family that generates continuous media (images, video, audio) by learning to reverse a noising process. A model-layer reference under the ai-agent-engineering hub (2024–2026). This is the ge"
---

# Diffusion & Generative-Media Models — Image / Video / Audio

The model family that **generates** continuous media (images, video, audio) by learning to reverse a noising process. A model-layer reference under the `ai-agent-engineering` hub (2024–2026). This is the *generation* side and is deliberately separate from `multimodal-llm-architecture` (which is media **understanding** — vision encoders, VLMs) and from `da-35-synthetic-data-generation` (which is **tabular** synthesis). When the task is "make a picture/video/sound," it lives here.

## 1. The denoising-diffusion core (DDPM)

A forward process gradually adds Gaussian noise to data over T steps until it is ~pure noise; a neural network learns the **reverse** (denoising) process. Training minimizes a simple objective: predict the noise added at a random timestep.

- **Parameterizations**: predict the noise **ε** (DDPM), the data **x₀**, or the **v** (velocity) target. **v-prediction** is preferred at high noise/high resolution and for distillation stability.
- **Noise schedule**: linear, cosine (Nichol & Dhariwal — better for high-res), or the continuous σ-space of EDM. The schedule controls how SNR decays and matters a lot for quality.
- DDPM is the foundation; everything below is either a faster *sampler*, a better *parameterization/space*, a better *architecture*, or a *control* method on top.

## 2. The score-based / SDE view

Song & Ermon's score-based generative models unified diffusion under stochastic differential equations: the reverse process integrates the **score** (∇ₓ log p(x)) learned by the network.

- **VP-SDE** (variance-preserving ≈ DDPM) and **VE-SDE** (variance-exploding ≈ NCSN).
- The **probability-flow ODE**: a deterministic ODE with the same marginals as the SDE — enables fast deterministic sampling and exact likelihoods, and is the bridge to flow matching.
- **EDM (Karras et al.)**: a cleaner design space — σ-parameterized noise, preconditioning of network in/out, and the Heun sampler; "EDM2" refines training dynamics. EDM's framing is the modern default mental model.

## 3. Latent diffusion (why almost everything runs in latent space)

Pixel-space diffusion is expensive. **Latent Diffusion (Rombach et al. → Stable Diffusion)** runs the diffusion process in the compressed latent space of a pretrained **VAE**: encode image → diffuse/denoise the latent → decode. This cut compute ~10–100× and made open text-to-image practical. The VAE's quality (and its KL/VQ regularization) bounds the system's fidelity; the denoiser is conditioned on text via cross-attention to a text encoder (CLIP/T5).

## 4. Architectures: UNet → Diffusion Transformer

- The original denoiser is a **UNet** (conv encoder–decoder + skip connections + attention at low resolutions).
- **Diffusion Transformer (DiT)** replaces the UNet backbone with a transformer over latent patches — better scaling with parameters/compute, variable-length handling, and reuse of LLM-stack techniques. DiT is now dominant for frontier models.
- **MMDiT** (multimodal DiT, SD3) runs separate but interacting streams for text and image tokens; **FLUX** is a large rectified-flow DiT. The throughline: frontier image/video models are DiTs trained with flow matching (next section).

## 5. Flow matching & rectified flow

A simpler, often-superior alternative training framework that has largely won at the frontier:

- **Continuous Normalizing Flows / Flow Matching (Lipman et al.)**: regress a time-dependent **velocity field** that transports noise to data along a probability path. **Conditional FM** makes the objective tractable (regress to a per-sample conditional velocity).
- **Rectified Flow (Liu et al.)**: learn **straight** transport paths between noise and data — straighter paths integrate in fewer steps. **Reflow** iteratively straightens.
- **Stochastic interpolants** generalize diffusion + FM under one theory.
- FM/RF improve sample quality and few-step generation and are the training objective behind **SD3** and **FLUX**. **Diff2Flow** (CVPR 2025) shows diffusion and FM are close enough to fine-tune a diffusion prior *as* an FM model by rescaling timesteps — evidence of the paradigms' convergence.

## 6. Guidance — classifier & classifier-free

- **Classifier guidance** (Dhariwal & Nichol) steers sampling with a separate classifier's gradient.
- **Classifier-free guidance (CFG)** (Ho & Salimans) is the workhorse: jointly train conditional + unconditional (drop the prompt p% of the time), then at sampling extrapolate `ε = ε_uncond + s·(ε_cond − ε_uncond)`. The **guidance scale s** trades prompt-adherence vs diversity/fidelity; **negative prompts** put content in the unconditional branch to push it away.
- Costs/caveats: CFG **doubles** per-step compute (two evals); high s over-saturates — hence **CFG rescaling** (Lin et al.) and guidance-distillation (§8) to fold CFG into one eval.

## 7. Samplers / schedulers (the steps↔quality knob)

The sampler numerically integrates the reverse ODE/SDE; fewer steps = faster but lower quality:

- **DDIM** — deterministic, non-Markovian; enables 20–50-step sampling and latent interpolation/inversion.
- **DPM-Solver / DPM-Solver++** — high-order ODE solvers; good quality at ~10–20 steps (a common default).
- **Euler / Euler-a / Heun**, **UniPC**, **Karras σ schedule** for step spacing.
- Rule of thumb: solver choice + step count + schedule jointly set the speed/quality frontier *before* you reach for distillation.

## 8. Few-step generation & distillation

Pushing from ~20–50 steps down to 1–4:

- **Consistency Models (Song et al.)** — learn a function mapping any point on a trajectory directly to its origin; sample in 1–2 steps. **Latent Consistency Models (LCM)** bring this to Stable Diffusion; **LCM-LoRA** is a plug-in accelerator.
- **Distillation families**: **progressive distillation** (halve steps repeatedly), **guidance distillation** (bake CFG into one eval), **consistency distillation**, **adversarial** (**ADD/SDXL-Turbo**, **LADD** latent ADD) for 1–4-step high-quality, and **sCM** (score-regularized continuous-time consistency) for large-scale.
- **Video**: **TurboDiffusion** (ShengShu/Tsinghua, 2025) reports **~100–200× end-to-end speedups** via step distillation (rCM) + low-bit SageAttention/sparse-linear attention + W8A8 — enabling near-real-time video.

## 9. Conditioning & control (the six levers)

Customizing/conditioning a frozen or lightly-tuned base model:

- **ControlNet** — clones the encoder to add **spatial** conditioning (edges, depth, pose, segmentation) while locking the pretrained backbone.
- **T2I-Adapter** — lighter-weight spatial conditioning.
- **IP-Adapter** — **image-prompt** (reference-image) style/content conditioning via decoupled cross-attention.
- **DreamBooth** — fine-tune on a few images to bind a subject to a token (with class-preservation loss).
- **LoRA** — low-rank adapters for cheap style/subject fine-tuning (the dominant community method); composable.
- **Textual Inversion** — learn a new embedding ("a new word") for a concept without touching weights.
- (Note: LoRA/DreamBooth **for diffusion** live here; LoRA/PEFT for **LLM text** is `llm-fine-tuning-peft`.)

## 10. Text-to-video & the video-diffusion stack

- **Architecture**: latent video DiT with **spatiotemporal attention** (full 3D, or factorized spatial+temporal); a 3D/causal VAE compresses time as well as space. Conditioning and CFG carry over from image diffusion.
- **The hard problem is temporal consistency** (flicker, identity drift, motion coherence) and cost (sequence length explodes with frames).
- **Landscape (2025–26)**: closed — **Sora/Sora 2**, Google **Veo 2/3**, **Kling**, **Runway Gen-3**, **Pika**, **Luma**, Minimax/Hailuo. Open — **CogVideoX**, **Mochi-1**, **HunyuanVideo**, **Wan** (Wan2.x), **LTX-Video/LTX-2**, Allegro. Diffusers documents the open stack.
- **Control for video**: WanVideo + ControlNet, image-to-video conditioning, motion LoRAs.

## 11. Audio, music & other modalities (brief)

Diffusion also drives **audio/music** generation (e.g. Stable Audio, audio latent diffusion) and **3D/robotics** (diffusion policies for manipulation). The same core — denoise in a learned latent, condition via cross-attention, guide with CFG — transfers across modalities. Deep audio/music modeling is out of scope here; this is the connective overview.

## 12. Evaluation & efficiency

- **Image**: **FID** (Fréchet Inception Distance — distribution match), **CLIPScore** (prompt alignment), **FID-CLIP** trade-off curves, increasingly **human-preference** models (PickScore, ImageReward, HPS).
- **Video**: **FVD** (Fréchet Video Distance), **VBench** dimensions (temporal flicker, motion, subject consistency), human eval.
- **Efficiency** is its own active survey area (TMLR/TPAMI 2025 efficient-diffusion surveys): architecture, sampler, distillation, and quantization axes — know which axis you're optimizing before reaching for the next trick.

## When to reach for which

| Goal | Reach for |
| --- | --- |
| Understand the math | DDPM → score-SDE/EDM → flow matching/rectified flow |
| Train/choose a frontier image model | latent diffusion + **DiT/MMDiT** + **flow matching** (SD3/FLUX class) |
| Faster sampling, no retrain | better **sampler** (DPM-Solver++) + fewer steps + CFG tuning |
| 1–4-step generation | **LCM/LCM-LoRA**, ADD/**SDXL-Turbo**, consistency/guidance **distillation** |
| Control the output | spatial → **ControlNet**; reference image → **IP-Adapter**; subject → **DreamBooth/LoRA**; concept → **textual inversion** |
| Generate video | spatiotemporal **DiT** + 3D VAE; pick from the open/closed landscape; budget for temporal consistency |
| Score results | image **FID/CLIPScore/human-pref**; video **FVD/VBench** |

## Sources

- *Efficient Diffusion Models: A Survey* — TMLR 2025 (AIoT-MLSys-Lab); *Efficient Diffusion Models* — TPAMI 2025 (TsinghuaC3I)
- *Video Diffusion Models Survey* (2025); HuggingFace, *State of open video generation models in Diffusers*
- *Diff2Flow: Training Flow Matching Models via Diffusion Model Alignment* — CVPR 2025 (CompVis)
- *On Distillation of Guided Diffusion Models* — arXiv 2210.03142; *Large-Scale Diffusion Distillation via Score-Regularized Continuous-Time Consistency (sCM)* — arXiv 2510.08431
- *TurboDiffusion: Accelerating Video Diffusion Models by 100–200×* — arXiv 2512.16093 (ShengShu / Tsinghua)
- *Six Ways to Control Style and Content in Diffusion Models* — Towards Data Science; *Understanding and Training IP-Adapters* — Mercity Research
- *Adaptive Video Distillation: Mitigating Oversaturation and Temporal Collapse* — arXiv 2603.21864
- Foundational (pre-cutoff canon): DDPM (Ho 2020), score-SDE (Song 2021), Latent Diffusion/Stable Diffusion (Rombach 2022), CFG (Ho & Salimans 2022), EDM (Karras 2022), Rectified Flow (Liu 2022), Flow Matching (Lipman 2023), Consistency Models (Song 2023), DiT (Peebles & Xie 2023), SD3/MMDiT (Esser 2024)
