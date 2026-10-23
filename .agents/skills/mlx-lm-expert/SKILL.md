---
name: mlx-lm-expert
description: >-
  Explain MLX-LM. TRIGGER: 'configure LoRA'; 'fix streaming'; 'integrate GRPO'. Scope: DoRA/data/losses, sampling/vision, PPL, HTTP, loaders/cache/versions, distributed. SKIP: general PEFT -> ai-llm-model-layer; Mac hardware/runtimes -> running-llm-models-locally-on-mac-expert; new research -> dr.
version: 1.0.0
updated: '2026-10-23'
category: custom
keywords:
  - mlx-lm
  - LoRA
  - QLoRA
  - DoRA
  - fine-tuning
  - prompt masking
  - adapter fusion
  - stream_generate
  - logits processors
  - perplexity
  - distributed training
  - Hugging Face cache
  - request cancellation
  - vision inputs
  - distillation loss
  - teacher student distillation
  - GRPO
  - GSPO
  - external integration
tags: [mlx-lm, apple-silicon, fine-tuning, inference]
whenToUse:
  - Configure MLX-LM training data, adapters and optimization
  - Use MLX-LM Python generation, sampling and evaluation APIs
  - Diagnose MLX-LM service, model-loading or release compatibility behavior
  - Understand native DoRA and distributed fine-tuning limits
  - Check speculative processor rollback, vision caching and request cancellation
  - Distinguish native loss primitives from external training workflows
  - Trace external distillation and GRPO/GSPO APIs, rollout metadata and adapter files
related_skills: [ai-llm-model-layer, running-llm-models-locally-on-mac-expert, dr]
---

# MLX-LM

Read the reference for the requested surface before answering. Keep each statement's
citations, confidence, version limits and verification date. Source research does
not establish local model quality, throughput or hardware compatibility.

In the native training CLI, `--fine-tune-type full` still obeys `--num-layers`.
The selected base layers train; the generic definition of full fine-tuning does
not imply that every base weight trains in that CLI invocation. Read the
[training reference](references/mlx-lm-training.md) for the frozen-model and
layer-selection contracts.

| Topic | Reference |
| --- | --- |
| LoRA, QLoRA and full fine-tuning; datasets and prompt masking; optimizer configuration and metrics; memory and gradients; adapter checkpoints, fusion and export | [Training and adapter lifecycle](references/mlx-lm-training.md) |
| Python generation and streaming; custom sampling and logits processors; perplexity and lm-evaluation | [Python APIs and evaluation](references/mlx-lm-python-evaluation.md) |
| Native DoRA and quantized adapters; distributed fine-tuning and gradient synchronization | [Training extensions](references/mlx-lm-training-extensions.md) |
| Native HTTP requests, streaming and errors; architecture and loader contracts; model and Hub cache management; release compatibility | [Native service and model contracts](references/mlx-lm-native-contracts.md) |
| Speculative processor rollback; cancellation and resource cleanup; native vision inputs and image-aware caching | [Advanced generation contracts](references/mlx-lm-advanced-generation.md) |
| Native distillation loss kernels, custom Python losses and DWQ parameter selection | [Custom training losses](references/mlx-lm-custom-training-loss.md) |
| External mlx-train pipeline backpropagation prototype and compatibility limits | [Pipeline prototype](references/mlx-train-pipeline-backpropagation.md) |
| External teacher/student distillation and GRPO/GSPO wrappers: native APIs, token alignment, rewards and adapter handoff | [External post-training integration](references/mlx-lm-external-post-training.md) |

Use `ai-llm-model-layer` for general model selection and PEFT theory. Use
`running-llm-models-locally-on-mac-expert` for Mac runtimes and hardware. Use `dr` to
refresh a volatile claim or investigate an unresolved question in a reference.
