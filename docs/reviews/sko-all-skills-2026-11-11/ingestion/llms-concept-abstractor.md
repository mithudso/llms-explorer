# /sko receipt: llms-concept-abstractor

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 6 | 7 | applied anchored source fixes and generated/supplemented evals |
| 2 | 0 | 0 | author re-audit/static verification; no independent-clean claim |
| 3 | 1 | 1 | repaired corroborated blind/integration findings in one bounded round; final author residual count zero, independent recheck pending |

Hygiene: final scoped diff/Markdown checks clean; no severity credit for byte cleanup.
Pre-lint: inherited result is retained in JSON; the illustrative `file.md` index link remains a documented false positive for memory export. Parsed descriptions are all ≤1000 characters.

| Finding | Level | Action |
|---|---|---|
| BI-ING-003 | High | Directory/glob expansion checks resolved containment before reads, deduplicates resolved identities and records rejected/duplicate/missing/unreadable inputs. |
| BI-ING-004 | Medium | The compiler budgets the fully rendered small digest, preserves complete source units and every facet, and raises before replacement if the selected minimum cannot fit. |

eval: predicted (no Claude activation harness; no empirical gain claim).

| Metric | Result | Target |
|---|---:|---:|
| should-trigger | 10/10 | ≥9/10 |
| false-positive | 0/10 | ≤1/10 |

Repair diff preview, bounded excerpts:

````diff
--- repair-preimage/SKILL.md
+++ repaired/SKILL.md
@@ -9,5 +9,5 @@
   audit an existing llms file or use a graded topical fact pool → llms-deep-optimizer; narrative
   essay → writing-expert; organize mixed notes → notes-to-llms-txt.
-version: 1.5.0
+version: 1.5.1
 updated: '2026-11-11'
 model: claude-opus-5-5
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "llms-concept-abstractor-01", "query": "Abstract connection pooling out of these three existing docsets.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3301af3c4a0bbc62912647e9f6fbcf4a08d3331fda442d59e7f30cf35a3323c2", "skill_version": "1.5.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-concept-abstractor-02", "query": "Build a concept pack for rate limiting from the supplied mirrors.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3301af3c4a0bbc62912647e9f6fbcf4a08d3331fda442d59e7f30cf35a3323c2", "skill_version": "1.5.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-concept-abstractor-03", "query": "Collect every source-anchored thing these docs say about webhooks.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3301af3c4a0bbc62912647e9f6fbcf4a08d3331fda442d59e7f30cf35a3323c2", "skill_version": "1.5.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-concept-abstractor-04", "query": "Make a vocabulary-rich reference on indexing across this database corpus.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3301af3c4a0bbc62912647e9f6fbcf4a08d3331fda442d59e7f30cf35a3323c2", "skill_version": "1.5.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "llms-concept-abstractor-05", "query": "/lca \"heart\" --from chapter.md --no-persist", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "3301af3c4a0bbc62912647e9f6fbcf4a08d3331fda442d59e7f30cf35a3323c2", "skill_version": "1.5.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # llms-concept-abstractor changelog

+- 2026-11-11 /sko repair 1.5.0 → 1.5.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.4.1 → 1.5.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````
````diff
--- repair-preimage/references/output-contract.md
+++ repaired/references/output-contract.md
@@ -131,4 +131,6 @@
 unit alone exceeds the remaining budget; then shorten via `text_fix` or raise the budget).

+The compiler counts the complete rendered small file, including its header, facet headings, blank lines and omission notices, against the native characters/4 estimate. It requires one complete unit from every nonempty facet. If that minimum cannot fit, it raises a bounded budget error before replacing compiled files. Increase the ceiling or provide a verified source-contiguous trim; do not pad, silently truncate a claim or report an oversized digest as within budget. `manifest.small_budget` records the measured character/byte counts.
+
 ## 7. Report template
