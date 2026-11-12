---
name: mlx-lm-expert
description: 'Explain source-qualified MLX-LM training, generation and native service contracts. TRIGGER: MLX-LM LoRA or DoRA;
  stream_generate; MLX-LM HTTP cancellation; native loss APIs versus external GRPO or distillation wrappers. Read the matching
  dated reference. SKIP: general PEFT -> ai-llm-model-layer; general runtime selection -> ai-llm-model-layer; Mac hardware
  -> apple-hardware-router; new source research -> dr.'
version: 1.1.0
updated: '2026-11-11'
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
tags:
- mlx-lm
- apple-silicon
- fine-tuning
- inference
whenToUse:
- Configure MLX-LM training data, adapters and optimization
- Use MLX-LM Python generation, sampling and evaluation APIs
- Diagnose MLX-LM service, model-loading or release compatibility behavior
- Understand native DoRA and distributed fine-tuning limits
- Check speculative processor rollback, vision caching and request cancellation
- Distinguish native loss primitives from external training workflows
- Trace external distillation and GRPO/GSPO APIs, rollout metadata and adapter files
related_skills:
- ai-llm-model-layer
- dr
- apple-hardware-router
model: gpt-6.1-sol
effort: medium
triggers:
- MLX-LM LoRA
- MLX-LM stream_generate
- MLX-LM cancellation
- MLX-LM native versus external training
metadata:
  changelog_ref: references/CHANGELOG.md
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

Use `ai-llm-model-layer` for general model selection, runtime choices and PEFT theory.
Use `apple-hardware-router` for Mac hardware and eGPU topics. Use `dr` to
refresh a volatile claim or investigate an unresolved question in a reference.

## Response contract

Name the native MLX-LM surface or external wrapper before describing its contract.
Cite the matching reference and retain version, confidence and verification dates.
An external training integration does not establish a native MLX-LM feature.
If the reference cannot answer the selected version's question, state the gap;
do not invent compatibility or claim a local benchmark was run.

## Look for llms files first

Before reading the subject raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
1. Locate the subject's `llms.txt`, source-qualified concept pack, or relevant documentation index. Existing keyword hits can help locate it.
2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map.
4. If you have the repo, search the code before opening an llms file. The code is the authority. Verify each fact against its source `path:line`.
5. Index and llms hits are leads. Confirm their sources before acting.
