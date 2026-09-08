---
title: "Real-Time OLAP and Analytical Databases"
description: "Real-time OLAP databases are the query and storage engines that answer"
---

# Real-Time OLAP & Analytical Databases

## Overview

Real-time OLAP databases are the **query and storage engines** that answer
analytical questions (aggregations, group-bys, filters, top-N, time-series
rollups) over large, **continuously updating** datasets with **sub-second
latency** and **high concurrency**. They sit between stream processing (which
transforms events in flight — da-14) and the BI/semantic layer (da-18), serving
as the low-latency serving layer for dashboards, monitoring, and
user/customer-facing analytics.

What makes an engine "real-time OLAP" rather than a cloud data warehouse:

- **Fresh data**: rows are queryable seconds (often sub-second) after they land,
  via streaming ingestion — not after a nightly batch load.
- **High concurrency / QPS**: built to serve thousands of concurrent queries
  (a per-user dashboard feature), not a handful of internal analysts. ClickHouse
  reports 1,000+ concurrent queries per node; Snowflake defaults to ~8 queries
  per warehouse, Redshift caps ~50 concurrent across queues
  ([ClickHouse, 2025](https://clickhouse.com/blog/cloud-data-warehouses-cost-performance-comparison)).
- **Tight latency SLAs**: tens of milliseconds, achieved with columnar storage,
  vectorized execution, and pre-aggregation/indexing.

This skill covers the **engines and the query layer**. It is the OLAP-database
node of the data-analytics curriculum (da-1 onward); it does not cover stream
processing (da-14), pipeline orchestration (da-13), or the metrics layer (da-18).

## Core Concepts

### 1. Columnar storage
Data is stored **by column, not by row**. Analytical queries touch few columns
but many rows, so columnar layout reads only the needed columns, drastically
cutting I/O, and stores like-typed values together so they compress far better
(delta, dictionary, RLE, LZ4/ZSTD). This is the foundational OLAP advantage over
row stores ([SQLFlash, 2025](https://sqlflash.ai/article/20250722_olap-database-architecture/);
[Airbyte, 2024](https://airbyte.com/data-engineering-resources/columnar-storage)).
Compression both saves storage and increases effective scan throughput.

### 2. Vectorized execution
Instead of processing one row at a time through a tuple-at-a-time interpreter,
the engine processes **batches (vectors) of column values** in tight loops,
exploiting CPU **SIMD** instructions, cache locality, and amortized
virtual-function/branch overhead. This yields multi-x to order-of-magnitude
speedups and is paired with columnar storage in every modern engine
([SQLFlash, 2025](https://sqlflash.ai/article/20250722_olap-database-architecture/);
[Cockroach Labs](https://www.cockroachlabs.com/blog/how-we-built-a-vectorized-execution-engine/)).
Even hybrid OLTP/OLAP systems (Google Spanner's columnar engine, OceanBase 4.3)
adopt columnar + vectorized execution for analytics, up to ~200x faster on live
data ([InfoQ, 2025](https://www.infoq.com/news/2025/09/google-spanner-oltp-olap-unify/)).

### 3. Real-time vs batch analytics (Lambda / Kappa)
- **Batch**: data loaded and computed periodically; high latency, high accuracy,
  cheap recompute (classic warehouse / BI pattern).
- **Real-time**: data queryable seconds after arrival; low latency, continuous
  ingestion.
- **Lambda** keeps two paths: a batch layer for correctness and a speed layer
  for low latency, at the cost of dual code and reconciliation.
- **Kappa** collapses everything into a single streaming path over an immutable
  log (e.g., Kafka), replaying when recompute is needed; simpler but harder for
  large historical batch jobs
  ([bix-tech, 2025](https://bix-tech.com/kappa-vs-lambda-vs-batch-choosing-the-right-data-architecture-for-your-business/);
  [Materialize](https://materialize.com/blog/when-is-kappa-architecture-most-effective/)).
  Most 2025 teams run a hybrid: streaming for operational decisions, batch for
  trusted reporting and model training
  ([makitsol, 2025](https://makitsol.com/real-time-analytics-vs-batch-processing-in-us-eu/)).

### 4. Streaming ingestion & upserts
Real-time OLAP engines ingest directly from **Kafka, Pulsar, and Kinesis**.
Apache Pinot transforms bytes from Kafka into queryable segments with sub-second
visibility from write to query as the default; end-to-end latency under 5s is
normal in production
([StarTree, 2025](https://startree.ai/resources/inside-the-flight-path-of-real-time-ingestion-in-apache-pinot/);
[Confluent](https://www.confluent.io/blog/real-time-analytics-with-kafka-and-pinot/)).
- **Append-only** is the simplest model (events never change). Pinot was
  append-only until 2022.
- **Upserts** let the same key be ingested many times but return only the latest
  value at query time. Pinot supports **full upsert** (new row replaces the old
  entirely) and **partial upsert** (only specified columns update)
  ([Pinot deep dive, 2026](https://pdpspectra.com/blog/apache-pinot-realtime-olap-2026/)).
  StarRocks uses a **primary-key table model** (cloud-native PK index in
  shared-data) for upserts and CDC-style mutable data
  ([StarRocks, 2025](https://www.starrocks.io/blog/vbill-payment-handling-billions-of-records-in-real-time-with-starrocks)).

### 5. Materialized views & pre-aggregation
Precompute aggregates so dashboard queries hit ready answers instead of scanning
raw rows.
- **Pinot star-tree index**: precomputes selected aggregation paths during
  segment generation; returns aggregation/group-by over billions of rows in
  milliseconds when the query shape matches configured dimensions/metrics, with
  no separate MV maintenance. Benchmarks show ~126x throughput over an inverted
  index (27 to 3,494 QPS on 4 vCPU)
  ([Pinot docs](https://docs.pinot.apache.org/build-with-pinot/indexing/star-tree-index);
  [StarTree, 2023](https://startree.ai/resources/star-tree-indexes-in-apache-pinot-part-2-understanding-the-impact-during-high-concurrency/)).
- **StarRocks / Doris asynchronous materialized views**: precompute joins and
  aggregations; the optimizer **automatically rewrites** base-table queries to
  use the MV (transparent query rewrite). Can be built over external lake
  catalogs (Iceberg/Hive/Hudi/Paimon)
  ([StarRocks docs](https://docs.starrocks.io/docs/using_starrocks/async_mv/use_cases/query_rewrite_with_materialized_views/);
  [Doris docs](https://doris.apache.org/docs/query-acceleration/materialized-view/async-materialized-view/overview/)).
- **ClickHouse materialized views / projections**: MVs are insert-time triggers
  that populate a target table (often with `AggregatingMergeTree`); projections
  store an alternate sorted/aggregated copy inside the part.

### 6. Indexing & the ClickHouse MergeTree model
ClickHouse's `MergeTree` family writes each `INSERT` as an immutable **data
part** (one file per column + index), merged in the background.
- **Sparse primary index**: one mark per **granule** (default 8,192 rows), stored
  in `primary.idx`; it does **not** enforce uniqueness, it lets the engine skip
  granules that cannot match a filter
  ([ClickHouse docs](https://clickhouse.com/docs/guides/best-practices/sparse-primary-indexes)).
- **Data-skipping indexes** (`minmax`, `set(N)`, `bloom_filter`, `ngrambf_v1`,
  `tokenbf_v1`) summarize non-key columns so granules can be skipped on
  secondary predicates; tune `GRANULARITY` and materialize after adding to
  existing data ([oneuptime, 2026](https://oneuptime.com/blog/post/2026-03-31-clickhouse-data-skipping-sparse-indexes/view)).
  Druid instead indexes within each **segment** (300-700 MB target) including
  inverted (bitmap) indexes for fast filtering
  ([Druid docs](https://druid.apache.org/docs/latest/design/segments/)).

### 7. Star-schema-on-OLAP & denormalization
Two camps: (a) **flatten/denormalize** into one wide table for fastest scans
(historically favored by Druid/ClickHouse, which are weaker at large joins);
(b) **keep the star/snowflake schema** and join at query time. StarRocks
explicitly preserves star/snowflake schemas and does real-time pre-processing at
load, with a strong distributed join engine, so you avoid the maintenance burden
of giant denormalized tables
([StarRocks features](https://docs.starrocks.io/docs/introduction/Features/);
[jusdb, 2026](https://www.jusdb.com/blog/starrocks-explained-the-complete-guide-to-real-time-analytics)).
Rule of thumb: denormalize when joins dominate latency and the engine joins
poorly; keep the star schema when the engine joins well and dimensions change.

### 8. Storage-compute separation / shared-data / tiered storage
Modern engines decouple **cheap durable object storage** (S3/GCS/Azure Blob)
from **elastic compute**, mirroring cloud-DW architecture but for real-time
workloads. StarRocks 3.0+ shared-data mode replaces storage-bearing backends
with **compute nodes (CN)** that cache hot data and read cold data from S3,
giving elastic scaling; 4.0 cut object-store API costs and reached 15-30s data
freshness in this mode
([StarRocks architecture](https://docs.starrocks.io/docs/introduction/Architecture/);
[Medium/Ding, 2025](https://medium.com/@tracymacding/faster-and-cheaper-real-time-analytics-with-starrocks-slashes-costs-5ceddaf5ca17)).
Tiered storage (hot local SSD to warm/cold object store) is now standard across
ClickHouse, Druid, Pinot, and StarRocks.

### 9. High-QPS user-facing / customer-facing analytics
"User-facing analytics" embeds analytics **in the product**, exposed to end
users, so every user gets personalized metrics, producing **hundreds of thousands
of QPS** rather than a few analyst sessions
([Pinot](https://pinot.apache.org/)). This is the workload real-time OLAP engines
exist for and where cloud DWs fail on concurrency/cost. Pinot has served
20,000+ QPS at sub-second p99 with 99.99% availability via star-tree
pre-aggregation; ClickHouse powers a customer-facing feature and a BI dashboard
from one service ([StarTree](https://startree.ai/resources/star-tree-index-in-apache-pinot-part-3-understanding-the-impact-in-real-customer/);
[ClickHouse, 2025](https://clickhouse.com/blog/clickhouse-vs-snowflake-for-real-time-analytics-comparison-migration-guide)).

## Tools / Frameworks

| Engine | Sweet spot | Notable strengths | Watch-outs |
| --- | --- | --- | --- |
| **ClickHouse** | Fastest single-table aggregation; warehouse + real-time in one | Vectorized engine, best compression, MergeTree indexing, 1,000+ concurrent q/node, ClickPipes CDC | Joins historically weaker; eventual-consistency mutations |
| **Apache Pinot** | Lowest-latency high-QPS user-facing analytics | Star-tree pre-agg, upserts, real-time Kafka/Pulsar ingestion, very high QPS | Operationally heavy; query flexibility narrower than full SQL DW |
| **Apache Druid** | Interactive exploration, time-series, high concurrency UIs | Segment + bitmap indexes, real-time + batch ingestion, instant visibility | Many services to operate; joins limited |
| **StarRocks** | Real-time analytics with joins on star schemas; lakehouse | Cost-based optimizer, strong joins, async MVs + query rewrite, PK upserts, shared-data on S3 | Younger ecosystem; cluster ops |
| **Apache Doris** | MPP analytics, MV-accelerated reporting | Async MVs, MySQL protocol, easier ops than some | StarRocks (its fork) often faster on benchmarks |
| **DuckDB** | Embedded / in-process single-node analytics | Columnar+vectorized, reads Parquet/CSV/Arrow directly, zero server | Not distributed, not a streaming/high-concurrency serving engine |
| Cloud DWs (**Snowflake / BigQuery / Redshift**) | Batch BI, ad-hoc internal analysis, scheduled dashboards | Managed, separation of storage/compute, Iceberg support | Concurrency limits + cost for real-time/user-facing serving |

Benchmarks (treat as directional, vendor-published): StarRocks reports
ClickHouse ~2.2x and Druid ~8.9x slower on 13 SSB flat-table queries; Pinot
reported 2-4x faster than Druid on some queries
([StarRocks](https://www.starrocks.io/blog/benchmark-test);
[StarTree](https://startree.ai/resources/a-tale-of-three-real-time-olap-databases/)).

## Methodology — choosing & designing

1. **Classify the workload.** Internal batch BI / ad-hoc to cloud DW (Snowflake/
   BigQuery/Redshift) or DuckDB for single-node. User-facing / sub-second / high
   QPS / streaming-fresh to a real-time OLAP engine.
2. **Match engine to query shape.**
   - Massive single-table aggregations, want simplicity: **ClickHouse**.
   - Per-user dashboards, very high QPS, fixed query shapes: **Pinot** (star-tree).
   - Interactive time-series exploration with high concurrency: **Druid**.
   - Real-time analytics needing **joins** on a star schema, lakehouse: **StarRocks**/**Doris**.
   - Embedded/local, no server, Parquet on disk: **DuckDB**.
3. **Decide the freshness path** (Kappa-style streaming vs hybrid Lambda) and the
   mutability model (append-only vs full/partial upsert).
4. **Model the schema**: denormalize for join-weak engines; keep star schema for
   StarRocks/Doris with strong join engines.
5. **Pre-aggregate intentionally**: star-tree (Pinot) or async MVs (StarRocks/
   Doris) or MV+projections (ClickHouse) for the known dashboard query shapes.
6. **Tune indexing**: sort key / primary index ordered by your most selective
   filter; add data-skipping/bitmap indexes for secondary predicates.
7. **Right-size storage**: separate storage/compute (shared-data) and tier hot to cold
   to control cost at scale.

## Practical Patterns

- **Kafka to real-time OLAP serving layer**: stream events to Kafka, ingest into
  Pinot/Druid/ClickHouse for sub-5s freshness, serve the product dashboard
  directly from the engine.
- **CDC upserts**: stream Postgres/MySQL changes (Debezium/ClickPipes) into a
  PK/upsert table so the OLAP store mirrors mutable source state.
- **Query-shape-driven pre-aggregation**: enumerate the dimensions/metrics your
  dashboards actually use, then build a matching star-tree or async MV; do not
  pre-aggregate everything.
- **Two-tier serving**: cloud DW for deep batch/historical + real-time OLAP engine
  for the hot, user-facing layer; sync via Iceberg or scheduled exports.
- **Sort by the dominant filter**: order the table by the column(s) most queries
  filter/range on (e.g., `(tenant_id, timestamp)`) so the sparse index skips the
  most data.

## Anti-Patterns

- **Using a cloud DW for user-facing analytics**: concurrency caps (Snowflake ~8,
  Redshift ~50) and per-query cost make per-user dashboards slow and expensive
  ([ClickHouse, 2025](https://clickhouse.com/blog/cloud-data-warehouses-cost-performance-comparison)).
- **Real-time OLAP for OLTP**: these engines are not for point updates/deletes,
  transactions, or single-row lookups by a service of record.
- **Pre-aggregating for query shapes you do not run**: star-trees and MVs cost
  storage and ingestion CPU; build them for real query shapes only.
- **Over-indexing ClickHouse**: too many data-skipping indexes slow inserts and
  rarely help; they also do not help with negations
  ([oneuptime, 2026](https://oneuptime.com/blog/post/2026-03-31-clickhouse-avoid-over-indexing/view)).
- **Expecting DuckDB to be a streaming/high-concurrency server**: it is
  in-process, single-node, batch/interactive, not a serving engine
  ([Kestra, 2026](https://kestra.io/blogs/embedded-databases)).
- **Many tiny inserts into MergeTree**: floods the engine with small parts; batch
  inserts (or use async inserts) so merges keep up.
- **Treating vendor benchmarks as neutral**: SSB/flat-table benchmarks favor the
  publisher; validate on your own query shapes and data.

## Troubleshooting

- **Slow aggregation / group-by**: confirm pre-aggregation matches the query
  shape (star-tree dims/metrics, MV grouping keys); check vectorized path is used.
- **High latency under concurrency**: check QPS vs node count; add star-tree/MV;
  scale compute (shared-data CNs) horizontally.
- **Stale data**: inspect ingestion lag (Kafka consumer lag, segment commit/
  handoff in Pinot/Druid, publish batching/freshness in StarRocks shared-data).
- **Query scans too much data**: primary/sort key not aligned to the dominant
  filter, or missing data-skipping/bitmap index; reorder sort key.
- **Insert pressure / "too many parts" (ClickHouse)**: inserts too small/frequent;
  batch them; let background merges catch up.
- **Upsert results look wrong**: verify full vs partial upsert semantics and that
  the upsert primary key and partitioning are configured correctly.
- **Costs spiking on object store (shared-data)**: API call volume; enable batch
  publish / caching (StarRocks 4.0 addressed this) and size the local hot cache.

## References

- ClickHouse — How the 5 major cloud data warehouses compare on cost-performance (2025): https://clickhouse.com/blog/cloud-data-warehouses-cost-performance-comparison
- ClickHouse — ClickHouse vs Snowflake for Real-Time Analytics (2025): https://clickhouse.com/blog/clickhouse-vs-snowflake-for-real-time-analytics-comparison-migration-guide
- ClickHouse docs — A practical introduction to primary indexes (sparse index/granules): https://clickhouse.com/docs/guides/best-practices/sparse-primary-indexes
- oneuptime — Data Skipping with Sparse Indexes in ClickHouse (2026): https://oneuptime.com/blog/post/2026-03-31-clickhouse-data-skipping-sparse-indexes/view
- oneuptime — Avoid Over-Indexing in ClickHouse (2026): https://oneuptime.com/blog/post/2026-03-31-clickhouse-avoid-over-indexing/view
- StarTree — Inside the flight path of real-time ingestion in Apache Pinot (2025): https://startree.ai/resources/inside-the-flight-path-of-real-time-ingestion-in-apache-pinot/
- StarTree — A Tale of Three Real-Time OLAP Databases (Pinot/Druid/ClickHouse): https://startree.ai/resources/a-tale-of-three-real-time-olap-databases/
- StarTree — Star-Tree Index Part 2: High Concurrency (2023): https://startree.ai/resources/star-tree-indexes-in-apache-pinot-part-2-understanding-the-impact-during-high-concurrency/
- Apache Pinot docs — Star-Tree Index: https://docs.pinot.apache.org/build-with-pinot/indexing/star-tree-index
- pdpspectra — Apache Pinot Deep Dive 2026: User-Facing Analytics, Upserts (2026): https://pdpspectra.com/blog/apache-pinot-realtime-olap-2026/
- Confluent — Real-Time Analytics with Apache Kafka and Pinot: https://www.confluent.io/blog/real-time-analytics-with-kafka-and-pinot/
- StarRocks — Benchmark: StarRocks vs ClickHouse, Druid, Trino: https://www.starrocks.io/blog/benchmark-test
- StarRocks docs — Query rewrite with materialized views: https://docs.starrocks.io/docs/using_starrocks/async_mv/use_cases/query_rewrite_with_materialized_views/
- StarRocks docs — Architecture (shared-data / compute nodes): https://docs.starrocks.io/docs/introduction/Architecture/
- jusdb — StarRocks Database (2026): Architecture & Real-Time Analytics Guide (2026): https://www.jusdb.com/blog/starrocks-explained-the-complete-guide-to-real-time-analytics
- Apache Doris docs — Overview of Asynchronous Materialized Views: https://doris.apache.org/docs/query-acceleration/materialized-view/async-materialized-view/overview/
- Apache Druid docs — Segments: https://druid.apache.org/docs/latest/design/segments/
- Apache Druid docs — Ingestion: https://druid.apache.org/docs/latest/ingestion/index.html
- SQLFlash — OLAP Database Architecture: Columnar Storage & Vectorized Execution (2025): https://sqlflash.ai/article/20250722_olap-database-architecture/
- InfoQ — Google Spanner Unifies OLTP and OLAP with Columnar Engine (2025): https://www.infoq.com/news/2025/09/google-spanner-oltp-olap-unify/
- bix-tech — Kappa vs. Lambda vs. Batch: https://bix-tech.com/kappa-vs-lambda-vs-batch-choosing-the-right-data-architecture-for-your-business/
- Materialize — When Is Kappa Architecture Most Effective?: https://materialize.com/blog/when-is-kappa-architecture-most-effective/
- makitsol — Real-Time Analytics vs Batch Processing (2025): https://makitsol.com/real-time-analytics-vs-batch-processing-in-us-eu/
- Kestra — Embedded Databases in 2026: DuckDB, SQLite, Polars, chDB (2026): https://kestra.io/blogs/embedded-databases
- Tinybird — OLAP databases: what's new and what's best in 2026 (2026): https://www.tinybird.co/blog/best-database-for-olap
- Estuary — Top 10 Real-Time OLAP Databases in 2026 (2026): https://estuary.dev/blog/real-time-olap-databases/
- pracdata — State of Open Source Real-Time OLAP Systems 2025 (2025): https://www.pracdata.io/p/state-of-open-source-read-time-olap-2025
