# skill-optimizer — final scoped SKO receipt

The source audit is complete with operational DEGRADED status. Raw bounded dissent
and subsequent focused corrections remain separate in the [final ledger](../final-report.json).

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
|1|1|6|0|Author findings collected and scoped fixes applied|
|2|0|0|not tallied|Author verification; independent gates followed|

Hygiene: final changed-line check passes; reference Nits remain visible in the raw review.
Pre-lint: author evidence retained privately; final strict PyYAML/caps/corpus checks pass.

| Pass | Finding | Level | Action |
|---|---|---|---|
|A|Copy-overwrite promises conflicted with the newer ownership rail.|High|Selected-source resolution, active-shadow classification and synchronization rules now preserve independently owned sources.|
|A|All provider targets inherited a Claude-only model resolver.|Medium|Model advice now matches the target runtime.|
|A|User-level corpus writes were mandatory for repository-only runs.|Medium|Scoped source corpora preserve and replay user history without modifying it.|
|A|Registry rebuild rules ignored an existing service pause.|Medium|Pause and scope gates now take precedence.|
|F|Eval6 rewarded unauthorized overwrite of a newer independent source.|Medium|Corrected the unsafe expectation and retained its baseline in recovery.|
|P|The llms-first section ordered map reads before available source code.|Medium|Applied the size-first and source-authority section.|
|G|Shared champion contract referenced absent evidence dependencies.|Medium|Included complete verified evidence contract and helper locally.|
|F/H|History growth prevented a balanced audit projection|Medium|Focused history-safe projector and6 regression methods; source history unchanged|

eval: predicted (independent frontmatter reader; no activation harness).

| Metric | Result | Target | Pass? |
|---|---|---|---|
|Should trigger|10/10|≥9/10|yes|
|False positives|1/10|≤1/10|yes|

Unified diff previews below cover this source's final write set, capped at80 lines per file.

````diff
--- baseline/.claude/skills/skill-optimizer/SKILL.md
+++ .claude/skills/skill-optimizer/SKILL.md
@@ -1,7 +1,7 @@
 ---
 name: skill-optimizer
 description: >-
-  Audit and improve a Claude Code skill to production quality: convergence-loop quality gate, Medium+ fixes, trigger and behavior evals on every run (missing ones created), peer-deferral edges, sync of every copy to the accessed one, hub registry rebuild.
+  Audit and improve a skill: run a convergence loop, fix Medium+ findings, add and grade trigger and behavior evals, and check peer routing. Discover copies; synchronize owned destinations only within the requested scope. Rebuild the hub registry when permitted.
   TRIGGER: "optimize skill", "audit skill", "run sko", "skill trigger accuracy", "skill too long", "fix skill", "skill collision check", "check my /command wrapper for drift", "add missing evals", "sync skill copies". `--meta` does wiring/registry/validation only: "register skill to the hub", "validate placement/folder/manifest", "wire up peer deferral edges". `--read-only` audits without writing.
   SKIP: non-skill prompt files → prompt-deep-optimizer / phe; new skill from scratch → skill-creator; prose-only edits → writing-expert; deep eval suite optimization → deep-eval-optimizer / deo; MCP tool audits → ai-mcp-sdk-prompting; whole-TREE rebalance → skill-tree-architect; freshness → skill-refresher.
 whenToUse:
@@ -23,10 +23,10 @@
   - "add appropriate evals to a skill missing them"
   - "make every copy of this skill identical to the one Claude loads"
   - "add the look-for-llms-files-first section to this skill"
-version: 2.24.1
+version: 2.25.0
 category: meta
-updated: "2026-11-06"
-model: claude-opus-5
+updated: "2026-11-11"
+model: claude-opus-5-5
 effort: xhigh
 triggers:
   - sko
@@ -77,17 +77,18 @@
 ---
 # Skill Optimizer

-Audit + rewrite Claude Code skill til pass measurable quality bar. Reads `SKILL.md` (or legacy `context.md` + `manifest.yaml`), runs 16 analytical passes (A–P, defined in `references/passes.md`) inside convergence loop (≤3 iterations, extendable to 5 per canonical contract; configurable via `--max-iter`), fixes all Medium+ findings (`--read-only`: reports them, writes nothing), ensures appropriate evals exist by creating missing functional test cases (`evals/evals.json`) and trigger evals (`evals/trigger-eval.json`) and runs both every time (no eval results, no clean exit), recommends model + effort skill run under and writes to frontmatter (Step 4.6), seeds reciprocal deferral refs into peer skills (Pass O), verifies post-write state, makes every on-disk copy of the skill identical to the accessed one (Step 6.7), rebuilds hub registry index over target + touched peers.
+Audit a skill against a stated quality bar. Read `SKILL.md` (or legacy `context.md` + `manifest.yaml`), then run the 16 analytical passes A–P in `references/passes.md`. Collect findings before rewriting. The convergence loop defaults to three iterations; the shared contract governs any extension, with `--max-iter` as a hard ceiling. Fix Medium+ findings, add missing evals and report both trigger and behavior results. Recommend runtime-compatible model and effort metadata, verify the candidate, and check peer routing. Discover copies and synchronize only authorized, owned destinations under Step 6.7. Rebuild the registry only when its gates and the session's service permissions allow it. Read-only runs report proposals and write nothing.

 **Registry model.** The hub registry is **derived, not authored**: `~/.global-ai-hub` indexes `~/.claude/skills/*/SKILL.md` (plus its own `skills/` and the plugin cache) into `registry.db` via `semantic_ops.router build`. There is no create/update API call — you write the file, then rebuild the index. Every registry read is `hub_route` (or its CLI form); Step 7 is a rebuild, not a push.

 ## Look for llms files first

-`/sko` works on a skill tree, so it reads the target's llms files before the tree. Follow `references/llms-first-section.md` (the format spec's section 5 and `llms-usage-guidance`).
-1. Look for the target's llms files: `~/.global-ai-hub/skills.llms/<name>.repo/`, its hub's `llms.txt`, and memory-central rows (`python3 ~/.global-ai-hub/scripts/keyword_index.py query "<name>" --prefix ~/.llms --top 5 --mode any --json`).
-2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it. Prefer `llms-facts.txt` and `llms-sitemap.txt`; `llms-small.txt` is a map.
-3. Then read the whole skill tree (Step 1.4). The files on disk are the authority: verify every llms fact against its `path:line` before you act on it.
-4. Index hits are leads. Confirm each with Read.
+Before reading the subject raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
+1. Locate the subject's `llms.txt`, source-qualified concept pack, or relevant documentation index. Existing keyword hits can help locate it.
+2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map.
+4. If you have the repo, search the code before opening an llms file. The code is the authority. Verify each fact against its source `path:line`.
+5. Index and llms hits are leads. Confirm their sources before acting.

 ## When not to use

@@ -136,12 +137,12 @@
 ### Step 1 — Locate skill

 1. Skill ID given? Resolve to `~/.claude/skills/<id>/SKILL.md`, the canonical location. Not there? Try `~/.global-ai-hub/skills/<id>/SKILL.md`, then a folded hub spoke via `~/.claude/skill-consolidation/*-manifest.json`, then the plugin cache (`~/.claude/plugins/cache/*/*/*/skills/<id>/SKILL.md`; indexed by the router, never edited here). **Wrapper resolution:** the argument names a `~/.claude/commands/<arg>.md` file instead (leading `/` optional)? Read it, take the skill it invokes (its `**<id>** skill` line or the `SKILL.md` path it cites) as the target, and keep the wrapper path for Pass G's wrapper-drift check. Skill ID given directly? Still locate its wrappers: `grep -l -e "\*\*<id>\*\*" -e "skills/<id>/" ~/.claude/commands/*.md`.
