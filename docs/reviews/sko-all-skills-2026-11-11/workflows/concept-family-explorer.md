# /sko concept-family-explorer — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 7 | 1 | applied scoped repairs |
| 2 | 0 | 0 | 1 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 1 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| J | Historical frontmatter and a ~9.2k-token body obstruct progressive disclosure. (`frontmatter metadata.changelog; Evidence required before publication; Steps 9-9d`) | Medium | Retain complete historical/evidence/finalization text in references with mandatory reads; keep safety and budget decisions visible. |
| A | Retired local-tree fallback and website-skip claim contradict /dr mandatory completion. (`Step 2 local fallback; Step 6 website skip; Step 9d description`) | Medium | Use the current hub tree fallback and retain per-concept completion plus final placement refresh. |
| A | The fixed deep-lane claim and fixed 5-concept authority floor contradict /dr depth-specific contracts. (`Step 6 research lane and failure authority description`) | Medium | Delegate defaults and source/claim floors to /dr; retain existing no-override rule. |
| M | The long scope preamble hides the trigger clause. (`SKILL.md frontmatter description: TRIGGER clause follows more than 400 characters at baseline`) | Medium | Front-load distinct user phrasings while preserving scope and all deferral topics. |
| A | The entrypoint forbids a missing concept-tree MCP while Step 2 documents a local fallback. (`When not to use vs Step 2 local fallback`) | Medium | Allow the current local inventory fallback and explicitly avoid unavailable MCP calls. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/concept-family-explorer/SKILL.md
@@ -1,9 +1,11 @@
 ---
 description: >-
-  Gap-discovery layer ABOVE /dr: map a subject's full conceptual family (parent domain, siblings, sub-concepts, adjacent/cross-over fields, frontier), surface useful/novel concepts you're MISSING, score each via the da-* skills, then loop /dr on every viable gap until the concept tree saturates; finishes with skill-optimizer + prompt-deep-optimizer, a skill-tree-architect rebalance, and a sync to the site + ~/.global-ai-hub concept trees. TRIGGER: 'what am I missing about X', 'map the concept space/family of X', 'find adjacent/sibling concepts to X', 'what skills should I build around X', 'saturate/complete my coverage of X', 'expand my concept tree for X'. SKIP: researching a topic you ALREADY named → /dr; cited web report with no skill-building → deep-research; create ONE skill interactively → skill-creator; audit/improve one existing skill → skill-optimizer; optimize one prompt → phe / prompt-deep-optimizer; reorganize the EXISTING skill tree, no new research → skill-tree-architect.
+  Map a subject's conceptual family, inventory coverage, score missing concepts with CVS, and orchestrate /dr for viable gaps with explicit saturation and persistence gates.
+  TRIGGER: "what am I missing about X", "map the concept space", "find adjacent/sibling concepts", "expand my concept tree to saturation".
+  SKIP: one ordinary topic → dr; exhaustive depth inside one concept → rabbithole; cited report only → deep-research; create one skill interactively → skill-creator; skill audit → skill-optimizer; prompt optimization → prompt-helper-optimizer / prompt-deep-optimizer; reorganize existing tree → skill-tree-architect.
 name: concept-family-explorer
-version: "1.14.0"
-updated: "2026-11-06"
+version: "1.15.0"
+updated: "2026-11-11"
 model: claude-sonnet-5-5
 effort: max
 category: meta
@@ -28,19 +30,6 @@
   - da-analytical-methods
   - da-applied-and-communication
   - prompt-helper-optimizer
