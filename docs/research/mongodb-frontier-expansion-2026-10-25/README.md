# MongoDB frontier expansion — 2026-10-25

Version: 1.0.0
Delta: initial independently reviewed frontier plan.

Status: 33 pending frontier concepts applied and locally verified; CI delivery pending.

This pass examined 42 proposals. It selected 33 genuinely missing local frontier labels, rejected eight already-present proposals and retained one below-threshold skip. All 34 scored gaps passed the canonical CVS checker with zero arithmetic or decision failures. The selected CVS range is 3.40–4.65. No concept is marked researched by this plan.

## Conceptual family map

### Parent / super-domain

- MongoDB Replication
- MongoDB Security Architecture
- MongoDB Aggregation Pipeline
- MongoDB Monitoring and Observability
- MongoDB Driver Internals

### Siblings

- MongoDB Atlas Search
- MongoDB Atlas Stream Processing
- MongoDB Atlas Online Archive
- MongoDB Atlas Data Federation
- CMAP Connection Pooling

### Children / sub-concepts


### Adjacent / cross-over

- Atlas Stream Processing per-event vector search enrichment
- Client-side encryption DEK rewrapping with rewrapManyDataKey
- Atlas Data Federation single-collection proxy optimization
- Load-balanced cursor and transaction connection pinning
- Aggregation EJSON round-tripping and BSON type preservation

### Frontier / emerging

- Tracked query memory across explain, currentOp and profiler
- validate full versus BSON conformance checks across upgrades
- Aggregation EJSON round-tripping and BSON type preservation
- Query-settings representative-query backfill and FCV boundaries
- BinData subtype-aware aggregation dispatch and invalid inputs

## Scored gap table

CVS scores are planning judgments. Novelty measures the missing local coverage, and source links are discovery leads. These rows do not establish claim verification or research completeness.

| Concept | Parent | Rel | Use | Nov | Int | Via | CVS | Decision |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Queryable Encryption prefix, suffix and substring query configuration | MongoDB Security Architecture | 5 | 5 | 4 | 4 | 5 | 4.65 | RESEARCH |
| Change-stream point-in-time images and retention lifecycle | MongoDB Replication | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| Client-side encryption DEK rewrapping with rewrapManyDataKey | MongoDB Security Architecture | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| Load-balanced cursor and transaction connection pinning | CMAP Connection Pooling | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| MongoClient bulkWrite multi-namespace batching and result cursors | MongoDB Driver Internals | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| Queryable Encryption ESC/ECOC metadata compaction and leakage tradeoffs | MongoDB Security Architecture | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| Replication flow-control tickets and majority-commit lag diagnosis | MongoDB Replication | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| Resharding catch-up critical section and commit boundary | Shard Key Design and Resharding as Cost Levers | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| Sharding catalog consistency checks beyond index parity | Shard Key Design and Resharding as Cost Levers | 5 | 5 | 4 | 4 | 4 | 4.50 | RESEARCH |
| Tracked query memory across explain, currentOp and profiler | MongoDB Monitoring and Observability | 5 | 5 | 3 | 4 | 5 | 4.45 | RESEARCH |
| Atlas Online Archive pause, expiration and deletion lifecycle boundaries | MongoDB Atlas Online Archive | 5 | 4 | 4 | 4 | 5 | 4.40 | RESEARCH |
| Atlas Stream Processing per-event vector search enrichment | MongoDB Atlas Stream Processing | 5 | 4 | 4 | 5 | 4 | 4.40 | RESEARCH |
| Atlas Data Federation single-collection proxy optimization | MongoDB Atlas Data Federation | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Atlas Online Archive sharding identity safety and orphan recovery | MongoDB Atlas Online Archive | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Atlas Stream Processing cached lookup TTL and eviction | MongoDB Atlas Stream Processing | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Atlas Stream Processing partition idleness versus window idleness | MongoDB Atlas Stream Processing | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Atlas Stream Processing resumable initial sync and source retention | MongoDB Atlas Stream Processing | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Atlas Stream Processing throttle rate limits and backpressure | MongoDB Atlas Stream Processing | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| MongoDB Search concurrent segment execution | MongoDB Atlas Search | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| MongoDB Search searchNodePreference routing and result consistency | MongoDB Atlas Search | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Queryable Encryption contention and range-index tuning | MongoDB Security Architecture | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Sharded routing-cache invalidation and stale-metadata diagnosis | MongoDB Query Shape Optimization: Sort, Pagination, Operators and Sharded Targeting | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Split change-stream event fragments and fragment-token recovery | MongoDB Replication | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| Targeted mirrored reads for replica cache warming | MongoDB Replication | 5 | 4 | 4 | 4 | 4 | 4.25 | RESEARCH |
| NoWritesPerformed and retryable batch outcome ambiguity | Retryable Writes | 5 | 5 | 3 | 3 | 4 | 4.15 | RESEARCH |
| validate full versus BSON conformance checks across upgrades | Corruption (validate, --repair, wt CLI) | 5 | 4 | 3 | 3 | 5 | 4.05 | RESEARCH |
| Awaitable hello streaming monitoring and FaaS polling | SDAM Topology State Machine | 5 | 4 | 3 | 4 | 4 | 4.05 | RESEARCH |
| Atlas Stream Processing Lambda external functions and error semantics | MongoDB Atlas Stream Processing | 5 | 3 | 4 | 4 | 4 | 4.00 | RESEARCH |
| Atlas Stream Processing regional failover processor semantics | MongoDB Atlas Stream Processing | 5 | 3 | 4 | 4 | 4 | 4.00 | RESEARCH |
| MongoDB Search synonym map update propagation and validation | MongoDB Atlas Search | 5 | 3 | 4 | 4 | 4 | 4.00 | RESEARCH |
| Aggregation EJSON round-tripping and BSON type preservation | MongoDB Aggregation Pipeline | 4 | 4 | 4 | 4 | 4 | 4.00 | RESEARCH |
| Query-settings representative-query backfill and FCV boundaries | MongoDB query planner, plan cache, query settings and hints | 5 | 4 | 3 | 3 | 4 | 3.90 | RESEARCH |
| BinData subtype-aware aggregation dispatch and invalid inputs | BSON BinData vector ingestion | 4 | 3 | 3 | 3 | 4 | 3.40 | RESEARCH |
| currentOp versionContext for FCV transition diagnosis | Feature Compatibility Version (FCV) | 4 | 2 | 3 | 2 | 4 | 3.00 | SKIP |

