---
title: "Comparing Output Quality Across Claude Model Tiers and Effort Levels"
description: "A reported June Claude comparison with one response per condition; raw outputs are missing, and its score differences do not establish causal effects."
date: "2026-09-05"
order: 11
---

*A reported experiment from 2026-06-17, using Claude Code subagent model overrides. The tables preserve the author's single-sample scores. Original model responses, routing receipts, token counts, and grader records were not recovered in the September 30 review, so these results are not independently verified or sufficient for model-selection guidance.*

---

## Abstract

I ran a fixed 4-task benchmark (quantitative reasoning, logic deduction, code generation, constrained writing) against three reported model tiers (**Haiku 4.5**, **Sonnet 4.6**, and **Opus 4.8**) and, separately, against two **effort** prompt regimes (visible working omitted versus requested) on the two endpoint models. Grading used a rubric fixed before any output was seen (max 40 points).

At neutral prompting, the reported totals were 38–40 / 40. The two prompt regimes differed by 10 points for Haiku and Opus, entirely on the arithmetic item. Those descriptive differences do not isolate a causal effect of internal reasoning or establish that prompting matters more than model tier: each condition has one response, the tasks are few, and the original outputs are unavailable for independent grading.

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

Each model was driven as a fresh Claude Code subagent with the `model` parameter set to the tier; agents were instructed to answer directly with **no tool or skill use**, so tool assistance was intended to be excluded. The system instructions, routing behavior, and other harness settings were not archived; the scores cannot be attributed to an isolated base model. (Exact per-token pricing is deliberately not asserted here; tier *ordering* by cost/capability is Haiku < Sonnet < Opus.)

### 2.2 The "effort level" lever — what it is and is not

There is no public per-request "reasoning effort" dial exposed through the subagent interface I used, so **effort here is a prompt-induced proxy**, operationalized as two prompt regimes applied to the *same* benchmark:

- **Low effort:** *"Answer as directly and briefly as possible. Do not show any reasoning or working. Give only the final answer."* (visible working omitted)  
- **High effort:** *"Reason carefully and step by step, consider edge cases, and double-check your work before giving your final answer."* (visible working requested)  
- **Neutral** (used in the tier experiment): answer each task, no constraint on showing work.

This is a real and well-understood lever (visible test-time reasoning / chain-of-thought), but it is **not** the same thing as a model-internal "thinking budget." Conclusions are scoped accordingly.

### 2.3 Benchmark (fixed before grading)

- **T1: Quantitative reasoning.** Tank holds 240 L, starts empty. Pipe A fills 8 L/min; pipe B drains 5 L/min. Both open 10 min, then B closes. How many *more* minutes after the first 10 to fill completely? **Ground truth: 26.25.** (30 L after 10 min; 210 L ÷ 8 = 26.25.)  
- **T2: Logic deduction.** Ann/Bob/Cara own cat/dog/fish. (1) Ann ≠ cat; (2) Bob = dog; (3) the fish owner is alphabetically first. **Ground truth: Ann=fish, Bob=dog, Cara=cat.**  
- **T3: Code generation.** `merge_intervals(intervals)` returns merged, sorted intervals; *touching* intervals (e.g., `[1,2]`,`[2,3]`) merge; handle the empty list. Graded on five test cases including empty, unsorted input, and a touching pair.  
- **T4: Constrained writing.** Explain how a DB index speeds queries for a layperson in **exactly 3 sentences, each < 20 words**, using none of {`pointer`, `B-tree`, `algorithm`}.

### 2.4 Rubric (0–10 per task, 40 total; fixed a priori)

- **T1:** 10 = 26.25 exact; 7 = right method, arithmetic slip; 4 = right setup, conceptual error; 0 = wrong/no answer.  
- **T2:** 10 = full correct assignment; 5 = partial; 0 = wrong.  
- **T3:** 10 = passes all 5 test cases (incl. touching + empty); −1 for spec deviations (e.g., returns tuples not `[start,end]`); 4 = partial; 0 = broken.  
- **T4:** 2 (exactly 3 sentences) + 2 (all sentences < 20 words; 1 if exactly one over) + 2 (no banned words) + 4 (clarity/accuracy for a layperson).

### 2.5 Design

- **Experiment A (tier):** 4 tiers attempted; 3 completed the full benchmark at neutral prompting. *n = 1 response per completed cell.*  
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

¹ The author reported tuple output instead of `[start,end]` lists (−1 under the stated rubric) and input mutation through `.sort()`. The task did not prohibit mutation, so it is not an additional specified failure. The original code and test receipts are unavailable. ² The first T4 sentence was reported as **21 words**; with fewer than 20 permitted, the maximum is 19, so 21 is two above it. The original text is unavailable for recounting.

**Finding (RQ1):** Reported totals differ by 2 points. Output type and sentence length are correctness requirements in this rubric, not merely presentation polish. This small, near-ceiling sample does not establish a monotonic population effect of model tier or meaningfully discriminate Sonnet from Opus.

### 3.2 Experiment B — effort level (Haiku & Opus)

