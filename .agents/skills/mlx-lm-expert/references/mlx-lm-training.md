<!-- hub-reference-banner -->
> **Reference file — part of the `mlx-lm-expert` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/mlx-lm-training-20261023`.

---
name: mlx-lm-training
description: "Explain MLX-LM LoRA QLoRA and full fine-tuning from source-qualified research. TRIGGER: training datasets and prompt masking; learning-rate schedules and metrics; memory controls and gradient accumulation; adapter checkpoints resume fusion and export. SKIP: native DoRA and distributed synchronization -> mlx-lm-expert training-extensions reference."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
whenToUse:
  - "Choose and configure MLX-LM fine-tuning"
  - "Prepare masked training data"
  - "Manage training memory and adapter checkpoints"
keywords: ["mlx-lm", "LoRA", "QLoRA", "fine-tuning", "prompt masking", "datasets", "learning rate", "gradient checkpointing", "gradient accumulation", "adapter fusion"]
tags: ["mlx-lm", "training", "adapters", "datasets"]
provenance: "/dr · ~/.global-ai-hub/research/mlx-lm-training-20261023"
---

# MLX-LM training and adapter lifecycle

## Overview

MLX-LM’s adapter workflow defaults to LoRA; a quantized input selects QLoRA, and full-weight fine-tuning is also available. LoRA freezes base weights and learns low-rank matrices, reducing trainable parameters. QLoRA adds a quantized frozen base and routes gradients into adapters. These approaches can lower training cost, yet actual memory use, speed, and task quality depend on the model, rank, batch size, quantization, and implementation. Studies report parity in some configurations and full-tuning wins in others. Treat them as distinct adaptation choices and validate against the target task and hardware.

MLX-LM fine-tuning data can come from local JSONL files or Hugging Face datasets. Its loader recognizes chat, tools, prompt/completion, and plain-text records, then serializes structured chat-like rows with the model's chat template. Data shape and template compatibility determine which tokens the model sees. By default, MLX-LM computes loss on the whole serialized example. `--mask-prompt` is supported for chat and completion formats; a chat record's last message is the target span. This makes row endings important: earlier assistant actions in a multi-turn tool trace are masked if a later message follows them. Research on prompt-token loss shows no universal best masking rule, so dataset design and held-out task metrics should drive the choice.

MLX-LM exposes YAML and CLI controls for training iterations, batch size, learning-rate schedules, optimizer settings, and evaluation intervals. These controls let a run be adjusted for a particular model, dataset, and hardware; the current guide says command-line flags override matching YAML keys. The training guide supports periodic validation loss, optional test-set perplexity, and metric logging integrations. Those measures help diagnose training, but they do not establish task success by themselves. Independent MLX write-ups recommend adding task-level evaluation and show that apparently improving validation loss can coexist with poor task scores. Reliable optimization compares training behavior with a held-out target-task measure and records the effective configuration.

MLX-LM documents several distinct controls for training memory: smaller per-pass batches, fewer layers, shorter examples, gradient accumulation, and gradient checkpointing. Accumulation combines gradients from small batches before an optimizer update, preserving a larger effective batch without increasing per-pass batch memory. Checkpointing reduces saved activation memory by recomputing activations during backpropagation, at extra compute cost; its value depends on batch size and sequence length. A user report shows that an `Insufficient Memory` error can also be build-specific: the same long-sequence run continued after reinstalling MLX-LM from source. That report did not isolate the original failure cause, so it is a troubleshooting lead rather than a memory estimate.

MLX-LM keeps adapter weights in a separate directory until `mlx_lm.fuse` merges them into the base model and writes a self-contained MLX model directory. The default adapter input is `adapters/`; the default output is `fused_model/`. The loader reads a config plus the canonical `adapters.safetensors` file, so a numbered checkpoint must be staged in that shape before fusion. Built-in GGUF export is limited to llama, mixtral, and mistral model types and documented for fp16. Independent reports show quantized fusion can alter adapter behavior for some models, so compare the fused model with adapter-attached inference. A GGUF serialization failure reported on `mlx-lm` 0.31.3 was fixed in upstream PR #1743.

## Core Concepts

### MLX-LM LoRA and QLoRA versus full fine-tuning

- LoRA freezes pretrained base weights and trains low-rank matrices, while full fine-tuning updates all original model parameters. LoRA therefore uses fewer trainable parameters, although its adapter matrices and optimizer states still consume memory.[^c1-3][^c1-8][^c1-10]
- QLoRA propagates gradients through a frozen quantized pretrained model into trainable LoRA adapters. The original QLoRA method uses a 4-bit base and introduces NF4, double quantization, and paged optimizers; MLX-LM documents QLoRA as its LoRA training path for quantized models.[^c1-4][^c1-9][^c1-1]

### MLX-LM training datasets and prompt masking

- For a local --data directory, MLX-LM reads JSONL records from train.jsonl for training, accepts valid.jsonl as an optional validation split, and reads test.jsonl for testing. The current loader returns an empty split when a file is missing, then raises for an empty training or test split and warns but continues when validation is empty. If the --data path does not exist, the loader treats it as a Hugging Face dataset ID. verified-as-of: 2026-10-23[^c2-1][^c2-2]
- For Hugging Face datasets, YAML fields such as prompt_feature, completion_feature, chat_feature, and text_feature map dataset columns to MLX-LM inputs. MLX-LM applies the model's chat template to chat, tools, and completion records by default; Hugging Face documents that chat templates and control tokens vary by model, so the training serialization should match the tokenizer. verified-as-of: 2026-10-23[^c2-1][^c2-3]
- Prompt masking is disabled by default. Without --mask-prompt, MLX-LM computes loss for every sample token; with it, the documented supported formats are chat and completion, and the final chat message is treated as the completion. The current loader raises ValueError when prompt masking is requested for a text dataset. verified-as-of: 2026-10-23[^c2-1][^c2-2]

### MLX-LM training configuration optimization and metrics

_(no core claims)_

### MLX-LM training memory and gradient control

- Activation memory grows with batch size and sequence length, so the MLX-LM guide recommends lowering `--batch-size` and shortening long examples when memory is constrained; it notes that smaller batches may slow training. verified-as-of: 2026-10-23[^c4-5][^c4-6]

### MLX-LM adapter checkpoints fusion and export

- Current MLX-LM training writes the current adapter weights to `adapters.safetensors` and, at each configured save interval, also writes a numbered `<step>_adapters.safetensors` snapshot beside it. The loader called by fusion reads `adapter_config.json` and `adapters.safetensors` from the `--adapter-path` directory, so using a numbered snapshot requires exposing the chosen weights under the expected `adapters.safetensors` name beside the corresponding config. verified-as-of: 2026-10-23[^c5-11][^c5-3][^c5-2][^c5-1][^c5-6]

## Tools & Frameworks

- In the MLX-LM guide pinned to commit 0d4d3d04, adapter fine-tuning defaults to LoRA; a quantized input model uses QLoRA; and full-weight fine-tuning is exposed with `--fine-tune-type full`. The README also advertises low-rank and full fine-tuning with quantized-model support. verified-as-of: 2026-10-23[^c1-1][^c1-2][^c1-9] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- The current MLX-LM guide accepts YAML through -c/--config, and a repeated command-line flag overrides the corresponding YAML key. Apple's WWDC25 walkthrough says the config file controls learning-rate schedules, optimizer settings, and evaluation intervals. verified-as-of: 2026-10-23[^c3-1][^c3-2] _(MLX-LM training configuration optimization and metrics)_
- MLX-LM exposes configuration for iteration count, batch size, validation batches and intervals, loss-report intervals, gradient accumulation, maximum sequence length, learning-rate schedules, and optimizer settings; these controls let a run be adjusted to its training and evaluation needs. verified-as-of: 2026-10-23[^c3-2][^c3-6][^c3-7] _(MLX-LM training configuration optimization and metrics)_
- The current `mlx_lm.fuse` command loads a base model and adapter directory, fuses model modules that expose a `fuse` method, and saves the combined model at `--save-path`; the defaults are `mlx_model`, `adapters`, and `fused_model`. It can also upload the saved model when given `--upload-repo`. Apple describes the fused result as a self-contained model for simpler deployment and sharing. verified-as-of: 2026-10-23[^c5-2][^c5-1][^c5-4][^c5-6] _(MLX-LM adapter checkpoints fusion and export)_
- The current `--export-gguf` path accepts only `model_type` values `llama`, `mixtral`, and `mistral`; the docs also scope support to those model styles at fp16 and give `fused_model/ggml-model-f16.gguf` as the default output, overridable with `--gguf-path`. The optional `--dequantize` path dequantizes before saving and removes quantization metadata from the saved config. A `gpt_oss` export rejection was reported through the same model-type gate. verified-as-of: 2026-10-23[^c5-2][^c5-1][^c5-10][^c5-6][^c5-12] _(MLX-LM adapter checkpoints fusion and export)_

## Methodology

- LoRA’s quality relative to full fine-tuning is conditional. An LREC-COLING study reports comparable performance for appropriately ranked LoRA in high-resource multitask instruction tuning, while Thinking Machines reports a performance gap at larger batch sizes in its experiments; spectral-analysis research finds that LoRA and full fine-tuning can reach similar task performance with different weight-space structures.[^c1-7][^c1-6][^c1-5][^c1-12] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- Memory and quality do not follow a universal ranking. In one 2026 FLAN-T5 Query-DSL experiment, full-precision fine-tuning had the best average evaluation loss among the configurations that could be run, while average memory ranking changed with model size: LoRA and QLoRA used more memory than full precision at FLAN-T5 Large, and QLoRA enabled FLAN-T5 XL under that study’s resource limit. The QLoRA paper reports preserving 16-bit task performance in its own evaluations, so results depend on experimental conditions. (two sources)[^c1-8][^c1-4] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- A 2026 theoretical preprint analyzes a simple linear-regression setting and identifies conditions where LoRA can have lower excess risk than full fine-tuning when the downstream task shift is effectively low-rank. This is a conditional result, not a general LLM quality guarantee; the EAMT translation study provides a contrasting task-specific result. (two sources)[^c1-11][^c1-10] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- The current loader chooses a row format from the first record: prompt and completion keys take precedence, then the chat key (messages by default), then the text key (text by default). Configurable feature names can rename those keys. Completion rows become a user/assistant message pair, and chat rows can pass a tools field to the tokenizer's chat template, so records within a split should use a consistent shape. verified-as-of: 2026-10-23[^c2-2][^c2-1] _(MLX-LM training datasets and prompt masking)_
- Prompt masking is not a universal best choice. A 2026 TACL survey reports that including prompt-token loss can improve generalization in some long-instruction, low-data settings, while a prompt-loss-weighting study says the useful weight depends on the task and dataset. Evaluate masking choices on held-out task outputs instead of assuming completion-only loss always wins. (two sources)[^c2-4][^c2-5][^c2-10] _(MLX-LM training datasets and prompt masking)_
- MLX-LM calculates the prompt boundary in token space with tokenizer.apply_chat_template: chat data uses the template for all messages except the last, and completion data uses a prompt-only message with add_generation_prompt=True. Hugging Face documents that chat templates serialize messages into model-specific token sequences and that generation prompts affect this serialization, so the tokenizer and template used for training must match the intended format. verified-as-of: 2026-10-23[^c2-2][^c2-3] _(MLX-LM training datasets and prompt masking)_
- Tentative: The guide says an optional valid.jsonl enables periodic validation-loss reporting; --test evaluates test.jsonl and reports test-set perplexity. It also supports sending training metrics to Weights & Biases and/or SwanLab. verified-as-of: 2026-10-23[^c3-1] _(MLX-LM training configuration optimization and metrics)_
- Training and validation loss should be paired with a task-level evaluation: an MLX-LM practitioner case study reported validation loss improving while hard-set macro-F1 remained very poor, and a separate local-LLM evaluation guide recommends task-specific measures or human review alongside training metrics. (two sources)[^c3-3][^c3-4][^c3-1] _(MLX-LM training configuration optimization and metrics)_
- The current trainer reports training loss, the realized learning rate, iterations per second, tokens per second, cumulative trained tokens, and peak memory; validation reports validation loss and elapsed time at the first iteration, configured evaluation intervals, and the final iteration. verified-as-of: 2026-10-23[^c3-6][^c3-2] _(MLX-LM training configuration optimization and metrics)_
- The current schedule builder uses the named MLX optimizer schedule with the configured arguments; when warmup is enabled, it linearly ramps from warmup_init to arguments[0] and joins the main schedule at warmup_steps + 1. Inspect the logged learning rate to verify that the configured schedule follows the intended trajectory. verified-as-of: 2026-10-23[^c3-7][^c3-6] _(MLX-LM training configuration optimization and metrics)_
- Learning-rate selection is consequential and should be tested for the model and run: an LLM learning-rate study argues that policies designed for traditional DNN training may not transfer directly, and a reported mlx-lm 0.31.3 case saw one 1e-4 run produce 162 errors on a held-out task versus 18 errors in a later 1e-5 run. The author notes that the example order also changed and there was only one run per setting, so it does not establish a universal rate or isolate learning rate as the sole cause. (two sources)[^c3-9][^c3-3] _(MLX-LM training configuration optimization and metrics)_
- Training or validation loss alone can misstate task quality: in the reported mlx-lm 0.31.3 case, validation loss reached 0.39 while held-out macro-F1 fell to 0.05–0.09 from 0.64–0.78 for the untrained model; a separate BERT fine-tuning study also found different test performance among runs with the same training loss. Pair loss curves with metrics that represent the intended task. (two sources)[^c3-3][^c3-10] _(MLX-LM training configuration optimization and metrics)_
- MLX-LM's memory guide says `--grad-accumulation-steps N` accumulates gradients across N batches before updating, so users can keep each microbatch small while increasing effective batch size without increasing batch memory; Hugging Face's training documentation describes the same effective-batch relationship. verified-as-of: 2026-10-23[^c4-1][^c4-8][^c4-5][^c4-3] _(MLX-LM training memory and gradient control)_
- MLX-LM's `--grad-checkpoint` trades extra computation for lower activation memory by recomputing intermediate values needed during backpropagation; its guide says the option is more helpful with larger batches or sequences. Framework documentation describes the same recomputation tradeoff and notes that checkpoint placement affects peak-memory savings. verified-as-of: 2026-10-23[^c4-5][^c4-2][^c4-6][^c4-1][^c4-3] _(MLX-LM training memory and gradient control)_

## Practical Patterns

- Quality parity is task-dependent. The original LoRA paper reports on-par or better quality than full tuning on its evaluated RoBERTa, DeBERTa, GPT-2, and GPT-3 tasks, and the QLoRA paper reports preserving full 16-bit fine-tuning task performance on its evaluations. In contrast, an EAMT study of Llama-2 13B for business translation found full tuning superior to LoRA and QLoRA; its 4-bit QLoRA preliminary results were unsatisfactory, so the reported experiments used 8-bit QLoRA. (two sources)[^c1-3][^c1-4][^c1-10] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- Pass the base model through --model <local_directory_or_Hugging_Face_repo>. --fine-tune-type accepts lora, dora, and full; fine_tune_type defaults to lora. These choices select adaptation mechanics; a quantized base is supplied as the model rather than selected by a separate qlora fine_tune_type. (two sources) verified-as-of: 2026-10-23[^c1-13][^c1-14] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- Configure adapter rank and module selection in YAML under lora_parameters: rank sets the low-rank dimension and keys supplies module paths such as self_attn.q_proj. Without keys, the converter discovers modules with to_lora or supported linear, switch-linear, and embedding types. --num-layers selects the last N model layers; -1 selects all. (two sources) verified-as-of: 2026-10-23[^c1-13][^c1-14][^c1-15][^c1-16] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- lora_parameters.scale directly multiplies the low-rank update; LoRALinear returns base_linear(x) + scale*((dropout(x) @ lora_a) @ lora_b). It does not divide scale by rank. lora_parameters.dropout is passed as nn.Dropout's probability on the adapter input. The entry-point defaults are rank=8, scale=20.0, dropout=0.0. (two sources) verified-as-of: 2026-10-23[^c1-13][^c1-15] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- Research does not establish completion-only loss as a universal optimum. The 2024 EMNLP study reports that useful prompt-token weights varied with generation length and benchmark, while the 2025 TACL study reports that the standard zero-prompt/full-response objective was often suboptimal across its tested models, datasets, and benchmarks; target-specific evaluation is needed before choosing masking. (two sources)[^c2-11][^c2-12] _(MLX-LM training datasets and prompt masking)_
- Tentative: A 2024 practitioner experiment using Llama-2-7b on a RACE subset reported that completion-only training reached 80% validation accuracy versus 75% with full-sequence loss and converged faster. The author cautioned that the result may not generalize beyond that dataset and setup.[^c2-10] _(MLX-LM training datasets and prompt masking)_
- Tentative: Use consistent JSONL row shapes: text records contain {"text":"..."}; completion records contain {"prompt":"...","completion":"..."}; chat records contain {"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}. prompt_feature and completion_feature rename completion columns; chat_feature and text_feature rename the other formats. verified-as-of: 2026-10-23[^c2-13] _(MLX-LM training datasets and prompt masking)_
- Tentative: mask-prompt removes loss on the prompt prefix. Completion masking templates the user prompt alone with add_generation_prompt=True to locate that prefix; chat masking templates all messages except the last. Chat and completion records support masking; text records raise ValueError("Prompt masking not supported for text dataset."). verified-as-of: 2026-10-23[^c2-13][^c2-14] _(MLX-LM training datasets and prompt masking)_
- Tentative: For memory-constrained training, the current guide recommends lowering --batch-size from its default of 4 to 2 or 1 at possible speed cost; --grad-accumulation-steps can increase effective batch size without increasing memory, and --grad-checkpoint trades memory for computation. verified-as-of: 2026-10-23[^c3-1] _(MLX-LM training configuration optimization and metrics)_
- The current MLX Adam and AdamW implementations default bias_correction to false. Treat optimizer settings as part of the run configuration when comparing learning-rate experiments or porting settings from another framework. verified-as-of: 2026-10-23[^c3-8][^c3-3] _(MLX-LM training configuration optimization and metrics)_
- Tentative: Load YAML training settings with --config <file.yaml> or -c <file.yaml>. main() copies each YAML value only when the parsed CLI value for that key is None, then fills remaining None values from CONFIG_DEFAULTS. Explicit non-None CLI values take precedence; parser defaults that are already non-None can also block a YAML override. verified-as-of: 2026-10-23[^c3-12] _(MLX-LM training configuration optimization and metrics)_
- Tentative: learning-rate sets the scalar learning rate. --optimizer accepts adam, adamw, muon, sgd, and adafactor. Put optimizer-specific keyword arguments such as weight_decay under optimizer_config.<optimizer_name> in YAML; the entry point passes that selected dictionary to the optimizer constructor. verified-as-of: 2026-10-23[^c3-12] _(MLX-LM training configuration optimization and metrics)_
- For a schedule, set lr_schedule.name to an mlx.optimizers.schedulers function and lr_schedule.arguments to its positional arguments. An optional warmup count builds a linear schedule from warmup_init (default 0.0) to arguments[0], then joins it to the requested schedule at warmup+1. A truthy lr_schedule takes precedence over the scalar learning_rate. (two sources) verified-as-of: 2026-10-23[^c3-12][^c3-13] _(MLX-LM training configuration optimization and metrics)_
- steps-per-report controls training report intervals; --steps-per-eval controls validation intervals; --val-batches -1 selects the entire validation iterator instead of a fixed number of batches. on_train_loss_report receives iteration, train_loss, learning_rate, iterations_per_second, tokens_per_second, trained_tokens, and peak_memory. (two sources) verified-as-of: 2026-10-23[^c3-12][^c3-14] _(MLX-LM training configuration optimization and metrics)_
- MLX-LM's guide also recommends reducing `--batch-size`, `--num-layers`, or example length to lower memory; it cautions that training fewer layers may reduce quality on data-heavy runs, while research treats microbatching and checkpointing as separate techniques with workload-dependent memory and compute tradeoffs. (two sources)[^c4-1][^c4-3] _(MLX-LM training memory and gradient control)_
- grad-checkpoint enables training gradient checkpointing. --batch-size reduces examples in each minibatch, while --num-layers reduces the last-layer subset selected for training. For one worker, batch_size B and --grad-accumulation-steps A combine A minibatches before an optimizer update, giving an effective example batch size B*A. (two sources) verified-as-of: 2026-10-23[^c4-9][^c4-10] _(MLX-LM training memory and gradient control)_
- Tentative: train() rejects grad_accumulation_steps below one with ValueError("grad_accumulation_steps must be at least 1"). It sums successive microbatch gradients; at an update it calls average_gradients, divides each accumulated gradient by grad_accumulation_steps when greater than one, then calls optimizer.update. verified-as-of: 2026-10-23[^c4-10] _(MLX-LM training memory and gradient control)_
- The --adapter-path option chooses the adapter directory. Training creates that directory and writes adapters.safetensors plus adapter_config.json there; --save-every controls the periodic checkpoint interval by populating TrainingArgs.steps_per_save. verified-as-of: 2026-10-23[^c5-14][^c5-15] _(MLX-LM adapter checkpoints fusion and export)_
- Use an unfused adapter for generation with mlx_lm.generate --model <base_model> --adapter-path <adapter_directory> --prompt "<prompt>". LORA.md documents --upload-repo as the fused-model upload destination and --hf-path as the original model for its card, but the pinned fuse.py parser has no --hf-path option. Treat that documented upload invocation as a guide/parser disagreement and inspect the installed mlx_lm.fuse --help before publishing. verified-as-of: 2026-10-23[^c5-15][^c5-16] _(MLX-LM adapter checkpoints fusion and export)_

## Anti-Patterns

- Chat masking computes one prefix offset from all messages except the final message. Earlier assistant actions in a multi-turn tool trace are therefore masked when a later tool result or answer follows them; a practitioner report documented this behavior and split rows so each assistant action became a final-message target. Keep the intended assistant target last in each row. (two sources) verified-as-of: 2026-10-23[^c2-2][^c2-1][^c2-6] _(MLX-LM training datasets and prompt masking)_
- Tentative: resume-adapter-file loads model weights with model.load_weights(..., strict=False). It does not restore optimizer state or a previous iteration counter in this entry point, so it is a weight-based continuation rather than a complete training-state restart. verified-as-of: 2026-10-23[^c5-14] _(MLX-LM adapter checkpoints fusion and export)_

## Troubleshooting

- Tentative: Before training, the entry point rejects num_layers greater than len(model.layers) with ValueError: Requested to train N layers but the model only has M layers. It freezes the model before selecting full-training layers or converting adapter modules. verified-as-of: 2026-10-23[^c1-13] _(MLX-LM LoRA and QLoRA versus full fine-tuning)_
- A CompletionsDataset prompt-masking crash was reported in issue #786 and addressed by PR #967, which merged into main on 2026-03-11 and changed the mask calculation to template a prompt-only message list. The current loader uses that prompt-only list when computing the completion offset. verified-as-of: 2026-10-23[^c2-7][^c2-8][^c2-2] _(MLX-LM training datasets and prompt masking)_
- Tentative: For local data, train.jsonl is the training split, valid.jsonl supplies validation, and test.jsonl supplies --test evaluation. A missing file becomes an empty split: the final loader rejects empty training/test splits when requested and warns for missing validation. A zero-line existing JSONL file instead reaches create_dataset(data[0]) without an empty-data guard and can fail before those final split checks; ensure every supplied split file has records. verified-as-of: 2026-10-23[^c2-13] _(MLX-LM training datasets and prompt masking)_
- Tentative: An mlx-lm issue reports that the same stated data and configuration produced different training and validation loss behavior after upgrading from 0.21.5 to 0.22.0. The thread does not establish the cause, so this is a version-specific user report rather than evidence of a confirmed regression.[^c3-11] _(MLX-LM training configuration optimization and metrics)_
- Tentative: A June 2025 user report recorded Metal `Insufficient Memory` at a reported 34.108 GB peak with batch size 1, `--grad-checkpoint`, and a 5,000-token maximum sequence; after reinstalling MLX-LM from source, the follow-up log reached iteration 100, so the report does not isolate a memory-control limit or give a portable capacity estimate.[^c4-4] _(MLX-LM training memory and gradient control)_
- Tentative: As of 2026-10-23, open MLX-LM issue #1206 contains reports of Qwen3.5 training OOM despite `--grad-checkpoint` on M5 Max and M3 Pro systems, alongside a base-M5 report that the OOM was not reproducible and training completed normally through iteration 5; treat this as configuration-specific evidence rather than a general memory limit. verified-as-of: 2026-10-23[^c4-7] _(MLX-LM training memory and gradient control)_
- Tentative: iterate_batches truncates examples longer than max_seq_length, emits a warning, and updates the recorded lengths to the truncated lengths. If the dataset contains fewer examples than batch_size, it raises ValueError stating that the dataset must have at least batch_size examples. Pre-split long examples and choose a batch size no larger than the dataset. verified-as-of: 2026-10-23[^c4-10] _(MLX-LM training memory and gradient control)_
- Two case reports show quantized fusion can change observed behavior: an independent test found a rank-8 adapter's behavior disappeared after fusion into a 4-bit base without `--dequantize`, while issue #654 reports that direct fusion changed hidden reasoning for `gpt_oss-20b` and that dequantizing before a separate 4-bit conversion restored it. These reports are model-specific and do not establish a general degradation rate; evaluate the target model after fusion. (two sources) verified-as-of: 2026-07-30[^c5-5][^c5-7][^c5-2] _(MLX-LM adapter checkpoints fusion and export)_
- On `mlx-lm` 0.31.3 with `mlx` 0.32.0, issue #1723 reported `[save_gguf] can only serialize row-major arrays` during `--export-gguf` because `save()` ignored `donate_model=False` and emptied weights before conversion. Upstream merged PR #1743 on 2026-08-17 to pass that flag through. Treat the error as version-specific and check the installed build before reapplying workarounds. verified-as-of: 2026-08-17[^c5-8][^c5-9][^c5-2] _(MLX-LM adapter checkpoints fusion and export)_
- Tentative: A 2026 llama.cpp issue reports that its separate `convert_hf_to_gguf.py` path rejected `lm_head.scales` and sometimes `lm_head.biases` in an MLX-fused artifact. That report is specific to the downstream converter and does not establish a failure in MLX-LM's built-in `--export-gguf` implementation.[^c5-13][^c5-2] _(MLX-LM adapter checkpoints fusion and export)_

## Disagreements & Open Questions

- Disagreement (MLX-LM LoRA and QLoRA versus full fine-tuning): The QLoRA paper reports preserving full 16-bit fine-tuning task performance in its evaluations, while a 2026 FLAN-T5 Query-DSL comparison reports lower average evaluation loss for full-precision fine-tuning. The studies use different models, data, and training setups, so the difference scopes the claims rather than forming a direct replication conflict.[^c1-4][^c1-8]
- Disagreement (MLX-LM LoRA and QLoRA versus full fine-tuning): Quality parity is not consistent across study settings: the QLoRA paper reports preserving full 16-bit fine-tuning task performance on its evaluations, while the EAMT business-translation study reports full fine-tuning ahead of QLoRA and finds 4-bit quantization hindered model fit in its setup.[^c1-4][^c1-10]
- Open (MLX-LM LoRA and QLoRA versus full fine-tuning): The pinned MLX-LM guide does not give one universal bit width or quantization format for all model checkpoints used with QLoRA; verify the selected checkpoint’s quantization settings.
- Open (MLX-LM LoRA and QLoRA versus full fine-tuning): Which MLX quantization formats and model families preserve task quality against full fine-tuning under matched data and training settings is not established by these sources.
- Disagreement (MLX-LM training datasets and prompt masking): A November 2024 mlx-examples discussion described an earlier iterator that did not preserve prompt/completion boundaries for loss masking. That is historical behavior: current MLX-LM docs and dataset code expose --mask-prompt and compute a prompt offset.[^c2-9][^c2-1][^c2-2]
- Disagreement (MLX-LM training datasets and prompt masking): The RACE practitioner experiment found that completion-only loss improved accuracy and convergence in its setup, while the broader studies report settings where nonzero prompt-token weights perform better. These results differ by data, model, and evaluation target and do not establish one universally best mask.[^c2-10][^c2-11][^c2-12]
- Open (MLX-LM training datasets and prompt masking): The dataset API masks one serialized prefix span. The upstream docs do not specify a native representation for supervising multiple assistant tool calls within one chat row.
- Open (MLX-LM training datasets and prompt masking): A Chinese-language tutorial search hit contained a prompt asking an assistant to clean local data and produce training files. It was treated as untrusted page content and was not followed.
- Open (MLX-LM training datasets and prompt masking): Which published MLX-LM release first includes the merged PR #967 fix was not verified; the review confirmed the merge date and current main-branch loader behavior.
- Disagreement (MLX-LM training configuration optimization and metrics): A reporter described cosine decay crossing the warmup boundary one step early in MLX 0.17.1 as a scheduler bug; the maintainer said a one-step boundary shift should not significantly affect the result. This old issue does not establish a defect in current releases.[^c3-5]
- Disagreement (MLX-LM training configuration optimization and metrics): A single mlx-lm 0.31.3 comparison associates the learning-rate change with a large held-out performance difference, but its author reports an unseeded example order and only one run per setting. The result does not isolate learning rate as the sole cause.[^c3-3]
- Open (MLX-LM training configuration optimization and metrics): Does the current MLX-LM learning-rate scheduler differ materially from the one-step warmup boundary behavior reported for MLX 0.17.1?
- Open (MLX-LM training configuration optimization and metrics): This pass found no controlled, multi-seed MLX-LM comparison that establishes a universally best learning rate, schedule, or optimizer across model families.
- Disagreement (MLX-LM training memory and gradient control): In issue #236, an early commenter attributed a 34 GB Metal failure on a 128 GB Mac to Metal allocation limits, while an MLX-LM maintainer replied that MLX can use all 128 GB; the reporter later said reinstalling from source let the run continue, but the cause was not isolated.[^c4-4]
- Disagreement (MLX-LM training memory and gradient control): The issue thread reports Qwen3.5 OOM despite checkpointing on some systems, while a later commenter could not reproduce the failure on a base M5; the thread does not establish a universal cause.[^c4-7]
- Open (MLX-LM training memory and gradient control): Issue #236 does not identify why the original installation aborted while the source installation continued, so the report cannot distinguish a build problem from a data-dependent allocation failure.
- Open (MLX-LM training memory and gradient control): Whether the Qwen3.5 backward-pass failures reflect model-specific live activation demand or Metal resource limits remains unresolved in issue #1206.
- Disagreement (MLX-LM adapter checkpoints fusion and export): The current LORA.md tells users to pass `--hf-path` to `mlx_lm.fuse` when uploading, but the current `fuse.py` argument parser has no `--hf-path` option; independent notes also flag the option as absent. The documented upload syntax and current parser therefore disagree.[^c5-1][^c5-2][^c5-5]
- Disagreement (MLX-LM adapter checkpoints fusion and export): InsiderLLM's guide spells the dequantization option `--de-quantize`, while current upstream `fuse.py` defines `--dequantize`; the guide's spelling does not match the current CLI.[^c5-12][^c5-2]
- Open (MLX-LM adapter checkpoints fusion and export): Whether `--hf-path` should be removed from the docs or restored in the CLI, and which upload invocation works across released versions.
- Open (MLX-LM adapter checkpoints fusion and export): Whether MLX-LM will add direct support for fusing a numbered checkpoint file; current loader code expects an adapter directory with a canonical filename.
- Open (MLX-LM adapter checkpoints fusion and export): How often quantized fusion changes task behavior across model families; the available reports are case-specific and do not provide a general rate.
- Open (MLX-LM adapter checkpoints fusion and export): The llama.cpp issue does not establish whether the reported `lm_head` tensor-mapping case still reproduces in later converter versions; it concerns one downstream conversion path and artifact.

## References

### MLX-LM LoRA and QLoRA versus full fine-tuning

[^c1-1]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/LORA.md — MLX-LM LoRA training documentation at pinned commit 0d4d3d04 (repo)
[^c1-2]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/README.md — MLX-LM README at pinned commit 0d4d3d04 (repo)
[^c1-3]: https://arxiv.org/abs/2106.09685 — LoRA: Low-Rank Adaptation of Large Language Models (paper)
[^c1-4]: https://arxiv.org/abs/2305.14314 — QLoRA: Efficient Finetuning of Quantized LLMs (paper)
[^c1-5]: https://arxiv.org/abs/2410.21228 — LoRA vs Full Fine-tuning: An Illusion of Equivalence (paper)
[^c1-6]: https://doi.org/10.64434/tml.20250929 — LoRA Without Regret (blog)
[^c1-7]: https://aclanthology.org/2024.lrec-main.206/ — Beyond Full Fine-tuning: Harnessing the Power of LoRA for Multi-Task Instruction Tuning (paper)
[^c1-8]: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1665992/full — An efficient strategy for fine-tuning large language models (paper)
[^c1-9]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md — MLX-LM LoRA training and fusion documentation (docs)
[^c1-10]: https://aclanthology.org/2024.eamt-1.51.pdf — Exploring the Effectiveness of LLM Domain Adaptation for Business IT Machine Translation (paper)
[^c1-11]: https://arxiv.org/abs/2605.19018 — LoRA vs. Full Fine-Tuning: A Theoretical Perspective (paper)
[^c1-12]: https://arxiv.org/pdf/2410.21228 — LoRA vs Full Fine-tuning: An Illusion of Equivalence (full paper) (paper)
[^c1-13]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — lora.py pinned primary (repo)
[^c1-14]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/utils.py — utils.py pinned primary (repo)
[^c1-15]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/lora.py — lora.py pinned primary (repo)
[^c1-16]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/examples/lora_config.yaml — examples/lora_config.yaml pinned source (repo)

### MLX-LM training datasets and prompt masking

[^c2-1]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md — MLX-LM LORA.md at main (docs)
[^c2-2]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/datasets.py — MLX-LM dataset loader source (repo)
[^c2-3]: https://huggingface.co/docs/transformers/en/chat_templating — Hugging Face Transformers chat templates documentation (docs)
[^c2-4]: https://aclanthology.org/2026.tacl-1.17.pdf — Fine-tuning Large Language Models with Limited Data: A Survey and Practical Guide (PDF) (paper)
[^c2-5]: https://aclanthology.org/2026.tacl-1.17/ — Fine-tuning Large Language Models with Limited Data: A Survey and Practical Guide (ACL Anthology) (paper)
[^c2-6]: https://justinbarias.io/blog/notes-from-fine-tuning-a-tekken-coach/ — Notes From Fine-Tuning a Tekken Coach (blog)
[^c2-7]: https://github.com/ml-explore/mlx-lm/issues/786 — Problem with CompletionsDataset and mask-prompt (forum)
[^c2-8]: https://github.com/ml-explore/mlx-lm/pull/967 — Fix CompletionsDataset mask_prompt crash (repo)
[^c2-9]: https://github.com/ml-explore/mlx-examples/discussions/1086 — Discussion 1086: ignoring input tokens in LoRA training (forum)
[^c2-10]: https://dsssolutions.com/to-mask-or-not-to-mask-the-effect-of-prompt-tokens-on-instruction-tuning/ — To Mask or Not to Mask: The Effect of Prompt Tokens on Instruction Tuning (blog)
[^c2-11]: https://aclanthology.org/2024.emnlp-main.1267/ — Instruction Fine-Tuning: Does Prompt Loss Matter? (paper)
[^c2-12]: https://aclanthology.org/2025.tacl-1.62/ — On the Effect of Instruction Tuning Loss on Generalization (paper)
[^c2-13]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/datasets.py — datasets.py pinned primary (repo)
[^c2-14]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/trainer.py — mlx_lm/tuner/trainer.py pinned source (repo)

### MLX-LM training configuration optimization and metrics

[^c3-1]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md — MLX-LM training guide (current main) (repo)
[^c3-2]: https://developer.apple.com/videos/play/wwdc2025/298/ — Explore large language models on Apple silicon with MLX (WWDC25 session 298) (docs)
[^c3-3]: https://vincentvandeth.nl/blog/lora-fine-tuning-mlx-lm-qwen35-mac-mini — LoRA Fine-Tuning Qwen3.5 with mlx-lm: 162 Wrong Answers, Then 18 (blog)
[^c3-4]: https://blog.amsayed.dev/blog/local-llm-evaluation-testing — Testing Your Fine-Tuned Model: Did It Actually Learn? (blog)
[^c3-5]: https://github.com/ml-explore/mlx/issues/2617 — Cosine decay starts during warmup phase, issue 2617 (forum)
[^c3-6]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/trainer.py — MLX-LM tuner trainer implementation (repo)
[^c3-7]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/utils.py — MLX-LM tuner schedule utilities (repo)
[^c3-8]: https://github.com/ml-explore/mlx/blob/main/python/mlx/optimizers/optimizers.py — MLX optimizer implementation (repo)
[^c3-9]: https://arxiv.org/abs/2309.08859 — Rethinking Learning Rate Tuning in the Era of Large Language Models (paper)
[^c3-10]: https://arxiv.org/abs/2006.04884 — On the Stability of Fine-tuning BERT: Misconceptions, Explanations, and Strong Baselines (paper)
[^c3-11]: https://github.com/ml-explore/mlx-lm/issues/18 — Weird validation and train values after upgrade from 0.21.5 to 0.22 (forum)
[^c3-12]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — lora.py pinned primary (repo)
[^c3-13]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/utils.py — utils.py pinned primary (repo)
[^c3-14]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/trainer.py — trainer.py pinned primary (repo)

### MLX-LM training memory and gradient control

[^c4-1]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/LORA.md — MLX-LM training memory guidance at pinned commit (repo)
[^c4-2]: https://huggingface.co/docs/transformers/v5.10.1/en/grad_checkpointing — Hugging Face Transformers gradient checkpointing guide v5.10.1 (docs)
[^c4-3]: https://arxiv.org/abs/1904.10631 — Low-Memory Neural Network Training: A Technical Report (paper)
[^c4-4]: https://github.com/ml-explore/mlx-lm/issues/236 — Why Does Memory Error Occur During Training? #236 (forum)
[^c4-5]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md — MLX-LM training and memory guidance at main (repo)
[^c4-6]: https://pytorch.org/blog/activation-checkpointing-techniques/ — Current and New Activation Checkpointing Techniques in PyTorch (blog)
[^c4-7]: https://github.com/ml-explore/mlx-lm/issues/1206 — Qwen3.5 training OOM issue #1206 (forum)
[^c4-8]: https://huggingface.co/docs/accelerate/usage_guides/gradient_accumulation — Hugging Face Accelerate: Performing gradient accumulation (docs)
[^c4-9]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — lora.py pinned primary (repo)
[^c4-10]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/trainer.py — trainer.py pinned primary (repo)

### MLX-LM adapter checkpoints fusion and export

[^c5-1]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md — MLX-LM LoRA training guide at main (docs)
[^c5-2]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/fuse.py — MLX-LM fuse command implementation (repo)
[^c5-3]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/utils.py — MLX-LM adapter checkpoint loader (repo)
[^c5-4]: https://developer.apple.com/videos/play/wwdc2025/298/ — Explore large language models on Apple silicon (WWDC25) (docs)
[^c5-5]: https://git.spboucher.ai/zyquo-mlx/blob/main/docs/TRAINING-RESEARCH.md — ZYQUO-MLX training research: fusion notes and empirical tests (repo)
[^c5-6]: https://notes.nicolasdeville.com/nicai/fine-tuning/ — Fine-tuning my own model (LLM): NicAI (blog)
[^c5-7]: https://github.com/ml-explore/mlx-lm/issues/654 — Discrepancy between dynamic adapters and fused model (forum)
[^c5-8]: https://github.com/ml-explore/mlx-lm/issues/1723 — MLX-LM fuse export row-major error report (forum)
[^c5-9]: https://github.com/ml-explore/mlx-lm/pull/1743 — Fix fuse GGUF export donation regression (forum)
[^c5-10]: https://github.com/ml-explore/mlx-lm/issues/447 — Unsupported model type gpt_oss for GGUF conversion (forum)
[^c5-11]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/trainer.py — MLX-LM tuner trainer implementation (repo)
[^c5-12]: https://insiderllm.com/guides/fine-tuning-mac-lora-mlx/ — Fine-tuning on Mac with MLX (blog)
[^c5-13]: https://github.com/ggml-org/llama.cpp/issues/22431 — GGUF conversion issue for MLX fused model (forum)
[^c5-14]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — Pinned primary source (repo)
[^c5-15]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/LORA.md — Pinned primary source (repo)
[^c5-16]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/fuse.py — Pinned primary source (repo)
