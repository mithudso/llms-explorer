---
title: "Distributed Training &amp; Training Infrastructure"
description: "> Hub reference under ai-agent-engineering (hub-and-spoke). Owns the LLM training-infrastructure layer: how you split a model + optimizer + activations across many GPUs to TRAIN it. Loaded on demand w"
---

# Distributed Training & Training Infrastructure

> Hub reference under `ai-agent-engineering` (hub-and-spoke). Owns the LLM **training-infrastructure** layer: how you split a model + optimizer + activations across many GPUs to TRAIN it. Loaded on demand when the hub routing row matches. Local copy: `~/.claude/skills/ai-agent-engineering/references/distributed-training.md`.

Training a modern LLM does not fit on one GPU. A 70B model in BF16 is 140 GB of weights alone; add Adam optimizer states (≈12 bytes/param → 840 GB), gradients (another 140 GB), and activations, and you are far past any single accelerator's 80–192 GB. **Distributed training is the discipline of splitting the four things that consume GPU memory — parameters, gradients, optimizer states, and activations — across tens to tens of thousands of GPUs, while keeping the math identical to single-device training and keeping the expensive accelerators busy.**

**The one mental model that unlocks everything:** every parallelism strategy is a different answer to "what do we split, and what must we therefore communicate?"

- **Data parallel** — split the *batch*; replicate the model; communicate *gradients* (all-reduce).
- **Sharded data parallel (FSDP / ZeRO)** — split the *model states* too; communicate *parameters* (all-gather) on demand + *gradients* (reduce-scatter).
- **Tensor parallel** — split *layers / matmuls*; communicate *activations* every layer (high bandwidth → keep inside one NVLink node).
- **Pipeline parallel** — split *layers into stages*; communicate *activations* at stage boundaries (point-to-point); introduces the *bubble*.
- **Sequence / context parallel** — split the *sequence dimension*; communicate *attention* partials (unlocks long context).
- **Expert parallel** — split *MoE experts*; communicate *tokens* (all-to-all).

## Concepts covered (MECE, 12)

