# prompt-helper-optimizer

Status: author pass complete; final blind review and output-assertion grading pending. No final convergence claim.

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
| 1 | 1 | 6 | 0 | collected findings, applied owned fixes |
| 2 | 0 | 0 | 0 | author re-audit and static checks; blind gate pending |

Hygiene: deterministic byte and relative-link checks pass. Pre-lint: retained in private evidence; strict PyYAML validation also ran.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| A | The external optimizer receives the prompt as-is; warning to redact does not prevent credentials/private data from being sent or saved. | High | Use inline optimization for sensitive prompts unless the destination is authorized; skip external saves of sensitive bodies and expose no values. |
| A | The skill labels all attempted actions as completion and stops at 20 tool calls even when authorized work remains possible. | Medium | Require verified completion; make 20 calls a checkpoint, and use honest blocked/partial status for actual impediments. |
| F | There are no functional evals or canonical trigger cases for review, auto-execution, intent preservation or sensitive input. | Medium | Create realistic behavior and 10+10 corpus suites. |
| F | Legacy hub tools have no unavailable-tool fallback after inline optimization. | Medium | Discover currently exposed tools, then use available skill/agent descriptions without inventing servers or starting services. |
| K | Several banned filler terms occur outside code; replace nontechnical wording while preserving named methods. | Medium | Use method, current research and using; retain technical meaning. |
| B | The text requires six sections but also omits Relevant agents when none fit. | Medium | Name five required sections plus the conditional agents section. |
| A | Capability selection runs before the curated Goal it requires exists; the review-mode order is different. | Medium | Curate intent first, then select capabilities from the raw request and curated Goal. |

eval: predicted (same-model author-context prediction; Claude quota block; no provider calls).

| Metric | Result | Target | Pass? |
|---|---:|---:|---|
| should-trigger rate | 10/10 | ≥9/10 | yes |
| false-positive rate | 0/10 | ≤1/10 | yes |

Exploratory corpus only. Global canonical histories were preserved where present; each target evals/trigger-corpus.jsonl is its scoped source of truth; original global histories remain private. New corpora were authored after the content audit; baseline replay is retrospective, not independent holdout evidence.

