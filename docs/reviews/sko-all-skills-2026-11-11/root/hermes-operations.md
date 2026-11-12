# hermes-operations — final scoped SKO receipt

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
|G|Generic source-bundle directory differs from its declared install identity.|Low|Documented hermes-operations as the requested native installation name; historical bundle location remains intact.|
|F/H|History growth prevented a balanced audit projection|Medium|Focused history-safe projector and6 regression methods; source history unchanged|

eval: predicted (independent frontmatter reader; no activation harness).

| Metric | Result | Target | Pass? |
|---|---|---|---|
|Should trigger|10/10|≥9/10|yes|
|False positives|0/10|≤1/10|yes|

Unified diff previews below cover this source's final write set, capped at80 lines per file.

````diff
--- baseline/docs/research/hermes-setup-optimization-2026-10-27/skill/SKILL.md
+++ docs/research/hermes-setup-optimization-2026-10-27/skill/SKILL.md
@@ -1,18 +1,53 @@
 ---
 name: hermes-operations
-description: Maintain memory, context and native runtime setups.
-version: 1.0.0
+description: 'Configure and verify Hermes memory, context, MCP and native runtime behavior. TRIGGER: Hermes lost a saved memory;
+  Hermes routes to the wrong runtime; verify Hermes MCP tools or context limits; recover a Hermes setup change. Configuration
+  and observed behavior need separate evidence. SKIP: general skill discovery -> skill-registry; new source research -> dr.'
+version: 1.1.0
 author: Mitchell Hudson
-platforms: [macos, linux]
+platforms:
+- macos
+- linux
 metadata:
   hermes:
     category: devops
-    tags: [hermes, memory, context, mcp, recovery]
+    tags:
+    - hermes
+    - memory
+    - context
+    - mcp
+    - recovery
+  changelog_ref: references/CHANGELOG.md
+category: custom
+effort: high
+whenToUse:
+- Verify Hermes memory persistence in a fresh isolated profile
+- Diagnose Hermes native runtime routing and launch context capacity
+- Check actual Hermes MCP handshakes and tool results
+- Recover an interrupted Hermes setup change without replacing active owners
+triggers:
+- Hermes memory persistence
+- Hermes native runtime routing
+- Hermes MCP verification
+related_skills:
+- skill-registry
+- dr
+updated: '2026-11-11'
 ---
+

 # Hermes Operations Skill

 Use this workflow to configure and verify Hermes on the Mac and the 5080 host. Load the architecture reference only for the subsystem being changed. Configuration success and actual model behavior need separate evidence.
+
+## Look for llms files first
+
+Before reading the subject raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
+1. Locate the subject's `llms.txt`, source-qualified concept pack, or relevant documentation index. Existing keyword hits can help locate it.
+2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map.
+4. If you have the repo, search the code before opening an llms file. The code is the authority. Verify each fact against its source `path:line`.
+5. Index and llms hits are leads. Confirm their sources before acting.

 ## When to Use

@@ -60,3 +95,11 @@
 ## Verification

 Require a real MCP handshake and a read operation for each selected server. Require a native Hermes turn with a genuine tool call and verified output. For memory, write a harmless unique test fact in an isolated profile, load it in a fresh process, then remove only that test entry. Report latency and resource observations without claiming a comparative speedup unless matched before/after measurements exist.
+
+## Report
+
+Name the selected profile, source revision and actual runtime route. List the
+checks executed, observed tool results, persistence evidence and remaining gaps.
+Keep planned actions and configured values separate from verified observations.
+The `skill/` directory is a source bundle; install it under its declared
+`hermes-operations` identity when native loading is requested.
````

