# /sko receipt: notes-to-llms

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 3 | 7 | applied anchored source fixes and generated/supplemented evals |
| 2 | 0 | 0 | author re-audit/static verification; no independent-clean claim |
| 3 | 0 | 4 | repaired corroborated blind/integration findings in one bounded round; final author residual count zero, independent recheck pending |

Hygiene: final scoped diff/Markdown checks clean; no severity credit for byte cleanup.
Pre-lint: inherited result is retained in JSON; the illustrative `file.md` index link remains a documented false positive for memory export. Parsed descriptions are all ≤1000 characters.

| Finding | Level | Action |
|---|---|---|
| BI-ING-001 | Medium | Parsed YAML identifiers and aliases remain whole; folding occurs only between complete tokens. |
| BI-ING-005 | Medium | The normalizer emits a body-free, root-qualified source_statuses ledger with empty, duplicate-of, unsupported, unreadable, outside-root and hidden dispositions. |
| BI-ING-007 | Medium | The reference and main procedure distinguish valid headingless bare URLs from present broken fragments; only the latter count against the R3 threshold. |
| INTEGRATION-PATH-001 | Medium | Tests resolve an explicit LLMS_EXPLORER_REPO or discover repository markers, and missing required helpers fail instead of skipping. |

eval: predicted (no Claude activation harness; no empirical gain claim).

| Metric | Result | Target |
|---|---:|---:|
| should-trigger | 10/10 | ≥9/10 |
| false-positive | 0/10 | ≤1/10 |

Repair diff preview, bounded excerpts:

````diff
--- repair-preimage/SKILL.md
+++ repaired/SKILL.md
@@ -8,7 +8,7 @@
   normalizer/linter pipeline → notes-to-llms-txt; preserve notes as notes → note-organizer;
   existing llms-family audit or graded topical pool → llms-deep-optimizer; format spec →
-  document-formats; one-document inventory → llms-txt-tooling (references/document-
-  distiller.md); live site mirroring → web-text-mirror.
-version: 1.1.0
+  document-formats; one-document inventory → llms-txt-tooling
+  (references/document-distiller.md); live site mirroring → web-text-mirror.
+version: 1.1.1
 updated: '2026-11-11'
 model: claude-opus-5-5
@@ -114,5 +114,5 @@
 `my-notes.mirror.llms/`, which no documented command expects.

