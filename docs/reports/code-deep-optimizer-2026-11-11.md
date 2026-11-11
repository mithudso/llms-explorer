# Code deep optimizer — research lifecycle

Version: 1.0.0; date: 2026-11-11.
Delta: initial scoped audit, repairs and explicit coverage receipt.

Target baseline: `3dd863b0`. Structural mode (`--no-empirical`); no held-out
retrieval collection was bound to this run and no champion was persisted. The
selection ceiling was 50; actual complete diagnostic coverage is **17 source
files**, not 50 and not the entire repository. The initial helper inventory had
631 source files; five new regression files make the final inventory 636.

## 1. Per-iteration severity

| Stage | Critical | High | Medium | Applied | Gate result |
| --- | ---: | ---: | ---: | ---: | --- |
| Initial nine-file diagnostic | 0 | 4 | 2 | 6 | Blind review found numeric-token rejection |
| Expanded seventeen-file repair iteration | 0 | 0 | 7 | 7 | Second blind review found inactive-vector candidate starvation |
| Targeted repair after gate exit | 0 | 0 | 1 | 1 | Actual Neo4j red/green and integration regression passed |

The optimizer exits **BLIND-AUDIT-DISSENT**. It does not claim CLEAN: the second
blind gate found a real defect. That defect was subsequently repaired and
verified without a third blind gate. All **14 discovered defects** are repaired
(4 High, 10 Medium). The repository-wide review remains partial.

## 2. Findings and repairs

| ID / pass | Source anchor | Severity | Defect and resulting behavior | Status |
| --- | --- | --- | --- | --- |
| RX-SPACE / C1,C2,T1 | `hub/research-expertise/src/research_expertise/store.py:32` | High | Cache keys, unchanged-document decisions and dense eligibility now bind model/repository/revision/dimensions/FastEmbed/route recipe. Old unbound rows require explicit refresh. | Repaired |
| TX-TEMP / C1,P2 | `scripts/research_transaction.py:94` | High | Exclusive random temporary files replace a fixed sibling that could overwrite another transaction's destination; rollback stops deleting that sibling. | Repaired |
| TX-ALIAS / C1,S3 | `scripts/research_transaction.py:13` | High | Resolve destination aliases before preimage-coverage checks; refuse final symlinks and preserve nested symlinks in directory snapshots. | Repaired |
| SOURCE-RECEIPT / C2,S3 | `scripts/research_provenance.py:76` | High | Existing receipts must match schema, source/snapshot identity, path, URL, hash and character count. Corrupt records fail without replacement. | Repaired |
| CAPTURE-CASE / S3,S4 | `hub/research-expertise/src/research_expertise/capture.py:69` | Medium | Case-folded source-ID collisions fail before any canonical write, including on case-insensitive filesystems. | Repaired |
| CAPTURE-LOG / S5 | `hub/research-expertise/src/research_expertise/capture.py:454` | Medium | Pending projection failures log safe operation, slug and exception class; source bodies and raw provider errors stay out of logs. | Repaired |
| GATE-NUMERIC / C1 | `scripts/research_gate.py:292` | Medium | Complete scientific and underscore-grouped numeric literals pass; exact-token and quote-edge boundaries still reject substitutions. | Repaired |
| MCP-WORKER / P2 | `hub/research-expertise/src/research_expertise/mcp_server.py:45` | Medium | Blocking tool work runs on one owner thread, preserving SQLite affinity and protocol responsiveness. Shutdown waits and closes on that thread. | Repaired |
| CLI-PREFLIGHT / M5 | `hub/research-expertise/src/research_expertise/cli.py:36` | Medium | Missing/invalid connection config exits 3 with setup guidance and no traceback or echoed values. | Repaired |
| SNAPSHOT-REVISION / C1,P2 | `hub/research-expertise/src/research_expertise/inspection.py:31` | Medium | Graph reads bind the selected document/manifest revision and suppress a record changed during collection. | Repaired |
| INSTALL-ROLLBACK / C1,S2 | `hub/research-expertise/install.py:30` | Medium | Retain complete prior app/venv, build at the final path and restore on failure; preflight executable conflicts and active ingest ownership. | Repaired |
| INSTALL-ABI / S4 | `hub/research-expertise/install.py:75` | Medium | Actual fresh setup exposed missing Python 3.15 ONNX wheels. Installer selects 3.14; package support is 3.11–3.14. Dependency versions stay unchanged. | Repaired |
| SOURCE-INGEST / P2,C2 | `scripts/research_library.py:29` | Medium | Cooperating same-source refreshes serialize prearchive/fetch/postarchive by normalized source ID; unrelated sources remain concurrent. | Repaired |
| RETIRED-ANN / C1,P1 | `hub/research-expertise/src/research_expertise/store.py:303` | Medium | Deactivated documents lose derived embedding properties, so retired vectors cannot consume all ANN candidates before filtering. Text/history/cache remain. | Repaired after blind gate |

