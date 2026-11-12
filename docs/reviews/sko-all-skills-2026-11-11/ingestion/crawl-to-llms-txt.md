# /sko receipt: crawl-to-llms-txt

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 2 | 5 | applied anchored source fixes and generated/supplemented evals |
| 2 | 0 | 0 | author re-audit/static verification; no independent-clean claim |
| 3 | 0 | 0 | repaired corroborated blind/integration findings in one bounded round; final author residual count zero, independent recheck pending |

Hygiene: final scoped diff/Markdown checks clean; no severity credit for byte cleanup.
Pre-lint: inherited result is retained in JSON; the illustrative `file.md` index link remains a documented false positive for memory export. Parsed descriptions are all ≤1000 characters.

| Finding | Level | Action |
|---|---|---|
| bounded repair | n/a | No new blind finding for this target; shared representation/hash checks passed. |

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
 name: crawl-to-llms-txt
-version: 1.4.0
+version: 1.4.1
 updated: '2026-11-11'
 model: claude-opus-5-5
@@ -12,6 +12,6 @@
   notes → notes-to-llms-txt; new web research → full-suite; raw mirroring → web-text-mirror; one
   concept → llms-concept-abstractor; structured data → firecrawl-scrape; publishable AI-search
-  guidance → generative-engine-optimization; existing-family audit → llms-deep-optimizer. Auth-
-  gated acquisition belongs to firecrawl-knowledge-ingest.
+  guidance → generative-engine-optimization; existing-family audit → llms-deep-optimizer.
+  Auth-gated acquisition belongs to firecrawl-knowledge-ingest.
 category: developer
 whenToUse:
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "crawl-to-llms-txt-01", "query": "Condense this public documentation site into private llms reference files.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "d7e280d534b3b352a8ec410091146f73551dfc582300e985cd20bc8bfb61e85e", "skill_version": "1.4.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-to-llms-txt-02", "query": "Crawl this fixed docs root and distill commands and gotchas.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "d7e280d534b3b352a8ec410091146f73551dfc582300e985cd20bc8bfb61e85e", "skill_version": "1.4.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-to-llms-txt-03", "query": "Pre-digest this library documentation for an agent.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "d7e280d534b3b352a8ec410091146f73551dfc582300e985cd20bc8bfb61e85e", "skill_version": "1.4.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-to-llms-txt-04", "query": "Create a compact operator reference from README and docs.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "d7e280d534b3b352a8ec410091146f73551dfc582300e985cd20bc8bfb61e85e", "skill_version": "1.4.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-to-llms-txt-05", "query": "/crawl2llms https://docs.fixture.invalid/v2 --no-adopt", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "d7e280d534b3b352a8ec410091146f73551dfc582300e985cd20bc8bfb61e85e", "skill_version": "1.4.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # crawl-to-llms-txt changelog

+- 2026-11-11 /sko repair 1.4.0 → 1.4.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.3.0 → 1.4.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 7 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `d8c5da6d3de9335cb60fb5d785b5befd2178017d47d3c4fd62fe58369026f1b8` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: n/a (llms producer; reads the authoritative format directly).
Body: approximately 5798 tokens (bytes/4). Within the soft budget.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `high`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/crawl-to-llms-txt/SKILL.md" ".claude/skills/crawl-to-llms-txt/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `be1a937f75e2a1b0b50051accda679b169e9d27cbfb30aebd2fe3a8df9cf26dd`.
Repair preimage SKILL hash: `2f9e1295e42e4c368d4bd4b8f1bd58189fdbb14cbd4a57f140cf597821d9243c`.
Final SKILL hash: `d8c5da6d3de9335cb60fb5d785b5befd2178017d47d3c4fd62fe58369026f1b8`.

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
