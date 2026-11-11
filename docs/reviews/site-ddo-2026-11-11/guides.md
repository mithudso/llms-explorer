# Guide and reference prose review

Version:1.0.1. Delta:v1.0.0 to v1.0.1; completed check receipts. TASK-1351.

Full-depth prose review covered 62 public document sources. 60 confirmed findings were corrected. The result remains **partial**, because every external factual claim has not been independently checked and the root blind audit remains pending. The JSON holds per-document contracts, baseline/final hashes, pass dispositions, finding/source records, deltas and unresolved gaps.

The main corrections remove stale paid-plan/API/CLI promises, explain domain nodes and existing accounts, separate citation format from truth, constrain rights/permission claims, correct retrieval-agreement and hash-ID reasoning, and distinguish offline work from acquisition. Canonical reference sources were edited before regenerating the public copies. The terminal user guide was changed at its package source and copied with the existing sync_guide helper.

Canonical parity warning: the committed attributes/passes projections were already behind their canonical files. Regeneration also incorporates those existing v3 rubric additions; this is a projection refresh, not new optimizer policy authored here.

## Coverage

| Collection | Documents |
|---|---:|
| Reference |15|
| Examples |14|
| Skill descriptions |32|
| Package user guide |1|

Code blocks and historical transcript output were retained verbatim. They have not been executed as part of this review. Do not treat their presence, or a zero editorial finding count, as a claim of runtime success. Current vendor/API compatibility for the recipe07 Chroma/Ollama example remains unverified. Historic hiring claims and aggregate confidence require primary evidence. Canonical rubric policy discrepancies require their owner rather than a silent prose change.

Snapshot & rollback: each JSON row gives its private snapshot path. Restore only after checking for later writers, with `cp <snapshot> <absolute-target>` using the exact paths recorded there.

## Verification receipts

- `python3 site/tools/gen_reference.py`: exit0; six canonical copies regenerated.
- Existing `gen_downloads.sync_guide()` helper: exit0; guide copied from package source.
- `git diff --check` over owned paths: exit0.
- Five relevant pytest files: **exit1,17passed,4failed**. Each failure is `FileNotFoundError` for absent built output under `site/dist/` (sitemap, article HTML or downloads HTML). This is not a passing rendered check; the root must rebuild and rerun.

Final candidates remain `REVIEWED_WITH_GAPS` until all-claim evidence and independent blind review are resolved.