-metadata:
-  delta: "1.13.1 to 1.14.0: add per-concept landing receipts (scripts/landing_receipts.py) and a final receipt table. 1.13.0 to 1.13.1: preserve the concept purpose summary by placing evidence instructions after the overview and routing."
-  changelog: |
-    2026-10-29 v1.12.0 — consume validated research-scout handoffs before family discovery and /dr dispatch; preserve CVS, evidence and saturation gates
-    2026-10-20 v1.11.0 — research lane is two Sonnet 5.5 `max` passes per concept merged by `dr_run.py research` (frontmatter model/effort moved from Opus xhigh to Sonnet max); Step 6 says not to override it; basis: llms-explorer docs/research/dr-model-repeats-2026-10-20 (one Sonnet max run ≈ one Fable max run in both judge directions at 55 % of the price)
-    2026-10-02 v1.10.0 — remove default concept-count cap; research the full run-start queue in source-sharing cohorts of up to eight concepts, inherit parent evidence, preserve child-only deltas, and keep per-concept authority checks; explicit maxConcepts remains an opt-in user budget
-      2026-09-18 v1.9.1 — align with /dr v3 (dr_run.py finish already writes the hub tree; website tree is Phase 3 step 1b for standalone runs, skipped when dispatched by this skill)
-    2026-09-18 v1.9.0 — new Step 9d: sync the run into BOTH file concept trees (website `concept-tree/tree.json` → `site/src/data/tree.json`, and `~/.global-ai-hub/concept-tree/tree.json`) after the 9b rebalance; merge-only via scripts/sync_trees.py (dry-run default, shrink/validate guards, refuses site writes on main); runs on BUDGET_EXHAUSTED/SATURATION-DISSENT too; procedure in references/tree-sync.md
-    2026-07-20 v1.8.1 — gate-dissent remediation (5 Medium, loop exit at cap 5): SATURATION-DISSENT post-exit contract (9–9c run; unresearched gaps listed); resume ask now triggers on ANY non-complete status; warm-start inheritance gated on prior CVS < current threshold; Step 6 pre-dispatch GAP recheck clause (cites reference §Dedup); failure-handling paragraph compressed to pointer (run-state-and-resume normative)
-    2026-07-20 v1.8.0 — blind-audit iter-2 (6 Medium fixed): worked trace brought above the 5-per-neighborhood floor with formula-correct new-information rates (0/26) + hub no-op note; queue→failed write point added (resume + budget counter honesty); coverage-terminal category widened to decision-SKIP incl. hard-gated; status "optimizing:budget" variant (budget resume re-enters 9c only, never un-skips owed 9/9b); Step 2 tree bullet compressed to rules+pointer; exit-status header exempts LOCK-HELD from telemetry, dissent row notes no-rounds-left immediate exit
-    2026-07-20 v1.7.0 — blind-audit convergence pass (15 Medium fixed): BUDGET_EXHAUSTED path defined (skip 9/9b as owed work, 9c+10 always run); repo-persistence steps 5–7 given their Step 9c slot; blind-gate dead-end → SATURATION-DISSENT when maxRounds exhausted; failed gaps count as coverage-terminal; resume branch for Steps 9–9c interruption (status "optimizing"); dryRun CQ write now lock-checked; LOCK-HELD writes no telemetry row; SKIPPED-PRIOR moved to rationale (decision stays SKIP for cvs_check); "parent subject" slug-prefix rule; rubric example row relabeled alias-missed dup; Step 9 mechanics extracted to references/optimization-pass.md (token budget); lock spec de-duplicated (run-state-and-resume normative); Step 8 bullets compressed to condition+status+pointer
-    2026-07-20 v1.6.0 — 20-improvement pass: run lock cfe-<subject-slug>.lock (2h stale-steal, LOCK-HELD, dryRun exempt); subject-slug derivation rule unifies checkpoint/lock/CQ paths (<family> alias retired); exit-status vocabulary + telemetry mapping; hub local-sources copy regenerated from this content (was stale v2); manifest description/version parity (category stays custom — registry enum); model/effort frontmatter; skill-tree-architect SKIP edge; Workflow-availability fallback + concurrency decision rule (Step 6); per-return persistence timing fixed; dryRun side-effect contract; CQ append-only rule (Step 7); warm-start "inventory changed" rule; local-fallback confidence labeling (Step 2); budget-used line mandated in report; diagram redrawn to full flow; trace + frontier-header + Step 9c fragment fixes; rubric example ranked with semantic-layer CVS 3.20 gate demo
-    2026-06-15 v1.5.0 — sko + user request: Step 6 now MANDATES parallel fan-out (agents or a Workflow) over selected gaps with serialized batch persist/sync, never strictly sequential (CFE-6); report template extracted to references/report-template.md (CFE-2/J); "strong hit" GAP/HAVE gate defined (CFE-3/D); Step 2 pagination/alias dedup vs saturation-and-loop-control.md (CFE-4/E); batch sync relocated to its own Step 9c after 9b (CFE-5/B); dryRun writes no resume checkpoint (CFE-1/F); Pass H 10/10 pos, 0/10 false-pos (predicted)
 whenToUse:
   - "what concepts am I missing about <subject>"
   - "map the conceptual family / concept space of <subject>"
