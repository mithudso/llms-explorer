<!-- hub-reference-banner -->
> **Reference file — part of the `mlx-lm-expert` hub.** Created by `/dr` deep research 2026-10-23; research dir `~/.global-ai-hub/research/mlx-lm-training-extensions-20261023`.

---
name: mlx-lm-training-extensions
description: "Explain native MLX-LM DoRA and distributed fine-tuning from source-qualified research. TRIGGER: DoRA quantized adapters; DoRALinear fusion; distributed training gradient averaging and accumulation; Ring and JACCL source differences. SKIP: training data and basic LoRA -> mlx-lm-expert training reference."
version: "1.0.0"
updated: "2026-10-23"
category: "research"
whenToUse:
  - "Understand native DoRA quantized adapters"
  - "Explain distributed fine-tuning gradient synchronization"
  - "Compare documented Ring and JACCL limits"
keywords: ["mlx-lm", "DoRA", "DoRALinear", "quantized adapters", "distributed training", "average_gradients", "gradient accumulation", "JACCL", "Ring"]
tags: ["mlx-lm", "training", "adapters", "distributed"]
provenance: "/dr · ~/.global-ai-hub/research/mlx-lm-training-extensions-20261023"
---

# MLX-LM DoRA and distributed training extensions

## Overview

DoRA separates a pretrained weight into direction and magnitude, using a low-rank update for direction and a trainable magnitude. In current MLX-LM Python code, DoRA wraps regular and quantized linear layers, but its quantized-base forward path dequantizes the weight and performs dense operations plus weight normalization on each call. Regular LoRA on a quantized base keeps the base layer's own forward call, which the MLX-LM guide describes as QLoRA. The dispatcher rejects MoE SwitchLinear variants for DoRA. This distinction matters because storing a base in quantized form does not guarantee that an unmerged DoRA adapter uses a quantized fast path. The DoRA paper's no-extra-inference-overhead statement and MLX-LM's unmerged adapter path describe different execution states.

MLX-LM distributed fine-tuning uses synchronous data parallelism: each worker holds a model replica, processes a rank-specific slice of the batch, computes gradients locally, then averages gradients across the distributed group before the optimizer update. The current trainer delays this collective until the update boundary when gradient accumulation is enabled. The multi-Mac CLI path uses mlx.launch, and MLX-LM shards data across workers. A September 2026 preprint studies all-reduce costs and gradient overlap for RDMA-over-Thunderbolt fine-tuning. A separate open GitHub issue reports possible repeated ring-backend collective failures on three or more ranks; treat that as an unconfirmed, version- and backend-specific report.

## Core Concepts

### MLX-LM native DoRA and quantized adapter mechanics

- DoRA reparameterizes pretrained weights into direction and magnitude, applying a low-rank LoRA update to direction while learning magnitude separately; MLX-LM's DoRALinear implements this with lora_a, lora_b, and a trainable per-output magnitude vector m.[^c1-5][^c1-1][^c1-8]
- For a QuantizedLinear base, MLX-LM's DoRALinear forward calls _dequantized_weight(), computes the base output with a dense x @ w.T, constructs the full adapted weight matrix, and computes its row norms on each call. A quantized base is therefore accepted, but the unmerged DoRA forward path does not preserve the base QuantizedLinear forward path; an independent practitioner report describes the same dequantization and dense-normalization behavior. verified-as-of: 2026-10-23[^c1-1][^c1-6][^c1-8]
- In MLX-LM's DoRALinear, the learned base magnitude is stored per output row; each forward pass adds the scaled low-rank update, computes the adapted row norms with stop_gradient, and rescales the output by the ratio of base magnitude to adapted norm. verified-as-of: 2026-10-23[^c1-1][^c1-5][^c1-8]
- For an nn.QuantizedLinear base, DoRALinear.from_base recovers the logical input dimension from the packed weight width using 32 // bits; DoRALinear then dequantizes weight, scales, and biases using the layer's group_size, bits, and mode for its forward calculation. verified-as-of: 2026-10-23[^c1-1][^c1-8]

### MLX-LM distributed fine-tuning and gradient synchronization