The machine-readable score table preserves all five axes, rationale and primary-source URLs. New candidates are ordered by CVS, then viability, relevance and interest. Existing queue order and the frozen ranked projections remain unchanged.

## Researched this run

No claim research or skill installation was performed. The deliverable is pending research candidates, parent links, queue rows and score provenance.

## Skipped and failed

- Already present: Long-running secondary read termination during orphan cleanup. Existing concept and multiple frontier children already cover termination, QueryPlanKilled, resume-from-key, delay and snapshot history. Current docs confirm mechanism; no additional gap retained.
- Already present: 8.3 cost-based ranker and cardinality estimation. Existing advanced-explain parent, plan-cache ranker, sampling CE and sorted-query frontier already cover proposed mechanism.
- Already present: SBE and classic plan-cache shape/key behavior. Existing complete nodes and frontier labels cover keys, parameterization, DDL invalidation and $in expansion.
- Already present: Same-key resharding and jumbo-chunk shard removal. Existing frontier explicitly includes same-key redistribution and balancer/jumbo remediation; retained only the distinct commit-critical-section mechanism.
- Already present: Atlas vector automatic quantization. Already represented by multiple queued mechanism labels and parent coverage.
- Already present: Atlas hybrid rank and score fusion. Already queued directly; no new missing delta.
- Already present: Online Archive partitioning and query cost limits. Partition-field and billing mechanisms already in frontier and queues.
- Already present: Slow in-progress query logging. Exact existing frontier already covers this mechanism.
- Below threshold: currentOp versionContext for FCV transition diagnosis (CVS 3.00). The narrower diagnostic field scored low on expected recurring use.

Independent review corrected the DEK candidate scope: rewrapping existing DEKs under a new wrapping key is distinct from replacing DEKs or re-encrypting stored data. No material audit findings remain.

## Optimization results

No skills or executable prompts changed, so skill optimization, prompt optimization and skill-tree rebalancing were outside this frontier-only pass. The saved user prompt is a continuation record.