@@ -56,12 +45,23 @@
   - "an existing skill just needs a quality audit (use skill-optimizer)"
   - "optimize a single prompt (use phe or prompt-deep-optimizer)"
   - "reorganize, re-file, or rebalance the existing skill tree with no new research (use skill-tree-architect)"
-  - "neither web research nor the concept-tree MCP is available — the loop cannot verify coverage or saturate"
+  - "neither readable source evidence nor a usable current inventory is available — report the access gaps"
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # Concept Family Explorer

 Given subject, find useful/relevant/novel/interesting concepts in its conceptual family **currently missing** from skill library and concept tree, fill worthwhile ones to saturation via `/dr`, finish by optimizing every changed skill.
+
+## Look for llms files first
+
+Before reading the subject family and coverage stores raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Routing detail

@@ -90,53 +90,12 @@
 - One skill from scratch, interactive → `skill-creator`.
 - Existing skill needs quality audit → `skill-optimizer`.
 - Skill tree needs reorganizing, re-filing, or rebalancing with no new research → `skill-tree-architect`.
-- No web research or concept-tree MCP → say so, stop; loop can't verify coverage or saturate without at least one.
+- If neither readable source evidence nor a usable current inventory is available, report the access gaps and stop. A missing MCP alone does not forbid the documented local fallback.
 - Want llms-family packs (llms.txt/-full/-small/-facts/-vocabulary) + a categorical rollup + indexes built on top of this gap map, not just the map itself → llms-txt-tooling (references/full-suite.md).

 ## Evidence required before publication