- The standard distributed fine-tuning arrangement is data parallel: ranks keep model replicas, process different data batches, and average gradients so replicas can apply matching updates; Apple's WWDC26 walkthrough and an independent multi-Mac guide describe this workflow. verified-as-of: 2026-10-23[^c2-1][^c2-5][^c2-2][^c2-3]
- Tentative: The October 4, 2026 v3 paper reports 936 tokens per second for four-node Qwen3-9B fine-tuning at sequence length 17,408, or 3.5x its single-node throughput; this is a weak-scaling result for that M3 Ultra setup with local batch size one, not a general speedup guarantee. verified-as-of: 2026-10-06[^c2-3][^c2-8]
- `mlx_lm.tuner.trainer.train()` initializes an MLX distributed group, computes local gradients with `nn.value_and_grad`, calls `average_gradients` on update steps, and passes the synchronized gradient tree to the optimizer.[^c2-2][^c2-1]

## Tools & Frameworks

- As of 2026-10-23, MLX-LM exposes fine_tune_type=dora and maps nn.Linear and nn.QuantizedLinear layers to DoRALinear; its dispatcher raises for SwitchLinear and QuantizedSwitchLinear, so native DoRA conversion does not cover those MoE layer types. verified-as-of: 2026-10-23[^c1-2][^c1-4][^c1-7][^c1-8] _(MLX-LM native DoRA and quantized adapter mechanics)_
- MLX-LM exposes `--fine-tune-type dora` and maps nn.Linear and nn.QuantizedLinear targets to DoRALinear; its DoRALinear.fuse merges the low-rank delta and magnitude scaling, then requantizes a quantized layer with its original group_size, bits, and mode unless dequantize=True. verified-as-of: 2026-10-23[^c1-4][^c1-2][^c1-1][^c1-8] _(MLX-LM native DoRA and quantized adapter mechanics)_
- Apple's WWDC26 walkthrough launches distributed fine-tuning with `mlx.launch` and `mlx_lm.lora`; an independent community repository also documents multi-node `mlx-lm` LoRA runs through `mlx.launch --hostfile`, with Ring and JACCL setup examples. (two sources) verified-as-of: 2026-10-23[^c2-1][^c2-5] _(MLX-LM distributed fine-tuning and gradient synchronization)_

## Methodology

- The current trainer treats `batch_size` as the distributed global batch: it partitions examples by rank and creates each worker's local batch with `batch_size // world_size`, rejecting batch sizes that are not divisible by the worker count. Apple's walkthrough accordingly scales `--batch-size` with the device count to preserve the same per-worker batch. verified-as-of: 2026-10-23[^c2-2][^c2-1] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- Distributed fine-tuning and model-parallel inference are separate paths: Apple's WWDC26 walkthrough presents `mlx_lm.lora` fine-tuning as data parallel, while Matt Beton describes pipeline-parallel training as a separate `mlx-train` implementation with custom stage-boundary gradient flow.[^c2-1][^c2-7] _(MLX-LM distributed fine-tuning and gradient synchronization)_

## Practical Patterns

