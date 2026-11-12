# /sko receipt: llms-deep-optimizer

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 3 | 7 | applied anchored source fixes and generated/supplemented evals |
| 2 | 0 | 0 | author re-audit/static verification; no independent-clean claim |
| 3 | 0 | 1 | repaired corroborated blind/integration findings in one bounded round; final author residual count zero, independent recheck pending |

Hygiene: final scoped diff/Markdown checks clean; no severity credit for byte cleanup.
Pre-lint: inherited result is retained in JSON; the illustrative `file.md` index link remains a documented false positive for memory export. Parsed descriptions are all ≤1000 characters.

| Finding | Level | Action |
|---|---|---|
| BI-ING-006 | Medium | Worked topical facts place the URL immediately after the em dash; no literal source: token remains in either example. |

eval: predicted (no Claude activation harness; no empirical gain claim).

| Metric | Result | Target |
|---|---:|---:|
| should-trigger | 10/10 | ≥9/10 |
| false-positive | 0/10 | ≤1/10 |

Repair diff preview, bounded excerpts:

````diff
--- repair-preimage/SKILL.md
+++ repaired/SKILL.md
@@ -2,6 +2,6 @@
 name: llms-deep-optimizer
 description: >-
-  Audit and repair llms indexes, facts, full/small catalogues and families through evidence-
-  based convergence: shape, links, descriptions, source fidelity, privacy and available
+  Audit and repair llms indexes, facts, full/small catalogues and families through
+  evidence-based convergence: shape, links, descriptions, source fidelity, privacy and available
   retrieval/agent probes. Also builds topical files from graded fact pools. TRIGGER: "optimize
   this llms.txt", "check the facts file", "fix the llms family", "/ldo", "build a topical llms
@@ -10,5 +10,5 @@
   prompt-deep-optimizer; prose critique → writing-expert (references/document-critique.md); SQL
   → deep-query-optimizer; raw crawling → web-text-mirror.
-version: 1.3.0
+version: 1.3.1
 updated: '2026-11-11'
 model: claude-opus-5-5
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "llms-deep-optimizer-01", "query": "Audit and fix this llms.txt family.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "b17d81c9380b50dd2cfaa64bc094148e68167f415dde553ceac4f67cebc4aabe", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-deep-optimizer-02", "query": "/ldo ./fixture.llms --kind index", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "b17d81c9380b50dd2cfaa64bc094148e68167f415dde553ceac4f67cebc4aabe", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-deep-optimizer-03", "query": "Check the facts file against its source mirror.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "b17d81c9380b50dd2cfaa64bc094148e68167f415dde553ceac4f67cebc4aabe", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-deep-optimizer-04", "query": "Why does this llms-full file break its parser?", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "b17d81c9380b50dd2cfaa64bc094148e68167f415dde553ceac4f67cebc4aabe", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-deep-optimizer-05", "query": "Optimize navigation and descriptions in this existing llms index.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "b17d81c9380b50dd2cfaa64bc094148e68167f415dde553ceac4f67cebc4aabe", "skill_version": "1.3.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/evals/test_reference_contracts.py
+++ repaired/evals/test_reference_contracts.py
@@ -0,0 +1,23 @@
+"""Worked prose examples must agree with the bundled deterministic source grammar."""
+import os
+from pathlib import Path
+import sys
+
+SKILL = Path(os.environ.get("SKO_TEST_SKILL_ROOT", Path(__file__).parents[1]))
+sys.path.insert(0, str(SKILL / "scripts"))
+import _ldo_v3 as lint
+
+
+def test_topical_worked_facts_match_the_source_grammar(tmp_path):
+    text = (SKILL / "references/facts-to-llms-howto.md").read_text()
+    excerpt = text.split("Facts excerpt:", 1)[1].split("```", 2)[1]
+    rows = [line for line in excerpt.splitlines() if line.startswith("- [")]
+    assert len(rows) == 2
+    findings = lint.pass_facts("# Fixture facts\n\n" + "\n".join(rows), tmp_path / "facts.txt", None)
+    assert not [f for f in findings if f["severity"] == "high"], findings
+
+
+def test_headingless_source_and_broken_fragment_are_distinct():
+    headings = {"/fixture/plain.md": set()}
+    assert not lint._anchor_unresolved(headings, "/fixture/plain.md")
+    assert lint._anchor_unresolved(headings, "/fixture/plain.md#top")
````
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,4 +1,5 @@
 # llms-deep-optimizer changelog

+- 2026-11-11 /sko repair 1.3.0 → 1.3.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.2.1 → 1.3.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````
````diff
--- repair-preimage/references/facts-to-llms-howto.md
+++ repaired/references/facts-to-llms-howto.md
@@ -240,6 +240,6 @@
 ```
 ## Discovery and serving
-- [statement] A page advertises its markdown twin with `Link: <page.md>; rel="alternate"; type="text/markdown"` — source: https://llmstxt.org/#discovery · keywords: Link, alternate, text/markdown · verified-as-of: 2026-08-30
-- [fact] In the Ahrefs 137k-domain log study, the Claude-Code user agent fetched llms.txt more than every retrieval bot except statespace-indexer and GPTBot — source: https://ahrefs.com/blog/llms-txt-study#results · keywords: Claude-Code, GPTBot, user agent · verified-as-of: 2026-08-30
+- [statement] A page advertises its markdown twin with `Link: <page.md>; rel="alternate"; type="text/markdown"` — https://llmstxt.org/#discovery · keywords: Link, alternate, text/markdown · verified-as-of: 2026-08-30
````
Diff excerpt truncated (11 lines total).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 7 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `988c8e1465e1192d870ef2f751f08d1ed291c5054ac518526ac7698f86614812` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: n/a (llms producer; reads the authoritative format directly).
Body: approximately 3062 tokens (bytes/4). Within the soft budget.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `xhigh`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/llms-deep-optimizer/SKILL.md" ".claude/skills/llms-deep-optimizer/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `f02a1f07ace4d30b907a4f84520567e8522442647e1c92ffa69126f580582cf1`.
Repair preimage SKILL hash: `fe2dda10e2a72f4f0da537f4813a8f2cc4c89189d9a41365bfe29ec6c4da347e`.
Final SKILL hash: `988c8e1465e1192d870ef2f751f08d1ed291c5054ac518526ac7698f86614812`.

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

Remaining limits: Fresh independent content/case recheck is pending after the bounded repair; no independent-clean claim. Global copy/wrapper/peer synchronization, registry rebuild and shared index refresh belong to root; this worker used --no-sync. Semantic collision ranking/own-intent routing were not executed while embeddings are paused.

Source findings repaired; no independent-clean or live-workflow completion claim. Modified files/sections are enumerated in the JSON hash manifest.