Two candidate classes were excluded from defect counts with evidence:

- Existing exported packs are intentionally trusted by `research_site_sync.py:334`
  and `:365`; `gen_concepts.py:259` consumes their structured units. The synthetic
  scoped-refresh test at `tests/test_research_site_sync.py:415` explicitly uses a
  placeholder artifact marker. Stronger exact projection receipts are a roadmap
  item, not an established violated contract. Historical native recovery has its
  separate proof checks in `scripts/recover_dr_packs.py:45`.
- Narrow concept filtering can underfill approximate ANN candidates, as already
  documented by the package guide. This remains distinct from retaining deleted
  vectors in the search index. A formal retrieval evaluation is still needed.

## 3. Verify gate

| Check | Baseline / before | Final observed result | Exit |
| --- | --- | --- | ---: |
| Expertise owning-package pytest | 109 passed | 130 passed; one opt-in DB integration skipped by default | 0 |
| Expertise Ruff | Passed | Passed, including installer and new tests | 0 |
| Native lifecycle/adapter suite | Initial standalone environment: 394 passed, 31 failed because `llms_txt` was absent | Existing pure-Python private dependency exposed explicitly; 445 passed, 15 subtests | 0 |
| Adapter synchronization | Mirrored helpers changed during repair | Official helper checks 31 files, zero drift | 0 |
| Curated documentation paths | 16 existing paths | 22 paths exist; CI now runs the checker | 0 |
| Privacy gate | Whole-tree scan, 18,024 files | Zero findings; final changed-artifact check belongs to delivery | 0 |
| Installer actual uv lifecycle | Default fresh Python 3.15 failed on missing ONNX wheel | Fresh install, forced offline uv failure/complete rollback, successful upgrade and final entrypoints exercised | 0 |
| Installer rollback inventory | Seeded old release | 4,139 app/venv files identical after actual failed upgrade | 0 |
| Retired-vector actual Neo4j probe | 15 inactive vectors, zero hits; assertion exit 1 | Zero inactive vectors; active semantic hit; no new embeddings | 0 |
| Checked-in opt-in Neo4j integration | Explicit connection-config opt-in | One real integration test passed; temporary labels/indexes removed | 0 |

Conventional package commands:

```sh
uv run --directory hub/research-expertise --frozen pytest -q
uv run --directory hub/research-expertise --frozen ruff check src tests install.py
python3 scripts/sync_codex_research_skills.py --check
python3 scripts/check_doc_indexes.py
```

Full private command/log receipts retain actual nonzero results, environment
corrections and runtime identities. Two installer-verifier assertions were
corrected after observing uv's valid long-path shell trampoline and macOS path
aliases; neither was reported as a product defect. The first retirement-probe
setup had a Python argument-name collision; its corrected unchanged probe
then reproduced the real bug before repair.

The legacy fusion-related pytest module could not collect in the standalone
environment because `ollama_client` was absent. Pure-stdlib fusion checks passed.
No legacy dependencies, Ollama process or paused indexer were started to hide
that limitation.

## 4. Activated review references

