<!-- mongodb-research-inventory:start -->
# MongoDB research queue and coverage inventory

Scores are priority judgments with provenance; source URLs are discovery leads. Unscored concepts await real scoring. The legacy 3.2 cutoff does not filter this view.

Canonical rows: **461**; gaps/reviews: **336**; unscored gaps: **11**; held: **0**.

## Source-sharing cohorts

Every gap and review candidate appears below, including held, low-scored and unscored concepts.

| cohort | source family / affinity | members · CVS | shared discovery sources |
|---|---|---|---|
| mongodb-cohort-a17745affdcc | mongodb-general / parent:read offload via caching and precomputed views ($merge/$out, computed pattern) | Delete propagation and reconciliation for $merge-maintained views (CVS 4.375); Idempotent incremental refresh design for $merge (high-water marks, delete handling) (CVS 4.350); Atlas Stream Processing streaming materialized views (CVS 4.025); Cache stampede protection: leases, request coalescing, TTL jitter (CVS 3.900) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-c53f316f2ab7 | query-index-planner / index-design | Index build commit quorum and hung builds (CVS 4.350); Unique and TTL index side effects on removal (CVS 4.275); Index filters (planCacheSetFilter) deprecation and migration to query settings (CVS 4.275); Query settings: index hints and queryFramework (persistent query settings) (CVS 4.250) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-494e1aa39f55 | query-index-planner / query-shape | $queryStats and $currentOp as alternatives to the profiler (CVS 4.350); Atlas Query Profiler and slow-ops logs for shape discovery (CVS 4.250); Query shape and queryShapeHash stability (CVS 4.150); Query shapes and queryShapeHash stability (CVS 4.150) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-6047f9cce83c | storage-wiredtiger / parent:oplog sizing under storage auto-scaling | Atlas storage auto-scaling triggers, cooldowns and write blocking (CVS 4.300); replSetResizeOplog and oplog compaction on self-managed replica sets (CVS 3.775); EBS volume modification limits and Atlas disk resize mechanics (CVS 3.450); Atlas Infinite oplog and storage-layer replication (CVS 3.300) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-99501ef9834d | storage-wiredtiger / parent:atlas storage auto-scaling and disk reclaim via compact | Oplog minimum retention window and storage auto-scaling (CVS 4.275); Atlas disk write-blocking thresholds and recovery (CVS 4.225); WiredTiger block reuse, file fragmentation and freeStorageSize (CVS 3.950); Archive and TTL data lifecycle followed by compaction (CVS 3.950) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-47b75166139c | replication-transactions / replication | Read concern available, secondary reads and orphaned documents (CVS 4.275); Oplog capacity for initial sync, live migration and bulk loads (CVS 4.250); Per-node and per-shard $indexStats aggregation across replica sets and shards (CVS 4.175); Orphaned documents and read concern available versus local (CVS 4.075) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-99762008d157 | storage-wiredtiger / parent:sort_merge and $in sort expansion | Blocking sort memory limit and allowDiskUse (CVS 4.250) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-0243ade22f9d | sharding / parent:shard key selection for query isolation | analyzeShardKey workload sampling (CVS 4.250); Compound shard-key prefix targeting (CVS 4.175); Hashed versus ranged shard-key tradeoffs (CVS 3.950) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-e28d711cee18 | query-index-planner / index-design | setQuerySettings index hints and queryFramework (CVS 4.250); Index build commit quorum (commitQuorum and setIndexCommitQuorum) (CVS 4.175); Leading-prefix redundant index detection (CVS 4.175); Multikey indexes and index-provided sort order (CVS 4.175) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-ea1f4fe33d9f | cost-billing / cluster-sizing | Snapshot reads (atClusterTime) and history window sizing on secondaries (CVS 4.250); Oplog sizing and embedded-verifier memory for migrations (CVS 4.175); WiredTiger cache sizing and memory fragmentation (CVS 4.075); Destination temporary scaling and post-cutover right-sizing (CVS 4.000) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-a4d0714f2d41 | sharding / parent:long-running secondary reads in sharded clusters | Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds (CVS 4.250); Resume-from-last-key pattern for killed cursors (CVS 4.250); terminateSecondaryReadsOnOrphanCleanup and QueryPlanKilled 175 (CVS 4.125); Chunk migration commit, range deleter and orphan cleanup internals (CVS 4.050) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-6d975ea7dbf2 | time-series / parent:bucket fragmentation remediation (re-insert/merge) | Time series backfill ordering and batching (CVS 4.250); $out-based time series rewrite and cutover (CVS 3.900); Time series bucket reopening (archived and query-based) (CVS 3.875); Time series compact and disk space reclaim (CVS 3.800) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-9da1cfbc1747 | search-vector / vector-embedding | Vector index memory sizing and quantization trade-offs on Search Nodes (CVS 4.225); Atlas Vector Search RAM sizing and automatic quantization (CVS 4.150); Embedding generation and reranking token spend in retrieval TCO (CVS 4.100); Atlas Vector Search numCandidates tuning and recall measurement against ENN (CVS 4.025) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-dc0d0485fbfe | sharding / parent:unused index detection with $indexstats | Unique, TTL and shard-key indexes that read as unused (CVS 4.200) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-92f18235288a | mongodb-general / parent:total count strategies for paginated uis | hasNextPage without computing total pages (CVS 4.200); Maintained or cached count counters (CVS 3.775) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-ba08ada0b128 | archive-federation / parent:online archive partition-field selection | Online Archive Data Access and Data Seek Query Cost Model (CVS 4.200); Partition Field Immutability and Merge-Delete-Recreate Migration (CVS 3.925); Partition Field Leftmost-Prefix Ordering (CVS 3.900); Partition Field Count Limits (DATE vs CUSTOM) (CVS 3.150) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-4902740ddccc | query-index-planner / index-design | Multikey indexes and sort provision (multikeyPaths) (CVS 4.175); Compound-index prefix and sort-direction compatibility (CVS 4.150); $indexStats usage statistics and their reset conditions (CVS 4.075); Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes) (CVS 4.075) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-a8fb88989aee | replication-transactions / transactions | TemporarilyUnavailable and TransactionTooLargeForCache errors (CVS 4.175); MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later) (CVS 3.625); Read concern and causal consistency with secondary reads (CVS 3.600) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-b80b8cc0fac8 | search-vector / search-index | Atlas Search index behaviour with $out versus $merge targets (CVS 4.175); Atlas Search index lifecycle on $out and $merge targets (CVS 4.175); mongot replication lag, oplog window and index rebuild cost (CVS 4.175); Co-located vs dedicated mongot decision thresholds and failure modes (CVS 4.125) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-fdacc8310b4f | diagnostics-operations / parent:distributed sharded transactions | Coordinator failure recovery (CVS 4.175) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-e71ad6d99f1d | storage-wiredtiger / parent:index build resource limits (maxnumactiveuserindexbuilds, disk space) | WiredTiger cache pressure and write tickets during index builds (CVS 4.175); Commit quorum and the vote-to-commit point of no return (CVS 4.150); DiskSpaceMonitor and low-disk index build abort (7.1+) (CVS 3.725) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-49d659b13000 | storage-wiredtiger / parent:wiredtiger cache eviction and dirty ratio | WiredTiger history store and majority commit point cache pressure (CVS 4.175); WiredTiger checkpoints and checkpoint duration (CVS 4.150); Application-thread eviction and cache stalls (CVS 3.975); eviction_updates_trigger and the updates ratio (CVS 3.075) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-0346bef27420 | query-index-planner / planner-explain | Reading indexed `$or` plans with explain (CVS 4.150); Multiplanning storms after a plan cache flush (CVS 4.100); Plan cache key and $in length (classic vs SBE) (CVS 4.100); Plan cache flushes on index DDL (CVS 3.950) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-ae24704bd90e | cost-billing / billing-pricing | Balancer tuning and chunk migration cost (CVS 4.150); WiredTiger checkpoints and dirty-page write cost (CVS 4.050); Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams (CVS 4.050); Flex versus Dedicated boundary: ops-per-second pricing and missing features (CVS 3.975) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-70ad329d8e95 | query-index-planner / query-shape | Keyset (resume) pagination for restartable cursors (CVS 4.150); Inline user-facing querySettings (9.0) (CVS 4.125); Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis) (CVS 4.025); mongod diagnostic log slow-query format and slowOpSampleRate (CVS 4.000) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-c33aa5e84f28 | api-tooling / automation | Terraform effective fields and auto-scaling drift (CVS 4.150); Terraform state reconciliation after a Flex-to-Dedicated conversion (CVS 3.600); Atlas tag enforcement through Terraform and APIs (CVS 3.525); Auto-scaling min/max bounds and Terraform drift (CVS 2.850) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-27b1229cf1bf | sharding / parent:random-key (hashed/uuid) index insert behavior | Hashed shard-key write distribution and local index locality (CVS 4.125) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-7a717238450f | search-vector / search-index | Elasticsearch-to-Atlas Search migration and dual-run cost (CVS 4.125); Atlas Search index rebuild after migration (CVS 4.075); Atlas Search Nodes cost floor and co-located versus dedicated search (CVS 4.050); Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes (CVS 4.000) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-c5470a8d6ad1 | sharding / parent:rolling index builds | Detecting inconsistent indexes across shards (CVS 4.100) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-86c227f5e718 | sharding / parent:shard key design and resharding as cost levers | Atlas independent shard scaling and per-shard auto-scaling (CVS 4.100); Balancer, chunk migration and jumbo chunk remediation (CVS 4.075); Hashed, ranged and compound hashed shard keys (CVS 4.025); Zone sharding and region-aware shard keys (CVS 4.025) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-7b84bed0b7eb | storage-wiredtiger / parent:cluster tier limits and feature gates as cost drivers (connections, iops caps, minimum tiers) | Gen1 versus Gen2 IOPS provisioning and instance-level EBS/VM IOPS caps (CVS 4.100) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-74076c97a7f3 | query-index-planner / parent:resumable index builds | Commit quorum and votingMembers (CVS 4.075) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-fa377fb70b55 | replication-transactions / replication | Safe index removal: locks, rollback and regression checks (CVS 4.075); mongosync reversible sync and the rollback window (CVS 3.975); Replica set oplog window and initial sync (CVS 3.950); Atlas Live Migration pull versus push versus standalone mongosync selection (CVS 3.950) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-b05ce0d7baab | sharding / parent:covered queries on sharded collections | readConcern available on sharded clusters (CVS 4.075); Hashed shard keys and index support (CVS 3.925); Covered distinct and $group on sharded collections (CVS 3.850); COUNT_SCAN and sharded count accuracy (CVS 3.800) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-bae29937ea6d | mongodb-general / parent:cesource cardinality estimation (sampling vs heuristics) | Sampling CE accuracy under sparse sample matches (CVS 4.075); MongoDB CBR CE source metadata (CVS 3.200) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-6f4c87e440df | query-index-planner / index-design | ESR guideline and $in placement in compound indexes (CVS 4.050); dropIndexes locking and in-flight query behavior (CVS 4.000); Hidden indexes as a safe drop trial (CVS 4.000); Redundant (prefix) index detection for compound indexes (CVS 3.975) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-e79d2e686285 | networking / parent:migration and cutover cost (live migration, mongosync, dual-running, egress) | Application-level dual-write migration pattern (CVS 4.050); Cross-cloud application-tier placement and Atlas internet egress (CVS 3.975); EU Data Act switching charges and in-parallel egress (CVS 3.025); Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure) (CVS 2.975) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-91172fd79593 | sharding / parent:shard key design and resharding as cost levers | Reducing shard count and unsharding collections on Atlas (CVS 4.025); moveCollection and unshardCollection (CVS 3.975); Zone sharding and Global Cluster shard keys (CVS 3.950); Reshard to the same key for adding and removing shards (CVS 3.900) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-4f8b19686130 | sharding / parent:long-running secondary reads in sharded clusters | Balancer windows and per-collection balancing control (CVS 4.000); Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete) (CVS 3.925); Atlas analytics nodes and read preference tags (CVS 3.825); Workload isolation with tagged secondaries and Atlas analytics nodes (CVS 3.825) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-9506d4f6a2ef | storage-wiredtiger / parent:independent shard scaling and per-shard tiering | Per-shard disk IOPS and storage constraints (CVS 4.000); Per-shard IOPS and Gen2 storage on Atlas (CVS 3.925) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-8805540c719d | cost-billing / cluster-sizing | MongoDB Node.js driver pool sizing under Lambda concurrency (CVS 3.975); Zone sharding for hardware-tiered shards (CVS 3.950); Zone sharding for tiered hardware (hot, warm, cold) (CVS 3.950); Reverse sync and rollback-window economics (CVS 3.925) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-25bc80072973 | cost-billing / billing-pricing | Write amplification and cache cost of unused indexes (CVS 3.950); Relational-to-MongoDB migration cost (Relational Migrator) (CVS 3.850); Hybrid search ($rankFusion) vs two-system fusion TCO (CVS 3.850); Embedded verifier and post-migration data verification cost (CVS 3.800) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-a65c6320d64b | networking / parent:global ai hub research corpus | VPC Peering GCP Atlas (CVS 3.950); VPC Atlas Security (CVS 3.475) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-656e9592139b | query-index-planner / planner-explain | Multi-planner trial period and candidate plan ranking (CVS 3.950); Plan cache entry lifecycle: Inactive and Active entries and works growth (CVS 3.875); SBE plan cache keys and parameterized explode-for-sort plans (CVS 3.600); Plan cache invalidation on index DDL (hide, drop, create) (CVS 3.525) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-5cc6a5873cd4 | query-index-planner / index-design | Index filters and query settings versus hidden indexes (CVS 3.925); Side-writes table and hybrid index builds (CVS 3.775); Exporting $indexStats metrics with mongodb_exporter and PMM (CVS 3.775); Persisting index usage metrics with PMM and mongodb_exporter (CVS 3.775) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-3269334e5d34 | diagnostics-operations / parent:wiredtiger cache eviction and dirty ratio | MongoDB cache-pressure monitor and ticket admission (CVS 3.925) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-cab501a32cc1 | cost-billing / cluster-sizing | Dedicated Search Node storage and compute sizing (CVS 3.875); Standalone mongosync hosting and sizing (CVS 3.875); Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized (CVS 3.825); One-way tier gates: sharding, Global Writes, edition changes (CVS 3.750) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-56826f16d0e2 | query-index-planner / query-shape | serverStatus metrics.query.planCache counters (CVS 3.875); Atlas Query Insights: Query Shape Insights and Namespace Insights (CVS 3.850); Rooted $or subplanning and SORT_MERGE (CVS 3.725); Mixed-schema measurement predicate safety (CVS 3.700) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-437048a92799 | replication-transactions / replication | mongosync and live-migration oplog capacity planning (CVS 3.875); Count consistency under concurrent writes (CVS 3.850); Replication Oplog Window alerts and Oplog GB/Hour monitoring (CVS 3.800); Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom) (CVS 3.800) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-a971e035801b | search-vector / vector-embedding | Atlas Automated Embedding economics (Voyage tokens vs external embedding service) (CVS 3.875); numCandidates tuning for quantized HNSW indexes (CVS 3.850); Search Node sizing and disk-to-RAM ratios for quantized vector indexes (CVS 3.800); Search Node sizing for quantized vector indexes (RAM, disk, vCPU) (CVS 3.800) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-0decd84b4936 | query-index-planner / parent:rolling index builds | Hidden and priority-0 members during maintenance (CVS 3.850); Automated rolling builds in Atlas, Cloud Manager and Ops Manager (CVS 3.500) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-ded7cec0af2e | time-series / parent:bucket-level predicate rewriting for measurement operators | Loose versus tight bucket predicates (CVS 3.850); Time-field bucket predicates (CVS 3.750) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-d9cc5fb1cc98 | mongodb-general / parent:read offload via caching and precomputed views ($merge/$out, computed pattern) | Approximation pattern for write-heavy computed counters (CVS 3.850); Cache-aside vs write-through and cache stampede prevention (CVS 3.700); Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads) (CVS 3.475); Refresh scheduling with Atlas Scheduled Triggers (CVS 2.925) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-2daa30f3ff56 | sharding / parent:independent shard scaling and per-shard tiering | moveCollection and collection isolation on dedicated shards (CVS 3.850) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-7a36032fa829 | query-index-planner / parent:random-key (hashed/uuid) index insert behavior | UUIDv4 versus UUIDv7 key locality (CVS 3.850) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-b32256c25266 | api-tooling / app-services | Rolling resync (initial sync) as a space-reclaim technique on Atlas (CVS 3.850) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-2ccf282e3940 | mongodb-general / parent:operation rejection filters | defaultMaxTimeMS cluster-level read timeout (CVS 3.825) | [MongoDB server and Atlas documentation](https://www.mongodb.com/docs/) |
| mongodb-cohort-2350070cfddf | cost-billing / parent:cluster tier limits and feature gates as cost drivers (connections, iops caps, minimum tiers) | Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates) (CVS 3.825) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-62e6ed3dce38 | search-vector / search-index | Dedicated Search Nodes two-node cost floor versus coupled mongot (CVS 3.825); Atlas Search nodes in sharded clusters (CVS 3.800); Atlas Search node scaling per shard (CVS 3.750); Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections (CVS 3.625) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-bdd5f61f7553 | time-series / parent:bucket catalog memory and closure reasons | Bucket archiving and query-based reopening (CVS 3.775); Frozen buckets and compression failures (CVS 3.700); Idle bucket expiry and archived bucket reopening (CVS 3.675); Cache-derived dynamic bucket size limit (CVS 3.100) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-0c9ecdd50528 | schema-modeling / parent:natural language to mongodb query generation | Validation and performance review of generated queries (CVS 3.775); Schema grounding and value linking for MQL generation (CVS 3.625) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-4b508bb32935 | cost-billing / billing-pricing | Atlas invoice tag coverage and cost export reconciliation (CVS 3.775); Config server placement and cost (dedicated vs embedded) (CVS 3.775); Index rebuild cost after a wrong drop (CVS 3.725); Cost-based ranker and the plan cache (8.3+) (CVS 3.700) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-94bd5b52a712 | query-index-planner / index-design | MongoDB commit quorum and two-phase index builds (CVS 3.750); Two-phase (simultaneous) index builds (CVS 3.750); Rolling index builds as a resource-isolation alternative (CVS 3.750); serverStatus indexBuilds metrics and index build observability (CVS 3.725) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-036e3ca805ee | sharding / parent:covered queries on sharded collections | SHARDING_FILTER stage internals and orphaned-document filtering (CVS 3.750); Shard key index design (CVS 3.550); DISTINCT_SCAN with shard filtering in 8.2 (CVS 3.400); Express path for _id lookups on sharded collections (CVS 3.225) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-ead4605ef88b | schema-modeling / parent:random-key (hashed/uuid) index insert behavior | Clustered collection insert locality (CVS 3.725) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-e4fd097ac406 | search-vector / vector-embedding | Hybrid search ($rankFusion) vs separate search plus vector stack (CVS 3.725); Pre-quantized BinData (int8 and int1) ingestion (CVS 3.675); Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB (CVS 3.675); Measuring ANN recall against ENN baselines (CVS 3.625) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-f07644513ef2 | query-index-planner / index-design | Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden) (CVS 3.700); Query settings and index filters as plan pinning (CVS 3.700); Initial sync index build memory limits (CVS 3.700); Atlas managed slow operation threshold and Performance Advisor index suggestions (CVS 3.675) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-773223a064d7 | cost-billing / cluster-sizing | Destination right-sizing after cutover (CVS 3.700); Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes) (CVS 3.650); Gen2 clusters and Extended Standard IOPS economics (CVS 3.525); Enterprise Advanced licensing economics (CVS 2.950) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-975ece847641 | aggregation / parent:$group accumulator memory caps | per-accumulator explain memory statistics (CVS 3.700); custom $accumulator spill and merge semantics (CVS 3.675) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-70d788d6d368 | replication-transactions / replication | MongoDB Search eventual consistency and replication-lag metrics (CVS 3.675); Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields) (CVS 3.675); Atlas minimum oplog window (oplogMinRetentionHours) tuning (CVS 3.650); Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration (CVS 3.575) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-7a1e4d4e27ad | query-index-planner / query-shape | External sorter spill files in dbpath/_tmp (CVS 3.675); $querySettings stage and query settings inspection (CVS 3.600); Per-shape maxTimeMS and queryKnobs (9.0) (CVS 3.600); Per-shape queryKnobs and maxTimeMS (9.0) (CVS 3.600) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-c6b651987a29 | query-index-planner / index-design | Index usage measurement with $indexStats (CVS 3.650); Redundant and prefix index detection (CVS 3.650); MongoDB rolling index builds (CVS 3.650); Primary-driven index builds and write-rate throttles (CVS 3.625) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-d7196ea52923 | sharding / parent:shard key design and resharding as cost levers | Config shard versus dedicated config server (CVS 3.650) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-4be01f8fb55a | storage-wiredtiger / parent:atlas storage auto-scaling and disk reclaim via compact | Atlas disk decrease by volume replacement on AWS, Azure and GCP (CVS 3.650); Reducing Atlas storage capacity (new-volume sync, per-node downtime) (CVS 3.650); Atlas write-blocking thresholds and Intelligent Workload Management (CVS 3.600); Atlas Infinite storage metering and max storage limit (CVS 3.425) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-ea7ac08cebd8 | query-index-planner / parent:natural language to mongodb query generation | Execution-guided text-to-MQL refinement (CVS 3.650) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-8ec9154ebfb3 | sharding / parent:long-running secondary reads in sharded clusters | orphanCleanupDelaySecs and range deletion timing (CVS 3.625) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-e429df955a2f | cost-billing / billing-pricing | Burstable M10/M20 CPU credits and the M30 production threshold (CVS 3.625); Burstable M10/M20 CPU-credit throttling and when to move to M30 (CVS 3.625); Atlas billing alert notification delivery (CVS 3.575); Config shard (embedded config server) cost trade-off (CVS 3.525) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-0be0a58a9134 | time-series / parent:bucket fragmentation remediation (re-insert/merge) | rawData bucket-level CRUD (8.2 and later) (CVS 3.625); Rebuilding a time series collection with $out or mongorestore (CVS 3.500); Dynamic bucket sizing and cache-pressure closures (CVS 3.300); V2 and V3 compressed buckets and unsorted conversion (CVS 3.275) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-057bb6e3f810 | search-vector / search-index | Self-managed mongot on Community Edition: hardware and labour TCO (CVS 3.625) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-0a764cdc0199 | query-index-planner / index-design | multikey index sort behaviour (CVS 3.600); Sparse versus partial index equivalence (CVS 3.600); Rolling index builds on Kubernetes with the Percona Operator (CVS 3.550); Collation-aware index key size (CVS 3.475) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-28706a00e932 | time-series / parent:wiredtiger cache eviction and dirty ratio | Time-series bucket closure under cache pressure (CVS 3.575) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-9950ed680654 | networking / parent:platform consolidation tco (atlas search/vector search vs separate search or vector db) | Search Node network transfer and multi-region cost (CVS 3.575) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-2ffe965e5114 | query-index-planner / query-shape | explodeForSort integer overflow (CVE-2026-82076) (CVS 3.575); External sorter spill files and the _tmp directory (CVS 3.525); internalQueryMaxScansToExplode and maxScansToExplodeReached (CVS 3.525); Atlas Query Profiler and Operation Throttling metrics (CVS 3.525) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-02055194c32b | replication-transactions / replication | Atlas Minimum Oplog Window (oplogMinRetentionHours) (CVS 3.525); Atlas auto-scaling gating by oplog window and its alerts (CVS 3.425); Rolling index build key inconsistency incident (CVS 2.725) | [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/replication/); [Server replication, transactions and consistency](https://www.mongodb.com/docs/manual/core/transactions/) |
| mongodb-cohort-74707dd8f826 | identity-governance / identity-federation | GCP Workload Identity Atlas (CVS 3.425) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-2672a54425cd | query-index-planner / query-shape | Atlas Query Shape Insights and Namespace Insights (CVS 3.400); Percona PMM mongolog query source (CVS 2.725); queryKnobs and per-command querySettings (CVS 2.650) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-66670eb51cca | cost-billing / billing-pricing | Cost-based ranker plan selection for sorted queries (8.3+) (CVS 3.400); Atlas backup/PITR and data transfer cost drivers (CVS 3.250); Atlas-only feature lock-in and exit cost (CVS 3.000); AWS Marketplace EDP drawdown for Atlas (CVS 3.000) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-fb2e5c6c7cc5 | search-vector / vector-embedding | Matryoshka and quantization-aware embedding models (CVS 3.375); Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors (CVS 2.950); Lucene BBQ binary quantization compared with Atlas binary quantization (CVS 2.775); Search node tier sizing for vector indexes (CVS 2.550) | [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-search/); [Atlas Search and Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/) |
| mongodb-cohort-23dbaf3674d0 | query-index-planner / index-design | Atlas Performance Advisor drop-index recommendations (CVS 3.325); Sparse and partial indexes for $exists (CVS 3.200); Rolling index builds as a resource-limited alternative (CVS 3.000); positional index path caveat (CVS 2.925) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-b2cc9c3897c5 | sharding / parent:mongodb query shape optimization: sort, pagination, operators and sharded targeting | Counter-document pattern (CVS 3.300); Tailable cursors and maxAwaitTimeMS (CVS 3.300) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-97d0be9985d2 | cost-billing / parent:atlas cost planning: region pricing, estimation, scheduled scaling and competitor tco | Atlas Infinite compute auto-scaling (CVS 3.050); Scale-down tuning for spiky batch workloads (CVS 2.850); DynamoDB on-demand vs provisioned break-even (CVS 2.600); Cosmos DB RU estimation for MongoDB workloads (CVS 2.450) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-1f33141d477d | storage-wiredtiger / parent:wiredtiger cache eviction and dirty ratio | Spill WiredTiger instance cache (CVS 3.000); WiredTiger spill instance cache (CVS 3.000) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-bc364323a011 | cost-billing / billing-pricing | Backup and PIT oplog storage region billing (CVS 3.000); Cost Explorer filters for AI services (CVS 3.000); Query limits and billing alerts for archive spend (CVS 3.000); Atlas Infinite oplog and storage cost (CVS 2.975) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-de1c0f2fac41 | networking / parent:migration and cutover cost (live migration, mongosync, dual-running, egress) | Cloud exit-credit programs and EU Data Act in-parallel egress (CVS 2.975) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-cc7805a2b4af | cost-billing / billing-pricing | Project-level billing change alerts (CVS 2.950); Shared-cost splitting for Atlas projects (CVS 2.950); Config shard versus dedicated config server cost (CVS 2.850); MongoDB Charts billing dashboards (CVS 2.850) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-4b089bde7a44 | schema-modeling / parent:operation rejection filters | maxEstimatedScanBytes collection-scan rejection (9.0) (CVS 2.900) | [Server data modeling and schema validation](https://www.mongodb.com/docs/manual/data-modeling/) |
| mongodb-cohort-1537f1c9f03c | networking / parent:storage and data-lifecycle cost levers | Network (wire) compression (CVS 2.900) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-1df99675f929 | cost-billing / cluster-sizing | Oplog sizing in Kubernetes operators and managed MongoDB-compatible services (CVS 2.850) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-f3e3c14c2e33 | archive-federation / parent:online archive partition-field selection | Partition Field Type Enum Docs-vs-Spec Disagreement (CVS 2.850) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-06b0f31e2303 | query-index-planner / index-design | Persisting index usage metrics across restarts (PMM/monitoring) (CVS 2.850); Collation-based case-insensitive indexes as a $regex alternative (CVS 2.800); Rolling index build table-logging incident (CVS 2.725); PostgreSQL invalid indexes from failed CONCURRENTLY builds (CVS 2.400) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-69b213634bbc | cost-billing / billing-pricing | Intra-cluster replication transfer billing (CVS 2.800); Retroactive support billing on reactivation (CVS 2.800); Atlas billing alert configuration via Admin API (CVS 2.750); Atlas included-replica pricing vs per-instance HA billing (CVS 2.650) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-d945bf6ed1c3 | time-series / parent:data lifecycle cost model (ttl vs online archive vs data federation) | Time series collection expireAfterSeconds (CVS 2.800) | [Server time-series collections and query execution](https://www.mongodb.com/docs/manual/core/timeseries-collections/) |
| mongodb-cohort-a29d8407e9dc | storage-wiredtiger / parent:online archive partition-field selection | Partition Field Cardinality and the 2023-06-07 Storage Engine Change (CVS 2.700) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-18067a89fb07 | networking / parent:atlas cost planning: region pricing, estimation, scheduled scaling and competitor tco | Atlas PrivateLink regional endpoint rates (CVS 2.700); Egress and data transfer estimation (CVS 2.650) | [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-private-endpoint/); [Atlas networking and cloud-provider connectivity](https://www.mongodb.com/docs/atlas/security-vpc-peering/) |
| mongodb-cohort-019ea6c7f819 | cost-billing / billing-pricing | Re-indexing cost when changing numDimensions (CVS 2.650); Atlas Admin API billing alert configuration (CVS 2.600); FOCUS column mapping for Atlas credits (CVS 2.600); Linking Atlas orgs to marketplace billing accounts (CVS 2.600) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-86157c3fe16f | cost-billing / parent:atlas cost commitments, cross-org billing and finops tooling | Untagged spend reporting (CVS 2.650); Proportional minimum-commit allocation (CVS 2.450); Unlinking an organization (CVS 2.250) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-f2bea3de4b89 | api-tooling / automation | Atlas Admin API rate limiting for scheduled polling (CVS 2.600); Conftest/OPA rules over terraform show -json plans (CVS 2.550); Atlas Admin API pending-invoice tags field (CVS 2.400); Atlas CLI (unscored) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-4612d59db35d | aggregation / parent:atlas cost commitments, cross-org billing and finops tooling | Cross-vendor FOCUS pipelines (BigQuery/Snowflake) (CVS 2.600) | [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/aggregation/); [Server aggregation operators and optimization](https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/) |
| mongodb-cohort-a9c2cc4bbf19 | storage-wiredtiger / parent:atlas cost planning: region pricing, estimation, scheduled scaling and competitor tco | Backup storage rates by region (CVS 2.450) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-325a09333de2 | identity-governance / audit-compliance | Scheduled compliance polling and alerting (CVS 2.450) | [Atlas identity, access management and security](https://www.mongodb.com/docs/atlas/security/); [Atlas identity, access management and security](https://www.mongodb.com/docs/manual/security/) |
| mongodb-cohort-e298d0919726 | query-index-planner / index-design | SQL Server resumable online index operations (CVS 2.400); PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY (CVS 2.300); SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints (CVS 2.200) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-dab118cd8660 | storage-wiredtiger / parent:storage and data-lifecycle cost levers | Journal compression (CVS 2.350) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-3da97516cefc | cost-billing / billing-pricing | Billing incidents and refunds (CVS 2.300); Charts billing ingestion for linked orgs (CVS 2.000) | [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/billing/); [Atlas pricing, billing and cluster sizing](https://www.mongodb.com/docs/atlas/manage-clusters/) |
| mongodb-cohort-86b55445bd3c | query-index-planner / parent:mongodb wildcard and hidden indexes, index builds and index overhead | Cosmos DB for MongoDB wildcard differences (CVS 2.150) | [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/indexes/); [Server query planner, indexes and explain](https://www.mongodb.com/docs/manual/reference/explain-results/) |
| mongodb-cohort-2255fa8f9dbd | diagnostics-operations / parent:atlas diagnostics expert | Atlas Triage Workflows (unscored); Diagnostic Tool Design (unscored); FTDC and Log Tooling (unscored); KB-Backed Troubleshooting (unscored) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-acec48250f2d | storage-wiredtiger / parent:wiredtiger compaction algorithm | Background-Compaction Skip/EMA Heuristic (unscored) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |
| mongodb-cohort-aadbc815fdee | diagnostics-operations / parent:mongodb developer patterns | Error Codes and Troubleshooting (unscored) | [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/); [Server diagnostics, Atlas monitoring and operations](https://www.mongodb.com/docs/atlas/monitoring-alerts/) |
| mongodb-cohort-9ee49621e5ca | archive-federation / parent:mongodb atlas | MongoDB Atlas Data Federation (unscored) | [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/data-federation/); [Atlas Data Federation and Online Archive](https://www.mongodb.com/docs/atlas/online-archive/) |
| mongodb-cohort-34d60aede5df | api-tooling / drivers | MongoDB Drivers (unscored) | [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/drivers/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/cli/); [MongoDB drivers, tools and automation](https://www.mongodb.com/docs/atlas/api/) |
| mongodb-cohort-065b5964e6f4 | sharding / parent:mongodb developer patterns | mongosh Reference (unscored) | [Server sharding, routing and balancing](https://www.mongodb.com/docs/manual/sharding/) |
| mongodb-cohort-5c4fb85a6f32 | storage-wiredtiger / parent:mongodb autocompact | WiredTiger Compaction Algorithm (unscored) | [Server storage and WiredTiger architecture](https://www.mongodb.com/docs/manual/core/wiredtiger/); [Server storage and WiredTiger architecture](https://source.wiredtiger.com/) |

## Full inventory

| # | CVS | decision | concept | parent | mode | tree state | cohort | holder |
|---:|---:|---|---|---|---|---|---|---|
| 1 | 4.525 | RESEARCH | Time series cardinality and metaField design | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 2 | 4.475 | RESEARCH | Shard key index constraints when dropping or hiding indexes | Hidden indexes and safe index removal | dr | covered | mongodb-cohort-ab6ca72e8dcd | — |
| 3 | 4.450 | RESEARCH | Connection pool sizing and connection-storm control for Atlas (serverless and Lambda clients) | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | covered | mongodb-cohort-e72e1992fdeb | — |
| 4 | 4.450 | RESEARCH | Hot shard diagnosis and shard key remediation | Independent shard scaling and per-shard tiering | dr | covered | mongodb-cohort-1d6ef7b4932c | — |
| 5 | 4.450 | RESEARCH | $queryStats aggregation stage | Database Profiler vs Query Profiler | dr | covered | mongodb-cohort-5bc61fcfe3ec | — |
| 6 | 4.425 | RESEARCH | Reading sharded explain output (shards, SINGLE_SHARD, SHARD_MERGE) | Covered queries on sharded collections | dr | covered | mongodb-cohort-74cd39f19180 | — |
| 7 | 4.375 | RESEARCH | analyzeShardKey and query sampling | Shard Key Design and Resharding as Cost Levers | dr | covered | mongodb-cohort-2e478e8e7c3f | — |
| 8 | 4.375 | RESEARCH | analyzeShardKey query sampling and candidate-key scoring | Shard Key Design and Resharding as Cost Levers | dr | covered | mongodb-cohort-2e478e8e7c3f | — |
| 9 | 4.375 | RESEARCH | Delete propagation and reconciliation for $merge-maintained views | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 10 | 4.350 | RESEARCH | Index build commit quorum and hung builds | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 11 | 4.350 | RESEARCH | $queryStats and $currentOp as alternatives to the profiler | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 12 | 4.350 | RESEARCH | Hashed and compound hashed shard keys and index coverage | Covered queries on sharded collections | dr | covered | mongodb-cohort-74cd39f19180 | — |
| 13 | 4.350 | RESEARCH | Idempotent incremental refresh design for $merge (high-water marks, delete handling) | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 14 | 4.325 | RESEARCH | Time series bucketing parameters: granularity, bucketMaxSpanSeconds, bucketRoundingSeconds | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 15 | 4.325 | RESEARCH | WiredTiger cache sizing and working-set fit | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | covered | mongodb-cohort-e72e1992fdeb | — |
| 16 | 4.300 | RESEARCH | Atlas storage auto-scaling triggers, cooldowns and write blocking | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 17 | 4.275 | RESEARCH | Unique and TTL index side effects on removal | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 18 | 4.275 | RESEARCH | Index filters (planCacheSetFilter) deprecation and migration to query settings | Operation rejection filters | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 19 | 4.275 | RESEARCH | Oplog minimum retention window and storage auto-scaling | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 20 | 4.275 | RESEARCH | Read concern available, secondary reads and orphaned documents | Covered queries on sharded collections | dr | frontier | mongodb-cohort-47b75166139c | — |
| 21 | 4.250 | RESEARCH | Blocking sort memory limit and allowDiskUse | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-99762008d157 | — |
| 22 | 4.250 | RESEARCH | analyzeShardKey workload sampling | Shard key selection for query isolation | dr | frontier | mongodb-cohort-0243ade22f9d | — |
| 23 | 4.250 | RESEARCH | Atlas Query Profiler and slow-ops logs for shape discovery | Operation rejection filters | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 24 | 4.250 | RESEARCH | Oplog capacity for initial sync, live migration and bulk loads | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-47b75166139c | — |
| 25 | 4.250 | RESEARCH | Query settings: index hints and queryFramework (persistent query settings) | Operation rejection filters | dr | frontier | mongodb-cohort-c53f316f2ab7 | — |
| 26 | 4.250 | RESEARCH | setQuerySettings index hints and queryFramework | Operation rejection filters | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 27 | 4.250 | RESEARCH | Snapshot reads (atClusterTime) and history window sizing on secondaries | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-ea1f4fe33d9f | — |
| 28 | 4.250 | RESEARCH | Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 29 | 4.250 | RESEARCH | Time series backfill ordering and batching | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 30 | 4.250 | RESEARCH | Two-phase write protocol and writes without the shard key | Shard Key Design and Resharding as Cost Levers | dr | covered | mongodb-cohort-2e478e8e7c3f | — |
| 31 | 4.250 | RESEARCH | Resume-from-last-key pattern for killed cursors | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 32 | 4.250 | RESEARCH | Distributed Sharded Transactions | MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 33 | 4.250 | RESEARCH | Transaction Anti-Patterns | MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 34 | 4.225 | RESEARCH | Balancer data-size policy and zone-aware migration | Independent shard scaling and per-shard tiering | dr | covered | mongodb-cohort-1d6ef7b4932c | — |
| 35 | 4.225 | RESEARCH | Vector index memory sizing and quantization trade-offs on Search Nodes | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-9da1cfbc1747 | — |
| 36 | 4.225 | RESEARCH | Atlas disk write-blocking thresholds and recovery | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 37 | 4.200 | RESEARCH | Unique, TTL and shard-key indexes that read as unused | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-dc0d0485fbfe | — |
| 38 | 4.200 | RESEARCH | hasNextPage without computing total pages | Total count strategies for paginated UIs | dr | frontier | mongodb-cohort-92f18235288a | — |
| 39 | 4.200 | RESEARCH | Online Archive Data Access and Data Seek Query Cost Model | Online Archive partition-field selection | dr | frontier | mongodb-cohort-ba08ada0b128 | — |
| 40 | 4.175 | RESEARCH | Compound shard-key prefix targeting | Shard key selection for query isolation | dr | frontier | mongodb-cohort-0243ade22f9d | — |
| 41 | 4.175 | RESEARCH | Index build commit quorum (commitQuorum and setIndexCommitQuorum) | Rolling index builds | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 42 | 4.175 | RESEARCH | Leading-prefix redundant index detection | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 43 | 4.175 | RESEARCH | Multikey indexes and index-provided sort order | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-e28d711cee18 | — |
| 44 | 4.175 | RESEARCH | Multikey indexes and sort provision (multikeyPaths) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 45 | 4.175 | RESEARCH | Oplog sizing and embedded-verifier memory for migrations | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-ea1f4fe33d9f | — |
| 46 | 4.175 | RESEARCH | Per-node and per-shard $indexStats aggregation across replica sets and shards | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-47b75166139c | — |
| 47 | 4.175 | RESEARCH | TemporarilyUnavailable and TransactionTooLargeForCache errors | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-a8fb88989aee | — |
| 48 | 4.175 | RESEARCH | Atlas Search index behaviour with $out versus $merge targets | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-b80b8cc0fac8 | — |
| 49 | 4.175 | RESEARCH | Atlas Search index lifecycle on $out and $merge targets | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-b80b8cc0fac8 | — |
| 50 | 4.175 | RESEARCH | Coordinator failure recovery | Distributed Sharded Transactions | dr | frontier | mongodb-cohort-fdacc8310b4f | — |
| 51 | 4.175 | RESEARCH | WiredTiger cache pressure and write tickets during index builds | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-e71ad6d99f1d | — |
| 52 | 4.175 | RESEARCH | WiredTiger history store and majority commit point cache pressure | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 53 | 4.175 | RESEARCH | mongot replication lag, oplog window and index rebuild cost | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-b80b8cc0fac8 | — |
| 54 | 4.150 | RESEARCH | Compound-index prefix and sort-direction compatibility | Collation and index sort compatibility | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 55 | 4.150 | RESEARCH | Reading indexed `$or` plans with explain | Compound index vs index union for $or | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 56 | 4.150 | RESEARCH | Balancer tuning and chunk migration cost | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-ae24704bd90e | — |
| 57 | 4.150 | RESEARCH | Query shape and queryShapeHash stability | Operation rejection filters | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 58 | 4.150 | RESEARCH | Query shapes and queryShapeHash stability | Operation rejection filters | dr | frontier | mongodb-cohort-494e1aa39f55 | — |
| 59 | 4.150 | RESEARCH | WiredTiger checkpoints and checkpoint duration | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 60 | 4.150 | RESEARCH | Commit quorum and the vote-to-commit point of no return | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-e71ad6d99f1d | — |
| 61 | 4.150 | RESEARCH | Keyset (resume) pagination for restartable cursors | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 62 | 4.150 | RESEARCH | Terraform effective fields and auto-scaling drift | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-c33aa5e84f28 | — |
| 63 | 4.150 | RESEARCH | Atlas Vector Search RAM sizing and automatic quantization | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-9da1cfbc1747 | — |
| 64 | 4.125 | RESEARCH | Hashed shard-key write distribution and local index locality | Random-key (hashed/UUID) index insert behavior | dr | frontier | mongodb-cohort-27b1229cf1bf | — |
| 65 | 4.125 | RESEARCH | terminateSecondaryReadsOnOrphanCleanup and QueryPlanKilled 175 | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 66 | 4.125 | RESEARCH | Co-located vs dedicated mongot decision thresholds and failure modes | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-b80b8cc0fac8 | — |
| 67 | 4.125 | RESEARCH | Orphaned documents and range deletion | Covered queries on sharded collections | dr | covered | mongodb-cohort-74cd39f19180 | — |
| 68 | 4.125 | RESEARCH | Inline user-facing querySettings (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 69 | 4.125 | RESEARCH | Elasticsearch-to-Atlas Search migration and dual-run cost | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-7a717238450f | — |
| 70 | 4.100 | RESEARCH | Detecting inconsistent indexes across shards | Rolling index builds | dr | frontier | mongodb-cohort-c5470a8d6ad1 | — |
| 71 | 4.100 | RESEARCH | Embedding generation and reranking token spend in retrieval TCO | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-9da1cfbc1747 | — |
| 72 | 4.100 | RESEARCH | Atlas independent shard scaling and auto-scaling | Shard Key Design and Resharding as Cost Levers | dr | covered | mongodb-cohort-2e478e8e7c3f | — |
| 73 | 4.100 | RESEARCH | Atlas independent shard scaling and per-shard auto-scaling | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 74 | 4.100 | RESEARCH | Multiplanning storms after a plan cache flush | Replanning loops and replanReason | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 75 | 4.100 | RESEARCH | Gen1 versus Gen2 IOPS provisioning and instance-level EBS/VM IOPS caps | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-7b84bed0b7eb | — |
| 76 | 4.100 | RESEARCH | Plan cache key and $in length (classic vs SBE) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 77 | 4.075 | RESEARCH | $indexStats usage statistics and their reset conditions | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 78 | 4.075 | RESEARCH | Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes) | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-4902740ddccc | — |
| 79 | 4.075 | RESEARCH | Atlas compute auto-scaling for sharded clusters | Independent shard scaling and per-shard tiering | dr | covered | mongodb-cohort-1d6ef7b4932c | — |
| 80 | 4.075 | RESEARCH | Balancer, chunk migration and jumbo chunk remediation | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 81 | 4.075 | RESEARCH | Commit quorum and votingMembers | Resumable index builds | dr | frontier | mongodb-cohort-74076c97a7f3 | — |
| 82 | 4.075 | RESEARCH | Orphaned documents and read concern available versus local | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-47b75166139c | — |
| 83 | 4.075 | RESEARCH | Safe index removal: locks, rollback and regression checks | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-fa377fb70b55 | — |
| 84 | 4.075 | RESEARCH | SHARDING_FILTER stage and chunkSkips | Covered queries on sharded collections | dr | covered | mongodb-cohort-74cd39f19180 | — |
| 85 | 4.075 | RESEARCH | Atlas Search index rebuild after migration | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-7a717238450f | — |
| 86 | 4.075 | RESEARCH | readConcern available on sharded clusters | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 87 | 4.075 | RESEARCH | WiredTiger cache sizing and memory fragmentation | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-ea1f4fe33d9f | — |
| 88 | 4.075 | RESEARCH | Sampling CE accuracy under sparse sample matches | ceSource cardinality estimation (sampling vs heuristics) | dr | frontier | mongodb-cohort-bae29937ea6d | — |
| 89 | 4.050 | RESEARCH | ESR guideline and $in placement in compound indexes | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 90 | 4.050 | RESEARCH | WiredTiger checkpoints and dirty-page write cost | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-ae24704bd90e | — |
| 91 | 4.050 | RESEARCH | Atlas Search Nodes cost floor and co-located versus dedicated search | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-7a717238450f | — |
| 92 | 4.050 | RESEARCH | Chunk migration commit, range deleter and orphan cleanup internals | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-a4d0714f2d41 | — |
| 93 | 4.050 | RESEARCH | Application-level dual-write migration pattern | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 94 | 4.050 | RESEARCH | Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-ae24704bd90e | — |
| 95 | 4.050 | RESEARCH | Multi-Document Transactions | MongoDB Driver Internals; MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 96 | 4.025 | RESEARCH | Hashed, ranged and compound hashed shard keys | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 97 | 4.025 | RESEARCH | Zone sharding and region-aware shard keys | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-86c227f5e718 | — |
| 98 | 4.025 | RESEARCH | Atlas Vector Search numCandidates tuning and recall measurement against ENN | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-9da1cfbc1747 | — |
| 99 | 4.025 | RESEARCH | Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis) | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 100 | 4.025 | RESEARCH | Atlas Stream Processing streaming materialized views | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 101 | 4.025 | RESEARCH | Reducing shard count and unsharding collections on Atlas | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 102 | 4.000 | RESEARCH | Balancer windows and per-collection balancing control | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 103 | 4.000 | RESEARCH | Destination temporary scaling and post-cutover right-sizing | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-ea1f4fe33d9f | — |
| 104 | 4.000 | RESEARCH | dropIndexes locking and in-flight query behavior | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 105 | 4.000 | RESEARCH | Hidden indexes as a safe drop trial | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 106 | 4.000 | RESEARCH | mongod diagnostic log slow-query format and slowOpSampleRate | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-70ad329d8e95 | — |
| 107 | 4.000 | RESEARCH | Per-shard disk IOPS and storage constraints | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-9506d4f6a2ef | — |
| 108 | 4.000 | RESEARCH | Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-7a717238450f | — |
| 109 | 3.975 | RESEARCH | Redundant (prefix) index detection for compound indexes | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-6f4c87e440df | — |
| 110 | 3.975 | RESEARCH | Application-thread eviction and cache stalls | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 111 | 3.975 | RESEARCH | Flex versus Dedicated boundary: ops-per-second pricing and missing features | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-ae24704bd90e | — |
| 112 | 3.975 | RESEARCH | metaField cardinality and active-bucket count | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 113 | 3.975 | RESEARCH | MongoDB Node.js driver pool sizing under Lambda concurrency | Lambda MongoDB Driver Pattern | dr | frontier | mongodb-cohort-8805540c719d | — |
| 114 | 3.975 | RESEARCH | serverStatus bucketCatalog and collStats timeseries counters | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-2d50f9ab0851 | — |
| 115 | 3.975 | RESEARCH | moveCollection and unshardCollection | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 116 | 3.975 | RESEARCH | Cross-cloud application-tier placement and Atlas internet egress | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 117 | 3.975 | RESEARCH | mongosync reversible sync and the rollback window | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-fa377fb70b55 | — |
| 118 | 3.950 | RESEARCH | Hashed versus ranged shard-key tradeoffs | Shard key selection for query isolation | dr | frontier | mongodb-cohort-0243ade22f9d | — |
| 119 | 3.950 | RESEARCH | WiredTiger block reuse, file fragmentation and freeStorageSize | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 120 | 3.950 | RESEARCH | Write amplification and cache cost of unused indexes | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-25bc80072973 | — |
| 121 | 3.950 | RESEARCH | Plan cache flushes on index DDL | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-0346bef27420 | — |
| 122 | 3.950 | RESEARCH | Archive and TTL data lifecycle followed by compaction | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-99501ef9834d | — |
| 123 | 3.950 | RESEARCH | Replica set oplog window and initial sync | Rolling index builds | dr | frontier | mongodb-cohort-fa377fb70b55 | — |
| 124 | 3.950 | RESEARCH | Zone sharding for hardware-tiered shards | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-8805540c719d | — |
| 125 | 3.950 | RESEARCH | Zone sharding for tiered hardware (hot, warm, cold) | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-8805540c719d | — |
| 126 | 3.950 | RESEARCH | Atlas Live Migration pull versus push versus standalone mongosync selection | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-fa377fb70b55 | — |
| 127 | 3.950 | RESEARCH | VPC Peering GCP Atlas | Global AI Hub Research Corpus | dr | frontier | mongodb-cohort-a65c6320d64b | — |
| 128 | 3.950 | RESEARCH | Multi-planner trial period and candidate plan ranking | Replanning loops and replanReason | dr | frontier | mongodb-cohort-656e9592139b | — |
| 129 | 3.950 | RESEARCH | Zone sharding and Global Cluster shard keys | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 130 | 3.925 | RESEARCH | Hashed shard keys and index support | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 131 | 3.925 | RESEARCH | Index filters and query settings versus hidden indexes | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 132 | 3.925 | RESEARCH | Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete) | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 133 | 3.925 | RESEARCH | Per-shard compute auto-scaling rules and limits on Atlas | Independent shard scaling and per-shard tiering | dr | covered | mongodb-cohort-1d6ef7b4932c | — |
| 134 | 3.925 | RESEARCH | Reverse sync and rollback-window economics | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-8805540c719d | — |
| 135 | 3.925 | RESEARCH | Per-shard IOPS and Gen2 storage on Atlas | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-9506d4f6a2ef | — |
| 136 | 3.925 | RESEARCH | Partition Field Immutability and Merge-Delete-Recreate Migration | Online Archive partition-field selection | dr | frontier | mongodb-cohort-ba08ada0b128 | — |
| 137 | 3.925 | RESEARCH | MongoDB cache-pressure monitor and ticket admission | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-3269334e5d34 | — |
| 138 | 3.900 | RESEARCH | Cache stampede protection: leases, request coalescing, TTL jitter | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-a17745affdcc | — |
| 139 | 3.900 | RESEARCH | $out-based time series rewrite and cutover | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 140 | 3.900 | RESEARCH | Partition Field Leftmost-Prefix Ordering | Online Archive partition-field selection | dr | frontier | mongodb-cohort-ba08ada0b128 | — |
| 141 | 3.900 | RESEARCH | Reshard to the same key for adding and removing shards | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-91172fd79593 | — |
| 142 | 3.875 | RESEARCH | Dedicated Search Node storage and compute sizing | Atlas Search index sync lag and search-node sizing | dr | frontier | mongodb-cohort-cab501a32cc1 | — |
| 143 | 3.875 | RESEARCH | Plan cache entry lifecycle: Inactive and Active entries and works growth | Replanning loops and replanReason | dr | frontier | mongodb-cohort-656e9592139b | — |
| 144 | 3.875 | RESEARCH | serverStatus metrics.query.planCache counters | Replanning loops and replanReason | dr | frontier | mongodb-cohort-56826f16d0e2 | — |
| 145 | 3.875 | RESEARCH | Standalone mongosync hosting and sizing | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-cab501a32cc1 | — |
| 146 | 3.875 | RESEARCH | Time series bucket reopening (archived and query-based) | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 147 | 3.875 | RESEARCH | mongosync and live-migration oplog capacity planning | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-437048a92799 | — |
| 148 | 3.875 | RESEARCH | Atlas Automated Embedding economics (Voyage tokens vs external embedding service) | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-a971e035801b | — |
| 149 | 3.850 | RESEARCH | numCandidates tuning for quantized HNSW indexes | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-a971e035801b | — |
| 150 | 3.850 | RESEARCH | Count consistency under concurrent writes | Total count strategies for paginated UIs | dr | frontier | mongodb-cohort-437048a92799 | — |
| 151 | 3.850 | RESEARCH | Hidden and priority-0 members during maintenance | Rolling index builds | dr | frontier | mongodb-cohort-0decd84b4936 | — |
| 152 | 3.850 | RESEARCH | Loose versus tight bucket predicates | Bucket-level predicate rewriting for measurement operators | dr | frontier | mongodb-cohort-ded7cec0af2e | — |
| 153 | 3.850 | RESEARCH | Approximation pattern for write-heavy computed counters | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 154 | 3.850 | RESEARCH | Atlas Query Insights: Query Shape Insights and Namespace Insights | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-56826f16d0e2 | — |
| 155 | 3.850 | RESEARCH | Covered distinct and $group on sharded collections | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 156 | 3.850 | RESEARCH | moveCollection and collection isolation on dedicated shards | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-2daa30f3ff56 | — |
| 157 | 3.850 | RESEARCH | Relational-to-MongoDB migration cost (Relational Migrator) | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-25bc80072973 | — |
| 158 | 3.850 | RESEARCH | UUIDv4 versus UUIDv7 key locality | Random-key (hashed/UUID) index insert behavior | dr | frontier | mongodb-cohort-7a36032fa829 | — |
| 159 | 3.850 | RESEARCH | Hybrid search ($rankFusion) vs two-system fusion TCO | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-25bc80072973 | — |
| 160 | 3.850 | RESEARCH | Rolling resync (initial sync) as a space-reclaim technique on Atlas | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-b32256c25266 | — |
| 161 | 3.825 | RESEARCH | Atlas analytics nodes and read preference tags | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 162 | 3.825 | RESEARCH | Workload isolation with tagged secondaries and Atlas analytics nodes | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-4f8b19686130 | — |
| 163 | 3.825 | RESEARCH | defaultMaxTimeMS cluster-level read timeout | Operation rejection filters | dr | frontier | mongodb-cohort-2ccf282e3940 | — |
| 164 | 3.825 | RESEARCH | Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates) | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-2350070cfddf | — |
| 165 | 3.825 | RESEARCH | Dedicated Search Nodes two-node cost floor versus coupled mongot | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-62e6ed3dce38 | — |
| 166 | 3.825 | RESEARCH | Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-cab501a32cc1 | — |
| 167 | 3.800 | RESEARCH | Replication Oplog Window alerts and Oplog GB/Hour monitoring | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-437048a92799 | — |
| 168 | 3.800 | RESEARCH | Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom) | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-437048a92799 | — |
| 169 | 3.800 | RESEARCH | Atlas Search nodes in sharded clusters | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-62e6ed3dce38 | — |
| 170 | 3.800 | RESEARCH | Embedded verifier and post-migration data verification cost | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-25bc80072973 | — |
| 171 | 3.800 | RESEARCH | Time series compact and disk space reclaim | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-6d975ea7dbf2 | — |
| 172 | 3.800 | RESEARCH | Bucket reopening and the {metaField, timeField} index requirement | Bucket fragmentation remediation (re-insert/merge) | dr | covered | mongodb-cohort-3a39b842dcf7 | — |
| 173 | 3.800 | RESEARCH | Search Node sizing and disk-to-RAM ratios for quantized vector indexes | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-a971e035801b | — |
| 174 | 3.800 | RESEARCH | Search Node sizing for quantized vector indexes (RAM, disk, vCPU) | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-a971e035801b | — |
| 175 | 3.800 | RESEARCH | COUNT_SCAN and sharded count accuracy | Covered queries on sharded collections | dr | frontier | mongodb-cohort-b05ce0d7baab | — |
| 176 | 3.775 | RESEARCH | dropIndexes locking and rollback by rebuild | Unused index detection with $indexStats | dr | covered | mongodb-cohort-924cda5ff47d | — |
| 177 | 3.775 | RESEARCH | Maintained or cached count counters | Total count strategies for paginated UIs | dr | frontier | mongodb-cohort-92f18235288a | — |
| 178 | 3.775 | RESEARCH | replSetResizeOplog and oplog compaction on self-managed replica sets | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 179 | 3.775 | RESEARCH | Bucket archiving and query-based reopening | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 180 | 3.775 | RESEARCH | Cache-pressure early bucket closure and bucket catalog memory | Bucket fragmentation remediation (re-insert/merge) | dr | covered | mongodb-cohort-3a39b842dcf7 | — |
| 181 | 3.775 | RESEARCH | Side-writes table and hybrid index builds | Resumable index builds | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 182 | 3.775 | RESEARCH | Validation and performance review of generated queries | Natural language to MongoDB query generation | dr | frontier | mongodb-cohort-0c9ecdd50528 | — |
| 183 | 3.775 | RESEARCH | Atlas invoice tag coverage and cost export reconciliation | Atlas tag taxonomy for showback and chargeback | dr | frontier | mongodb-cohort-4b508bb32935 | — |
| 184 | 3.775 | RESEARCH | Exporting $indexStats metrics with mongodb_exporter and PMM | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 185 | 3.775 | RESEARCH | Persisting index usage metrics with PMM and mongodb_exporter | Unused index detection with $indexStats | dr | frontier | mongodb-cohort-5cc6a5873cd4 | — |
| 186 | 3.775 | RESEARCH | Config server placement and cost (dedicated vs embedded) | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-4b508bb32935 | — |
| 187 | 3.750 | RESEARCH | MongoDB commit quorum and two-phase index builds | Resumable index builds | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 188 | 3.750 | RESEARCH | Time-field bucket predicates | Bucket-level predicate rewriting for measurement operators | dr | frontier | mongodb-cohort-ded7cec0af2e | — |
| 189 | 3.750 | RESEARCH | Two-phase (simultaneous) index builds | Resumable index builds | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 190 | 3.750 | RESEARCH | Rolling index builds as a resource-isolation alternative | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 191 | 3.750 | RESEARCH | SHARDING_FILTER stage internals and orphaned-document filtering | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 192 | 3.750 | RESEARCH | One-way tier gates: sharding, Global Writes, edition changes | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-cab501a32cc1 | — |
| 193 | 3.750 | RESEARCH | Atlas Search node scaling per shard | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-62e6ed3dce38 | — |
| 194 | 3.725 | RESEARCH | Index rebuild cost after a wrong drop | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-4b508bb32935 | — |
| 195 | 3.725 | RESEARCH | Delete and re-insert safety on time series | Bucket fragmentation remediation (re-insert/merge) | dr | covered | mongodb-cohort-3a39b842dcf7 | — |
| 196 | 3.725 | RESEARCH | DiskSpaceMonitor and low-disk index build abort (7.1+) | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-e71ad6d99f1d | — |
| 197 | 3.725 | RESEARCH | Clustered collection insert locality | Random-key (hashed/UUID) index insert behavior | dr | frontier | mongodb-cohort-ead4605ef88b | — |
| 198 | 3.725 | RESEARCH | Rooted $or subplanning and SORT_MERGE | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-56826f16d0e2 | — |
| 199 | 3.725 | RESEARCH | serverStatus indexBuilds metrics and index build observability | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-94bd5b52a712 | — |
| 200 | 3.725 | RESEARCH | Hybrid search ($rankFusion) vs separate search plus vector stack | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-e4fd097ac406 | — |
| 201 | 3.700 | RESEARCH | Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden) | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 202 | 3.700 | RESEARCH | Destination right-sizing after cutover | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-773223a064d7 | — |
| 203 | 3.700 | RESEARCH | Cache-aside vs write-through and cache stampede prevention | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 204 | 3.700 | RESEARCH | Query settings and index filters as plan pinning | Replanning loops and replanReason | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 205 | 3.700 | RESEARCH | Frozen buckets and compression failures | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 206 | 3.700 | RESEARCH | Initial sync index build memory limits | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 207 | 3.700 | RESEARCH | per-accumulator explain memory statistics | $group accumulator memory caps | dr | frontier | mongodb-cohort-975ece847641 | — |
| 208 | 3.700 | RESEARCH | Mixed-schema measurement predicate safety | Bucket-level predicate rewriting for measurement operators | dr | frontier | mongodb-cohort-56826f16d0e2 | — |
| 209 | 3.700 | RESEARCH | Oplog windows and Search initial-sync recovery | Atlas Search index sync lag and search-node sizing | dr | covered | mongodb-cohort-924cda5ff47d | — |
| 210 | 3.700 | RESEARCH | Sharded time series rebuild and resharding | Bucket fragmentation remediation (re-insert/merge) | dr | covered | mongodb-cohort-3a39b842dcf7 | — |
| 211 | 3.700 | RESEARCH | Cost-based ranker and the plan cache (8.3+) | Replanning loops and replanReason | dr | frontier | mongodb-cohort-4b508bb32935 | — |
| 212 | 3.675 | RESEARCH | Idle bucket expiry and archived bucket reopening | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 213 | 3.675 | RESEARCH | MongoDB Search eventual consistency and replication-lag metrics | Atlas Search index sync lag and search-node sizing | dr | frontier | mongodb-cohort-70d788d6d368 | — |
| 214 | 3.675 | RESEARCH | Atlas managed slow operation threshold and Performance Advisor index suggestions | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-f07644513ef2 | — |
| 215 | 3.675 | RESEARCH | External sorter spill files in dbpath/_tmp | Resumable index builds | dr | frontier | mongodb-cohort-7a1e4d4e27ad | — |
| 216 | 3.675 | RESEARCH | Pre-quantized BinData (int8 and int1) ingestion | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-e4fd097ac406 | — |
| 217 | 3.675 | RESEARCH | Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-e4fd097ac406 | — |
| 218 | 3.675 | RESEARCH | custom $accumulator spill and merge semantics | $group accumulator memory caps | dr | frontier | mongodb-cohort-975ece847641 | — |
| 219 | 3.675 | RESEARCH | Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields) | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-70d788d6d368 | — |
| 220 | 3.650 | SKIP | Index usage measurement with $indexStats | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 221 | 3.650 | SKIP | Redundant and prefix index detection | Hidden indexes and safe index removal; Unused index detection with $indexStats | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 222 | 3.650 | RESEARCH | MongoDB rolling index builds | Resumable index builds | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 223 | 3.650 | RESEARCH | Config shard versus dedicated config server | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-d7196ea52923 | — |
| 224 | 3.650 | RESEARCH | Atlas minimum oplog window (oplogMinRetentionHours) tuning | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-70d788d6d368 | — |
| 225 | 3.650 | RESEARCH | Atlas disk decrease by volume replacement on AWS, Azure and GCP | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 226 | 3.650 | RESEARCH | Reducing Atlas storage capacity (new-volume sync, per-node downtime) | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 227 | 3.650 | RESEARCH | Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes) | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-773223a064d7 | — |
| 228 | 3.650 | RESEARCH | Execution-guided text-to-MQL refinement | Natural language to MongoDB query generation | dr | frontier | mongodb-cohort-ea7ac08cebd8 | — |
| 229 | 3.625 | RESEARCH | Measuring ANN recall against ENN baselines | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-e4fd097ac406 | — |
| 230 | 3.625 | RESEARCH | orphanCleanupDelaySecs and range deletion timing | Long-running secondary reads in sharded clusters | dr | frontier | mongodb-cohort-8ec9154ebfb3 | — |
| 231 | 3.625 | RESEARCH | Burstable M10/M20 CPU credits and the M30 production threshold | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-e429df955a2f | — |
| 232 | 3.625 | RESEARCH | Burstable M10/M20 CPU-credit throttling and when to move to M30 | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-e429df955a2f | — |
| 233 | 3.625 | RESEARCH | Schema grounding and value linking for MQL generation | Natural language to MongoDB query generation | dr | frontier | mongodb-cohort-0c9ecdd50528 | — |
| 234 | 3.625 | RESEARCH | Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-62e6ed3dce38 | — |
| 235 | 3.625 | RESEARCH | MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later) | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-a8fb88989aee | — |
| 236 | 3.625 | RESEARCH | Primary-driven index builds and write-rate throttles | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-c6b651987a29 | — |
| 237 | 3.625 | RESEARCH | rawData bucket-level CRUD (8.2 and later) | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 238 | 3.625 | RESEARCH | Self-managed mongot on Community Edition: hardware and labour TCO | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-057bb6e3f810 | — |
| 239 | 3.600 | RESEARCH | $querySettings stage and query settings inspection | Operation rejection filters | dr | frontier | mongodb-cohort-7a1e4d4e27ad | — |
| 240 | 3.600 | RESEARCH | Terraform state reconciliation after a Flex-to-Dedicated conversion | Flex Limitations and migration to Dedicated | dr | frontier | mongodb-cohort-c33aa5e84f28 | — |
| 241 | 3.600 | RESEARCH | Atlas write-blocking thresholds and Intelligent Workload Management | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 242 | 3.600 | RESEARCH | SBE plan cache keys and parameterized explode-for-sort plans | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-656e9592139b | — |
| 243 | 3.600 | RESEARCH | Per-shape maxTimeMS and queryKnobs (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-7a1e4d4e27ad | — |
| 244 | 3.600 | RESEARCH | Per-shape queryKnobs and maxTimeMS (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-7a1e4d4e27ad | — |
| 245 | 3.600 | RESEARCH | multikey index sort behaviour | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | frontier | mongodb-cohort-0a764cdc0199 | — |
| 246 | 3.600 | RESEARCH | Read concern and causal consistency with secondary reads | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-a8fb88989aee | — |
| 247 | 3.600 | RESEARCH | Replica Set Transactions | MongoDB Transactions | dr | covered | mongodb-cohort-700382c55bcd | — |
| 248 | 3.600 | RESEARCH | Sparse versus partial index equivalence | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | dr | frontier | mongodb-cohort-0a764cdc0199 | — |
| 249 | 3.575 | RESEARCH | Atlas billing alert notification delivery | Admin API alert configurations for billing events | dr | frontier | mongodb-cohort-e429df955a2f | — |
| 250 | 3.575 | RESEARCH | Time-series bucket closure under cache pressure | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-28706a00e932 | — |
| 251 | 3.575 | RESEARCH | Search Node network transfer and multi-region cost | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-9950ed680654 | — |
| 252 | 3.575 | RESEARCH | Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration | Independent shard scaling and per-shard tiering | dr | frontier | mongodb-cohort-70d788d6d368 | — |
| 253 | 3.575 | RESEARCH | explodeForSort integer overflow (CVE-2026-82076) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-2ffe965e5114 | — |
| 254 | 3.550 | RESEARCH | Shard key index design | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 255 | 3.550 | RESEARCH | Multiplanner scoring and tie-breakers | SORT_MERGE and $in sort expansion | dr | covered | mongodb-cohort-f44ec837e1b3 | — |
| 256 | 3.550 | RESEARCH | Rolling index builds on Kubernetes with the Percona Operator | Rolling index builds | dr | frontier | mongodb-cohort-0a764cdc0199 | — |
| 257 | 3.550 | RESEARCH | SBE plan cache pinned entries and the classic runtime planner for SBE | Replanning loops and replanReason | dr | covered | mongodb-cohort-f44ec837e1b3 | — |
| 258 | 3.525 | SKIP | Plan cache invalidation on index DDL (hide, drop, create) | Hidden indexes and safe index removal | dr | frontier | mongodb-cohort-656e9592139b | — |
| 259 | 3.525 | RESEARCH | External sorter spill files and the _tmp directory | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-2ffe965e5114 | — |
| 260 | 3.525 | RESEARCH | Atlas tag enforcement through Terraform and APIs | Atlas tag taxonomy for showback and chargeback | dr | frontier | mongodb-cohort-c33aa5e84f28 | — |
| 261 | 3.525 | RESEARCH | Config shard (embedded config server) cost trade-off | Shard Key Design and Resharding as Cost Levers | dr | frontier | mongodb-cohort-e429df955a2f | — |
| 262 | 3.525 | RESEARCH | Atlas Minimum Oplog Window (oplogMinRetentionHours) | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-02055194c32b | — |
| 263 | 3.525 | RESEARCH | internalQueryMaxScansToExplode and maxScansToExplodeReached | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-2ffe965e5114 | — |
| 264 | 3.525 | RESEARCH | Flex backup and recovery planning | Flex Limitations and migration to Dedicated | dr | covered | mongodb-cohort-734b288e14c5 | — |
| 265 | 3.525 | RESEARCH | Atlas Query Profiler and Operation Throttling metrics | Operation rejection filters | dr | frontier | mongodb-cohort-2ffe965e5114 | — |
| 266 | 3.525 | RESEARCH | Gen2 clusters and Extended Standard IOPS economics | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | frontier | mongodb-cohort-773223a064d7 | — |
| 267 | 3.500 | RESEARCH | Rebuilding a time series collection with $out or mongorestore | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 268 | 3.500 | RESEARCH | Atlas security add-on uplifts (auditing, LDAP, customer-managed keys, private endpoints) | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | covered | mongodb-cohort-2fc27615a9f6 | — |
| 269 | 3.500 | RESEARCH | Automated rolling builds in Atlas, Cloud Manager and Ops Manager | Rolling index builds | dr | frontier | mongodb-cohort-0decd84b4936 | — |
| 270 | 3.475 | RESEARCH | Collation-aware index key size | Collation and index sort compatibility | dr | frontier | mongodb-cohort-0a764cdc0199 | — |
| 271 | 3.475 | RESEARCH | Ops Manager Profiler | Database Profiler vs Query Profiler | dr | covered | mongodb-cohort-9767e9fb3174 | — |
| 272 | 3.475 | RESEARCH | Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads) | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 273 | 3.475 | RESEARCH | VPC Atlas Security | Global AI Hub Research Corpus | dr | frontier | mongodb-cohort-a65c6320d64b | — |
| 274 | 3.450 | RESEARCH | path-level multikey tracking | explain multiKeyPaths interpretation | dr | covered | mongodb-cohort-6b0d6e198335 | — |
| 275 | 3.450 | RESEARCH | Percona PMM mongolog versus profiler query source | Database Profiler vs Query Profiler | dr | covered | mongodb-cohort-1c8b3f490617 | — |
| 276 | 3.450 | RESEARCH | EBS volume modification limits and Atlas disk resize mechanics | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 277 | 3.450 | RESEARCH | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | MongoDB Atlas Cost Optimization; Replica Set Node Topology Cost | dr | covered | mongodb-cohort-75acba036546 | — |
| 278 | 3.450 | RESEARCH | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-97c656997272 | — |
| 279 | 3.425 | RESEARCH | Atlas Real-Time Performance Panel | Database Profiler vs Query Profiler | dr | covered | mongodb-cohort-27f762df4c87 | — |
| 280 | 3.425 | RESEARCH | Atlas auto-scaling gating by oplog window and its alerts | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-02055194c32b | — |
| 281 | 3.425 | RESEARCH | Atlas Infinite storage metering and max storage limit | Atlas storage auto-scaling and disk reclaim via compact | dr | frontier | mongodb-cohort-4be01f8fb55a | — |
| 282 | 3.425 | RESEARCH | GCP Workload Identity Atlas | Global AI Hub Research Corpus | dr | frontier | mongodb-cohort-74707dd8f826 | — |
| 283 | 3.400 | SKIP | Atlas Query Shape Insights and Namespace Insights | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-2672a54425cd | — |
| 284 | 3.400 | RESEARCH | Atlas Administration API rolling index endpoint | Rolling index builds | dr | covered | mongodb-cohort-6b0d6e198335 | — |
| 285 | 3.400 | RESEARCH | Cost-based ranker plan selection for sorted queries (8.3+) | SORT_MERGE and $in sort expansion | dr | frontier | mongodb-cohort-66670eb51cca | — |
| 286 | 3.400 | RESEARCH | MongoDB primary-driven index builds (PDIB) | Resumable index builds | dr | covered | mongodb-cohort-6b0d6e198335 | — |
| 287 | 3.400 | RESEARCH | Primary-driven index builds | Resumable index builds | dr | covered | mongodb-cohort-6b0d6e198335 | — |
| 288 | 3.400 | RESEARCH | DISTINCT_SCAN with shard filtering in 8.2 | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 289 | 3.400 | RESEARCH | Covered queries and projection design | Query Efficiency as a Cost Lever; Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-9860e797131c | — |
| 290 | 3.400 | RESEARCH | Multikey index sort bounds | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-a96a1c48d085 | — |
| 291 | 3.375 | RESEARCH | Matryoshka and quantization-aware embedding models | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-fb2e5c6c7cc5 | — |
| 292 | 3.350 | RESEARCH | Interval evaluation trees and parameterized plan caching | SORT_MERGE and $in sort expansion | dr | covered | mongodb-cohort-46673b83291a | — |
| 293 | 3.350 | RESEARCH | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-db4475b6de67 | — |
| 294 | 3.325 | SKIP | Atlas Performance Advisor drop-index recommendations | Hidden indexes and safe index removal; Unused index detection with $indexStats | dr | frontier | mongodb-cohort-23dbaf3674d0 | — |
| 295 | 3.325 | RESEARCH | Atlas Infinite fixed-IOPS tiers and decoupled storage | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | covered | mongodb-cohort-e72e1992fdeb | — |
| 296 | 3.300 | RESEARCH | Dynamic bucket sizing and cache-pressure closures | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 297 | 3.300 | RESEARCH | Quantization-aware and Matryoshka embeddings (voyage-3-large) with Atlas dimension slicing | Atlas Vector Search automatic quantization and rescoring | dr | covered | mongodb-cohort-97c656997272 | — |
| 298 | 3.300 | RESEARCH | Atlas Infinite oplog and storage-layer replication | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-6047f9cce83c | — |
| 299 | 3.300 | RESEARCH | Counter-document pattern | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-b2cc9c3897c5 | — |
| 300 | 3.300 | RESEARCH | Field-name abbreviation trade-offs | Schema Design for Storage Cost; Storage and Data-Lifecycle Cost Levers | dr | covered | mongodb-cohort-d4596a7c1ce4 | — |
| 301 | 3.300 | RESEARCH | M10 shared-vCPU dedicated tier economics | Atlas Flex Pricing and Flex-vs-Dedicated Break-Even; Atlas Pricing Programs, Cost Governance and TCO | dr | covered | mongodb-cohort-e72e1992fdeb | — |
| 302 | 3.300 | RESEARCH | Tailable cursors and maxAwaitTimeMS | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-b2cc9c3897c5 | — |
| 303 | 3.275 | RESEARCH | Eviction thread sizing and wiredTigerEngineRuntimeConfig tuning | WiredTiger cache eviction and dirty ratio | dr | covered | mongodb-cohort-710af3a88726 | — |
| 304 | 3.275 | RESEARCH | V2 and V3 compressed buckets and unsorted conversion | Bucket fragmentation remediation (re-insert/merge) | dr | frontier | mongodb-cohort-0be0a58a9134 | — |
| 305 | 3.250 | RESEARCH | Atlas index build tier defaults | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | covered | mongodb-cohort-710af3a88726 | — |
| 306 | 3.250 | RESEARCH | Atlas tier-fixed index build limits | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | covered | mongodb-cohort-710af3a88726 | — |
| 307 | 3.250 | RESEARCH | MongoDB 8.0 autoCompact background compaction on Atlas | Atlas storage auto-scaling and disk reclaim via compact | dr | covered | mongodb-cohort-733862797816 | — |
| 308 | 3.250 | RESEARCH | IAM Role Atlas API Access | Global AI Hub Research Corpus | dr | covered | mongodb-cohort-bef2224dcee8 | — |
| 309 | 3.250 | RESEARCH | Atlas backup/PITR and data transfer cost drivers | Atlas Pricing Programs, Cost Governance and TCO; Self-Managed MongoDB vs Atlas TCO | dr | frontier | mongodb-cohort-66670eb51cca | — |
| 310 | 3.250 | RESEARCH | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | MongoDB Atlas Cost Optimization | dr | covered | mongodb-cohort-b6cf8b1e516a | — |
| 311 | 3.250 | RESEARCH | Shard Key Design and Resharding as Cost Levers | MongoDB Atlas Cost Optimization; Sharded Cluster Cost Economics | dr | covered | mongodb-cohort-75acba036546 | — |
| 312 | 3.225 | RESEARCH | Express path for _id lookups on sharded collections | Covered queries on sharded collections | dr | frontier | mongodb-cohort-036e3ca805ee | — |
| 313 | 3.200 | RESEARCH | MongoDB CBR CE source metadata | ceSource cardinality estimation (sampling vs heuristics) | dr | frontier | mongodb-cohort-bae29937ea6d | — |
| 314 | 3.200 | SKIP | Atlas Query Shape Insights | MongoDB Explain Plans, Query Planner and Plan Cache | dr | covered | mongodb-cohort-1c8b3f490617 | — |
| 315 | 3.200 | SKIP | Namespace Insights | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | covered | mongodb-cohort-9fc6f09a3009 | — |
| 316 | 3.200 | RESEARCH | Sparse and partial indexes for $exists | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | frontier | mongodb-cohort-23dbaf3674d0 | — |
| 317 | 3.175 | RESEARCH | Organization-scoped alert configuration API | Admin API alert configurations for billing events | dr | covered | mongodb-cohort-e1ba7cea1572 | — |
| 318 | 3.175 | RESEARCH | Lambda Managed Instances and MongoClient concurrency safety | Lambda MongoDB Driver Pattern | dr | covered | mongodb-cohort-e1ba7cea1572 | — |
| 319 | 3.175 | RESEARCH | Atlas Infinite storage model (max storage limit, no auto-scaling) | Atlas storage auto-scaling and disk reclaim via compact | dr | covered | mongodb-cohort-733862797816 | — |
| 320 | 3.150 | RESEARCH | replSetResizeOplog and oplog compaction runbook | Oplog sizing under storage auto-scaling | dr | covered | mongodb-cohort-37fc02336c5b | — |
| 321 | 3.150 | RESEARCH | Partition Field Count Limits (DATE vs CUSTOM) | Online Archive partition-field selection | dr | frontier | mongodb-cohort-ba08ada0b128 | — |
| 322 | 3.150 | RESEARCH | Atlas Infinite fixed per-tier IOPS and public-preview feature exclusions | Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers) | dr | covered | mongodb-cohort-710af3a88726 | — |
| 323 | 3.150 | RESEARCH | Primary-driven index builds (spill to a replicated table) | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | covered | mongodb-cohort-924cda5ff47d | — |
| 324 | 3.150 | SKIP | $function and server-side JavaScript hardening | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-9cff09d95361 | — |
| 325 | 3.150 | SKIP | Atlas Charts billing dashboards | Atlas Billing Mechanics and Cost Visibility; Atlas Cost Explorer and Billing Data API | dr | covered | mongodb-cohort-75acba036546 | — |
| 326 | 3.150 | SKIP | Credit expiry and History table | Atlas Billing Mechanics and Cost Visibility; Atlas Credits Prepaid Subscriptions and Overage | dr | covered | mongodb-cohort-75acba036546 | — |
| 327 | 3.150 | SKIP | Index hints on time series collections | MongoDB Time-Series Query and Index Optimization | dr | covered | mongodb-cohort-7e83aa58193c | — |
| 328 | 3.100 | RESEARCH | Cache-derived dynamic bucket size limit | Bucket catalog memory and closure reasons | dr | frontier | mongodb-cohort-bdd5f61f7553 | — |
| 329 | 3.100 | RESEARCH | Dynamic bucket size cap under cache pressure | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-bd6489c69c3d | — |
| 330 | 3.100 | SKIP | Atlas marketplace private offers | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit) | dr | covered | mongodb-cohort-3d1ba45ce31f | — |
| 331 | 3.100 | SKIP | Gen1 vs Gen2 storage and IOPS billing | Atlas Cluster Topology and Tier Economics; Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe); Storage Growth and IOPS Forecasting for Cost | dr | covered | mongodb-cohort-3d1ba45ce31f | — |
| 332 | 3.100 | SKIP | SBE $lookup pushdown and hash join | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-468120abc19f | — |
| 333 | 3.075 | RESEARCH | Shared-cost allocation rules for managed database services | Atlas tag taxonomy for showback and chargeback | dr | covered | mongodb-cohort-3d1ba45ce31f | — |
| 334 | 3.075 | RESEARCH | eviction_updates_trigger and the updates ratio | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-49d659b13000 | — |
| 335 | 3.050 | RESEARCH | Same-field `$or` to `$in` rewrite | Compound index vs index union for $or | dr | covered | mongodb-cohort-68aac318a142 | — |
| 336 | 3.050 | RESEARCH | Gen1 vs Gen2 IOPS billing | Storage Growth and IOPS Forecasting for Cost | dr | covered | mongodb-cohort-3d1ba45ce31f | — |
| 337 | 3.050 | SKIP | Atlas Admin API invoice endpoints | Atlas Billing and Invoice Anatomy; Atlas Billing Mechanics and Cost Visibility | dr | covered | mongodb-cohort-e1ba7cea1572 | — |
| 338 | 3.050 | SKIP | Atlas Infinite compute auto-scaling | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 339 | 3.050 | SKIP | Auto-scaling tier ranges | Atlas Cluster Topology and Tier Economics; Cluster Tier Families and Hourly Pricing (General vs Low-CPU vs NVMe) | dr | covered | mongodb-cohort-900a68979346 | — |
| 340 | 3.050 | SKIP | Backup and PITR cost modelling | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator) | dr | covered | mongodb-cohort-3b41fd0d3ebd | — |
| 341 | 3.050 | SKIP | Cedar policy authoring for cluster size and autoscaling caps | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Resource Policy Drift Monitoring (nonCompliantResources) | dr | covered | mongodb-cohort-900a68979346 | — |
| 342 | 3.050 | SKIP | Multi-region cluster cost premium | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Region and Cloud Provider Price Differentials for Atlas | dr | covered | mongodb-cohort-3b41fd0d3ebd | — |
| 343 | 3.050 | SKIP | Pause/resume automation with Terraform or GitHub Actions | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | covered | mongodb-cohort-e1ba7cea1572 | — |
| 344 | 3.050 | SKIP | Right-sizing from Atlas metrics | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator) | dr | covered | mongodb-cohort-900a68979346 | — |
| 345 | 3.025 | RESEARCH | EU Data Act switching charges and in-parallel egress | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 346 | 3.000 | SKIP | Rolling index builds as a resource-limited alternative | Index build resource limits (maxNumActiveUserIndexBuilds, disk space) | dr | frontier | mongodb-cohort-23dbaf3674d0 | — |
| 347 | 3.000 | RESEARCH | Automated Embedding (autoEmbed) quantization types | Atlas Vector Search automatic quantization and rescoring | dr | covered | mongodb-cohort-97c656997272 | — |
| 348 | 3.000 | RESEARCH | Automated Embedding (autoEmbed) quantization types including binaryNoRescore | Atlas Vector Search automatic quantization and rescoring | dr | covered | mongodb-cohort-97c656997272 | — |
| 349 | 3.000 | RESEARCH | Spill WiredTiger instance cache | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-1f33141d477d | — |
| 350 | 3.000 | RESEARCH | WiredTiger spill instance cache | WiredTiger cache eviction and dirty ratio | dr | frontier | mongodb-cohort-1f33141d477d | — |
| 351 | 3.000 | SKIP | $groupByDistinct internal stage | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | covered | mongodb-cohort-468120abc19f | — |
| 352 | 3.000 | SKIP | Analytics node tier prorating | Atlas Cluster Topology and Tier Economics; Replica Set Node Topology Cost | dr | covered | mongodb-cohort-900a68979346 | — |
| 353 | 3.000 | SKIP | Atlas-only feature lock-in and exit cost | Atlas Pricing Programs, Cost Governance and TCO; Self-Managed MongoDB vs Atlas TCO | dr | frontier | mongodb-cohort-66670eb51cca | — |
| 354 | 3.000 | SKIP | AWS Marketplace EDP drawdown for Atlas | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit) | dr | frontier | mongodb-cohort-66670eb51cca | — |
| 355 | 3.000 | SKIP | Backup and PIT oplog storage region billing | Atlas Cluster Topology and Tier Economics; Multi-Region and Cross-Cloud Data Transfer Costs | dr | frontier | mongodb-cohort-bc364323a011 | — |
| 356 | 3.000 | SKIP | Cost Explorer filters for AI services | Atlas AI Services Pricing (Agent Engine and Voyage AI); Atlas Pricing Programs, Cost Governance and TCO | dr | frontier | mongodb-cohort-bc364323a011 | — |
| 357 | 3.000 | SKIP | Query limits and billing alerts for archive spend | Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation); Storage and Data-Lifecycle Cost Levers | dr | frontier | mongodb-cohort-bc364323a011 | — |
| 358 | 3.000 | SKIP | Support line items per cloud provider on invoices | Atlas Billing Mechanics and Cost Visibility; Atlas Support Plan Pricing | dr | covered | mongodb-cohort-7b4b502e3f24 | — |
| 359 | 2.975 | RESEARCH | Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure) | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-e79d2e686285 | — |
| 360 | 2.975 | RESEARCH | Cloud exit-credit programs and EU Data Act in-parallel egress | Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress) | dr | frontier | mongodb-cohort-de1c0f2fac41 | — |
| 361 | 2.975 | RESEARCH | Atlas Infinite oplog and storage cost | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-bc364323a011 | — |
| 362 | 2.950 | RESEARCH | Idle-spend and minimum-commit economics of serverless vector stores | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | covered | mongodb-cohort-e0a1491db062 | — |
| 363 | 2.950 | RESEARCH | Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors | Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB) | dr | frontier | mongodb-cohort-fb2e5c6c7cc5 | — |
| 364 | 2.950 | SKIP | Enterprise Advanced licensing economics | Atlas Pricing Programs, Cost Governance and TCO; Self-Managed MongoDB vs Atlas TCO | dr | frontier | mongodb-cohort-773223a064d7 | — |
| 365 | 2.950 | SKIP | Project-level billing change alerts | Atlas Billing Mechanics and Cost Visibility; Billing Alerts and Budget Controls | dr | frontier | mongodb-cohort-cc7805a2b4af | — |
| 366 | 2.950 | SKIP | Shared-cost splitting for Atlas projects | Atlas Billing Mechanics and Cost Visibility; Resource Tags and Cost Allocation (Showback/Chargeback) | dr | frontier | mongodb-cohort-cc7805a2b4af | — |
| 367 | 2.925 | RESEARCH | Refresh scheduling with Atlas Scheduled Triggers | Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern) | dr | frontier | mongodb-cohort-d9cc5fb1cc98 | — |
| 368 | 2.925 | RESEARCH | positional index path caveat | explain multiKeyPaths interpretation | dr | frontier | mongodb-cohort-23dbaf3674d0 | — |
| 369 | 2.900 | RESEARCH | maxEstimatedScanBytes collection-scan rejection (9.0) | Operation rejection filters | dr | frontier | mongodb-cohort-4b089bde7a44 | — |
| 370 | 2.900 | SKIP | Network (wire) compression | Storage and Data-Lifecycle Cost Levers; WiredTiger Block and Prefix Compression as Storage Cost Lever | dr | frontier | mongodb-cohort-1537f1c9f03c | — |
| 371 | 2.875 | RESEARCH | Side bucket catalog | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-bd6489c69c3d | — |
| 372 | 2.875 | RESEARCH | Side bucket catalog for time series updates and deletes | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-bd6489c69c3d | — |
| 373 | 2.850 | RESEARCH | Oplog sizing in Kubernetes operators and managed MongoDB-compatible services | Oplog sizing under storage auto-scaling | dr | frontier | mongodb-cohort-1df99675f929 | — |
| 374 | 2.850 | RESEARCH | Partition Field Type Enum Docs-vs-Spec Disagreement | Online Archive partition-field selection | dr | frontier | mongodb-cohort-f3e3c14c2e33 | — |
| 375 | 2.850 | SKIP | Auto-scaling min/max bounds and Terraform drift | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | frontier | mongodb-cohort-c33aa5e84f28 | — |
| 376 | 2.850 | SKIP | Config shard versus dedicated config server cost | Atlas Cluster Topology and Tier Economics; Sharded Cluster Cost Economics | dr | frontier | mongodb-cohort-cc7805a2b4af | — |
| 377 | 2.850 | SKIP | MongoDB Charts billing dashboards | Atlas Billing Mechanics and Cost Visibility; Resource Tags and Cost Allocation (Showback/Chargeback) | dr | frontier | mongodb-cohort-cc7805a2b4af | — |
| 378 | 2.850 | SKIP | Persisting index usage metrics across restarts (PMM/monitoring) | MongoDB Explain Plans, Query Planner and Plan Cache | dr | frontier | mongodb-cohort-06b0f31e2303 | — |
| 379 | 2.850 | SKIP | Scale-down tuning for spiky batch workloads | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Scheduled and Predictive Scaling for Atlas Cost | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 380 | 2.825 | RESEARCH | Amazon DocumentDB profiler (CloudWatch Logs) | Database Profiler vs Query Profiler | dr | covered | mongodb-cohort-9767e9fb3174 | — |
| 381 | 2.825 | RESEARCH | Bucket catalog stripes, state registry and eras | Bucket catalog memory and closure reasons | dr | covered | mongodb-cohort-bd6489c69c3d | — |
| 382 | 2.800 | SKIP | Client-side operation timeout (CSOT) | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | dr | covered | mongodb-cohort-9cff09d95361 | — |
| 383 | 2.800 | SKIP | Collation-based case-insensitive indexes as a $regex alternative | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | dr | frontier | mongodb-cohort-06b0f31e2303 | — |
| 384 | 2.800 | SKIP | Intra-cluster replication transfer billing | Atlas Cluster Topology and Tier Economics; Replica Set Node Topology Cost | dr | frontier | mongodb-cohort-69b213634bbc | — |
| 385 | 2.800 | SKIP | Retroactive support billing on reactivation | Atlas Billing Mechanics and Cost Visibility; Atlas Support Plan Pricing | dr | frontier | mongodb-cohort-69b213634bbc | — |
| 386 | 2.800 | SKIP | Time series collection expireAfterSeconds | Data Lifecycle Cost Model (TTL vs Online Archive vs Data Federation); Storage and Data-Lifecycle Cost Levers | dr | frontier | mongodb-cohort-d945bf6ed1c3 | — |
| 387 | 2.775 | RESEARCH | Lucene BBQ binary quantization compared with Atlas binary quantization | Atlas Vector Search automatic quantization and rescoring | dr | frontier | mongodb-cohort-fb2e5c6c7cc5 | — |
| 388 | 2.750 | SKIP | Atlas billing alert configuration via Admin API | Atlas Pricing Programs, Cost Governance and TCO; Cost Governance Guardrails (Resource Policies and IaC Cost Controls) | dr | frontier | mongodb-cohort-69b213634bbc | — |
| 389 | 2.725 | SKIP | Rolling index build key inconsistency incident | Rolling index builds | dr | frontier | mongodb-cohort-02055194c32b | — |
| 390 | 2.725 | SKIP | Rolling index build table-logging incident | Rolling index builds | dr | frontier | mongodb-cohort-06b0f31e2303 | — |
| 391 | 2.725 | RESEARCH | Percona PMM mongolog query source | Database Profiler vs Query Profiler | dr | frontier | mongodb-cohort-2672a54425cd | — |
| 392 | 2.700 | RESEARCH | Partition Field Cardinality and the 2023-06-07 Storage Engine Change | Online Archive partition-field selection | dr | frontier | mongodb-cohort-a29d8407e9dc | — |
| 393 | 2.700 | SKIP | Atlas PrivateLink regional endpoint rates | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Region and Cloud Provider Price Differentials for Atlas | dr | frontier | mongodb-cohort-18067a89fb07 | — |
| 394 | 2.650 | SKIP | Atlas included-replica pricing vs per-instance HA billing | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB) | dr | frontier | mongodb-cohort-69b213634bbc | — |
| 395 | 2.650 | SKIP | Egress and data transfer estimation | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Pre-Deployment Cost Estimation and Sizing Model (Atlas Pricing Calculator) | dr | frontier | mongodb-cohort-18067a89fb07 | — |
| 396 | 2.650 | SKIP | queryKnobs and per-command querySettings | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | dr | frontier | mongodb-cohort-2672a54425cd | — |
| 397 | 2.650 | SKIP | Re-indexing cost when changing numDimensions | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Matryoshka Dimension Truncation for Vector Storage Cost | dr | frontier | mongodb-cohort-019ea6c7f819 | — |
| 398 | 2.650 | SKIP | Untagged spend reporting | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Terraform Tag Enforcement and Policy-as-Code for Atlas Cost | dr | frontier | mongodb-cohort-86157c3fe16f | — |
| 399 | 2.600 | SKIP | Atlas Admin API billing alert configuration | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets) | dr | frontier | mongodb-cohort-019ea6c7f819 | — |
| 400 | 2.600 | SKIP | Atlas Admin API rate limiting for scheduled polling | Atlas Slow-Query Log and Performance Advisor Automation | dr | frontier | mongodb-cohort-f2bea3de4b89 | — |
| 401 | 2.600 | SKIP | Cross-vendor FOCUS pipelines (BigQuery/Snowflake) | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets) | dr | frontier | mongodb-cohort-4612d59db35d | — |
| 402 | 2.600 | SKIP | DynamoDB on-demand vs provisioned break-even | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB) | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 403 | 2.600 | SKIP | FOCUS column mapping for Atlas credits | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; FinOps Tooling for Atlas (FOCUS Ingestion Anomaly Detection Budgets) | dr | frontier | mongodb-cohort-019ea6c7f819 | — |
| 404 | 2.600 | SKIP | Linking Atlas orgs to marketplace billing accounts | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cloud Commit Drawdown via Atlas Marketplace (EDP MACC GCP commit) | dr | frontier | mongodb-cohort-019ea6c7f819 | — |
| 405 | 2.550 | SKIP | Conftest/OPA rules over terraform show -json plans | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Terraform Tag Enforcement and Policy-as-Code for Atlas Cost | dr | frontier | mongodb-cohort-f2bea3de4b89 | — |
| 406 | 2.550 | SKIP | Search node tier sizing for vector indexes | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Matryoshka Dimension Truncation for Vector Storage Cost | dr | frontier | mongodb-cohort-fb2e5c6c7cc5 | — |
| 407 | 2.450 | SKIP | Backup storage rates by region | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Region and Cloud Provider Price Differentials for Atlas | dr | frontier | mongodb-cohort-a9c2cc4bbf19 | — |
| 408 | 2.450 | SKIP | Cosmos DB RU estimation for MongoDB workloads | Atlas Cost Planning: Region Pricing, Estimation, Scheduled Scaling and Competitor TCO; Cross-Vendor Document Database Pricing Comparison (DocumentDB Cosmos DB DynamoDB) | dr | frontier | mongodb-cohort-97d0be9985d2 | — |
| 409 | 2.450 | SKIP | Proportional minimum-commit allocation | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cross-Organization Billing and Linked Invoices | dr | frontier | mongodb-cohort-86157c3fe16f | — |
| 410 | 2.450 | SKIP | Scheduled compliance polling and alerting | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Resource Policy Drift Monitoring (nonCompliantResources) | dr | frontier | mongodb-cohort-325a09333de2 | — |
| 411 | 2.400 | RESEARCH | PostgreSQL invalid indexes from failed CONCURRENTLY builds | Resumable index builds | dr | frontier | mongodb-cohort-06b0f31e2303 | — |
| 412 | 2.400 | RESEARCH | SQL Server resumable online index operations | Resumable index builds | dr | frontier | mongodb-cohort-e298d0919726 | — |
| 413 | 2.400 | SKIP | Atlas Admin API pending-invoice tags field | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Terraform Tag Enforcement and Policy-as-Code for Atlas Cost | dr | frontier | mongodb-cohort-f2bea3de4b89 | — |
| 414 | 2.350 | SKIP | Journal compression | Storage and Data-Lifecycle Cost Levers; WiredTiger Block and Prefix Compression as Storage Cost Lever | dr | frontier | mongodb-cohort-dab118cd8660 | — |
| 415 | 2.300 | RESEARCH | PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY | Resumable index builds | dr | frontier | mongodb-cohort-e298d0919726 | — |
| 416 | 2.300 | SKIP | Billing incidents and refunds | Atlas Billing and Invoice Anatomy; Atlas Billing Mechanics and Cost Visibility | dr | frontier | mongodb-cohort-3da97516cefc | — |
| 417 | 2.250 | SKIP | Unlinking an organization | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cross-Organization Billing and Linked Invoices | dr | frontier | mongodb-cohort-86157c3fe16f | — |
| 418 | 2.200 | RESEARCH | SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints | Resumable index builds | dr | frontier | mongodb-cohort-e298d0919726 | — |
| 419 | 2.150 | SKIP | Cosmos DB for MongoDB wildcard differences | MongoDB Wildcard and Hidden Indexes, Index Builds and Index Overhead | dr | frontier | mongodb-cohort-86b55445bd3c | — |
| 420 | 2.000 | SKIP | Charts billing ingestion for linked orgs | Atlas Cost Commitments, Cross-Org Billing and FinOps Tooling; Cross-Organization Billing and Linked Invoices | dr | frontier | mongodb-cohort-3da97516cefc | — |
| 421 | — | — | Atlas CLI | MongoDB Developer Patterns | revisit | refresh-review | mongodb-cohort-f2bea3de4b89 | — |
| 422 | — | — | Atlas cluster tiers (M30) & major-version upgrade mechanics | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9edc5d1a1f81 | — |
| 423 | — | — | Atlas Service Accounts | MongoDB Atlas | dr | covered | mongodb-cohort-bef2224dcee8 | — |
| 424 | — | — | Atlas Triage Workflows | Atlas Diagnostics Expert | revisit | refresh-review | mongodb-cohort-2255fa8f9dbd | — |
| 425 | — | — | autoCompact and Replica-Set Write Blocking | MongoDB autoCompact | dr | covered | mongodb-cohort-924cda5ff47d | — |
| 426 | — | — | autoCompact Atlas-Specific Behavior | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 427 | — | — | autoCompact Checkpoint Interaction | MongoDB autoCompact | dr | covered | mongodb-cohort-25c35d51d44b | — |
| 428 | — | — | autoCompact Cluster Topology Behavior | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 429 | — | — | autoCompact freeSpaceTargetMB Gating | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 430 | — | — | autoCompact Lifecycle and Persistence | MongoDB autoCompact | dr | covered | mongodb-cohort-4476e89804ea | — |
| 431 | — | — | autoCompact runOnce vs Continuous Mode | MongoDB autoCompact | dr | covered | mongodb-cohort-1ff7eed674cb | — |
| 432 | — | — | Background-Compaction Skip/EMA Heuristic | WiredTiger Compaction Algorithm | revisit | refresh-review | mongodb-cohort-acec48250f2d | — |
| 433 | — | — | Delbridge Data API | Atlas Data API Removal | dr | covered | mongodb-cohort-816c84e8e2ba | — |
| 434 | — | — | Diagnostic Tool Design | Atlas Diagnostics Expert | revisit | refresh-review | mongodb-cohort-2255fa8f9dbd | — |
| 435 | — | — | Driver Examples | MongoDB Transactions | dr | covered | mongodb-cohort-ce699f367ef9 | — |
| 436 | — | — | Error Codes and Troubleshooting | MongoDB Developer Patterns | revisit | refresh-review | mongodb-cohort-aadbc815fdee | — |
| 437 | — | — | Express MongoDB Driver Pattern | Atlas Data API Removal | dr | covered | mongodb-cohort-ce699f367ef9 | — |
| 438 | — | — | FastAPI Motor Pattern | Atlas Data API Removal | dr | covered | mongodb-cohort-816c84e8e2ba | — |
| 439 | — | — | FTDC and Log Tooling | Atlas Diagnostics Expert | revisit | refresh-review | mongodb-cohort-2255fa8f9dbd | — |
| 440 | — | — | KB-Backed Troubleshooting | Atlas Diagnostics Expert | revisit | refresh-review | mongodb-cohort-2255fa8f9dbd | — |
| 441 | — | — | MongoDB 8.0 performance changes & read-path regressions vs 7.0 | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9926293a8ae6 | — |
| 442 | — | — | MongoDB Atlas Analytics Node | MongoDB Atlas | dr | covered | mongodb-cohort-5432c1b568fa | — |
| 443 | — | — | MongoDB Atlas Data Federation | MongoDB Atlas | revisit | refresh-review | mongodb-cohort-9ee49621e5ca | — |
| 444 | — | — | MongoDB Atlas Triggers and Functions | MongoDB Atlas | dr | covered | mongodb-cohort-5432c1b568fa | — |
| 445 | — | — | MongoDB autoCompact | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9926293a8ae6 | — |
| 446 | — | — | MongoDB Backup and Restore | MongoDB Atlas | dr | covered | mongodb-cohort-b40001359bc9 | — |
| 447 | — | — | MongoDB Connection String URI | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9926293a8ae6 | — |
| 448 | — | — | MongoDB Driver Internals | MongoDB Developer Patterns | dr | covered | mongodb-cohort-ce699f367ef9 | — |
| 449 | — | — | MongoDB Drivers | MongoDB Developer Patterns | revisit | refresh-review | mongodb-cohort-34d60aede5df | — |
| 450 | — | — | MongoDB Java driver 5.x version timeline & 8.0 compatibility | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-ce699f367ef9 | — |
| 451 | — | — | MongoDB Performance Benchmarking | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-9926293a8ae6 | — |
| 452 | — | — | MongoDB Performance Regression Detection and Testing Methodology | MongoDB Performance Benchmarking | dr | covered | mongodb-cohort-123beacc8566 | — |
| 453 | — | — | MongoDB Performance Troubleshooting | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-993d4fac083c | — |
| 454 | — | — | MongoDB Spark Connector and Databricks Integration | MongoDB Developer Patterns | dr | covered | mongodb-cohort-9145188a1779 | — |
| 455 | — | — | MongoDB Stress, Soak, and Chaos-Resilience Testing | MongoDB Expert Knowledge | dr | covered | mongodb-cohort-01ed1ee15811 | — |
| 456 | — | — | mongosh Reference | MongoDB Developer Patterns | revisit | refresh-review | mongodb-cohort-065b5964e6f4 | — |
| 457 | — | — | Performance Impact | MongoDB Transactions | dr | covered | mongodb-cohort-f0e4301e68e0 | — |
| 458 | — | — | RESTHeart | Atlas Data API Removal | dr | covered | mongodb-cohort-9d1235b3ac64 | — |
| 459 | — | — | Retryable Transactions | MongoDB Transactions | dr | covered | mongodb-cohort-cf716ce2ed75 | — |
| 460 | — | — | Transaction Limits | MongoDB Transactions | dr | covered | mongodb-cohort-cf716ce2ed75 | — |
| 461 | — | — | WiredTiger Compaction Algorithm | MongoDB autoCompact | revisit | refresh-review | mongodb-cohort-5c4fb85a6f32 | — |

