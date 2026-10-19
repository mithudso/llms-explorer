---
title: "Comparative Review — Case-Resolution Diagnosis Strategies"
description: "Case-diagnosis strategies scored blind on real Atlas support cases: skill knowledge leads on 244 cases, but the ranking flips with the rubric and the quality of the ground truth."
date: "2026-10-16"
order: 12
---

A head-to-head review of the four seed diagnosis strategies in the scoreboard repo, scored blind against real Atlas support cases from two enterprise customers. Customer A is 244 closed/resolved cases; Customer B is a second customer's 1,000 most recent cases. Every number below traces to a file in the repo (`scoreboard/leaderboard.md`, `evaluations/*-n244.md`, and the case-level outcomes file for the Customer B run). The repo is not public, so the paths are for reference only. Results are as of the leaderboard generated on 2026-05-29. Where a figure is not in the repo, I say so. Customer names are withheld, and strategy, panel and file names that embedded one are renamed.

**Scope note:** each strategy runs *blind*. Its only input is `case.initial_prompt`, the case title plus the customer's first message, and it never sees the resolution. So this compares methodologies that diagnose from the customer's first message alone. I treat `blind-244-v1` (Customer A, the first case set evaluated) as the primary panel and the Customer B `n=1000` run as a secondary check on scale and generalization.

---

## 1. TL;DR

On the full 244-case Customer A panel under the calibrated rubric, **`mongodb-skill-knowledge-v1`** (pure expert-skill knowledge, no flowcharts) ranks first: **72.5% raw accuracy, 90.3% accuracy-on-gradable, 100% defensibility (0 Wrong)**. The documented **`flowchart-corpus-v1`** is a clear second (51.0% / 63.5% / 86% on the same three measures). **`account-flowcharts-v1`**, the bundle built for Customer A's own incident patterns, is last by a wide margin (21.1% / 26.3% / 37%).

But the ranking flips by panel and by customer, and that is the most important finding. On the 20-case seed panel the *corpus* wins and skill knowledge comes third. On the Customer B `n=1000` set the *corpus* wins again (84.2% acc/gradable) and skill knowledge scores 74.7%, though on a small gradable cohort (§6). The 20-case flip traces to the grading thresholds and the Customer B flip to ground-truth quality, not to the methods themselves.

Ground truth is thin throughout: 188 of 244 Customer A resolutions (77%) are "autoclose" echoes of the customer's first message, and 98.9% of Customer B grade records lack strong ground truth. **The scores read as plausibility, not accuracy.** Running all three strategies together (best-of-3) adds only +7 Correct cases over skill knowledge alone.

