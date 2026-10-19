# Concept Family Explorer — mongodb mql query optimization
*Run: 2026-10-18/19 (dispatched by /full-suite) · concept-count budget: none, maxRounds=3 · threshold: 3.2/5 · inventory: hub tree `~/.global-ai-hub/concept-tree/tree.json` (canonical v3) + installed skills · Stele MCP absent this session*

## Conceptual family map
- **Parent / super-domain**: database query optimization (HAVE: deep-query-optimizer, postgresql-expert); MongoDB Performance Troubleshooting (HAVE, STALE 2026-05-25); mongodb-query-performance reference (HAVE, STALE 2026-05-29); learned/ML query optimization (HAVE: da-43); SQL query optimization (HAVE).
- **Siblings**: WiredTiger internals (HAVE); FTDC diagnostics (HAVE); schema design for query patterns (HAVE); sharding/shard-key design (HAVE); Atlas Search tuning (HAVE); Atlas Vector Search/HNSW (frontier, Atlas family); transactions (HAVE); driver pooling/CSOT (HAVE); collation (HAVE); geospatial (HAVE 2026-09-24).
- **Children / sub-concepts**: 40 GAPs researched in cohorts A–F (explain/planner, compound index design, special indexes and builds, query shapes, time series, tooling) — see the scored table; HAVE-fresh from the stalled suite: Pipeline Optimization, Memory Limits and allowDiskUse, SBE vs classic defaults, express execution path, $lookup.
- **Adjacent / cross-over**: Compass explain, Atlas Query Insights/Profiler, Performance Advisor, Atlas Admin API/CLI automation (researched); log tooling, ODM pitfalls, benchmarking, MCP natural-language querying (HAVE).
- **Frontier / emerging**: 8.0 query settings and $queryStats, 8.0 block processing, 8.3 cost-based ranker, post-8.0 engine changes incl. 9.0 (researched); LLM-assisted optimization (researched); Queryable Encryption query performance, CQF/Bonsai history (skipped, logged).

