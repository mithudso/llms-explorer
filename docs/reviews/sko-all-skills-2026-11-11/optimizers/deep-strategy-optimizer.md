# deep-strategy-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 4 | 0 | 1 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 1 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| A | --promote can run with verification disabled or read-only despite a full-suite must-pass veto. | High | Read-only suppresses promotion and persistence; --no-verify disables promotion and retains an unverified report. |
| A | Five holdout blocks with eight total blocks violate the cited contract minimum 30 holdout and 30 working cases. | High | Keep small-block audits exploratory; require minimum independent split sizes for actual promotion, with no substitution of correlated bars for cases. |
| A | Required acceptance contract/helper files are absent. | High | Bundle full authoritative dependencies. |
| K | Financial leverage and robust statistical estimators are domain terms, not AI filler. | Low | Preserve technical finance terminology; replace the one generic robust claim with stable. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/deep-strategy-optimizer/SKILL.md
+++ .claude/skills/deep-strategy-optimizer/SKILL.md
@@ -1,17 +1,7 @@
 ---
 name: deep-strategy-optimizer
 description: >-
-  Audit-and-fix convergence optimizer for trading strategies, indicators, strategy cards and their
-  backtests, one pass per evaluation method (273 passes, 9 families: data integrity,
-  out-of-sample, multiple testing, risk metrics, robustness, costs and execution, regimes,
-  indicator quality, reproducibility). Classifies strategy vs indicator, skips inapplicable
-  passes, applies Medium+ fixes, verifies with the project's tests, loops to convergence. Opt-in
-  `--promote` runs a gated champion-challenger climb; "no promotion" is normal. TRIGGER: "run
```
Diff preview truncated (62 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/deep-strategy-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Run dso on this strategy and its backtest.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Audit the reported Sharpe ratio for lookahead and omitted costs.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Evaluate this indicator against its labelled outcomes.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Check whether the strategy card matches its simulation code.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "This strategy dies out of sample; audit the evidence.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Is this trading signal real or just multiple-testing noise?", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Verify the backtest equity and quoted performance figures.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review the cost and fill assumptions behind this momentum strategy.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Optimize this strategy with the gated promotion track only if the data supports it.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.1.1", "description_sha256": "5118f781375c50cac085f6d8842a08ff57c82d153d8683a8205a73ad4ac4ae0b", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/evals/trigger-eval.json
+++ .claude/skills/deep-strategy-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
   {
-    "query": "run dso on the rsi strategy",
+    "query": "Run dso on this strategy and its backtest.",
     "should_trigger": true
   },
   {
-    "query": "audit this backtest for lookahead and cost bugs",
+    "query": "Audit the reported Sharpe ratio for lookahead and omitted costs.",
```
Diff preview truncated (105 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/CHANGELOG.md
+++ .claude/skills/deep-strategy-optimizer/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+2026-11-11 v2.1.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 2.0.0->2.1.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
+# Changelog
```
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/evaluation-methods.md
+++ .claude/skills/deep-strategy-optimizer/references/evaluation-methods.md
@@ -81,7 +81,7 @@

 | Method | What it tests | Applies to | Inputs and minimum sample | Failure it catches | Source | Pass ID |
 | --- | --- | --- | --- | --- | --- | --- |
-| Protocol grade | Names and grades the protocol behind the headline (single split < walk-forward < CPCV) | both | protocol label and parameters | a single-split number sold as robust | LDP18 Pitfall 9; ARIAN; `backtester/strategy_cards/README.md:105-110` | OV-01 |
+| Protocol grade | Names and grades the protocol behind the headline (single split < walk-forward < CPCV) | both | protocol label and parameters | a single-split number sold as stable | LDP18 Pitfall 9; ARIAN; `backtester/strategy_cards/README.md:105-110` | OV-01 |
 | Single chronological split (holdout) | A rule found in-sample holds on later bars | both | ordered bars, frozen rules; holdout not under 1,000 observations (PBO, citing Weiss & Kulikowski); repo rank floor 10 OOS trades | time-period overfit; a holdout too short to conclude | PBO §1; `research/sweep.py:80-89,300-325` | OV-02 |
 | Split-position regime audit | Regime content of the test slice vs the train slice | both | close series, split index | a split landing on the price top (repo SOL precedent) | `backtester/strategy_cards/README.md:107-110`; `backtester/core/cpcv.py:7-9` | OV-03 |
 | IS-rank vs OOS-rank correlation | In-sample ranking predicts out-of-sample ranking | strategy | IS and OOS metric per configuration | anti-informative leaderboards (repo Spearman −0.419) | `research/RANKED_LISTS.md:43` | OV-04 |
```
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/passes.md
+++ .claude/skills/deep-strategy-optimizer/references/passes.md
@@ -106,4 +106,3 @@

 **Skip protocol:** any pass may report `N/A (reason)` or `partial`, never silently dropped. The
 Summary line names the active pass count (e.g. `17 of 19 passes active`).
-
```
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/deep-strategy-optimizer/references/shared/convergence-and-severity.md
@@ -245,18 +245,13 @@
 every table row's roots) is read and searched with ordinary tools — no fallback note needed, since
 no index claim was ever made for it.

-**Keep the index warm.** Any write this run makes to a file under `gen-prose-index.mjs`'s corpus
-roots (`~/.claude/skills`, `~/.claude/skill-consolidation`, and the mdb-context-hub `docs/` and
-repo-root markdown) leaves `tam_search_prose` stale for that file until re-embedded. After Step
-7/Step 5's writes land (and after Pass O's peer writes, if any), run `node
-scripts/gen-prose-index.mjs --embed` from the mdb-context-hub repo root — the embed is incremental
-and keyed by `srcHash(model+chunk)`, so re-running it after a small edit only re-embeds the changed
```
Diff preview truncated (28 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/shared/cross-model-gate.md
+++ .claude/skills/deep-strategy-optimizer/references/shared/cross-model-gate.md
@@ -22,14 +22,7 @@
 1. **Availability check** — `copilot --version`. On failure, log
    `cross-model gate: skipped (copilot CLI unavailable)` in the report and continue to the normal
    exit. The gate must never block a run.
-2. **Model detection** — reuse copilot-adversarial-review's Step 0 latest-GPT snippet, or skip
-   detection entirely and use the hardcoded fallback to save one CLI round-trip:
-
-   ```bash
-   LATEST_GPT=$(copilot -p "What is the single most capable base GPT model ID available to you right now? Reply with only the model ID, nothing else." --silent \
-     | grep -oE 'gpt-[0-9]+\.[0-9]+' | head -1)
```
Diff preview truncated (18 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/deep-strategy-optimizer/references/shared/evidence-contract.md
@@ -0,0 +1,112 @@
+# Shared optimizer acceptance evidence
+
+Version: 1.0.0
+Delta: initial executable verification contract.
+
+## Purpose and limits
+
+Use this contract for every optimizer that cites convergence-and-severity.md.
+A verified acceptance claim needs current artifact bindings, completed successful
```
Diff preview truncated (115 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/deep-strategy-optimizer/references/shared/evidence_gate.py
@@ -0,0 +1,152 @@
+#!/usr/bin/env python3
+"""Validate declared optimizer acceptance evidence offline; never manufacture observations."""
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+from pathlib import Path
+
```
Diff preview truncated (155 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-strategy-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/deep-strategy-optimizer/references/shared/test_evidence_gate.py
@@ -0,0 +1,160 @@
+"""Shared acceptance compliance regressions; fixture receipts are not UI observations."""
+import copy
+import json
+from pathlib import Path
+import subprocess
+import sys
+import tempfile
+import unittest
+
```
Diff preview truncated (163 lines; complete file and baseline hashes are in JSON).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger (Pass H) | pos 10/10, false-positive 0/10 | predicted | yes |
| behavior | 0/14 output assertions graded; 4 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 7 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/deep-strategy-optimizer/SKILL.md | canonical selected source | b50b1de2510e | verified source edits | a9346af0f436 |
| $HOME/.claude/skills/deep-strategy-optimizer/SKILL.md | copy | 924e6afbb7f2 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/deep-strategy-optimizer/SKILL.md | copy | 924e6afbb7f2 | skipped (--no-sync); root ownership check | unchanged |

llms-first: present

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| deep-strategy-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/deep-strategy-optimizer/baseline/SKILL.md" ".claude/skills/deep-strategy-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

4 high, 0 medium, 1 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | --promote can run with verification disabled or read-only despite a full-suite must-pass veto.; Five holdout blocks with eight total blocks violate the cited contract minimum 30 holdout and 30 working cases.; Required acceptance contract/helper files are absent.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Behavior suite retained or repaired; realistic input/error/boundary cases exist; assertion grading is pending a fresh reviewer. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 823/1000 characters; body 6221 estimated tokens. Soft overage justified by operative multi-pass/safety/convergence content; below hard ceiling. |
| K Prose terms | Financial leverage and robust statistical estimators are domain terms, not AI filler. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 823 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | present |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| Run dso on this strategy and its backtest. | True | True | pass |
| Audit the reported Sharpe ratio for lookahead and omitted costs. | True | True | pass |
| Evaluate this indicator against its labelled outcomes. | True | True | pass |
| Check whether the strategy card matches its simulation code. | True | True | pass |
| This strategy dies out of sample; audit the evidence. | True | True | pass |
| Is this trading signal real or just multiple-testing noise? | True | True | pass |
| Verify the backtest equity and quoted performance figures. | True | True | pass |
| Review the cost and fill assumptions behind this momentum strategy. | True | True | pass |
| Optimize this strategy with the gated promotion track only if the data supports it. | True | True | pass |
| Check a directional indicator hit rate against the observed base rate. | True | True | pass |
| Explain what MACD means with no strategy artifact. | False | False | pass |
| Refactor variable names in the trading app without evaluating its strategy. | False | False | pass |
| Fix the live exchange order-routing service. | False | False | pass |
| Polish the prose in this investment memo without auditing its numbers. | False | False | pass |
| Optimize a SQL query that stores trade events. | False | False | pass |
| Harden the system prompt in a financial assistant. | False | False | pass |
| Rebalance the skill tree for trading-related skills. | False | False | pass |
| Help me buy stock through my broker account. | False | False | pass |
| Create a new backtest from scratch; no strategy or outcomes exist. | False | False | pass |
| Format this Python indicator file with black only. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `a9346af0f436752e287cddbf00bb33d345f1245aa34d1ed07872670c60573f71`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
