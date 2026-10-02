# MongoDB historical frontier batch

Version: 1.6.0
Delta: Sync the 686-row ledger and both trees with the first completed concept and current source-gate outcomes.

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

The exact 686-name queue is running with one concurrent concept. `AKO CRDs` is the first completed row: it used nine new source hosts and compiled successfully, and its result is now present in both trees. `AKO Deletion Protection v2.0` and `AKO Dry Run Mode` each failed the independent-source gate with two new hosts. `AKO GitOps` is active. Two earlier `AKO CRDs` attempts were interrupted while correcting Firecrawl mapping and parent-reference inheritance; the successful third attempt completed the row. The resumed runner assigns unique slugs deterministically for two pairs of exact labels that normalize to the same slug. Shared retrieval examined 588 deduplicated parent URLs: 216 page bodies were cached and 380 URLs did not produce a recognized cached page, often because inherited references contain placeholders or parameterized API examples. Child research still uses independent web search and must meet the new-host gate. See `row-status.jsonl` for all labels and the private run directory's `results.jsonl` for the append-only checkpoint. The aggregate counts are in `run-state.json`; the process-local runner remains authoritative for its active concept.

Firecrawl retrieval counts do not measure model token savings. No token total or controlled comparison against individual retrieval was captured.


The second concept, `AKO Deletion Protection v2.0`, produced only two new hosts after inherited sources were excluded. The runner recorded it as failed, kept it unresolved, and moved on. This label remains a frontier item until a later pass supplies independent sources.
