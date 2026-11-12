# design-deep-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 3 | 5 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| I | The routing surface still claims full UI/UX workflows despite handing that scope to ui-deep-optimizer in the body. | Medium | Limit description to visual design and add an explicit UI workflow handoff. |
| A | The required standalone vision-model-design-critique skill and fallback spoke do not exist. | High | Make the existing P9 inspection procedure self-contained; use verified frontend-ui references for available visual rubrics; drop unsupported universal recall percentages. |
| A | Cap 5 and a small-profile rule conflict with the cited skill/document cap of 3, conditionally raised to 5. | Medium | Match the shared cap/raise rule and keep independent final acceptance before clean. |
| F | Generic architecture cases test nonexistent domain behavior instead of visual critique and rendered acceptance. | Medium | Replace invalid cases with brand image, read-only code, unavailable rendering and workflow handoff cases. |
| J | An always-loaded historical changelog adds non-executing bulk. | Medium | Move history to references/CHANGELOG.md; keep changelog_ref. |
| A | Acceptance contract/helper dependencies are missing. | High | Bundle complete authoritative files. |
| P | Code-backed design mode lacks size-first repository/source guidance. | Medium | Add conditional standard section; screenshot-only mode skips repository discovery. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/design-deep-optimizer/SKILL.md
+++ .claude/skills/design-deep-optimizer/SKILL.md
@@ -1,9 +1,10 @@
 ---
 name: design-deep-optimizer
-description: "Multi-stage design & image critique-and-fix optimizer for graphic/brand & UI/UX screens; sibling of code-deep-optimizer/document-critique. Ingests a screenshot, URL, code (HTML/CSS), or spec and runs an 11-pass critique (hierarchy, gestalt, typography, color, usability heuristics/Laws of UX, WCAG, trust, brand-parity, hallucination guard) over the frontend-ui spokes; severity-rates Blocker\u2192Nit and, for code-backed designs, applies Medium+ fixes to convergence (axe/contrast verified). Image/URL/spec inputs get critique-only findings. TRIGGER: \"critique/optimize this design|mockup|UI|screen|landing page|brand asset\", \"/deso\", \"review this screenshot's design\", \"run a design critique\", \"improve this UI's visual design\". SKIP: evals -> deep-eval-optimizer; producing a NEW design (web-design / ui-ux-pro-max); one narrow question (the matching frontend-ui spoke); prose (document-critique); code logic (code-deep-optimizer); photographic or AI-generated-image critique."
+description: >-
+  Audit existing graphic/brand assets and visual design in screenshots or editable components. TRIGGER: "critique this brand asset", "review this screenshot visually", "run deso", "improve typography and spacing". Run 11 critique passes; editable code gets Medium+ repairs with rendered checks, while images, external URLs and specs get findings only. SKIP: full interface workflows, navigation, interaction and accessibility audits → ui-deep-optimizer; new designs or one narrow visual question → frontend-ui; prose → writing-expert (references/document-critique.md); code logic → code-deep-optimizer; eval suites → deep-eval-optimizer. Photographic or generated-art aesthetic critique is outside this skill.
 origin: local
