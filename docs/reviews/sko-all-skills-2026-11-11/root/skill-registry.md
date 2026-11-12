# skill-registry — final scoped SKO receipt

The source audit is complete with operational DEGRADED status. Raw bounded dissent
and subsequent focused corrections remain separate in the [final ledger](../final-report.json).

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
|1|0|3|0|Author findings collected and scoped fixes applied|
|2|0|0|not tallied|Author verification; independent gates followed|

Hygiene: final changed-line check passes; reference Nits remain visible in the raw review.
Pre-lint: author evidence retained privately; final strict PyYAML/caps/corpus checks pass.

| Pass | Finding | Level | Action |
|---|---|---|---|
|F|The source had no functional and trigger eval suites.|Medium|Add realistic source-bound cases and a source trigger corpus.|
|P|The source lacked the applicable llms-first section.|Medium|Added size-bounded lookup and source verification guidance.|
|M|The description lacked concrete activation and exclusion boundaries.|Medium|Added domain-specific TRIGGER and SKIP clauses.|
|F/H|History growth prevented a balanced audit projection|Medium|Focused history-safe projector and6 regression methods; source history unchanged|

eval: predicted (independent frontmatter reader; no activation harness).

| Metric | Result | Target | Pass? |
|---|---|---|---|
|Should trigger|10/10|≥9/10|yes|
|False positives|0/10|≤1/10|yes|

Unified diff previews below cover this source's final write set, capped at80 lines per file.

````diff
--- baseline/.agents/skills/skill-registry/SKILL.md
+++ .agents/skills/skill-registry/SKILL.md
@@ -1,7 +1,31 @@
 ---
 name: skill-registry
-description: Find and load indexed local skills, share pinned private skill releases, or queue optional artifact optimization through the Skill Registry MCP and CLI.
+description: 'Find and load indexed local skills, manage pinned private skill releases, or queue explicitly requested optimization.
+  TRIGGER: find a skill for this task; load an exact skill hash; inspect a private skill release; queue an optimizer job.
+  Catalog search does not enable automatic policies. SKIP: direct skill audit and rewrite -> skill-optimizer; concept research
+  -> dr.'
+version: 1.1.0
+category: meta
+model: gpt-6.1-sol
+effort: medium
+whenToUse:
+- Find the most specific installed skill for this task
+- Load this skill using the returned source hash
+- Inspect or fetch a pinned private skill release
+- Queue an explicitly requested artifact optimization job
+triggers:
+- find a local skill
+- load skill by source hash
+- private skill release
+- queue optimizer job
+related_skills:
+- skill-optimizer
+- dr
+updated: '2026-11-11'
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---
+

 # Skill Registry

@@ -42,3 +66,12 @@
 Use `skills_status` to report coverage and `skills_refresh` for a requested
 refresh. The router does not require Ollama or start legacy embedding pipelines.
 For CLI details, use `skill-registry --help` and its command-specific help.
+
+## Look for llms files first
+
+Before reading the subject raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
+1. Locate the subject's `llms.txt`, source-qualified concept pack, or relevant documentation index. Existing keyword hits can help locate it.
+2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map.
+4. If you have the repo, search the code before opening an llms file. The code is the authority. Verify each fact against its source `path:line`.
+5. Index and llms hits are leads. Confirm their sources before acting.
````