-2. Claude Code skill path given (`~/.claude/skills/<name>/SKILL.md`)? Treat single file as both context + manifest (frontmatter is manifest).
+2. Explicit skill path given? Resolve that path and follow its repository ownership rules. Treat its `SKILL.md` as both context and manifest. Do not silently redirect an explicitly selected repository source to a same-named installed copy. Inventory other copies separately; a selected source does not authorize overwriting them.
 3. Legacy `context.md` / `manifest.yaml` path given? Derive its companion and optimize the pair. Note in Step 8 that this format is **not indexed**: the router globs `*/SKILL.md` only, so Step 7's rebuild will not surface it.
 4. Read all files in full before any analysis. Only one file readable (e.g., `manifest.yaml` absent)? Proceed w/ available file, note missing companion in Step 8 report.
-5. **Duplicate-copy guard (High).** Before any analysis, list every copy of the target on disk with the command in `references/sync-protocol.md` § Duplicate-copy guard: it deduplicates by real path (a symlinked root such as `~/.claude/skills → ~/.global-ai-hub/skills` yields two paths to one file, not a twin), prunes git worktrees, run backups, and the eval shadow dir, and covers the plugin cache. One real path ⇒ clean. More? Compare their `version` values and report a **High** finding naming every path and version. Optimize the canonical copy (`~/.claude/skills/<id>/SKILL.md`) only; never edit a twin, never merge them. Step 6.7 makes the other copies identical to the canonical one (`references/location-sync.md`); deleting a copy stays with `skill-tree-architect`. This step exists so a run cannot silently optimize one of several copies and report clean. Extra copies differ in kind:
-
-   - **A top-level twin in another indexed root** (a real `~/.global-ai-hub/skills/<id>/` directory, or the plugin cache) competes in the registry: roots are searched hub → `~/.claude/skills` → plugin cache and the first `name` wins, so no amount of rebuilding registers an edit to the shadowed copy. Report the winning root; Step 6.7 syncs the twin from canonical with a backup. Do not hand-edit it. Step 7 records the shadowing and withholds a clean routing verdict while the winning copy differs. See `references/sync-protocol.md` § The shadowing trap.
+5. **Duplicate-copy guard.** Before analysis, list copies with the command in `references/sync-protocol.md`. Deduplicate real paths; classify installed competitors, repository distributions, generated overlays, plugin-managed copies and historical snapshots. Compare versions and hashes. A divergent copy that shadows the selected source in an active index is **High**. An intentional distribution copy is not a collision merely because it exists. Optimize the selected owned source. Step 6.7 records permitted syncs and preserved differences; it never grants ownership or permission to overwrite another source.
+
+   - **A top-level twin in another indexed root** can shadow the selected source. Verify the collector's current root order and report the winning file. Preserve a divergent or independently owned twin unless its synchronization is authorized and its preimage is unchanged. Withhold a clean routing verdict while the indexed source differs. See `references/sync-protocol.md` § The shadowing trap.
    - **A nested `<bucket>/<id>/SKILL.md`** is invisible to both the router (one-level glob) and the Claude Code loader, so it is stale-staging risk rather than live competition. Report, do not panic.
 6. **Registry unavailable fallback.** `global_ai_hub` MCP not connected? Use the CLI for every registry read:

