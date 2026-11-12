# /sko receipt: crawl-repo-to-llms

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 3 | 5 | applied anchored source fixes and generated/supplemented evals |
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
@@ -1,5 +1,5 @@
 ---
 name: crawl-repo-to-llms
-version: 1.3.0
+version: 1.3.1
 updated: '2026-11-11'
 model: claude-opus-5-5
@@ -8,10 +8,10 @@
   Compile a repository dossier by static reading: file cards, purpose, safe-edit evidence,
   indexes, infrastructure, history and executable options. TRIGGER: "repo dossier", "per-file
-  breakdown", "onboard an agent to this repo", "inventory every command and flag", "/crawl-
-  repo2llms". SKIP: commands/docs condensation only → crawl-to-llms-txt; one concept → llms-
-  concept-abstractor; notes → notes-to-llms-txt; one document or SKILL.md conversion → llms-txt-
-  tooling; web research → full-suite; edit repo meta-docs → repo-bootstrapper; code fixes →
-  code-deep-optimizer; existing-family quality → llms-deep-optimizer. Full handoffs are in
-  Routing detail.
+  breakdown", "onboard an agent to this repo", "inventory every command and flag",
+  "/crawl-repo2llms". SKIP: commands/docs condensation only → crawl-to-llms-txt; one concept →
+  llms-concept-abstractor; notes → notes-to-llms-txt; one document or SKILL.md conversion →
+  llms-txt-tooling; web research → full-suite; edit repo meta-docs → repo-bootstrapper; code
+  fixes → code-deep-optimizer; existing-family quality → llms-deep-optimizer. Full handoffs are
+  in Routing detail.
 category: developer
 whenToUse:
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "crawl-repo-to-llms-01", "query": "Build a static repo dossier with a card for each file.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "a5dbda8af79e1c1405027efd9540aa02201254f5296cfd6c77df054b342dc74b", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-repo-to-llms-02", "query": "Give an agent the purpose and safe-edit evidence for this codebase.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "a5dbda8af79e1c1405027efd9540aa02201254f5296cfd6c77df054b342dc74b", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-repo-to-llms-03", "query": "Inventory every entrypoint, parser option and environment variable.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "a5dbda8af79e1c1405027efd9540aa02201254f5296cfd6c77df054b342dc74b", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-repo-to-llms-04", "query": "Map this repo infrastructure, indexes and history into llms files.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "a5dbda8af79e1c1405027efd9540aa02201254f5296cfd6c77df054b342dc74b", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-repo-to-llms-05", "query": "Create the per-file importance map for this repository.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "a5dbda8af79e1c1405027efd9540aa02201254f5296cfd6c77df054b342dc74b", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # crawl-repo-to-llms changelog

+- 2026-11-11 /sko repair 1.3.0 → 1.3.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.2.0 → 1.3.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 8 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `7e9457b496674d84e776dd7f40953305ea7988681f7ac058ec1679410a7db0ef` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: n/a (llms producer; reads the authoritative format directly).
Body: approximately 6642 tokens (bytes/4). Over soft budget, justified: remaining phases and output/privacy/provenance checks are required on a normal full invocation. Customer-specific Drive/card/flag reference material was extracted where useful; no hard ceiling is exceeded.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `high`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/crawl-repo-to-llms/SKILL.md" ".claude/skills/crawl-repo-to-llms/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `79c3a803f49d58168e93669d8c078bb0c4d1c3357071ed39a081689e95d7c468`.
Repair preimage SKILL hash: `16440d3d63cbf5160d7d51c1cfe74fc5c711d346b32b1752e4a50c9ac3c8a123`.
Final SKILL hash: `7e9457b496674d84e776dd7f40953305ea7988681f7ac058ec1679410a7db0ef`.

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
| J | Over soft budget, justified: remaining phases and output/privacy/provenance checks are required on a normal full invocation. Customer-specific Drive/card/flag reference material was extracted where useful; no hard ceiling is exceeded. |
| K | Target content reviewed; no further anchored Medium+ identified by author. |
| L | Final Markdown byte hygiene checked; reference blank-line cleanup applied where needed. |
| M | Target content reviewed; no further anchored Medium+ identified by author. |
| N | Target content reviewed; no further anchored Medium+ identified by author. |
| O | Owned target routing surfaces carry reciprocal handoffs where applicable. No outside-peer write; external mesh/copy changes deferred to root. |
| P | n/a (llms producer; reads the authoritative format directly) |

Repair evidence: `repair-round-1.json` lists every executed test and the source bindings. Files read and precise original/repair scope are recorded in this target’s JSON.

Remaining limits: Fresh independent content/case recheck is pending after the bounded repair; no independent-clean claim. Global copy/wrapper/peer synchronization, registry rebuild and shared index refresh belong to root; this worker used --no-sync. Semantic collision ranking/own-intent routing were not executed while embeddings are paused. Native producer/consumer compatibility is preserved. The current-format /ldo gate must resolve any v3 migration conflict before a generated output can be called delivered; no real output family was produced in this audit.

Source findings repaired; no independent-clean or live-workflow completion claim. Modified files/sections are enumerated in the JSON hash manifest.