````diff
--- baseline/.agents/skills/skill-registry/evals/README.md
+++ .agents/skills/skill-registry/evals/README.md
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
--- baseline/.agents/skills/skill-registry/evals/evals.json
+++ .agents/skills/skill-registry/evals/evals.json
@@ -0,0 +1,64 @@
+{
+  "skill_name": "skill-registry",
+  "version": "1.0.0",
+  "evaluation_contract": "Structural and negative scenario assertions require fresh blind prediction; no target workflow execution is implied.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "stale-source",
+      "prompt": "The skill lookup hash is older than the source returned by load.",
+      "expected_output": "Refresh lookup and preserve source identity before loading a pinned revision.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "stale-source-1",
+          "type": "negative",
+          "check": "Does not claim stale-hash content is current."
+        },
+        {
+          "name": "stale-source-2",
+          "type": "structural",
+          "check": "Keeps same-name canonical sources and installation aliases distinct."
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "optimizer-snapshot",
+      "prompt": "An optimizer job is queued and structural checks passed. Is the source now optimized?",
+      "expected_output": "Separate queued snapshot, actual worker execution, checks, model convergence and publication.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "optimizer-snapshot-1",
+          "type": "negative",
+          "check": "Does not infer native optimizer convergence from structural checks or exit zero."
+        },
+        {
+          "name": "optimizer-snapshot-2",
+          "type": "negative",
+          "check": "Does not overwrite the original as a side effect of queue submission."
+        }
+      ]
+    },
+    {
+      "id": 3,
+      "name": "private-release",
+      "prompt": "Install this private release into a destination that already holds another skill.",
+      "expected_output": "Preserve existing installations and require a new authorized destination with exact release integrity.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "private-release-1",
+          "type": "structural",
+          "check": "Uses exact release SHA256 and member validation."
+        },
+        {
+          "name": "private-release-2",
+          "type": "negative",
+          "check": "Does not enable library-wide auto-optimization or change disabled installation policy."
+        }
+      ]
+    }
+  ]
+}
````

````diff
--- baseline/.agents/skills/skill-registry/evals/project_triggers.py
+++ .agents/skills/skill-registry/evals/project_triggers.py
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
--- baseline/.agents/skills/skill-registry/evals/trigger-corpus.jsonl
+++ .agents/skills/skill-registry/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Find the most specific local skill for this task", "should_trigger": true, "source": "new domain-specific audit query", "id": 1, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Load a skill using its returned source hash", "should_trigger": true, "source": "new domain-specific audit query", "id": 2, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Show the source identity behind this skill match", "should_trigger": true, "source": "new domain-specific audit query", "id": 3, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Inspect a pinned private skill release", "should_trigger": true, "source": "new domain-specific audit query", "id": 4, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Fetch this exact skill release SHA256", "should_trigger": true, "source": "new domain-specific audit query", "id": 5, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Check local skill catalog coverage", "should_trigger": true, "source": "new domain-specific audit query", "id": 6, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Queue an explicitly requested document optimization job", "should_trigger": true, "source": "new domain-specific audit query", "id": 7, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Show optimizer_status and recorded checks for a queued skill job", "should_trigger": true, "source": "new domain-specific audit query", "id": 8, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Find a skill without loading every match", "should_trigger": true, "source": "new domain-specific audit query", "id": 9, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Refresh the requested local skill catalog", "should_trigger": true, "source": "new domain-specific audit query", "id": 10, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Run the full skill-optimizer audit on this SKILL.md", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 11, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Research an unresolved scientific concept", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 12, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Start all automatic optimization policies", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 13, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Import an entire private research corpus", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 14, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Design a Neo4j graph schema", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 15, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Train a language model", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 16, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Deploy a public website", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 17, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Optimize this SQL statement directly", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 18, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Rewrite a marketing paragraph directly", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 19, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Audit a subagent tool-permission definition", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 20, "description_sha256": "7a2f8be846fff2c17407164092e6b10524bff538caf42124234b3f79237cf6df", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
````

