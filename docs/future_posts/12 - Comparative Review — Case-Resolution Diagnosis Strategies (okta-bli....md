# Comparative Review — Case-Resolution Diagnosis Strategies (okta-blind-244-v1)

A head-to-head review of the four seed diagnosis strategies in this repo, scored blind against real closed Okta Atlas support cases. Every number below traces to a file in the repo (`scoreboard/leaderboard.md`, `evaluations/*-n244.md`, `evaluations/case-level-outcomes-gs-1000.md`). Where a figure is not in the repo it is marked `[not in repo]`.

**Scope note (the "first customer prompt"):** each strategy is run *blind* — its only input is `case.initial_prompt` (the case title + the customer's first message). It never sees the resolution. So this is, literally, a comparison of methodologies that diagnose **from the first customer prompt alone.** Primary panel: `okta-blind-244-v1` (the first/largest customer case set). The Goldman Sachs `n=1000` run is used as a secondary scale-and-generalization check.

---

## 1. TL;DR

On the full 244-case Okta panel under the calibrated rubric, **`mongodb-skill-knowledge-v1` (pure expert-skill knowledge, no flowcharts) wins decisively** — **72.5% raw accuracy, 90.3% accuracy-on-gradable, 100% defensibility (0 Wrong)**. The documented **`flowchart-corpus-v1`** is a clear second (51.0% / 63.5% / 86%), and **`chandler-flowcharts-v1`** (the Okta-specific bundle) is last by a wide margin (21.1% / 26.3% / 37%).

But the ranking flips by panel and by customer, and that is the most important finding. On the strict 20-case seed panel the *corpus* wins and skill knowledge comes third; on the Goldman Sachs `n=1000` set the *corpus* wins again (84.2% acc/gradable) and skill knowledge drops to (74.7% acc/gradable). The cause is not methodology — it is **ground-truth quality**. ~80% of Okta resolutions and 98.9% of GS grade records are thin "autoclose" echoes, so **the scores read as plausibility, not accuracy.** Running all three strategies together (best-of-3) adds only **+7 Correct cases** over skill-knowledge alone. The practical recommendation is therefore *skill-knowledge as the primary predictor, corpus as a parallel audit trail* — and to treat the binding constraint as the `r2` engineer-narrative ground truth, not the choice of strategy.

---

## 2. The evaluation setup

The repo is a git-backed scoreboard: a **strategy** (a prompt + the knowledge it may consult) is run blind against a frozen **sample-set** of cases; a versioned **judge** (`blind-diagnosis-judge-v1`) grades each prediction against the case's separately-stored ground-truth resolution; scores roll into a leaderboard. Two runs are comparable only within the same sample-set + ground-truth version.

- **Corpus:** `okta-blind-244-v1` — all 244 closed/resolved Okta MongoDB Atlas cases, calibrated rubric. Ground-truth version `r1-autoclose-fallback`.  
- **Blind input:** case title + first customer message only.  
- **Ground truth:** the case `final_solution`, stored apart so strategies cannot peek.

Each prediction lands in one of four tiers; three metrics are computed deterministically (`harness/score.py`):

| Metric | Definition | Reads as |
| :---- | :---- | :---- |
| **Raw accuracy** | `Σweight / n` (Correct=1.0, Partial=0.5) | quality across the whole panel — *penalizes abstaining* |
| **Accuracy-on-gradable** | `Σweight / gradable`, gradable = C+P+W | quality on the answers we could actually check |
| **Defensibility** | `1 − Wrong / gradable` | of checkable answers, how often we weren't flat wrong |
| *(Abstention)* | `Unverifiable / n` | how often the strategy declined to commit |

`Unverifiable` predictions are excluded from gradable. An **honesty downgrade** applies when ground truth is an autoclose fallback — central to the caveats in §6.

---

## 3. The strategies compared

| Strategy | Kind | Knowledge source | Mechanism |
| :---- | :---- | :---- | :---- |
| **`mongodb-skill-knowledge-v1`** | skill-knowledge | the `mongodb-*` expert skills only (replication, sharding, query perf, Atlas, networking) | free-form root-cause prediction from domain expertise; **no flowcharts**; abstains when unsure |
| **`flowchart-corpus-v1`** | flowchart-corpus | canonical *documented* MongoDB troubleshooting decision flowcharts | walks a documented trigger → branch → terminal-node trail; most **explainable**; abstains when no flowchart matches |
| **`chandler-flowcharts-v1`** | flowchart-bundle | Chandler Wyatt's **Okta-specific** incident-remediation flowcharts (20 scenarios) | maps the case to an Okta scenario and walks the decision tree; high Okta-pattern coverage, but falls back to a broad "Atlas Platform Incident" node when nothing matches |
| **`hybrid-cascade-v1`** | hybrid (forked from corpus) | all three above | defer-to-explainable cascade: corpus → Chandler → skill, deferring whenever the preferred component is low-confidence; uses prediction-time signals only (no grade peeking) |

Note the hybrid was scored on the **seed 20-panel**, not on `okta-blind-244-v1` (`[hybrid n=244 run not in repo]`), so the head-to-head in §4 is the three base strategies plus an *analytic* ensemble computed post-hoc in `hybrid-scoring-analysis-n244.md`.

---

## 4. Head-to-head results

### Full corpus — `okta-blind-244-v1` (calibrated rubric)

*(C = Correct, P = Partial, W = Wrong, U = Unverifiable)*

| Rank | Strategy | n | C | P | W | U | Defensibility | Acc/Gradable | Raw Acc |
| ----: | :---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| 1 | `mongodb-skill-knowledge-v1` | 244 | 158 | 38 | **0** | 48 | **100%** | **90.3%** | **72.5%** |
| 2 | `flowchart-corpus-v1` | 244 | 80 | 89 | 27 | 48 | 86% | 63.5% | 51.0% |
| 3 | `chandler-flowcharts-v1` | 244 | 30 | 43 | 123 | 48 | 37% | 26.3% | 21.1% |

### Seed panel — `okta-blind-20-v1` (strict closed-fallback rubric) — the ranking *inverts*

| Rank | Strategy | Defensibility | Acc/Gradable | Raw Acc |
| ----: | :---- | ----: | ----: | ----: |
| 1 | `flowchart-corpus-v1` | 84% | 60.5% | 57.5% |
| 2 | `hybrid-cascade-v1` | 80% | 56.7% | 42.5% |
| 3 | `mongodb-skill-knowledge-v1` | 80% | 40.0% | 10.0% |
| 4 | `chandler-flowcharts-v1` | 73% | 36.7% | 27.5% |

The two groups disagree on the leader **by design** — the n=20 strict rubric demotes most skill-knowledge predictions to Unverifiable (it abstains heavily: raw 10.0%), while the n=244 calibrated rubric keeps closed-fallback resolutions gradable when they preserve the domain noun-phrase, which rewards the skill strategy's prompt-mirroring. **The rubric, not the methodology, picks the winner.**

### Ensemble aggregations (analytic, n=244)

| Aggregation | C | W | Raw acc | Acc/Gradable |
| :---- | ----: | ----: | ----: | ----: |
| Phase 1 alone (skill) | 158 | 0 | 72.5% | 90.3% |
| **Best-of-3** (any Correct wins) | **165** | 0 | **74.0%** | **92.1%** |
| Majority vote (P1 tiebreak) | 131 | 19 | 63.1% | 78.6% |
| Worst-of-3 (any Wrong wins) | 16 | 131 | 16.6% | 20.7% |

**The gradable-vs-raw gap** is the story of abstention: all three share the same 48 Unverifiable cases (Bucket A — no diagnostic content to grade), so raw accuracy sits well below acc/gradable for every strategy. **Best-of-3 only adds 7 Correct over skill-alone (158 → 165)** at 3× runtime, and **majority vote is *worse* than skill-alone** because it outvotes the 16 "C/W/W" cases where only skill knowledge stayed in-domain.

---

## 5. Why the winner won — and why the others lagged

**Skill knowledge won because it never went flat Wrong (0/244) and rarely abstained on gradable cases.** Its free-form predictions handle the long tail the flowcharts can't: 71 "loose Phase-1 solo" cases and 16 hard "C/W/W" cases — Atlas Admin / API / SDK / feature-inquiry questions (OpenSSL version, restore deleted project, region-name tags, `databaseVersionRefreshDurationMillis`) that no flowchart taxonomy enumerates. The honest asterisk: the calibrated rubric's 0-Wrong outcome is *partly structural* (methodology rule 5), and the win is amplified by prompt-mirroring against thin resolutions — see §6.

**The documented corpus placed second on accuracy but is the explainability leader.** Every prediction carries a trigger → branch → terminal-node trail, and it tops defensibility on the strict 20-panel (84%). Its 27 Wrong on n=244 come mostly from *over-broadening* a section (e.g., picking §32 Monitoring for a Terraform/`alertConfigs` case that was really §8 Atlas-API). In 4 cases (`P/W/C`) its enumerated branches acted as a checklist and caught a mechanism the skill predictor missed — the genuine additive value of a flowchart pass.

**Chandler's Okta bundle lost because it is too narrow.** 123 of 244 graded Wrong, and **117 of those used the broad "Atlas Platform Incident" fallback** when no scenario keyword matched. `chandler-flowcharts-coverage-gap.md` buckets the misses into 7 missing-flowchart families — Atlas Cluster-State & API (20 cases), non-incident Performance (20), Auth/Federation/IAM (12, zero current coverage), Replication election/rollback (10), Storage-tier inquiry (9), Sharding topology (8), non-incident Backup/Recovery (7). The repo estimates that decomposing the fallback plus filling those gaps (a `chandler-flowcharts-v2`) could lift it to ~55–65% raw accuracy — to roughly corpus parity — before hitting the same ground-truth ceiling everyone hits.

---

## 6. Threats to validity

1. **Ground truth is mostly autoclose echoes — the dominant caveat.** On Okta `r1`, only ~8 of 244 resolutions carry substantive engineer narrative; **188 are autoclose fallbacks** (the "resolution" echoes the customer's first message) and 44 are unavailable. Scores measure *plausibility against thin transcripts*, not verified diagnostic accuracy. 3 of the 8 strong-resolution cases are all-Partial — the hardest cases in the panel.  
2. **The rubric calibration favors the eventual winner.** Keeping closed-fallback resolutions gradable when the domain noun-phrase is preserved rewards skill knowledge's prompt-mirroring. The leader literally changes (corpus ↔ skill) when the rubric changes, so "skill knowledge wins" is rubric-conditional, not absolute.  
3. **0 Wrong is partly an artifact.** Because Phase 1 records 0 Wrong by construction on this rubric, the all-Wrong intersection is empty and the "every case had someone in-domain" claim is partly definitional, not earned.  
4. **Single-customer-domain generalization fails on the scale check.** On Goldman Sachs `n=1000`, the winner **reverses** — `flowchart-corpus-v1` wins (84.2% acc/gradable) and skill knowledge drops to (74.7% acc/gradable); **Chandler's Okta flowcharts are not portable** (97.1% abstain) and should be excluded from the GS comparable group. Only **1.1% (33/3,000) of GS grade records have strong ground truth.** The reversal reflects ground-truth characteristics, not methodology.  
5. **High shared abstention.** The 48-case Bucket A (and 88–97% abstain rates on GS) means a large fraction of every score is "we couldn't check," limiting how much any ranking can claim.

**Net unsolved on Okta n=244: 79/244 (~32%)** — 48 unverifiable by data quality + 31 "practically unsolved" (Partial/Wrong only). All 79 are blocked on `r2` ground truth, not on strategy quality.

---

## 7. Recommendation

1. **Ship `mongodb-skill-knowledge-v1` as the primary predictor for Okta-like accounts** — highest single-strategy accuracy and zero Wrong on the calibrated panel. It captures ~95% of the achievable accuracy on this panel by itself.  
2. **Run `flowchart-corpus-v1` as a parallel audit pass, not a competitor.** Its value is the trigger→branch→terminal citation trail on the 70%+ of cases where skill and corpus converge, plus the rare `P/W/C` catches. This is the `hybrid-cascade-v2` design the repo already sketches: skill first → corpus in parallel → **surface disagreement to a human** rather than auto-pick → cite the corpus section for auditability.  
3. **Do not deploy Chandler's bundle as-is beyond Okta**, and prioritize the `chandler-flowcharts-v2` decomposition (Tier 1: split the "Atlas Platform Incident" fallback; Tier 2: add Auth/Federation, Storage-sizing, Replication-election) only if Okta-specific audit trails are the goal.  
4. **Treat ground truth as the real bottleneck.** The single highest-leverage next step is the **`r2` engineer-narrative resolution ingest** (from live case-MCP comment threads) for both Okta and GS — until then, report all of the above as plausibility, re-run, and revisit the ranking. Mechanism-confirmation in `r2` is expected to shrink skill knowledge's prompt-mirroring edge and likely re-rank the field.

---

### Assumptions

- `[ASSUMED]` "Based on first customer prompt" = the harness's blind input (`case.initial_prompt` = title + first customer message); the review compares strategies diagnosing from that input.  
- `[ASSUMED]` `okta-blind-244-v1` is the "first customer" primary corpus; GS `n=1000` is the secondary generalization check.  
- Hybrid cascade head-to-head uses the seed 20-panel + the analytic ensemble; **a `hybrid-cascade-v1` run against `okta-blind-244-v1` is `[not in repo]`.**

### Sources

`scoreboard/leaderboard.md` · `README.md` · `evaluations/case-level-outcomes-n244.md` · `evaluations/hybrid-scoring-analysis-n244.md` · `evaluations/chandler-flowcharts-coverage-gap.md` · `evaluations/case-level-outcomes-gs-1000.md` · `strategies/README.md` · grading defs from `harness/score.py` (per README §"How scoring works").