## Handoffs

The 33 selected candidates are eligible inputs for later research. Both historical ranked projections and the unavailable remote execution plan retain their prior assignments. A future ranked-run dispatch must deliberately include these new candidates in a new plan; this pass does not globally rerank or restart existing research.

The discovery pass also flagged an older archive reference for future re-verification against current archive lifecycle documentation. That source lead is not a silently applied technical correction.

## Saturation verdict

FRONTIER EXPANDED. This was one source-backed discovery pass, with no saturation assertion and no concept-count budget. All qualified candidates found in the pass were retained. Local availability does not prove remote coverage while the other source machine is unavailable.

## Updated concept tree

Application uses append-only child labels under existing parents and the native queue-only sync. It must preserve every existing node, research date, source count, binding, queue row, reservation and frozen ranked plan. Pending labels become visible in both runtime trees, the TUI outline and the generated website tree. Guarded read-back passed for all 33 raw parent links, queue rows and CVS values in both targets. Node counts and all other metadata stayed unchanged. The loaded hub frontier API independently returned all 33 new labels. Existing ranked projections and 139 protected research-state files stayed unchanged.

## Candidate scopes and primary-source leads

### Queryable Encryption prefix, suffix and substring query configuration

String query schemas, query length bounds, mutually exclusive substring mode, and migration from preview query types; verify server and driver compatibility before adoption.

Local gap: No Queryable Encryption label or child exists in either inventory; generic CSFLE does not capture randomized searchable string indexes. Fresh official release confirms GA in September 2026.

https://www.mongodb.com/products/updates/now-ga-queryable-encryption-prefix-suffix-and-substring-support/

https://www.mongodb.com/docs/manual/core/queryable-encryption/qe-create-encryption-schema/

### Change-stream point-in-time images and retention lifecycle

Differentiate updateLookup current-document reads from stored pre-image based event-time images; required/whenAvailable, config.system.preimages retention, oplog-coupled expiry, and missing images after logical initial sync.

Local gap: Change-stream resumability and resume-token concepts exist, but labels contain no pre/post-image retention or lookup-consistency frontier. The delta is image availability and temporal correctness rather than token handling.

https://www.mongodb.com/docs/manual/changestreams/

### Client-side encryption DEK rewrapping with rewrapManyDataKey

Rewrapping existing key-vault DEKs under a new CMK; distinguish wrapping-key/provider rotation from DEK replacement and data re-encryption.

Local gap: KMS Key Rotation Atlas concerns managed at-rest keys; no existing label addresses client-side encrypted DEK rewrapping or the key-vault boundary.

https://www.mongodb.com/docs/v8.0/core/queryable-encryption/fundamentals/keys-key-vaults/

### Load-balanced cursor and transaction connection pinning

loadBalanced handshake/serviceId discovery, connection rather than server pinning, cursor getMore/killCursors lifetime, transaction affinity, and pool-exhaustion implications.

Local gap: CMAP and distributed transactions are broad existing nodes, but labels have no MongoDB load-balanced pinning frontier. This is backend affinity over a load balancer, distinct from ordinary pool sizing. Adjacent CMAP pack was absent.

https://specifications.readthedocs.io/en/latest/load-balancers/load-balancers/

### MongoClient bulkWrite multi-namespace batching and result cursors

MongoDB 8.0 client-level multi-namespace writes: ops/nsInfo mapping, command splitting against hello limits, verboseResults/errorsOnly inversion, partial-result aggregation, and response cursor consumption.

Local gap: bulk-write-ordering and Streaming Write Semantics exist, but no multi-namespace bulkWrite frontier does. The gap is cross-namespace wire batching and result reconstruction, not ordered/unordered write semantics alone.

https://specifications.readthedocs.io/en/latest/crud/bulk-write/

### Queryable Encryption ESC/ECOC metadata compaction and leakage tradeoffs

Metadata write amplification, ESC/ECOC integrity, compactStructuredEncryptionData scheduling, storage recovery and compaction leakage.

Local gap: Existing encryption coverage has no searchable-encryption metadata lifecycle; ordinary WiredTiger compaction is a different mechanism.

https://www.mongodb.com/docs/manual/core/queryable-encryption/fundamentals/manage-collections/

### Replication flow-control tickets and majority-commit lag diagnosis

