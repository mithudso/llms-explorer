# apple-intelligence — final scoped SKO receipt

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
|D|An answer could omit version/date or native-versus-external limits.|Medium|Added an explicit response contract without changing factual references.|
|F/H|History growth prevented a balanced audit projection|Medium|Focused history-safe projector and6 regression methods; source history unchanged|

eval: predicted (independent frontmatter reader; no activation harness).

| Metric | Result | Target | Pass? |
|---|---|---|---|
|Should trigger|10/10|≥9/10|yes|
|False positives|0/10|≤1/10|yes|

Unified diff previews below cover this source's final write set, capped at80 lines per file.

````diff
--- baseline/.agents/skills/apple-intelligence/SKILL.md
+++ .agents/skills/apple-intelligence/SKILL.md
@@ -1,23 +1,43 @@
 ---
 name: apple-intelligence
-version: "1.0.0"
-updated: "2026-10-23"
-description: >-
-  Explain Apple Intelligence product features, privacy and developer integration.
-  TRIGGER: Apple Intelligence eligibility; Siri AI; Writing Tools; Visual Intelligence;
-  image provenance; Shortcuts Use Model; managed controls; Private Cloud Compute;
-  ChatGPT consent; App Schemas, content transfer and AppIntentsTesting; Foundation Models capability,
-  provider, guardrails and OS changes. Read the matching dated reference first.
-  SKIP: MLX-LM training or runtime APIs -> mlx-lm-expert; new source research -> dr.
+version: 1.1.0
+updated: '2026-11-11'
+description: 'Explain Apple Intelligence product features, privacy and developer integration. TRIGGER: Apple Intelligence
+  eligibility; Siri AI; Writing Tools; Visual Intelligence; image provenance; Shortcuts Use Model; managed controls; Private
+  Cloud Compute; ChatGPT consent; App Schemas, content transfer and AppIntentsTesting; Foundation Models capability, provider,
+  guardrails and OS changes. Read the matching dated reference first. SKIP: MLX-LM training or runtime APIs -> mlx-lm-expert;
+  new source research -> dr.'
 category: developer
-keywords: [Apple Intelligence, Siri AI, Private Cloud Compute, Foundation Models, AppIntentsTesting, App Schemas, image provenance, Shortcuts, privacy, availability]
-related_skills: [mlx-lm-expert, dr]
+keywords:
+- Apple Intelligence
+- Siri AI
+- Private Cloud Compute
+- Foundation Models
+- AppIntentsTesting
+- App Schemas
+- image provenance
+- Shortcuts
+- privacy
+- availability
+related_skills:
+- mlx-lm-expert
+- dr
 whenToUse:
-  - Explain Apple Intelligence availability and supported product workflows
-  - Check privacy, external intelligence consent and managed-device controls
-  - Integrate and test Siri App Schemas, entities and contextual actions
-  - Reconcile dated Foundation Models and Private Cloud Compute API contracts
+- Explain Apple Intelligence eligibility using the dated product references
+- Check Private Cloud Compute privacy and ChatGPT consent boundaries
+- Find the documented App Schemas or AppIntentsTesting contract
+- Distinguish a dated Foundation Models source from verified device behavior
+model: gpt-6.1-sol
+effort: medium
+triggers:
+- Apple Intelligence eligibility
+- Private Cloud Compute
+- Siri App Schemas
+- Foundation Models contracts
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---
+

 # Apple Intelligence

@@ -26,6 +46,15 @@
 or an announcement does not establish behavior on a particular device or SDK build.
 For volatile availability, language, region, entitlement or quota details, refresh
 sources when the question requires a more recent answer than the reference provides.
+
+## Look for llms files first
+
+Before reading the subject raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
+1. Locate the subject's `llms.txt`, source-qualified concept pack, or relevant documentation index. Existing keyword hits can help locate it.
+2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map.
+4. If you have the repo, search the code before opening an llms file. The code is the authority. Verify each fact against its source `path:line`.
+5. Index and llms hits are leads. Confirm their sources before acting.

 ## Research references