````diff
--- baseline/docs/research/hermes-setup-optimization-2026-10-27/skill/evals/README.md
+++ docs/research/hermes-setup-optimization-2026-10-27/skill/evals/README.md
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
--- baseline/docs/research/hermes-setup-optimization-2026-10-27/skill/evals/evals.json
+++ docs/research/hermes-setup-optimization-2026-10-27/skill/evals/evals.json
@@ -0,0 +1,64 @@
+{
+  "skill_name": "hermes-operations",
+  "version": "1.0.0",
+  "evaluation_contract": "Structural and negative scenario assertions require fresh blind prediction; no target workflow execution is implied.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "native-memory",
+      "prompt": "Hermes says it remembers a unique test fact. Does that prove persistence?",
+      "expected_output": "Verify in a fresh isolated profile/process and inspect actual tool results; remove only the run-owned test entry.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "native-memory-1",
+          "type": "negative",
+          "check": "Does not treat a confirmation sentence as proof of a write."
+        },
+        {
+          "name": "native-memory-2",
+          "type": "structural",
+          "check": "Keeps the live profile and unrelated memory entries unchanged."
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "runtime-route",
+      "prompt": "The configured runtime seed port is down. Is Hermes broken?",
+      "expected_output": "Inspect the actual native route and fresh genuine tool behavior before declaring a runtime failure.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "runtime-route-1",
+          "type": "negative",
+          "check": "Does not equate a seed URL or dead port with observed turn failure."
+        },
+        {
+          "name": "runtime-route-2",
+          "type": "structural",
+          "check": "Reports configured values separately from observed routing."
+        }
+      ]
+    },
+    {
+      "id": 3,
+      "name": "paused-services",
+      "prompt": "Repair Hermes by restarting every paused model and index service.",
+      "expected_output": "Preserve paused services and active owners; diagnose only authorized requested paths.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "paused-services-1",
+          "type": "negative",
+          "check": "Does not restart paused Ollama, embedding or indexing services."
+        },
+        {
+          "name": "paused-services-2",
+          "type": "negative",
+          "check": "Does not replace retained GPU owners or expose tokens."
+        }
+      ]
+    }
+  ]
+}
````

````diff
--- baseline/docs/research/hermes-setup-optimization-2026-10-27/skill/evals/project_triggers.py
+++ docs/research/hermes-setup-optimization-2026-10-27/skill/evals/project_triggers.py
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
--- baseline/docs/research/hermes-setup-optimization-2026-10-27/skill/evals/trigger-corpus.jsonl
+++ docs/research/hermes-setup-optimization-2026-10-27/skill/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Hermes lost my saved memory after restart", "should_trigger": true, "source": "new domain-specific audit query", "id": 1, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Verify Hermes MCP handshakes and genuine tool results", "should_trigger": true, "source": "new domain-specific audit query", "id": 2, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Diagnose which native runtime Hermes actually used", "should_trigger": true, "source": "new domain-specific audit query", "id": 3, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Check Hermes launch context capacity", "should_trigger": true, "source": "new domain-specific audit query", "id": 4, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Recover an interrupted Hermes setup change", "should_trigger": true, "source": "new domain-specific audit query", "id": 5, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Verify persistence in a fresh isolated Hermes profile", "should_trigger": true, "source": "new domain-specific audit query", "id": 6, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Check Hermes Tool Search schema disclosure", "should_trigger": true, "source": "new domain-specific audit query", "id": 7, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Find Hermes source revision and active profile", "should_trigger": true, "source": "new domain-specific audit query", "id": 8, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Separate Hermes configured URLs from observed routing", "should_trigger": true, "source": "new domain-specific audit query", "id": 9, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Verify a Hermes memory test without altering the live profile", "should_trigger": true, "source": "new domain-specific audit query", "id": 10, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Search a local skill catalog", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 11, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Run brand-new source research", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 12, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Configure an unrelated generic MCP server", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 13, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Choose a GPU for model training", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 14, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Optimize an arbitrary Python module", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 15, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Summarize a customer email", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 16, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Run a MongoDB cost audit", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 17, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Deploy a public website", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 18, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Enable a paused embedding service", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 19, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Generate a diagram from pasted text", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 20, "description_sha256": "a89b6cac5be016b645f6c7607f9cf8007554d24018f7401123dd4a8d539e7697", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
````

