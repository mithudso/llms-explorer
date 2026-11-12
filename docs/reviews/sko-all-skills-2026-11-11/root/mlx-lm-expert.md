# mlx-lm-expert — final scoped SKO receipt

The source audit is complete with operational DEGRADED status. Raw bounded dissent
and subsequent focused corrections remain separate in the [final ledger](../final-report.json).

| Iter | High | Medium | Low | Action |
|---|---:|---:|---:|---|
|1|0|4|0|Author findings collected and scoped fixes applied|
|2|0|0|not tallied|Author verification; independent gates followed|

Hygiene: final changed-line check passes; reference Nits remain visible in the raw review.
Pre-lint: author evidence retained privately; final strict PyYAML/caps/corpus checks pass.

| Pass | Finding | Level | Action |
|---|---|---|---|
|F|The source had no functional and trigger eval suites.|Medium|Add realistic source-bound cases and a source trigger corpus.|
|P|The source lacked the applicable llms-first section.|Medium|Added size-bounded lookup and source verification guidance.|
|D|An answer could omit version/date or native-versus-external limits.|Medium|Added an explicit response contract without changing factual references.|
|A|The former Mac runtime expert id could not be resolved in the installed catalog or manifests.|Medium|Use the verified ai-llm-model-layer and apple-hardware-router peers for general runtime and hardware topics.|
|F/H|History growth prevented a balanced audit projection|Medium|Focused history-safe projector and6 regression methods; source history unchanged|

eval: predicted (independent frontmatter reader; no activation harness).

| Metric | Result | Target | Pass? |
|---|---|---|---|
|Should trigger|10/10|≥9/10|yes|
|False positives|0/10|≤1/10|yes|

Unified diff previews below cover this source's final write set, capped at80 lines per file.

````diff
--- baseline/.agents/skills/mlx-lm-expert/SKILL.md
+++ .agents/skills/mlx-lm-expert/SKILL.md
@@ -1,41 +1,62 @@
 ---
 name: mlx-lm-expert
-description: >-
-  Explain MLX-LM. TRIGGER: 'configure LoRA'; 'fix streaming'; 'integrate GRPO'. Scope: DoRA/data/losses, sampling/vision, PPL, HTTP, loaders/cache/versions, distributed. SKIP: general PEFT -> ai-llm-model-layer; Mac hardware/runtimes -> running-llm-models-locally-on-mac-expert; new research -> dr.
-version: 1.0.0
-updated: '2026-10-23'
+description: 'Explain source-qualified MLX-LM training, generation and native service contracts. TRIGGER: MLX-LM LoRA or DoRA;
+  stream_generate; MLX-LM HTTP cancellation; native loss APIs versus external GRPO or distillation wrappers. Read the matching
+  dated reference. SKIP: general PEFT -> ai-llm-model-layer; general runtime selection -> ai-llm-model-layer; Mac hardware
+  -> apple-hardware-router; new source research -> dr.'
+version: 1.1.0
+updated: '2026-11-11'
 category: custom
 keywords:
-  - mlx-lm
-  - LoRA
-  - QLoRA
-  - DoRA
-  - fine-tuning
-  - prompt masking
-  - adapter fusion
-  - stream_generate
-  - logits processors
-  - perplexity
-  - distributed training
-  - Hugging Face cache
-  - request cancellation
-  - vision inputs
-  - distillation loss
-  - teacher student distillation
-  - GRPO
-  - GSPO
-  - external integration
-tags: [mlx-lm, apple-silicon, fine-tuning, inference]
+- mlx-lm
+- LoRA
+- QLoRA
+- DoRA
+- fine-tuning
+- prompt masking
+- adapter fusion
+- stream_generate
+- logits processors
+- perplexity
+- distributed training
+- Hugging Face cache
+- request cancellation
+- vision inputs
+- distillation loss
+- teacher student distillation
+- GRPO
+- GSPO
+- external integration
+tags:
+- mlx-lm
+- apple-silicon
+- fine-tuning
+- inference
 whenToUse:
-  - Configure MLX-LM training data, adapters and optimization
-  - Use MLX-LM Python generation, sampling and evaluation APIs
-  - Diagnose MLX-LM service, model-loading or release compatibility behavior
-  - Understand native DoRA and distributed fine-tuning limits
-  - Check speculative processor rollback, vision caching and request cancellation
-  - Distinguish native loss primitives from external training workflows
-  - Trace external distillation and GRPO/GSPO APIs, rollout metadata and adapter files
-related_skills: [ai-llm-model-layer, running-llm-models-locally-on-mac-expert, dr]
+- Configure MLX-LM training data, adapters and optimization
+- Use MLX-LM Python generation, sampling and evaluation APIs
+- Diagnose MLX-LM service, model-loading or release compatibility behavior
+- Understand native DoRA and distributed fine-tuning limits
+- Check speculative processor rollback, vision caching and request cancellation
+- Distinguish native loss primitives from external training workflows
+- Trace external distillation and GRPO/GSPO APIs, rollout metadata and adapter files
+related_skills:
+- ai-llm-model-layer
+- dr
````
Preview truncated: 123 diff lines.