-Apply this contract to every factual assertion, including summaries, inherited parent
-facts, disagreements, open-question premises and final dossiers. Discovery leads and
-coverage labels do not establish support.
-
-- Keep each atomic claim's exact statement, immutable claim ID, source URL, source
-  snapshot hash, exact quoted passage and locator together. For v4, author an `evidence`
-  list of spans with `url`, `source_id`, `snapshot_sha256`, `start`, `end`, `quote` and
-  `extraction_status: complete`. Mark complete only after reading a usable source;
... truncated; complete final bytes and hashes are bound in the JSON receipt.
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/concept-family-explorer/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "concept-family-explorer",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "full-queue",
+      "prompt": "Map RAG evaluation and fill every worthwhile gap. I did not set a concept count budget.",
+      "expected_output": "Inventory aliases, score all gaps and process the complete viable queue in bounded cohorts; apply no default concept-count truncation.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "no-default-cap",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "no default concept-count cap",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "gap-recheck",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Re-confirm each concept is still GAP immediately before",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "budget-persist",
+      "prompt": "The wall-clock budget just expired while two /dr concepts returned.",
+      "expected_output": "Drain every in-flight persistence, list optimization/rebalance as owed, and still run final sync/report; do not call this saturation.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "inflight-persist",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "every in-flight `/dr` run",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "budget-finalize",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "references/finalization.md",
+            "regex": "BUDGET_EXHAUSTED",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/evals/trigger-eval.json
+++ .claude/skills/concept-family-explorer/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "What am I missing about prompt-optimization algorithms?",
+    "should_trigger": true
+  },
+  {
+    "query": "Map the concept space of data observability",
+    "should_trigger": true
+  },
+  {
+    "query": "Find adjacent and sibling concepts to MongoDB performance tuning",
+    "should_trigger": true
+  },
+  {
+    "query": "What skills should I build around Kubernetes?",
+    "should_trigger": true
+  },
+  {
+    "query": "Saturate my coverage of RAG techniques — fill every worthwhile gap",
+    "should_trigger": true
+  },
+  {
+    "query": "Expand my concept tree for LLM evaluation to saturation",
+    "should_trigger": true
+  },
+  {
+    "query": "Explore the conceptual neighborhood of streaming data architectures",
+    "should_trigger": true
+  },
+  {
+    "query": "I've got a few MongoDB skills — what concepts am I missing across that family?",
+    "should_trigger": true
+  },
+  {
+    "query": "Map the conceptual neighborhood of data observability and build out whatever's worth building",
+    "should_trigger": true
+  },
+  {
+    "query": "Is my prompt-engineering knowledge complete, and if not, fill it",
+    "should_trigger": true
+  },
+  {
+    "query": "Research RAFT consensus and make a skill",
+    "should_trigger": false
+  },
+  {
+    "query": "Write me a cited report on the vector-DB market",
+    "should_trigger": false
+  },
+  {
+    "query": "My da-7 skill triggers badly, fix it",
+    "should_trigger": false
+  },
+  {
+    "query": "Optimize this system prompt",
+    "should_trigger": false
+  },
+  {
+    "query": "Create one new skill for Jira workflows, interactively",
+    "should_trigger": false
+  },
+  {
+    "query": "Research the current state of nuclear fusion energy",
+    "should_trigger": false
+  },
+  {
+    "query": "How should I plan my research on LLMs?",
+    "should_trigger": false
+  },
+  {
+    "query": "Rebalance the whole skill tree — are any hubs over the description cap?",
+    "should_trigger": false
+  },
+  {
+    "query": "Summarize the article I just pasted",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/concept-family-explorer/references/CHANGELOG.md
@@ -0,0 +1,16 @@
+# Changelog
+
+2026-11-11 sko v1.14.0->v1.15.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 7 Medium findings fixed in reviewed scope; global sync and blind review deferred.
+
+delta: 1.13.1 to 1.14.0: add per-concept landing receipts (scripts/landing_receipts.py) and a final receipt table. 1.13.0 to 1.13.1: preserve the concept purpose summary by placing evidence instructions after the overview and routing.
+
+2026-10-29 v1.12.0 — consume validated research-scout handoffs before family discovery and /dr dispatch; preserve CVS, evidence and saturation gates
+2026-10-20 v1.11.0 — research lane is two Sonnet 5.5 `max` passes per concept merged by `dr_run.py research` (frontmatter model/effort moved from Opus xhigh to Sonnet max); Step 6 says not to override it; basis: llms-explorer docs/research/dr-model-repeats-2026-10-20 (one Sonnet max run ≈ one Fable max run in both judge directions at 55 % of the price)
+2026-10-02 v1.10.0 — remove default concept-count cap; research the full run-start queue in source-sharing cohorts of up to eight concepts, inherit parent evidence, preserve child-only deltas, and keep per-concept authority checks; explicit maxConcepts remains an opt-in user budget
+  2026-09-18 v1.9.1 — align with /dr v3 (dr_run.py finish already writes the hub tree; website tree is Phase 3 step 1b for standalone runs, skipped when dispatched by this skill)
+2026-09-18 v1.9.0 — new Step 9d: sync the run into BOTH file concept trees (website `concept-tree/tree.json` → `site/src/data/tree.json`, and `~/.global-ai-hub/concept-tree/tree.json`) after the 9b rebalance; merge-only via scripts/sync_trees.py (dry-run default, shrink/validate guards, refuses site writes on main); runs on BUDGET_EXHAUSTED/SATURATION-DISSENT too; procedure in references/tree-sync.md
+2026-07-20 v1.8.1 — gate-dissent remediation (5 Medium, loop exit at cap 5): SATURATION-DISSENT post-exit contract (9–9c run; unresearched gaps listed); resume ask now triggers on ANY non-complete status; warm-start inheritance gated on prior CVS < current threshold; Step 6 pre-dispatch GAP recheck clause (cites reference §Dedup); failure-handling paragraph compressed to pointer (run-state-and-resume normative)
+2026-07-20 v1.8.0 — blind-audit iter-2 (6 Medium fixed): worked trace brought above the 5-per-neighborhood floor with formula-correct new-information rates (0/26) + hub no-op note; queue→failed write point added (resume + budget counter honesty); coverage-terminal category widened to decision-SKIP incl. hard-gated; status "optimizing:budget" variant (budget resume re-enters 9c only, never un-skips owed 9/9b); Step 2 tree bullet compressed to rules+pointer; exit-status header exempts LOCK-HELD from telemetry, dissent row notes no-rounds-left immediate exit
+2026-07-20 v1.7.0 — blind-audit convergence pass (15 Medium fixed): BUDGET_EXHAUSTED path defined (skip 9/9b as owed work, 9c+10 always run); repo-persistence steps 5–7 given their Step 9c slot; blind-gate dead-end → SATURATION-DISSENT when maxRounds exhausted; failed gaps count as coverage-terminal; resume branch for Steps 9–9c interruption (status "optimizing"); dryRun CQ write now lock-checked; LOCK-HELD writes no telemetry row; SKIPPED-PRIOR moved to rationale (decision stays SKIP for cvs_check); "parent subject" slug-prefix rule; rubric example row relabeled alias-missed dup; Step 9 mechanics extracted to references/optimization-pass.md (token budget); lock spec de-duplicated (run-state-and-resume normative); Step 8 bullets compressed to condition+status+pointer
+2026-07-20 v1.6.0 — 20-improvement pass: run lock cfe-<subject-slug>.lock (2h stale-steal, LOCK-HELD, dryRun exempt); subject-slug derivation rule unifies checkpoint/lock/CQ paths (<family> alias retired); exit-status vocabulary + telemetry mapping; hub local-sources copy regenerated from this content (was stale v2); manifest description/version parity (category stays custom — registry enum); model/effort frontmatter; skill-tree-architect SKIP edge; Workflow-availability fallback + concurrency decision rule (Step 6); per-return persistence timing fixed; dryRun side-effect contract; CQ append-only rule (Step 7); warm-start "inventory changed" rule; local-fallback confidence labeling (Step 2); budget-used line mandated in report; diagram redrawn to full flow; trace + frontier-header + Step 9c fragment fixes; rubric example ranked with semantic-layer CVS 3.20 gate demo
+2026-06-15 v1.5.0 — sko + user request: Step 6 now MANDATES parallel fan-out (agents or a Workflow) over selected gaps with serialized batch persist/sync, never strictly sequential (CFE-6); report template extracted to references/report-template.md (CFE-2/J); "strong hit" GAP/HAVE gate defined (CFE-3/D); Step 2 pagination/alias dedup vs saturation-and-loop-control.md (CFE-4/E); batch sync relocated to its own Step 9c after 9b (CFE-5/B); dryRun writes no resume checkpoint (CFE-1/F); Pass H 10/10 pos, 0/10 false-pos (predicted)
```

```diff
--- baseline/references/finalization.md
+++ .claude/skills/concept-family-explorer/references/finalization.md
@@ -0,0 +1,30 @@
+# Finalization procedures (Steps 9-9d)
+
+Read this file in full before entering Step 9 (or Step 9c on a budget exit). These are the complete operative steps extracted from the entrypoint.
+
+### Step 9 — Optimize the resulting skills (spokes AND their hubs)
+
+User asked to run optimizers on results. `/dr` may have optimized each skill individually as it built it; your job is **consolidated pass over everything that changed this run**, which also catches cross-skill trigger collisions in newly-expanded family:
+
+1. **Spokes** — check certification first: spoke is **CERTIFIED** when a `skill-optimizer` run this session exited CLEAN (via `/dr` Phase 2 step 4, or the install-write PostToolUse hook; same-day `exit_status: CLEAN` telemetry row corroborates). Certified ⇒ `/sko <id> --meta --no-sync` only (`--eval` only if collision suspected); uncertified ⇒ full `/sko <skill-id> --no-sync`. **Never stack a third full content pass; never use `--max-iter=1` as the skip.** Evidence rules, hook-path nuances, flag rationale: `references/optimization-pass.md`.
+2. **Hubs** — distinct set of hubs that gained a spoke this run (new spoke's `parentConcept` node → its `skillId`), deduped (hub gaining N spokes optimized **once**); run `/sko <hub-id> --no-sync` on each **after** spokes, always a **full** loop — mid-run hub audits saw only a partial family, and spoke-side Pass O seeds the deferral edge but never re-audits the hub's own card (description/keywords, TRIGGER/SKIP routing, collision vs new spokes, description budget). Scope: changed hub's own card only — whole-tree shape is Step 9b. Full rationale: `references/optimization-pass.md`.
+3. For **prompt artifacts**, two cases: standalone saved prompts from `/dr` get full `prompt-deep-optimizer` run (`/pdo`); prompt blocks **embedded** in new/updated skill already covered inside owning item-1 `sko` run via bounded pass-bundle dispatch — per `references/shared/convergence-and-severity.md` §Composed artifacts ("Never run a second nested convergence loop"). Skip this item when no prompt artifact exists — say so rather than inventing work.
+4. **Sync and re-verify deferred to Step 9c** — must run *after* Step 9b rebalance (which can re-file or fold skills), so not part of this step.
+
+### Step 9b — Rebalance the tree (skill-tree-architect)
+
+Saturating run can add whole new sub-family, push a hub past the 1000-character description cap, or land new skills under wrong hub — so after per-skill pass, invoke **`skill-tree-architect`** once over whole `~/.claude/skills` tree. It runs read-only analysis (`audit-placement.mjs`, `detect-candidates.mjs`, `meta-validate.mjs` sweep) and surfaces ranked rebalance plan — new-family / split-over-cap-hub / re-file-misplaced-spoke / hub-homeless. Apply only zero-risk idempotent repairs; surface folding, splits, and registry sync for review (`~/.claude/skills` not git-backed). Same delegation rule as Step 9: you orchestrate whole-tree shape; skill-tree-architect owns it. If rebalance re-filed or folded any skill researched this run, re-run tree write (`tam_concept_tree_upsert` with new parent + `tam_concept_tree_link`) so tree parentage matches final placement — tree write happens BEFORE 9b and goes stale the moment a spoke moves. (That covers the mdb-context-hub tree only; the two file trees are written once, after 9b, in Step 9d.)
+
+### Step 9c — One batch sync, then re-verify
+
+Every per-spoke and per-hub `sko` run in Step 9 invoked with `--no-sync` (sko's "When driven by an outer loop" rule), and `--no-sync` withholds Pass O peer re-syncs — so run this **after** Step 9b (its rebalance can re-file or fold skills, resulting tree write must be captured): perform ONE batch sync — `/sync-skills`, `npm run sync:skills` in repo-native path, or Step 6b's `persist-spoke.mjs <last-id> --sync` form; all three are whole-pack/registry syncs covering spokes, hubs, and any touched peers. Repo-native: follow the sync with repo-persistence steps 6–7 (`referents.mjs --repair` dry-run then `--apply`; workflow log + version bump). Then re-verify each optimized skill — **spoke and hub** — findable via `tam_search_skills`. Runs on the `BUDGET_EXHAUSTED` path too (Step 8) — persistence completeness is never budget-gated.
+
+### Step 9d — Sync the website and global-ai-hub concept trees
+
+`/dr` (v3: `dr_run.py finish`) writes each concept's node into the hub tree as it finishes, and Step 6b the mdb-context-hub tree (`tam_concept_tree_*`, where that MCP exists) — and its mandatory completion refreshes generated website content; Step 9d refreshes final placement after the 9b rebalance. Two file trees must end the run consistent — merge into both **after** 9b so parentage is final placement:
+
+- **global-ai-hub** — `~/.global-ai-hub/concept-tree/tree.json` (the runtime tree the hub MCP `hub_concept_*` tools, TUI, and `hub_concept_frontier` read).
+- **website** — `<llms-explorer>/concept-tree/tree.json`, then `--regen` rebuilds `site/src/data/tree.json` (+ reader pages under `site/src/data/concepts/` when a concept pack exists).
+
+Build one spec from run-state `researched[]`, plus a `scores` map of every scored row (skips included) so the Concept Viability Score is stored with each concept (+ `queue`: above-threshold gaps left unresearched on `BUDGET_EXHAUSTED` / `SATURATION-DISSENT`; below-threshold skips are never queued), run `scripts/sync_trees.py` dry first, then `--apply --regen` against a llms-explorer **branch/worktree** (helper refuses `main`). It is **merge-only** — never copy one tree over the other (that has clobbered the site tree 3×); it backs up, refuses to shrink a tree or add a structural validate problem, and re-running is a no-op. One target refusing does not abort the run or change the verdict — record it in the report. `dryRun` prints the helper's dry-run plan only. Spec format, verification (`concept_tree.py show`, the CI `gen_tree.py` diff, site tests) and commit rules: `references/tree-sync.md`. Checkpoint: nothing extra — idempotent, so resume just re-runs it.
+
```

```diff
--- baseline/references/research-evidence.md
+++ .claude/skills/concept-family-explorer/references/research-evidence.md
@@ -0,0 +1,44 @@
+## Evidence required before publication
+
+Apply this contract to every factual assertion, including summaries, inherited parent
+facts, disagreements, open-question premises and final dossiers. Discovery leads and
+coverage labels do not establish support.
+
+- Keep each atomic claim's exact statement, immutable claim ID, source URL, source
+  snapshot hash, exact quoted passage and locator together. For v4, author an `evidence`
+  list of spans with `url`, `source_id`, `snapshot_sha256`, `start`, `end`, `quote` and
+  `extraction_status: complete`. Mark complete only after reading a usable source;
+  the attestation never overrides a missing identifier or invalid span. Read the snapshot;
+  a URL, reference list, cache hash or model recollection supplies no evidence credit.
+- Run deterministic integrity checks over **all** claims before paid semantic review.
+  Require each quote to exist in the pinned body and belong to the cited source.
+  Check exact technical identifiers, values, units and applicability against the
+  passage. Missing identifiers or an incomplete Markdown derivative require readable
+  rendered HTML, original RST/source or another complete primary source; withhold the
+  assertion until reacquisition succeeds. A keyword match alone does not prove support.
+- A semantic judge decides whether the passage supports the complete assertion,
+  including negation, version, scope and caveats. It cannot override a failed integrity
+  check. In research-gate/v4, review every new or changed factual assertion once.
+  Reuse a prior validated SUPPORTED verdict only when the exact assertion and bound
+  source snapshots are unchanged. Structural binding alone cannot qualify publication.
+  Do not turn structural failures into expensive blanket multi-model reruns.
+- Preserve contradictory claims with both source passages and their applicability.
+  Record the conflict explicitly and block an unconditional conclusion. Resolve it
+  with source evidence or publish only an accurately scoped, qualified conflict.
+  Never average opposing claims, silently choose the preferred source, lower confidence
+  to bypass a failure, or treat absence from an incomplete extract as proof of absence.
+- Build prose and every persisted projection from canonical claim records. Validate
+  citation and evidence bindings through concept packs, reader JSON, context and facts
+  downloads before completion. Missing bindings or changed assertions stop publication;
+  a dossier or tree update alone cannot bypass the shared /dr completion gate.
+- Repair only failed claim/source pairs. Keep successful claims, snapshots and paid
+  attempts. Allow one bounded evidence repair followed by a fresh bound gate; residual
+  substantive dissent stops that claim. An unchanged failed evidence packet must not
+  incur another paid judgment; one malformed-JSON repair is allowed. Retry recognized
+  transport failures at most twice within the original deadline. Do not repeat discovery, whole-family research
+  or successful website generation to repair a citation.
+- Before shipping changes to this workflow, exercise real failure regressions:
+  uncited claims, wrong-source quotes, incomplete derivatives, missing field names,
+  negation or version conflicts, stale snapshot hashes and dropped output citations.
+  Verify canonical, installed and runtime-specific skill copies with their sync check;
+  equal version numbers alone do not establish parity. Report loaded state separately.
```

```diff
--- baseline/references/tree-sync.md
+++ .claude/skills/concept-family-explorer/references/tree-sync.md
@@ -6,7 +6,7 @@

 ## Why a separate stage

-A run touches **three** tree surfaces; `/dr` covers the first (and the hub file node as it finishes), but nothing writes the website file or corrects parentage after the 9b rebalance:
+A run touches **three** tree surfaces; `/dr` covers the first (and the hub file node as it finishes), and its completion hook refreshes website content; Step 9d corrects final parentage after the 9b rebalance:

 | Surface | Written by | Where |
 | --- | --- | --- |
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 10; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/concept-family-explorer/SKILL.md | canonical (explicit repository target) | fffdbc514198 | audited and changed in isolated worktree | d04c446d954a |
| $HOME/.claude/skills/concept-family-explorer/SKILL.md | installed copy | 7566929f8f4c | report only; preserve divergence; root-coordinated ownership review | 7566929f8f4c |
| $HOME/.global-ai-hub/skills/concept-family-explorer/SKILL.md | installed copy | 7566929f8f4c | report only; preserve divergence; root-coordinated ownership review | 7566929f8f4c |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| concept-family-explorer | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-sonnet-5-5 · effort: max (tier: mid (preserved explicit researcher role); caller constraint to preserve explicit research model/effort). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/concept-family-explorer/baseline/SKILL.md" ".claude/skills/concept-family-explorer/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

7 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

Modified sections: frontmatter routing/model/version metadata; Look for llms files first.

A-P dispositions:

| Pass | Disposition |
|---|---|
| A | Reviewed entrypoint correctness and operative supporting files; fixed anchored contradictions/broken pointers. Large unchanged reference facts are not independently revalidated. |
| B | Reviewed claimed scope, stage ordering and output promises; preserved research evidence/budget/STOP boundaries. |
| C | Strict YAML parsed with duplicate-key rejection; checked target-local introduced links and hub table file existence. |
| D | Reviewed procedural clarity and concrete examples; retained domain terms and source-qualified claims. |
| E | Applied only scoped routing/progressive-disclosure repairs; retained author workflow and purpose. |
| F | Created three realistic functional scenario cases; static instruction-contract checks ran at 6/6. Scenario outputs were not executed. |
| G | Manifest parsed, version/date updated, advisory model provenance recorded; no claim that prior model IDs are invalid. |
| H | 20-query corpus replay/generated first, projection derived afterward; author predictions 10/10 positive, 0/10 false positives. No measured activation. |
| I | Local keyword/referrer discovery and explicit peer boundaries reviewed. Global semantic ranking/collision rates remain unverified because services are paused. |
| J | Description 623 characters; body estimate 7392 tokens. Soft overage justified: active evidence, budgets, resume/fan-out and completion gates remain load-bearing; hard ceiling not crossed. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: references/optimization-pass.md, references/repo-persistence.md, references/report-template.md, references/run-state-and-resume.md, references/saturation-and-loop-control.md, references/scoring-rubric.md, references/tree-sync.md, references/research-evidence.md, references/finalization.md.
Unread supporting files: references/shared/convergence-and-severity.md, references/shared/cross-model-gate.md, scripts/landing_receipts.py, scripts/sync_trees.py.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| retired-local-tree-removed | false | true | static instruction check |
| per-concept-site-completion-preserved | false | true | static instruction check |
| depth-authority-contract | false | true | static instruction check |
| MCP-fallback-allowed | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| What am I missing about prompt-optimization algorithms? | trigger | trigger | true |
| Map the concept space of data observability | trigger | trigger | true |
| Find adjacent and sibling concepts to MongoDB performance tuning | trigger | trigger | true |
| What skills should I build around Kubernetes? | trigger | trigger | true |
| Saturate my coverage of RAG techniques — fill every worthwhile gap | trigger | trigger | true |
| Expand my concept tree for LLM evaluation to saturation | trigger | trigger | true |
| Explore the conceptual neighborhood of streaming data architectures | trigger | trigger | true |
| I've got a few MongoDB skills — what concepts am I missing across that family? | trigger | trigger | true |
| Map the conceptual neighborhood of data observability and build out whatever's worth building | trigger | trigger | true |
| Is my prompt-engineering knowledge complete, and if not, fill it | trigger | trigger | true |
| Research RAFT consensus and make a skill | skip | skip | true |
| Write me a cited report on the vector-DB market | skip | skip | true |
| My da-7 skill triggers badly, fix it | skip | skip | true |
| Optimize this system prompt | skip | skip | true |
| Create one new skill for Jira workflows, interactively | skip | skip | true |
| Research the current state of nuclear fusion energy | skip | skip | true |
| How should I plan my research on LLMs? | skip | skip | true |
| Rebalance the whole skill tree — are any hubs over the description cap? | skip | skip | true |
| Summarize the article I just pasted | skip | skip | true |
| Audit my deep-research skill for production quality | skip | skip | true |

</details>