## Scored gap table (round 0)
| Concept | Rel | Use | Nov | Int | Via | CVS | Decision | Why |
|---|---|---|---|---|---|---|---|---|
| Query Operator Anti-Patterns ($regex, negation, $where, $expr, $exists) | 5 | 5 | 4 | 4 | 5 | 4.65 | RESEARCH (D) | dmqo audit lists them; no reference depth |
| Blocking Sort and Index-Backed Sort | 5 | 5 | 4 | 3 | 5 | 4.50 | RESEARCH (D) | no coverage of 100MB sort limit / sort+limit coalescence / SORT_MERGE |
| Pagination Patterns (skip/limit vs range/keyset) | 5 | 5 | 4 | 3 | 5 | 4.50 | RESEARCH (D) | no coverage |
| Explain Plan Interpretation | 5 | 5 | 3 | 4 | 5 | 4.45 | RESEARCH (A) | frontier placeholder; refs cover explain() output only partially (no 8.0 express/SBE stage vocab) |
| Query Planning and Plan Cache | 5 | 5 | 3 | 4 | 5 | 4.45 | RESEARCH (A) | placeholder; §3.2 covers basics, no SBE plan cache / replanning / eviction |
| Compound Indexes and ESR Rule | 5 | 5 | 3 | 4 | 5 | 4.45 | RESEARCH (B) | placeholder; §2 covers ESR basics, no bounds/prefix edge cases |
| Slow Query Monitoring (profiler, slow-query log, planSummary) | 5 | 5 | 3 | 3 | 5 | 4.30 | RESEARCH (A) | placeholder; §5 covers profiler, no log-field semantics |
| Index Selectivity and Covering Queries | 5 | 5 | 3 | 3 | 5 | 4.30 | RESEARCH (B) | placeholder; §14 brief |
| Index Anti-Patterns | 5 | 5 | 3 | 3 | 5 | 4.30 | RESEARCH (B) | placeholder; scattered across refs, no consolidated catalogue |
| Atlas Query Insights and Query Profiler | 4 | 5 | 5 | 3 | 4 | 4.30 | RESEARCH (F) | no coverage; Atlas 2025 surface |
| Query Shapes, Query Hash and $queryStats | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH (A) | $queryStats (7.1+) absent from library; query shape partially in §3.3 |
| Sharded Query Targeting and Scatter-Gather | 4 | 5 | 3 | 4 | 5 | 4.20 | RESEARCH (D) | sharding ref covers key design, not query targeting/explain on mongos |
| Query Settings and Persistent Index Hints (8.0) | 5 | 4 | 4 | 3 | 4 | 4.10 | RESEARCH (A) | setQuerySettings / index-filter deprecation only touched in 8.0 ref |
| Multikey Indexes and Array Query Bounds | 5 | 4 | 3 | 3 | 5 | 4.05 | RESEARCH (B) | placeholder; multikey bounds / $elemMatch tightening missing |
| Index Analysis with $indexStats and Unused-Index Detection | 4 | 5 | 3 | 3 | 5 | 4.05 | RESEARCH (A) | placeholder 'Index Analysis'; §1.8 brief |
| Time-Series Bucket Unpacking and $match Pushdown | 4 | 4 | 5 | 3 | 4 | 4.05 | RESEARCH (E) | new; no coverage |
| Secondary Indexes on Time Series | 4 | 4 | 4 | 3 | 5 | 4.00 | RESEARCH (E) | placeholder; no coverage |
| MongoDB 8.0 Block Processing (time series) | 4 | 4 | 4 | 4 | 4 | 4.00 | RESEARCH (E) | placeholder; frontier |
| Count, Distinct and Sampling Optimization | 4 | 4 | 4 | 2 | 5 | 3.85 | RESEARCH (D) | countDocuments vs estimatedDocumentCount, distinct index use, $sample absent |
| Index Effectiveness Measurement | 4 | 4 | 4 | 3 | 4 | 3.85 | RESEARCH (A) | placeholder under Performance Benchmarking; no coverage |
| $in/$or Index Bounds and Union Plans | 4 | 4 | 4 | 3 | 4 | 3.85 | RESEARCH (D) | SUBPLAN / OR pushdown absent |
| Post-8.0 Query Engine Changes (8.1/8.2 rapid releases) | 4 | 4 | 4 | 4 | 3 | 3.85 | RESEARCH (F) | frontier; 8.0 ref stops at 8.0.x |
| Wildcard and Compound Wildcard Indexes | 4 | 4 | 3 | 3 | 5 | 3.80 | RESEARCH (C) | placeholder; compound wildcard (7.0) absent |
| Cursor and Read-Path Tuning (batchSize, maxTimeMS, read preference/concern) | 4 | 4 | 3 | 3 | 5 | 3.80 | RESEARCH (D) | §1.10 read concern only |
| $lookup Optimization | 5 | 5 | 0 | 3 | 5 | 3.70 | SKIP | HAVE: $lookup node 2026-09-18, 16 sources (Nov 0 hard gate) |
| Pipeline Optimization (stage ordering/pushdown) | 5 | 5 | 0 | 3 | 5 | 3.70 | SKIP | HAVE: fresh node 2026-10-15 (Nov 0 hard gate) |
| metaField Cardinality Anti-Patterns | 4 | 4 | 4 | 2 | 4 | 3.70 | RESEARCH (E) | placeholder; no coverage |
| hint() and Index Forcing | 4 | 4 | 3 | 2 | 5 | 3.65 | RESEARCH (A) | placeholder; §1.9 brief |
| Partial Indexes | 4 | 4 | 3 | 2 | 5 | 3.65 | RESEARCH (B) | placeholder; §4 brief, no planner-eligibility rules |
| Hidden Indexes | 4 | 4 | 3 | 2 | 5 | 3.65 | RESEARCH (C) | placeholder; safe-drop workflow absent |
| Projection Optimization and Covered Query Design | 4 | 4 | 3 | 2 | 5 | 3.65 | RESEARCH (D) | projection pushdown, $slice/$elemMatch projection absent |
| Index Storage, RAM Fit and Write-Path Overhead | 4 | 4 | 3 | 3 | 4 | 3.65 | RESEARCH (C) | new; §14 index memory footprint only |
| Atlas Performance Advisor (index and schema suggestions) | 4 | 4 | 2 | 3 | 5 | 3.60 | RESEARCH (F) | two placeholders; Auto-Index Evaluation fresh node + §5.4 cover part |
| Atlas Search vs $text vs $regex (search offload decision) | 3 | 4 | 3 | 3 | 5 | 3.55 | RESEARCH (F) | Text Indexes placeholder + Atlas Search node; decision rule absent |
| Time-Series Sort and Range Query Patterns | 3 | 4 | 4 | 2 | 4 | 3.45 | RESEARCH (E) | new; no coverage |
| Index Intersection | 4 | 3 | 3 | 2 | 5 | 3.40 | RESEARCH (B) | placeholder; §12 brief |
| Index Build Strategies | 3 | 4 | 3 | 2 | 5 | 3.40 | RESEARCH (C) | placeholder; §13 brief |
| Compass Explain Plan Visualizer | 3 | 3 | 4 | 2 | 5 | 3.35 | RESEARCH (F) | placeholder; no coverage |
| AI/LLM-Assisted MongoDB Query and Index Optimization | 3 | 3 | 4 | 4 | 3 | 3.35 | RESEARCH (F) | frontier; only plugin skills, no sourced reference |
| Sparse Indexes | 4 | 3 | 3 | 1 | 5 | 3.25 | RESEARCH (B) | placeholder; §5 brief |
| Index Build Conflicts, Commit Quorum and In-Flight Builds | 3 | 3 | 4 | 2 | 4 | 3.20 | RESEARCH (C) | three Upgrade Paths placeholders folded; no coverage |
| Working Set Sizing for Time Series | 3 | 3 | 4 | 2 | 4 | 3.20 | RESEARCH (E) | placeholder; no coverage |
| Hashed Indexes | 3 | 3 | 3 | 2 | 5 | 3.15 | SKIP | sharding-oriented; §9 covers; below threshold |
| Text Indexes | 3 | 3 | 3 | 2 | 5 | 3.15 | SKIP | §7 covers; search-offload decision scored separately |
| TTL Indexes | 3 | 3 | 3 | 2 | 5 | 3.15 | SKIP | write-side; §6 covers; below threshold |
| Search Index Mapping | 2 | 3 | 4 | 2 | 5 | 3.10 | SKIP | Atlas Search family owns it |
| HNSW Index Parameters | 2 | 3 | 4 | 3 | 4 | 3.10 | SKIP | Atlas Vector Search family owns it |
| Memory Limits and allowDiskUse | 4 | 4 | 0 | 2 | 5 | 3.05 | SKIP | HAVE: fresh node 2026-10-15 (Nov 0 hard gate) |
| Performance Diagnostic Workflow | 3 | 4 | 1 | 2 | 5 | 3.00 | SKIP | covered by troubleshooting ref 'Diagnostic workflow' |
| Unique Indexes | 3 | 3 | 3 | 1 | 5 | 3.00 | SKIP | §11 covers; below threshold |
| Compass Index Management | 2 | 3 | 4 | 1 | 5 | 2.95 | SKIP | Compass family; below threshold |
| Stored Source Performance Optimization | 2 | 3 | 4 | 2 | 4 | 2.95 | SKIP | Atlas Search family owns it |
| Prefix Compression (indexes) | 2 | 3 | 4 | 2 | 4 | 2.95 | SKIP | WiredTiger family |
| Batch Reads and Aggregation Pushdown (Spark) | 2 | 3 | 4 | 2 | 4 | 2.95 | SKIP | Spark connector family |
| Hardware Saturation Profiling via ts-diag | 2 | 3 | 4 | 2 | 4 | 2.95 | SKIP | ts-diag family |
| explain-executionStats-usedDisk | 4 | 3 | 1 | 1 | 5 | 2.85 | SKIP | placeholder; answered by allowDiskUse node + Explain concept (alias) |
| allowDiskUse-100MB-stage | 4 | 3 | 1 | 1 | 5 | 2.85 | SKIP | placeholder; answered by allowDiskUse node |
| Compass Aggregation Pipeline Builder | 2 | 2 | 4 | 2 | 5 | 2.85 | SKIP | Compass family; not optimization |
| Compass Natural Language Query | 2 | 2 | 4 | 2 | 5 | 2.85 | SKIP | Compass family |
| Single-Field Indexes | 3 | 3 | 2 | 1 | 5 | 2.80 | SKIP | covered in indexes-deep §1; below threshold |
| SQL Query Optimization (cost-based optimizers) | 3 | 3 | 0 | 3 | 5 | 2.70 | SKIP | HAVE: deep-query-optimizer, postgresql-expert |
| Geospatial $lookup Patterns | 2 | 2 | 4 | 2 | 4 | 2.70 | SKIP | geospatial family; low relevance |
| Federated Query on Archive | 2 | 2 | 4 | 2 | 4 | 2.70 | SKIP | Online Archive family |
| MongoDB 8.0 WT Improvements (TCMalloc, ExpressPlan) | 3 | 3 | 1 | 2 | 4 | 2.60 | SKIP | TCMalloc + express path nodes already fresh |
| Learned / ML Query Optimization (general) | 3 | 3 | 0 | 3 | 4 | 2.55 | SKIP | HAVE: da-43 spoke |
| Queryable Backups | 1 | 2 | 4 | 1 | 4 | 2.30 | SKIP | backup family |