````diff
--- baseline/.agents/skills/skill-registry/evals/trigger-eval.json
+++ .agents/skills/skill-registry/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Find the most specific local skill for this task",
+    "should_trigger": true
+  },
+  {
+    "query": "Load a skill using its returned source hash",
+    "should_trigger": true
+  },
+  {
+    "query": "Show the source identity behind this skill match",
+    "should_trigger": true
+  },
+  {
+    "query": "Inspect a pinned private skill release",
+    "should_trigger": true
+  },
+  {
+    "query": "Fetch this exact skill release SHA256",
+    "should_trigger": true
+  },
+  {
+    "query": "Check local skill catalog coverage",
+    "should_trigger": true
+  },
+  {
+    "query": "Queue an explicitly requested document optimization job",
+    "should_trigger": true
+  },
+  {
+    "query": "Show optimizer_status and recorded checks for a queued skill job",
+    "should_trigger": true
+  },
+  {
+    "query": "Find a skill without loading every match",
+    "should_trigger": true
+  },
+  {
+    "query": "Refresh the requested local skill catalog",
+    "should_trigger": true
+  },
+  {
+    "query": "Run the full skill-optimizer audit on this SKILL.md",
+    "should_trigger": false
+  },
+  {
+    "query": "Research an unresolved scientific concept",
+    "should_trigger": false
+  },
+  {
+    "query": "Start all automatic optimization policies",
+    "should_trigger": false
+  },
+  {
+    "query": "Import an entire private research corpus",
+    "should_trigger": false
+  },
+  {
+    "query": "Design a Neo4j graph schema",
+    "should_trigger": false
+  },
+  {
+    "query": "Train a language model",
+    "should_trigger": false
+  },
+  {
+    "query": "Deploy a public website",
+    "should_trigger": false
+  },
+  {
+    "query": "Optimize this SQL statement directly",
+    "should_trigger": false
+  },
+  {
+    "query": "Rewrite a marketing paragraph directly",
+    "should_trigger": false
+  },
````
Preview truncated: 85 diff lines.

````diff
--- baseline/.agents/skills/skill-registry/references/CHANGELOG.md
+++ .agents/skills/skill-registry/references/CHANGELOG.md
@@ -0,0 +1,5 @@
+2026-11-11 final SKO TASK-1372: A–P and bounded independent rechecks recorded; exploratory predicted triggers; scoped operational exit DEGRADED. Raw dissent and focused correction receipts remain in the repository review ledger. No measured activation, semantic refresh or empirical promotion.
+
+2026-11-11 SKO unversioned to 1.1.0: scoped source, routing and evaluation repairs. Author trigger predictions: 10/10 positive, 0/10 false positive. Fresh blind review and global routing remain pending; no measured activation or empirical promotion.
+
+# Change log
````

| Eval | Result | Level | Files present? |
|---|---|---|---|
|Trigger|pos10/10; false-positive0/10|predicted|yes|
|Behavior|6/6 assertions across3 cases|predicted source support|yes|

index-discovery: degraded; bounded read-only keyword results and installed-source leads are in the ledger.

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
|.agents/skills/skill-registry/SKILL.md|selected repository source|6f531fb78f1696426b12a9de91f3329cfb69a0a3893bb0112cf8eec11ff528bd|scoped source edits|34efccf86756b7cb37c2dd36f95028c2b330dc19be6fedf2714b7b2e96237efc|
|External installed sources|independently owned copies|see locations.json|preserved divergence|unchanged|

llms-first: present; authoritative source verification retained.

| Skill | Verdict | Indexed description matches? | Own intent surfaces? | Stale rows |
|---|---|---|---|---|
|skill-registry|stale; rebuild withheld|no|not probed under pause|see routing.json|

prose-index: existing daemon observed up; no restart or forced refresh.
index: skipped for the global catalog under repository scope and existing pauses.
degraded: semantic discovery, candidate registration and global catalog refresh did not land; exit DEGRADED.
model/effort: see final source frontmatter and centrally recorded advisory-source limits.
Snapshot & rollback (entrypoint): `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/root/skill-registry/baseline/SKILL.md" ".agents/skills/skill-registry/SKILL.md"`.
Telemetry: scoped private task ledger; global ledger not rewritten.

Summary: bounded audit and focused correction evidence complete; no measured activation,
empirical promotion, full factual recertification or global installation acceptance.
Modified sections and exact file hashes are in the diff previews and source integrity manifest.