````
Diff excerpt truncated (9 lines total).
````diff
--- repair-preimage/references/harvest-playbook.md
+++ repaired/references/harvest-playbook.md
@@ -31,4 +31,6 @@
 keywords, origin, source_kind`), so mixed scopes are fine in one harvest. IDs are
 `s<NN>u<NNNNNN>` — `s` numbers the input file, which is how the report attributes hits.
+
+Directory and glob expansion checks resolved containment before opening a discovered file and deduplicates real file identities. An outside symlink is excluded, never read. `input_statuses` in the harvest/semantic report records admitted inputs, duplicate-of links and rejected/missing/unreadable sources with scoped IDs. An empty or rejected source remains a coverage gap; it does not authorize a wider crawl.
````
Diff excerpt truncated (9 lines total).
````diff
--- repair-preimage/scripts/concept_abstract.py
+++ repaired/scripts/concept_abstract.py
@@ -57,4 +57,5 @@

 import argparse
+import glob
 import json
 import re
@@ -64,5 +65,5 @@
 from pathlib import Path

-VERSION = "1.5.0"
+VERSION = "1.5.1"
 CHARS_PER_TOKEN = 4
 CORE_WEIGHT = 0.7   # relations at/above this weight can qualify a unit on their own
@@ -387,36 +388,79 @@


-def iter_inputs(paths: list[str], base_url: str | None = None):
-    """Expand files/dirs/globs; pick a reader per file shape."""
-    files: list[Path] = []
-    for p in paths:
-        pp = Path(p).expanduser()
-        if any(ch in p for ch in "*?["):
-            files += sorted(Path().glob(p)) if not pp.is_absolute() else sorted(pp.parent.glob(pp.name))
+def iter_inputs(paths: list[str], base_url: str | None = None, *, ledger: list | None = None):
+    """Expand only declared roots; account for omissions and deduplicate real files.
+
+    A directory/glob authorizes its resolved root, not an outside file reached
+    through a descendant symlink. Explicit files authorize their parent root.
+    """
+    ledger = ledger if ledger is not None else []
+    candidates: list[tuple[Path, Path, int]] = []
+    approved = []
+    for number, p in enumerate(paths, 1):
+        raw = str(p)
+        pp = Path(raw).expanduser()
+        if glob.has_magic(raw):
+            parts = pp.parts
+            root = Path(pp.anchor) if pp.is_absolute() else Path()
````
Diff excerpt truncated (242 lines total).
````diff
--- repair-preimage/scripts/test_scope_and_budget.py
+++ repaired/scripts/test_scope_and_budget.py
@@ -0,0 +1,114 @@
+"""Counterexamples use only original temporary files and private compilation."""
+from argparse import Namespace
+from collections import Counter
+import contextlib
+import importlib.util
+import io
+import json
+import os
+from pathlib import Path
+
+import pytest
+
+SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parent))
+spec = importlib.util.spec_from_file_location("scope_budget_lca", SOURCE / "concept_abstract.py")
+lca = importlib.util.module_from_spec(spec)
+spec.loader.exec_module(lca)
+
+
+@pytest.mark.parametrize("use_glob", [False, True])
+def test_discovered_symlink_stays_inside_approved_root(tmp_path, use_glob):
+    root = tmp_path / "approved"
+    root.mkdir()
+    (root / "inside.md").write_text("# Fixture\n\nFixture INSIDE is original content under the approved root.\n")
+    outside = tmp_path / "outside.md"
+    outside.write_text("# Fixture\n\nFixture OUTSIDE is original content that was not approved.\n")
+    (root / "external.md").symlink_to(outside)
+    paths = [str(root / "*.md")] if use_glob else [str(root)]
+    rows = [(p, list(units)) for p, units in lca.iter_inputs(paths)]
+    assert not any("OUTSIDE" in u["text"] for _, units in rows for u in units)
+    assert len(rows) == 1
+    ledger = []
+    list(lca.iter_inputs(paths, ledger=ledger))
+    assert Counter(r["status"] for r in ledger) == {"kept": 1, "outside-root": 1}
+
+
+def test_aliases_deduplicate_resolved_files(tmp_path):
+    root = tmp_path / "approved"
````
Diff excerpt truncated (117 lines total).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 17 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `37cd5719a138ed976a5c19624c674037ba8b657bc480c612cb2e409f76c4de41` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: n/a (llms producer; reads the authoritative format directly).
Body: approximately 5662 tokens (bytes/4). Within the soft budget.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `high`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/llms-concept-abstractor/SKILL.md" ".claude/skills/llms-concept-abstractor/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `2d165b36db5468b6dcebb5e3e92d9f8eec1387647ee337f32339c0f4d62559b1`.
Repair preimage SKILL hash: `cd6c5df3ab53f1d665284a0d79b6a4b160412053e72f54b935391d123a953433`.
Final SKILL hash: `37cd5719a138ed976a5c19624c674037ba8b657bc480c612cb2e409f76c4de41`.

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
