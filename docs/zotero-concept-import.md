# Zotero concept-tree import

Version: 1.0.0. Delta: adds a provenance-preserving concept union, RDF export, guarded connector import, and live verification.

`scripts/zotero_concept_import.py` reads the hub and repository trees without editing either. Stable slugs identify concepts; matching normalized names reconcile changed slugs. It retains every input record verbatim in the manifest and in each note. List fields are unioned. The first input wins scalar conflicts, which are recorded separately. Missing parents, parent cycles, and contradictory slug identities stop preparation.

The destination is **My Library → Global AI Concept Tree**. Every concept has a nested collection and a standalone **concept/index note**. These records are deliberately not presented as scholarly publications. A declared `sourcesCount` does not establish bibliographic identity or mean that number of papers exists in Zotero. Local skill and concept-pack files are linked when present. HTTP URLs extracted from those files are listed as unverified cited URLs. Declared published pack links are retained with that label. The importer does not download content, fetch PDFs, invoke embeddings, or access Ollama.

## Commands

```sh
# Prepare private local manifest and RDF; no Zotero changes.
python3 scripts/zotero_concept_import.py

# Import using Zotero's built-in connector. Select My Library root first.
python3 scripts/zotero_concept_import.py --execute

# Verify a connector or native File > Import operation using the read-only API.
python3 scripts/zotero_concept_import.py --verify-only

# Focused tests in a transient uv environment.
uv run --with pytest python -m pytest tests/test_zotero_concept_import.py -q
```

The default private state directory is `~/.codex/evals/zotero/concept-tree`. It contains `manifest.json`, `concept-tree.rdf`, `checkpoint.json`, the successful connector response, and `verification.json` with the slug-to-item/collection key mapping. A process lock prevents overlapping importer runs. A completed run can be repeated without creating items. Source changes and incomplete imports stop rather than silently duplicating or overwriting existing data. A interrupted import that actually finished can be recovered with readback. A partially written hierarchy requires explicit repair before another import; the script does not claim transactional rollback.

Readback verifies a unique root, all collection parent edges, note item types, collection memberships, unique stable-slug tags, content digest tags, and concept identifiers in note HTML. Existing item keys are checked after a connector import. No path opens or writes Zotero's SQLite database.

## Supported routes and fallback

The built-in [connector HTTP server](https://www.zotero.org/support/dev/client_coding/connector_http_server) performs imports. The installed RDF translator supports collections and notes. The [local API](https://www.zotero.org/support/dev/web_api/v3/basics) supplies paginated readback. Zotero 10 additionally supports authenticated local writes, but this script does not request persistent authorization.

On the initial Zotero 10.0.4 test, `/connector/import` returned HTTP 400 before creating records when given RDF with either `application/rdf+xml` or `text/plain`. If this occurs, preserve the artifacts and use Zotero's native **File → Import** on `concept-tree.rdf`. Do not add a second wrapper collection; the RDF already contains `Global AI Concept Tree`. Then run `--verify-only`. Do not repeatedly import the file before readback: native import does not perform the script's duplicate checks.

## Initial prepared scope

The September 28, 2026 inputs contain 686 hub records and 684 repository records. Their union contains 687 concepts (683 shared slugs, three hub-only records, and one repository-only record). Five shared records differ in their declared child lists. Exact originals remain in the provenance blocks. Collection edges follow `parentConcept`; declared child names without separate records remain note metadata, not fabricated concept records.
