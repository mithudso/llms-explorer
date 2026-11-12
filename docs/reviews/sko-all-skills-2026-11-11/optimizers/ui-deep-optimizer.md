# ui-deep-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 2 | 2 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| G | Version/updated/category/effort/whenToUse/related_skills are nested scalars instead of the routing surface used by optimizer peers. | Medium | Add canonical top-level keys with concrete lists; preserve metadata delta and align mirrored version/effort. |
| A | Required evidence-contract.md and evidence_gate.py are absent. | High | Bundle the complete existing authoritative dependencies. |
| P | Existing llms guidance forces map-first access before source even with a local repository. | Medium | Use repository source before llms summaries; preserve size and source-verification safeguards. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/ui-deep-optimizer/SKILL.md
+++ .claude/skills/ui-deep-optimizer/SKILL.md
@@ -11,13 +11,28 @@
   code-deep-optimizer; prompt authoring use prompt-deep-optimizer; skill authoring
   use skill-optimizer.
 metadata:
+  changelog_ref: references/CHANGELOG.md
   category: developer
   whenToUse: Run ui-deep-optimizer on this dashboard; audit and fix this interface until no Medium findings remain; review and repair checkout workflows, hierarchy and accessibility together
-  version: '1.0.1'
-  delta: '1.0.0 to 1.0.1; verified read-only, research-selection and evidence-role guards'
-  updated: '2026-11-09'
```
Diff preview truncated (44 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/ui-deep-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/ui-deep-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Audit and fix this checkout interface until no Medium findings remain.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Run ui-deep-optimizer on this existing dashboard.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review app workflows, hierarchy and accessibility together.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Repair navigation, error states and responsive behavior in this app.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Deeply review the current interface with one method per pass.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Audit the end-to-end signup user journey and apply confirmed repairs.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review this existing UI in read-only mode with its evidence limits.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Fix visual hierarchy and interaction failures in this runnable screen.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Inspect all states of this interface and require a final no-edit sweep.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.0", "description_sha256": "cd9d5d20408f3a148764d24ebbf02f04698b9d44da22d210768d9bb30ba8eb04", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/ui-deep-optimizer/evals/trigger-eval.json
+++ .claude/skills/ui-deep-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
   {
-    "query": "Run the deep UI optimizer on this app.",
+    "query": "Audit and fix this checkout interface until no Medium findings remain.",
     "should_trigger": true
   },
   {
-    "query": "Use /ui-deep-optimizer on the dashboard.",
+    "query": "Run ui-deep-optimizer on this existing dashboard.",
```
Diff preview truncated (105 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/ui-deep-optimizer/references/CHANGELOG.md
+++ .claude/skills/ui-deep-optimizer/references/CHANGELOG.md
@@ -0,0 +1,2 @@
+2026-11-11 sko 1.0.1->1.1.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
+# Changelog
```
```diff
--- baseline/.claude/skills/ui-deep-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/ui-deep-optimizer/references/shared/convergence-and-severity.md
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
--- baseline/.claude/skills/ui-deep-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/ui-deep-optimizer/references/shared/evidence-contract.md
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
--- baseline/.claude/skills/ui-deep-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/ui-deep-optimizer/references/shared/evidence_gate.py
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
--- baseline/.claude/skills/ui-deep-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/ui-deep-optimizer/references/shared/test_evidence_gate.py
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
| behavior | 0/32 output assertions graded; 10 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 5 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/ui-deep-optimizer/SKILL.md | canonical selected source | 535c2aac4869 | verified source edits | 938df7cc7858 |

llms-first: present (inline scope step names llms.txt, size and source verification)

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| ui-deep-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/ui-deep-optimizer/baseline/SKILL.md" ".claude/skills/ui-deep-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

2 high, 2 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | Required evidence-contract.md and evidence_gate.py are absent.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Behavior suite retained or repaired; realistic input/error/boundary cases exist; assertion grading is pending a fresh reviewer. |
| G Manifest/wrappers | Version/updated/category/effort/whenToUse/related_skills are nested scalars instead of the routing surface used by optimizer peers. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 680/1000 characters; body 2874 estimated tokens. Within soft and hard body limits. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 680 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Existing llms guidance forces map-first access before source even with a local repository. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| Audit and fix this checkout interface until no Medium findings remain. | True | True | pass |
| Run ui-deep-optimizer on this existing dashboard. | True | True | pass |
| Review app workflows, hierarchy and accessibility together. | True | True | pass |
| Repair navigation, error states and responsive behavior in this app. | True | True | pass |
| Deeply review the current interface with one method per pass. | True | True | pass |
| Audit the end-to-end signup user journey and apply confirmed repairs. | True | True | pass |
| Review this existing UI in read-only mode with its evidence limits. | True | True | pass |
| Fix visual hierarchy and interaction failures in this runnable screen. | True | True | pass |
| Inspect all states of this interface and require a final no-edit sweep. | True | True | pass |
| Review this screenshot through the UI methods and disclose unavailable interaction evidence. | True | True | pass |
| Design a new checkout interface from scratch. | False | False | pass |
| Critique only the visual design of this brand logo. | False | False | pass |
| Compute one WCAG contrast ratio. | False | False | pass |
| Debug the backend payment API. | False | False | pass |
| Optimize a production system prompt. | False | False | pass |
| Audit the SKILL.md for this UI skill. | False | False | pass |
| Improve the assertion quality of a UI skill eval suite. | False | False | pass |
| Polish the copy in this one error message. | False | False | pass |
| Explain one Nielsen heuristic with no target interface. | False | False | pass |
| Audit only the graphic composition of a marketing banner. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `938df7cc785805ccbd12fb19867c1e2884a292a277620ae069bcfe93e05df102`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