How primary write admission uses majority-commit lag, flowControlTargetLagSeconds, ticket limits, and primary-only flowControl diagnostics. Distinguish this from WiredTiger execution tickets and lag on any individual secondary.

Local gap: No flow-control concept or frontier child exists. Replication Lag Monitoring and majority commit point mechanics cover symptoms/visibility, while this delta is the feedback mechanism that throttles primary writes.

https://www.mongodb.com/docs/manual/replication/

### Resharding catch-up critical section and commit boundary

Donor/recipient cloning and oplog catch-up, write-blocking entry, commitReshardCollection early blocking, strict consistency, rename/drop transition, and the point after which abort is impossible.

Local gap: Reshard to the same key and zone/cost levers exist, but labels have no resharding phase or critical-section concept. The delta is correctness and application latency during cutover, not shard-key choice or redistribution economics.

https://www.mongodb.com/docs/manual/reference/command/reshardcollection/

### Sharding catalog consistency checks beyond index parity

checkMetadataConsistency namespace scopes and inconsistency cursor; distinguish config-server/shard/in-memory chunk metadata from optional index checks; investigate current 9.0 strict-chunk threshold with explicit version gating.

Local gap: Detecting inconsistent indexes across shards exists, but no frontier covers non-index catalog consistency. This scope excludes redoing index parity and instead covers placement/catalog checks after maintenance.

https://www.mongodb.com/docs/manual/reference/command/checkmetadataconsistency/

### Tracked query memory across explain, currentOp and profiler

Investigate per-query versus blocking-stage peak tracking and diagnostic correlation.

Local gap: Existing memory-limit and profiling labels do not name tracked-memory correlation.

https://www.mongodb.com/docs/v8.3/reference/explain-results/

### Atlas Online Archive pause, expiration and deletion lifecycle boundaries

Pausing ingestion while expiration continues; archive deletion grace interval, cluster-deletion consequences and inability to recover removed archive objects.

Local gap: Existing expiration rule covers retention configuration; missing delta is lifecycle coupling across pause, deletion and cluster removal, including the five-day object purge.

https://www.mongodb.com/docs/atlas/online-archive/pause-resume-online-archive/

https://www.mongodb.com/docs/atlas/online-archive/manage-online-archive/

### Atlas Stream Processing per-event vector search enrichment

Middle-stage $vectorSearch against registered Atlas collections; per-event explicit vectors or auto-embedded text, result attachment and DLQ versus processor-failure errors.

Local gap: Vector Search packs describe retrieval for applications; no existing ASP child or queue binds per-event semantic enrichment to stream processing failure semantics.

https://www.mongodb.com/docs/atlas/atlas-stream-processing/sp-agg-vectorsearch/

### Atlas Data Federation single-collection proxy optimization

Virtual collections mapped to one Atlas collection forward queries to Atlas; mapping multiple collections disables the proxy optimization; impact on scan cost and profiling appName.

Local gap: Federation architecture label is broad; no child, alias or queue names the mapping-dependent direct proxy fast path, distinct from object-store partition pruning.

https://www.mongodb.com/docs/atlas/data-federation/query/query-federated-database/

### Atlas Online Archive sharding identity safety and orphan recovery

Archive deletion identity (_id plus shard keys), immutability of eligible documents, pausing before sharding and resharding-induced orphan cleanup.

Local gap: Existing archive skill omits shard and reshard terms and incorrectly associates ORPHANED only with a missing cluster. No child or queue covers the identity hazard.

https://www.mongodb.com/docs/atlas/online-archive/manage-online-archive/

### Atlas Stream Processing cached lookup TTL and eviction

$cachedLookup enrichment cache staleness, TTL, per-processor memory cap, expired/random eviction, and lack of let/pipeline support.

Local gap: Existing ASP reference includes ordinary $lookup but no cachedLookup; no queue or child covers bounded enrichment-cache behavior.

https://www.mongodb.com/docs/atlas/atlas-stream-processing/sp-agg-cachedlookup/

### Atlas Stream Processing partition idleness versus window idleness

Kafka partitionIdleTimeout excludes idle partitions from watermark progress; window idleTimeout closes idle event-time windows using processing time.