### Round 1 (childConcepts of new nodes; 5 new above threshold / 88 cumulative)

| Concept | Rel | Use | Nov | Int | Via | CVS | Decision | Why |
|---|---|---|---|---|---|---|---|---|
| Aggregation Explain and Spill Statistics ($lookup, $group, memory limits) | 4 | 4 | 3 | 3 | 4 | 3.65 | RESEARCH (G) | merges: Aggregation explain and $lookup/spill stats; Aggregation pipeline explain and $lookup visibility; Per-operation memory limit tuning |
| Sharded Explain and Split Pipelines (SHARD_MERGE, per-shard stats, merge shard selection) | 4 | 4 | 3 | 3 | 4 | 3.65 | RESEARCH (G) | merges: Sharded explain; Aggregation split pipelines and merge shard selection |
| $group $first Loose Index Scan (DISTINCT_SCAN for sort-group-first) | 4 | 4 | 3 | 3 | 4 | 3.65 | RESEARCH (G) | merges: Sort-group-$first loose index scan; Last-point queries and DISTINCT_SCAN (E covers the time-series case only) |
| Cost-Based Ranker and Multi-Planning Changes (8.3 and 9.0) | 4 | 3 | 4 | 4 | 3 | 3.60 | RESEARCH (G) | merges: Cost-based ranker (8.3); Cost-based ranker and multi-planning in 8.3; Query knobs (9.0); queryStats output schema in 9.0; Slow in-progress query logging (8.3) |
| Atlas Slow-Query Log and Performance Advisor Automation (managedSlowMs, Admin API listSuggestedIndexes, Atlas CLI) | 3 | 4 | 3 | 2 | 4 | 3.25 | RESEARCH (H) | merges: Atlas-managed slow operation threshold; Atlas CLI/Admin API slow query log download; Admin API listSuggestedIndexes automation; Atlas Performance Advisor MCP server access |
| Time-Series Bucket Catalog Memory and Fragmentation Remediation | 3 | 4 | 2 | 2 | 4 | 3.05 | SKIP | E covers bucket close rules and the 2.5% cap |
| Partial Index Patterns (unique soft-delete, TTL, time series) | 3 | 4 | 2 | 2 | 4 | 3.05 | SKIP | B/E cover partial-index eligibility; patterns only |
| Index Build Resource Limits and Resumable Builds | 3 | 3 | 3 | 2 | 4 | 3.00 | SKIP | merges 3 C children; ops angle; C covers builds/quorum |
| Explain sub-angles already in spoke A (hint/$natural, $querySettings reject filters, index-filter migration, replanReason, SBE vs classic output and cache keys, $planCacheStats/planCacheSize, HMAC transformIdentifiers, currentOp planSummary, hint in aggregate/update, min()/max() hint, Index filters, covered detection, ESR ordering, hidden drop trial, redundant-prefix detection, Atlas advisor/profiler/targeting echoes) | 4 | 3 | 1 | 2 | 5 | 3.00 | SKIP | each is a paragraph in mongodb-explain-plans-and-query-planner; Nov 1 |
| Index-design sub-angles already in spoke B ($elemMatch subdocuments, $exists bounds, $in+SORT_MERGE, AND_SORTED vs AND_HASH, covered on sharded, ERS exception, hint/knobs, hidden removal, prefix compression, plan scoring/EOF bonus, sort direction rules, sparse vs partial, multiKeyPaths, executionStats reading, multikey sort) | 4 | 3 | 1 | 2 | 5 | 3.00 | SKIP | paragraphs in mongodb-compound-index-design; Nov 1 |
| Query-shape sub-angles already in spoke D (COUNT_SCAN, compound vs union for $or, projection vs $project, hashed vs ranged shard key, index-only on sharded, compound keyset, secondary reads/read concern, multikey coverage/sort bounds, bound unionizing, SORT_MERGE variants, shard key isolation, sparse/partial for $exists, total-count strategies) | 4 | 3 | 1 | 2 | 5 | 3.00 | SKIP | paragraphs in mongodb-query-shape-optimization; Nov 1 |
| Time-series sub-angles already in spoke E ($_internalUnpackBucket explain, bounded sort, bucket-level predicate rewriting, granularity params, index hints, last-point DISTINCT_SCAN, partial/TTL on time series, slotBasedPlan explain, SBE eligibility, cache eviction monitoring) | 4 | 3 | 1 | 2 | 5 | 3.00 | SKIP | paragraphs in mongodb-time-series-query-optimization; Nov 1 |
| Persisting index usage metrics across restarts (PMM/monitoring) | 3 | 3 | 3 | 2 | 3 | 2.85 | SKIP | monitoring family |
| Collation-based case-insensitive indexes as a $regex alternative | 3 | 4 | 0 | 2 | 5 | 2.80 | SKIP | HAVE mongodb-collation (Nov 0 gate) |
| Client-side operation timeout (CSOT) | 3 | 4 | 0 | 2 | 5 | 2.80 | SKIP | HAVE node under MongoDB Driver Internals (Nov 0 gate) |
| Validating AI-suggested indexes with explain / MCP read-only model | 3 | 3 | 1 | 3 | 4 | 2.75 | SKIP | F covers |
| Atlas Search regex/wildcard cost, searchAfter pagination, index sync lag, substring matching | 2 | 3 | 3 | 2 | 4 | 2.75 | SKIP | Atlas Search family owns it |
| Index-build sub-angles already in spoke C (attribute pattern/wildcardProjection, rolling builds incl. sharded, safe drop with $indexStats, unused detection, wildcard planner/rejectedPlans, collMod index.hidden, dropIndexes abort) | 3 | 3 | 1 | 2 | 5 | 2.75 | SKIP | paragraphs in mongodb-special-indexes-and-index-builds; Nov 1 |
| Tooling sub-angles already in spoke F (Database Profiler vs Query Profiler, explain verbosity modes, hide-before-drop, Namespace Insights, NL query generation, SBE explain output) | 3 | 3 | 1 | 2 | 5 | 2.75 | SKIP | paragraphs in mongodb-query-optimization-tooling; Nov 1 |
| WiredTiger cache eviction, dirty ratio, random-key (hashed/UUID) insert behavior | 3 | 3 | 1 | 2 | 4 | 2.60 | SKIP | WiredTiger internals family covers |
| Counter-document pattern / $function hardening / tailable cursors and maxAwaitTimeMS | 2 | 2 | 3 | 1 | 4 | 2.35 | SKIP | schema or driver topics |
| Cosmos DB for MongoDB wildcard differences | 1 | 2 | 4 | 1 | 3 | 2.15 | SKIP | different product |
### Round 2 (childConcepts of G and H nodes; 0 new above threshold / 96 cumulative)