```diff
--- baseline/.claude/skills/prompt-helper-optimizer/SKILL.md
+++ .claude/skills/prompt-helper-optimizer/SKILL.md
@@ -1,26 +1,11 @@
 ---
 name: prompt-helper-optimizer
 title: "Prompt Helper and Optimizer"
-description: >
-  One-off and exploratory prompt improvement — interprets a raw prompt, finds
-  weaknesses, and rewrites it into an agent-ready instruction. Two aliases:
-  /ph (review mode: critique + recommendations) and /phe (auto-execute mode:
-  optimize, save, and immediately run the improved prompt). Algorithm-aware:
-  recommends APE, OPRO, ProTeGi, TextGrad, EvoPrompt, DSPy/MIPROv2, GEPA,
```
Diff preview truncated (126 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-helper-optimizer/evals/evals.json
+++ .claude/skills/prompt-helper-optimizer/evals/evals.json
@@ -0,0 +1,83 @@
+{
+  "skill_name": "prompt-helper-optimizer",
+  "version": "1.0.0",
+  "description": "Behavioral regression cases for the documented workflow and scope boundaries.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "review-does-not-execute",
+      "prompt": "/ph Improve this one-off prompt: Summarize the meeting in five bullets and list each action owner.",
```
Diff preview truncated (86 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-helper-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/prompt-helper-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Improve this short prompt before I paste it into chat.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Use ph to critique a one-off prompt draft.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Run phe on this short exploratory task prompt and carry out the result.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Make this vague one-off instruction agent-ready.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Strengthen this three-sentence prompt for a single meeting summary.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Rubber-duck this short prompt with me.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Rewrite this prompt for one immediate chat session.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Interpret this raw request and turn it into a focused instruction.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
+{"query": "Recommend an algorithm for improving this exploratory prompt draft.", "should_trigger": true, "predicted_trigger": true, "verdict": "pass", "mode": "predicted", "reason": "Description scope covers the requested artifact and action.", "date": "2026-11-11", "skill_version": "1.8.1", "description_sha256": "21fbd3875da53c20dd29ced578e7ae3134d91926ba0bdbe1dc9213382b3e8e20", "evaluation_context": "same-model author-context replay after bounded repairs; fresh independent recheck pending", "split": "exploratory", "retired": null}
```
Diff preview truncated (23 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-helper-optimizer/evals/trigger-eval.json
+++ .claude/skills/prompt-helper-optimizer/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Improve this short prompt before I paste it into chat.",
+    "should_trigger": true
+  },
+  {
+    "query": "Use ph to critique a one-off prompt draft.",
+    "should_trigger": true
+  },
```
Diff preview truncated (85 lines; complete file and baseline hashes are in JSON).
```diff
--- baseline/.claude/skills/prompt-helper-optimizer/references/CHANGELOG.md
+++ .claude/skills/prompt-helper-optimizer/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+2026-11-11 v1.8.1 — bounded blind-review repairs; offline regression evidence recorded; final fresh recheck pending.
+2026-11-11 sko 1.7.1->1.8.0 — content/routing audit and evaluation evidence; predicted results only; blind acceptance pending.
+# Changelog
```
```diff
--- baseline/.claude/skills/prompt-helper-optimizer/references/prompt-optimization-algorithms.md
+++ .claude/skills/prompt-helper-optimizer/references/prompt-optimization-algorithms.md
@@ -2,7 +2,7 @@

 verified-as-of: 2026-10-05 — volatile sections (re-verify via deep-research every 90 days): Section 1 tier-table benchmark claims, 3.1 DSPy stats, 3.6 MIPROv2 modes, 3.7 GEPA, 3.10 Assertions status, Section 7 tool matrix, Section 8 recent developments. Re-verified 2026-10-05 against arXiv abstracts, the DSPy repo/releases (3.4.0), PyPI, and vendor docs. NOT re-verified: dollar-cost figures in the tier tables and 3.3/3.6 (~$0.50, ~$5), PromptWizard's "<30 examples" threshold, the Anthropic Console prompt improver, and Sections 2, 4, 5 (stable background; stamp 2026-06-11 or earlier).

-Comprehensive reference for prompt optimization algorithms, practical techniques, and management systems. Compiled from primary research papers, documentation, and 2025-2026 state-of-the-art surveys.
+Comprehensive reference for prompt optimization algorithms, practical techniques, and management systems. Compiled from primary research papers, documentation, and 2025-2026 research surveys.

 ## How to use this context

@@ -21,7 +21,7 @@
```
Diff preview truncated (52 lines; complete file and baseline hashes are in JSON).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger (Pass H) | pos 10/10, false-positive 0/10 | predicted | yes |
| behavior | 0/8 output assertions graded; 4 cases await independent reviewer | predicted pending | yes |

index-discovery: degraded (semantic probes withheld under embedding pause; 19 direct referrers read/scanned).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/prompt-helper-optimizer/SKILL.md | canonical selected source | 2a7954a4b1fa | verified source edits | 36f2a59d4c03 |
| $HOME/.claude/skills/prompt-helper-optimizer/SKILL.md | copy | 2a7954a4b1fa | skipped (--no-sync); root ownership check | unchanged |
| $HOME/.global-ai-hub/skills/prompt-helper-optimizer/SKILL.md | copy | 2a7954a4b1fa | skipped (--no-sync); root ownership check | unchanged |

llms-first: n/a (One-off pasted prompt transformation; codebase prompts route to prompt-deep-optimizer.)

| Skill | Verdict | Indexed description matches? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---:|
| prompt-helper-optimizer | unverified (own-intent ranking not run) | True | not probed; embedding pause | 0 |

prose-index: daemon up (observed only)
index: deferred to root coordinated phase
degraded: semantic discovery, catalog refresh and routing acceptance incomplete; exit DEGRADED+EVALS-MISSING pending root continuation.

model: claude-opus-5-5 · effort: high (tier: flagship; classification: heuristic; ID: models overview checked 2026-11-11).

Snapshot & rollback: `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/optimizers/prompt-helper-optimizer/baseline/SKILL.md" ".claude/skills/prompt-helper-optimizer/SKILL.md"`
Telemetry: private task-state rows; global aggregation deferred to root.

1 high, 6 medium, 0 low author findings; full A-P dispositions below. Registry rebuild skipped (--no-sync). Final acceptance pending.

Modified sections: see each changed-file diff above and JSON changed_files.

| Pass | Disposition and evidence |
|---|---|
| A Correctness | The external optimizer receives the prompt as-is; warning to redact does not prevent credentials/private data from being sent or saved.; The skill labels all attempted actions as completion and stops at 20 tool calls even when authorized work remains possible.; Capability selection runs before the curated Goal it requires exists; the review-mode order is different. |
| B Consistency | The text requires six sections but also omits Relevant agents when none fit. |
| C Formatting | Strict PyYAML6.0.3 parse with duplicate-key rejection, JSON parsing, Python AST checks and Markdown structure scan. |
| D Clarity | Reviewed conditional gates, missing-input paths and example-bearing workflow/eval references. |
| E Optimization | Preserved operative gates; moved only non-executing history and avoided speculative prose rewrites. |
| F Feature/eval gaps | There are no functional evals or canonical trigger cases for review, auto-execution, intent preservation or sensitive input.; Legacy hub tools have no unavailable-tool fallback after inline optimization. |
| G Manifest/wrappers | Compared manifest to final scope and read global wrappers; global write authority remains with root. |
| H Trigger eval | Exploratory author-context prediction: positive 10/10, false-positive 0/10; every query/verdict is bound to description hash. |
| I Collisions | Compared family descriptions and artifact boundaries (code/query/prompt/agent/skill/eval/UI/graphic); semantic ranking withheld under embedding pause. |
| J Length/disclosure | Description 818/1000 characters; body 5412 estimated tokens. Within soft and hard body limits. |
| K Prose terms | Several banned filler terms occur outside code; replace nontechnical wording while preserving named methods. |
| L Hygiene | Full-file byte hygiene scan completed; new/changed Markdown uses LF and one final newline. |
| M Description | Lead purpose, TRIGGER and SKIP clauses retained/strengthened; description is 818 characters. |
| N Routing precision | Concrete whenToUse phrases and real specialist/hub-aware deferrals retained; installed peer descriptions are external evidence only. |
| O Peer edges | Checked family downward/lifecycle handoffs; target changes are owned audits, not peer writes. External reciprocal edits deferred to root. |
| P llms-first | n/a (One-off pasted prompt transformation; codebase prompts route to prompt-deep-optimizer.) |

Read coverage: every source file received full-byte identity/static scanning. Core operational content was read; large historical/reference tables received bounded semantic reading. The JSON distinguishes these evidence levels.

<details><summary>Trigger queries and verdicts</summary>

| Query | Expected | Predicted | Verdict |
|---|---|---|---|
| Improve this short prompt before I paste it into chat. | True | True | pass |
| Use ph to critique a one-off prompt draft. | True | True | pass |
| Run phe on this short exploratory task prompt and carry out the result. | True | True | pass |
| Make this vague one-off instruction agent-ready. | True | True | pass |
| Strengthen this three-sentence prompt for a single meeting summary. | True | True | pass |
| Rubber-duck this short prompt with me. | True | True | pass |
| Rewrite this prompt for one immediate chat session. | True | True | pass |
| Interpret this raw request and turn it into a focused instruction. | True | True | pass |
| Recommend an algorithm for improving this exploratory prompt draft. | True | True | pass |
| Review this one-off prompt without executing it. | True | True | pass |
| Optimize the production system prompt in src/prompts/support.ts. | False | False | pass |
| Run a multi-pass iterative audit on this long 2000-token prompt. | False | False | pass |
| Teach me how OPRO and MIPROv2 work. | False | False | pass |
| Find an existing saved prompt in the library. | False | False | pass |
| Optimize this MongoDB aggregation query. | False | False | pass |
| Audit and repair this SKILL.md. | False | False | pass |
| Review a whole Claude Code subagent definition file. | False | False | pass |
| Refactor the code that builds our LLM request. | False | False | pass |
| Tune this SQL query and its indexes. | False | False | pass |
| Plan and execute a whole repository task without improving any prompt. | False | False | pass |

</details>

No target skill was executed. Measured behavior, provider invocation, live UI/database/backtest operations and final blind acceptance are not claimed.


Bounded repair round: final source `36f2a59d4c03a2353bb2a2752f096940066a7ef72f4b6297faf2914ac2b8ddfc`; final fresh recheck pending. See [repair-receipt.md](repair-receipt.md). Prior author-pass zero counts are historical; the independent findings and current operator action are retained in the repair receipt.