````diff
--- baseline/.agents/skills/mlx-lm-expert/evals/README.md
+++ .agents/skills/mlx-lm-expert/evals/README.md
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
--- baseline/.agents/skills/mlx-lm-expert/evals/evals.json
+++ .agents/skills/mlx-lm-expert/evals/evals.json
@@ -0,0 +1,64 @@
+{
+  "skill_name": "mlx-lm-expert",
+  "version": "1.0.0",
+  "evaluation_contract": "Structural and negative scenario assertions require fresh blind prediction; no target workflow execution is implied.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "training-layer-scope",
+      "prompt": "If I select full fine-tuning with num-layers set, does every MLX-LM base weight train?",
+      "expected_output": "Read the training reference and preserve the documented layer-selection qualification.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "training-layer-scope-1",
+          "type": "structural",
+          "check": "Retains the num-layers qualification rather than using the generic definition of full fine-tuning."
+        },
+        {
+          "name": "training-layer-scope-2",
+          "type": "structural",
+          "check": "Cites the matching source-qualified training reference."
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "external-grpo",
+      "prompt": "Can I describe an external GRPO wrapper as a native MLX-LM feature?",
+      "expected_output": "Separate native loss APIs from the external training wrapper and retain version/compatibility limits.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "external-grpo-1",
+          "type": "structural",
+          "check": "Distinguishes native MLX-LM APIs from the external integration."
+        },
+        {
+          "name": "external-grpo-2",
+          "type": "negative",
+          "check": "Does not claim an external prototype proves current native support."
+        }
+      ]
+    },
+    {
+      "id": 3,
+      "name": "local-benchmark",
+      "prompt": "What throughput did you measure on my hardware from these notes?",
+      "expected_output": "State that source research does not establish a local benchmark and name any missing measurement.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "local-benchmark-1",
+          "type": "negative",
+          "check": "Does not fabricate an executed benchmark."
+        },
+        {
+          "name": "local-benchmark-2",
+          "type": "structural",
+          "check": "Routes hardware/runtime qualification to the appropriate requested work."
+        }
+      ]
+    }
+  ]
+}
````

