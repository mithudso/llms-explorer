---
title: "Reasoning Models and Test-Time Compute"
description: "The frontier (2024–2026) shift from 'scale the model and prompt it well' to 'train the model to reason, then spend extra compute at inference to reason harder.' Two coupled ideas drive it:"
---

# Reasoning Models & Test-Time Compute

The frontier (2024–2026) shift from "scale the model and prompt it well" to "**train the model to reason, then spend extra compute at inference to reason harder**." Two coupled ideas drive it:

1. **Test-time / inference-time compute (TTC):** a model can be made more accurate on a hard problem by spending *more compute when answering* — sampling many solutions, searching over reasoning steps, or generating a long internal chain of thought — instead of (or in addition to) growing the model. Snell et al. (2024) showed this can be **more parameter-efficient than scaling pretraining** on a fixed compute budget for many problems.
2. **Reasoning models** (o1/o3, DeepSeek-R1, Gemini "thinking", Claude extended thinking): models *post-trained with reinforcement learning to produce long chains of thought before answering*. The RL teaches the model to use its inference budget well, so the two ideas reinforce each other: the model both *generates* a long CoT and *benefits* from being allowed to.

## Scope boundary (read first)

- **This reference** = the model's *reasoning*: long-CoT, reasoning-specific RL (GRPO, RLVR), process vs outcome reward models, test-time-compute scaling (best-of-N, self-consistency, search), inference-time scaling laws, the o-series/R1 landscape, budget forcing, reasoning distillation, reasoning benchmarks, and the cost/latency/accuracy trade-off.
- **Classic preference alignment** — RLHF with PPO, the DPO-variant family (DPO/IPO/KTO/ORPO/SimPO/CPO), RLAIF, Constitutional AI — is a **different objective** (match human *preference* via a learned reward model). It lives in `references/llm-alignment-post-training.md`. The line: **reasoning-RL optimizes *verifiable correctness*; alignment-RL optimizes *human preference*.** GRPO/RLVR-for-reasoning are here; the same algorithms used for preference tuning are there.
- **Agent loops / tool use** (a model calling tools in a multi-step loop) → `references/agent-ecosystem.md`, `references/autonomous-loops.md`, `references/agent-harness-construction.md`. This reference is about the *model's own* reasoning, not the orchestration around it. (Reasoning models *can* call tools mid-thought — "agentic reasoning" — but the orchestration belongs to those references.)
- **Serving throughput** (vLLM batching, speculative decoding, KV-cache) → `references/llm-inference-serving.md`. Speculative decoding *speeds up* token generation; it is not test-time *scaling* (spending more compute to get a better answer). Don't conflate them.
- **Model selection / the landscape** (which model to pick) → `references/llm-models.md`; this reference covers the *reasoning-specific* properties of those models. **Offline benchmark mechanics** (HELM/MMLU harness internals) → `da-7-machine-learning` (`da-analytical-methods`).

---

## 1. Chain-of-thought (CoT) and long-CoT

**Chain-of-thought prompting** (Wei et al., NeurIPS 2022, arXiv:2201.11903) is the origin: prompting a model to emit *intermediate reasoning steps* before its final answer ("Let's think step by step" / few-shot exemplars with worked reasoning) sharply improves arithmetic, commonsense, and symbolic reasoning. The paper's key empirical claim: CoT is an **emergent ability of scale** — it does not help (and can hurt) small models, and only yields gains at roughly ≥100B-parameter scale. CoT works because autoregressive decoding lets the model **externalize computation into tokens**: each generated step conditions the next, so the model can do serial work it cannot do in a single forward pass. A useful mental model is that CoT trades extra output tokens for extra effective "depth."

**Long-CoT** is the 2024–2026 evolution. Where prompted CoT produces a few tidy steps, reasoning models produce **thousands of tokens of unpolished internal reasoning** — exploring, backtracking, self-correcting, re-checking ("Wait, let me reconsider…"), trying multiple approaches. This is not just "more steps"; it qualitatively includes **reflection, verification, and search-like behavior in a single linear stream**. DeepSeek-R1-Zero exhibited a now-famous **"aha moment"**: mid-training, the model spontaneously learned to stop and re-evaluate its approach, allocating more thinking to harder sub-problems — an emergent behavior from RL, not something explicitly taught. Long-CoT is what reasoning-model RL *produces*, and what makes test-time-compute scaling work: a longer, self-correcting chain is more likely to reach the right answer.

