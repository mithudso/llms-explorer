# deep-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 1 | 3 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| J | Description exceeds the 1000-character hard cap. | High | Condense routing summary; retain detailed member table in body. |
| M | Description has no explicit TRIGGER or SKIP and no concrete whenToUse entries. | Medium | Add disjoint family-router trigger phrases, member handoffs and concrete use cases. |
| A | Router claims 15 passes A-O; current /sko has 16 passes A-P. | Medium | Correct the row. |
| F | Router has no functional suite or canonical trigger corpus. | Medium | Add realistic mixed-artifact routing, read-only and resume cases plus canonical 10+10 corpus. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/deep-optimizer/SKILL.md
+++ .claude/skills/deep-optimizer/SKILL.md
@@ -1,20 +1,25 @@
 ---
 name: deep-optimizer
 description: >-
-  Convergence-loop optimizer ROUTER for code, prose, prompts, skills, agents, SQL, UI/UX,
-  llms files and trading strategies. Members fix Medium+ and verify. Routes to: code-deep-optimizer (source files & repos, /cdo);
-  document-critique (prose docs, /ddo); prompt-deep-optimizer (production prompts in code, /pdo);
-  skill-optimizer (SKILL.md files, /sko); agent-deep-optimizer (Claude Code subagent definitions,
-  /ado); deep-eval-optimizer (skill evaluation suites, /deo); deep-query-optimizer (SQL, EXPLAIN-verified, /dqo); design-deep-optimizer (graphic/UI/UX
-  screens, /deso); ui-deep-optimizer (interface workflows, /ui-deep-optimizer); deep-strategy-optimizer (trading strategies, indicators, cards & backtests, /dso);
```
Diff preview truncated (65 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-optimizer/evals/evals.json
+++ .claude/skills/deep-optimizer/evals/evals.json
@@ -0,0 +1,74 @@
+{
+  "skill_name": "deep-optimizer",
+  "version": "1.0.0",
+  "description": "Behavioral regression cases for the documented workflow and scope boundaries.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "mixed-artifact-routing",
+      "prompt": "I changed src/api.py, queries/report.sql, .claude/agents/reviewer.md and a brand-logo.svg. Route each artifact to its optimizer without executing those optimizers.",
```
Diff preview truncated (77 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/deep-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Which optimizer should review these mixed files?", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Run deep optimizer across this folder.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Sweep everything modified in this session with the matching optimizers.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Route a SQL file, SKILL.md and screenshot to the right optimizers.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Plan a resumable optimizer sweep for this repository folder.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Resume the mixed-file optimization ledger after an interruption.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Optimize every artifact in this folder using its family member.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "I have prompts, source code and brand assets; choose their review loops.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Use --sweep session and show what remains open.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.5.0", "description_sha256": "9ff83a73adef6cf8b69733ca16bc66bdd51d7579ee7438c8f6758b19072678f3", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-optimizer/evals/trigger-eval.json
+++ .claude/skills/deep-optimizer/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Which optimizer should review these mixed files?",
+    "should_trigger": true
+  },
+  {
+    "query": "Run deep optimizer across this folder.",
+    "should_trigger": true
+  },
```
Diff preview truncated (85 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-optimizer/references/CHANGELOG.md
+++ .claude/skills/deep-optimizer/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+2026-11-11 v1.5.0 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.3.2->1.4.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
+# Changelog
```
```diff
--- baseline/.claude/skills/deep-optimizer/scripts/sweep.py
+++ .claude/skills/deep-optimizer/scripts/sweep.py
@@ -15,6 +15,7 @@
     sweep.py done  PATH --status done|failed [--findings N] [--note T]
     sweep.py status                        counts, and the rows still open
     sweep.py reset                         running -> pending (after a crash)
+    sweep.py retry PATH                    explicitly requeue a failed row, keeping history

 Ledger: `<DIR>/.sweep/ledger.json` for a folder sweep, `<git root>/.sweep/session.json`
 for a session sweep, or --ledger PATH. Re-running `plan` keeps `done` rows whose
@@ -53,6 +54,7 @@
     "skill-optimizer": "/sko",
```
Diff preview truncated (74 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-optimizer/scripts/test_sweep_failures.py
+++ .claude/skills/deep-optimizer/scripts/test_sweep_failures.py
@@ -0,0 +1,62 @@
+"""Failure preservation and explicit MongoDB route regressions."""
+import contextlib
+import io
+import json
+from pathlib import Path
+import tempfile
+import unittest
+
+import sweep as S
```
Diff preview truncated (65 lines; complete file and baseline hashes are in JSON).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger (Pass H) | pos 10/10, false-positive 0/10 | predicted | yes |
| behavior | 0/8 output assertions graded; 3 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 151 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/deep-optimizer/SKILL.md | canonical selected source | 9d29e1111863 | verified source edits | 3814d3fd4075 |
| $HOME/.claude/skills/deep-optimizer/SKILL.md | copy | 408fb260d178 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/deep-optimizer/SKILL.md | copy | 408fb260d178 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude/standalone/deep-optimizer/SKILL.md | copy | 4f628c178ee7 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude-code/deep-optimizer/SKILL.md | copy | 7ffa5313df32 | skipped (--no-sync); root ownership check | unchanged |

llms-first: n/a (Thin artifact router; it delegates subject analysis to its members.)

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| deep-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: high (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/deep-optimizer/baseline/SKILL.md" ".claude/skills/deep-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

1 high, 3 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | Router claims 15 passes A-O; current /sko has 16 passes A-P. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Router has no functional suite or canonical trigger corpus. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description exceeds the 1000-character hard cap. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Description has no explicit TRIGGER or SKIP and no concrete whenToUse entries. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | n/a (Thin artifact router; it delegates subject analysis to its members.) |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| Which optimizer should review these mixed files? | True | True | pass |
| Run deep optimizer across this folder. | True | True | pass |
| Sweep everything modified in this session with the matching optimizers. | True | True | pass |
| Route a SQL file, SKILL.md and screenshot to the right optimizers. | True | True | pass |
| Plan a resumable optimizer sweep for this repository folder. | True | True | pass |
| Resume the mixed-file optimization ledger after an interruption. | True | True | pass |
| Optimize every artifact in this folder using its family member. | True | True | pass |
| I have prompts, source code and brand assets; choose their review loops. | True | True | pass |
| Use --sweep session and show what remains open. | True | True | pass |
| Which deep optimizer owns each artifact in this change set? | True | True | pass |
| Optimize this single PostgreSQL query without changing results. | False | False | pass |
| Run cdo directly on src/server.py. | False | False | pass |
| Audit only this SKILL.md file with sko. | False | False | pass |
| Fix this one production system prompt with pdo. | False | False | pass |
| Review this subagent definition with ado. | False | False | pass |
| Audit the assertion quality in this one evaluation suite. | False | False | pass |
| Critique this brand logo with deso. | False | False | pass |
| Audit and fix this existing checkout workflow with ui-deep-optimizer. | False | False | pass |
| Rebalance the complete skill taxonomy. | False | False | pass |
| Explain the meaning of gradient descent; there is no artifact to review. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `3814d3fd407548cd36d2062b8ca8b15f8f4490ca936b1376ad32ff9ef9970c1f`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