Local gap: Generic watermarks are present, but existing reference contains neither idleTimeout nor partitionIdleTimeout; separate idle sources and idle partitions need distinct controls.

https://www.mongodb.com/docs/atlas/atlas-stream-processing/architecture/

### Atlas Stream Processing resumable initial sync and source retention

Change-stream initialSync partition copies, persisted copy progress, source starting oplog position, supported _id ordering and replay after interruption.

Local gap: Generic checkpoint and migration CDC labels exist; ASP reference lacks initialSync and does not describe checkpointing the source-copy phase.

https://www.mongodb.com/docs/atlas/atlas-stream-processing/architecture/

### Atlas Stream Processing throttle rate limits and backpressure

$throttle dual byte/message limits, oversized-document handling, downstream quota protection and source-lag monitoring.

Local gap: No ASP throttle concept exists; general throttling or operation rejection labels address different systems.

https://www.mongodb.com/docs/atlas/atlas-stream-processing/sp-agg-throttle/

### MongoDB Search concurrent segment execution

$search concurrent intra-query parallelism on dedicated Search Nodes; segment-level execution versus request-level load balancing and workload tradeoffs.

Local gap: Existing Search reference contains no concurrent option; existing node sizing covers capacity but not explicit segment-parallel query execution.

https://www.mongodb.com/docs/search/query/aggregation-stages/search/

### MongoDB Search searchNodePreference routing and result consistency

Stable arbitrary routing keys, default search-node load balancing and limits of consistency during data, index, topology and availability changes.

Local gap: Existing Search reference has no searchNodePreference. Pagination and index-lag concepts do not cover routing affinity or its consistency limits.

https://www.mongodb.com/docs/search/query/aggregation-stages/search/

### Queryable Encryption contention and range-index tuning

Counter partitioning for repeated encrypted values; contention versus read cost, range bounds, precision and trimFactor throughput tradeoffs.

Local gap: Neither a searchable-encryption contention mechanism nor encrypted range-index parameter coverage appears in trees, aliases, frontier children, manifests or queues.

https://www.mongodb.com/docs/manual/core/queryable-encryption/fundamentals/encrypt-and-query/

### Sharded routing-cache invalidation and stale-metadata diagnosis

Separate query predicate targeting from cached routing metadata; collection/database/global flushRouterConfig scope, automatic refresh, and limits of router refresh when authoritative shard metadata disagrees.

Local gap: Sharded query targeting and orphan filtering already exist. No routing-cache or stale-config concept exists; this frontier explains cache freshness and safe diagnostic scope rather than index-based shard targeting.

https://www.mongodb.com/docs/manual/reference/command/flushRouterConfig/

### Split change-stream event fragments and fragment-token recovery

Use $changeStreamSplitLargeEvent only as the last stage; top-level-field splitting limitations, splitEvent fragment/of metadata, consumer reassembly, and resuming from a fragment token.

Local gap: Neither split-event nor fragment concepts occur in labels. Existing resume-token coverage concerns complete events; per-fragment tokens and events exceeding BSON size introduce a separate reconstruction/recovery contract.

https://www.mongodb.com/docs/manual/reference/operator/aggregation/changestreamsplitlargeevent/

### Targeted mirrored reads for replica cache warming

General mirrored-read sampling versus 8.2 targetedMirroring tags, hidden-node warming, eligible source nodes, and mirroredReads observability.

Local gap: Neither mirrored reads nor targeted mirrored reads occurs in labels. Election timing does not describe the cache-warming work that reduces cold-cache failover latency.

https://www.mongodb.com/docs/manual/replication/

### NoWritesPerformed and retryable batch outcome ambiguity

Use the NoWritesPerformed error label to distinguish zero work from potentially partial work after retryable batch failures; preserve server/driver version boundaries and distinguish CSOT retry budgets.

Local gap: Retryable Writes is an existing leaf, and Java retry semantics/CSOT are covered elsewhere. No child isolates proof of zero writes versus ambiguous or partial batch outcomes. Existing retry pack was absent, so novelty is conservatively reduced.

https://www.mongodb.com/docs/manual/core/retryable-writes/

### validate full versus BSON conformance checks across upgrades

Investigate full validation, explicit BSON conformance and upgrade-related validation coverage.

Local gap: Existing corruption recovery is broad and no frontier names the validation-option boundary.

