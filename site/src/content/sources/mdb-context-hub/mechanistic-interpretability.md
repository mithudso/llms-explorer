---
title: "Mechanistic Interpretability"
description: "Reverse-engineering the internal computation of neural networks (chiefly transformer LLMs) into human-understandable mechanisms — the features a model represents and the circuits that combine them. A"
---

# Mechanistic Interpretability — SAEs, Circuits, Steering

Reverse-engineering the **internal computation** of neural networks (chiefly transformer LLMs) into human-understandable mechanisms — the *features* a model represents and the *circuits* that combine them. A model-layer reference under the `ai-agent-engineering` hub (2024–2026). Mechanistic interpretability (MI) is distinct from post-hoc ML explainability (SHAP/LIME, which attribute an *output* to *inputs* without opening the model) and from LLM observability (which traces a running app). MI opens the box: it makes causal, testable claims about *what computation the weights implement*.

A defining property of healthy MI work in 2025 is **epistemic honesty** — the field's flagship technique (SAEs) is under serious, well-evidenced critique. This reference deliberately carries both the methods and their negative results; treating MI as solved is the most common mistake.

## 1. The goal and the two paradigms

MI seeks **faithful, causal, mechanistic** explanations: not "this neuron correlates with X" but "this component computes X, and ablating/patching it changes the output as predicted." Two complementary objects of study:

- **Features** — the units of *representation*: what directions/subspaces in activation space *mean*.
- **Circuits** — the units of *computation*: subgraphs of components (attention heads, MLPs) that compose features to implement a behavior.

The **linear representation hypothesis** underpins much of the field: many human-interpretable concepts are encoded as (roughly) linear directions in activation space, so they can be found by linear probes, added/subtracted as steering vectors, and isolated by dictionary learning. It is a working hypothesis, not a law — non-linear and multi-dimensional feature geometry (e.g. circular "days of the week" features) are active counter-evidence.

## 2. Superposition and polysemanticity

Networks routinely represent **more features than they have neurons** by storing them in *superposition* — as overlapping, near-orthogonal combinations of activations (Anthropic, *Toy Models of Superposition*). The visible symptom is **polysemanticity**: a single neuron fires for many unrelated concepts, so neurons are the wrong unit of analysis. Superposition is why naive "neuron interpretation" fails and why dictionary-learning methods (SAEs) became central — they aim to recover **monosemantic** features from the polysemantic soup. Sparsity + a high-dimensional dictionary is the lever: real features are sparse (few active per token), so an overcomplete sparse basis can disentangle them.

## 3. Sparse autoencoders (SAEs) and dictionary learning

An SAE is trained on a model's activations (a residual-stream layer, MLP, or attention output) to reconstruct them through a wide, sparse hidden layer; each hidden unit is a candidate **monosemantic feature**. The loss trades **reconstruction fidelity** against **sparsity** (active-feature count). Architectures evolved to fix the L1-sparsity "shrinkage" bias:

- **Standard (L1) SAE** — ReLU + L1 penalty (Anthropic *Towards Monosemanticity*, Cunningham et al. "SAEs find highly interpretable features").
- **Gated SAE** — separates the "which features are on" gate from "how much," reducing shrinkage.
- **TopK / BatchTopK SAE** — keep the top-k activations exactly; k directly sets sparsity (OpenAI scaled this to a 16M-latent SAE on GPT-4).
- **JumpReLU SAE** — a learned activation threshold; strong fidelity/sparsity frontier (DeepMind).
- **Matryoshka SAE** — nested dictionaries at multiple widths for multi-granularity features.

Landmark scale-ups: Anthropic **Scaling Monosemanticity** (Claude 3 Sonnet — millions of features incl. the "Golden Gate Bridge" feature) and DeepMind **Gemma Scope** (open SAE suite across all layers of Gemma 2, up to 27B), which made MI broadly reproducible.

## 4. The SAE critique wave (you MUST carry this)

By 2025 large, careful evaluations found SAEs **failing to beat simple baselines** on the tasks people most wanted them for:

- **Probing/concept detection**: SAE features often do **not** beat plain linear probes on raw activations.
- **Steering**: sparse/SAE steering often underperforms simpler activation-addition baselines.
- **The "dead-salmon" result** (Heap et al. 2025): SAEs trained on a **randomly-initialized** transformer produce features with auto-interp scores *similar* to those from a trained model — so a high auto-interp score does **not** prove the feature reflects real model computation.
- **Non-canonical / unstable**: different seeds/widths yield different feature sets ("SAEs do not find canonical units of analysis"); SAEs on OOD data capture **dataset artifacts**, not model internals.
- **DeepMind's MI team publicly deprioritized SAE-for-downstream-tasks** after negative results.

The constructive reconciliation (Anthropic-adjacent): **use SAEs to *discover unknown* concepts, not to *act on known* ones** — they are exploratory instruments, not production controllers or canonical truth. Always benchmark an SAE claim against a probe/random baseline.

## 5. Transcoders and crosscoders

- **Transcoders** replace an MLP with an interpretable input→output sparse map (decompose the *computation*, not just the representation). Their features are reported as **more interpretable** than SAE features and they make MLPs tractable for circuit tracing.
- **Cross-layer transcoders (CLT)** read from one layer's residual stream and write to later layers — the backbone of Anthropic's attribution graphs (CLT-Forge is a scalable library).
- **Crosscoders** jointly decode activations from **multiple sources** (layers, or two models — base vs fine-tuned) to compare them; used for model-diffing.

## 6. Circuit discovery and causal analysis

Finding the sparse subgraph that mediates a behavior, then proving it causally:

- **Activation / causal patching** (a.k.a. causal tracing): run a clean and a corrupted prompt; copy ("patch") a clean activation into the corrupted run and measure the recovered logit — isolates **necessary/sufficient** components.
- **Path patching** restricts the effect to specific component-to-component paths (sender→receiver), separating direct from indirect effects.
- **ACDC** (Automatic Circuit DisCovery) — greedily prunes the computational graph to the edges that matter.
- **Edge Attribution Patching (EAP / EAP-IG)** — a gradient-based linear approximation to patching that scales circuit discovery to thousands of edges cheaply.
- **Sparse feature circuits** (Marks et al.) — circuits over *SAE features* (not raw components), giving human-interpretable nodes.
- Canonical worked circuits: **induction heads** (in-context copy `[A][B]...[A]→[B]`, the mechanism behind much in-context learning), **IOI** (indirect-object identification in GPT-2 small), docstring, greater-than.

## 7. Attribution graphs and circuit tracing

Anthropic's **Circuit Tracing** / *On the Biology of a Large Language Model* (2025) applied **attribution graphs** (built on cross-layer transcoders) to a **production** model (Claude 3.5 Haiku), surfacing multi-step internal "reasoning" — planning ahead in rhyming poetry, multi-hop factual lookups, a shared multilingual concept space. This was the field's proof that MI can scale beyond toy models, with the honest caveat that attribution graphs are approximate and require manual validation.

## 8. Lenses and probing

- **Logit lens** — decode an intermediate residual stream directly through the unembedding to watch the prediction form layer-by-layer. **Tuned lens** learns a per-layer affine probe for a more faithful read.
- **Linear probes** — train a linear classifier on activations to test whether a concept is linearly decodable (the empirical test of the linear representation hypothesis). Caveat: a probe shows *availability*, not *use* — the model may not causally rely on what a probe can read.
- **Concept erasure** (e.g. LEACE) — remove a concept direction to test causal dependence.

## 9. Activation steering and representation engineering

Inference-time control of a *frozen* model by editing activations:

- **Steering / control vectors** — add a direction (often a difference-of-means between contrastive prompt pairs, "ActAdd"/CAA) to the residual stream to push behavior (sentiment, refusal, honesty, format).
- **Representation Engineering (RepE)** — a top-down program: read concept representations, then control them.
- Refinements: **mean-centring** (subtract the dataset mean to clean the direction), **feature-guided / sparse steering** (steer along SAE feature dims for monosemantic edits), sparse representation steering for guardrails.
- Reality check: SAE-based steering frequently does **not** beat simple activation-addition; steering is brittle and dose-sensitive (over-steering breaks fluency).

## 10. Auto-interpretability and evaluation