- `code-deep-optimizer` 1.17.1; `repo-bootstrapper` 5.4.2.
- `lang-python`: Python, CLI, pytest, ownership and resource behavior.
- `software-engineering-patterns`: code-review and coding-standards references.
- `security-review`: backend/file trust-boundary and safe logging reference.
- Shared convergence/severity, audit-ledger and evidence contracts govern status.

## 5. Diff evidence

The complete task source diff is [research-lifecycle-code-2026-11-11.patch](research-lifecycle-code-2026-11-11.patch).
This is a zero-context code diff, with no private corpus bodies or credentials.
Use `git apply --unidiff-zero` when applying it.
Selected per-file previews follow; each is explicitly capped at 18 lines.

### `hub/research-expertise/src/research_expertise/capture.py`

```diff
diff --git a/hub/research-expertise/src/research_expertise/capture.py b/hub/research-expertise/src/research_expertise/capture.py
index 2e2f49f9..584355ed 100644
--- a/hub/research-expertise/src/research_expertise/capture.py
+++ b/hub/research-expertise/src/research_expertise/capture.py
@@ -14,0 +15 @@ import json
+import logging
@@ -28,0 +30 @@ _SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,49}\Z")
+_LOG = logging.getLogger(__name__)
@@ -63 +65 @@ def _normalize(slug, title, question, summary, findings, sources):
-    clean_sources, source_map = [], {}
+    clean_sources, source_map, source_filenames = [], {}, set()
@@ -70,0 +73,3 @@ def _normalize(slug, title, question, summary, findings, sources):
+        if sid.casefold() in source_filenames:
+            raise ValueError("source.id must be unique on case-insensitive filesystems")
+        source_filenames.add(sid.casefold())
@@ -446,0 +452,6 @@ def save_research(
+            _LOG.warning(
+                "research_capture_index_pending slug=%s error_type=%s",
+                payload["slug"],
+                type(exc).__name__,
+                extra={"capture_slug": payload["slug"], "error_type": type(exc).__name__},
+            )
```

Preview capped; complete diff is in the linked patch.

### `hub/research-expertise/src/research_expertise/cli.py`

```diff
diff --git a/hub/research-expertise/src/research_expertise/cli.py b/hub/research-expertise/src/research_expertise/cli.py
index a64513bb..377ba302 100644
--- a/hub/research-expertise/src/research_expertise/cli.py
+++ b/hub/research-expertise/src/research_expertise/cli.py
@@ -9 +9 @@ from pathlib import Path
-from .store import Store
+from .store import CONFIG, Store
@@ -36 +36,11 @@ def main():
-    store = Store()
+    guidance = (
+        f"Neo4j connection configuration is missing or invalid: {CONFIG}. "
+        "Create a private JSON object with uri, username, password and optional database; "
+        "restrict permissions to 600. See the installed application README.md.\n"
+    )
+    try:
+        if not CONFIG.is_file():
+            parser.exit(3, guidance)
+        store = Store()
+    except (OSError, ValueError, KeyError, TypeError):
+        parser.exit(3, guidance)
```

Preview capped; complete diff is in the linked patch.

### `hub/research-expertise/src/research_expertise/inspection.py`

```diff
diff --git a/hub/research-expertise/src/research_expertise/inspection.py b/hub/research-expertise/src/research_expertise/inspection.py
index 7b4a0334..e4e05d52 100644
--- a/hub/research-expertise/src/research_expertise/inspection.py
+++ b/hub/research-expertise/src/research_expertise/inspection.py
@@ -19 +19 @@ def snapshot(store, concept="", demo=None):
-    docs = []
+    docs, verified = [], {}
@@ -22,0 +23 @@ def snapshot(store, concept="", demo=None):
+            verified[d["id"]] = dict(d)
@@ -29,0 +31 @@ def snapshot(store, concept="", demo=None):
+        binding = verified[d["id"]]
@@ -33 +35,3 @@ def snapshot(store, concept="", demo=None):
-            "WHERE type(r) IN ['RX_ABOUT','RX_CITES','RX_HAS_PASSAGE'] "
+            "WHERE d.sha256=$sha256 AND d.manifest_sha256=$manifest_sha256 "
+            "AND d.corpus=$corpus AND d.active=true "
+            "AND type(r) IN ['RX_ABOUT','RX_CITES','RX_HAS_PASSAGE'] "
@@ -38,0 +43,3 @@ def snapshot(store, concept="", demo=None):
+            sha256=binding["sha256"],
+            manifest_sha256=binding["manifest_sha256"],
+            corpus=CORPUS,
@@ -39,0 +47,4 @@ def snapshot(store, concept="", demo=None):
+        if not current(dict(binding, doc_sha256=binding["sha256"])):
```