https://www.mongodb.com/docs/v8.3/reference/method/db.collection.validate/

### Awaitable hello streaming monitoring and FaaS polling

topologyVersion process/counter semantics, awaitable hello and OP_MSG exhaust, dedicated RTT connections, and serverMonitoringMode auto/poll/stream including FaaS detection.

Local gap: SDAM is an existing broad leaf with no children. The proposed frontier isolates the concrete monitoring protocol and the FaaS exception rather than repeating topology classification or server-selection timeout. Adjacent named pack was not present for fact-level confirmation.

https://specifications.readthedocs.io/en/latest/server-discovery-and-monitoring/server-monitoring/

### Atlas Stream Processing Lambda external functions and error semantics

$externalFunction synchronous/asynchronous invocation, same-region Lambda, Unified AWS Access permissions and onError boundaries.

Local gap: Existing ASP reference contains no Lambda or externalFunction coverage; cloud connector labels do not describe execution and error semantics.

https://www.mongodb.com/docs/atlas/atlas-stream-processing/sp-agg-externalfunction/

### Atlas Stream Processing regional failover processor semantics

Graceful, forced and dry-run failover; checkpoint transfer, at-least-once delivery and region-specific private Kafka connections.

Local gap: No failover processor label exists. Generic MongoDB replica-set failover does not describe ASP regional execution or connector rebinding.

https://www.mongodb.com/docs/atlas/atlas-stream-processing/architecture/

### MongoDB Search synonym map update propagation and validation

Same-database synonym source lifecycle, automatic eventual map refresh without reindexing, invalid documents blocking index creation and mapping-size cost.

Local gap: Existing skill describes equivalent/explicit synonym syntax, but no tree/queue mechanism covers watched synonym updates or validation failure; this scope excludes basic synonym syntax.

https://www.mongodb.com/docs/search/indexes/synonyms/

### Aggregation EJSON round-tripping and BSON type preservation

Investigate canonical versus relaxed EJSON, deserialize round trips and conversion error handling.

Local gap: No EJSON or Extended JSON conversion label exists in either tree, aliases or frontier queues.

https://www.mongodb.com/docs/manual/reference/operator/aggregation/serializeejson/

### Query-settings representative-query backfill and FCV boundaries

Investigate hash-only settings, missing representative queries and asynchronous FCV-gated backfill.

Local gap: Existing settings inspection and pinning labels omit representative-query lifecycle.

https://www.mongodb.com/docs/v8.3/reference/command/setquerysettings/

### BinData subtype-aware aggregation dispatch and invalid inputs

Investigate subtype inspection, null/missing values and errors before binary/vector conversion.

Local gap: Existing BinData ingestion does not expose an explicit subtype-inspection frontier.

https://www.mongodb.com/docs/manual/reference/operator/aggregation/subtype/

### currentOp versionContext for FCV transition diagnosis

Investigate operation-level FCV context during compatibility transitions.

Local gap: FCV pinning is present but the operation-context diagnostic field is not named.

https://www.mongodb.com/docs/v8.3/release-notes/8.3/


## Validation and access

- Canonical CVS checker:34 scored rows,0 arithmetic or decision failures.
- Independent planning/source audit: passed after the DEK scope correction.
- Guarded read-back:33 new pending children and queue entries in each target,17 parents,0 new researched nodes.
- Existing metadata and queue prefixes: preserved.
- Protected plan/manifest/reservation/ranked files:139 unchanged.
- Native helper idempotence:0 byte changes on exact post-state copies.
- Narrow tests:37 passed (2 llmsx,10 hub,25 site).
- Deterministic tree/context regeneration: matched; context byte-identical.
- Loaded hub MCP frontier API:33/33 present, correct parent and CVS values.
- Installed Explorer data loader with explicit updated hub/publication paths:33/33 frontier and queued; no interactive GUI was launched.

The original /Users/mitch/dev/llms-explorer checkout has its own preserved divergent snapshot and remains on older data. Use the updated canonical hub explicitly with the installed CLI:

```sh
/Users/mitch/.local/pipx/venvs/pip/bin/llmsx explorer --repo /Users/mitch/.global-ai-hub --no-sync
```

The generated tree retains the previous maximum researched date by design. Adding pending frontier labels does not advance research dates.
