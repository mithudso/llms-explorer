# /sko receipt: note-organizer

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 1 | 3 | applied anchored source fixes and generated/supplemented evals |
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
| should-trigger | 9/10 | ≥9/10 |
| false-positive | 0/10 | ≤1/10 |

Repair diff preview, bounded excerpts:

````diff
--- repair-preimage/SKILL.md
+++ repaired/SKILL.md
@@ -6,11 +6,11 @@
   coherent document; reconcile every input item and preserve conflicts. TRIGGER: "organize these
   notes", "sort my meeting notes", "make sense of this brain dump", "dedupe my capture inbox".
-  SKIP: explicit llms output → notes-to-llms-txt; live capture or external extraction → content-
-  ingestion-extraction; new prose → writing-expert; choose a PKM system → research-methodology
-  (references/research-note-taking-pkm.md); one-document fact inventory → llms-txt-tooling
-  (references/document-distiller.md); saving a memory entry without reorganizing notes belongs
-  to the host memory workflow.
+  SKIP: explicit llms output → notes-to-llms-txt; live capture or external extraction →
+  content-ingestion-extraction; new prose → writing-expert; choose a PKM system →
+  research-methodology (references/research-note-taking-pkm.md); one-document fact inventory →
+  llms-txt-tooling (references/document-distiller.md); saving a memory entry without
+  reorganizing notes belongs to the host memory workflow.
 category: custom
-version: 1.3.0
+version: 1.3.1
 updated: '2026-11-11'
 model: claude-sonnet-5-5
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "note-organizer-01", "query": "organize these notes", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "global canonical corpus replay", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "e19dcafc3e0e57210eb39f32f742e81dce01faf7e9da6f64d5762e69fb043d11", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "note-organizer-02", "query": "sort my meeting notes from today's standup", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "global canonical corpus replay", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "e19dcafc3e0e57210eb39f32f742e81dce01faf7e9da6f64d5762e69fb043d11", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "note-organizer-03", "query": "here's a brain dump of everything in my head, help me structure it", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "global canonical corpus replay", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "e19dcafc3e0e57210eb39f32f742e81dce01faf7e9da6f64d5762e69fb043d11", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "note-organizer-04", "query": "make sense of this mess", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "global canonical corpus replay", "verdict": {"predicted_trigger": false, "level": "predicted", "reason": "The query lacks a note/domain anchor; the frontmatter alone does not establish that the mess is notes.", "description_sha256": "e19dcafc3e0e57210eb39f32f742e81dce01faf7e9da6f64d5762e69fb043d11", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "note-organizer-05", "query": "can you clean up ~/notes/inbox.md? it's a total dump", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "global canonical corpus replay", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "e19dcafc3e0e57210eb39f32f742e81dce01faf7e9da6f64d5762e69fb043d11", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # note-organizer changelog

+- 2026-11-11 /sko repair 1.3.0 → 1.3.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.2.1 → 1.3.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 9/10; false-positive 0/10 | predicted | yes |
| behavior cases | 23 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `83dc67dd161aa1e391cde621fb946f28af81ad73d713b87dc6606a1bc9290dd0` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: added.
Body: approximately 3066 tokens (bytes/4). Within the soft budget.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-sonnet-5-5` · effort `medium`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/note-organizer/SKILL.md" ".claude/skills/note-organizer/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `b71d5c1aa6aeb5b729c509bab3157b467a2f8846e40b2182637b8c1cb275ccc4`.
Repair preimage SKILL hash: `724ed334d0db3f826842606dbe51879738dde86a8c106e63291a1e9d98fe7cbc`.
Final SKILL hash: `83dc67dd161aa1e391cde621fb946f28af81ad73d713b87dc6606a1bc9290dd0`.

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
