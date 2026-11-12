# agent-deep-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 3 | 3 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| A | The fixed deny list omits MCP and other side-effecting tools while claiming all are denied. | High | Use documented empty built-in tool set, wildcard denial and strict empty MCP config; mock command regression without starting Claude. |
| D | The required inputs section was replaced by a misc-catch-all reference, obscuring the actual delegation contract. | Medium | Restore the literal inputs section name. |
| A | Stale routing retries a global rebuild even under --no-sync/read-only. | Medium | Apply the no-sync and read-only gates to retries too. |
| A | Required local acceptance contract/helper are missing. | High | Bundle complete authoritative dependencies. |
| P | Agent-tree audit lacks size-first llms/source verification guidance. | Medium | Add concise standard section. |
| A | The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. | High | Keep paused embedding/index services untouched; observe/report an existing daemon and require explicit authorization for a separate re-embedding run. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/agent-deep-optimizer/SKILL.md
+++ .claude/skills/agent-deep-optimizer/SKILL.md
@@ -1,9 +1,7 @@
 ---
 name: agent-deep-optimizer
 description: >-
-  Audit and improve a Claude Code subagent definition (~/.claude/agents, .claude/agents): a 16-pass convergence loop over the delegation surface (description, name, precedence, collisions), delegation contract (inputs, final report, stop rules), capability grant (tools, MCP, skills preload, permissionMode, isolation, memory), safety, resilience, model/effort fit and the system-prompt body; fixes Medium+ in place, adds delegation evals and a smoke load check, rebuilds the hub registry and verifies routing.
-  TRIGGER: "optimize this agent", "run ado", "agent deep optimizer", "audit my subagent", "agent never gets delegated to", "least-privilege tools for this agent", "validate agent frontmatter fields", "which model should this agent run on", "add delegation evals".
-  SKIP: prompt text in code → prompt-deep-optimizer / pdo; SKILL.md → skill-optimizer / sko; eval suites → deep-eval-optimizer / deo; running an agent → that agent; missing or ignored agents → agent-asset-parity-auditor.
+  Audit and repair a Claude Code subagent definition and its delegation contract. TRIGGER: "optimize this agent", "run ado", "my agent never gets delegated to", "audit its tool grant", "validate agent frontmatter". Runs 16 passes over description/name/precedence, inputs/final report/stop rules, tools/MCP/preloads/permissions/isolation/memory, safety, resilience, model/effort and prompt body; fixes Medium+, adds delegation evals, verifies parsing and optional load, and checks registry routing. SKIP: prompt text in code → prompt-deep-optimizer; SKILL.md → skill-optimizer; eval suites → deep-eval-optimizer; running an agent → that agent; roster-wide missing or ignored agents → agent-asset-parity-auditor.
 whenToUse:
   - "optimize the <agent-name> agent"
