# code-deep-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 3 | 2 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| A | Read-only promises no writes but mandatory begin/plan/record/receipt commands persist .cdo state. | High | Use in-memory coverage/receipt in read-only mode; skip all ledger mutations and telemetry writes. |
| A | The required local evidence contract and checker are missing. | High | Bundle the full authoritative dependencies. |
| P | Repo-wide optimizer lacks the standard size-first llms/source-authority section. | Medium | Add the concise standard section. |
| N | MQL is an installed top-level optimizer, but the deferral points at an absent mongodb-expert spoke. | Medium | Route to deep-mongodb-mql-query-optimizer directly. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/code-deep-optimizer/CHANGELOG.md
+++ .claude/skills/code-deep-optimizer/CHANGELOG.md
@@ -1,3 +1,5 @@
+2026-11-11 v1.19.0 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.17.1->1.18.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
 # code-deep-optimizer — changelog

 Moved out of SKILL.md frontmatter 2026-09-09: it was 2,546 bytes, 47% of the always-loaded
```
```diff
--- baseline/.claude/skills/code-deep-optimizer/SKILL.md
+++ .claude/skills/code-deep-optimizer/SKILL.md
@@ -1,21 +1,10 @@
 ---
 name: code-deep-optimizer
 description: >-
-  Multi-stage review-and-fix optimizer for a source file or whole repo. Detects stack,
-  activates reviewer skills, runs an 18-pass audit plus an opt-in advisory track,
-  applies every Medium+ fix in place, verifies via build/lint/tests (backing out
-  regressions), and loops to convergence.
-  TRIGGER: "optimize this code", "run cdo", "deep code review and fix", "review and fix this
-  file or repo", "audit this codebase and fix it until clean", "find and fix bugs in this repo".
```
Diff preview truncated (109 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/docs/2026-06-15-code-deep-optimizer-plan.md
+++ .claude/skills/code-deep-optimizer/docs/2026-06-15-code-deep-optimizer-plan.md
@@ -23,7 +23,7 @@
   - **FM-PARSE** (frontmatter parses): `python3 -c "import yaml,sys; t=open(sys.argv[1]).read(); fm=t.split('---',2)[1]; yaml.safe_load(fm); print('FM OK')" <file>`
   - **DESC-LEN** (description ≤1000 chars): `python3 -c "import yaml,sys; fm=yaml.safe_load(open(sys.argv[1]).read().split('---',2)[1]); d=fm['description']; print(len(d),'chars'); assert len(d)<=1000,'DESC TOO LONG'" <file>`
   - **TOKENS** (SKILL.md body budget): `python3 -c "import sys; b=len(open(sys.argv[1]).read().encode()); print(b,'bytes ~', b//4,'tokens')" SKILL.md` — soft target <24000 bytes (~6k tokens), hard ceiling <40000 bytes (~10k tokens).
-  - **WS-LINT** (whitespace hygiene, from sko Pass L): `python3 -c "import sys,re; [print(n, repr(ln)) for n, ln in enumerate(open(sys.argv[1], newline='').read().splitlines(keepends=True), 1) if re.search('[ \t]+(?=\r?\n|\$)|\t|[​-‍ ﻿\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\r\n', ln)]" <file>` — clean file prints nothing.
+  - **WS-LINT** (whitespace hygiene, from sko Pass L): `python3 -c "import sys,re; [print(n, repr(ln)) for n, ln in enumerate(open(sys.argv[1], newline='').read().splitlines(keepends=True), 1) if re.search('[ \t]+(?=\r?\n|\$)|\t|[\u200b-\u200d \ufeff\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\r\n', ln)]" <file>` — clean file prints nothing.

 ---

```
```diff
--- baseline/.claude/skills/code-deep-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/code-deep-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "optimize this code", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "run cdo on the payments module", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "do a deep multi-pass audit of my repo and auto-fix what you find", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "review and fix this file until the build and tests are green", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "find and fix bugs in this repo until it's clean", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "cdo ./server.js", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "go through my whole project, fix everything you find, then re-check until nothing's left", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "sweep this codebase for perf and security problems and patch them in place", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "keep iterating on my code until lint and the test suite pass clean", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.19.0", "description_sha256": "07fc1205970278f6055c657d32e4fa27aaf11dae92a3a1b45aebbdc99789ff10", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/evals/trigger-eval.json
+++ .claude/skills/code-deep-optimizer/evals/trigger-eval.json
@@ -78,13 +78,5 @@
   {
     "query": "optimize this slow SQL query that's doing a full table scan",
     "should_trigger": false
-  },
-  {
-    "query": "help me figure out why this one jest test keeps failing",
-    "should_trigger": false
-  },
-  {
```
Diff preview truncated (16 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/references/advisory-track.md
+++ .claude/skills/code-deep-optimizer/references/advisory-track.md
@@ -18,7 +18,7 @@

 ### Implementing features & improvements (`--implement-features` / `--auto-improve`)

-When `--implement-features` (or `--auto-improve`) is provided, cdo overrides the report-only constraint for the features it identifies: after the structural loop exits `CLEAN` or `CONVERGED`, it implements each evidence-grounded feature in its own verified round. Full procedure, ordering, and bounds: `references/implement-features.md`.
+When `--implement-features` (or `--auto-improve`) is provided, cdo overrides the report-only constraint for the features it identifies: after the structural loop exits `CLEAN` with zero unresolved Medium+ and successful current verification, it implements each evidence-grounded feature in its own verified round. Full procedure, ordering, and bounds: `references/implement-features.md`.

 ## Dispatch (agent fan-out)

```
```diff
--- baseline/.claude/skills/code-deep-optimizer/references/audit-ledger.md
+++ .claude/skills/code-deep-optimizer/references/audit-ledger.md
@@ -15,12 +15,15 @@
 so a re-run that changes nothing produces no diff. Files carry the git blob sha (`git hash-object`),
 not an mtime.

-## Run protocol (repo mode)
+## Read-only mode
+
+Under `--read-only` or `--report`, do not invoke `begin`, `plan`, `record`, `pass` or `receipt`: they persist ledger state. Read the existing ledger only, compute the proposed plan in memory, and include an in-memory receipt with every pass, coverage and reason. No .cdo file or telemetry is created or updated.
+
+## Run protocol (repo write mode)
```
Diff preview truncated (30 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/references/flags-and-statuses.md
+++ .claude/skills/code-deep-optimizer/references/flags-and-statuses.md
@@ -30,7 +30,7 @@
 | `--implement-features` + `--quick` | `--implement-features` ignored; quick mode is a triage, not an improvement run. |
 | `--implement-features` + `--read-only` / `--report` | `--implement-features` ignored; read-only mode cannot write feature code. Identified improvements are emitted in the report as prescribed diffs only. |
 | `--implement-features` + `--annotate` | `--implement-features` ignored; annotate mode writes comments, not implementations. |
-| `--implement-features` + `--no-verify` | **`--implement-features` forces verify gate ON.** Feature additions without build/test verification are unsafe; `--no-verify` is overridden for the feature-implementation phase. |
+| `--implement-features` + `--no-verify` | **`--implement-features` forces verify gate ON.** Feature additions without build/test verification are unsafe; `--no-verify` is overridden for the feature-implementation phase, including its entry verification on the structural candidate. |
 | `--implement-features` + empirical mode | Sequenced, not merged: the empirical loop runs first on the structural result; the feature phase runs after it and outside champion–challenger, because a feature addition fails the public-API-unchanged veto by design. |
 | `--implement-features` + `--suggest` | Composable: `--suggest` emits the Recommendations section as usual; `--implement-features` additionally implements all identified features. Advisory A1/A2/A3 findings that overlap with implemented features are marked `Implemented` in the report. |

@@ -63,7 +63,7 @@
```
Diff preview truncated (20 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/references/implement-features.md
+++ .claude/skills/code-deep-optimizer/references/implement-features.md
@@ -14,9 +14,11 @@
 - The feature phase runs **once, after the structural convergence loop exits**, and after the
   empirical loop when that loop ran. It never runs inside a loop iteration, so its additions
   never enter the Medium+ exit math.
-- It runs only when the structural loop exited `CLEAN` or `CONVERGED`. On any other exit, skip it
+- It runs only when the structural loop exited `CLEAN` with zero unresolved Medium+ and successful current verification. On any other exit, skip it
   and report `implement-features: skipped (loop exited <status>)`. Adding features on top of
   unresolved Medium+ defects or an unstable loop compounds risk.
+- Run the detected verify gate on the structural candidate before checking feature-entry eligibility, even under `--no-verify`; this entry check is part of the forced feature verification. Missing or failing verification skips feature work.
+- `CONVERGED` means no progress with remaining findings; it never permits the feature phase. Recheck unresolved totals and current verification after empirical mode before adding behavior.
```
Diff preview truncated (15 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/references/quick-mode.md
+++ .claude/skills/code-deep-optimizer/references/quick-mode.md
@@ -28,16 +28,14 @@
    after**: the baseline is a single extra run, not a loop, and without it a
    `FAIL` cannot be attributed. Skip only the bisect. If the after-run is red
    and the baseline was green, report
-   `Verify: FAIL (regression introduced by this run)` and leave the fix in
-   place with that warning; quick mode has no iteration budget to bisect; the
-   caller decides whether to revert or run full `/cdo`. If the baseline was
+   `Verify: FAIL (regression introduced by this run)`, restore only this run's owned regressing repair from its preimage without bisecting, and leave its Critical finding unresolved as `BLOCKED (verify-gate regression)`. Rerun the affected check once to verify restoration; if restoration cannot be verified, retain the failure and exit `TRIAGE-PARTIAL`. Never leave a known regressing repair in place as a completed fix. If the baseline was
    already red, report `Verify: FAIL (pre-existing — baseline was red)` and do
    not attribute it to this run. If no suite is detected, report
```
Diff preview truncated (21 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/code-deep-optimizer/references/shared/convergence-and-severity.md
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
--- baseline/.claude/skills/code-deep-optimizer/references/shared/cross-model-gate.md
+++ .claude/skills/code-deep-optimizer/references/shared/cross-model-gate.md
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
--- baseline/.claude/skills/code-deep-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/code-deep-optimizer/references/shared/evidence-contract.md
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
--- baseline/.claude/skills/code-deep-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/code-deep-optimizer/references/shared/evidence_gate.py
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
--- baseline/.claude/skills/code-deep-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/code-deep-optimizer/references/shared/test_evidence_gate.py
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
```diff
--- baseline/.claude/skills/code-deep-optimizer/references/worked-example.md
+++ .claude/skills/code-deep-optimizer/references/worked-example.md
@@ -151,7 +151,7 @@
 -  return out;
 +  return results.filter((r) => r.status === "fulfilled").map((r) => r.value);
  }
-
+
  export function summarize(items) {
 ```

```
```diff
--- baseline/.claude/skills/code-deep-optimizer/scripts/cdo_ledger.py
+++ .claude/skills/code-deep-optimizer/scripts/cdo_ledger.py
@@ -49,6 +49,8 @@
 )
 CONDITIONAL = ("M5",)
 REPO_SCOPE_ONLY = ("M3", "T2", "T3")  # N/A for a single file by definition
+FILE_PASSES = tuple(p for p in PASSES if p not in REPO_SCOPE_ONLY)
+REVIEW_CONTRACT = "cdo-file-coverage-v2"

 SOURCE_EXT = {
     ".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java",
@@ -160,6 +162,13 @@
```
Diff preview truncated (117 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/scripts/test_cdo_coverage.py
+++ .claude/skills/code-deep-optimizer/scripts/test_cdo_coverage.py
@@ -0,0 +1,60 @@
+"""Coverage/resume regressions; all files live in a temporary directory."""
+import contextlib
+import io
+import json
+from pathlib import Path
+import tempfile
+import unittest
+
+import cdo_ledger as L
```
Diff preview truncated (63 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/code-deep-optimizer/scripts/test_cdo_ledger.py
+++ .claude/skills/code-deep-optimizer/scripts/test_cdo_ledger.py
@@ -46,7 +46,8 @@

     def test_rerun_reviews_only_changed_and_new(self):
         run("begin", "--repo", str(self.repo))
-        run("record", "--repo", str(self.repo), "--passes", "C1,S1", "a.py", "b.py", "c.js")
+        run("record", "--repo", str(self.repo), "--passes", ",".join(L.PASSES),
+            "--verdict", "CLEAN", "a.py", "b.py", "c.js")
         self.assertEqual(self.plan()["review"], [])
         (self.repo / "b.py").write_text("print('edited')\n")
         (self.repo / "d.py").write_text("print('d')\n")
```
Diff preview truncated (22 lines; complete file and baseline hashes are in JSON).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger (Pass H) | pos 10/10, false-positive 0/10 | predicted | yes |
| behavior | 0/18 output assertions graded; 5 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 60 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/code-deep-optimizer/SKILL.md | canonical selected source | 8758d9a3c0d3 | verified source edits | 6054a95afaaa |
| $HOME/.claude/skills/code-deep-optimizer/SKILL.md | copy | e24613cbdcf1 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/code-deep-optimizer/SKILL.md | copy | e24613cbdcf1 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude/standalone/code-deep-optimizer/SKILL.md | copy | 04de06fdc247 | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude-code/code-deep-optimizer/SKILL.md | copy | a1537ea6eaa2 | skipped (--no-sync); root ownership check | unchanged |

llms-first: added

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| code-deep-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/code-deep-optimizer/baseline/SKILL.md" ".claude/skills/code-deep-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

3 high, 2 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | Read-only promises no writes but mandatory begin/plan/record/receipt commands persist .cdo state.; The required local evidence contract and checker are missing.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Behavior suite retained or repaired; realistic input/error/boundary cases exist; assertion grading is pending a fresh reviewer. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 848/1000 characters; body 9627 estimated tokens. Soft overage justified by operative multi-pass/safety/convergence content; below hard ceiling. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 848 characters. |
| N Routing precision | MQL is an installed top-level optimizer, but the deferral points at an absent mongodb-expert spoke. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Repo-wide optimizer lacks the standard size-first llms/source-authority section. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| optimize this code | True | True | pass |
| run cdo on the payments module | True | True | pass |
| do a deep multi-pass audit of my repo and auto-fix what you find | True | True | pass |
| review and fix this file until the build and tests are green | True | True | pass |
| find and fix bugs in this repo until it's clean | True | True | pass |
| cdo ./server.js | True | True | pass |
| go through my whole project, fix everything you find, then re-check until nothing's left | True | True | pass |
| sweep this codebase for perf and security problems and patch them in place | True | True | pass |
| keep iterating on my code until lint and the test suite pass clean | True | True | pass |
| audit this file, apply the medium-plus fixes, and loop to convergence | True | True | pass |
| give my current branch's git diff a quick one-shot code review | False | False | pass |
| review and fix this README until it reads clean | False | False | pass |
| optimize this system prompt that runs in my agent | False | False | pass |
| audit and fix my SKILL.md file | False | False | pass |
| just run prettier to format this file | False | False | pass |
| set up eslint and a CI pipeline for my new repo from scratch | False | False | pass |
| recommend a microservices architecture for a project I haven't built yet | False | False | pass |
| why is this aggregation pipeline slow and what index should I add | False | False | pass |
| root-cause this runtime error from my production logs and open a remediation PR | False | False | pass |
| optimize this slow SQL query that's doing a full table scan | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `6054a95afaaa2e591d95386b34599725a792dcd2cc30d7aeafa8a4e7328a8acd`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