| Concept | Rel | Use | Nov | Int | Via | CVS | Decision | Why |
|---|---|---|---|---|---|---|---|---|
| SBE $lookup pushdown and hash join | 4 | 4 | 1 | 2 | 4 | 3.10 | SKIP | covered: $lookup node (2026-09-18), 8.0 ref, G spill stats |
| $group accumulator memory caps / Per-operation memory limit in 9.0 | 4 | 3 | 1 | 2 | 4 | 2.85 | SKIP | G covers 100 MB cap and 9.0 per-operation cap |
| $groupByDistinct internal stage / DISTINCT_SCAN for distinct command / $top-$bottom rewrite | 3 | 3 | 2 | 2 | 3 | 2.65 | SKIP | G loose-index-scan concept; D distinct |
| $mergeCursors stage in explain / SHARDING_FILTER orphan filtering / targeted vs scatter-gather in explain | 4 | 3 | 1 | 2 | 4 | 2.85 | SKIP | G sharded explain + D targeting cover |
| ceSource cardinality estimation (sampling vs heuristics) / serverStatus metrics.query.cbr | 3 | 3 | 2 | 3 | 2 | 2.65 | SKIP | G CBR concept mentions ceSource; thin 8.3 sources |
| queryKnobs and per-command querySettings | 3 | 3 | 2 | 2 | 3 | 2.65 | SKIP | A query settings + G 9.0 knobs |
| Atlas Admin API rate limiting for scheduled polling | 2 | 3 | 3 | 1 | 4 | 2.60 | SKIP | Atlas platform family |
| Drop-index suggestions endpoint / Query Profiler vs slow query log | 3 | 3 | 1 | 1 | 4 | 2.45 | SKIP | H and F cover |
### Round 3 (References sections of the 8 spokes (235 source titles); 0 new above threshold / 103 cumulative)