@@ -53,3 +82,11 @@
 The suite report records partial competency-question coverage and the actual
 CFE exit status. Keyword retrieval and source verification do not establish
````
Preview truncated: 89 diff lines.

````diff
--- baseline/.agents/skills/apple-intelligence/evals/README.md
+++ .agents/skills/apple-intelligence/evals/README.md
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
--- baseline/.agents/skills/apple-intelligence/evals/evals.json
+++ .agents/skills/apple-intelligence/evals/evals.json
@@ -0,0 +1,64 @@
+{
+  "skill_name": "apple-intelligence",
+  "version": "1.0.0",
+  "evaluation_contract": "Structural and negative scenario assertions require fresh blind prediction; no target workflow execution is implied.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "dated-eligibility",
+      "prompt": "My device runs a later OS than the dated reference. Is every listed Apple Intelligence feature available?",
+      "expected_output": "Use the product reference with its date; separate documentation from device-tested behavior and name the unverified version gap.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "dated-eligibility-1",
+          "type": "negative",
+          "check": "Does not upgrade a dated statement into confirmed current device behavior."
+        },
+        {
+          "name": "dated-eligibility-2",
+          "type": "structural",
+          "check": "Names the relevant dated reference or the missing coverage."
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "app-intents",
+      "prompt": "Which reference should I consult before testing AppEntity content transfer and Siri integration?",
+      "expected_output": "Select the App Intents or cross-app content transfer reference and preserve its documented boundaries.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "app-intents-1",
+          "type": "structural",
+          "check": "Selects the narrow matching reference rather than unrelated creative features."
+        },
+        {
+          "name": "app-intents-2",
+          "type": "negative",
+          "check": "Does not claim a local SDK test was run."
+        }
+      ]
+    },
+    {
+      "id": 3,
+      "name": "wrong-domain",
+      "prompt": "Use these Apple Intelligence notes to train an MLX-LM LoRA adapter.",
+      "expected_output": "Defer training/runtime work to mlx-lm-expert.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "wrong-domain-1",
+          "type": "structural",
+          "check": "Routes the request to the named MLX-LM peer."
+        },
+        {
+          "name": "wrong-domain-2",
+          "type": "negative",
+          "check": "Does not invent training advice from Apple product-feature notes."
+        }
+      ]
+    }
+  ]
+}
````

````diff
--- baseline/.agents/skills/apple-intelligence/evals/project_triggers.py
+++ .agents/skills/apple-intelligence/evals/project_triggers.py
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
--- baseline/.agents/skills/apple-intelligence/evals/trigger-corpus.jsonl
+++ .agents/skills/apple-intelligence/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Does Apple Intelligence support my language and region?", "should_trigger": true, "source": "new domain-specific audit query", "id": 1, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Show the dated Private Cloud Compute privacy reference", "should_trigger": true, "source": "new domain-specific audit query", "id": 2, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Explain ChatGPT consent in Apple Intelligence", "should_trigger": true, "source": "new domain-specific audit query", "id": 3, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "What do the references say about Siri App Schemas?", "should_trigger": true, "source": "new domain-specific audit query", "id": 4, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Find the AppIntentsTesting fixture contract", "should_trigger": true, "source": "new domain-specific audit query", "id": 5, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Which source covers Shortcuts Use Model?", "should_trigger": true, "source": "new domain-specific audit query", "id": 6, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Explain Visual Intelligence eligibility with its date", "should_trigger": true, "source": "new domain-specific audit query", "id": 7, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Distinguish Foundation Models documentation from device testing", "should_trigger": true, "source": "new domain-specific audit query", "id": 8, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Check the reference for image provenance and export limits", "should_trigger": true, "source": "new domain-specific audit query", "id": 9, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Where are managed Apple Intelligence control limits documented?", "should_trigger": true, "source": "new domain-specific audit query", "id": 10, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Choose a USB-C dock for my MacBook", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 11, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Train a LoRA adapter using MLX-LM", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 12, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Write a general Python CSV parser", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 13, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Audit a Claude Code skill description", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 14, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Compare PyTorch and JAX training loops", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 15, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Configure MongoDB Atlas private endpoints", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 16, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Book an Apple Store repair appointment", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 17, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Create a customer research project", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 18, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Optimize a SQL aggregation query", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 19, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Start a new source-research investigation from scratch", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 20, "description_sha256": "c329fb4b809d475777bcce5c37cc4ac05a5f007d66798b528829049d2488f53e", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
````

