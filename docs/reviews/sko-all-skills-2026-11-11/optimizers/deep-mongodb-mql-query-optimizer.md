# deep-mongodb-mql-query-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 5 | 4 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| A | The instruction treats equal $gte/$lt bounds as equality, changing an empty interval into matching documents. | High | Distinguish inclusive equal bounds from an exclusive bound; preserve empty results and add an explicit counterexample. |
| A | The text recommends a strength-2 collation index to accelerate case-insensitive regex; MongoDB documents regex as not collation-aware. | High | Correct the rule and cite current official regex/case-insensitive-index documentation. |
| A | Read-only does not explicitly suppress --report/--annotate writes; sampled counts/sets are treated as full equivalence. | High | Give read-only global precedence; compare multiplicity/order and disclose sampled evidence limits. |
| A | A High-only mode can report convergence while Medium and Blocking findings remain. | Medium | Register its compatibility triage mode locally, report unresolved totals and TRIAGE-PARTIAL, never convergence. |
| J | Four history entries occupy the always-loaded frontmatter. | Medium | Extract history to references/CHANGELOG.md and keep changelog_ref. |
| F | No functional evaluation suite exists. | Medium | Add query-equivalence, regex, read-only and guarded index cases; replay canonical trigger corpus. |
| A | Acceptance dependencies and the local optional cross-model reference are missing. | High | Bundle full dependencies and correct reference paths. |
| P | Query repository audit lacks standard size-first llms/source guidance. | Medium | Add concise standard section. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/SKILL.md
+++ .claude/skills/deep-mongodb-mql-query-optimizer/SKILL.md
@@ -12,9 +12,9 @@
   MCP is connected. Indexes recommend-only. SKIP: theory -> mongodb-expert; live cluster triage
   -> atlas-diagnostics-expert; schema redesign -> mongodb:mongodb-schema-design; ODM fixes ->
   mongodb-odm-patterns; SQL -> deep-query-optimizer; Search relevance -> mongodb-atlas-expert.
