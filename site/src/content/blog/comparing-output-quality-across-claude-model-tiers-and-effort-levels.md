---
title: "Comparing Output Quality Across Claude Model Tiers and Effort Levels"
description: "A small benchmark finding that Claude model tier barely affected correctness, while a step-by-step reasoning 'effort' prompt produced a far larger score swing concentrated entirely in one multi-step arithmetic task."
date: "2026-09-05"
order: 11
---

*An experiment run end-to-end on 2026-06-17. All numbers below are from outputs actually generated this run by dispatching the same benchmark to different Claude models via the Claude Code subagent `model` override. No figures are imported from training data or external leaderboards.*

---

## Abstract

I ran a fixed 4-task benchmark (quantitative reasoning, logic deduction, code generation, constrained writing) against three live Claude model tiers — **Haiku 4.5**, **Sonnet 4.6**, and **Opus 4.8** — and, separately, against a two-level **effort** manipulation (reasoning suppressed vs. reasoning required) on the two endpoint models. Grading used a rubric fixed before any output was seen (max 40 points).

**Bottom line up front:** at neutral prompting the three tiers were nearly indistinguishable (38–40 / 40); the tasks were near the models' ceiling. The **effort manipulation moved scores more than the model tier did**: suppressing visible step-by-step reasoning dropped *both* Haiku and Opus from 40 to 30, and the entire 10-point loss came from a single multi-step arithmetic task that both models got wrong without externalized reasoning. The practical implication: for multi-step reasoning, *how* you prompt (whether the model is allowed to work step-by-step) can dominate *which* tier you pick.

---

## 1. Research questions and hypotheses

- **RQ1 (tier effect):** Does output quality increase monotonically from Haiku → Sonnet → Opus on a mixed benchmark?  
  - *H1:* Larger tiers score higher, with the gap largest on the hardest tasks.  
- **RQ2 (effort effect):** Does increasing "effort" (requiring explicit step-by-step reasoning vs. forbidding it) improve quality?  
  - *H2:* Higher effort improves quality, most on multi-step tasks.  
- **RQ3 (interaction):** Does the weaker model (Haiku) benefit more from added effort than the stronger one (Opus)?  
  - *H3:* Effort helps Haiku more than Opus (Opus is closer to ceiling).

---

## 2. Method

### 2.1 Models under test

| Tier label | Model | Model ID | Role |
| :---- | :---- | :---- | :---- |
| Small | Haiku 4.5 | `claude-haiku-4-5-20251001` | Fastest / lowest-cost tier |
| Mid | Sonnet 4.6 | `claude-sonnet-4-6` | Balanced quality/cost |
| Large | Opus 4.8 | `claude-opus-4-8` | Most capable tier |
| Frontier | Fable 5 | `claude-fable-5` | **Not tested — returned "currently unavailable" this run** |

Each model was driven as a fresh Claude Code subagent with the `model` parameter set to the tier; agents were instructed to answer directly with **no tool or skill use**, so the score reflects the base model, not an agentic harness. (Exact per-token pricing is deliberately not asserted here; tier *ordering* by cost/capability is Haiku < Sonnet < Opus.)

### 2.2 The "effort level" lever — what it is and is not

There is no public per-request "reasoning effort" dial exposed through the subagent interface I used, so **effort here is a prompt-induced proxy**, operationalized as two prompt regimes applied to the *same* benchmark:

- **Low effort:** *"Answer as directly and briefly as possible. Do not show any reasoning or working. Give only the final answer."* (chain-of-thought suppressed)  
- **High effort:** *"Reason carefully and step by step, consider edge cases, and double-check your work before giving your final answer."* (chain-of-thought required)  
- **Neutral** (used in the tier experiment): answer each task, no constraint on showing work.

This is a real and well-understood lever (visible test-time reasoning / chain-of-thought), but it is **not** the same thing as a model-internal "thinking budget." Conclusions are scoped accordingly.

### 2.3 Benchmark (fixed before grading)

- **T1 — Quantitative reasoning.** Tank holds 240 L, starts empty. Pipe A fills 8 L/min; pipe B drains 5 L/min. Both open 10 min, then B closes. How many *more* minutes after the first 10 to fill completely? **Ground truth: 26.25.** (30 L after 10 min; 210 L ÷ 8 = 26.25.)  
- **T2 — Logic deduction.** Ann/Bob/Cara own cat/dog/fish. (1) Ann ≠ cat; (2) Bob = dog; (3) the fish owner is alphabetically first. **Ground truth: Ann=fish, Bob=dog, Cara=cat.**  
- **T3 — Code generation.** `merge_intervals(intervals)` returns merged, sorted intervals; *touching* intervals (e.g., `[1,2]`,`[2,3]`) merge; handle the empty list. Graded on five test cases including empty, unsorted input, and a touching pair.  
- **T4 — Constrained writing.** Explain how a DB index speeds queries for a layperson in **exactly 3 sentences, each < 20 words**, using none of {`pointer`, `B-tree`, `algorithm`}.

