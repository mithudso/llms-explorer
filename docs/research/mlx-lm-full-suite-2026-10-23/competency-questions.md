# MLX-LM competency questions

As of 2026-10-23. Run-start plan for TASK-866. Inventory: local-fallback; GAP decisions remain provisional until the pre-dispatch dedup check.

A HAVE mapping below is inherited context. It does not close a missing MLX-LM-specific child. Open questions close only after the listed planned concepts finish research.

## CQ1

Which local runtime and model format fits a Mac and how does MLX-LM differ from its peers?

Status: HAVE

Existing HAVE mapping: mac-local-llms-runtime-selection-and-frontends, mlx-and-mlx-lm-on-apple-silicon

Planned resolver: none; current HAVE coverage answers this question

## CQ2

How do I choose and run MLX-LM LoRA QLoRA DoRA or full fine-tuning?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: llm-fine-tuning-amp-peft

Planned resolver: mlx-lm-lora-qlora-and-full-fine-tuning, mlx-lm-native-dora-and-quantized-adapter-mechanics

## CQ3

How do I format local or Hugging Face training data and select the tokens that contribute to loss?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: llm-fine-tuning-amp-peft

Planned resolver: mlx-lm-training-datasets-and-prompt-masking

## CQ4

How do I set MLX-LM configuration optimizer schedule metrics and training memory controls?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: apple-silicon-unified-memory-and-llm-sizing

Planned resolver: mlx-lm-training-configuration-optimization-and-metrics, mlx-lm-training-memory-and-gradient-control

## CQ5

What does an adapter checkpoint restore and how do I fuse export and attribute the resulting model?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: llm-fine-tuning-amp-peft

Planned resolver: mlx-lm-adapter-checkpoints-fusion-and-export

## CQ6

How do Python generation streaming caches samplers and logits processors compose correctly?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: mlx-and-mlx-lm-on-apple-silicon, mac-local-llms-prompt-cache-and-persistent-kv, continuous-batching-on-mlx

Planned resolver: mlx-lm-python-generation-and-streaming-contracts, mlx-lm-custom-sampling-and-logits-processors

## CQ7

How do I measure native test perplexity and task quality without confusing them with throughput?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: mac-local-llms-quantization-evaluation, benchmark-methodology-pitfalls-for-local-llm-run

Planned resolver: mlx-lm-perplexity-and-lm-evaluation

## CQ8

Which native HTTP request response streaming and error behaviors are compatible with an OpenAI client?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: mlx-and-mlx-lm-on-apple-silicon, mac-local-llms-chat-templates-reasoning-and-tool-calling

Planned resolver: mlx-lm-http-request-streaming-and-error-contracts

## CQ9

How do I extend model loading qualify supported architectures and manage local Hub cache revisions?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: transformer-architecture-internals-amp-variants

Planned resolver: mlx-lm-model-architecture-integration-and-loader-contracts, mlx-lm-model-management-and-hub-cache-lifecycle

## CQ10

Which release and dependencies provide a behavior and how does distributed training differ from inference sharding?

Status: OPEN-until-per-concept-research-completes

Existing HAVE mapping: tensor-vs-pipeline-vs-expert-parallelism-for-moe, mac-local-llms-clusters-rdma-exo-ds4

Planned resolver: mlx-lm-version-pinning-and-release-compatibility-delta, mlx-lm-distributed-fine-tuning-and-gradient-synchronization


# Round 1 competency questions

Append new entries; preserve existing questions and status history.

| ID | Competency question | Planned resolver slug | Status |
|---|---|---|---|
| CQ-R1-01 | How do native MLX-LM image inputs select a processor, reach generation, and retain correct image identity during prompt-cache reuse? | `mlx-lm-native-vision-inputs-and-image-aware-prompt-caching` | OPEN |
| CQ-R1-02 | How does native MLX-LM observe request cancellation and release generation resources across queued, sequential, and batched work? | `mlx-lm-native-request-cancellation-and-generation-resource-lifecycle` | OPEN |
| CQ-R1-03 | How must caller-owned logits processor state stay aligned with accepted token history when speculative decoding rejects draft tokens? | `mlx-lm-stateful-logits-processor-rollback-during-speculative-decoding` | OPEN |
| CQ-R1-04 | How can a Python caller compose native divergence-loss primitives with the MLX-LM custom trainer loss interface? | `mlx-lm-distillation-loss-kernels-and-custom-training-loss` | OPEN |
| CQ-R1-05 | How does the separate MattBeton/mlx-train implementation propagate gradients across pipeline stages and assemble distributed adapters? | `pipeline-parallel-backpropagation-on-apple-silicon-with-mlx-train` | OPEN |

# Round 2 competency questions

Append new entries; preserve existing questions and status history.

| ID | Competency question | Planned resolver slug | Status |
|---|---|---|---|
| CQ-R2-01 | How can an external teacher-student distillation trainer use native MLX-LM model, loss, masking, and adapter interfaces while preserving the external checkpoint state? | `mlx-lm-integration-contracts-for-external-teacher-student-distillation` | OPEN |
| CQ-R2-02 | How can an external GRPO or GSPO trainer connect rollouts, grouped objective inputs, and policy checkpoints to native MLX-LM APIs and adapter artifacts? | `mlx-lm-integration-contracts-for-external-grpo-and-gspo-training` | OPEN |

## Final resolution

All 17 competency questions resolve to existing coverage or the 21 researched concepts. Initial OPEN labels above preserve the run-start history. The fixed 210-question banks and all 42 hash-bound small/full answer-test results are included beside this report.