| Concept | Rel | Use | Nov | Int | Via | CVS | Decision | Why |
|---|---|---|---|---|---|---|---|---|
| Unbounded array growth anti-pattern (schema) | 3 | 4 | 0 | 2 | 5 | 2.80 | SKIP | HAVE mongodb-schema-design (Nov 0 gate) |
| Top-k sort algorithm internals | 3 | 3 | 1 | 2 | 4 | 2.60 | SKIP | D blocking-sort concept covers sort+limit |
| Datadog/Prometheus MongoDB Atlas integration for slow-query metrics | 2 | 3 | 0 | 2 | 5 | 2.30 | SKIP | HAVE monitoring-observability (Nov 0 gate) |
| Learned / LLM-driven index tuning papers (DTA, ADBIS 2023 automatic indexing) | 3 | 3 | 1 | 3 | 3 | 2.60 | SKIP | F AI concept + da-43 cover |
| Secondary reads blocking replication | 2 | 3 | 0 | 2 | 4 | 2.15 | SKIP | HAVE replication ref (Nov 0 gate) |
| WiredTiger cache sizing for working set | 3 | 3 | 0 | 2 | 5 | 2.55 | SKIP | HAVE mongodb-wiredtiger (Nov 0 gate) |
| CVE-2026-4358 (server security advisory) | 1 | 2 | 3 | 1 | 4 | 2.10 | SKIP | security family; not query optimization |