## Original labels and parent provenance

Every label remains assigned to its canonical identity in the JSON inventory. Repeated input occurrences remain separate.

- **Time series cardinality and metaField design** (`mongodb-37c367b29bc32cb1`): Time series cardinality and metaField design
- **Shard key index constraints when dropping or hiding indexes** (`mongodb-efd576940abfe93a`): Shard key index constraints when dropping or hiding indexes
- **Connection pool sizing and connection-storm control for Atlas (serverless and Lambda clients)** (`mongodb-2f1fbe31e1058a42`): Connection pool sizing and connection-storm control for Atlas (serverless and Lambda clients)
- **Hot shard diagnosis and shard key remediation** (`mongodb-e18f2f1019762eea`): Hot shard diagnosis and shard key remediation
- **$queryStats aggregation stage** (`mongodb-fc9325d08a92f24b`): $queryStats aggregation stage
- **Reading sharded explain output (shards, SINGLE_SHARD, SHARD_MERGE)** (`mongodb-9cfbe719bb847f18`): Reading sharded explain output (shards, SINGLE_SHARD, SHARD_MERGE)
- **analyzeShardKey and query sampling** (`mongodb-779f34dfa36f6756`): analyzeShardKey and query sampling
- **analyzeShardKey query sampling and candidate-key scoring** (`mongodb-fe8dc1ff0a3946a4`): analyzeShardKey query sampling and candidate-key scoring
- **Delete propagation and reconciliation for $merge-maintained views** (`mongodb-ca53ac7eb7938f77`): Delete propagation and reconciliation for $merge-maintained views
- **Index build commit quorum and hung builds** (`mongodb-4a35364ee8642200`): Index build commit quorum and hung builds
- **$queryStats and $currentOp as alternatives to the profiler** (`mongodb-43e566a9f0877fdd`): $queryStats and $currentOp as alternatives to the profiler
- **Hashed and compound hashed shard keys and index coverage** (`mongodb-7fbf6e87171ca9e8`): Hashed and compound hashed shard keys and index coverage
- **Idempotent incremental refresh design for $merge (high-water marks, delete handling)** (`mongodb-cda5307f33b4a8cd`): Idempotent incremental refresh design for $merge (high-water marks, delete handling)
- **Time series bucketing parameters: granularity, bucketMaxSpanSeconds, bucketRoundingSeconds** (`mongodb-e6ac0ae929aaad78`): Time series bucketing parameters: granularity, bucketMaxSpanSeconds, bucketRoundingSeconds
- **WiredTiger cache sizing and working-set fit** (`mongodb-0831aa6a730c33af`): WiredTiger cache sizing and working-set fit
- **Atlas storage auto-scaling triggers, cooldowns and write blocking** (`mongodb-307154446e50395e`): Atlas storage auto-scaling triggers, cooldowns and write blocking
- **Unique and TTL index side effects on removal** (`mongodb-c6e55a2528d91131`): Unique and TTL index side effects on removal
- **Index filters (planCacheSetFilter) deprecation and migration to query settings** (`mongodb-55e65f5d4cc3196b`): Index filters (planCacheSetFilter) deprecation and migration to query settings
- **Oplog minimum retention window and storage auto-scaling** (`mongodb-491fab6d89343906`): Oplog minimum retention window and storage auto-scaling
- **Read concern available, secondary reads and orphaned documents** (`mongodb-c0c218d6058d6708`): Read concern available, secondary reads and orphaned documents
- **Blocking sort memory limit and allowDiskUse** (`mongodb-2ec006134792b0c5`): Blocking sort memory limit and allowDiskUse
- **analyzeShardKey workload sampling** (`mongodb-82725d8090f62c84`): analyzeShardKey workload sampling
- **Atlas Query Profiler and slow-ops logs for shape discovery** (`mongodb-c0b4ec4abda68f2a`): Atlas Query Profiler and slow-ops logs for shape discovery
- **Oplog capacity for initial sync, live migration and bulk loads** (`mongodb-09bbc3b6858039a7`): Oplog capacity for initial sync, live migration and bulk loads
- **Query settings: index hints and queryFramework (persistent query settings)** (`mongodb-ca205f42c57aed6d`): Query settings: index hints and queryFramework (persistent query settings)
- **setQuerySettings index hints and queryFramework** (`mongodb-d10b2336807b3bca`): setQuerySettings index hints and queryFramework
- **Snapshot reads (atClusterTime) and history window sizing on secondaries** (`mongodb-1069c8846346b64e`): Snapshot reads (atClusterTime) and history window sizing on secondaries
- **Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds** (`mongodb-8adf3e10aee700b8`): Snapshot reads on secondaries and minSnapshotHistoryWindowInSeconds
- **Time series backfill ordering and batching** (`mongodb-c9027de218a3e1bb`): Time series backfill ordering and batching
- **Two-phase write protocol and writes without the shard key** (`mongodb-acb9c6f2bef7be75`): Two-phase write protocol and writes without the shard key
- **Resume-from-last-key pattern for killed cursors** (`mongodb-87979fda64c57aa4`): Resume-from-last-key pattern for killed cursors
- **Distributed Sharded Transactions** (`mongodb-fa66e239fa751be7`): Distributed Sharded Transactions
- **Transaction Anti-Patterns** (`mongodb-4928c87584404e5d`): Transaction Anti-Patterns
- **Balancer data-size policy and zone-aware migration** (`mongodb-ba374350fd1b2bfc`): Balancer data-size policy and zone-aware migration
- **Vector index memory sizing and quantization trade-offs on Search Nodes** (`mongodb-ba7654359cbe0bed`): Vector index memory sizing and quantization trade-offs on Search Nodes
- **Atlas disk write-blocking thresholds and recovery** (`mongodb-929575493d4087d5`): Atlas disk write-blocking thresholds and recovery
- **Unique, TTL and shard-key indexes that read as unused** (`mongodb-07243021cb28b849`): Unique, TTL and shard-key indexes that read as unused
- **hasNextPage without computing total pages** (`mongodb-374a48a694584c66`): hasNextPage without computing total pages
- **Online Archive Data Access and Data Seek Query Cost Model** (`mongodb-2f4168ceffea93a9`): Online Archive Data Access and Data Seek Query Cost Model
- **Compound shard-key prefix targeting** (`mongodb-ce157abec5c6e09d`): Compound shard-key prefix targeting
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
- **mongot replication lag, oplog window and index rebuild cost** (`mongodb-9f2f133f2977052b`): mongot replication lag, oplog window and index rebuild cost
- **Compound-index prefix and sort-direction compatibility** (`mongodb-d074d6ebe3c3758e`): Compound-index prefix and sort-direction compatibility
- **Reading indexed `$or` plans with explain** (`mongodb-3f1dc80ac02788d8`): Reading indexed `$or` plans with explain
- **Balancer tuning and chunk migration cost** (`mongodb-812fc7cfa213d693`): Balancer tuning and chunk migration cost
- **Query shape and queryShapeHash stability** (`mongodb-ba11218fbabf4ce3`): Query shape and queryShapeHash stability
- **Query shapes and queryShapeHash stability** (`mongodb-3fcfc50df3a9d30a`): Query shapes and queryShapeHash stability
- **WiredTiger checkpoints and checkpoint duration** (`mongodb-e6181cc3d05b4127`): WiredTiger checkpoints and checkpoint duration
- **Commit quorum and the vote-to-commit point of no return** (`mongodb-5f54c51046d88611`): Commit quorum and the vote-to-commit point of no return
- **Keyset (resume) pagination for restartable cursors** (`mongodb-7a91ee8d2368657f`): Keyset (resume) pagination for restartable cursors
- **Terraform effective fields and auto-scaling drift** (`mongodb-6da6e3ca2340a232`): Terraform effective fields and auto-scaling drift
- **Atlas Vector Search RAM sizing and automatic quantization** (`mongodb-7a014dcb5be07f3c`): Atlas Vector Search RAM sizing and automatic quantization
- **Hashed shard-key write distribution and local index locality** (`mongodb-fa3aaf6e5b264c5d`): Hashed shard-key write distribution and local index locality
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
- **$indexStats usage statistics and their reset conditions** (`mongodb-c0603c927eb5e2af`): $indexStats usage statistics and their reset conditions
- **Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes)** (`mongodb-5cf3317db9573e29`): Index build memory limit and external sorter spill (maxIndexBuildMemoryUsageMegabytes)
- **Atlas compute auto-scaling for sharded clusters** (`mongodb-8a8588d225b66629`): Atlas compute auto-scaling for sharded clusters
- **Balancer, chunk migration and jumbo chunk remediation** (`mongodb-e9767d35bd3564d7`): Balancer, chunk migration and jumbo chunk remediation
- **Commit quorum and votingMembers** (`mongodb-bf66bee7b46e6125`): Commit quorum and votingMembers
- **Orphaned documents and read concern available versus local** (`mongodb-7b6bda9bc92b8d74`): Orphaned documents and read concern available versus local
- **Safe index removal: locks, rollback and regression checks** (`mongodb-639b9604ad5f8611`): Safe index removal: locks, rollback and regression checks
- **SHARDING_FILTER stage and chunkSkips** (`mongodb-4f273eb41d058596`): SHARDING_FILTER stage and chunkSkips
- **Atlas Search index rebuild after migration** (`mongodb-a79da32a252623e6`): Atlas Search index rebuild after migration
- **readConcern available on sharded clusters** (`mongodb-4baf9880f7b8ff7e`): readConcern available on sharded clusters
- **WiredTiger cache sizing and memory fragmentation** (`mongodb-ed3d0074fb4a0951`): WiredTiger cache sizing and memory fragmentation
- **Sampling CE accuracy under sparse sample matches** (`mongodb-96e56dfd23741c03`): Sampling CE accuracy under sparse sample matches
- **ESR guideline and $in placement in compound indexes** (`mongodb-7410bfb0be0aa4ce`): ESR guideline and $in placement in compound indexes
- **WiredTiger checkpoints and dirty-page write cost** (`mongodb-bea205b365b40fc6`): WiredTiger checkpoints and dirty-page write cost
- **Atlas Search Nodes cost floor and co-located versus dedicated search** (`mongodb-81d16539892f095e`): Atlas Search Nodes cost floor and co-located versus dedicated search
- **Chunk migration commit, range deleter and orphan cleanup internals** (`mongodb-b61f815eb024910f`): Chunk migration commit, range deleter and orphan cleanup internals
- **Application-level dual-write migration pattern** (`mongodb-f2eecec57154f31b`): Application-level dual-write migration pattern
- **Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams** (`mongodb-4b2ca1d9c19e5ee0`): Sync pipeline cost: CDC (Debezium, Kafka, Monstache) vs native change streams
- **Multi-Document Transactions** (`mongodb-c9e37257a87fa913`): Multi-Document Transactions; Multi-document Transactions
- **Hashed, ranged and compound hashed shard keys** (`mongodb-6fb4e66a9e4066ec`): Hashed, ranged and compound hashed shard keys
- **Zone sharding and region-aware shard keys** (`mongodb-96f5d5a08cab86fe`): Zone sharding and region-aware shard keys
- **Atlas Vector Search numCandidates tuning and recall measurement against ENN** (`mongodb-ac984432ae410e27`): Atlas Vector Search numCandidates tuning and recall measurement against ENN
- **Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis)** (`mongodb-90c2d5519c3220af`): Parsing the mongod slow-query log (id 51803, workingMillis, durationMillis)
- **Atlas Stream Processing streaming materialized views** (`mongodb-fa4d655140a67c4f`): Atlas Stream Processing streaming materialized views
- **Reducing shard count and unsharding collections on Atlas** (`mongodb-e55deac1bde07add`): Reducing shard count and unsharding collections on Atlas
- **Balancer windows and per-collection balancing control** (`mongodb-696982ad112245fe`): Balancer windows and per-collection balancing control
- **Destination temporary scaling and post-cutover right-sizing** (`mongodb-5ccf34e9dd7c904e`): Destination temporary scaling and post-cutover right-sizing
- **dropIndexes locking and in-flight query behavior** (`mongodb-dd277d166251c39f`): dropIndexes locking and in-flight query behavior
- **Hidden indexes as a safe drop trial** (`mongodb-3dc7ee2ae326a104`): Hidden indexes as a safe drop trial
- **mongod diagnostic log slow-query format and slowOpSampleRate** (`mongodb-b548b9347267db0b`): mongod diagnostic log slow-query format and slowOpSampleRate
- **Per-shard disk IOPS and storage constraints** (`mongodb-f5ea1a5b9eabc238`): Per-shard disk IOPS and storage constraints
- **Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes** (`mongodb-ba0a48b5785697ff`): Atlas Search Node sizing: high-CPU vs low-CPU vs storage-optimized classes
- **Redundant (prefix) index detection for compound indexes** (`mongodb-4e32a19d1f2c5971`): Redundant (prefix) index detection for compound indexes
- **Application-thread eviction and cache stalls** (`mongodb-9867c635985c54ea`): Application-thread eviction and cache stalls
- **Flex versus Dedicated boundary: ops-per-second pricing and missing features** (`mongodb-9d93aba50859f3d4`): Flex versus Dedicated boundary: ops-per-second pricing and missing features
- **metaField cardinality and active-bucket count** (`mongodb-3d2f9fb21415d4cc`): metaField cardinality and active-bucket count
- **MongoDB Node.js driver pool sizing under Lambda concurrency** (`mongodb-9a69c000f8846b80`): MongoDB Node.js driver pool sizing under Lambda concurrency
- **serverStatus bucketCatalog and collStats timeseries counters** (`mongodb-0aeaaf1da0623b3c`): serverStatus bucketCatalog and collStats timeseries counters
- **moveCollection and unshardCollection** (`mongodb-0014a99f0d101e15`): moveCollection and unshardCollection
- **Cross-cloud application-tier placement and Atlas internet egress** (`mongodb-20ae69c53f13d417`): Cross-cloud application-tier placement and Atlas internet egress
- **mongosync reversible sync and the rollback window** (`mongodb-b1abe7bf26bd5cf5`): mongosync reversible sync and the rollback window
- **Hashed versus ranged shard-key tradeoffs** (`mongodb-991d5f922cc78788`): Hashed versus ranged shard-key tradeoffs
- **WiredTiger block reuse, file fragmentation and freeStorageSize** (`mongodb-e5de220a8f56a644`): WiredTiger block reuse, file fragmentation and freeStorageSize
- **Write amplification and cache cost of unused indexes** (`mongodb-d859a3df74f89ce0`): Write amplification and cache cost of unused indexes
- **Plan cache flushes on index DDL** (`mongodb-9f10df9b9162e00b`): Plan cache flushes on index DDL
- **Archive and TTL data lifecycle followed by compaction** (`mongodb-bc36eea828943d88`): Archive and TTL data lifecycle followed by compaction
- **Replica set oplog window and initial sync** (`mongodb-3e7a15a9315bdf6a`): Replica set oplog window and initial sync
- **Zone sharding for hardware-tiered shards** (`mongodb-7342a6b00fb95f34`): Zone sharding for hardware-tiered shards
- **Zone sharding for tiered hardware (hot, warm, cold)** (`mongodb-3ef0d50044b95622`): Zone sharding for tiered hardware (hot, warm, cold)
- **Atlas Live Migration pull versus push versus standalone mongosync selection** (`mongodb-2863c01b9e032316`): Atlas Live Migration pull versus push versus standalone mongosync selection
- **VPC Peering GCP Atlas** (`mongodb-f305dcbf647fed32`): VPC Peering GCP Atlas
- **Multi-planner trial period and candidate plan ranking** (`mongodb-5efaa7e8d778364a`): Multi-planner trial period and candidate plan ranking
- **Zone sharding and Global Cluster shard keys** (`mongodb-097c5c30db2cddc7`): Zone sharding and Global Cluster shard keys
- **Hashed shard keys and index support** (`mongodb-b3f8a3c9021603e8`): Hashed shard keys and index support
- **Index filters and query settings versus hidden indexes** (`mongodb-3cb7eb42f317b1d7`): Index filters and query settings versus hidden indexes
- **Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete)** (`mongodb-c4f1160e54c251fc`): Balancer control for long reads (balancing window, configureCollectionBalancing, _waitForDelete)
- **Per-shard compute auto-scaling rules and limits on Atlas** (`mongodb-69f911f95ca28217`): Per-shard compute auto-scaling rules and limits on Atlas
- **Reverse sync and rollback-window economics** (`mongodb-7655d46620fe7e30`): Reverse sync and rollback-window economics
- **Per-shard IOPS and Gen2 storage on Atlas** (`mongodb-ed34f8099debb39e`): Per-shard IOPS and Gen2 storage on Atlas
- **Partition Field Immutability and Merge-Delete-Recreate Migration** (`mongodb-3262e83e6bffc840`): Partition Field Immutability and Merge-Delete-Recreate Migration
- **MongoDB cache-pressure monitor and ticket admission** (`mongodb-df5f7de57f6ca275`): MongoDB cache-pressure monitor and ticket admission
- **Cache stampede protection: leases, request coalescing, TTL jitter** (`mongodb-706c1e6361758778`): Cache stampede protection: leases, request coalescing, TTL jitter
- **$out-based time series rewrite and cutover** (`mongodb-869013037a0a4c33`): $out-based time series rewrite and cutover
- **Partition Field Leftmost-Prefix Ordering** (`mongodb-82062063877c20d7`): Partition Field Leftmost-Prefix Ordering
- **Reshard to the same key for adding and removing shards** (`mongodb-33676740c89bacf0`): Reshard to the same key for adding and removing shards
- **Dedicated Search Node storage and compute sizing** (`mongodb-e2b4909feecca57a`): Dedicated Search Node storage and compute sizing
- **Plan cache entry lifecycle: Inactive and Active entries and works growth** (`mongodb-4e03ff1169490c95`): Plan cache entry lifecycle: Inactive and Active entries and works growth
- **serverStatus metrics.query.planCache counters** (`mongodb-21cfa0b88853e4ef`): serverStatus metrics.query.planCache counters
- **Standalone mongosync hosting and sizing** (`mongodb-7925b47a64e7b3de`): Standalone mongosync hosting and sizing
- **Time series bucket reopening (archived and query-based)** (`mongodb-d7584bdb38451a97`): Time series bucket reopening (archived and query-based)
- **mongosync and live-migration oplog capacity planning** (`mongodb-a795f66b3ce719c6`): mongosync and live-migration oplog capacity planning
- **Atlas Automated Embedding economics (Voyage tokens vs external embedding service)** (`mongodb-4bee35475c703fbe`): Atlas Automated Embedding economics (Voyage tokens vs external embedding service)
- **numCandidates tuning for quantized HNSW indexes** (`mongodb-a0baeec2d41c9aaa`): numCandidates tuning for quantized HNSW indexes
- **Count consistency under concurrent writes** (`mongodb-07cfc0fb94bc955d`): Count consistency under concurrent writes
- **Hidden and priority-0 members during maintenance** (`mongodb-10c4b1be8766477e`): Hidden and priority-0 members during maintenance
- **Loose versus tight bucket predicates** (`mongodb-3072d2a4e371f608`): Loose versus tight bucket predicates
- **Approximation pattern for write-heavy computed counters** (`mongodb-a3d3c857a04c0a0e`): Approximation pattern for write-heavy computed counters
- **Atlas Query Insights: Query Shape Insights and Namespace Insights** (`mongodb-e62e1e5f0a14a6c0`): Atlas Query Insights: Query Shape Insights and Namespace Insights
- **Covered distinct and $group on sharded collections** (`mongodb-21d5889a8e37c9a6`): Covered distinct and $group on sharded collections
- **moveCollection and collection isolation on dedicated shards** (`mongodb-1313ca23009179da`): moveCollection and collection isolation on dedicated shards
- **Relational-to-MongoDB migration cost (Relational Migrator)** (`mongodb-2a5ba92b53dbdf49`): Relational-to-MongoDB migration cost (Relational Migrator)
- **UUIDv4 versus UUIDv7 key locality** (`mongodb-44df64c27395c94f`): UUIDv4 versus UUIDv7 key locality
- **Hybrid search ($rankFusion) vs two-system fusion TCO** (`mongodb-11efb59e53667c2b`): Hybrid search ($rankFusion) vs two-system fusion TCO
- **Rolling resync (initial sync) as a space-reclaim technique on Atlas** (`mongodb-5b5b4cfcf84799ff`): Rolling resync (initial sync) as a space-reclaim technique on Atlas
- **Atlas analytics nodes and read preference tags** (`mongodb-c9679101de543f34`): Atlas analytics nodes and read preference tags
- **Workload isolation with tagged secondaries and Atlas analytics nodes** (`mongodb-48de7a278d0d4126`): Workload isolation with tagged secondaries and Atlas analytics nodes
- **defaultMaxTimeMS cluster-level read timeout** (`mongodb-99d4d1b0a47c689a`): defaultMaxTimeMS cluster-level read timeout
- **Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates)** (`mongodb-6ce47e86e19dad6f`): Flex-to-Dedicated migration triggers (500 ops/sec, 5 GB, feature gates)
- **Dedicated Search Nodes two-node cost floor versus coupled mongot** (`mongodb-cb1abdaf537229f9`): Dedicated Search Nodes two-node cost floor versus coupled mongot
- **Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized** (`mongodb-983c9002cb539e0a`): Search Node tier selection: S10, High-CPU vs Low-CPU vs storage-optimized
- **Replication Oplog Window alerts and Oplog GB/Hour monitoring** (`mongodb-bd2ec94cfc3e0c7d`): Replication Oplog Window alerts and Oplog GB/Hour monitoring
- **Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom)** (`mongodb-b22b7ad3bfec0d0e`): Replication oplog window monitoring (Oplog GB/Hour, Replication Headroom)
- **Atlas Search nodes in sharded clusters** (`mongodb-5e2d71b8262fc147`): Atlas Search nodes in sharded clusters
- **Embedded verifier and post-migration data verification cost** (`mongodb-1f8a6036de438274`): Embedded verifier and post-migration data verification cost
- **Time series compact and disk space reclaim** (`mongodb-3fc0d5495e547f9d`): Time series compact and disk space reclaim
- **Bucket reopening and the {metaField, timeField} index requirement** (`mongodb-0a10b489706a380f`): Bucket reopening and the {metaField, timeField} index requirement
- **Search Node sizing and disk-to-RAM ratios for quantized vector indexes** (`mongodb-8c5c35085f3b6c32`): Search Node sizing and disk-to-RAM ratios for quantized vector indexes
- **Search Node sizing for quantized vector indexes (RAM, disk, vCPU)** (`mongodb-7af7e4d6845945d6`): Search Node sizing for quantized vector indexes (RAM, disk, vCPU)
- **COUNT_SCAN and sharded count accuracy** (`mongodb-d4200ab2ca7b6cb5`): COUNT_SCAN and sharded count accuracy
- **dropIndexes locking and rollback by rebuild** (`mongodb-7e8b96bdf697cd86`): dropIndexes locking and rollback by rebuild
- **Maintained or cached count counters** (`mongodb-3cfe80671cfeec47`): Maintained or cached count counters
- **replSetResizeOplog and oplog compaction on self-managed replica sets** (`mongodb-01e5968b3c6a6095`): replSetResizeOplog and oplog compaction on self-managed replica sets
- **Bucket archiving and query-based reopening** (`mongodb-6f7952f8bc36e6ac`): Bucket archiving and query-based reopening
- **Cache-pressure early bucket closure and bucket catalog memory** (`mongodb-64ee8f1a399655a0`): Cache-pressure early bucket closure and bucket catalog memory
- **Side-writes table and hybrid index builds** (`mongodb-ab63bfa824bdfca1`): Side-writes table and hybrid index builds
- **Validation and performance review of generated queries** (`mongodb-4688c1035515d88b`): Validation and performance review of generated queries
- **Atlas invoice tag coverage and cost export reconciliation** (`mongodb-df9f123599ebe33f`): Atlas invoice tag coverage and cost export reconciliation
- **Exporting $indexStats metrics with mongodb_exporter and PMM** (`mongodb-0b46e1f993a1159c`): Exporting $indexStats metrics with mongodb_exporter and PMM
- **Persisting index usage metrics with PMM and mongodb_exporter** (`mongodb-b17bfdcd6d33ab29`): Persisting index usage metrics with PMM and mongodb_exporter
- **Config server placement and cost (dedicated vs embedded)** (`mongodb-eb3caa0d55a39552`): Config server placement and cost (dedicated vs embedded)
- **MongoDB commit quorum and two-phase index builds** (`mongodb-d62e0732163fcf5b`): MongoDB commit quorum and two-phase index builds
- **Time-field bucket predicates** (`mongodb-ce9f22f88277e81e`): Time-field bucket predicates
- **Two-phase (simultaneous) index builds** (`mongodb-fd8a391e36c2f1cb`): Two-phase (simultaneous) index builds
- **Rolling index builds as a resource-isolation alternative** (`mongodb-53ebb7c31bd889d6`): Rolling index builds as a resource-isolation alternative
- **SHARDING_FILTER stage internals and orphaned-document filtering** (`mongodb-72047567328b3784`): SHARDING_FILTER stage internals and orphaned-document filtering
- **One-way tier gates: sharding, Global Writes, edition changes** (`mongodb-154d85446aca8d3c`): One-way tier gates: sharding, Global Writes, edition changes
- **Atlas Search node scaling per shard** (`mongodb-764bd81a5a773e26`): Atlas Search node scaling per shard
- **Index rebuild cost after a wrong drop** (`mongodb-fefaa0b8e8e04414`): Index rebuild cost after a wrong drop
- **Delete and re-insert safety on time series** (`mongodb-923ceb9b3e18edd6`): Delete and re-insert safety on time series
- **DiskSpaceMonitor and low-disk index build abort (7.1+)** (`mongodb-f2ba7b6cbaf4b07d`): DiskSpaceMonitor and low-disk index build abort (7.1+)
- **Clustered collection insert locality** (`mongodb-882d953d06ecf092`): Clustered collection insert locality
- **Rooted $or subplanning and SORT_MERGE** (`mongodb-ec08ff8b974e0f70`): Rooted $or subplanning and SORT_MERGE
- **serverStatus indexBuilds metrics and index build observability** (`mongodb-f133778e0dd645e1`): serverStatus indexBuilds metrics and index build observability
- **Hybrid search ($rankFusion) vs separate search plus vector stack** (`mongodb-cb8fa38113d4a3bf`): Hybrid search ($rankFusion) vs separate search plus vector stack
- **Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden)** (`mongodb-5de70bb852c542b0`): Atlas Performance Advisor drop-index recommendations (unused, redundant, hidden)
- **Destination right-sizing after cutover** (`mongodb-f61d9a822b83c2cc`): Destination right-sizing after cutover
- **Cache-aside vs write-through and cache stampede prevention** (`mongodb-455e51a21604bfdc`): Cache-aside vs write-through and cache stampede prevention
- **Query settings and index filters as plan pinning** (`mongodb-de4657c9ed97854c`): Query settings and index filters as plan pinning
- **Frozen buckets and compression failures** (`mongodb-4730c00dc9ee7135`): Frozen buckets and compression failures
- **Initial sync index build memory limits** (`mongodb-241793c17bb3b2cc`): Initial sync index build memory limits
- **per-accumulator explain memory statistics** (`mongodb-66052fda66c0dd23`): per-accumulator explain memory statistics
- **Mixed-schema measurement predicate safety** (`mongodb-486aa566eb9f3fec`): Mixed-schema measurement predicate safety
- **Oplog windows and Search initial-sync recovery** (`mongodb-85b45d8030420f41`): Oplog windows and Search initial-sync recovery
- **Sharded time series rebuild and resharding** (`mongodb-12f204d0f73d5c70`): Sharded time series rebuild and resharding
- **Cost-based ranker and the plan cache (8.3+)** (`mongodb-6e54bf0743fd3ab5`): Cost-based ranker and the plan cache (8.3+)
- **Idle bucket expiry and archived bucket reopening** (`mongodb-f233d10934a5e0d7`): Idle bucket expiry and archived bucket reopening
- **MongoDB Search eventual consistency and replication-lag metrics** (`mongodb-bf53032042a472a5`): MongoDB Search eventual consistency and replication-lag metrics
- **Atlas managed slow operation threshold and Performance Advisor index suggestions** (`mongodb-dadb3de5ec7b8a6b`): Atlas managed slow operation threshold and Performance Advisor index suggestions
- **External sorter spill files in dbpath/_tmp** (`mongodb-63ce4d2c03fecae1`): External sorter spill files in dbpath/_tmp
- **Pre-quantized BinData (int8 and int1) ingestion** (`mongodb-dbcbc1d7561ca48d`): Pre-quantized BinData (int8 and int1) ingestion
- **Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB** (`mongodb-807c3ccd211eeab7`): Pre-quantized BinData vector ingestion (int8 and int1) in MongoDB
- **custom $accumulator spill and merge semantics** (`mongodb-009e3c9554b34360`): custom $accumulator spill and merge semantics
- **Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields)** (`mongodb-d49655fd3c7cff9e`): Terraform management of asymmetric sharded clusters (replication_specs, use_effective_fields)
- **Index usage measurement with $indexStats** (`mongodb-6f5f321045e0edf3`): Index usage measurement with $indexStats
- **Redundant and prefix index detection** (`mongodb-fcb9495dd1174a73`): Redundant and prefix index detection
- **MongoDB rolling index builds** (`mongodb-a16b483837d9ea51`): MongoDB rolling index builds
- **Config shard versus dedicated config server** (`mongodb-8b57223f4133bbad`): Config shard versus dedicated config server
- **Atlas minimum oplog window (oplogMinRetentionHours) tuning** (`mongodb-c85605b2cc4dc9d2`): Atlas minimum oplog window (oplogMinRetentionHours) tuning
- **Atlas disk decrease by volume replacement on AWS, Azure and GCP** (`mongodb-13c6b1eeb704e59e`): Atlas disk decrease by volume replacement on AWS, Azure and GCP
- **Reducing Atlas storage capacity (new-volume sync, per-node downtime)** (`mongodb-56adaf63af16ccb6`): Reducing Atlas storage capacity (new-volume sync, per-node downtime)
- **Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes)** (`mongodb-f8df8715fc512ffc`): Kubernetes operator PVC resizing and oplog management (Percona, MongoDB Controllers for Kubernetes)
- **Execution-guided text-to-MQL refinement** (`mongodb-c830a49b1716607f`): Execution-guided text-to-MQL refinement
- **Measuring ANN recall against ENN baselines** (`mongodb-58d3075bb6bcb3ac`): Measuring ANN recall against ENN baselines
- **orphanCleanupDelaySecs and range deletion timing** (`mongodb-8886daa104930363`): orphanCleanupDelaySecs and range deletion timing
- **Burstable M10/M20 CPU credits and the M30 production threshold** (`mongodb-8c2c7ba4cb87f068`): Burstable M10/M20 CPU credits and the M30 production threshold
- **Burstable M10/M20 CPU-credit throttling and when to move to M30** (`mongodb-6c7186204e8017d6`): Burstable M10/M20 CPU-credit throttling and when to move to M30
- **Schema grounding and value linking for MQL generation** (`mongodb-e367e15ab372e407`): Schema grounding and value linking for MQL generation
- **Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections** (`mongodb-2f0d3d755535f053`): Post-cutover rebuilds: Atlas Search indexes, users and roles, time-series collections
- **MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later)** (`mongodb-5e77d4557f37e1b1`): MongoDB cache-pressure monitor and oldest-transaction aborts (8.2 and later)
- **Primary-driven index builds and write-rate throttles** (`mongodb-971ffff4d9ee3092`): Primary-driven index builds and write-rate throttles
- **rawData bucket-level CRUD (8.2 and later)** (`mongodb-b14dc0828d8b50be`): rawData bucket-level CRUD (8.2 and later)
- **Self-managed mongot on Community Edition: hardware and labour TCO** (`mongodb-499ad5dfcc676208`): Self-managed mongot on Community Edition: hardware and labour TCO
- **$querySettings stage and query settings inspection** (`mongodb-b07a637b21b88412`): $querySettings stage and query settings inspection
- **Terraform state reconciliation after a Flex-to-Dedicated conversion** (`mongodb-99c3b85f8ea2f600`): Terraform state reconciliation after a Flex-to-Dedicated conversion
- **Atlas write-blocking thresholds and Intelligent Workload Management** (`mongodb-a5b02b4713b48099`): Atlas write-blocking thresholds and Intelligent Workload Management
- **SBE plan cache keys and parameterized explode-for-sort plans** (`mongodb-86d9655eef37c43c`): SBE plan cache keys and parameterized explode-for-sort plans
- **Per-shape maxTimeMS and queryKnobs (9.0)** (`mongodb-18c93953c25aee74`): Per-shape maxTimeMS and queryKnobs (9.0)
- **Per-shape queryKnobs and maxTimeMS (9.0)** (`mongodb-b065371ac638e191`): Per-shape queryKnobs and maxTimeMS (9.0)
- **multikey index sort behaviour** (`mongodb-a1a26836af6af277`): multikey index sort behaviour
- **Read concern and causal consistency with secondary reads** (`mongodb-571599b65ef802bf`): Read concern and causal consistency with secondary reads
- **Replica Set Transactions** (`mongodb-3bb6f8165c73d25b`): Replica Set Transactions
- **Sparse versus partial index equivalence** (`mongodb-681c3ccf51360db2`): Sparse versus partial index equivalence
- **Atlas billing alert notification delivery** (`mongodb-daf5f04ff38e5b74`): Atlas billing alert notification delivery
- **Time-series bucket closure under cache pressure** (`mongodb-2913bf52cf381766`): Time-series bucket closure under cache pressure
- **Search Node network transfer and multi-region cost** (`mongodb-ba06efd5a3a65ecb`): Search Node network transfer and multi-region cost
- **Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration** (`mongodb-83cd6ae06eff3d17`): Terraform mongodbatlas_advanced_cluster per-shard replication_specs migration
- **explodeForSort integer overflow (CVE-2026-82076)** (`mongodb-6f3be80e7ee2148e`): explodeForSort integer overflow (CVE-2026-82076)
- **Shard key index design** (`mongodb-6495b656928cd28c`): Shard key index design
- **Multiplanner scoring and tie-breakers** (`mongodb-29d0dd392fb6801c`): Multiplanner scoring and tie-breakers
- **Rolling index builds on Kubernetes with the Percona Operator** (`mongodb-49e91c2695d1a6f8`): Rolling index builds on Kubernetes with the Percona Operator
- **SBE plan cache pinned entries and the classic runtime planner for SBE** (`mongodb-e67c70b79575bbfb`): SBE plan cache pinned entries and the classic runtime planner for SBE
- **Plan cache invalidation on index DDL (hide, drop, create)** (`mongodb-190b283c18d76a07`): Plan cache invalidation on index DDL (hide, drop, create)
- **External sorter spill files and the _tmp directory** (`mongodb-3026c7d51b5d2f7d`): External sorter spill files and the _tmp directory
- **Atlas tag enforcement through Terraform and APIs** (`mongodb-87e87c1dd2080346`): Atlas tag enforcement through Terraform and APIs
- **Config shard (embedded config server) cost trade-off** (`mongodb-65c27c0dfba72a11`): Config shard (embedded config server) cost trade-off
- **Atlas Minimum Oplog Window (oplogMinRetentionHours)** (`mongodb-5d31399755f14ab9`): Atlas Minimum Oplog Window (oplogMinRetentionHours)
- **internalQueryMaxScansToExplode and maxScansToExplodeReached** (`mongodb-c7bd06d38432e9c2`): internalQueryMaxScansToExplode and maxScansToExplodeReached
- **Flex backup and recovery planning** (`mongodb-993aec1833eb6e6c`): Flex backup and recovery planning
- **Atlas Query Profiler and Operation Throttling metrics** (`mongodb-00788b1b3bb92bad`): Atlas Query Profiler and Operation Throttling metrics
- **Gen2 clusters and Extended Standard IOPS economics** (`mongodb-4437555c82bb9745`): Gen2 clusters and Extended Standard IOPS economics
- **Rebuilding a time series collection with $out or mongorestore** (`mongodb-d50feb629e688162`): Rebuilding a time series collection with $out or mongorestore
- **Atlas security add-on uplifts (auditing, LDAP, customer-managed keys, private endpoints)** (`mongodb-22325bda55f48ce0`): Atlas security add-on uplifts (auditing, LDAP, customer-managed keys, private endpoints)
- **Automated rolling builds in Atlas, Cloud Manager and Ops Manager** (`mongodb-601bc1adb5c8a1da`): Automated rolling builds in Atlas, Cloud Manager and Ops Manager
- **Collation-aware index key size** (`mongodb-f68a7b59a5714970`): Collation-aware index key size
- **Ops Manager Profiler** (`mongodb-d0254b9e675051e0`): Ops Manager Profiler
- **Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads)** (`mongodb-5d657d5afb5dd01f`): Refresh scheduling on Atlas (Scheduled Triggers, cron, secondary or analytics reads)
- **VPC Atlas Security** (`mongodb-66629057aa248ea5`): VPC Atlas Security
- **path-level multikey tracking** (`mongodb-ac1652e7c2bfd255`): path-level multikey tracking
- **Percona PMM mongolog versus profiler query source** (`mongodb-788180d569d7d884`): Percona PMM mongolog versus profiler query source
- **EBS volume modification limits and Atlas disk resize mechanics** (`mongodb-bf2466898d41baab`): EBS volume modification limits and Atlas disk resize mechanics
- **Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers)** (`mongodb-3fba0026158c3051`): Cluster Tier Limits and Feature Gates as Cost Drivers (Connections, IOPS Caps, Minimum Tiers); Three-node minimum for non-production
- **Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB)** (`mongodb-e7fc6eda266cf57d`): Platform Consolidation TCO (Atlas Search/Vector Search vs Separate Search or Vector DB)
- **Atlas Real-Time Performance Panel** (`mongodb-8789f69d361dfdf9`): Atlas Real-Time Performance Panel
- **Atlas auto-scaling gating by oplog window and its alerts** (`mongodb-2a06abfc749f181d`): Atlas auto-scaling gating by oplog window and its alerts
- **Atlas Infinite storage metering and max storage limit** (`mongodb-290473cfefc454a9`): Atlas Infinite storage metering and max storage limit
- **GCP Workload Identity Atlas** (`mongodb-90fdd0f46c688fab`): GCP Workload Identity Atlas
- **Atlas Query Shape Insights and Namespace Insights** (`mongodb-cbc35723dae300d2`): Atlas Query Shape Insights and Namespace Insights
- **Atlas Administration API rolling index endpoint** (`mongodb-1d8cdf7b5a1b8ece`): Atlas Administration API rolling index endpoint
- **Cost-based ranker plan selection for sorted queries (8.3+)** (`mongodb-56ea3f475182e73c`): Cost-based ranker plan selection for sorted queries (8.3+)
- **MongoDB primary-driven index builds (PDIB)** (`mongodb-f5fe8246bc1f373b`): MongoDB primary-driven index builds (PDIB)
- **Primary-driven index builds** (`mongodb-c1bd38937e366405`): Primary-driven index builds
- **DISTINCT_SCAN with shard filtering in 8.2** (`mongodb-db4cbab4dbb77651`): DISTINCT_SCAN with shard filtering in 8.2
- **Covered queries and projection design** (`mongodb-8c1f45c525ccf3e4`): Covered queries and projection design
- **Multikey index sort bounds** (`mongodb-628fedbd91c89a1e`): Multikey index sort bounds
- **Matryoshka and quantization-aware embedding models** (`mongodb-3df89994c3c60fd5`): Matryoshka and quantization-aware embedding models
- **Interval evaluation trees and parameterized plan caching** (`mongodb-877171bb4e49da96`): Interval evaluation trees and parameterized plan caching
- **Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern)** (`mongodb-8a48380dc82bfddc`): Read Offload via Caching and Precomputed Views ($merge/$out, Computed Pattern)
- **Atlas Performance Advisor drop-index recommendations** (`mongodb-50ec9dcdbff2ae63`): Atlas Performance Advisor drop-index recommendations
- **Atlas Infinite fixed-IOPS tiers and decoupled storage** (`mongodb-c385a05c16af82e4`): Atlas Infinite fixed-IOPS tiers and decoupled storage
- **Dynamic bucket sizing and cache-pressure closures** (`mongodb-daf240a9ba3ba62e`): Dynamic bucket sizing and cache-pressure closures
- **Quantization-aware and Matryoshka embeddings (voyage-3-large) with Atlas dimension slicing** (`mongodb-8d61b695eec98ece`): Quantization-aware and Matryoshka embeddings (voyage-3-large) with Atlas dimension slicing
- **Atlas Infinite oplog and storage-layer replication** (`mongodb-850019f33a974bd2`): Atlas Infinite oplog and storage-layer replication
- **Counter-document pattern** (`mongodb-0c0b0a1154fd4e2f`): Counter-document pattern
- **Field-name abbreviation trade-offs** (`mongodb-650613677dbd2261`): Field-name abbreviation trade-offs
- **M10 shared-vCPU dedicated tier economics** (`mongodb-aa673735c7a186fc`): M10 shared-vCPU dedicated tier economics
- **Tailable cursors and maxAwaitTimeMS** (`mongodb-bfbf617cf85a9d45`): Tailable cursors and maxAwaitTimeMS
- **Eviction thread sizing and wiredTigerEngineRuntimeConfig tuning** (`mongodb-02d995b3895148bd`): Eviction thread sizing and wiredTigerEngineRuntimeConfig tuning
- **V2 and V3 compressed buckets and unsorted conversion** (`mongodb-f80ad0c2b80d8801`): V2 and V3 compressed buckets and unsorted conversion
- **Atlas index build tier defaults** (`mongodb-9b3f6cc7e3d3ac23`): Atlas index build tier defaults
- **Atlas tier-fixed index build limits** (`mongodb-ce4a0cb22fbb3201`): Atlas tier-fixed index build limits
- **MongoDB 8.0 autoCompact background compaction on Atlas** (`mongodb-55db4d991e83d87c`): MongoDB 8.0 autoCompact background compaction on Atlas
- **IAM Role Atlas API Access** (`mongodb-8cdf351b913d7856`): IAM Role Atlas API Access
- **Atlas backup/PITR and data transfer cost drivers** (`mongodb-33cd7f0ef85a1717`): Atlas backup/PITR and data transfer cost drivers
- **Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress)** (`mongodb-317efde63c35f04e`): Migration and Cutover Cost (Live Migration, mongosync, Dual-Running, Egress)
- **Shard Key Design and Resharding as Cost Levers** (`mongodb-8c1f7f52a5a83b63`): Shard Key Design and Resharding as Cost Levers; Shard-key choice and scatter-gather cost
- **Express path for _id lookups on sharded collections** (`mongodb-f9c388b7c70355e6`): Express path for _id lookups on sharded collections
- **MongoDB CBR CE source metadata** (`mongodb-f4b4df52106131ad`): MongoDB CBR CE source metadata
- **Atlas Query Shape Insights** (`mongodb-4fdb99e4891908d0`): Atlas Query Shape Insights
- **Namespace Insights** (`mongodb-4ae8627725bdc8e0`): Namespace Insights
- **Sparse and partial indexes for $exists** (`mongodb-41f6434505be256e`): Sparse and partial indexes for $exists
- **Organization-scoped alert configuration API** (`mongodb-9507fa25c7d06b40`): Organization-scoped alert configuration API
- **Lambda Managed Instances and MongoClient concurrency safety** (`mongodb-c56934954429e244`): Lambda Managed Instances and MongoClient concurrency safety
- **Atlas Infinite storage model (max storage limit, no auto-scaling)** (`mongodb-a2f56f7f5271253e`): Atlas Infinite storage model (max storage limit, no auto-scaling)
- **replSetResizeOplog and oplog compaction runbook** (`mongodb-b68de527be6e2e1b`): replSetResizeOplog and oplog compaction runbook
- **Partition Field Count Limits (DATE vs CUSTOM)** (`mongodb-5135f31e186c3438`): Partition Field Count Limits (DATE vs CUSTOM)
- **Atlas Infinite fixed per-tier IOPS and public-preview feature exclusions** (`mongodb-926e1c744b633b85`): Atlas Infinite fixed per-tier IOPS and public-preview feature exclusions
- **Primary-driven index builds (spill to a replicated table)** (`mongodb-9ac00e735a7f32be`): Primary-driven index builds (spill to a replicated table)
- **$function and server-side JavaScript hardening** (`mongodb-96aa57b9e6f1d8f2`): $function and server-side JavaScript hardening
- **Atlas Charts billing dashboards** (`mongodb-1585ac28474d20d9`): Atlas Charts billing dashboards
- **Credit expiry and History table** (`mongodb-51d2f0001920e1e6`): Credit expiry and History table
- **Index hints on time series collections** (`mongodb-7eea626bfebceba6`): Index hints on time series collections
- **Cache-derived dynamic bucket size limit** (`mongodb-2c58908da1fa80b5`): Cache-derived dynamic bucket size limit
- **Dynamic bucket size cap under cache pressure** (`mongodb-4508beee32348bbe`): Dynamic bucket size cap under cache pressure
- **Atlas marketplace private offers** (`mongodb-be13cc5ab72690be`): Atlas marketplace private offers
- **Gen1 vs Gen2 storage and IOPS billing** (`mongodb-cfed93e5e3217b53`): Gen1 vs Gen2 storage and IOPS billing
- **SBE $lookup pushdown and hash join** (`mongodb-dd877ae5b4fdc443`): SBE $lookup pushdown and hash join
- **Shared-cost allocation rules for managed database services** (`mongodb-7fed8a5c0e525682`): Shared-cost allocation rules for managed database services
- **eviction_updates_trigger and the updates ratio** (`mongodb-3d8082b039d1a5b5`): eviction_updates_trigger and the updates ratio
- **Same-field `$or` to `$in` rewrite** (`mongodb-24b4ec4143de82f7`): Same-field `$or` to `$in` rewrite
- **Gen1 vs Gen2 IOPS billing** (`mongodb-a61b2707340ba6da`): Gen1 vs Gen2 IOPS billing
- **Atlas Admin API invoice endpoints** (`mongodb-95f163645ff4d869`): Atlas Admin API invoice endpoints
- **Atlas Infinite compute auto-scaling** (`mongodb-0e173d1a4a7be744`): Atlas Infinite compute auto-scaling
- **Auto-scaling tier ranges** (`mongodb-912dd90d8980ae92`): Auto-scaling tier ranges
- **Backup and PITR cost modelling** (`mongodb-7957a71b8005114a`): Backup and PITR cost modelling
- **Cedar policy authoring for cluster size and autoscaling caps** (`mongodb-28c3a0f533452bc5`): Cedar policy authoring for cluster size and autoscaling caps
- **Multi-region cluster cost premium** (`mongodb-9fdf26d536b91015`): Multi-region cluster cost premium
- **Pause/resume automation with Terraform or GitHub Actions** (`mongodb-072eec3613eb7532`): Pause/resume automation with Terraform or GitHub Actions
- **Right-sizing from Atlas metrics** (`mongodb-f9b0361626e95678`): Right-sizing from Atlas metrics
- **EU Data Act switching charges and in-parallel egress** (`mongodb-d72b938404e888d1`): EU Data Act switching charges and in-parallel egress
- **Rolling index builds as a resource-limited alternative** (`mongodb-524ff443222313b4`): Rolling index builds as a resource-limited alternative
- **Automated Embedding (autoEmbed) quantization types** (`mongodb-1672753667a8a066`): Automated Embedding (autoEmbed) quantization types
- **Automated Embedding (autoEmbed) quantization types including binaryNoRescore** (`mongodb-939c6afccdc05227`): Automated Embedding (autoEmbed) quantization types including binaryNoRescore
- **Spill WiredTiger instance cache** (`mongodb-b0ea562a020af0f2`): Spill WiredTiger instance cache
- **WiredTiger spill instance cache** (`mongodb-6193357302c34e7a`): WiredTiger spill instance cache
- **$groupByDistinct internal stage** (`mongodb-5d21f894eb00e4db`): $groupByDistinct internal stage
- **Analytics node tier prorating** (`mongodb-e44a05f678750f34`): Analytics node tier prorating
- **Atlas-only feature lock-in and exit cost** (`mongodb-dad75167e372f795`): Atlas-only feature lock-in and exit cost
- **AWS Marketplace EDP drawdown for Atlas** (`mongodb-24f205c548a05790`): AWS Marketplace EDP drawdown for Atlas
- **Backup and PIT oplog storage region billing** (`mongodb-55169fce81931358`): Backup and PIT oplog storage region billing
- **Cost Explorer filters for AI services** (`mongodb-3455606a49d0ae97`): Cost Explorer filters for AI services
- **Query limits and billing alerts for archive spend** (`mongodb-af8bfd1b3f4a9a17`): Query limits and billing alerts for archive spend
- **Support line items per cloud provider on invoices** (`mongodb-9b823f0f1fba9804`): Support line items per cloud provider on invoices
- **Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure)** (`mongodb-57ad2f2520b1d24c`): Hyperscaler exit-egress waiver programs (AWS, Google Cloud, Azure)
- **Cloud exit-credit programs and EU Data Act in-parallel egress** (`mongodb-2a049fdcae415842`): Cloud exit-credit programs and EU Data Act in-parallel egress
- **Atlas Infinite oplog and storage cost** (`mongodb-f54190428672705c`): Atlas Infinite oplog and storage cost
- **Idle-spend and minimum-commit economics of serverless vector stores** (`mongodb-57fe4d836a248d22`): Idle-spend and minimum-commit economics of serverless vector stores
- **Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors** (`mongodb-9e8aa89ebeeddb75`): Separate-stack cost floors: Pinecone, OpenSearch Serverless NextGen, Elastic Serverless, S3 Vectors
- **Enterprise Advanced licensing economics** (`mongodb-dd68044b3d888f7c`): Enterprise Advanced licensing economics
- **Project-level billing change alerts** (`mongodb-0fa1f571793d7a59`): Project-level billing change alerts
- **Shared-cost splitting for Atlas projects** (`mongodb-618d04a674b2e33e`): Shared-cost splitting for Atlas projects
- **Refresh scheduling with Atlas Scheduled Triggers** (`mongodb-cafa7a241b938ab0`): Refresh scheduling with Atlas Scheduled Triggers
- **positional index path caveat** (`mongodb-8e48f8b83be4e936`): positional index path caveat
- **maxEstimatedScanBytes collection-scan rejection (9.0)** (`mongodb-55851d1ec7332aa1`): maxEstimatedScanBytes collection-scan rejection (9.0)
- **Network (wire) compression** (`mongodb-6d1d3a3f9fbe01ad`): Network (wire) compression
- **Side bucket catalog** (`mongodb-c6459d640bbea983`): Side bucket catalog
- **Side bucket catalog for time series updates and deletes** (`mongodb-844cb4caa9361223`): Side bucket catalog for time series updates and deletes
- **Oplog sizing in Kubernetes operators and managed MongoDB-compatible services** (`mongodb-010e200700708f00`): Oplog sizing in Kubernetes operators and managed MongoDB-compatible services
- **Partition Field Type Enum Docs-vs-Spec Disagreement** (`mongodb-b655e2e370710552`): Partition Field Type Enum Docs-vs-Spec Disagreement
- **Auto-scaling min/max bounds and Terraform drift** (`mongodb-1affc6a1b924281d`): Auto-scaling min/max bounds and Terraform drift
- **Config shard versus dedicated config server cost** (`mongodb-530d60bd5242f78d`): Config shard versus dedicated config server cost
- **MongoDB Charts billing dashboards** (`mongodb-301547a99e11b6b3`): MongoDB Charts billing dashboards
- **Persisting index usage metrics across restarts (PMM/monitoring)** (`mongodb-23dc66c763b719d7`): Persisting index usage metrics across restarts (PMM/monitoring)
- **Scale-down tuning for spiky batch workloads** (`mongodb-110b9d56520f4ac1`): Scale-down tuning for spiky batch workloads
- **Amazon DocumentDB profiler (CloudWatch Logs)** (`mongodb-78fdc802398495b2`): Amazon DocumentDB profiler (CloudWatch Logs)
- **Bucket catalog stripes, state registry and eras** (`mongodb-0a3be19203e9172f`): Bucket catalog stripes, state registry and eras
- **Client-side operation timeout (CSOT)** (`mongodb-57629268b2c2e6cb`): Client-side operation timeout (CSOT)
- **Collation-based case-insensitive indexes as a $regex alternative** (`mongodb-f91e30bd5aaf2ccd`): Collation-based case-insensitive indexes as a $regex alternative
- **Intra-cluster replication transfer billing** (`mongodb-34bba6054db50a88`): Intra-cluster replication transfer billing
- **Retroactive support billing on reactivation** (`mongodb-ea29c899a57b0a5e`): Retroactive support billing on reactivation
- **Time series collection expireAfterSeconds** (`mongodb-f7d449c60e94f3b9`): Time series collection expireAfterSeconds
- **Lucene BBQ binary quantization compared with Atlas binary quantization** (`mongodb-746e0de29ea30509`): Lucene BBQ binary quantization compared with Atlas binary quantization
- **Atlas billing alert configuration via Admin API** (`mongodb-e34eab21447b18d4`): Atlas billing alert configuration via Admin API
- **Rolling index build key inconsistency incident** (`mongodb-b41c8cb4dfa445cf`): Rolling index build key inconsistency incident
- **Rolling index build table-logging incident** (`mongodb-82f5b1f3a52c8ad2`): Rolling index build table-logging incident
- **Percona PMM mongolog query source** (`mongodb-29d81049e9589a0a`): Percona PMM mongolog query source
- **Partition Field Cardinality and the 2023-06-07 Storage Engine Change** (`mongodb-eca6bdfeb802b0e3`): Partition Field Cardinality and the 2023-06-07 Storage Engine Change
- **Atlas PrivateLink regional endpoint rates** (`mongodb-0a6ce44bfef7c552`): Atlas PrivateLink regional endpoint rates
- **Atlas included-replica pricing vs per-instance HA billing** (`mongodb-4fc92e3a76fc64a9`): Atlas included-replica pricing vs per-instance HA billing
- **Egress and data transfer estimation** (`mongodb-7f3ba3ad9cb271c0`): Egress and data transfer estimation
- **queryKnobs and per-command querySettings** (`mongodb-0f7e0554d978cb8e`): queryKnobs and per-command querySettings
- **Re-indexing cost when changing numDimensions** (`mongodb-2e32f4acda4557c2`): Re-indexing cost when changing numDimensions
- **Untagged spend reporting** (`mongodb-7436041c120e41d7`): Untagged spend reporting
- **Atlas Admin API billing alert configuration** (`mongodb-f64481d2ec8394f5`): Atlas Admin API billing alert configuration
- **Atlas Admin API rate limiting for scheduled polling** (`mongodb-2a9b2c66ae4897e3`): Atlas Admin API rate limiting for scheduled polling
- **Cross-vendor FOCUS pipelines (BigQuery/Snowflake)** (`mongodb-8483cc56f40c9bdd`): Cross-vendor FOCUS pipelines (BigQuery/Snowflake)
- **DynamoDB on-demand vs provisioned break-even** (`mongodb-b400b540461e780a`): DynamoDB on-demand vs provisioned break-even
- **FOCUS column mapping for Atlas credits** (`mongodb-62acea60461f46a0`): FOCUS column mapping for Atlas credits
- **Linking Atlas orgs to marketplace billing accounts** (`mongodb-00464fef4f41a2e0`): Linking Atlas orgs to marketplace billing accounts
- **Conftest/OPA rules over terraform show -json plans** (`mongodb-4d03e735ca976838`): Conftest/OPA rules over terraform show -json plans
- **Search node tier sizing for vector indexes** (`mongodb-6019089339a51f59`): Search node tier sizing for vector indexes
- **Backup storage rates by region** (`mongodb-f982a1742cbb79f2`): Backup storage rates by region
- **Cosmos DB RU estimation for MongoDB workloads** (`mongodb-1a844e0df74a38de`): Cosmos DB RU estimation for MongoDB workloads
- **Proportional minimum-commit allocation** (`mongodb-fb538eb4250cda06`): Proportional minimum-commit allocation
- **Scheduled compliance polling and alerting** (`mongodb-19826c5f8cc4ec78`): Scheduled compliance polling and alerting
- **PostgreSQL invalid indexes from failed CONCURRENTLY builds** (`mongodb-7ec18ee4ed0cf964`): PostgreSQL invalid indexes from failed CONCURRENTLY builds
- **SQL Server resumable online index operations** (`mongodb-a7f881bd35836f95`): SQL Server resumable online index operations
- **Atlas Admin API pending-invoice tags field** (`mongodb-219f38122399dbab`): Atlas Admin API pending-invoice tags field
- **Journal compression** (`mongodb-48df1b736c264578`): Journal compression
- **PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY** (`mongodb-1f6a5f22aae30ad4`): PostgreSQL invalid-index cleanup and REINDEX CONCURRENTLY
- **Billing incidents and refunds** (`mongodb-a048ccb7e608b58b`): Billing incidents and refunds
- **Unlinking an organization** (`mongodb-c63c368f0dede092`): Unlinking an organization
- **SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints** (`mongodb-257362073fe4e362`): SQL Server resumable index operations: ELEVATE_RESUMABLE and resumable constraints
- **Cosmos DB for MongoDB wildcard differences** (`mongodb-7323eb0342be4b6c`): Cosmos DB for MongoDB wildcard differences
- **Charts billing ingestion for linked orgs** (`mongodb-ce6e8e8d76e9c72e`): Charts billing ingestion for linked orgs
- **Atlas CLI** (`mongodb-a7bc654c500d19b5`): Atlas CLI; atlas-cli
- **Atlas cluster tiers (M30) & major-version upgrade mechanics** (`mongodb-bd98132165e458ac`): Atlas cluster tiers (M30) & major-version upgrade mechanics
- **Atlas Service Accounts** (`mongodb-85937d1cb788be53`): Atlas Service Accounts
- **Atlas Triage Workflows** (`mongodb-d4ed85cc09916e0c`): Atlas Triage Workflows; atlas-triage-workflows
- **autoCompact and Replica-Set Write Blocking** (`mongodb-a792e0075d93fa17`): RSWB; autoCompact and Replica-Set Write Blocking; blockReplicaSetWrites
- **autoCompact Atlas-Specific Behavior** (`mongodb-c6eeffd1ee4b2393`): autoCompact Atlas-Specific Behavior
- **autoCompact Checkpoint Interaction** (`mongodb-522ba776d46ae0c8`): autoCompact Checkpoint Interaction
- **autoCompact Cluster Topology Behavior** (`mongodb-b56aa0302376fb8d`): autoCompact Cluster Topology Behavior
- **autoCompact freeSpaceTargetMB Gating** (`mongodb-6f17722ce708d8a3`): autoCompact freeSpaceTargetMB Gating; freeSpaceTargetMB
- **autoCompact Lifecycle and Persistence** (`mongodb-9ea0452e80b9982d`): autoCompact Lifecycle and Persistence; enableAutoCompaction
- **autoCompact runOnce vs Continuous Mode** (`mongodb-54e6a74148d5054b`): autoCompact runOnce vs Continuous Mode; runOnce mode
- **Background-Compaction Skip/EMA Heuristic** (`mongodb-d9214cdc09926575`): Background-Compaction Skip/EMA Heuristic; exclude_list_hash; stat_hash
- **Delbridge Data API** (`mongodb-2e4b5c89e48ca365`): Delbridge Data API
- **Diagnostic Tool Design** (`mongodb-1de388843e62fcd6`): Diagnostic Tool Design; diagnostic-tool-design
- **Driver Examples** (`mongodb-5c1f18de01ee9047`): Driver Examples
- **Error Codes and Troubleshooting** (`mongodb-20120b43be1ba061`): Error Codes and Troubleshooting; error-codes-and-troubleshooting
- **Express MongoDB Driver Pattern** (`mongodb-2e0ab631ade8fb5a`): Express MongoDB Driver Pattern
- **FastAPI Motor Pattern** (`mongodb-107085c4770bb819`): FastAPI Motor Pattern
- **FTDC and Log Tooling** (`mongodb-c330c7ad3dbb4973`): FTDC and Log Tooling; ftdc-and-log-tooling
- **KB-Backed Troubleshooting** (`mongodb-c59681d79f02ca60`): KB-Backed Troubleshooting; kb-backed-troubleshooting
- **MongoDB 8.0 performance changes & read-path regressions vs 7.0** (`mongodb-80399f0419458499`): MongoDB 8.0 performance changes & read-path regressions vs 7.0
- **MongoDB Atlas Analytics Node** (`mongodb-0c218fe88169f5d0`): MongoDB Atlas Analytics Node
- **MongoDB Atlas Data Federation** (`mongodb-c682bbc6e08dff15`): MongoDB Atlas Data Federation; mongodb-atlas-data-federation
- **MongoDB Atlas Triggers and Functions** (`mongodb-e3778c0687095883`): MongoDB Atlas Triggers and Functions
- **MongoDB autoCompact** (`mongodb-a4a89b2c0375d071`): MongoDB autoCompact; autoCompact; background compaction; mongodb background compaction
- **MongoDB Backup and Restore** (`mongodb-9f201994ae74aeb1`): MongoDB Backup and Restore
- **MongoDB Connection String URI** (`mongodb-4d0d315c971c60dc`): MongoDB Connection String URI
- **MongoDB Driver Internals** (`mongodb-09f41dedaf4ff2a9`): MongoDB Driver Internals
- **MongoDB Drivers** (`mongodb-b5639184c589a4f1`): MongoDB Drivers; mongodb-drivers
- **MongoDB Java driver 5.x version timeline & 8.0 compatibility** (`mongodb-0c6fc1af14b63ca6`): MongoDB Java driver 5.x version timeline & 8.0 compatibility
- **MongoDB Performance Benchmarking** (`mongodb-c2e8019b44ddddf1`): MongoDB Performance Benchmarking
- **MongoDB Performance Regression Detection and Testing Methodology** (`mongodb-ab8aecd20ee36a07`): MongoDB Performance Regression Detection and Testing Methodology
- **MongoDB Performance Troubleshooting** (`mongodb-9a5d6d6d6827148c`): MongoDB Performance Troubleshooting
- **MongoDB Spark Connector and Databricks Integration** (`mongodb-f78f0e85b6a1f92b`): MongoDB Spark Connector and Databricks Integration
- **MongoDB Stress, Soak, and Chaos-Resilience Testing** (`mongodb-041e0c13bb9aac86`): MongoDB Stress, Soak, and Chaos-Resilience Testing
- **mongosh Reference** (`mongodb-dbc7aadec9256534`): mongosh Reference; mongosh-reference
- **Performance Impact** (`mongodb-28b4bd53f636eb61`): Performance Impact
- **RESTHeart** (`mongodb-d1d29980f15ac9cd`): RESTHeart
- **Retryable Transactions** (`mongodb-575253db176be40a`): Retryable Transactions
- **Transaction Limits** (`mongodb-2d54318676631383`): Transaction Limits
- **WiredTiger Compaction Algorithm** (`mongodb-cfae06f226515122`): WiredTiger Compaction Algorithm
<!-- mongodb-research-inventory:end -->