````diff
--- baseline/.agents/skills/apple-intelligence/evals/trigger-eval.json
+++ .agents/skills/apple-intelligence/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Does Apple Intelligence support my language and region?",
+    "should_trigger": true
+  },
+  {
+    "query": "Show the dated Private Cloud Compute privacy reference",
+    "should_trigger": true
+  },
+  {
+    "query": "Explain ChatGPT consent in Apple Intelligence",
+    "should_trigger": true
+  },
+  {
+    "query": "What do the references say about Siri App Schemas?",
+    "should_trigger": true
+  },
+  {
+    "query": "Find the AppIntentsTesting fixture contract",
+    "should_trigger": true
+  },
+  {
+    "query": "Which source covers Shortcuts Use Model?",
+    "should_trigger": true
+  },
+  {
+    "query": "Explain Visual Intelligence eligibility with its date",
+    "should_trigger": true
+  },
+  {
+    "query": "Distinguish Foundation Models documentation from device testing",
+    "should_trigger": true
+  },
+  {
+    "query": "Check the reference for image provenance and export limits",
+    "should_trigger": true
+  },
+  {
+    "query": "Where are managed Apple Intelligence control limits documented?",
+    "should_trigger": true
+  },
+  {
+    "query": "Choose a USB-C dock for my MacBook",
+    "should_trigger": false
+  },
+  {
+    "query": "Train a LoRA adapter using MLX-LM",
+    "should_trigger": false
+  },
+  {
+    "query": "Write a general Python CSV parser",
+    "should_trigger": false
+  },
+  {
+    "query": "Audit a Claude Code skill description",
+    "should_trigger": false
+  },
+  {
+    "query": "Compare PyTorch and JAX training loops",
+    "should_trigger": false
+  },
+  {
+    "query": "Configure MongoDB Atlas private endpoints",
+    "should_trigger": false
+  },
+  {
+    "query": "Book an Apple Store repair appointment",
+    "should_trigger": false
+  },
+  {
+    "query": "Create a customer research project",
+    "should_trigger": false
+  },
+  {
+    "query": "Optimize a SQL aggregation query",
+    "should_trigger": false
+  },
````
Preview truncated: 85 diff lines.

````diff
--- baseline/.agents/skills/apple-intelligence/references/CHANGELOG.md
+++ .agents/skills/apple-intelligence/references/CHANGELOG.md
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
|.agents/skills/apple-intelligence/SKILL.md|selected repository source|eb8da73bfed1db4502749ec907f76b2c8cb50767d962b589fe5fd415242236d2|scoped source edits|2f6f67d5b66b0132164417817c271fde698e38fa85c34d8f64c402c4d36f1259|
|External installed sources|independently owned copies|see locations.json|preserved divergence|unchanged|

llms-first: present; authoritative source verification retained.

| Skill | Verdict | Indexed description matches? | Own intent surfaces? | Stale rows |
|---|---|---|---|---|
|apple-intelligence|stale; rebuild withheld|no|not probed under pause|see routing.json|

prose-index: existing daemon observed up; no restart or forced refresh.
index: skipped for the global catalog under repository scope and existing pauses.
degraded: semantic discovery, candidate registration and global catalog refresh did not land; exit DEGRADED.
model/effort: see final source frontmatter and centrally recorded advisory-source limits.
Snapshot & rollback (entrypoint): `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/root/apple-intelligence/baseline/SKILL.md" ".agents/skills/apple-intelligence/SKILL.md"`.
Telemetry: scoped private task ledger; global ledger not rewritten.

Summary: bounded audit and focused correction evidence complete; no measured activation,
empirical promotion, full factual recertification or global installation acceptance.
Modified sections and exact file hashes are in the diff previews and source integrity manifest.
