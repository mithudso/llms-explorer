<!-- hub-reference-banner -->
> **Reference file — part of the `mlx-lm-expert` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/mlx-train-pipeline-backpropagation-20261023`.

---
name: mlx-train-pipeline-backpropagation
description: "Explain the external mlx-train pipeline-backpropagation prototype on Apple silicon. TRIGGER: ppp.py stages; autograd communication; pipeline scheduling. SKIP: native MLX-LM data-parallel fine-tuning -> mlx-lm-expert training-extensions reference."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
whenToUse:
  - "External mlx-train pipeline prototype"
keywords: ["mlx-lm", "Apple silicon", "generation", "training", "compatibility", "source contracts", "version pinning", "limitations"]
tags: ["mlx-lm", "research"]
provenance: "/dr · ~/.global-ai-hub/research/mlx-train-pipeline-backpropagation-20261023"
---

# Pipeline parallel backpropagation on Apple silicon with mlx-train

## Overview

Pipeline parallel backprop splits a model across Apple Silicon devices, sends activations forward, then returns gradients backward so each stage can compute parameter and input gradients. The mlx-train implementation uses MLX's core value_and_grad over parameters and stage inputs, with an auxiliary scalar dot product against a stop-gradient downstream cotangent. A single lazy graph can deadlock if a blocking backward receive runs before the forward send; the large-model path orders forward and backward evaluation separately. The described schedule processes one microbatch at a time. Apple's WWDC26 material shows native MLX-LM pipeline inference and data-parallel fine-tuning, but does not demonstrate native pipeline-backprop training, so current training support remains an open question.

## Core Concepts

### Pipeline parallel backpropagation on Apple silicon with mlx-train

- Pipeline parallel training divides a sequential model across stages. Activations move downstream during the forward pass, then boundary gradients move upstream during backprop so each stage can compute gradients for its parameters and input.[^c1-1][^c1-7][^c1-8]
- mlx-train splits the model into contiguous transformer-layer PipelineSlice modules: rank 0 embeds token IDs, later ranks accept hidden states, and the final slice applies normalization and the language-model head before producing logits for the loss. verified-as-of: 2026-10-23[^c1-3][^c1-2]
- Pipeline backpropagation reverses the message direction: every rank except the final rank receives the output cotangent from the next rank; the final rank instead differentiates masked_loss. The stages compute local parameter gradients, and nonzero ranks also compute and send their input-boundary cotangent to rank-1. Rank 0 has no preceding stage.[^c1-3][^c1-1][^c1-8][^c1-10]

## Tools & Frameworks

- MLX's core mx.value_and_grad requires a scalar loss (or a tuple whose first value is scalar) and accepts argnums to select input positions for gradients. A stage can use it to differentiate with respect to both model parameters and its input activation; mlx.nn.value_and_grad is the parameter-oriented helper. verified-as-of: 2026-10-23[^c1-5][^c1-6][^c1-1] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- Apple's WWDC26 material documents MLX-LM's --pipeline option for distributed inference and demonstrates distributed fine-tuning by replicating the model and processing separate batches. It does not demonstrate a native pipeline-parallel backprop training interface, so inference support alone does not establish that training feature. (two sources) verified-as-of: 2026-10-23[^c1-4][^c1-1][^c1-9] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_

## Methodology

- For a nonfinal stage, ppp.py defines a scalar local loss as the sum of the stage output multiplied by the stopped received cotangent. Differentiating this surrogate seeds the local reverse pass with that cotangent; mx.value_and_grad with argnums=(0,1) returns gradients for trainable parameters and the stage input. verified-as-of: 2026-10-23[^c1-3][^c1-1][^c1-5] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- The published mlx-train schedule processes one batch at a time. The author leaves multi-minibatch schedules such as 1F1B and GPipe as future work because overlapping minibatches requires preserving the right activations and model state for each backward pass. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-3][^c1-7] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_

## Practical Patterns

- The project article describes a one-batch-at-a-time schedule. GPipe uses batch splitting to overlap microbatches, and PipeDream admits multiple minibatches into the pipeline to reduce idle stalls; that comparison shows the mlx-train example's pipeline-parallel label alone does not establish high utilization or a speedup.[^c1-1][^c1-7][^c1-8] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- This pipeline-training implementation belongs to external MattBeton/mlx-train at ee8aea37ffd3adb95bf6c03c936afb3ea79d3fe7. Its load_configure_model slices a loaded MLX-LM model into PipelineSlice when distributed="pp", and its own train loop calls train_step_pp. Native mlx_lm.lora instead calls mlx_lm.tuner.trainer.train; these sources do not make the external prototype a supported native pipeline-training option or prove current-version compatibility. (two sources) verified-as-of: 2026-10-23[^c1-13][^c1-11][^c1-12] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- Tentative: build_graph(model:PipelineSlice,tokens,targets,lengths) constructs lazy stage-local forward/loss/gradient arrays and a tokens_out communication dictionary, then returns (loss,g_s,tokens_out). Noninitial ranks recv (B,L,H) bfloat16 activations from rank-1; nonfinal ranks send their (B,L,H) outputs to rank+1 and receive downstream cotangents. It does not by itself execute a forward-before-backward schedule. Asserts check nonfinal output rank and hidden width, and the dependency-like ordering call is commented out. verified-as-of: 2026-10-23[^c1-10] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- Tentative: Inside build_graph, nonfinal local_loss is sum(y_loc*stop_gradient(dy_loc)); differentiation seeds the local reverse pass with the received downstream cotangent. Nonzero ranks use mx.value_and_grad(local_loss,argnums=(0,1)) to obtain parameter gradients and the stage-input gradient dx, then send dx to rank-1. Rank zero in a multi-stage pipeline differentiates parameters only; the final rank differentiates masked_loss instead of a downstream-cotangent surrogate. verified-as-of: 2026-10-23[^c1-10] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- Tentative: train_step_pp shifts a batch into inputs/targets, calls build_graph, and groups its y/x and dx/dy tokens into forward and backward evaluation lists. It loops stages forward with barriers to evaluate receive/send work, loops stages backward with barriers to evaluate cotangent receive/send work, then applies optimizer.update(model,g_s) and evaluates model/optimizer state. This explicit evaluation schedule supplies ordering; Python send-expression construction alone does not. verified-as-of: 2026-10-23[^c1-12] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- Stage allocation in load_configure_model and _rank_bounds uses per=total_layers//world_size, start=rank*per, and end=(rank+1)*per except that the last rank receives the remainder through total_layers. PipelineSlice owns that contiguous layer slice; only start=0 owns token embeddings and only end=total owns norm/output projection. build_graph assumes these rank roles and compatible (B,L,H) boundaries rather than validating arbitrary layer assignments. The pinned allocation has no explicit rejection for world_size greater than total_layers, which can produce empty slices. (two sources) verified-as-of: 2026-10-23[^c1-11][^c1-10] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- Tentative: write_adapters_distributed in mlx_train/model.py assembles stage adapters. It maps each slice-local layers/h index to a canonical (start+local_layer_index,parameter_tail) identity, gathers LoRA tensors neighbor-to-neighbor toward rank zero, and matches those identities to a lazy reference model's official parameter keys. Rank zero asserts no reference LoRA key is missing, saves adapters.safetensors and adapter_config.json, and all ranks synchronize. The reference-key mapping preserves model-wide layer identities instead of reusing each slice's local layer numbering. verified-as-of: 2026-10-23[^c1-11] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- The blog explains that an unconstrained lazy graph may schedule a blocking backward recv before the forward send that enables it. Its single-eval proof of concept adds a forward-before-backward dependency; the large-model path instead evaluates forward and backward phases in order. In ppp.py at ee8aea37ffd3, the send expression precedes the cotangent recv expression in Python, but the _depends_like call is commented out, so expression construction alone does not guarantee their lazy execution order. The README documents two-step forward/backward evaluation; the stage code also computes an input cotangent for the prior rank. (two sources) verified-as-of: 2026-10-23[^c1-1][^c1-3][^c1-2][^c1-10] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_
- The current repository exposes activation and gradient send/receive tokens and documents separate forward and backward evaluation phases. The project article reports that a single evaluation graph could leave ranks waiting on blocking receives long enough to time out on a large model; the staged evaluation limits each wait to the relevant communication phase. (two sources) verified-as-of: 2026-10-23[^c1-2][^c1-3][^c1-1] _(Pipeline parallel backpropagation on Apple silicon with mlx-train)_

## Disagreements & Open Questions

- Disagreement (Pipeline parallel backpropagation on Apple silicon with mlx-train): Older accounts say MLX lacks built-in pipeline parallel support. Apple's WWDC26 material shows that MLX-LM now has a pipeline option for inference, while its distributed fine-tuning example is data parallel. Scope those older statements to pipeline backprop training or to their publication context; they do not describe current pipeline inference support.[^c1-1][^c1-9][^c1-4]
- Disagreement (Pipeline parallel backpropagation on Apple silicon with mlx-train): The blog's early single-eval proof of concept inserts a forward-before-backward dependency with mx.depends. The current ppp.py implementation separates forward and backward evaluation, and its dependency-like ordering helper is commented out as necessary only for a single-step graph.[^c1-1][^c1-3]
- Disagreement (Pipeline parallel backpropagation on Apple silicon with mlx-train): The article presents mx.depends as an ordering fix for its single-evaluation graph, while the current README documents separate forward and backward evaluation and ppp.py leaves the _depends_like call on the received cotangent commented out. Treat these as different execution designs rather than assuming the article's mx.depends call is active in the current code.[^c1-1][^c1-2][^c1-3]
- Open (Pipeline parallel backpropagation on Apple silicon with mlx-train): Does the current MLX or MLX-LM release expose native pipeline-parallel gradient training? Apple's WWDC26 session shows pipeline inference and data-parallel fine-tuning but does not settle this.
- Open (Pipeline parallel backpropagation on Apple silicon with mlx-train): Has the current mlx-train main branch been independently reproduced across current MLX versions and distributed backends?
- Open (Pipeline parallel backpropagation on Apple silicon with mlx-train): Can mlx-train preserve model state and activations for overlapping microbatches in a 1F1B or GPipe schedule?
- Open (Pipeline parallel backpropagation on Apple silicon with mlx-train): The article leaves multi-minibatch scheduling and activation retention across concurrent batches as future work; the reviewed sources do not establish whether a later implementation has added them.

## References

### Pipeline parallel backpropagation on Apple silicon with mlx-train

[^c1-1]: https://mattbeton.com/blog/pipeline-parallel-apple-silicon.html — Pipeline Parallel Training with Apple Silicon (blog)
[^c1-2]: https://github.com/MattBeton/mlx-train — MattBeton/mlx-train repository README (repo)
[^c1-3]: https://github.com/MattBeton/mlx-train/blob/main/mlx_train/ppp.py — mlx-train ppp.py pipeline graph implementation (repo)
[^c1-4]: https://developer.apple.com/videos/play/wwdc2026/233/ — Explore distributed inference and training with MLX (WWDC26) (docs)
[^c1-5]: https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.value_and_grad.html — mlx.core.value_and_grad — MLX 0.32.4 documentation (docs)
[^c1-6]: https://ml-explore.github.io/mlx/build/html/usage/function_transforms.html — Function Transforms — MLX 0.32.4 documentation (docs)
[^c1-7]: https://research.google/pubs/gpipe-efficient-training-of-giant-neural-networks-using-pipeline-parallelism/ — GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism (paper)
[^c1-8]: https://www.microsoft.com/en-us/research/wp-content/uploads/2019/08/pipedream.pdf — PipeDream: Generalized Pipeline Parallelism for DNN Training (paper)
[^c1-9]: https://latentnode.pages.dev/articles/dist-mlx — Distributed Training on Heterogeneous Macs (blog)
[^c1-10]: https://raw.githubusercontent.com/MattBeton/mlx-train/ee8aea37ffd3adb95bf6c03c936afb3ea79d3fe7/mlx_train/ppp.py — mlx-train ppp.py at ee8aea37ffd3 (repo)
[^c1-11]: https://raw.githubusercontent.com/MattBeton/mlx-train/ee8aea37ffd3adb95bf6c03c936afb3ea79d3fe7/mlx_train/model.py — model.py (pinned primary source) (repo)
[^c1-12]: https://raw.githubusercontent.com/MattBeton/mlx-train/ee8aea37ffd3adb95bf6c03c936afb3ea79d3fe7/mlx_train/train.py — train.py (pinned primary source) (repo)
[^c1-13]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — lora.py (pinned primary source) (repo)