-version: 1.3.2
-updated: '2026-11-09'
+version: "1.4.1"
```
Diff preview truncated (196 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/design-deep-optimizer/evals/evals.json
+++ .claude/skills/design-deep-optimizer/evals/evals.json
@@ -1,92 +1,80 @@
 {
-  "": "https://json-schema.org/draft/2020-12/schema",
   "skill_name": "design-deep-optimizer",
   "version": "1.0.0",
-  "description": "Functional evaluation suite for design-deep-optimizer hub verifying spoke routing, architecture guidance, and domain invariants.",
+  "description": "Behavioral regression cases for the documented workflow and scope boundaries.",
   "evals": [
     {
       "id": 1,
```
Diff preview truncated (137 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/design-deep-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/design-deep-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Critique the visual hierarchy of this brand asset.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Run deso on this logo mockup.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review only the typography and spacing in this screenshot.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Improve the color palette of this existing graphic.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Critique this landing page visually, without auditing its user journey.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Check this component design against our supplied brand tokens.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review the visual composition of this product mockup.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Give me locatable visual findings for this screenshot.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Audit and fix the typography in this editable HTML component.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.4.1", "description_sha256": "372f17649d6dffbedc594482692d70c1ee98e7e4ea0985dbcbe05ff39a4dc5d1", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/design-deep-optimizer/evals/trigger-eval.json
+++ .claude/skills/design-deep-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
   {
-    "query": "how do I use passes for our application architecture",
+    "query": "Critique the visual hierarchy of this brand asset.",
     "should_trigger": true
   },
   {
-    "query": "best practices and patterns for passes",
+    "query": "Run deso on this logo mockup.",
```
Diff preview truncated (105 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/design-deep-optimizer/references/CHANGELOG.md
+++ .claude/skills/design-deep-optimizer/references/CHANGELOG.md
@@ -0,0 +1,10 @@
+2026-11-11 v1.4.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.3.2->1.4.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
+# Changelog
+
+2026-06-23 v1.1.0->1.2.0 — Empirical mode now default-on (gated auto-promote + persist) per § Default policy in the shared contract — for code-backed designs with held-out metrics + must-pass checks the gate auto-runs and persists the champion across runs (prior archived for rollback); mandatory holdout rotation/budget/noise vs reusable-holdout overfitting; honest guarantee = monotonically non-decreasing on the held-out metric, not "better every run"; opt out --dry-run/--no-promote/--structural-only; image/URL/spec inputs stay critique-only. Per operator request.
+2026-06-23 v1.0.1->1.1.0 — added Empirical mode (champion–challenger held-out loop) section citing the new shared contract references/shared/champion-challenger.md; calibration: score = held-out a11y/aesthetic metric (axe pass rate, contrast pass count, computational-aesthetic score), must-pass veto = WCAG AA contrast on all text + no axe criticals + brand-token parity. Per operator request.
+2026-06-16 v1.0.0 — created via concept-family-explorer Phase B + skill-creator. Orchestrates
+the 6 visual-design knowledge spokes built in the same run. Input-adaptive: auto-fix
+convergence loop for code-backed designs, critique-only for image/URL/spec. Pending
```
Diff preview truncated (13 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/design-deep-optimizer/references/passes.md
+++ .claude/skills/design-deep-optimizer/references/passes.md
@@ -31,7 +31,7 @@
 ---

 ## Bundle A — Composition & visual
-*Spoke: `visual-design-principles-and-critique`*
+*Spoke: `frontend-ui` (references/visual-design-principles-and-critique.md)*

 ### P0 — Intent & context

@@ -113,20 +113,21 @@
```
Diff preview truncated (95 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/design-deep-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/design-deep-optimizer/references/shared/convergence-and-severity.md
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
--- baseline/.claude/skills/design-deep-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/design-deep-optimizer/references/shared/evidence-contract.md
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
--- baseline/.claude/skills/design-deep-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/design-deep-optimizer/references/shared/evidence_gate.py
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
--- baseline/.claude/skills/design-deep-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/design-deep-optimizer/references/shared/test_evidence_gate.py
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
| behavior | 0/8 output assertions graded; 4 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 9 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/design-deep-optimizer/SKILL.md | canonical selected source | 9a37da299f82 | verified source edits | 2341fcd2bd74 |
| $HOME/.claude/skills/design-deep-optimizer/SKILL.md | copy | fa8e60297dfa | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/design-deep-optimizer/SKILL.md | copy | fa8e60297dfa | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude/standalone/design-deep-optimizer/SKILL.md | copy | 12b81f4054e7 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude-code/design-deep-optimizer/SKILL.md | copy | 188653581e1e | skipped (--no-sync); root ownership check | unchanged |

llms-first: added

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| design-deep-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/design-deep-optimizer/baseline/SKILL.md" ".claude/skills/design-deep-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

3 high, 5 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | The required standalone vision-model-design-critique skill and fallback spoke do not exist.; Cap 5 and a small-profile rule conflict with the cited skill/document cap of 3, conditionally raised to 5.; Acceptance contract/helper dependencies are missing.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Generic architecture cases test nonexistent domain behavior instead of visual critique and rendered acceptance. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | The routing surface still claims full UI/UX workflows despite handing that scope to ui-deep-optimizer in the body. |
| J Length/disclosure | An always-loaded historical changelog adds non-executing bulk. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 707 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Code-backed design mode lacks size-first repository/source guidance. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| Critique the visual hierarchy of this brand asset. | True | True | pass |
| Run deso on this logo mockup. | True | True | pass |
| Review only the typography and spacing in this screenshot. | True | True | pass |
| Improve the color palette of this existing graphic. | True | True | pass |
| Critique this landing page visually, without auditing its user journey. | True | True | pass |
| Check this component design against our supplied brand tokens. | True | True | pass |
| Review the visual composition of this product mockup. | True | True | pass |
| Give me locatable visual findings for this screenshot. | True | True | pass |
| Audit and fix the typography in this editable HTML component. | True | True | pass |
| Compare this banner design with the brand specification. | True | True | pass |
| Audit checkout workflows, keyboard interactions and accessibility together. | False | False | pass |
| Create a new dashboard design from scratch. | False | False | pass |
| Compute one contrast ratio for these two colors. | False | False | pass |
| Debug the payment submission logic in this component. | False | False | pass |
| Polish this design-review prose document. | False | False | pass |
| Optimize the skill evaluation suite for design critique. | False | False | pass |
| Review the aesthetic quality of my wildlife photograph. | False | False | pass |
| Fix a production system prompt for an image model. | False | False | pass |
| Rebalance the entire frontend skill taxonomy. | False | False | pass |
| Run a participant usability study on this app. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `2341fcd2bd7435be7e81def0dd867f8b9057295cdfa6514fae336906e101fcc1`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