My recommendation is skill knowledge as the primary predictor with the corpus as a parallel audit trail, and to treat the planned `r2` ground truth (a second resolution version built from engineers' comment threads), not the choice of strategy, as the binding constraint.

---

## 2. The evaluation setup

The repo is a git-backed scoreboard. A **strategy** (a prompt plus the knowledge it may consult) runs blind against a frozen **sample set** of cases. A versioned **judge** (`blind-diagnosis-judge-v1`) grades each prediction against the case's separately stored ground-truth resolution, and scores roll up into a leaderboard ranked by accuracy-on-gradable. Two runs are comparable only within the same sample set and ground-truth version.

- **Primary panel:** `blind-244-v1` holds all 244 closed/resolved Customer A MongoDB Atlas cases, graded with the calibrated rubric. Ground-truth version: `r1-autoclose-fallback`.
- **Ground truth:** the case `final_solution`, stored apart so strategies cannot peek.

Each prediction lands in one of four tiers (Correct, Partial, Wrong, Unverifiable). The harness computes three metrics deterministically (`harness/score.py`), plus an abstention rate:

| Metric | Definition | Reads as |
| :---- | :---- | :---- |
| **Raw accuracy** | `Σweight / n` (Correct=1.0, Partial=0.5) | quality across the whole panel; *penalizes abstaining* |
| **Accuracy-on-gradable** ("acc/gradable") | `Σweight / gradable`, gradable = C+P+W | quality on the answers we could actually check |
| **Defensibility** | `1 − Wrong / gradable` | of checkable answers, how often we weren't flat wrong |
| *(Abstention)* | `Unverifiable / n` | how often the strategy or the ground truth could not commit |

`Unverifiable` predictions are excluded from gradable. An **honesty downgrade** applies when ground truth is an autoclose fallback, which is central to the caveats in §6.

---

## 3. The strategies compared

| Strategy | Kind | Knowledge source | Mechanism |
| :---- | :---- | :---- | :---- |
| **`mongodb-skill-knowledge-v1`** ("skill knowledge") | skill-knowledge | the `mongodb-*` expert skills only (replication, sharding, query perf, Atlas, networking) | free-form root-cause prediction from domain expertise; no flowcharts; abstains when unsure |
| **`flowchart-corpus-v1`** ("the corpus") | flowchart-corpus | canonical *documented* MongoDB troubleshooting decision flowcharts | walks a documented trigger → branch → terminal-node trail; most explainable; abstains when no flowchart matches |
| **`account-flowcharts-v1`** ("the account bundle") | flowchart-bundle | a colleague's Customer A-specific incident-remediation flowcharts (20 scenarios) | maps the case to a Customer A scenario and walks the decision tree; high Customer A-pattern coverage, but falls back to a broad "Atlas Platform Incident" node when nothing matches |
| **`hybrid-cascade-v1`** | hybrid (forked from corpus) | all three above | defer-to-explainable cascade: corpus → account bundle → skill knowledge, deferring whenever the preferred component is low-confidence; uses prediction-time signals only (no grade peeking) |

The hybrid was scored on the seed 20-panel, not on `blind-244-v1` (no hybrid n=244 run is in the repo). So §4 compares the three base strategies and adds an *analytic* ensemble computed after the fact in `hybrid-scoring-analysis-n244.md`.

---

## 4. Head-to-head results

Case triples such as C/W/W list the grades for skill knowledge / account bundle / corpus, in that order.

### Full panel — `blind-244-v1` (calibrated rubric)

*(C = Correct, P = Partial, W = Wrong, U = Unverifiable)*

| Rank | Strategy | n | C | P | W | U | Defensibility | Acc/Gradable | Raw Acc |
| ----: | :---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| 1 | `mongodb-skill-knowledge-v1` | 244 | 158 | 38 | **0** | 48 | **100%** | **90.3%** | **72.5%** |
| 2 | `flowchart-corpus-v1` | 244 | 80 | 89 | 27 | 48 | 86% | 63.5% | 51.0% |
| 3 | `account-flowcharts-v1` | 244 | 30 | 43 | 123 | 48 | 37% | 26.3% | 21.1% |

### Seed panel — `blind-20-v1` (curated 20-case panel, original grades): the leader flips

| Rank | Strategy | Defensibility | Acc/Gradable | Raw Acc |
| ----: | :---- | ----: | ----: | ----: |
| 1 | `flowchart-corpus-v1` | 84% | 60.5% | 57.5% |
| 2 | `hybrid-cascade-v1` | 80% | 56.7% | 42.5% |
| 3 | `mongodb-skill-knowledge-v1` | 80% | 40.0% | 10.0% |
| 4 | `account-flowcharts-v1` | 73% | 36.7% | 27.5% |

The two groups are separate comparable scopes and disagree on the leader because they were graded differently. The 20-case panel kept its original per-phase grades, strict on closed-fallback resolutions for skill knowledge and lenient for the corpus, so most skill-knowledge predictions became Unverifiable (15 of 20, hence the raw 10.0%). The n=244 group was re-graded under one calibrated threshold that keeps closed-fallback resolutions gradable when they preserve the domain noun phrase, which rewards the skill strategy's prompt-mirroring: a prediction that restates the customer's wording matches a resolution that only echoes it. **The grading thresholds, more than the methods, pick the winner.**

### Ensemble aggregations (analytic, n=244)

| Aggregation | C | W | Raw acc | Acc/Gradable |
| :---- | ----: | ----: | ----: | ----: |
| Skill knowledge alone | 158 | 0 | 72.5% | 90.3% |
| **Best-of-3** (any Correct wins) | **165** | 0 | **74.0%** | **92.1%** |
| Majority vote (skill breaks ties) | 131 | 19 | 63.1% | 78.6% |
| Worst-of-3 (any Wrong wins) | 16 | 131 | 16.6% | 20.7% |

All three strategies share the same 48 Unverifiable cases (Bucket A: no diagnostic content to grade), which is why raw accuracy sits well below acc/gradable for every strategy. Best-of-3 adds only 7 Correct over skill knowledge alone (158 → 165), for the cost of running all three strategies (3× the runtime by the repo's count, about 1.5× by the leaderboard's recorded compute times). Majority vote is *worse* than skill knowledge alone, because it outvotes the 16 C/W/W cases where only skill knowledge stayed in-domain and downgrades 11 C/P/P cases to Partial.

---

## 5. Why the winner won, and why the others lagged

**Skill knowledge ranked first on this panel** because it never went flat Wrong (0/244), and its only Unverifiable cases are the 48 that every strategy shares. Its free-form predictions handle the long tail the flowcharts can't: 71 "loose skill-solo" cases (skill knowledge Correct, neither flowchart method Correct), including 16 hard C/W/W cases. Those 16 are mostly Atlas Admin, API, SDK and feature-inquiry questions (OpenSSL version, restore deleted project, region-name tags, `databaseVersionRefreshDurationMillis`) that no flowchart taxonomy enumerates. One caveat: the 0-Wrong result depends on the calibrated rubric (rule 5 in the repo's methodology notes), and the win is amplified by prompt-mirroring against thin resolutions (§6).