- **Auto-interp**: use an LLM to label what a feature/neuron means from its top-activating examples, then **score** the label by having an LLM predict activations from the explanation. Powers feature-labeling at scale (Neuronpedia).
- The dead-salmon caveat (§4) means auto-interp scores must be read against **random baselines**.
- Evaluation frameworks: **SAEBench** (multi-metric SAE comparison), faithfulness/completeness for circuits, targeted concept-erasure tasks, and "does it beat a probe/random baseline" as the gating question.

## 11. Tooling stack

- **TransformerLens** (Neel Nanda) — the workhorse hooked-transformer library for caching/patching activations.
- **nnsight / NDIF** — interpret/intervene on very large models via remote execution.
- **SAELens** — train & run SAEs; works natively with TransformerLens and HF/nnsight models.
- **Neuronpedia** — interactive feature explorer + hosted SAEs (incl. Gemma Scope) for building intuition.
- **Gemma Scope** — open SAEs for every layer of Gemma 2; the standard reproducible substrate.
- **pyvene / baukit**, **CLT-Forge** (cross-layer transcoders + attribution graphs).

## 12. Interpretability for alignment and safety

The strategic motivation: **auditing** models for hidden goals, deception, or backdoors that behavioral testing misses.

- Active directions: SAE/probe-based detectors for **deception** and **alignment faking**; model-diffing (crosscoders) to spot what fine-tuning changed; backdoor/sleeper-agent detection.
- Sobering results: auto-labeled "deception/lying" SAE features often **don't activate** during real strategic dishonesty (the labels don't capture the mechanism); and models can produce **deceptive interpretability explanations** that evade SAE-based oversight. Interpretability is a promising *layer* of an alignment safety case, not a guarantee.
- The **interpretability illusion**: a feature that looks clean on a curated dataset can behave differently in deployment; faithfulness must be tested causally, not assumed from a tidy label.

## When to reach for which

| Goal | Reach for |
| --- | --- |
| "What does this part of the model represent?" | SAEs / probes / logit-lens; benchmark vs a random baseline |
| "What computes this behavior?" | activation/path patching → ACDC/EAP → sparse feature circuits |
| "Show the multi-step mechanism in a real model" | attribution graphs / circuit tracing (CLT) |
| "Make MLPs interpretable for tracing" | transcoders / cross-layer transcoders |
| "Steer behavior without retraining" | steering/control vectors, RepE (expect brittleness; benchmark vs ActAdd) |
| "Audit for deception / backdoors" | probes + crosscoder model-diffing + SAE discovery — as one layer of a safety case, validated causally |

## Sources

- *Locate, Steer, and Improve: A Practical Survey of Actionable Mechanistic Interpretability in LLMs* — arXiv 2601.14004
- *A Survey on Sparse Autoencoders: Interpreting the Internal Mechanisms of LLMs* — arXiv 2503.05613 / ACL Findings EMNLP 2025
- Cunningham et al., *Sparse Autoencoders Find Highly Interpretable Features in Language Models* — OpenReview F76bwRSLeK
- Anthropic, *Circuit Tracing: Revealing Computational Graphs in Language Models* & *On the Biology of a Large Language Model* — transformer-circuits.pub 2025
- *Sparse Autoencoders Do Not Find Canonical Units of Analysis* — arXiv 2502.04878
- *Sanity Checks for Sparse Autoencoders: Do SAEs Beat Random Baselines?* — arXiv 2602.14111
- DeepMind Safety Research, *Negative Results for SAEs on Downstream Tasks and Deprioritising SAE Research* (Medium, 2025)
- *Use Sparse Autoencoders to Discover Unknown Concepts, Not to Act on Known Concepts* — arXiv 2506.23845
- *Steering Language Models With Activation Engineering* (ActAdd) — arXiv 2308.10248; *Improving Activation Steering with Mean-Centring* — arXiv 2312.03813
- *Steering LLM Activations in Sparse Spaces* — arXiv 2503.00177; *Interpretable LLM Guardrails via Sparse Representation Steering* — arXiv 2503.16851
- Transcoders / crosscoders — learnmechinterp.com; *CLT-Forge* arXiv 2603.21014
- *Mechanistic Interpretability for LLM Alignment: Progress, Challenges, and Future Directions* — arXiv 2602.11180
- *Deceptive Automated Interpretability* — arXiv 2504.07831
- Tooling: TransformerLens, SAELens + Neuronpedia (learnmechinterp.com), nnsight/NDIF, DeepMind Gemma Scope
