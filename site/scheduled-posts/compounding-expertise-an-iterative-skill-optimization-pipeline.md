---
title: "Compounding Expertise — An Iterative Skill-Optimization Pipeline"
description: "A retrospective on an iterative skill-optimization pipeline for MongoDB case resolution: its four stages, one blind 244-ticket backtest, and what that evidence does not show."
date: "2026-10-24"
order: 23
---

### How an iterative, multi-stage skill-optimization pipeline is built, and what one blind backtest shows about MongoDB case-resolution knowledge

**A technical retrospective from the mdb-tam (Technical Account Management) engineering work · first written June 2026, revised October 2026; backtest run late May 2026**

---

## Executive summary

Automated case resolution is, at its core, a prediction problem: given only what a customer first reported, predict the root cause accurately enough to act on. The instinct is to solve it with a bigger model and a bigger prompt. This paper argues that the binding constraint is knowledge engineering, not model size. The one measured comparison it reports fits that view without testing it: it compares strategies, each bundling its own prompt and knowledge, and it varies no model size.

We built a system that treats expertise as something to be engineered, not just prompted. It integrates five skillsets (MongoDB domain authority, applied psychology, writing, troubleshooting and diagnostic reasoning, and expertise engineering) and drives each through the same iterative, multi-stage optimization pipeline: acquire the missing knowledge, optimize every skill, prompt, and document to convergence against a severity-gated quality bar, compose the optimized components in a runtime orchestrator, and validate the diagnostic core with a blind backtest whose errors are meant to feed the next cycle.

We ran that backtest on a **blind panel of 244 tickets** (`blind-244-v1`) exported from one customer account. The predictor saw only the customer's first report, never the resolution, and the design calls for a separate grader (Section 4.3 says what the run records show). The skill-knowledge strategy (twelve `mongodb-*` skills, the kind of knowledge this pipeline exists to build and tune) scored:

- **72.5% raw accuracy** across all 244 cases (partial predictions get half credit),
- **90.3% accuracy on the 196 gradable cases** (the other 48 had no diagnostic content to grade), and
- **100% defensibility**: none of the gradable predictions was graded Wrong.

Treat these as plausibility scores from one account, not as verified accuracy: 185 of the 196 gradable cases were graded against auto-close echoes of the customer's first message, not against engineer-written resolutions (Section 4.3).

The comparison is the main finding. Skill knowledge outscored both an authored-flowchart bundle and a documented-flowchart corpus on this panel, and an after-the-fact best-of-three ensemble (a case counts as correct if any strategy got it right) added only 1.5 points (72.5% → 74.0%). The ranking is specific to this panel and rubric: it reverses on a 20-ticket seed panel graded with unequal thresholds and on a second account's 1,000-case set. Whether the optimization loop raised the score is untested: the backtest ran in late May 2026, before the optimizer runs on record for these skills (Section 4.3).

The intended reader is a technical leader deciding whether to invest in engineered, measured expertise over ad-hoc prompt iteration. The practical takeaway: build the blind panel, a separate grader, and a baseline first, because this paper compares strategies but does not measure the pipeline's lift.

**Scope and limits.** The backtest scores diagnostic accuracy only. The psychology and writing skillsets address whether the delivered reply repairs trust, avoids resistance, and lets a human calibrate trust in the AI's hypothesis; this backtest does not score that.

---

## 1. The problem: case resolution is a blind prediction under a low accuracy ceiling

A support case arrives as a customer's first description of a symptom. The resolver, human or machine, must predict the root cause from that description, gather the right evidence, and act. In our experience, three properties make this hard and make naive solutions plateau.

**It is blind.** At prediction time the resolution does not exist yet. Any method that has even indirect access to the answer in testing will overstate its real-world accuracy. A credible accuracy number can only come from a panel where the predictor sees what the customer first saw and nothing more.

**The domain is broad and interacting.** A MongoDB/Atlas case can sit in any of a dozen subdomains (among them CRUD and indexing, the aggregation framework, replication, sharding, drivers, the Atlas control plane, networking, encryption, search, and capacity), and the hardest cases span several at once. A method strong in one subdomain and weak in the next has a low ceiling on a representative panel.

