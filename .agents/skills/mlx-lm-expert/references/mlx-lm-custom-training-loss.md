<!-- hub-reference-banner -->
> **Reference file — part of the `mlx-lm-expert` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/mlx-lm-custom-training-loss-20261023`.

---
name: mlx-lm-custom-training-loss
description: "Explain MLX-LM loss primitives and custom Python training loss hooks. TRIGGER: KL or JS distillation kernels; custom loss callable; DWQ parameter selection. SKIP: complete teacher/student or reward-training orchestration -> mlx-lm-expert (references/mlx-lm-external-post-training.md)."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
whenToUse:
  - "MLX-LM custom training losses"
keywords: ["mlx-lm", "Apple silicon", "generation", "training", "compatibility", "source contracts", "version pinning", "limitations"]
tags: ["mlx-lm", "research"]
provenance: "/dr · ~/.global-ai-hub/research/mlx-lm-custom-training-loss-20261023"
---

# MLX-LM distillation loss kernels and custom training loss

## Overview

MLX-LM's Python tuner accepts a caller-supplied loss callable, and its tuner loss module contains KL and Jensen-Shannon objectives with custom Metal forward and backward kernels plus a non-Metal fallback. The trainer autodifferentiates the callable, but this hook is distinct from a general teacher/student distillation pipeline. Upstream uses teacher-reference KL in dynamic quantization sensitivity estimation, while an open feature request asks for general structural knowledge distillation. The distinction matters because a loss function supplies an objective and gradients; teacher logits, token alignment, masking, and rollout orchestration require separate code or a higher-level extension.

## Core Concepts

### MLX-LM distillation loss kernels and custom training loss

- The current MLX-LM tuner loss module implements `kl_div_loss` and `js_div_loss` using `mx.fast.metal_kernel` forward kernels and hand-written VJPs registered with `mx.custom_function`; it uses composed MLX loss operations when Metal is unavailable. The dynamic quantization implementation imports and calls `kl_div_loss`. verified-as-of: 2026-10-23[^c1-2][^c1-3]
- An upstream issue opened on 2026-09-17 asks for a native general structural knowledge-distillation framework. This is scoped: MLX-LM already has low-level KL/JS loss kernels and uses teacher-reference KL in quantization sensitivity estimation, but its generic trainer hook is not itself a general teacher/student training pipeline. (two sources) verified-as-of: 2026-10-23[^c1-5][^c1-1][^c1-3][^c1-2]
- In the source snapshot checked on 2026-10-23, `mlx_lm.tuner.losses` implements per-last-axis KL and JS losses with custom Metal forward and backward kernels when `can_run_metal()` is true; `kl_div_loss` otherwise normalizes both logits with log-sum-exp and calls `mlx.nn.losses.kl_div_loss` with no reduction. verified-as-of: 2026-10-23[^c1-2][^c1-10]
- MLX-LM's DWQ path uses teacher logits computed on demand or optionally precomputed top-logit targets, and computes KL between the quantized model's logits and those targets. dwq_quantize explicitly unfreezes scales and biases on affine quantized layers below 8 bits, then optimizes the full model.trainable_parameters() collection; exclusivity to those scales and biases depends on which other parameters were already frozen. This is teacher-guided quantization fine-tuning rather than general student-architecture distillation. verified-as-of: 2026-10-23[^c1-4][^c1-5][^c1-11]

## Tools & Frameworks

- `mlx_lm.tuner.trainer.train` and `evaluate` accept a `loss` callable that defaults to masked next-token cross-entropy; training differentiates the callable with `nn.value_and_grad(model, loss)`, and the callable returns a loss value and token count. This is a Python-level custom-loss hook; separate teacher loading and rollout orchestration are supplied by caller or external code. verified-as-of: 2026-10-23[^c1-1][^c1-9] _(MLX-LM distillation loss kernels and custom training loss)_

## Methodology

- MLX's `value_and_grad` pattern differentiates a scalar objective. In its pipeline-training example, Matt Beton uses `sum(output * stop_gradient(upstream_gradient))` as an auxiliary scalar for intermediate-stage backpropagation; MLX-LM's KL kernel similarly provides an explicit VJP for its custom Metal computation. (two sources)[^c1-6][^c1-2] _(MLX-LM distillation loss kernels and custom training loss)_
- The Metal `kl_div_loss(logits_q, logits_p)` path computes KL(softmax(logits_p) || softmax(logits_q)) and returns a gradient for `logits_q` but zeros for `logits_p`. AutoContext documents its on-policy distillation objective as reverse KL(student || teacher), so callers must account for this gradient direction instead of assuming the helper directly implements that reverse-KL objective. (two sources) verified-as-of: 2026-10-23[^c1-2][^c1-9] _(MLX-LM distillation loss kernels and custom training loss)_

## Practical Patterns

- `kl_div_loss(logits_q, logits_p)` returns one loss value per position (`logits_q.shape[:-1]`); its custom VJP computes a gradient for `logits_q` and returns zeros for `logits_p`. MLX-LM's dynamic quantization sensitivity path computes targets with the original model and differentiates the quantized model against them, using the second KL input as fixed reference logits. verified-as-of: 2026-10-23[^c1-2][^c1-3] _(MLX-LM distillation loss kernels and custom training loss)_
- Independent MLX-related implementations document higher-level distillation patterns: MLXSmith separates offline teacher-generated SFT from online preference distillation, while `mlx-go-lm` exposes weighted cross-entropy/KL/JS terms and APIs for precomputing teacher logits. (two sources) verified-as-of: 2026-10-23[^c1-7][^c1-8] _(MLX-LM distillation loss kernels and custom training loss)_
- An open MLX-LM issue filed on 2026-09-17 describes DWQ as present but general structural knowledge distillation as missing, and proposes off-policy distillation followed by on-policy rollouts. The issue page showed no maintainer response when checked on 2026-10-23, so it records a user request rather than a repository roadmap commitment. (two sources) verified-as-of: 2026-10-23[^c1-5][^c1-4] _(MLX-LM distillation loss kernels and custom training loss)_
- Independent MLX tooling documents broader distillation orchestration: MLXSmith describes offline teacher-generated responses followed by student SFT and online preference distillation using student-generated candidates, teacher scoring, and an importance-sampled loss; AutoContext describes an in-process path with student rollouts, a frozen teacher, and per-token reverse KL. These are external workflows, not evidence of a built-in MLX-LM teacher-student trainer. verified-as-of: 2026-10-23[^c1-7][^c1-9][^c1-1] _(MLX-LM distillation loss kernels and custom training loss)_
- Tentative: kl_div_loss(logits_q,logits_p) and js_div_loss(logits_q,logits_p) take unnormalized logits with vocabulary on the last axis; normalization is internal. Their public results omit that vocabulary axis and retain the preceding batch/token positions, so the caller supplies token masking and reduction rather than expecting a scalar training loss. The Metal custom VJPs compute the logits_q gradient and explicitly return zeros_like(logits_p) for the target gradient. verified-as-of: 2026-10-23[^c1-13] _(MLX-LM distillation loss kernels and custom training loss)_
- Tentative: trainer.default_loss uses inputs=batch[:,:-1] and targets=batch[:,1:]. It constructs one-based token positions and includes only lengths[:,0] <= position <= lengths[:,1], multiplies per-token cross-entropy by that mask, and returns the float32 sum divided by ntoks together with ntoks=mask.sum(). This is the literal supplied-boundary rule, not a guarantee that every padded target is excluded: iterate_batches records an L-token sequence with upper length L, so when that row is padded, shifted target position L (original index L, the first padding token) is still included by the inclusive upper comparison. verified-as-of: 2026-10-23[^c1-14] _(MLX-LM distillation loss kernels and custom training loss)_
- Tentative: A Python caller supplies train(...,loss=my_loss). train builds nn.value_and_grad(model,loss), then invokes it as loss_value_and_grad(model,*batch); the standard batch iterator yields (token_batch,lengths), so my_loss receives (model,token_batch,lengths) and must return (scalar_loss,token_count). The scalar drives differentiation; token_count supports reporting and weighted evaluation. verified-as-of: 2026-10-23[^c1-14] _(MLX-LM distillation loss kernels and custom training loss)_
- At 0d4d3d04f8ab, the native mlx_lm.lora CLI parser exposes fine-tuning and optimizer settings but no generic teacher/student or custom-loss selector. Its train_model call invokes train without overriding loss, so the default next-token objective applies. A general distillation workflow must supply teacher loading, targets, alignment and a custom Python loss/integration; low-level KL/JS primitives or the separate DWQ path do not establish such a CLI workflow. (two sources) verified-as-of: 2026-10-23[^c1-12][^c1-14] _(MLX-LM distillation loss kernels and custom training loss)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

_(none recorded)_

## Disagreements & Open Questions

- Disagreement (MLX-LM distillation loss kernels and custom training loss): Issue 1900 describes the lack of a native general KD framework, while current MLX-LM code includes KL/JS kernels and teacher-reference KL in a quantization sensitivity workflow. These statements differ in scope: low-level or quantization-specific KL support is not a general structural distillation trainer.[^c1-5][^c1-2][^c1-3]
- Open (MLX-LM distillation loss kernels and custom training loss): The MLX-LM loss implementation establishes the KL argument and gradient direction, but no public docstring in the inspected file explains that orientation for callers.
- Open (MLX-LM distillation loss kernels and custom training loss): The checked sources do not provide performance benchmarks for these kernels across vocabulary sizes, Metal devices, or fallback backends.
- Open (MLX-LM distillation loss kernels and custom training loss): Whether MLX-LM maintainers adopt or reject the general distillation proposal in issue 1900 remains unresolved.

## References

### MLX-LM distillation loss kernels and custom training loss

[^c1-1]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/trainer.py — MLX-LM tuner trainer implementation (repo)
[^c1-2]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/losses.py — MLX-LM tuner KL and JS loss kernels (repo)
[^c1-3]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/quant/dynamic_quant.py — MLX-LM dynamic quantization sensitivity implementation (repo)
[^c1-4]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/quant/dwq.py — MLX-LM distilled weight quantization implementation (repo)
[^c1-5]: https://github.com/ml-explore/mlx-lm/issues/1900 — Missing general Knowledge Distillation paradigm, issue 1900 (forum)
[^c1-6]: https://mattbeton.com/blog/pipeline-parallel-apple-silicon.html — Pipeline Parallel Training with Apple Silicon (blog)
[^c1-7]: https://github.com/Hmbown/MLXSmith/blob/main/docs/cli/distillation.md — MLXSmith distillation CLI documentation (repo)
[^c1-8]: https://pkg.go.dev/github.com/tmc/mlx-go-lm/mlxlm/llm/training — mlx-go-lm training package API (repo)
[^c1-9]: https://autocontext.ai/docs/guides/distillation-mlx — Training and distillation with MLX (docs)
[^c1-10]: https://ml-explore.github.io/mlx/build/html/dev/custom_metal_kernels.html — Custom Metal Kernels — MLX documentation (docs)
[^c1-11]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/quant/dwq.py — MLX-LM DWQ implementation at 0d4d3d04f8ab (repo)
[^c1-12]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — lora.py (pinned primary source) (repo)
[^c1-13]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/losses.py — losses.py (pinned primary source) (repo)
[^c1-14]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/trainer.py — trainer.py (pinned primary source) (repo)