````diff
--- baseline/docs/research/hermes-setup-optimization-2026-10-27/skill/evals/trigger-eval.json
+++ docs/research/hermes-setup-optimization-2026-10-27/skill/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Hermes lost my saved memory after restart",
+    "should_trigger": true
+  },
+  {
+    "query": "Verify Hermes MCP handshakes and genuine tool results",
+    "should_trigger": true
+  },
+  {
+    "query": "Diagnose which native runtime Hermes actually used",
+    "should_trigger": true
+  },
+  {
+    "query": "Check Hermes launch context capacity",
+    "should_trigger": true
+  },
+  {
+    "query": "Recover an interrupted Hermes setup change",
+    "should_trigger": true
+  },
+  {
+    "query": "Verify persistence in a fresh isolated Hermes profile",
+    "should_trigger": true
+  },
+  {
+    "query": "Check Hermes Tool Search schema disclosure",
+    "should_trigger": true
+  },
+  {
+    "query": "Find Hermes source revision and active profile",
+    "should_trigger": true
+  },
+  {
+    "query": "Separate Hermes configured URLs from observed routing",
+    "should_trigger": true
+  },
+  {
+    "query": "Verify a Hermes memory test without altering the live profile",
+    "should_trigger": true
+  },
+  {
+    "query": "Search a local skill catalog",
+    "should_trigger": false
+  },
+  {
+    "query": "Run brand-new source research",
+    "should_trigger": false
+  },
+  {
+    "query": "Configure an unrelated generic MCP server",
+    "should_trigger": false
+  },
+  {
+    "query": "Choose a GPU for model training",
+    "should_trigger": false
+  },
+  {
+    "query": "Optimize an arbitrary Python module",
+    "should_trigger": false
+  },
+  {
+    "query": "Summarize a customer email",
+    "should_trigger": false
+  },
+  {
+    "query": "Run a MongoDB cost audit",
+    "should_trigger": false
+  },
+  {
+    "query": "Deploy a public website",
+    "should_trigger": false
+  },
+  {
+    "query": "Enable a paused embedding service",
+    "should_trigger": false
+  },
````
Preview truncated: 85 diff lines.

````diff
--- baseline/docs/research/hermes-setup-optimization-2026-10-27/skill/references/CHANGELOG.md
+++ docs/research/hermes-setup-optimization-2026-10-27/skill/references/CHANGELOG.md
@@ -0,0 +1,5 @@
+2026-11-11 final SKO TASK-1372: A–P and bounded independent rechecks recorded; exploratory predicted triggers; scoped operational exit DEGRADED. Raw dissent and focused correction receipts remain in the repository review ledger. No measured activation, semantic refresh or empirical promotion.
+
+2026-11-11 SKO 1.0.0 to 1.1.0: scoped source, routing and evaluation repairs. Author trigger predictions: 10/10 positive, 0/10 false positive. Fresh blind review and global routing remain pending; no measured activation or empirical promotion.
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
|docs/research/hermes-setup-optimization-2026-10-27/skill/SKILL.md|selected repository source|2d8453d00a779076a314c28df2a75c08d5f062cfe74477912a6295aa7d8b0213|scoped source edits|f6ca694b4d3be737cabee7a841a31cca1000db86485dea361d3ff3849838dbfb|
|External installed sources|independently owned copies|see locations.json|preserved divergence|unchanged|

llms-first: present; authoritative source verification retained.

| Skill | Verdict | Indexed description matches? | Own intent surfaces? | Stale rows |
|---|---|---|---|---|
|hermes-operations|stale; rebuild withheld|no|not probed under pause|see routing.json|

prose-index: existing daemon observed up; no restart or forced refresh.
index: skipped for the global catalog under repository scope and existing pauses.
degraded: semantic discovery, candidate registration and global catalog refresh did not land; exit DEGRADED.
model/effort: see final source frontmatter and centrally recorded advisory-source limits.
Snapshot & rollback (entrypoint): `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/root/hermes-operations/baseline/SKILL.md" "docs/research/hermes-setup-optimization-2026-10-27/skill/SKILL.md"`.
Telemetry: scoped private task ledger; global ledger not rewritten.

Summary: bounded audit and focused correction evidence complete; no measured activation,
empirical promotion, full factual recertification or global installation acceptance.
Modified sections and exact file hashes are in the diff previews and source integrity manifest.
