# deep-query-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 4 | 5 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | All three cases expect nonexistent references/overview.md instead of testing SQL semantics. | Medium | Replace invalid generated cases with SQL equivalence, read-only and MongoDB routing cases. |
| A | --read-only writes nothing conflicts with --annotate, --report and empirical champion persistence. | High | Make read-only precedence explicit for all write surfaces and run one diagnostic iteration. |
| A | SELECT-only classification permits data-modifying CTEs, side-effect functions and locking reads. | High | Require proven read-only statements and reject unsafe/unknown execution; use bounded disposable data with timeouts. |
| A | --minimal leaves Medium findings but the contract still promises convergence with zero Medium+. | Medium | Keep compatibility as explicitly partial severity filtering; never report clean and report unresolved totals. |
| A | A bounded sample/checksum is treated as result equivalence without multiset/order caveats. | Medium | Require semantic proof plus multiset/order comparison; label sampling as limited, never full equivalence. |
| G | No concrete whenToUse, category, related_skills or model/effort metadata. | Medium | Add specific SQL phrases and current advisory model/effort. |
| P | Repository SQL review lacks the size-first llms/source authority section. | Medium | Add concise standard guidance. |
| A | Required acceptance contract and helper are absent from the self-contained shared-reference directory. | High | Include complete authoritative contract/helper locally; no stub. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/deep-query-optimizer/SKILL.md
+++ .claude/skills/deep-query-optimizer/SKILL.md
@@ -1,8 +1,22 @@
 ---
 name: deep-query-optimizer