Preview capped; complete diff is in the linked patch.

### `hub/research-expertise/install.py`

```diff
diff --git a/hub/research-expertise/install.py b/hub/research-expertise/install.py
index 1a95fb1b..1ac450dd 100644
--- a/hub/research-expertise/install.py
+++ b/hub/research-expertise/install.py
@@ -2 +2 @@
-"""Install the checked-in expertise application into a stable user-local directory."""
+"""Install a stable user-local application with recoverable upgrades."""
@@ -6,0 +7 @@ import argparse
+import fcntl
@@ -11,0 +13,4 @@ import subprocess
+import sys
+import tempfile
+import tomllib
+from uuid import uuid4
@@ -14,17 +19,14 @@ import subprocess
-def main():
-    parser = argparse.ArgumentParser(description=__doc__)
-    parser.add_argument("--schedule", action="store_true", help="Refresh only this corpus hourly")
-    args = parser.parse_args()
-    source = Path(__file__).resolve().parent
-    home = Path.home()
-    target = home / ".local/share/research-expertise/app"
```

Preview capped; complete diff is in the linked patch.

### `hub/research-expertise/src/research_expertise/mcp_server.py`

```diff
diff --git a/hub/research-expertise/src/research_expertise/mcp_server.py b/hub/research-expertise/src/research_expertise/mcp_server.py
index eb558fb5..3b5c0449 100644
--- a/hub/research-expertise/src/research_expertise/mcp_server.py
+++ b/hub/research-expertise/src/research_expertise/mcp_server.py
@@ -5,2 +5,3 @@ from __future__ import annotations
-import atexit
-from functools import lru_cache
+import asyncio
+from concurrent.futures import ThreadPoolExecutor
+from functools import lru_cache, wraps
@@ -40 +41,23 @@ def _close_store() -> None:
-atexit.register(_close_store)
+# One owner thread preserves the cached Embedder's SQLite connection affinity.
+_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="research-expertise")
+
+
+def _worker_tool(**options):
+    """Register asynchronous MCP dispatch while retaining the local sync API."""
+    def register(function):
+        @wraps(function)
+        async def invoke(*args, **kwargs):
+            loop = asyncio.get_running_loop()
```

Preview capped; complete diff is in the linked patch.

### `scripts/research_gate.py`

```diff
diff --git a/scripts/research_gate.py b/scripts/research_gate.py
index 23540f43..7d09d5ed 100644
--- a/scripts/research_gate.py
+++ b/scripts/research_gate.py
@@ -292 +292,3 @@ def check_spans(packet, claim, spans, root, *, authored=False):
-    numbers = re.findall(r'(?<![\w])\d+(?:[.,]\d+)*(?:%|[a-zA-Z]+)?', numeric_text)
+    numbers = re.findall(
+        r'(?<!\w)\d(?:_?\d)*(?:[.,]\d(?:_?\d)*)*'
+        r'(?:[eE][+-]?\d(?:_?\d)*)?(?:%|[a-zA-Z]+)?', numeric_text)
```

### `scripts/research_library.py`