- [LoRA, QLoRA and full fine-tuning](../../../outputs/llms-concepts/mlx-lm-lora-and-qlora-versus-full-fine-tuning.llms/llms-full.txt)
- [Adapter checkpoints, fusion and export](../../../outputs/llms-concepts/mlx-lm-adapter-checkpoints-fusion-and-export.llms/llms-full.txt)
- [Perplexity and task evaluation](../../../outputs/llms-concepts/mlx-lm-perplexity-and-lm-evaluation.llms/llms-full.txt)
- [Training configuration and metrics](../../../outputs/llms-concepts/mlx-lm-training-configuration-optimization-and-metrics.llms/llms-full.txt)
- [Datasets and prompt masking](../../../outputs/llms-concepts/mlx-lm-training-datasets-and-prompt-masking.llms/llms-full.txt)
- [Training memory and gradients](../../../outputs/llms-concepts/mlx-lm-training-memory-and-gradient-control.llms/llms-full.txt)
- [Python generation and streaming](../../../outputs/llms-concepts/mlx-lm-python-generation-and-streaming-contracts.llms/llms-full.txt)
- [Native HTTP and SSE contracts](../../../outputs/llms-concepts/mlx-lm-native-http-request-streaming-and-error-contracts.llms/llms-full.txt)
- [Release and version compatibility](../../../outputs/llms-concepts/mlx-lm-version-pinning-and-current-release-compatibility-delta.llms/llms-full.txt)
- [Sampling and logits processors](../../../outputs/llms-concepts/mlx-lm-custom-sampling-and-logits-processors.llms/llms-full.txt)
- [DoRA and quantized adapters](../../../outputs/llms-concepts/mlx-lm-native-dora-and-quantized-adapter-mechanics.llms/llms-full.txt)
- [Architecture and loader integration](../../../outputs/llms-concepts/mlx-lm-model-architecture-integration-and-loader-contracts.llms/llms-full.txt)
- [Distributed fine-tuning](../../../outputs/llms-concepts/mlx-lm-distributed-fine-tuning-and-gradient-synchronization.llms/llms-full.txt)
- [Model and Hub cache management](../../../outputs/llms-concepts/mlx-lm-model-management-and-hugging-face-cache-lifecycle.llms/llms-full.txt)
- [Speculative processor rollback](../../../outputs/llms-concepts/mlx-lm-stateful-logits-processor-rollback-during-speculative-decoding.llms/llms-full.txt)
- [Cancellation and resource lifecycle](../../../outputs/llms-concepts/mlx-lm-native-request-cancellation-and-generation-resource-lifecycle.llms/llms-full.txt)
- [Vision inputs and image-aware cache](../../../outputs/llms-concepts/mlx-lm-native-vision-inputs-and-image-aware-prompt-caching.llms/llms-full.txt)
- [Custom training losses](../../../outputs/llms-concepts/mlx-lm-distillation-loss-kernels-and-custom-training-loss.llms/llms-full.txt)
- [External mlx-train pipeline prototype](../../../outputs/llms-concepts/pipeline-parallel-backpropagation-on-apple-silicon-with-mlx-train.llms/llms-full.txt)
- [External teacher/student integration](../../../outputs/llms-concepts/mlx-lm-integration-contracts-for-external-teacher-student-distillation.llms/llms-full.txt)
- [External GRPO/GSPO integration](../../../outputs/llms-concepts/mlx-lm-integration-contracts-for-external-grpo-and-gspo-training.llms/llms-full.txt)

## Question-to-reference resolution

| Question | Coverage | Reference |
| --- | --- | --- |
| CQ-R1-01 | Researched this run | [mlx-lm-advanced-generation](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-advanced-generation.md) |
| CQ-R1-02 | Researched this run | [mlx-lm-advanced-generation](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-advanced-generation.md) |
| CQ-R1-03 | Researched this run | [mlx-lm-advanced-generation](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-advanced-generation.md) |
| CQ-R1-04 | Researched this run | [mlx-lm-custom-training-loss](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-custom-training-loss.md) |
| CQ-R1-05 | Researched this run | [mlx-train-pipeline-backpropagation](../../../.agents/skills/mlx-lm-expert/references/mlx-train-pipeline-backpropagation.md) |
| CQ-R2-01 | Researched this run | [mlx-lm-external-post-training](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-external-post-training.md) |
| CQ-R2-02 | Researched this run | [mlx-lm-external-post-training](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-external-post-training.md) |
| CQ1 | HAVE | [Existing Mac runtime coverage](https://llms-explorer.com/tree/mlx-and-mlx-lm-on-apple-silicon/read/) |
| CQ10 | Researched this run | [mlx-lm-native-contracts](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-native-contracts.md) |
| CQ2 | Researched this run | [mlx-lm-training](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-training.md) |
| CQ3 | Researched this run | [mlx-lm-training](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-training.md) |
| CQ4 | Researched this run | [mlx-lm-training](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-training.md) |
| CQ5 | Researched this run | [mlx-lm-training](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-training.md) |
| CQ6 | Researched this run | [mlx-lm-python-evaluation](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-python-evaluation.md) |
| CQ7 | Researched this run | [mlx-lm-python-evaluation](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-python-evaluation.md) |
| CQ8 | Researched this run | [mlx-lm-native-contracts](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-native-contracts.md) |
| CQ9 | Researched this run | [mlx-lm-native-contracts](../../../.agents/skills/mlx-lm-expert/references/mlx-lm-native-contracts.md) |