-description: "SQL member of the deep-optimizer family: a multi-pass review-and-fix optimizer for a SQL query or file. Detects the dialect (Postgres/MySQL/SQLite/SQL Server), audits sargability, indexes, joins and N+1, predicates, pagination, subqueries/CTEs and the EXPLAIN plan; severity-rates findings; applies every Medium+ rewrite; and given a DB connection, verifies via EXPLAIN/EXPLAIN ANALYZE that the plan improved and the result set is unchanged, backing out regressions and looping to convergence. Recommends index DDL. TRIGGER: \"optimize this SQL\", \"run dqo\", \"tune this query\", \"why is this query slow\", \"what index for this query\", full-scan/N+1/deep-paging SQL. SKIP: evals -> deep-eval-optimizer; MongoDB/MQL \u2192 deep-mongodb-mql-query-optimizer (/dmqo); warehouse/dbt or SQL schema modeling \u2192 da-data-engineering-platform; ORM or app-layer N+1 in code \u2192 code-deep-optimizer; one-shot advice with no query \u2192 software-engineering-patterns; prose \u2192 ddo; prompts \u2192 prompt-deep-optimizer."
-version: 1.1.1
-updated: '2026-11-07'
+description: >-
+  Review and tune a concrete SQL query or file while preserving its results. TRIGGER: "optimize this SQL", "run dqo", "tune this query", "why is this SQL slow", "what index serves this query". Covers Postgres/MySQL/SQLite/SQL Server, sargability, indexes, joins/N+1, predicates, pagination, CTEs and EXPLAIN. Apply Medium+ only in permitted write mode; verify plans and result semantics when a safe connection exists, back out regressions, recommend index DDL. SKIP: evals → deep-eval-optimizer; MongoDB/MQL → deep-mongodb-mql-query-optimizer; warehouse/dbt/schema modeling → da-data-engineering-platform; ORM/app N+1 → code-deep-optimizer; advice without a query → software-engineering-patterns; prose → ddo; prompts → prompt-deep-optimizer.
+version: "1.2.1"
+updated: "2026-11-11"
```
Diff preview truncated (83 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-query-optimizer/evals/evals.json
+++ .claude/skills/deep-query-optimizer/evals/evals.json
@@ -1,92 +1,85 @@
 {
-  "": "https://json-schema.org/draft/2020-12/schema",
   "skill_name": "deep-query-optimizer",
   "version": "1.0.0",
-  "description": "Functional evaluation suite for deep-query-optimizer hub verifying spoke routing, architecture guidance, and domain invariants.",
+  "description": "Behavioral regression cases for the documented workflow and scope boundaries.",
   "evals": [
     {
       "id": 1,
```
Diff preview truncated (141 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-query-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/deep-query-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Optimize this PostgreSQL SELECT without changing its results.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Run dqo on queries/report.sql.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Why does this SQL query do a full table scan?", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Suggest an index for this exact MySQL join query.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Tune the OFFSET pagination in this SQL file.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Read this EXPLAIN plan and fix the SQL bottleneck.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "This correlated subquery is slow; rewrite it with equivalent SQL semantics.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Audit SQL NULL behavior before replacing NOT IN.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review my SQLite query in read-only mode.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.2.1", "description_sha256": "ef7119a65534a6be752b501ab5317cad3264109974cef150fd0c2bcb503a20e7", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-query-optimizer/evals/trigger-eval.json
+++ .claude/skills/deep-query-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
   {
-    "query": "how do I use overview for our application architecture",
+    "query": "Optimize this PostgreSQL SELECT without changing its results.",
     "should_trigger": true
   },
   {
-    "query": "best practices and patterns for overview",
+    "query": "Run dqo on queries/report.sql.",
```
Diff preview truncated (105 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-query-optimizer/references/CHANGELOG.md
+++ .claude/skills/deep-query-optimizer/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+2026-11-11 v1.2.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.1.1->1.2.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
+# Changelog
```
```diff
--- baseline/.claude/skills/deep-query-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/deep-query-optimizer/references/shared/convergence-and-severity.md
@@ -132,6 +132,7 @@
 | --- | --- | --- | --- | --- |
 | `code-deep-optimizer` | `--quick` | Critical only | C1, C3, S1 (3 of 18) | Stage 0 activation ceremony, advisory track, empirical mode, blind re-audit gate, verify-gate bisect loop |
 | `ddo` | `--quick` | Blocking only | 3, 6 (Blocking), 10.5 (flagged claims), 11.5, 12 (Blocking) | Full domain/intent routing, structure/tone/voice, full sourcing sweep, convergence loop, blind exit audit. Keep pre-write preservation and conflict checks; shared finalization still runs. |
+| `deep-query-optimizer` | `--minimal` | Blocking/High only | P0-P11 | Medium fixes; retain equivalence and read-only execution gates; report TRIAGE-PARTIAL/TRIAGE-CLEAN and unresolved totals, never convergence |

 ## Guardrails carried by every optimizer

@@ -245,18 +246,13 @@
 every table row's roots) is read and searched with ordinary tools — no fallback note needed, since
```
Diff preview truncated (36 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-query-optimizer/references/shared/cross-model-gate.md
+++ .claude/skills/deep-query-optimizer/references/shared/cross-model-gate.md
@@ -0,0 +1,56 @@
+# Cross-model exit gate (shared mechanics)
+
+Single source of mechanics for the optional `--cross-model` exit gate carried by
+`prompt-deep-optimizer`, `skill-optimizer`, and `ddo`/`document-critique`. Each skill carries only
+a 3–5 line stub at its insertion point — sko Step 6.5 (before the Step 7 sync), pdo Step 6a.5
+(after intent preservation), document-critique/ddo Pass 13.5 (before Pass 14 synthesis, final
+iteration only, like Pass 13) — pointing here. Canonical contract:
+`convergence-and-severity.md`. This gate is the model-family extension of the contract's blind
+re-audit guardrail: that gate isolates the judge's context; this one isolates the judge's model
```
Diff preview truncated (59 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-query-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/deep-query-optimizer/references/shared/evidence-contract.md
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
--- baseline/.claude/skills/deep-query-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/deep-query-optimizer/references/shared/evidence_gate.py
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
--- baseline/.claude/skills/deep-query-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/deep-query-optimizer/references/shared/test_evidence_gate.py
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

index-discovery: degraded (semantic probes withheld under embedding pause; 18 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/deep-query-optimizer/SKILL.md | canonical selected source | f73ecf184645 | verified source edits | e5fcc9ce1ab9 |
| $HOME/.claude/skills/deep-query-optimizer/SKILL.md | copy | f4fa0377c383 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/deep-query-optimizer/SKILL.md | copy | f4fa0377c383 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude/standalone/deep-query-optimizer/SKILL.md | copy | e088421d6230 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude-code/deep-query-optimizer/SKILL.md | copy | 03a255724130 | skipped (--no-sync); root ownership check | unchanged |

llms-first: added

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| deep-query-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/deep-query-optimizer/baseline/SKILL.md" ".claude/skills/deep-query-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

4 high, 5 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | --read-only writes nothing conflicts with --annotate, --report and empirical champion persistence.; SELECT-only classification permits data-modifying CTEs, side-effect functions and locking reads.; --minimal leaves Medium findings but the contract still promises convergence with zero Medium+.; A bounded sample/checksum is treated as result equivalence without multiset/order caveats.; Required acceptance contract and helper are absent from the self-contained shared-reference directory.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | All three cases expect nonexistent references/overview.md instead of testing SQL semantics. |
| G Manifest/wrappers | No concrete whenToUse, category, related_skills or model/effort metadata. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 740/1000 characters; body 3260 estimated tokens. Within soft and hard body limits. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 740 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Repository SQL review lacks the size-first llms/source authority section. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| Optimize this PostgreSQL SELECT without changing its results. | True | True | pass |
| Run dqo on queries/report.sql. | True | True | pass |
| Why does this SQL query do a full table scan? | True | True | pass |
| Suggest an index for this exact MySQL join query. | True | True | pass |
| Tune the OFFSET pagination in this SQL file. | True | True | pass |
| Read this EXPLAIN plan and fix the SQL bottleneck. | True | True | pass |
| This correlated subquery is slow; rewrite it with equivalent SQL semantics. | True | True | pass |
| Audit SQL NULL behavior before replacing NOT IN. | True | True | pass |
| Review my SQLite query in read-only mode. | True | True | pass |
| Improve this SQL query and compare before/after plans. | True | True | pass |
| Optimize this MongoDB aggregation pipeline. | False | False | pass |
| Refactor the ORM code that issues one query per user. | False | False | pass |
| Design a dimensional warehouse and dbt models. | False | False | pass |
| Normalize the database schema without a concrete query. | False | False | pass |
| Teach me how SQL indexes work in general. | False | False | pass |
| Audit a skill evaluation JSON suite. | False | False | pass |
| Harden this system prompt that generates SQL. | False | False | pass |
| Review this prose SQL migration guide for clarity. | False | False | pass |
| Find a bug in the database connection pool implementation. | False | False | pass |
| Tune Atlas Search relevance for my index. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `e5fcc9ce1ab9854a15f68e7570056767295ccaa112f394545d7940a5e8c3a7f4`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