1. **Data parallelism & DDP** — replicate model, all-reduce gradients; PyTorch DDP gradient bucketing (~25 MB) + backward/comm overlap; scales throughput not model size (the reason FSDP/ZeRO exist); ring all-reduce moves `2·(N-1)/N·|params|`.
2. **ZeRO** — partition training states across the DP group: Stage 1 (optimizer states, ~4×), Stage 2 (+gradients, ~8×), Stage 3 (+parameters, linear in DP degree, ~1.5× comm). ZeRO-Offload (CPU RAM), ZeRO-Infinity (CPU+NVMe) for capacity. ZeRO-3 ≈ FSDP.
3. **FSDP & FSDP2** — PyTorch-native ZeRO-3. FSDP1 FlatParameter (deprecated) → FSDP2 per-parameter DTensor (`fully_shard`): communication-free sharded state dicts, mixed dtypes (FP8) in one model, partial freezing → LoRA composes. HSDP (`HYBRID_SHARD`) shards within node, replicates across nodes.
4. **Tensor parallelism** — Megatron column/row matmul split; two all-reduces of full activation per block per direction → kept inside one NVLink node (TP ≤ 8). **Sequence parallelism** shards the inter-matmul norm/dropout regions along the sequence dim (paired with TP).
5. **Pipeline parallelism** — contiguous layer stages, P2P at boundaries; the **bubble** (idle fill/drain). GPipe bubble ≈ `(P-1)/m`; 1F1B caps in-flight activations; interleaved 1F1B (virtual stages) shrinks bubble by `v`; Seq1F1B / zero-bubble / DualPipe (DeepSeek-V3) push further.
6. **Context / sequence parallelism** — shard the sequence across GPUs for 100K–1M+ tokens. Ring Attention (rotate K/V, overlap P2P) and DeepSpeed-Ulysses (all-to-all, head-subset attention); USP combines both (2D). Cuts attention memory up to ~87.5%.
7. **3D / ND parallelism** — compose TP × PP × CP × EP × DP. Placement heuristic: **TP innermost (NVLink), then CP, then PP across nodes, then DP/FSDP outermost.** `micro_batch × grad_accum × DP = global batch`; `TP×PP×CP×EP×DP = total GPUs`. Llama 8B = FSDP2; 405B = TP×PP×CP×DP; DeepSeek-V3 = EP×PP×DP.
8. **Mixed precision** — FP16 (narrow range → needs dynamic loss scaling); **BF16** (FP32-range, no loss scaling, the pretraining default); **FP8** (Hopper/Blackwell + Transformer Engine, ~42% memory / ~64% faster vs BF16, needs per-tensor `DelayedScaling`). Keep master weights + moments in FP32.
9. **Gradient checkpointing & accumulation** — recompute activations in backward (trade compute for memory, ~`O(√L)`); **selective** recompute (Megatron) checkpoints only memory-heavy/cheap-to-recompute ops. Gradient accumulation decouples global batch from memory; wrap non-final micro-steps in `no_sync()` under DDP/FSDP.
10. **Collective communication** — NCCL AllReduce (=reduce-scatter+all-gather), ReduceScatter (FSDP grad), AllGather (FSDP param / TP+SP), All-to-All (MoE / Ulysses), P2P (pipeline). Ring (bandwidth-optimal, large msgs) vs Tree (`O(log N)` latency, small msgs). **Compute-comm overlap** (prefetch, async-TP) is the main scaling lever.
11. **Training stability** — loss spikes/NaN; LR **warmup** (ramp from ~0); **z-loss** (push softmax normalizer → 0, curb logit growth) + QK-LayerNorm; scaled init (`1/√(2·n_layers)`); global-norm grad clip + ZClip; checkpoint-often + roll-back-and-curate recovery.
12. **Distributed checkpointing, frameworks & MFU** — PyTorch DCP saves per-rank shards (DTensor), async writes (5–15× less overhead), resharding on load. Frameworks: torchtitan, Megatron-Core, DeepSpeed, NeMo, MosaicML Composer. **MFU** = observed ÷ peak FLOPs (`6N` per token); 35–55% healthy (PaLM 46%, MegaScale 55.2% @ 12,288 GPUs); HFU counts recompute, so HFU > MFU when checkpointing.

## Boundaries (defers to siblings — no duplication)

- **Inference / serving parallelism** (vLLM/SGLang TP+PP, paged KV, continuous batching) → `llm-inference-serving`. Serving has no backward pass, no optimizer state, no gradient sync.
- **GPU kernels / CUDA / Triton / roofline / occupancy** → GPU-kernels reference (pointer only). Kernels are a black box here.
- **LoRA / QLoRA single-GPU fine-tuning depth** → `llm-fine-tuning-peft`. FSDP2+LoRA composition is noted here; LoRA mechanics live there.
- **Attention / MoE-routing / norm architecture** → `transformer-architecture`. EP *placement* is a parallelism axis here; MoE routing math is there.
- **Pretraining objectives, data mixtures, scaling laws (Chinchilla)** → pretraining reference (pointer only). This reference covers the *systems* of training.

## Sources

35+ primary docs and papers (2024–2026): PyTorch FSDP2 `fully_shard` docs + FSDP VLDB'23 paper + FSDP blog; DeepSpeed ZeRO tutorial/docs + ZeRO-Infinity; Megatron-LM SC'21 + Megatron-Core parallelism guide + pipeline schedules; torchtitan repo + ICLR 2025 paper; NVIDIA NeMo DeepSeek-V3 recipe + activation-recomputation docs; NCCL collectives docs + deep-dive blog; PyTorch Distributed Checkpoint blog + async recipe; arXiv 2205.05198 (activation recompute), 2405.07719 (unified SP), 2406.03488 (Seq1F1B), 2310.18313 (FP8-LM), 2411.08719 (FP8 vs BF16), 2410.19313 (COAT), 2410.16682 (stability), 2504.02507 (ZClip), 2402.15627 (MegaScale), NeurIPS 2024 (LR warmup). Full citation list in the local reference file.