### Blind saturation gate (fresh-context agent, names only; 22 proposals, 0 corroborated ≥ 3.2)
| Concept | Rel | Use | Nov | Int | Via | CVS | Decision | Why |
|---|---|---|---|---|---|---|---|---|
| Index advisor algorithms and what-if index analysis | 3 | 3 | 3 | 3 | 3 | 3.00 | SKIP | da-43 learned query optimization + F AI concept cover |
| Cardinality estimation and selectivity heuristics | 4 | 3 | 2 | 3 | 3 | 3.05 | SKIP | G cost-based ranker + B selectivity cover |
| Plan regression detection and plan baselines (Query Store / SPM analogues) | 3 | 3 | 2 | 3 | 4 | 2.95 | SKIP | A plan cache + query settings cover the MongoDB side |
| Join algorithms and join ordering for SBE $lookup | 3 | 3 | 1 | 2 | 4 | 2.60 | SKIP | $lookup node + G cover |
| Tail-latency (p95/p99) analysis and queueing effects | 3 | 3 | 1 | 2 | 4 | 2.60 | SKIP | performance benchmarking family |
| Read/write concern durability latency | 3 | 3 | 1 | 2 | 5 | 2.75 | SKIP | transactions/replication refs |
| Replication lag, oplog sizing, secondary-read staleness | 3 | 3 | 0 | 2 | 5 | 2.55 | SKIP | HAVE replication (Nov 0 gate) |
| OS and filesystem tuning for mongod (THP, readahead, XFS, NUMA, ulimits) | 2 | 4 | 3 | 2 | 5 | 3.15 | SKIP | ops family (production notes); not query optimization — handoff to mongodb-operations-expert |
| Balancer, chunk migration and StaleConfig retries | 3 | 3 | 0 | 2 | 5 | 2.55 | SKIP | HAVE sharding (Nov 0 gate) |
| Write-path optimization (bulkWrite, ordered vs unordered, upsert patterns) | 2 | 3 | 2 | 2 | 5 | 2.70 | SKIP | developer ref covers bulk ops; write side |
| currentOp and killOp in-flight operation diagnosis | 4 | 3 | 1 | 2 | 5 | 3.00 | SKIP | A (currentOp planSummary) + troubleshooting ref cover |
| Index filters (planCacheSetFilter) and migration to query settings | 4 | 4 | 0 | 2 | 5 | 3.05 | SKIP | covered in A (Nov 0 gate) |
| On-demand materialized views with $merge/$out | 3 | 3 | 0 | 2 | 5 | 2.55 | SKIP | HAVE mongodb-views-materialized-views (Nov 0 gate) |
| Clustered collections as a layout optimization | 3 | 3 | 0 | 2 | 5 | 2.55 | SKIP | HAVE mongodb-clustered-collections (Nov 0 gate) |
| $facet/$unionWith/$graphLookup/$setWindowFields stage tuning | 4 | 3 | 1 | 2 | 4 | 2.85 | SKIP | HAVE stages-deep nodes |
| Atlas Query Targeting alerts (scanned-to-returned ratio) | 4 | 3 | 1 | 2 | 5 | 3.00 | SKIP | A index-effectiveness concept + Atlas alerts node |
| Atlas Real-Time Performance Panel and Namespace Insights | 3 | 3 | 1 | 2 | 5 | 2.75 | SKIP | F Namespace Insights + Atlas metrics node |
| mongostat and mongotop | 3 | 3 | 1 | 1 | 5 | 2.60 | SKIP | query-performance ref 5.5 + database tools ref |
| Driver command monitoring (APM events) and OpenTelemetry tracing | 3 | 3 | 3 | 3 | 4 | 3.15 | SKIP | near-threshold; app-side attribution, owned by driver-internals/observability hubs |
| Atlas tier sizing, IOPS limits, analytics-node isolation (readPreferenceTags) | 3 | 3 | 0 | 2 | 5 | 2.55 | SKIP | HAVE capacity planning + analytics node (Nov 0 gate) |
| Cascades-style CQF/Bonsai optimizer (shelved) history | 3 | 2 | 4 | 3 | 2 | 2.80 | SKIP | historical context; thin sources |
| Queryable Encryption range/substring query performance | 3 | 3 | 3 | 3 | 3 | 3.00 | SKIP | security/encryption family owns QE |