- For ordinary LoRA on a quantized base, MLX-LM retains the wrapped base layer and calls self.linear(x) before adding the low-rank branch; its guide calls LoRA training on a quantized model QLoRA. This preserves the base module's own forward implementation, unlike DoRALinear's explicit full-weight dequantization path. verified-as-of: 2026-10-23[^c1-3][^c1-4][^c1-1] _(MLX-LM native DoRA and quantized adapter mechanics)_
- The fine-tuning entry point calls model.freeze() before converting selected layers to DoRA. The new DoRA wrapper introduces trainable lora_a, lora_b and magnitude m while retaining the frozen pretrained base layer; full fine-tuning instead explicitly unfreezes selected base layers. verified-as-of: 2026-10-23[^c1-9][^c1-10][^c1-11] _(MLX-LM native DoRA and quantized adapter mechanics)_
- Tentative: DoRALinear uses scale directly: z=(dropout(x) @ lora_a) @ lora_b and out=x @ w.T + scale*z before magnitude normalization. The adapted weight is w + (scale*lora_b.T) @ lora_a.T. This code does not divide scale by rank; its quantized base w comes from mx.dequantize. verified-as-of: 2026-10-23[^c1-10] _(MLX-LM native DoRA and quantized adapter mechanics)_
- The MLX-LM trainer adds local gradient trees across accumulation microbatches, synchronizes them with `average_gradients` only when an update is due, divides by the accumulation-step count, and then updates the optimizer; MLX's distributed guide recommends `average_gradients` because it batches many small communications into a larger one. verified-as-of: 2026-10-23[^c2-2][^c2-6][^c2-3] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- The v3 research paper describes a non-overlapped data-parallel baseline with gradient all-reduce after backpropagation. Its modified JACCL path queues gradients as layers finish and uses a separate CPU consumer thread to reduce ready gradients while GPU backpropagation continues. This is the paper's research implementation; the stock MLX-LM trainer source alone does not establish this overlap. (two sources) verified-as-of: 2026-10-06[^c2-2][^c2-3][^c2-8] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- Tentative: A 2026 research paper describes extending Apple's distributed fine-tuning implementation with multi-trunk communication, persistent worker threads, and CPU-side gradient overlap; for a four-node Mac Studio Qwen3-9B run, its authors report up to 1.6× weak-scaling throughput over a single-trunk, non-overlapped baseline. verified-as-of: 2026-10-04[^c2-3] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- Tentative: iterate_batches first sorts dataset indices by sequence length. For each complete global batch starting at i, rank r of W workers takes idx[i+r:i+r+batch_size:W]; it then permutes batch order, using the supplied seed if present. It allocates batch_size//W local rows and omits the incomplete trailing global batch. verified-as-of: 2026-10-23[^c2-9] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- Tentative: At training report time, train() all-sums each rank's accumulated losses on the CPU stream and divides by steps*world_size. It separately all-sums n_tokens, computes tokens_per_second from that global count divided by local measured train_time, and adds the global token count to trained_tokens. This training-loss report averages per-step losses across ranks rather than using the token-weighted validation formula. verified-as-of: 2026-10-23[^c2-9] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- Tentative: Only rank zero writes periodic adapter snapshots and the final adapter weights. Periodic saves write both args.adapter_file and a seven-digit iteration-named *_adapters.safetensors checkpoint from model.trainable_parameters(); the final save writes args.adapter_file. verified-as-of: 2026-10-23[^c2-9] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- Tentative: evaluate() accumulates loss*tokens and token counts for local validation batches. It all-sums both accumulators across workers on the CPU stream and returns total_weighted_loss/total_tokens, giving a token-weighted validation loss across the distributed evaluation. verified-as-of: 2026-10-23[^c2-9] _(MLX-LM distributed fine-tuning and gradient synchronization)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- Tentative: A practitioner report dated 2026-08-08 measured 4.1 tokens/s for one DoRA adapter on a 4-bit Qwen base on an M5 Max and about 33 tokens/s after fusing the adapter or switching to LoRA. These are setup-specific measurements, not a portable speed ratio. verified-as-of: 2026-08-08[^c1-6] _(MLX-LM native DoRA and quantized adapter mechanics)_
- The adapter converter routes nn.QuantizedEmbedding to DoRAEmbedding, but DoRAEmbedding.from_base explicitly checks for nn.QuantizedLinear rather than nn.QuantizedEmbedding; the independent guide flags that the packed embedding path can therefore miss the intended guard and fail later on shape mismatch, so quantized embedding targets need version-specific verification. (two sources) verified-as-of: 2026-10-23[^c1-2][^c1-1][^c1-8] _(MLX-LM native DoRA and quantized adapter mechanics)_
- DoRAEmbedding.from_base contains the exact error message "DoRAEmbedding does not yet support quantization." Its guard tests nn.QuantizedLinear rather than nn.QuantizedEmbedding, although the converter selects DoRAEmbedding for nn.QuantizedEmbedding. Do not interpret the message as proof that every quantized embedding is rejected cleanly. verified-as-of: 2026-10-23[^c1-10][^c1-11] _(MLX-LM native DoRA and quantized adapter mechanics)_
- Tentative: An issue report opened 2026-09-08 records intermittent failures in `mlx==0.32.2` ring-backend gradient reductions at three or more ranks, including CPU-stream deadlocks and a GPU-stream watchdog timeout; it documents a reporter's reproduction and does not establish behavior for other releases or backends. verified-as-of: 2026-09-08[^c2-4] _(MLX-LM distributed fine-tuning and gradient synchronization)_
- The captured MLX distributed guide describes a closed TCP ring and lists JACCL, MPI and NCCL backends. It says JACCL requires a fully connected mesh, while the captured WWDC26 transcript says JACCL supports both mesh and ring topologies. These sources disagree about JACCL topology support; neither establishes an unqualified restriction across versions.[^c2-6][^c2-1] _(MLX-LM distributed fine-tuning and gradient synchronization)_

## Disagreements & Open Questions

