# deep-eval-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 2 | 4 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| A | Missing-eval generation can run before the read-only audit gate. | High | Resolve audit/dry-run and managed-source boundaries before creating or rewriting any file. |
| A | Body says max 5 by default; flag catalog default is 3. | Medium | Use the catalog default 3, hard maximum 5, without unrequested execution. |
| A | Missing fixtures and malformed trigger rows are not safely validated despite Pass G/L guarantees. | High | Add schema/type/fixture checks with regression tests and useful findings instead of crashes. |
| D | Advanced techniques require inaccessible gradients/kernel probes and make unsupported guarantees without prerequisites. | Medium | Make these opt-in evidence-backed diagnostics and state unavailable limits; remove false mathematical guarantees. |
| F | Only two abstract cases; no unavailable executor or read-only missing-eval boundary case. | Medium | Preserve existing cases and add concrete safety/failure-recovery scenarios. |
| P | Skill-tree/eval work lacks size-first llms/source authority guidance. | Medium | Add the concise standard section. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/deep-eval-optimizer/SKILL.md
+++ .claude/skills/deep-eval-optimizer/SKILL.md
@@ -1,9 +1,7 @@
 ---
 name: deep-eval-optimizer
 description: >-
-  Audit, grade, optimize, and generate evaluation suites for AI agent skills across the corpus: runs a 12-pass convergence loop (Passes A-L) on eval prompts, assertions, near-miss trigger sets, and fixtures; writes Medium+ fixes in place; creates missing evals from templates; runs tests via --run only when a verified real executor is available.
-  TRIGGER: "optimize evals", "audit skill evals", "create evals for skill", "eval optimizer", "run deo", "deep eval optimizer", "grade evals", "fix evals", "run skill evals", "eval test cases".
-  SKIP: optimize skill markdown/code/prompts → skill-optimizer / sko; optimize general system prompts → prompt-deep-optimizer / pdo; code AST refactoring → code-deep-optimizer / cdo; tree rebalancing → skill-tree-architect.
+  Audit, improve and create evaluation suites for AI agent skills. TRIGGER: "optimize evals", "run deo", "audit skill evals", "create missing evals", "grade assertions", "run skill benchmarks". The 12-pass loop covers realistic prompts, objective assertions, near-miss triggers, fixtures, leakage and schemas; fixes Medium+ and preserves valid cases. --run requires a verified real executor; audit/dry-run writes nothing. SKIP: skill markdown → skill-optimizer; production prompts → prompt-deep-optimizer; code refactoring → code-deep-optimizer; skill-tree taxonomy → skill-tree-architect.
 whenToUse:
   - "optimize evals for a skill"