## Researched this run
| Cohort | Concepts | Run / spoke | Hub | Gate |
|---|---|---|---|---|
| A | 8: Explain Plan Interpretation; Query Planning and Plan Cache; Slow Query Monitoring (profiler, slow-query log, planSummary); Query Shapes, Query Hash and $queryStats; Query Settings and Persistent Index Hints (8.0); Index Analysis with $indexStats and Unused-Index Detection; Index Effectiveness Measurement; hint() and Index Forcing | `mongodb-explain-plans-and-query-planner` | mongodb-expert | 13/13 SUPPORTED |
| B | 7: Compound Indexes and ESR Rule; Index Selectivity and Covering Queries; Index Anti-Patterns; Multikey Indexes and Array Query Bounds; Partial Indexes; Index Intersection; Sparse Indexes | `mongodb-compound-index-design` | mongodb-expert | 10/10 |
| C | 5: Wildcard and Compound Wildcard Indexes; Hidden Indexes; Index Storage, RAM Fit and Write-Path Overhead; Index Build Strategies; Index Build Conflicts, Commit Quorum and In-Flight Builds | `mongodb-special-indexes-and-index-builds` | mongodb-expert | 11/11 |
| D | 8: Query Operator Anti-Patterns ($regex, negation, $where, $expr, $exists); Blocking Sort and Index-Backed Sort; Pagination Patterns (skip/limit vs range/keyset); Sharded Query Targeting and Scatter-Gather; Count, Distinct and Sampling Optimization; $in/$or Index Bounds and Union Plans; Cursor and Read-Path Tuning (batchSize, maxTimeMS, read preference/concern); Projection Optimization and Covered Query Design | `mongodb-query-shape-optimization` | mongodb-expert | 10/10 |
| E | 6: Time-Series Bucket Unpacking and $match Pushdown; Secondary Indexes on Time Series; MongoDB 8.0 Block Processing (time series); metaField Cardinality Anti-Patterns; Time-Series Sort and Range Query Patterns; Working Set Sizing for Time Series | `mongodb-time-series-query-optimization` | mongodb-expert | 11/11 |
| F | 6: Atlas Query Insights and Query Profiler; Post-8.0 Query Engine Changes (8.1/8.2 rapid releases); Atlas Performance Advisor (index and schema suggestions); Atlas Search vs $text vs $regex (search offload decision); Compass Explain Plan Visualizer; AI/LLM-Assisted MongoDB Query and Index Optimization | `mongodb-query-optimization-tooling` | atlas-diagnostics-expert | 10/10 |
| G | 4: Aggregation Explain and Spill Statistics ($lookup, $group, memory limits); Sharded Explain and Split Pipelines (SHARD_MERGE, per-shard stats, merge shard selection); $group $first Loose Index Scan (DISTINCT_SCAN for sort-group-first); Cost-Based Ranker and Multi-Planning Changes (8.3 and 9.0) | `mongodb-advanced-explain-and-planner-changes` | mongodb-expert | 10/10 |
| H | 1: Atlas Slow-Query Log and Performance Advisor Automation (managedSlowMs, Admin API listSuggestedIndexes, Atlas CLI) | `mongodb-atlas-slow-query-and-advisor-automation` | atlas-diagnostics-expert | 10/10 |