```diff
diff --git a/scripts/research_library.py b/scripts/research_library.py
index 9d8eca82..85734d70 100755
--- a/scripts/research_library.py
+++ b/scripts/research_library.py
@@ -10,0 +11,2 @@ import argparse
+import fcntl
+import hashlib
@@ -14,0 +17 @@ import sys
+from contextlib import contextmanager
@@ -24,0 +28,18 @@ def load(name, path):
+@contextmanager
+def source_guard(root, source_id):
+    """Serialize cooperating wrapper ingests of one upstream source identity.
+
+    Take this guard before the provenance and upstream library locks. Neither
+    inner lock calls back into the wrapper. Direct upstream writers that bypass
+    this wrapper must adopt the same protocol to share this protection.
+    """
+    directory = Path(root) / 'provenance/ingest-locks'
+    directory.mkdir(parents=True, exist_ok=True)
+    key = hashlib.sha256(source_id.encode()).hexdigest()
+    path = directory / (key + '.lock')
```

Preview capped; complete diff is in the linked patch.

### `scripts/research_provenance.py`

```diff
diff --git a/scripts/research_provenance.py b/scripts/research_provenance.py
index fbc1e594..ab467e69 100644
--- a/scripts/research_provenance.py
+++ b/scripts/research_provenance.py
@@ -78 +78,5 @@ def archive(library, metadata):
-            if saved['snapshot_sha256'] != sha:
+            expected = {'schema': 'research-source/v1', 'snapshot_id': identity,
+                        'source_id': metadata['id'], 'url': metadata['url'],
+                        'snapshot_sha256': sha, 'snapshot_path': str(path),
+                        'chars': len(body.decode('utf-8'))}
+            if not isinstance(saved, dict) or any(saved.get(key) != value for key, value in expected.items()):
```

### `scripts/research_transaction.py`

```diff
diff --git a/scripts/research_transaction.py b/scripts/research_transaction.py
index 8fd83576..2b659e44 100644
--- a/scripts/research_transaction.py
+++ b/scripts/research_transaction.py
@@ -5,0 +6 @@ import json
+import os
@@ -6,0 +8,2 @@ import shutil
+import stat
+import tempfile
@@ -9,0 +13,8 @@ from pathlib import Path
+def destination(path):
+    """Resolve aliases before coverage checks while refusing final symlinks."""
+    path = Path(path).absolute()
+    if path.is_symlink():
+        raise ValueError('projection destination cannot be a symlink: ' + str(path))
+    return path.resolve()
+
+
@@ -12,2 +23,2 @@ class Transaction:
-        self.root = Path(root).absolute()
-        self.registry = Path(registry).absolute() if registry is not None else None
+        self.root = Path(root).resolve()
```

Preview capped; complete diff is in the linked patch.

### `hub/research-expertise/src/research_expertise/store.py`

```diff
diff --git a/hub/research-expertise/src/research_expertise/store.py b/hub/research-expertise/src/research_expertise/store.py
index 2d8a3d37..b46a9d3b 100644
--- a/hub/research-expertise/src/research_expertise/store.py
+++ b/hub/research-expertise/src/research_expertise/store.py
@@ -7,0 +8 @@ import hashlib
+from importlib.metadata import version
@@ -24,0 +26 @@ CHUNKING_VERSION = "bge-480tokens-v1"
+EMBEDDING_RECIPE = "fastembed-passage-query-v1"
@@ -29,0 +32,17 @@ CORPUS = "hub-concepts"
+def embedding_recipe():
+    """Describe the exact vector space; changes require a deliberate refresh."""
+    return {
+        "model": MODEL,
+        "repository": MODEL_REPO,
+        "revision": MODEL_REVISION,
+        "dimensions": DIMENSIONS,
+        "fastembed_version": version("fastembed"),
+        "recipe": EMBEDDING_RECIPE,
+    }
+
+
+def embedding_space_id():
```

Preview capped; complete diff is in the linked patch.

## 6. Blind re-audit

The first independent nine-file review found numeric-token rejection. The final
independent review read all 17 assigned files, 5,024 lines, and rechecked hashes.
It found inactive-vector candidate starvation. Its 516 successful checks and
five missing-`llms_txt` environment failures were preserved; the five dependency
failures passed with the already-installed dependency path. The final retirement
repair adds one source line, making the scoped current source total 5,025.

No third blind gate ran. The later actual Neo4j test establishes the specific
repair, not a new independent CLEAN verdict.