**The documented corpus placed second on accuracy and leads on explainability.** Every prediction carries a trigger → branch → terminal-node trail, and it tops defensibility on the 20-panel (84%). Its 27 Wrong on n=244 split three ways:

- 16 are the C/W/W cases above, which the repo says no flowchart taxonomy has scenarios for.
- 8 are wrong-section picks where skill knowledge was Correct. The repo's example is §32 Monitoring chosen for a Terraform/`alertConfigs` case that was really §8 Atlas API (section numbers refer to the documented corpus).
- 3 are cases where skill knowledge was only Partial and both flowchart methods were Wrong (P/W/W).

In 4 cases (P/W/C) the corpus's enumerated branches acted as a checklist and caught a mechanism the skill predictor missed. That is the additive value of a flowchart pass.

**The account bundle lost because it is too narrow.** 123 of 244 graded Wrong, and 88 of those used the broad "Atlas Platform Incident" fallback when no scenario keyword matched, per the repo's per-flowchart usage table (its coverage-gap note says 117, which that table does not support). The repo's coverage-gap analysis (`account-flowcharts-coverage-gap.md`) buckets the misses into 7 missing-flowchart families (86 of the 123 cases, plus a 17-case long tail; about 20 are not itemised): Atlas Cluster-State & API (20 cases), non-incident Performance (20), Auth/Federation/IAM (12, zero current coverage), Replication election/rollback (10), Storage-tier inquiry (9), Sharding topology (8), and non-incident Backup/Recovery (7). It estimates that decomposing the fallback and filling those gaps (a proposed `account-flowcharts-v2`, not yet built or run) could lift the bundle to a projected ~55–65% raw accuracy (a rough estimate for a strategy that does not exist yet; the corpus scored 51.0%), before it hits the same ground-truth ceiling everyone hits.

---

## 6. Threats to validity

