# Continuation memory

Version: 3.5.0
Delta: Add AWS Marketplace and Atlas Charts access control and advance the queue.

## Durable context

- User explicitly authorized retaining and committing the prior 25-concept research; do not discard it.
- The exact historical input is pinned by the source commit and SHA in `README.md`; do not reconstruct it from the changing live trees.
- All 686 exact labels were present in the hub frontier when reconciled. Eight have site-tree state drift. Preserve these exact labels and report any row the runner cannot complete.
- Parent facts and Firecrawl page caches are context only. Every child must meet the independent source-host gate before it is eligible for tree sync.
- Research page bodies and compiled packs remain under `/Users/mitch/.global-ai-hub/research-tests/mongodb-full-frontier-20261002/`; public repository files contain only inventory, status, citations, and summaries.
- Keep Ollama, semantic indexing, embeddings, registry rebuilds, and semantic routing paused.

## Current implementation and remaining work

The clean branch `/Users/mitch/dev/worktrees/mongodb-frontier-batch-tui` adds a Textual batch action with a local queue manifest, per-concept resume checkpoint, selectable concurrency, and a post-run merge-only sync to the site and hub trees. `hub/scripts/frontier_research_batch.py` now reads parent packs or the maintained parent skill reference, batch-scrapes deduplicated source URLs, and excludes inherited sources from each child's independent host gate. Its per-concept run folders use a hash suffix to preserve exact-label identity when slugs collide.

The historical queue file is `frontier-input.json`; the immutable live queue is `/Users/mitch/.global-ai-hub/research-tests/mongodb-full-frontier-20261002/full-frontier-run/concepts.txt` (686 exact labels, SHA-256 `8089d5aa1dcd4bc7dd93f66b4a20ac3383ca4a92589302ce84e1d404ef094367`). Resume with the same runner arguments and `--jobs 3`; the runner skips complete rows and retries failed ones. Each concept fans out four role processes, so three concept workers use about twelve simultaneous research subprocesses. Parent contexts were sourced for 69 of 71 parents. The initial shared scrape examined 588 URLs; a resumed retrieval examined 543 URLs, with 260 cached pages and two retrieval issues. Child roles still gather independent sources. Avoid firing a duplicate run while its runner PID remains active.

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


## Current checkpoint — 2026-10-02T03:52:48Z

`AKO Subobject CRDs Deprecated` passed with four new sources and seven inherited references excluded from qualification. Its compiled pack and tree node are in both canonical trees. `AKO Troubleshooting` is now active. The exact 686-row ledger has six complete, two source-gate failures, one active, and 677 not yet started. The site build and generated-tree comparison passed. Add `ako-subobject-crds-deprecated` to the deferred semantic-index manifest; keep vector metadata and binaries unchanged.


## Current checkpoint — 2026-10-02T04:02:00Z

`AKO Troubleshooting` passed with ten sources, including one inherited source, and compiled successfully. Its pack and tree node are in both canonical trees. `AKO Workload Identity` is now active. The exact 686-row ledger has seven complete, two source-gate failures, one active, and 676 not yet started. The site build and tree guard passed. Add `ako-troubleshooting` to the deferred semantic-index manifest; do not regenerate vectors while indexing is paused.


## Current checkpoint — 2026-10-02T04:48:32Z

The runner resumed the same immutable 686-label queue with `--jobs 3`. Ten additional concepts have completed: the AKO Workload Identity and AKS concepts, ASP Pricing Model, AWS CloudFormation, CDK, IAM federation, ISV, Marketplace, and Atlas Charts Access Control rows. All are present in both trees. Their qualifying source counts are in the results log; inherited sources remain context-only. The twelve new packs are excluded from semantic indexing while vectors remain paused. `AWS PrivateLink`, `Aggregation Expressions`, and `Aggregation Pipeline in Charts` are active. The two prior source-gate failures were retried and again yielded only two independent hosts each. There are nineteen unique completed labels, two unique source-gate failures, three active concepts, and 662 not-yet-started labels. The log has 25 entries because it preserves attempts. Parent retrieval for the resumed frontier covered 543 URLs, cached 260 pages, and recorded two retrieval issues. Continue syncing every newly completed, qualified concept into both trees and commit only the scoped repository files.


## Current checkpoint — 2026-10-02T04:54:33Z

The live runner has 20 unique qualified concepts, 2 retryable source-gate failures, 3 active concepts, and 661 pending labels out of the immutable 686-row queue. The append-only log has 26 attempt records, including 6 failed attempts. Active labels: Aggregation Expressions, Aggregation Pipeline in Charts, Air-Gap and Local Mode. `row-status.jsonl` was rebuilt from the result log and active child processes. Continue the same runner; do not start a duplicate. Both trees need a scoped checkpoint commit after sync. Semantic indexing, embeddings, registry rebuilds, and Ollama remain paused.


## Current checkpoint — 2026-10-02T04:58:51Z

The live runner has 23 unique qualified concepts, 2 retryable source-gate failures, 3 active concepts, and 658 pending labels out of 686. The append-only log has 29 attempts, including 6 failed attempts. Active labels: Analytics Node Configuration, Analytics Node Cost Model, Analytics Node Monitoring. Site and hub trees now include all 23 qualified concepts. Continue the existing runner; do not start a duplicate. Semantic indexing, embeddings, registry rebuilds, and Ollama remain paused.


## Current checkpoint — 2026-10-02T05:05:37Z

The live runner has 26 unique qualified concepts, 2 retryable source-gate failures, 3 active concepts, and 655 pending labels out of 686. The append-only log has 32 attempts, including 6 failed attempts. Active labels: Analytics Node Read Preference Routing, Analytics Node Sizing, Anti-Patterns. Both concept trees include all qualified concepts through Analytics Node Configuration, Analytics Node Cost Model, and Analytics Node Monitoring. Continue the existing runner; do not start a duplicate. Semantic indexing, embeddings, registry rebuilds, and Ollama remain paused.