### 2.4 Rubric (0–10 per task, 40 total; fixed a priori)

- **T1:** 10 = 26.25 exact; 7 = right method, arithmetic slip; 4 = right setup, conceptual error; 0 = wrong/no answer.  
- **T2:** 10 = full correct assignment; 5 = partial; 0 = wrong.  
- **T3:** 10 = passes all 5 test cases (incl. touching + empty); −1 for spec deviations (e.g., returns tuples not `[start,end]`); 4 = partial; 0 = broken.  
- **T4:** 2 (exactly 3 sentences) + 2 (all sentences < 20 words; 1 if exactly one over) + 2 (no banned words) + 4 (clarity/accuracy for a layperson).

### 2.5 Design

- **Experiment A (tier):** 4 tiers × neutral prompting × full benchmark. *n = 1 per cell.*  
- **Experiment B (effort):** {Haiku, Opus} × {low, high} × full benchmark. *n = 1 per cell.*

---

## 3. Results

### 3.1 Experiment A — model tier (neutral prompting)

| Model | T1 quant | T2 logic | T3 code | T4 writing | Total / 40 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Haiku 4.5 | 10 | 10 | 9¹ | 9² | **38** |
| Sonnet 4.6 | 10 | 10 | 10 | 10 | **40** |
| Opus 4.8 | 10 | 10 | 10 | 10 | **40** |
| Fable 5 | — | — | — | — | **n/a (unavailable)** |

¹ Haiku's `merge_intervals` returned **tuples** instead of the specified `[start,end]` lists and mutated its input via `.sort()`; logic was correct on all five test cases (−1 for spec deviation). ² Haiku's first T4 sentence was **21 words** (one over the < 20 limit); the other two constraints were met (−1).

**Finding (RQ1):** Tier separation was minimal. Haiku trailed by 2 points on *presentation/spec* details, not on correctness. With these tasks near ceiling, **H1 is only weakly supported** — the benchmark cannot discriminate the top tiers.

### 3.2 Experiment B — effort level (Haiku & Opus)

| Condition | T1 quant | T2 logic | T3 code | T4 writing | Total / 40 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Haiku — low effort | **0**³ | 10 | 10 | 10 | **30** |
| Haiku — high effort | 10 | 10 | 10 | 10 | **40** |
| Opus — low effort | **0**⁴ | 10 | 10 | 10 | **30** |
| Opus — high effort | 10 | 10 | 10 | 10 | **40** |

³ Haiku low-effort answered T1 = **"15 minutes"** (wrong). ⁴ Opus low-effort answered T1 = **"30"** (wrong) — i.e., even the largest tier failed the multi-step arithmetic when forbidden from showing work.

**Finding (RQ2):** Effort had a **large, clean effect: +10 points** for both models, **entirely** attributable to T1. When reasoning was suppressed, both models produced a fast wrong number on the only genuinely multi-step task; when reasoning was required, both produced the exact answer. **H2 is supported, with the strong caveat that the effect was concentrated in one task type (multi-step quantitative).**

### 3.3 Interaction (RQ3)

|  | Low | High | Effort Δ |
| :---- | :---- | :---- | :---- |
| Haiku | 30 | 40 | **+10** |
| Opus | 30 | 40 | **+10** |

**Finding (RQ3):** **No interaction detected** — effort helped both models identically (+10). **H3 is not supported** in this data: the larger model was *not* more robust to reasoning suppression; Opus failed T1 at low effort just as Haiku did. (This is plausibly because the failure mode is "no scratch space for multi-step arithmetic," which afflicts any model regardless of size.)

### 3.4 Cross-experiment note

Neutral-prompt Haiku and Opus both scored T1 correctly (they were free to show work): Haiku's total (38) landed *between* the low- and high-effort conditions, while Opus's (40) matched the high-effort condition outright. So the operative variable is not "more tokens" per se but **whether the model externalizes intermediate steps** on a multi-step problem.

---

## 4. Analysis