````diff
--- baseline/.agents/skills/mlx-lm-expert/evals/project_triggers.py
+++ .agents/skills/mlx-lm-expert/evals/project_triggers.py
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
--- baseline/.agents/skills/mlx-lm-expert/evals/trigger-corpus.jsonl
+++ .agents/skills/mlx-lm-expert/evals/trigger-corpus.jsonl
@@ -0,0 +1,20 @@
+{"query": "Explain MLX-LM fine-tune-type full and num-layers", "should_trigger": true, "source": "new domain-specific audit query", "id": 1, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Find the MLX-LM LoRA data-masking reference", "should_trigger": true, "source": "new domain-specific audit query", "id": 2, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Trace MLX-LM stream_generate cancellation", "should_trigger": true, "source": "new domain-specific audit query", "id": 3, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Which MLX-LM logits processor contract covers rollback?", "should_trigger": true, "source": "new domain-specific audit query", "id": 4, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Does the reference describe native MLX-LM DoRA?", "should_trigger": true, "source": "new domain-specific audit query", "id": 5, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Compare native loss primitives with external GRPO wrappers in the MLX-LM notes", "should_trigger": true, "source": "new domain-specific audit query", "id": 6, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Find the MLX-LM HTTP streaming error contract", "should_trigger": true, "source": "new domain-specific audit query", "id": 7, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Explain the cited MLX-LM vision-cache limitation", "should_trigger": true, "source": "new domain-specific audit query", "id": 8, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Where are MLX-LM adapter fusion and export documented?", "should_trigger": true, "source": "new domain-specific audit query", "id": 9, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Show the dated MLX-LM distributed fine-tuning limits", "should_trigger": true, "source": "new domain-specific audit query", "id": 10, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": true, "reason": "The description names this workflow or domain."}
+{"query": "Explain general PEFT theory without a specific library", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 11, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Which Mac should I buy for local inference?", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 12, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Enable Apple Intelligence Siri features", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 13, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Implement a PyTorch distributed training launcher", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 14, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Run new source research on an unreviewed library", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 15, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Audit skill routing collisions", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 16, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Search the private skill release catalog", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 17, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Optimize a MongoDB query plan", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 18, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Compare cloud GPU rental prices", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 19, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
+{"query": "Fix a generic HTTP proxy unrelated to MLX-LM", "should_trigger": false, "source": "new adjacent-intent near miss", "id": 20, "description_sha256": "1c71cd75d65cbf1106f96ec9b55a66d185cfe15b6ffb0c5fadabde4148879806", "skill_version": "1.1.0", "evaluated_at": "2026-11-11", "level": "predicted", "predicted_trigger": false, "reason": "This adjacent task belongs to an excluded workflow or different domain; this description does not authorize it."}
````

````diff
--- baseline/.agents/skills/mlx-lm-expert/evals/trigger-eval.json
+++ .agents/skills/mlx-lm-expert/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Explain MLX-LM fine-tune-type full and num-layers",
+    "should_trigger": true
+  },
+  {
+    "query": "Find the MLX-LM LoRA data-masking reference",
+    "should_trigger": true
+  },
+  {
+    "query": "Trace MLX-LM stream_generate cancellation",
+    "should_trigger": true
+  },
+  {
+    "query": "Which MLX-LM logits processor contract covers rollback?",
+    "should_trigger": true
+  },
+  {
+    "query": "Does the reference describe native MLX-LM DoRA?",
+    "should_trigger": true
+  },
+  {
+    "query": "Compare native loss primitives with external GRPO wrappers in the MLX-LM notes",
+    "should_trigger": true
+  },
+  {
+    "query": "Find the MLX-LM HTTP streaming error contract",
+    "should_trigger": true
+  },
+  {
+    "query": "Explain the cited MLX-LM vision-cache limitation",
+    "should_trigger": true
+  },
+  {
+    "query": "Where are MLX-LM adapter fusion and export documented?",
+    "should_trigger": true
+  },
+  {
+    "query": "Show the dated MLX-LM distributed fine-tuning limits",
+    "should_trigger": true
+  },
+  {
+    "query": "Explain general PEFT theory without a specific library",
+    "should_trigger": false
+  },
+  {
+    "query": "Which Mac should I buy for local inference?",
+    "should_trigger": false
+  },
+  {
+    "query": "Enable Apple Intelligence Siri features",
+    "should_trigger": false
+  },
+  {
+    "query": "Implement a PyTorch distributed training launcher",
+    "should_trigger": false
+  },
+  {
+    "query": "Run new source research on an unreviewed library",
+    "should_trigger": false
+  },
+  {
+    "query": "Audit skill routing collisions",
+    "should_trigger": false
+  },
+  {
+    "query": "Search the private skill release catalog",
+    "should_trigger": false
+  },
+  {
+    "query": "Optimize a MongoDB query plan",
+    "should_trigger": false
+  },
+  {
+    "query": "Compare cloud GPU rental prices",
+    "should_trigger": false
+  },
````
Preview truncated: 85 diff lines.

````diff
--- baseline/.agents/skills/mlx-lm-expert/references/CHANGELOG.md
+++ .agents/skills/mlx-lm-expert/references/CHANGELOG.md
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
|.agents/skills/mlx-lm-expert/SKILL.md|selected repository source|d777d3d8a004c8c1ce2aeee2709820c45e1bce49f622d918d17efd5e5143a8c6|scoped source edits|024d2407cb4f0b7062a01e574b9ab295f86237a68d9a5352973109b7d1bfcc8f|
|External installed sources|independently owned copies|see locations.json|preserved divergence|unchanged|

llms-first: present; authoritative source verification retained.

| Skill | Verdict | Indexed description matches? | Own intent surfaces? | Stale rows |
|---|---|---|---|---|
|mlx-lm-expert|stale; rebuild withheld|no|not probed under pause|see routing.json|

prose-index: existing daemon observed up; no restart or forced refresh.
index: skipped for the global catalog under repository scope and existing pauses.
degraded: semantic discovery, candidate registration and global catalog refresh did not land; exit DEGRADED.
model/effort: see final source frontmatter and centrally recorded advisory-source limits.
Snapshot & rollback (entrypoint): `cp "$HOME/.local/state/llms-explorer-sko/task1372/workers/root/mlx-lm-expert/baseline/SKILL.md" ".agents/skills/mlx-lm-expert/SKILL.md"`.
Telemetry: scoped private task ledger; global ledger not rewritten.

Summary: bounded audit and focused correction evidence complete; no measured activation,
empirical promotion, full factual recertification or global installation acceptance.
Modified sections and exact file hashes are in the diff previews and source integrity manifest.
