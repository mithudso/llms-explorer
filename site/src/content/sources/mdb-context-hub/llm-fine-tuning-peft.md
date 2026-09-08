---
title: "LLM Fine-Tuning &amp; PEFT"
description: "Adapting a pretrained LLM to a specific task, domain, format, or behavior by"
---

# LLM Fine-Tuning & PEFT

Adapting a pretrained LLM to a specific task, domain, format, or behavior by
**continuing training on labeled examples** — and doing it cheaply with
**parameter-efficient fine-tuning (PEFT)**, which freezes the base model and
trains a tiny set of new weights instead of all of them.

Five things this reference answers:

1. **Should I even fine-tune?** Full FT vs PEFT vs RAG vs prompting.
2. **How does LoRA work, and how do I set its knobs?** rank, alpha, target modules, init.
3. **Which PEFT method?** LoRA family (QLoRA / DoRA / rsLoRA / LoRA+), adapters, (IA)^3, prefix/P-tuning/prompt-tuning.
4. **How do I run it?** The HuggingFace PEFT workflow, SFT data prep + chat templating, the tooling stack.
5. **How do I ship it?** Merge vs swap for serving, catastrophic-forgetting mitigation, and evaluating the result.

## Scope boundary (read first)

- **This reference = supervised fine-tuning + the PEFT method zoo.** SFT data
  preparation and chat templating are **here** because they are the input to any
  fine-tune (PEFT or full).
- **Preference optimization / RLHF / DPO** — turning a *preference* signal
  (pairwise comparisons, reward models) into model behavior — is the sibling
  **`references/llm-alignment-post-training.md`**. SFT is the post-training *base
  step* that precedes RLHF/DPO; once you have preference data, go there. The
  DPO-variant family, PPO loop, reward modeling, and alignment eval all live there.
- **Quantization algorithm internals.** QLoRA fine-tunes LoRA adapters on top of a
  frozen **4-bit NF4** base. The NF4 data type, double quantization, and the
  PTQ/QAT landscape are the sibling **`references/llm-compression.md`** reference —
  this reference treats NF4 as a black-box dependency of QLoRA.
- **Multi-LoRA *serving runtime*.** Deciding **merge vs swap** and what an adapter
  costs at inference is here. Tuning the *engine* that serves many adapters
  (S-LoRA/Punica kernels inside vLLM, PagedAttention, continuous batching,
  autoscaling) is the sibling **`references/llm-inference-serving.md`**.
- **Offline benchmark-harness mechanics** (running MMLU/HELM, LLM-as-judge
  scaffolding) → `da-7-machine-learning`. The *fine-tune-specific* eval design
  (held-out task set + base-model regression check) is here.
- **Reasoning RL** (GRPO/RLVR/DeepSeek-R1-style) is neither SFT nor preference
  optimization → the reasoning-models material (pointer only).

---

## Part 1 — Should you fine-tune at all? (the decision framework)

Fine-tuning is the **most expensive and slowest** of the three adaptation levers.
Climb the ladder; stop at the first rung that clears your quality bar.

| Lever | Changes | Cost / time | Best at | Cannot |
| --- | --- | --- | --- | --- |
| **Prompt engineering** | The input only | Hours; ~free | Fast iteration, behavior you can describe in instructions + few-shot | Enforce format/style *reliably* at scale; teach genuinely new skills |
| **RAG** | The input (adds retrieved context) | Days; infra + per-query retrieval cost | Injecting **fresh / proprietary / large** factual knowledge; citations; data that changes | Change *behavior*, *style*, *format*, or *reasoning patterns* |
| **Fine-tuning** | The weights | Weeks; training + 6x-ish inference if you add an adapter layer | **Behavior / format / style / tone / domain reasoning**; distilling a big model's behavior into a cheaper small one | Add facts that change daily (they bake in stale); fix a problem RAG+prompting already solves |

**The canonical order (2025 consensus):** start with prompt engineering →
add RAG when you need current/proprietary *knowledge* → fine-tune only when
behavior stays inconsistent *after* prompts and RAG, or when a **small fine-tuned
model is cheaper than a large general one** on your narrow task.