1. **Tier choice was nearly irrelevant for correctness on this set.** All three tiers solved the logic puzzle, wrote correct interval-merging code, and followed the writing constraints. The only tier-linked differences were cosmetic/spec (Haiku's tuple output and one 21-word sentence). On easy-to-mid tasks, paying for a larger tier bought *polish*, not *correctness*.  
     
2. **The effort lever dominated.** A prompt change worth zero extra model capability swung the score by 25% (30 → 40) — a larger effect than any tier difference observed. The lesson mirrors the test-time-compute literature: for multi-step reasoning, *eliciting* reasoning matters more than scaling the model.  
     
3. **The discriminating task carried the whole signal.** T2/T3/T4 were at ceiling in every condition (10/10 everywhere except Haiku's two cosmetic dings). All variance lived in T1. This is itself the most important methodological result: **a benchmark only teaches you something on items that are hard enough to fail.**

---

## 5. Limitations (read before citing any number)

- **n = 1 per cell.** No repeats, so no variance estimate and **no statistical significance** — every number is a single sample and could move on a re-run, especially the near-ceiling 10s. Treat all findings as **directional**.  
- **"Effort" is a prompt proxy**, not a model-internal reasoning-budget setting. The low-effort result partly measures "what happens when you forbid chain-of-thought," which is a known failure mode and may overstate how often a normally-prompted model would fail.  
- **Self-grading bias.** The grader is the same model family as the subjects (I scored my own family's outputs). Best practice (`eval-driven-development`) is a *different*-family judge plus human calibration (Cohen's κ); neither was done here. Grading was kept objective where possible (T1–T3 have checkable answers; T4 constraints are countable) to limit this, but T4's 4 "clarity" points are subjective.  
- **Ceiling effect / tiny benchmark.** Four tasks, three of them too easy to separate the tiers. A fair tier comparison needs harder, more numerous items (long-context, ambiguous spec, adversarial edge cases) where Opus would be expected to pull ahead.  
- **Fable 5 was unavailable**, so the frontier tier is missing entirely.  
- **No latency/cost axis.** Quality-per-dollar and quality-per-second — the metrics that usually decide tier selection — were not measured. (Observed wall-clock durations were small and not controlled.)

---

## 6. Conclusion

On this small benchmark, **model tier barely affected correctness** (Haiku 38, Sonnet 40, Opus 40 at neutral prompting), while the **effort regime had a large, clean effect** (+10/40 for both Haiku and Opus), concentrated entirely in multi-step arithmetic and showing **no tier × effort interaction**. The actionable takeaway: **for multi-step reasoning, ensure the model is prompted to reason step-by-step before reaching for a bigger, costlier tier — the prompt lever was the cheaper and larger win here.** These conclusions are directional only; a defensible version needs repeated trials, a harder and larger task set, an independent judge, and the missing cost/latency and Fable-5 data.

---

## Appendix A — Reproducibility

**Harness.** Each condition = one Claude Code subagent, `model` ∈ {`haiku`,`sonnet`,`opus`,`fable`}, instructed to use no tools/skills and to answer directly. Tier experiment used neutral prompting; effort experiment used the low/high preambles in §2.2.

**Verbatim task block sent to every agent (effort preamble prepended in Exp. B):**

```
T1: A water tank holds 240 liters and starts empty. Pipe A fills it at 8 liters
per minute; pipe B drains it at 5 liters per minute. Both pipes are open for the
first 10 minutes, then pipe B is closed and only pipe A continues. Starting from
empty, how many MORE minutes after the first 10 minutes are needed to fill the
tank completely?

T2: Ann, Bob, and Cara each own exactly one different pet: a cat, a dog, or a
fish. Clues: (1) Ann does not own the cat. (2) Bob owns the dog. (3) Among the
three owners, the fish owner's first name comes earliest alphabetically. Who owns
which pet?

T3: Write a Python function merge_intervals(intervals) that takes a list of
[start, end] integer pairs and returns the list of merged non-overlapping
intervals, sorted by start. Touching intervals like [1,2] and [2,3] must merge to
[1,3]. Handle the empty list.

T4: Explain, for a non-technical reader, how a database index makes queries
faster. Write EXACTLY three sentences. Each sentence must contain fewer than 20
words. Do NOT use the words "pointer", "B-tree", or "algorithm".
```

**T3 grading test cases:** `[]→[]`; `[[1,3],[2,6],[8,10],[15,18]]→[[1,6],[8,10],[15,18]]`; `[[1,2],[2,3]]→[[1,3]]`; `[[1,4],[5,6]]→[[1,4],[5,6]]`; `[[8,10],[1,3],[2,6]]→[[1,6],[8,10]]`.

**Rubric:** as in §2.4, fixed before outputs were seen.

## Appendix B — Skills applied

- **`eval-driven-development`** — supplied the discipline: a rubric fixed before grading, objective-where-possible metrics, LLM-as-judge bias awareness (position/self-preference), and the ceiling-effect/error-analysis lens used in §3–§5.  
- **`claude-api`** — source for the correct model IDs and tier ordering in §2.1.  
- **`da-applied-and-communication`** — BLUF structure, results tables, and honest-uncertainty disclosure in the Limitations section.

## Appendix C — Assumptions [ASSUMED]

- "Different Claude models" was interpreted as the **tier lineup** (Haiku/Sonnet/Opus, plus Fable 5 if available), not historical versions.  
- "Effort levels" was interpreted as a **prompt-induced reasoning regime** (the only effort lever available through the subagent interface), explicitly flagged as a proxy.  
- A compact 4-task benchmark with n=1 was chosen to fit a single interactive session; this is the central limitation, not a recommended design.