- Disagreement (MLX-LM native DoRA and quantized adapter mechanics): The DoRA paper says DoRA adds no inference overhead, while MLX-LM's unmerged DoRALinear performs dequantization, dense matrix operations, and normalization at runtime. These statements describe different execution states: the paper's claim concerns merged inference, while the MLX-LM code shows the live adapter path.[^c1-5][^c1-1]
- Open (MLX-LM native DoRA and quantized adapter mechanics): Will MLX-LM add a quantized DoRA forward path that avoids dequantizing the full base weight on every call?
- Open (MLX-LM native DoRA and quantized adapter mechanics): How does unmerged quantized DoRA throughput vary across model families, bit widths, and Apple hardware? This probe found one practitioner measurement but no controlled cross-model benchmark.
- Open (MLX-LM native DoRA and quantized adapter mechanics): Does MLX-LM's generic LORA.md statement that quantized-base training uses QLoRA intend to include --fine-tune-type dora, given that DoRALinear dequantizes the dense base weight during each forward calculation?
- Open (MLX-LM distributed fine-tuning and gradient synchronization): The September 2026 MLX issue targets the Ring backend with a synthetic gradient tree and three or more ranks. Whether maintainers confirmed or resolved it after the captured issue state is not established here.
- Open (MLX-LM distributed fine-tuning and gradient synchronization): The paper's throughput results use a four-node M3 Ultra cluster and a customized JACCL backend. Performance on other hardware, network topologies, model sizes, and the unmodified default path remains unverified.
- Open (MLX-LM distributed fine-tuning and gradient synchronization): The cited ring-backend failure report is pinned to mlx 0.32.2; whether later MLX releases still reproduce it is unresolved here.

## References

### MLX-LM native DoRA and quantized adapter mechanics

[^c1-1]: https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/tuner/dora.py — MLX-LM native DoRA layer implementation (repo)
[^c1-2]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/utils.py — MLX-LM adapter layer dispatch (repo)
[^c1-3]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/lora.py — MLX-LM LoRA and quantized LoRA layers (repo)
[^c1-4]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md — MLX-LM LoRA and QLoRA documentation (docs)
[^c1-5]: https://arxiv.org/abs/2402.09353 — DoRA: Weight-Decomposed Low-Rank Adaptation (paper)
[^c1-6]: https://justinbarias.io/blog/notes-from-fine-tuning-a-tekken-coach/ — Notes From Fine-Tuning a Tekken Coach (blog)
[^c1-7]: https://github.com/ml-explore/mlx/issues/3435 — Missing precompiled Metal kernel for MoE gather_mm during LoRA/DoRA training (forum)
[^c1-8]: https://hbmartin.github.io/Foundation-Models-and-Core-AI-and-MLX-skills/part-12-mlx-python/references/06-finetuning-and-porting-models/ — LoRA and DoRA fine-tuning, and adding a new architecture (blog)
[^c1-9]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/lora.py — lora.py pinned MLX-LM source (repo)
[^c1-10]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/dora.py — dora.py pinned MLX-LM source (repo)
[^c1-11]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/utils.py — utils.py pinned MLX-LM source (repo)

### MLX-LM distributed fine-tuning and gradient synchronization

[^c2-1]: https://developer.apple.com/videos/play/wwdc2026/233/ — Explore distributed inference and training with MLX (WWDC26) (docs)
[^c2-2]: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/trainer.py — MLX-LM tuner trainer implementation (repo)
[^c2-3]: https://arxiv.org/abs/2609.18066 — Towards Training Private LLMs: Exploring Fine-Tuning Language Models on Apple Silicon with RDMA over Thunderbolt (paper)
[^c2-4]: https://github.com/ml-explore/mlx/issues/4475 — MLX ring backend gradient-shaped all_sum deadlock report (forum)
[^c2-5]: https://github.com/RavenXAILabs/mlx-distributed-lora/ — Distributed LoRA Training on Apple Silicon with MLX and JACCL (repo)
[^c2-6]: https://github.com/ml-explore/mlx/blob/main/docs/src/usage/distributed.rst — MLX Distributed Communication documentation (docs)
[^c2-7]: https://mattbeton.com/blog/pipeline-parallel-apple-silicon.html — Pipeline Parallel Training with Apple Silicon (blog)
[^c2-8]: https://arxiv.org/html/2609.18066v3 — Towards Training Private LLMs full paper v3 (paper)
[^c2-9]: https://raw.githubusercontent.com/ml-explore/mlx-lm/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d/mlx_lm/tuner/trainer.py — trainer.py pinned MLX-LM source (repo)