@@ -162,8 +163,8 @@
 1. Record `wc -l` for `SKILL.md` (or `context.md`) + `manifest.yaml`.
 2. Compute SHA-256 of each file, store as `baseline.sha256`; alongside, persist pre-write copy of every file run will modify to `~/.claude/skill-consolidation/backups/<skill>-<YYYYMMDD-HHMMSS>/<filename>` (contract's pre-write snapshot guardrail — central directory, never sibling `.bak` files). Persisted copy makes Step 8's `diff -u baseline current` preview computable, is rollback source. Same run directory holds streaming-checkpoint stub (§ Guardrails, "Streaming checkpoint" in `references/shared/convergence-and-severity.md`) — appended after each pass bundle + each iteration's writes, so crash resumes from last completed step instead of re-running Step 3 from scratch; cite that section for write mechanics.
 3. **Assemble eval suite & audit missing evals.**
-   - **Functional execution evals (`evals/evals.json`):** Check if `<skill-dir>/evals/evals.json` exists. If absent or lacking test cases, flag a **Medium** finding (Pass F) to generate appropriate evals: author at least 2–3 realistic test cases with `id`, `name`, realistic user `prompt`, `expected_output`, `files` (if any), and objectively verifiable `assertions` conforming to standard skill eval schema.
-   - **Trigger-accuracy evals (`evals/trigger-eval.json` / canonical corpus):** Assemble Pass H trigger-eval set per `references/passes.md` (Pass H, step 1). **Canonical corpus** is `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`, the single store of record, carrying every query, verdict, description hash, skill version, and `retired:` marker. Replay it when it exists, fill to the 20-query set w/ fresh queries, persist every query + verdict back to it. If missing, generate the full 20-query set (10 should-trigger, 10 should-not-trigger near-misses). The target's own `<skill-dir>/evals/trigger-eval.json` is a **derived, disposable projection** of that corpus, regenerated from it when missing evals are created or before Pass H runs the measured harness (`run_eval` requires that exact path + shape) — never hand-edited, never read as the source of truth. Disagreement between the two? Canonical wins; overwrite the projection.
+   - **Functional execution evals (`evals/evals.json`):** Check if `<skill-dir>/evals/evals.json` exists. If absent or lacking test cases, flag a **Medium** finding (Pass F) to generate appropriate evals: author at least 2–3 realistic test cases with `id`, `name`, realistic user `prompt`, `expected_output`, `files` (if any), and objectively verifiable `assertions` conforming to the schema and template in `references/eval-gate.md#functional-file-schema`.
+   - **Trigger-accuracy evals:** Resolve the source corpus with `references/corpus-scope.md`, replay existing rows, then add fresh queries to the 10-positive/10-negative audit set. Preserve query history, verdict level, description hash, skill version and retirement markers. Derive `evals/trigger-eval.json` from the selected corpus; never use that disposable projection as the source. Keep user-level corpus files read-only when the requested scope is a repository.
 4. **Offline pre-lint (zero-token).** Run `python3 ~/.claude/scripts/skill_optimizer_offline.py <skill-dir> --json`. Its deterministic findings (frontmatter parse and required keys, duplicate keys, description over the index cap, body token budget, heading hierarchy, table shape, broken links, banned terms) enter iteration 1 as pre-computed evidence for Passes C, G, J, and K at those passes' severities; its prose heuristics (readability, hedges, empty quantifiers) stay Low. Script absent or failing? Record `pre-lint: skipped (<reason>)` and continue; it never blocks. It complements `meta-validate.mjs` (cross-file wiring), never replaces it, and runs in `--meta` too.

 Snapshot used in Step 5 to produce unified diff.
@@ -208,7 +209,7 @@

````
Preview truncated: 119 diff lines.

````diff
--- baseline/.claude/skills/skill-optimizer/evals/README.md
+++ .claude/skills/skill-optimizer/evals/README.md
@@ -0,0 +1,20 @@
+# Scoped evaluation inputs
+
+`trigger-corpus.jsonl` is this repository source's authoritative publication-safe
+query and verdict history. `trigger-eval.json` is a disposable projection.
+Original global history stays in the private run snapshot. Predictions are not
+measured activation or held-out promotion.
+
+From a clean checkout, run `python3 <skill-dir>/evals/project_triggers.py` to
+regenerate the projection. Add `--check` to verify parity without writing.
+
+The helper replays the last record for each query and honors retirement. It
+selects 10 positive and 10 negative queries without deleting source history.
+Within each class it prefers the newest rows marked `selected_for_standard: true`,
+then fills from the newest unmarked rows. Rows with `selected_for_standard: false` are ineligible.
+The projection keeps the selected rows in latest-record source order. Fewer than
+10 eligible queries in either class produces an explicit error.
+
+Append or retire source rows before regenerating; do not edit the projection as
+input. The functional file uses `{ "skill_name": "...", "evals": [...] }`.
+Its author `expected_output` fields must be withheld from independent reviewers.
````

````diff
--- baseline/.claude/skills/skill-optimizer/evals/evals.json
+++ .claude/skills/skill-optimizer/evals/evals.json
@@ -1,7 +1,7 @@
 {
   "$schema": "https://json-schema.org/draft/2020-12/schema",
   "skill_name": "skill-optimizer",
-  "version": "1.2.0",
+  "version": "1.3.0",
   "description": "Functional evaluation suite for skill-optimizer (/sko) verifying 16-pass convergence, negative skip edges, eval generation, location sync, mandatory evals and the llms-first section.",
   "evals": [
     {
@@ -125,7 +125,7 @@
         },
         {
           "name": "kinds named",
-          "check": "Rows are classified as canonical, clone, copy, symlink, stub or remote; ~/.claude/skills/skill-optimizer is canonical",
+          "check": "Rows identify the selected source and classify every confirmed copy by owner and loading role; no same-named global source is assumed canonical over an explicitly selected path.",
           "type": "structural"
         },
         {
@@ -147,24 +147,24 @@
     },
     {
       "id": 6,
-      "name": "canonical-wins-with-backup",
+      "name": "preserve-newer-independent-source",
       "prompt": "A copy of my skill at ~/.agents/skills/my-skill has version 3.0.0 and a later updated date than the accessed copy in ~/.claude/skills/my-skill (version 2.1.0). Their SKILL.md hashes differ. Run /sko sync on my-skill.",
-      "expected_output": "Canonical (~/.claude/skills) wins. The newer copy is backed up to ~/.claude/skill-consolidation/backups/sko-sync-<timestamp>/agents-root/ before it is overwritten, and the report lists it loudly.",
+      "expected_output": "Preserve the newer divergent copy, report its ownership and hash, and synchronize only explicitly authorized unchanged destinations. A backup alone does not authorize overwrite.",
       "files": [],
       "assertions": [
         {
-          "name": "canonical wins",
-          "check": "The ~/.claude/skills copy is the source; the newer-version copy is overwritten, not promoted",
+          "name": "selected source respects ownership",
+          "check": "The selected source is optimized; a newer independent copy remains unchanged unless the owner explicitly authorizes its synchronization.",
           "type": "structural"
         },
         {
           "name": "backup before overwrite",
-          "check": "A backup path under ~/.claude/skill-consolidation/backups/sko-sync-<YYYYMMDD-HHMMSS>/<root-label>/ is created and verified before the overwrite",
-          "type": "deterministic"
-        },
-        {
-          "name": "loud newer-copy warning",
-          "check": "Report starts with a NEWER COPY OVERWRITTEN line naming the path, its version and the backup path",
+          "check": "Every authorized overwrite requires a verified preimage and an unchanged destination hash; an unauthorized overwrite is rejected.",
+          "type": "structural"
+        },
+        {
+          "name": "divergence reported",
+          "check": "Report includes the divergent newer version and the preserved action without claiming global synchronization.",
           "type": "structural"
         },
         {
````

````diff
--- baseline/.claude/skills/skill-optimizer/evals/project_triggers.py
+++ .claude/skills/skill-optimizer/evals/project_triggers.py
@@ -0,0 +1,58 @@
+#!/usr/bin/env python3
+"""Derive the disposable trigger projection from this bundle's scoped corpus."""
+import argparse
+import json
+from pathlib import Path
+
+
+def project(directory):
+    latest = {}
+    for line in (directory / 'trigger-corpus.jsonl').read_text().splitlines():
+        if not line.strip():
+            continue
+        row = json.loads(line)
+        query = row['query']
+        latest.pop(query, None)
+        if row.get('retired'):
+            continue
+        if not isinstance(row['should_trigger'], bool):
+            raise ValueError('should_trigger must be boolean')
+        selected = row.get('selected_for_standard')
+        if selected is not None and not isinstance(selected, bool):
+            raise ValueError('selected_for_standard must be boolean when set')
+        latest[query] = row
+    # Keep all source history. Project a balanced working subset, preferring
+    # explicitly selected rows, then the newest unmarked rows per class.
+    chosen = set()
+    for label in (True, False):
+        eligible = [row for row in latest.values()
+                    if row['should_trigger'] is label
+                    and row.get('selected_for_standard') is not False]
+        preferred = [row for row in eligible if row.get('selected_for_standard') is True][-10:]
+        unmarked = [row for row in eligible if row.get('selected_for_standard') is not True]
+        needed = 10 - len(preferred)
+        selection = preferred + (unmarked[-needed:] if needed else [])
+        if len(selection) != 10:
+            raise ValueError('scoped trigger corpus needs at least 10 eligible queries of each class')
+        chosen.update(row['query'] for row in selection)
+    rows = [{'query': row['query'], 'should_trigger': row['should_trigger']}
+            for row in latest.values() if row['query'] in chosen]
+    return json.dumps(rows, ensure_ascii=False, indent=2) + '\n'
+
+
+def main():
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.add_argument('--check', action='store_true')
+    args = parser.parse_args()
+    directory = Path(__file__).resolve().parent
+    candidate = project(directory)
+    output = directory / 'trigger-eval.json'
+    if args.check:
+        if not output.exists() or output.read_text() != candidate:
+            raise SystemExit('trigger projection is stale; run project_triggers.py')
+    else:
+        output.write_text(candidate)
+
+
+if __name__ == '__main__':
+    main()
````

````diff
--- baseline/.claude/skills/skill-optimizer/evals/test_project_triggers.py
+++ .claude/skills/skill-optimizer/evals/test_project_triggers.py
@@ -0,0 +1,70 @@
+"""Disposable history-growth fixtures; no real trigger corpus or model calls."""
+import importlib.util
+import json
+import os
+from pathlib import Path
+import tempfile
+import unittest
+
+PROJECTOR = Path(os.environ.get('SKO_PROJECTOR_PATH', str(Path(__file__).with_name('project_triggers.py'))))
+
+
+class ProjectionHistory(unittest.TestCase):
+    def setUp(self):
+        spec = importlib.util.spec_from_file_location('projector_under_test', PROJECTOR)
+        self.module = importlib.util.module_from_spec(spec)
+        spec.loader.exec_module(self.module)
+        self.temp = tempfile.TemporaryDirectory()
+        self.addCleanup(self.temp.cleanup)
+        self.root = Path(self.temp.name)
+        self.rows = [{'query': f'{label}-{number}', 'should_trigger': label}
+                     for label in (True, False) for number in range(10)]
+
+    def project(self, rows):
+        source = self.root/'trigger-corpus.jsonl'
+        source.write_text(''.join(json.dumps(row) + '\n' for row in rows))
+        before = source.read_bytes()
+        result = json.loads(self.module.project(self.root))
+        self.assertEqual(source.read_bytes(), before)
+        self.assertEqual(len(result), 20)
+        self.assertEqual(sum(row['should_trigger'] for row in result), 10)
+        return result
+
+    def test_existing_balanced_projection_stays_identical(self):
+        self.assertEqual(self.project(self.rows), self.rows)
+
+    def test_extra_active_query_keeps_history_and_balanced_subset(self):
+        result = self.project(self.rows + [{'query': 'fresh-positive', 'should_trigger': True}])
+        self.assertIn('fresh-positive', {row['query'] for row in result})
+        self.assertNotIn('True-0', {row['query'] for row in result})
+
+    def test_retirement_and_latest_duplicate_records_are_respected(self):
+        rows = self.rows + [{'query': 'True-0', 'retired': '2026-11-11'},
+                            {'query': 'replacement', 'should_trigger': True},
+                            {'query': 'True-1', 'should_trigger': True, 'verdict': 'new source verdict'}]
+        result = self.project(rows)
+        queries = [row['query'] for row in result]
+        self.assertNotIn('True-0', queries)
+        self.assertEqual(queries.count('True-1'), 1)
+        self.assertIn('replacement', queries)
+
+    def test_explicit_selection_takes_priority_over_unmarked_growth(self):
+        rows = [dict(row, selected_for_standard=True) for row in self.rows]
+        result = self.project(rows + [{'query': 'unmarked-positive', 'should_trigger': True}])
+        self.assertNotIn('unmarked-positive', {row['query'] for row in result})
+
+    def test_excluded_row_can_be_replaced_without_deleting_history(self):
+        rows = [dict(row, selected_for_standard=True) for row in self.rows]
+        rows[0]['selected_for_standard'] = False
+        result = self.project(rows + [{'query': 'unmarked-positive', 'should_trigger': True}])
+        self.assertIn('unmarked-positive', {row['query'] for row in result})
+        self.assertNotIn('True-0', {row['query'] for row in result})
+
+    def test_missing_class_and_invalid_labels_fail_explicitly(self):
+        for rows in (self.rows[1:], self.rows + [{'query': 'bad', 'should_trigger': 'yes'}]):
+            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
+                self.project(rows)
+
+
+if __name__ == '__main__':
+    unittest.main()
````

````diff
--- baseline/.claude/skills/skill-optimizer/evals/trigger-corpus.jsonl
+++ .claude/skills/skill-optimizer/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "optimize the mongodb-connection skill", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 1, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "run sko on phe", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 2, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "audit this skill for quality before I ship it", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 3, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "my skill keeps triggering on the wrong prompts", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 4, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "this SKILL.md is way too long, trim it down", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 5, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "check my new skill for collisions with existing skills", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 6, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "fix the description so this skill fires correctly", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 7, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "register this skill to the context hub", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 8, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "run sko --meta on deep-research", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 9, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "wire up the SKIP deferral edges between my skills", "should_trigger": true, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 10, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "optimize this system prompt for my agent", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 11, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "create a new skill for Kafka monitoring from scratch", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 12, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "rewrite this runbook so it reads better", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 13, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "sync all my skills to the hub", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 14, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "rebalance the whole skill tree, some hubs are over the cap", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 15, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "audit my MCP server's tool descriptions for discoverability", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 16, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "optimize this MongoDB aggregation, it's slow", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 17, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "why does my prompt produce inconsistent JSON output", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 18, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "clean up the AI-isms in this blog post", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 19, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "which Claude model should I use for this task", "should_trigger": false, "source": "replayed user corpus; original rows retained privately", "source_version": "2.22.3", "id": 20, "description_sha256": "3aaac5c2eb0516ffbce951c91e4bf0c3b9347b992c4a709b347a6ab98e1e40f1", "skill_version": "2.25.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
````

````diff
--- baseline/.claude/skills/skill-optimizer/evals/trigger-eval.json
+++ .claude/skills/skill-optimizer/evals/trigger-eval.json
@@ -1,82 +1,82 @@
 [
- {
-  "query": "optimize the mongodb-connection skill",
-  "should_trigger": true
- },
- {
-  "query": "run sko on phe",
-  "should_trigger": true
- },
- {
-  "query": "audit this skill for quality before I ship it",
-  "should_trigger": true
- },
- {
-  "query": "my skill keeps triggering on the wrong prompts",
-  "should_trigger": true
- },
- {
-  "query": "this SKILL.md is way too long, trim it down",
-  "should_trigger": true
- },
- {
-  "query": "check my new skill for collisions with existing skills",
-  "should_trigger": true
- },
- {
-  "query": "fix the description so this skill fires correctly",
-  "should_trigger": true
- },
- {
-  "query": "register this skill to the context hub",
-  "should_trigger": true
- },
- {
-  "query": "run sko --meta on deep-research",
-  "should_trigger": true
- },
- {
-  "query": "wire up the SKIP deferral edges between my skills",
-  "should_trigger": true
- },
- {
-  "query": "optimize this system prompt for my agent",
-  "should_trigger": false
- },
- {
-  "query": "create a new skill for Kafka monitoring from scratch",
-  "should_trigger": false
- },
- {
-  "query": "rewrite this runbook so it reads better",
-  "should_trigger": false
- },
- {
-  "query": "sync all my skills to the hub",
-  "should_trigger": false
- },
- {
-  "query": "rebalance the whole skill tree, some hubs are over the cap",
-  "should_trigger": false
- },
- {
-  "query": "audit my MCP server's tool descriptions for discoverability",
-  "should_trigger": false
- },
- {
-  "query": "optimize this MongoDB aggregation, it's slow",
-  "should_trigger": false
- },
- {
-  "query": "why does my prompt produce inconsistent JSON output",
-  "should_trigger": false
- },
- {
-  "query": "clean up the AI-isms in this blog post",
-  "should_trigger": false
- },
````
Preview truncated: 165 diff lines.

````diff
--- baseline/.claude/skills/skill-optimizer/references/CHANGELOG.md
+++ .claude/skills/skill-optimizer/references/CHANGELOG.md
@@ -1,3 +1,7 @@
+2026-11-11 final SKO TASK-1372: A–P and bounded independent rechecks recorded; exploratory predicted triggers; scoped operational exit DEGRADED. Raw dissent and focused correction receipts remain in the repository review ledger. No measured activation, semantic refresh or empirical promotion. Mapping freshness remains BLOCKED/operator action for separately authorized research; historical verification dates are preserved.
+
+2026-11-11 SKO 2.24.1 to 2.25.0: scoped source, routing and evaluation repairs. Author trigger predictions: 10/10 positive, 0/10 false positive. Fresh blind review and global routing remain pending; no measured activation or empirical promotion.
+
 2026-11-06 v2.24.0->v2.24.1 — improve location discovery and safeguards for divergent skill copies.
 2026-11-06 v2.23.1->v2.24.0 — manual upgrade, not a certified sko run (Pass H not re-run). Step 6.7 location sync (accessed copy wins, backup to skill-consolidation/backups/sko-sync-<ts>/, clones via git, remotes report-only, location table; new `SYNC-PARTIAL` status). Step 6.3 eval gate on every run (reuses Pass F/H and deep-eval-optimizer; new `EVALS-MISSING` status). Step 1.7 semantic and keyword index discovery with script fallbacks. New Pass P (llms-first section, Medium) with references/llms-first-section.md; /sko carries the section itself. Evals 5-8 added; commands/sko.md wrapper updated.
 2026-10-15 v2.23.0->v2.23.1 — peer deferral seeded by agent-deep-optimizer v1.0.0: one when-not-to-use line routing subagent definitions to /ado; related_skills gains agent-deep-optimizer. Additive only; no pass run.
````

````diff
--- baseline/.claude/skills/skill-optimizer/references/corpus-scope.md
+++ .claude/skills/skill-optimizer/references/corpus-scope.md
@@ -0,0 +1,26 @@
+# Source corpus and write scope
+
+Resolve one authoritative trigger corpus before generating a projection.
+
+1. For an installed user-level target, use the existing
+   `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`.
+2. For an explicitly selected repository target, use its
+   `evals/trigger-corpus.jsonl`. Before creating it, read any existing user-level
+   corpus and preserve its rows and provenance in the run snapshot. Replay its
+   applicable queries. Repository scope does not authorize modifying that file.
+3. If the target is read-only or the owner forbids corpus writes, keep the
+   selection and predictions in memory. Do not create a corpus or projection.
+
+Record the selected path, source hashes, skill identity and corpus version in the
+run receipt. Append new query/verdict records with the current description hash,
+skill version and evaluation level. Retain history. If the skill's scope changes,
+retire an affected query with a dated reason instead of deleting it.
+
+Each query row includes `query` and Boolean `should_trigger`. Rows that record a
+prediction also include `predicted_trigger`, `level: predicted`, and a reason.
+Project only the selected active queries as
+`[{"query": "...", "should_trigger": true}]` in `evals/trigger-eval.json`.
+The projection carries no authority over source history.
+
+The 20-query audit is exploratory. It does not satisfy the larger held-out
+promotion requirements in `shared/champion-challenger.md`.
````

````diff
--- baseline/.claude/skills/skill-optimizer/references/empirical-mode.md
+++ .claude/skills/skill-optimizer/references/empirical-mode.md
@@ -1,6 +1,6 @@
 # Empirical mode: champion and challenger held-out loop

-skill-optimizer already runs this loop in part. **Pass H** is a 20-query trigger-accuracy eval with a persisted held-out corpus (`~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`). Empirical mode names the promotion gate around it explicitly, per the shared contract `references/shared/champion-challenger.md` (**cite, don't restate**). It is **on by default** only when the corpus, must-pass invariants, and working/holdout splits satisfy the shared contract's minimum sizes and split discipline. A standard 20-query Pass H audit does not meet those minima: run it as exploratory trigger evaluation, with no empirical promotion. An eligible promotion persists the champion and its eval state across runs. Opt out with `--dry-run`, `--no-promote`, or `--structural-only`.
+Pass H provides a 20-query trigger audit. Resolve its persisted source corpus with `corpus-scope.md`. Empirical mode adds the promotion gate in `shared/champion-challenger.md`. It is on by default only when corpus sizes, must-pass invariants and working/holdout splits satisfy that contract. The standard 20-query audit is exploratory and does not qualify for empirical promotion. An eligible promotion persists the champion and its eval state. Opt out with `--dry-run`, `--no-promote` or `--structural-only`.

 Calibration:

````

````diff
--- baseline/.claude/skills/skill-optimizer/references/eval-gate.md
+++ .claude/skills/skill-optimizer/references/eval-gate.md
@@ -1,6 +1,36 @@
 # Eval gate (Step 6.3)

 Every run reports eval results. A run without them cannot exit `converged`. It exits `EVALS-MISSING`. This gate reuses Pass F (evals exist), Pass H (trigger eval) and the `deep-eval-optimizer` hand-off. It adds no parallel harness.
+
+## Functional file schema
+
+Use an object with `skill_name` and an `evals` array. A top-level case array is
+not this format. Start with the shape below, then author at least 2–3 distinct,
+realistic cases. Use unique IDs, authorized fixture paths, and assertions whose
+level is explicit. `expected_output` is an author reference; withhold it from the
+blind judge. An empty `files` array means the case needs no input fixture.
+
+```json
+{
+  "skill_name": "example-skill",
+  "evals": [
+    {
+      "id": 1,
+      "name": "missing-input",
+      "prompt": "Turn my completed migration into a reusable procedure, but I have not supplied its artifacts.",
+      "expected_output": "Identify the missing source artifact before making claims about the completed migration.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "source-required",
+          "type": "negative",
+          "check": "Does not invent migration steps or claim it inspected an absent artifact."
+        }
+      ]
+    }
+  ]
+}
+```

 ## What runs, in order

````

````diff
--- baseline/.claude/skills/skill-optimizer/references/location-sync.md
+++ .claude/skills/skill-optimizer/references/location-sync.md
@@ -3,3 +3,23 @@
 Discover the target skill's installed copies and hash their contents. Treat the explicitly selected source as canonical only after checking repository instructions and the user's intent. Report divergent, newer, vendored, remote, and plugin-managed copies. Do not overwrite them automatically.

 Respect git worktree ownership and preserve other work. Before any authorized synchronization, save a recoverable preimage, check for concurrent writers and symlink loops, and verify the destination after writing. Never push or merge another repository without authorization. In read-only mode, inspect and report only. If a required copy cannot be synchronized, report SYNC-PARTIAL.
+
+## Git clone destinations
+
+A git clone is a repository destination. Do not copy a source file into it and
+call that delivered. Inspect its branch, worktree ownership, remote and dirty or
+divergent state first. Preserve active work and concurrent writers.
+
+When delivery to that repository is authorized, use its commit, push, PR, required
+checks and merge workflow. Verify the final content on the remote default branch.
+Then fetch and fast-forward only a clean compatible clone; never reset, stash
+another writer's work, force-push or rewrite its default branch. A dirty,
+divergent, independently owned or inaccessible clone stays unchanged and appears
+as blocked or report-only in the location table. Record the exact blocker and
+recoverable branch/PR when delivery cannot finish. Authorization for this source
+repository does not authorize publishing a different repository.
+
+Example: a clean clone on its default branch and strictly behind the verified
+remote may run `git fetch origin` followed by `git merge --ff-only origin/main`
+when `main` is its actual default branch. A clone with local commits or edits
+remains preserved while delivery proceeds in an isolated owned worktree.
````

````diff
--- baseline/.claude/skills/skill-optimizer/references/model-effort.md
+++ .claude/skills/skill-optimizer/references/model-effort.md
@@ -24,6 +24,7 @@

 - **Default when uncertain:** flagship tier with `high` effort as this skill's conservative heuristic for intelligence-sensitive work; provider defaults vary by model. Never guess below this tier for a skill that makes judgments.
 - **Resolve the tier to an exact current model ID from a live source**, in this order: (1) the `claude-api` skill's `shared/models.md`, when that skill is installed (it is not on every machine; check before citing it); (2) the `Claude API ID` row, not the alias row, of Anthropic's models overview at `https://platform.claude.com/docs/en/models/overview` (WebFetch; the page redirects there from the older `about-claude/models/overview` path); (3) the harness's own model roster when the session's system prompt names current IDs, recorded as `source: harness roster`. Never an ID recalled from memory, never a dated suffix the source does not show. No source reachable? Write no `model` key at all and record `model: unresolved (no live model source)`. An absent key is advisory-neutral; a wrong one misroutes every future dispatch.
+- **Match the target runtime first.** The source chain above applies to Claude entrypoints. For a Codex or another provider's target, resolve an ID from that runtime's live model roster or official model source. Never write a Claude ID into a Codex target merely because the Claude overview was reachable. Preserve an explicit workflow default or caller pin. If the runtime or tier mapping is unclear, leave the model unchanged and record the unresolved recommendation.
 - **Effort validity.** Valid levels are `low`, `medium`, `high`, `xhigh`, and `max`. Validate each level against the selected model's current documented support at `https://platform.claude.com/docs/en/build-with-claude/effort`; heuristic tiers are recommendations, not API capability restrictions. Do not reject a supported caller-pinned pairing just because it uses a lower tier. The key is an advisory run-under hint, so a model that ignores the parameter still gets its recorded level and treats it as advisory.
 - **Caller override wins.** `--model=<id>` and `--effort=<level>` pin the value and skip the heuristic. Validate the override (real ID, valid effort level) and record that it was caller-set.
 - This step is deterministic enough to run in `--meta` mode, since it touches only frontmatter, and it runs in every artifact-size profile.
````

````diff
--- baseline/.claude/skills/skill-optimizer/references/passes.md
+++ .claude/skills/skill-optimizer/references/passes.md
@@ -79,7 +79,7 @@

 Measure whether the description actually fires correctly. This is the single most impactful pass because mis-triggering is the dominant skill failure mode.

-1. **Replay the canonical corpus first.** The single store of record is `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl` (SKILL.md Step 2.3). If it exists, replay its stored queries against the current description before generating new ones — a previously-passing query that now fails is a true regression. Then append fresh queries to fill the 20-query set, and persist every query + verdict back to that file, recording the description hash (SHA-256) and skill version each verdict was predicted against. If the canonical corpus and projection do not exist, generate the 20 realistic queries (10 should-trigger, 10 should-not-trigger near-misses) and establish the canonical corpus first, then derive `<skill-dir>/evals/trigger-eval.json` from its query/expectation rows (missing trigger evals is a **Medium** finding). Never read `<skill-dir>/evals/trigger-eval.json` as input: it is a disposable projection this pass writes in step 4.1, and a hand-edited or stale projection would silently replace the corpus's history. Staleness rule: when a run intentionally changes the skill's scope, retire affected stored queries (`retired: <date>` + reason) instead of counting their failures as regressions.
+1. **Replay the source corpus first.** Resolve its ownership and path with `corpus-scope.md`. Replay applicable existing queries before adding a fresh 10-positive/10-negative audit set. Append query verdicts with description SHA-256, skill version and evaluation level. Preserve history and retire scope-invalid queries with a dated reason. Derive `<skill-dir>/evals/trigger-eval.json` from these source rows; never read that disposable projection as the input corpus. A repository run preserves user-level corpora without writing to them.
 2. Generate the 20 realistic queries (one-line user phrasings, not abstract task descriptions). This ≈20-query shape with near-miss negatives matches the official agentskills.io eval methodology; apply its 60/40 train/validation split when iterating a description more than once, to prevent description overfitting:
    - 10 **should-trigger**: varied phrasings of the skill's intent, including casual, terse, and uncommon wordings
    - 10 **should-not-trigger**: near-miss adjacent queries that share keywords but actually need a different skill (e.g., for `mongodb-encryption`: "encrypt a SQLite database" or "set up TLS on my Atlas cluster")
````

````diff
--- baseline/.claude/skills/skill-optimizer/references/post-sync-steps.md
+++ .claude/skills/skill-optimizer/references/post-sync-steps.md
@@ -29,7 +29,7 @@

 - **Regenerate:** run `node ~/.claude/skill-consolidation/gen-skills-index.mjs`. It re-reads every `SKILL.md` in a bounded parallel pass and rewrites both `SKILLS-INDEX.json` and `SKILLS-INDEX.md`.
 - **Gate:** then run `node ~/.claude/skill-consolidation/gen-skills-index.mjs --check`; it must exit 0. A non-zero (`STALE`) exit means the regenerate did not land, so re-run it once and re-gate.
-- **Runs in `--meta` and under `--no-sync`.** The index is a local artifact independent of the registry, and `--meta` still changes frontmatter and version, so a refresh is always warranted. Skipped only when the generator is absent.
+- **Scope first.** This local artifact is independent of the semantic registry. Refresh it in `--meta` or under `--no-sync` only when it indexes the changed source and the destination is within the authorized write scope. A repository-only run does not rewrite an unrelated installed-library index. If those conditions do not hold, inspect with `--check` when available and report the scope limit.
 - **Non-blocking:** generator unavailable or errors? Record `index: skipped (<reason>)`, continue.
 - Record outcome in Step 8 report: `index: refreshed (N skills)` or `index: skipped (<reason>)`.

````

````diff
--- baseline/.claude/skills/skill-optimizer/references/report-format.md
+++ .claude/skills/skill-optimizer/references/report-format.md
@@ -39,12 +39,12 @@

 **Index discovery** (Step 1.7), one line: `index-discovery: colliders n, referrers n, copies n (verified v, lead only l)` or `index-discovery: degraded (<reason>)`.

-**Location sync table** (Step 6.7), required in every run. Lead with a `NEWER COPY OVERWRITTEN: <path> v<x> updated <date>; backup <path>` line for each copy that was newer than canonical.
+**Location sync table** (Step 6.7), required in every run. Emit `NEWER COPY OVERWRITTEN: <path> v<x> updated <date>; backup <path>` only after an actual authorized overwrite of a newer copy and verification of its backup. For every preserved newer copy, report `preserved divergence` and its actual unchanged hash. Never imply an overwrite or invent a backup.

 | Location | Kind | Before-hash | Action | After-hash |
 |---|---|---|---|---|

-Kinds: canonical, clone, copy, symlink, stub, remote, vendored. Actions: none, symlinked, synced, synced (worktree), ff-merged, blocked (dirty), blocked (diverged), FAILED, would sync, skipped (--no-sync), unreachable, orphan (report), report only, lead only (definitions in `references/location-sync.md`). Remote boxes and vendored copies are reported, never written. Add the backup directory when anything was written: `$HOME/Archive/sko-sync-<ts>/` for overwritten copies, `$HOME/Archive/symlinkify-<ts>/` for roots replaced by a symlink.
+Kinds: canonical, clone, copy, symlink, stub, remote, vendored, generated overlay, historical snapshot. Actions include verified sync, preserved divergence, report only, skipped (--no-sync), blocked (dirty), blocked (diverged), would sync, unreachable and lead only. Remote, plugin-managed and independently owned copies remain report-only unless separately authorized. Record the actual verified backup path for each permitted overwrite; do not invent a backup location or imply that the presence of a backup authorizes the write.

 **llms-first** (Pass P), one line: `llms-first: present | added | n/a (<reason>)`.

````

````diff
--- baseline/.claude/skills/skill-optimizer/references/shared/convergence-and-severity.md
+++ .claude/skills/skill-optimizer/references/shared/convergence-and-severity.md
@@ -7,10 +7,12 @@
 *calibration table* (which finding maps to which tier for that artifact) but should stay consistent
 with the ladder and exit conditions below. Cite this file; do not silently diverge from it.

-> mapping-table cross-checked against pdo/sko/ddo/document-critique SKILL.md tier vocabularies:
-> 2026-06-11 — re-check on any tier rename or every 90 days. After re-verifying, re-save this
-> file's shared-library registry entry (`tam_update_shared_library`) in the same pass —
-> `tam_staleness_scan` keys on the catalog-entry timestamp, not file content.
+> Historical mapping-table check: 2026-06-11. Re-check on a tier rename or when
+> the owning workflow requires a current review, including its 90-day freshness gate.
+> This date is not a fresh verification. Emit a BLOCKED/operator-action row when
+> that gate is due; do not replace this stamp without re-verifying the claims.
+> Retired catalog APIs do not authorize registry writes. Follow the invoking
+> optimizer's current registry, ownership and service-pause gates.

 ## Severity ladder (canonical)

@@ -245,7 +247,14 @@
 every table row's roots) is read and searched with ordinary tools — no fallback note needed, since
 no index claim was ever made for it.

-**Keep the index warm.** Any write this run makes to a file under `gen-prose-index.mjs`'s corpus
+**Workflow-specific indexing.** For `skill-optimizer`, Step 7.6 in
+`post-sync-steps.md` replaces this paragraph: observe its owning daemon, perform
+no per-run prose refresh, and never start or force the indexer. For another
+workflow, the legacy procedure below applies only when its current owner still
+specifies this index and explicitly authorizes the work. Respect every existing
+service pause and ownership boundary.
+
+**Legacy incremental index.** Any write this run makes to a file under `gen-prose-index.mjs`'s corpus
 roots (`~/.claude/skills`, `~/.claude/skill-consolidation`, and the mdb-context-hub `docs/` and
 repo-root markdown) leaves `tam_search_prose` stale for that file until re-embedded. After Step
 7/Step 5's writes land (and after Pass O's peer writes, if any), run `node
````

````diff
--- baseline/.claude/skills/skill-optimizer/references/shared/cross-model-gate.md
+++ .claude/skills/skill-optimizer/references/shared/cross-model-gate.md
@@ -22,14 +22,13 @@
 1. **Availability check** — `copilot --version`. On failure, log
    `cross-model gate: skipped (copilot CLI unavailable)` in the report and continue to the normal
    exit. The gate must never block a run.
-2. **Model detection** — reuse copilot-adversarial-review's Step 0 latest-GPT snippet, or skip
-   detection entirely and use the hardcoded fallback to save one CLI round-trip:
-
-   ```bash
-   LATEST_GPT=$(copilot -p "What is the single most capable base GPT model ID available to you right now? Reply with only the model ID, nothing else." --silent \
-     | grep -oE 'gpt-[0-9]+\.[0-9]+' | head -1)
-   [[ "$LATEST_GPT" =~ ^gpt-[0-9] ]] || LATEST_GPT="gpt-4.1"
-   ```
+2. **Model selection without a provider call** — use a caller-pinned GPT model or
+   a model ID verified in the CLI's local roster or current configuration. Record
+   that source and the selected model. Check documented selection syntax with
+   local `--help` when needed. Do not call `copilot -p` for discovery, and do not
+   infer availability from an old fallback ID. If no eligible model can be
+   verified without a provider call, report
+   `cross-model gate: skipped (model availability unverified)`.

 3. **One review call** — exactly one `copilot -p` invocation per run (hard limit), passing the
    FINAL artifact with the review-prompt template below.
````

````diff
--- baseline/.claude/skills/skill-optimizer/references/shared/evidence-contract.md
+++ .claude/skills/skill-optimizer/references/shared/evidence-contract.md
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
+checks and an independent final review. Installed changes also need actual loaded
+identity and an exercised installed entry point. The existing ship-it installation
+rule remains authoritative.
+
+The stdlib evidence_gate.py checks declared roles, file hashes and outcomes. It
+cannot establish that a reviewer was independent, that a logged observation is
+truthful, or that the declared files cover the entire product. The orchestrator
+must collect actual tool outputs and independent review, define the complete
+scoped artifact set, and preserve the underlying captures/logs. Never create a
+self-authored statement as a substitute for an unexecuted check.
+
+## Artifact binding
+
+An acceptance JSON object has schema_version equal to 1 and an artifacts list.
+Each artifact has a unique nonempty string id, path, and exact lowercase SHA-256.
+Paths are absolute or relative to the JSON file. The checker reads each actual
+file and rejects a stale declared hash. The combined artifact_sha256 is SHA-256
+of the sorted (id, file-hash) pairs encoded with compact JSON. IDs remain stable
+across source and installation locations, so equal contents can share a binding.
+Include all source/configuration/data files that can affect the scoped result.
+
+Compute the binding from actual files, without editing the supplied JSON:
+
+```sh
+python3 evidence_gate.py acceptance.json --fingerprint
+```
+
+Copy the returned artifact_sha256 into the acceptance object and its current
+receipts. Recollect affected evidence after any artifact change. The validator
+must not treat an unchanged capture file as proof that it belongs to changed code.
+
+## Required evidence
+
+| Field | Required content |
+| --- | --- |
+| checks | Nonempty list of actual EXECUTED checks, each completed successfully on the current binding |
+| review | ISOLATED receipt, nonempty reviewer identity, verdict PASS, and current binding |
+| correctness_findings | Explicit list of reproduced correctness-finding IDs, or an empty list when none apply |
+| regressions | Exactly one before/after regression record for each correctness finding |
+| installation | Explicit required boolean; true adds loaded-source and entry-point requirements |
+
+Each receipt has kind, completed equal to true, artifact_sha256, and proof.
+Proof has a path to a real capture/log and its exact sha256. Its contents must
+come from the actual operation. EXPERT, SIMULATED and PARTICIPANT grades retain
+their uses elsewhere; they cannot satisfy these different acceptance roles.
+
+An EXECUTED receipt declares exactly one nonempty command or tool. A command
+receipt includes its completed integer exit_code (0 for success; a Boolean is
+invalid). A tool receipt records actual success equal to true; do not invent a
+process exit code for a tool that did not return one. Preserve nonzero command
+status through pipelines and log capture.
+
+The independent reviewer receives the final artifact and criteria without prior
+verdicts. A label saying ISOLATED is not itself proof of isolation. Preserve the
+separate review output as proof and record the reviewer identity.
+
+## Regression records
+
+For each reproduced correctness bug, preserve baseline_artifacts in the same
+artifact-list shape as artifacts. The baseline files are the actual pre-repair
+snapshots. Baseline and final lists must use the same stable artifact IDs.
+Their fingerprints must differ because file bytes changed; renaming an ID cannot
+serve as evidence of repair. The multiset of file hashes must change too, so
+swapping labels among unchanged files does not pass. For a layout-only repair,
+include an actual deployment/source manifest as a stable artifact whose bytes
+record the changed layout. A regression row contains finding_id, test (path/sha256), before and
+after receipts. Both receipts are EXECUTED command results, use the same command
+and test_sha256, and point to preserved logs. Before binds to the baseline and
````
Preview truncated: 115 diff lines.

````diff
--- baseline/.claude/skills/skill-optimizer/references/shared/evidence_gate.py
+++ .claude/skills/skill-optimizer/references/shared/evidence_gate.py
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
+
+def file_hash(path):
+    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
+
+
+def fingerprint(artifacts, base):
+    if not isinstance(artifacts, list) or not artifacts:
+        raise ValueError('artifacts must be a nonempty list')
+    records = []
+    for row in artifacts:
+        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
+            raise ValueError('each artifact needs a nonempty string id')
+        digest = file_hash(base / row['path'])
+        if row.get('sha256') != digest:
+            raise ValueError(f'artifact {row["id"]}: stale file hash')
+        records.append((row['id'], digest))
+    if len({key for key, _ in records}) != len(records):
+        raise ValueError('duplicate artifact id')
+    return hashlib.sha256(json.dumps(sorted(records), separators=(',', ':')).encode()).hexdigest()
+
+
+def validate(manifest, base):
+    """Return consistency/freshness failures, not proof that the author told the truth."""
+    errors = []
+    base = Path(base)
+
+    def need(condition, message):
+        if not condition:
+            errors.append(message)
+
+    def proof(value, label):
+        if not isinstance(value, dict):
+            errors.append(label + ': missing proof')
+            return
+        try:
+            need(file_hash(base / value['path']) == value.get('sha256'), label + ': proof hash mismatch')
+        except (KeyError, OSError, TypeError):
+            errors.append(label + ': proof file unavailable')
+
+    def receipt(row, label, kind, revision, exit_success=None):
+        if not isinstance(row, dict):
+            errors.append(label + ': missing receipt')
+            return
+        need(row.get('kind') == kind, label + ': requires ' + kind)
+        need(row.get('completed') is True, label + ': result incomplete')
+        need(row.get('artifact_sha256') == revision, label + ': stale artifact binding')
+        proof(row.get('proof'), label)
+        if kind == 'EXECUTED':
+            command = isinstance(row.get('command'), str) and bool(row['command'].strip())
+            tool = isinstance(row.get('tool'), str) and bool(row['tool'].strip())
+            need(command != tool, label + ': declare one command or tool')
+            if command:
+                code = row.get('exit_code')
+                need(type(code) is int, label + ': missing integer exit code')
+                if exit_success is not None:
+                    need(type(code) is int and (code == 0) == exit_success, label + ': unexpected exit code')
+            elif tool:
+                need(exit_success is not False, label + ': regression failure needs a command exit code')
+                need(row.get('success') is True, label + ': tool did not succeed')
+
+    if not isinstance(manifest, dict):
+        return ['acceptance must be an object']
+    try:
+        need(manifest.get('schema_version') == 1, 'unsupported acceptance schema')
+        current = fingerprint(manifest.get('artifacts'), base)
+        need(manifest.get('artifact_sha256') == current, 'acceptance artifact fingerprint mismatch')
+        checks = manifest.get('checks')
+        need(isinstance(checks, list) and bool(checks), 'missing required executed checks')
````
Preview truncated: 155 diff lines.

````diff
--- baseline/.claude/skills/skill-optimizer/references/structural-mode.md
+++ .claude/skills/skill-optimizer/references/structural-mode.md
@@ -66,7 +66,7 @@

 ## Registration still runs

-Registry registration is a kept capability, so **Step 7 runs in `--meta`** and is **not** a dry run. `--meta` changes the description and version, which is exactly what the router indexes, so the rebuild matters here as much as in a full run. The rebuild is suppressed only when `--no-sync` was passed or the run exited with High findings remaining (override: `--sync-anyway`); both are orthogonal to `--meta`. Under `--no-sync` or a withheld rebuild, the routing verify still runs read-only and reports `stale` or `unroutable` without retrying.
+Registry registration is a kept capability, so **Step 7 runs in `--meta`** and is **not** a dry run. `--meta` changes the description and version, which is exactly what the router indexes, so the rebuild matters here as much as in a full run. Apply the complete Step 7 gate in `sync-protocol.md`: withhold the rebuild under `--no-sync`, residual High findings, an existing service/index pause, or a write outside authorized ownership and scope. `--sync-anyway` overrides only residual High findings; it grants no authority and does not lift pauses. These gates also apply in `--meta`. Under `--no-sync` or a withheld rebuild, the routing verify still runs read-only and reports `stale` or `unroutable` without retrying.

 ## Report shape

````

````diff
--- baseline/.claude/skills/skill-optimizer/references/sync-protocol.md
+++ .claude/skills/skill-optimizer/references/sync-protocol.md
@@ -14,7 +14,7 @@

 ### The shadowing trap (read this before trusting a rebuild)

-Roots are searched in order `~/.global-ai-hub/skills/`, then `~/.claude/skills/`, then the plugin cache, and the first `name` seen wins. If a stale twin of the target sits in an earlier root, every rebuild re-indexes *that* file and the copy you edited is never read. The failure is silent and total: the build prints a normal entry count, exits 0, and the registry keeps serving the old description no matter how many times you rebuild. When `~/.claude/skills` is a symlink to the hub root (this machine's layout since 2026-09), those two roots are one directory and cannot shadow each other; a same-`name` plugin-cache copy is still shadowed by the local one, and a hub-root twin reappears the moment the symlink is replaced by a real directory.
+Verify root order against the current collector. In the legacy collector described here, the hub root precedes the Claude root and plugin cache. An earlier same-name source can keep serving an older description even after a successful rebuild. Resolve real paths: two symlink aliases can name one file. Do not assume that a previous machine's root layout still applies.

 Before Step 7's rebuild, confirm the copy you edited is the one that will be indexed:

@@ -25,7 +25,7 @@
 done
 ```

-Two lines with the **same real path** are one file, not a twin. Two hits with different real paths and different hashes ⇒ Step 1's duplicate guard should already have filed this **High**. Do not overwrite the twin by hand. Report the winning root and withhold a clean routing verdict until Step 6.7 (`references/location-sync.md`) makes that copy identical to the canonical target. Step 6.7 syncs content; deleting a twin stays with `skill-tree-architect`. Observed live 2026-09-09 on this skill: two rebuilds, exit 0 both times, description unchanged in the index, because a v2.16.1 twin in the hub root was shadowing the edited v2.17.0 file.
+Two lines with the same real path name one file. A divergent, actively indexed source that shadows the selected source is a High finding. Report its owner and winning root. Step 6.7 may synchronize it only within the user's scope, after an unchanged-preimage check. Otherwise preserve it and report the routing limit. Repository distributions, overlays and historical snapshots are classified separately; their existence alone is not a High finding. Deleting a copy stays with `skill-tree-architect`.
 | Rebuild | `cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router build --prune` |
 | Read | `hub_route(task, kinds="skill", top=N)` — returns `score`, `ref`, `description`, `origin` |
 | Read (CLI, MCP not connected) | `PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router route "<task>" --top 5 --kinds skill` |
@@ -34,7 +34,7 @@

 - **One rebuild covers every skill written this run.** The target and all Pass O peers are re-indexed by the same command; there is no per-peer sync loop.
 - **No fallback chain.** There is one write path. A rebuild either runs or it doesn't.
-- **No durability caveat.** Nothing regenerates the registry from a separate mirror, so a rebuild cannot be silently undone by a later batch job.
+- **Verify the result.** A successful rebuild does not prove that the selected source won collection or that later automation will preserve it. Record the actual source and compare stored descriptions.
 - **A legacy `context.md` + `manifest.yaml` pair is never indexed.** The glob matches `SKILL.md` only. Optimizing such a target is valid; reporting it as registered is not.

 ## Duplicate-copy guard (Step 1.5 mechanics)
@@ -49,11 +49,11 @@
 done | xargs -n1 realpath 2>/dev/null | sort -u
 ```

-One line ⇒ a single copy. Classify every extra line by depth under its root: `<root>/<id>/SKILL.md` is a top-level twin (registry competition, **High**; see § The shadowing trap); anything deeper is a nested stale copy (unindexed, unloaded; report it and hand cleanup to `skill-tree-architect`). Observed live 2026-09-17 on this skill: the naive `find -path "*/<id>/*"` form returned 14 hits, of which one was the canonical file seen through the symlink, two were nested stale copies (v2.11.0, v2.15.1), and eleven were git worktrees.
+Also inspect the explicitly selected repository's skill roots and its generator manifests. Classify each real path by owner and loading role. An active indexed shadow with different content is High; an intentional distribution, generated overlay or historical snapshot is reported with its role. A path's depth alone does not prove that every runtime ignores it. Preserve other worktrees and plugin-managed sources. See `location-sync.md` for permitted writes.

 ## Sub-steps

-**7.0 Outcome changelog line.** A write outside the convergence loop, exempt from Step 6's SHA/parse checks (which ran before it): prepend one run-outcome line to the file named by the target's frontmatter `metadata.changelog_ref` (default `references/CHANGELOG.md`; create the file and set the key when absent, moving any inline `metadata.changelog` array into it at the same time, per Pass J.1). Newest first, no cap: the file loads only when read, never on invocation. Skipped under `--read-only`. Format: `<date> sko vX->vY — Pass H n/10->n/10 pos, n/10->n/10 neg; <counts> fixed`. One line, not a paragraph. Run a one-line frontmatter re-parse check after the write.
+**7.0 Outcome changelog line.** Prepend one outcome line to the file named by `metadata.changelog_ref` (default `references/CHANGELOG.md`). Preserve its preimage before writing. If a metadata key must be added, parse the frontmatter again. Recompute the final write-set hashes after this step; a post-verification changelog write is not exempt from the final manifest. Skip writes under `--read-only`. Record prediction, measurement and operational limits without claiming an unrun gate passed.

 **1. Rebuild the index.**

@@ -61,7 +61,7 @@
 cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router build --prune
 ```

-Runs unless the caller passed `--no-sync` or the run exited with High findings remaining (override `--sync-anyway`). The command is idempotent and covers the target plus every Pass O peer in one pass. Record its exit status.
+Run only within the authorized index scope and service permissions. Withhold it for `--no-sync`, an existing indexing pause or residual High findings. `--sync-anyway` overrides only the High-findings gate. It does not authorize embeddings, a service restart or writes outside the requested scope. Record either the actual exit status or the precise withheld reason.

 **2. Verify routing.** Read-only; **always runs**, even under `--no-sync`. For the target and each Pass O peer, record one verdict:

````

| Eval | Result | Level | Files present? |
|---|---|---|---|
|Trigger|pos10/10; false-positive1/10|predicted|yes|
|Behavior|32/32 assertions across8 cases|predicted source support|yes|

index-discovery: degraded; bounded read-only keyword results and installed-source leads are in the ledger.

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
|.claude/skills/skill-optimizer/SKILL.md|selected repository source|a40ce1cf0a3be20e0233997d23215655433f0ef51c21483b42662c09e912b950|scoped source edits|2e299879b928b635706267ae7ee5fb25b6ed2e5cee25b50ad6784083254f3461|
|External installed sources|independently owned copies|see locations.json|preserved divergence|unchanged|

llms-first: present; authoritative source verification retained.

| Skill | Verdict | Indexed description matches? | Own intent surfaces? | Stale rows |
|---|---|---|---|---|
|skill-optimizer|stale; rebuild withheld|no|not probed under pause|see routing.json|

prose-index: existing daemon observed up; no restart or forced refresh.
index: skipped for the global catalog under repository scope and existing pauses.
degraded: semantic discovery, candidate registration and global catalog refresh did not land; exit DEGRADED.
model/effort: see final source frontmatter and centrally recorded advisory-source limits.
Snapshot & rollback (entrypoint): `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/root/skill-optimizer/baseline/SKILL.md" ".claude/skills/skill-optimizer/SKILL.md"`.
Telemetry: scoped private task ledger; global ledger not rewritten.

Summary: bounded audit and focused correction evidence complete; no measured activation,
empirical promotion, full factual recertification or global installation acceptance.
Modified sections and exact file hashes are in the diff previews and source integrity manifest.
