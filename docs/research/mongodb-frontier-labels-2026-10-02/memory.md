# Continuation memory

Version: 2.1.0
Delta: Add AKO Reconciliation Skip Annotation to both trees, defer its pack from vector search, and continue at AKO Subobject CRDs Deprecated.

## Durable context

- User explicitly authorized retaining and committing the prior 25-concept research; do not discard it.
- The exact historical input is pinned by the source commit and SHA in `README.md`; do not reconstruct it from the changing live trees.
- All 686 exact labels were present in the hub frontier when reconciled. Eight have site-tree state drift. Preserve these exact labels and report any row the runner cannot complete.
- Parent facts and Firecrawl page caches are context only. Every child must meet the independent source-host gate before it is eligible for tree sync.
- Research page bodies and compiled packs remain under `/Users/mitch/.global-ai-hub/research-tests/mongodb-full-frontier-20261002/`; public repository files contain only inventory, status, citations, and summaries.
- Keep Ollama, semantic indexing, embeddings, registry rebuilds, and semantic routing paused.

## Current implementation and remaining work

The clean branch `/Users/mitch/dev/worktrees/mongodb-frontier-batch-tui` adds a Textual batch action with a local queue manifest, per-concept resume checkpoint, selectable concurrency, and a post-run merge-only sync to the site and hub trees. `hub/scripts/frontier_research_batch.py` now reads parent packs or the maintained parent skill reference, batch-scrapes deduplicated source URLs, and excludes inherited sources from each child's independent host gate. Its per-concept run folders use a hash suffix to preserve exact-label identity when slugs collide.

The historical queue file is `frontier-input.json`; the immutable live queue is `/Users/mitch/.global-ai-hub/research-tests/mongodb-full-frontier-20261002/full-frontier-run/concepts.txt` (686 exact labels, SHA-256 `8089d5aa1dcd4bc7dd93f66b4a20ac3383ca4a92589302ce84e1d404ef094367`). Resume with the same runner arguments and `--jobs 1`; the runner skips complete rows and retries failed ones. Parent contexts were sourced for 69 of 71 parents. The shared scrape examined 588 URLs; 169 page bodies were reusable and 425 did not map to a saved body, frequently because references contain placeholders or templated API URLs. The child roles must still gather independent sources. Avoid firing a duplicate run while its runner PID remains active.

The original short-lived test run wrote two interruption-related `failed` result rows; neither changed a tree. `AKO CRDs` later passed the three-new-host check and compiled; its private report and pack are complete. The runner paused before continuing so future cases use deterministic slug mapping. Failed rows are retryable and must not be counted as final outcomes. The existing 25-gap report remains at `docs/research/mongodb-uncapped-frontier-batch-2026-10-02/README.md` and must stay committed with the new work.


## Current checkpoint — 2026-10-02T03:08:50Z

The runner remains active in `/Users/mitch/dev/worktrees/mongodb-frontier-batch-tui` and is researching `AKO GitOps`. Its append-only result log has five entries: two interrupted `AKO CRDs` attempts, one successful `AKO CRDs` result, and source-gate failures for `AKO Deletion Protection v2.0` and `AKO Dry Run Mode`. The current AKO CRDs pack passed with nine new hosts and has been added to the hub and site concept trees. The site build passed with 1,304 routes. The public 686-row status ledger now records one complete, two failed, one active, and 682 not-yet-started rows; the two source-gate failures remain unresolved and retryable.

The aggregate private `run-state.json` was stale while the runner advanced, so do not use it as the live source. Inspect the active process and append-only `results.jsonl` before updating counts. Keep the PR draft and continue the exact immutable queue; do not claim full-frontier completion. Semantic indexing, embeddings, registry rebuilds, and Ollama remain paused.


## Current checkpoint — 2026-10-02T03:16:07Z

`AKO GitOps` completed with 11 total sources, including one inherited source; its independent-source gate passed and the pack compiled. The concept is committed in the global hub tree and synced into the site tree. `AKO Helm Installation` is now the live concept. The status ledger covers all 686 exact input rows: two complete, two failed source gates, one active, and 681 not yet started. The private append-only runner log is authoritative; do not infer completion from the stale private aggregate checkpoint while the process is running.

The site build passed with the two completed concepts. After running `sync_trees.py --targets site --apply --regen`, retain the new AKO concept packs and generated context/tree changes; restore unrelated LiteLLM and other pack churn from `gen_concepts`. Keep PR 138 draft while 684 rows remain unresolved.


## Search-index pause and CI contract

The CI site test `test_meta_covers_exactly_the_committed_concept_packs` failed because it required every new pack to have a vector-search metadata row. The project must keep semantic indexing and embeddings paused. Do not run `site/tools/gen_search_index.mjs` to fix this. `site/src/data/search-meta-exclusions.json` now lists researched packs that are deliberately deferred; the test requires the indexed and deferred slug sets to be disjoint and together cover all committed packs. The vector binary and search metadata stay unchanged until indexing resumes. This follows MongoDB CFE decision `KNOW-291`.


## Current checkpoint — 2026-10-02T03:27:04Z

`AKO Helm Installation` completed the source gate with eleven sources, including one inherited source, and compiled successfully. Its concept is committed in the hub tree and synced into the site tree. The runner has moved to `AKO Independent CRDs`. The 686-row ledger now has three complete, two source-gate failures, one active, and 680 not yet started. Add `ako-helm-installation` to the explicit semantic-index deferrals; leave search vectors and metadata unchanged while indexing is paused.


## Current checkpoint — 2026-10-02T03:37:23Z

`AKO Independent CRDs` passed with four new sources; seven inherited references remained context-only. Its compiled pack and tree node are in both canonical trees. `AKO Reconciliation Skip Annotation` is now active. The exact 686-row ledger has four complete, two independent-source failures, one active, and 679 not yet started. The site tree and generated data passed consistency checks. Add `ako-independent-crds` to the deferred semantic-index manifest; do not regenerate embeddings.


## Current checkpoint — 2026-10-02T03:45:27Z

`AKO Reconciliation Skip Annotation` passed with five new sources and seven inherited references excluded from qualification. Its compiled pack and tree node are in both canonical trees. `AKO Subobject CRDs Deprecated` is now active. The exact 686-row ledger has five complete, two independent-source failures, one active, and 678 not yet started. The site tree generated successfully and remains guarded against regressions. Add `ako-reconciliation-skip-annotation` to the deferred semantic-index manifest; keep vector metadata and binaries unchanged.
