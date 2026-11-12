# prompt-deep-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 3 | 3 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| A | The body/table allow clamping to 10 despite the canonical prompt ceiling of 5. | High | Clamp to 1-5 consistently and preserve small-profile cap/raise behavior. |
| B | The rationale names stale claude-opus-5 while the advisory frontmatter names the verified current claude-opus-5-5. | Medium | Make the rationale tier-based and preserve live-source metadata provenance. |
| A | Relative contract link resolves to references/references/shared; helper documentation claims a sibling library but code loads a bundled scripts helper. | Medium | Correct the relative link and document the actual bundled helper location. |
| P | Code prompt audit lacks size-first repository/source discovery guidance. | Medium | Add standard section conditional on a repository target; pasted text remains direct input. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |
| A | The checkpoint records the fixed baseline hash even after candidate rewrites; it cannot establish the identity of the candidate being resumed. | High | Keep baseline and current saved-candidate SHA bindings separate and verify both on resume. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 9/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/prompt-deep-optimizer/SKILL.md
+++ .claude/skills/prompt-deep-optimizer/SKILL.md
@@ -1,20 +1,10 @@
 ---
 name: prompt-deep-optimizer
 description: >-
-  Optimize a production system prompt, agent instruction block, tool-call template, or workflow
-  scaffold that lives in code and runs repeatedly. Runs a 16-pass audit, applies every Medium+
-  fix, loops to convergence, and outputs the drop-in rewrite plus a named algorithm pick (APE,
-  OPRO, MIPROv2, GEPA, ProTeGi, TextGrad, EvoPrompt) or "structural-only" without training data.
-  TRIGGER: "optimize this system prompt"; "run pdo"; "harden the tool-call template we ship";
-  inconsistent prompt output; audit a prompt for injection holes; which prompt optimization
```
Diff preview truncated (108 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-deep-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/prompt-deep-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "optimize this system prompt", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "run pdo on our agent's instruction block", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "my production prompt gives inconsistent answers every run, tighten it up", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "run a champion-challenger loop on this support-assistant prompt and only promote if it beats the holdout", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "audit this system prompt for prompt-injection holes", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "harden the tool-call template we ship in the codebase", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "this agent prompt runs on every request and needs cleaning up before we ship", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "which prompt optimization algorithm should I use, OPRO or MIPROv2?", "should_trigger": true, "predicted_trigger": false, "verdict": "fail", "mode": "predicted", "reason": "No production or repeatedly executed prompt context is given; generic algorithm advice is ambiguous.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "optimize my policy prompt against these eval cases with must-pass checks", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "2.12.1", "description_sha256": "3b34c4ef2b0593f6d41cd2bbc59b750d33241b5b193251f6b88035cfbbc3a5fa", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-deep-optimizer/evals/trigger-eval.json
+++ .claude/skills/prompt-deep-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
- {
-  "query": "optimize this system prompt",
-  "should_trigger": true
- },
- {
-  "query": "run pdo on our agent's instruction block",
-  "should_trigger": true
- },
```
Diff preview truncated (165 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-deep-optimizer/references/CHANGELOG.md
+++ .claude/skills/prompt-deep-optimizer/references/CHANGELOG.md
@@ -1,3 +1,5 @@
+2026-11-11 v2.12.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 2.11.0->2.12.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
 2026-10-15 v2.10.1->v2.10.2 — peer deferral seeded by agent-deep-optimizer v1.0.0: one when-not-to-use line routing whole subagent definition files to /ado (pdo keeps bare instruction blocks and the bounded Group 1+4 sub-audit); related_skills gains agent-deep-optimizer. Additive only; no pass run.
 # prompt-deep-optimizer — archived changelog

```
```diff
--- baseline/.claude/skills/prompt-deep-optimizer/references/operations.md
+++ .claude/skills/prompt-deep-optimizer/references/operations.md
@@ -37,7 +37,7 @@
 |---|---|---|
 | Passes | 16 (A–P) | Every pass emits a row each iteration, `N/A` and `partial` included. `partial` counts as active. |
 | Groups | 5 (3 under `profile: small`) | Parallel-dispatch bundles. Group 5 carries 4 passes because 16 does not divide by 5. |
-| Iteration cap | 5 (3 under `profile: small`) | Step 5 condition 5. `--max-iter=N` replaces it, clamped 1–10. |
+| Iteration cap | 5 (3 under `profile: small`) | Step 5 condition 5. `--max-iter=N` replaces it, clamped 1–5. |
 | Cap raise | 3 → 5 | Small profile only. Evaluated **once**, at the iteration-3 boundary: if Medium+ findings fell by ≥50% from iteration 2 to 3, the cap is 5 for the rest of the run. |
 | Default budget | 20 minutes wall clock | Step 5 condition 7 runs **by default** (registered deviation, see § Exit-condition notes). `--budget-minutes=N` overrides; `--budget-minutes=0` disables. |
 | Subagent round-trips | 1 per group per iteration | No mid-iteration retry. A second consecutive error escalates that group to sequential. |
@@ -57,7 +57,7 @@
```
Diff preview truncated (26 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-deep-optimizer/references/operator-actions.md
+++ .claude/skills/prompt-deep-optimizer/references/operator-actions.md
@@ -0,0 +1,7 @@
+# Outstanding operator verification
+
+| Dependency | State | Evidence | Required action |
+|---|---|---|---|
+| references/shared/convergence-and-severity.md vocabulary mapping | BLOCKED / operator action | The cross-check stamp remains 2026-06-11. On 2026-11-11 it was 153 days old, beyond the 90-day review interval. | Re-verify the stamped mapping through a separately authorized review/research action. Update the stamp only after that verification. |
+
+This record handles frozen Pass A's freshness requirement. It does not claim that the mapping was re-verified, and it does not authorize new research, indexing or provider calls. Keep the row visible while unresolved; do not certify clean dependency freshness.
```
```diff
--- baseline/.claude/skills/prompt-deep-optimizer/references/output-spec.md
+++ .claude/skills/prompt-deep-optimizer/references/output-spec.md
@@ -53,7 +53,7 @@

 1. **Intent-preservation check** — per-version 5-field checklist plus "Deliberate behavioral deltas (finding-justified)" block (or drift note if arrived here despite gate). When blind re-audit gate (6a0) ran, note result here.
 2. **Behavioral smoke test** — per-input PASS/FAIL table from Step 6a2 (input class | original result | rewrite result | contract-equivalent? | validator result | evidence grade), or explicit N/A reason row.
-3. **Original prompt** — the ingested text verbatim, so the reader can diff it against item 4 without holding their own copy. Above ~1,500 tokens, emit a unified diff instead. Omit only when the target was a file path the reader already has, and say which.
+3. **Original prompt** — a redacted display copy of the ingested text, preserving non-sensitive content so the reader can compare item 4. Above ~1,500 tokens, emit a unified diff of the redacted original and redacted candidate. Redact both removed and added lines before rendering a diff. Omit only when the target was a file path the reader already has, and say which. Never print the raw credential/PII-bearing original.
 4. **Final optimized prompt** — drop-in ready, complete, no truncation. Secrets/PII redacted per Step 4. On non-clean exit, this is best-of-pool candidate selected in Step 5.
 5. **Iteration log** — per-iteration table from Step 5.
 6. **Changes-made table** — cumulative across all iterations, explicit Status column:
@@ -67,6 +67,8 @@
```
Diff preview truncated (29 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-deep-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/prompt-deep-optimizer/references/shared/convergence-and-severity.md
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
--- baseline/.claude/skills/prompt-deep-optimizer/references/shared/cross-model-gate.md
+++ .claude/skills/prompt-deep-optimizer/references/shared/cross-model-gate.md
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
--- baseline/.claude/skills/prompt-deep-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/prompt-deep-optimizer/references/shared/evidence_gate.py
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
--- baseline/.claude/skills/prompt-deep-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/prompt-deep-optimizer/references/shared/test_evidence_gate.py
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
| trigger (Pass H) | pos 9/10, false-positive 0/10 | predicted | yes |
| behavior | 0/19 output assertions graded; 6 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 123 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/prompt-deep-optimizer/SKILL.md | canonical selected source | a852a60fdff5 | verified source edits | 7352f32f495b |
| $HOME/.claude/skills/prompt-deep-optimizer/SKILL.md | copy | 0ad785b1c16c | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/prompt-deep-optimizer/SKILL.md | copy | 0ad785b1c16c | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude/standalone/prompt-deep-optimizer/SKILL.md | copy | 194722961fbb | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/claude-code/prompt-deep-optimizer/SKILL.md | copy | 6d390c3e71bb | skipped (--no-sync); root ownership check | unchanged |

llms-first: added

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| prompt-deep-optimizer | stale | False | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/prompt-deep-optimizer/baseline/SKILL.md" ".claude/skills/prompt-deep-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

3 high, 3 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | The body/table allow clamping to 10 despite the canonical prompt ceiling of 5.; Relative contract link resolves to references/references/shared; helper documentation claims a sibling library but code loads a bundled scripts helper.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive.; The checkpoint records the fixed baseline hash even after candidate rewrites; it cannot establish the identity of the candidate being resumed. |
| B Consistency | The rationale names stale claude-opus-5 while the advisory frontmatter names the verified current claude-opus-5-5. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Behavior suite retained or repaired; realistic input/error/boundary cases exist; assertion grading is pending a fresh reviewer. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 9/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 914/1000 characters; body 9604 estimated tokens. Soft overage justified by operative multi-pass/safety/convergence content; below hard ceiling. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 914 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Code prompt audit lacks size-first repository/source discovery guidance. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| optimize this system prompt | True | True | pass |
| run pdo on our agent's instruction block | True | True | pass |
| my production prompt gives inconsistent answers every run, tighten it up | True | True | pass |
| run a champion-challenger loop on this support-assistant prompt and only promote if it beats the holdout | True | True | pass |
| audit this system prompt for prompt-injection holes | True | True | pass |
| harden the tool-call template we ship in the codebase | True | True | pass |
| this agent prompt runs on every request and needs cleaning up before we ship | True | True | pass |
| which prompt optimization algorithm should I use, OPRO or MIPROv2? | True | False | fail |
| optimize my policy prompt against these eval cases with must-pass checks | True | True | pass |
| keep looping over my workflow-scaffold prompt until no medium findings are left | True | True | pass |
| help me quickly reword this one-off prompt I'm about to paste into Claude | False | False | pass |
| critique this short prompt draft, it's only about three sentences | False | False | pass |
| optimize my SKILL.md so it triggers more reliably | False | False | pass |
| audit this skill file and fix its trigger accuracy | False | False | pass |
| review and polish this on-call runbook document | False | False | pass |
| optimize this RFC doc for clarity and flow | False | False | pass |
| optimize my MongoDB aggregation query, it's running slow | False | False | pass |
| review this codebase for bugs and fix them | False | False | pass |
| teach me prompt engineering best practices | False | False | pass |
| how much will this prompt cost to run on Opus vs Sonnet | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `7352f32f495b300437125d1abf6e10a850aa9a962187a1e5ea97795acf96cda0`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