-version: 1.4.0
-updated: 2026-10-19
-model: claude-opus-4-8
+version: "1.5.1"
+updated: "2026-11-11"
+model: claude-opus-5-5
```
Diff preview truncated (100 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/evals/evals.json
+++ .claude/skills/deep-mongodb-mql-query-optimizer/evals/evals.json
@@ -0,0 +1,88 @@
+{
+  "skill_name": "deep-mongodb-mql-query-optimizer",
+  "version": "1.0.0",
+  "description": "Behavioral regression cases for the documented workflow and scope boundaries.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "equal-exclusive-range",
+      "prompt": "Optimize db.items.find({x:{$gte:5,$lt:5}}). x is a scalar number; no connection is available.",
```
Diff preview truncated (91 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/deep-mongodb-mql-query-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "optimize this MQL query", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "run dmqo on pipelines/rollup.json", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "why is this aggregation pipeline slow?", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "what index should I create for this query?", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "this find() is doing a COLLSCAN, fix it", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "my $lookup stage is killing performance, rewrite the pipeline", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "getting QueryExceededMemoryLimitNoDiskUseAllowed on my sort", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "make this aggregation use the index", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "tune db.events.find({tenant:'x'}).sort({ts:-1})", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.1", "description_sha256": "8e7ace8d0a1198a40bc50b3630301b0f019bab11af8412df4974887c6748cf2a", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/evals/trigger-eval.json
+++ .claude/skills/deep-mongodb-mql-query-optimizer/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "optimize this MQL query",
+    "should_trigger": true
+  },
+  {
+    "query": "run dmqo on pipelines/rollup.json",
+    "should_trigger": true
+  },
```
Diff preview truncated (85 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/references/CHANGELOG.md
+++ .claude/skills/deep-mongodb-mql-query-optimizer/references/CHANGELOG.md
@@ -0,0 +1,8 @@
+2026-11-11 v1.5.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.4.0->1.5.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
+# Changelog
+
+2026-10-19 v1.3.0->v1.4.0 — folded in the 2026-10-18 MQL full-suite research (8 gated mongodb-expert/atlas-diagnostics-expert spokes, 45 concepts): ERS exception, $in 201-element threshold and SORT_MERGE, rooted-$or blocking-sort risk, same-field $or->$in, $where deprecation, covered-query disqualifiers, partial/sparse eligibility, count/distinct/$sample shapes, batchSize/maxTimeMS semantics, sharded skip/limit and split-pipeline merge, time-series bucket rules (6.3 default index, metaField cardinality, unpack pushdown, 8.0 block processing, last-point DISTINCT_SCAN), 8.0 setQuerySettings vs hint vs index filters, queryShapeHash/planCacheShapeHash, $queryStats, 8.3 cost-based ranker explain fields, spill statistics, slow-log field reading, batch-of-queries edge case; installed top-level (fixes the /dmqo wrapper); description compressed 1430->~1000 chars
+2026-09-14 workload-informed audit v1.2.0->v1.3.0 — grounded in ExampleCorp accounts log analysis (v0.4, 2026-09-11) + 31-case /dmqo case corpus; added: degenerate $gte=$lte ranges, $or per-branch index rule, sparse-field $exists / positive-state-model guidance, $elemMatch attribute-pattern checks, string-typed numeric comparison guard, $group accumulator hygiene ($firstN/$topN, sort-before-group, DISTINCT_SCAN), $search-adjacent stage shape, change-stream & cursor/batchSize economics, shard-targeting promoted to P2/P3 audit check, index-consolidation & plan-cache-stability rules, multi-cardinality verification, $indexStats/hidden-index retirement protocol; deferral row for code-deep-optimizer (closes eng-ref L12); bundle now ships convergence_check.py (closes L11); eval set re-pinned + 6 new rows
+2026-07-20 sko v1.1.0->v1.2.0 — Pass H 10/10 pos, 0/10 neg (predicted); 1 High + 21 Medium fixed across 3 iters; Blocking-apply contradiction, sharding/write-ops/hint/$expr/regex-i coverage, desc rewrite; edge: code-deep-optimizer
+2026-07-17 sko v1.0->v1.1.0 — Pass H 10/10 pos, 9/10->10/10 neg (predicted); 1 High + 15 Medium fixed; edges: collation/clustered/odm/gridfs/time-series/docset-lookup
```
```diff
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/deep-mongodb-mql-query-optimizer/references/shared/convergence-and-severity.md
@@ -132,6 +132,7 @@
 | --- | --- | --- | --- | --- |
 | `code-deep-optimizer` | `--quick` | Critical only | C1, C3, S1 (3 of 18) | Stage 0 activation ceremony, advisory track, empirical mode, blind re-audit gate, verify-gate bisect loop |
 | `ddo` | `--quick` | Blocking only | 3, 6 (Blocking), 10.5 (flagged claims), 11.5, 12 (Blocking) | Full domain/intent routing, structure/tone/voice, full sourcing sweep, convergence loop, blind exit audit. Keep pre-write preservation and conflict checks; shared finalization still runs. |
+| `deep-mongodb-mql-query-optimizer` | `--minimal` | High only; Blocking reported | P0-P9 | Medium fixes; retain result-equivalence and recommend-only index rails; TRIAGE-PARTIAL/TRIAGE-CLEAN with unresolved totals, never convergence |

 ## Guardrails carried by every optimizer

@@ -245,18 +246,13 @@
 every table row's roots) is read and searched with ordinary tools — no fallback note needed, since
```
Diff preview truncated (36 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/references/shared/cross-model-gate.md
+++ .claude/skills/deep-mongodb-mql-query-optimizer/references/shared/cross-model-gate.md
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
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/deep-mongodb-mql-query-optimizer/references/shared/evidence-contract.md
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
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/deep-mongodb-mql-query-optimizer/references/shared/evidence_gate.py
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
--- baseline/.claude/skills/deep-mongodb-mql-query-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/deep-mongodb-mql-query-optimizer/references/shared/test_evidence_gate.py
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
| behavior | 0/9 output assertions graded; 4 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 13 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/deep-mongodb-mql-query-optimizer/SKILL.md | canonical selected source | c53b0b74466d | verified source edits | 00b490a06f79 |
| $HOME/.claude/skills/deep-mongodb-mql-query-optimizer/SKILL.md | copy | 1c30ec9ca3ef | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/deep-mongodb-mql-query-optimizer/SKILL.md | copy | 1c30ec9ca3ef | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/custom/mqloptimizer/deep-mongodb-mql-query-optimizer/SKILL.md | copy | 19b45d8ae745 | skipped (--no-sync); root ownership check | unchanged |

llms-first: added

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| deep-mongodb-mql-query-optimizer | unverified (own-intent ranking not run) | True | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/deep-mongodb-mql-query-optimizer/baseline/SKILL.md" ".claude/skills/deep-mongodb-mql-query-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

5 high, 4 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | The instruction treats equal $gte/$lt bounds as equality, changing an empty interval into matching documents.; The text recommends a strength-2 collation index to accelerate case-insensitive regex; MongoDB documents regex as not collation-aware.; Read-only does not explicitly suppress --report/--annotate writes; sampled counts/sets are treated as full equivalence.; A High-only mode can report convergence while Medium and Blocking findings remain.; Acceptance dependencies and the local optional cross-model reference are missing.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | No functional evaluation suite exists. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Four history entries occupy the always-loaded frontmatter. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 998 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Query repository audit lacks standard size-first llms/source guidance. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| optimize this MQL query | True | True | pass |
| run dmqo on pipelines/rollup.json | True | True | pass |
| why is this aggregation pipeline slow? | True | True | pass |
| what index should I create for this query? | True | True | pass |
| this find() is doing a COLLSCAN, fix it | True | True | pass |
| my $lookup stage is killing performance, rewrite the pipeline | True | True | pass |
| getting QueryExceededMemoryLimitNoDiskUseAllowed on my sort | True | True | pass |
| make this aggregation use the index | True | True | pass |
| tune db.events.find({tenant:'x'}).sort({ts:-1}) | True | True | pass |
| docsExamined is way higher than nReturned on this query | True | True | pass |
| how do indexes work in MongoDB? | False | False | pass |
| optimize this SQL query | False | False | pass |
| my cluster is slow, check FTDC | False | False | pass |
| how should I model orders vs orderItems? | False | False | pass |
| tune my $search relevance scoring | False | False | pass |
| write a query to find users by name | False | False | pass |
| MongoDB query optimization best practices? | False | False | pass |
| why is my Mongoose populate slow? | False | False | pass |
| create a case-insensitive index | False | False | pass |
| performance dropped after upgrade, analyze the logs | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.

The regex correction is grounded in the [MongoDB Manual](https://www.mongodb.com/docs/manual/core/index-case-insensitive/).


Bounded repair round: final source `00b490a06f79afca961307b7be18947f03efc342fbc95206662d36afc81125d1`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