**CoT faithfulness caveat:** the visible chain is not guaranteed to be the model's true computation. Models can reach a correct answer via a reasoning trace that is post-hoc or partially confabulated, so a CoT should be treated as *an aid to accuracy*, not *a transparent log of mechanism* — relevant for both interpretability and safety.

---

## 2. Reinforcement learning for reasoning — GRPO and the DeepSeek-R1 recipe

The central insight of reasoning models: **you can RL a base model toward better reasoning using only an automatic correctness signal** (does the final answer match? does the code pass tests?), with no human preference labels and no learned reward model. This is what separates reasoning-RL from RLHF.

### GRPO (Group Relative Policy Optimization)

GRPO (introduced in **DeepSeekMath**, arXiv:2402.03300; used at scale in R1) is the workhorse algorithm. It is a PPO-style policy-gradient method that **removes the value/critic network**. Instead of a learned baseline, GRPO samples a **group of G outputs** for each prompt, scores them all with the reward function, and uses the **group's mean reward as the baseline** — each sample's advantage is its reward standardized against its group (`(r_i − mean) / std`). Benefits: no critic model (roughly halves memory/compute vs PPO's four-model loop), and a baseline that is naturally calibrated per-prompt. It keeps PPO's clipped surrogate objective and a **KL penalty to a reference policy** to prevent drift. Known issue: the original formulation can induce a **response-length bias** (especially inflating length on *incorrect* answers); several 2025 variants (e.g., length-normalized / token-level objectives, Dr. GRPO) correct this.

### The R1-Zero and R1 recipe (arXiv:2501.12948)

- **DeepSeek-R1-Zero** = pure RL, *no SFT at all*, applied directly to a base model (DeepSeek-V3-Base) with GRPO and **rule-based rewards** (accuracy reward for verifiable answers + format reward for putting reasoning in `<think>` tags). Powerful reasoning **emerged from RL alone** — the model taught itself long-CoT, reflection, and the "aha moment." But R1-Zero had poor readability and **language mixing** (switching languages mid-thought).
- **DeepSeek-R1** fixes this with a **multi-stage pipeline**:
  1. **Cold-start SFT** — fine-tune the base on a small set of curated long-CoT examples to give a readable starting point.
  2. **Reasoning-oriented RL** — large-scale GRPO with verifiable rewards (plus a language-consistency reward to stop language mixing).
  3. **Rejection-sampling SFT** — generate many samples from the RL checkpoint, keep the correct/readable ones, add general-purpose data, and SFT a fresh checkpoint.
  4. **Final RL** — a second RL stage over both reasoning and general (helpfulness/harmlessness) prompts.

  Result: R1 matched OpenAI o1 across math, code, and reasoning while being openly published. The recipe — **small cold-start SFT → verifiable-reward RL → rejection-sample SFT → RL again** — is now the canonical open template for building a reasoning model. (For the *preference*-alignment side of post-training — reward modeling, RLHF/PPO, DPO — see `llm-alignment-post-training.md`.)

---

## 3. RLVR — Reinforcement Learning with Verifiable Rewards

**RLVR** (named and formalized in **Tülu 3**, Lambert et al., arXiv:2411.15124) is the general principle behind reasoning-RL: **replace RLHF's learned reward model with a deterministic verification function**, and give reward *only when the output is verifiably correct*. The verifier can be an exact-match check on a math answer, a unit-test suite for code, a format/constraint checker for instruction-following, or a symbolic checker. Because the signal is grounded truth rather than a learned proxy, RLVR is **far less prone to reward hacking** than RLHF — there is no reward model to exploit (though *verifier* gaming and reward-spec gaps still exist).

- **Scope:** RLVR works wherever correctness is cheaply checkable — math, code, logic, structured output. It does **not** directly apply to open-ended generation (essays, dialogue) where there is no verifier; that remains preference-alignment territory. A 2026 line of work ("verifiable reference-based rewards") tries to extend RLVR-style signals to open-ended tasks via reference answers.
- **Algorithm-agnostic:** RLVR is the *reward design*; the *optimizer* can be PPO (Tülu 3) or GRPO (R1). Don't conflate "RLVR" (verifiable reward) with "GRPO" (critic-free optimizer) — they're orthogonal and often combined.

### The RLVR effectiveness debate (important, unresolved as of mid-2026)

A prominent 2025 result (Yue et al., Tsinghua, arXiv:2504.13837) argued that RLVR may **not teach genuinely new reasoning** — under pass@k with large k, RLVR-trained models do not exceed the *base* model's coverage of solvable problems; RL appears to **sharpen / up-weight reasoning paths already in the base distribution** (raising pass@1) rather than discovering paths the base could never find. Follow-ups (e.g., arXiv:2506.14245) counter that RLVR *implicitly improves* the correctness of sampled reasoning. The practical takeaway: **RLVR reliably makes a model better at *finding* its good reasoning faster (sample-efficiency / pass@1), but whether it expands the reasoning *ceiling* beyond the base model is contested** — relevant when deciding between RL and just distilling from a stronger teacher (§7).

---

## 4. Process reward models (PRM) vs outcome reward models (ORM)

When you score reasoning, you can reward the **outcome** (final answer only) or the **process** (each intermediate step). This choice shapes both RL training and test-time verification.

- **ORM (Outcome Reward Model):** one scalar for the whole solution, based on final-answer correctness. Cheap to label (just check the answer), but gives **sparse, delayed credit** — a solution with a fatal error in step 2 that luckily reaches the right answer is rewarded; the model cannot localize *where* it went wrong.
- **PRM (Process Reward Model):** scores **each reasoning step** as correct/helpful or not. Originated in OpenAI's **"Let's Verify Step by Step"** (Lightman et al., 2023), which released **PRM800K** (800K human step-level labels on MATH solutions). Their headline result: **process supervision trains substantially more reliable verifiers than outcome supervision** — a PRM-reranked solver solved **78.2%** of a representative MATH subset, beating ORM reranking. PRMs give **dense credit assignment** and **interpretability** (you see which step failed).

**Two uses of reward models — keep them distinct:**
1. **As a training signal** (in RL): PRMs can densify the RL reward. *However*, the R1 team found PRMs hard to use as the RL reward at scale — defining "a good step" is fuzzy, step-level labels are expensive, and PRMs are themselves **reward-hackable**. R1 therefore used simple **rule-based outcome+format rewards** for RL, not a PRM. This is a key practical lesson: **PRMs shine at test-time verification more than as the RL objective.**
2. **As a test-time verifier** (§5–6): a PRM scores candidate solutions/steps so search or best-of-N can pick the best — this is where PRMs deliver the most value.

The **PRM survey** (arXiv:2510.08049) traces the field from outcome signals to process supervision and covers automatic PRM-label generation (e.g., Monte-Carlo rollouts that label a step by how often continuing from it reaches a correct answer — "Math-Shepherd" style), which removes the human-labeling bottleneck.

---

## 5. Parallel test-time compute — best-of-N, self-consistency, verifiers

The simplest way to spend more inference compute: **sample multiple independent solutions and aggregate**. This is "parallel" scaling (independent samples) as opposed to "sequential" scaling (one long, self-correcting chain — §9).

- **Self-consistency** (Wang et al., 2022, arXiv:2203.11171): sample N diverse CoT paths with temperature > 0, then **take the majority-vote final answer** (marginalizing over reasoning paths). Requires no extra model — just the solver — and reliably beats greedy single-path CoT. The canonical, cheapest TTC method for tasks with a discrete answer. Diminishing returns set in as N grows (gains are roughly logarithmic in N).
- **Best-of-N (BoN) with a verifier/reward model:** sample N solutions, **score each with an ORM/PRM (or a generative verifier)**, and return the highest-scored one. Unlike majority vote, BoN can pick a *minority-but-correct* answer if the verifier recognizes it — so it scales better when a good verifier exists. **Weighted best-of-N** combines both: weight votes by verifier score.
- **Generative verifiers (GenRM, arXiv:2408.15240):** instead of a scalar reward head, train the verifier to *generate* a correctness judgment as next-token prediction ("Is this correct? Yes/No" with its own CoT). This lets the verifier itself **use CoT and its own test-time compute** (e.g., majority-vote the verdict), giving 16–40% more problems solved at BoN on math/algorithmic tasks vs a discriminative ORM.
- **Self-certainty / confidence-based selection** (arXiv:2502.18581): use the model's *own* output-distribution confidence to rank the N samples — a verifier-free BoN proxy that scales without a reward model.

**Verifier quality is the ceiling on BoN.** A weak verifier makes BoN plateau or even degrade as N grows (you increasingly select confidently-wrong answers — "reward over-optimization" at inference). With a perfect verifier (e.g., unit tests for code), BoN is extremely strong: pass@N rises steeply.

---

## 6. Search-based test-time compute — beam, lookahead, MCTS, reward-guided decoding

Beyond independent samples, you can **search over the space of reasoning steps**, using a process verifier to guide which partial paths to expand. The tree-search-for-reasoning survey (arXiv:2510.09988) unifies these.

- **Step-level beam search:** expand the solution step-by-step; at each step sample several continuations, score partial paths with a **PRM**, and keep the top-`b` (beam width). Spends compute on promising prefixes instead of full independent rollouts.
- **Lookahead search:** at each step, roll out a few steps ahead (or to completion) to estimate a partial path's value before committing — more accurate per-step scoring, more compute per step.
- **MCTS-style search** (e.g., **ReST-MCTS\***, rStar, AlphaZero-flavored methods): build a search tree of reasoning steps with selection (UCT), expansion, simulation, and backpropagation of value estimates. A process reward / value model guides exploration vs exploitation. MCTS is the most compute-intensive but, with a good value model, the most sample-efficient for very hard problems; it also **generates high-quality process labels** for self-training (the search finds good trajectories you then SFT/RL on).
- **Reward-guided / verifier-guided decoding:** more generally, steer token- or step-level generation with a reward/value signal so the decode itself favors high-reward continuations.

**When search beats best-of-N (Snell et al., 2024):** on **easier** problems, simple best-of-N / sequential revision is compute-optimal; on **harder** problems, **search (beam/lookahead) over a PRM** uses the budget better. The optimal strategy is **difficulty-dependent** — there is no single best TTC method (§7). Caveat: much of the strongest search work uses small models + strong PRMs on math; with a top-tier reasoning model that already does long-CoT, a long single chain plus self-consistency often matches elaborate external search at lower engineering cost.

---

## 7. Inference-time scaling laws and compute-optimal test-time scaling

Just as pretraining has scaling laws, **inference has scaling laws**: accuracy improves predictably as you spend more test-time compute, up to a point.

- **Inference Scaling Laws** (Wu et al., 2024, arXiv:2408.00724): for a fixed *inference* compute budget, there is an **optimal model size** — and it is often **smaller than you'd pick for single-shot use**. A smaller model run with more samples/search can beat a larger model run once, at equal inference FLOPs. Error rates fall smoothly with inference compute, and the **compute-optimal model size shifts smaller as the inference budget grows**.
- **Compute-Optimal Test-Time Scaling** (Snell et al., 2024, arXiv:2408.03314): the headline result — **optimally allocating test-time compute can be more effective than scaling model parameters.** The two main TTC "knobs" are (a) **refining the proposal distribution** (sequential revisions — the model edits its own answer) and (b) **searching against a verifier** (PRM-guided beam/best-of-N). Crucially, the **best knob depends on prompt difficulty**: easy → sequential revision; hard → search. They define a **"compute-optimal" scaling strategy** that picks the knob per-difficulty, and show that under it a smaller model + TTC can **match a ~14× larger model** on some problem distributions.
- **TTC vs pretraining is not free lunch:** Snell et al. also note the trade is **problem-dependent and bounded** — on the hardest problems beyond a base model's reach, *no* amount of TTC closes the gap; you need a stronger base model. And a 2026 result ("Test-Time Scaling Makes Overtraining Compute-Optimal," arXiv:2604.01411) shows the optimal *pretraining* recipe shifts once you account for downstream TTC. **Practical rule:** TTC buys the most on problems within a model's reach that it gets wrong by *under*-thinking; it cannot manufacture capability the base model lacks.

---

## 8. The reasoning-model landscape — the o-series, R1-class, and mid-2026 SOTA

- **OpenAI o-series** — **o1** (late 2024) launched the category: "trained with RL to think before answering" with a long hidden CoT; the *reasoning tokens are not shown* to the user (summarized only). **o3 / o4-mini** (system card, Apr 16 2025) scaled the RL and added **native tool use inside the reasoning loop** (browsing, Python, image analysis). Key dial: **reasoning effort** (`low`/`medium`/`high`, e.g. `o4-mini-high`) trades latency/cost for accuracy; OpenAI confirmed performance keeps climbing with more inference-time reasoning. o1/o3 are the proprietary reference points; R1 is the open one.
- **DeepSeek-R1 / R1-Zero** (Jan 2025) — the first openly published o1-class reasoning model, MIT-licensed, with the full recipe (§2) and **R1-Distill** checkpoints (§10). It made the entire reasoning-RL recipe reproducible and triggered the open-reasoning wave.
- **Hybrid "thinking" models** — rather than ship a separate reasoning model, the major labs added a **toggleable thinking mode** to general models, with an explicit **thinking budget**:
  - **Gemini 2.5** (Pro/Flash, 2025) — "thinking models" with a developer-set **thinking budget** (0 disables thinking; up to tens of thousands of tokens). Thinking tokens are billed as output.
  - **Claude extended thinking** — a `thinking` block with a developer-set **budget_tokens** (min 1,024); Anthropic recommends starting at the minimum and raising it. Visible (summarized) thinking, billed as output tokens.
  - **Qwen / other open families** ship "thinking" variants and hybrid toggles.
- **Mid-2026 SOTA (directional — version numbers move monthly).** As of mid-2026 the frontier is a **three-way race** (OpenAI GPT-5.x, Google Gemini 3.x, Anthropic Claude Opus 4.x), all reasoning/thinking models, with **GPQA-Diamond saturating in the low-to-mid 90s%** and **AIME 2025 effectively solved** by the top models (≈95% no-tools, ~100% with code execution). No single model dominates — each leads a different problem shape (math/science vs agentic coding vs abstract reasoning like ARC-AGI-2). The reliable signal isn't the leaderboard number (benchmarks saturate, §11) but the *shape*: every frontier model now ships long-CoT reasoning with a controllable compute budget. **Anchor exact figures to the primary system cards/papers, not to secondary blog roundups** (version labels and headline numbers in those vary).

---

## 9. Budget forcing and thinking-token control

Once a model produces long-CoT, you need a **dial on how much it thinks**. Two layers:

- **API-level thinking budget** (production): set a max thinking-token budget per request (Gemini `thinkingBudget`, Claude `budget_tokens`, OpenAI `reasoning_effort`). Higher budget → better on hard problems, but **more latency and cost** (thinking tokens are billed, usually at output rates). Lower/zero budget for easy tasks (fact lookup, classification) where reasoning is wasted (§12).
- **Budget forcing** (research technique, **s1**, Muennighoff et al., 2025, arXiv:2501.19393): a remarkably simple way to *control and extend* test-time compute by editing the decode:
  - **To cap thinking:** force-append the end-of-thinking delimiter + a "Final Answer:" cue, making the model stop and commit.
  - **To extend thinking:** when the model tries to end its thinking, **suppress the end token and append "Wait"** (one or more times). The model continues — often **catching and fixing its own errors** on the extra pass. This is **sequential** test-time scaling (one chain made longer), which the s1 authors find scales more cleanly than parallel sampling for a fixed budget.
  - **s1 result:** SFT **Qwen2.5-32B on just 1,000 curated reasoning traces (s1K)** — selected for *difficulty, diversity, quality* — plus budget forcing yields **s1-32B**, which **exceeds o1-preview on AIME24/MATH by up to 27%**, and budget forcing **extrapolates AIME24 from 50%→57%** by simply forcing more "Wait"s. The headline lesson of s1: **a tiny amount of high-quality long-CoT SFT + a test-time control knob recovers much of the reasoning gain** — reasoning ability is substantially *elicited*, not only *trained in* with massive RL.
- **Overthinking / underthinking** are the failure modes of the dial (§12).

---

## 10. Distilling reasoning into smaller models

You don't have to *RL* a small model to make it reason — you can **distill** a big reasoning model's long-CoT into a smaller one via plain SFT on its traces.

- **DeepSeek-R1-Distill** (released with R1): generate **~800K reasoning samples from R1**, then **SFT** them into smaller bases — **Qwen** (1.5B/7B/14B/32B) and **Llama** (8B/70B). **No RL stage** on the small model — just supervised fine-tuning on the teacher's traces.
- **Headline finding (decision-relevant):** **distillation beats running RL directly on the small model.** DeepSeek showed that R1-Distill-Qwen-32B (e.g., **72.6% pass@1 AIME 2024**, **94.3% MATH-500**) **outperforms** trying to RL that same 32B from scratch — and even beats much larger *non-reasoning* models (GPT-4o, Claude-3.5-Sonnet of that era) on reasoning benchmarks. **The practical rule: if a strong reasoning teacher exists, distill from it before spending compute on RL for a small model.** RL pays off mainly at the frontier (where no stronger teacher exists). This connects to the §3 debate: if RLVR mostly *sharpens* base-distribution paths, a teacher that already found those paths can transfer them cheaply by SFT.
- **Caveats:** the student inherits the teacher's *failure modes* and *style* (verbosity, language quirks); distillation transfers what the teacher can do, not beyond it; license terms on teacher outputs matter. (For the broader compression toolkit — quantization, pruning, merging — see `llm-compression.md`; this section is specifically about distilling *reasoning behavior*.)

---

## 11. Reasoning benchmarks — and why they keep breaking

Reasoning models are evaluated on **verifiable, hard** tasks (so RLVR/verifier signals apply):

- **AIME (2024/2025):** 30 competition-math problems with integer answers 000–999 — the canonical hard-math reasoning eval. Small N (30 problems) makes single runs **high-variance**; report **pass@1 averaged over many seeds** (e.g., avg@32), not a single attempt.
- **MATH / MATH-500:** competition math; **largely saturated** by frontier reasoning models (>94%), so it now mainly separates mid-tier models.
- **GPQA-Diamond:** ~198 **graduate-level, Google-proof** science questions (bio/chem/physics) written by domain experts — a reasoning eval resistant to lookup. Approaching saturation at the frontier (low-to-mid 90s%) but still discriminates the 60–90% band.
- **LiveCodeBench** (arXiv:2403.07974): **contamination-free** competitive-programming eval — every problem is **timestamped by release date**, so you can evaluate a model **only on problems published after its training cutoff**, defeating memorization. The gold standard for *honest* code-reasoning numbers. (A harder "LiveCodeBench Pro" curated by olympiad medalists, arXiv:2506.11928, pushes the frontier.)

**Evaluation hygiene (treat as the real lesson):**
- **Contamination & saturation** are the dominant threats. Legacy benchmarks (MATH, GPQA) saturate within a model generation or two, and static test sets leak into training corpora. Prefer **time-gated / live** benchmarks (LiveCodeBench), **freshly authored** sets (AIME each year), and **contamination-mitigation** synthesis (arXiv:2509.00072).
- **pass@1 vs pass@k:** pass@1 measures single-shot accuracy (what users get); pass@k measures *coverage* (whether the model *can* solve it in k tries) — the §3 RLVR debate hinges on the gap between them. Report both when claiming RL "improved reasoning."
- **Variance:** on tiny sets like AIME, always average many samples; a single pass@1 is noise.
- **Tools vs no-tools:** "100% AIME with code execution" ≠ "100% innate math." State the tool condition.

---

## 12. Cost, latency, and accuracy trade-offs (the operating decision)

Reasoning is **expensive**: thinking tokens are billed (usually at output rates) and **dominate latency** — a hard query can burn tens of thousands of hidden tokens before the first visible output. The engineering job is allocating that budget.

- **Route by difficulty.** Don't pay for reasoning on easy tasks. Use a cheap/non-thinking model (or `reasoning_effort: low` / `thinkingBudget: 0`) for retrieval, classification, formatting, simple Q&A; reserve high thinking budgets for genuinely hard math/code/planning. A router or a difficulty classifier in front of the model captures most of the savings.
- **Tune the budget empirically.** Accuracy vs budget is a **concave curve with sharply diminishing returns** — there's a knee beyond which extra thinking adds cost/latency but little accuracy. Sweep the budget on a representative eval set and pick the knee, per task type. Anthropic's guidance (start at the 1,024-token minimum and increase) operationalizes this.
- **Overthinking** = the model burns budget on easy problems, second-guesses a correct answer into a wrong one, or loops. **Underthinking** = budget too low, model commits before it has worked the problem. Both are real failure modes; budget control (§9) is the lever.
- **The "thinking-token trap":** thinking tokens count against `max_tokens`/output budget and can **silently consume the whole budget before any answer is emitted** — set thinking and answer budgets separately and monitor reasoning-token usage as a first-class cost metric.
- **TTC vs a bigger model (cost framing):** §7's scaling laws are also a *cost* argument — a smaller reasoning model with a tuned budget can be **cheaper at equal accuracy** than a larger single-shot model on many workloads, but only within the smaller model's capability ceiling. Benchmark both on *your* traffic.
- **Caching & latency mitigation:** prompt/prefix caching (see `llm-inference-serving.md`) cuts the *input* cost of long reasoning prompts but not the thinking-token cost; streaming the thinking summary improves perceived latency.

---

## Practical patterns

- **Building a reasoning model (open recipe):** start from the **R1 template** — small cold-start long-CoT SFT → **GRPO with rule-based verifiable rewards** (accuracy + format) → rejection-sample SFT → final RL. Use a **length-corrected GRPO variant** to avoid length bias. Add a **language-consistency reward** if you see language mixing.
- **Cheapest path to a reasoning small model:** **distill** (SFT on a strong teacher's traces, §10) before attempting RL. Try **s1-style** tiny-but-curated SFT (1K high-quality traces) + budget forcing first — it's astonishingly strong for the cost.
- **Squeezing more accuracy at inference without retraining:** (1) **self-consistency** (majority vote over N samples) if the answer is discrete and you have no verifier; (2) **best-of-N with a verifier** (unit tests for code; PRM/GenRM for math) if a verifier exists; (3) **PRM-guided beam/lookahead search** for the hardest problems; (4) **budget forcing / raise the thinking budget** for sequential scaling. Pick by **difficulty** (Snell): easy → revise/self-consistency; hard → search.
- **Verifier first.** Most TTC value comes from a good verifier. For code, your verifier is **tests** — invest there. For math, a **GenRM** or PRM. A weak verifier caps best-of-N and can make it *worse* at large N.
- **Operate it:** route by difficulty, sweep the budget to the knee, treat reasoning tokens as a first-class cost/latency metric, separate thinking and answer budgets.

## Anti-patterns

- **Treating the visible CoT as ground-truth mechanism** — it can be unfaithful/post-hoc; don't build safety or audit guarantees on raw CoT (§1).
- **Conflating speculative decoding with test-time scaling** — speculative decoding makes tokens *faster*; TTC spends *more* compute for a *better* answer. Different goals; one is in `llm-inference-serving.md` (§Scope).
- **Conflating RLHF/DPO with reasoning-RL** — different objective (preference vs verifiable correctness). Use `llm-alignment-post-training.md` for the former.
- **Using a PRM as the RL reward by default** — R1's lesson: PRMs are reward-hackable and fuzzy to define as an RL signal; prefer **rule-based outcome+format rewards for RL**, and **save the PRM for test-time verification** (§4).
- **Cranking the thinking budget globally** — pays cost/latency on easy traffic and risks overthinking; route by difficulty and tune to the knee (§12).
- **Assuming RLVR creates new capability** — contested (§3); it reliably improves pass@1 sample-efficiency but may only sharpen base-distribution reasoning. If a stronger teacher exists, distill (§10).
- **Trusting saturated/contaminated benchmarks** — MATH/GPQA saturate; static sets leak. Use time-gated/live evals and report pass@1 over many seeds with the tool condition stated (§11).
- **Best-of-N with a weak verifier at large N** — selects confidently-wrong answers; verifier quality is the ceiling (§5).

## Troubleshooting

- **Reasoning model gives no/empty answer, or truncates mid-thought** → thinking tokens consumed the entire output budget ("thinking-token trap"). Raise/separate `max_tokens` from the thinking budget; monitor reasoning-token counts (§12).
- **Long-CoT model switches languages / unreadable** → R1-Zero symptom; add cold-start SFT and a **language-consistency reward**, or use the distilled (R1-Distill) variant which is cleaner (§2, §10).
- **RL reasoning training: responses keep getting longer with no accuracy gain** → GRPO length bias; switch to a length-normalized/token-level GRPO variant (Dr. GRPO-style) (§2).
- **Best-of-N stops helping (or degrades) as N grows** → verifier is too weak (reward over-optimization at inference). Improve the verifier (tests for code; GenRM for math) or fall back to self-consistency (§5).
- **Small model won't learn to reason under RL** → expected; RL on small models is sample-hungry and may not exceed the base ceiling. **Distill from a stronger teacher instead** (§10, §3).
- **High cost/latency in production** → route by difficulty, drop the budget to the empirical knee, disable thinking on easy intents, cache long prompt prefixes (§12).
- **AIME/benchmark score swings run-to-run** → tiny test set; average pass@1 over many seeds (avg@k); don't report a single attempt (§11).

## References (primary sources)

- Wei et al. (2022), *Chain-of-Thought Prompting Elicits Reasoning in LLMs* — arXiv:2201.11903 (NeurIPS 2022).
- Wang et al. (2022), *Self-Consistency Improves Chain-of-Thought Reasoning* — arXiv:2203.11171.
- Lightman et al. (2023), *Let's Verify Step by Step* (PRM800K, process supervision) — OpenAI.
- Shao et al. (2024), *DeepSeekMath* (GRPO) — arXiv:2402.03300.
- Wu et al. (2024), *Inference Scaling Laws: Compute-Optimal Inference* — arXiv:2408.00724.
- Snell et al. (2024), *Scaling LLM Test-Time Compute Optimally…* — arXiv:2408.03314.
- Zhang et al. (2024), *Generative Verifiers: Reward Modeling as Next-Token Prediction* — arXiv:2408.15240.
- Lambert et al. (2024), *Tülu 3* (RLVR) — arXiv:2411.15124.
- DeepSeek-AI (2025), *DeepSeek-R1 / R1-Zero* — arXiv:2501.12948 (+ R1-Distill checkpoints).
- Muennighoff et al. (2025), *s1: Simple Test-Time Scaling* (budget forcing, s1K) — arXiv:2501.19393.
- OpenAI (2025), *o3 and o4-mini System Card* (reasoning effort, RL-trained reasoning) — Apr 16 2025.
- Yue et al. (2025), *Does RL Really Incentivize Reasoning Capacity Beyond the Base Model?* — arXiv:2504.13837 (RLVR debate); cf. arXiv:2506.14245.
- *A Survey of Process Reward Models* — arXiv:2510.08049.
- *Unifying Tree Search Algorithms and Reward Design for LLM Reasoning: A Survey* — arXiv:2510.09988.
- Jain et al. (2024), *LiveCodeBench* (contamination-free code eval) — arXiv:2403.07974.
- Google (2025), *Gemini 2.5 thinking models / thinking budget* — ai.google.dev/gemini-api/docs/thinking. Anthropic, *Building with extended thinking* — platform.claude.com docs.