-Read the **inventory**, not the note bodies. Report what it dropped (empty, duplicate,
+Read the **inventory**, not the note bodies. Use its complete `report.source_statuses` ledger to account for each root-qualified input; duplicate rows carry `duplicate_of` pointing to the retained source. Report what it dropped (empty, duplicate,
 unsupported suffix), which pages have no headings, and which headings share an anchor.

@@ -124,6 +124,6 @@
 ```

-Then re-run the normaliser and check `pages_without_headings` did not grow: conversion
-routinely flattens headings, and a headingless page costs every unit on it its anchor.
+Then re-run the normaliser and report any growth in `pages_without_headings`: conversion
+can flatten headings and reduce navigation precision. A headingless source uses its bare page URL and remains valid. Only a present fragment that fails resolution counts as an unresolved anchor; never invent `#top`.

 ### 2 · Extract units
@@ -225,6 +225,5 @@
 the model and live passes (navigation, facts truth, serving headers, agent usability).

-**If the Highs cannot be cleared** — most often more than 20 % of units unresolved because
-too many pages lost their headings in conversion — do not ship. Report the run as
+**If the Highs cannot be cleared** — for example, more than 20 % of units still carry fragments that no longer resolve after conversion — do not ship. Bare URLs on headingless pages do not count toward that threshold. Report the run as
 `evidence-limited`, name the blocking finding and the pages responsible, and offer the two
 real fixes: restore headings in those sources, or drop their units.
````
````diff
--- repair-preimage/evals/test_distribution_layout.py
+++ repaired/evals/test_distribution_layout.py
@@ -0,0 +1,25 @@
+"""Exercise source and legacy distribution layouts without installing either one."""
+import os
+from pathlib import Path
+import shutil
+import subprocess
+import sys
+
+import pytest
+
+SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parents[1] / "scripts"))
+
+
+@pytest.mark.parametrize("layout", [".claude/skills", "skills"])
+def test_source_and_distribution_use_the_explicit_repository(tmp_path, layout):
+    repo = Path(os.environ.get("LLMS_EXPLORER_REPO", Path.cwd())).resolve()
+    assert (repo / "hub/scripts/docset_refine").is_dir(), "LLMS_EXPLORER_REPO must name the reviewed repo"
+    stage = tmp_path / layout / "notes-to-llms/scripts"
+    stage.mkdir(parents=True)
+    for name in ["notes_normalise.py", "test_notes_normalise.py"]:
+        shutil.copy2(SOURCE / name, stage / name)
+    env = {**os.environ, "LLMS_EXPLORER_REPO": str(repo), "PYTHONDONTWRITEBYTECODE": "1"}
+    result = subprocess.run([sys.executable, "-m", "pytest", str(stage / "test_notes_normalise.py"), "-q"],
+                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
+    assert result.returncode == 0, result.stdout + result.stderr
+    assert "skipped" not in result.stdout.lower(), result.stdout
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "notes-to-llms-01", "query": "/n2l ./vault --project test-notes", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "dbf1e9205994ad09e528dd1296d371a68a37ad6ea09bce8a41f49e462774a7c5", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "notes-to-llms-02", "query": "Normalize this Obsidian folder into source-anchored llms files.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "dbf1e9205994ad09e528dd1296d371a68a37ad6ea09bce8a41f49e462774a7c5", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "notes-to-llms-03", "query": "Convert this local notes export with a mirror and lint gate.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "dbf1e9205994ad09e528dd1296d371a68a37ad6ea09bce8a41f49e462774a7c5", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "notes-to-llms-04", "query": "Make the local note sources pass llms_lint with real heading anchors.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "dbf1e9205994ad09e528dd1296d371a68a37ad6ea09bce8a41f49e462774a7c5", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "notes-to-llms-05", "query": "Build reproducible llms files from these two notes directories.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "dbf1e9205994ad09e528dd1296d371a68a37ad6ea09bce8a41f49e462774a7c5", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # notes-to-llms changelog

+- 2026-11-11 /sko repair 1.1.0 → 1.1.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.0.0 → 1.1.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````
````diff
--- repair-preimage/references/from-disorder-to-skeleton.md
+++ repaired/references/from-disorder-to-skeleton.md
@@ -22,7 +22,9 @@
 | Report field | What it means | What you do |
 |---|---|---|
-| `pages_without_headings` | those pages contribute **no** resolvable anchor | their units carry the bare page URL, no `#`. If they hold more than ~20 % of your units, add headings to the sources first — otherwise `P7 R3` is a High you cannot fix later |
+| `pages_without_headings` | those pages have no heading fragment; bare page URLs remain valid | omit the fragment and report the loss of navigation precision. Restore real source headings when that precision matters; never invent `#top`. The P7 R3 20% threshold applies only to present fragments that fail resolution, not to headingless units with bare URLs |
 | `duplicate_anchors` | two headings share one slug | a unit pointing there is ambiguous, not broken. Rename one heading in the source, or accept it and say so |
````
Diff excerpt truncated (13 lines total).
````diff
--- repair-preimage/scripts/notes_normalise.py
+++ repaired/scripts/notes_normalise.py
@@ -235,8 +235,21 @@
     for p in paths:
         if p.is_dir():
-            files.extend(sorted(q for q in p.rglob("*") if q.is_file()))
-        elif p.is_file():
+            files.extend(sorted(q for q in p.rglob("*") if q.is_file() or q.is_symlink()))
+        else:
             files.append(p)
-    return [f for f in files if not any(part.startswith(".") for part in f.parts)]
+    return files
+
+
+def _source_identity(path: Path, roots: list[Path], *, namespace: bool) -> tuple[str, str]:
+    """Display path and root-qualified input identity, without following an alias."""
+    for root in roots:
+        try:
+            relative = path.absolute().relative_to(root.absolute()).as_posix()
+        except ValueError:
+            continue
+        identity = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:8]
+        qualified = f"{root.name}-{identity}/{relative}"
+        return (qualified if namespace else relative), qualified
+    return path.name, "unscoped/" + path.name


@@ -271,19 +284,37 @@
         "pages_without_headings": [],
         "duplicate_anchors": [],
+        "source_statuses": [],
     }
     by_hash: dict[str, str] = {}
+    explicit_files = {p.absolute() for p in inputs if not p.is_dir()}

     for path in _iter_inputs(inputs):
+        display, source_id = _source_identity(path, roots, namespace=namespace)
+        status = {"source_id": source_id, "path": display}
+        report["source_statuses"].append(status)
         if not any(path.resolve().is_relative_to(root.resolve()) for root in roots):