## Previous ranked snapshot (retained)

# Research queue, ranked by Concept Viability Score

Generated from the live hub queue and saved cohort outcomes. This is a view; the queue remains the source of truth.
Held, repair-required and coverage-review rows require their existing workflow; they are not fresh-discovery assignments.
Pending unique concepts: **108**. Score gate: **3.2**. Repository frontier coverage remains separate.

| # | CVS | decision | concept | parent | mode | tree state |
|---:|---:|---|---|---|---|---|
| 1 | 4.85 | RESEARCH | Apple Intelligence Home camera summaries and video search | Apple Intelligence | dr | frontier |
| 2 | 4.40 | RESEARCH | Safari Apple Intelligence browsing and generated extension workflows | Apple Intelligence | dr | frontier |
| 3 | 4.30 | RESEARCH | Describe a Shortcut natural-language automation authoring | Shortcuts Use Model and intelligent automation | dr | frontier |
| 4 | 4.30 | HELD | Disk IOPS Burst Credit Depletion Playbook | Atlas Triage Workflows | revisit | held |
| 5 | 4.10 | HELD | Pipeline Optimization | MongoDB Aggregation Pipeline | revisit | held |
| 6 | 3.95 | REVIEW | Matryoshka dimension truncation for storage | Vector Search Quantization and Embedding Storage Cost | — | coverage-review |
| 7 | 3.90 | HELD | SBE vs classic engine defaults | MongoDB 8.0 performance changes &amp; read-path regressions vs 7.0 | revisit | held |
| 8 | 3.85 | HELD | Entra ID group overage in Atlas | Atlas Identity Federation and Resource Policy Boundaries | revisit | held |
| 9 | 3.85 | HELD | maxTimeMS (Server-side Operation Timeout) | Client Side Operations Timeout (CSOT) | revisit | held |
| 10 | 3.80 | HELD | majority-ack write concern change | MongoDB 8.0 performance changes &amp; read-path regressions vs 7.0 | revisit | held |
| 11 | 3.80 | HELD | mtools Log Analysis Integration | FTDC and Log Tooling | revisit | held |
| 12 | 3.80 | HELD | Online Archive query performance optimization | DATE Criteria | revisit | held |
| 13 | 3.80 | REVIEW | Terraform tag enforcement for Atlas clusters | Resource Tags and Cost Allocation (Showback/Chargeback) | — | coverage-review |
| 14 | 3.70 | RESEARCH | Siri content loading through UIKit drag interactions | Siri app actions confirmation and contextual cues | dr | frontier |
| 15 | 3.65 | HELD | App Services Migration Paths | MongoDB Atlas App Services | revisit | held |
| 16 | 3.65 | REVIEW | Atlas Operate-phase anomaly detection and budgets | FinOps Framework Applied to Atlas | — | coverage-review |
| 17 | 3.65 | HELD | Atlas WIF built-in vs callback authentication | Atlas Identity Federation and Resource Policy Boundaries | revisit | held |
| 18 | 3.65 | REVIEW | Cloud commit drawdown (EDP, MACC, GCP commit) via Atlas | Cloud Marketplace Billing for Atlas (AWS GCP Azure) | — | coverage-review |
| 19 | 3.65 | HELD | Deadline Propagation and Context Cancellation in MongoDB Drivers | Client Side Operations Timeout (CSOT) | revisit | held |
| 20 | 3.65 | HELD | Per-query fusion weighting | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | held |
| 21 | 3.65 | HELD | SERVER JIRA Ticket Regression Mapping | KB-Backed Troubleshooting | revisit | held |
| 22 | 3.60 | REVIEW | Atlas FOCUS Cost and Usage Report | Atlas Billing and Invoice Anatomy | — | coverage-review |
| 23 | 3.60 | HELD | DNS and SRV Records | MongoDB Atlas AWS Networking | revisit | held |
| 24 | 3.60 | HELD | Maintenance Impact Minimization | Atlas Maintenance Windows | revisit | held |
| 25 | 3.60 | RESEARCH | multikey index sort behaviour | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | — | frontier |
| 26 | 3.60 | RESEARCH | Read concern and causal consistency with secondary reads | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | — | frontier |
| 27 | 3.60 | HELD | read your own writes | Causal Consistency | revisit | held |
| 28 | 3.60 | RESEARCH | Sparse versus partial index equivalence | MongoDB Compound Index Design: ESR, Selectivity, Covering and Multikey Bounds | — | frontier |
| 30 | 3.50 | HELD | FTDC Storage Overhead &amp; Retention Budgeting | FTDC and Log Tooling | revisit | held |
| 31 | 3.45 | HELD | BM25 IDF corpus statistics | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | held |
| 32 | 3.45 | HELD | BM25 term frequency saturation and field length normalization | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | held |
| 33 | 3.45 | HELD | Deferring Maintenance | Atlas Maintenance Windows | revisit | held |
| 34 | 3.45 | HELD | Fusion score normalization strategies | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | held |
| 35 | 3.45 | HELD | M30 specs &amp; connection limits | Atlas cluster tiers (M30) &amp; major-version upgrade mechanics | revisit | held |
| 36 | 3.45 | HELD | Security Groups | MongoDB Atlas AWS Networking | revisit | held |
| 37 | 3.40 | HELD | Atlas Data API (EOL) | MongoDB Atlas App Services | revisit | held |
| 38 | 3.40 | REVIEW | Covered queries and projection design | Storage and Data-Lifecycle Cost Levers | — | coverage-review |
| 39 | 3.40 | REVIEW | Multikey index sort bounds | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | — | coverage-review |
| 40 | 3.30 | RESEARCH | Counter-document pattern | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | — | frontier |
| 41 | 3.30 | REVIEW | Field-name abbreviation trade-offs | Storage and Data-Lifecycle Cost Levers | — | coverage-review |
| 42 | 3.30 | REVIEW | M10 shared-vCPU dedicated tier economics | Atlas Pricing Programs, Cost Governance and TCO | — | coverage-review |
| 43 | 3.30 | RESEARCH | Tailable cursors and maxAwaitTimeMS | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | — | frontier |
| 44 | 3.25 | RESEARCH | Atlas backup/PITR and data transfer cost drivers | Atlas Pricing Programs, Cost Governance and TCO | — | frontier |
| 45 | 3.25 | HELD | Ranked and scored input pipeline eligibility | Atlas Hybrid Fusion and BM25 Diagnostics | revisit | held |
| 46 | 3.20 | REVIEW | Atlas Query Shape Insights | MongoDB Explain Plans, Query Planner and Plan Cache | — | coverage-review |
| 47 | 3.20 | REVIEW | FOCUS 1.3 Atlas cost reports | Atlas Cost Explorer and Billing Data API | — | coverage-review |
| 48 | 3.20 | RESEARCH | ICMP and setuid ping under Local Network attribution | Apple Platform Publishing (Mac App Store) | dr | frontier |
| 49 | 3.20 | HELD | Index Sufficiency Warning | Archive Rules | revisit | held |
| 50 | 3.20 | REVIEW | Namespace Insights | MongoDB Query Optimization Tooling: Compass Explain, Atlas Query Insights and Performance Advisor | — | coverage-review |
| 51 | 3.20 | RESEARCH | Sparse and partial indexes for $exists | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | — | frontier |
| 52 | 3.15 | REVIEW | $function and server-side JavaScript hardening | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | — | coverage-review |
| 53 | 3.15 | REVIEW | Atlas Charts billing dashboards | Atlas Billing Mechanics and Cost Visibility | — | coverage-review |
| 54 | 3.15 | HELD | Atlas GraphQL API (EOL) | MongoDB Atlas App Services | revisit | held |
| 55 | 3.15 | HELD | Atlas SQL Schema Builder | Atlas SQL Interface MongoSQL | revisit | held |
| 56 | 3.15 | REVIEW | Credit expiry and History table | Atlas Billing Mechanics and Cost Visibility | — | coverage-review |
| 57 | 3.15 | HELD | Custom HTTPS Endpoints (EOL) | MongoDB Atlas App Services | revisit | held |
| 58 | 3.15 | REVIEW | Index hints on time series collections | MongoDB Time-Series Query and Index Optimization | — | coverage-review |
| 59 | 3.15 | HELD | JIT user provisioning | Atlas Federated Authentication | revisit | held |
| 60 | 3.10 | HELD | Client Side Field Level Encryption (CSFLE) | Client Side Operations Timeout (CSOT) | revisit | held |
| 61 | 3.05 | BELOW-GATE | Local Network permission decision observed on macOS 27.2 via nehelper and mDNSResponder logs | Apple Platform Publishing (Mac App Store) | dr | frontier |
| 62 | 3.05 | HELD | Memory Limits and allowDiskUse | MongoDB Aggregation Pipeline | revisit | held |
| 63 | 3.05 | REVIEW | nonCompliantResources drift monitoring | Cost Governance Guardrails (Resource Policies and IaC Cost Controls) | — | coverage-review |
| 64 | 3.05 | BELOW-GATE | Staged-source py2app prune and privileges.py split for dormant-code exclusion | Apple Platform Publishing (Mac App Store) | dr | frontier |
| 65 | 3.00 | REVIEW | $groupByDistinct internal stage | MongoDB Advanced Explain: Aggregation, Sharded Plans, Loose Index Scans and the 8.3 Cost-Based Ranker | — | coverage-review |
| 66 | 3.00 | REVIEW | Analytics node tier prorating | Atlas Cluster Topology and Tier Economics | — | coverage-review |
| 67 | 3.00 | HELD | App Services Deployment Model | MongoDB Atlas App Services | revisit | held |
| 68 | 3.00 | HELD | App Services Rules and Permissions | MongoDB Atlas App Services | revisit | held |
| 69 | 3.00 | HELD | App Services Schema Validation | MongoDB Atlas App Services | revisit | held |
| 70 | 3.00 | HELD | App Services Values and Secrets | MongoDB Atlas App Services | revisit | held |
| 71 | 3.00 | REVIEW | Atlas FOCUS report ingestion into FinOps tools | FinOps Framework Applied to Atlas | — | coverage-review |
| 72 | 3.00 | BELOW-GATE | Backup and PIT oplog storage region billing | Atlas Cluster Topology and Tier Economics | — | frontier |
| 73 | 3.00 | BELOW-GATE | Cost Explorer filters for AI services | Atlas Pricing Programs, Cost Governance and TCO | — | frontier |
| 74 | 3.00 | REVIEW | Marketplace private offers and contracts for Atlas | Cloud Marketplace Billing for Atlas (AWS GCP Azure) | — | coverage-review |
| 75 | 3.00 | HELD | MongoSQL ODBC Driver | Atlas SQL Interface MongoSQL | revisit | held |
| 76 | 3.00 | HELD | PII Masking &amp; Query Hash Anonymization | Diagnostic Tool Design | revisit | held |
| 77 | 3.00 | HELD | Power BI DirectQuery | Atlas SQL Interface MongoSQL | revisit | held |
| 78 | 3.00 | BELOW-GATE | Query limits and billing alerts for archive spend | Storage and Data-Lifecycle Cost Levers | — | frontier |
| 79 | 3.00 | REVIEW | Support line items per cloud provider on invoices | Atlas Billing Mechanics and Cost Visibility | — | coverage-review |
| 80 | 2.95 | REVIEW | Cross-organization billing and linked invoices | Atlas Billing and Invoice Anatomy | — | coverage-review |
| 81 | 2.95 | HELD | DATE criteria field types and formats | DATE Criteria | revisit | held |
| 83 | 2.95 | BELOW-GATE | Project-level billing change alerts | Atlas Billing Mechanics and Cost Visibility | — | frontier |
| 84 | 2.90 | BELOW-GATE | App Review reviewer OS and visit telemetry for Mac submissions | Apple Platform Publishing (Mac App Store) | dr | frontier |
| 85 | 2.85 | BELOW-GATE | Config shard versus dedicated config server cost | Atlas Cluster Topology and Tier Economics | — | frontier |
| 87 | 2.80 | BELOW-GATE | Retroactive support billing on reactivation | Atlas Billing Mechanics and Cost Visibility | — | frontier |
| 88 | 2.75 | BELOW-GATE | Atlas billing alert configuration via Admin API | Atlas Pricing Programs, Cost Governance and TCO | — | frontier |
| 89 | 2.75 | REVIEW | Cross-Organization Billing | Resource Tags and Cost Allocation (Showback/Chargeback) | — | coverage-review |
| 91 | 2.70 | HELD | Quantile Estimation (DDSketch) | Client Side Operations Timeout (CSOT) | revisit | held |
| 92 | 2.65 | HELD | Atlas CLI Failure Scenarios | Atlas CLI | revisit | held |
| 93 | 2.55 | BELOW-GATE | explanation-doc-writing | — | — | frontier |
| 94 | 2.50 | HELD | MongoDB Atlas Data Federation Architecture Internals | MongoDB Atlas Data Federation | revisit | held |
| 95 | 2.50 | HELD | MongoDB Atlas Data Federation Benchmark Metrics | MongoDB Atlas Data Federation | revisit | held |
| 96 | 2.50 | HELD | MongoDB Atlas Data Federation Failure Scenarios | MongoDB Atlas Data Federation | revisit | held |
| 97 | 2.50 | HELD | MongoDB Atlas Data Federation Operational Runbook | MongoDB Atlas Data Federation | revisit | held |
| 98 | 2.50 | HELD | MongoDB Drivers Architecture Internals | MongoDB Drivers | dr | held |
| 99 | 2.50 | HELD | MongoDB Drivers Benchmark Metrics | MongoDB Drivers | dr | held |
| 100 | 2.50 | HELD | MongoDB Drivers Failure Scenarios | MongoDB Drivers | dr | held |
| 101 | 2.50 | HELD | MongoDB Drivers Operational Runbook | MongoDB Drivers | dr | held |
| 102 | 2.50 | HELD | mongosh Reference Architecture Internals | mongosh Reference | dr | held |
| 103 | 2.50 | HELD | mongosh Reference Benchmark Metrics | mongosh Reference | dr | held |
| 104 | 2.50 | HELD | mongosh Reference Failure Scenarios | mongosh Reference | dr | held |
| 105 | 2.50 | HELD | mongosh Reference Operational Runbook | mongosh Reference | dr | held |
| 106 | 2.25 | HELD | Error Codes and Troubleshooting Benchmark Metrics | Error Codes and Troubleshooting | revisit | held |
| 107 | 2.05 | BELOW-GATE | typed-claims-publication | — | — | frontier |
| 108 | 1.85 | BELOW-GATE | project-registrar-single-project-spot-check | — | — | frontier |
