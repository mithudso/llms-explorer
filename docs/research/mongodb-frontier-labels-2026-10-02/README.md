# MongoDB historical frontier batch

Version: 2.12.0
Delta: Reconcile AWS PrivateLink and current 686-row batch state.

## Input and reconciliation

The immutable queue is `frontier-input.json`. It contains 686 distinct exact labels from `MongoDB Expert Knowledge` at global-ai-hub commit `2a8fee3fc01befd8fff630aedc2d75565582c441` (tree SHA-256 `3fc510aeb562e43636aa81454e7693ee73dfe4ebddb67c75d43d5d646a81f922`). The snapshot had 703 nodes, 120 MongoDB-family nodes, and 696 child edges. Case-folding yields 685 labels because two exact labels differ only in capitalization; both are retained and researched independently.

At run start, all 686 exact labels were frontier entries in the hub tree. The website tree had 678 matching frontier entries and eight tree-state differences: one researched (`Partition Fields`) and seven absent. The batch uses the hub frontier as source of truth while retaining all eight initial differences in the reconciliation ledger. The qualified `AKO CRDs` result has since been added to both trees. See `reconciliation.json` for every row and parent edge.

The complete parent grouping is in [`parent-cohorts.md`](parent-cohorts.md): 71 source-sharing cohorts cover all 696 parent-child edges while retaining 686 exact research rows.

## Method

The resumable runner uses one concept row as the unit of synthesis and persistence. Each row receives four bounded research roles, inherits compact parent facts, and receives cached parent-source pages retrieved in deduplicated Firecrawl cohorts. Inherited parent origins do not count toward the child’s independent-source gate; a concept completes only after at least three new source hosts and successful pack compilation. Completed rows are checkpointed in `results.jsonl`; failed and not-yet-started rows remain available for resumption. Only completed rows are merged into either concept tree.

This design batches retrieval across related concepts without merging sibling claims into a single synthesis. No research result is presumed qualified until its row passes the runner’s source gate and compile checks. Firecrawl page bodies and per-concept source packs stay in the private global-ai-hub research run; this public report stores the input inventory, status ledger, and concise outcomes only.

## Run state

The private append-only `results.jsonl` is authoritative for per-label completion. The public `row-status.jsonl` mirrors the 686 historical labels, and `run-state.json` records aggregate counts and version/delta. Update both after each resume. `prompts.md` and `memory.md` preserve the exact request and continuation state.

Research run: `/Users/mitch/.global-ai-hub/research-tests/mongodb-full-frontier-20261002/full-frontier-run`

## Current progress

The exact 686-name queue is running with up to three concurrent concepts; each concept fans out four bounded research roles. 20 concepts have passed and compiled. 2 concepts remain retryable after two source-gate failures each. Active concepts: `Aggregation Expressions`, `Aggregation Pipeline in Charts`, `Air-Gap and Local Mode`. The ledger records 661 pending rows. The append-only results log has 26 attempt records, including 6 failed attempts. Inherited origins do not count toward child qualification. The resumed retrieval examined 543 URLs, found 260 cached pages, and recorded two retrieval issues. Parent page caches are shared context; child research still uses independent web search and must meet the three-new-host gate. See `row-status.jsonl` for all labels and the private run directory's `results.jsonl` for the authoritative checkpoint. The process-local runner remains authoritative for active concepts.

Firecrawl retrieval counts do not measure model token savings. No token total or controlled comparison against individual retrieval was captured. The twelve new site packs are explicitly excluded from semantic vector search while indexing remains paused; `site/src/data/search-meta-exclusions.json` tracks them so pack/metadata coverage remains verifiable without generating embeddings.


The second concept, `AKO Deletion Protection v2.0`, produced only two new hosts after inherited sources were excluded. The runner recorded it as failed, kept it unresolved, and moved on. This label remains a frontier item until a later pass supplies independent sources.