| Condition | T1 quant | T2 logic | T3 code | T4 writing | Total / 40 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Haiku — low effort | **0**³ | 10 | 10 | 10 | **30** |
| Haiku — high effort | 10 | 10 | 10 | 10 | **40** |
| Opus — low effort | **0**⁴ | 10 | 10 | 10 | **30** |
| Opus — high effort | 10 | 10 | 10 | 10 | **40** |

³ Haiku low-effort answered T1 = **"15 minutes"** (wrong). ⁴ Opus low-effort answered T1 = **"30"** (wrong). These are the reported incorrect answers under the no-visible-working prompt; that prompt does not prove that internal reasoning was absent.

**Finding (RQ2):** The reported total is 10 points higher under the visible-working prompt for each model, with all of that difference in T1. With one response per condition and no controlled timing, this is an observed score difference rather than a reliable effect size or evidence that the incorrect answers were faster. Repeated, randomized trials are needed to assess H2.

### 3.3 Interaction (RQ3)

|  | Low | High | Effort Δ |
| :---- | :---- | :---- | :---- |
| Haiku | 30 | 40 | **+10** |
| Opus | 30 | 40 | **+10** |

**Finding (RQ3):** Both reported differences are +10, so the observed difference of differences is zero. Without repeats or variance estimates, this is not a statistical test showing that an interaction is absent. The proposed scratch-space explanation was not tested, and H3 remains unresolved.

### 3.4 Cross-experiment note

Neutral-prompt Haiku and Opus both scored T1 correctly (they were free to show work): Haiku's total (38) landed *between* the low- and high-effort conditions, while Opus's (40) matched the high-effort condition outright. This does not identify the operative variable: internal reasoning, output length, sampling variation, and other harness differences were not controlled.

---

## 4. Analysis

1. **The neutral totals show little separation in this sample.** The reported Haiku output failed the return-type and sentence-length requirements, while Sonnet and Opus received full marks. These are rubric differences in single responses; they do not establish the value of paying for a larger model on other tasks.  
     
2. **The prompt regimes differ by 10 points in the reported samples.** That is 25% of the 40-point scale, or a 33.3% increase relative to 30. It is larger than the neutral tier difference observed here, but this design cannot compare general prompt and scaling effects or their costs.  
     
3. **T1 carried the Experiment B score difference.** T2/T3/T4 were 10/10 in every Experiment B condition. The neutral-prompt comparison also showed Haiku's T3 return-type and T4 sentence-length failures; those were correctness requirements in the rubric. Interpret each difference against the task's stated requirements, and use harder or more varied tasks to distinguish near-ceiling results.

---

## 5. Limitations (read before citing any number)

- **n = 1 per cell.** No repeats, so no variance estimate and **no statistical significance**: every number is a single sample and could move on a re-run, especially the near-ceiling 10s. Treat all findings as **directional**.  
- **"Effort" is a prompt label**, not a controlled internal reasoning budget. One prompt forbids visible working and the other requests it. The experiment does not measure how much hidden reasoning either model performed.  
- **Self-grading bias.** The grader is the same model family as the subjects (I scored my own family's outputs). Best practice (`eval-driven-development`) is a *different*-family judge plus human calibration (Cohen's κ); neither was done here. Grading was kept objective where possible (T1–T3 have checkable answers; T4 constraints are countable) to limit this, but T4's 4 "clarity" points are subjective.  
- **Ceiling effect / tiny benchmark.** Four tasks, three of them too easy to separate the tiers. A fair tier comparison needs harder, more numerous items (long-context, ambiguous spec, adversarial edge cases) where Opus would be expected to pull ahead.  
- **Fable 5 was unavailable**, so the frontier tier is missing entirely.  
- **No latency/cost axis.** Quality-per-dollar and quality-per-second were not measured; those metrics often guide tier selection. (Observed wall-clock durations were small and not controlled.)

---

## 6. Conclusion

The preserved tables report neutral scores of 38, 40, and 40 and a 10-point prompt-regime difference for Haiku and Opus, entirely in one arithmetic item. They do not establish a causal prompting advantage, the absence of an interaction, or a cheaper model-selection strategy. A follow-up needs archived raw outputs and exact model-routing receipts, randomized repeated trials, a larger task set, independent grading, and measured token cost and latency. The current results are a small historical observation whose grading could not be independently reproduced.

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

- **`eval-driven-development`**: supplied the discipline: a rubric fixed before grading, objective-where-possible metrics, LLM-as-judge bias awareness (position/self-preference), and the ceiling-effect/error-analysis lens used in §3–§5.  
- **`claude-api`**: source for the correct model IDs and tier ordering in §2.1.  
- **`da-applied-and-communication`**: BLUF structure, results tables, and honest-uncertainty disclosure in the Limitations section.

## Appendix C — Assumptions [ASSUMED]

- "Different Claude models" was interpreted as the **tier lineup** (Haiku/Sonnet/Opus, plus Fable 5 if available), not historical versions.  
- "Effort levels" was interpreted as a **prompt-induced reasoning regime** (the only effort lever available through the subagent interface), explicitly flagged as a proxy.  
- A compact 4-task benchmark with n=1 was chosen to fit a single interactive session; this is the central limitation, not a recommended design.