````
Diff excerpt truncated (105 lines total).
````diff
--- repair-preimage/scripts/test_source_ledger.py
+++ repaired/scripts/test_source_ledger.py
@@ -0,0 +1,56 @@
+"""Every selected input must have a body-free, root-qualified disposition."""
+from collections import Counter
+import importlib.util
+import json
+import os
+from pathlib import Path
+
+SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parent))
+spec = importlib.util.spec_from_file_location("ledger_normaliser", SOURCE / "notes_normalise.py")
+nn = importlib.util.module_from_spec(spec)
+spec.loader.exec_module(nn)
+
+
+def test_source_statuses_cover_omissions_and_duplicate_identity(tmp_path, monkeypatch):
+    root = tmp_path / "approved"
+    root.mkdir()
+    body = "# Fixture\n\nThis original fixture claim has enough content to be retained.\n"
+    (root / "a.md").write_text(body)
+    (root / "b.md").write_text(body)
+    (root / "empty.md").write_text("")
+    (root / "unsupported.pdf").write_bytes(b"%PDF original fixture")
+    (root / "unreadable.md").write_text(body + "unreadable fixture marker")
+    outside = tmp_path / "outside.md"
+    outside.write_text(body + "OUTSIDE")
+    (root / "escape.md").symlink_to(outside)
+    original_read = nn._read
+    monkeypatch.setattr(nn, "_read", lambda p: None if p.name == "unreadable.md" else original_read(p))
+    pages, report = nn.normalise([root], project="fixture")
+    ledger = report["source_statuses"]
+    assert Counter(r["status"] for r in ledger) == {
+        "kept": 1, "duplicate": 1, "empty": 1, "unsupported": 1,
+        "unreadable": 1, "outside-root": 1,
+    }
+    assert len({r["source_id"] for r in ledger}) == 6
+    assert all(r["source_id"].startswith("approved-") for r in ledger)
+    kept = next(r for r in ledger if r["status"] == "kept")
+    duplicate = next(r for r in ledger if r["status"] == "duplicate")
````
Diff excerpt truncated (59 lines total).
````diff
--- repair-preimage/scripts/test_notes_normalise.py
+++ repaired/scripts/test_notes_normalise.py
@@ -14,4 +14,5 @@

 import json
+import os
 import sys
 from pathlib import Path
@@ -23,5 +24,20 @@
 import notes_normalise as nn  # noqa: E402

-HUB = Path(__file__).resolve().parents[4] / "hub" / "scripts"
+def resolve_repo_root(start: Path | None = None) -> Path:
+    """Use the explicit reviewed repository, or discover its local markers."""
+    configured = os.environ.get("LLMS_EXPLORER_REPO")
+    if configured:
+        candidates = [Path(configured).expanduser().resolve()]
+    else:
+        source = (start or Path(__file__)).resolve()
+        candidates = [source if source.is_dir() else source.parent, *source.parents]
+    for root in candidates:
+        marker = (root / "AGENTS.md").is_file() or (root / ".git").exists() or (root / "pyproject.toml").is_file()
+        if marker and (root / "hub/scripts").is_dir():
+            return root
+    raise RuntimeError("Cannot locate the reviewed hub checkout; set LLMS_EXPLORER_REPO to its repository root")
+
+
+HUB = resolve_repo_root() / "hub" / "scripts"

 LIMITS = """---
@@ -74,5 +90,5 @@
     sys.path.insert(0, str(HUB))
     if not (HUB / "llms_lint.py").exists():  # pragma: no cover
-        pytest.skip("hub checkout not present")
+        pytest.fail("reviewed hub linter is absent; check LLMS_EXPLORER_REPO")
     return __import__(module)

@@ -242,5 +258,5 @@
     nn.write_mirror(pages, mirror)
     if not (HUB / "docset_refine" / "mirror_io.py").exists():  # pragma: no cover
````
Diff excerpt truncated (78 lines total).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 9 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `a4e54656f281d4c50dbf84e917ae92b0a4ce4daf2681d1b53aed2ddd1072347f` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: n/a (llms producer; reads the authoritative format directly).
Body: approximately 4103 tokens (bytes/4). Within the soft budget.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `high`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/notes-to-llms/SKILL.md" ".claude/skills/notes-to-llms/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `d6e6f8c68ee72c6d2d8b41472e4580432477ccd08c28844d354c3c3c6dde4017`.
Repair preimage SKILL hash: `ee67cc3076fd3136ec1e12367798b0b1c8eb5a9ce9662bd88cfffff6096dda39`.
Final SKILL hash: `a4e54656f281d4c50dbf84e917ae92b0a4ce4daf2681d1b53aed2ddd1072347f`.

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
