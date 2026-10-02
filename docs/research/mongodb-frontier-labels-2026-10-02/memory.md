# Continuation memory

Version: 1.6.0
Delta: Record two source-gate failures, sync AKO CRDs to both trees, and resume at AKO GitOps.

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