All 45 concepts recorded at the standard depth (≥3 independent sources each); every blind gate sampled 10–13 claims, all SUPPORTED. Research spend $14.87; gates ≈ $0.24–0.34 each. Tree: 8 new nodes under MongoDB Performance Troubleshooting / MongoDB Indexes Deep Dive / mongodb-time-series / the new explain and tooling nodes; 49 frontier placeholders consumed as aliases; own-concept echoes folded into aliases.

## Skipped and failed (saturation evidence)
Round 0: 26 deliberate skips (below 3.2 or Nov-0 gate) — see the table. Rounds 1–3 and the gate: every candidate scored; 0 failed gaps (no /dr agent errored or fell below the authority floor).

## Optimization results
- Spokes: `/sko --meta --no-sync` deterministic checks — meta-validate.mjs on both hubs 0 High (pre-existing Mediums only: mongodb-mql-quick-reference orphan row, ext-manifest tier-config, hub descriptions over the 300-char hub cap tree-wide); offline pre-lint 1 Low; referents.mjs --repair dry-run 0 rewrites; injection scan 0 hits across 8 spokes; registry rebuilt (31 new entries); routing check 5/7 trigger phrases rank the new spoke first, 2 fixed by description tightening (query-shape, advanced-explain).
- Hubs: full `/sko --no-sync` loops — mongodb-expert 1.8.0→1.9.0 (10→3→0 Medium+, 15 fixed, Pass H 10/10 predicted, exit BLIND-AUDIT-DISSENT on out-of-scope evals placeholders); atlas-diagnostics-expert 1.6.0→1.6.1 (10→2→1, 13 fixed, Pass H 10/10 predicted, exit BUDGET_EXHAUSTED with 8 residual findings). Details: sko-hub-reports.md. Step 9c batch sync: skills repo 02238b948 pushed, hub twin copies refreshed, registry pruned+rebuilt, SKILLS-INDEX regenerated, routing re-verified.
- Prompt artifacts: none created by /dr this run — no /pdo.

## Handoffs
- skill-tree-architect: 68/74 hubs over the 300-char hub description cap (pre-existing, tree-wide); homeless standalone mongodb-* skills (mongodb-atlas-cli, mongodb-atlas-data-federation, mongodb-atlas-triage-workflows, mongodb-ftdc-and-log-tooling, mongodb-drivers, mongodb-mongosh-reference, mongodb-diagnostic-tool-design, mongodb-kb-backed-troubleshooting, mongodb-error-codes-and-troubleshooting, mongodb-ts-diag-and-diagnostic-workflows) fit existing hubs; 18 misplaced spokes none from this run. No MISPLACED concept from this run (tree parent vs hub noted: A/D/F/G sit under MongoDB Performance Troubleshooting whose skillId lives in atlas-diagnostics-expert while A/D/G render into mongodb-expert — recorded, not re-filed).
- mongodb-operations-expert: OS/filesystem tuning for mongod (THP, readahead, XFS, NUMA) surfaced by the gate; ops family, not this one.

## Saturation verdict
Reached by: frontier saturation (SATURATED-FRONTIER). Round 0 productive (40 concepts), round 1 productive (5/88 = 5.7%), round 2 empty (0/96), round 3 empty (0/103, References probe over 235 source titles), blind gate 22 proposals / 0 corroborated. Round-0 map met the 5-per-neighborhood floor.
Concepts processed: 45/all queued via 8 /dr calls; 3/3 rounds.

## Updated concept tree
8 nodes new (see tree-sync-spec.json); parents: MongoDB Performance Troubleshooting (×4 incl. two under the new explain node and the new tooling node), MongoDB Indexes Deep Dive (×2), mongodb-time-series (×1).
Tree sync (Step 9d):
- mdb-context-hub: skipped: no tam_* MCP on this machine
- global-ai-hub (`~/.global-ai-hub/concept-tree/tree.json`): written 0 add / 8 update (nodes written by dr_run finish; merge no-op), 0 queued
- website (`concept-tree/tree.json` → `site/src/data/tree.json`): written 8 add + regenerated, branch `cfe/mql-query-optimization-tree` (PR https://github.com/mithudso/llms-explorer/pull/196)