```
Diff preview truncated (91 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/agent-deep-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/agent-deep-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "My subagent never gets picked; audit its delegation description.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Run ado on the release-notes agent definition.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Review the tool grant in .claude/agents/reviewer.md for least privilege.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Optimize this agent file and its final report contract.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Check why the user-level and project-level agents with the same name collide.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Validate agent frontmatter fields and stop conditions.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Audit my custom Claude Code agent, but leave its definition read-only.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Add delegation evals to this existing agent definition.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Which model and effort should this subagent run under?", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.1.1", "description_sha256": "c6dfd8c5204d085a8bc78d4b1c8c7463d99919f8f664c3cc6ec857d4b4e0dc09", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/agent-deep-optimizer/evals/trigger-eval.json
+++ .claude/skills/agent-deep-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
- {
-  "query": "optimize this agent definition",
-  "should_trigger": true
- },
- {
-  "query": "run ado on research-contract-auditor",
-  "should_trigger": true
- },
```
Diff preview truncated (165 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/agent-deep-optimizer/references/CHANGELOG.md
+++ .claude/skills/agent-deep-optimizer/references/CHANGELOG.md
@@ -1,3 +1,5 @@
+2026-11-11 v1.1.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.0.0->1.1.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
 # agent-deep-optimizer changelog

 Newest first. Lives in `references/` so the frontmatter stays free of non-executing bulk (skill-optimizer Pass J.1). This file records changes to agent-deep-optimizer itself; per-run outcomes on a target go to that run's `run-stub.jsonl` (Step 7.0), not here.
```
```diff
--- baseline/.claude/skills/agent-deep-optimizer/references/passes.md
+++ .claude/skills/agent-deep-optimizer/references/passes.md
@@ -79,7 +79,7 @@
 ### Pass G — Tool grant (least privilege)

 - **Resolvability.** Every `tools` entry resolves (`ado_tools.py schema`: `tools-unresolved*`); all unresolved ⇒ High (zero-tool launch failure), some ⇒ Medium with the list.
-- **Read-only agents.** Body declares read-only / audit-only and `tools` is omitted or includes Write/Edit/NotebookEdit without a `disallowedTools` counter ⇒ High. Fix: explicit `tools: Read, Grep, Glob, Bash` (plus the MCP read tools it needs) and a Bash discipline line, or `disallowedTools: Write, Edit, NotebookEdit`.
+- **Read-only agents.** Body declares read-only / audit-only and `tools` is omitted or any granted Write/Edit/NotebookEdit survives the complete `disallowedTools` list ⇒ High. A denial of Edit does not remove Write; inspect the effective tool set, not whether any denial exists. Fix: explicit `tools: Read, Grep, Glob, Bash` (plus the MCP read tools it needs) and a Bash discipline line, or `disallowedTools: Write, Edit, NotebookEdit`.
 - **Omitted `tools` on a narrow agent.** Medium for a specialist (inherits everything, including outward-facing MCP tools); Low for a deliberate general orchestrator with a stated reason.
 - **Specifier misuse.** `disallowedTools: Bash(git push *)` removes all of Bash ⇒ Medium; move the pattern to a permission rule or state the intent in the body.
 - **`Skill` in `tools`.** Medium: use `skills:` to preload; the Skill tool is available regardless.
@@ -148,7 +148,7 @@
```
Diff preview truncated (20 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/agent-deep-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/agent-deep-optimizer/references/shared/convergence-and-severity.md
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
--- baseline/.claude/skills/agent-deep-optimizer/references/shared/cross-model-gate.md
+++ .claude/skills/agent-deep-optimizer/references/shared/cross-model-gate.md
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
--- baseline/.claude/skills/agent-deep-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/agent-deep-optimizer/references/shared/evidence-contract.md
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
--- baseline/.claude/skills/agent-deep-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/agent-deep-optimizer/references/shared/evidence_gate.py
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
--- baseline/.claude/skills/agent-deep-optimizer/references/shared/test_evidence_gate.py
+++ .claude/skills/agent-deep-optimizer/references/shared/test_evidence_gate.py
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
--- baseline/.claude/skills/agent-deep-optimizer/scripts/ado_tools.py
+++ .claude/skills/agent-deep-optimizer/scripts/ado_tools.py
@@ -15,13 +15,14 @@
   backup  <path> --run-id ID [--iter N --from FILE]
                                              pre-write snapshot into the family backup dir

-Stdlib only. PyYAML parses the frontmatter when importable; otherwise a minimal
-key / value / list parser runs and the output carries "yaml_parser": "fallback".
+Stdlib diagnostics. The schema success gate requires PyYAML; without it, the
+minimal parser is diagnostic only and cannot certify strict YAML validity.
 The contract the checks encode lives in ../references/agent-contract.md.
 """
```
Diff preview truncated (80 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/agent-deep-optimizer/scripts/test_ado_schema.py
+++ .claude/skills/agent-deep-optimizer/scripts/test_ado_schema.py
@@ -0,0 +1,56 @@
+"""Synthetic permission/parser counterexamples; no provider or target execution."""
+import argparse
+import contextlib
+import io
+import json
+from pathlib import Path
+import tempfile
+import unittest
+from unittest.mock import patch
```
Diff preview truncated (59 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/agent-deep-optimizer/scripts/test_ado_smoke.py
+++ .claude/skills/agent-deep-optimizer/scripts/test_ado_smoke.py
@@ -0,0 +1,31 @@
+"""Verify probe tool isolation without launching Claude or connecting MCP servers."""
+import argparse
+import contextlib
+import io
+import json
+import unittest
+from unittest.mock import patch
+
+import ado_tools
```
Diff preview truncated (34 lines; complete file and baseline hashes are in JSON).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger (Pass H) | pos 10/10, false-positive 0/10 | predicted | yes |
| behavior | 0/14 output assertions graded; 4 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 62 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/agent-deep-optimizer/SKILL.md | canonical selected source | 6d6a90af141b | verified source edits | bad03d6cd843 |
| $HOME/.claude/skills/agent-deep-optimizer/SKILL.md | copy | 5c4fd9a0f6ea | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/agent-deep-optimizer/SKILL.md | copy | 5c4fd9a0f6ea | skipped (--no-sync); root ownership check | unchanged |

llms-first: added

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| agent-deep-optimizer | unverified (own-intent ranking not run) | True | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: xhigh (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/agent-deep-optimizer/baseline/SKILL.md" ".claude/skills/agent-deep-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

3 high, 3 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | The fixed deny list omits MCP and other side-effecting tools while claiming all are denied.; Stale routing retries a global rebuild even under --no-sync/read-only.; Required local acceptance contract/helper are missing.; The inherited section starts re-embedding after writes while target post-sync guidance makes the daemon passive. |
| B Consistency | Checked lead scope, body procedures, labels and output obligations for agreement. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | The required inputs section was replaced by a misc-catch-all reference, obscuring the actual delegation contract. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | Behavior suite retained or repaired; realistic input/error/boundary cases exist; assertion grading is pending a fresh reviewer. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 708/1000 characters; body 7314 estimated tokens. Soft overage justified by operative multi-pass/safety/convergence content; below hard ceiling. |
| K Prose terms | No remaining generic banned-term hits in the final skill body; proper technical/source names preserved. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 708 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | Agent-tree audit lacks size-first llms/source verification guidance. |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| My subagent never gets picked; audit its delegation description. | True | True | pass |
| Run ado on the release-notes agent definition. | True | True | pass |
| Review the tool grant in .claude/agents/reviewer.md for least privilege. | True | True | pass |
| Optimize this agent file and its final report contract. | True | True | pass |
| Check why the user-level and project-level agents with the same name collide. | True | True | pass |
| Validate agent frontmatter fields and stop conditions. | True | True | pass |
| Audit my custom Claude Code agent, but leave its definition read-only. | True | True | pass |
| Add delegation evals to this existing agent definition. | True | True | pass |
| Which model and effort should this subagent run under? | True | True | pass |
| Fix an agent that assumes it can see the parent conversation. | True | True | pass |
| Run the release-notes agent on this commit range. | False | False | pass |
| Rewrite the production system prompt string in src/prompts.py. | False | False | pass |
| Audit my SKILL.md trigger accuracy. | False | False | pass |
| Optimize the assertion quality in evals/evals.json. | False | False | pass |
| List every missing or ignored agent across the whole roster. | False | False | pass |
| Design an AG2 multi-agent workflow from scratch. | False | False | pass |
| Explain how Claude subagents work in general. | False | False | pass |
| Fix the Python function used by my agent tool. | False | False | pass |
| Polish this prose handoff note for a colleague. | False | False | pass |
| Create a new agent from an idea; I have no definition yet. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.

The probe restriction uses the documented [Claude Code tool and MCP flags](https://code.claude.com/docs/en/cli-reference). A mocked command test does not prove a live loaded invocation.


Bounded repair round: final source `bad03d6cd84316fbc879b5e28dc17036c43af68216a17d4b91128be7b75fd97f`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