1. **Ground truth is mostly autoclose echoes, the dominant caveat.** On Customer A `r1`, only ~8 of 244 resolutions carry substantive engineer narrative. 188 are autoclose fallbacks (the "resolution" echoes the customer's first message), 44 are unavailable and 4 are empty. Scores measure *plausibility against thin transcripts*, not verified diagnostic accuracy. On 3 of the 8 strong-resolution cases no strategy reached Correct, which makes them the hardest in the panel.
2. **The rubric calibration favors the eventual winner.** Keeping closed-fallback resolutions gradable when the domain noun phrase is preserved rewards skill knowledge's prompt-mirroring. The leader changes (corpus ↔ skill) when the grading threshold changes, so "skill knowledge wins" is rubric-conditional, not absolute.
3. **0 Wrong is partly an artifact.** Skill knowledge scored 0 Wrong on the calibrated rubric, so no case can be Wrong for all three strategies. The repo's observation that every gradable case had at least one strategy in-domain is therefore partly definitional, not earned.
4. **Generalization across customers fails on the scale check.** On Customer B `n=1000`, the winner reverses: `flowchart-corpus-v1` wins (84.2% acc/gradable) and skill knowledge scores 74.7%. Those figures rest on small scored cohorts (114 corpus, 85 skill knowledge and 29 account bundle, out of 1,000 cases; only 203 were gradable by any strategy), so the repo's own write-up calls the gap suggestive, not conclusive. The account bundle's 82.8% on its 29 cases also tops skill knowledge, but the bundle is not portable (97.1% abstain) and should be excluded from the Customer B comparable group. Only 1.1% (33 of 3,000) of Customer B grade records have strong ground truth; there, ground truth is each case's transcript text, not a curated `final_solution`. The repo's analysis attributes the reversal to ground-truth characteristics, not methodology, and the run is not yet on the leaderboard, which needs a pinned resolution version for its sample set.
5. **High shared abstention.** The 48-case Bucket A (and 88–97% abstain rates on Customer B) means a large fraction of every score is "we couldn't check," which limits what any ranking can claim.

**Net unsolved on Customer A n=244: 79/244 (~32%).** That is 48 Unverifiable because of data quality plus 31 "practically unsolved" (Partial or Wrong only). At least 76 of the 79 are blocked on `r2` ground truth rather than strategy quality; the other 3 are strong-resolution cases where no strategy reached Correct.

---

## 7. Recommendation

1. **Ship `mongodb-skill-knowledge-v1` as the primary predictor for accounts like Customer A.** It has the highest single-strategy accuracy and zero Wrong on the calibrated panel (both rubric-conditional, per §6), and on its own it reaches 158 of the 165 Correct grades that best-of-3 achieves (~95%).
2. **Run `flowchart-corpus-v1` as a parallel audit pass, not a competitor.** Its value is the trigger → branch → terminal citation trail on the roughly 70% of cases where skill knowledge and the corpus converge, plus the rare P/W/C catches. This is the `hybrid-cascade-v2` design the repo sketches (not yet built): skill knowledge first, corpus in parallel, surface disagreement to a human rather than auto-picking, and cite the corpus section for auditability.
3. **Do not deploy the account bundle as-is.** It ranked last even on Customer A (37% defensibility) and does not transfer to other accounts. Prioritize the `account-flowcharts-v2` decomposition (Tier 1: split the "Atlas Platform Incident" fallback; Tier 2: add Auth/Federation, Storage-sizing, Replication-election) only if Customer A-specific audit trails are the goal.
4. **Treat ground truth as the real bottleneck.** The highest-leverage next step is the `r2` engineer-narrative resolution ingest (not yet produced), built from engineers' comment threads on the live cases, for both Customer A and Customer B. Until then, report all of the above as plausibility. Once `r2` exists, re-run and revisit the ranking. I expect mechanism confirmation in `r2` to shrink skill knowledge's prompt-mirroring edge and likely re-rank the field.

---

### Sources

`scoreboard/leaderboard.md` · `README.md` · `evaluations/case-level-outcomes-n244.md` · `evaluations/hybrid-scoring-analysis-n244.md` · `evaluations/account-flowcharts-coverage-gap.md` · the case-level outcomes file for the Customer B run · `strategies/README.md` · `docs/methodology.md` · grading definitions from `harness/score.py` (per README §"How scoring works").