```
Diff preview truncated (102 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/evals/evals.json
+++ .claude/skills/deep-eval-optimizer/evals/evals.json
@@ -9,19 +9,97 @@
       "prompt": "Audit the existing evals for a skill that has vague assertions and only 1 test case. Optimize it to production standard.",
       "expected_output": "Optimized evals.json with expanded realistic test cases, objective verifiable assertions, and 0 Medium+ findings across Passes A-L.",
       "assertions": [
-        {"name": "eliminates subjective assertions", "check": "no assertions containing subjective qualifiers without structural verification"},
-        {"name": "minimum test case threshold", "check": "produces at least 2 distinct test cases"},
-        {"name": "schema validity", "check": "valid JSON matching canonical evals schema"}
-      ]
+        {
+          "name": "eliminates subjective assertions",
```
Diff preview truncated (107 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/evals/fixtures/transform-helper.txt
+++ .claude/skills/deep-eval-optimizer/evals/fixtures/transform-helper.txt
@@ -0,0 +1,3 @@
+Name: data-transform-helper
+Purpose: Sort a pasted comma-separated list of integers in ascending order, keeping duplicates. Report invalid tokens without changing valid values.
+Output: sorted integers and a separate invalid-token list.
```
```diff
--- baseline/.claude/skills/deep-eval-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/deep-eval-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Audit the eval cases for this skill and fix vague assertions.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Run deo on this evaluation suite.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Create missing functional and trigger tests for the attached skill.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Our negative trigger queries are irrelevant; replace them with near misses.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Grade the prompts and expected outputs in this eval suite.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Check fixture paths and JSON schema in evals/evals.json.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Improve our benchmark cases without leaking the skill answers.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review why every assertion passes even with the skill disabled.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Validate this trigger test corpus has 10 positives and 10 realistic negatives.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "da0825a67c6edefdbb2a621ae3ec3fff0c040c1e4cac6e797805b80594e7c9e1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/evals/trigger-eval.json
+++ .claude/skills/deep-eval-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
   {
-    "query": "optimize the eval suite for this skill",
+    "query": "Audit the eval cases for this skill and fix vague assertions.",
     "should_trigger": true
   },
   {
-    "query": "run deo on my-skill",
+    "query": "Run deo on this evaluation suite.",
```
Diff preview truncated (105 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/references/CHANGELOG.md
+++ .claude/skills/deep-eval-optimizer/references/CHANGELOG.md
@@ -1,3 +1,5 @@
+2026-11-11 v1.1.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.0.0->1.1.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
 # deep-eval-optimizer changelog

 - "2026-09-29 deo v1.0.0 — initial release of Deep Eval Optimizer: 12-pass convergence loop (Passes A-L) for grading and optimizing eval suites; automatic missing eval generation from ~/dev/evals/templates; integration with ~/dev/evals runner and benchmark aggregator; --run execution support."
```
```diff
--- baseline/.claude/skills/deep-eval-optimizer/references/eval-schemas.md
+++ .claude/skills/deep-eval-optimizer/references/eval-schemas.md
@@ -12,6 +12,7 @@
     {
       "id": 1,
       "name": "descriptive-eval-name",
+      "evaluation_intent": "task",
       "prompt": "Realistic user input without leaked skill names or answers",
       "expected_output": "Comprehensive deliverable specification",
       "files": ["inputs/fixture.txt"],
@@ -32,6 +33,8 @@
 }
```
Diff preview truncated (19 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/references/flags-and-statuses.md
+++ .claude/skills/deep-eval-optimizer/references/flags-and-statuses.md
@@ -19,6 +19,5 @@
 | `evals-created` | Missing evals generated and verified |
 | `benchmark-passed` | `--run` executed and all assertions passed >= 90% threshold |
 | `benchmark-failed` | `--run` executed and assertions failed pass bar |
-| `clean` | Audit found 0 Medium+ findings |
-
+| `clean` | Read-only audit found 0 Medium+ findings; not an executed benchmark |
 | `EXECUTOR_UNAVAILABLE` | The requested real execution harness or evidence is unavailable; no pass rate or convergence is claimed. |
```
```diff
--- baseline/.claude/skills/deep-eval-optimizer/references/passes.md
+++ .claude/skills/deep-eval-optimizer/references/passes.md
@@ -3,6 +3,8 @@
 The 12 analytical passes run by `deep-eval-optimizer` (`/deo`) to audit, grade, and optimize evaluation suites for AI agent skills.

 ---
+
+Advanced diagnostics below are optional, not prerequisites for a static suite audit. Before selecting syscall tracing, gradient attribution, semantic-boundary mining, Shapley evaluation or sequential trials, verify compatible tools, authorization, reference data and a declared measurement contract. Do not fabricate observations or introduce probes into a customer workspace. Selected methods without prerequisites are UNAVAILABLE; report their gaps. Plain token-frequency entropy is a text heuristic, not attention-gradient or saliency evidence.

 ### Pass A — Prompt Realism & Ecological Validity
 Audits user prompt authenticity.
@@ -44,11 +46,11 @@
```
Diff preview truncated (39 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/scripts/suite_validator.py
+++ .claude/skills/deep-eval-optimizer/scripts/suite_validator.py
@@ -8,6 +8,7 @@
 import json
 from pathlib import Path
 import math
+import re
 from typing import Dict, Any, List

 PASSES = {
@@ -27,13 +28,85 @@

```
Diff preview truncated (116 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/scripts/test_invocation_cases.py
+++ .claude/skills/deep-eval-optimizer/scripts/test_invocation_cases.py
@@ -0,0 +1,43 @@
+"""Manual/routing coverage is not answer leakage merely for naming a skill."""
+import json
+from pathlib import Path
+import tempfile
+import unittest
+
+from suite_validator import validate_suite
+
+
```
Diff preview truncated (46 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/deep-eval-optimizer/scripts/test_suite_validator.py
+++ .claude/skills/deep-eval-optimizer/scripts/test_suite_validator.py
@@ -0,0 +1,51 @@
+"""Regression tests for malformed suites and fixture integrity; no skill execution."""
+import json
+from pathlib import Path
+import tempfile
+import unittest
+
+from suite_validator import validate_suite
+
+
```
Diff preview truncated (54 lines; complete file and baseline hashes are in JSON).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger (Pass H) | pos 10/10, false-positive 0/10 | predicted | yes |
| behavior | 0/11 output assertions graded; 5 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 18 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/deep-eval-optimizer/SKILL.md | canonical selected source | 40109868cca3 | verified source edits | 891f65566173 |
| $HOME/.claude/skills/deep-eval-optimizer/SKILL.md | copy | c188906a3695 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/deep-eval-optimizer/SKILL.md | copy | c188906a3695 | skipped (--no-sync); root ownership check | unchanged |

llms-first: added

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| deep-eval-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/deep-eval-optimizer/baseline/SKILL.md" ".claude/skills/deep-eval-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

2 high, 4 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | Missing-eval generation can run before the read-only audit gate.; Body says max 5 by default; flag catalog default is 3.; Missing fixtures and malformed trigger rows are not safely validated despite Pass G/L guarantees. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Advanced techniques require inaccessible gradients/kernel probes and make unsupported guarantees without prerequisites. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Only two abstract cases; no unavailable executor or read-only missing-eval boundary case. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 587/1000 characters; body 2573 estimated tokens. Within soft and hard body limits. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 587 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Skill-tree/eval work lacks size-first llms/source authority guidance. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| Audit the eval cases for this skill and fix vague assertions. | True | True | pass |
| Run deo on this evaluation suite. | True | True | pass |
| Create missing functional and trigger tests for the attached skill. | True | True | pass |
| Our negative trigger queries are irrelevant; replace them with near misses. | True | True | pass |
| Grade the prompts and expected outputs in this eval suite. | True | True | pass |
| Check fixture paths and JSON schema in evals/evals.json. | True | True | pass |
| Improve our benchmark cases without leaking the skill answers. | True | True | pass |
| Review why every assertion passes even with the skill disabled. | True | True | pass |
| Validate this trigger test corpus has 10 positives and 10 realistic negatives. | True | True | pass |
| Run skill evals if a real executor is available and disclose any gap. | True | True | pass |
| Fix the trigger description in the skill markdown itself. | False | False | pass |
| Harden our production system prompt against injection. | False | False | pass |
| Refactor the benchmark runner Python implementation. | False | False | pass |
| Rebalance the entire skill tree taxonomy. | False | False | pass |
| Evaluate whether a trading strategy backtest is overfit. | False | False | pass |
| Explain evaluation metrics for a classification model. | False | False | pass |
| Run an existing application unit test without auditing skill evals. | False | False | pass |
| Audit my subagent tool permissions. | False | False | pass |
| Optimize this slow SQL query. | False | False | pass |
| Rewrite a one-off prompt before I paste it into chat. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `891f6556617353ff392f267872fa37d251142c699fdd97bc822d580a64203a7d`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