## 9. Summary

2 diagnostic/repair iterations plus targeted post-gate repair · 18 fix-track
passes considered, plus M5 · standard profile · 14 fixes (4 High, 10 Medium) ·
final known C/H/M: 0/0/0 · Verify: PASS for changed surfaces ·
**Status: BLIND-AUDIT-DISSENT** · repository coverage: partial, 17/636 current files.

## 10. Snapshot and rollback

Preimages are retained outside the checkout under the local skill-consolidation
backup convention. Run a restoration only in the same owned isolated checkout.
Preserve unrelated work. For example, the exact source restoration is:

```sh
cp "$HOME/.claude/skill-consolidation/backups/llms-explorer-lifecycle-20261111/hub/research-expertise/src/research_expertise/store.py" hub/research-expertise/src/research_expertise/store.py
cp "$HOME/.claude/skill-consolidation/backups/llms-explorer-lifecycle-20261111/scripts/research_transaction.py" scripts/research_transaction.py
cp "$HOME/.claude/skill-consolidation/backups/llms-explorer-lifecycle-20261111/scripts/research_provenance.py" scripts/research_provenance.py
cp "$HOME/.claude/skill-consolidation/backups/llms-explorer-lifecycle-20261111/scripts/research_gate.py" scripts/research_gate.py
cp "$HOME/.claude/skill-consolidation/backups/llms-explorer-lifecycle-20261111/scripts/research_library.py" scripts/research_library.py
rm hub/research-expertise/tests/test_cli.py
rm hub/research-expertise/tests/test_inspection.py
rm hub/research-expertise/tests/test_install.py
rm hub/research-expertise/tests/test_neo4j_retirement.py
rm tests/test_research_library.py
```

Companion mirrors, changed existing tests and metadata have their own retained
preimages. Production upgrades now retain a complete previous app/venv and
restore it on failure. Canonical research is not part of a source rollback.

## 11. Index and scope

Index: curated static source/navigation metadata refreshed and path-checked.
Semantic index refresh skipped to preserve the legacy pause.
The committed `.cdo/ledger.json` records final hashes for exactly 17 files. The
[next source coverage record](research-lifecycle-source-coverage-2026-11-11.json)
distinguishes diagnostic coverage, final bytes and post-gate verification.
The remaining 619 current source files are not reviewed by this run.

## 12. Memory-central

10 relevant lesson rows and 1 convention row consulted through bounded search;
no stale row reversed an architecture decision. No memory-central file was
rewritten. Durable findings and continuation are recorded by the parent task.

## Passes that ran (receipt)

| Pass | State | Files | Note |
|---|---|---|---|
| C1 | ran | 17 |  |
| C2 | ran | 17 |  |
| C3 | ran | 17 |  |
| S1 | ran | 17 |  |
| S2 | ran | 17 |  |
| S3 | ran | 17 |  |
| S4 | ran | 17 |  |
| S5 | ran | 17 |  |
| P1 | ran | 17 |  |
| P2 | ran | 17 |  |
| M1 | ran | 17 |  |
| M2 | ran | 17 |  |
| M3 | ran | 0 | Research canonical/projection boundaries and existing contracts reviewed; broader architecture remains outside selected scope. |
| M4 | ran | 17 |  |
| T1 | ran | 17 |  |
| T2 | ran | 0 | Owning package locks, model pin, Python ABI and Dependabot reviewed; no comprehensive CVE or license certification. |
| T3 | ran | 0 | Existing CI, exact owning-package environments, index gate and adapter sync verified. |
| T4 | ran | 0 | Suite eligibility and timers reviewed; no parallelism change justified for subsecond package suite. Site build/render tests remain sequential. |
| M5 | ran | 0 | CLI config preflight, supported Python installer runtime, stable paths, rollback and worker shutdown exercised. |

Fix-track passes that ran: 18 of 18 (+1 conditional)
Mode: incremental   Status: BLIND-AUDIT-DISSENT
Files reviewed this run: 17
Source files covered by the ledger now: 17 of 636
Still unreviewed or changed since review: 619