**Resolution is more than the diagnosis.** Even a correct root cause fails the customer if the reply triggers reactance (resistance to being told what to do), erodes trust after an incident, or leaves a human unable to judge how far to trust the analysis. Accuracy and delivery are separate axes, and a system optimized for one can still fail on the other.

The consequence is a low, deceptive ceiling. Methods that look strong in a demo, such as a clever prompt or a favorite flowchart, can collapse on a broad blind panel when they were tuned against the cases their author already understood. The question this paper takes up is: *what architecture raises the real, blind-panel ceiling, and how do you show the number can be trusted?*

---

## 2. Why single-technique approaches fall short

Four common approaches each capture part of the answer and stall on the rest. Apart from the flowchart comparison (Section 4), these are arguments from our experience, not tested results.

**A bigger model with a bigger prompt.** Concatenating all available knowledge into one context window is easy and scales badly. It pays for redundant and irrelevant context on every call, buries the few relevant facts, and has no mechanism to *improve*. When it gets a case wrong, nothing changes. There is no loop.

**Raw, un-tuned domain knowledge.** A comprehensive knowledge base is necessary but not sufficient. Knowledge written for humans to browse is not organized for a model to retrieve and reason over under blind conditions. Without an optimization pass it tends to carry dead weight, ambiguity, and untested assumptions that surface as wrong or hedged predictions.

**Authored decision flowcharts.** Expert-authored flowcharts encode real diagnostic skill, but they encode *one expert's* paths. On a broad panel they are strong where the author's experience was deep and silent where it was thin. In our backtest, an authored-flowchart bundle and a documented-flowchart corpus both scored below skill knowledge on the 244-ticket panel, and adding them to it produced almost no lift (Section 4).

**Prompt iteration without evaluation.** Hand-tuning a prompt against a handful of cases optimizes for those cases. Without a blind panel and error analysis, the practitioner cannot tell whether a change helped in general or just fit the examples in front of them. This is the classic overfitting failure that `eval-driven-development` is built to prevent.

None of the four alone both raises knowledge quality systematically and measures the result on a blind panel. That is the joint problem the pipeline is built to solve.

---

## 3. The approach: five skillsets, one convergence loop

The system rests on a single idea: **treat expertise as an engineered artifact with a quality bar, a tuning loop, and an acceptance test.** Concretely, that means five complementary skillsets driven through four pipeline stages.

### 3.1 The five skillsets

A skill here is a packaged set of instructions and reference files that an agent loads on demand. The names below are working identifiers; Appendix A lists them by family. In brief:

1. **MongoDB domain authority.** The deep `mongodb-*` and Atlas expert hubs, compiled for diagnosis into the 66-part `uber-mongodb-skill` behind the read-only `uber-mongodb-diagnostician`. This is the diagnostic engine, and the agent is the productized form of the skill-knowledge strategy tested in Section 4, although the agent itself was not part of that run.
2. **Troubleshooting and diagnostic reasoning.** The methodology of fault-finding: choosing a diagnostic surface, gathering evidence, and the illness-script and key-feature framings from clinical reasoning, drawn from `teaching-troubleshooting-diagnostic-reasoning` and `software-engineering-patterns`.
3. **Writing.** The craft and the critique loops (`technical-writing-craft`, `content-and-marketing-writing`, `document-critique`/`ddo`, `kill-the-AI-ism`) that turn a cited analysis into a customer-ready reply and an internal readout.
4. **Applied psychology.** Trust repair (Mayer's ability, benevolence, and integrity model), reactance avoidance, and calibrated reliance on AI output (automation bias and algorithm aversion), so that a human neither rubber-stamps nor reflexively rejects the AI's hypothesis.
5. **Expertise engineering.** The meta-layer that *captures* tacit expert knowledge (`cognitive-task-analysis`), *measures* competence (`assessment-certification-design`, `learning-measurement-evaluation`), and *builds and tunes* the skills, prompts, and code themselves (`skill-creator`/`skill-optimizer`, `prompt-deep-optimizer`, `code-deep-optimizer`, `concept-family-explorer`).

The first four are domains an answer is built from. The fifth is the layer meant to improve the other four over successive cycles.

### 3.2 The four pipeline stages

**Stage 1: Acquire (close the knowledge gaps).** `concept-family-explorer` maps a subject's full conceptual family (parent domain, siblings, sub-concepts, adjacent fields, frontier), surfaces what is *missing*, scores each gap, and loops deep research (`/dr`) on every viable gap until the concept tree saturates. This is how the domain authority reaches breadth before anything is tuned: gaps are found deliberately, not discovered by failing a case in production. [A Closed-Loop System for Autonomous Skill-Knowledge Acquisition](/blog/a-closed-loop-system-for-autonomous-skill-knowledge-acquisition/) describes the loop.

**Stage 2: Optimize (raise every artifact to a quality bar).** Each artifact type has a deep-optimizer, and they are all the *same loop* over a single shared reference, `convergence-and-severity.md`. [Semantic Skill Discovery and the Optimizer Family](/blog/semantic-skill-discovery-and-the-optimizer-family/) compares four of the siblings in detail.

- `prompt-deep-optimizer`: production prompts (a 16-pass audit in 5 parallel bundles)
- `code-deep-optimizer`: source code (16 passes as of June 2026, verified against build, lint, and tests; the current skill runs 18)
- `document-critique` / `ddo` (the document deep-optimizer): prose (passes 0–14)
- `design-deep-optimizer`: visual and UI artifacts (11 passes)
- `skill-optimizer`: the skills themselves

The shared model gives "optimize" a precise meaning: a severity ladder (Blocking → Major → Medium → Minor → Nit; fix everything Medium and above), seven convergence exit conditions (clean, no-progress, content-cycling, stable-rewrite, loop-instability, iteration-cap, budget), and bounded iteration caps (five for prompts; three for skills and documents, raised to five only if Medium+ findings dropped by half in the prior pass). It also defines the **blind re-audit gate**, the safeguard against self-congratulation: before an artifact may be declared "clean," a fresh-context subagent re-audits the final version with no access to the findings history or fix rationale, and a finding counts only if a second read of the flagged text or a deterministic check corroborates it. This reduces the risk of an optimizer grading its own homework, although the auditor is a fresh context, not necessarily a different model.

**Stage 3: Compose (run the optimized components on a live case).** `solve-case` is the runtime orchestrator. Its eight phases (numbered 0–7) take a case from intake through assembling the right expertise, customer identification, troubleshooting and diagnosis, a deep-dive on any unknown, and a fact-based cited analysis, to a customer-psychology-informed reply and a wrap-up bundle (analysis, drafted reply, blockers, tools used, who to talk to, escalation decision, insights). It calls the optimized domain authority for diagnosis and the writing loops for the reply. For high-stakes or trust-damaged cases it also calls the psychology agent to pressure-test the message. The system drafts; a human, the account's TAM, reviews and sends.

**Stage 4: Evaluate and feed back (measure blind, improve deliberately).** `diagnosis-methodology-backtest` runs a blind, parallel, multi-agent evaluation against ground-truth resolutions. It enforces two invariants: a strategy sees only the customer's first report (the blindness Section 1 requires), and the predictor is never its own grader. It runs each strategy in an isolated subagent. `eval-driven-development` supplies the surrounding discipline: error analysis as the engine, the Three Gulfs framing (Specification, Generalization, Comprehension; after Shankar and Husain), and judge calibration against human labels (Cohen's kappa, Krippendorff's alpha). This paper reports no such calibration for the grader used in Section 4. The errors the backtest surfaces are meant to become the gaps Stage 1 closes and the findings Stage 2 fixes on the next cycle.

The feedback loop is meant to make the architecture self-improving: Stage 4's errors drive Stage 1's acquisition and Stage 2's optimization, which improve Stage 3's runtime, which Stage 4 then re-measures. This paper reports a single measurement, so it does not show the loop's effect across cycles.

---

## 4. Evidence: the blind-244-v1 backtest

We ran the backtest on 2026-05-28 against a blind panel of 244 tickets (`blind-244-v1`) exported from one customer account; 42 of them are release-label tickets, not support cases (below, "case" means any of the 244). The predicting strategy saw only the customer's first report, never the resolution, and the design calls for a separate grader; the judge definition names a Claude Opus model, but the run records do not show who graded. Blindness rested on the subagents' file-access boundary; file timestamps could not serve as a second check because an earlier extraction step had inverted them.

Three diagnosis strategies were compared (the source files label them Phase 1 to 3):

1. **Strategy 1, skill knowledge:** `mongodb-expert` plus 11 sibling `mongodb-*` skills (12 in all), as they stood on that date. It predicts a root cause freely from domain expertise and may abstain when unsure; it never did here.
2. **Strategy 2, authored flowcharts:** a bundle of 20 incident-remediation flowcharts that one engineer authored around one account's incident patterns.
3. **Strategy 3, flowchart corpus:** a documented corpus of troubleshooting flowcharts (40 sections in the version used here).

### 4.1 Results

Strategy 1 produced this confusion matrix over the 244 cases:

| Outcome | Count |
| :---- | :---- |
| Correct | 158 |
| Partial | 38 |
| **Wrong** | **0** |
| Unverifiable (resolution has no diagnostic content to grade) | 48 |

Grades are meant to rest on the failure mechanism (the causal noun and its qualifier), not on surface wording; against an auto-close echo, though, the only mechanism available is the customer's own noun phrase (Section 4.3). Each grade quotes a line from the resolution, and a grader torn between two grades takes the lower one. Unverifiable means the resolution can neither confirm nor deny the prediction. From the matrix the headline metrics follow (partial predictions are half-credited):

| Metric | Value | Definition |
| :---- | :---- | :---- |
| Raw accuracy | **72.5%** | Credit over all 244 cases: (158 + ½·38) / 244 |
| Accuracy-on-gradable | **90.3%** | Credit over the 196 gradable cases (excluding 48 unverifiable): (158 + ½·38) / 196 |
| Defensibility | **100%** | 1 − Wrong / gradable = 1 − 0/196: zero **Wrong** predictions across all gradable cases |

For a system whose output a human will act on, "never confidently wrong" counts for more than raw accuracy, but zero Wrong is also the figure most sensitive to the rubric. The strategy's shortfalls were Partial resolutions and cases with no gradable ground truth, not predictions graded Wrong. Section 4.3 explains why this result is partly structural.

Two caveats bound the numbers. First, treated as a binomial proportion (an approximation, since partial predictions are half-credited), the 95% interval on the 90.3% accuracy-on-gradable (n = 196) is roughly 86–94%; it covers case sampling only, not rubric validity or ground-truth quality. Second, no naive baseline (a most-common-root-cause prior, say, or an un-optimized zero-shot call) was run on this panel, so the figures are not a measured lift over any baseline. Read them as a relative comparison between strategies under one rubric and one grader.

### 4.2 The strategy-comparison finding

Skill knowledge outscored both alternatives:

| Strategy | Correct | Partial | Wrong | Unverifiable | Raw accuracy | Accuracy-on-gradable | Defensibility |
| :---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| 1, skill knowledge | 158 | 38 | 0 | 48 | 72.5% | 90.3% | 100% |
| 2, authored flowcharts | 30 | 43 | 123 | 48 | 21.1% | 26.3% | 37% |
| 3, flowchart corpus | 80 | 89 | 27 | 48 | 51.0% | 63.5% | 86% |

Strategy 2 lost mainly on coverage: 88 of its 123 Wrong grades (72%) came from a broad fallback scenario it used when no other scenario matched.

An analytic best-of-three ensemble, which counts a case as correct if any strategy got it right, raised raw accuracy from 72.5% to only 74.0% (158 → 165 Correct), about 1.5 points. That rule is the most favorable way to combine the strategies, so the gain is an upper bound for any rule that picks among the three. We computed it from the case-level grades after the fact; a combined system was not scored on this panel. Skill knowledge alone therefore accounted for nearly all of the accuracy the three strategies reached together. The full confusion matrices and the ensemble arithmetic are in the source file cited in Appendix B.

On this panel and rubric, free-form skill prediction scored highest and the flowchart strategies added at most 1.5 points. That argues against flowchart-first and ensemble-first instincts only where the same holds on your panel. Our separate comparative review recommends running the documented corpus alongside skill knowledge as a parallel audit pass for its citation trail, a design the repository sketches but did not score here.

### 4.3 What the evidence does and does not establish

On this panel, skill knowledge scored highest of the three: 90.3% accuracy-on-gradable, with no gradable prediction graded Wrong. The evidence does not measure the writing or psychology skillsets, which act on reply quality and human trust calibration rather than on the root-cause prediction the panel scores. Those axes need their own instruments (reply-quality review, trust-calibration and customer-satisfaction (CSAT) measurement).

Five limits bound the result:

- **What was measured.** Strategy 1 drew on a set of 12 `mongodb-*` skills as they stood on 2026-05-28, not the compiled 66-part skill. The optimizer telemetry on record starts on 2026-06-11, and the only optimizer runs on record for these skills (two of the twelve, `mongodb-expert` and `mongodb-atlas-expert`) are dated July 2026. This paper therefore does not show that the optimization loop produced the scored knowledge or how much it improved it; that needs a before-and-after run on one panel. It also does not say whether any of these cases informed the skills before the run.
- **Thin ground truth.** Of the 196 gradable cases, 185 (including 151 of the 158 Correct grades) were graded against auto-close echoes of the customer's first message, 8 against resolutions the repository labels substantive (its scorecard counts 12 by including 4 empty ones), and 3 against otherwise empty resolutions. On the 8, Strategy 1 scored 4 Correct, 4 Partial, and 0 Wrong (75.0%), too few cases to read much into. The grades were re-issued under one calibrated rubric so the three strategies compare like for like; it keeps an auto-close resolution gradable when it preserves the domain noun phrase, which rewards a predictor that mirrors the customer's wording. The backtest's own methodology says to report such scores as plausibility, not accuracy.
- **A partly structural zero-Wrong result.** Strategy 1 committed to a prediction on all 244 tickets, so abstention does not explain its zero Wrong. Our separate comparative review attributes it partly to the calibrated rubric, which rewards predictions that mirror the customer's wording against echo resolutions. On the strict grading the seed panel applied to this strategy, it had one Wrong in five gradable cases (80% defensibility), and on the 1,000-case set all three strategies had zero Wrong but 89% to 97% of cases were abstained or unverifiable. Defensibility therefore does not prove the strategy cannot be wrong.
- **A rubric- and panel-specific ranking.** A 20-ticket seed panel (a subset of these 244) was graded with a different threshold per strategy: strict for skill knowledge, lenient for the corpus. There the corpus ranked first (60.5% accuracy-on-gradable against 40.0% for skill knowledge, which rests on 5 gradable cases), but that is largely an effect of the unequal thresholds, and the grades are not comparable with the 244-ticket set. On a second account's 1,000-case set the corpus also ranked first (84.2% on 114 gradable cases against 74.7% on 85). This paper reports no calibration of the grader against human labels, and the run records show neither who graded nor which model made the predictions, so grader independence and same-family grading bias cannot be assessed; the repository itself lists judge self-grading bias as a watch item.
- **One account.** All 244 tickets come from one customer account. Their mix, and how representative it is of the broader MongoDB/Atlas caseload, are not characterized here, so generalization is not established.

---

## 5. Implementation considerations

A team adapting this architecture should weigh six points drawn from how it was built.

**Engineer expertise; do not just prompt it.** In our judgment, the decision that mattered most was treating each skill as an artifact with a severity-gated quality bar and a convergence loop, not as a prompt to hand-tune. The panel did not isolate that effect (Section 4.3), so it is a design judgment, not a measured result. Budget for the optimization layer explicitly; we did not measure its build or maintenance cost.

**Use one convergence model across artifact types.** Prompts, code, prose, and skills share one loop and one severity-and-convergence reference. That keeps "done" meaning the same thing everywhere and keeps the iteration caps and exit conditions auditable; a loop per artifact type reintroduces the inconsistency.

**Make the optimizer prove convergence to a blind auditor.** The blind re-audit gate, a fresh-context reviewer with no access to the fix history, is what separates real convergence from an optimizer flattering its own work. Without it, "no findings remain" is unfalsifiable.

**Measure on a blind panel, keep the predictor out of the grader's seat, and check the ground truth.** These conditions are what make figures like 72.5%/90.3%/100% worth reporting: the predictor saw what the customer saw and nothing more, and the design keeps it out of the grader's seat. Relaxing either condition inflates the number. Thin resolutions still make a blind panel measure plausibility more than accuracy (Section 4.3), so audit the reference answers too.

**Prefer skill knowledge to added decision structure, and test that on your own panel.** On this panel the marginal authored flowchart bought little once skill knowledge was in place, but the ranking reversed on a second account's 1,000-case set. Where the comparison holds for you, spend the next unit of effort closing a knowledge gap (Stage 1) or fixing an optimization finding (Stage 2) rather than authoring another flowchart.

**Separate the accuracy axis from the delivery axis, and instrument both.** Diagnostic accuracy and resolution quality are different things measured by different instruments. The backtest covers the first. Trust-repair, reactance, and calibrated-reliance outcomes need their own measurement before any claim is made about them.

---

## 6. Out of scope and future work

- **A baseline and stronger ground truth:** naive and un-optimized baselines, and a before-and-after run of the optimization loop, on one panel whose resolutions carry substantive engineer narrative.
- **Direct measurement of the psychology and writing contributions** to resolution quality and customer trust, which are not yet instrumented.
- **Live-traffic A/B evaluation** of pipeline-resolved vs. human-only cases. The backtest is offline.
- **Cost and latency optimization** of the runtime composition. The mdb-tam dashboard's reduce-then-cache design addresses it separately; see [Reducing LLM Cost and Latency Without Losing Context](/blog/reducing-llm-cost-and-latency-without-losing-context/).

---

## 7. Conclusion

The strategy comparison matters more than the headline accuracy. On a 244-ticket blind panel from one account, skill knowledge outscored both flowchart strategies, none of its 196 gradable predictions was graded Wrong, and an after-the-fact ensemble added only 1.5 points. Those results rest on thin ground truth and a rubric-specific ranking. Each strategy bundles its own prompt with its knowledge and the panel varied no model size, and the run predates the optimizer runs on record, so it shows neither that a bigger model or a cleverer prompt would have done worse nor that the optimization loop produced the score. It supports something narrower: among three strategies, the free-form skill-knowledge strategy scored highest on this panel.

The pipeline's stages exist as working tools, but this paper shows them neither end to end nor across cycles; what it adds is one blind comparison of the knowledge they target. The transferable thesis is narrow and testable: **integrate complementary skillsets, drive each through one iterative multi-stage optimization loop, and prove the diagnostic result on a blind panel whose ground truth you trust.** The test of that thesis is a before-and-after run of the optimization loop on a panel with stronger ground truth, which this paper does not report.

---

## Appendix A — Skill inventory

The five skillsets and the optimization machinery are summarized below and catalogued in full, with per-skill descriptions and case-resolution roles, in a separate companion document, the *Skill Catalog*.

| Family | Lead skills | Role in resolution |
| :---- | :---- | :---- |
| MongoDB domain authority | `mongodb-expert`, `mongodb-atlas-expert`, `mongodb-operations-expert`, `atlas-diagnostics-expert`, `mongodb-kb`, `mongodb-docset-lookup`; compiled into the 66-part `uber-mongodb-skill` behind `uber-mongodb-diagnostician` | Generates and ranks cited root-cause hypotheses: the diagnostic engine; the backtest measured the skill knowledge behind it, not the agent |
| Troubleshooting and diagnostic reasoning | `atlas-diagnostics-expert`, `software-engineering-patterns`, `teaching-troubleshooting-diagnostic-reasoning` | Chooses the diagnostic surface and gathers evidence |
| Writing | `technical-writing-craft`, `content-and-marketing-writing`, `document-critique`/`ddo`, `kill-the-AI-ism` | Turns cited analysis into a customer reply and internal readout |
| Applied psychology | `applied-psychology` hub, `customer-comms-psychologist` agent | Trust repair, reactance avoidance, calibrated human reliance on AI output |
| Expertise engineering | `cognitive-task-analysis`, `assessment-certification-design`, `skill-creator`/`skill-optimizer`, `concept-family-explorer`, `prompt-deep-optimizer`, `code-deep-optimizer`, `eval-driven-development` | Captures, measures, builds, and tunes the other four families |
| Pipeline machinery | shared `convergence-and-severity` model; the deep-optimizer family; `diagnosis-methodology-backtest`; `solve-case` | Acquire → optimize → compose → evaluate → feed back |

## Appendix B — Methodology and sources

**Backtest design (`diagnosis-methodology-backtest`).** Blind, parallel, multi-agent comparison of competing diagnosis strategies against ground-truth resolutions, under the two invariants described in Stage 4 (a strategy sees only the customer's first report; the predictor is never the grader), with each strategy in an isolated subagent. Outcomes are scored Correct / Partial / Wrong / Unverifiable, with partials half-credited. The judge definition names a Claude Opus model, but the run records do not show who graded.

**Panel.** `blind-244-v1`: 244 tickets exported from one customer account; 196 gradable, 48 unverifiable (42 of them release-label tickets). The headline figures and the approximate 95% interval (binomial normal approximation, n = 196) are in Sections 4.1 and 4.2. Under the calibrated rubric, an auto-close ("closed-fallback") resolution stays gradable when it preserves the domain noun phrase. A 20-case seed panel kept its original per-strategy grades, whose thresholds differed between strategies.

**Source of truth.** A private working repository holds the run records, the cited knowledge sources, and `evaluations/hybrid-scoring-analysis-n244.md` (full confusion matrix and per-strategy comparison). The seed-panel, 1,000-case, and ground-truth-composition figures in Section 4.3 come from that repository's scoreboard and evaluation notes (the 1,000-case figures from a note, not a pinned run) and from our separate comparative review. The read-only `uber-mongodb-diagnostician` agent, backed by the 66-part `uber-mongodb-skill` compiled from the `mongodb-*` skills, is the productized form of Strategy 1, which itself drew on 12 of those skills. None of these files is public, so external readers cannot reproduce the figures from this paper alone, and the panel's tickets cannot be published.

**Optimization machinery.** Shared convergence-and-severity reference: `convergence-and-severity.md` (a private file covering the severity ladder, the seven exit conditions, the iteration caps, and the blind re-audit gate). The optimizer telemetry cited in Section 4.3 is a private log. Deep-optimizer pass counts: `prompt-deep-optimizer` (16 passes / 5 bundles), `code-deep-optimizer` (16 passes as of June 2026), `design-deep-optimizer` (11 passes), `document-critique` (passes 0–14).

**Runtime orchestration.** `solve-case` (eight phases numbered 0–7, intake → wrap-up). Customer-communication safeguard: `customer-comms-psychologist` agent over the `applied-psychology` hub (Mayer's ability, benevolence, and integrity trust model; automation bias, algorithm aversion, and calibrated reliance for human-AI interaction).

---

*This paper documents the system as implemented as of June 2026, except where dated; the backtest ran on 2026-05-28, and the provenance details in Section 4.3 were added in October 2026. Its figures come from the private sources described in Appendix B.*