**Knowledge vs behavior is the load-bearing distinction.** RAG is for *what the
model knows*; fine-tuning is for *how the model acts*. Fine-tuning is a poor way
to inject facts (they go stale and the model still hallucinates around them) and
RAG is a poor way to fix formatting/tone.

**They compose.** The highest-performing production systems often do **both**:
fine-tune to shape behavior/format/domain reasoning, RAG to supply current facts
at inference. Fine-tuning and RAG are not mutually exclusive.

**Good fine-tune use cases:** consistent structured output prompts can't enforce;
domain-specific reasoning absent from pretraining; style/tone calibration beyond
what prompts achieve; **cost optimization** (a fine-tuned 8B beating a prompted
70B on your task at a fraction of the inference cost); behavior cloning / distillation.

---

## Part 2 — Full fine-tuning vs PEFT

**Full fine-tuning (FFT)** updates *every* weight. **PEFT** freezes the base and
trains a small add-on (often <1% of params). The trade-off is memory/cost vs
peak capacity.

**Memory.** FFT of a 7B model needs ~100-120 GB VRAM (weights + gradients +
Adam's two moments + activations, all in fp16/bf16 → roughly 16-20 bytes/param).
The same model fine-tunes with **QLoRA on a single 24 GB RTX 4090**. PEFT broadly
cuts training memory **10-20x** while retaining **90-95%+** of FFT quality on
typical adaptation tasks. You also store a **few-MB adapter** instead of a full
model checkpoint per task.

**When PEFT (LoRA) is ~equal to FFT:** instruction-following, style transfer,
classification, most NLU (GLUE/SuperGLUE). Well-configured LoRA reaches
95-100% of FFT here.

**When FFT still wins:** large *new-knowledge* infusion (continued pretraining on
20B tokens) and hard generative skills (**code, math**). The "LoRA Learns Less and
Forgets Less" paper (Biderman et al., 2024) found LoRA **substantially
underperforms FFT** on programming and math in *both* instruction-tuning (~100K
pairs) and continued-pretraining (20B tokens) regimes, because full fine-tuning
learns weight perturbations with a rank **10-100x higher** than typical LoRA
configs, so low rank is genuinely capacity-limited there.

**The upside of "learning less":** the *same* paper shows LoRA **forgets less**.
It better preserves the base model's out-of-domain capabilities and maintains more
diverse generation, acting as a **stronger regularizer than weight decay or
dropout**. So the FFT-vs-LoRA choice is a **plasticity-vs-stability** trade:
FFT for max new capability, LoRA when retaining general ability and avoiding
forgetting matters.

> Closing the gap: a 2024-2026 line of work ("LoRA vs Full Fine-tuning: An
> Illusion of Equivalence") argues even when LoRA *matches* FFT on the target
> metric it does so via "**intruder dimensions**" (new singular directions
> unlike the pretrained weights) which drive forgetting. The practical levers:
> **raise the rank** and **apply LoRA to all linear layers** (Part 4) to behave
> more like FFT, or use the intruder-dimension mitigation (Part 8).

---

## Part 3 — LoRA mechanics (the one method to understand deeply)

**LoRA (Low-Rank Adaptation; Hu et al., 2021)** freezes the pretrained weight
matrix `W ∈ R^(d×k)` and learns a **low-rank update**: `W' = W + ΔW = W + (α/r)·BA`,
where `B ∈ R^(d×r)`, `A ∈ R^(r×k)`, and `r ≪ min(d,k)`. Only `A` and `B` train.
The hypothesis: the *update* a model needs for a downstream task has low
"intrinsic rank," so a thin `BA` product captures it with a fraction of the params.

### The four knobs

- **`r` (rank) — capacity.** Small `r` = fewer params, cheaper, more
  regularization; large `r` = more capacity but more memory and overfitting risk.
  Rules of thumb: **r=4-8** for easy/well-covered tasks (classification,
  sentiment); **r=16-32** typical for instruction tuning; **r=64-256** when
  approaching FFT quality on hard tasks (code/math) per "LoRA Learns Less." When in
  doubt start at **r=16** and sweep.

- **`lora_alpha` (α) — scaling.** The update is scaled by `α/r`. α controls how
  *strongly* the adapter speaks relative to the frozen base. The widespread
  heuristic is **α = 2·r** (e.g. r=16 → α=32). Because the *effective* scale is
  `α/r`, **raising r without raising α shrinks each update**: this is exactly the
  pathology rsLoRA fixes (Part 5).

- **`target_modules` — where.** Which `nn.Linear` layers get an adapter. Original
  LoRA targeted only attention **`q_proj`, `v_proj`** (PEFT's default). Modern best
  practice (QLoRA, "LoRA Learns Less") is **`target_modules="all-linear"`**: every
  linear layer including the **MLP** (`gate_proj`/`up_proj`/`down_proj`) and
  `k_proj`/`o_proj`, which closes most of the gap to FFT at modest extra cost. For
  MoE models whose experts are fused `nn.Parameter` tensors, use `target_parameters`.

- **`lora_dropout` — regularization.** Dropout on the LoRA path (e.g. 0.05-0.1 for
  small datasets, 0 for large clean ones).

### Initialization

Default PEFT init: **`A` ~ Kaiming-uniform, `B` = zeros** → `BA = 0` at start, so
the adapter begins as an **identity transform** (training starts exactly at the
base model — critical for stability). `init_lora_weights="gaussian"` uses a
Gaussian `A` (Diffusers convention). Data-driven inits that converge faster /
preserve knowledge better: **PiSSA** (principal singular values/vectors of `W`),
**OLoRA** (QR decomposition), **EVA** (SVD of input activations + adaptive
per-layer rank via `rho`), **CorDA** (task- or knowledge-oriented decomposition,
KPM mode mitigates forgetting), **LoRA-GA** (aligns to FFT gradient), and
**LoftQ** (init to minimize *quantization* error for QLoRA).

### Why LoRA is "free" at inference

Because `ΔW = (α/r)BA` is just a matrix, you can **fold it into `W`** after
training (`W' = W + ΔW`) → a standalone model with **zero added latency or
params**. This is the merge path (Part 7). Keep it *unmerged* only when you need
to swap adapters.

---

## Part 4 — The LoRA family: QLoRA, DoRA, rsLoRA, LoRA+

These keep LoRA's low-rank update but fix a specific weakness.

### QLoRA (Dettmers et al., 2023) — memory

Fine-tune LoRA adapters on top of a base model **quantized to 4-bit**, so the
frozen weights occupy ~1/4 the VRAM while gradients flow through them in bf16.
Three ingredients: **(1) NF4** (4-bit NormalFloat, information-theoretically
optimal for the ~normally-distributed weights — *internals live in
`llm-compression.md`*), **(2) double quantization** (quantize the quantization
constants too), **(3) paged optimizers** (page optimizer state to CPU to survive
memory spikes). Result: **fine-tune a 65-70B model on a single 48 GB GPU** with
quality matching 16-bit LoRA and 16-bit FFT. Enable in PEFT by loading the base
with a bitsandbytes 4-bit `quantization_config`, then attaching LoRA as usual.
Pair with **LoftQ** init for best quantized-training quality. "QDoRA" = QLoRA + DoRA.

### DoRA (Liu et al., ICML 2024) — low-rank quality

**Weight-Decomposed LoRA.** Decompose each weight into **magnitude** (a scalar
vector) and **direction**; let LoRA update only the *direction* while a separate
learnable parameter handles *magnitude*. This decoupling makes DoRA's learning
pattern closer to FFT and **beats LoRA especially at low rank** (r=4-8) on
commonsense reasoning and multimodal tasks, with no extra inference cost once
merged. Enable: `LoraConfig(use_dora=True)`. Caveats: bigger *training* overhead
than plain LoRA (mitigated by `DoraCaching` / `ephemeral_gpu_offload`); supports
linear/embedding/Conv2d only; **merge for inference** to erase the overhead.

### rsLoRA (Kalajdzievski, 2023) — stable high rank

**Rank-Stabilized LoRA** changes the scaling from `α/r` to **`α/√r`**. With the
original `α/r`, gradients *collapse* as `r` grows, so large ranks learn no better
than small ones (the reason "just raise the rank" historically failed). With
`α/√r` gradients stay healthy and **higher ranks finally pay off**: better
perplexity/quality at large `r`, zero inference cost. Enable:
`LoraConfig(use_rslora=True)`. Use it whenever you want r ≥ 32.

### LoRA+ (Hayou et al., 2024) — efficient feature learning

Vanilla LoRA updates `A` and `B` with the **same learning rate**, which is
provably suboptimal for feature learning in wide models. LoRA+ uses a **higher LR
for `B`** than `A` by a fixed ratio (`loraplus_lr_ratio`, e.g. 16). Result:
**~1-2% accuracy** and **up to ~2x faster** convergence at the same compute.
Enable via `create_loraplus_optimizer(...)`. (Related: a 2026 line of work argues
careful LR *tuning* alone often suffices, so always tune LR before reaching for
exotic variants.)

> **Picking within the family:** start **LoRA**; tight on VRAM → **QLoRA**; low
> rank but want more quality → **DoRA**; want high rank to work → **rsLoRA**; want
> faster/slightly-better at no cost → **LoRA+**. They compose (e.g. QLoRA + rsLoRA + LoRA+).

---

## Part 5 — The other PEFT families (non-LoRA)

PEFT methods differ in *where* they put the new parameters. (Survey framing:
Han et al. 2024; HuggingFace PEFT.)

- **Adapters (Houlsby 2019 / Pfeiffer 2021).** Insert small **bottleneck MLP
  modules** (down-project → nonlinearity → up-project, with residual) *inside* each
  transformer block. **Houlsby** = two adapters per layer (after attention *and*
  after FFN); **Pfeiffer** = one (after FFN only) — cheaper, near-equal quality.
  Match FFT within ~95%+ at <5% params. Downside vs LoRA: adapters add **layers in
  series → real inference latency** that you *cannot* merge away (LoRA can).

- **(IA)^3 (Liu et al., 2022).** "Infused Adapter by Inhibiting and Amplifying
  Inner Activations." Learns three **element-wise scaling vectors** that rescale
  keys, values, and FFN activations. *Extremely* parameter-light — **~0.5 M params
  for a 7B model** (one scalar per activation dim, no matrices). Designed to beat
  few-shot in-context learning more cheaply. Often slightly *below* LoRA on
  accuracy; shines when parameter budget is the hard constraint.

- **Prefix-tuning (Li & Liang, 2021).** Prepend trainable **continuous vectors
  ("virtual tokens")** to the keys/values at **every** layer; the real model stays
  frozen. Steers behavior without touching weights.

- **P-tuning v2 (Liu et al., 2021).** Deep prompt tuning — trainable prompts at
  **every layer** (not just the input). Effectively prefix-tuning generalized to
  NLU; the first prompt-based method to match FFT across scales/tasks.

- **Prompt tuning (Lester et al., 2021).** The lightest: trainable **soft-prompt
  embeddings at the input layer only**. Competitive *only at large model scale*;
  weaker on smaller models and harder tasks.

> **The mental model:** LoRA/adapters/(IA)^3 = *reparameterize the weights*;
> prefix/P-tuning/prompt-tuning = *learn a soft prompt*, weights untouched.
> In 2024-2026 practice **LoRA (and its family) is the default**; (IA)^3 for
> extreme parameter thrift; prompt-based methods are mostly of historical /
> multi-task-serving interest. Prefix/prompt methods also **consume context
> length** at inference.

---

## Part 6 — The HuggingFace PEFT workflow

`peft` is the standard library; it wraps any `transformers` model.

```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B")
config = LoraConfig(
    r=16, lora_alpha=32,
    target_modules="all-linear",   # QLoRA-style: every linear layer
    lora_dropout=0.05,
    use_rslora=True,               # α/√r scaling for stable higher rank
    # use_dora=True,               # weight-decomposed variant
    # init_lora_weights="pissa",   # data-driven init
    task_type="CAUSAL_LM",
)
model = get_peft_model(base, config)   # ~0.5-2% params now trainable
model.print_trainable_parameters()
# ... train with transformers Trainer or TRL SFTTrainer ...
model.save_pretrained("my-adapter")    # saves only the few-MB adapter
```

**Knob summary in `LoraConfig`:** `r`, `lora_alpha`, `target_modules`
(or `"all-linear"`), `lora_dropout`, `use_rslora`, `use_dora`, `init_lora_weights`
(`True`/`"gaussian"`/`"pissa"`/`"olora"`/`"eva"`/`"loftq"`/`"corda"`),
`rank_pattern`/`alpha_pattern` (per-layer overrides), `target_parameters` (MoE
experts), `modules_to_save` (fully-train extra modules like a new classifier head),
`trainable_token_indices` (train just new special-token embeddings).

**Multiple adapters on one base** (Part 7): `PeftModel.from_pretrained(base, id,
adapter_name="a")`, then `model.load_adapter(id2, adapter_name="b")`,
`model.set_adapter("b")` to switch, `model.disable_adapter()` context for the raw
base, `model.delete_adapter("b")` to drop. **LoRA+** optimizer:
`create_loraplus_optimizer(model, optimizer_cls, lr, loraplus_lr_ratio)`.

**PEFT supports** LoRA + variants (DoRA/rsLoRA/PiSSA/…), adapters, (IA)^3,
prefix-tuning, P-tuning, prompt-tuning, LoHa/LoKr, and more — same wrap-and-train
shape.

---

## Part 7 — Multi-LoRA serving: merge vs swap (+ adapter merging)

You trained an adapter. Two ways to serve it, and a third way to *combine* several.

**Merge (`merge_and_unload`).** Fold `ΔW` into `W` to get a **standalone model with
zero added latency**. Use when one adapter serves all traffic. It is **not
in-place**, so assign the return value. **Lossy for quantized bases** (merging fp16
deltas into a 4-bit base reintroduces error) and irreversible; for QLoRA, either
serve unmerged or dequantize-then-merge. DoRA/MoE-LoRA *should* be merged to erase
their inference overhead.

```python
model = PeftModel.from_pretrained(base, "my-adapter")
model = model.merge_and_unload()      # standalone, no PEFT overhead
# Reversible variant: model.merge_adapter() ... model.unmerge_adapter()
```

**Swap / multi-tenant (keep unmerged).** Keep the **frozen base resident once** and
hot-swap small adapters per request — N tasks served from 1 base + N few-MB
adapters instead of N full models. The economic win behind LoRA serving. PEFT can
even **mix adapters within one batch** via the `adapter_names` argument
(`base`/`adapter_fr`/`adapter_de` rows in the same forward pass). At scale, the
*serving engine* does this efficiently:

- **S-LoRA** — custom heterogeneous CUDA kernels + **unified paging** (adapters in
  CPU memory, active slices paged to GPU alongside KV-cache). Serves **thousands**
  of concurrent adapters; **up to 4x** throughput over naive PEFT/vLLM LoRA.
- **Punica** — **SGMV** kernel fuses heterogeneous LoRA deltas (different adapters
  *and ranks*) into one batched matmul.
- **vLLM / TGI / SGLang** ship multi-LoRA serving built on these ideas;
  mid-sequence adapter switching is still the open overhead.

> The **kernel/runtime** side of multi-LoRA (PagedAttention, continuous batching,
> KV-aware routing, autoscaling) is the sibling **`references/llm-inference-serving.md`**.
> This reference owns the *decision* (merge vs swap) and the *adapter-combination*
> math below.

**Combining several adapters into one** — `add_weighted_adapter(adapters=[...],
weights=[...], combination_type=...)`. `combination_type` options:

- **`linear`** — weighted sum of the deltas (e.g. blend an SFT and a DPO adapter
  `[0.7, 0.3]`).
- **`cat`** — concatenate (ranks add; no information loss, larger adapter).
- **`ties`** / **`dare_ties`** / **`dare_linear`** — sign-resolution / random-drop
  merge methods that reduce interference between task adapters (these merge
  *algorithms* are detailed in `llm-compression.md`'s model-merging section).
- **`svd`** — SVD-based combine (not supported in fp16/bf16).

> **aLoRA (Activated LoRA)** is a serving-time variant that activates the adapter
> only *after* an invocation token, so it **reuses the base model's KV cache** —
> an order-of-magnitude speedup when the base does most of the work and the adapter
> handles a checking/correcting sub-task. aLoRA **cannot be merged** by definition.

---

## Part 8 — Catastrophic forgetting & mitigations

**Catastrophic forgetting:** fine-tuning on a narrow task degrades the base model's
*general* abilities (it overwrites pretrained knowledge). The classic symptom is a
fine-tune that nails your task but loses MMLU points and general chat quality.

**Mitigations, roughly strongest-first:**

1. **Use PEFT, especially LoRA.** Because the base is *frozen* and only a small
   add-on trains, **parameter isolation** structurally protects pretrained
   weights (the "LoRA forgets less" result, Part 2), and LoRA out-forgets weight
   decay and dropout. The single biggest lever.
2. **Experience replay / rehearsal.** Mix a slice of **general / prior-task data**
   (or pretraining-style data) into the fine-tune set. The most effective standalone
   technique; recent work prioritizes rehearsing "collateral-damage" examples (ones
   the base got right but the fine-tune started getting wrong).
3. **Regularization toward the base.** Weight decay, dropout, **lower learning
   rate**, **fewer epochs**, **early stopping** on a held-out set.
4. **Forgetting-aware init / structure.** **CorDA-KPM** (knowledge-preserved init)
   and **OPLoRA** (orthogonal-projection LoRA) explicitly protect base knowledge;
   **KappaTune** targets only the most *isotropic* (high-entropy) layers, leaving
   specialized layers intact.
5. **Intruder-dimension reduction** (`reduce_intruder_dimension`) — post-hoc remove
   the "intruder" singular directions a LoRA introduced; a tunable trade-off
   between task accuracy kept and base knowledge restored.

**Always quantify it:** run a general-capability benchmark (e.g. MMLU) on the base
*and* the fine-tune. A **>2-3 point drop** signals forgetting (Part 10).

---

## Part 9 — SFT data preparation & chat templating

The fine-tune's quality is **bounded by its data**. Supervised fine-tuning (SFT) =
training on **(instruction/prompt → desired response)** pairs so the model shifts
from generic next-token prediction to following instructions in your format.
(SFT is also the *first stage* of post-training that precedes RLHF/DPO →
`llm-alignment-post-training.md`.)

**Quality over quantity.** A few thousand **clean, diverse, correctly-formatted,
deduplicated** examples beat a noisy large set (the LIMA "less is more" finding).
Curate for correctness, format consistency, and coverage of the behaviors you want;
decontaminate against your eval set.

**Dataset formats** (TRL `SFTTrainer` conventions):

- **Conversational** — `{"messages": [{"role": "system"/"user"/"assistant",
  "content": ...}]}`. Preferred for chat models; the trainer applies the model's
  chat template for you.
- **Prompt-completion** — `{"prompt": ..., "completion": ...}`.
- **Instruction** (Alpaca-style) — `{"instruction", "input", "output"}`, usually
  rendered into one of the above.

**Chat templating is non-negotiable.** Chat models were trained with an *exact*
token format (role markers + special tokens, e.g. `<|im_start|>user … <|im_end|>`).
The template is a **Jinja** string shipped on the tokenizer
(`tokenizer.apply_chat_template(...)`). **Mismatched formatting between fine-tuning
and inference is the #1 silent fine-tune killer**: train and serve with the *same*
template and special tokens. When introducing genuinely new special tokens,
`resize_token_embeddings` and train them (PEFT `trainable_token_indices` does this
cheaply).

**Completion-only / loss masking.** You almost always want loss computed **only on
the assistant/response tokens**, not the prompt — set the prompt-token labels to
the ignore index **`-100`** so cross-entropy skips them. This focuses learning on
*generating* the response rather than *memorizing* the instruction. TRL's
`SFTTrainer` does completion-only masking for prompt-completion data by default;
for conversational data use its assistant-only-loss option.

**Packing.** Concatenate short examples into full-length sequences to avoid wasted
padding compute (`packing=True`) — watch that cross-example attention is masked.

---

## Part 10 — Tooling stack

| Tool | Shape | Pick when |
| --- | --- | --- |
| **HuggingFace PEFT + TRL** | Libraries (`LoraConfig`/`get_peft_model` + `SFTTrainer`) | You want code-level control / are already in the HF stack; the canonical baseline |
| **Unsloth** | Notebook-first, custom Triton kernels | **Single-GPU**, limited VRAM; **~2x faster, ~50-70% less memory** via hand-written kernels. No multi-GPU |
| **Axolotl** | YAML-config wrapper over HF | **Reproducible team runs** and **multi-GPU**; broad model + technique coverage |
| **Llama-Factory** | Zero-code **web UI** (+ Unsloth backend option) | Fastest path to a first run; 100+ model templates; "use if unsure" |
| **torchtune** | PyTorch-native, abstraction-free recipes | You want to **modify the training loop** in pure PyTorch / research |

All support LoRA + QLoRA; the differences are ergonomics, kernel speed, and
multi-GPU. For preference optimization (DPO/PPO) the same tools route into TRL /
OpenRLHF → `llm-alignment-post-training.md`.

---

## Part 11 — Evaluating a fine-tune

A fine-tune eval needs **two prongs** — and you must beat a real baseline.

1. **Task improvement.** A **held-out test set** of your task (never seen in
   training), scored with a task-appropriate metric: exact-match/F1 for extraction,
   pass@k for code, an **LLM-as-judge** rubric for open-ended generation,
   classification metrics for labels. (Harness mechanics → `da-7-machine-learning`.)
2. **Capability-regression check.** Run a **general benchmark (e.g. MMLU)** on the
   base *and* the fine-tune. A **>2-3 point drop = catastrophic forgetting** —
   address with Part 8 before shipping.

**Always compare against the base model on the same held-out set** to prove the
fine-tune actually helped (and ideally against a strong *prompted* base — sometimes
prompting alone matches it).

**Detect overfitting:** track **validation loss** during training and stop when it
turns up (early stopping); a train-loss that keeps dropping while val-loss rises is
the tell. Watch for **benchmark contamination**: the NeurIPS-2023 fine-tuning
competition found top models heavily overfit popular benchmarks, so a clean,
private held-out set is worth more than a public leaderboard number.

---

## Anti-patterns

- **Fine-tuning to add knowledge that changes often.** It bakes in stale facts and
  the model still hallucinates. Use RAG. Fine-tune behavior, retrieve facts.
- **Reaching for fine-tuning before exhausting prompting + RAG.** It's the slowest,
  costliest lever; most "fine-tune" problems are prompt/RAG problems.
- **Train/inference chat-template mismatch.** Different template or special tokens
  at serving than at training → silent quality collapse. The #1 fine-tune bug.
- **Computing loss on prompt tokens.** Teaches the model to parrot instructions;
  mask the prompt with `-100` / use completion-only.
- **Targeting only `q_proj`,`v_proj` and expecting FFT quality.** For hard tasks use
  **`all-linear`** and a **higher rank** (and rsLoRA so the higher rank helps).
- **Raising `r` without rsLoRA.** With `α/r` scaling, gradients collapse and the
  larger rank buys nothing — use `use_rslora=True`.
- **Merging an fp16 adapter into a 4-bit QLoRA base and expecting no loss.** Merge
  reintroduces quantization error; serve unmerged or dequantize first.
- **No base-model regression check.** Shipping a fine-tune that quietly lost 5 MMLU
  points. Always eval both prongs (Part 11).
- **Huge noisy dataset over a small clean one.** Quality, diversity, and dedup beat
  raw volume; decontaminate against eval.
- **Same learning rate as full fine-tuning.** LoRA usually wants a **higher LR**
  (e.g. 1e-4 to 3e-4) than FFT (~1e-5); tune it before reaching for exotic variants.

## Troubleshooting

- **Fine-tune nails the task but general chat degraded** → catastrophic forgetting:
  switch to LoRA, add replay data, lower LR / fewer epochs, check MMLU delta (Part 8).
- **LoRA underperforms FFT on code/math** → raise rank to 64-256, use `all-linear`,
  `use_rslora=True`; or accept FFT for that workload (Part 2).
- **Garbage/looping generations after fine-tuning** → almost always a chat-template
  or special-token mismatch, or EOS not learned; verify `apply_chat_template`
  parity train↔serve (Part 9).
- **OOM during training** → QLoRA (4-bit base), Unsloth, gradient checkpointing,
  smaller batch + gradient accumulation, paged optimizer, lower rank.
- **Adapter "does nothing" at inference** → forgot to `set_adapter`/load it, or
  merged then tried to swap; confirm the active adapter.
- **High inference latency with the adapter** → `merge_and_unload` for single-task
  serving; DoRA/MoE-LoRA especially must be merged.
- **Loss not decreasing** → LR too low (LoRA likes higher LR), or loss masked
  wrong, or `B` not actually training (check `print_trainable_parameters`).
- **QLoRA quality below expectation** → use **LoftQ** init to minimize quantization
  error; consider QDoRA.

## References

- LoRA: Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models" — https://arxiv.org/abs/2106.09685
- QLoRA: Dettmers et al., "QLoRA: Efficient Finetuning of Quantized LLMs" — https://arxiv.org/abs/2305.14314
- DoRA: Liu et al., "DoRA: Weight-Decomposed Low-Rank Adaptation" (ICML 2024) — https://arxiv.org/abs/2402.09353
- rsLoRA: Kalajdzievski, "A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA" — https://arxiv.org/pdf/2312.03732
- LoRA+: Hayou et al., "LoRA+: Efficient Low Rank Adaptation of Large Models" — https://arxiv.org/pdf/2402.12354
- "LoRA Learns Less and Forgets Less": Biderman et al. — https://arxiv.org/pdf/2405.09673
- "LoRA vs Full Fine-tuning: An Illusion of Equivalence" — https://arxiv.org/html/2410.21228v3
- (IA)^3 / T-Few: Liu et al., "Few-Shot PEFT is Better and Cheaper than In-Context Learning" — https://proceedings.neurips.cc/paper_files/paper/2022/file/0cde695b83bd186c1fd456302888454c-Paper-Conference.pdf
- PEFT survey: Han et al., "Parameter-Efficient Fine-Tuning for Large Models: A Survey" — https://link.springer.com/article/10.1007/s10462-025-11236-4
- S-LoRA: "Serving Thousands of Concurrent LoRA Adapters" (MLSys 2024) — https://arxiv.org/pdf/2311.03285
- Punica: "Multi-Tenant LoRA Serving" — https://arxiv.org/pdf/2310.18547
- HuggingFace PEFT — LoRA developer guide — https://huggingface.co/docs/peft/main/en/developer_guides/lora
- HuggingFace TRL — SFTTrainer — https://huggingface.co/docs/trl/en/sft_trainer
- bitsandbytes 4-bit + QLoRA (HF blog) — https://huggingface.co/blog/4bit-transformers-bitsandbytes
- LoRA hyperparameters (rank/alpha/target modules) — https://mbrenndoerfer.com/writing/lora-hyperparameters-rank-alpha-target-modules
- Fine-tuning framework comparison (Unsloth/Axolotl/torchtune/Llama-Factory) — https://modal.com/blog/fine-tuning-llms
- RAG vs Fine-tuning vs Prompt Engineering (IBM) — https://www.ibm.com/think/topics/rag-vs-fine-tuning-vs-prompt-engineering
- Catastrophic-forgetting rehearsal scheme — https://arxiv.org/html/2402.08096
- OPLoRA (orthogonal-projection LoRA, forgetting) — https://arxiv.org/pdf/2510.13003
