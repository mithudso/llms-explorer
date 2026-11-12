# /sko receipt: memory-to-llms-txt

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 2 | 6 | applied anchored source fixes and generated/supplemented evals |
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
@@ -5,8 +5,8 @@
   provenance, recency tiers and checked drift instead of reclustering away its structure.
   TRIGGER: "make MEMORY.md queryable", "export the .remember pyramid", "compile the memory store
-  into llms.txt", "/memory2llms". SKIP: unstructured scratch or meeting notes → notes-to-llms-
-  txt; repository code/docs → crawl-repo-to-llms; organize notes without llms output → note-
-  organizer; audit an existing llms family → llms-deep-optimizer.
-version: 1.1.0
+  into llms.txt", "/memory2llms". SKIP: unstructured scratch or meeting notes →
+  notes-to-llms-txt; repository code/docs → crawl-repo-to-llms; organize notes without llms
+  output → note-organizer; audit an existing llms family → llms-deep-optimizer.
+version: 1.1.1
 updated: '2026-11-11'
 model: claude-opus-5-5
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "memory-to-llms-txt-01", "query": "Export this maintained MEMORY.md as a queryable llms docset.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3843db092e9869e1901a1eed84a039a25ed878fb34c09efa460d29959c455646", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "memory-to-llms-txt-02", "query": "/memory2llms .remember/", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3843db092e9869e1901a1eed84a039a25ed878fb34c09efa460d29959c455646", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "memory-to-llms-txt-03", "query": "Compile the typed agent memory store into llms files.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3843db092e9869e1901a1eed84a039a25ed878fb34c09efa460d29959c455646", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "memory-to-llms-txt-04", "query": "Make my feedback/project memory entries queryable with provenance.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3843db092e9869e1901a1eed84a039a25ed878fb34c09efa460d29959c455646", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "memory-to-llms-txt-05", "query": "Export the time-decay memory pyramid with recency facets.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3843db092e9869e1901a1eed84a039a25ed878fb34c09efa460d29959c455646", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # memory-to-llms-txt changelog

+- 2026-11-11 /sko repair 1.1.0 → 1.1.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.0.0 → 1.1.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 8 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `f106c93e51d24c36e2c66719ef161fb5b4c2534c39bce0dc42ed7bd036fda0da` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: n/a (llms producer; reads the authoritative format directly).
Body: approximately 2985 tokens (bytes/4). Within the soft budget.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `high`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/memory-to-llms-txt/SKILL.md" ".claude/skills/memory-to-llms-txt/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `97cbc99322d677b84461353c71103a619b717a2655729bc6d4bf6e0830f6051d`.
Repair preimage SKILL hash: `2520f0f0c3780bfb880b8a9762aee8999e7fa9bcc6e90b812b2a06eb93439651`.
Final SKILL hash: `f106c93e51d24c36e2c66719ef161fb5b4c2534c39bce0dc42ed7bd036fda0da`.

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
| P | n/a (llms producer; reads the authoritative format directly) |

Repair evidence: `repair-round-1.json` lists every executed test and the source bindings. Files read and precise original/repair scope are recorded in this target’s JSON.

Remaining limits: Fresh independent content/case recheck is pending after the bounded repair; no independent-clean claim. Global copy/wrapper/peer synchronization, registry rebuild and shared index refresh belong to root; this worker used --no-sync. Semantic collision ranking/own-intent routing were not executed while embeddings are paused. Native producer/consumer compatibility is preserved. The current-format /ldo gate must resolve any v3 migration conflict before a generated output can be called delivered; no real output family was produced in this audit.

Source findings repaired; no independent-clean or live-workflow completion claim. Modified files/sections are enumerated in the JSON hash manifest.
