---
title: "Dimensional and Analytics Data Modeling"
description: "The discipline of structuring data for analytics: how to shape facts, dimensions,"
---

# Dimensional & Analytics Data Modeling

The discipline of structuring data for analytics: how to shape facts, dimensions,
and layered models so a warehouse or lakehouse is queryable, consistent, and
maintainable. This skill covers the **modeling** decisions, not the engines or
pipelines that move the data.

**Scope boundaries.** Document/NoSQL schema design → `mongodb-schema-design`.
Ingestion/orchestration/ETL → `da-13-data-engineering-and-pipelines`. Metric &
headless-BI semantic layer → `da-18-semantic-layer-headless-bi`. OLAP engine
internals → `da-28-realtime-olap-databases`. This skill owns the analytical
modeling discipline that those skills sit on top of.

---

## 1. Kimball dimensional modeling — the core

Dimensional modeling organizes data into **fact tables** (numeric measurements of
a business process) and **dimension tables** (the descriptive "who/what/where/
when/why/how" context, wide and denormalized). Instantiated in a relational DB
this is a **star schema**: a central fact table joined to dimensions via
primary/foreign keys.

**Four-step design process** (always in this order):
1. **Select the business process** (e.g. orders, shipments, web sessions) — a
   process produces one or more fact tables, not a department or report.
2. **Declare the grain** — exactly what one fact row represents. This is the
   pivotal step; every candidate dimension and fact must be consistent with it.
   Prefer the lowest (atomic) grain — it is the most flexible and future-proof.
3. **Identify the dimensions** — descriptive context that applies at that grain.
4. **Identify the facts** — numeric measures valid at that grain.

**Star vs snowflake.** A star keeps each dimension as one flat denormalized table.
A **snowflake** normalizes dimension hierarchies into sub-tables (e.g. product →
brand → category). Kimball discourages snowflaking: it saves little storage,
complicates queries, and hurts BI-tool usability. Normalize a dimension only for
genuine outriggers or very large/volatile sub-hierarchies.

**Fact additivity.** Facts are *additive* (summable across all dimensions, e.g.
sales amount), *semi-additive* (summable across some dims but not time, e.g.
account balances, inventory levels — use periodic snapshots), or *non-additive*
(ratios, percentages — store the numerator and denominator as additive facts and
compute the ratio at query time, never store the ratio).

Sources: Kimball Group, [Four-Step Design Process](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/four-4-step-design-process/);
[Grain](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/);
[Star Schema / OLAP Cube](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/star-schema-olap-cube/);
[A Dimensional Modeling Manifesto, 1997](https://www.kimballgroup.com/1997/08/a-dimensional-modeling-manifesto/).

---

## 2. Conformed dimensions & the enterprise data warehouse bus matrix

A **conformed dimension** is shared across multiple fact tables/business processes
with identical keys, attribute names, and meanings (or one is a perfect subset of
the other). Conformed dimensions are what let you **drill across** and integrate
results from different processes (e.g. compare Sales and Returns by the same
Customer and Date dimensions).

The **bus matrix** is the planning artifact: **rows = business processes**,
**columns = dimensions**, shaded cells mark which dims a process uses. Scanning a
column shows where a dimension must be conformed. The matrix is how a team plans
incremental, integrated delivery (deliver one process/data mart at a time, but
plan the shared dimension bus up front so marts integrate later).

Sources: Kimball Group, [Enterprise DW Bus Matrix](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/enterprise-data-warehouse-bus-matrix/);
[Bus Architecture](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/kimball-data-warehouse-bus-architecture/);
[The Matrix: Revisited, 2005](https://www.kimballgroup.com/2005/12/the-matrix-revisited/).

---

## 3. Slowly changing dimensions (SCD)

How to handle dimension attributes that change over time. The three basics are
type 1, 2, 3; the rest are hybrids.

| Type | Technique | History | Use when |
| --- | --- | --- | --- |
| **0** | Retain original — never overwrite | Frozen | "Original" attributes (original credit score, durable IDs) |
| **1** | Overwrite in place | None (destroys history) | Corrections; nobody cares about prior value |
| **2** | Add a new row with a **new surrogate key**, plus row-effective/expiration dates and a current-flag | Full | The default for preserving history; partitions facts by the value in effect at event time |
| **3** | Add an **alternate column** (e.g. `prior_region`) | Limited (one prior value) | Soft, occasional realignments where both views are wanted simultaneously |
| **4** | **Mini-dimension** — split rapidly changing attributes into their own dimension | Full (for volatile attrs) | A large dimension with a few fast-changing attributes |
| **5** | Type 4 mini-dim + a type-1 "current mini-dim" key on the base dimension | Full + current | As-was and as-is via the mini-dim |
| **6** | Type 1 + 2 + 3 combined in one dimension | Full + current-in-row | Single dimension serving both contemporary and current views |
| **7** | **Dual** type-1 and type-2 dimensions on the same fact (join via durable key for current, via surrogate key for historical) | Full + current | Cleanest as-was/as-is without overloading one table |

Type 2 is the workhorse — most "track history" requirements resolve to type 2.

Sources: Kimball Group, [Design Tip #152: SCD Types 0,4,5,6,7, 2013](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/);
[Type 0](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-0/);
[Type 1](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-1/);
[Type 7](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-7/);
[SCD overview, 2008](https://www.kimballgroup.com/2008/08/slowly-changing-dimensions/).

---

## 4. Fact table types

| Type | One row = | Behavior | Example |
| --- | --- | --- | --- |
| **Transaction** | One measurement event at an instant | Insert-only; can be enormous (billions of rows) | A line item, a click, a payment |
| **Periodic snapshot** | A summary of activity over a fixed period | One row per entity per period; holds semi-additive balances | Daily account balance, monthly inventory |
| **Accumulating snapshot** | One row per process instance with milestones | **Row is revisited and updated** as the process advances; multiple date FKs (one per step) | Order fulfillment, claim processing, hiring pipeline |
| **Factless** | An event or a coverage relationship, no numeric measure | Captures M:N between dimension keys; count rows | Student attendance, promotion coverage, eligibility |

The accumulating snapshot is the only type whose rows are routinely **updated**.
Factless tables answer "did it happen / what was eligible" questions. The three
core types complement each other and often coexist for the same process.

Sources: Kimball Group, [Periodic Snapshot](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/periodic-snapshot-fact-table/);
[Accumulating Snapshot](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/);
[Design Tip #133: Factless Fact Tables, 2011](https://www.kimballgroup.com/2011/04/design-tip-133-factless-fact-tables-for-simplification/);
[Design Tip #167: Complementary Fact Table Types, 2014](https://www.kimballgroup.com/2014/06/design-tip-167-complementary-fact-table-types/).

---

## 5. Keys & specialized dimensions

- **Surrogate keys** — meaningless integer (or hash) primary keys on dimensions,
  generated by the warehouse. Required for SCD type 2 (each version gets its own
  key), insulates the warehouse from source-system key changes/reuse, and joins
  faster than wide natural keys. Facts carry surrogate FKs, not business keys.
- **Natural / business keys** — the source-system identifier (e.g. `customer_id`).
  Keep it as a **durable attribute** on the dimension; under type 2 it is *not*
  unique (it repeats across versions). The durable key joins all versions of an
  entity together.
- **Degenerate dimension** — a dimension key with no attributes of its own, stored
  directly on the fact (e.g. order number, invoice number, ticket ID). No separate
  table.
- **Role-playing dimension** — one physical dimension referenced multiple times in
  one fact under different roles (e.g. Date as order_date, ship_date, due_date).
  Expose via views/aliases with role-specific column names.
- **Junk dimension** — a single table collecting low-cardinality flags and
  indicators (yes/no, status codes) that would otherwise clutter the fact, holding
  the distinct combinations actually observed.

Sources: Kimball Group, [Dimensional Modeling Techniques index](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/);
[The 10 Essential Rules of Dimensional Modeling, 2009](https://www.kimballgroup.com/2009/05/the-10-essential-rules-of-dimensional-modeling/);
[Fact Tables and Dimension Tables, 2003](https://www.kimballgroup.com/2003/01/fact-tables-and-dimension-tables/).

---

## 6. Methodology comparison — Inmon vs Kimball vs Data Vault 2.0

| | **Inmon (CIF)** | **Kimball** | **Data Vault 2.0** |
| --- | --- | --- | --- |
| Direction | Top-down | Bottom-up | Hybrid |
| Core store | Normalized **3NF** enterprise warehouse ("single version of truth"); dimensional marts derived *after* | Dimensional **star schemas** organized by business process, integrated via conformed dims/bus | **Hubs / Links / Satellites** raw vault, then a business vault, then dimensional marts for consumption |
| First deliverable | Slow (build the enterprise model first) | Fast (deliver one process/mart, integrate via the bus) | Incremental, highly auditable, parallel-loadable |
| Strength | Enterprise consistency, low redundancy | Query performance, business-friendly, fast time-to-value | Auditability, source-change resilience, agile loads, full history |
| Cost | High up-front design | Conformance discipline required | More tables/joins; needs a presentation layer on top |

**Data Vault 2.0 building blocks** (Dan Linstedt): **Hubs** store unique business
keys; **Links** store the relationships (often M:N) between hubs; **Satellites**
store descriptive attributes and their history, are **append-only** (every change
is preserved, like type-2 history), and hang off hubs or links. DV2.0 adds hash
keys, hash diffs, and load metadata for parallel, scalable, auditable loads. The
raw vault is *not* a query layer — you build dimensional marts on top for users.

A common real-world pattern is **hybrid**: an Inmon/3NF or Data Vault integration
core feeding Kimball star-schema marts for consumption.

Sources: [Keboola — Kimball vs Inmon](https://www.keboola.com/blog/kimball-vs-inmon);
[Scalefree — Data Vault 2.0 Definition](https://www.scalefree.com/consulting/data-vault-2-0/);
[Data Vault modeling — Wikipedia](https://en.wikipedia.org/wiki/Data_vault_modeling);
[WhereScape — What is Data Vault 2.0](https://www.wherescape.com/blog/data-vault-2-0/).

---

## 7. One Big Table (OBT) vs star schema in columnar cloud warehouses

Modern columnar MPP warehouses (BigQuery, Snowflake, Redshift, Databricks SQL)
change the normalization math. Columnar storage with run-length/dictionary
encoding makes repeated dimension values cheap, and join-heavy star queries incur
cross-node shuffles. So a fully denormalized **One Big Table** (facts + all
dimension attributes pre-joined into one wide table) is often *faster* than a star.

- Benchmarks: OBT ~10-45% faster than star across many queries; BigQuery ~49%
  average improvement (parallel engine, fewer shuffles). Snowflake is **mixed** —
  the star sometimes wins on simpler queries, so test on your engine.
- **OBT cost**: heavy redundancy and painful updates — renaming one product means
  rewriting millions of rows, vs a one-row dimension update in a star. SCD history
  is also awkward in an OBT.
- **Recommended hybrid (2024-2026)**: keep a **star schema in the silver layer**
  for integrity, history (SCD), and exploration; **materialize OBT/wide tables in
  the gold layer** to power high-concurrency BI dashboards. dbt makes this a single
  extra model — build the OBT as a `ref()` over your dimensional marts.

Don't reflexively denormalize: a star is still the better default when you need
SCD history, frequent dimension updates, governed conformed dimensions, or
ad-hoc exploration. Reach for OBT for read-heavy, high-concurrency dashboard
serving.

Sources: [Fivetran — Star Schema vs OBT](https://www.fivetran.com/blog/star-schema-vs-obt);
[MotherDuck — Star Schema Guide](https://motherduck.com/learn/star-schema-data-warehouse-guide/);
[CloudQuery — 3NF vs Star Schema](https://www.cloudquery.io/blog/explainer-3nf_vs_star-schema).

---

## 8. Medallion architecture (bronze / silver / gold)

A lakehouse layering pattern that progressively improves data quality:

- **Bronze** — raw landing, source structure "as-is" plus ingest metadata
  (load timestamp, source file, process ID). Append/immutable; no business logic.
- **Silver** — cleansed, conformed, deduplicated, type-cast; matched and merged
  to an "enterprise view" of key business entities ("just-enough" cleaning). This
  is the natural home for normalized/3NF or dimensional integration models.
- **Gold** — business-level aggregates, dimensional marts, and OBT/wide tables
  ready for BI, reporting, and ML features.

It is a **reference architecture, not a mandate** — add or remove layers to fit.
Databricks guidance: don't write to silver directly from ingestion (schema
drift / corrupt records); prefer streaming reads from bronze for append-only
sources; use Unity Catalog with a separate catalog/schema per layer. Medallion
is *orthogonal* to Kimball/Inmon/Data Vault — those describe how you model
*within* a layer (typically silver and gold).

Sources: [Databricks — What is Medallion Architecture](https://www.databricks.com/blog/what-is-medallion-architecture);
[Databricks docs — Medallion lakehouse architecture](https://docs.databricks.com/aws/en/lakehouse/medallion);
[Databricks — Lakehouse Data Modeling: Myths, Truths, Best Practices](https://www.databricks.com/blog/databricks-lakehouse-data-modeling-myths-truths-and-best-practices).

---

## 9. dbt modeling layers & materializations

dbt's recommended **3-layer structure** maps cleanly onto medallion silver/gold:

- **Staging** (`stg_<source>__<entity>`) — one model per source table, **1:1**
  with the source. Rename/recast/clean only; no joins. Materialize as **views**.
  Organize subfolders **by source system**. Define raw inputs as **sources** in
  YAML and reference them with `source()`.
- **Intermediate** (`int_<concept>`) — purpose-built transformation steps that
  combine a handful (~4-6) of staging models. Shift to **business-conformed**
  subfolders by area of concern. Ideal as **ephemeral** (interpolated as CTEs).
- **Marts** (`fct_<process>`, `dim_<entity>`, or plain entity names) — the
  business-defined fact and dimension tables, each at its own grain. Materialize
  as **tables** (or incremental). If a mart pulls together more than ~4-5
  concepts, factor out intermediate models.

**`ref()` and `source()`** build the DAG: models reference each other with
`ref('model_name')` and raw tables with `source('schema','table')`, so dbt infers
lineage and build order. Set defaults per folder in `dbt_project.yml` (e.g.
staging→view, marts→table, separate schemas per layer).

**Five built-in materializations**: `view` (default, logic only, instant/cheap),
`table` (stores data), `incremental` (only transform new/changed rows), `ephemeral`
(no DB object, inlined as a CTE), `materialized_view` (platform-managed refresh of
incremental logic). Choose incremental for large append-mostly facts; views for
staging; tables for marts users hit directly.

Sources: dbt Labs, [How we structure our dbt projects](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
([Staging](https://docs.getdbt.com/best-practices/how-we-structure/2-staging),
[Intermediate](https://docs.getdbt.com/best-practices/how-we-structure/3-intermediate),
[Marts](https://docs.getdbt.com/best-practices/how-we-structure/4-marts));
[Materializations](https://docs.getdbt.com/docs/build/materializations);
[Best practices for materializations](https://docs.getdbt.com/best-practices/materializations/5-best-practices).

---

## 10. Semantic vs physical modeling

- **Physical model** — the actual tables/views in the warehouse: facts, dims, marts,
  OBTs, their grain, keys, types, and materializations. This is everything above.
- **Semantic model** — a metadata layer *on top* of the physical marts that defines
  metrics, dimensions, and join paths once, so every BI tool computes "revenue" or
  "active users" identically (avoids metric drift). In dbt this is the Semantic
  Layer / MetricFlow; semantic marts sit above physical marts.

Keep physical marts clean and conformed; express reusable business metrics in the
semantic layer rather than baking every aggregate into a physical table. **Deep
semantic-layer / headless-BI work belongs to `da-18-semantic-layer-headless-bi`** —
this skill stops at the modeling boundary and the handoff.

Sources: dbt Labs, [Semantic structure / semantic-layer marts](https://docs.getdbt.com/best-practices/how-we-structure/5-semantic-layer-marts);
[MotherDuck — Star Schema Guide](https://motherduck.com/learn/star-schema-data-warehouse-guide/).

---

## Practical patterns

- **Always declare the grain in one sentence before modeling anything.** "One row
  per ___." If you can't, you don't understand the process yet.
- **Model the atomic grain first.** Aggregates are derivable; you can't drill into
  detail you didn't keep.
- **Plan the dimension bus up front, deliver marts incrementally.** Conform Date,
  Customer, Product early — retrofitting conformance is painful.
- **Default dimension change handling = type 2 with surrogate keys**, unless the
  business explicitly only wants the current value (type 1) or "original" (type 0).
- **Store additive components, not ratios.** Compute percentages/averages at query
  time from additive numerator+denominator facts.
- **Hybrid layering**: 3NF/Data-Vault or conformed star in silver for integrity +
  history; OBT/wide tables in gold for dashboard speed.
- **In dbt**: staging=views 1:1 with sources, intermediate=ephemeral, marts=tables;
  one fact/dim concept per mart at its own grain.

## Anti-patterns

- **Mixed grain in one fact table** — the cardinal sin; forces double-counting.
  Split into separate fact tables.
- **Storing non-additive ratios** as facts — they can't be summed correctly.
- **Snowflaking everything** — normalizing dimensions for "cleanliness"; hurts
  usability and performance with negligible storage gain on columnar engines.
- **Smart/natural keys as fact FKs** — couples the warehouse to source key changes
  and breaks SCD type 2. Use surrogate keys.
- **Reflexive OBT everywhere** — denormalizing without considering update cost,
  SCD history, or that Snowflake sometimes favors the star. Benchmark your engine.
- **Writing to silver directly from ingestion** — schema drift and bad records
  leak in; always land in bronze first.
- **Reports as the design driver** — designing the fact table around a specific
  report instead of the physical measurement event; build at the atomic event
  grain and let reports aggregate.
- **Baking every metric into physical tables** — causes metric drift; define
  reusable metrics in the semantic layer.

## Troubleshooting

- **Numbers double-count when joining two facts** → you joined fact-to-fact. Never
  do that; drill across via conformed dimensions and combine aggregated results.
- **Totals wrong after summing a snapshot over time** → the fact is semi-additive
  (balances/levels); don't sum across the time dimension — take a point-in-time or
  average.
- **Dimension table row count exploding** → a fast-changing attribute under type 2;
  split it into a type-4 mini-dimension.
- **Can't reproduce a historical report** → attributes were handled as type 1
  (overwritten). Convert the relevant attributes to type 2.
- **Star query slow / shuffling on columnar DW** → consider a gold-layer OBT/wide
  table for that dashboard; keep the star for exploration.
- **Same metric differs across dashboards** → metric defined per-report in physical
  tables; move it to the semantic layer.
- **dbt build slow / rebuilding huge facts every run** → switch the large fact mart
  from `table` to `incremental`.

## References (selected, with years)

Kimball Group — [Four-Step Design Process](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/four-4-step-design-process/);
[Grain](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/);
[Bus Matrix](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/enterprise-data-warehouse-bus-matrix/);
[SCD Design Tip #152 (2013)](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/);
[Type 7](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-7/);
[Periodic Snapshot](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/periodic-snapshot-fact-table/);
[Accumulating Snapshot](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/);
[Factless Fact Tables, Design Tip #133 (2011)](https://www.kimballgroup.com/2011/04/design-tip-133-factless-fact-tables-for-simplification/);
[10 Essential Rules (2009)](https://www.kimballgroup.com/2009/05/the-10-essential-rules-of-dimensional-modeling/).
dbt Labs — [How we structure our dbt projects](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview);
[Staging](https://docs.getdbt.com/best-practices/how-we-structure/2-staging);
[Intermediate](https://docs.getdbt.com/best-practices/how-we-structure/3-intermediate);
[Marts](https://docs.getdbt.com/best-practices/how-we-structure/4-marts);
[Materializations](https://docs.getdbt.com/docs/build/materializations);
[Semantic-layer marts](https://docs.getdbt.com/best-practices/how-we-structure/5-semantic-layer-marts).
Data Vault — [Scalefree DV2.0 Definition](https://www.scalefree.com/consulting/data-vault-2-0/);
[WhereScape — What is Data Vault 2.0](https://www.wherescape.com/blog/data-vault-2-0/);
[Data Vault modeling, Wikipedia](https://en.wikipedia.org/wiki/Data_vault_modeling).
Inmon vs Kimball — [Keboola (2024)](https://www.keboola.com/blog/kimball-vs-inmon);
[Computer Weekly](https://www.computerweekly.com/tip/Inmon-or-Kimball-Which-approach-is-suitable-for-your-data-warehouse).
Medallion — [Databricks — What is Medallion Architecture](https://www.databricks.com/blog/what-is-medallion-architecture);
[Databricks docs — Medallion](https://docs.databricks.com/aws/en/lakehouse/medallion);
[Databricks — Lakehouse Data Modeling (2024)](https://www.databricks.com/blog/databricks-lakehouse-data-modeling-myths-truths-and-best-practices).
OBT vs Star — [Fivetran — Star Schema vs OBT](https://www.fivetran.com/blog/star-schema-vs-obt);
[MotherDuck — Star Schema Guide](https://motherduck.com/learn/star-schema-data-warehouse-guide/);
[CloudQuery — 3NF vs Star Schema](https://www.cloudquery.io/blog/explainer-3nf_vs_star-schema).
