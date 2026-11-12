# /sko receipt: artifact-to-procedure

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 0 | 6 | applied anchored source fixes and generated/supplemented evals |
| 2 | 0 | 0 | author re-audit/static verification; no independent-clean claim |
| 3 | 0 | 1 | repaired corroborated blind/integration findings in one bounded round; final author residual count zero, independent recheck pending |

Hygiene: final scoped diff/Markdown checks clean; no severity credit for byte cleanup.
Pre-lint: inherited result is retained in JSON; the illustrative `file.md` index link remains a documented false positive for memory export. Parsed descriptions are all ≤1000 characters.

| Finding | Level | Action |
|---|---|---|
| BI-ING-001 | Medium | Parsed YAML identifiers and aliases remain whole; folding occurs only between complete tokens. |

eval: predicted (no Claude activation harness; no empirical gain claim).

| Metric | Result | Target |
|---|---:|---:|
| should-trigger | 10/10 | ≥9/10 |
| false-positive | 0/10 | ≤1/10 |

Repair diff preview, bounded excerpts:

````diff
--- repair-preimage/SKILL.md
+++ repaired/SKILL.md
@@ -6,9 +6,9 @@
   the method", "capture this workflow", "make what we did reusable". SKIP: a new skill with no
   completed artifact → skill-creator; organizing continuity notes → note-organizer; API or
-  project documentation → technical-writing-craft; a one-document fact inventory → llms-txt-
-  tooling (references/document-distiller.md).
+  project documentation → technical-writing-craft; a one-document fact inventory →
+  llms-txt-tooling (references/document-distiller.md).
 model: claude-opus-5-5
 effort: high
-version: 1.2.0
+version: 1.2.1
 updated: '2026-11-11'
 category: meta
````
````diff
--- repair-preimage/evals/test_routing_surface.py
+++ repaired/evals/test_routing_surface.py
@@ -0,0 +1,33 @@
+"""Parsed routing identifiers must survive the YAML representation intact."""
+import os
+from pathlib import Path
+import re
+
+import pytest
+import yaml
+
+SKILLS = next(p for p in Path(__file__).resolve().parents
+              if p.name == "skills" and (p / "artifact-to-procedure/SKILL.md").is_file())
+SOURCE = Path(os.environ.get("SKO_TEST_SKILLS_ROOT", SKILLS))
+NAMES = ["artifact-to-procedure", "crawl-customer-to-llms", "crawl-repo-to-llms",
+         "crawl-to-llms-txt", "llms-concept-abstractor", "llms-deep-optimizer",
+         "memory-to-llms-txt", "note-organizer", "notes-to-llms", "notes-to-llms-txt",
+         "skill-tree-architect"]
+
+
+@pytest.mark.parametrize("name", NAMES)
+def test_folded_description_preserves_complete_tokens(name):
+    description = yaml.safe_load((SOURCE / name / "SKILL.md").read_text().split("---", 2)[1])["description"]
+    assert not re.search(r"[\w/][\w/-]*-\s+[a-z][\w-]*(?:\.[a-z]+)?", description), description
+    assert len(description) <= 1000
+
+
+@pytest.mark.parametrize("name,token", [
+    ("crawl-repo-to-llms", "/crawl-repo2llms"),
+    ("memory-to-llms-txt", "notes-to-llms-txt"),
+    ("note-organizer", "content-ingestion-extraction"),
+    ("notes-to-llms", "references/document-distiller.md"),
+])
+def test_concrete_alias_and_deferral_tokens(name, token):
+    description = yaml.safe_load((SOURCE / name / "SKILL.md").read_text().split("---", 2)[1])["description"]
+    assert token in description
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "artifact-to-procedure-01", "query": "Turn this completed deployment into a reusable procedure.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "7a0e69cfaf2beecaec1ef30c9f448e852d235737f3fef07354a0ed367c4bf502", "skill_version": "1.2.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "artifact-to-procedure-02", "query": "Extract the method from the incident we just solved.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "7a0e69cfaf2beecaec1ef30c9f448e852d235737f3fef07354a0ed367c4bf502", "skill_version": "1.2.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "artifact-to-procedure-03", "query": "Capture what we did as a playbook for the next project.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "7a0e69cfaf2beecaec1ef30c9f448e852d235737f3fef07354a0ed367c4bf502", "skill_version": "1.2.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "artifact-to-procedure-04", "query": "Make the completed onboarding workflow reusable.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "7a0e69cfaf2beecaec1ef30c9f448e852d235737f3fef07354a0ed367c4bf502", "skill_version": "1.2.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "artifact-to-procedure-05", "query": "Convert this successful session into a skill, with transfer limits.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "7a0e69cfaf2beecaec1ef30c9f448e852d235737f3fef07354a0ed367c4bf502", "skill_version": "1.2.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # artifact-to-procedure changelog

+- 2026-11-11 /sko repair 1.2.0 → 1.2.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.1.1 → 1.2.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 8 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `d2dd32839b0c9f583ef934dc04fb024c24e5b98b7e5683c67f4862fe064b7d02` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: added.
Body: approximately 1724 tokens (bytes/4). Within the soft budget.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `high`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/artifact-to-procedure/SKILL.md" ".claude/skills/artifact-to-procedure/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `53fdc0e9bdc8f90f04414a805775e5b171b48ebf349983f2f3dad80702322537`.
Repair preimage SKILL hash: `033406d5069f86ef91f2021118db431989927e1b5a76ab53c9deedcd18fb8fc0`.
Final SKILL hash: `d2dd32839b0c9f583ef934dc04fb024c24e5b98b7e5683c67f4862fe064b7d02`.

| Pass | Disposition |
|---|---|
| A | Target content reviewed; no further anchored Medium+ identified by author. |
| B | Target content reviewed; no further anchored Medium+ identified by author. |
| C | Target content reviewed; no further anchored Medium+ identified by author. |
| D | Target content reviewed; no further anchored Medium+ identified by author. |
| E | Target content reviewed; no further anchored Medium+ identified by author. |
| F | Target content reviewed; no further anchored Medium+ identified by author. |
| G | Target content reviewed; no further anchored Medium+ identified by author. |
| H | 20 source-bound, same-model predictions; no activation harness or empirical promotion. |
| I | Owned source/output boundaries tightened; external semantic ranking unavailable under paused embeddings. |
| J | Description <=1000 characters; body within the soft budget; history stored in a reference. |
| K | Target content reviewed; no further anchored Medium+ identified by author. |
| L | Final Markdown byte hygiene checked; reference blank-line cleanup applied where needed. |
| M | Target content reviewed; no further anchored Medium+ identified by author. |
| N | Target content reviewed; no further anchored Medium+ identified by author. |
| O | Owned target routing surfaces carry reciprocal handoffs where applicable. No outside-peer write; external mesh/copy changes deferred to root. |
| P | added |

Repair evidence: `repair-round-1.json` lists every executed test and the source bindings. Files read and precise original/repair scope are recorded in this target’s JSON.

Remaining limits: Fresh independent content/case recheck is pending after the bounded repair; no independent-clean claim. Global copy/wrapper/peer synchronization, registry rebuild and shared index refresh belong to root; this worker used --no-sync. Semantic collision ranking/own-intent routing were not executed while embeddings are paused.

Source findings repaired; no independent-clean or live-workflow completion claim. Modified files/sections are enumerated in the JSON hash manifest.
