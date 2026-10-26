<!-- mongodb-research-inventory:start -->
# MongoDB research queue and coverage inventory

Scores are priority judgments with provenance; source URLs are discovery leads. Unscored concepts await real scoring. The legacy 3.2 cutoff does not filter this view.

Canonical rows: **1387**; gaps/reviews: **926**; unscored gaps: **10**; held: **135**.

## Source-sharing cohorts

Every gap and review candidate appears below, including held, low-scored and unscored concepts.

| cohort | source family / affinity | members · CVS | shared discovery sources |
|---|---|---|---|
| mongodb-cohort-a0a420b316d1 | mongodb-general / parent:mongodb performance regression detection and testing methodology | MongoDB Major-Version Upgrade Regression Detection (CVS 4.475); Canary and Shadow-Traffic Comparison (CVS 3.725); Change Point Detection (CVS 3.350); CI Performance Regression Gating (CVS 3.325) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-321ef5e25160 | cost-billing / cluster-sizing | Connection pool sizing and connection-storm control for Atlas (serverless and Lambda clients) (CVS 4.450); WiredTiger cache sizing and working-set fit (CVS 4.325); Oplog Sizing (CVS 4.275); Working Set Sizing (CVS 4.250) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-0e7a6f84ee61 | diagnostics-operations / parent:mongodb backup and restore | Continuous Cloud Backup (PITR) (CVS 4.450); Backup Verification and Tabletop Exercises (CVS 4.175); Atlas Cloud Backup (snapshots) (CVS 4.150); Cross-Region Snapshot Copy (CVS 3.850) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-1d6ef7b4932c | sharding / parent:independent shard scaling and per-shard tiering | Hot shard diagnosis and shard key remediation (CVS 4.450); Balancer data-size policy and zone-aware migration (CVS 4.225); Atlas compute auto-scaling for sharded clusters (CVS 4.075); Per-shard compute auto-scaling rules and limits on Atlas (CVS 3.925) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-18121faaf93a | sharding / parent:mongodb multi-tenancy | Shard Key Design for Multi-Tenancy (CVS 4.450) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-5bc61fcfe3ec | aggregation / parent:database profiler vs query profiler | $queryStats aggregation stage (CVS 4.450) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-6f6a12e41dfc | mongodb-general / parent:mongodb connection string uri | CSOT Client-Side Operations Timeout (CVS 4.450); Read Preference (CVS 4.125); Standard URI Format (CVS 3.375) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-a04dd23fc577 | mongodb-general / parent:mongodb spark connector and databricks integration | Streaming Write Semantics (CVS 4.450); Partitioner Strategies (CVS 4.325); Batch Writes and Idempotency (CVS 4.225); Connector Error Patterns (CVS 3.600) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-f1ebe93a2c8b | mongodb-general / parent:mongodb migration patterns | Relational Migrator (CVS 4.450); Cutover Strategies (CVS 4.375); Atlas Live Migration (CVS 4.250); Common Migration Failures (CVS 3.675) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-74cd39f19180 | sharding / parent:covered queries on sharded collections | Reading sharded explain output (shards, SINGLE_SHARD, SHARD_MERGE) (CVS 4.425); Hashed and compound hashed shard keys and index coverage (CVS 4.350); Orphaned documents and range deletion (CVS 4.125); SHARDING_FILTER stage and chunkSkips (CVS 4.075) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-beeb86966a6e | api-tooling / parent:mongodb driver internals | Sessions (CVS 4.425) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-3aa797450c89 | search-vector / parent:mongodb atlas search | Relevance Scoring (CVS 4.375); Custom Analyzers (CVS 4.050); Autocomplete (CVS 3.775) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-2e478e8e7c3f | sharding / parent:shard key design and resharding as cost levers | analyzeShardKey and query sampling (CVS 4.375); analyzeShardKey query sampling and candidate-key scoring (CVS 4.375); Two-phase write protocol and writes without the shard key (CVS 4.250); Atlas independent shard scaling and auto-scaling (CVS 4.100) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-f8dad38f861e | mongodb-general / parent:mongodb upgrade paths | Binary downgrade window (CVS 4.375); FCV unpinned too early (CVS 4.300); Arbiter handling and PSA topology (CVS 4.275); Change-stream resumability (CVS 4.075) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-1d798a0d85d1 | mongodb-general / parent:mongodb capacity planning | Connection Capacity (CVS 4.375); Read vs Write Distribution (CVS 3.825); Capacity Testing (CVS 3.250); Growth Signals (CVS 3.250) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-0a5c86f5c884 | storage-wiredtiger / parent:wiredtiger storage engine internals | Long-Running Transactions and Cache Pressure (CVS 4.375); WT_CACHE_FULL / Cache Pressure Troubleshooting (CVS 4.300); Journal (Write-Ahead Log) (CVS 3.825); MVCC and Snapshot Isolation (CVS 3.675) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-a17745affdcc | mongodb-general / parent:read offload via caching and precomputed views ($merge/$out, computed pattern) | Delete propagation and reconciliation for $merge-maintained views (CVS 4.375); Idempotent incremental refresh design for $merge (high-water marks, delete handling) (CVS 4.350); Atlas Stream Processing streaming materialized views (CVS 4.025); Cache stampede protection: leases, request coalescing, TTL jitter (CVS 3.900) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-c53f316f2ab7 | query-index-planner / index-design | Index build commit quorum and hung builds (CVS 4.350); Unique and TTL index side effects on removal (CVS 4.275); Index filters (planCacheSetFilter) deprecation and migration to query settings (CVS 4.275); Query settings: index hints and queryFramework (persistent query settings) (CVS 4.250) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-494e1aa39f55 | query-index-planner / query-shape | $queryStats and $currentOp as alternatives to the profiler (CVS 4.350); Atlas Query Profiler and slow-ops logs for shape discovery (CVS 4.250); Query shape and queryShapeHash stability (CVS 4.150); Query shapes and queryShapeHash stability (CVS 4.150) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-22646bcd15df | mongodb-general / parent:mongodb ops manager and cloud manager | Goal-State Automation Configuration (CVS 4.350); Ops Manager High Availability (CVS 4.250); Blockstore and Snapshot Stores (CVS 4.200); Cross-DC App DB Placement (CVS 4.175) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-e128bd27e4b1 | time-series / parent:mongodb-time-series | Time Series Sharding Patterns (CVS 4.350); Time Series Collection Creation (timeField, metaField, granularity) (CVS 4.075); TTL and Automatic Bucket Deletion (CVS 4.050); Granularity Anti-Patterns (CVS 3.675) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-b00c6e9c0178 | mongodb-general / parent:kafka-source-connector | change-stream-resume-token (CVS 4.350); startup-mode-copy-existing (CVS 4.225); heartbeat-configuration (CVS 3.850) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-f173c69ee97a | mongodb-general / parent:mongodb atlas infrastructure as code | mongodbatlas_advanced_cluster Resource (CVS 4.325); Pulumi mongodbatlas Provider (CVS 4.000); moved Block Migration Pattern (CVS 3.625); CloudFormation Third Party Activation (CVS 3.625) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-7030217d35d1 | mongodb-general / parent:mongodb atlas multi-cloud | Multi-Cloud Global Clusters (CVS 4.325); Multi-Cloud Failure Modes (CVS 3.825); Atlas on Azure (CVS 3.750); Atlas on GCP (CVS 3.750) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-ce1440cf3126 | cost-billing / parent:mongodb upgrade paths | FCV pinning and downgrade preservation window (CVS 4.300) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-6b0ef514c7df | sharding / parent:mongosync | verification-modes (CVS 4.300); namespace-filtering (CVS 4.000); mongosync-state-machine (CVS 3.875); atlas-live-migration-comparison (CVS 3.825) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-eac239cf87d4 | search-vector / vector-embedding | Embedding Pipelines (CVS 4.300); Vector index memory sizing and quantization trade-offs on Search Nodes (CVS 4.225); Vector Quantization (CVS 4.225); Atlas Vector Search RAM sizing and automatic quantization (CVS 4.150) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-71277350690d | search-vector / search-index | Hybrid Search (CVS 4.300); Atlas Search Analyzers and Tokenizers (CVS 4.275); Atlas Search index behaviour with $out versus $merge targets (CVS 4.175); Atlas Search index lifecycle on $out and $merge targets (CVS 4.175) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-6047f9cce83c | storage-wiredtiger / parent:oplog sizing under storage auto-scaling | Atlas storage auto-scaling triggers, cooldowns and write blocking (CVS 4.300); replSetResizeOplog and oplog compaction on self-managed replica sets (CVS 3.775); EBS volume modification limits and Atlas disk resize mechanics (CVS 3.450); Atlas Infinite oplog and storage-layer replication (CVS 3.300) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-9eb6db80c07d | mongodb-general / parent:mongodb multi-tenancy | Row-Level Security Patterns (CVS 4.300); Tenant Lifecycle Operations (CVS 4.275); Tenant Isolation Models (CVS 4.250); Atlas Projects as Hard Isolation (CVS 4.200) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-ebfddb6584b7 | cost-billing / billing-pricing | Disk IOPS Burst Credit Depletion Playbook (CVS 4.300); Balancer tuning and chunk migration cost (CVS 4.150); WiredTiger checkpoints and dirty-page write cost (CVS 4.050); Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams (CVS 4.050) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-99501ef9834d | storage-wiredtiger / parent:atlas storage auto-scaling and disk reclaim via compact | Oplog minimum retention window and storage auto-scaling (CVS 4.275); Atlas disk write-blocking thresholds and recovery (CVS 4.225); WiredTiger block reuse, file fragmentation and freeStorageSize (CVS 3.950); Archive and TTL data lifecycle followed by compaction (CVS 3.950) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-9343057e721a | replication-transactions / replication | Read concern available, secondary reads and orphaned documents (CVS 4.275); Oplog window overflow (CVS 4.250); majority commit point mechanics (CVS 4.250); Oplog capacity for initial sync, live migration and bulk loads (CVS 4.250) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-f09da64a2f6e | mongodb-general / parent:mongodb atlas triggers and functions | Trigger Error Handling and Suspension (CVS 4.275); Database Triggers (CVS 3.750); Scheduled Triggers (CVS 3.650); Atlas Functions JavaScript Runtime (CVS 3.600) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-99762008d157 | storage-wiredtiger / parent:sort_merge and $in sort expansion | Blocking sort memory limit and allowDiskUse (CVS 4.250) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-0243ade22f9d | sharding / parent:shard key selection for query isolation | analyzeShardKey workload sampling (CVS 4.250); Compound shard-key prefix targeting (CVS 4.175); Hashed versus ranged shard-key tradeoffs (CVS 3.950) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-b0e4f880a1a3 | identity-governance / audit-compliance | Org and Project Governance (CVS 4.250); Atlas Database Auditing (CVS 3.650); Atlas Audit Logging (CVS 3.550); Atlas Audit Logs Cloud Logging (CVS 3.275) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-e28d711cee18 | query-index-planner / index-design | setQuerySettings index hints and queryFramework (CVS 4.250); Index build commit quorum (commitQuorum and setIndexCommitQuorum) (CVS 4.175); Leading-prefix redundant index detection (CVS 4.175); Multikey indexes and index-provided sort order (CVS 4.175) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-da6be74d8a76 | cost-billing / cluster-sizing | Snapshot reads (atClusterTime) and history window sizing on secondaries (CVS 4.250); Oplog sizing and embedded-verifier memory for migrations (CVS 4.175); Atlas Tier Selection (CVS 4.150); WiredTiger cache sizing and memory fragmentation (CVS 4.075) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-a4d0714f2d41 | sharding / parent:long-running secondary reads in sharded clusters | Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds (CVS 4.250); Resume-from-last-key pattern for killed cursors (CVS 4.250); terminateSecondaryReadsOnOrphanCleanup and QueryPlanKilled 175 (CVS 4.125); Chunk migration commit, range deleter and orphan cleanup internals (CVS 4.050) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-6d975ea7dbf2 | time-series / parent:bucket fragmentation remediation (re-insert/merge) | Time series backfill ordering and batching (CVS 4.250); $out-based time series rewrite and cutover (CVS 3.900); Time series bucket reopening (archived and query-based) (CVS 3.875); Time series compact and disk space reclaim (CVS 3.800) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-705afd785fe1 | replication-transactions / replication | MongoDB Replication (CVS 4.250); Per-node and per-shard $indexStats aggregation across replica sets and shards (CVS 4.175); snapshot read concern (CVS 4.125); read concern in sharding (CVS 4.125) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-eec7f143c4d7 | api-tooling / drivers | Connection Pooling Strategies (CVS 4.225); Azure Functions Atlas Connection Pooling (CVS 4.025); Driver mismatch failure mode (CVS 3.975); Java driver 4.10 and 5.x retry semantics (CVS 3.700) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-642e05e32e3c | mongodb-general / parent:cdc-patterns | exactly-once-semantics (CVS 4.225); outbox-pattern (CVS 4.200); debezium-handlers (CVS 3.725) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-8cacc610d606 | mongodb-general / parent:mongodb atlas stream processing | Watermarks and Late-Event Tolerance (CVS 4.225); Dead Letter Queue (DLQ) (CVS 4.050); Connection Registry (CVS 3.750); Stream Processing Instance (SPI) (CVS 3.650) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-acd9dfcd8eeb | mongodb-general / parent:kafka-sink-connector | write-model-strategies (CVS 4.225); DLQ-error-handling (CVS 4.150); bulk-write-ordering (CVS 4.050) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-dc0d0485fbfe | sharding / parent:unused index detection with $indexstats | Unique, TTL and shard-key indexes that read as unused (CVS 4.200) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-92f18235288a | mongodb-general / parent:total count strategies for paginated uis | hasNextPage without computing total pages (CVS 4.200); Maintained or cached count counters (CVS 3.775) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-715247b3e8b5 | archive-federation / parent:partition fields | Online Archive Data Access and Data Seek Query Cost Model (CVS 4.200) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-4902740ddccc | query-index-planner / index-design | Multikey indexes and sort provision (multikeyPaths) (CVS 4.175); Compound-index prefix and sort-direction compatibility (CVS 4.150); $indexStats usage statistics and their reset conditions (CVS 4.075); Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes) (CVS 4.075) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-cf9a0f8ed75e | replication-transactions / transactions | TemporarilyUnavailable and TransactionTooLargeForCache errors (CVS 4.175); Retryable Reads (CVS 4.150); MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later) (CVS 3.625); Read concern and causal consistency with secondary reads (CVS 3.600) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-fdacc8310b4f | diagnostics-operations / parent:distributed sharded transactions | Coordinator failure recovery (CVS 4.175) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-e71ad6d99f1d | storage-wiredtiger / parent:index build resource limits (maxnumactiveuserindexbuilds, disk space) | WiredTiger cache pressure and write tickets during index builds (CVS 4.175); Commit quorum and the vote-to-commit point of no return (CVS 4.150); DiskSpaceMonitor and low-disk index build abort (7.1+) (CVS 3.725) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-49d659b13000 | storage-wiredtiger / parent:wiredtiger cache eviction and dirty ratio | WiredTiger history store and majority commit point cache pressure (CVS 4.175); WiredTiger checkpoints and checkpoint duration (CVS 4.150); Application-thread eviction and cache stalls (CVS 3.975); eviction_updates_trigger and the updates ratio (CVS 3.075) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-31cfc547f721 | search-vector / search-index | mongot replication lag, oplog window and index rebuild cost (CVS 4.175); Co-located vs dedicated mongot decision thresholds and failure modes (CVS 4.125); Elasticsearch-to-Atlas Search migration and dual-run cost (CVS 4.125); Atlas Search index rebuild after migration (CVS 4.075) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-0346bef27420 | query-index-planner / planner-explain | Reading indexed `$or` plans with explain (CVS 4.150); Multiplanning storms after a plan cache flush (CVS 4.100); Plan cache key and $in length (classic vs SBE) (CVS 4.100); Plan cache flushes on index DDL (CVS 3.950) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-69e987c81008 | diagnostics-operations / parent:mongodb kb articles | Connectivity Troubleshooting (CVS 4.150) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-5682e98c0453 | schema-modeling / parent:mongodb multi-tenancy | Schema Design for Multi-Tenancy (CVS 4.150) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-70ad329d8e95 | query-index-planner / query-shape | Keyset (resume) pagination for restartable cursors (CVS 4.150); Inline user-facing querySettings (9.0) (CVS 4.125); Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis) (CVS 4.025); mongod diagnostic log slow-query format and slowOpSampleRate (CVS 4.000) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-236f7c7ed9cf | api-tooling / automation | Terraform effective fields and auto-scaling drift (CVS 4.150); Atlas Admin API Date Versioned Media Types (CVS 4.075); Terraform Provider v2 Migration (CVS 4.075); PSC Terraform GCP (CVS 3.950) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-641b3decfe43 | schema-modeling / parent:mongodb expert knowledge | mongodb-schema-design (CVS 4.150) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-f5625c57d0b7 | networking / parent:mongodb driver internals | DNS SRV Discovery (CVS 4.125); TLS and OCSP (CVS 3.850) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-27b1229cf1bf | sharding / parent:random-key (hashed/uuid) index insert behavior | Hashed shard-key write distribution and local index locality (CVS 4.125) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-c5470a8d6ad1 | sharding / parent:rolling index builds | Detecting inconsistent indexes across shards (CVS 4.100) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-6505e3f3ea07 | search-vector / vector-embedding | Embedding generation and reranking token spend in retrieval TCO (CVS 4.100); Atlas Vector Search numCandidates tuning and recall measurement against ENN (CVS 4.025); Lexical Prefilters for Vector Search (CVS 3.925); Atlas Automated Embedding economics (Voyage tokens vs external embedding service) (CVS 3.875) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-86c227f5e718 | sharding / parent:shard key design and resharding as cost levers | Atlas independent shard scaling and per-shard auto-scaling (CVS 4.100); Balancer, chunk migration and jumbo chunk remediation (CVS 4.075); Hashed, ranged and compound hashed shard keys (CVS 4.025); Zone sharding and region-aware shard keys (CVS 4.025) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-7b84bed0b7eb | storage-wiredtiger / parent:cluster tier limits and feature gates as cost drivers (connections, iops caps, minimum tiers) | Gen1 versus Gen2 IOPS provisioning and instance-level EBS/VM IOPS caps (CVS 4.100) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-cde8f5008414 | aggregation / parent:mongodb aggregation pipeline | Pipeline Optimization (CVS 4.100) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-15b633636009 | replication-transactions / replication | Rolling replica-set upgrade (CVS 4.075); Orphaned documents and read concern available versus local (CVS 4.075); Safe index removal: locks, rollback and regression checks (CVS 4.075); Read and Write Concerns (CVS 4.050) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-03f16747a38f | identity-governance / authorization-policy | Atlas Custom Database Roles (CVS 4.075); Service Account OAuth 2.0 Authentication (CVS 4.050); Atlas IdP Group to Role Mapping (CVS 3.875); RBAC and Connection Security (CVS 3.875) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-74076c97a7f3 | query-index-planner / parent:resumable index builds | Commit quorum and votingMembers (CVS 4.075) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-dc748bec19fd | mongodb-general / parent:mongodb atlas on azure | Atlas Key Rotation AKV (CVS 4.075); Azure Container Apps Atlas (CVS 3.800); Azure Event Hub Atlas Stream Processing (CVS 3.750); Azure App Service Atlas (CVS 3.725) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-b05ce0d7baab | sharding / parent:covered queries on sharded collections | readConcern available on sharded clusters (CVS 4.075); Hashed shard keys and index support (CVS 3.925); Covered distinct and $group on sharded collections (CVS 3.850); COUNT_SCAN and sharded count accuracy (CVS 3.800) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-7ee309139bcc | networking / parent:mongodb atlas terraform provider | Atlas Networking IaC (CVS 4.075) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-bae29937ea6d | mongodb-general / parent:cesource cardinality estimation (sampling vs heuristics) | Sampling CE accuracy under sparse sample matches (CVS 4.075); MongoDB CBR CE source metadata (CVS 3.200) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-b74fe6f94c37 | identity-governance / identity-federation | Workload Identity Federation Atlas (CVS 4.075); Entra ID group overage in Atlas (CVS 3.850); Entra ID Workload Identity Federation (CVS 3.775); GCP Workload Identity Federation OIDC (CVS 3.775) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-8db54400cdbf | diagnostics-operations / parent:mongodb monitoring and observability | Atlas Alerts (CVS 4.050); Atlas Metrics and Dashboards (CVS 4.000); Connection Metrics (CVS 3.950); Prometheus Integration (CVS 3.925) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-2d92638e9112 | identity-governance / parent:mongodb connection string uri | Authentication Mechanisms (CVS 4.050) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-6f4c87e440df | query-index-planner / index-design | ESR guideline and $in placement in compound indexes (CVS 4.050); dropIndexes locking and in-flight query behavior (CVS 4.000); Hidden indexes as a safe drop trial (CVS 4.000); Redundant (prefix) index detection for compound indexes (CVS 3.975) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-431c1cbaf986 | search-vector / search-index | Atlas Search Nodes cost floor and co-located versus dedicated search (CVS 4.050); Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes (CVS 4.000); Faceted Search (CVS 3.850); Dedicated Search Nodes two-node cost floor versus coupled mongot (CVS 3.825) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-fc7e308a4a68 | networking / parent:mongodb atlas multi-cloud | Azure Private Link for Atlas (CVS 4.050); GCP Private Service Connect for Atlas (CVS 4.050) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-1ea1a94ccad7 | api-tooling / app-services | Cluster-to-Cluster Sync Phases (CVS 4.050); initial-sync-and-cdc (CVS 4.000); reverse-sync-cutover (CVS 4.000); Rolling resync (initial sync) as a space-reclaim technique on Atlas (CVS 3.850) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-e79d2e686285 | networking / parent:migration and cutover cost (live migration, mongosync, dual-running, egress) | Application-level dual-write migration pattern (CVS 4.050); Cross-cloud application-tier placement and Atlas internet egress (CVS 3.975); EU Data Act switching charges and in-parallel egress (CVS 3.025); Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure) (CVS 2.975) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-50c2ce240545 | mongodb-general / parent:mongodb ops manager and cloud manager | Local Mode and Air-Gap Deployments (CVS 4.050); Application Database (App DB) (CVS 3.950); Automation Agent (CVS 3.950); Migration Host Provisioning (CVS 3.775) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-c84c26fc913e | mongodb-general / parent:mongodb bi connector and sql access | BI Connector EOL Migration (CVS 4.050); SQL-to-MQL Translation (CVS 3.925); HTTP Data Access Replacements (CVS 3.225) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-91172fd79593 | sharding / parent:shard key design and resharding as cost levers | Reducing shard count and unsharding collections on Atlas (CVS 4.025); moveCollection and unshardCollection (CVS 3.975); Zone sharding and Global Cluster shard keys (CVS 3.950); Reshard to the same key for adding and removing shards (CVS 3.900) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-1aa648d70e12 | cost-billing / cluster-sizing | Atlas Auth Tier Feature Matrix M0 Flex M10 (CVS 4.000); Destination temporary scaling and post-cutover right-sizing (CVS 4.000); oplog-window-sizing (CVS 4.000); MongoDB Node.js driver pool sizing under Lambda concurrency (CVS 3.975) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-4f8b19686130 | sharding / parent:long-running secondary reads in sharded clusters | Balancer windows and per-collection balancing control (CVS 4.000); Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete) (CVS 3.925); Atlas analytics nodes and read preference tags (CVS 3.825); Workload isolation with tagged secondaries and Atlas analytics nodes (CVS 3.825) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-7c7aab86e51d | storage-wiredtiger / parent:mongodb upgrade paths | Disk pre-warming SOP (Cookie 7.0→8.0 lesson) (CVS 4.000); WiredTiger cache warm-up (CVS 3.850) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-9506d4f6a2ef | storage-wiredtiger / parent:independent shard scaling and per-shard tiering | Per-shard disk IOPS and storage constraints (CVS 4.000); Per-shard IOPS and Gen2 storage on Atlas (CVS 3.925) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-8450487cdc7b | networking / parent:mongodb connection string uri | SRV DNS Seedlist Format (CVS 3.975); TLS/SSL Configuration (CVS 3.975) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-f959bb6a503b | cost-billing / billing-pricing | Flex versus Dedicated boundary: ops-per-second pricing and missing features (CVS 3.975); Write amplification and cache cost of unused indexes (CVS 3.950); Relational-to-MongoDB migration cost (Relational Migrator) (CVS 3.850); Hybrid search ($rankFusion) vs two-system fusion TCO (CVS 3.850) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-252dc4668191 | archive-federation / parent:mongodb atlas online archive | Partition Fields (CVS 3.975); Archive Anti-Patterns (CVS 3.000) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-b62cb9f27cd5 | cost-billing / cluster-sizing | Source Oplog Window Sizing for Migration (CVS 3.975); Zone sharding for hardware-tiered shards (CVS 3.950); Zone sharding for tiered hardware (hot, warm, cold) (CVS 3.950); Reverse sync and rollback-window economics (CVS 3.925) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-1fdc93c7569e | replication-transactions / replication | mongosync reversible sync and the rollback window (CVS 3.975); majority read concern (CVS 3.950); Replica set oplog window and initial sync (CVS 3.950); Atlas Live Migration pull versus push versus standalone mongosync selection (CVS 3.950) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-687aed0d21fd | mongodb-general / parent:mongodb atlas on gcp | PSC Port-Mapped Architecture (CVS 3.975); GCP Forwarding Rule Quota (CVS 3.750); Cloud Functions Gen2 Atlas (CVS 3.725); Cloud NAT for Atlas (CVS 3.725) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-1482bd9b61d6 | diagnostics-operations / parent:mongodb ops manager and cloud manager | MongoDB Agent (Automation, Monitoring, Backup) (CVS 3.950); Continuous Backup with PITR (CVS 3.875); Backup Daemon HA and Failure Domains (CVS 3.775); OpenTelemetry MongoDB Receiver (CVS 3.725) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-205df5e830d6 | identity-governance / parent:mongodb atlas iam and rbac | Atlas AWS IAM Database Auth (CVS 3.950); Atlas X.509 Certificate Auth (CVS 3.750); Atlas SCRAM-SHA-256 (CVS 3.675); Atlas Database Users (CVS 3.575) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-f912d5a4c6c7 | identity-governance / encryption-keys | Azure Key Vault Atlas BYOK (CVS 3.950); Google Cloud KMS BYOK (CVS 3.950); KMS Failsafe Behavior Atlas (CVS 3.825); KMS Unavailability Failsafe (CVS 3.825) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-2b89fbc3d8fa | mongodb-general / parent:mongodb security architecture | Secrets Management (CVS 3.950); Self-Managed Security Config (CVS 3.800); Atlas Security Posture Checklist (CVS 3.650) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-a65c6320d64b | networking / parent:global ai hub research corpus | VPC Peering GCP Atlas (CVS 3.950); VPC Atlas Security (CVS 3.475) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-6e1e9ef33885 | query-index-planner / planner-explain | Multi-planner trial period and candidate plan ranking (CVS 3.950); SBE vs classic engine defaults (CVS 3.900); Plan cache entry lifecycle: Inactive and Active entries and works growth (CVS 3.875); SBE plan cache keys and parameterized explode-for-sort plans (CVS 3.600) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-0dfda3ebd6a5 | sharding / parent:mongodb upgrade paths | Config server / shards / mongos upgrade sequence (CVS 3.925); mongos version skew failure (CVS 3.925); mongos version skew rules (CVS 3.825); Config shard caveat (8.0+) (CVS 2.575) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-b9e8cc9dff41 | storage-wiredtiger / parent:mongodb connection string uri | Wire Protocol Compression (CVS 3.925) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-5cc6a5873cd4 | query-index-planner / index-design | Index filters and query settings versus hidden indexes (CVS 3.925); Side-writes table and hybrid index builds (CVS 3.775); Exporting $indexStats metrics with mongodb_exporter and PMM (CVS 3.775); Persisting index usage metrics with PMM and mongodb_exporter (CVS 3.775) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-41d59b577242 | mongodb-general / parent:mongodb upgrade paths | PSA topology stepdown failure (CVS 3.925); Cold-cache latency regression (CVS 3.800); Version upgrade paths (4.4 → 5.0 → 6.0 → 7.0 → 8.0) (CVS 3.700); Pre-upgrade safety checks (CVS 3.600) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-1e99b9bf1966 | mongodb-general / parent:partition fields | Partition Field Immutability and Merge-Delete-Recreate Migration (CVS 3.925); Partition Field Leftmost-Prefix Ordering (CVS 3.900); Partition Field Count Limits (DATE vs CUSTOM) (CVS 3.150); Partition Field Type Enum Docs-vs-Spec Disagreement (CVS 2.850) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-3269334e5d34 | diagnostics-operations / parent:wiredtiger cache eviction and dirty ratio | MongoDB cache-pressure monitor and ticket admission (CVS 3.925) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-38fae6930416 | sharding / parent:mongodb ops manager and cloud manager | Live Migration to Atlas via mongosync (CVS 3.900) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-1e0eea1b3fda | cost-billing / cluster-sizing | Dedicated Search Node storage and compute sizing (CVS 3.875); Standalone mongosync hosting and sizing (CVS 3.875); Oplog window sizing (CVS 3.850); Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized (CVS 3.825) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-e515b403d48b | query-index-planner / query-shape | serverStatus metrics.query.planCache counters (CVS 3.875); Atlas Query Insights: Query Shape Insights and Namespace Insights (CVS 3.850); BigQuery Atlas Dataflow CDC (CVS 3.750); Rooted $or subplanning and SORT_MERGE (CVS 3.725) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-437048a92799 | replication-transactions / replication | mongosync and live-migration oplog capacity planning (CVS 3.875); Count consistency under concurrent writes (CVS 3.850); Replication Oplog Window alerts and Oplog GB/Hour monitoring (CVS 3.800); Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom) (CVS 3.800) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-4c4a60fe08de | diagnostics-operations / parent:mongodb expert knowledge | MongoDB Monitoring and Observability (CVS 3.875) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-3bde70611ed4 | search-vector / vector-embedding | numCandidates tuning for quantized HNSW indexes (CVS 3.850); Search Node sizing and disk-to-RAM ratios for quantized vector indexes (CVS 3.800); Search Node sizing for quantized vector indexes (RAM, disk, vCPU) (CVS 3.800); Hybrid search ($rankFusion) vs separate search plus vector stack (CVS 3.725) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-0decd84b4936 | query-index-planner / parent:rolling index builds | Hidden and priority-0 members during maintenance (CVS 3.850); Automated rolling builds in Atlas, Cloud Manager and Ops Manager (CVS 3.500) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-ded7cec0af2e | time-series / parent:bucket-level predicate rewriting for measurement operators | Loose versus tight bucket predicates (CVS 3.850); Time-field bucket predicates (CVS 3.750) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-d9cc5fb1cc98 | mongodb-general / parent:read offload via caching and precomputed views ($merge/$out, computed pattern) | Approximation pattern for write-heavy computed counters (CVS 3.850); Cache-aside vs write-through and cache stampede prevention (CVS 3.700); Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads) (CVS 3.475); Refresh scheduling with Atlas Scheduled Triggers (CVS 2.925) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-d5cef667ffc4 | diagnostics-operations / parent:mongodb atlas terraform provider | Atlas Backup IaC (CVS 3.850) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-2daa30f3ff56 | sharding / parent:independent shard scaling and per-shard tiering | moveCollection and collection isolation on dedicated shards (CVS 3.850) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-7a36032fa829 | query-index-planner / parent:random-key (hashed/uuid) index insert behavior | UUIDv4 versus UUIDv7 key locality (CVS 3.850) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-f7898c0e7b37 | mongodb-general / parent:client side operations timeout (csot) | maxTimeMS (Server-side Operation Timeout) (CVS 3.850); Quantile Estimation (DDSketch) (CVS 2.700) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-4451fc8be02a | api-tooling / shell-tools | Compass Schema Analysis (CVS 3.825); Compass Data Import Export (CVS 3.750); Compass Connection Management (CVS 3.650); Compass Real-Time Performance Monitoring (CVS 3.525) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-1d77b14f4cb1 | api-tooling / automation | Terraform Drift Detection (CVS 3.825); Atlas Admin API v2 REST (CVS 3.750); Terraform Import generate-config-out (CVS 3.725); Atlas Terraform mongodbatlas_resource_policy (CVS 3.650) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-2ccf282e3940 | mongodb-general / parent:operation rejection filters | defaultMaxTimeMS cluster-level read timeout (CVS 3.825) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-2350070cfddf | cost-billing / parent:cluster tier limits and feature gates as cost drivers (connections, iops caps, minimum tiers) | Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates) (CVS 3.825) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-292dd656b5d2 | identity-governance / authorization-policy | Backup Compliance Policy One-Way (CVS 3.825); MongoDB AI Policy Scanning (CVS 3.800); Atlas RBAC IaC (CVS 3.775); Atlas Project Roles (15 Purpose-Built) (CVS 3.575) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-3218ab1d6cd5 | cost-billing / parent:mongodb atlas flex and serverless tiers | Atlas Flex Unsupported Features (CVS 3.800); Atlas Flex Technical Limits (CVS 3.600); Serverless Cold Start Behavior (CVS 2.850) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-1ffb989b662b | search-vector / search-index | Atlas Search nodes in sharded clusters (CVS 3.800); Atlas Search node scaling per shard (CVS 3.750); Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections (CVS 3.625); Self-managed mongot on Community Edition: hardware and labour TCO (CVS 3.625) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-01e1f13f468a | aggregation / parent:mongodb spark connector and databricks integration | Batch Reads and Aggregation Pushdown (CVS 3.800) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-0d1fc8db4911 | schema-modeling / parent:mongodb spark connector and databricks integration | Schema Inference and Type Promotion (CVS 3.800) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-df647968356b | cost-billing / billing-pricing | Embedded verifier and post-migration data verification cost (CVS 3.800); Atlas invoice tag coverage and cost export reconciliation (CVS 3.775); Config server placement and cost (dedicated vs embedded) (CVS 3.775); Index rebuild cost after a wrong drop (CVS 3.725) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-91fafd3a2f3c | sharding / parent:mongosync | loadlevel-tuning (CVS 3.800) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-1c65b14aa5e2 | identity-governance / encryption-keys | KMS Key Rotation Atlas (CVS 3.800); Encryption In Transit (CVS 3.775); Atlas Encryption IaC (CVS 3.575); BYOK Key Management (CVS 3.550) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-596d3e14c0db | replication-transactions / change-streams | Structured Streaming with Change Streams (CVS 3.800); Atlas Triggers Workarounds (no change streams) (CVS 2.575) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-30599b0ff34f | networking / parent:mongodb stress, soak, and chaos-resilience testing | Chaos-style resilience testing under load (kill primary during peak writes, network partition, disk-full/IO-stall injection) (CVS 3.800) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-3a39b842dcf7 | time-series / parent:bucket fragmentation remediation (re-insert/merge) | Bucket reopening and the {metaField, timeField} index requirement (CVS 3.800); Cache-pressure early bucket closure and bucket catalog memory (CVS 3.775); Delete and re-insert safety on time series (CVS 3.725); Sharded time series rebuild and resharding (CVS 3.700) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-b17c7aa5e0c9 | replication-transactions / replication | majority-ack write concern change (CVS 3.800); dropIndexes locking and rollback by rebuild (CVS 3.775); Upgrade rollback playbook (CVS 3.750); Oplog windows and Search initial-sync recovery (CVS 3.700) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-2f2019ed2bed | diagnostics-operations / parent:ftdc and log tooling | mtools Log Analysis Integration (CVS 3.800) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-5b406510c316 | archive-federation / parent:date criteria | Online Archive query performance optimization (CVS 3.800) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-bdd5f61f7553 | time-series / parent:bucket catalog memory and closure reasons | Bucket archiving and query-based reopening (CVS 3.775); Frozen buckets and compression failures (CVS 3.700); Idle bucket expiry and archived bucket reopening (CVS 3.675); Cache-derived dynamic bucket size limit (CVS 3.100) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-0c9ecdd50528 | schema-modeling / parent:natural language to mongodb query generation | Validation and performance review of generated queries (CVS 3.775); Schema grounding and value linking for MQL generation (CVS 3.625) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-94bd5b52a712 | query-index-planner / index-design | MongoDB commit quorum and two-phase index builds (CVS 3.750); Two-phase (simultaneous) index builds (CVS 3.750); Rolling index builds as a resource-isolation alternative (CVS 3.750); serverStatus indexBuilds metrics and index build observability (CVS 3.725) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-a83ebb3f0b61 | identity-governance / identity-federation | Atlas SAML Entra ID (CVS 3.750); Entra ID OIDC Workforce Federation (CVS 3.650); GCP Workload Identity Atlas (CVS 3.425); LDAP and Federation (CVS 3.375) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-366a07958d6d | schema-modeling / parent:mongodb-time-series | Migration from Regular Collections (CVS 3.750) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-52b87d174a64 | diagnostics-operations / parent:mongodb backup and restore | Ops Manager Backup (CVS 3.750); Restore Workflows (CVS 3.075); Backup Anti-Patterns (CVS 3.000) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-036e3ca805ee | sharding / parent:covered queries on sharded collections | SHARDING_FILTER stage internals and orphaned-document filtering (CVS 3.750); Shard key index design (CVS 3.550); DISTINCT_SCAN with shard filtering in 8.2 (CVS 3.400); Express path for _id lookups on sharded collections (CVS 3.225) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-c5a4ee6b0d70 | mongodb-general / parent:mongodb-kafka-connector | MSK-Connect-deployment (CVS 3.750) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-12c8de3441e5 | cost-billing / cluster-sizing | One-way tier gates: sharding, Global Writes, edition changes (CVS 3.750); Destination right-sizing after cutover (CVS 3.700); Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes) (CVS 3.650); Gen2 clusters and Extended Standard IOPS economics (CVS 3.525) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-8df40ccd287c | mongodb-general / parent:mongodb geospatial | GeoJSON Object Types (CVS 3.725); Radius Unit Conversions (CVS 3.675); Geospatial Anti-Patterns (CVS 3.675) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-ead4605ef88b | schema-modeling / parent:random-key (hashed/uuid) index insert behavior | Clustered collection insert locality (CVS 3.725) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-a6b03cd32221 | mongodb-general / parent:mongodb atlas on azure | ExpressRoute Atlas Connectivity (CVS 3.725); NSG Rules for Atlas (CVS 3.550); Atlas Application Insights OTel (CVS 3.325); Azure Service Bus Atlas Triggers (CVS 3.175) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-664b801b87e8 | schema-modeling / parent:mongodb-kafka-connector | schema-registry-integration (CVS 3.725) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-9b275081d62e | search-vector / vector-embedding | Multi-Vector Patterns (CVS 3.725); Pre-quantized BinData (int8 and int1) ingestion (CVS 3.675); Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB (CVS 3.675); Auto Embedding Voyage AI (CVS 3.675) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-f07644513ef2 | query-index-planner / index-design | Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden) (CVS 3.700); Query settings and index filters as plan pinning (CVS 3.700); Initial sync index build memory limits (CVS 3.700); Atlas managed slow operation threshold and Performance Advisor index suggestions (CVS 3.675) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-975ece847641 | aggregation / parent:$group accumulator memory caps | per-accumulator explain memory statistics (CVS 3.700); custom $accumulator spill and merge semantics (CVS 3.675) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-4aea6e2a2abf | mongodb-general / parent:mongodb atlas on gcp | PSC Legacy Migration (CVS 3.700); GCP Global Access PSC (CVS 3.675); Atlas Stream Processing Pub/Sub (CVS 3.500); Looker Atlas BI Connector (CVS 3.450) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-3d90e57354b7 | query-index-planner / query-shape | Mixed-schema measurement predicate safety (CVS 3.700); External sorter spill files in dbpath/_tmp (CVS 3.675); Per-query fusion weighting (CVS 3.650); $querySettings stage and query settings inspection (CVS 3.600) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-f78d07b225d9 | cost-billing / billing-pricing | Cost-based ranker and the plan cache (8.3+) (CVS 3.700); Burstable M10/M20 CPU credits and the M30 production threshold (CVS 3.625); Burstable M10/M20 CPU-credit throttling and when to move to M30 (CVS 3.625); Atlas billing alert notification delivery (CVS 3.575) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-6f6dce76771c | replication-transactions / replication | MongoDB Search eventual consistency and replication-lag metrics (CVS 3.675); Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields) (CVS 3.675); Atlas minimum oplog window (oplogMinRetentionHours) tuning (CVS 3.650); linearizable read concern (CVS 3.625) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-7c50b4afaa88 | diagnostics-operations / parent:mongodb atlas stream processing | Stream Processor Monitoring (CVS 3.675) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-c6b651987a29 | query-index-planner / index-design | Index usage measurement with $indexStats (CVS 3.650); Redundant and prefix index detection (CVS 3.650); MongoDB rolling index builds (CVS 3.650); Primary-driven index builds and write-rate throttles (CVS 3.625) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-c778f20011cb | identity-governance / parent:mongodb security architecture | Authentication Methods (CVS 3.650) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-441524d0c05b | mongodb-general / parent:mongodb performance benchmarking | Workload Characterization (CVS 3.650); YCSB Workload Reference (CVS 3.600); Benchmarking Anti-Patterns (CVS 3.250); Baseline Methodology (CVS 3.025) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-d7196ea52923 | sharding / parent:shard key design and resharding as cost levers | Config shard versus dedicated config server (CVS 3.650) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-4be01f8fb55a | storage-wiredtiger / parent:atlas storage auto-scaling and disk reclaim via compact | Atlas disk decrease by volume replacement on AWS, Azure and GCP (CVS 3.650); Reducing Atlas storage capacity (new-volume sync, per-node downtime) (CVS 3.650); Atlas write-blocking thresholds and Intelligent Workload Management (CVS 3.600); Atlas Infinite storage metering and max storage limit (CVS 3.425) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-ea7ac08cebd8 | query-index-planner / parent:natural language to mongodb query generation | Execution-guided text-to-MQL refinement (CVS 3.650) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-faa5aa005f8b | api-tooling / app-services | App Services Migration Paths (CVS 3.650); Realm Migration Paths (CVS 3.375); MongoDB Realm Mobile Sync (CVS 3.325); Flexible Sync (CVS 3.225) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-2c3c2af5f1b7 | identity-governance / parent:atlas identity federation and resource policy boundaries | Atlas WIF built-in vs callback authentication (CVS 3.650) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-b245a56e13e9 | api-tooling / drivers | Deadline Propagation and Context Cancellation in MongoDB Drivers (CVS 3.650); Connection Pool Benchmarking (CVS 2.975); Realm SDK Languages and Platforms (CVS 2.700); MongoDB Drivers Architecture Internals (CVS 2.500) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-03dd84b04983 | diagnostics-operations / parent:kb-backed troubleshooting | SERVER JIRA Ticket Regression Mapping (CVS 3.650) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-3efebf992645 | search-vector / vector-embedding | Measuring ANN recall against ENN baselines (CVS 3.625); Atlas Vector Search HNSW IVF (CVS 3.450); Voyage AI Embeddings (CVS 3.375); Matryoshka and quantization-aware embedding models (CVS 3.375) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-367067ba7a92 | networking / parent:mongodb atlas on gcp | GCP VPC Peering (CVS 3.625); GCP Shared VPC (CVS 3.325); GCP Private Service Connect (CVS 3.200); Cloud DNS Private Zone for Atlas (CVS 2.775) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-8ec9154ebfb3 | sharding / parent:long-running secondary reads in sharded clusters | orphanCleanupDelaySecs and range deletion timing (CVS 3.625) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-a0f287f79c49 | mongodb-general / parent:mongodb ops manager and cloud manager | Upgrade Procedures (CVS 3.625); Version Manifest Mirroring (CVS 3.575); Live Migration to Atlas (CVS 3.450); PagerDuty/Datadog/Splunk Integration (CVS 3.450) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-746f46bdae21 | api-tooling / parent:mongodb realm mobile sync | Offline-First Patterns (CVS 3.625); Permissions Model (CVS 3.600); Conflict Resolution (CVS 3.525); Common Pitfalls (CVS 2.075) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-7451be70c74d | mongodb-general / parent:mongodb migration patterns | mongomirror Deprecation (CVS 3.625) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-68b4130466d8 | diagnostics-operations / parent:mongodb atlas online archive | Archive Restore (CVS 3.625); Archive Monitoring (CVS 3.250) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-0be0a58a9134 | time-series / parent:bucket fragmentation remediation (re-insert/merge) | rawData bucket-level CRUD (8.2 and later) (CVS 3.625); Rebuilding a time series collection with $out or mongorestore (CVS 3.500); Dynamic bucket sizing and cache-pressure closures (CVS 3.300); V2 and V3 compressed buckets and unsorted conversion (CVS 3.275) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-a52306435b73 | search-vector / search-index | Search Nodes Dedicated Infrastructure (CVS 3.600); Atlas Search Nodes (CVS 3.175); Search Nodes (CVS 3.175); Atlas Search Lucene Architecture (CVS 3.175) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-a60b195db1d3 | schema-modeling / parent:mongodb migration patterns | Migration Validation Patterns (CVS 3.600); Schema Transformation (CVS 3.200) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-0444cf01e935 | api-tooling / automation | Terraform state reconciliation after a Flex-to-Dedicated conversion (CVS 3.600); Terraform Atlas Provider v2.x (CVS 3.575); Ops Manager Admin API (CVS 3.550); Atlas tag enforcement through Terraform and APIs (CVS 3.525) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-7b807b8ba86d | mongodb-general / parent:mongodb atlas infrastructure as code | Atlas IaC Migration Paths (CVS 3.600); AKO Deletion Protection v2.0 (CVS 3.550); Atlas IaC Tool Decision Matrix (CVS 3.450); Atlas IaC Anti-Patterns (CVS 3.150) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-835ffca778c9 | storage-wiredtiger / parent:mongodb ops manager and cloud manager | S3-Compatible Snapshot Storage with Object Lock (CVS 3.600); Blockstore Snapshot Storage (CVS 3.225); Filesystem Snapshot Storage (CVS 3.050) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-26278075d879 | query-index-planner / query-shape | Per-shape maxTimeMS and queryKnobs (9.0) (CVS 3.600); Per-shape queryKnobs and maxTimeMS (9.0) (CVS 3.600); explodeForSort integer overflow (CVE-2026-82076) (CVS 3.575); External sorter spill files and the _tmp directory (CVS 3.525) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-480e6fc91e5c | networking / parent:mongodb atlas aws networking | DNS and SRV Records (CVS 3.600); Security Groups (CVS 3.450) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-6a7dac291e46 | sharding / parent:mongodb query shape optimization: sort, pagination, operators and sharded targeting | Hashed vs ranged shard key query trade-offs (CVS 3.600); Collation-based case-insensitive equality (CVS 3.400); Counter-document pattern (CVS 3.300); Tailable cursors and maxAwaitTimeMS (CVS 3.300) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-18c61444ac02 | mongodb-general / parent:atlas maintenance windows | Maintenance Impact Minimization (CVS 3.600); Deferring Maintenance (CVS 3.450) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-269bea7beb3a | query-index-planner / index-design | Multikey index coverage and multiKeyPaths (CVS 3.600); multikey index sort behaviour (CVS 3.600); Sparse versus partial index equivalence (CVS 3.600); Rolling index builds on Kubernetes with the Percona Operator (CVS 3.550) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-a70f5ba6e98d | replication-transactions / parent:causal consistency | read your own writes (CVS 3.600) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-8dd74aa67f67 | replication-transactions / replication | local read concern (CVS 3.575); Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration (CVS 3.575); Atlas Minimum Oplog Window (oplogMinRetentionHours) (CVS 3.525); Atlas auto-scaling gating by oplog window and its alerts (CVS 3.425) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-372a6407eb6e | cost-billing / billing-pricing | Safe execution against non-production Atlas (cluster isolation, guardrails, cost/cleanup discipline) (CVS 3.575); Config shard (embedded config server) cost trade-off (CVS 3.525); Cost-based ranker plan selection for sorted queries (8.3+) (CVS 3.400); Atlas backup/PITR and data transfer cost drivers (CVS 3.250) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-0d0939aba268 | sharding / parent:mongodb migration patterns | Sharded Cluster Migrations (CVS 3.575); MongoSync GA Tool (CVS 3.350) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-2ce9556582f9 | mongodb-general / parent:mongodb atlas multi-cloud | Multi-Cloud DR Pattern (CVS 3.575); Azure Partnership and MACC (CVS 2.400) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-80b202d28b71 | mongodb-general / parent:mongodb multi-tenancy | Multi-Tenancy Anti-Patterns (CVS 3.575) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-28706a00e932 | time-series / parent:wiredtiger cache eviction and dirty ratio | Time-series bucket closure under cache pressure (CVS 3.575) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-9950ed680654 | networking / parent:platform consolidation tco (atlas search/vector search vs separate search or vector db) | Search Node network transfer and multi-region cost (CVS 3.575) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-586d5ccba289 | mongodb-general / parent:mongodb expert knowledge | MongoDB Atlas (CVS 3.575); MongoDB Developer Patterns (CVS 3.050); MongoDB KB Articles (CVS 2.150) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-0594c62af41d | identity-governance / authorization-policy | Atlas RBAC (CVS 3.550); Atlas Organization Roles (CVS 3.450); Atlas Access Control and RBAC (CVS 3.425); Cedar forbid-only policy patterns for Atlas (CVS 3.375) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-272a1048a22c | identity-governance / parent:mongodb compliance and regulatory | HIPAA BAA and ePHI Configuration (CVS 3.550); Data Residency and EU Sovereignty (CVS 3.475); FedRAMP and AtlasGov (CVS 3.325); PCI DSS Scoping and Tokenization (CVS 3.225) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-71089ad6ce1a | query-index-planner / planner-explain | Multiplanner scoring and tie-breakers (CVS 3.550); SBE plan cache pinned entries and the classic runtime planner for SBE (CVS 3.550); Plan cache invalidation on index DDL (hide, drop, create) (CVS 3.525) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-70b86d349efb | sharding / parent:database proxies & query-optimization middleware | mongos as MongoDB's native router & why MongoDB rarely uses third-party proxies (CVS 3.550) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-353b35c18a09 | aggregation / parent:mongodb query shape optimization: sort, pagination, operators and sharded targeting | Find projection vs $project aggregation coverage (CVS 3.550) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-e4e31a146993 | diagnostics-operations / parent:mongodb monitoring and observability | Datadog Integration (CVS 3.525); New Relic Integration (CVS 3.250) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-e12888479cf1 | query-index-planner / query-shape | internalQueryMaxScansToExplode and maxScansToExplodeReached (CVS 3.525); Atlas Query Profiler and Operation Throttling metrics (CVS 3.525); Percona PMM mongolog versus profiler query source (CVS 3.450); Atlas Query Shape Insights and Namespace Insights (CVS 3.400) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-6c84a071d812 | networking / parent:mongodb atlas infrastructure as code | Atlas IP Access List Ownership Conflict (CVS 3.525) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-734b288e14c5 | diagnostics-operations / parent:flex limitations and migration to dedicated | Flex backup and recovery planning (CVS 3.525) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-40309c756b09 | mongodb-general / parent:mongodb atlas stream processing | Hopping Windows (CVS 3.500); Tumbling Windows (CVS 3.475); Session Windows (CVS 3.375) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-f6ac572aba6f | mongodb-general / parent:mongodb atlas triggers and functions | Change Data Capture Patterns (CVS 3.500); Function Context Object (CVS 3.400); Trigger and Function Anti-Patterns (CVS 3.150); HTTPS Endpoints (CVS 2.575) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-b397d383429d | api-tooling / automation | Atlas CLI Scripting (CVS 3.500); Flex Tooling Migration Terraform K8s CLI (CVS 3.500); GKE Atlas Kubernetes Operator (CVS 3.425); Atlas Kubernetes Operator AKO v2.14 (CVS 3.425) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-ae873d2f56e0 | storage-wiredtiger / parent:wiredtiger storage engine internals | Timestamp APIs (oldest/stable/pinned) (CVS 3.500); Reconciliation and Page Splitting (CVS 3.025); MongoDB 8.0 WT Improvements (TCMalloc, ExpressPlan) (CVS 2.600) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-3e9502b80e34 | identity-governance / encryption-keys | Atlas security add-on uplifts (auditing, LDAP, customer-managed keys, private endpoints) (CVS 3.500); Azure Key Vault RBAC Atlas (CVS 3.300); Encryption Requirements (At-Rest, In-Transit, Field-Level) (CVS 3.175); Atlas Programmatic API Keys (Legacy) (CVS 3.150) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-b7c969c2a118 | cost-billing / cluster-sizing | FTDC Storage Overhead & Retention Budgeting (CVS 3.500); Atlas Infinite fixed-IOPS tiers and decoupled storage (CVS 3.325); M10 shared-vCPU dedicated tier economics (CVS 3.300); Eviction thread sizing and wiredTigerEngineRuntimeConfig tuning (CVS 3.275) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-5e1e804f42f7 | query-index-planner / index-design | Collation-aware index key size (CVS 3.475); path-level multikey tracking (CVS 3.450); Atlas Administration API rolling index endpoint (CVS 3.400); MongoDB primary-driven index builds (PDIB) (CVS 3.400) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-9767e9fb3174 | diagnostics-operations / parent:database profiler vs query profiler | Ops Manager Profiler (CVS 3.475); Amazon DocumentDB profiler (CloudWatch Logs) (CVS 2.825) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-6893051d2409 | sharding / parent:mongodb capacity planning | Sharding Triggers (CVS 3.475) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-b7cbe85f979c | mongodb-general / parent:mongodb upgrade paths | Point of No Return (CVS 3.475); Straight-to-8 jump pattern (CVS 3.450); Common upgrade failures (CVS 3.400); Upgrade event coverage (pre/during/post) (CVS 3.025) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-66a976b0eee5 | diagnostics-operations / parent:mongodb ops manager and cloud manager | Backup Daemon (CVS 3.450); Backup Daemon and Head DB (CVS 2.875); Monitoring Agent (CVS 2.575) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-a8bd98441f1a | mongodb-general / parent:mongodb spark connector and databricks integration | Spark Connector vs Alternatives (CVS 3.450); Databricks Workspace Integration (CVS 3.025); Spark Connector V10 Architecture (CVS 3.025); Performance Tuning Checklist (CVS 2.900) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-1131b10a900e | diagnostics-operations / parent:atlas hybrid fusion and bm25 diagnostics | BM25 IDF corpus statistics (CVS 3.450); BM25 term frequency saturation and field length normalization (CVS 3.450); Fusion score normalization strategies (CVS 3.450) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-e843d0959617 | cost-billing / parent:atlas cluster tiers (m30) & major-version upgrade mechanics | M30 specs & connection limits (CVS 3.450) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-27f762df4c87 | query-index-planner / parent:database profiler vs query profiler | Atlas Real-Time Performance Panel (CVS 3.425) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-0d9513c00c8a | networking / parent:mongosync | tls-x509-auth (CVS 3.425) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-aa8dae0ac5e2 | api-tooling / automation | Kubernetes Operator Deployment (CVS 3.425); Atlas Data API (EOL) (CVS 3.400); Cloud Build Atlas API Auth (CVS 3.250); Atlas CLI Terraform Plugin (CVS 3.200) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-343b4f1fd839 | storage-wiredtiger / parent:mongosync | resume-and-checkpoint (CVS 3.425) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-7cd1c9c93f1a | replication-transactions / replication | Multi-Cloud Replica Sets (CVS 3.400); Primary-driven index builds (spill to a replicated table) (CVS 3.150); available read concern (CVS 3.050); Rolling index build key inconsistency incident (CVS 2.725) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-b63ded16c61f | api-tooling / shell-tools | Compass Data Modeling ER Diagrams (CVS 3.400); Compass CRUD and Documents Tab (CVS 3.200); Compass Performance Insights (CVS 3.175); Compass Anti-Patterns (CVS 2.575) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-4d7e60c43906 | query-index-planner / index-design | Primary-driven index builds (CVS 3.400); Multikey index sort bounds (CVS 3.400); Atlas Performance Advisor drop-index recommendations (CVS 3.325); Index Sufficiency Warning (CVS 3.200) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-9860e797131c | cost-billing / parent:query efficiency as a cost lever | Covered queries and projection design (CVS 3.400) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-1525e6d34833 | diagnostics-operations / parent:mongodb atlas iam and rbac | Atlas Log Push SIEM (CVS 3.375) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-46673b83291a | query-index-planner / parent:sort_merge and $in sort expansion | Interval evaluation trees and parameterized plan caching (CVS 3.350) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-59597c811d2a | identity-governance / parent:mongodb atlas iam and rbac | Atlas Activity Feed (CVS 3.325); Atlas Organization Teams (CVS 3.225); Atlas LDAPS (Deprecated 8.0) (CVS 3.050) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-511384aadb70 | identity-governance / identity-federation | Google Workspace SAML Federation (CVS 3.325); Atlas Three-Tier Identity Model (CVS 2.950); Ops Manager LDAP/Kerberos/SAML/OIDC Federation (CVS 2.875); Workforce and Workload Identity Federation (CVS 2.575) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-6a1c409b355b | mongodb-general / parent:mongodb ops manager and cloud manager | Ops Manager Architecture (CVS 3.325); Common Failure Modes (CVS 3.300); Ops Manager Application (CVS 3.275); Multi-Org Scale Patterns (CVS 3.150) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-2618e44302ce | search-vector / vector-embedding | Azure OpenAI Atlas Vector Search (CVS 3.325); Vertex AI Atlas Vector Search (CVS 3.325); Quantization-aware and Matryoshka embeddings (voyage-3-large) with Atlas dimension slicing (CVS 3.300); RAG Patterns with Vector Search (CVS 3.200) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-5ceedb05d0f7 | aggregation / parent:mongodb atlas stream processing | Stream Processor Pipeline (CVS 3.300) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-fb5f4021932f | networking / parent:mongodb atlas on azure | Hub-and-Spoke Atlas Networking (CVS 3.300); Atlas Bicep Private Endpoint (CVS 3.200); Azure Private DNS Resolver (CVS 3.050); Atlas Private DNS Zones Azure (CVS 2.775) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-d4596a7c1ce4 | cost-billing / parent:schema design for storage cost | Field-name abbreviation trade-offs (CVS 3.300) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-803bb5221982 | mongodb-general / parent:mongodb performance regression detection and testing methodology | Coefficient of Variation / Run-to-Run Noise Control (CVS 3.275) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-d9a82186dbd1 | identity-governance / authorization-policy | Service Account per Environment Pattern (CVS 3.275); IAM Role Atlas API Access (CVS 3.250) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-88cc8939dcad | cost-billing / cluster-sizing | Atlas index build tier defaults (CVS 3.250); Atlas tier-fixed index build limits (CVS 3.250); Atlas Infinite fixed per-tier IOPS and public-preview feature exclusions (CVS 3.150); Auto-scaling tier ranges (CVS 3.050) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-e97ebaff6742 | mongodb-general / parent:mongodb atlas on gcp | GKE NodeLocal DNSCache Atlas (CVS 3.250); Cloud HSM Atlas (CVS 3.250); GCP Regions Atlas Mapping (CVS 3.125); Google Distributed Cloud GDC (CVS 2.525) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-733862797816 | storage-wiredtiger / parent:atlas storage auto-scaling and disk reclaim via compact | MongoDB 8.0 autoCompact background compaction on Atlas (CVS 3.250); Atlas Infinite storage model (max storage limit, no auto-scaling) (CVS 3.175) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-c40e2099a647 | aggregation / parent:atlas hybrid fusion and bm25 diagnostics | Ranked and scored input pipeline eligibility (CVS 3.250) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-77fb33304703 | search-vector / parent:mongodb atlas vector search | RAG Patterns (CVS 3.200) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-0bd972ad850c | identity-governance / parent:atlas resource policies cedar | Atlas nonCompliantResources endpoint (CVS 3.200) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-44e99a657c0c | query-index-planner / query-shape | Atlas Query Shape Insights (CVS 3.200); Power BI DirectQuery (CVS 3.000); Compass Natural Language Query (CVS 2.850); Percona PMM mongolog query source (CVS 2.725) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-9fc6f09a3009 | query-index-planner / parent:mongodb query optimization tooling: compass explain, atlas query insights and performance advisor | Namespace Insights (CVS 3.200) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-0d1e62176238 | query-index-planner / index-design | Sparse and partial indexes for $exists (CVS 3.200); Hashed Indexes (CVS 3.150); Text Indexes (CVS 3.150); TTL Indexes (CVS 3.150) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-0ecd8d6fb6f0 | api-tooling / app-services | Partition-Based Sync (Legacy) (CVS 3.175); Sync Configuration (CVS 3.100); Realm Object Model (CVS 3.075); Realm Migration (CVS 3.075) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-32c3803915b5 | api-tooling / automation | Organization-scoped alert configuration API (CVS 3.175); Atlas GraphQL API Removal (CVS 3.175); Lambda Managed Instances and MongoClient concurrency safety (CVS 3.175); atlas kubernetes config generate (CVS 3.150) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-8ff70ee25045 | search-vector / search-index | Search Highlighting (CVS 3.150); Atlas Search Architecture (CVS 2.875); Atlas Search Anti-Patterns (CVS 2.750) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-37fc02336c5b | storage-wiredtiger / parent:oplog sizing under storage auto-scaling | replSetResizeOplog and oplog compaction runbook (CVS 3.150) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-d624439a89da | identity-governance / audit-compliance | Compliance Gaps and Shared Responsibility (CVS 3.150); PII Masking & Query Hash Anonymization (CVS 3.000); Atlas IAM Compliance Mapping (CVS 2.875); Atlas Compliance Certifications (CVS 2.850) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-9cff09d95361 | sharding / parent:mongodb query shape optimization: sort, pagination, operators and sharded targeting | $function and server-side JavaScript hardening (CVS 3.150); Client-side operation timeout (CSOT) (CVS 2.800) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-91cc19c76420 | cost-billing / billing-pricing | Atlas Charts billing dashboards (CVS 3.150); Credit expiry and History table (CVS 3.150); Atlas marketplace private offers (CVS 3.100); Gen1 vs Gen2 storage and IOPS billing (CVS 3.100) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-4308c7661d27 | api-tooling / automation | Atlas GraphQL API (EOL) (CVS 3.150); Multi-Environment Terraform Directories vs Workspaces (CVS 3.125); Atlas Admin API invoice endpoints (CVS 3.050); Pause/resume automation with Terraform or GitHub Actions (CVS 3.050) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-d53c2a9ffb01 | schema-modeling / parent:atlas sql interface mongosql | Atlas SQL Schema Builder (CVS 3.150) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-a337172ad861 | api-tooling / parent:mongodb atlas app services | Custom HTTPS Endpoints (EOL) (CVS 3.150) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-7e83aa58193c | time-series / parent:mongodb time-series query and index optimization | Index hints on time series collections (CVS 3.150) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-f989d473b7e1 | identity-governance / parent:atlas federated authentication | JIT user provisioning (CVS 3.150) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-ac926399aa55 | api-tooling / parent:mongodb atlas terraform provider | Atlas Cluster IaC (CVS 3.125) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-949f44190f7a | mongodb-general / parent:mongodb atlas on azure | Atlas Azure Regions Mapping (CVS 3.125); AtlasGov Azure Government (CVS 3.025); Azure Native MongoDB ANM (CVS 2.950); Atlas MACC Eligibility (CVS 2.700) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-29539c2a7d1c | mongodb-general / parent:mongodb kb articles | Error Code Lookup (CVS 3.125); Performance KB Articles (CVS 2.575); Security KB Articles (CVS 2.575) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-2030af7213e7 | identity-governance / encryption-keys | Atlas Envelope Encryption GCP (CVS 3.100); Client Side Field Level Encryption (CSFLE) (CVS 3.100); Programmatic API Keys Legacy Auth (CVS 3.050) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-22db29b88ceb | storage-wiredtiger / parent:mongodb stress, soak, and chaos-resilience testing | Breaking-point / overload testing methodology (first bottleneck vs visible symptom, cascading failure, thundering herd, cache-eviction death spiral) (CVS 3.100); Sustained overload / soak testing (memory leaks, connection pool exhaustion, WiredTiger cache thrashing, ticket starvation, oplog window shrinkage) (CVS 3.050) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-bd6489c69c3d | time-series / parent:bucket catalog memory and closure reasons | Dynamic bucket size cap under cache pressure (CVS 3.100); Side bucket catalog (CVS 2.875); Side bucket catalog for time series updates and deletes (CVS 2.875); Bucket catalog stripes, state registry and eras (CVS 2.825) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-a7061a319c83 | archive-federation / parent:mongodb atlas on gcp | Atlas Data Federation GCS (CVS 3.100) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-326a9da785a4 | search-vector / vector-embedding | HNSW Index Parameters (CVS 3.100); Automated Embedding (autoEmbed) quantization types (CVS 3.000); Automated Embedding (autoEmbed) quantization types including binaryNoRescore (CVS 3.000); Idle-spend and minimum-commit economics of serverless vector stores (CVS 2.950) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-468120abc19f | aggregation / parent:mongodb advanced explain: aggregation, sharded plans, loose index scans and the 8.3 cost-based ranker | SBE $lookup pushdown and hash join (CVS 3.100); $groupByDistinct internal stage (CVS 3.000) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-b58330cefc6d | query-index-planner / index-design | Search Index Mapping (CVS 3.100); Rolling index builds as a resource-limited alternative (CVS 3.000); Unique Indexes (CVS 3.000); Compass Index Management (CVS 2.950) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-c8ad8a77bff0 | cost-billing / billing-pricing | Shared-cost allocation rules for managed database services (CVS 3.075); Gen1 vs Gen2 IOPS billing (CVS 3.050); Backup and PITR cost modelling (CVS 3.050); Multi-region cluster cost premium (CVS 3.050) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-68aac318a142 | query-index-planner / parent:compound index vs index union for $or | Same-field `$or` to `$in` rewrite (CVS 3.050) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-e1eb00faceff | archive-federation / parent:mongodb atlas on azure | Azure Synapse Atlas Data Federation (CVS 3.050) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-a634f98f5cef | mongodb-general / parent:mongodb atlas infrastructure as code | AKO Dry Run Mode (CVS 3.050) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-97d0be9985d2 | cost-billing / parent:atlas cost planning: region pricing, estimation, scheduled scaling and competitor tco | Atlas Infinite compute auto-scaling (CVS 3.050); Scale-down tuning for spiky batch workloads (CVS 2.850); DynamoDB on-demand vs provisioned break-even (CVS 2.600); Cosmos DB RU estimation for MongoDB workloads (CVS 2.450) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-047d3a5eff67 | cost-billing / cluster-sizing | Cedar policy authoring for cluster size and autoscaling caps (CVS 3.050); Right-sizing from Atlas metrics (CVS 3.050); Common Sizing Mistakes (CVS 3.025); Analytics node tier prorating (CVS 3.000) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-8f2fb9450e90 | storage-wiredtiger / parent:mongodb aggregation pipeline | Memory Limits and allowDiskUse (CVS 3.050) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-ec3558b1401a | cost-billing / billing-pricing | Atlas App Services Cost Model (CVS 3.025); Atlas-only feature lock-in and exit cost (CVS 3.000); AWS Marketplace EDP drawdown for Atlas (CVS 3.000); Backup and PIT oplog storage region billing (CVS 3.000) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-52a06240c41f | api-tooling / parent:mongodb java driver 5.x version timeline & 8.0 compatibility | minor-version compatibility rule (CVS 3.000) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-1f33141d477d | storage-wiredtiger / parent:wiredtiger cache eviction and dirty ratio | Spill WiredTiger instance cache (CVS 3.000); WiredTiger spill instance cache (CVS 3.000) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-5e7b26f7bdcf | api-tooling / app-services | App Services Deployment Model (CVS 3.000); App Services Rules and Permissions (CVS 3.000); App Services Schema Validation (CVS 3.000); App Services Values and Secrets (CVS 3.000) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-e570f811eac4 | cost-billing / billing-pricing | Cost Explorer filters for AI services (CVS 3.000); Query limits and billing alerts for archive spend (CVS 3.000); Atlas Infinite oplog and storage cost (CVS 2.975); Project-level billing change alerts (CVS 2.950) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-7bd3b5b8b388 | sharding / parent:atlas sql interface mongosql | MongoSQL ODBC Driver (CVS 3.000) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-68222234dd24 | diagnostics-operations / parent:mongodb performance troubleshooting | Performance Diagnostic Workflow (CVS 3.000) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-7b4b502e3f24 | cost-billing / parent:atlas billing mechanics and cost visibility | Support line items per cloud provider on invoices (CVS 3.000) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-631639b707f5 | networking / parent:mongodb security architecture | Network Security Layers (CVS 2.975) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-dfaf850dab9b | identity-governance / parent:mongodb atlas on azure | Atlas LDAP Azure AD DS (CVS 2.975); Atlas Secretless KV Authentication (CVS 2.625) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-de1c0f2fac41 | networking / parent:migration and cutover cost (live migration, mongosync, dual-running, egress) | Cloud exit-credit programs and EU Data Act in-parallel egress (CVS 2.975) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-03e4970d4503 | search-vector / vector-embedding | Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors (CVS 2.950); Lucene BBQ binary quantization compared with Atlas binary quantization (CVS 2.775); Search node tier sizing for vector indexes (CVS 2.550) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-49ee480ab53f | mongodb-general / parent:date criteria | DATE criteria field types and formats (CVS 2.950) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-d75e388f7c62 | cost-billing / cluster-sizing | Enterprise Advanced licensing economics (CVS 2.950); Oplog sizing in Kubernetes operators and managed MongoDB-compatible services (CVS 2.850); Cloud Manager Free/Standard/Premium Tiers (CVS 2.525) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-6adc93138105 | cost-billing / billing-pricing | Shared-cost splitting for Atlas projects (CVS 2.950); Config shard versus dedicated config server cost (CVS 2.850); MongoDB Charts billing dashboards (CVS 2.850); Intra-cluster replication transfer billing (CVS 2.800) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-0700af48832c | search-vector / parent:mongodb atlas search and vector search | Stored Source Performance Optimization (CVS 2.950) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-e4ebaf2ad65a | query-index-planner / index-design | positional index path caveat (CVS 2.925); Persisting index usage metrics across restarts (PMM/monitoring) (CVS 2.850); Collation-based case-insensitive indexes as a $regex alternative (CVS 2.800); Single-Field Indexes (CVS 2.800) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-b956cbf404fd | mongodb-general / parent:mongodb ops manager and cloud manager | Enterprise Advanced Licensing (CVS 2.900) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-4b089bde7a44 | schema-modeling / parent:operation rejection filters | maxEstimatedScanBytes collection-scan rejection (9.0) (CVS 2.900) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-1537f1c9f03c | networking / parent:storage and data-lifecycle cost levers | Network (wire) compression (CVS 2.900) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-0d11435299da | diagnostics-operations / parent:mongodb atlas on gcp | Atlas Alerts Pub/Sub Escalation (CVS 2.875); Cloud Monitoring Atlas Metrics (CVS 2.875); Atlas GCP Troubleshooting (CVS 2.600) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-d369cc167fa2 | diagnostics-operations / parent:mongodb atlas on azure | Atlas Azure Monitor Metrics (CVS 2.875); Atlas Sentinel Log Integration (CVS 2.875); Atlas Azure Troubleshooting Playbook (CVS 2.600) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-8b6b0620aca1 | mongodb-general / parent:mongodb university & certification | Learning Paths by Role (CVS 2.850); Associate Developer Certification (CVS 2.675); Associate Atlas Administrator (CVS 2.625); Associate DBA Certification (CVS 2.600) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-f5126bc4749e | storage-wiredtiger / parent:mongodb-aggregation-stages-deep | allowDiskUse-100MB-stage (CVS 2.850) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-c2b116f7efea | api-tooling / automation | Auto-scaling min/max bounds and Terraform drift (CVS 2.850); Atlas Terraform Azure Provider (CVS 2.675); Atlas Terraform GCP Provider (CVS 2.675); Atlas CLI Failure Scenarios (CVS 2.650) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-0b99f427bf56 | aggregation / parent:mongodb compass | Compass Aggregation Pipeline Builder (CVS 2.850) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-c7655b542f60 | sharding / parent:mongodb bi connector and sql access | mongosqld Architecture (CVS 2.825) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-72ec775bc1f4 | identity-governance / parent:mongodb bi connector and sql access | BI Connector Authentication (CVS 2.825) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-eebdcce5b375 | schema-modeling / parent:mongodb bi connector and sql access | DRDL Schema Management (CVS 2.800) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-fd6aad8dc2b9 | cost-billing / billing-pricing | Retroactive support billing on reactivation (CVS 2.800); Atlas billing alert configuration via Admin API (CVS 2.750); Atlas included-replica pricing vs per-instance HA billing (CVS 2.650); Re-indexing cost when changing numDimensions (CVS 2.650) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-d945bf6ed1c3 | time-series / parent:data lifecycle cost model (ttl vs online archive vs data federation) | Time series collection expireAfterSeconds (CVS 2.800) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-9effc0514098 | identity-governance / audit-compliance | Atlas Azure Security Compliance (CVS 2.750); Audit-Ready Architecture and Evidence Collection (CVS 2.750); Common Audit Findings and Remediation (CVS 2.475); Scheduled compliance polling and alerting (CVS 2.450) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-f73749345fb5 | query-index-planner / index-design | Rolling index build table-logging incident (CVS 2.725); PostgreSQL invalid indexes from failed CONCURRENTLY builds (CVS 2.400); SQL Server resumable online index operations (CVS 2.400); PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY (CVS 2.300) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-d276eb514345 | mongodb-general / parent:mongodb performance benchmarking | Benchmark Result Reporting (CVS 2.700) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-2ff1852dc9f0 | time-series / parent:mongodb-time-series | Atlas Charts Integration (CVS 2.700) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-a29d8407e9dc | storage-wiredtiger / parent:partition fields | Partition Field Cardinality and the 2023-06-07 Storage Engine Change (CVS 2.700) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-18067a89fb07 | networking / parent:atlas cost planning: region pricing, estimation, scheduled scaling and competitor tco | Atlas PrivateLink regional endpoint rates (CVS 2.700); Egress and data transfer estimation (CVS 2.650) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-210d2a18c904 | query-index-planner / query-shape | Federated Query on Archive (CVS 2.700); queryKnobs and per-command querySettings (CVS 2.650); Queryable Backups (CVS 2.300) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-0a2873eb4ed8 | aggregation / parent:mongodb geospatial | Geospatial $lookup Patterns (CVS 2.700) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-86157c3fe16f | cost-billing / parent:atlas cost commitments, cross-org billing and finops tooling | Untagged spend reporting (CVS 2.650); Proportional minimum-commit allocation (CVS 2.450); Unlinking an organization (CVS 2.250) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-a0275432efc9 | cost-billing / billing-pricing | GCP Partnership and Marketplace (CVS 2.600); Atlas Admin API billing alert configuration (CVS 2.600); FOCUS column mapping for Atlas credits (CVS 2.600); Linking Atlas orgs to marketplace billing accounts (CVS 2.600) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-d8c01f75fb44 | api-tooling / automation | Atlas Admin API rate limiting for scheduled polling (CVS 2.600); Conftest/OPA rules over terraform show -json plans (CVS 2.550); Atlas Admin API pending-invoice tags field (CVS 2.400) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-4612d59db35d | aggregation / parent:atlas cost commitments, cross-org billing and finops tooling | Cross-vendor FOCUS pipelines (BigQuery/Snowflake) (CVS 2.600) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-d6f76edaa459 | mongodb-general / parent:mongodb upgrade paths | Error Envelope and customer sign-off (CVS 2.500) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-bf9495060320 | api-tooling / drivers | MongoDB Drivers Benchmark Metrics (CVS 2.500); MongoDB Drivers Failure Scenarios (CVS 2.500); MongoDB Drivers Operational Runbook (CVS 2.500) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-500f97098aa4 | sharding / parent:mongosh reference | mongosh Reference Architecture Internals (CVS 2.500); mongosh Reference Benchmark Metrics (CVS 2.500); mongosh Reference Failure Scenarios (CVS 2.500); mongosh Reference Operational Runbook (CVS 2.500) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-a9c2cc4bbf19 | storage-wiredtiger / parent:atlas cost planning: region pricing, estimation, scheduled scaling and competitor tco | Backup storage rates by region (CVS 2.450) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-beb7bc3a2e9a | replication-transactions / replication | Replica Set Support Articles (CVS 2.425); Connection URI server-selection options (unscored); Oplog recovery headroom (unscored); Per-member replica-set telemetry (unscored) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-d01cd2452df0 | networking / parent:mongodb atlas on gcp | Cloud DNS Terraform Atlas (CVS 2.350) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-dab118cd8660 | storage-wiredtiger / parent:storage and data-lifecycle cost levers | Journal compression (CVS 2.350) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-ebe6aebafc39 | api-tooling / shell-tools | Compass Plugins and Extensibility (CVS 2.325); Compass Editions (CVS 2.250) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-3da97516cefc | cost-billing / billing-pricing | Billing incidents and refunds (CVS 2.300); Charts billing ingestion for linked orgs (CVS 2.000) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-256d4ce7d86f | diagnostics-operations / parent:error codes and troubleshooting | Error Codes and Troubleshooting Benchmark Metrics (CVS 2.250) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-0fa2d89641e4 | identity-governance / parent:mongodb atlas triggers and functions | Authentication Triggers (CVS 2.225) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-41eb8b5e0dea | query-index-planner / index-design | SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints (CVS 2.200) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-21710e9f436c | api-tooling / app-services | Atlas Device Sync Overview (CVS 2.200) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-d64949dd25b2 | mongodb-general / parent:mongodb university & certification | Instructor-Led Training (CVS 2.200); Skill Badges (free micro-credentials) (CVS 2.175); MongoDB University Platform (CVS 2.150); TAM Positioning Playbook (CVS 1.925) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-6e3285aedc9b | diagnostics-operations / parent:mongodb developer patterns | Customer Troubleshooting Playbooks (CVS 2.175) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-21700f493683 | schema-modeling / parent:mongodb university & certification | Associate Data Modeler (CVS 2.150) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-86b55445bd3c | query-index-planner / parent:mongodb wildcard and hidden indexes, index builds and index overhead | Cosmos DB for MongoDB wildcard differences (CVS 2.150) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-1c1358758476 | mongodb-general / parent:mongodb atlas on gcp | MongoDB for Startups GCP (CVS 2.000); Google Cloud Partner of Year (CVS 1.400) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-79683d333c0b | identity-governance / audit-compliance | Process & governance (OWASP GenAI Red Teaming Guide, MITRE ATLAS, NIST AI RMF, red-team-in-CI) (CVS 1.625) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-ccad973cc77f | mongodb-general / parent:mongodb university & certification | Credly Digital Badges (CVS 1.475) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-d05fd98164be | replication-transactions / parent:server selection algorithm | Custom server selectors (unscored); Read preference candidate filtering (unscored) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-bd3136e37397 | replication-transactions / parent:replication lag monitoring | Delayed-member lag interpretation (unscored) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-67232cc8ea85 | sharding / parent:shard key index constraints when dropping or hiding indexes | Hashed shard-key index drop operational procedure (unscored); Unique index requirements when refining a shard key (unscored) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-6c026d4056b6 | diagnostics-operations / parent:server selection algorithm | Server Discovery and Monitoring RTT estimates (unscored) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-9cfafc173079 | replication-transactions / replication | Server selection timeout and retry loop (unscored) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |

## Full inventory

| # | CVS | decision | concept | parent | mode | tree state | cohort | holder |
|---:|---:|---|---|---|---|---|---|---|
| 1 | 4.725 | RESEARCH | Connection pooling and connection-storm control for Atlas (serverless and Lambda clients) | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | covered | mongodb-cohort-2a03c480ee30 | — |
| 2 | 4.650 | RESEARCH | Atlas Billing and Invoice Anatomy | Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-7b5383d7d6ca | — |
| 3 | 4.650 | RESEARCH | Atlas Cost Explorer and Billing Data API | Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-7b5383d7d6ca | — |
| 4 | 4.625 | RESEARCH | Connection Pool Tuning | MongoDB Connection String URI | dr | covered | mongodb-cohort-2a03c480ee30 | — |
| 5 | 4.600 | REFRESH | MongoDB Atlas Cost Optimization | MongoDB Atlas | dr | covered | mongodb-cohort-7b5383d7d6ca | — |
| 6 | 4.525 | RESEARCH | Read Concern | MongoDB Connection String URI; MongoDB Transactions | dr | covered | mongodb-cohort-67b8def68c5a | — |
| 7 | 4.525 | RESEARCH | Time series cardinality and metaField design | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 8 | 4.525 | RESEARCH | Write Concern | MongoDB Connection String URI; MongoDB Transactions | dr | covered | mongodb-cohort-67b8def68c5a | — |
| 9 | 4.500 | RESEARCH | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | MongoDB Performance Troubleshooting | dr | covered | mongodb-cohort-7189a33f6864 | — |
| 10 | 4.500 | RESEARCH | Resource Tags and Cost Allocation (Showback/Chargeback) | Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-7b5383d7d6ca | — |
| 11 | 4.475 | RESEARCH | Shard key index constraints when dropping or hiding indexes | Hidden indexes and safe index removal | dr | covered | mongodb-cohort-ab6ca72e8dcd | — |
| 12 | 4.475 | RESEARCH | MongoDB Major-Version Upgrade Regression Detection | MongoDB Performance Regression Detection and Testing Methodology | dr | frontier | mongodb-cohort-a0a420b316d1 | — |
| 13 | 4.450 | RESEARCH | Connection pool sizing and connection-storm control for Atlas (serverless and Lambda clients) | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-321ef5e25160 | — |
| 14 | 4.450 | RESEARCH | Continuous Cloud Backup (PITR) | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-0e7a6f84ee61 | — |
| 15 | 4.450 | RESEARCH | Replication Lag Monitoring | MongoDB Monitoring and Observability | dr | covered | mongodb-cohort-67b8def68c5a | — |
| 16 | 4.450 | RESEARCH | Hot shard diagnosis and shard key remediation | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-1d6ef7b4932c | — |
| 17 | 4.450 | RESEARCH | Shard Key Design for Multi-Tenancy | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-18121faaf93a | — |
| 18 | 4.450 | RESEARCH | $queryStats aggregation stage | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-5bc61fcfe3ec | — |
| 19 | 4.450 | RESEARCH | CSOT Client-Side Operations Timeout | MongoDB Connection String URI | dr | frontier | mongodb-cohort-6f6a12e41dfc | — |
| 20 | 4.450 | RESEARCH | Streaming Write Semantics | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a04dd23fc577 | — |
| 21 | 4.450 | RESEARCH | Relational Migrator | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-f1ebe93a2c8b | — |
| 22 | 4.450 | RESEARCH | $elemMatch semantics on arrays of subdocuments | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-b786132ea6d4 | — |
| 23 | 4.450 | RESEARCH | Atlas Required Memory metric sizing | Atlas Cluster Topology and Tier Economics; Vector Search Quantization and Embedding Storage Cost | dr | covered | mongodb-cohort-3bc7bd71277a | — |
| 24 | 4.450 | RESEARCH | Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe) | Atlas Cluster Topology and Tier Economics | dr | covered | mongodb-cohort-526e32151244 | — |
| 25 | 4.450 | REFRESH | Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation) | Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-237970d23d85 | — |
| 26 | 4.450 | RESEARCH | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | MongoDB Indexes Deep Dive | dr | covered | mongodb-cohort-b786132ea6d4 | the research suite run mongodb-2026-10-14 |
| 27 | 4.450 | RESEARCH | MongoDB Explain Plans, Query Planner and Plan Cache | MongoDB Indexes Deep Dive; MongoDB Monitoring and Observability; MongoDB Performance Benchmarking; MongoDB Performance Troubleshooting; mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-d49f86c79017 | the research suite run mongodb-2026-10-14 |
| 28 | 4.425 | RESEARCH | Reading sharded explain output (shards, SINGLE_SHARD, SHARD_MERGE) | Covered queries on sharded collections | dr | frontier | mongodb-cohort-74cd39f19180 | — |
| 29 | 4.425 | RESEARCH | Sessions | MongoDB Driver Internals | dr | frontier | mongodb-cohort-beeb86966a6e | — |
| 30 | 4.375 | RESEARCH | Relevance Scoring | MongoDB Atlas Search | dr | frontier | mongodb-cohort-3aa797450c89 | — |
| 31 | 4.375 | RESEARCH | analyzeShardKey and query sampling | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-2e478e8e7c3f | — |
| 32 | 4.375 | RESEARCH | analyzeShardKey query sampling and candidate-key scoring | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-2e478e8e7c3f | — |
| 33 | 4.375 | RESEARCH | Binary downgrade window | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-f8dad38f861e | — |
| 34 | 4.375 | RESEARCH | Connection Capacity | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-1d798a0d85d1 | — |
| 35 | 4.375 | RESEARCH | Cutover Strategies | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-f1ebe93a2c8b | — |
| 36 | 4.375 | RESEARCH | Long-Running Transactions and Cache Pressure | WiredTiger Storage Engine Internals | dr | frontier | mongodb-cohort-0a5c86f5c884 | — |
| 37 | 4.375 | RESEARCH | Delete propagation and reconciliation for $merge-maintained views | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 38 | 4.350 | RESEARCH | Index build commit quorum and hung builds | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 39 | 4.350 | RESEARCH | $queryStats and $currentOp as alternatives to the profiler | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 40 | 4.350 | RESEARCH | Goal-State Automation Configuration | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-22646bcd15df | — |
| 41 | 4.350 | RESEARCH | Hashed and compound hashed shard keys and index coverage | Covered queries on sharded collections | dr | frontier | mongodb-cohort-74cd39f19180 | — |
| 42 | 4.350 | RESEARCH | Idempotent incremental refresh design for $merge (high-water marks, delete handling) | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 43 | 4.350 | RESEARCH | Time Series Sharding Patterns | mongodb-time-series | dr | frontier | mongodb-cohort-e128bd27e4b1 | — |
| 44 | 4.350 | RESEARCH | change-stream-resume-token | kafka-source-connector | dr | frontier | mongodb-cohort-b00c6e9c0178 | — |
| 45 | 4.325 | RESEARCH | mongodbatlas_advanced_cluster Resource | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-f173c69ee97a | — |
| 46 | 4.325 | RESEARCH | Time series bucketing parameters: granularity, bucketMaxSpanSeconds, bucketRoundingSeconds | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 47 | 4.325 | RESEARCH | WiredTiger cache sizing and working-set fit | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-321ef5e25160 | — |
| 48 | 4.325 | RESEARCH | Multi-Cloud Global Clusters | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-7030217d35d1 | — |
| 49 | 4.325 | RESEARCH | Partitioner Strategies | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a04dd23fc577 | — |
| 50 | 4.300 | RESEARCH | Server Selection Algorithm | MongoDB Driver Internals | dr | covered | mongodb-cohort-67b8def68c5a | — |
| 51 | 4.300 | RESEARCH | FCV pinning and downgrade preservation window | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-ce1440cf3126 | — |
| 52 | 4.300 | RESEARCH | FCV unpinned too early | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-f8dad38f861e | — |
| 53 | 4.300 | RESEARCH | verification-modes | mongosync | dr | frontier | mongodb-cohort-6b0ef514c7df | — |
| 54 | 4.300 | RESEARCH | Embedding Pipelines | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-eac239cf87d4 | — |
| 55 | 4.300 | RESEARCH | Hybrid Search | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-71277350690d | — |
| 56 | 4.300 | RESEARCH | Atlas storage auto-scaling triggers, cooldowns and write blocking | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 57 | 4.300 | RESEARCH | WT_CACHE_FULL / Cache Pressure Troubleshooting | WiredTiger Storage Engine Internals | dr | frontier | mongodb-cohort-0a5c86f5c884 | — |
| 58 | 4.300 | RESEARCH | Row-Level Security Patterns | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-9eb6db80c07d | — |
| 59 | 4.300 | REFRESH | Atlas Flex Pricing and Flex-vs-Dedicated Break-Even | Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-526e32151244 | — |
| 60 | 4.300 | RESEARCH | Atlas Query Targeting alerts | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-67ae76bb4141 | — |
| 61 | 4.300 | RESEARCH | Atlas Search index sync lag and search-node sizing | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-9b0a0e06ee53 | — |
| 62 | 4.300 | RESEARCH | Cost Governance Guardrails (Resource Policies and IaC Cost Controls) | Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-88f6ca74e8c0 | — |
| 63 | 4.300 | RESEARCH | currentOp planSummary for running operations | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-ca60df035474 | — |
| 64 | 4.300 | RESEARCH | Disk IOPS Burst Credit Depletion Playbook | Atlas Triage Workflows | revisit | refresh-review | mongodb-cohort-ebfddb6584b7 | — |
| 65 | 4.275 | RESEARCH | Driver compatibility matrix (Java/Node/Python/.NET/Go) | MongoDB Upgrade Paths | dr | covered | mongodb-cohort-2a03c480ee30 | — |
| 66 | 4.275 | RESEARCH | Oplog Sizing | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-321ef5e25160 | — |
| 67 | 4.275 | RESEARCH | Unique and TTL index side effects on removal | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 68 | 4.275 | RESEARCH | Atlas Search Analyzers and Tokenizers | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-71277350690d | — |
| 69 | 4.275 | RESEARCH | Arbiter handling and PSA topology | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-f8dad38f861e | — |
| 70 | 4.275 | RESEARCH | Index filters (planCacheSetFilter) deprecation and migration to query settings | Operation rejection filters | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 71 | 4.275 | RESEARCH | Oplog minimum retention window and storage auto-scaling | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 72 | 4.275 | RESEARCH | Read concern available, secondary reads and orphaned documents | Covered queries on sharded collections | dr | frontier | mongodb-cohort-9343057e721a | — |
| 73 | 4.275 | RESEARCH | Trigger Error Handling and Suspension | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f09da64a2f6e | — |
| 74 | 4.275 | RESEARCH | Tenant Lifecycle Operations | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-9eb6db80c07d | — |
| 75 | 4.250 | RESEARCH | Working Set Sizing | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-321ef5e25160 | — |
| 76 | 4.250 | RESEARCH | Blocking sort memory limit and allowDiskUse | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-99762008d157 | — |
| 77 | 4.250 | RESEARCH | Oplog window overflow | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-9343057e721a | — |
| 78 | 4.250 | RESEARCH | Tenant Isolation Models | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-9eb6db80c07d | — |
| 79 | 4.250 | RESEARCH | analyzeShardKey workload sampling | Shard key selection for query isolation | dr | frontier | mongodb-cohort-0243ade22f9d | — |
| 80 | 4.250 | RESEARCH | Atlas Live Migration | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-f1ebe93a2c8b | — |
| 81 | 4.250 | RESEARCH | Atlas Query Profiler and slow-ops logs for shape discovery | Operation rejection filters | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 82 | 4.250 | RESEARCH | majority commit point mechanics | Read Concern Levels | dr | frontier | mongodb-cohort-9343057e721a | — |
| 83 | 4.250 | RESEARCH | Oplog capacity for initial sync, live migration and bulk loads | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-9343057e721a | — |
| 84 | 4.250 | RESEARCH | Ops Manager High Availability | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-22646bcd15df | — |
| 85 | 4.250 | RESEARCH | Org and Project Governance | MongoDB Security Architecture | dr | frontier | mongodb-cohort-b0e4f880a1a3 | — |
| 86 | 4.250 | RESEARCH | Query settings: index hints and queryFramework (persistent query settings) | Operation rejection filters | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 87 | 4.250 | RESEARCH | setQuerySettings index hints and queryFramework | Operation rejection filters | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 88 | 4.250 | RESEARCH | Snapshot reads (atClusterTime) and history window sizing on secondaries | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-da6be74d8a76 | — |
| 89 | 4.250 | RESEARCH | Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 90 | 4.250 | RESEARCH | Time series backfill ordering and batching | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 91 | 4.250 | RESEARCH | Two-phase write protocol and writes without the shard key | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-2e478e8e7c3f | — |
| 92 | 4.250 | RESEARCH | Resume-from-last-key pattern for killed cursors | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 93 | 4.250 | REFRESH | MongoDB Replication | MongoDB Expert Knowledge | revisit | refresh-review | mongodb-cohort-705afd785fe1 | — |
| 94 | 4.250 | RESEARCH | Distributed Sharded Transactions | MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 95 | 4.250 | RESEARCH | Forcing plans with hint and internal query knobs | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-67ae76bb4141 | — |
| 96 | 4.250 | RESEARCH | Keyset pagination with compound sort keys | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-67ae76bb4141 | — |
| 97 | 4.250 | RESEARCH | Replica Set Node Topology Cost | Atlas Cluster Topology and Tier Economics | dr | covered | mongodb-cohort-526e32151244 | — |
| 98 | 4.250 | RESEARCH | Sharded Cluster Cost Economics | Atlas Cluster Topology and Tier Economics | dr | covered | mongodb-cohort-526e32151244 | — |
| 99 | 4.250 | RESEARCH | Targeted vs scatter-gather shard routing in explain | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-7ab2e09cc5a9 | — |
| 100 | 4.250 | RESEARCH | Transaction Anti-Patterns | MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 101 | 4.225 | RESEARCH | Balancer data-size policy and zone-aware migration | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-1d6ef7b4932c | — |
| 102 | 4.225 | RESEARCH | Batch Writes and Idempotency | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a04dd23fc577 | — |
| 103 | 4.225 | RESEARCH | Cloud Run Atlas Connection Pooling | MongoDB Atlas on GCP | dr | covered | mongodb-cohort-2a03c480ee30 | — |
| 104 | 4.225 | RESEARCH | Connection Pooling Strategies | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-eec7f143c4d7 | — |
| 105 | 4.225 | RESEARCH | exactly-once-semantics | CDC-patterns | dr | frontier | mongodb-cohort-642e05e32e3c | — |
| 106 | 4.225 | RESEARCH | startup-mode-copy-existing | kafka-source-connector | dr | frontier | mongodb-cohort-b00c6e9c0178 | — |
| 107 | 4.225 | RESEARCH | Vector index memory sizing and quantization trade-offs on Search Nodes | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-eac239cf87d4 | — |
| 108 | 4.225 | RESEARCH | Vector Quantization | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-eac239cf87d4 | — |
| 109 | 4.225 | RESEARCH | Watermarks and Late-Event Tolerance | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-8cacc610d606 | — |
| 110 | 4.225 | RESEARCH | write-model-strategies | kafka-sink-connector; mongodb-kafka-connector | dr | frontier | mongodb-cohort-acd9dfcd8eeb | — |
| 111 | 4.225 | RESEARCH | Atlas disk write-blocking thresholds and recovery | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 112 | 4.200 | RESEARCH | Unique, TTL and shard-key indexes that read as unused | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-dc0d0485fbfe | — |
| 113 | 4.200 | RESEARCH | outbox-pattern | CDC-patterns | dr | frontier | mongodb-cohort-642e05e32e3c | — |
| 114 | 4.200 | RESEARCH | hasNextPage without computing total pages | Total count strategies for paginated UIs | dr | frontier | mongodb-cohort-92f18235288a | — |
| 115 | 4.200 | RESEARCH | Blockstore and Snapshot Stores | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-22646bcd15df | — |
| 116 | 4.200 | RESEARCH | Online Archive Data Access and Data Seek Query Cost Model | Partition Fields | dr | frontier | mongodb-cohort-715247b3e8b5 | — |
| 117 | 4.200 | RESEARCH | Atlas Projects as Hard Isolation | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-9eb6db80c07d | — |
| 118 | 4.200 | RESEARCH | Planner plan scoring and EOF bonus | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-d49f86c79017 | — |
| 119 | 4.175 | RESEARCH | Compound shard-key prefix targeting | Shard key selection for query isolation | dr | frontier | mongodb-cohort-0243ade22f9d | — |
| 120 | 4.175 | RESEARCH | Backup Verification and Tabletop Exercises | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-0e7a6f84ee61 | — |
| 121 | 4.175 | RESEARCH | Index build commit quorum (commitQuorum and setIndexCommitQuorum) | Rolling index builds | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 122 | 4.175 | RESEARCH | Leading-prefix redundant index detection | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 123 | 4.175 | RESEARCH | Multikey indexes and index-provided sort order | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 124 | 4.175 | RESEARCH | Multikey indexes and sort provision (multikeyPaths) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 125 | 4.175 | RESEARCH | Oplog sizing and embedded-verifier memory for migrations | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-da6be74d8a76 | — |
| 126 | 4.175 | RESEARCH | Per-node and per-shard $indexStats aggregation across replica sets and shards | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-705afd785fe1 | — |
| 127 | 4.175 | RESEARCH | TemporarilyUnavailable and TransactionTooLargeForCache errors | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-cf9a0f8ed75e | — |
| 128 | 4.175 | RESEARCH | Atlas Search index behaviour with $out versus $merge targets | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-71277350690d | — |
| 129 | 4.175 | RESEARCH | Atlas Search index lifecycle on $out and $merge targets | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-71277350690d | — |
| 130 | 4.175 | RESEARCH | Coordinator failure recovery | Distributed Sharded Transactions | dr | frontier | mongodb-cohort-fdacc8310b4f | — |
| 131 | 4.175 | RESEARCH | WiredTiger cache pressure and write tickets during index builds | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-e71ad6d99f1d | — |
| 132 | 4.175 | RESEARCH | WiredTiger history store and majority commit point cache pressure | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 133 | 4.175 | RESEARCH | Cross-DC App DB Placement | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-22646bcd15df | — |
| 134 | 4.175 | RESEARCH | mongot replication lag, oplog window and index rebuild cost | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-31cfc547f721 | — |
| 135 | 4.150 | RESEARCH | Atlas Cloud Backup (snapshots) | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-0e7a6f84ee61 | — |
| 136 | 4.150 | RESEARCH | Compound-index prefix and sort-direction compatibility | Collation and index sort compatibility | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 137 | 4.150 | RESEARCH | Reading indexed `$or` plans with explain | Compound index vs index union for $or | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 138 | 4.150 | RESEARCH | Retryable Reads | MongoDB Driver Internals | dr | frontier | mongodb-cohort-cf9a0f8ed75e | — |
| 139 | 4.150 | RESEARCH | Atlas Tier Selection | MongoDB Performance Benchmarking | dr | frontier | mongodb-cohort-da6be74d8a76 | — |
| 140 | 4.150 | RESEARCH | Balancer tuning and chunk migration cost | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-ebfddb6584b7 | — |
| 141 | 4.150 | RESEARCH | Connectivity Troubleshooting | MongoDB KB Articles | dr | frontier | mongodb-cohort-69e987c81008 | — |
| 142 | 4.150 | RESEARCH | Query shape and queryShapeHash stability | Operation rejection filters | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 143 | 4.150 | RESEARCH | Query shapes and queryShapeHash stability | Operation rejection filters | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 144 | 4.150 | RESEARCH | Schema Design for Multi-Tenancy | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-5682e98c0453 | — |
| 145 | 4.150 | RESEARCH | WiredTiger checkpoints and checkpoint duration | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 146 | 4.150 | RESEARCH | Commit quorum and the vote-to-commit point of no return | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-e71ad6d99f1d | — |
| 147 | 4.150 | RESEARCH | DLQ-error-handling | kafka-sink-connector; mongodb-kafka-connector | dr | frontier | mongodb-cohort-acd9dfcd8eeb | — |
| 148 | 4.150 | RESEARCH | Keyset (resume) pagination for restartable cursors | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 149 | 4.150 | RESEARCH | Terraform effective fields and auto-scaling drift | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-236f7c7ed9cf | — |
| 150 | 4.150 | REFRESH | mongodb-schema-design | MongoDB Expert Knowledge | revisit | refresh-review | mongodb-cohort-641b3decfe43 | — |
| 151 | 4.150 | RESEARCH | Atlas Vector Search RAM sizing and automatic quantization | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-eac239cf87d4 | — |
| 152 | 4.150 | RESEARCH | Vector Search Quantization and Embedding Storage Cost | Atlas Cluster Topology and Tier Economics | dr | covered | mongodb-cohort-27781ed3f782 | — |
| 153 | 4.125 | RESEARCH | Read Preference | MongoDB Connection String URI | dr | frontier | mongodb-cohort-6f6a12e41dfc | — |
| 154 | 4.125 | RESEARCH | snapshot read concern | Read Concern Levels | dr | frontier | mongodb-cohort-705afd785fe1 | — |
| 155 | 4.125 | RESEARCH | DNS SRV Discovery | MongoDB Driver Internals | dr | frontier | mongodb-cohort-f5625c57d0b7 | — |
| 156 | 4.125 | RESEARCH | Hashed shard-key write distribution and local index locality | Random-key (hashed/UUID) index insert behavior | dr | frontier | mongodb-cohort-27b1229cf1bf | — |
| 157 | 4.125 | RESEARCH | read concern in sharding | Read Concern Levels | dr | frontier | mongodb-cohort-705afd785fe1 | — |
| 158 | 4.125 | RESEARCH | terminateSecondaryReadsOnOrphanCleanup and QueryPlanKilled 175 | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 159 | 4.125 | RESEARCH | Co-located vs dedicated mongot decision thresholds and failure modes | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-31cfc547f721 | — |
| 160 | 4.125 | RESEARCH | Orphaned documents and range deletion | Covered queries on sharded collections | dr | frontier | mongodb-cohort-74cd39f19180 | — |
| 161 | 4.125 | RESEARCH | Inline user-facing querySettings (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 162 | 4.125 | RESEARCH | Elasticsearch-to-Atlas Search migration and dual-run cost | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-31cfc547f721 | — |
| 163 | 4.100 | RESEARCH | Detecting inconsistent indexes across shards | Rolling index builds | dr | frontier | mongodb-cohort-c5470a8d6ad1 | — |
| 164 | 4.100 | RESEARCH | Embedding generation and reranking token spend in retrieval TCO | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-6505e3f3ea07 | — |
| 165 | 4.100 | RESEARCH | Atlas independent shard scaling and auto-scaling | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-2e478e8e7c3f | — |
| 166 | 4.100 | RESEARCH | Atlas independent shard scaling and per-shard auto-scaling | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 167 | 4.100 | RESEARCH | Multiplanning storms after a plan cache flush | Replanning loops and replanReason | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 168 | 4.100 | RESEARCH | Gen1 versus Gen2 IOPS provisioning and instance-level EBS/VM IOPS caps | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-7b84bed0b7eb | — |
| 169 | 4.100 | RESEARCH | Plan cache key and $in length (classic vs SBE) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 170 | 4.100 | RESEARCH | Atlas Performance Advisor index suggestions | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds; MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-b786132ea6d4 | — |
| 171 | 4.100 | RESEARCH | Pipeline Optimization | MongoDB Aggregation Pipeline | revisit | refresh-review | mongodb-cohort-cde8f5008414 | — |
| 172 | 4.100 | RESEARCH | Right-sizing Atlas tier from cache and CPU metrics | Query Efficiency as a Cost Lever; Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-3bc7bd71277a | — |
| 173 | 4.100 | RESEARCH | Sort direction and compound index prefix rules | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-b786132ea6d4 | — |
| 174 | 4.075 | RESEARCH | Rolling replica-set upgrade | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-15b633636009 | — |
| 175 | 4.075 | RESEARCH | $indexStats usage statistics and their reset conditions | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 176 | 4.075 | RESEARCH | Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes) | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 177 | 4.075 | RESEARCH | Time Series Collection Creation (timeField, metaField, granularity) | mongodb-time-series | dr | frontier | mongodb-cohort-e128bd27e4b1 | — |
| 178 | 4.075 | RESEARCH | Atlas compute auto-scaling for sharded clusters | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-1d6ef7b4932c | — |
| 179 | 4.075 | RESEARCH | Atlas Custom Database Roles | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-03f16747a38f | — |
| 180 | 4.075 | RESEARCH | Balancer, chunk migration and jumbo chunk remediation | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 181 | 4.075 | RESEARCH | Commit quorum and votingMembers | Resumable index builds | dr | frontier | mongodb-cohort-74076c97a7f3 | — |
| 182 | 4.075 | RESEARCH | Orphaned documents and read concern available versus local | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-15b633636009 | — |
| 183 | 4.075 | RESEARCH | Safe index removal: locks, rollback and regression checks | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-15b633636009 | — |
| 184 | 4.075 | RESEARCH | SHARDING_FILTER stage and chunkSkips | Covered queries on sharded collections | dr | frontier | mongodb-cohort-74cd39f19180 | — |
| 185 | 4.075 | RESEARCH | Atlas Admin API Date Versioned Media Types | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-236f7c7ed9cf | — |
| 186 | 4.075 | RESEARCH | Atlas Key Rotation AKV | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-dc748bec19fd | — |
| 187 | 4.075 | RESEARCH | Atlas Search index rebuild after migration | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-31cfc547f721 | — |
| 188 | 4.075 | RESEARCH | readConcern available on sharded clusters | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 189 | 4.075 | RESEARCH | Terraform Provider v2 Migration | MongoDB Atlas Terraform Provider | dr | frontier | mongodb-cohort-236f7c7ed9cf | — |
| 190 | 4.075 | RESEARCH | Atlas Networking IaC | MongoDB Atlas Terraform Provider | dr | frontier | mongodb-cohort-7ee309139bcc | — |
| 191 | 4.075 | RESEARCH | WiredTiger cache sizing and memory fragmentation | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-da6be74d8a76 | — |
| 192 | 4.075 | RESEARCH | Change-stream resumability | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-f8dad38f861e | — |
| 193 | 4.075 | RESEARCH | Sampling CE accuracy under sparse sample matches | ceSource cardinality estimation (sampling vs heuristics) | dr | frontier | mongodb-cohort-bae29937ea6d | — |
| 194 | 4.075 | RESEARCH | Workload Identity Federation Atlas | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-b74fe6f94c37 | — |
| 195 | 4.050 | RESEARCH | Atlas Alerts | MongoDB Monitoring and Observability | dr | frontier | mongodb-cohort-8db54400cdbf | — |
| 196 | 4.050 | RESEARCH | Authentication Mechanisms | MongoDB Connection String URI | dr | frontier | mongodb-cohort-2d92638e9112 | — |
| 197 | 4.050 | RESEARCH | TTL and Automatic Bucket Deletion | mongodb-time-series | dr | frontier | mongodb-cohort-e128bd27e4b1 | — |
| 198 | 4.050 | RESEARCH | Custom Analyzers | MongoDB Atlas Search | dr | frontier | mongodb-cohort-3aa797450c89 | — |
| 199 | 4.050 | RESEARCH | ESR guideline and $in placement in compound indexes | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 200 | 4.050 | RESEARCH | Read and Write Concerns | MongoDB Driver Internals | dr | frontier | mongodb-cohort-15b633636009 | — |
| 201 | 4.050 | RESEARCH | WiredTiger checkpoints and dirty-page write cost | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-ebfddb6584b7 | — |
| 202 | 4.050 | RESEARCH | Atlas Search Nodes cost floor and co-located versus dedicated search | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-431c1cbaf986 | — |
| 203 | 4.050 | RESEARCH | Azure Private Link for Atlas | MongoDB Atlas Multi-Cloud; MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-fc7e308a4a68 | — |
| 204 | 4.050 | RESEARCH | bulk-write-ordering | kafka-sink-connector | dr | frontier | mongodb-cohort-acd9dfcd8eeb | — |
| 205 | 4.050 | RESEARCH | Cluster-to-Cluster Sync Phases | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-1ea1a94ccad7 | — |
| 206 | 4.050 | RESEARCH | Dead Letter Queue (DLQ) | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-8cacc610d606 | — |
| 207 | 4.050 | RESEARCH | GCP Private Service Connect for Atlas | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-fc7e308a4a68 | — |
| 208 | 4.050 | RESEARCH | Service Account OAuth 2.0 Authentication | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-03f16747a38f | — |
| 209 | 4.050 | RESEARCH | Chunk migration commit, range deleter and orphan cleanup internals | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 210 | 4.050 | RESEARCH | Application-level dual-write migration pattern | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 211 | 4.050 | RESEARCH | Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-ebfddb6584b7 | — |
| 212 | 4.050 | RESEARCH | Local Mode and Air-Gap Deployments | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-50c2ce240545 | — |
| 213 | 4.050 | RESEARCH | BI Connector EOL Migration | MongoDB BI Connector and SQL Access | dr | frontier | mongodb-cohort-c84c26fc913e | — |
| 214 | 4.050 | RESEARCH | $group accumulator memory caps | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-f08967f01b08 | — |
| 215 | 4.050 | RESEARCH | Billing Alerts and Budget Controls | Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-2f06cfb2b7c0 | — |
| 216 | 4.050 | RESEARCH | Compound index vs index union for $or | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-00acf5133e37 | — |
| 217 | 4.050 | RESEARCH | DISTINCT_SCAN for distinct command | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-d49f86c79017 | — |
| 218 | 4.050 | RESEARCH | Equality-Sort-Range index ordering | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-00acf5133e37 | — |
| 219 | 4.050 | RESEARCH | ERS exception for selective range predicates | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-00acf5133e37 | — |
| 220 | 4.050 | RESEARCH | explain() executionStats reading | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-d49f86c79017 | — |
| 221 | 4.050 | RESEARCH | Multi-Document Transactions | MongoDB Driver Internals; MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 222 | 4.050 | RESEARCH | Private endpoints and VPC peering transfer charges | Atlas Cluster Topology and Tier Economics; Multi-Region and Cross-Cloud Data Transfer Costs | dr | covered | mongodb-cohort-2b6d35d6c562 | — |
| 223 | 4.050 | RESEARCH | SHARDING_FILTER orphan filtering | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-7ab2e09cc5a9 | — |
| 224 | 4.025 | RESEARCH | Hashed, ranged and compound hashed shard keys | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 225 | 4.025 | RESEARCH | Zone sharding and region-aware shard keys | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 226 | 4.025 | RESEARCH | Atlas Vector Search numCandidates tuning and recall measurement against ENN | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-6505e3f3ea07 | — |
| 227 | 4.025 | RESEARCH | Azure Functions Atlas Connection Pooling | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-eec7f143c4d7 | — |
| 228 | 4.025 | RESEARCH | Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis) | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 229 | 4.025 | RESEARCH | Atlas Stream Processing streaming materialized views | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 230 | 4.025 | RESEARCH | Reducing shard count and unsharding collections on Atlas | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 231 | 4.000 | RESEARCH | Atlas Metrics and Dashboards | MongoDB Monitoring and Observability | dr | frontier | mongodb-cohort-8db54400cdbf | — |
| 232 | 4.000 | RESEARCH | Pulumi mongodbatlas Provider | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-f173c69ee97a | — |
| 233 | 4.000 | RESEARCH | initial-sync-and-cdc | mongosync | dr | frontier | mongodb-cohort-1ea1a94ccad7 | — |
| 234 | 4.000 | RESEARCH | Atlas Auth Tier Feature Matrix M0 Flex M10 | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-1aa648d70e12 | — |
| 235 | 4.000 | RESEARCH | Balancer windows and per-collection balancing control | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 236 | 4.000 | RESEARCH | Destination temporary scaling and post-cutover right-sizing | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-1aa648d70e12 | — |
| 237 | 4.000 | RESEARCH | dropIndexes locking and in-flight query behavior | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 238 | 4.000 | RESEARCH | Hidden indexes as a safe drop trial | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 239 | 4.000 | RESEARCH | mongod diagnostic log slow-query format and slowOpSampleRate | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 240 | 4.000 | RESEARCH | namespace-filtering | mongosync | dr | frontier | mongodb-cohort-6b0ef514c7df | — |
| 241 | 4.000 | RESEARCH | oplog-window-sizing | mongosync | dr | frontier | mongodb-cohort-1aa648d70e12 | — |
| 242 | 4.000 | RESEARCH | Disk pre-warming SOP (Cookie 7.0→8.0 lesson) | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-7c7aab86e51d | — |
| 243 | 4.000 | RESEARCH | Per-shard disk IOPS and storage constraints | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-9506d4f6a2ef | — |
| 244 | 4.000 | RESEARCH | reverse-sync-cutover | mongosync | dr | frontier | mongodb-cohort-1ea1a94ccad7 | — |
| 245 | 4.000 | RESEARCH | Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-431c1cbaf986 | — |
| 246 | 4.000 | RESEARCH | Validating AI-suggested indexes with explain | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-c554dd99dde4 | — |
| 247 | 3.975 | RESEARCH | Redundant (prefix) index detection for compound indexes | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 248 | 3.975 | RESEARCH | SRV DNS Seedlist Format | MongoDB Connection String URI | dr | frontier | mongodb-cohort-8450487cdc7b | — |
| 249 | 3.975 | RESEARCH | Application-thread eviction and cache stalls | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 250 | 3.975 | RESEARCH | Driver mismatch failure mode | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-eec7f143c4d7 | — |
| 251 | 3.975 | RESEARCH | Flex versus Dedicated boundary: ops-per-second pricing and missing features | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-f959bb6a503b | — |
| 252 | 3.975 | RESEARCH | metaField cardinality and active-bucket count | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 253 | 3.975 | RESEARCH | MongoDB Node.js driver pool sizing under Lambda concurrency | Lambda MongoDB Driver Pattern | dr | frontier | mongodb-cohort-1aa648d70e12 | — |
| 254 | 3.975 | RESEARCH | Partition Fields | MongoDB Atlas Online Archive | dr | frontier | mongodb-cohort-252dc4668191 | — |
| 255 | 3.975 | RESEARCH | serverStatus bucketCatalog and collStats timeseries counters | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 256 | 3.975 | RESEARCH | TLS/SSL Configuration | MongoDB Connection String URI | dr | frontier | mongodb-cohort-8450487cdc7b | — |
| 257 | 3.975 | RESEARCH | Source Oplog Window Sizing for Migration | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-b62cb9f27cd5 | — |
| 258 | 3.975 | RESEARCH | moveCollection and unshardCollection | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 259 | 3.975 | RESEARCH | Cross-cloud application-tier placement and Atlas internet egress | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 260 | 3.975 | RESEARCH | mongosync reversible sync and the rollback window | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-1fdc93c7569e | — |
| 261 | 3.975 | RESEARCH | PSC Port-Mapped Architecture | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-687aed0d21fd | — |
| 262 | 3.950 | RESEARCH | Hashed versus ranged shard-key tradeoffs | Shard key selection for query isolation | dr | frontier | mongodb-cohort-0243ade22f9d | — |
| 263 | 3.950 | RESEARCH | majority read concern | Read Concern Levels | dr | frontier | mongodb-cohort-1fdc93c7569e | — |
| 264 | 3.950 | RESEARCH | WiredTiger block reuse, file fragmentation and freeStorageSize | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 265 | 3.950 | RESEARCH | Write amplification and cache cost of unused indexes | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-f959bb6a503b | — |
| 266 | 3.950 | RESEARCH | Connection Metrics | MongoDB Monitoring and Observability | dr | frontier | mongodb-cohort-8db54400cdbf | — |
| 267 | 3.950 | RESEARCH | Plan cache flushes on index DDL | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 268 | 3.950 | RESEARCH | Application Database (App DB) | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-50c2ce240545 | — |
| 269 | 3.950 | RESEARCH | Archive and TTL data lifecycle followed by compaction | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 270 | 3.950 | RESEARCH | Automation Agent | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-50c2ce240545 | — |
| 271 | 3.950 | RESEARCH | MongoDB Agent (Automation, Monitoring, Backup) | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-1482bd9b61d6 | — |
| 272 | 3.950 | RESEARCH | Replica set oplog window and initial sync | Rolling index builds | dr | frontier | mongodb-cohort-1fdc93c7569e | — |
| 273 | 3.950 | RESEARCH | Zone sharding for hardware-tiered shards | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-b62cb9f27cd5 | — |
| 274 | 3.950 | RESEARCH | Zone sharding for tiered hardware (hot, warm, cold) | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-b62cb9f27cd5 | — |
| 275 | 3.950 | RESEARCH | Atlas AWS IAM Database Auth | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-205df5e830d6 | — |
| 276 | 3.950 | RESEARCH | Atlas Live Migration pull versus push versus standalone mongosync selection | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-1fdc93c7569e | — |
| 277 | 3.950 | RESEARCH | Azure Key Vault Atlas BYOK | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-f912d5a4c6c7 | — |
| 278 | 3.950 | RESEARCH | Google Cloud KMS BYOK | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-f912d5a4c6c7 | — |
| 279 | 3.950 | RESEARCH | Secrets Management | MongoDB Security Architecture | dr | frontier | mongodb-cohort-2b89fbc3d8fa | — |
| 280 | 3.950 | RESEARCH | VPC Peering GCP Atlas | Global AI Hub Research Corpus | dr | frontier | mongodb-cohort-a65c6320d64b | — |
| 281 | 3.950 | RESEARCH | Multi-planner trial period and candidate plan ranking | Replanning loops and replanReason | dr | frontier | mongodb-cohort-6e1e9ef33885 | — |
| 282 | 3.950 | RESEARCH | Zone sharding and Global Cluster shard keys | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 283 | 3.950 | RESEARCH | PSC Terraform GCP | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-236f7c7ed9cf | — |
| 284 | 3.950 | RESEARCH | Schema Design for Storage Cost | Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-2f06cfb2b7c0 | — |
| 285 | 3.925 | RESEARCH | Hashed shard keys and index support | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 286 | 3.925 | RESEARCH | Config server / shards / mongos upgrade sequence | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-0dfda3ebd6a5 | — |
| 287 | 3.925 | RESEARCH | Wire Protocol Compression | MongoDB Connection String URI | dr | frontier | mongodb-cohort-b9e8cc9dff41 | — |
| 288 | 3.925 | RESEARCH | mongos version skew failure | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-0dfda3ebd6a5 | — |
| 289 | 3.925 | RESEARCH | Index filters and query settings versus hidden indexes | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 290 | 3.925 | RESEARCH | Prometheus Integration | MongoDB Monitoring and Observability | dr | frontier | mongodb-cohort-8db54400cdbf | — |
| 291 | 3.925 | RESEARCH | Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete) | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 292 | 3.925 | RESEARCH | Per-shard compute auto-scaling rules and limits on Atlas | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-1d6ef7b4932c | — |
| 293 | 3.925 | RESEARCH | PSA topology stepdown failure | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-41d59b577242 | — |
| 294 | 3.925 | RESEARCH | Reverse sync and rollback-window economics | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-b62cb9f27cd5 | — |
| 295 | 3.925 | RESEARCH | SQL-to-MQL Translation | MongoDB BI Connector and SQL Access | dr | frontier | mongodb-cohort-c84c26fc913e | — |
| 296 | 3.925 | RESEARCH | Per-shard IOPS and Gen2 storage on Atlas | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-9506d4f6a2ef | — |
| 297 | 3.925 | RESEARCH | Partition Field Immutability and Merge-Delete-Recreate Migration | Partition Fields | dr | frontier | mongodb-cohort-1e99b9bf1966 | — |
| 298 | 3.925 | RESEARCH | MongoDB cache-pressure monitor and ticket admission | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-3269334e5d34 | — |
| 299 | 3.925 | RESEARCH | Lexical Prefilters for Vector Search | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-6505e3f3ea07 | — |
| 300 | 3.900 | RESEARCH | Cache stampede protection: leases, request coalescing, TTL jitter | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 301 | 3.900 | RESEARCH | $out-based time series rewrite and cutover | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 302 | 3.900 | RESEARCH | Partition Field Leftmost-Prefix Ordering | Partition Fields | dr | frontier | mongodb-cohort-1e99b9bf1966 | — |
| 303 | 3.900 | RESEARCH | Reshard to the same key for adding and removing shards | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 304 | 3.900 | RESEARCH | Live Migration to Atlas via mongosync | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-38fae6930416 | — |
| 305 | 3.900 | RESEARCH | Atlas Query Profiler and Performance Advisor | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-67ae76bb4141 | — |
| 306 | 3.900 | RESEARCH | SBE vs classic engine defaults | MongoDB 8.0 performance changes & read-path regressions vs 7.0 | revisit | refresh-review | mongodb-cohort-6e1e9ef33885 | — |
| 307 | 3.875 | RESEARCH | Dedicated Search Node storage and compute sizing | Atlas Search index sync lag and search-node sizing | dr | frontier | mongodb-cohort-1e0eea1b3fda | — |
| 308 | 3.875 | RESEARCH | mongosync-state-machine | mongosync | dr | frontier | mongodb-cohort-6b0ef514c7df | — |
| 309 | 3.875 | RESEARCH | Plan cache entry lifecycle: Inactive and Active entries and works growth | Replanning loops and replanReason | dr | frontier | mongodb-cohort-6e1e9ef33885 | — |
| 310 | 3.875 | RESEARCH | serverStatus metrics.query.planCache counters | Replanning loops and replanReason | dr | frontier | mongodb-cohort-e515b403d48b | — |
| 311 | 3.875 | RESEARCH | Standalone mongosync hosting and sizing | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-1e0eea1b3fda | — |
| 312 | 3.875 | RESEARCH | Atlas IdP Group to Role Mapping | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-03f16747a38f | — |
| 313 | 3.875 | RESEARCH | Time series bucket reopening (archived and query-based) | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 314 | 3.875 | RESEARCH | Continuous Backup with PITR | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-1482bd9b61d6 | — |
| 315 | 3.875 | RESEARCH | mongosync and live-migration oplog capacity planning | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-437048a92799 | — |
| 316 | 3.875 | RESEARCH | RBAC and Connection Security | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-03f16747a38f | — |
| 317 | 3.875 | RESEARCH | Atlas Automated Embedding economics (Voyage tokens vs external embedding service) | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-6505e3f3ea07 | — |
| 318 | 3.875 | REFRESH | MongoDB Monitoring and Observability | MongoDB Expert Knowledge | revisit | refresh-review | mongodb-cohort-4c4a60fe08de | — |
| 319 | 3.850 | RESEARCH | Oplog window sizing | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-1e0eea1b3fda | — |
| 320 | 3.850 | RESEARCH | Faceted Search | MongoDB Atlas Search | dr | frontier | mongodb-cohort-431c1cbaf986 | — |
| 321 | 3.850 | RESEARCH | numCandidates tuning for quantized HNSW indexes | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-3bde70611ed4 | — |
| 322 | 3.850 | RESEARCH | Count consistency under concurrent writes | Total count strategies for paginated UIs | dr | frontier | mongodb-cohort-437048a92799 | — |
| 323 | 3.850 | RESEARCH | Cross-Region Snapshot Copy | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-0e7a6f84ee61 | — |
| 324 | 3.850 | RESEARCH | heartbeat-configuration | kafka-source-connector | dr | frontier | mongodb-cohort-b00c6e9c0178 | — |
| 325 | 3.850 | RESEARCH | Hidden and priority-0 members during maintenance | Rolling index builds | dr | frontier | mongodb-cohort-0decd84b4936 | — |
| 326 | 3.850 | RESEARCH | Loose versus tight bucket predicates | Bucket-level predicate rewriting for measurement operators | dr | frontier | mongodb-cohort-ded7cec0af2e | — |
| 327 | 3.850 | RESEARCH | Approximation pattern for write-heavy computed counters | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 328 | 3.850 | RESEARCH | Atlas Backup IaC | MongoDB Atlas Terraform Provider | dr | frontier | mongodb-cohort-d5cef667ffc4 | — |
| 329 | 3.850 | RESEARCH | Atlas Query Insights: Query Shape Insights and Namespace Insights | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-e515b403d48b | — |
| 330 | 3.850 | RESEARCH | Covered distinct and $group on sharded collections | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 331 | 3.850 | RESEARCH | moveCollection and collection isolation on dedicated shards | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-2daa30f3ff56 | — |
| 332 | 3.850 | RESEARCH | Relational-to-MongoDB migration cost (Relational Migrator) | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-f959bb6a503b | — |
| 333 | 3.850 | RESEARCH | TLS and OCSP | MongoDB Driver Internals | dr | frontier | mongodb-cohort-f5625c57d0b7 | — |
| 334 | 3.850 | RESEARCH | UUIDv4 versus UUIDv7 key locality | Random-key (hashed/UUID) index insert behavior | dr | frontier | mongodb-cohort-7a36032fa829 | — |
| 335 | 3.850 | RESEARCH | WiredTiger cache warm-up | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-7c7aab86e51d | — |
| 336 | 3.850 | RESEARCH | Hybrid search ($rankFusion) vs two-system fusion TCO | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-f959bb6a503b | — |
| 337 | 3.850 | RESEARCH | Rolling resync (initial sync) as a space-reclaim technique on Atlas | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-1ea1a94ccad7 | — |
| 338 | 3.850 | RESEARCH | Atlas Vector Search Automated Embedding rate limits | Atlas AI Services Pricing (Agent Engine and Voyage AI); Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-27781ed3f782 | — |
| 339 | 3.850 | RESEARCH | Autoscaling tier bounds as cost ceiling | Atlas Pricing Programs, Cost Governance and TCO; Cost Governance Guardrails (Resource Policies and IaC Cost Controls) | dr | covered | mongodb-cohort-2f06cfb2b7c0 | — |
| 340 | 3.850 | RESEARCH | Entra ID group overage in Atlas | Atlas Identity Federation and Resource Policy Boundaries | revisit | refresh-review | mongodb-cohort-b74fe6f94c37 | — |
| 341 | 3.850 | RESEARCH | explain multiKeyPaths interpretation | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-c554dd99dde4 | — |
| 342 | 3.850 | RESEARCH | Explain verbosity modes | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-c554dd99dde4 | — |
| 343 | 3.850 | RESEARCH | maxTimeMS (Server-side Operation Timeout) | Client Side Operations Timeout (CSOT) | revisit | refresh-review | mongodb-cohort-f7898c0e7b37 | — |
| 344 | 3.850 | RESEARCH | Query Efficiency as a Cost Lever | Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-2f06cfb2b7c0 | — |
| 345 | 3.850 | RESEARCH | Self-Managed MongoDB vs Atlas TCO | Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-d969be1abbd9 | — |
| 346 | 3.850 | RESEARCH | Shard key selection for query isolation | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-e2f2efd61e49 | — |
| 347 | 3.825 | RESEARCH | Journal (Write-Ahead Log) | WiredTiger Storage Engine Internals | dr | frontier | mongodb-cohort-0a5c86f5c884 | — |
| 348 | 3.825 | RESEARCH | mongos version skew rules | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-0dfda3ebd6a5 | — |
| 349 | 3.825 | RESEARCH | Atlas analytics nodes and read preference tags | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 350 | 3.825 | RESEARCH | Compass Schema Analysis | MongoDB Compass | dr | frontier | mongodb-cohort-4451fc8be02a | — |
| 351 | 3.825 | RESEARCH | Read vs Write Distribution | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-1d798a0d85d1 | — |
| 352 | 3.825 | RESEARCH | Workload isolation with tagged secondaries and Atlas analytics nodes | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 353 | 3.825 | RESEARCH | Terraform Drift Detection | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-1d77b14f4cb1 | — |
| 354 | 3.825 | RESEARCH | defaultMaxTimeMS cluster-level read timeout | Operation rejection filters | dr | frontier | mongodb-cohort-2ccf282e3940 | — |
| 355 | 3.825 | RESEARCH | Multi-Cloud Failure Modes | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-7030217d35d1 | — |
| 356 | 3.825 | RESEARCH | Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates) | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-2350070cfddf | — |
| 357 | 3.825 | RESEARCH | atlas-live-migration-comparison | mongosync | dr | frontier | mongodb-cohort-6b0ef514c7df | — |
| 358 | 3.825 | RESEARCH | Backup Compliance Policy One-Way | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-292dd656b5d2 | — |
| 359 | 3.825 | RESEARCH | Dedicated Search Nodes two-node cost floor versus coupled mongot | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-431c1cbaf986 | — |
| 360 | 3.825 | RESEARCH | KMS Failsafe Behavior Atlas | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-f912d5a4c6c7 | — |
| 361 | 3.825 | RESEARCH | KMS Unavailability Failsafe | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-f912d5a4c6c7 | — |
| 362 | 3.825 | RESEARCH | Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-1e0eea1b3fda | — |
| 363 | 3.800 | RESEARCH | Atlas Flex Unsupported Features | MongoDB Atlas Flex and Serverless Tiers | dr | frontier | mongodb-cohort-3218ab1d6cd5 | — |
| 364 | 3.800 | RESEARCH | Replication Oplog Window alerts and Oplog GB/Hour monitoring | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-437048a92799 | — |
| 365 | 3.800 | RESEARCH | Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom) | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-437048a92799 | — |
| 366 | 3.800 | RESEARCH | Atlas Search nodes in sharded clusters | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-1ffb989b662b | — |
| 367 | 3.800 | RESEARCH | Azure Container Apps Atlas | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-dc748bec19fd | — |
| 368 | 3.800 | RESEARCH | Batch Reads and Aggregation Pushdown | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-01e1f13f468a | — |
| 369 | 3.800 | RESEARCH | Schema Inference and Type Promotion | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-0d1fc8db4911 | — |
| 370 | 3.800 | RESEARCH | Embedded verifier and post-migration data verification cost | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-df647968356b | — |
| 371 | 3.800 | RESEARCH | loadlevel-tuning | mongosync | dr | frontier | mongodb-cohort-91fafd3a2f3c | — |
| 372 | 3.800 | RESEARCH | Time series compact and disk space reclaim | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 373 | 3.800 | RESEARCH | KMS Key Rotation Atlas | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-1c65b14aa5e2 | — |
| 374 | 3.800 | RESEARCH | Structured Streaming with Change Streams | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-596d3e14c0db | — |
| 375 | 3.800 | RESEARCH | MongoDB AI Policy Scanning | Security Compliance Auditor | dr | frontier | mongodb-cohort-292dd656b5d2 | — |
| 376 | 3.800 | RESEARCH | Chaos-style resilience testing under load (kill primary during peak writes, network partition, disk-full/IO-stall injection) | MongoDB Stress, Soak, and Chaos-Resilience Testing | dr | frontier | mongodb-cohort-30599b0ff34f | — |
| 377 | 3.800 | RESEARCH | Bucket reopening and the {metaField, timeField} index requirement | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-3a39b842dcf7 | — |
| 378 | 3.800 | RESEARCH | Self-Managed Security Config | MongoDB Security Architecture | dr | frontier | mongodb-cohort-2b89fbc3d8fa | — |
| 379 | 3.800 | RESEARCH | Search Node sizing and disk-to-RAM ratios for quantized vector indexes | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-3bde70611ed4 | — |
| 380 | 3.800 | RESEARCH | Search Node sizing for quantized vector indexes (RAM, disk, vCPU) | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-3bde70611ed4 | — |
| 381 | 3.800 | RESEARCH | Cold-cache latency regression | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-41d59b577242 | — |
| 382 | 3.800 | RESEARCH | COUNT_SCAN and sharded count accuracy | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 383 | 3.800 | RESEARCH | $exists query bounds on indexes | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-00acf5133e37 | — |
| 384 | 3.800 | RESEARCH | Atlas Search for substring matching | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-9b0a0e06ee53 | — |
| 385 | 3.800 | RESEARCH | Atlas Search regex and wildcard operator cost | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-9b0a0e06ee53 | — |
| 386 | 3.800 | RESEARCH | Atlas Search searchAfter pagination | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-9b0a0e06ee53 | — |
| 387 | 3.800 | RESEARCH | Attribute pattern and wildcardProjection design | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | covered | mongodb-cohort-56cd900b7fc1 | — |
| 388 | 3.800 | RESEARCH | BSON BinData vector ingestion | Atlas Cluster Topology and Tier Economics; Vector Search Quantization and Embedding Storage Cost | dr | covered | mongodb-cohort-27781ed3f782 | — |
| 389 | 3.800 | RESEARCH | Burstable M10/M20 tiers | Atlas Cluster Topology and Tier Economics; Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe) | dr | covered | mongodb-cohort-3bc7bd71277a | — |
| 390 | 3.800 | RESEARCH | COUNT_SCAN covered counts | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-70bfdc1552cd | — |
| 391 | 3.800 | RESEARCH | Data Federation over customer S3 with partitioning | Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation); Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-6c47589901c9 | — |
| 392 | 3.800 | RESEARCH | Data type selection for storage | Schema Design for Storage Cost; Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-2419c4ff9ac4 | — |
| 393 | 3.800 | RESEARCH | Drop-index suggestions endpoint | Atlas Slow-Query Log and Performance Advisor Automation | dr | covered | mongodb-cohort-d5736a3db62d | — |
| 394 | 3.800 | RESEARCH | FinOps Framework Applied to Atlas | Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-d969be1abbd9 | — |
| 395 | 3.800 | RESEARCH | Flex cluster spend ceiling | Atlas Billing Mechanics and Cost Visibility; Billing Alerts and Budget Controls | dr | covered | mongodb-cohort-20c760e1289b | — |
| 396 | 3.800 | RESEARCH | Flex Limitations and migration to Dedicated | Atlas Flex Pricing and Flex-vs-Dedicated Break-Even; Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-6b54e14a5aec | — |
| 397 | 3.800 | RESEARCH | hint in aggregate and update/delete | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-ca60df035474 | — |
| 398 | 3.800 | RESEARCH | Index filters deprecation and migration | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-d5736a3db62d | — |
| 399 | 3.800 | RESEARCH | Index prefix compression and index size | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-436c498b1a20 | — |
| 400 | 3.800 | RESEARCH | Lambda MongoDB Driver Pattern | Atlas Data API Removal | dr | covered | mongodb-cohort-669bbd14ed32 | — |
| 401 | 3.800 | RESEARCH | majority-ack write concern change | MongoDB 8.0 performance changes & read-path regressions vs 7.0 | revisit | refresh-review | mongodb-cohort-b17c7aa5e0c9 | — |
| 402 | 3.800 | RESEARCH | MongoDB MCP Server read-only and permission model | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-62e91e3112d4 | — |
| 403 | 3.800 | RESEARCH | mtools Log Analysis Integration | FTDC and Log Tooling | revisit | refresh-review | mongodb-cohort-2f2019ed2bed | — |
| 404 | 3.800 | RESEARCH | natural hint and collection scans | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-b393cf16e5a7 | — |
| 405 | 3.800 | RESEARCH | Online Archive partition-field selection | Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation); Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-6c47589901c9 | — |
| 406 | 3.800 | RESEARCH | Online Archive query performance optimization | DATE Criteria | revisit | refresh-review | mongodb-cohort-5b406510c316 | — |
| 407 | 3.800 | RESEARCH | Partial and TTL indexes on time series | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-c3f8cd065825 | — |
| 408 | 3.800 | RESEARCH | Partial TTL indexes | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-d5736a3db62d | — |
| 409 | 3.800 | RESEARCH | Partial unique indexes for soft delete | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-d5736a3db62d | — |
| 410 | 3.800 | RESEARCH | planCacheSize and $planCacheStats | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-ca60df035474 | — |
| 411 | 3.800 | RESEARCH | Total count strategies for paginated UIs | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-70bfdc1552cd | — |
| 412 | 3.800 | RESEARCH | Wildcard index query-planner behavior and explain rejectedPlans | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | covered | mongodb-cohort-c554dd99dde4 | — |
| 413 | 3.800 | RESEARCH | WiredTiger Block and Prefix Compression as Storage Cost Lever | Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-d969be1abbd9 | — |
| 414 | 3.775 | RESEARCH | Encryption In Transit | Global AI Hub Research Corpus; MongoDB Security Architecture | dr | frontier | mongodb-cohort-1c65b14aa5e2 | — |
| 415 | 3.775 | RESEARCH | Autocomplete | MongoDB Atlas Search | dr | frontier | mongodb-cohort-3aa797450c89 | — |
| 416 | 3.775 | RESEARCH | dropIndexes locking and rollback by rebuild | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-b17c7aa5e0c9 | — |
| 417 | 3.775 | RESEARCH | Maintained or cached count counters | Total count strategies for paginated UIs | dr | frontier | mongodb-cohort-92f18235288a | — |
| 418 | 3.775 | RESEARCH | Atlas RBAC IaC | MongoDB Atlas Terraform Provider | dr | frontier | mongodb-cohort-292dd656b5d2 | — |
| 419 | 3.775 | RESEARCH | replSetResizeOplog and oplog compaction on self-managed replica sets | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 420 | 3.775 | RESEARCH | Bucket archiving and query-based reopening | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 421 | 3.775 | RESEARCH | Cache-pressure early bucket closure and bucket catalog memory | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-3a39b842dcf7 | — |
| 422 | 3.775 | RESEARCH | Side-writes table and hybrid index builds | Resumable index builds | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 423 | 3.775 | RESEARCH | Validation and performance review of generated queries | Natural language to MongoDB query generation | dr | frontier | mongodb-cohort-0c9ecdd50528 | — |
| 424 | 3.775 | RESEARCH | Atlas invoice tag coverage and cost export reconciliation | Atlas tag taxonomy for showback and chargeback | dr | frontier | mongodb-cohort-df647968356b | — |
| 425 | 3.775 | RESEARCH | Exporting $indexStats metrics with mongodb_exporter and PMM | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 426 | 3.775 | RESEARCH | Migration Host Provisioning | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-50c2ce240545 | — |
| 427 | 3.775 | RESEARCH | Persisting index usage metrics with PMM and mongodb_exporter | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 428 | 3.775 | RESEARCH | Backup Daemon HA and Failure Domains | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-1482bd9b61d6 | — |
| 429 | 3.775 | RESEARCH | Config server placement and cost (dedicated vs embedded) | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-df647968356b | — |
| 430 | 3.775 | RESEARCH | Entra ID Workload Identity Federation | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-b74fe6f94c37 | — |
| 431 | 3.775 | RESEARCH | GCP Workload Identity Federation OIDC | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-b74fe6f94c37 | — |
| 432 | 3.750 | RESEARCH | Database Triggers | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f09da64a2f6e | — |
| 433 | 3.750 | RESEARCH | MongoDB commit quorum and two-phase index builds | Resumable index builds | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 434 | 3.750 | RESEARCH | Time-field bucket predicates | Bucket-level predicate rewriting for measurement operators | dr | frontier | mongodb-cohort-ded7cec0af2e | — |
| 435 | 3.750 | RESEARCH | Two-phase (simultaneous) index builds | Resumable index builds | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 436 | 3.750 | RESEARCH | Atlas SAML Entra ID | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-a83ebb3f0b61 | — |
| 437 | 3.750 | RESEARCH | Atlas X.509 Certificate Auth | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-205df5e830d6 | — |
| 438 | 3.750 | RESEARCH | Compass Data Import Export | MongoDB Compass | dr | frontier | mongodb-cohort-4451fc8be02a | — |
| 439 | 3.750 | RESEARCH | Connection Registry | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-8cacc610d606 | — |
| 440 | 3.750 | RESEARCH | Migration from Regular Collections | mongodb-time-series | dr | frontier | mongodb-cohort-366a07958d6d | — |
| 441 | 3.750 | RESEARCH | Rolling index builds as a resource-isolation alternative | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 442 | 3.750 | RESEARCH | GCP Forwarding Rule Quota | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-687aed0d21fd | — |
| 443 | 3.750 | RESEARCH | Ops Manager Backup | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-52b87d174a64 | — |
| 444 | 3.750 | RESEARCH | SHARDING_FILTER stage internals and orphaned-document filtering | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 445 | 3.750 | RESEARCH | MSK-Connect-deployment | mongodb-kafka-connector | dr | frontier | mongodb-cohort-c5a4ee6b0d70 | — |
| 446 | 3.750 | RESEARCH | One-way tier gates: sharding, Global Writes, edition changes | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-12c8de3441e5 | — |
| 447 | 3.750 | RESEARCH | Upgrade rollback playbook | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-b17c7aa5e0c9 | — |
| 448 | 3.750 | RESEARCH | Atlas Admin API v2 REST | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-1d77b14f4cb1 | — |
| 449 | 3.750 | RESEARCH | Atlas on Azure | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-7030217d35d1 | — |
| 450 | 3.750 | RESEARCH | Atlas on GCP | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-7030217d35d1 | — |
| 451 | 3.750 | RESEARCH | Atlas Search node scaling per shard | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-1ffb989b662b | — |
| 452 | 3.750 | RESEARCH | Azure Event Hub Atlas Stream Processing | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-dc748bec19fd | — |
| 453 | 3.750 | RESEARCH | BigQuery Atlas Dataflow CDC | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-e515b403d48b | — |
| 454 | 3.725 | RESEARCH | GeoJSON Object Types | MongoDB Geospatial | dr | frontier | mongodb-cohort-8df40ccd287c | — |
| 455 | 3.725 | RESEARCH | Index rebuild cost after a wrong drop | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-df647968356b | — |
| 456 | 3.725 | RESEARCH | Azure App Service Atlas | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-dc748bec19fd | — |
| 457 | 3.725 | RESEARCH | Cloud Functions Gen2 Atlas | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-687aed0d21fd | — |
| 458 | 3.725 | RESEARCH | Cloud NAT for Atlas | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-687aed0d21fd | — |
| 459 | 3.725 | RESEARCH | Terraform Import generate-config-out | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-1d77b14f4cb1 | — |
| 460 | 3.725 | RESEARCH | Delete and re-insert safety on time series | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-3a39b842dcf7 | — |
| 461 | 3.725 | RESEARCH | DiskSpaceMonitor and low-disk index build abort (7.1+) | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-e71ad6d99f1d | — |
| 462 | 3.725 | RESEARCH | Clustered collection insert locality | Random-key (hashed/UUID) index insert behavior | dr | frontier | mongodb-cohort-ead4605ef88b | — |
| 463 | 3.725 | RESEARCH | Rooted $or subplanning and SORT_MERGE | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-e515b403d48b | — |
| 464 | 3.725 | RESEARCH | debezium-handlers | CDC-patterns | dr | frontier | mongodb-cohort-642e05e32e3c | — |
| 465 | 3.725 | RESEARCH | ExpressRoute Atlas Connectivity | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-a6b03cd32221 | — |
| 466 | 3.725 | RESEARCH | OpenTelemetry MongoDB Receiver | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-1482bd9b61d6 | — |
| 467 | 3.725 | RESEARCH | schema-registry-integration | mongodb-kafka-connector | dr | frontier | mongodb-cohort-664b801b87e8 | — |
| 468 | 3.725 | RESEARCH | serverStatus indexBuilds metrics and index build observability | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 469 | 3.725 | RESEARCH | Canary and Shadow-Traffic Comparison | MongoDB Performance Regression Detection and Testing Methodology | dr | frontier | mongodb-cohort-a0a420b316d1 | — |
| 470 | 3.725 | RESEARCH | Hybrid search ($rankFusion) vs separate search plus vector stack | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-3bde70611ed4 | — |
| 471 | 3.725 | RESEARCH | Multi-Vector Patterns | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-9b275081d62e | — |
| 472 | 3.700 | RESEARCH | Version upgrade paths (4.4 → 5.0 → 6.0 → 7.0 → 8.0) | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-41d59b577242 | — |
| 473 | 3.700 | RESEARCH | Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden) | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 474 | 3.700 | RESEARCH | Destination right-sizing after cutover | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-12c8de3441e5 | — |
| 475 | 3.700 | RESEARCH | Cache-aside vs write-through and cache stampede prevention | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 476 | 3.700 | RESEARCH | Query settings and index filters as plan pinning | Replanning loops and replanReason | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 477 | 3.700 | RESEARCH | Frozen buckets and compression failures | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 478 | 3.700 | RESEARCH | Initial sync index build memory limits | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 479 | 3.700 | RESEARCH | Java driver 4.10 and 5.x retry semantics | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-eec7f143c4d7 | — |
| 480 | 3.700 | RESEARCH | per-accumulator explain memory statistics | $group accumulator memory caps | dr | frontier | mongodb-cohort-975ece847641 | — |
| 481 | 3.700 | RESEARCH | PSC Legacy Migration | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-4aea6e2a2abf | — |
| 482 | 3.700 | RESEARCH | Mixed-schema measurement predicate safety | Bucket-level predicate rewriting for measurement operators | dr | frontier | mongodb-cohort-3d90e57354b7 | — |
| 483 | 3.700 | RESEARCH | Oplog windows and Search initial-sync recovery | Atlas Search index sync lag and search-node sizing | dr | frontier | mongodb-cohort-b17c7aa5e0c9 | — |
| 484 | 3.700 | RESEARCH | Sharded time series rebuild and resharding | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-3a39b842dcf7 | — |
| 485 | 3.700 | RESEARCH | Cost-based ranker and the plan cache (8.3+) | Replanning loops and replanReason | dr | frontier | mongodb-cohort-f78d07b225d9 | — |
| 486 | 3.700 | RESEARCH | MongoDB Time-Series Query and Index Optimization | mongodb-time-series | dr | covered | mongodb-cohort-426b58169dd6 | the research suite run mongodb-2026-10-14 |
| 487 | 3.700 | RESEARCH | serverStatus metrics.query.cbr | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-8774765806eb | — |
| 488 | 3.675 | RESEARCH | MVCC and Snapshot Isolation | WiredTiger Storage Engine Internals | dr | frontier | mongodb-cohort-0a5c86f5c884 | — |
| 489 | 3.675 | RESEARCH | Atlas SCRAM-SHA-256 | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-205df5e830d6 | — |
| 490 | 3.675 | RESEARCH | Radius Unit Conversions | MongoDB Geospatial | dr | frontier | mongodb-cohort-8df40ccd287c | — |
| 491 | 3.675 | RESEARCH | Granularity Anti-Patterns | mongodb-time-series | dr | frontier | mongodb-cohort-e128bd27e4b1 | — |
| 492 | 3.675 | RESEARCH | Idle bucket expiry and archived bucket reopening | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 493 | 3.675 | RESEARCH | MongoDB Search eventual consistency and replication-lag metrics | Atlas Search index sync lag and search-node sizing | dr | frontier | mongodb-cohort-6f6dce76771c | — |
| 494 | 3.675 | RESEARCH | Atlas managed slow operation threshold and Performance Advisor index suggestions | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 495 | 3.675 | RESEARCH | External sorter spill files in dbpath/_tmp | Resumable index builds | dr | frontier | mongodb-cohort-3d90e57354b7 | — |
| 496 | 3.675 | RESEARCH | Pre-quantized BinData (int8 and int1) ingestion | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-9b275081d62e | — |
| 497 | 3.675 | RESEARCH | Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-9b275081d62e | — |
| 498 | 3.675 | RESEARCH | Stream Processor Monitoring | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-7c50b4afaa88 | — |
| 499 | 3.675 | RESEARCH | Common Migration Failures | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-f1ebe93a2c8b | — |
| 500 | 3.675 | RESEARCH | Geospatial Anti-Patterns | MongoDB Geospatial | dr | frontier | mongodb-cohort-8df40ccd287c | — |
| 501 | 3.675 | RESEARCH | custom $accumulator spill and merge semantics | $group accumulator memory caps | dr | frontier | mongodb-cohort-975ece847641 | — |
| 502 | 3.675 | RESEARCH | GCP Global Access PSC | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-4aea6e2a2abf | — |
| 503 | 3.675 | RESEARCH | Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields) | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-6f6dce76771c | — |
| 504 | 3.675 | RESEARCH | Auto Embedding Voyage AI | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-9b275081d62e | — |
| 505 | 3.650 | SKIP | Index usage measurement with $indexStats | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 506 | 3.650 | SKIP | Redundant and prefix index detection | Hidden indexes and safe index removal; Unused index detection with $indexStats | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 507 | 3.650 | RESEARCH | Authentication Methods | MongoDB Security Architecture | dr | frontier | mongodb-cohort-c778f20011cb | — |
| 508 | 3.650 | RESEARCH | MongoDB rolling index builds | Resumable index builds | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 509 | 3.650 | RESEARCH | Atlas Security Posture Checklist | MongoDB Security Architecture | dr | frontier | mongodb-cohort-2b89fbc3d8fa | — |
| 510 | 3.650 | RESEARCH | Atlas Database Auditing | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-b0e4f880a1a3 | — |
| 511 | 3.650 | RESEARCH | Compass Connection Management | MongoDB Compass | dr | frontier | mongodb-cohort-4451fc8be02a | — |
| 512 | 3.650 | RESEARCH | Scheduled Triggers | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f09da64a2f6e | — |
| 513 | 3.650 | RESEARCH | Stream Processing Instance (SPI) | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-8cacc610d606 | — |
| 514 | 3.650 | RESEARCH | Workload Characterization | MongoDB Performance Benchmarking | dr | frontier | mongodb-cohort-441524d0c05b | — |
| 515 | 3.650 | RESEARCH | Config shard versus dedicated config server | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-d7196ea52923 | — |
| 516 | 3.650 | RESEARCH | Atlas Terraform mongodbatlas_resource_policy | Atlas Resource Policies Cedar | dr | frontier | mongodb-cohort-1d77b14f4cb1 | — |
| 517 | 3.650 | RESEARCH | Entra ID OIDC Workforce Federation | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-a83ebb3f0b61 | — |
| 518 | 3.650 | RESEARCH | Atlas minimum oplog window (oplogMinRetentionHours) tuning | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6f6dce76771c | — |
| 519 | 3.650 | RESEARCH | Atlas disk decrease by volume replacement on AWS, Azure and GCP | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 520 | 3.650 | RESEARCH | Reducing Atlas storage capacity (new-volume sync, per-node downtime) | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 521 | 3.650 | RESEARCH | Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes) | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-12c8de3441e5 | — |
| 522 | 3.650 | RESEARCH | Execution-guided text-to-MQL refinement | Natural language to MongoDB query generation | dr | frontier | mongodb-cohort-ea7ac08cebd8 | — |
| 523 | 3.650 | RESEARCH | $_internalUnpackBucket explain reading | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-c3f8cd065825 | — |
| 524 | 3.650 | RESEARCH | $mergeCursors stage in explain | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-a912b742ce3a | — |
| 525 | 3.650 | RESEARCH | $top/$bottom accumulators rewrite | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-f08967f01b08 | — |
| 526 | 3.650 | RESEARCH | App Services Migration Paths | MongoDB Atlas App Services | revisit | refresh-review | mongodb-cohort-faa5aa005f8b | — |
| 527 | 3.650 | RESEARCH | Atlas WIF built-in vs callback authentication | Atlas Identity Federation and Resource Policy Boundaries | revisit | refresh-review | mongodb-cohort-2c3c2af5f1b7 | — |
| 528 | 3.650 | RESEARCH | Bucket-level predicate rewriting for measurement operators | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-c3f8cd065825 | — |
| 529 | 3.650 | RESEARCH | Cloud Marketplace Billing for Atlas (AWS GCP Azure) | Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-d969be1abbd9 | — |
| 530 | 3.650 | RESEARCH | Co-located vs dedicated search migration thresholds | Atlas Cluster Topology and Tier Economics; Atlas Search and Dedicated Search Nodes Cost | dr | covered | mongodb-cohort-901582496b30 | — |
| 531 | 3.650 | RESEARCH | Deadline Propagation and Context Cancellation in MongoDB Drivers | Client Side Operations Timeout (CSOT) | revisit | refresh-review | mongodb-cohort-b245a56e13e9 | — |
| 532 | 3.650 | RESEARCH | Elastic Billing transition | Atlas Billing Mechanics and Cost Visibility; Atlas Credits Prepaid Subscriptions and Overage | dr | covered | mongodb-cohort-87a93e7f3809 | — |
| 533 | 3.650 | RESEARCH | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-87a93e7f3809 | — |
| 534 | 3.650 | RESEARCH | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | MongoDB Indexes Deep Dive; MongoDB Upgrade Paths | dr | covered | mongodb-cohort-6c00ac0035c3 | the research suite run mongodb-2026-10-14 |
| 535 | 3.650 | RESEARCH | Multi-Region and Cross-Cloud Data Transfer Costs | Atlas Cluster Topology and Tier Economics | dr | covered | mongodb-cohort-87a93e7f3809 | — |
| 536 | 3.650 | RESEARCH | Per-query fusion weighting | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | refresh-review | mongodb-cohort-3d90e57354b7 | — |
| 537 | 3.650 | RESEARCH | Random-key (hashed/UUID) index insert behavior | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | covered | mongodb-cohort-6c00ac0035c3 | — |
| 538 | 3.650 | RESEARCH | Read preference and write routing for cost | Atlas Cluster Topology and Tier Economics; Multi-Region and Cross-Cloud Data Transfer Costs | dr | covered | mongodb-cohort-87a93e7f3809 | — |
| 539 | 3.650 | RESEARCH | SERVER JIRA Ticket Regression Mapping | KB-Backed Troubleshooting | revisit | refresh-review | mongodb-cohort-03dd84b04983 | — |
| 540 | 3.650 | RESEARCH | Slot-based execution engine eligibility | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-c3f8cd065825 | — |
| 541 | 3.650 | RESEARCH | Storage Growth and IOPS Forecasting for Cost | Atlas Cluster Topology and Tier Economics | dr | covered | mongodb-cohort-d108c5a84192 | — |
| 542 | 3.625 | RESEARCH | linearizable read concern | Read Concern Levels | dr | frontier | mongodb-cohort-6f6dce76771c | — |
| 543 | 3.625 | RESEARCH | Measuring ANN recall against ENN baselines | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-3efebf992645 | — |
| 544 | 3.625 | RESEARCH | GCP VPC Peering | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-367067ba7a92 | — |
| 545 | 3.625 | RESEARCH | moved Block Migration Pattern | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-f173c69ee97a | — |
| 546 | 3.625 | RESEARCH | CloudFormation Third Party Activation | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-f173c69ee97a | — |
| 547 | 3.625 | RESEARCH | orphanCleanupDelaySecs and range deletion timing | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-8ec9154ebfb3 | — |
| 548 | 3.625 | RESEARCH | Burstable M10/M20 CPU credits and the M30 production threshold | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-f78d07b225d9 | — |
| 549 | 3.625 | RESEARCH | Burstable M10/M20 CPU-credit throttling and when to move to M30 | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-f78d07b225d9 | — |
| 550 | 3.625 | RESEARCH | Upgrade Procedures | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-a0f287f79c49 | — |
| 551 | 3.625 | RESEARCH | Offline-First Patterns | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-746f46bdae21 | — |
| 552 | 3.625 | RESEARCH | mongomirror Deprecation | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-7451be70c74d | — |
| 553 | 3.625 | RESEARCH | Schema grounding and value linking for MQL generation | Natural language to MongoDB query generation | dr | frontier | mongodb-cohort-0c9ecdd50528 | — |
| 554 | 3.625 | RESEARCH | Archive Restore | MongoDB Atlas Online Archive | dr | frontier | mongodb-cohort-68b4130466d8 | — |
| 555 | 3.625 | RESEARCH | Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-1ffb989b662b | — |
| 556 | 3.625 | RESEARCH | MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later) | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-cf9a0f8ed75e | — |
| 557 | 3.625 | RESEARCH | Primary-driven index builds and write-rate throttles | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 558 | 3.625 | RESEARCH | rawData bucket-level CRUD (8.2 and later) | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 559 | 3.625 | RESEARCH | Self-managed mongot on Community Edition: hardware and labour TCO | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-1ffb989b662b | — |
| 560 | 3.600 | RESEARCH | $querySettings stage and query settings inspection | Operation rejection filters | dr | frontier | mongodb-cohort-3d90e57354b7 | — |
| 561 | 3.600 | RESEARCH | Atlas Flex Technical Limits | MongoDB Atlas Flex and Serverless Tiers | dr | frontier | mongodb-cohort-3218ab1d6cd5 | — |
| 562 | 3.600 | RESEARCH | Search Nodes Dedicated Infrastructure | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-a52306435b73 | — |
| 563 | 3.600 | RESEARCH | YCSB Workload Reference | MongoDB Performance Benchmarking | dr | frontier | mongodb-cohort-441524d0c05b | — |
| 564 | 3.600 | RESEARCH | Pre-upgrade safety checks | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-41d59b577242 | — |
| 565 | 3.600 | RESEARCH | Permissions Model | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-746f46bdae21 | — |
| 566 | 3.600 | RESEARCH | Atlas Functions JavaScript Runtime | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f09da64a2f6e | — |
| 567 | 3.600 | RESEARCH | Connector Error Patterns | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a04dd23fc577 | — |
| 568 | 3.600 | RESEARCH | Migration Validation Patterns | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-a60b195db1d3 | — |
| 569 | 3.600 | RESEARCH | Terraform state reconciliation after a Flex-to-Dedicated conversion | Flex Limitations and migration to Dedicated | dr | frontier | mongodb-cohort-0444cf01e935 | — |
| 570 | 3.600 | RESEARCH | Atlas IaC Migration Paths | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-7b807b8ba86d | — |
| 571 | 3.600 | RESEARCH | Atlas write-blocking thresholds and Intelligent Workload Management | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 572 | 3.600 | RESEARCH | SBE plan cache keys and parameterized explode-for-sort plans | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-6e1e9ef33885 | — |
| 573 | 3.600 | RESEARCH | S3-Compatible Snapshot Storage with Object Lock | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-835ffca778c9 | — |
| 574 | 3.600 | RESEARCH | Per-shape maxTimeMS and queryKnobs (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-26278075d879 | — |
| 575 | 3.600 | RESEARCH | Per-shape queryKnobs and maxTimeMS (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-26278075d879 | — |
| 576 | 3.600 | RESEARCH | AND_SORTED vs AND_HASH plan stages | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | covered | mongodb-cohort-8774765806eb | — |
| 577 | 3.600 | RESEARCH | Atlas Search and Dedicated Search Nodes Cost | Atlas Cluster Topology and Tier Economics | dr | covered | mongodb-cohort-901582496b30 | — |
| 578 | 3.600 | RESEARCH | Backup snapshot storage growth cost | Atlas Cluster Topology and Tier Economics; Storage Growth and IOPS Forecasting for Cost | dr | covered | mongodb-cohort-d108c5a84192 | — |
| 579 | 3.600 | RESEARCH | Bounded sort ($_internalBoundedSort) | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-8774765806eb | — |
| 580 | 3.600 | RESEARCH | Collation and index sort compatibility | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-6c00ac0035c3 | — |
| 581 | 3.600 | RESEARCH | DNS and SRV Records | MongoDB Atlas AWS Networking | revisit | refresh-review | mongodb-cohort-480e6fc91e5c | — |
| 582 | 3.600 | RESEARCH | Granularity and custom bucketing parameters | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-98d2158f395e | — |
| 583 | 3.600 | RESEARCH | Hashed vs ranged shard key query trade-offs | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-6a7dac291e46 | — |
| 584 | 3.600 | RESEARCH | Maintenance Impact Minimization | Atlas Maintenance Windows | revisit | refresh-review | mongodb-cohort-18c61444ac02 | — |
| 585 | 3.600 | RESEARCH | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | Database Profiler vs Query Profiler; MongoDB Capacity Planning; MongoDB Compass; MongoDB Performance Benchmarking; MongoDB Performance Troubleshooting | dr | covered | mongodb-cohort-a912b742ce3a | the research suite run mongodb-2026-10-14 |
| 586 | 3.600 | RESEARCH | Multikey index coverage and multiKeyPaths | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-269bea7beb3a | — |
| 587 | 3.600 | RESEARCH | multikey index sort behaviour | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | frontier | mongodb-cohort-269bea7beb3a | — |
| 588 | 3.600 | RESEARCH | Read concern and causal consistency with secondary reads | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-cf9a0f8ed75e | — |
| 589 | 3.600 | RESEARCH | read your own writes | Causal Consistency | revisit | refresh-review | mongodb-cohort-a70f5ba6e98d | — |
| 590 | 3.600 | RESEARCH | Replica Set Transactions | MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 591 | 3.600 | RESEARCH | Sparse versus partial index equivalence | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | frontier | mongodb-cohort-269bea7beb3a | — |
| 592 | 3.575 | RESEARCH | Atlas Database Users | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-205df5e830d6 | — |
| 593 | 3.575 | RESEARCH | local read concern | Read Concern Levels | dr | frontier | mongodb-cohort-8dd74aa67f67 | — |
| 594 | 3.575 | RESEARCH | Atlas Project Roles (15 Purpose-Built) | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-292dd656b5d2 | — |
| 595 | 3.575 | RESEARCH | Atlas billing alert notification delivery | Admin API alert configurations for billing events | dr | frontier | mongodb-cohort-f78d07b225d9 | — |
| 596 | 3.575 | RESEARCH | Safe execution against non-production Atlas (cluster isolation, guardrails, cost/cleanup discipline) | MongoDB Stress, Soak, and Chaos-Resilience Testing | dr | frontier | mongodb-cohort-372a6407eb6e | — |
| 597 | 3.575 | RESEARCH | Atlas Encryption IaC | MongoDB Atlas Terraform Provider | dr | frontier | mongodb-cohort-1c65b14aa5e2 | — |
| 598 | 3.575 | RESEARCH | Version Manifest Mirroring | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-a0f287f79c49 | — |
| 599 | 3.575 | RESEARCH | Sharded Cluster Migrations | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-0d0939aba268 | — |
| 600 | 3.575 | RESEARCH | Multi-Cloud DR Pattern | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-2ce9556582f9 | — |
| 601 | 3.575 | RESEARCH | Multi-Tenancy Anti-Patterns | MongoDB Multi-Tenancy | dr | frontier | mongodb-cohort-80b202d28b71 | — |
| 602 | 3.575 | RESEARCH | Terraform Atlas Provider v2.x | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-0444cf01e935 | — |
| 603 | 3.575 | RESEARCH | Time-series bucket closure under cache pressure | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-28706a00e932 | — |
| 604 | 3.575 | RESEARCH | Search Node network transfer and multi-region cost | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-9950ed680654 | — |
| 605 | 3.575 | RESEARCH | Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-8dd74aa67f67 | — |
| 606 | 3.575 | RESEARCH | explodeForSort integer overflow (CVE-2026-82076) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-26278075d879 | — |
| 607 | 3.575 | REFRESH | MongoDB Atlas | MongoDB Expert Knowledge | revisit | refresh-review | mongodb-cohort-586d5ccba289 | — |
| 608 | 3.550 | RESEARCH | Atlas RBAC | MongoDB Security Architecture | dr | frontier | mongodb-cohort-0594c62af41d | — |
| 609 | 3.550 | RESEARCH | Atlas Audit Logging | MongoDB Compliance and Regulatory; MongoDB Security Architecture | dr | frontier | mongodb-cohort-b0e4f880a1a3 | — |
| 610 | 3.550 | RESEARCH | NSG Rules for Atlas | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-a6b03cd32221 | — |
| 611 | 3.550 | RESEARCH | Shard key index design | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 612 | 3.550 | RESEARCH | BYOK Key Management | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-1c65b14aa5e2 | — |
| 613 | 3.550 | RESEARCH | HIPAA BAA and ePHI Configuration | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-272a1048a22c | — |
| 614 | 3.550 | RESEARCH | Multiplanner scoring and tie-breakers | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-71089ad6ce1a | — |
| 615 | 3.550 | RESEARCH | Ops Manager Admin API | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-0444cf01e935 | — |
| 616 | 3.550 | RESEARCH | mongos as MongoDB's native router & why MongoDB rarely uses third-party proxies | Database Proxies & Query-Optimization Middleware | dr | frontier | mongodb-cohort-70b86d349efb | — |
| 617 | 3.550 | RESEARCH | Rolling index builds on Kubernetes with the Percona Operator | Rolling index builds | dr | frontier | mongodb-cohort-269bea7beb3a | — |
| 618 | 3.550 | RESEARCH | SBE plan cache pinned entries and the classic runtime planner for SBE | Replanning loops and replanReason | dr | frontier | mongodb-cohort-71089ad6ce1a | — |
| 619 | 3.550 | RESEARCH | AKO Deletion Protection v2.0 | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-7b807b8ba86d | — |
| 620 | 3.550 | RESEARCH | Atlas Support Plan Pricing | Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-d108c5a84192 | — |
| 621 | 3.550 | RESEARCH | Find projection vs $project aggregation coverage | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-353b35c18a09 | — |
| 622 | 3.525 | SKIP | Plan cache invalidation on index DDL (hide, drop, create) | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-71089ad6ce1a | — |
| 623 | 3.525 | RESEARCH | Compass Real-Time Performance Monitoring | MongoDB Compass | dr | frontier | mongodb-cohort-4451fc8be02a | — |
| 624 | 3.525 | RESEARCH | Datadog Integration | MongoDB Monitoring and Observability | dr | frontier | mongodb-cohort-e4e31a146993 | — |
| 625 | 3.525 | RESEARCH | External sorter spill files and the _tmp directory | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-26278075d879 | — |
| 626 | 3.525 | RESEARCH | Atlas tag enforcement through Terraform and APIs | Atlas tag taxonomy for showback and chargeback | dr | frontier | mongodb-cohort-0444cf01e935 | — |
| 627 | 3.525 | RESEARCH | Config shard (embedded config server) cost trade-off | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-372a6407eb6e | — |
| 628 | 3.525 | RESEARCH | Atlas Minimum Oplog Window (oplogMinRetentionHours) | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-8dd74aa67f67 | — |
| 629 | 3.525 | RESEARCH | internalQueryMaxScansToExplode and maxScansToExplodeReached | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-e12888479cf1 | — |
| 630 | 3.525 | RESEARCH | Atlas IP Access List Ownership Conflict | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-6c84a071d812 | — |
| 631 | 3.525 | RESEARCH | Flex backup and recovery planning | Flex Limitations and migration to Dedicated | dr | frontier | mongodb-cohort-734b288e14c5 | — |
| 632 | 3.525 | RESEARCH | Conflict Resolution | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-746f46bdae21 | — |
| 633 | 3.525 | RESEARCH | Atlas Query Profiler and Operation Throttling metrics | Operation rejection filters | dr | frontier | mongodb-cohort-e12888479cf1 | — |
| 634 | 3.525 | RESEARCH | Gen2 clusters and Extended Standard IOPS economics | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-12c8de3441e5 | — |
| 635 | 3.500 | RESEARCH | Hopping Windows | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-40309c756b09 | — |
| 636 | 3.500 | RESEARCH | Rebuilding a time series collection with $out or mongorestore | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 637 | 3.500 | RESEARCH | Change Data Capture Patterns | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f6ac572aba6f | — |
| 638 | 3.500 | RESEARCH | Atlas CLI Scripting | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-b397d383429d | — |
| 639 | 3.500 | RESEARCH | Timestamp APIs (oldest/stable/pinned) | WiredTiger Storage Engine Internals | dr | frontier | mongodb-cohort-ae873d2f56e0 | — |
| 640 | 3.500 | RESEARCH | Atlas security add-on uplifts (auditing, LDAP, customer-managed keys, private endpoints) | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-3e9502b80e34 | — |
| 641 | 3.500 | RESEARCH | Automated rolling builds in Atlas, Cloud Manager and Ops Manager | Rolling index builds | dr | frontier | mongodb-cohort-0decd84b4936 | — |
| 642 | 3.500 | RESEARCH | Flex Tooling Migration Terraform K8s CLI | MongoDB Atlas Flex and Serverless Tiers | dr | frontier | mongodb-cohort-b397d383429d | — |
| 643 | 3.500 | RESEARCH | Atlas Stream Processing Pub/Sub | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-4aea6e2a2abf | — |
| 644 | 3.500 | RESEARCH | FTDC Storage Overhead & Retention Budgeting | FTDC and Log Tooling | revisit | refresh-review | mongodb-cohort-b7c969c2a118 | — |
| 645 | 3.500 | RESEARCH | Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator) | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO | dr | covered | mongodb-cohort-d108c5a84192 | — |
| 646 | 3.500 | RESEARCH | Terraform Tag Enforcement and Policy-as-Code for Atlas Cost | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling | dr | covered | mongodb-cohort-1e5f42bef9c1 | — |
| 647 | 3.475 | RESEARCH | Tumbling Windows | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-40309c756b09 | — |
| 648 | 3.475 | RESEARCH | Collation-aware index key size | Collation and index sort compatibility | dr | frontier | mongodb-cohort-5e1e804f42f7 | — |
| 649 | 3.475 | RESEARCH | Ops Manager Profiler | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-9767e9fb3174 | — |
| 650 | 3.475 | RESEARCH | Sharding Triggers | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-6893051d2409 | — |
| 651 | 3.475 | RESEARCH | Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads) | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 652 | 3.475 | RESEARCH | VPC Atlas Security | Global AI Hub Research Corpus | dr | frontier | mongodb-cohort-a65c6320d64b | — |
| 653 | 3.475 | RESEARCH | Point of No Return | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-b7cbe85f979c | — |
| 654 | 3.475 | RESEARCH | Data Residency and EU Sovereignty | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-272a1048a22c | — |
| 655 | 3.450 | RESEARCH | Atlas Organization Roles | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-0594c62af41d | — |
| 656 | 3.450 | RESEARCH | path-level multikey tracking | explain multiKeyPaths interpretation | dr | frontier | mongodb-cohort-5e1e804f42f7 | — |
| 657 | 3.450 | RESEARCH | Live Migration to Atlas | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-a0f287f79c49 | — |
| 658 | 3.450 | RESEARCH | Atlas IaC Tool Decision Matrix | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-7b807b8ba86d | — |
| 659 | 3.450 | RESEARCH | Backup Daemon | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-66a976b0eee5 | — |
| 660 | 3.450 | RESEARCH | Straight-to-8 jump pattern | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-b7cbe85f979c | — |
| 661 | 3.450 | RESEARCH | Looker Atlas BI Connector | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-4aea6e2a2abf | — |
| 662 | 3.450 | RESEARCH | PagerDuty/Datadog/Splunk Integration | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-a0f287f79c49 | — |
| 663 | 3.450 | RESEARCH | Percona PMM mongolog versus profiler query source | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-e12888479cf1 | — |
| 664 | 3.450 | RESEARCH | EBS volume modification limits and Atlas disk resize mechanics | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 665 | 3.450 | RESEARCH | Spark Connector vs Alternatives | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a8bd98441f1a | — |
| 666 | 3.450 | RESEARCH | Atlas Vector Search HNSW IVF | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-3efebf992645 | — |
| 667 | 3.450 | RESEARCH | Atlas Credits Prepaid Subscriptions and Overage | Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-1e5f42bef9c1 | — |
| 668 | 3.450 | RESEARCH | BM25 IDF corpus statistics | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | refresh-review | mongodb-cohort-1131b10a900e | — |
| 669 | 3.450 | RESEARCH | BM25 term frequency saturation and field length normalization | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | refresh-review | mongodb-cohort-1131b10a900e | — |
| 670 | 3.450 | RESEARCH | ceSource cardinality estimation (sampling vs heuristics) | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-a0f9a99a9fe2 | — |
| 671 | 3.450 | RESEARCH | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | MongoDB Atlas Cost Optimization; Replica Set Node Topology Cost | dr | covered | mongodb-cohort-1e5f42bef9c1 | — |
| 672 | 3.450 | RESEARCH | Deferring Maintenance | Atlas Maintenance Windows | revisit | refresh-review | mongodb-cohort-18c61444ac02 | — |
| 673 | 3.450 | RESEARCH | Fusion score normalization strategies | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | refresh-review | mongodb-cohort-1131b10a900e | — |
| 674 | 3.450 | RESEARCH | M30 specs & connection limits | Atlas cluster tiers (M30) & major-version upgrade mechanics | revisit | refresh-review | mongodb-cohort-e843d0959617 | — |
| 675 | 3.450 | RESEARCH | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-27781ed3f782 | — |
| 676 | 3.450 | RESEARCH | SBE vs classic plan cache keys | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-a912b742ce3a | — |
| 677 | 3.450 | RESEARCH | Security Groups | MongoDB Atlas AWS Networking | revisit | refresh-review | mongodb-cohort-480e6fc91e5c | — |
| 678 | 3.425 | RESEARCH | Atlas Access Control and RBAC | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-0594c62af41d | — |
| 679 | 3.425 | RESEARCH | Atlas Real-Time Performance Panel | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-27f762df4c87 | — |
| 680 | 3.425 | RESEARCH | GKE Atlas Kubernetes Operator | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-b397d383429d | — |
| 681 | 3.425 | RESEARCH | tls-x509-auth | mongosync | dr | frontier | mongodb-cohort-0d9513c00c8a | — |
| 682 | 3.425 | RESEARCH | Atlas Kubernetes Operator AKO v2.14 | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-b397d383429d | — |
| 683 | 3.425 | RESEARCH | Kubernetes Operator Deployment | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-aa8dae0ac5e2 | — |
| 684 | 3.425 | RESEARCH | resume-and-checkpoint | mongosync | dr | frontier | mongodb-cohort-343b4f1fd839 | — |
| 685 | 3.425 | RESEARCH | Atlas auto-scaling gating by oplog window and its alerts | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-8dd74aa67f67 | — |
| 686 | 3.425 | RESEARCH | Atlas Infinite storage metering and max storage limit | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 687 | 3.425 | RESEARCH | GCP Workload Identity Atlas | Global AI Hub Research Corpus | dr | frontier | mongodb-cohort-a83ebb3f0b61 | — |
| 688 | 3.400 | SKIP | Atlas Query Shape Insights and Namespace Insights | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-e12888479cf1 | — |
| 689 | 3.400 | RESEARCH | Multi-Cloud Replica Sets | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-7cd1c9c93f1a | — |
| 690 | 3.400 | RESEARCH | Common upgrade failures | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-b7cbe85f979c | — |
| 691 | 3.400 | RESEARCH | Atlas Administration API rolling index endpoint | Rolling index builds | dr | frontier | mongodb-cohort-5e1e804f42f7 | — |
| 692 | 3.400 | RESEARCH | Function Context Object | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f6ac572aba6f | — |
| 693 | 3.400 | RESEARCH | Compass Data Modeling ER Diagrams | MongoDB Compass | dr | frontier | mongodb-cohort-b63ded16c61f | — |
| 694 | 3.400 | RESEARCH | Cost-based ranker plan selection for sorted queries (8.3+) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-372a6407eb6e | — |
| 695 | 3.400 | RESEARCH | MongoDB primary-driven index builds (PDIB) | Resumable index builds | dr | frontier | mongodb-cohort-5e1e804f42f7 | — |
| 696 | 3.400 | RESEARCH | Primary-driven index builds | Resumable index builds | dr | frontier | mongodb-cohort-4d7e60c43906 | — |
| 697 | 3.400 | RESEARCH | DISTINCT_SCAN with shard filtering in 8.2 | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 698 | 3.400 | RESEARCH | Atlas Data API (EOL) | MongoDB Atlas App Services | revisit | refresh-review | mongodb-cohort-aa8dae0ac5e2 | — |
| 699 | 3.400 | RESEARCH | Atlas tag taxonomy for showback and chargeback | Atlas Pricing Programs, Cost Governance and TCO; FinOps Framework Applied to Atlas | dr | covered | mongodb-cohort-1e5f42bef9c1 | — |
| 700 | 3.400 | RESEARCH | Collation-based case-insensitive equality | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-6a7dac291e46 | — |
| 701 | 3.400 | RESEARCH | Covered queries and projection design | Query Efficiency as a Cost Lever; Storage and Data-Lifecycle Cost Levers | dr | frontier | mongodb-cohort-9860e797131c | — |
| 702 | 3.400 | RESEARCH | Multikey index sort bounds | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-4d7e60c43906 | — |
| 703 | 3.375 | RESEARCH | Standard URI Format | MongoDB Connection String URI | dr | frontier | mongodb-cohort-6f6a12e41dfc | — |
| 704 | 3.375 | RESEARCH | Voyage AI Embeddings | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-3efebf992645 | — |
| 705 | 3.375 | RESEARCH | LDAP and Federation | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-a83ebb3f0b61 | — |
| 706 | 3.375 | RESEARCH | Cedar forbid-only policy patterns for Atlas | Atlas Resource Policies Cedar | dr | frontier | mongodb-cohort-0594c62af41d | — |
| 707 | 3.375 | RESEARCH | Matryoshka and quantization-aware embedding models | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-3efebf992645 | — |
| 708 | 3.375 | RESEARCH | Atlas Log Push SIEM | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-1525e6d34833 | — |
| 709 | 3.375 | RESEARCH | Realm Migration Paths | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-faa5aa005f8b | — |
| 710 | 3.375 | RESEARCH | Session Windows | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-40309c756b09 | — |
| 711 | 3.350 | RESEARCH | MongoSync GA Tool | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-0d0939aba268 | — |
| 712 | 3.350 | RESEARCH | Change Point Detection | MongoDB Performance Regression Detection and Testing Methodology | dr | frontier | mongodb-cohort-a0a420b316d1 | — |
| 713 | 3.350 | RESEARCH | Interval evaluation trees and parameterized plan caching | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-46673b83291a | — |
| 714 | 3.350 | RESEARCH | dropIndexes abort semantics | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | covered | mongodb-cohort-6c00ac0035c3 | — |
| 715 | 3.350 | RESEARCH | Matryoshka Dimension Truncation for Vector Storage Cost | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling | dr | covered | mongodb-cohort-676df347efbf | — |
| 716 | 3.350 | RESEARCH | min()/max() requiring hint | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-ca60df035474 | — |
| 717 | 3.350 | RESEARCH | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-069334033db9 | — |
| 718 | 3.350 | RESEARCH | Scheduled and Predictive Scaling for Atlas Cost | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO | dr | covered | mongodb-cohort-709a6f4ae7c9 | — |
| 719 | 3.325 | SKIP | Atlas Performance Advisor drop-index recommendations | Hidden indexes and safe index removal; Unused index detection with $indexStats | dr | frontier | mongodb-cohort-4d7e60c43906 | — |
| 720 | 3.325 | RESEARCH | Atlas Activity Feed | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-59597c811d2a | — |
| 721 | 3.325 | RESEARCH | FedRAMP and AtlasGov | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-272a1048a22c | — |
| 722 | 3.325 | RESEARCH | Google Workspace SAML Federation | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-511384aadb70 | — |
| 723 | 3.325 | RESEARCH | Ops Manager Architecture | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-6a1c409b355b | — |
| 724 | 3.325 | RESEARCH | CI Performance Regression Gating | MongoDB Performance Regression Detection and Testing Methodology | dr | frontier | mongodb-cohort-a0a420b316d1 | — |
| 725 | 3.325 | RESEARCH | Azure OpenAI Atlas Vector Search | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-2618e44302ce | — |
| 726 | 3.325 | RESEARCH | GCP Shared VPC | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-367067ba7a92 | — |
| 727 | 3.325 | REFRESH | MongoDB Realm Mobile Sync | MongoDB Atlas | revisit | refresh-review | mongodb-cohort-faa5aa005f8b | — |
| 728 | 3.325 | RESEARCH | Vertex AI Atlas Vector Search | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-2618e44302ce | — |
| 729 | 3.325 | RESEARCH | Atlas Application Insights OTel | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-a6b03cd32221 | — |
| 730 | 3.325 | RESEARCH | Atlas Infinite fixed-IOPS tiers and decoupled storage | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-b7c969c2a118 | — |
| 731 | 3.300 | RESEARCH | Stream Processor Pipeline | MongoDB Atlas Stream Processing | dr | frontier | mongodb-cohort-5ceedb05d0f7 | — |
| 732 | 3.300 | RESEARCH | Azure Key Vault RBAC Atlas | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-3e9502b80e34 | — |
| 733 | 3.300 | RESEARCH | Hub-and-Spoke Atlas Networking | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-fb5f4021932f | — |
| 734 | 3.300 | RESEARCH | Common Failure Modes | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-6a1c409b355b | — |
| 735 | 3.300 | RESEARCH | Dynamic bucket sizing and cache-pressure closures | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 736 | 3.300 | RESEARCH | Quantization-aware and Matryoshka embeddings (voyage-3-large) with Atlas dimension slicing | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-2618e44302ce | — |
| 737 | 3.300 | RESEARCH | Atlas Infinite oplog and storage-layer replication | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 738 | 3.300 | RESEARCH | Counter-document pattern | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-6a7dac291e46 | — |
| 739 | 3.300 | RESEARCH | Field-name abbreviation trade-offs | Schema Design for Storage Cost; Storage and Data-Lifecycle Cost Levers | dr | frontier | mongodb-cohort-d4596a7c1ce4 | — |
| 740 | 3.300 | RESEARCH | M10 shared-vCPU dedicated tier economics | Atlas Flex Pricing and Flex-vs-Dedicated Break-Even; Atlas Pricing Programs, Cost Governance and TCO | dr | frontier | mongodb-cohort-b7c969c2a118 | — |
| 741 | 3.300 | RESEARCH | Natural language to MongoDB query generation | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-8774765806eb | — |
| 742 | 3.300 | RESEARCH | Region and Cloud Provider Price Differentials for Atlas | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO | dr | covered | mongodb-cohort-709a6f4ae7c9 | — |
| 743 | 3.300 | RESEARCH | Tailable cursors and maxAwaitTimeMS | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-6a7dac291e46 | — |
| 744 | 3.275 | RESEARCH | Coefficient of Variation / Run-to-Run Noise Control | MongoDB Performance Regression Detection and Testing Methodology | dr | frontier | mongodb-cohort-803bb5221982 | — |
| 745 | 3.275 | RESEARCH | Ops Manager Application | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-6a1c409b355b | — |
| 746 | 3.275 | RESEARCH | Service Account per Environment Pattern | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-d9a82186dbd1 | — |
| 747 | 3.275 | RESEARCH | Eviction thread sizing and wiredTigerEngineRuntimeConfig tuning | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-b7c969c2a118 | — |
| 748 | 3.275 | RESEARCH | V2 and V3 compressed buckets and unsorted conversion | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 749 | 3.275 | RESEARCH | Atlas Audit Logs Cloud Logging | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-b0e4f880a1a3 | — |
| 750 | 3.250 | RESEARCH | Archive Monitoring | MongoDB Atlas Online Archive | dr | frontier | mongodb-cohort-68b4130466d8 | — |
| 751 | 3.250 | RESEARCH | Atlas index build tier defaults | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-88cc8939dcad | — |
| 752 | 3.250 | RESEARCH | Atlas tier-fixed index build limits | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-88cc8939dcad | — |
| 753 | 3.250 | RESEARCH | Benchmarking Anti-Patterns | MongoDB Performance Benchmarking | dr | frontier | mongodb-cohort-441524d0c05b | — |
| 754 | 3.250 | RESEARCH | Capacity Testing | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-1d798a0d85d1 | — |
| 755 | 3.250 | RESEARCH | Growth Signals | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-1d798a0d85d1 | — |
| 756 | 3.250 | RESEARCH | New Relic Integration | MongoDB Monitoring and Observability | dr | frontier | mongodb-cohort-e4e31a146993 | — |
| 757 | 3.250 | RESEARCH | Cloud Build Atlas API Auth | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-aa8dae0ac5e2 | — |
| 758 | 3.250 | RESEARCH | GKE NodeLocal DNSCache Atlas | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-e97ebaff6742 | — |
| 759 | 3.250 | RESEARCH | Cloud HSM Atlas | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-e97ebaff6742 | — |
| 760 | 3.250 | RESEARCH | MongoDB 8.0 autoCompact background compaction on Atlas | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-733862797816 | — |
| 761 | 3.250 | RESEARCH | IAM Role Atlas API Access | Global AI Hub Research Corpus | dr | frontier | mongodb-cohort-d9a82186dbd1 | — |
| 762 | 3.250 | RESEARCH | Atlas AI Services Pricing (Agent Engine and Voyage AI) | Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-709a6f4ae7c9 | — |
| 763 | 3.250 | RESEARCH | Atlas backup/PITR and data transfer cost drivers | Atlas Pricing Programs, Cost Governance and TCO; Self-Managed MongoDB vs Atlas TCO | dr | frontier | mongodb-cohort-372a6407eb6e | — |
| 764 | 3.250 | RESEARCH | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-1a42b3c0d1f3 | — |
| 765 | 3.250 | RESEARCH | Ranked and scored input pipeline eligibility | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | refresh-review | mongodb-cohort-c40e2099a647 | — |
| 766 | 3.250 | RESEARCH | Reading slotBasedPlan explain output for time series | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-98d2158f395e | — |
| 767 | 3.250 | RESEARCH | Resource Policy Drift Monitoring (nonCompliantResources) | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling | dr | covered | mongodb-cohort-88f6ca74e8c0 | — |
| 768 | 3.250 | RESEARCH | Shard Key Design and Resharding as Cost Levers | MongoDB Atlas Cost Optimization; Sharded Cluster Cost Economics | dr | covered | mongodb-cohort-709a6f4ae7c9 | — |
| 769 | 3.225 | RESEARCH | Atlas Organization Teams | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-59597c811d2a | — |
| 770 | 3.225 | RESEARCH | Blockstore Snapshot Storage | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-835ffca778c9 | — |
| 771 | 3.225 | RESEARCH | Flexible Sync | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-faa5aa005f8b | — |
| 772 | 3.225 | RESEARCH | PCI DSS Scoping and Tokenization | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-272a1048a22c | — |
| 773 | 3.225 | RESEARCH | HTTP Data Access Replacements | MongoDB BI Connector and SQL Access | dr | frontier | mongodb-cohort-c84c26fc913e | — |
| 774 | 3.225 | RESEARCH | Express path for _id lookups on sharded collections | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 775 | 3.200 | RESEARCH | Compass CRUD and Documents Tab | MongoDB Compass | dr | frontier | mongodb-cohort-b63ded16c61f | — |
| 776 | 3.200 | SKIP | GCP Private Service Connect | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-367067ba7a92 | — |
| 777 | 3.200 | RESEARCH | MongoDB CBR CE source metadata | ceSource cardinality estimation (sampling vs heuristics) | dr | frontier | mongodb-cohort-bae29937ea6d | — |
| 778 | 3.200 | RESEARCH | Schema Transformation | MongoDB Migration Patterns | dr | frontier | mongodb-cohort-a60b195db1d3 | — |
| 779 | 3.200 | RESEARCH | RAG Patterns | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-77fb33304703 | — |
| 780 | 3.200 | RESEARCH | RAG Patterns with Vector Search | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-2618e44302ce | — |
| 781 | 3.200 | RESEARCH | Atlas Bicep Private Endpoint | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-fb5f4021932f | — |
| 782 | 3.200 | RESEARCH | Atlas CLI Terraform Plugin | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-aa8dae0ac5e2 | — |
| 783 | 3.200 | RESEARCH | Atlas nonCompliantResources endpoint | Atlas Resource Policies Cedar | dr | frontier | mongodb-cohort-0bd972ad850c | — |
| 784 | 3.200 | RESEARCH | Admin API alert configurations for billing events | Atlas Billing Mechanics and Cost Visibility; Billing Alerts and Budget Controls | dr | covered | mongodb-cohort-0b5e4ac764ba | — |
| 785 | 3.200 | SKIP | Atlas Query Shape Insights | MongoDB Explain Plans, Query Planner and Plan Cache | dr | frontier | mongodb-cohort-44e99a657c0c | — |
| 786 | 3.200 | SKIP | Atlas Vector Search automatic quantization and rescoring | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Matryoshka Dimension Truncation for Vector Storage Cost; Vector Search Quantization and Embedding Storage Cost | dr | covered | mongodb-cohort-676df347efbf | — |
| 787 | 3.200 | RESEARCH | Index Sufficiency Warning | Archive Rules | revisit | refresh-review | mongodb-cohort-4d7e60c43906 | — |
| 788 | 3.200 | SKIP | Namespace Insights | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | frontier | mongodb-cohort-9fc6f09a3009 | — |
| 789 | 3.200 | RESEARCH | Sparse and partial indexes for $exists | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-0d1e62176238 | — |
| 790 | 3.200 | RESEARCH | transformIdentifiers HMAC privacy mode | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-542b6e07af2f | — |
| 791 | 3.200 | RESEARCH | Unlinking marketplace billing safely | Atlas Billing Mechanics and Cost Visibility; Cloud Marketplace Billing for Atlas (AWS GCP Azure) | dr | covered | mongodb-cohort-0b5e4ac764ba | — |
| 792 | 3.175 | RESEARCH | Atlas Search Nodes | MongoDB Atlas Search | dr | frontier | mongodb-cohort-a52306435b73 | — |
| 793 | 3.175 | RESEARCH | Search Nodes | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-a52306435b73 | — |
| 794 | 3.175 | RESEARCH | Partition-Based Sync (Legacy) | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-0ecd8d6fb6f0 | — |
| 795 | 3.175 | RESEARCH | Atlas Search Lucene Architecture | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-a52306435b73 | — |
| 796 | 3.175 | RESEARCH | Encryption Requirements (At-Rest, In-Transit, Field-Level) | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-3e9502b80e34 | — |
| 797 | 3.175 | RESEARCH | Organization-scoped alert configuration API | Admin API alert configurations for billing events | dr | frontier | mongodb-cohort-32c3803915b5 | — |
| 798 | 3.175 | RESEARCH | Atlas GraphQL API Removal | Atlas Data API Removal; MongoDB BI Connector and SQL Access | dr | frontier | mongodb-cohort-32c3803915b5 | — |
| 799 | 3.175 | RESEARCH | Compass Performance Insights | MongoDB Compass | dr | frontier | mongodb-cohort-b63ded16c61f | — |
| 800 | 3.175 | RESEARCH | Azure Service Bus Atlas Triggers | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-a6b03cd32221 | — |
| 801 | 3.175 | RESEARCH | Lambda Managed Instances and MongoClient concurrency safety | Lambda MongoDB Driver Pattern | dr | frontier | mongodb-cohort-32c3803915b5 | — |
| 802 | 3.175 | RESEARCH | Atlas Infinite storage model (max storage limit, no auto-scaling) | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-733862797816 | — |
| 803 | 3.150 | RESEARCH | Search Highlighting | MongoDB Atlas Search | dr | frontier | mongodb-cohort-8ff70ee25045 | — |
| 804 | 3.150 | RESEARCH | replSetResizeOplog and oplog compaction runbook | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-37fc02336c5b | — |
| 805 | 3.150 | RESEARCH | Atlas Programmatic API Keys (Legacy) | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-3e9502b80e34 | — |
| 806 | 3.150 | RESEARCH | Partition Field Count Limits (DATE vs CUSTOM) | Partition Fields | dr | frontier | mongodb-cohort-1e99b9bf1966 | — |
| 807 | 3.150 | RESEARCH | Atlas IaC Anti-Patterns | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-7b807b8ba86d | — |
| 808 | 3.150 | RESEARCH | Trigger and Function Anti-Patterns | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f6ac572aba6f | — |
| 809 | 3.150 | RESEARCH | Compliance Gaps and Shared Responsibility | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-d624439a89da | — |
| 810 | 3.150 | RESEARCH | atlas kubernetes config generate | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-32c3803915b5 | — |
| 811 | 3.150 | RESEARCH | Multi-Org Scale Patterns | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-6a1c409b355b | — |
| 812 | 3.150 | RESEARCH | Atlas Infinite fixed per-tier IOPS and public-preview feature exclusions | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-88cc8939dcad | — |
| 813 | 3.150 | RESEARCH | Primary-driven index builds (spill to a replicated table) | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-7cd1c9c93f1a | — |
| 814 | 3.150 | SKIP | $function and server-side JavaScript hardening | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-9cff09d95361 | — |
| 815 | 3.150 | SKIP | Atlas Charts billing dashboards | Atlas Billing Mechanics and Cost Visibility; Atlas Cost Explorer and Billing Data API | dr | frontier | mongodb-cohort-91cc19c76420 | — |
| 816 | 3.150 | SKIP | Atlas GraphQL API (EOL) | MongoDB Atlas App Services | dr | frontier | mongodb-cohort-4308c7661d27 | — |
| 817 | 3.150 | SKIP | Atlas SQL Schema Builder | Atlas SQL Interface MongoSQL | revisit | refresh-review | mongodb-cohort-d53c2a9ffb01 | — |
| 818 | 3.150 | SKIP | Credit expiry and History table | Atlas Billing Mechanics and Cost Visibility; Atlas Credits Prepaid Subscriptions and Overage | dr | frontier | mongodb-cohort-91cc19c76420 | — |
| 819 | 3.150 | SKIP | Custom HTTPS Endpoints (EOL) | MongoDB Atlas App Services | dr | frontier | mongodb-cohort-a337172ad861 | — |
| 820 | 3.150 | SKIP | Hashed Indexes | MongoDB Indexes Deep Dive | dr | frontier | mongodb-cohort-0d1e62176238 | — |
| 821 | 3.150 | SKIP | Index hints on time series collections | MongoDB Time-Series Query and Index Optimization | dr | frontier | mongodb-cohort-7e83aa58193c | — |
| 822 | 3.150 | SKIP | JIT user provisioning | Atlas Federated Authentication | revisit | refresh-review | mongodb-cohort-f989d473b7e1 | — |
| 823 | 3.150 | SKIP | Text Indexes | MongoDB Indexes Deep Dive | dr | frontier | mongodb-cohort-0d1e62176238 | — |
| 824 | 3.150 | SKIP | TTL Indexes | MongoDB Indexes Deep Dive | dr | frontier | mongodb-cohort-0d1e62176238 | — |
| 825 | 3.125 | RESEARCH | Multi-Environment Terraform Directories vs Workspaces | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-4308c7661d27 | — |
| 826 | 3.125 | RESEARCH | Atlas Cluster IaC | MongoDB Atlas Terraform Provider | dr | frontier | mongodb-cohort-ac926399aa55 | — |
| 827 | 3.125 | RESEARCH | Atlas Azure Regions Mapping | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-949f44190f7a | — |
| 828 | 3.125 | RESEARCH | Error Code Lookup | MongoDB KB Articles | dr | frontier | mongodb-cohort-29539c2a7d1c | — |
| 829 | 3.125 | RESEARCH | GCP Regions Atlas Mapping | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-e97ebaff6742 | — |
| 830 | 3.100 | RESEARCH | Atlas Envelope Encryption GCP | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-2030af7213e7 | — |
| 831 | 3.100 | RESEARCH | Sync Configuration | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-0ecd8d6fb6f0 | — |
| 832 | 3.100 | RESEARCH | Breaking-point / overload testing methodology (first bottleneck vs visible symptom, cascading failure, thundering herd, cache-eviction death spiral) | MongoDB Stress, Soak, and Chaos-Resilience Testing | dr | frontier | mongodb-cohort-22db29b88ceb | — |
| 833 | 3.100 | RESEARCH | Cache-derived dynamic bucket size limit | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 834 | 3.100 | RESEARCH | Dynamic bucket size cap under cache pressure | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bd6489c69c3d | — |
| 835 | 3.100 | RESEARCH | Atlas Data Federation GCS | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-a7061a319c83 | — |
| 836 | 3.100 | SKIP | Atlas marketplace private offers | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit) | dr | frontier | mongodb-cohort-91cc19c76420 | — |
| 837 | 3.100 | SKIP | Client Side Field Level Encryption (CSFLE) | Client Side Operations Timeout (CSOT) | revisit | refresh-review | mongodb-cohort-2030af7213e7 | — |
| 838 | 3.100 | SKIP | Gen1 vs Gen2 storage and IOPS billing | Atlas Cluster Topology and Tier Economics; Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe); Storage Growth and IOPS Forecasting for Cost | dr | frontier | mongodb-cohort-91cc19c76420 | — |
| 839 | 3.100 | SKIP | HNSW Index Parameters | MongoDB Atlas Vector Search | dr | frontier | mongodb-cohort-326a9da785a4 | — |
| 840 | 3.100 | SKIP | SBE $lookup pushdown and hash join | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | frontier | mongodb-cohort-468120abc19f | — |
| 841 | 3.100 | SKIP | Search Index Mapping | MongoDB Atlas Search | dr | frontier | mongodb-cohort-b58330cefc6d | — |
| 842 | 3.075 | RESEARCH | Realm Object Model | MongoDB Atlas Device SDK; MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-0ecd8d6fb6f0 | — |
| 843 | 3.075 | RESEARCH | Shared-cost allocation rules for managed database services | Atlas tag taxonomy for showback and chargeback | dr | frontier | mongodb-cohort-c8ad8a77bff0 | — |
| 844 | 3.075 | RESEARCH | eviction_updates_trigger and the updates ratio | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 845 | 3.075 | RESEARCH | Realm Migration | MongoDB Atlas Device SDK | dr | frontier | mongodb-cohort-0ecd8d6fb6f0 | — |
| 846 | 3.075 | RESEARCH | Restore Workflows | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-52b87d174a64 | — |
| 847 | 3.050 | RESEARCH | available read concern | Read Concern Levels | dr | frontier | mongodb-cohort-7cd1c9c93f1a | — |
| 848 | 3.050 | RESEARCH | Programmatic API Keys Legacy Auth | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-2030af7213e7 | — |
| 849 | 3.050 | RESEARCH | Filesystem Snapshot Storage | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-835ffca778c9 | — |
| 850 | 3.050 | RESEARCH | Azure Private DNS Resolver | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-fb5f4021932f | — |
| 851 | 3.050 | RESEARCH | Same-field `$or` to `$in` rewrite | Compound index vs index union for $or | dr | frontier | mongodb-cohort-68aac318a142 | — |
| 852 | 3.050 | RESEARCH | Sustained overload / soak testing (memory leaks, connection pool exhaustion, WiredTiger cache thrashing, ticket starvation, oplog window shrinkage) | MongoDB Stress, Soak, and Chaos-Resilience Testing | dr | frontier | mongodb-cohort-22db29b88ceb | — |
| 853 | 3.050 | RESEARCH | Atlas LDAPS (Deprecated 8.0) | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-59597c811d2a | — |
| 854 | 3.050 | REFRESH | MongoDB Developer Patterns | MongoDB Expert Knowledge | revisit | refresh-review | mongodb-cohort-586d5ccba289 | — |
| 855 | 3.050 | RESEARCH | Azure Synapse Atlas Data Federation | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-e1eb00faceff | — |
| 856 | 3.050 | RESEARCH | AKO Dry Run Mode | MongoDB Atlas Infrastructure as Code | dr | frontier | mongodb-cohort-a634f98f5cef | — |
| 857 | 3.050 | RESEARCH | Gen1 vs Gen2 IOPS billing | Storage Growth and IOPS Forecasting for Cost | dr | frontier | mongodb-cohort-c8ad8a77bff0 | — |
| 858 | 3.050 | SKIP | Atlas Admin API invoice endpoints | Atlas Billing and Invoice Anatomy; Atlas Billing Mechanics and Cost Visibility | dr | frontier | mongodb-cohort-4308c7661d27 | — |
| 859 | 3.050 | SKIP | Atlas Infinite compute auto-scaling | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 860 | 3.050 | SKIP | Auto-scaling tier ranges | Atlas Cluster Topology and Tier Economics; Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe) | dr | frontier | mongodb-cohort-88cc8939dcad | — |
| 861 | 3.050 | SKIP | Backup and PITR cost modelling | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator) | dr | frontier | mongodb-cohort-c8ad8a77bff0 | — |
| 862 | 3.050 | SKIP | Cedar policy authoring for cluster size and autoscaling caps | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Resource Policy Drift Monitoring (nonCompliantResources) | dr | frontier | mongodb-cohort-047d3a5eff67 | — |
| 863 | 3.050 | SKIP | Memory Limits and allowDiskUse | MongoDB Aggregation Pipeline | revisit | refresh-review | mongodb-cohort-8f2fb9450e90 | — |
| 864 | 3.050 | SKIP | Multi-region cluster cost premium | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Region and Cloud Provider Price Differentials for Atlas | dr | frontier | mongodb-cohort-c8ad8a77bff0 | — |
| 865 | 3.050 | SKIP | Pause/resume automation with Terraform or GitHub Actions | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | frontier | mongodb-cohort-4308c7661d27 | — |
| 866 | 3.050 | SKIP | Right-sizing from Atlas metrics | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator) | dr | frontier | mongodb-cohort-047d3a5eff67 | — |
| 867 | 3.025 | RESEARCH | Databricks Workspace Integration | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a8bd98441f1a | — |
| 868 | 3.025 | RESEARCH | Reconciliation and Page Splitting | WiredTiger Storage Engine Internals | dr | frontier | mongodb-cohort-ae873d2f56e0 | — |
| 869 | 3.025 | RESEARCH | Spark Connector V10 Architecture | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a8bd98441f1a | — |
| 870 | 3.025 | RESEARCH | Baseline Methodology | MongoDB Performance Benchmarking | dr | frontier | mongodb-cohort-441524d0c05b | — |
| 871 | 3.025 | RESEARCH | Common Sizing Mistakes | MongoDB Capacity Planning | dr | frontier | mongodb-cohort-047d3a5eff67 | — |
| 872 | 3.025 | RESEARCH | Upgrade event coverage (pre/during/post) | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-b7cbe85f979c | — |
| 873 | 3.025 | RESEARCH | EU Data Act switching charges and in-parallel egress | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 874 | 3.025 | RESEARCH | Atlas App Services Cost Model | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-ec3558b1401a | — |
| 875 | 3.025 | RESEARCH | AtlasGov Azure Government | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-949f44190f7a | — |
| 876 | 3.000 | SKIP | Rolling index builds as a resource-limited alternative | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-b58330cefc6d | — |
| 877 | 3.000 | RESEARCH | minor-version compatibility rule | MongoDB Java driver 5.x version timeline & 8.0 compatibility | dr | frontier | mongodb-cohort-52a06240c41f | — |
| 878 | 3.000 | RESEARCH | Archive Anti-Patterns | MongoDB Atlas Online Archive | dr | frontier | mongodb-cohort-252dc4668191 | — |
| 879 | 3.000 | RESEARCH | Backup Anti-Patterns | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-52b87d174a64 | — |
| 880 | 3.000 | RESEARCH | Automated Embedding (autoEmbed) quantization types | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-326a9da785a4 | — |
| 881 | 3.000 | RESEARCH | Automated Embedding (autoEmbed) quantization types including binaryNoRescore | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-326a9da785a4 | — |
| 882 | 3.000 | RESEARCH | Spill WiredTiger instance cache | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-1f33141d477d | — |
| 883 | 3.000 | RESEARCH | WiredTiger spill instance cache | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-1f33141d477d | — |
| 884 | 3.000 | SKIP | $groupByDistinct internal stage | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | frontier | mongodb-cohort-468120abc19f | — |
| 885 | 3.000 | SKIP | Analytics node tier prorating | Atlas Cluster Topology and Tier Economics; Replica Set Node Topology Cost | dr | frontier | mongodb-cohort-047d3a5eff67 | — |
| 886 | 3.000 | SKIP | App Services Deployment Model | MongoDB Atlas App Services | dr | frontier | mongodb-cohort-5e7b26f7bdcf | — |
| 887 | 3.000 | SKIP | App Services Rules and Permissions | MongoDB Atlas App Services | dr | frontier | mongodb-cohort-5e7b26f7bdcf | — |
| 888 | 3.000 | SKIP | App Services Schema Validation | MongoDB Atlas App Services | revisit | refresh-review | mongodb-cohort-5e7b26f7bdcf | — |
| 889 | 3.000 | SKIP | App Services Values and Secrets | MongoDB Atlas App Services | revisit | refresh-review | mongodb-cohort-5e7b26f7bdcf | — |
| 890 | 3.000 | SKIP | Atlas-only feature lock-in and exit cost | Atlas Pricing Programs, Cost Governance and TCO; Self-Managed MongoDB vs Atlas TCO | dr | frontier | mongodb-cohort-ec3558b1401a | — |
| 891 | 3.000 | SKIP | AWS Marketplace EDP drawdown for Atlas | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit) | dr | frontier | mongodb-cohort-ec3558b1401a | — |
| 892 | 3.000 | SKIP | Backup and PIT oplog storage region billing | Atlas Cluster Topology and Tier Economics; Multi-Region and Cross-Cloud Data Transfer Costs | dr | frontier | mongodb-cohort-ec3558b1401a | — |
| 893 | 3.000 | SKIP | Cost Explorer filters for AI services | Atlas AI Services Pricing (Agent Engine and Voyage AI); Atlas Pricing Programs, Cost Governance and TCO | dr | frontier | mongodb-cohort-e570f811eac4 | — |
| 894 | 3.000 | SKIP | MongoSQL ODBC Driver | Atlas SQL Interface MongoSQL | revisit | refresh-review | mongodb-cohort-7bd3b5b8b388 | — |
| 895 | 3.000 | SKIP | Performance Diagnostic Workflow | MongoDB Performance Troubleshooting | dr | frontier | mongodb-cohort-68222234dd24 | — |
| 896 | 3.000 | SKIP | PII Masking & Query Hash Anonymization | Diagnostic Tool Design | revisit | refresh-review | mongodb-cohort-d624439a89da | — |
| 897 | 3.000 | SKIP | Power BI DirectQuery | Atlas SQL Interface MongoSQL | revisit | refresh-review | mongodb-cohort-44e99a657c0c | — |
| 898 | 3.000 | SKIP | Query limits and billing alerts for archive spend | Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation); Storage and Data-Lifecycle Cost Levers | dr | frontier | mongodb-cohort-e570f811eac4 | — |
| 899 | 3.000 | SKIP | Support line items per cloud provider on invoices | Atlas Billing Mechanics and Cost Visibility; Atlas Support Plan Pricing | dr | frontier | mongodb-cohort-7b4b502e3f24 | — |
| 900 | 3.000 | SKIP | Unique Indexes | MongoDB Indexes Deep Dive | dr | frontier | mongodb-cohort-b58330cefc6d | — |
| 901 | 2.975 | RESEARCH | Network Security Layers | MongoDB Security Architecture | dr | frontier | mongodb-cohort-631639b707f5 | — |
| 902 | 2.975 | RESEARCH | Atlas LDAP Azure AD DS | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-dfaf850dab9b | — |
| 903 | 2.975 | RESEARCH | Connection Pool Benchmarking | MongoDB Performance Benchmarking | dr | frontier | mongodb-cohort-b245a56e13e9 | — |
| 904 | 2.975 | RESEARCH | Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure) | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 905 | 2.975 | RESEARCH | Cloud exit-credit programs and EU Data Act in-parallel egress | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-de1c0f2fac41 | — |
| 906 | 2.975 | RESEARCH | Atlas Infinite oplog and storage cost | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-e570f811eac4 | — |
| 907 | 2.950 | RESEARCH | Atlas Three-Tier Identity Model | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-511384aadb70 | — |
| 908 | 2.950 | RESEARCH | Idle-spend and minimum-commit economics of serverless vector stores | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-326a9da785a4 | — |
| 909 | 2.950 | RESEARCH | Azure Native MongoDB ANM | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-949f44190f7a | — |
| 910 | 2.950 | RESEARCH | Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-03e4970d4503 | — |
| 911 | 2.950 | SKIP | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling | Atlas Billing and Invoice Anatomy; Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Atlas Cost Explorer and Billing Data API; Cloud Marketplace Billing for Atlas (AWS GCP Azure); Cost Governance Guardrails (Resource Policies and IaC Cost Controls); FinOps Framework Applied to Atlas; MongoDB Atlas Cost Optimization; Resource Tags and Cost Allocation (Showback/Chargeback); Vector Search Quantization and Embedding Storage Cost | dr | covered | mongodb-cohort-0b5e4ac764ba | — |
| 912 | 2.950 | SKIP | Block Compression (snappy/zlib/zstd) | MongoDB Atlas Cost Optimization; MongoDB Atlas Online Archive; mongodb-time-series; WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-9d537d138113 | the research suite run mongodb-2026-10-14 |
| 913 | 2.950 | SKIP | Compass Index Management | MongoDB Compass | dr | frontier | mongodb-cohort-b58330cefc6d | — |
| 914 | 2.950 | SKIP | DATE criteria field types and formats | DATE Criteria | revisit | refresh-review | mongodb-cohort-49ee480ab53f | — |
| 915 | 2.950 | SKIP | Enterprise Advanced licensing economics | Atlas Pricing Programs, Cost Governance and TCO; Self-Managed MongoDB vs Atlas TCO | dr | frontier | mongodb-cohort-d75e388f7c62 | — |
| 916 | 2.950 | SKIP | Project-level billing change alerts | Atlas Billing Mechanics and Cost Visibility; Billing Alerts and Budget Controls | dr | frontier | mongodb-cohort-e570f811eac4 | — |
| 917 | 2.950 | SKIP | Shared-cost splitting for Atlas projects | Atlas Billing Mechanics and Cost Visibility; Resource Tags and Cost Allocation (Showback/Chargeback) | dr | frontier | mongodb-cohort-6adc93138105 | — |
| 918 | 2.950 | SKIP | Stored Source Performance Optimization | MongoDB Atlas Search and Vector Search | dr | frontier | mongodb-cohort-0700af48832c | — |
| 919 | 2.925 | RESEARCH | Refresh scheduling with Atlas Scheduled Triggers | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 920 | 2.925 | RESEARCH | positional index path caveat | explain multiKeyPaths interpretation | dr | frontier | mongodb-cohort-e4ebaf2ad65a | — |
| 921 | 2.900 | RESEARCH | Performance Tuning Checklist | MongoDB Spark Connector and Databricks Integration | dr | frontier | mongodb-cohort-a8bd98441f1a | — |
| 922 | 2.900 | RESEARCH | Enterprise Advanced Licensing | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-b956cbf404fd | — |
| 923 | 2.900 | RESEARCH | maxEstimatedScanBytes collection-scan rejection (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-4b089bde7a44 | — |
| 924 | 2.900 | SKIP | Network (wire) compression | Storage and Data-Lifecycle Cost Levers; WiredTiger Block and Prefix Compression as Storage Cost Lever | dr | frontier | mongodb-cohort-1537f1c9f03c | — |
| 925 | 2.875 | RESEARCH | Atlas Search Architecture | MongoDB Atlas Search | dr | frontier | mongodb-cohort-8ff70ee25045 | — |
| 926 | 2.875 | RESEARCH | Backup Daemon and Head DB | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-66a976b0eee5 | — |
| 927 | 2.875 | RESEARCH | Atlas IAM Compliance Mapping | MongoDB Atlas IAM and RBAC | dr | frontier | mongodb-cohort-d624439a89da | — |
| 928 | 2.875 | RESEARCH | Ops Manager LDAP/Kerberos/SAML/OIDC Federation | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-511384aadb70 | — |
| 929 | 2.875 | RESEARCH | Side bucket catalog | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bd6489c69c3d | — |
| 930 | 2.875 | RESEARCH | Side bucket catalog for time series updates and deletes | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bd6489c69c3d | — |
| 931 | 2.875 | RESEARCH | Atlas Alerts Pub/Sub Escalation | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-0d11435299da | — |
| 932 | 2.875 | RESEARCH | Atlas Azure Monitor Metrics | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-d369cc167fa2 | — |
| 933 | 2.875 | RESEARCH | Atlas Sentinel Log Integration | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-d369cc167fa2 | — |
| 934 | 2.875 | RESEARCH | Cloud Monitoring Atlas Metrics | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-0d11435299da | — |
| 935 | 2.850 | RESEARCH | Atlas Compliance Certifications | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-d624439a89da | — |
| 936 | 2.850 | RESEARCH | Learning Paths by Role | MongoDB University & Certification | dr | frontier | mongodb-cohort-8b6b0620aca1 | — |
| 937 | 2.850 | RESEARCH | Serverless Cold Start Behavior | MongoDB Atlas Flex and Serverless Tiers | dr | frontier | mongodb-cohort-3218ab1d6cd5 | — |
| 938 | 2.850 | RESEARCH | Oplog sizing in Kubernetes operators and managed MongoDB-compatible services | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-d75e388f7c62 | — |
| 939 | 2.850 | RESEARCH | Partition Field Type Enum Docs-vs-Spec Disagreement | Partition Fields | dr | frontier | mongodb-cohort-1e99b9bf1966 | — |
| 940 | 2.850 | SKIP | allowDiskUse-100MB-stage | mongodb-aggregation-stages-deep | dr | frontier | mongodb-cohort-f5126bc4749e | — |
| 941 | 2.850 | SKIP | Auto-scaling min/max bounds and Terraform drift | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | frontier | mongodb-cohort-c2b116f7efea | — |
| 942 | 2.850 | SKIP | Compass Aggregation Pipeline Builder | MongoDB Compass | dr | frontier | mongodb-cohort-0b99f427bf56 | — |
| 943 | 2.850 | SKIP | Compass Natural Language Query | MongoDB Compass | dr | frontier | mongodb-cohort-44e99a657c0c | — |
| 944 | 2.850 | SKIP | Config shard versus dedicated config server cost | Atlas Cluster Topology and Tier Economics; Sharded Cluster Cost Economics | dr | frontier | mongodb-cohort-6adc93138105 | — |
| 945 | 2.850 | SKIP | MongoDB Charts billing dashboards | Atlas Billing Mechanics and Cost Visibility; Resource Tags and Cost Allocation (Showback/Chargeback) | dr | frontier | mongodb-cohort-6adc93138105 | — |
| 946 | 2.850 | SKIP | Persisting index usage metrics across restarts (PMM/monitoring) | MongoDB Explain Plans, Query Planner and Plan Cache | dr | frontier | mongodb-cohort-e4ebaf2ad65a | — |
| 947 | 2.850 | SKIP | Scale-down tuning for spiky batch workloads | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 948 | 2.825 | RESEARCH | Amazon DocumentDB profiler (CloudWatch Logs) | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-9767e9fb3174 | — |
| 949 | 2.825 | RESEARCH | mongosqld Architecture | MongoDB BI Connector and SQL Access | dr | frontier | mongodb-cohort-c7655b542f60 | — |
| 950 | 2.825 | RESEARCH | BI Connector Authentication | MongoDB BI Connector and SQL Access | dr | frontier | mongodb-cohort-72ec775bc1f4 | — |
| 951 | 2.825 | RESEARCH | Bucket catalog stripes, state registry and eras | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bd6489c69c3d | — |
| 952 | 2.800 | RESEARCH | DRDL Schema Management | MongoDB BI Connector and SQL Access | dr | frontier | mongodb-cohort-eebdcce5b375 | — |
| 953 | 2.800 | SKIP | Client-side operation timeout (CSOT) | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-9cff09d95361 | — |
| 954 | 2.800 | SKIP | Collation-based case-insensitive indexes as a $regex alternative | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | frontier | mongodb-cohort-e4ebaf2ad65a | — |
| 955 | 2.800 | SKIP | Intra-cluster replication transfer billing | Atlas Cluster Topology and Tier Economics; Replica Set Node Topology Cost | dr | frontier | mongodb-cohort-6adc93138105 | — |
| 956 | 2.800 | SKIP | Retroactive support billing on reactivation | Atlas Billing Mechanics and Cost Visibility; Atlas Support Plan Pricing | dr | frontier | mongodb-cohort-fd6aad8dc2b9 | — |
| 957 | 2.800 | SKIP | Single-Field Indexes | MongoDB Indexes Deep Dive | dr | frontier | mongodb-cohort-e4ebaf2ad65a | — |
| 958 | 2.800 | SKIP | Time series collection expireAfterSeconds | Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation); Storage and Data-Lifecycle Cost Levers | dr | frontier | mongodb-cohort-d945bf6ed1c3 | — |
| 959 | 2.775 | RESEARCH | Lucene BBQ binary quantization compared with Atlas binary quantization | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-03e4970d4503 | — |
| 960 | 2.775 | RESEARCH | Atlas Private DNS Zones Azure | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-fb5f4021932f | — |
| 961 | 2.775 | RESEARCH | Cloud DNS Private Zone for Atlas | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-367067ba7a92 | — |
| 962 | 2.750 | RESEARCH | Atlas Search Anti-Patterns | MongoDB Atlas Search | dr | frontier | mongodb-cohort-8ff70ee25045 | — |
| 963 | 2.750 | RESEARCH | Atlas Azure Security Compliance | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-9effc0514098 | — |
| 964 | 2.750 | RESEARCH | Audit-Ready Architecture and Evidence Collection | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-9effc0514098 | — |
| 965 | 2.750 | SKIP | Atlas billing alert configuration via Admin API | Atlas Pricing Programs, Cost Governance and TCO; Cost Governance Guardrails (Resource Policies and IaC Cost Controls) | dr | frontier | mongodb-cohort-fd6aad8dc2b9 | — |
| 966 | 2.725 | SKIP | Rolling index build key inconsistency incident | Rolling index builds | dr | frontier | mongodb-cohort-7cd1c9c93f1a | — |
| 967 | 2.725 | SKIP | Rolling index build table-logging incident | Rolling index builds | dr | frontier | mongodb-cohort-f73749345fb5 | — |
| 968 | 2.725 | RESEARCH | Percona PMM mongolog query source | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-44e99a657c0c | — |
| 969 | 2.700 | RESEARCH | Realm SDK Languages and Platforms | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-b245a56e13e9 | — |
| 970 | 2.700 | RESEARCH | Benchmark Result Reporting | MongoDB Performance Benchmarking | dr | frontier | mongodb-cohort-d276eb514345 | — |
| 971 | 2.700 | RESEARCH | Atlas MACC Eligibility | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-949f44190f7a | — |
| 972 | 2.700 | RESEARCH | Atlas Charts Integration | mongodb-time-series | dr | frontier | mongodb-cohort-2ff1852dc9f0 | — |
| 973 | 2.700 | RESEARCH | Partition Field Cardinality and the 2023-06-07 Storage Engine Change | Partition Fields | dr | frontier | mongodb-cohort-a29d8407e9dc | — |
| 974 | 2.700 | SKIP | Atlas PrivateLink regional endpoint rates | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Region and Cloud Provider Price Differentials for Atlas | dr | frontier | mongodb-cohort-18067a89fb07 | — |
| 975 | 2.700 | SKIP | Federated Query on Archive | MongoDB Atlas Online Archive | dr | frontier | mongodb-cohort-210d2a18c904 | — |
| 976 | 2.700 | SKIP | Geospatial $lookup Patterns | MongoDB Geospatial | dr | frontier | mongodb-cohort-0a2873eb4ed8 | — |
| 977 | 2.700 | SKIP | Quantile Estimation (DDSketch) | Client Side Operations Timeout (CSOT) | revisit | refresh-review | mongodb-cohort-f7898c0e7b37 | — |
| 978 | 2.675 | RESEARCH | Associate Developer Certification | MongoDB University & Certification | dr | frontier | mongodb-cohort-8b6b0620aca1 | — |
| 979 | 2.675 | RESEARCH | Atlas Terraform Azure Provider | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-c2b116f7efea | — |
| 980 | 2.675 | RESEARCH | Atlas Terraform GCP Provider | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-c2b116f7efea | — |
| 981 | 2.650 | SKIP | Atlas CLI Failure Scenarios | Atlas CLI | revisit | refresh-review | mongodb-cohort-c2b116f7efea | — |
| 982 | 2.650 | SKIP | Atlas included-replica pricing vs per-instance HA billing | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB) | dr | frontier | mongodb-cohort-fd6aad8dc2b9 | — |
| 983 | 2.650 | SKIP | Egress and data transfer estimation | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator) | dr | frontier | mongodb-cohort-18067a89fb07 | — |
| 984 | 2.650 | SKIP | queryKnobs and per-command querySettings | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | frontier | mongodb-cohort-210d2a18c904 | — |
| 985 | 2.650 | SKIP | Re-indexing cost when changing numDimensions | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Matryoshka Dimension Truncation for Vector Storage Cost | dr | frontier | mongodb-cohort-fd6aad8dc2b9 | — |
| 986 | 2.650 | SKIP | Untagged spend reporting | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Terraform Tag Enforcement and Policy-as-Code for Atlas Cost | dr | frontier | mongodb-cohort-86157c3fe16f | — |
| 987 | 2.625 | RESEARCH | Associate Atlas Administrator | MongoDB University & Certification | dr | frontier | mongodb-cohort-8b6b0620aca1 | — |
| 988 | 2.625 | RESEARCH | Atlas Secretless KV Authentication | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-dfaf850dab9b | — |
| 989 | 2.600 | RESEARCH | Associate DBA Certification | MongoDB University & Certification | dr | frontier | mongodb-cohort-8b6b0620aca1 | — |
| 990 | 2.600 | RESEARCH | GCP Partnership and Marketplace | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-a0275432efc9 | — |
| 991 | 2.600 | RESEARCH | Atlas Azure Troubleshooting Playbook | MongoDB Atlas on Azure | dr | frontier | mongodb-cohort-d369cc167fa2 | — |
| 992 | 2.600 | RESEARCH | Atlas GCP Troubleshooting | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-0d11435299da | — |
| 993 | 2.600 | SKIP | Atlas Admin API billing alert configuration | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets) | dr | frontier | mongodb-cohort-a0275432efc9 | — |
| 994 | 2.600 | SKIP | Atlas Admin API rate limiting for scheduled polling | Atlas Slow-Query Log and Performance Advisor Automation | dr | frontier | mongodb-cohort-d8c01f75fb44 | — |
| 995 | 2.600 | SKIP | Cross-vendor FOCUS pipelines (BigQuery/Snowflake) | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets) | dr | frontier | mongodb-cohort-4612d59db35d | — |
| 996 | 2.600 | SKIP | DynamoDB on-demand vs provisioned break-even | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB) | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 997 | 2.600 | SKIP | FOCUS column mapping for Atlas credits | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets) | dr | frontier | mongodb-cohort-a0275432efc9 | — |
| 998 | 2.600 | SKIP | Linking Atlas orgs to marketplace billing accounts | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit) | dr | frontier | mongodb-cohort-a0275432efc9 | — |
| 999 | 2.600 | SKIP | MongoDB 8.0 WT Improvements (TCMalloc, ExpressPlan) | WiredTiger Storage Engine Internals | dr | frontier | mongodb-cohort-ae873d2f56e0 | — |
| 1000 | 2.575 | RESEARCH | Monitoring Agent | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-66a976b0eee5 | — |
| 1001 | 2.575 | RESEARCH | Compass Anti-Patterns | MongoDB Compass | dr | frontier | mongodb-cohort-b63ded16c61f | — |
| 1002 | 2.575 | RESEARCH | Performance KB Articles | MongoDB KB Articles | dr | frontier | mongodb-cohort-29539c2a7d1c | — |
| 1003 | 2.575 | RESEARCH | Security KB Articles | MongoDB KB Articles | dr | frontier | mongodb-cohort-29539c2a7d1c | — |
| 1004 | 2.575 | RESEARCH | Config shard caveat (8.0+) | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-0dfda3ebd6a5 | — |
| 1005 | 2.575 | RESEARCH | Atlas Triggers Workarounds (no change streams) | mongodb-time-series | dr | frontier | mongodb-cohort-596d3e14c0db | — |
| 1006 | 2.575 | RESEARCH | HTTPS Endpoints | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-f6ac572aba6f | — |
| 1007 | 2.575 | RESEARCH | Workforce and Workload Identity Federation | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-511384aadb70 | — |
| 1008 | 2.550 | SKIP | Conftest/OPA rules over terraform show -json plans | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Terraform Tag Enforcement and Policy-as-Code for Atlas Cost | dr | frontier | mongodb-cohort-d8c01f75fb44 | — |
| 1009 | 2.550 | SKIP | Search node tier sizing for vector indexes | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Matryoshka Dimension Truncation for Vector Storage Cost | dr | frontier | mongodb-cohort-03e4970d4503 | — |
| 1010 | 2.525 | RESEARCH | Cloud Manager Free/Standard/Premium Tiers | MongoDB Ops Manager and Cloud Manager | dr | frontier | mongodb-cohort-d75e388f7c62 | — |
| 1011 | 2.525 | RESEARCH | Google Distributed Cloud GDC | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-e97ebaff6742 | — |
| 1012 | 2.500 | RESEARCH | Error Envelope and customer sign-off | MongoDB Upgrade Paths | dr | frontier | mongodb-cohort-d6f76edaa459 | — |
| 1013 | 2.500 | SKIP | MongoDB Atlas Data Federation Architecture Internals | MongoDB Atlas Data Federation | dr | covered | mongodb-cohort-e70628ca4539 | the research suite run mongodb-2026-10-14 |
| 1014 | 2.500 | SKIP | MongoDB Atlas Data Federation Benchmark Metrics | MongoDB Atlas Data Federation | dr | covered | mongodb-cohort-e70628ca4539 | the research suite run mongodb-2026-10-14 |
| 1015 | 2.500 | SKIP | MongoDB Atlas Data Federation Failure Scenarios | MongoDB Atlas Data Federation | dr | covered | mongodb-cohort-e70628ca4539 | the research suite run mongodb-2026-10-14 |
| 1016 | 2.500 | SKIP | MongoDB Atlas Data Federation Operational Runbook | MongoDB Atlas Data Federation | dr | covered | mongodb-cohort-e70628ca4539 | the research suite run mongodb-2026-10-14 |
| 1017 | 2.500 | SKIP | MongoDB Drivers Architecture Internals | MongoDB Drivers | dr | frontier | mongodb-cohort-b245a56e13e9 | — |
| 1018 | 2.500 | SKIP | MongoDB Drivers Benchmark Metrics | MongoDB Drivers | dr | frontier | mongodb-cohort-bf9495060320 | — |
| 1019 | 2.500 | SKIP | MongoDB Drivers Failure Scenarios | MongoDB Drivers | dr | frontier | mongodb-cohort-bf9495060320 | — |
| 1020 | 2.500 | SKIP | MongoDB Drivers Operational Runbook | MongoDB Drivers | dr | frontier | mongodb-cohort-bf9495060320 | — |
| 1021 | 2.500 | SKIP | mongosh Reference Architecture Internals | mongosh Reference | dr | frontier | mongodb-cohort-500f97098aa4 | — |
| 1022 | 2.500 | SKIP | mongosh Reference Benchmark Metrics | mongosh Reference | dr | frontier | mongodb-cohort-500f97098aa4 | — |
| 1023 | 2.500 | SKIP | mongosh Reference Failure Scenarios | mongosh Reference | dr | frontier | mongodb-cohort-500f97098aa4 | — |
| 1024 | 2.500 | SKIP | mongosh Reference Operational Runbook | mongosh Reference | dr | frontier | mongodb-cohort-500f97098aa4 | — |
| 1025 | 2.475 | RESEARCH | Common Audit Findings and Remediation | MongoDB Compliance and Regulatory | dr | frontier | mongodb-cohort-9effc0514098 | — |
| 1026 | 2.450 | SKIP | Backup storage rates by region | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Region and Cloud Provider Price Differentials for Atlas | dr | frontier | mongodb-cohort-a9c2cc4bbf19 | — |
| 1027 | 2.450 | SKIP | Cosmos DB RU estimation for MongoDB workloads | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB) | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 1028 | 2.450 | SKIP | Proportional minimum-commit allocation | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cross-Organization Billing and Linked Invoices | dr | frontier | mongodb-cohort-86157c3fe16f | — |
| 1029 | 2.450 | SKIP | Scheduled compliance polling and alerting | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Resource Policy Drift Monitoring (nonCompliantResources) | dr | frontier | mongodb-cohort-9effc0514098 | — |
| 1030 | 2.425 | RESEARCH | Replica Set Support Articles | MongoDB KB Articles | dr | frontier | mongodb-cohort-beb7bc3a2e9a | — |
| 1031 | 2.400 | RESEARCH | PostgreSQL invalid indexes from failed CONCURRENTLY builds | Resumable index builds | dr | frontier | mongodb-cohort-f73749345fb5 | — |
| 1032 | 2.400 | RESEARCH | SQL Server resumable online index operations | Resumable index builds | dr | frontier | mongodb-cohort-f73749345fb5 | — |
| 1033 | 2.400 | RESEARCH | Azure Partnership and MACC | MongoDB Atlas Multi-Cloud | dr | frontier | mongodb-cohort-2ce9556582f9 | — |
| 1034 | 2.400 | SKIP | Atlas Admin API pending-invoice tags field | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Terraform Tag Enforcement and Policy-as-Code for Atlas Cost | dr | frontier | mongodb-cohort-d8c01f75fb44 | — |
| 1035 | 2.350 | RESEARCH | Cloud DNS Terraform Atlas | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-d01cd2452df0 | — |
| 1036 | 2.350 | SKIP | Journal compression | Storage and Data-Lifecycle Cost Levers; WiredTiger Block and Prefix Compression as Storage Cost Lever | dr | frontier | mongodb-cohort-dab118cd8660 | — |
| 1037 | 2.325 | RESEARCH | Compass Plugins and Extensibility | MongoDB Compass | dr | frontier | mongodb-cohort-ebe6aebafc39 | — |
| 1038 | 2.300 | RESEARCH | PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY | Resumable index builds | dr | frontier | mongodb-cohort-f73749345fb5 | — |
| 1039 | 2.300 | SKIP | Billing incidents and refunds | Atlas Billing and Invoice Anatomy; Atlas Billing Mechanics and Cost Visibility | dr | frontier | mongodb-cohort-3da97516cefc | — |
| 1040 | 2.300 | SKIP | Queryable Backups | MongoDB Backup and Restore | dr | frontier | mongodb-cohort-210d2a18c904 | — |
| 1041 | 2.250 | RESEARCH | Compass Editions | MongoDB Compass | dr | frontier | mongodb-cohort-ebe6aebafc39 | — |
| 1042 | 2.250 | SKIP | Error Codes and Troubleshooting Benchmark Metrics | Error Codes and Troubleshooting | revisit | refresh-review | mongodb-cohort-256d4ce7d86f | — |
| 1043 | 2.250 | SKIP | Unlinking an organization | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cross-Organization Billing and Linked Invoices | dr | frontier | mongodb-cohort-86157c3fe16f | — |
| 1044 | 2.225 | RESEARCH | Authentication Triggers | MongoDB Atlas Triggers and Functions | dr | frontier | mongodb-cohort-0fa2d89641e4 | — |
| 1045 | 2.200 | RESEARCH | SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints | Resumable index builds | dr | frontier | mongodb-cohort-41eb8b5e0dea | — |
| 1046 | 2.200 | SKIP | Atlas Device Sync Overview | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-21710e9f436c | — |
| 1047 | 2.200 | RESEARCH | Instructor-Led Training | MongoDB University & Certification | dr | frontier | mongodb-cohort-d64949dd25b2 | — |
| 1048 | 2.175 | RESEARCH | Skill Badges (free micro-credentials) | MongoDB University & Certification | dr | frontier | mongodb-cohort-d64949dd25b2 | — |
| 1049 | 2.175 | RESEARCH | Customer Troubleshooting Playbooks | MongoDB Developer Patterns | dr | frontier | mongodb-cohort-6e3285aedc9b | — |
| 1050 | 2.150 | RESEARCH | Associate Data Modeler | MongoDB University & Certification | dr | frontier | mongodb-cohort-21700f493683 | — |
| 1051 | 2.150 | RESEARCH | MongoDB University Platform | MongoDB University & Certification | dr | frontier | mongodb-cohort-d64949dd25b2 | — |
| 1052 | 2.150 | REFRESH | MongoDB KB Articles | MongoDB Expert Knowledge | revisit | refresh-review | mongodb-cohort-586d5ccba289 | — |
| 1053 | 2.150 | SKIP | Cosmos DB for MongoDB wildcard differences | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | frontier | mongodb-cohort-86b55445bd3c | — |
| 1054 | 2.075 | RESEARCH | Common Pitfalls | MongoDB Realm Mobile Sync | dr | frontier | mongodb-cohort-746f46bdae21 | — |
| 1055 | 2.000 | RESEARCH | MongoDB for Startups GCP | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-1c1358758476 | — |
| 1056 | 2.000 | SKIP | Charts billing ingestion for linked orgs | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cross-Organization Billing and Linked Invoices | dr | frontier | mongodb-cohort-3da97516cefc | — |
| 1057 | 1.925 | RESEARCH | TAM Positioning Playbook | MongoDB University & Certification | dr | frontier | mongodb-cohort-d64949dd25b2 | — |
| 1058 | 1.625 | RESEARCH | Process & governance (OWASP GenAI Red Teaming Guide, MITRE ATLAS, NIST AI RMF, red-team-in-CI) | AI Red-Teaming and Security-Testing Tooling | dr | frontier | mongodb-cohort-79683d333c0b | — |
| 1059 | 1.475 | RESEARCH | Credly Digital Badges | MongoDB University & Certification | dr | frontier | mongodb-cohort-ccad973cc77f | — |
| 1060 | 1.400 | RESEARCH | Google Cloud Partner of Year | MongoDB Atlas on GCP | dr | frontier | mongodb-cohort-1c1358758476 | — |
| 1061 | — | — | $bucket-bucketAuto | mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-8f1d1e3953c7 | — |
| 1062 | — | — | $dateTrunc Downsampling | mongodb-time-series | dr | covered | mongodb-cohort-426b58169dd6 | — |
| 1063 | — | — | $densify-$fill | mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-ec0498a17c95 | — |
| 1064 | — | — | $emit Operators | MongoDB Atlas Stream Processing | dr | covered | mongodb-cohort-3586041115a3 | — |
| 1065 | — | — | $facet | mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-ec0498a17c95 | — |
| 1066 | — | — | $geoIntersects | MongoDB Geospatial | dr | covered | mongodb-cohort-ff6951b6a6be | — |
| 1067 | — | — | $geoNear Aggregation Stage | MongoDB Geospatial | dr | covered | mongodb-cohort-837ceefaf200 | — |
| 1068 | — | — | $geoWithin and $centerSphere | MongoDB Geospatial | dr | covered | mongodb-cohort-ff6951b6a6be | — |
| 1069 | — | — | $graphLookup | mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-ec0498a17c95 | — |
| 1070 | — | — | $lookup | mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-ec0498a17c95 | — |
| 1071 | — | — | $merge and $out Materialized Views | MongoDB Aggregation Pipeline | dr | covered | mongodb-cohort-bcf08df8af4c | — |
| 1072 | — | — | $near and $nearSphere | MongoDB Geospatial | dr | covered | mongodb-cohort-ff6951b6a6be | — |
| 1073 | — | — | $search Operators | MongoDB Atlas Search | dr | covered | mongodb-cohort-901582496b30 | — |
| 1074 | — | — | $setWindowFields | mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-8f70125ad204 | — |
| 1075 | — | — | $setWindowFields Window Functions | mongodb-time-series | dr | covered | mongodb-cohort-960023fbf242 | — |
| 1076 | — | — | $source Operators | MongoDB Atlas Stream Processing | dr | covered | mongodb-cohort-3586041115a3 | — |
| 1077 | — | — | $unionWith | mongodb-aggregation-stages-deep | dr | covered | mongodb-cohort-8f70125ad204 | — |
| 1078 | — | — | 2d Indexes | MongoDB Geospatial | dr | covered | mongodb-cohort-5d6e2fe84fc2 | — |
| 1079 | — | — | 2dsphere Indexes | MongoDB Geospatial | dr | covered | mongodb-cohort-5d6e2fe84fc2 | — |
| 1080 | — | — | 5.6.x RawBsonDocument codec regression | MongoDB Java driver 5.x version timeline & 8.0 compatibility | dr | covered | mongodb-cohort-91c637b361e9 | — |
| 1081 | — | — | 5.7/5.8 release notes | MongoDB Java driver 5.x version timeline & 8.0 compatibility | dr | covered | mongodb-cohort-88978bef1b68 | — |
| 1082 | — | — | 8.0.x regression catalog | MongoDB 8.0 performance changes & read-path regressions vs 7.0 | dr | covered | mongodb-cohort-af5a1bf59f02 | — |
| 1083 | — | — | Access Control | MongoDB Atlas Charts | dr | covered | mongodb-cohort-88f6ca74e8c0 | — |
| 1084 | — | — | Adaptive Timeouts in Database Drivers | Client Side Operations Timeout (CSOT) | dr | covered | mongodb-cohort-669bbd14ed32 | the research suite run mongodb-2026-10-14 |
| 1085 | — | — | afterClusterTime | Causal Consistency | dr | covered | mongodb-cohort-42c8c70cfaa9 | the research suite run mongodb-2026-10-14 |
| 1086 | — | — | Aggregation Expressions | MongoDB Aggregation Pipeline | dr | covered | mongodb-cohort-bcf08df8af4c | — |
| 1087 | — | — | Aggregation Pipeline in Charts | MongoDB Atlas Charts | dr | covered | mongodb-cohort-d96d7212454f | — |
| 1088 | — | — | Air-Gap and Local Mode | MongoDB Ops Manager and Cloud Manager | dr | covered | mongodb-cohort-5ffc3426d7d3 | — |
| 1089 | — | — | AKO CRDs | Atlas Kubernetes Operator | dr | covered | mongodb-cohort-088eb29619d5 | — |
| 1090 | — | — | AKO GitOps | Atlas Kubernetes Operator | dr | covered | mongodb-cohort-088eb29619d5 | — |
| 1091 | — | — | AKO Helm Installation | Atlas Kubernetes Operator | dr | covered | mongodb-cohort-088eb29619d5 | — |
| 1092 | — | — | AKO Independent CRDs | MongoDB Atlas Infrastructure as Code | dr | covered | mongodb-cohort-1e21067091b2 | — |
| 1093 | — | — | AKO Reconciliation Skip Annotation | MongoDB Atlas Infrastructure as Code | dr | covered | mongodb-cohort-1e21067091b2 | — |
| 1094 | — | — | AKO Subobject CRDs Deprecated | MongoDB Atlas Infrastructure as Code | dr | covered | mongodb-cohort-1e21067091b2 | — |
| 1095 | — | — | AKO Troubleshooting | Atlas Kubernetes Operator | dr | covered | mongodb-cohort-b2c31c7f9d7d | — |
| 1096 | — | — | AKO vs Terraform | Atlas Kubernetes Operator | dr | covered | mongodb-cohort-3586041115a3 | — |
| 1097 | — | — | AKO Workload Identity | Atlas Kubernetes Operator | dr | covered | mongodb-cohort-39622c20ff16 | — |
| 1098 | — | — | AKS Atlas Kubernetes Operator | MongoDB Atlas on Azure | dr | covered | mongodb-cohort-3586041115a3 | — |
| 1099 | — | — | AKS Workload Identity Atlas | MongoDB Atlas on Azure | dr | covered | mongodb-cohort-39622c20ff16 | — |
| 1100 | — | — | Analytics Node Configuration | MongoDB Atlas Analytics Node | dr | covered | mongodb-cohort-7cb5038f263f | — |
| 1101 | — | — | Analytics Node Cost Model | MongoDB Atlas Analytics Node | dr | covered | mongodb-cohort-0b5e4ac764ba | — |
| 1102 | — | — | Analytics Node Monitoring | MongoDB Atlas Analytics Node | dr | covered | mongodb-cohort-e315aa4b629c | — |
| 1103 | — | — | Analytics Node Read Preference Routing | MongoDB Atlas Analytics Node | dr | covered | mongodb-cohort-38eeca2988f4 | — |
| 1104 | — | — | Analytics Node Sizing | MongoDB Atlas Analytics Node | dr | covered | mongodb-cohort-3bc7bd71277a | — |
| 1105 | — | — | Anti-Patterns | MongoDB Aggregation Pipeline; MongoDB Atlas Charts | dr | covered | mongodb-cohort-bcf08df8af4c | — |
| 1106 | — | — | App Services Authentication Providers | MongoDB Atlas App Services | dr | covered | mongodb-cohort-3a0c17348ab7 | — |
| 1107 | — | — | App Services Billing Model | MongoDB Atlas App Services | dr | covered | mongodb-cohort-ae6b2ecb67ed | — |
| 1108 | — | — | App Services CLI Deployment | MongoDB Atlas Triggers and Functions | dr | covered | mongodb-cohort-e8024a3dd4fe | — |
| 1109 | — | — | App Services Context | MongoDB Realm Mobile Sync | dr | covered | mongodb-cohort-83dcc10387f6 | — |
| 1110 | — | — | Application Thread Eviction | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-fc1adea52115 | the research suite run mongodb-2026-10-14 |
| 1111 | — | — | Archive Data Expiration Rule | Archive Rules | dr | covered | mongodb-cohort-646bb42493b4 | the research suite run mongodb-2026-10-14 |
| 1112 | — | — | Archive Rules | Archive Rules; MongoDB Atlas Online Archive | dr | covered | mongodb-cohort-095f520099a9 | the research suite run mongodb-2026-10-14 |
| 1113 | — | — | Archive Schedule Window | Archive Rules | dr | covered | mongodb-cohort-646bb42493b4 | the research suite run mongodb-2026-10-14 |
| 1114 | — | — | ASP Pricing Model | MongoDB Atlas Stream Processing | dr | covered | mongodb-cohort-ae6b2ecb67ed | — |
| 1115 | — | — | Asymmetric Sync | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-83dcc10387f6 | the research suite run mongodb-2026-10-14 |
| 1116 | — | — | Atlas Admin API GCP Auth | MongoDB Atlas on GCP | dr | covered | mongodb-cohort-e8024a3dd4fe | — |
| 1117 | — | — | Atlas Billing Mechanics and Cost Visibility | MongoDB Atlas Cost Optimization; MongoDB Atlas on Azure; MongoDB Atlas on GCP; MongoDB Multi-Tenancy | dr | covered | mongodb-cohort-ae6b2ecb67ed | the research suite run mongodb-2026-10-14 |
| 1118 | — | — | Atlas CLI | MongoDB Developer Patterns | dr | covered | mongodb-cohort-e8024a3dd4fe | — |
| 1119 | — | — | Atlas CLI Architecture Internals | Atlas CLI | dr | covered | mongodb-cohort-e8024a3dd4fe | the research suite run mongodb-2026-10-14 |
| 1120 | — | — | Atlas CLI Benchmark Metrics | Atlas CLI | dr | covered | mongodb-cohort-b3f850aa5dec | the research suite run mongodb-2026-10-14 |
| 1121 | — | — | Atlas CLI Integration | Atlas Service Accounts | dr | covered | mongodb-cohort-b3f850aa5dec | the research suite run mongodb-2026-10-14 |
| 1122 | — | — | Atlas CLI Operational Runbook | Atlas CLI | dr | covered | mongodb-cohort-b3f850aa5dec | the research suite run mongodb-2026-10-14 |
| 1123 | — | — | Atlas cluster tiers (M30) & major-version upgrade mechanics | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-b57656beb48c | — |
| 1124 | — | — | Atlas Cluster Topology and Tier Economics | MongoDB Atlas Cost Optimization; MongoDB Atlas Multi-Cloud; MongoDB Capacity Planning | dr | covered | mongodb-cohort-b57656beb48c | the research suite run mongodb-2026-10-14 |
| 1125 | — | — | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-ae6b2ecb67ed | — |
| 1126 | — | — | Atlas Data API Removal | MongoDB BI Connector and SQL Access | dr | covered | mongodb-cohort-b3f850aa5dec | — |
| 1127 | — | — | Atlas Device Sync | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-83dcc10387f6 | the research suite run mongodb-2026-10-14 |
| 1128 | — | — | Atlas Diagnostics Expert | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-ba79a03d1b95 | — |
| 1129 | — | — | Atlas Edge Server | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-17b369d4637b | the research suite run mongodb-2026-10-14 |
| 1130 | — | — | Atlas Federated Authentication | MongoDB Atlas | dr | covered | mongodb-cohort-39622c20ff16 | — |
| 1131 | — | — | Atlas federated database users and groups | Atlas Identity Federation and Resource Policy Boundaries | dr | covered | mongodb-cohort-782bea347229 | the research suite run mongodb-2026-10-14 |
| 1132 | — | — | Atlas Gen2 ARM hardware | Atlas cluster tiers (M30) & major-version upgrade mechanics | dr | covered | mongodb-cohort-c82853a1ba4f | the research suite run mongodb-2026-10-14 |
| 1133 | — | — | Atlas Hybrid Fusion and BM25 Diagnostics | MongoDB Atlas Search and Vector Search | dr | covered | mongodb-cohort-2a51908b33d8 | the research suite run mongodb-2026-10-14 |
| 1134 | — | — | Atlas Identity Federation and Resource Policy Boundaries | MongoDB Atlas IAM and RBAC | dr | covered | mongodb-cohort-39622c20ff16 | the research suite run mongodb-2026-10-14 |
| 1135 | — | — | Atlas IP access list for service accounts | Atlas Identity Federation and Resource Policy Boundaries | dr | covered | mongodb-cohort-88f6ca74e8c0 | the research suite run mongodb-2026-10-14 |
| 1136 | — | — | Atlas Kubernetes Operator | MongoDB Atlas | dr | covered | mongodb-cohort-ec6726c0f56e | — |
| 1137 | — | — | Atlas Maintenance Windows | MongoDB Monitoring and Observability | dr | covered | mongodb-cohort-a58e34a96257 | — |
| 1138 | — | — | Atlas org mapping and domain mapping | Atlas Identity Federation and Resource Policy Boundaries | dr | covered | mongodb-cohort-df87ba6c358a | the research suite run mongodb-2026-10-14 |
| 1139 | — | — | Atlas Performance Advisor Auto-Index Evaluation | Atlas Triage Workflows | dr | covered | mongodb-cohort-5d6e2fe84fc2 | the research suite run mongodb-2026-10-14 |
| 1140 | — | — | Atlas Pricing Programs, Cost Governance and TCO | MongoDB Atlas Cost Optimization; MongoDB Atlas Flex and Serverless Tiers | dr | covered | mongodb-cohort-79e219ee98e0 | the research suite run mongodb-2026-10-14 |
| 1141 | — | — | Atlas Query Insights, Performance Advisor and Compass explain | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-a912b742ce3a | — |
| 1142 | — | — | Atlas Resource Policies Cedar | Atlas Identity Federation and Resource Policy Boundaries; MongoDB Atlas IAM and RBAC | dr | covered | mongodb-cohort-52377be9eeaf | — |
| 1143 | — | — | Atlas Service Accounts | MongoDB Atlas | dr | covered | mongodb-cohort-52377be9eeaf | — |
| 1144 | — | — | Atlas Slow-Query Log and Performance Advisor Automation | Database Profiler vs Query Profiler; MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-70be6349f202 | — |
| 1145 | — | — | Atlas SQL Interface MongoSQL | MongoDB BI Connector and SQL Access | dr | covered | mongodb-cohort-44f56096db58 | — |
| 1146 | — | — | Atlas storage auto-scaling and disk reclaim via compact | Storage and Data-Lifecycle Cost Levers; WiredTiger Block and Prefix Compression as Storage Cost Lever | dr | covered | mongodb-cohort-d1ec2ec48995 | — |
| 1147 | — | — | Atlas Triage Workflows | Atlas Diagnostics Expert | dr | covered | mongodb-cohort-2255fa8f9dbd | — |
| 1148 | — | — | autoCompact and Replica-Set Write Blocking | MongoDB autoCompact | dr | covered | mongodb-cohort-e2f2efd61e49 | — |
| 1149 | — | — | autoCompact Atlas-Specific Behavior | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 1150 | — | — | autoCompact Checkpoint Interaction | MongoDB autoCompact | dr | covered | mongodb-cohort-afc52fa5e292 | — |
| 1151 | — | — | autoCompact Cluster Topology Behavior | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 1152 | — | — | autoCompact freeSpaceTargetMB Gating | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 1153 | — | — | autoCompact Lifecycle and Persistence | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 1154 | — | — | autoCompact runOnce vs Continuous Mode | MongoDB autoCompact | dr | covered | mongodb-cohort-1ff7eed674cb | — |
| 1155 | — | — | Automated Cluster Scaling Decision Matrix | Atlas Triage Workflows | dr | covered | mongodb-cohort-e795bae03047 | the research suite run mongodb-2026-10-14 |
| 1156 | — | — | AWS CDK awscdk-resources-mongodbatlas | MongoDB Atlas Infrastructure as Code | dr | covered | mongodb-cohort-1e21067091b2 | — |
| 1157 | — | — | AWS CloudFormation Atlas | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-2b531c2e4338 | — |
| 1158 | — | — | AWS CloudFormation Atlas Resources | MongoDB Atlas Infrastructure as Code | dr | covered | mongodb-cohort-b26d99837f3c | — |
| 1159 | — | — | AWS IAM Outbound Identity Federation to Atlas | Atlas Identity Federation and Resource Policy Boundaries | dr | covered | mongodb-cohort-7c2a3608bae4 | — |
| 1160 | — | — | AWS ISV Accelerate | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-2b531c2e4338 | — |
| 1161 | — | — | AWS Marketplace Atlas | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-edff8da37572 | — |
| 1162 | — | — | AWS PrivateLink | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-2b531c2e4338 | — |
| 1163 | — | — | Background-Compaction Skip/EMA Heuristic | WiredTiger Compaction Algorithm | dr | covered | mongodb-cohort-acec48250f2d | — |
| 1164 | — | — | Backup Compliance Policy (WORM) | MongoDB Backup and Restore | dr | covered | mongodb-cohort-52377be9eeaf | — |
| 1165 | — | — | Backup Cost Optimization | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-edff8da37572 | the research suite run mongodb-2026-10-14 |
| 1166 | — | — | BI Connector to MongoSQL Migration | Atlas SQL Interface MongoSQL | dr | covered | mongodb-cohort-1edff5c43b6b | the research suite run mongodb-2026-10-14 |
| 1167 | — | — | Block Manager and Page Sizing | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-b57656beb48c | the research suite run mongodb-2026-10-14 |
| 1168 | — | — | Bucket catalog memory and closure reasons | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-98d2158f395e | — |
| 1169 | — | — | Bucket fragmentation remediation (re-insert/merge) | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-98d2158f395e | — |
| 1170 | — | — | Bypass SAML mode | Atlas Federated Authentication | dr | covered | mongodb-cohort-7c2a3608bae4 | the research suite run mongodb-2026-10-14 |
| 1171 | — | — | Cache Architecture | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-fc1adea52115 | the research suite run mongodb-2026-10-14 |
| 1172 | — | — | Causal Consistency | MongoDB Driver Internals; MongoDB Replication | dr | covered | mongodb-cohort-0b980a99f9dc | — |
| 1173 | — | — | CDC-patterns | mongodb-kafka-connector | dr | covered | mongodb-cohort-25290fa9c76f | — |
| 1174 | — | — | Chart Types | MongoDB Atlas Charts | dr | covered | mongodb-cohort-9930879fa33e | the research suite run mongodb-2026-10-14 |
| 1175 | — | — | Charts REST API | MongoDB Atlas Charts | dr | covered | mongodb-cohort-ec6726c0f56e | the research suite run mongodb-2026-10-14 |
| 1176 | — | — | Checkpoint Mechanism | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-fc1adea52115 | — |
| 1177 | — | — | Client Reset Strategies | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-ec6726c0f56e | the research suite run mongodb-2026-10-14 |
| 1178 | — | — | client sessions | Causal Consistency | dr | covered | mongodb-cohort-42c8c70cfaa9 | the research suite run mongodb-2026-10-14 |
| 1179 | — | — | Client Side Operations Timeout (CSOT) | Client Side Operations Timeout (CSOT); MongoDB Driver Internals | dr | covered | mongodb-cohort-ec6726c0f56e | the research suite run mongodb-2026-10-14 |
| 1180 | — | — | Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit) | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling | dr | covered | mongodb-cohort-edff8da37572 | — |
| 1181 | — | — | Cluster Pause | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-069334033db9 | the research suite run mongodb-2026-10-14 |
| 1182 | — | — | clusterTime | Causal Consistency | dr | covered | mongodb-cohort-42c8c70cfaa9 | the research suite run mongodb-2026-10-14 |
| 1183 | — | — | CMAP Connection Pooling | MongoDB Driver Internals | dr | covered | mongodb-cohort-669bbd14ed32 | — |
| 1184 | — | — | Common Cost Overruns | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-edff8da37572 | the research suite run mongodb-2026-10-14 |
| 1185 | — | — | Connected organizations | Atlas Federated Authentication | dr | covered | mongodb-cohort-d6226addaa2f | the research suite run mongodb-2026-10-14 |
| 1186 | — | — | Connection Troubleshooting | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-1f2540ed7877 | the research suite run mongodb-2026-10-14 |
| 1187 | — | — | Connection URI server-selection options | Server Selection Algorithm | dr | frontier | mongodb-cohort-beb7bc3a2e9a | — |
| 1188 | — | — | Corruption (validate, --repair, wt CLI) | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-fc1adea52115 | the research suite run mongodb-2026-10-14 |
| 1189 | — | — | Cost Model | MongoDB Atlas Charts | dr | covered | mongodb-cohort-86724c05f689 | the research suite run mongodb-2026-10-14 |
| 1190 | — | — | Cost Monitoring | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-86724c05f689 | the research suite run mongodb-2026-10-14 |
| 1191 | — | — | Covered queries on sharded collections | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds; MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-6fde22c2b544 | — |
| 1192 | — | — | Crash Stack Trace Symbolization | KB-Backed Troubleshooting | dr | covered | mongodb-cohort-48599247dc26 | the research suite run mongodb-2026-10-14 |
| 1193 | — | — | cross-service causal tokens | Causal Consistency | dr | covered | mongodb-cohort-0b980a99f9dc | the research suite run mongodb-2026-10-14 |
| 1194 | — | — | Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB) | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO | dr | covered | mongodb-cohort-86724c05f689 | — |
| 1195 | — | — | Custom server selectors | Server Selection Algorithm | dr | frontier | mongodb-cohort-d05fd98164be | — |
| 1196 | — | — | Customer Hotfix & Patch Verification | KB-Backed Troubleshooting | dr | covered | mongodb-cohort-48599247dc26 | the research suite run mongodb-2026-10-14 |
| 1197 | — | — | Dashboards | MongoDB Atlas Charts | dr | covered | mongodb-cohort-9930879fa33e | the research suite run mongodb-2026-10-14 |
| 1198 | — | — | Data Sources | MongoDB Atlas Charts | dr | covered | mongodb-cohort-9930879fa33e | the research suite run mongodb-2026-10-14 |
| 1199 | — | — | Database Profiler vs Query Profiler | Atlas Slow-Query Log and Performance Advisor Automation; MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-70be6349f202 | — |
| 1200 | — | — | DATE criteria date format specifications | DATE Criteria | dr | covered | mongodb-cohort-5e97bf42ef54 | the research suite run mongodb-2026-10-14 |
| 1201 | — | — | DATE vs CUSTOM criteria selection | DATE Criteria | dr | covered | mongodb-cohort-e2f2efd61e49 | the research suite run mongodb-2026-10-14 |
| 1202 | — | — | Delayed-member lag interpretation | Replication Lag Monitoring | dr | frontier | mongodb-cohort-bd3136e37397 | — |
| 1203 | — | — | Delbridge Data API | Atlas Data API Removal | dr | covered | mongodb-cohort-647b54b90f3d | — |
| 1204 | — | — | Diagnostic Tool Design | Atlas Diagnostics Expert | dr | covered | mongodb-cohort-2255fa8f9dbd | — |
| 1205 | — | — | Domain verification | Atlas Federated Authentication | dr | covered | mongodb-cohort-d6226addaa2f | the research suite run mongodb-2026-10-14 |
| 1206 | — | — | Driver Examples | MongoDB Transactions | dr | covered | mongodb-cohort-669bbd14ed32 | — |
| 1207 | — | — | Driver Examples (Node.js, Python, Java) | MongoDB Aggregation Pipeline | dr | covered | mongodb-cohort-d51829cbeec4 | the research suite run mongodb-2026-10-14 |
| 1208 | — | — | EDP Credits | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-86724c05f689 | the research suite run mongodb-2026-10-14 |
| 1209 | — | — | Elastic Compute Autoscaling | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-b57656beb48c | the research suite run mongodb-2026-10-14 |
| 1210 | — | — | Embedded Charts | MongoDB Atlas Charts | dr | covered | mongodb-cohort-9930879fa33e | the research suite run mongodb-2026-10-14 |
| 1211 | — | — | Embedding SDK | MongoDB Atlas Charts | dr | covered | mongodb-cohort-676df347efbf | the research suite run mongodb-2026-10-14 |
| 1212 | — | — | Emergency Security Patches | Atlas Maintenance Windows | dr | covered | mongodb-cohort-a8da4321224d | the research suite run mongodb-2026-10-14 |
| 1213 | — | — | Encryption at Rest (KMIP, AES-256-CBC/GCM) | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-a01124d580c7 | the research suite run mongodb-2026-10-14 |
| 1214 | — | — | Error Code Hierarchy & Assertion Types | KB-Backed Troubleshooting | dr | covered | mongodb-cohort-48599247dc26 | the research suite run mongodb-2026-10-14 |
| 1215 | — | — | Error Codes and Troubleshooting | MongoDB Developer Patterns | dr | covered | mongodb-cohort-aadbc815fdee | — |
| 1216 | — | — | Error Codes and Troubleshooting Architecture Internals | Error Codes and Troubleshooting | dr | covered | mongodb-cohort-609ae431b4d6 | the research suite run mongodb-2026-10-14 |
| 1217 | — | — | Error Codes and Troubleshooting Failure Scenarios | Error Codes and Troubleshooting | dr | covered | mongodb-cohort-609ae431b4d6 | the research suite run mongodb-2026-10-14 |
| 1218 | — | — | Error Codes and Troubleshooting Operational Runbook | Error Codes and Troubleshooting | dr | covered | mongodb-cohort-609ae431b4d6 | the research suite run mongodb-2026-10-14 |
| 1219 | — | — | EventBridge Integration | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-2b531c2e4338 | the research suite run mongodb-2026-10-14 |
| 1220 | — | — | Eviction (clean/dirty targets and triggers) | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-1a8369a70852 | — |
| 1221 | — | — | expireAfterDays data age calculation | DATE Criteria | dr | covered | mongodb-cohort-5e97bf42ef54 | the research suite run mongodb-2026-10-14 |
| 1222 | — | — | express execution path | MongoDB 8.0 performance changes & read-path regressions vs 7.0 | dr | covered | mongodb-cohort-af5a1bf59f02 | the research suite run mongodb-2026-10-14 |
| 1223 | — | — | Express MongoDB Driver Pattern | Atlas Data API Removal | dr | covered | mongodb-cohort-d51829cbeec4 | — |
| 1224 | — | — | FastAPI Motor Pattern | Atlas Data API Removal | dr | covered | mongodb-cohort-647b54b90f3d | — |
| 1225 | — | — | FCV pinning no-downgrade rule | Atlas cluster tiers (M30) & major-version upgrade mechanics | dr | covered | mongodb-cohort-c82853a1ba4f | the research suite run mongodb-2026-10-14 |
| 1226 | — | — | Feature Compatibility Version (FCV) | MongoDB Upgrade Paths | dr | covered | mongodb-cohort-a00749d71440 | — |
| 1227 | — | — | Federated database user mapping by sub/groups claim | Atlas Identity Federation and Resource Policy Boundaries | dr | covered | mongodb-cohort-782bea347229 | the research suite run mongodb-2026-10-14 |
| 1228 | — | — | Federation Management Console | Atlas Federated Authentication | dr | covered | mongodb-cohort-7c2a3608bae4 | the research suite run mongodb-2026-10-14 |
| 1229 | — | — | FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets) | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling | dr | covered | mongodb-cohort-c7b0307350e5 | — |
| 1230 | — | — | Flexible Sync Subscriptions | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-83dcc10387f6 | the research suite run mongodb-2026-10-14 |
| 1231 | — | — | Flutter Dart Realm SDK | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-d51829cbeec4 | the research suite run mongodb-2026-10-14 |
| 1232 | — | — | FTDC and Log Tooling | Atlas Diagnostics Expert | dr | covered | mongodb-cohort-2255fa8f9dbd | — |
| 1233 | — | — | FTDC Chunk Decompression & Stream Parsing | FTDC and Log Tooling | dr | covered | mongodb-cohort-fec23d9e5b40 | the research suite run mongodb-2026-10-14 |
| 1234 | — | — | FTDC Diagnostics | MongoDB Monitoring and Observability; MongoDB Performance Troubleshooting | dr | covered | mongodb-cohort-a58e34a96257 | — |
| 1235 | — | — | Group-to-role mapping | Atlas Federated Authentication | dr | covered | mongodb-cohort-52377be9eeaf | the research suite run mongodb-2026-10-14 |
| 1236 | — | — | Hashed shard-key index drop operational procedure | Shard key index constraints when dropping or hiding indexes | dr | frontier | mongodb-cohort-67232cc8ea85 | — |
| 1237 | — | — | Hidden indexes and safe index removal | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds; MongoDB Explain Plans, Query Planner and Plan Cache; MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor; MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead; Schema Design for Storage Cost; Unused index detection with $indexStats | dr | covered | mongodb-cohort-5d6e2fe84fc2 | — |
| 1238 | — | — | History Store (WiredTigerHS.wt) | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-1a8369a70852 | — |
| 1239 | — | — | IAM Authentication | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-7f5446fbf99d | the research suite run mongodb-2026-10-14 |
| 1240 | — | — | IdP configuration (Entra ID) | Atlas Federated Authentication | dr | covered | mongodb-cohort-7c2a3608bae4 | the research suite run mongodb-2026-10-14 |
| 1241 | — | — | IdP configuration (Okta) | Atlas Federated Authentication | dr | covered | mongodb-cohort-d6226addaa2f | the research suite run mongodb-2026-10-14 |
| 1242 | — | — | implicit vs explicit sessions | Causal Consistency | dr | covered | mongodb-cohort-42c8c70cfaa9 | the research suite run mongodb-2026-10-14 |
| 1243 | — | — | In-Memory Storage Engine (Enterprise) | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-1a8369a70852 | the research suite run mongodb-2026-10-14 |
| 1244 | — | — | Independent shard scaling and per-shard tiering | Atlas Cluster Topology and Tier Economics; Sharded Cluster Cost Economics | dr | covered | mongodb-cohort-aca8b137d5ba | — |
| 1245 | — | — | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | covered | mongodb-cohort-a4dab3467278 | — |
| 1246 | — | — | Index Storage Cost | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-c7b0307350e5 | the research suite run mongodb-2026-10-14 |
| 1247 | — | — | Instance Right-Sizing | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-aca8b137d5ba | the research suite run mongodb-2026-10-14 |
| 1248 | — | — | kafka-sink-connector | mongodb-kafka-connector | dr | covered | mongodb-cohort-25290fa9c76f | — |
| 1249 | — | — | kafka-source-connector | mongodb-kafka-connector | dr | covered | mongodb-cohort-25290fa9c76f | — |
| 1250 | — | — | KB-Backed Troubleshooting | Atlas Diagnostics Expert | dr | covered | mongodb-cohort-2255fa8f9dbd | — |
| 1251 | — | — | KMS Encryption at Rest | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-a01124d580c7 | the research suite run mongodb-2026-10-14 |
| 1252 | — | — | Lambda Integration | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-7872c1e1d1c9 | the research suite run mongodb-2026-10-14 |
| 1253 | — | — | Local embeddings from Ollama into MongoDB Atlas Vector Search | Ollama deployment, cloud, security and operations | dr | covered | mongodb-cohort-676df347efbf | — |
| 1254 | — | — | Lock-Free Diagnostic Sampling Engine | Diagnostic Tool Design | dr | covered | mongodb-cohort-5914885288b0 | the research suite run mongodb-2026-10-14 |
| 1255 | — | — | Long-running secondary reads in sharded clusters | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-70bfdc1552cd | — |
| 1256 | — | — | Maintenance Window Configuration | Atlas Maintenance Windows | dr | covered | mongodb-cohort-a8da4321224d | the research suite run mongodb-2026-10-14 |
| 1257 | — | — | MongoDB 8.0 performance changes & read-path regressions vs 7.0 | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-4a80c4b6f382 | — |
| 1258 | — | — | MongoDB 8.1–9.0 query-engine changes and AI-assisted optimization | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-70be6349f202 | — |
| 1259 | — | — | MongoDB Aggregation Pipeline | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-b24c703bbfc1 | — |
| 1260 | — | — | MongoDB Atlas Analytics Node | MongoDB Atlas | dr | covered | mongodb-cohort-953775438c83 | — |
| 1261 | — | — | MongoDB Atlas App Services | MongoDB Atlas | dr | covered | mongodb-cohort-b00bb4e0c1b2 | — |
| 1262 | — | — | MongoDB Atlas AWS Networking | MongoDB Atlas | dr | covered | mongodb-cohort-a7ea5f10b522 | — |
| 1263 | — | — | MongoDB Atlas Charts | MongoDB Atlas | dr | covered | mongodb-cohort-953775438c83 | — |
| 1264 | — | — | MongoDB Atlas Data Federation | MongoDB Atlas | dr | covered | mongodb-cohort-45f0b3909b92 | — |
| 1265 | — | — | MongoDB Atlas Device SDK | MongoDB Atlas | dr | covered | mongodb-cohort-d51829cbeec4 | — |
| 1266 | — | — | MongoDB Atlas Flex and Serverless Tiers | MongoDB Atlas; MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-aca8b137d5ba | — |
| 1267 | — | — | MongoDB Atlas IAM and RBAC | MongoDB Atlas | dr | covered | mongodb-cohort-c80f8ee91387 | — |
| 1268 | — | — | MongoDB Atlas Infrastructure as Code | MongoDB Atlas | dr | covered | mongodb-cohort-953775438c83 | — |
| 1269 | — | — | MongoDB Atlas Multi-Cloud | MongoDB Atlas | dr | covered | mongodb-cohort-953775438c83 | — |
| 1270 | — | — | MongoDB Atlas on Azure | MongoDB Atlas | dr | covered | mongodb-cohort-7808e18d9d80 | — |
| 1271 | — | — | MongoDB Atlas on GCP | MongoDB Atlas | dr | covered | mongodb-cohort-7808e18d9d80 | — |
| 1272 | — | — | MongoDB Atlas Online Archive | MongoDB Atlas | dr | covered | mongodb-cohort-45f0b3909b92 | — |
| 1273 | — | — | MongoDB Atlas Search | MongoDB Atlas | dr | covered | mongodb-cohort-901582496b30 | — |
| 1274 | — | — | MongoDB Atlas Search and Vector Search | MongoDB Atlas | dr | covered | mongodb-cohort-beb79749f849 | — |
| 1275 | — | — | MongoDB Atlas Stream Processing | MongoDB Atlas | dr | covered | mongodb-cohort-7808e18d9d80 | — |
| 1276 | — | — | MongoDB Atlas Terraform Provider | MongoDB Atlas | dr | covered | mongodb-cohort-647b54b90f3d | — |
| 1277 | — | — | MongoDB Atlas Triggers and Functions | MongoDB Atlas | dr | covered | mongodb-cohort-7808e18d9d80 | — |
| 1278 | — | — | MongoDB Atlas Vector Search | MongoDB Atlas | dr | covered | mongodb-cohort-beb79749f849 | — |
| 1279 | — | — | MongoDB autoCompact | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-4a80c4b6f382 | — |
| 1280 | — | — | MongoDB Backup and Restore | MongoDB Atlas | dr | covered | mongodb-cohort-b40001359bc9 | — |
| 1281 | — | — | MongoDB BI Connector and SQL Access | MongoDB Atlas | dr | covered | mongodb-cohort-5323615755c3 | — |
| 1282 | — | — | MongoDB Capacity Planning | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-4a80c4b6f382 | — |
| 1283 | — | — | MongoDB Compass | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-1c39d46a81a5 | — |
| 1284 | — | — | MongoDB Compliance and Regulatory | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-79e219ee98e0 | — |
| 1285 | — | — | MongoDB Connection String URI | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-4a80c4b6f382 | — |
| 1286 | — | — | MongoDB counts, distinct, cursors and read-path tuning | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-8925d4eba1e0 | — |
| 1287 | — | — | MongoDB Driver Internals | MongoDB Developer Patterns | dr | covered | mongodb-cohort-30638906d3dc | — |
| 1288 | — | — | MongoDB Drivers | MongoDB Developer Patterns | dr | covered | mongodb-cohort-30638906d3dc | — |
| 1289 | — | — | MongoDB Expert Knowledge |  | dr | covered | mongodb-cohort-9aebcca531bf | — |
| 1290 | — | — | MongoDB explain output and plan stages | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-3bd33f3d5a98 | — |
| 1291 | — | — | MongoDB Geospatial | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9aebcca531bf | — |
| 1292 | — | — | MongoDB Indexes Deep Dive | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-fcb1d31d10fd | — |
| 1293 | — | — | MongoDB Java driver 5.x version timeline & 8.0 compatibility | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-30638906d3dc | — |
| 1294 | — | — | MongoDB Migration Patterns | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9aebcca531bf | — |
| 1295 | — | — | MongoDB Multi-Tenancy | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9aebcca531bf | — |
| 1296 | — | — | MongoDB Ops Manager and Cloud Manager | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-dd2834adadc2 | — |
| 1297 | — | — | MongoDB Performance Benchmarking | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-dd2834adadc2 | — |
| 1298 | — | — | MongoDB Performance Regression Detection and Testing Methodology | MongoDB Performance Benchmarking | dr | covered | mongodb-cohort-123beacc8566 | — |
| 1299 | — | — | MongoDB Performance Troubleshooting | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-ba79a03d1b95 | — |
| 1300 | — | — | MongoDB query operators, index bounds and projection | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-fcb1d31d10fd | — |
| 1301 | — | — | MongoDB query planner, plan cache, query settings and hints | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-3bd33f3d5a98 | — |
| 1302 | — | — | MongoDB query shapes, $queryStats, profiler and index usage | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-fcb1d31d10fd | — |
| 1303 | — | — | MongoDB Security Architecture | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-dd2834adadc2 | — |
| 1304 | — | — | MongoDB sharded query targeting and scatter-gather | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-5f531cf409ab | — |
| 1305 | — | — | MongoDB sort and pagination optimization | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-70be6349f202 | — |
| 1306 | — | — | MongoDB Spark Connector and Databricks Integration | MongoDB Developer Patterns | dr | covered | mongodb-cohort-9145188a1779 | — |
| 1307 | — | — | MongoDB Stress, Soak, and Chaos-Resilience Testing | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-dd2834adadc2 | — |
| 1308 | — | — | MongoDB time-series indexes and metaField design | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-b3d40a574609 | — |
| 1309 | — | — | MongoDB time-series query execution: bucket unpacking, pushdown, block processing and sorts | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-b3d40a574609 | — |
| 1310 | — | — | MongoDB time-series working-set sizing and sharding | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-b3d40a574609 | — |
| 1311 | — | — | MongoDB Transactions | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-0b980a99f9dc | — |
| 1312 | — | — | MongoDB University & Certification | MongoDB Expert Knowledge; Technical Instruction & Engineering Education | dr | covered | mongodb-cohort-28b16aa767e7 | — |
| 1313 | — | — | MongoDB Upgrade Paths | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-28b16aa767e7 | — |
| 1314 | — | — | mongodb-aggregation-stages-deep | MongoDB Aggregation Pipeline | dr | covered | mongodb-cohort-bcf08df8af4c | — |
| 1315 | — | — | mongodb-kafka-connector | MongoDB Atlas Stream Processing | dr | covered | mongodb-cohort-f05f8b2f958c | — |
| 1316 | — | — | mongodb-time-series | MongoDB Aggregation Pipeline; mongodb-schema-design | dr | covered | mongodb-cohort-9951a37f6fb4 | — |
| 1317 | — | — | mongosh Reference | MongoDB Developer Patterns | dr | covered | mongodb-cohort-065b5964e6f4 | — |
| 1318 | — | — | mongosync | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-b3b66aff89bd | — |
| 1319 | — | — | monotonic reads | Causal Consistency | dr | covered | mongodb-cohort-ab79a82a5823 | the research suite run mongodb-2026-10-14 |
| 1320 | — | — | Multi-Region Networking | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-7872c1e1d1c9 | the research suite run mongodb-2026-10-14 |
| 1321 | — | — | Network Access Lists | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-7872c1e1d1c9 | the research suite run mongodb-2026-10-14 |
| 1322 | — | — | Network Connection Quota Management | Atlas Triage Workflows | dr | covered | mongodb-cohort-874914c8d333 | the research suite run mongodb-2026-10-14 |
| 1323 | — | — | Network Egress Costs | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-1a42b3c0d1f3 | the research suite run mongodb-2026-10-14 |
| 1324 | — | — | OAuth2 Token Exchange | Atlas Service Accounts | dr | covered | mongodb-cohort-cc8b558405fc | the research suite run mongodb-2026-10-14 |
| 1325 | — | — | Offline-First Mobile | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-b00bb4e0c1b2 | the research suite run mongodb-2026-10-14 |
| 1326 | — | — | Online Archive Terraform Resource | Archive Rules | dr | covered | mongodb-cohort-095f520099a9 | the research suite run mongodb-2026-10-14 |
| 1327 | — | — | Operation rejection filters | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-542b6e07af2f | — |
| 1328 | — | — | operationTime | Causal Consistency | dr | covered | mongodb-cohort-ab79a82a5823 | the research suite run mongodb-2026-10-14 |
| 1329 | — | — | Oplog recovery headroom | Replication Lag Monitoring | dr | frontier | mongodb-cohort-beb7bc3a2e9a | — |
| 1330 | — | — | Oplog sizing under storage auto-scaling | Atlas Cluster Topology and Tier Economics; Atlas storage auto-scaling and disk reclaim via compact; Storage Growth and IOPS Forecasting for Cost | dr | covered | mongodb-cohort-aca8b137d5ba | — |
| 1331 | — | — | Partition fields constraints for DATE rules | DATE Criteria | dr | covered | mongodb-cohort-5e97bf42ef54 | the research suite run mongodb-2026-10-14 |
| 1332 | — | — | Per-member replica-set telemetry | Replication Lag Monitoring | dr | frontier | mongodb-cohort-beb7bc3a2e9a | — |
| 1333 | — | — | Performance Impact | MongoDB Transactions | dr | covered | mongodb-cohort-f0e4301e68e0 | — |
| 1334 | — | — | Pipeline Stages Reference | MongoDB Aggregation Pipeline | dr | covered | mongodb-cohort-58a562caa2ac | the research suite run mongodb-2026-10-14 |
| 1335 | — | — | Quick Reference | MongoDB Atlas Charts | dr | covered | mongodb-cohort-8507026d5bdd | the research suite run mongodb-2026-10-14 |
| 1336 | — | — | Read Concern Levels | MongoDB Replication | dr | covered | mongodb-cohort-e2f2efd61e49 | — |
| 1337 | — | — | Read preference candidate filtering | Server Selection Algorithm | dr | frontier | mongodb-cohort-d05fd98164be | — |
| 1338 | — | — | Read/Write Tickets and Dynamic Concurrency (7.0+) | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-1a8369a70852 | — |
| 1339 | — | — | Realm Authentication | MongoDB Atlas Device SDK | dr | covered | mongodb-cohort-e8cd3f87c4cc | the research suite run mongodb-2026-10-14 |
| 1340 | — | — | Replanning loops and replanReason | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-542b6e07af2f | — |
| 1341 | — | — | Replica-set election timing | MongoDB Upgrade Paths | dr | covered | mongodb-cohort-85a1dc6f9f63 | — |
| 1342 | — | — | Request Hedging | Client Side Operations Timeout (CSOT) | dr | covered | mongodb-cohort-269152d0bf72 | the research suite run mongodb-2026-10-14 |
| 1343 | — | — | Reserved Capacity and Committed Use | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-069334033db9 | the research suite run mongodb-2026-10-14 |
| 1344 | — | — | RESTHeart | Atlas Data API Removal | dr | covered | mongodb-cohort-9d1235b3ac64 | — |
| 1345 | — | — | Resumable index builds | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | covered | mongodb-cohort-fcb1d31d10fd | — |
| 1346 | — | — | Retryable Transactions | MongoDB Transactions | dr | covered | mongodb-cohort-0b980a99f9dc | — |
| 1347 | — | — | Retryable Writes | MongoDB Driver Internals | dr | covered | mongodb-cohort-c98d28ad4b7f | — |
| 1348 | — | — | Rolling index builds | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead; Resumable index builds | dr | covered | mongodb-cohort-b8244b58f531 | — |
| 1349 | — | — | Rolling Maintenance Procedure | Atlas Maintenance Windows | dr | covered | mongodb-cohort-a8da4321224d | the research suite run mongodb-2026-10-14 |
| 1350 | — | — | rolling upgrade & elections | Atlas cluster tiers (M30) & major-version upgrade mechanics | dr | covered | mongodb-cohort-85a1dc6f9f63 | the research suite run mongodb-2026-10-14 |
| 1351 | — | — | SAML 2.0 SSO flow | Atlas Federated Authentication | dr | covered | mongodb-cohort-80fbdb0c7a29 | the research suite run mongodb-2026-10-14 |
| 1352 | — | — | SCIM provisioning | Atlas Federated Authentication | dr | covered | mongodb-cohort-80fbdb0c7a29 | the research suite run mongodb-2026-10-14 |
| 1353 | — | — | SDAM Topology State Machine | MongoDB Driver Internals | dr | covered | mongodb-cohort-807fe1a78902 | — |
| 1354 | — | — | Secret Rotation | Atlas Service Accounts | dr | covered | mongodb-cohort-cc8b558405fc | the research suite run mongodb-2026-10-14 |
| 1355 | — | — | Server Discovery and Monitoring RTT estimates | Server Selection Algorithm | dr | frontier | mongodb-cohort-6c026d4056b6 | — |
| 1356 | — | — | Server Selection Timeout | Client Side Operations Timeout (CSOT) | dr | covered | mongodb-cohort-85a1dc6f9f63 | the research suite run mongodb-2026-10-14 |
| 1357 | — | — | Server selection timeout and retry loop | Server Selection Algorithm | dr | frontier | mongodb-cohort-9cfafc173079 | — |
| 1358 | — | — | Service Account Roles | Atlas Service Accounts | dr | covered | mongodb-cohort-c80f8ee91387 | the research suite run mongodb-2026-10-14 |
| 1359 | — | — | Service account secret rotation | Atlas Identity Federation and Resource Policy Boundaries | dr | covered | mongodb-cohort-c80f8ee91387 | the research suite run mongodb-2026-10-14 |
| 1360 | — | — | Sharded Cluster Maintenance | Atlas Maintenance Windows | dr | covered | mongodb-cohort-ea02d11a28a2 | the research suite run mongodb-2026-10-14 |
| 1361 | — | — | Sharded cluster upgrade ordering | MongoDB Upgrade Paths | dr | covered | mongodb-cohort-1228883058e5 | — |
| 1362 | — | — | SORT_MERGE and $in sort expansion | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds; MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-b8aaa2ab12b6 | — |
| 1363 | — | — | Storage Autoscaling | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-f087e8e1b919 | the research suite run mongodb-2026-10-14 |
| 1364 | — | — | Storage Tier Selection | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-f087e8e1b919 | the research suite run mongodb-2026-10-14 |
| 1365 | — | — | Streaming BSON Parser Architecture | Diagnostic Tool Design | dr | covered | mongodb-cohort-1b886b15b9c1 | the research suite run mongodb-2026-10-14 |
| 1366 | — | — | Tableau Certified Connector | Atlas SQL Interface MongoSQL | dr | covered | mongodb-cohort-1edff5c43b6b | the research suite run mongodb-2026-10-14 |
| 1367 | — | — | Tail Latency Mitigation | Client Side Operations Timeout (CSOT) | dr | covered | mongodb-cohort-269152d0bf72 | the research suite run mongodb-2026-10-14 |
| 1368 | — | — | TCMalloc per-CPU caches | MongoDB 8.0 performance changes & read-path regressions vs 7.0 | dr | covered | mongodb-cohort-af5a1bf59f02 | the research suite run mongodb-2026-10-14 |
| 1369 | — | — | Telemetry Overhead Bounding Algorithms | Diagnostic Tool Design | dr | covered | mongodb-cohort-5914885288b0 | the research suite run mongodb-2026-10-14 |
| 1370 | — | — | Terraform Atlas Provider | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-647b54b90f3d | the research suite run mongodb-2026-10-14 |
| 1371 | — | — | Terraform Integration | Atlas Service Accounts | dr | covered | mongodb-cohort-a490b7d70d3f | the research suite run mongodb-2026-10-14 |
| 1372 | — | — | Terraform mongodbatlas_service_account without initial secret | Atlas Identity Federation and Resource Policy Boundaries | dr | covered | mongodb-cohort-a490b7d70d3f | the research suite run mongodb-2026-10-14 |
| 1373 | — | — | Tier 0 Tier 1 Tier 2 Strategy | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-f087e8e1b919 | the research suite run mongodb-2026-10-14 |
| 1374 | — | — | Time Series Aggregation | MongoDB Aggregation Pipeline | dr | covered | mongodb-cohort-9951a37f6fb4 | the research suite run mongodb-2026-10-14 |
| 1375 | — | — | Time Series Archive Rules | Archive Rules | dr | covered | mongodb-cohort-8125c71e823d | the research suite run mongodb-2026-10-14 |
| 1376 | — | — | TLS Encryption | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-a01124d580c7 | the research suite run mongodb-2026-10-14 |
| 1377 | — | — | Transaction Limits | MongoDB Transactions | dr | covered | mongodb-cohort-c98d28ad4b7f | — |
| 1378 | — | — | Transit Gateway Patterns | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-7872c1e1d1c9 | the research suite run mongodb-2026-10-14 |
| 1379 | — | — | Unique index requirements when refining a shard key | Shard key index constraints when dropping or hiding indexes | dr | frontier | mongodb-cohort-67232cc8ea85 | — |
| 1380 | — | — | Unused index detection with $indexStats | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds; MongoDB Explain Plans, Query Planner and Plan Cache; MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead; Query Efficiency as a Cost Lever | dr | covered | mongodb-cohort-b8244b58f531 | — |
| 1381 | — | — | VPC Peering | MongoDB Atlas AWS Networking | dr | covered | mongodb-cohort-663a537252ef | the research suite run mongodb-2026-10-14 |
| 1382 | — | — | Window Functions ($setWindowFields) | MongoDB Aggregation Pipeline | dr | covered | mongodb-cohort-58a562caa2ac | the research suite run mongodb-2026-10-14 |
| 1383 | — | — | WiredTiger cache eviction and dirty ratio | MongoDB Time-Series Query and Index Optimization; MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | covered | mongodb-cohort-c708d87eacee | — |
| 1384 | — | — | WiredTiger Compaction Algorithm | MongoDB autoCompact | dr | covered | mongodb-cohort-afc52fa5e292 | — |
| 1385 | — | — | WiredTiger Storage Engine Internals | MongoDB Performance Troubleshooting | dr | covered | mongodb-cohort-30502856e637 | — |
| 1386 | — | — | WiredTiger Ticket Metric Telemetry in FTDC | FTDC and Log Tooling | dr | covered | mongodb-cohort-fec23d9e5b40 | the research suite run mongodb-2026-10-14 |
| 1387 | — | — | wiredTigerEngineRuntimeConfig | WiredTiger Storage Engine Internals | dr | covered | mongodb-cohort-889b8ae4c694 | the research suite run mongodb-2026-10-14 |

## Original labels and parent provenance

Every label remains assigned to its canonical identity in the JSON inventory. Repeated input occurrences remain separate.

- **Connection pooling and connection-storm control for Atlas (serverless and Lambda clients)** (`mongodb-f87842d57963ee96`): Connection pooling and connection-storm control for Atlas (serverless and Lambda clients)
- **Atlas Billing and Invoice Anatomy** (`mongodb-0ece5184c1fdef4e`): Atlas Billing and Invoice Anatomy
- **Atlas Cost Explorer and Billing Data API** (`mongodb-a2731cc352109017`): Atlas Cost Explorer and Billing Data API
- **Connection Pool Tuning** (`mongodb-2ba59d0ac82626c2`): Connection Pool Tuning
- **MongoDB Atlas Cost Optimization** (`mongodb-2e0ab5902f609d4e`): MongoDB Atlas Cost Optimization
- **Read Concern** (`mongodb-886c88cd44874155`): Read Concern
- **Time series cardinality and metaField design** (`mongodb-37c367b29bc32cb1`): Time series cardinality and metaField design
- **Write Concern** (`mongodb-cbb1a24df4b92704`): Write Concern
- **MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting** (`mongodb-ebf75b34158e1aef`): $in and $or Index Bounds and Union Plans; Blocking Sort and Index-Backed Sort; Count and Distinct and Sampling Optimization; Cursor and Read-Path Tuning (batchSize and maxTimeMS and read preference); MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting; Pagination Patterns (skip-limit vs range-keyset); Projection Optimization and Covered Query Design; Query Operator Anti-Patterns ($regex and negation and $where and $expr and $exists); Sharded Query Targeting and Scatter-Gather
- **Resource Tags and Cost Allocation (Showback/Chargeback)** (`mongodb-34b0f66158b4615c`): Resource Tags and Cost Allocation (Showback/Chargeback)
- **Shard key index constraints when dropping or hiding indexes** (`mongodb-efd576940abfe93a`): Shard key index constraints when dropping or hiding indexes
- **MongoDB Major-Version Upgrade Regression Detection** (`mongodb-c636876aa5b37f1a`): MongoDB Major-Version Upgrade Regression Detection
- **Connection pool sizing and connection-storm control for Atlas (serverless and Lambda clients)** (`mongodb-2f1fbe31e1058a42`): Connection pool sizing and connection-storm control for Atlas (serverless and Lambda clients)
- **Continuous Cloud Backup (PITR)** (`mongodb-e83f4299444c980a`): Continuous Cloud Backup (PITR)
- **Replication Lag Monitoring** (`mongodb-293fc63defd20640`): Replication Lag Monitoring
- **Hot shard diagnosis and shard key remediation** (`mongodb-e18f2f1019762eea`): Hot shard diagnosis and shard key remediation
- **Shard Key Design for Multi-Tenancy** (`mongodb-0722ac70ba512fc5`): Shard Key Design for Multi-Tenancy
- **$queryStats aggregation stage** (`mongodb-fc9325d08a92f24b`): $queryStats aggregation stage
- **CSOT Client-Side Operations Timeout** (`mongodb-ff15c623b8b09037`): CSOT Client-Side Operations Timeout
- **Streaming Write Semantics** (`mongodb-8e2185f1d186e66e`): Streaming Write Semantics
- **Relational Migrator** (`mongodb-9aeb2a14db65818e`): Relational Migrator
- **$elemMatch semantics on arrays of subdocuments** (`mongodb-08429aa785fe6371`): $elemMatch semantics on arrays of subdocuments
- **Atlas Required Memory metric sizing** (`mongodb-1364d4a397c6e1b9`): Atlas Required Memory metric sizing
- **Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe)** (`mongodb-573b556653dd02bc`): Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe)
- **Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation)** (`mongodb-c10d82f9b114b9c2`): Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation)
- **MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds** (`mongodb-c1d520a28cfd05f5`): Compound Indexes and ESR Rule; Index Anti-Patterns; Index Intersection; Index Selectivity and Covering Queries; MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds; Multikey Indexes; Multikey Indexes and Array Query Bounds; Partial Indexes; Sparse Indexes
- **MongoDB Explain Plans, Query Planner and Plan Cache** (`mongodb-3ca1bf011ae25308`): Explain Plan Interpretation; Index Analysis; Index Analysis with $indexStats and Unused-Index Detection; Index Effectiveness Measurement; MongoDB Explain Plans, Query Planner and Plan Cache; Query Planning and Plan Cache; Query Settings and Persistent Index Hints (8.0); Query Shapes and Query Hash and $queryStats; Slow Query Monitoring; Slow Query Monitoring (profiler and slow-query log and planSummary); explain-executionStats-usedDisk; hint() and Index Forcing
- **Reading sharded explain output (shards, SINGLE_SHARD, SHARD_MERGE)** (`mongodb-9cfbe719bb847f18`): Reading sharded explain output (shards, SINGLE_SHARD, SHARD_MERGE)
- **Sessions** (`mongodb-1225ae6c1ae69dcb`): Sessions
- **Relevance Scoring** (`mongodb-d7b51fdbeeafc6d4`): Relevance Scoring
- **analyzeShardKey and query sampling** (`mongodb-779f34dfa36f6756`): analyzeShardKey and query sampling
- **analyzeShardKey query sampling and candidate-key scoring** (`mongodb-fe8dc1ff0a3946a4`): analyzeShardKey query sampling and candidate-key scoring
- **Binary downgrade window** (`mongodb-fed1dbd358082eb0`): Binary downgrade window
- **Connection Capacity** (`mongodb-9b3f4271a4f94566`): Connection Capacity
- **Cutover Strategies** (`mongodb-fada6ecbb197050a`): Cutover Strategies
- **Long-Running Transactions and Cache Pressure** (`mongodb-bd48f163cf4aad2f`): Long-Running Transactions and Cache Pressure
- **Delete propagation and reconciliation for $merge-maintained views** (`mongodb-ca53ac7eb7938f77`): Delete propagation and reconciliation for $merge-maintained views
- **Index build commit quorum and hung builds** (`mongodb-4a35364ee8642200`): Index build commit quorum and hung builds
- **$queryStats and $currentOp as alternatives to the profiler** (`mongodb-43e566a9f0877fdd`): $queryStats and $currentOp as alternatives to the profiler
- **Goal-State Automation Configuration** (`mongodb-7eeff17750501acd`): Goal-State Automation Configuration
- **Hashed and compound hashed shard keys and index coverage** (`mongodb-7fbf6e87171ca9e8`): Hashed and compound hashed shard keys and index coverage
- **Idempotent incremental refresh design for $merge (high-water marks, delete handling)** (`mongodb-cda5307f33b4a8cd`): Idempotent incremental refresh design for $merge (high-water marks, delete handling)
- **Time Series Sharding Patterns** (`mongodb-b95997f3bf6b8cd2`): Time Series Sharding Patterns
- **change-stream-resume-token** (`mongodb-e61fc4071aaf13a2`): change-stream-resume-token
- **mongodbatlas_advanced_cluster Resource** (`mongodb-a9d3b419f8005bea`): mongodbatlas_advanced_cluster Resource
- **Time series bucketing parameters: granularity, bucketMaxSpanSeconds, bucketRoundingSeconds** (`mongodb-e6ac0ae929aaad78`): Time series bucketing parameters: granularity, bucketMaxSpanSeconds, bucketRoundingSeconds
- **WiredTiger cache sizing and working-set fit** (`mongodb-0831aa6a730c33af`): WiredTiger cache sizing and working-set fit
- **Multi-Cloud Global Clusters** (`mongodb-6e296e4d14ba240e`): Multi-Cloud Global Clusters
- **Partitioner Strategies** (`mongodb-d68258b7aabbe882`): Partitioner Strategies
- **Server Selection Algorithm** (`mongodb-e96f3cea4615f8a6`): Server Selection Algorithm
- **FCV pinning and downgrade preservation window** (`mongodb-04bf2db495d9e0d8`): FCV pinning and downgrade preservation window
- **FCV unpinned too early** (`mongodb-9b6bd5c9474a5870`): FCV unpinned too early
- **verification-modes** (`mongodb-85ea9fa5090b43bc`): verification-modes
- **Embedding Pipelines** (`mongodb-8f22092270f5a0d9`): Embedding Pipelines
- **Hybrid Search** (`mongodb-81db1c65ba54475f`): Hybrid Search
- **Atlas storage auto-scaling triggers, cooldowns and write blocking** (`mongodb-307154446e50395e`): Atlas storage auto-scaling triggers, cooldowns and write blocking
- **WT_CACHE_FULL / Cache Pressure Troubleshooting** (`mongodb-db7c9d824f2bdcc7`): WT_CACHE_FULL / Cache Pressure Troubleshooting
- **Row-Level Security Patterns** (`mongodb-6cd779dbe9ee778f`): Row-Level Security Patterns
- **Atlas Flex Pricing and Flex-vs-Dedicated Break-Even** (`mongodb-b1335293548be263`): Atlas Flex Pricing and Flex-vs-Dedicated Break-Even
- **Atlas Query Targeting alerts** (`mongodb-8415f2cba2c3b369`): Atlas Query Targeting alerts
- **Atlas Search index sync lag and search-node sizing** (`mongodb-f705ab03ffdbb849`): Atlas Search index sync lag and search-node sizing
- **Cost Governance Guardrails (Resource Policies and IaC Cost Controls)** (`mongodb-b5c7cf5056927357`): Cost Governance Guardrails (Resource Policies and IaC Cost Controls)
- **currentOp planSummary for running operations** (`mongodb-384737b464038979`): currentOp planSummary for running operations
- **Disk IOPS Burst Credit Depletion Playbook** (`mongodb-ecfb036c4afe2ff2`): Disk IOPS Burst Credit Depletion Playbook
- **Driver compatibility matrix (Java/Node/Python/.NET/Go)** (`mongodb-8bf55ee4e65b9622`): Driver compatibility matrix (Java/Node/Python/.NET/Go)
- **Oplog Sizing** (`mongodb-0a476e64b6d39db7`): Oplog Sizing
- **Unique and TTL index side effects on removal** (`mongodb-c6e55a2528d91131`): Unique and TTL index side effects on removal
- **Atlas Search Analyzers and Tokenizers** (`mongodb-30fc967f108fb07d`): Atlas Search Analyzers and Tokenizers
- **Arbiter handling and PSA topology** (`mongodb-44536837d3b06d08`): Arbiter handling and PSA topology
- **Index filters (planCacheSetFilter) deprecation and migration to query settings** (`mongodb-55e65f5d4cc3196b`): Index filters (planCacheSetFilter) deprecation and migration to query settings
- **Oplog minimum retention window and storage auto-scaling** (`mongodb-491fab6d89343906`): Oplog minimum retention window and storage auto-scaling
- **Read concern available, secondary reads and orphaned documents** (`mongodb-c0c218d6058d6708`): Read concern available, secondary reads and orphaned documents
- **Trigger Error Handling and Suspension** (`mongodb-11a76a3c5a140569`): Trigger Error Handling and Suspension
- **Tenant Lifecycle Operations** (`mongodb-03092fba35b0c679`): Tenant Lifecycle Operations
- **Working Set Sizing** (`mongodb-ee926c17fd0c9aab`): Working Set Sizing
- **Blocking sort memory limit and allowDiskUse** (`mongodb-2ec006134792b0c5`): Blocking sort memory limit and allowDiskUse
- **Oplog window overflow** (`mongodb-2f8b900ca59491b6`): Oplog window overflow
- **Tenant Isolation Models** (`mongodb-f1d542e05e7cbb05`): Tenant Isolation Models
- **analyzeShardKey workload sampling** (`mongodb-82725d8090f62c84`): analyzeShardKey workload sampling
- **Atlas Live Migration** (`mongodb-c0e7740b3474ad22`): Atlas Live Migration
- **Atlas Query Profiler and slow-ops logs for shape discovery** (`mongodb-c0b4ec4abda68f2a`): Atlas Query Profiler and slow-ops logs for shape discovery
- **majority commit point mechanics** (`mongodb-1d7040ecb276c204`): majority commit point mechanics
- **Oplog capacity for initial sync, live migration and bulk loads** (`mongodb-09bbc3b6858039a7`): Oplog capacity for initial sync, live migration and bulk loads
- **Ops Manager High Availability** (`mongodb-231bbf4fcc010083`): Ops Manager High Availability
- **Org and Project Governance** (`mongodb-a0b18cacc47f9816`): Org and Project Governance
- **Query settings: index hints and queryFramework (persistent query settings)** (`mongodb-ca205f42c57aed6d`): Query settings: index hints and queryFramework (persistent query settings)
- **setQuerySettings index hints and queryFramework** (`mongodb-d10b2336807b3bca`): setQuerySettings index hints and queryFramework
- **Snapshot reads (atClusterTime) and history window sizing on secondaries** (`mongodb-1069c8846346b64e`): Snapshot reads (atClusterTime) and history window sizing on secondaries
- **Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds** (`mongodb-8adf3e10aee700b8`): Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds
- **Time series backfill ordering and batching** (`mongodb-c9027de218a3e1bb`): Time series backfill ordering and batching
- **Two-phase write protocol and writes without the shard key** (`mongodb-acb9c6f2bef7be75`): Two-phase write protocol and writes without the shard key
- **Resume-from-last-key pattern for killed cursors** (`mongodb-87979fda64c57aa4`): Resume-from-last-key pattern for killed cursors
- **MongoDB Replication** (`mongodb-9dfbda4aab833ec7`): MongoDB Replication
- **Distributed Sharded Transactions** (`mongodb-fa66e239fa751be7`): Distributed Sharded Transactions
- **Forcing plans with hint and internal query knobs** (`mongodb-3c16bf2fb6163207`): Forcing plans with hint and internal query knobs
- **Keyset pagination with compound sort keys** (`mongodb-206b17ff2b661cc6`): Keyset pagination with compound sort keys
- **Replica Set Node Topology Cost** (`mongodb-0603a1469d27616e`): Replica Set Node Topology Cost
- **Sharded Cluster Cost Economics** (`mongodb-6d289c725d18d57c`): Sharded Cluster Cost Economics
- **Targeted vs scatter-gather shard routing in explain** (`mongodb-ae24ea0dd0b4adcd`): Targeted vs scatter-gather shard routing in explain
- **Transaction Anti-Patterns** (`mongodb-4928c87584404e5d`): Transaction Anti-Patterns
- **Balancer data-size policy and zone-aware migration** (`mongodb-ba374350fd1b2bfc`): Balancer data-size policy and zone-aware migration
- **Batch Writes and Idempotency** (`mongodb-2309e853cdbdaa04`): Batch Writes and Idempotency
- **Cloud Run Atlas Connection Pooling** (`mongodb-1150b2a3d696f3bd`): Cloud Run Atlas Connection Pooling
- **Connection Pooling Strategies** (`mongodb-5f7fe4f73702481f`): Connection Pooling Strategies
- **exactly-once-semantics** (`mongodb-0a0f08e1065c4eb3`): exactly-once-semantics
- **startup-mode-copy-existing** (`mongodb-644dc3e672f9cef0`): startup-mode-copy-existing
- **Vector index memory sizing and quantization trade-offs on Search Nodes** (`mongodb-ba7654359cbe0bed`): Vector index memory sizing and quantization trade-offs on Search Nodes
- **Vector Quantization** (`mongodb-80d57bbc1a3ff7f0`): Vector Quantization
- **Watermarks and Late-Event Tolerance** (`mongodb-70a301174c7b5100`): Watermarks and Late-Event Tolerance
- **write-model-strategies** (`mongodb-26a47b53403f7d61`): write-model-strategies
- **Atlas disk write-blocking thresholds and recovery** (`mongodb-929575493d4087d5`): Atlas disk write-blocking thresholds and recovery
- **Unique, TTL and shard-key indexes that read as unused** (`mongodb-07243021cb28b849`): Unique, TTL and shard-key indexes that read as unused
- **outbox-pattern** (`mongodb-805a32223498832d`): outbox-pattern
- **hasNextPage without computing total pages** (`mongodb-374a48a694584c66`): hasNextPage without computing total pages
- **Blockstore and Snapshot Stores** (`mongodb-3c606797486e510a`): Blockstore and Snapshot Stores
- **Online Archive Data Access and Data Seek Query Cost Model** (`mongodb-2f4168ceffea93a9`): Online Archive Data Access and Data Seek Query Cost Model
- **Atlas Projects as Hard Isolation** (`mongodb-99b11dbde8bbd42c`): Atlas Projects as Hard Isolation
- **Planner plan scoring and EOF bonus** (`mongodb-80aea28e75b65dc6`): Planner plan scoring and EOF bonus
- **Compound shard-key prefix targeting** (`mongodb-ce157abec5c6e09d`): Compound shard-key prefix targeting
- **Backup Verification and Tabletop Exercises** (`mongodb-1f3bb6e22efac259`): Backup Verification and Tabletop Exercises
- **Index build commit quorum (commitQuorum and setIndexCommitQuorum)** (`mongodb-8cfb51d9d1717329`): Index build commit quorum (commitQuorum and setIndexCommitQuorum)
- **Leading-prefix redundant index detection** (`mongodb-e96aa6f8eaf5276b`): Leading-prefix redundant index detection
- **Multikey indexes and index-provided sort order** (`mongodb-2079ebf74b91e68a`): Multikey indexes and index-provided sort order
- **Multikey indexes and sort provision (multikeyPaths)** (`mongodb-6ee7d4ea2a06035e`): Multikey indexes and sort provision (multikeyPaths)
- **Oplog sizing and embedded-verifier memory for migrations** (`mongodb-4aeedcc6bc22ad05`): Oplog sizing and embedded-verifier memory for migrations
- **Per-node and per-shard $indexStats aggregation across replica sets and shards** (`mongodb-ddae0af93a2ef966`): Per-node and per-shard $indexStats aggregation across replica sets and shards
- **TemporarilyUnavailable and TransactionTooLargeForCache errors** (`mongodb-ddee6fb85d60a7b6`): TemporarilyUnavailable and TransactionTooLargeForCache errors
- **Atlas Search index behaviour with $out versus $merge targets** (`mongodb-1b80802c72c7649a`): Atlas Search index behaviour with $out versus $merge targets
- **Atlas Search index lifecycle on $out and $merge targets** (`mongodb-507dcfa59868cd10`): Atlas Search index lifecycle on $out and $merge targets
- **Coordinator failure recovery** (`mongodb-271ed7f506127b14`): Coordinator failure recovery
- **WiredTiger cache pressure and write tickets during index builds** (`mongodb-accb3591cec73542`): WiredTiger cache pressure and write tickets during index builds
- **WiredTiger history store and majority commit point cache pressure** (`mongodb-e6eb894969ac5dd9`): WiredTiger history store and majority commit point cache pressure
- **Cross-DC App DB Placement** (`mongodb-80b52929be625cc4`): Cross-DC App DB Placement
- **mongot replication lag, oplog window and index rebuild cost** (`mongodb-9f2f133f2977052b`): mongot replication lag, oplog window and index rebuild cost
- **Atlas Cloud Backup (snapshots)** (`mongodb-3a68d6abb30691ea`): Atlas Cloud Backup (snapshots)
- **Compound-index prefix and sort-direction compatibility** (`mongodb-d074d6ebe3c3758e`): Compound-index prefix and sort-direction compatibility
- **Reading indexed `$or` plans with explain** (`mongodb-3f1dc80ac02788d8`): Reading indexed `$or` plans with explain
- **Retryable Reads** (`mongodb-32f6f7319271dab0`): Retryable Reads
- **Atlas Tier Selection** (`mongodb-831ca81a94abf8f6`): Atlas Tier Selection
- **Balancer tuning and chunk migration cost** (`mongodb-812fc7cfa213d693`): Balancer tuning and chunk migration cost
- **Connectivity Troubleshooting** (`mongodb-9b7b21732613ea3f`): Connectivity Troubleshooting
- **Query shape and queryShapeHash stability** (`mongodb-ba11218fbabf4ce3`): Query shape and queryShapeHash stability
- **Query shapes and queryShapeHash stability** (`mongodb-3fcfc50df3a9d30a`): Query shapes and queryShapeHash stability
- **Schema Design for Multi-Tenancy** (`mongodb-367b33525f1a18ca`): Schema Design for Multi-Tenancy
- **WiredTiger checkpoints and checkpoint duration** (`mongodb-e6181cc3d05b4127`): WiredTiger checkpoints and checkpoint duration
- **Commit quorum and the vote-to-commit point of no return** (`mongodb-5f54c51046d88611`): Commit quorum and the vote-to-commit point of no return
- **DLQ-error-handling** (`mongodb-b349b54b746f26ff`): DLQ-error-handling
- **Keyset (resume) pagination for restartable cursors** (`mongodb-7a91ee8d2368657f`): Keyset (resume) pagination for restartable cursors
- **Terraform effective fields and auto-scaling drift** (`mongodb-6da6e3ca2340a232`): Terraform effective fields and auto-scaling drift
- **mongodb-schema-design** (`mongodb-d21a0f8668eb659b`): mongodb-schema-design
- **Atlas Vector Search RAM sizing and automatic quantization** (`mongodb-7a014dcb5be07f3c`): Atlas Vector Search RAM sizing and automatic quantization
- **Vector Search Quantization and Embedding Storage Cost** (`mongodb-68eed2fa6420c11a`): Vector Search Quantization and Embedding Storage Cost
- **Read Preference** (`mongodb-b25cdd40f55ed11a`): Read Preference
- **snapshot read concern** (`mongodb-7ae3417dfaa5aaa7`): snapshot read concern
- **DNS SRV Discovery** (`mongodb-867fbd2c0ff96460`): DNS SRV Discovery
- **Hashed shard-key write distribution and local index locality** (`mongodb-fa3aaf6e5b264c5d`): Hashed shard-key write distribution and local index locality
- **read concern in sharding** (`mongodb-b59979b00018c214`): read concern in sharding
- **terminateSecondaryReadsOnOrphanCleanup and QueryPlanKilled 175** (`mongodb-a980b7fae06cc7a2`): terminateSecondaryReadsOnOrphanCleanup and QueryPlanKilled 175
- **Co-located vs dedicated mongot decision thresholds and failure modes** (`mongodb-0999b277ab0619e9`): Co-located vs dedicated mongot decision thresholds and failure modes
- **Orphaned documents and range deletion** (`mongodb-cf4c82ea24e1e659`): Orphaned documents and range deletion
- **Inline user-facing querySettings (9.0)** (`mongodb-1acd77491ffa58b1`): Inline user-facing querySettings (9.0)
- **Elasticsearch-to-Atlas Search migration and dual-run cost** (`mongodb-6e39951e23eed351`): Elasticsearch-to-Atlas Search migration and dual-run cost
- **Detecting inconsistent indexes across shards** (`mongodb-b8db54bb2db88fcc`): Detecting inconsistent indexes across shards
- **Embedding generation and reranking token spend in retrieval TCO** (`mongodb-29cffc695732336b`): Embedding generation and reranking token spend in retrieval TCO
- **Atlas independent shard scaling and auto-scaling** (`mongodb-d45298dbbaa4894d`): Atlas independent shard scaling and auto-scaling
- **Atlas independent shard scaling and per-shard auto-scaling** (`mongodb-52309d79b2670167`): Atlas independent shard scaling and per-shard auto-scaling
- **Multiplanning storms after a plan cache flush** (`mongodb-298e8ce29188b7d8`): Multiplanning storms after a plan cache flush
- **Gen1 versus Gen2 IOPS provisioning and instance-level EBS/VM IOPS caps** (`mongodb-62d8459507a70ec8`): Gen1 versus Gen2 IOPS provisioning and instance-level EBS/VM IOPS caps
- **Plan cache key and $in length (classic vs SBE)** (`mongodb-46ba15d071976313`): Plan cache key and $in length (classic vs SBE)
- **Atlas Performance Advisor index suggestions** (`mongodb-3a87627c1ad10d38`): Atlas Performance Advisor index suggestions
- **Pipeline Optimization** (`mongodb-0d8208f3002d7111`): Pipeline Optimization
- **Right-sizing Atlas tier from cache and CPU metrics** (`mongodb-f60c6e68486dfc43`): Right-sizing Atlas tier from cache and CPU metrics
- **Sort direction and compound index prefix rules** (`mongodb-94216d2a3595e02e`): Sort direction and compound index prefix rules
- **Rolling replica-set upgrade** (`mongodb-db1fdc3b0ad9f563`): Rolling replica-set upgrade
- **$indexStats usage statistics and their reset conditions** (`mongodb-c0603c927eb5e2af`): $indexStats usage statistics and their reset conditions
- **Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes)** (`mongodb-5cf3317db9573e29`): Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes)
- **Time Series Collection Creation (timeField, metaField, granularity)** (`mongodb-67319bd9bd91629d`): Time Series Collection Creation (timeField, metaField, granularity)
- **Atlas compute auto-scaling for sharded clusters** (`mongodb-8a8588d225b66629`): Atlas compute auto-scaling for sharded clusters
- **Atlas Custom Database Roles** (`mongodb-95f4699b3f26e8cf`): Atlas Custom Database Roles
- **Balancer, chunk migration and jumbo chunk remediation** (`mongodb-e9767d35bd3564d7`): Balancer, chunk migration and jumbo chunk remediation
- **Commit quorum and votingMembers** (`mongodb-bf66bee7b46e6125`): Commit quorum and votingMembers
- **Orphaned documents and read concern available versus local** (`mongodb-7b6bda9bc92b8d74`): Orphaned documents and read concern available versus local
- **Safe index removal: locks, rollback and regression checks** (`mongodb-639b9604ad5f8611`): Safe index removal: locks, rollback and regression checks
- **SHARDING_FILTER stage and chunkSkips** (`mongodb-4f273eb41d058596`): SHARDING_FILTER stage and chunkSkips
- **Atlas Admin API Date Versioned Media Types** (`mongodb-1f0bce13214d13d7`): Atlas Admin API Date Versioned Media Types
- **Atlas Key Rotation AKV** (`mongodb-973728ab50559251`): Atlas Key Rotation AKV
- **Atlas Search index rebuild after migration** (`mongodb-a79da32a252623e6`): Atlas Search index rebuild after migration
- **readConcern available on sharded clusters** (`mongodb-4baf9880f7b8ff7e`): readConcern available on sharded clusters
- **Terraform Provider v2 Migration** (`mongodb-205c702762973dd4`): Terraform Provider v2 Migration
- **Atlas Networking IaC** (`mongodb-35098e91d1fce562`): Atlas Networking IaC
- **WiredTiger cache sizing and memory fragmentation** (`mongodb-ed3d0074fb4a0951`): WiredTiger cache sizing and memory fragmentation
- **Change-stream resumability** (`mongodb-fa0e1fa6bf45f432`): Change-stream resumability
- **Sampling CE accuracy under sparse sample matches** (`mongodb-96e56dfd23741c03`): Sampling CE accuracy under sparse sample matches
- **Workload Identity Federation Atlas** (`mongodb-785a339511d80111`): Workload Identity Federation Atlas
- **Atlas Alerts** (`mongodb-7d65ef6cbed4974e`): Atlas Alerts
- **Authentication Mechanisms** (`mongodb-65802435cf3141ee`): Authentication Mechanisms
- **TTL and Automatic Bucket Deletion** (`mongodb-c79267f91cb69487`): TTL and Automatic Bucket Deletion
- **Custom Analyzers** (`mongodb-11b24404904fb2ce`): Custom Analyzers
- **ESR guideline and $in placement in compound indexes** (`mongodb-7410bfb0be0aa4ce`): ESR guideline and $in placement in compound indexes
- **Read and Write Concerns** (`mongodb-f8b9729e885f5a45`): Read and Write Concerns
- **WiredTiger checkpoints and dirty-page write cost** (`mongodb-bea205b365b40fc6`): WiredTiger checkpoints and dirty-page write cost
- **Atlas Search Nodes cost floor and co-located versus dedicated search** (`mongodb-81d16539892f095e`): Atlas Search Nodes cost floor and co-located versus dedicated search
- **Azure Private Link for Atlas** (`mongodb-73a7e75a15696eae`): Azure Private Link for Atlas
- **bulk-write-ordering** (`mongodb-8a2fd57f6ba6b453`): bulk-write-ordering
- **Cluster-to-Cluster Sync Phases** (`mongodb-7d909a5d90df429d`): Cluster-to-Cluster Sync Phases
- **Dead Letter Queue (DLQ)** (`mongodb-c8b502b0a8b14d5c`): Dead Letter Queue (DLQ)
- **GCP Private Service Connect for Atlas** (`mongodb-6a015dec28c88af7`): GCP Private Service Connect for Atlas
- **Service Account OAuth 2.0 Authentication** (`mongodb-f568adfc144b0123`): Service Account OAuth 2.0 Authentication
- **Chunk migration commit, range deleter and orphan cleanup internals** (`mongodb-b61f815eb024910f`): Chunk migration commit, range deleter and orphan cleanup internals
- **Application-level dual-write migration pattern** (`mongodb-f2eecec57154f31b`): Application-level dual-write migration pattern
- **Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams** (`mongodb-4b2ca1d9c19e5ee0`): Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams
- **Local Mode and Air-Gap Deployments** (`mongodb-a796e7969055883f`): Local Mode and Air-Gap Deployments
- **BI Connector EOL Migration** (`mongodb-ad2410ac76a2c88f`): BI Connector EOL Migration
- **$group accumulator memory caps** (`mongodb-c9561fed40814a7b`): $group accumulator memory caps
- **Billing Alerts and Budget Controls** (`mongodb-688e8ec3b322c0be`): Billing Alerts and Budget Controls
- **Compound index vs index union for $or** (`mongodb-7ad2761789665771`): Compound index vs index union for $or
- **DISTINCT_SCAN for distinct command** (`mongodb-78d46bceec211263`): DISTINCT_SCAN for distinct command
- **Equality-Sort-Range index ordering** (`mongodb-ccd1360706f25e20`): Equality-Sort-Range index ordering
- **ERS exception for selective range predicates** (`mongodb-03da0e6d460a2198`): ERS exception for selective range predicates
- **explain() executionStats reading** (`mongodb-67d97cb48ec1e2cc`): explain() executionStats reading
- **Multi-Document Transactions** (`mongodb-c9e37257a87fa913`): Multi-Document Transactions; Multi-document Transactions
- **Private endpoints and VPC peering transfer charges** (`mongodb-473d0349f68173bb`): Private endpoints and VPC peering transfer charges
- **SHARDING_FILTER orphan filtering** (`mongodb-0a7d0c311546cd16`): SHARDING_FILTER orphan filtering
- **Hashed, ranged and compound hashed shard keys** (`mongodb-6fb4e66a9e4066ec`): Hashed, ranged and compound hashed shard keys
- **Zone sharding and region-aware shard keys** (`mongodb-96f5d5a08cab86fe`): Zone sharding and region-aware shard keys
- **Atlas Vector Search numCandidates tuning and recall measurement against ENN** (`mongodb-ac984432ae410e27`): Atlas Vector Search numCandidates tuning and recall measurement against ENN
- **Azure Functions Atlas Connection Pooling** (`mongodb-cbef6adc22277d34`): Azure Functions Atlas Connection Pooling
- **Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis)** (`mongodb-90c2d5519c3220af`): Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis)
- **Atlas Stream Processing streaming materialized views** (`mongodb-fa4d655140a67c4f`): Atlas Stream Processing streaming materialized views
- **Reducing shard count and unsharding collections on Atlas** (`mongodb-e55deac1bde07add`): Reducing shard count and unsharding collections on Atlas
- **Atlas Metrics and Dashboards** (`mongodb-00275dfdefbbbacb`): Atlas Metrics and Dashboards
- **Pulumi mongodbatlas Provider** (`mongodb-396ca083246d8572`): Pulumi mongodbatlas Provider
- **initial-sync-and-cdc** (`mongodb-75db6711cad0d33a`): initial-sync-and-cdc
- **Atlas Auth Tier Feature Matrix M0 Flex M10** (`mongodb-fbf5a6a3149b5f07`): Atlas Auth Tier Feature Matrix M0 Flex M10
- **Balancer windows and per-collection balancing control** (`mongodb-696982ad112245fe`): Balancer windows and per-collection balancing control
- **Destination temporary scaling and post-cutover right-sizing** (`mongodb-5ccf34e9dd7c904e`): Destination temporary scaling and post-cutover right-sizing
- **dropIndexes locking and in-flight query behavior** (`mongodb-dd277d166251c39f`): dropIndexes locking and in-flight query behavior
- **Hidden indexes as a safe drop trial** (`mongodb-3dc7ee2ae326a104`): Hidden indexes as a safe drop trial
- **mongod diagnostic log slow-query format and slowOpSampleRate** (`mongodb-b548b9347267db0b`): mongod diagnostic log slow-query format and slowOpSampleRate
- **namespace-filtering** (`mongodb-64b1fd1b8764172e`): namespace-filtering
- **oplog-window-sizing** (`mongodb-b9954a02df7be96d`): oplog-window-sizing
- **Disk pre-warming SOP (Cookie 7.0→8.0 lesson)** (`mongodb-eaa3c07e691b6244`): Disk pre-warming SOP (Cookie 7.0→8.0 lesson)
- **Per-shard disk IOPS and storage constraints** (`mongodb-f5ea1a5b9eabc238`): Per-shard disk IOPS and storage constraints
- **reverse-sync-cutover** (`mongodb-00e0870a73783513`): reverse-sync-cutover
- **Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes** (`mongodb-ba0a48b5785697ff`): Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes
- **Validating AI-suggested indexes with explain** (`mongodb-ee6fcba7f750ab8c`): Validating AI-suggested indexes with explain
- **Redundant (prefix) index detection for compound indexes** (`mongodb-4e32a19d1f2c5971`): Redundant (prefix) index detection for compound indexes
- **SRV DNS Seedlist Format** (`mongodb-33ab7e4df25cb0c7`): SRV DNS Seedlist Format
- **Application-thread eviction and cache stalls** (`mongodb-9867c635985c54ea`): Application-thread eviction and cache stalls
- **Driver mismatch failure mode** (`mongodb-a40f49184ccaac18`): Driver mismatch failure mode
- **Flex versus Dedicated boundary: ops-per-second pricing and missing features** (`mongodb-9d93aba50859f3d4`): Flex versus Dedicated boundary: ops-per-second pricing and missing features
- **metaField cardinality and active-bucket count** (`mongodb-3d2f9fb21415d4cc`): metaField cardinality and active-bucket count
- **MongoDB Node.js driver pool sizing under Lambda concurrency** (`mongodb-9a69c000f8846b80`): MongoDB Node.js driver pool sizing under Lambda concurrency
- **Partition Fields** (`mongodb-82247c13c947f7b3`): Partition Fields
- **serverStatus bucketCatalog and collStats timeseries counters** (`mongodb-0aeaaf1da0623b3c`): serverStatus bucketCatalog and collStats timeseries counters
- **TLS/SSL Configuration** (`mongodb-db3a865eb96ff746`): TLS/SSL Configuration
- **Source Oplog Window Sizing for Migration** (`mongodb-8d686e17f1564bdc`): Source Oplog Window Sizing for Migration
- **moveCollection and unshardCollection** (`mongodb-0014a99f0d101e15`): moveCollection and unshardCollection
- **Cross-cloud application-tier placement and Atlas internet egress** (`mongodb-20ae69c53f13d417`): Cross-cloud application-tier placement and Atlas internet egress
- **mongosync reversible sync and the rollback window** (`mongodb-b1abe7bf26bd5cf5`): mongosync reversible sync and the rollback window
- **PSC Port-Mapped Architecture** (`mongodb-6f290a5ef9d9549c`): PSC Port-Mapped Architecture
- **Hashed versus ranged shard-key tradeoffs** (`mongodb-991d5f922cc78788`): Hashed versus ranged shard-key tradeoffs
- **majority read concern** (`mongodb-9bf292479b756e20`): majority read concern
- **WiredTiger block reuse, file fragmentation and freeStorageSize** (`mongodb-e5de220a8f56a644`): WiredTiger block reuse, file fragmentation and freeStorageSize
- **Write amplification and cache cost of unused indexes** (`mongodb-d859a3df74f89ce0`): Write amplification and cache cost of unused indexes
- **Connection Metrics** (`mongodb-0452c6fa8bb0eb48`): Connection Metrics
- **Plan cache flushes on index DDL** (`mongodb-9f10df9b9162e00b`): Plan cache flushes on index DDL
- **Application Database (App DB)** (`mongodb-9056a266ab8416bc`): Application Database (App DB)
- **Archive and TTL data lifecycle followed by compaction** (`mongodb-bc36eea828943d88`): Archive and TTL data lifecycle followed by compaction
- **Automation Agent** (`mongodb-11b072377b15d608`): Automation Agent
- **MongoDB Agent (Automation, Monitoring, Backup)** (`mongodb-1364d86e29fdc0ef`): MongoDB Agent (Automation, Monitoring, Backup)
- **Replica set oplog window and initial sync** (`mongodb-3e7a15a9315bdf6a`): Replica set oplog window and initial sync
- **Zone sharding for hardware-tiered shards** (`mongodb-7342a6b00fb95f34`): Zone sharding for hardware-tiered shards
- **Zone sharding for tiered hardware (hot, warm, cold)** (`mongodb-3ef0d50044b95622`): Zone sharding for tiered hardware (hot, warm, cold)
- **Atlas AWS IAM Database Auth** (`mongodb-38fdb1957e90e461`): Atlas AWS IAM Database Auth
- **Atlas Live Migration pull versus push versus standalone mongosync selection** (`mongodb-2863c01b9e032316`): Atlas Live Migration pull versus push versus standalone mongosync selection
- **Azure Key Vault Atlas BYOK** (`mongodb-cfb70a76bc6e6639`): Azure Key Vault Atlas BYOK
- **Google Cloud KMS BYOK** (`mongodb-55151eb37156c9a9`): Google Cloud KMS BYOK
- **Secrets Management** (`mongodb-01379de8ff01efae`): Secrets Management
- **VPC Peering GCP Atlas** (`mongodb-f305dcbf647fed32`): VPC Peering GCP Atlas
- **Multi-planner trial period and candidate plan ranking** (`mongodb-5efaa7e8d778364a`): Multi-planner trial period and candidate plan ranking
- **Zone sharding and Global Cluster shard keys** (`mongodb-097c5c30db2cddc7`): Zone sharding and Global Cluster shard keys
- **PSC Terraform GCP** (`mongodb-7e4714e5245a39bc`): PSC Terraform GCP
- **Schema Design for Storage Cost** (`mongodb-4ee4c48b68a076a3`): Schema Design for Storage Cost
- **Hashed shard keys and index support** (`mongodb-b3f8a3c9021603e8`): Hashed shard keys and index support
- **Config server / shards / mongos upgrade sequence** (`mongodb-162cc81ec9646cca`): Config server / shards / mongos upgrade sequence
- **Wire Protocol Compression** (`mongodb-c993ed9b7845f754`): Wire Protocol Compression
- **mongos version skew failure** (`mongodb-760068866cc8c0d5`): mongos version skew failure
- **Index filters and query settings versus hidden indexes** (`mongodb-3cb7eb42f317b1d7`): Index filters and query settings versus hidden indexes
- **Prometheus Integration** (`mongodb-cbc723dd40023fd5`): Prometheus Integration
- **Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete)** (`mongodb-c4f1160e54c251fc`): Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete)
- **Per-shard compute auto-scaling rules and limits on Atlas** (`mongodb-69f911f95ca28217`): Per-shard compute auto-scaling rules and limits on Atlas
- **PSA topology stepdown failure** (`mongodb-c838df92b4aa1289`): PSA topology stepdown failure
- **Reverse sync and rollback-window economics** (`mongodb-7655d46620fe7e30`): Reverse sync and rollback-window economics
- **SQL-to-MQL Translation** (`mongodb-ca0e40de03774e87`): SQL-to-MQL Translation
- **Per-shard IOPS and Gen2 storage on Atlas** (`mongodb-ed34f8099debb39e`): Per-shard IOPS and Gen2 storage on Atlas
- **Partition Field Immutability and Merge-Delete-Recreate Migration** (`mongodb-3262e83e6bffc840`): Partition Field Immutability and Merge-Delete-Recreate Migration
- **MongoDB cache-pressure monitor and ticket admission** (`mongodb-df5f7de57f6ca275`): MongoDB cache-pressure monitor and ticket admission
- **Lexical Prefilters for Vector Search** (`mongodb-c02776b6cbb4f796`): Lexical Prefilters for Vector Search
- **Cache stampede protection: leases, request coalescing, TTL jitter** (`mongodb-706c1e6361758778`): Cache stampede protection: leases, request coalescing, TTL jitter
- **$out-based time series rewrite and cutover** (`mongodb-869013037a0a4c33`): $out-based time series rewrite and cutover
- **Partition Field Leftmost-Prefix Ordering** (`mongodb-82062063877c20d7`): Partition Field Leftmost-Prefix Ordering
- **Reshard to the same key for adding and removing shards** (`mongodb-33676740c89bacf0`): Reshard to the same key for adding and removing shards
- **Live Migration to Atlas via mongosync** (`mongodb-3bdf92a3b2440fdb`): Live Migration to Atlas via mongosync
- **Atlas Query Profiler and Performance Advisor** (`mongodb-687c0d431bcb801a`): Atlas Query Profiler and Performance Advisor
- **SBE vs classic engine defaults** (`mongodb-4a80c717d11b8805`): SBE vs classic engine defaults; SBE vs classic engine explain output; SBE vs classic explain output
- **Dedicated Search Node storage and compute sizing** (`mongodb-e2b4909feecca57a`): Dedicated Search Node storage and compute sizing
- **mongosync-state-machine** (`mongodb-929fdd578d228da6`): mongosync-state-machine
- **Plan cache entry lifecycle: Inactive and Active entries and works growth** (`mongodb-4e03ff1169490c95`): Plan cache entry lifecycle: Inactive and Active entries and works growth
- **serverStatus metrics.query.planCache counters** (`mongodb-21cfa0b88853e4ef`): serverStatus metrics.query.planCache counters
- **Standalone mongosync hosting and sizing** (`mongodb-7925b47a64e7b3de`): Standalone mongosync hosting and sizing
- **Atlas IdP Group to Role Mapping** (`mongodb-c09bfbc9243e60ca`): Atlas IdP Group to Role Mapping
- **Time series bucket reopening (archived and query-based)** (`mongodb-d7584bdb38451a97`): Time series bucket reopening (archived and query-based)
- **Continuous Backup with PITR** (`mongodb-5c4a6a20de2ff96e`): Continuous Backup with PITR
- **mongosync and live-migration oplog capacity planning** (`mongodb-a795f66b3ce719c6`): mongosync and live-migration oplog capacity planning
- **RBAC and Connection Security** (`mongodb-07a3bad64983e0ba`): RBAC and Connection Security
- **Atlas Automated Embedding economics (Voyage tokens vs external embedding service)** (`mongodb-4bee35475c703fbe`): Atlas Automated Embedding economics (Voyage tokens vs external embedding service)
- **MongoDB Monitoring and Observability** (`mongodb-99cac3ce4e627e93`): MongoDB Monitoring and Observability
- **Oplog window sizing** (`mongodb-5ee3ae648967bb3e`): Oplog window sizing
- **Faceted Search** (`mongodb-24b13a62c00de6cc`): Faceted Search
- **numCandidates tuning for quantized HNSW indexes** (`mongodb-a0baeec2d41c9aaa`): numCandidates tuning for quantized HNSW indexes
- **Count consistency under concurrent writes** (`mongodb-07cfc0fb94bc955d`): Count consistency under concurrent writes
- **Cross-Region Snapshot Copy** (`mongodb-188b1cbfa5176d80`): Cross-Region Snapshot Copy
- **heartbeat-configuration** (`mongodb-3c49ebc4ae93667d`): heartbeat-configuration
- **Hidden and priority-0 members during maintenance** (`mongodb-10c4b1be8766477e`): Hidden and priority-0 members during maintenance
- **Loose versus tight bucket predicates** (`mongodb-3072d2a4e371f608`): Loose versus tight bucket predicates
- **Approximation pattern for write-heavy computed counters** (`mongodb-a3d3c857a04c0a0e`): Approximation pattern for write-heavy computed counters
- **Atlas Backup IaC** (`mongodb-e91100f4e8d722b1`): Atlas Backup IaC
- **Atlas Query Insights: Query Shape Insights and Namespace Insights** (`mongodb-e62e1e5f0a14a6c0`): Atlas Query Insights: Query Shape Insights and Namespace Insights
- **Covered distinct and $group on sharded collections** (`mongodb-21d5889a8e37c9a6`): Covered distinct and $group on sharded collections
- **moveCollection and collection isolation on dedicated shards** (`mongodb-1313ca23009179da`): moveCollection and collection isolation on dedicated shards
- **Relational-to-MongoDB migration cost (Relational Migrator)** (`mongodb-2a5ba92b53dbdf49`): Relational-to-MongoDB migration cost (Relational Migrator)
- **TLS and OCSP** (`mongodb-46d5cb408c85082d`): TLS and OCSP
- **UUIDv4 versus UUIDv7 key locality** (`mongodb-44df64c27395c94f`): UUIDv4 versus UUIDv7 key locality
- **WiredTiger cache warm-up** (`mongodb-5c111e1e4e85d688`): WiredTiger cache warm-up
- **Hybrid search ($rankFusion) vs two-system fusion TCO** (`mongodb-11efb59e53667c2b`): Hybrid search ($rankFusion) vs two-system fusion TCO
- **Rolling resync (initial sync) as a space-reclaim technique on Atlas** (`mongodb-5b5b4cfcf84799ff`): Rolling resync (initial sync) as a space-reclaim technique on Atlas
- **Atlas Vector Search Automated Embedding rate limits** (`mongodb-8516b0e828fada49`): Atlas Vector Search Automated Embedding rate limits
- **Autoscaling tier bounds as cost ceiling** (`mongodb-e4ac2f3c49c86a24`): Autoscaling tier bounds as cost ceiling
- **Entra ID group overage in Atlas** (`mongodb-df62d1d947cdbd4f`): Entra ID group overage in Atlas
- **explain multiKeyPaths interpretation** (`mongodb-7965fd720f389728`): explain multiKeyPaths interpretation
- **Explain verbosity modes** (`mongodb-47f67e2bbd528a69`): Explain verbosity modes
- **maxTimeMS (Server-side Operation Timeout)** (`mongodb-d0ac0cf8d779b245`): maxTimeMS (Server-side Operation Timeout)
- **Query Efficiency as a Cost Lever** (`mongodb-051fe7e313af364d`): Query Efficiency as a Cost Lever
- **Self-Managed MongoDB vs Atlas TCO** (`mongodb-c82707c3b924395a`): Self-Managed MongoDB vs Atlas TCO
- **Shard key selection for query isolation** (`mongodb-284269edea0fc175`): Shard key selection for query isolation
- **Journal (Write-Ahead Log)** (`mongodb-b17414c4ae381541`): Journal (Write-Ahead Log)
- **mongos version skew rules** (`mongodb-306dbec4648505c8`): mongos version skew rules
- **Atlas analytics nodes and read preference tags** (`mongodb-c9679101de543f34`): Atlas analytics nodes and read preference tags
- **Compass Schema Analysis** (`mongodb-d7f77d4633ce53b6`): Compass Schema Analysis
- **Read vs Write Distribution** (`mongodb-cee754a40c7723af`): Read vs Write Distribution
- **Workload isolation with tagged secondaries and Atlas analytics nodes** (`mongodb-48de7a278d0d4126`): Workload isolation with tagged secondaries and Atlas analytics nodes
- **Terraform Drift Detection** (`mongodb-0092b96e17be26f8`): Terraform Drift Detection
- **defaultMaxTimeMS cluster-level read timeout** (`mongodb-99d4d1b0a47c689a`): defaultMaxTimeMS cluster-level read timeout
- **Multi-Cloud Failure Modes** (`mongodb-c515a324f51ac515`): Multi-Cloud Failure Modes
- **Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates)** (`mongodb-6ce47e86e19dad6f`): Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates)
- **atlas-live-migration-comparison** (`mongodb-690831a0bca52eee`): atlas-live-migration-comparison
- **Backup Compliance Policy One-Way** (`mongodb-1f561ecf52bd9c4e`): Backup Compliance Policy One-Way
- **Dedicated Search Nodes two-node cost floor versus coupled mongot** (`mongodb-cb1abdaf537229f9`): Dedicated Search Nodes two-node cost floor versus coupled mongot
- **KMS Failsafe Behavior Atlas** (`mongodb-ca183c0808fa1d8e`): KMS Failsafe Behavior Atlas
- **KMS Unavailability Failsafe** (`mongodb-64bd4c4d7f75136f`): KMS Unavailability Failsafe
- **Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized** (`mongodb-983c9002cb539e0a`): Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized
- **Atlas Flex Unsupported Features** (`mongodb-98f15c71167afcb0`): Atlas Flex Unsupported Features
- **Replication Oplog Window alerts and Oplog GB/Hour monitoring** (`mongodb-bd2ec94cfc3e0c7d`): Replication Oplog Window alerts and Oplog GB/Hour monitoring
- **Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom)** (`mongodb-b22b7ad3bfec0d0e`): Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom)
- **Atlas Search nodes in sharded clusters** (`mongodb-5e2d71b8262fc147`): Atlas Search nodes in sharded clusters
- **Azure Container Apps Atlas** (`mongodb-8a6e1dab071c1259`): Azure Container Apps Atlas
- **Batch Reads and Aggregation Pushdown** (`mongodb-9a1f69eaf1ad5a59`): Batch Reads and Aggregation Pushdown
- **Schema Inference and Type Promotion** (`mongodb-148e5a4f25b73cb7`): Schema Inference and Type Promotion
- **Embedded verifier and post-migration data verification cost** (`mongodb-1f8a6036de438274`): Embedded verifier and post-migration data verification cost
- **loadlevel-tuning** (`mongodb-24d55b92d6589375`): loadlevel-tuning
- **Time series compact and disk space reclaim** (`mongodb-3fc0d5495e547f9d`): Time series compact and disk space reclaim
- **KMS Key Rotation Atlas** (`mongodb-18b5e0e60cf51e4e`): KMS Key Rotation Atlas
- **Structured Streaming with Change Streams** (`mongodb-05084432b2acf3be`): Structured Streaming with Change Streams
- **MongoDB AI Policy Scanning** (`mongodb-8ad3c6477bcc2e98`): MongoDB AI Policy Scanning
- **Chaos-style resilience testing under load (kill primary during peak writes, network partition, disk-full/IO-stall injection)** (`mongodb-337d64aea5e32092`): Chaos-style resilience testing under load (kill primary during peak writes, network partition, disk-full/IO-stall injection)
- **Bucket reopening and the {metaField, timeField} index requirement** (`mongodb-0a10b489706a380f`): Bucket reopening and the {metaField, timeField} index requirement
- **Self-Managed Security Config** (`mongodb-3e7d46b3c347a3ed`): Self-Managed Security Config
- **Search Node sizing and disk-to-RAM ratios for quantized vector indexes** (`mongodb-8c5c35085f3b6c32`): Search Node sizing and disk-to-RAM ratios for quantized vector indexes
- **Search Node sizing for quantized vector indexes (RAM, disk, vCPU)** (`mongodb-7af7e4d6845945d6`): Search Node sizing for quantized vector indexes (RAM, disk, vCPU)
- **Cold-cache latency regression** (`mongodb-82f3c1f83c5da41a`): Cold-cache latency regression
- **COUNT_SCAN and sharded count accuracy** (`mongodb-d4200ab2ca7b6cb5`): COUNT_SCAN and sharded count accuracy
- **$exists query bounds on indexes** (`mongodb-b191ddc7adf248de`): $exists query bounds on indexes
- **Atlas Search for substring matching** (`mongodb-513b2efb598c5a72`): Atlas Search for substring matching
- **Atlas Search regex and wildcard operator cost** (`mongodb-1344c17f3a0fc1e7`): Atlas Search regex and wildcard operator cost
- **Atlas Search searchAfter pagination** (`mongodb-17deaa7477a73b32`): Atlas Search searchAfter pagination
- **Attribute pattern and wildcardProjection design** (`mongodb-121162dab4839db0`): Attribute pattern and wildcardProjection design
- **BSON BinData vector ingestion** (`mongodb-d092abfd1580c4d1`): BSON BinData vector ingestion
- **Burstable M10/M20 tiers** (`mongodb-cf7064ed65e99327`): Burstable M10/M20 tiers
- **COUNT_SCAN covered counts** (`mongodb-324f2bd5c0f46902`): COUNT_SCAN covered counts
- **Data Federation over customer S3 with partitioning** (`mongodb-37220e28d8149504`): Data Federation over customer S3 with partitioning
- **Data type selection for storage** (`mongodb-b86e5c11a37ab562`): Data type selection for storage
- **Drop-index suggestions endpoint** (`mongodb-82b91ce83344c45d`): Drop-index suggestions endpoint
- **FinOps Framework Applied to Atlas** (`mongodb-253634055c866df1`): FinOps Framework Applied to Atlas
- **Flex cluster spend ceiling** (`mongodb-afe7acd5ae6d1009`): Flex cluster spend ceiling
- **Flex Limitations and migration to Dedicated** (`mongodb-2f13cb5bd7131950`): Flex Limitations and migration to Dedicated
- **hint in aggregate and update/delete** (`mongodb-48a33bb609a5afc0`): hint in aggregate and update/delete
- **Index filters deprecation and migration** (`mongodb-3f7e20d8ac6a1bf7`): Index filters deprecation and migration
- **Index prefix compression and index size** (`mongodb-d8bf50e1c813e199`): Index prefix compression and index size
- **Lambda MongoDB Driver Pattern** (`mongodb-65b4f7fb4a0bf23a`): Lambda MongoDB Driver Pattern
- **majority-ack write concern change** (`mongodb-f0cc6fe6b4bd84f4`): majority-ack write concern change
- **MongoDB MCP Server read-only and permission model** (`mongodb-e9b73adc49805dd7`): MongoDB MCP Server read-only and permission model
- **mtools Log Analysis Integration** (`mongodb-4f3b50f2f6bbfee0`): mtools Log Analysis Integration
- **natural hint and collection scans** (`mongodb-53359faa41220950`): $natural hint and collection scans; natural hint and collection scans
- **Online Archive partition-field selection** (`mongodb-c41333a4b1900fad`): Online Archive partition-field selection
- **Online Archive query performance optimization** (`mongodb-c05c8184c25a5a42`): Online Archive query performance optimization
- **Partial and TTL indexes on time series** (`mongodb-11f9ca1561653b53`): Partial and TTL indexes on time series
- **Partial TTL indexes** (`mongodb-44a6471ac20e9c80`): Partial TTL indexes
- **Partial unique indexes for soft delete** (`mongodb-468e1ac3c8b67765`): Partial unique indexes for soft delete
- **planCacheSize and $planCacheStats** (`mongodb-0af3438c94f00e21`): planCacheSize and $planCacheStats
- **Total count strategies for paginated UIs** (`mongodb-9eca9762d375390f`): Total count strategies for paginated UIs
- **Wildcard index query-planner behavior and explain rejectedPlans** (`mongodb-24f1eabfaa3a9bb7`): Wildcard index query-planner behavior and explain rejectedPlans
- **WiredTiger Block and Prefix Compression as Storage Cost Lever** (`mongodb-cfa0dce648dab223`): WiredTiger Block and Prefix Compression as Storage Cost Lever
- **Encryption In Transit** (`mongodb-da430af06039337f`): Encryption In Transit; Encryption in Transit
- **Autocomplete** (`mongodb-ae387fbb19886f55`): Autocomplete
- **dropIndexes locking and rollback by rebuild** (`mongodb-7e8b96bdf697cd86`): dropIndexes locking and rollback by rebuild
- **Maintained or cached count counters** (`mongodb-3cfe80671cfeec47`): Maintained or cached count counters
- **Atlas RBAC IaC** (`mongodb-05627fe0b4122ef1`): Atlas RBAC IaC
- **replSetResizeOplog and oplog compaction on self-managed replica sets** (`mongodb-01e5968b3c6a6095`): replSetResizeOplog and oplog compaction on self-managed replica sets
- **Bucket archiving and query-based reopening** (`mongodb-6f7952f8bc36e6ac`): Bucket archiving and query-based reopening
- **Cache-pressure early bucket closure and bucket catalog memory** (`mongodb-64ee8f1a399655a0`): Cache-pressure early bucket closure and bucket catalog memory
- **Side-writes table and hybrid index builds** (`mongodb-ab63bfa824bdfca1`): Side-writes table and hybrid index builds
- **Validation and performance review of generated queries** (`mongodb-4688c1035515d88b`): Validation and performance review of generated queries
- **Atlas invoice tag coverage and cost export reconciliation** (`mongodb-df9f123599ebe33f`): Atlas invoice tag coverage and cost export reconciliation
- **Exporting $indexStats metrics with mongodb_exporter and PMM** (`mongodb-0b46e1f993a1159c`): Exporting $indexStats metrics with mongodb_exporter and PMM
- **Migration Host Provisioning** (`mongodb-25217c48c1f65399`): Migration Host Provisioning
- **Persisting index usage metrics with PMM and mongodb_exporter** (`mongodb-b17bfdcd6d33ab29`): Persisting index usage metrics with PMM and mongodb_exporter
- **Backup Daemon HA and Failure Domains** (`mongodb-ce71eb833cd65345`): Backup Daemon HA and Failure Domains
- **Config server placement and cost (dedicated vs embedded)** (`mongodb-eb3caa0d55a39552`): Config server placement and cost (dedicated vs embedded)
- **Entra ID Workload Identity Federation** (`mongodb-359ff82ad8819d45`): Entra ID Workload Identity Federation
- **GCP Workload Identity Federation OIDC** (`mongodb-27d185061715ab35`): GCP Workload Identity Federation OIDC
- **Database Triggers** (`mongodb-120857b8b1ed4870`): Database Triggers
- **MongoDB commit quorum and two-phase index builds** (`mongodb-d62e0732163fcf5b`): MongoDB commit quorum and two-phase index builds
- **Time-field bucket predicates** (`mongodb-ce9f22f88277e81e`): Time-field bucket predicates
- **Two-phase (simultaneous) index builds** (`mongodb-fd8a391e36c2f1cb`): Two-phase (simultaneous) index builds
- **Atlas SAML Entra ID** (`mongodb-a254a0cfd334d1db`): Atlas SAML Entra ID
- **Atlas X.509 Certificate Auth** (`mongodb-cd31306cfd48d9eb`): Atlas X.509 Certificate Auth
- **Compass Data Import Export** (`mongodb-d4cfc7eb8615e634`): Compass Data Import Export
- **Connection Registry** (`mongodb-8ae7aa0ae6915f08`): Connection Registry
- **Migration from Regular Collections** (`mongodb-b703e035c81d2e52`): Migration from Regular Collections
- **Rolling index builds as a resource-isolation alternative** (`mongodb-53ebb7c31bd889d6`): Rolling index builds as a resource-isolation alternative
- **GCP Forwarding Rule Quota** (`mongodb-3ebbad20332419a6`): GCP Forwarding Rule Quota
- **Ops Manager Backup** (`mongodb-96a0c2e3252763e9`): Ops Manager Backup
- **SHARDING_FILTER stage internals and orphaned-document filtering** (`mongodb-72047567328b3784`): SHARDING_FILTER stage internals and orphaned-document filtering
- **MSK-Connect-deployment** (`mongodb-b82412ebc14d24c3`): MSK-Connect-deployment
- **One-way tier gates: sharding, Global Writes, edition changes** (`mongodb-154d85446aca8d3c`): One-way tier gates: sharding, Global Writes, edition changes
- **Upgrade rollback playbook** (`mongodb-02dfabfbe463e470`): Upgrade rollback playbook
- **Atlas Admin API v2 REST** (`mongodb-82a91971777e4c66`): Atlas Admin API v2 REST
- **Atlas on Azure** (`mongodb-9ff78432439aeee6`): Atlas on Azure
- **Atlas on GCP** (`mongodb-5b4e70d0ae098395`): Atlas on GCP
- **Atlas Search node scaling per shard** (`mongodb-764bd81a5a773e26`): Atlas Search node scaling per shard
- **Azure Event Hub Atlas Stream Processing** (`mongodb-87cac5d61f9a5882`): Azure Event Hub Atlas Stream Processing
- **BigQuery Atlas Dataflow CDC** (`mongodb-1f352047b239c4d9`): BigQuery Atlas Dataflow CDC
- **GeoJSON Object Types** (`mongodb-90063e073a6de01a`): GeoJSON Object Types
- **Index rebuild cost after a wrong drop** (`mongodb-fefaa0b8e8e04414`): Index rebuild cost after a wrong drop
- **Azure App Service Atlas** (`mongodb-6258ee86309e462d`): Azure App Service Atlas
- **Cloud Functions Gen2 Atlas** (`mongodb-8de9f056d5cd3921`): Cloud Functions Gen2 Atlas
- **Cloud NAT for Atlas** (`mongodb-a6cee5fba28187b4`): Cloud NAT for Atlas
- **Terraform Import generate-config-out** (`mongodb-a957ee68d2b08485`): Terraform Import generate-config-out
- **Delete and re-insert safety on time series** (`mongodb-923ceb9b3e18edd6`): Delete and re-insert safety on time series
- **DiskSpaceMonitor and low-disk index build abort (7.1+)** (`mongodb-f2ba7b6cbaf4b07d`): DiskSpaceMonitor and low-disk index build abort (7.1+)
- **Clustered collection insert locality** (`mongodb-882d953d06ecf092`): Clustered collection insert locality
- **Rooted $or subplanning and SORT_MERGE** (`mongodb-ec08ff8b974e0f70`): Rooted $or subplanning and SORT_MERGE
- **debezium-handlers** (`mongodb-ab4d86428ce2ac80`): debezium-handlers
- **ExpressRoute Atlas Connectivity** (`mongodb-a2350afb4d0aa454`): ExpressRoute Atlas Connectivity
- **OpenTelemetry MongoDB Receiver** (`mongodb-cd198b392e76564c`): OpenTelemetry MongoDB Receiver
- **schema-registry-integration** (`mongodb-cbfbe62f93a1ba25`): schema-registry-integration
- **serverStatus indexBuilds metrics and index build observability** (`mongodb-f133778e0dd645e1`): serverStatus indexBuilds metrics and index build observability
- **Canary and Shadow-Traffic Comparison** (`mongodb-c385faefbd55b73e`): Canary and Shadow-Traffic Comparison
- **Hybrid search ($rankFusion) vs separate search plus vector stack** (`mongodb-cb8fa38113d4a3bf`): Hybrid search ($rankFusion) vs separate search plus vector stack
- **Multi-Vector Patterns** (`mongodb-bbd9073b823d2579`): Multi-Vector Patterns
- **Version upgrade paths (4.4 → 5.0 → 6.0 → 7.0 → 8.0)** (`mongodb-f1a2ccf80d338525`): Version upgrade paths (4.4 → 5.0 → 6.0 → 7.0 → 8.0)
- **Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden)** (`mongodb-5de70bb852c542b0`): Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden)
- **Destination right-sizing after cutover** (`mongodb-f61d9a822b83c2cc`): Destination right-sizing after cutover
- **Cache-aside vs write-through and cache stampede prevention** (`mongodb-455e51a21604bfdc`): Cache-aside vs write-through and cache stampede prevention
- **Query settings and index filters as plan pinning** (`mongodb-de4657c9ed97854c`): Query settings and index filters as plan pinning
- **Frozen buckets and compression failures** (`mongodb-4730c00dc9ee7135`): Frozen buckets and compression failures
- **Initial sync index build memory limits** (`mongodb-241793c17bb3b2cc`): Initial sync index build memory limits
- **Java driver 4.10 and 5.x retry semantics** (`mongodb-50329fb377d6646f`): Java driver 4.10 and 5.x retry semantics
- **per-accumulator explain memory statistics** (`mongodb-66052fda66c0dd23`): per-accumulator explain memory statistics
- **PSC Legacy Migration** (`mongodb-1696f7048bd5af3c`): PSC Legacy Migration
- **Mixed-schema measurement predicate safety** (`mongodb-486aa566eb9f3fec`): Mixed-schema measurement predicate safety
- **Oplog windows and Search initial-sync recovery** (`mongodb-85b45d8030420f41`): Oplog windows and Search initial-sync recovery
- **Sharded time series rebuild and resharding** (`mongodb-12f204d0f73d5c70`): Sharded time series rebuild and resharding
- **Cost-based ranker and the plan cache (8.3+)** (`mongodb-6e54bf0743fd3ab5`): Cost-based ranker and the plan cache (8.3+)
- **MongoDB Time-Series Query and Index Optimization** (`mongodb-bc3e800a23252bc4`): MongoDB 8.0 Block Processing; MongoDB 8.0 Block Processing (time series); MongoDB Time-Series Query and Index Optimization; Secondary Indexes on Time Series; Time-Series Bucket Unpacking and $match Pushdown; Time-Series Sort and Range Query Patterns; Working Set Sizing for Time Series; metaField Cardinality Anti-Patterns
- **serverStatus metrics.query.cbr** (`mongodb-73d2ba4357b168ee`): serverStatus metrics.query.cbr
- **MVCC and Snapshot Isolation** (`mongodb-0913cdf4c0074217`): MVCC and Snapshot Isolation
- **Atlas SCRAM-SHA-256** (`mongodb-7dc0c42e7111b475`): Atlas SCRAM-SHA-256
- **Radius Unit Conversions** (`mongodb-91e34e44305093f9`): Radius Unit Conversions
- **Granularity Anti-Patterns** (`mongodb-17fb32427ed52d4c`): Granularity Anti-Patterns
- **Idle bucket expiry and archived bucket reopening** (`mongodb-f233d10934a5e0d7`): Idle bucket expiry and archived bucket reopening
- **MongoDB Search eventual consistency and replication-lag metrics** (`mongodb-bf53032042a472a5`): MongoDB Search eventual consistency and replication-lag metrics
- **Atlas managed slow operation threshold and Performance Advisor index suggestions** (`mongodb-dadb3de5ec7b8a6b`): Atlas managed slow operation threshold and Performance Advisor index suggestions
- **External sorter spill files in dbpath/_tmp** (`mongodb-63ce4d2c03fecae1`): External sorter spill files in dbpath/_tmp
- **Pre-quantized BinData (int8 and int1) ingestion** (`mongodb-dbcbc1d7561ca48d`): Pre-quantized BinData (int8 and int1) ingestion
- **Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB** (`mongodb-807c3ccd211eeab7`): Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB
- **Stream Processor Monitoring** (`mongodb-a9322db789d9f05d`): Stream Processor Monitoring
- **Common Migration Failures** (`mongodb-0b82f46d21c5f7c8`): Common Migration Failures
- **Geospatial Anti-Patterns** (`mongodb-5221057a0f348db9`): Geospatial Anti-Patterns
- **custom $accumulator spill and merge semantics** (`mongodb-009e3c9554b34360`): custom $accumulator spill and merge semantics
- **GCP Global Access PSC** (`mongodb-97a12b3664d103f6`): GCP Global Access PSC
- **Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields)** (`mongodb-d49655fd3c7cff9e`): Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields)
- **Auto Embedding Voyage AI** (`mongodb-dab334804c0908f6`): Auto Embedding Voyage AI
- **Index usage measurement with $indexStats** (`mongodb-6f5f321045e0edf3`): Index usage measurement with $indexStats
- **Redundant and prefix index detection** (`mongodb-fcb9495dd1174a73`): Redundant and prefix index detection
- **Authentication Methods** (`mongodb-5ef0e30fd6151d0f`): Authentication Methods
- **MongoDB rolling index builds** (`mongodb-a16b483837d9ea51`): MongoDB rolling index builds
- **Atlas Security Posture Checklist** (`mongodb-18da6b98379ced72`): Atlas Security Posture Checklist
- **Atlas Database Auditing** (`mongodb-9f6f79e3a857effc`): Atlas Database Auditing
- **Compass Connection Management** (`mongodb-50fa08c52007958d`): Compass Connection Management
- **Scheduled Triggers** (`mongodb-89c810b9ae6294e0`): Scheduled Triggers
- **Stream Processing Instance (SPI)** (`mongodb-161ab65ac46d7e1b`): Stream Processing Instance (SPI)
- **Workload Characterization** (`mongodb-b8d22590a0222afa`): Workload Characterization
- **Config shard versus dedicated config server** (`mongodb-8b57223f4133bbad`): Config shard versus dedicated config server
- **Atlas Terraform mongodbatlas_resource_policy** (`mongodb-22776de21c906259`): Atlas Terraform mongodbatlas_resource_policy
- **Entra ID OIDC Workforce Federation** (`mongodb-bdc5d8939025e3f1`): Entra ID OIDC Workforce Federation
- **Atlas minimum oplog window (oplogMinRetentionHours) tuning** (`mongodb-c85605b2cc4dc9d2`): Atlas minimum oplog window (oplogMinRetentionHours) tuning
- **Atlas disk decrease by volume replacement on AWS, Azure and GCP** (`mongodb-13c6b1eeb704e59e`): Atlas disk decrease by volume replacement on AWS, Azure and GCP
- **Reducing Atlas storage capacity (new-volume sync, per-node downtime)** (`mongodb-56adaf63af16ccb6`): Reducing Atlas storage capacity (new-volume sync, per-node downtime)
- **Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes)** (`mongodb-f8df8715fc512ffc`): Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes)
- **Execution-guided text-to-MQL refinement** (`mongodb-c830a49b1716607f`): Execution-guided text-to-MQL refinement
- **$_internalUnpackBucket explain reading** (`mongodb-4a3ebeb68e286e63`): $_internalUnpackBucket explain reading
- **$mergeCursors stage in explain** (`mongodb-053566211bd30b3c`): $mergeCursors stage in explain
- **$top/$bottom accumulators rewrite** (`mongodb-c6dcc33e08e69831`): $top/$bottom accumulators rewrite
- **App Services Migration Paths** (`mongodb-8007a715efff791c`): App Services Migration Paths
- **Atlas WIF built-in vs callback authentication** (`mongodb-8490de66aee3efac`): Atlas WIF built-in vs callback authentication
- **Bucket-level predicate rewriting for measurement operators** (`mongodb-5e94ed89bedeb3c4`): Bucket-level predicate rewriting for measurement operators
- **Cloud Marketplace Billing for Atlas (AWS GCP Azure)** (`mongodb-124efd3b37d8eef7`): Cloud Marketplace Billing for Atlas (AWS GCP Azure)
- **Co-located vs dedicated search migration thresholds** (`mongodb-6cdc0d83364a95d6`): Co-located vs dedicated search migration thresholds
- **Deadline Propagation and Context Cancellation in MongoDB Drivers** (`mongodb-8d0b14734f9fa55b`): Deadline Propagation and Context Cancellation in MongoDB Drivers
- **Elastic Billing transition** (`mongodb-707a1dbd4ae9e0b2`): Elastic Billing transition
- **MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker** (`mongodb-54d761cdeec7c86c`): $group $first Loose Index Scan (DISTINCT_SCAN for sort-group-first); Aggregation Explain and Spill Statistics ($lookup and $group and memory limits); Aggregation explain and $lookup/spill stats; Aggregation pipeline explain and $lookup visibility; Aggregation split pipelines and merge shard selection; Cost-Based Ranker and Multi-Planning Changes (8.3 and 9.0); Cost-based ranker (8.3); Cost-based ranker and multi-planning in 8.3; Last-point queries and DISTINCT_SCAN; Last-point query DISTINCT_SCAN; MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker; Per-operation memory limit tuning; Query knobs (9.0); Sharded Explain and Split Pipelines (SHARD_MERGE and per-shard stats and merge shard selection); Sharded explain (SHARD_MERGE, per-shard stats); Slow in-progress query logging (8.3); Sort-group-$first loose index scan; queryStats output schema in 9.0
- **MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead** (`mongodb-d1008166fde8820b`): Hidden Indexes; In-flight index builds; Index Build Conflicts and Commit Quorum and In-Flight Builds; Index Build Strategies; Index Storage and RAM Fit and Write-Path Overhead; Index build commit quorum (8.0 nuance); Index build conflicts; MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead; Wildcard Indexes; Wildcard and Compound Wildcard Indexes
- **Multi-Region and Cross-Cloud Data Transfer Costs** (`mongodb-82d870a7cc863c51`): Multi-Region and Cross-Cloud Data Transfer Costs
- **Per-query fusion weighting** (`mongodb-0dff995da4e110ff`): Per-query fusion weighting
- **Random-key (hashed/UUID) index insert behavior** (`mongodb-8cba1455528c7e63`): Random-key (hashed/UUID) index insert behavior
- **Read preference and write routing for cost** (`mongodb-520ab78cff61ae32`): Read preference and write routing for cost
- **SERVER JIRA Ticket Regression Mapping** (`mongodb-c328495ef486c250`): SERVER JIRA Ticket Regression Mapping
- **Slot-based execution engine eligibility** (`mongodb-02193b259d468ce2`): Slot-based execution engine eligibility
- **Storage Growth and IOPS Forecasting for Cost** (`mongodb-b8a70c55993a60df`): Storage Growth and IOPS Forecasting for Cost
- **linearizable read concern** (`mongodb-239cb97de60dd17a`): linearizable read concern
- **Measuring ANN recall against ENN baselines** (`mongodb-58d3075bb6bcb3ac`): Measuring ANN recall against ENN baselines
- **GCP VPC Peering** (`mongodb-4b557b79d2cede40`): GCP VPC Peering
- **moved Block Migration Pattern** (`mongodb-2bed4a6f4c62b84f`): moved Block Migration Pattern
- **CloudFormation Third Party Activation** (`mongodb-10df6008dcca8386`): CloudFormation Third Party Activation
- **orphanCleanupDelaySecs and range deletion timing** (`mongodb-8886daa104930363`): orphanCleanupDelaySecs and range deletion timing
- **Burstable M10/M20 CPU credits and the M30 production threshold** (`mongodb-8c2c7ba4cb87f068`): Burstable M10/M20 CPU credits and the M30 production threshold
- **Burstable M10/M20 CPU-credit throttling and when to move to M30** (`mongodb-6c7186204e8017d6`): Burstable M10/M20 CPU-credit throttling and when to move to M30
- **Upgrade Procedures** (`mongodb-23cf2408a3e0aa8b`): Upgrade Procedures
- **Offline-First Patterns** (`mongodb-a6bd25857df38bbe`): Offline-First Patterns
- **mongomirror Deprecation** (`mongodb-15420f332f7489f8`): mongomirror Deprecation
- **Schema grounding and value linking for MQL generation** (`mongodb-e367e15ab372e407`): Schema grounding and value linking for MQL generation
- **Archive Restore** (`mongodb-37a65c8e0c5fac6a`): Archive Restore
- **Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections** (`mongodb-2f0d3d755535f053`): Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections
- **MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later)** (`mongodb-5e77d4557f37e1b1`): MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later)
- **Primary-driven index builds and write-rate throttles** (`mongodb-971ffff4d9ee3092`): Primary-driven index builds and write-rate throttles
- **rawData bucket-level CRUD (8.2 and later)** (`mongodb-b14dc0828d8b50be`): rawData bucket-level CRUD (8.2 and later)
- **Self-managed mongot on Community Edition: hardware and labour TCO** (`mongodb-499ad5dfcc676208`): Self-managed mongot on Community Edition: hardware and labour TCO
- **$querySettings stage and query settings inspection** (`mongodb-b07a637b21b88412`): $querySettings stage and query settings inspection
- **Atlas Flex Technical Limits** (`mongodb-bd2bc58eedbc8b11`): Atlas Flex Technical Limits
- **Search Nodes Dedicated Infrastructure** (`mongodb-ad9c75df9da42029`): Search Nodes Dedicated Infrastructure
- **YCSB Workload Reference** (`mongodb-0729b15998918b6e`): YCSB Workload Reference
- **Pre-upgrade safety checks** (`mongodb-bb9fdea35cb170e0`): Pre-upgrade safety checks
- **Permissions Model** (`mongodb-d459dd01ebf762cd`): Permissions Model
- **Atlas Functions JavaScript Runtime** (`mongodb-880c33b3f2f3a27c`): Atlas Functions JavaScript Runtime
- **Connector Error Patterns** (`mongodb-4b04a3df42e6484f`): Connector Error Patterns
- **Migration Validation Patterns** (`mongodb-0ef16ff9a079ceac`): Migration Validation Patterns
- **Terraform state reconciliation after a Flex-to-Dedicated conversion** (`mongodb-99c3b85f8ea2f600`): Terraform state reconciliation after a Flex-to-Dedicated conversion
- **Atlas IaC Migration Paths** (`mongodb-1fafd1cfcd6536bf`): Atlas IaC Migration Paths
- **Atlas write-blocking thresholds and Intelligent Workload Management** (`mongodb-a5b02b4713b48099`): Atlas write-blocking thresholds and Intelligent Workload Management
- **SBE plan cache keys and parameterized explode-for-sort plans** (`mongodb-86d9655eef37c43c`): SBE plan cache keys and parameterized explode-for-sort plans
- **S3-Compatible Snapshot Storage with Object Lock** (`mongodb-dcd739697836280f`): S3-Compatible Snapshot Storage with Object Lock
- **Per-shape maxTimeMS and queryKnobs (9.0)** (`mongodb-18c93953c25aee74`): Per-shape maxTimeMS and queryKnobs (9.0)
- **Per-shape queryKnobs and maxTimeMS (9.0)** (`mongodb-b065371ac638e191`): Per-shape queryKnobs and maxTimeMS (9.0)
- **AND_SORTED vs AND_HASH plan stages** (`mongodb-dbfd108f75cb2cb8`): AND_SORTED vs AND_HASH plan stages
- **Atlas Search and Dedicated Search Nodes Cost** (`mongodb-7b42d1896df3729b`): Atlas Search and Dedicated Search Nodes Cost; Per-region Search Node counts; Search Node tier sizing from index size and QPS
- **Backup snapshot storage growth cost** (`mongodb-593235aabedb9e65`): Backup snapshot storage growth cost
- **Bounded sort ($_internalBoundedSort)** (`mongodb-10e73b151359c7cb`): Bounded sort ($_internalBoundedSort)
- **Collation and index sort compatibility** (`mongodb-ce7375acf0a0117d`): Collation and index sort compatibility
- **DNS and SRV Records** (`mongodb-29e4ee2feddfb4bb`): DNS and SRV Records
- **Granularity and custom bucketing parameters** (`mongodb-2836fe4adf2fd74c`): Granularity and custom bucketing parameters
- **Hashed vs ranged shard key query trade-offs** (`mongodb-2f87ebbdda8bd996`): Hashed vs ranged shard key query trade-offs
- **Maintenance Impact Minimization** (`mongodb-778c1904e29ff4dc`): Maintenance Impact Minimization
- **MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor** (`mongodb-caddfb9afaca01fa`): AI and LLM-Assisted MongoDB Query and Index Optimization; Atlas Performance Advisor; Atlas Performance Advisor (index and schema suggestions); Atlas Query Insights and Query Profiler; Atlas Search vs $text vs $regex (search offload decision); Compass Explain Plan Visualizer; MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor; Post-8.0 Query Engine Changes (8.1 and 8.2 rapid releases and 9.0)
- **Multikey index coverage and multiKeyPaths** (`mongodb-cf9abc2172e20e2b`): Multikey index coverage and multiKeyPaths
- **multikey index sort behaviour** (`mongodb-a1a26836af6af277`): multikey index sort behaviour
- **Read concern and causal consistency with secondary reads** (`mongodb-571599b65ef802bf`): Read concern and causal consistency with secondary reads
- **read your own writes** (`mongodb-bc52bba3491fefc4`): read your own writes
- **Replica Set Transactions** (`mongodb-3bb6f8165c73d25b`): Replica Set Transactions
- **Sparse versus partial index equivalence** (`mongodb-681c3ccf51360db2`): Sparse versus partial index equivalence
- **Atlas Database Users** (`mongodb-88a4e486fbd16af0`): Atlas Database Users
- **local read concern** (`mongodb-558c5c7cac56fc38`): local read concern
- **Atlas Project Roles (15 Purpose-Built)** (`mongodb-6fc194875d31dbb6`): Atlas Project Roles (15 Purpose-Built)
- **Atlas billing alert notification delivery** (`mongodb-daf5f04ff38e5b74`): Atlas billing alert notification delivery
- **Safe execution against non-production Atlas (cluster isolation, guardrails, cost/cleanup discipline)** (`mongodb-e76e53a2fe2e6ce5`): Safe execution against non-production Atlas (cluster isolation, guardrails, cost/cleanup discipline)
- **Atlas Encryption IaC** (`mongodb-4642c14fd76d6329`): Atlas Encryption IaC
- **Version Manifest Mirroring** (`mongodb-1615862cc1c1e3cd`): Version Manifest Mirroring
- **Sharded Cluster Migrations** (`mongodb-e3516fd103c70f10`): Sharded Cluster Migrations
- **Multi-Cloud DR Pattern** (`mongodb-761dcf1fc1c2a579`): Multi-Cloud DR Pattern
- **Multi-Tenancy Anti-Patterns** (`mongodb-da71d7b6d5f56bc1`): Multi-Tenancy Anti-Patterns
- **Terraform Atlas Provider v2.x** (`mongodb-d3a46c5c64822520`): Terraform Atlas Provider v2.x
- **Time-series bucket closure under cache pressure** (`mongodb-2913bf52cf381766`): Time-series bucket closure under cache pressure
- **Search Node network transfer and multi-region cost** (`mongodb-ba06efd5a3a65ecb`): Search Node network transfer and multi-region cost
- **Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration** (`mongodb-83cd6ae06eff3d17`): Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration
- **explodeForSort integer overflow (CVE-2026-82076)** (`mongodb-6f3be80e7ee2148e`): explodeForSort integer overflow (CVE-2026-82076)
- **MongoDB Atlas** (`mongodb-d1d04a296fca07e0`): MongoDB Atlas
- **Atlas RBAC** (`mongodb-123b8e7d0b87e307`): Atlas RBAC
- **Atlas Audit Logging** (`mongodb-6aefc03f4a3d79c3`): Atlas Audit Logging
- **NSG Rules for Atlas** (`mongodb-7f4c6432a09c390f`): NSG Rules for Atlas
- **Shard key index design** (`mongodb-6495b656928cd28c`): Shard key index design
- **BYOK Key Management** (`mongodb-96f9e53a99b60ec7`): BYOK Key Management
- **HIPAA BAA and ePHI Configuration** (`mongodb-efb2c6f9acdfc5d1`): HIPAA BAA and ePHI Configuration
- **Multiplanner scoring and tie-breakers** (`mongodb-29d0dd392fb6801c`): Multiplanner scoring and tie-breakers
- **Ops Manager Admin API** (`mongodb-1f4a467d56b179de`): Ops Manager Admin API
- **mongos as MongoDB's native router & why MongoDB rarely uses third-party proxies** (`mongodb-39f8b275580b962b`): mongos as MongoDB's native router & why MongoDB rarely uses third-party proxies
- **Rolling index builds on Kubernetes with the Percona Operator** (`mongodb-49e91c2695d1a6f8`): Rolling index builds on Kubernetes with the Percona Operator
- **SBE plan cache pinned entries and the classic runtime planner for SBE** (`mongodb-e67c70b79575bbfb`): SBE plan cache pinned entries and the classic runtime planner for SBE
- **AKO Deletion Protection v2.0** (`mongodb-5b07b250b4b99e49`): AKO Deletion Protection v2.0
- **Atlas Support Plan Pricing** (`mongodb-bb63a8fcbb48990d`): Atlas Support Plan Pricing
- **Find projection vs $project aggregation coverage** (`mongodb-25e982368df65bca`): Find projection vs $project aggregation coverage
- **Plan cache invalidation on index DDL (hide, drop, create)** (`mongodb-190b283c18d76a07`): Plan cache invalidation on index DDL (hide, drop, create)
- **Compass Real-Time Performance Monitoring** (`mongodb-c4acb31ca42891f0`): Compass Real-Time Performance Monitoring
- **Datadog Integration** (`mongodb-22a6fd2a923b40d4`): Datadog Integration
- **External sorter spill files and the _tmp directory** (`mongodb-3026c7d51b5d2f7d`): External sorter spill files and the _tmp directory
- **Atlas tag enforcement through Terraform and APIs** (`mongodb-87e87c1dd2080346`): Atlas tag enforcement through Terraform and APIs
- **Config shard (embedded config server) cost trade-off** (`mongodb-65c27c0dfba72a11`): Config shard (embedded config server) cost trade-off
- **Atlas Minimum Oplog Window (oplogMinRetentionHours)** (`mongodb-5d31399755f14ab9`): Atlas Minimum Oplog Window (oplogMinRetentionHours)
- **internalQueryMaxScansToExplode and maxScansToExplodeReached** (`mongodb-c7bd06d38432e9c2`): internalQueryMaxScansToExplode and maxScansToExplodeReached
- **Atlas IP Access List Ownership Conflict** (`mongodb-79a9e2577961a386`): Atlas IP Access List Ownership Conflict
- **Flex backup and recovery planning** (`mongodb-993aec1833eb6e6c`): Flex backup and recovery planning
- **Conflict Resolution** (`mongodb-284c622fae433459`): Conflict Resolution
- **Atlas Query Profiler and Operation Throttling metrics** (`mongodb-00788b1b3bb92bad`): Atlas Query Profiler and Operation Throttling metrics
- **Gen2 clusters and Extended Standard IOPS economics** (`mongodb-4437555c82bb9745`): Gen2 clusters and Extended Standard IOPS economics
- **Hopping Windows** (`mongodb-2a2b1038e8fd6f58`): Hopping Windows
- **Rebuilding a time series collection with $out or mongorestore** (`mongodb-d50feb629e688162`): Rebuilding a time series collection with $out or mongorestore
- **Change Data Capture Patterns** (`mongodb-391fb4918d2428f0`): Change Data Capture Patterns
- **Atlas CLI Scripting** (`mongodb-44f8a125a11717cb`): Atlas CLI Scripting
- **Timestamp APIs (oldest/stable/pinned)** (`mongodb-cb875ff075996705`): Timestamp APIs (oldest/stable/pinned)
- **Atlas security add-on uplifts (auditing, LDAP, customer-managed keys, private endpoints)** (`mongodb-22325bda55f48ce0`): Atlas security add-on uplifts (auditing, LDAP, customer-managed keys, private endpoints)
- **Automated rolling builds in Atlas, Cloud Manager and Ops Manager** (`mongodb-601bc1adb5c8a1da`): Automated rolling builds in Atlas, Cloud Manager and Ops Manager
- **Flex Tooling Migration Terraform K8s CLI** (`mongodb-ea1257fa6e74bf2d`): Flex Tooling Migration Terraform K8s CLI
- **Atlas Stream Processing Pub/Sub** (`mongodb-4d5aa9ef09517f5d`): Atlas Stream Processing Pub/Sub
- **FTDC Storage Overhead & Retention Budgeting** (`mongodb-e34ce7cf92471e4c`): FTDC Storage Overhead & Retention Budgeting
- **Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator)** (`mongodb-9dad9f1e3b275b7d`): Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator)
- **Terraform Tag Enforcement and Policy-as-Code for Atlas Cost** (`mongodb-be7009a7a197f41f`): Terraform Tag Enforcement and Policy-as-Code for Atlas Cost
- **Tumbling Windows** (`mongodb-20594dd3f6296fd3`): Tumbling Windows
- **Collation-aware index key size** (`mongodb-f68a7b59a5714970`): Collation-aware index key size
- **Ops Manager Profiler** (`mongodb-d0254b9e675051e0`): Ops Manager Profiler
- **Sharding Triggers** (`mongodb-1a080c618ae77a7d`): Sharding Triggers
- **Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads)** (`mongodb-5d657d5afb5dd01f`): Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads)
- **VPC Atlas Security** (`mongodb-66629057aa248ea5`): VPC Atlas Security
- **Point of No Return** (`mongodb-c1f2f41427eddb7d`): Point of No Return
- **Data Residency and EU Sovereignty** (`mongodb-f7af90458c76714d`): Data Residency and EU Sovereignty
- **Atlas Organization Roles** (`mongodb-3ac4d5ea26e37f8d`): Atlas Organization Roles
- **path-level multikey tracking** (`mongodb-ac1652e7c2bfd255`): path-level multikey tracking
- **Live Migration to Atlas** (`mongodb-adff52a3fc11c54a`): Live Migration to Atlas
- **Atlas IaC Tool Decision Matrix** (`mongodb-e7f7420f93466b2a`): Atlas IaC Tool Decision Matrix
- **Backup Daemon** (`mongodb-1ea4b83a7d91eb83`): Backup Daemon
- **Straight-to-8 jump pattern** (`mongodb-f415269afd7437b5`): Straight-to-8 jump pattern
- **Looker Atlas BI Connector** (`mongodb-4806f379f5597763`): Looker Atlas BI Connector
- **PagerDuty/Datadog/Splunk Integration** (`mongodb-46c64989ec6f256d`): PagerDuty/Datadog/Splunk Integration
- **Percona PMM mongolog versus profiler query source** (`mongodb-788180d569d7d884`): Percona PMM mongolog versus profiler query source
- **EBS volume modification limits and Atlas disk resize mechanics** (`mongodb-bf2466898d41baab`): EBS volume modification limits and Atlas disk resize mechanics
- **Spark Connector vs Alternatives** (`mongodb-f33e340dc03df026`): Spark Connector vs Alternatives
- **Atlas Vector Search HNSW IVF** (`mongodb-5de331fc81ed2137`): Atlas Vector Search HNSW IVF
- **Atlas Credits Prepaid Subscriptions and Overage** (`mongodb-c221d1201b3f8d14`): Atlas Credits Prepaid Subscriptions and Overage
- **BM25 IDF corpus statistics** (`mongodb-fca2e7d671ed6a73`): BM25 IDF corpus statistics
- **BM25 term frequency saturation and field length normalization** (`mongodb-54426240611443ef`): BM25 term frequency saturation and field length normalization
- **ceSource cardinality estimation (sampling vs heuristics)** (`mongodb-9340d996ff39cf15`): ceSource cardinality estimation (sampling vs heuristics)
- **Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers)** (`mongodb-3fba0026158c3051`): Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers); Three-node minimum for non-production
- **Deferring Maintenance** (`mongodb-c6696b3065d5e83c`): Deferring Maintenance
- **Fusion score normalization strategies** (`mongodb-3d51006f8de308da`): Fusion score normalization strategies
- **M30 specs & connection limits** (`mongodb-04aafd3b9eb27198`): M30 specs & connection limits
- **Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB)** (`mongodb-e7fc6eda266cf57d`): Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB)
- **SBE vs classic plan cache keys** (`mongodb-cc7def978695356f`): SBE vs classic plan cache keys
- **Security Groups** (`mongodb-0b262a0603e67922`): Security Groups
- **Atlas Access Control and RBAC** (`mongodb-c156c7fae65cd994`): Atlas Access Control and RBAC
- **Atlas Real-Time Performance Panel** (`mongodb-8789f69d361dfdf9`): Atlas Real-Time Performance Panel
- **GKE Atlas Kubernetes Operator** (`mongodb-453d68fef45f1614`): GKE Atlas Kubernetes Operator
- **tls-x509-auth** (`mongodb-97b0256261e175d4`): tls-x509-auth
- **Atlas Kubernetes Operator AKO v2.14** (`mongodb-4b282dfe071d8ed3`): Atlas Kubernetes Operator AKO v2.14
- **Kubernetes Operator Deployment** (`mongodb-319ada705f7823ec`): Kubernetes Operator Deployment
- **resume-and-checkpoint** (`mongodb-e8cd8e986e841100`): resume-and-checkpoint
- **Atlas auto-scaling gating by oplog window and its alerts** (`mongodb-2a06abfc749f181d`): Atlas auto-scaling gating by oplog window and its alerts
- **Atlas Infinite storage metering and max storage limit** (`mongodb-290473cfefc454a9`): Atlas Infinite storage metering and max storage limit
- **GCP Workload Identity Atlas** (`mongodb-90fdd0f46c688fab`): GCP Workload Identity Atlas
- **Atlas Query Shape Insights and Namespace Insights** (`mongodb-cbc35723dae300d2`): Atlas Query Shape Insights and Namespace Insights
- **Multi-Cloud Replica Sets** (`mongodb-120c40fd91e55e9b`): Multi-Cloud Replica Sets
- **Common upgrade failures** (`mongodb-2d0a34e2c49f4884`): Common upgrade failures
- **Atlas Administration API rolling index endpoint** (`mongodb-1d8cdf7b5a1b8ece`): Atlas Administration API rolling index endpoint
- **Function Context Object** (`mongodb-577fa26daf8ef3e2`): Function Context Object
- **Compass Data Modeling ER Diagrams** (`mongodb-877ffcda272dcb0a`): Compass Data Modeling ER Diagrams
- **Cost-based ranker plan selection for sorted queries (8.3+)** (`mongodb-56ea3f475182e73c`): Cost-based ranker plan selection for sorted queries (8.3+)
- **MongoDB primary-driven index builds (PDIB)** (`mongodb-f5fe8246bc1f373b`): MongoDB primary-driven index builds (PDIB)
- **Primary-driven index builds** (`mongodb-c1bd38937e366405`): Primary-driven index builds
- **DISTINCT_SCAN with shard filtering in 8.2** (`mongodb-db4cbab4dbb77651`): DISTINCT_SCAN with shard filtering in 8.2
- **Atlas Data API (EOL)** (`mongodb-e1ddbf34cc672f78`): Atlas Data API (EOL)
- **Atlas tag taxonomy for showback and chargeback** (`mongodb-86041ef3cfe84899`): Atlas tag taxonomy for showback and chargeback
- **Collation-based case-insensitive equality** (`mongodb-4617d3df0f456a1b`): Collation-based case-insensitive equality
- **Covered queries and projection design** (`mongodb-8c1f45c525ccf3e4`): Covered queries and projection design
- **Multikey index sort bounds** (`mongodb-628fedbd91c89a1e`): Multikey index sort bounds
- **Standard URI Format** (`mongodb-f266e83645f0a63b`): Standard URI Format
- **Voyage AI Embeddings** (`mongodb-5dad7afc87cb6d02`): Voyage AI Embeddings
- **LDAP and Federation** (`mongodb-5ce35771381f77b4`): LDAP and Federation
- **Cedar forbid-only policy patterns for Atlas** (`mongodb-7f97f9313a333594`): Cedar forbid-only policy patterns for Atlas
- **Matryoshka and quantization-aware embedding models** (`mongodb-3df89994c3c60fd5`): Matryoshka and quantization-aware embedding models
- **Atlas Log Push SIEM** (`mongodb-4b4345da01d5d1d7`): Atlas Log Push SIEM
- **Realm Migration Paths** (`mongodb-70bfe64d4988e041`): Realm Migration Paths
- **Session Windows** (`mongodb-78341eed36106b0a`): Session Windows
- **MongoSync GA Tool** (`mongodb-be98665961019bba`): MongoSync GA Tool
- **Change Point Detection** (`mongodb-fd56e95646773af2`): Change Point Detection
- **Interval evaluation trees and parameterized plan caching** (`mongodb-877171bb4e49da96`): Interval evaluation trees and parameterized plan caching
- **dropIndexes abort semantics** (`mongodb-02fccc0175bf8fd5`): dropIndexes abort semantics
- **Matryoshka Dimension Truncation for Vector Storage Cost** (`mongodb-b5f4c0654aaba39d`): Matryoshka Dimension Truncation for Vector Storage Cost
- **min()/max() requiring hint** (`mongodb-8098aacdcbc7b7d6`): min()/max() requiring hint
- **Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern)** (`mongodb-8a48380dc82bfddc`): Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern)
- **Scheduled and Predictive Scaling for Atlas Cost** (`mongodb-42f9a99e97586251`): Scheduled and Predictive Scaling for Atlas Cost
- **Atlas Performance Advisor drop-index recommendations** (`mongodb-50ec9dcdbff2ae63`): Atlas Performance Advisor drop-index recommendations
- **Atlas Activity Feed** (`mongodb-381f9cb1f11c02c6`): Atlas Activity Feed
- **FedRAMP and AtlasGov** (`mongodb-d85a4dde5a84399b`): FedRAMP and AtlasGov
- **Google Workspace SAML Federation** (`mongodb-2ebeb8945d16290b`): Google Workspace SAML Federation
- **Ops Manager Architecture** (`mongodb-d707c731d700118f`): Ops Manager Architecture
- **CI Performance Regression Gating** (`mongodb-e63f9e56ab1438f4`): CI Performance Regression Gating
- **Azure OpenAI Atlas Vector Search** (`mongodb-7eb8140e6471708a`): Azure OpenAI Atlas Vector Search
- **GCP Shared VPC** (`mongodb-cc2de67c04f6dc80`): GCP Shared VPC
- **MongoDB Realm Mobile Sync** (`mongodb-aa6c118bd17c4c4d`): MongoDB Realm Mobile Sync
- **Vertex AI Atlas Vector Search** (`mongodb-fb6faf447a66c759`): Vertex AI Atlas Vector Search
- **Atlas Application Insights OTel** (`mongodb-0e95827b0ade29f8`): Atlas Application Insights OTel
- **Atlas Infinite fixed-IOPS tiers and decoupled storage** (`mongodb-c385a05c16af82e4`): Atlas Infinite fixed-IOPS tiers and decoupled storage
- **Stream Processor Pipeline** (`mongodb-4e5fb2f311299e5b`): Stream Processor Pipeline
- **Azure Key Vault RBAC Atlas** (`mongodb-157cd8e075fa7c59`): Azure Key Vault RBAC Atlas
- **Hub-and-Spoke Atlas Networking** (`mongodb-a3775c9d11bdbc90`): Hub-and-Spoke Atlas Networking
- **Common Failure Modes** (`mongodb-7e07d673e1be7c37`): Common Failure Modes
- **Dynamic bucket sizing and cache-pressure closures** (`mongodb-daf240a9ba3ba62e`): Dynamic bucket sizing and cache-pressure closures
- **Quantization-aware and Matryoshka embeddings (voyage-3-large) with Atlas dimension slicing** (`mongodb-8d61b695eec98ece`): Quantization-aware and Matryoshka embeddings (voyage-3-large) with Atlas dimension slicing
- **Atlas Infinite oplog and storage-layer replication** (`mongodb-850019f33a974bd2`): Atlas Infinite oplog and storage-layer replication
- **Counter-document pattern** (`mongodb-0c0b0a1154fd4e2f`): Counter-document pattern
- **Field-name abbreviation trade-offs** (`mongodb-650613677dbd2261`): Field-name abbreviation trade-offs
- **M10 shared-vCPU dedicated tier economics** (`mongodb-aa673735c7a186fc`): M10 shared-vCPU dedicated tier economics
- **Natural language to MongoDB query generation** (`mongodb-dc0e349b1a51390e`): Natural language to MongoDB query generation
- **Region and Cloud Provider Price Differentials for Atlas** (`mongodb-88a25e3164ccb96f`): Region and Cloud Provider Price Differentials for Atlas
- **Tailable cursors and maxAwaitTimeMS** (`mongodb-bfbf617cf85a9d45`): Tailable cursors and maxAwaitTimeMS
- **Coefficient of Variation / Run-to-Run Noise Control** (`mongodb-3e00c8e01fb3a553`): Coefficient of Variation / Run-to-Run Noise Control
- **Ops Manager Application** (`mongodb-29c4d8d154578c53`): Ops Manager Application
- **Service Account per Environment Pattern** (`mongodb-dc4854f92863692c`): Service Account per Environment Pattern
- **Eviction thread sizing and wiredTigerEngineRuntimeConfig tuning** (`mongodb-02d995b3895148bd`): Eviction thread sizing and wiredTigerEngineRuntimeConfig tuning
- **V2 and V3 compressed buckets and unsorted conversion** (`mongodb-f80ad0c2b80d8801`): V2 and V3 compressed buckets and unsorted conversion
- **Atlas Audit Logs Cloud Logging** (`mongodb-e81c7a40a5dd8ba8`): Atlas Audit Logs Cloud Logging
- **Archive Monitoring** (`mongodb-3b115ee0e0d6318c`): Archive Monitoring
- **Atlas index build tier defaults** (`mongodb-9b3f6cc7e3d3ac23`): Atlas index build tier defaults
- **Atlas tier-fixed index build limits** (`mongodb-ce4a0cb22fbb3201`): Atlas tier-fixed index build limits
- **Benchmarking Anti-Patterns** (`mongodb-0f53fd635c9fbc6c`): Benchmarking Anti-Patterns
- **Capacity Testing** (`mongodb-66bef086e555a1ce`): Capacity Testing
- **Growth Signals** (`mongodb-6274c15120b7ec90`): Growth Signals
- **New Relic Integration** (`mongodb-9fffebb211118f50`): New Relic Integration
- **Cloud Build Atlas API Auth** (`mongodb-1b899c93534c8684`): Cloud Build Atlas API Auth
- **GKE NodeLocal DNSCache Atlas** (`mongodb-f72b8570648c30f4`): GKE NodeLocal DNSCache Atlas
- **Cloud HSM Atlas** (`mongodb-678da7ba00a22e0c`): Cloud HSM Atlas
- **MongoDB 8.0 autoCompact background compaction on Atlas** (`mongodb-55db4d991e83d87c`): MongoDB 8.0 autoCompact background compaction on Atlas
- **IAM Role Atlas API Access** (`mongodb-8cdf351b913d7856`): IAM Role Atlas API Access
- **Atlas AI Services Pricing (Agent Engine and Voyage AI)** (`mongodb-65372e08c7329b01`): Atlas AI Services Pricing (Agent Engine and Voyage AI)
- **Atlas backup/PITR and data transfer cost drivers** (`mongodb-33cd7f0ef85a1717`): Atlas backup/PITR and data transfer cost drivers
- **Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress)** (`mongodb-317efde63c35f04e`): Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress)
- **Ranked and scored input pipeline eligibility** (`mongodb-2d3afdc9af021e50`): Ranked and scored input pipeline eligibility
- **Reading slotBasedPlan explain output for time series** (`mongodb-2f78513e26be14c1`): Reading slotBasedPlan explain output for time series
- **Resource Policy Drift Monitoring (nonCompliantResources)** (`mongodb-10d303000d21a5a4`): Resource Policy Drift Monitoring (nonCompliantResources)
- **Shard Key Design and Resharding as Cost Levers** (`mongodb-8c1f7f52a5a83b63`): Shard Key Design and Resharding as Cost Levers; Shard-key choice and scatter-gather cost
- **Atlas Organization Teams** (`mongodb-b1838a4c6d5a9330`): Atlas Organization Teams
- **Blockstore Snapshot Storage** (`mongodb-ca642828a73057d3`): Blockstore Snapshot Storage
- **Flexible Sync** (`mongodb-65efaa319f27a7f0`): Flexible Sync
- **PCI DSS Scoping and Tokenization** (`mongodb-d7f46c466da1b02f`): PCI DSS Scoping and Tokenization
- **HTTP Data Access Replacements** (`mongodb-3f2d54a8b927d286`): HTTP Data Access Replacements
- **Express path for _id lookups on sharded collections** (`mongodb-f9c388b7c70355e6`): Express path for _id lookups on sharded collections
- **Compass CRUD and Documents Tab** (`mongodb-52be8d6f6c272637`): Compass CRUD and Documents Tab
- **GCP Private Service Connect** (`mongodb-b1250b00bb0c74d2`): GCP Private Service Connect
- **MongoDB CBR CE source metadata** (`mongodb-f4b4df52106131ad`): MongoDB CBR CE source metadata
- **Schema Transformation** (`mongodb-7ed8978ed1d2b703`): Schema Transformation
- **RAG Patterns** (`mongodb-400d96b9c85329de`): RAG Patterns
- **RAG Patterns with Vector Search** (`mongodb-4794c1dff5e5d33b`): RAG Patterns with Vector Search
- **Atlas Bicep Private Endpoint** (`mongodb-8f15c6e48b67c05d`): Atlas Bicep Private Endpoint
- **Atlas CLI Terraform Plugin** (`mongodb-442ae9fb2adb854e`): Atlas CLI Terraform Plugin
- **Atlas nonCompliantResources endpoint** (`mongodb-1ce98941b0b66b02`): Atlas nonCompliantResources endpoint
- **Admin API alert configurations for billing events** (`mongodb-5c6881646c1184e6`): Admin API alert configurations for billing events
- **Atlas Query Shape Insights** (`mongodb-4fdb99e4891908d0`): Atlas Query Shape Insights
- **Atlas Vector Search automatic quantization and rescoring** (`mongodb-8065882d5c020aa0`): Atlas Vector Search automatic quantization and rescoring
- **Index Sufficiency Warning** (`mongodb-644ccfc4822faa60`): Index Sufficiency Warning
- **Namespace Insights** (`mongodb-4ae8627725bdc8e0`): Namespace Insights
- **Sparse and partial indexes for $exists** (`mongodb-41f6434505be256e`): Sparse and partial indexes for $exists
- **transformIdentifiers HMAC privacy mode** (`mongodb-65276786be8fc9a3`): transformIdentifiers HMAC privacy mode
- **Unlinking marketplace billing safely** (`mongodb-83af8b083c40dc81`): Unlinking marketplace billing safely
- **Atlas Search Nodes** (`mongodb-fa22fbd142979c69`): Atlas Search Nodes
- **Search Nodes** (`mongodb-480217ea9ca9e65e`): Search Nodes
- **Partition-Based Sync (Legacy)** (`mongodb-c838d9e21babc96a`): Partition-Based Sync (Legacy)
- **Atlas Search Lucene Architecture** (`mongodb-2c3d75bdda126d05`): Atlas Search Lucene Architecture
- **Encryption Requirements (At-Rest, In-Transit, Field-Level)** (`mongodb-37ff8a71a7274214`): Encryption Requirements (At-Rest, In-Transit, Field-Level)
- **Organization-scoped alert configuration API** (`mongodb-9507fa25c7d06b40`): Organization-scoped alert configuration API
- **Atlas GraphQL API Removal** (`mongodb-eb07b6ac4334f24b`): Atlas GraphQL API Removal
- **Compass Performance Insights** (`mongodb-86d03ff72b6824af`): Compass Performance Insights
- **Azure Service Bus Atlas Triggers** (`mongodb-a0e34fee1aa56fac`): Azure Service Bus Atlas Triggers
- **Lambda Managed Instances and MongoClient concurrency safety** (`mongodb-c56934954429e244`): Lambda Managed Instances and MongoClient concurrency safety
- **Atlas Infinite storage model (max storage limit, no auto-scaling)** (`mongodb-a2f56f7f5271253e`): Atlas Infinite storage model (max storage limit, no auto-scaling)
- **Search Highlighting** (`mongodb-65c96ce8f6ecde6d`): Search Highlighting
- **replSetResizeOplog and oplog compaction runbook** (`mongodb-b68de527be6e2e1b`): replSetResizeOplog and oplog compaction runbook
- **Atlas Programmatic API Keys (Legacy)** (`mongodb-c713b2d5c2d1effb`): Atlas Programmatic API Keys (Legacy)
- **Partition Field Count Limits (DATE vs CUSTOM)** (`mongodb-5135f31e186c3438`): Partition Field Count Limits (DATE vs CUSTOM)
- **Atlas IaC Anti-Patterns** (`mongodb-bd8a0fc4f9a66739`): Atlas IaC Anti-Patterns
- **Trigger and Function Anti-Patterns** (`mongodb-3eee9765892eec29`): Trigger and Function Anti-Patterns
- **Compliance Gaps and Shared Responsibility** (`mongodb-13b1050815e441ab`): Compliance Gaps and Shared Responsibility
- **atlas kubernetes config generate** (`mongodb-2574043c96fe5c3d`): atlas kubernetes config generate
- **Multi-Org Scale Patterns** (`mongodb-0a7ff37463f4e635`): Multi-Org Scale Patterns
- **Atlas Infinite fixed per-tier IOPS and public-preview feature exclusions** (`mongodb-926e1c744b633b85`): Atlas Infinite fixed per-tier IOPS and public-preview feature exclusions
- **Primary-driven index builds (spill to a replicated table)** (`mongodb-9ac00e735a7f32be`): Primary-driven index builds (spill to a replicated table)
- **$function and server-side JavaScript hardening** (`mongodb-96aa57b9e6f1d8f2`): $function and server-side JavaScript hardening
- **Atlas Charts billing dashboards** (`mongodb-1585ac28474d20d9`): Atlas Charts billing dashboards
- **Atlas GraphQL API (EOL)** (`mongodb-4abe3229d94cc8a1`): Atlas GraphQL API (EOL)
- **Atlas SQL Schema Builder** (`mongodb-44e5cf331389b4b5`): Atlas SQL Schema Builder
- **Credit expiry and History table** (`mongodb-51d2f0001920e1e6`): Credit expiry and History table
- **Custom HTTPS Endpoints (EOL)** (`mongodb-d58525528c39df1d`): Custom HTTPS Endpoints (EOL)
- **Hashed Indexes** (`mongodb-951dcc6b6f85de18`): Hashed Indexes
- **Index hints on time series collections** (`mongodb-7eea626bfebceba6`): Index hints on time series collections
- **JIT user provisioning** (`mongodb-a80ae57be2b5548f`): JIT user provisioning
- **Text Indexes** (`mongodb-08c8f2cc5ac72558`): Text Indexes
- **TTL Indexes** (`mongodb-50484d41c036bd05`): TTL Indexes
- **Multi-Environment Terraform Directories vs Workspaces** (`mongodb-5edf80958ba49aa5`): Multi-Environment Terraform Directories vs Workspaces
- **Atlas Cluster IaC** (`mongodb-6b3a869dee4738fa`): Atlas Cluster IaC
- **Atlas Azure Regions Mapping** (`mongodb-4878cd8649599271`): Atlas Azure Regions Mapping
- **Error Code Lookup** (`mongodb-438a31dd3b86ae4b`): Error Code Lookup
- **GCP Regions Atlas Mapping** (`mongodb-6fe8c519c22b2af0`): GCP Regions Atlas Mapping
- **Atlas Envelope Encryption GCP** (`mongodb-588b0a8b703c23ab`): Atlas Envelope Encryption GCP
- **Sync Configuration** (`mongodb-3193e5802c8a1989`): Sync Configuration
- **Breaking-point / overload testing methodology (first bottleneck vs visible symptom, cascading failure, thundering herd, cache-eviction death spiral)** (`mongodb-68c6469e72a8661c`): Breaking-point / overload testing methodology (first bottleneck vs visible symptom, cascading failure, thundering herd, cache-eviction death spiral)
- **Cache-derived dynamic bucket size limit** (`mongodb-2c58908da1fa80b5`): Cache-derived dynamic bucket size limit
- **Dynamic bucket size cap under cache pressure** (`mongodb-4508beee32348bbe`): Dynamic bucket size cap under cache pressure
- **Atlas Data Federation GCS** (`mongodb-553a6b0b2ccf2d90`): Atlas Data Federation GCS
- **Atlas marketplace private offers** (`mongodb-be13cc5ab72690be`): Atlas marketplace private offers
- **Client Side Field Level Encryption (CSFLE)** (`mongodb-7cc7652d0546c019`): Client Side Field Level Encryption (CSFLE)
- **Gen1 vs Gen2 storage and IOPS billing** (`mongodb-cfed93e5e3217b53`): Gen1 vs Gen2 storage and IOPS billing
- **HNSW Index Parameters** (`mongodb-bf204a625a79e124`): HNSW Index Parameters
- **SBE $lookup pushdown and hash join** (`mongodb-dd877ae5b4fdc443`): SBE $lookup pushdown and hash join
- **Search Index Mapping** (`mongodb-5064f0999643a516`): Search Index Mapping
- **Realm Object Model** (`mongodb-c20f03c61f6d8d86`): Realm Object Model
- **Shared-cost allocation rules for managed database services** (`mongodb-7fed8a5c0e525682`): Shared-cost allocation rules for managed database services
- **eviction_updates_trigger and the updates ratio** (`mongodb-3d8082b039d1a5b5`): eviction_updates_trigger and the updates ratio
- **Realm Migration** (`mongodb-00dccbe36e3c2845`): Realm Migration
- **Restore Workflows** (`mongodb-97955f4bfeff9961`): Restore Workflows
- **available read concern** (`mongodb-3adfa2de2738ffc4`): available read concern
- **Programmatic API Keys Legacy Auth** (`mongodb-7ff755dc9123f410`): Programmatic API Keys Legacy Auth
- **Filesystem Snapshot Storage** (`mongodb-403cfb9c953b3cfe`): Filesystem Snapshot Storage
- **Azure Private DNS Resolver** (`mongodb-2a7b6b28a22214d2`): Azure Private DNS Resolver
- **Same-field `$or` to `$in` rewrite** (`mongodb-24b4ec4143de82f7`): Same-field `$or` to `$in` rewrite
- **Sustained overload / soak testing (memory leaks, connection pool exhaustion, WiredTiger cache thrashing, ticket starvation, oplog window shrinkage)** (`mongodb-f6fc4637e92203e6`): Sustained overload / soak testing (memory leaks, connection pool exhaustion, WiredTiger cache thrashing, ticket starvation, oplog window shrinkage)
- **Atlas LDAPS (Deprecated 8.0)** (`mongodb-0e02523c109ee8d4`): Atlas LDAPS (Deprecated 8.0)
- **MongoDB Developer Patterns** (`mongodb-243b0c55e1170da3`): MongoDB Developer Patterns; mongodb-developer
- **Azure Synapse Atlas Data Federation** (`mongodb-e34977d75b52bae9`): Azure Synapse Atlas Data Federation
- **AKO Dry Run Mode** (`mongodb-d201c8f3cf225271`): AKO Dry Run Mode
- **Gen1 vs Gen2 IOPS billing** (`mongodb-a61b2707340ba6da`): Gen1 vs Gen2 IOPS billing
- **Atlas Admin API invoice endpoints** (`mongodb-95f163645ff4d869`): Atlas Admin API invoice endpoints
- **Atlas Infinite compute auto-scaling** (`mongodb-0e173d1a4a7be744`): Atlas Infinite compute auto-scaling
- **Auto-scaling tier ranges** (`mongodb-912dd90d8980ae92`): Auto-scaling tier ranges
- **Backup and PITR cost modelling** (`mongodb-7957a71b8005114a`): Backup and PITR cost modelling
- **Cedar policy authoring for cluster size and autoscaling caps** (`mongodb-28c3a0f533452bc5`): Cedar policy authoring for cluster size and autoscaling caps
- **Memory Limits and allowDiskUse** (`mongodb-5e76dadf4ce5f25a`): Memory Limits and allowDiskUse; Per-operation memory limit in 9.0
- **Multi-region cluster cost premium** (`mongodb-9fdf26d536b91015`): Multi-region cluster cost premium
- **Pause/resume automation with Terraform or GitHub Actions** (`mongodb-072eec3613eb7532`): Pause/resume automation with Terraform or GitHub Actions
- **Right-sizing from Atlas metrics** (`mongodb-f9b0361626e95678`): Right-sizing from Atlas metrics
- **Databricks Workspace Integration** (`mongodb-fd6e1b954193be03`): Databricks Workspace Integration
- **Reconciliation and Page Splitting** (`mongodb-7957499ab405ef88`): Reconciliation and Page Splitting
- **Spark Connector V10 Architecture** (`mongodb-c0a2b3768350bb12`): Spark Connector V10 Architecture
- **Baseline Methodology** (`mongodb-2760fe0a699e3288`): Baseline Methodology
- **Common Sizing Mistakes** (`mongodb-1abd5ce43178f631`): Common Sizing Mistakes
- **Upgrade event coverage (pre/during/post)** (`mongodb-8c41ced74b8c7dc9`): Upgrade event coverage (pre/during/post)
- **EU Data Act switching charges and in-parallel egress** (`mongodb-d72b938404e888d1`): EU Data Act switching charges and in-parallel egress
- **Atlas App Services Cost Model** (`mongodb-39e950406a57f276`): Atlas App Services Cost Model
- **AtlasGov Azure Government** (`mongodb-0d3d28f234f5982e`): AtlasGov Azure Government
- **Rolling index builds as a resource-limited alternative** (`mongodb-524ff443222313b4`): Rolling index builds as a resource-limited alternative
- **minor-version compatibility rule** (`mongodb-17bc98afbe35ace5`): minor-version compatibility rule
- **Archive Anti-Patterns** (`mongodb-704d5b56a3ed1f40`): Archive Anti-Patterns
- **Backup Anti-Patterns** (`mongodb-ae5239fa5d4fc5af`): Backup Anti-Patterns
- **Automated Embedding (autoEmbed) quantization types** (`mongodb-1672753667a8a066`): Automated Embedding (autoEmbed) quantization types
- **Automated Embedding (autoEmbed) quantization types including binaryNoRescore** (`mongodb-939c6afccdc05227`): Automated Embedding (autoEmbed) quantization types including binaryNoRescore
- **Spill WiredTiger instance cache** (`mongodb-b0ea562a020af0f2`): Spill WiredTiger instance cache
- **WiredTiger spill instance cache** (`mongodb-6193357302c34e7a`): WiredTiger spill instance cache
- **$groupByDistinct internal stage** (`mongodb-5d21f894eb00e4db`): $groupByDistinct internal stage
- **Analytics node tier prorating** (`mongodb-e44a05f678750f34`): Analytics node tier prorating
- **App Services Deployment Model** (`mongodb-631a7fff215706bc`): App Services Deployment Model
- **App Services Rules and Permissions** (`mongodb-013376b96fb1d8a1`): App Services Rules and Permissions
- **App Services Schema Validation** (`mongodb-3f873e88adc22c77`): App Services Schema Validation
- **App Services Values and Secrets** (`mongodb-47433a72b9ba26e0`): App Services Values and Secrets
- **Atlas-only feature lock-in and exit cost** (`mongodb-dad75167e372f795`): Atlas-only feature lock-in and exit cost
- **AWS Marketplace EDP drawdown for Atlas** (`mongodb-24f205c548a05790`): AWS Marketplace EDP drawdown for Atlas
- **Backup and PIT oplog storage region billing** (`mongodb-55169fce81931358`): Backup and PIT oplog storage region billing
- **Cost Explorer filters for AI services** (`mongodb-3455606a49d0ae97`): Cost Explorer filters for AI services
- **MongoSQL ODBC Driver** (`mongodb-12936442c62a6fe5`): MongoSQL ODBC Driver
- **Performance Diagnostic Workflow** (`mongodb-954b0f058dede948`): Performance Diagnostic Workflow
- **PII Masking & Query Hash Anonymization** (`mongodb-d67878358f98ad51`): PII Masking & Query Hash Anonymization
- **Power BI DirectQuery** (`mongodb-685dde441f0bde62`): Power BI DirectQuery
- **Query limits and billing alerts for archive spend** (`mongodb-af8bfd1b3f4a9a17`): Query limits and billing alerts for archive spend
- **Support line items per cloud provider on invoices** (`mongodb-9b823f0f1fba9804`): Support line items per cloud provider on invoices
- **Unique Indexes** (`mongodb-03460370b2d6d37b`): Unique Indexes
- **Network Security Layers** (`mongodb-e7a96f7bdbba9e83`): Network Security Layers
- **Atlas LDAP Azure AD DS** (`mongodb-9e7d177c434dbc26`): Atlas LDAP Azure AD DS
- **Connection Pool Benchmarking** (`mongodb-99072114e6d13c88`): Connection Pool Benchmarking
- **Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure)** (`mongodb-57ad2f2520b1d24c`): Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure)
- **Cloud exit-credit programs and EU Data Act in-parallel egress** (`mongodb-2a049fdcae415842`): Cloud exit-credit programs and EU Data Act in-parallel egress
- **Atlas Infinite oplog and storage cost** (`mongodb-f54190428672705c`): Atlas Infinite oplog and storage cost
- **Atlas Three-Tier Identity Model** (`mongodb-ad4304fc940b9fae`): Atlas Three-Tier Identity Model
- **Idle-spend and minimum-commit economics of serverless vector stores** (`mongodb-57fe4d836a248d22`): Idle-spend and minimum-commit economics of serverless vector stores
- **Azure Native MongoDB ANM** (`mongodb-5657dce804c8625f`): Azure Native MongoDB ANM
- **Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors** (`mongodb-9e8aa89ebeeddb75`): Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors
- **Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling** (`mongodb-122e84dfa7d2ad55`): Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Atlas FOCUS Cost and Usage Report; Atlas FOCUS report ingestion into FinOps tools; Atlas Operate-phase anomaly detection and budgets; Cloud commit drawdown (EDP, MACC, GCP commit) via Atlas; Cross-Organization Billing; Cross-Organization Billing and Linked Invoices; Cross-organization billing; Cross-organization billing and linked invoices; FOCUS 1.3 Atlas cost reports; Marketplace private offers and contracts for Atlas; Matryoshka dimension truncation for storage; Terraform tag enforcement for Atlas clusters; nonCompliantResources drift monitoring
- **Block Compression (snappy/zlib/zstd)** (`mongodb-f1cb37faef6f587b`): Archive Cost Model; Block Compression (snappy/zlib/zstd); Bucket Architecture and Columnar Compression; Prefix Compression (indexes); Storage and Data-Lifecycle Cost Levers
- **Compass Index Management** (`mongodb-4698e88555cc88f8`): Compass Index Management
- **DATE criteria field types and formats** (`mongodb-7d3f13cdff3fdc8b`): DATE criteria field types and formats
- **Enterprise Advanced licensing economics** (`mongodb-dd68044b3d888f7c`): Enterprise Advanced licensing economics
- **Project-level billing change alerts** (`mongodb-0fa1f571793d7a59`): Project-level billing change alerts
- **Shared-cost splitting for Atlas projects** (`mongodb-618d04a674b2e33e`): Shared-cost splitting for Atlas projects
- **Stored Source Performance Optimization** (`mongodb-09caeeadd9d7b368`): Stored Source Performance Optimization
- **Refresh scheduling with Atlas Scheduled Triggers** (`mongodb-cafa7a241b938ab0`): Refresh scheduling with Atlas Scheduled Triggers
- **positional index path caveat** (`mongodb-8e48f8b83be4e936`): positional index path caveat
- **Performance Tuning Checklist** (`mongodb-68f54e5e62e38cf6`): Performance Tuning Checklist
- **Enterprise Advanced Licensing** (`mongodb-b781ff20849e3088`): Enterprise Advanced Licensing
- **maxEstimatedScanBytes collection-scan rejection (9.0)** (`mongodb-55851d1ec7332aa1`): maxEstimatedScanBytes collection-scan rejection (9.0)
- **Network (wire) compression** (`mongodb-6d1d3a3f9fbe01ad`): Network (wire) compression
- **Atlas Search Architecture** (`mongodb-66c5f0e3369f51e5`): Atlas Search Architecture
- **Backup Daemon and Head DB** (`mongodb-8465fb21b1a62609`): Backup Daemon and Head DB
- **Atlas IAM Compliance Mapping** (`mongodb-6034240836f9df82`): Atlas IAM Compliance Mapping
- **Ops Manager LDAP/Kerberos/SAML/OIDC Federation** (`mongodb-7aadc337486dba28`): Ops Manager LDAP/Kerberos/SAML/OIDC Federation
- **Side bucket catalog** (`mongodb-c6459d640bbea983`): Side bucket catalog
- **Side bucket catalog for time series updates and deletes** (`mongodb-844cb4caa9361223`): Side bucket catalog for time series updates and deletes
- **Atlas Alerts Pub/Sub Escalation** (`mongodb-a366ff26c5ed3879`): Atlas Alerts Pub/Sub Escalation
- **Atlas Azure Monitor Metrics** (`mongodb-32861ee4c2903a3e`): Atlas Azure Monitor Metrics
- **Atlas Sentinel Log Integration** (`mongodb-d30cf2da8cfb6479`): Atlas Sentinel Log Integration
- **Cloud Monitoring Atlas Metrics** (`mongodb-1a845bc9089db6db`): Cloud Monitoring Atlas Metrics
- **Atlas Compliance Certifications** (`mongodb-af13ce2b294bc4da`): Atlas Compliance Certifications
- **Learning Paths by Role** (`mongodb-d99a2bbf2b84a66e`): Learning Paths by Role
- **Serverless Cold Start Behavior** (`mongodb-2af1a60394e45308`): Serverless Cold Start Behavior
- **Oplog sizing in Kubernetes operators and managed MongoDB-compatible services** (`mongodb-010e200700708f00`): Oplog sizing in Kubernetes operators and managed MongoDB-compatible services
- **Partition Field Type Enum Docs-vs-Spec Disagreement** (`mongodb-b655e2e370710552`): Partition Field Type Enum Docs-vs-Spec Disagreement
- **allowDiskUse-100MB-stage** (`mongodb-6f4052507f55a331`): allowDiskUse-100MB-stage
- **Auto-scaling min/max bounds and Terraform drift** (`mongodb-1affc6a1b924281d`): Auto-scaling min/max bounds and Terraform drift
- **Compass Aggregation Pipeline Builder** (`mongodb-619d9d2759179de5`): Compass Aggregation Pipeline Builder
- **Compass Natural Language Query** (`mongodb-765915002777e4c2`): Compass Natural Language Query
- **Config shard versus dedicated config server cost** (`mongodb-530d60bd5242f78d`): Config shard versus dedicated config server cost
- **MongoDB Charts billing dashboards** (`mongodb-301547a99e11b6b3`): MongoDB Charts billing dashboards
- **Persisting index usage metrics across restarts (PMM/monitoring)** (`mongodb-23dc66c763b719d7`): Persisting index usage metrics across restarts (PMM/monitoring)
- **Scale-down tuning for spiky batch workloads** (`mongodb-110b9d56520f4ac1`): Scale-down tuning for spiky batch workloads
- **Amazon DocumentDB profiler (CloudWatch Logs)** (`mongodb-78fdc802398495b2`): Amazon DocumentDB profiler (CloudWatch Logs)
- **mongosqld Architecture** (`mongodb-08aa4a8ddac5a810`): mongosqld Architecture
- **BI Connector Authentication** (`mongodb-c68b64ff052ee966`): BI Connector Authentication
- **Bucket catalog stripes, state registry and eras** (`mongodb-0a3be19203e9172f`): Bucket catalog stripes, state registry and eras
- **DRDL Schema Management** (`mongodb-f70a31016e7429c0`): DRDL Schema Management
- **Client-side operation timeout (CSOT)** (`mongodb-57629268b2c2e6cb`): Client-side operation timeout (CSOT)
- **Collation-based case-insensitive indexes as a $regex alternative** (`mongodb-f91e30bd5aaf2ccd`): Collation-based case-insensitive indexes as a $regex alternative
- **Intra-cluster replication transfer billing** (`mongodb-34bba6054db50a88`): Intra-cluster replication transfer billing
- **Retroactive support billing on reactivation** (`mongodb-ea29c899a57b0a5e`): Retroactive support billing on reactivation
- **Single-Field Indexes** (`mongodb-ef26cc1d0dbc3e18`): Single-Field Indexes
- **Time series collection expireAfterSeconds** (`mongodb-f7d449c60e94f3b9`): Time series collection expireAfterSeconds
- **Lucene BBQ binary quantization compared with Atlas binary quantization** (`mongodb-746e0de29ea30509`): Lucene BBQ binary quantization compared with Atlas binary quantization
- **Atlas Private DNS Zones Azure** (`mongodb-8dbee37d6cb6691b`): Atlas Private DNS Zones Azure
- **Cloud DNS Private Zone for Atlas** (`mongodb-cf2ab96ab3fe92c4`): Cloud DNS Private Zone for Atlas
- **Atlas Search Anti-Patterns** (`mongodb-01e2756fad33da09`): Atlas Search Anti-Patterns
- **Atlas Azure Security Compliance** (`mongodb-f7b2a023b1174f9f`): Atlas Azure Security Compliance
- **Audit-Ready Architecture and Evidence Collection** (`mongodb-7a989ec061f767c3`): Audit-Ready Architecture and Evidence Collection
- **Atlas billing alert configuration via Admin API** (`mongodb-e34eab21447b18d4`): Atlas billing alert configuration via Admin API
- **Rolling index build key inconsistency incident** (`mongodb-b41c8cb4dfa445cf`): Rolling index build key inconsistency incident
- **Rolling index build table-logging incident** (`mongodb-82f5b1f3a52c8ad2`): Rolling index build table-logging incident
- **Percona PMM mongolog query source** (`mongodb-29d81049e9589a0a`): Percona PMM mongolog query source
- **Realm SDK Languages and Platforms** (`mongodb-bee0bebe48e5df58`): Realm SDK Languages and Platforms
- **Benchmark Result Reporting** (`mongodb-c26a88841b1d5891`): Benchmark Result Reporting
- **Atlas MACC Eligibility** (`mongodb-c33e555ed435ce1a`): Atlas MACC Eligibility
- **Atlas Charts Integration** (`mongodb-37808c870d32c319`): Atlas Charts Integration
- **Partition Field Cardinality and the 2023-06-07 Storage Engine Change** (`mongodb-eca6bdfeb802b0e3`): Partition Field Cardinality and the 2023-06-07 Storage Engine Change
- **Atlas PrivateLink regional endpoint rates** (`mongodb-0a6ce44bfef7c552`): Atlas PrivateLink regional endpoint rates
- **Federated Query on Archive** (`mongodb-2d3198cf4d05f1ea`): Federated Query on Archive
- **Geospatial $lookup Patterns** (`mongodb-d4f8e4cc75d2b387`): Geospatial $lookup Patterns
- **Quantile Estimation (DDSketch)** (`mongodb-ef65b93b811e6c1a`): Quantile Estimation (DDSketch)
- **Associate Developer Certification** (`mongodb-699fe62f7eb165f2`): Associate Developer Certification
- **Atlas Terraform Azure Provider** (`mongodb-a66324ed3d3c4e22`): Atlas Terraform Azure Provider
- **Atlas Terraform GCP Provider** (`mongodb-6cccc78f566b5242`): Atlas Terraform GCP Provider
- **Atlas CLI Failure Scenarios** (`mongodb-c681ba5fc3682f30`): Atlas CLI Failure Scenarios
- **Atlas included-replica pricing vs per-instance HA billing** (`mongodb-4fc92e3a76fc64a9`): Atlas included-replica pricing vs per-instance HA billing
- **Egress and data transfer estimation** (`mongodb-7f3ba3ad9cb271c0`): Egress and data transfer estimation
- **queryKnobs and per-command querySettings** (`mongodb-0f7e0554d978cb8e`): queryKnobs and per-command querySettings
- **Re-indexing cost when changing numDimensions** (`mongodb-2e32f4acda4557c2`): Re-indexing cost when changing numDimensions
- **Untagged spend reporting** (`mongodb-7436041c120e41d7`): Untagged spend reporting
- **Associate Atlas Administrator** (`mongodb-d2e226ddc05adf05`): Associate Atlas Administrator
- **Atlas Secretless KV Authentication** (`mongodb-c9088713bcd43088`): Atlas Secretless KV Authentication
- **Associate DBA Certification** (`mongodb-79786832b560017b`): Associate DBA Certification
- **GCP Partnership and Marketplace** (`mongodb-0ce439a3cc502cdc`): GCP Partnership and Marketplace
- **Atlas Azure Troubleshooting Playbook** (`mongodb-a6730c590e68b7b3`): Atlas Azure Troubleshooting Playbook
- **Atlas GCP Troubleshooting** (`mongodb-a451ded7c4bc3ab8`): Atlas GCP Troubleshooting
- **Atlas Admin API billing alert configuration** (`mongodb-f64481d2ec8394f5`): Atlas Admin API billing alert configuration
- **Atlas Admin API rate limiting for scheduled polling** (`mongodb-2a9b2c66ae4897e3`): Atlas Admin API rate limiting for scheduled polling
- **Cross-vendor FOCUS pipelines (BigQuery/Snowflake)** (`mongodb-8483cc56f40c9bdd`): Cross-vendor FOCUS pipelines (BigQuery/Snowflake)
- **DynamoDB on-demand vs provisioned break-even** (`mongodb-b400b540461e780a`): DynamoDB on-demand vs provisioned break-even
- **FOCUS column mapping for Atlas credits** (`mongodb-62acea60461f46a0`): FOCUS column mapping for Atlas credits
- **Linking Atlas orgs to marketplace billing accounts** (`mongodb-00464fef4f41a2e0`): Linking Atlas orgs to marketplace billing accounts
- **MongoDB 8.0 WT Improvements (TCMalloc, ExpressPlan)** (`mongodb-afab306ff3cf4165`): MongoDB 8.0 WT Improvements (TCMalloc, ExpressPlan)
- **Monitoring Agent** (`mongodb-a844ba3e1cf70cac`): Monitoring Agent
- **Compass Anti-Patterns** (`mongodb-6259389b0fde158d`): Compass Anti-Patterns
- **Performance KB Articles** (`mongodb-52195cdc6f0d388d`): Performance KB Articles
- **Security KB Articles** (`mongodb-70bec2d9867486bc`): Security KB Articles
- **Config shard caveat (8.0+)** (`mongodb-82386c457ed496dc`): Config shard caveat (8.0+)
- **Atlas Triggers Workarounds (no change streams)** (`mongodb-f473863454ecd4bd`): Atlas Triggers Workarounds (no change streams)
- **HTTPS Endpoints** (`mongodb-0c442ef22f7b52a3`): HTTPS Endpoints
- **Workforce and Workload Identity Federation** (`mongodb-931e3798c496102e`): Workforce and Workload Identity Federation
- **Conftest/OPA rules over terraform show -json plans** (`mongodb-4d03e735ca976838`): Conftest/OPA rules over terraform show -json plans
- **Search node tier sizing for vector indexes** (`mongodb-6019089339a51f59`): Search node tier sizing for vector indexes
- **Cloud Manager Free/Standard/Premium Tiers** (`mongodb-87629f89d9e26c4c`): Cloud Manager Free/Standard/Premium Tiers
- **Google Distributed Cloud GDC** (`mongodb-3b6b097be5f70cab`): Google Distributed Cloud GDC
- **Error Envelope and customer sign-off** (`mongodb-28f634c995865584`): Error Envelope and customer sign-off
- **MongoDB Atlas Data Federation Architecture Internals** (`mongodb-df9d0bc2a7a7ca81`): MongoDB Atlas Data Federation Architecture Internals
- **MongoDB Atlas Data Federation Benchmark Metrics** (`mongodb-73d2b24448e3f151`): MongoDB Atlas Data Federation Benchmark Metrics
- **MongoDB Atlas Data Federation Failure Scenarios** (`mongodb-b2ed9dce83d067ba`): MongoDB Atlas Data Federation Failure Scenarios
- **MongoDB Atlas Data Federation Operational Runbook** (`mongodb-fac24e791fe7acdf`): MongoDB Atlas Data Federation Operational Runbook
- **MongoDB Drivers Architecture Internals** (`mongodb-1a9448e0f3318606`): MongoDB Drivers Architecture Internals
- **MongoDB Drivers Benchmark Metrics** (`mongodb-a09d610a47871a5a`): MongoDB Drivers Benchmark Metrics
- **MongoDB Drivers Failure Scenarios** (`mongodb-c397efc5d1f2c451`): MongoDB Drivers Failure Scenarios
- **MongoDB Drivers Operational Runbook** (`mongodb-e5ea512b67616c18`): MongoDB Drivers Operational Runbook
- **mongosh Reference Architecture Internals** (`mongodb-015ac78e13ef9f05`): mongosh Reference Architecture Internals
- **mongosh Reference Benchmark Metrics** (`mongodb-befcb053ca0a00f9`): mongosh Reference Benchmark Metrics
- **mongosh Reference Failure Scenarios** (`mongodb-54bb769be94b269e`): mongosh Reference Failure Scenarios
- **mongosh Reference Operational Runbook** (`mongodb-f651139da18b243e`): mongosh Reference Operational Runbook
- **Common Audit Findings and Remediation** (`mongodb-6094979b122ad5fe`): Common Audit Findings and Remediation
- **Backup storage rates by region** (`mongodb-f982a1742cbb79f2`): Backup storage rates by region
- **Cosmos DB RU estimation for MongoDB workloads** (`mongodb-1a844e0df74a38de`): Cosmos DB RU estimation for MongoDB workloads
- **Proportional minimum-commit allocation** (`mongodb-fb538eb4250cda06`): Proportional minimum-commit allocation
- **Scheduled compliance polling and alerting** (`mongodb-19826c5f8cc4ec78`): Scheduled compliance polling and alerting
- **Replica Set Support Articles** (`mongodb-ab3559cad3da459b`): Replica Set Support Articles
- **PostgreSQL invalid indexes from failed CONCURRENTLY builds** (`mongodb-7ec18ee4ed0cf964`): PostgreSQL invalid indexes from failed CONCURRENTLY builds
- **SQL Server resumable online index operations** (`mongodb-a7f881bd35836f95`): SQL Server resumable online index operations
- **Azure Partnership and MACC** (`mongodb-f60ebd5ae43d867d`): Azure Partnership and MACC
- **Atlas Admin API pending-invoice tags field** (`mongodb-219f38122399dbab`): Atlas Admin API pending-invoice tags field
- **Cloud DNS Terraform Atlas** (`mongodb-53d6f266cc6b04ae`): Cloud DNS Terraform Atlas
- **Journal compression** (`mongodb-48df1b736c264578`): Journal compression
- **Compass Plugins and Extensibility** (`mongodb-4242ef749c2308a9`): Compass Plugins and Extensibility
- **PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY** (`mongodb-1f6a5f22aae30ad4`): PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY
- **Billing incidents and refunds** (`mongodb-a048ccb7e608b58b`): Billing incidents and refunds
- **Queryable Backups** (`mongodb-bb22366c4d66dbf3`): Queryable Backups
- **Compass Editions** (`mongodb-e9c2b24e31844989`): Compass Editions
- **Error Codes and Troubleshooting Benchmark Metrics** (`mongodb-98c4cfdb6c7f87db`): Error Codes and Troubleshooting Benchmark Metrics
- **Unlinking an organization** (`mongodb-c63c368f0dede092`): Unlinking an organization
- **Authentication Triggers** (`mongodb-4830d6cf7c1ae676`): Authentication Triggers
- **SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints** (`mongodb-257362073fe4e362`): SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints
- **Atlas Device Sync Overview** (`mongodb-4a5f0c4fde4490d4`): Atlas Device Sync Overview
- **Instructor-Led Training** (`mongodb-0141a60bbcb5f57f`): Instructor-Led Training
- **Skill Badges (free micro-credentials)** (`mongodb-5f204010c3f7dda2`): Skill Badges (free micro-credentials)
- **Customer Troubleshooting Playbooks** (`mongodb-69669e4f5d5b7a5d`): Customer Troubleshooting Playbooks
- **Associate Data Modeler** (`mongodb-030915af7d76de1b`): Associate Data Modeler
- **MongoDB University Platform** (`mongodb-6426f266c379a7fe`): MongoDB University Platform
- **MongoDB KB Articles** (`mongodb-cd5d1bb84c993043`): MongoDB KB Articles
- **Cosmos DB for MongoDB wildcard differences** (`mongodb-7323eb0342be4b6c`): Cosmos DB for MongoDB wildcard differences
- **Common Pitfalls** (`mongodb-a4c11d42ea035436`): Common Pitfalls
- **MongoDB for Startups GCP** (`mongodb-8cbe1b7659a61bb5`): MongoDB for Startups GCP
- **Charts billing ingestion for linked orgs** (`mongodb-ce6e8e8d76e9c72e`): Charts billing ingestion for linked orgs
- **TAM Positioning Playbook** (`mongodb-097cc0a94a531196`): TAM Positioning Playbook
- **Process & governance (OWASP GenAI Red Teaming Guide, MITRE ATLAS, NIST AI RMF, red-team-in-CI)** (`mongodb-8b73611d4850a262`): Process & governance (OWASP GenAI Red Teaming Guide, MITRE ATLAS, NIST AI RMF, red-team-in-CI)
- **Credly Digital Badges** (`mongodb-b09b7b87f3f0d06d`): Credly Digital Badges
- **Google Cloud Partner of Year** (`mongodb-ff690284446ca615`): Google Cloud Partner of Year
- **$bucket-bucketAuto** (`mongodb-4fd180c5d28e6b9f`): $bucket-bucketAuto
- **$dateTrunc Downsampling** (`mongodb-a4d29a7ee6b59abe`): $dateTrunc Downsampling
- **$densify-$fill** (`mongodb-6a77065ae652a210`): $densify and $fill Gap Filling; $densify-$fill
- **$emit Operators** (`mongodb-8987bcabe1ca64a4`): $emit Operators
- **$facet** (`mongodb-a38682d5152e1b17`): $facet
- **$geoIntersects** (`mongodb-1330f33e089e9138`): $geoIntersects
- **$geoNear Aggregation Stage** (`mongodb-aeee07e3d2e90c66`): $geoNear Aggregation Stage
- **$geoWithin and $centerSphere** (`mongodb-8afb7a9ab65219e6`): $geoWithin and $centerSphere
- **$graphLookup** (`mongodb-23a6e8f9f938352b`): $graphLookup
- **$lookup** (`mongodb-bba70d52b3e318a5`): $lookup; $lookup Patterns
- **$merge and $out Materialized Views** (`mongodb-5366ab03426ba767`): $merge and $out Materialized Views; $merge-$out
- **$near and $nearSphere** (`mongodb-c23c6cabf35ea154`): $near and $nearSphere
- **$search Operators** (`mongodb-090a2e310b501740`): $search Operators
- **$setWindowFields** (`mongodb-d60ca5162d1fd8af`): $setWindowFields
- **$setWindowFields Window Functions** (`mongodb-687d300df2bcae09`): $setWindowFields Window Functions
- **$source Operators** (`mongodb-07f03b57d97dbdb8`): $source Operators
- **$unionWith** (`mongodb-6cafdceb228248f8`): $unionWith
- **2d Indexes** (`mongodb-4618b6d71c17545c`): 2d Indexes
- **2dsphere Indexes** (`mongodb-d9e88e406b466523`): 2dsphere Geospatial Indexes; 2dsphere Indexes
- **5.6.x RawBsonDocument codec regression** (`mongodb-c7c45513457adce2`): 5.6.x RawBsonDocument codec regression
- **5.7/5.8 release notes** (`mongodb-ce90da82ef3a47ba`): 5.7/5.8 release notes
- **8.0.x regression catalog** (`mongodb-fab37574c4aa9ecf`): 8.0.x regression catalog
- **Access Control** (`mongodb-bce56360af562bf4`): Access Control
- **Adaptive Timeouts in Database Drivers** (`mongodb-73c869364047fead`): Adaptive Timeouts in Database Drivers
- **afterClusterTime** (`mongodb-d70e228eb036aa65`): afterClusterTime
- **Aggregation Expressions** (`mongodb-04d26ad96e716c5e`): Aggregation Expressions
- **Aggregation Pipeline in Charts** (`mongodb-064f21af22332e1e`): Aggregation Pipeline in Charts
- **Air-Gap and Local Mode** (`mongodb-b0e87d8c70833acb`): Air-Gap and Local Mode
- **AKO CRDs** (`mongodb-4aa9fac2c24fc655`): AKO CRDs
- **AKO GitOps** (`mongodb-088b9294628212e3`): AKO GitOps
- **AKO Helm Installation** (`mongodb-f2bd38612bf64f61`): AKO Helm Installation
- **AKO Independent CRDs** (`mongodb-cba3de983033869f`): AKO Independent CRDs
- **AKO Reconciliation Skip Annotation** (`mongodb-3ed59405f04a6ec7`): AKO Reconciliation Skip Annotation
- **AKO Subobject CRDs Deprecated** (`mongodb-1fc414c64331cf19`): AKO Subobject CRDs Deprecated
- **AKO Troubleshooting** (`mongodb-5f35949ec5618f60`): AKO Troubleshooting
- **AKO vs Terraform** (`mongodb-8f3a99abe0aae8e6`): AKO vs Terraform
- **AKO Workload Identity** (`mongodb-41ef64f6e38d9e66`): AKO Workload Identity
- **AKS Atlas Kubernetes Operator** (`mongodb-771b2a5d816d6f4e`): AKS Atlas Kubernetes Operator
- **AKS Workload Identity Atlas** (`mongodb-f97232ad0e66206d`): AKS Workload Identity Atlas
- **Analytics Node Configuration** (`mongodb-262ad4fee8a0d3a2`): Analytics Node Configuration
- **Analytics Node Cost Model** (`mongodb-71388a8b9ab23deb`): Analytics Node Cost Model
- **Analytics Node Monitoring** (`mongodb-68ba174c54c90f40`): Analytics Node Monitoring
- **Analytics Node Read Preference Routing** (`mongodb-e6e8207e8a7a8f77`): Analytics Node Read Preference Routing
- **Analytics Node Sizing** (`mongodb-2bc83b7cddf40837`): Analytics Node Sizing
- **Anti-Patterns** (`mongodb-bd4f98e02c8fd2ba`): Anti-Patterns
- **App Services Authentication Providers** (`mongodb-9dc308ee4e93b818`): App Services Authentication Providers
- **App Services Billing Model** (`mongodb-d441367b53e6a6ea`): App Services Billing Model
- **App Services CLI Deployment** (`mongodb-674f8ead0248faf5`): App Services CLI Deployment
- **App Services Context** (`mongodb-bd0b58dddd2d44e8`): App Services Context
- **Application Thread Eviction** (`mongodb-4f1590a7780165f9`): Application Thread Eviction
- **Archive Data Expiration Rule** (`mongodb-0673dc063bfc34db`): Archive Data Expiration Rule
- **Archive Rules** (`mongodb-abb23c2fcc0eecda`): Archive Rules; CUSTOM Criteria; CUSTOM criteria; DATE Criteria; DATE criteria; archive criteria; archiving rule; online archive criteria
- **Archive Schedule Window** (`mongodb-677db6ffd1141b6c`): Archive Schedule Window
- **ASP Pricing Model** (`mongodb-11999eb2a03ea8ae`): ASP Pricing Model
- **Asymmetric Sync** (`mongodb-42bc5bef574d1e55`): Asymmetric Sync
- **Atlas Admin API GCP Auth** (`mongodb-e886038e08a67354`): Atlas Admin API GCP Auth
- **Atlas Billing Mechanics and Cost Visibility** (`mongodb-ec0a578f0eb2dc5d`): Atlas Billing Mechanics and Cost Visibility; Atlas GCP EDP Credits; Azure Marketplace Atlas Billing; Billing and Cost Chargeback; GCP Marketplace Atlas Billing
- **Atlas CLI** (`mongodb-a7bc654c500d19b5`): Atlas CLI; atlas-cli
- **Atlas CLI Architecture Internals** (`mongodb-488676e149ba5e07`): Atlas CLI Architecture Internals
- **Atlas CLI Benchmark Metrics** (`mongodb-aaf92a3088d37352`): Atlas CLI Benchmark Metrics
- **Atlas CLI Integration** (`mongodb-34b5f50a54f6af8c`): Atlas CLI Integration
- **Atlas CLI Operational Runbook** (`mongodb-babaf9be081def8f`): Atlas CLI Operational Runbook
- **Atlas cluster tiers (M30) & major-version upgrade mechanics** (`mongodb-bd98132165e458ac`): Atlas cluster tiers (M30) & major-version upgrade mechanics
- **Atlas Cluster Topology and Tier Economics** (`mongodb-f02eb728afc162ae`): Atlas Cluster Topology and Tier Economics; Cluster Tier Selection; Cross-Cloud Egress Costs; IOPS Forecasting; Multi-Cloud Billing; Storage Growth Modeling
- **Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO** (`mongodb-a8fd0dad11275233`): Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO
- **Atlas Data API Removal** (`mongodb-b8d223fac8273b92`): Atlas Data API Removal
- **Atlas Device Sync** (`mongodb-24f749b60d402d1e`): Atlas Device Sync
- **Atlas Diagnostics Expert** (`mongodb-32d05cbbbc3150df`): Atlas Diagnostics Expert
- **Atlas Edge Server** (`mongodb-2c1c20eb6f74a631`): Atlas Edge Server
- **Atlas Federated Authentication** (`mongodb-fe7205d4ca6c3a2a`): Atlas Federated Authentication
- **Atlas federated database users and groups** (`mongodb-cceff9ec02a17c68`): Atlas federated database users and groups
- **Atlas Gen2 ARM hardware** (`mongodb-4b35526ea0916bdf`): Atlas Gen2 ARM hardware
- **Atlas Hybrid Fusion and BM25 Diagnostics** (`mongodb-f60c2cad96d8d584`): Atlas Hybrid Fusion and BM25 Diagnostics; Hybrid Search $rankFusion $scoreFusion; Score Details BM25 Diagnostics
- **Atlas Identity Federation and Resource Policy Boundaries** (`mongodb-ec74c98d2fde7766`): Atlas Identity Federation and Resource Policy Boundaries; Atlas Service Accounts OAuth 2.0; Atlas Workforce Identity Federation; Atlas Workload Identity Federation
- **Atlas IP access list for service accounts** (`mongodb-664ae25217ab095b`): Atlas IP access list for service accounts
- **Atlas Kubernetes Operator** (`mongodb-8daaf32ff1a623b5`): Atlas Kubernetes Operator
- **Atlas Maintenance Windows** (`mongodb-fd040a9441e59b87`): Atlas Maintenance Windows
- **Atlas org mapping and domain mapping** (`mongodb-5fc4c002f30111da`): Atlas org mapping and domain mapping
- **Atlas Performance Advisor Auto-Index Evaluation** (`mongodb-92018eec3af52069`): Atlas Performance Advisor Auto-Index Evaluation
- **Atlas Pricing Programs, Cost Governance and TCO** (`mongodb-1c09ff0246754264`): Atlas Flex Pricing Model; Atlas Pricing Programs, Cost Governance and TCO; Flex Cost Break-Even Analysis; Flex vs Dedicated Decision Matrix; M0 Free Tier vs Flex Comparison; M2 M5 Migration to Flex; Serverless Deprecation and EOL; Serverless RPU WPU Billing
- **Atlas Query Insights, Performance Advisor and Compass explain** (`mongodb-154cc13095e07b0f`): Atlas Query Insights, Performance Advisor and Compass explain
- **Atlas Resource Policies Cedar** (`mongodb-df465182d1c8eca3`): Atlas Resource Policies Cedar
- **Atlas Service Accounts** (`mongodb-85937d1cb788be53`): Atlas Service Accounts
- **Atlas Slow-Query Log and Performance Advisor Automation** (`mongodb-e376edb94808f3e8`): Admin API listSuggestedIndexes automation; Atlas CLI/Admin API slow query log download; Atlas Performance Advisor MCP server access; Atlas Slow-Query Log and Performance Advisor Automation; Atlas Slow-Query Log and Performance Advisor Automation (managedSlowMs and Admin API listSuggestedIndexes and Atlas CLI); Atlas-managed slow operation threshold (managedSlowMs)
- **Atlas SQL Interface MongoSQL** (`mongodb-1d64e1de328a67b4`): Atlas SQL Interface MongoSQL
- **Atlas storage auto-scaling and disk reclaim via compact** (`mongodb-6768a2c67c76d1dc`): Atlas storage auto-scaling and disk reclaim via compact
- **Atlas Triage Workflows** (`mongodb-d4ed85cc09916e0c`): Atlas Triage Workflows; atlas-triage-workflows
- **autoCompact and Replica-Set Write Blocking** (`mongodb-a792e0075d93fa17`): RSWB; autoCompact and Replica-Set Write Blocking; blockReplicaSetWrites
- **autoCompact Atlas-Specific Behavior** (`mongodb-c6eeffd1ee4b2393`): autoCompact Atlas-Specific Behavior
- **autoCompact Checkpoint Interaction** (`mongodb-522ba776d46ae0c8`): autoCompact Checkpoint Interaction
- **autoCompact Cluster Topology Behavior** (`mongodb-b56aa0302376fb8d`): autoCompact Cluster Topology Behavior
- **autoCompact freeSpaceTargetMB Gating** (`mongodb-6f17722ce708d8a3`): autoCompact freeSpaceTargetMB Gating; freeSpaceTargetMB
- **autoCompact Lifecycle and Persistence** (`mongodb-9ea0452e80b9982d`): autoCompact Lifecycle and Persistence; enableAutoCompaction
- **autoCompact runOnce vs Continuous Mode** (`mongodb-54e6a74148d5054b`): autoCompact runOnce vs Continuous Mode; runOnce mode
- **Automated Cluster Scaling Decision Matrix** (`mongodb-02a739f81f2dba23`): Automated Cluster Scaling Decision Matrix
- **AWS CDK awscdk-resources-mongodbatlas** (`mongodb-d27540a689a3a4e5`): AWS CDK awscdk-resources-mongodbatlas
- **AWS CloudFormation Atlas** (`mongodb-6f17a3a9fd8a1a21`): AWS CloudFormation Atlas
- **AWS CloudFormation Atlas Resources** (`mongodb-cf4a15d60c7d898e`): AWS CloudFormation Atlas Resources
- **AWS IAM Outbound Identity Federation to Atlas** (`mongodb-8aae2ca5ac6e5526`): AWS IAM Outbound Identity Federation to Atlas
- **AWS ISV Accelerate** (`mongodb-9ba8340966b4c566`): AWS ISV Accelerate
- **AWS Marketplace Atlas** (`mongodb-0e236aa44bc9adfb`): AWS Marketplace Atlas
- **AWS PrivateLink** (`mongodb-f765a506ff704a94`): AWS PrivateLink
- **Background-Compaction Skip/EMA Heuristic** (`mongodb-d9214cdc09926575`): Background-Compaction Skip/EMA Heuristic; exclude_list_hash; stat_hash
- **Backup Compliance Policy (WORM)** (`mongodb-75efa613e85ade94`): Backup Compliance Policy (WORM)
- **Backup Cost Optimization** (`mongodb-7bfd95f59408a1e8`): Backup Cost Optimization
- **BI Connector to MongoSQL Migration** (`mongodb-f5aac39490db6993`): BI Connector to MongoSQL Migration
- **Block Manager and Page Sizing** (`mongodb-0f3bfdc0c942271f`): Block Manager and Page Sizing
- **Bucket catalog memory and closure reasons** (`mongodb-b8addb216a7bee1b`): Bucket catalog memory and closure reasons; Bucket catalog memory cap
- **Bucket fragmentation remediation (re-insert/merge)** (`mongodb-c3170175fcc240d3`): Bucket fragmentation remediation (re-insert/merge)
- **Bypass SAML mode** (`mongodb-b45d395a0074e230`): Bypass SAML mode
- **Cache Architecture** (`mongodb-c7beb93cd2c0d639`): Cache Architecture
- **Causal Consistency** (`mongodb-843f99f1b7d05473`): Causal Consistency
- **CDC-patterns** (`mongodb-cef2943f21061547`): CDC-patterns
- **Chart Types** (`mongodb-2fb8aa2db6b1b551`): Chart Types
- **Charts REST API** (`mongodb-3a507ba47df577e6`): Charts REST API
- **Checkpoint Mechanism** (`mongodb-57c87ac0cd7280f3`): Checkpoint Mechanism
- **Client Reset Strategies** (`mongodb-d61a2ca066c48e08`): Client Reset Strategies
- **client sessions** (`mongodb-79ef1c830d0d6cc6`): client sessions
- **Client Side Operations Timeout (CSOT)** (`mongodb-ca5ecb9417a4a139`): Client Side Operations Timeout (CSOT); client-side-operations-timeout-csot
- **Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit)** (`mongodb-be046d9ee7a6b5e5`): Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit)
- **Cluster Pause** (`mongodb-a9cc495fd226843f`): Cluster Pause
- **clusterTime** (`mongodb-6ebc285cd5958857`): clusterTime
- **CMAP Connection Pooling** (`mongodb-671791dc026cfa62`): CMAP Connection Pooling
- **Common Cost Overruns** (`mongodb-7d2fce1414e05788`): Common Cost Overruns
- **Connected organizations** (`mongodb-1f5add0f549c8718`): Connected organizations
- **Connection Troubleshooting** (`mongodb-7b65d7319e700f46`): Connection Troubleshooting
- **Connection URI server-selection options** (`mongodb-4b44dc3f37e36c18`): Connection URI server-selection options
- **Corruption (validate, --repair, wt CLI)** (`mongodb-e70910f7c3630d2f`): Corruption (validate, --repair, wt CLI)
- **Cost Model** (`mongodb-8259d66843cc0fd4`): Cost Model
- **Cost Monitoring** (`mongodb-a945e340f12f5724`): Cost Monitoring
- **Covered queries on sharded collections** (`mongodb-38d6ec0926ba83dd`): Covered queries on sharded collections; Index-only plans on sharded collections
- **Crash Stack Trace Symbolization** (`mongodb-f52f060df62a7687`): Crash Stack Trace Symbolization
- **cross-service causal tokens** (`mongodb-5b5664ae3196b1dd`): cross-service causal tokens
- **Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB)** (`mongodb-5dd92e0129ef797b`): Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB)
- **Custom server selectors** (`mongodb-1ac42abe4981149f`): Custom server selectors
- **Customer Hotfix & Patch Verification** (`mongodb-5e93ec31dd299572`): Customer Hotfix & Patch Verification
- **Dashboards** (`mongodb-21b2e2095fd38f7d`): Dashboards
- **Data Sources** (`mongodb-8b34ea9b008b22f6`): Data Sources
- **Database Profiler vs Query Profiler** (`mongodb-4ff40d38200310ce`): Database Profiler vs Query Profiler; Query Profiler vs slow query log
- **DATE criteria date format specifications** (`mongodb-7af7cc2097f5e3b0`): DATE criteria date format specifications
- **DATE vs CUSTOM criteria selection** (`mongodb-9eb84447516f20f2`): DATE vs CUSTOM criteria selection
- **Delayed-member lag interpretation** (`mongodb-c126c65d94746629`): Delayed-member lag interpretation
- **Delbridge Data API** (`mongodb-2e4b5c89e48ca365`): Delbridge Data API
- **Diagnostic Tool Design** (`mongodb-1de388843e62fcd6`): Diagnostic Tool Design; diagnostic-tool-design
- **Domain verification** (`mongodb-73258602dbad6863`): Domain verification
- **Driver Examples** (`mongodb-5c1f18de01ee9047`): Driver Examples
- **Driver Examples (Node.js, Python, Java)** (`mongodb-a6f364c5f8a0c9ff`): Driver Examples (Node.js, Python, Java)
- **EDP Credits** (`mongodb-a127feda7fd2f608`): EDP Credits
- **Elastic Compute Autoscaling** (`mongodb-a74da6f7e2c3d733`): Elastic Compute Autoscaling
- **Embedded Charts** (`mongodb-152576444a4c5fab`): Embedded Charts
- **Embedding SDK** (`mongodb-6dc8464fb0082141`): Embedding SDK
- **Emergency Security Patches** (`mongodb-992034152809181b`): Emergency Security Patches
- **Encryption at Rest (KMIP, AES-256-CBC/GCM)** (`mongodb-23df1e3067aaf9e3`): Encryption at Rest (KMIP, AES-256-CBC/GCM)
- **Error Code Hierarchy & Assertion Types** (`mongodb-2d6019b19e7d2f56`): Error Code Hierarchy & Assertion Types
- **Error Codes and Troubleshooting** (`mongodb-20120b43be1ba061`): Error Codes and Troubleshooting; error-codes-and-troubleshooting
- **Error Codes and Troubleshooting Architecture Internals** (`mongodb-5bd16d907803a5ca`): Error Codes and Troubleshooting Architecture Internals
- **Error Codes and Troubleshooting Failure Scenarios** (`mongodb-4e6c17011410eba6`): Error Codes and Troubleshooting Failure Scenarios
- **Error Codes and Troubleshooting Operational Runbook** (`mongodb-9d57284dbfa4fe1f`): Error Codes and Troubleshooting Operational Runbook
- **EventBridge Integration** (`mongodb-523f5a7d2b8b3988`): EventBridge Integration
- **Eviction (clean/dirty targets and triggers)** (`mongodb-4a91a4d100d89d02`): Eviction (clean/dirty targets and triggers)
- **expireAfterDays data age calculation** (`mongodb-3b6fab8176a85940`): expireAfterDays data age calculation
- **express execution path** (`mongodb-ec9369fccf27c14f`): express execution path
- **Express MongoDB Driver Pattern** (`mongodb-2e0ab631ade8fb5a`): Express MongoDB Driver Pattern
- **FastAPI Motor Pattern** (`mongodb-107085c4770bb819`): FastAPI Motor Pattern
- **FCV pinning no-downgrade rule** (`mongodb-ece4323e7d028cce`): FCV pinning no-downgrade rule
- **Feature Compatibility Version (FCV)** (`mongodb-1d99576a052ddc19`): Feature Compatibility Version (FCV)
- **Federated database user mapping by sub/groups claim** (`mongodb-9b4c1c6850f6b852`): Federated database user mapping by sub/groups claim
- **Federation Management Console** (`mongodb-5897e8605ddc8f1b`): Federation Management Console
- **FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets)** (`mongodb-16e20a3f088ac2a9`): FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets)
- **Flexible Sync Subscriptions** (`mongodb-43cb9a137cfc5fb7`): Flexible Sync Subscriptions
- **Flutter Dart Realm SDK** (`mongodb-21bd1e9aedd5a916`): Flutter Dart Realm SDK
- **FTDC and Log Tooling** (`mongodb-c330c7ad3dbb4973`): FTDC and Log Tooling; ftdc-and-log-tooling
- **FTDC Chunk Decompression & Stream Parsing** (`mongodb-6beb52caa7d1dd8d`): FTDC Chunk Decompression & Stream Parsing
- **FTDC Diagnostics** (`mongodb-228f8507dd05bcad`): FTDC Diagnostics
- **Group-to-role mapping** (`mongodb-95a078352bed4b5c`): Group-to-role mapping
- **Hashed shard-key index drop operational procedure** (`mongodb-200bb9edc4ba9e81`): Hashed shard-key index drop operational procedure
- **Hidden indexes and safe index removal** (`mongodb-609badcaf87b7613`): Hidden indexes and safe index removal; Hidden indexes as a drop trial; Hide-before-drop index workflow; Index pruning with hideIndex; Safe index-drop workflow with $indexStats; collMod index.hidden option
- **History Store (WiredTigerHS.wt)** (`mongodb-bfafea97a78c1527`): History Store (WiredTigerHS.wt)
- **IAM Authentication** (`mongodb-6b78ce8c09961ff1`): IAM Authentication
- **IdP configuration (Entra ID)** (`mongodb-c3c59d1f9932f3c3`): IdP configuration (Entra ID)
- **IdP configuration (Okta)** (`mongodb-24eff80c4c62e719`): IdP configuration (Okta)
- **implicit vs explicit sessions** (`mongodb-034f5ee1db88a5ec`): implicit vs explicit sessions
- **In-Memory Storage Engine (Enterprise)** (`mongodb-8335c55994660ad1`): In-Memory Storage Engine (Enterprise)
- **Independent shard scaling and per-shard tiering** (`mongodb-9d8df542323c0990`): Independent shard scaling and per-shard tiering
- **Index build resource limits (maxNumActiveUserIndexBuilds, disk space)** (`mongodb-3b6c6a7068545b0a`): Index build resource limits (maxNumActiveUserIndexBuilds, disk space)
- **Index Storage Cost** (`mongodb-9353f1302dc6a63b`): Index Storage Cost
- **Instance Right-Sizing** (`mongodb-efa603712ff70817`): Instance Right-Sizing
- **kafka-sink-connector** (`mongodb-f69bb4e05603c157`): kafka-sink-connector
- **kafka-source-connector** (`mongodb-d3ba6c9508b840b8`): kafka-source-connector
- **KB-Backed Troubleshooting** (`mongodb-c59681d79f02ca60`): KB-Backed Troubleshooting; kb-backed-troubleshooting
- **KMS Encryption at Rest** (`mongodb-abbd574f8b4f6308`): KMS Encryption at Rest
- **Lambda Integration** (`mongodb-23773a9ccc0dd1ea`): Lambda Integration
- **Local embeddings from Ollama into MongoDB Atlas Vector Search** (`mongodb-8defc62f5cb087c6`): Local Ollama embeddings into MongoDB Atlas Vector Search; Local embeddings from Ollama into MongoDB Atlas Vector Search
- **Lock-Free Diagnostic Sampling Engine** (`mongodb-17ee9e52ae9a80fc`): Lock-Free Diagnostic Sampling Engine
- **Long-running secondary reads in sharded clusters** (`mongodb-94f83939c307dfab`): Long-running secondary reads in sharded clusters
- **Maintenance Window Configuration** (`mongodb-aea2a23d9000a57e`): Maintenance Window Configuration
- **MongoDB 8.0 performance changes & read-path regressions vs 7.0** (`mongodb-80399f0419458499`): MongoDB 8.0 performance changes & read-path regressions vs 7.0
- **MongoDB 8.1–9.0 query-engine changes and AI-assisted optimization** (`mongodb-7e9d87202a40db4f`): MongoDB 8.1–9.0 query-engine changes and AI-assisted optimization
- **MongoDB Aggregation Pipeline** (`mongodb-eb7440ed73ebb525`): MongoDB Aggregation Pipeline
- **MongoDB Atlas Analytics Node** (`mongodb-0c218fe88169f5d0`): MongoDB Atlas Analytics Node
- **MongoDB Atlas App Services** (`mongodb-da368bc1b1718f60`): MongoDB Atlas App Services
- **MongoDB Atlas AWS Networking** (`mongodb-8f00e0773601581e`): MongoDB Atlas AWS Networking
- **MongoDB Atlas Charts** (`mongodb-556521c5102a7035`): MongoDB Atlas Charts
- **MongoDB Atlas Data Federation** (`mongodb-c682bbc6e08dff15`): MongoDB Atlas Data Federation; mongodb-atlas-data-federation
- **MongoDB Atlas Device SDK** (`mongodb-d4913ed99caa7acf`): MongoDB Atlas Device SDK
- **MongoDB Atlas Flex and Serverless Tiers** (`mongodb-87a1b56071ba8e79`): MongoDB Atlas Flex and Serverless Tiers
- **MongoDB Atlas IAM and RBAC** (`mongodb-2a18158aab1e0ce9`): MongoDB Atlas IAM and RBAC
- **MongoDB Atlas Infrastructure as Code** (`mongodb-7f0bc3386c3cfd8b`): MongoDB Atlas Infrastructure as Code
- **MongoDB Atlas Multi-Cloud** (`mongodb-2ad1f3e8db138156`): MongoDB Atlas Multi-Cloud
- **MongoDB Atlas on Azure** (`mongodb-4362c5de231ad0b8`): MongoDB Atlas on Azure
- **MongoDB Atlas on GCP** (`mongodb-da2535cf778aad03`): MongoDB Atlas on GCP
- **MongoDB Atlas Online Archive** (`mongodb-9ca12ad4a2a55aaa`): MongoDB Atlas Online Archive
- **MongoDB Atlas Search** (`mongodb-d30b646ec919335a`): MongoDB Atlas Search
- **MongoDB Atlas Search and Vector Search** (`mongodb-c94ff8c08bc870a1`): MongoDB Atlas Search and Vector Search
- **MongoDB Atlas Stream Processing** (`mongodb-5aaacfe7c169738f`): MongoDB Atlas Stream Processing
- **MongoDB Atlas Terraform Provider** (`mongodb-d6ee217e654b410c`): MongoDB Atlas Terraform Provider
- **MongoDB Atlas Triggers and Functions** (`mongodb-e3778c0687095883`): MongoDB Atlas Triggers and Functions
- **MongoDB Atlas Vector Search** (`mongodb-eb6e21870ec0d43f`): MongoDB Atlas Vector Search
- **MongoDB autoCompact** (`mongodb-a4a89b2c0375d071`): MongoDB autoCompact; autoCompact; background compaction; mongodb background compaction
- **MongoDB Backup and Restore** (`mongodb-9f201994ae74aeb1`): MongoDB Backup and Restore
- **MongoDB BI Connector and SQL Access** (`mongodb-6fb7d57635185dec`): MongoDB BI Connector and SQL Access
- **MongoDB Capacity Planning** (`mongodb-e79ef560ba113458`): MongoDB Capacity Planning
- **MongoDB Compass** (`mongodb-a8a3eca1b42bebf9`): MongoDB Compass
- **MongoDB Compliance and Regulatory** (`mongodb-b4029353663df095`): MongoDB Compliance and Regulatory
- **MongoDB Connection String URI** (`mongodb-4d0d315c971c60dc`): MongoDB Connection String URI
- **MongoDB counts, distinct, cursors and read-path tuning** (`mongodb-262d81b09119103b`): MongoDB counts, distinct, cursors and read-path tuning
- **MongoDB Driver Internals** (`mongodb-09f41dedaf4ff2a9`): MongoDB Driver Internals
- **MongoDB Drivers** (`mongodb-b5639184c589a4f1`): MongoDB Drivers; mongodb-drivers
- **MongoDB Expert Knowledge** (`mongodb-dc4652d79c189fda`): MongoDB Expert Knowledge
- **MongoDB explain output and plan stages** (`mongodb-3f315f711f232495`): MongoDB explain output and plan stages
- **MongoDB Geospatial** (`mongodb-6453f397fc07845d`): MongoDB Geospatial
- **MongoDB Indexes Deep Dive** (`mongodb-eec8bc76b4102aeb`): MongoDB Indexes Deep Dive
- **MongoDB Java driver 5.x version timeline & 8.0 compatibility** (`mongodb-0c6fc1af14b63ca6`): MongoDB Java driver 5.x version timeline & 8.0 compatibility
- **MongoDB Migration Patterns** (`mongodb-ea34d2ef9b0ee2e2`): MongoDB Migration Patterns
- **MongoDB Multi-Tenancy** (`mongodb-7f85982396e902de`): MongoDB Multi-Tenancy
- **MongoDB Ops Manager and Cloud Manager** (`mongodb-96e1a35a7841f4c4`): MongoDB Ops Manager; MongoDB Ops Manager and Cloud Manager
- **MongoDB Performance Benchmarking** (`mongodb-c2e8019b44ddddf1`): MongoDB Performance Benchmarking
- **MongoDB Performance Regression Detection and Testing Methodology** (`mongodb-ab8aecd20ee36a07`): MongoDB Performance Regression Detection and Testing Methodology
- **MongoDB Performance Troubleshooting** (`mongodb-9a5d6d6d6827148c`): MongoDB Performance Troubleshooting
- **MongoDB query operators, index bounds and projection** (`mongodb-42e536762602a59e`): MongoDB query operators, index bounds and projection
- **MongoDB query planner, plan cache, query settings and hints** (`mongodb-2f2a5be1b2da781d`): MongoDB query planner, plan cache, query settings and hints
- **MongoDB query shapes, $queryStats, profiler and index usage** (`mongodb-c57ec995ff8897ba`): MongoDB query shapes, $queryStats, profiler and index usage
- **MongoDB Security Architecture** (`mongodb-f507563a402a0ad1`): MongoDB Security Architecture
- **MongoDB sharded query targeting and scatter-gather** (`mongodb-8af4304f26ef1ec4`): MongoDB sharded query targeting and scatter-gather
- **MongoDB sort and pagination optimization** (`mongodb-781e2940b232df7a`): MongoDB sort and pagination optimization
- **MongoDB Spark Connector and Databricks Integration** (`mongodb-f78f0e85b6a1f92b`): MongoDB Spark Connector and Databricks Integration
- **MongoDB Stress, Soak, and Chaos-Resilience Testing** (`mongodb-041e0c13bb9aac86`): MongoDB Stress, Soak, and Chaos-Resilience Testing
- **MongoDB time-series indexes and metaField design** (`mongodb-4cbfdee9d2ba94ad`): MongoDB time-series indexes and metaField design
- **MongoDB time-series query execution: bucket unpacking, pushdown, block processing and sorts** (`mongodb-d500cf438d3af2c4`): MongoDB time-series query execution: bucket unpacking, pushdown, block processing and sorts
- **MongoDB time-series working-set sizing and sharding** (`mongodb-07988e9f6014b1b5`): MongoDB time-series working-set sizing and sharding
- **MongoDB Transactions** (`mongodb-7cd4e3fd0187cf62`): MongoDB Transactions
- **MongoDB University & Certification** (`mongodb-1f6aa91076f943b7`): MongoDB University & Certification
- **MongoDB Upgrade Paths** (`mongodb-86aa03976ec73ced`): MongoDB Upgrade Paths
- **mongodb-aggregation-stages-deep** (`mongodb-7561b186c6e471e6`): mongodb-aggregation-stages-deep
- **mongodb-kafka-connector** (`mongodb-92f35f5be19ae362`): mongodb-kafka-connector
- **mongodb-time-series** (`mongodb-fbd0374990470468`): mongodb-time-series
- **mongosh Reference** (`mongodb-dbc7aadec9256534`): mongosh Reference; mongosh-reference
- **mongosync** (`mongodb-958dc624e2c09e75`): mongosync
- **monotonic reads** (`mongodb-3dd8c7bf86af242a`): monotonic reads
- **Multi-Region Networking** (`mongodb-7097fbebc4708bef`): Multi-Region Networking
- **Network Access Lists** (`mongodb-609fea60016274cd`): Network Access Lists
- **Network Connection Quota Management** (`mongodb-592d3bed474645cc`): Network Connection Quota Management
- **Network Egress Costs** (`mongodb-46f4ba9e4d35a78d`): Network Egress Costs
- **OAuth2 Token Exchange** (`mongodb-8ff2fca20bb91f4d`): OAuth2 Token Exchange
- **Offline-First Mobile** (`mongodb-401c4a76e57ae999`): Offline-First Mobile
- **Online Archive Terraform Resource** (`mongodb-57b0914128263b0b`): Online Archive Terraform Resource
- **Operation rejection filters** (`mongodb-2375ce8f6f277a5f`): $querySettings and operation rejection filters; Operation rejection filters
- **operationTime** (`mongodb-7cf47829ba125213`): operationTime
- **Oplog recovery headroom** (`mongodb-a447350cf5aec261`): Oplog recovery headroom
- **Oplog sizing under storage auto-scaling** (`mongodb-46a4716e7a6433db`): Oplog sizing under storage auto-scaling
- **Partition fields constraints for DATE rules** (`mongodb-7a16fd3b3f34bed7`): Partition fields constraints for DATE rules
- **Per-member replica-set telemetry** (`mongodb-79ef674093040e91`): Per-member replica-set telemetry
- **Performance Impact** (`mongodb-28b4bd53f636eb61`): Performance Impact
- **Pipeline Stages Reference** (`mongodb-1d122188c9ebb713`): Pipeline Stages Reference
- **Quick Reference** (`mongodb-3c499e58c814c120`): Quick Reference
- **Read Concern Levels** (`mongodb-009186a648efd71f`): Read Concern Levels
- **Read preference candidate filtering** (`mongodb-ca8db90f991faa1e`): Read preference candidate filtering
- **Read/Write Tickets and Dynamic Concurrency (7.0+)** (`mongodb-9c79810008e280ae`): Read/Write Tickets and Dynamic Concurrency (7.0+)
- **Realm Authentication** (`mongodb-e301087117871b13`): Realm Authentication
- **Replanning loops and replanReason** (`mongodb-30415c27b3855b8e`): Replanning loops and replanReason
- **Replica-set election timing** (`mongodb-3b1f8ec06b415716`): Replica-set election timing
- **Request Hedging** (`mongodb-fc366b256408dc3a`): Request Hedging
- **Reserved Capacity and Committed Use** (`mongodb-4f0751f139c14bc9`): Reserved Capacity and Committed Use
- **RESTHeart** (`mongodb-d1d29980f15ac9cd`): RESTHeart
- **Resumable index builds** (`mongodb-38b8ca0a9c31a684`): Index build resumability and checkpoints; Resumable index builds
- **Retryable Transactions** (`mongodb-575253db176be40a`): Retryable Transactions
- **Retryable Writes** (`mongodb-411ea1b79cd3d9a6`): Retryable Writes
- **Rolling index builds** (`mongodb-7a208c1080d7ff65`): Rolling index builds; Rolling index builds on sharded clusters
- **Rolling Maintenance Procedure** (`mongodb-14ad0ee240d2c19e`): Rolling Maintenance Procedure
- **rolling upgrade & elections** (`mongodb-347239e47edf011a`): rolling upgrade & elections
- **SAML 2.0 SSO flow** (`mongodb-0679195dd0d6e3a8`): SAML 2.0 SSO flow
- **SCIM provisioning** (`mongodb-a434424f8bc980a7`): SCIM provisioning
- **SDAM Topology State Machine** (`mongodb-17a2e4c144379fe7`): SDAM Topology State Machine
- **Secret Rotation** (`mongodb-b0f6d552f5d3c5c3`): Secret Rotation
- **Server Discovery and Monitoring RTT estimates** (`mongodb-83f010c5d622244a`): Server Discovery and Monitoring RTT estimates
- **Server Selection Timeout** (`mongodb-80e31966ebba1804`): Server Selection Timeout
- **Server selection timeout and retry loop** (`mongodb-f01a13d18bcefb78`): Server selection timeout and retry loop
- **Service Account Roles** (`mongodb-8025e6527692a546`): Service Account Roles
- **Service account secret rotation** (`mongodb-cc5e4137c9df3795`): Service account secret rotation
- **Sharded Cluster Maintenance** (`mongodb-07cc6b06c2c46dd0`): Sharded Cluster Maintenance
- **Sharded cluster upgrade ordering** (`mongodb-513796e13072db9d`): Sharded cluster upgrade ordering
- **SORT_MERGE and $in sort expansion** (`mongodb-f61df09438da5790`): $in expansion and SORT_MERGE; Planner bound unionizing and large $in lists; SORT_MERGE and $in sort expansion; SORT_MERGE and sorted index unions
- **Storage Autoscaling** (`mongodb-653d0658dabf3057`): Storage Autoscaling
- **Storage Tier Selection** (`mongodb-8f64c1c8bb6ab545`): Storage Tier Selection
- **Streaming BSON Parser Architecture** (`mongodb-a3e7c369fce3bfa5`): Streaming BSON Parser Architecture
- **Tableau Certified Connector** (`mongodb-70df650d1113356a`): Tableau Certified Connector
- **Tail Latency Mitigation** (`mongodb-4cd9d534d8543a75`): Tail Latency Mitigation
- **TCMalloc per-CPU caches** (`mongodb-ae31ebaa35d5b251`): TCMalloc per-CPU caches
- **Telemetry Overhead Bounding Algorithms** (`mongodb-e96d332c5de93342`): Telemetry Overhead Bounding Algorithms
- **Terraform Atlas Provider** (`mongodb-bffe1ca63b393cda`): Terraform Atlas Provider
- **Terraform Integration** (`mongodb-f4b73604aa414b46`): Terraform Integration
- **Terraform mongodbatlas_service_account without initial secret** (`mongodb-261812fb389c1774`): Terraform mongodbatlas_service_account without initial secret
- **Tier 0 Tier 1 Tier 2 Strategy** (`mongodb-7488d401a7edfbd7`): Tier 0 Tier 1 Tier 2 Strategy
- **Time Series Aggregation** (`mongodb-74dc31678aaf78f5`): Time Series Aggregation
- **Time Series Archive Rules** (`mongodb-81b8255a01a53f88`): Time Series Archive Rules
- **TLS Encryption** (`mongodb-6db52addffe1c42e`): TLS Encryption
- **Transaction Limits** (`mongodb-2d54318676631383`): Transaction Limits
- **Transit Gateway Patterns** (`mongodb-ab46cce297c8e878`): Transit Gateway Patterns
- **Unique index requirements when refining a shard key** (`mongodb-b18c286cad9fa994`): Unique index requirements when refining a shard key
- **Unused index detection with $indexStats** (`mongodb-ebcd4a1bc6d468ab`): $indexStats usage analysis; Redundant and unused index pruning with $indexStats; Redundant-prefix index detection; Unused index detection with $indexStats
- **VPC Peering** (`mongodb-9b0f510e32ca1aa1`): VPC Peering
- **Window Functions ($setWindowFields)** (`mongodb-a8d6bcf31db610d2`): Window Functions ($setWindowFields)
- **WiredTiger cache eviction and dirty ratio** (`mongodb-a3037242ece82ce3`): WiredTiger cache eviction and dirty ratio; WiredTiger cache eviction monitoring for time series
- **WiredTiger Compaction Algorithm** (`mongodb-cfae06f226515122`): WiredTiger Compaction Algorithm
- **WiredTiger Storage Engine Internals** (`mongodb-60cddea0ba910cbf`): WiredTiger Storage Engine Internals
- **WiredTiger Ticket Metric Telemetry in FTDC** (`mongodb-5b109c1f1f910a9c`): WiredTiger Ticket Metric Telemetry in FTDC
- **wiredTigerEngineRuntimeConfig** (`mongodb-7e9d8c680e7b3cdf`): wiredTigerEngineRuntimeConfig
<!-- mongodb-research-inventory:end -->
