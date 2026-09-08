---
title: "Data Acquisition and Sampling"
description: "This skill covers the third stage of the data analysis curriculum: getting data into a form the"
---

# Data Acquisition and Sampling

This skill covers the **third stage** of the data analysis curriculum: getting data into a form the
analysis can operate on, and constructing a sample that supports valid inference about the target
population. The two activities are intertwined: the choice of source constrains what sampling design
is possible, and the sampling plan determines which sources are acceptable.

A common mistake is to treat acquisition as a logistics problem — "just pull the data" — and discover
only at the analysis stage that the population was wrong, the sample frame had coverage gaps, the
schema drifted mid-pull, or the file format made the planned query infeasible. This stage owns the
responsibility for catching these failures *before* they contaminate downstream work.

---

## Sub-skill routing table

This hub absorbs 9 former standalone skills as on-demand reference files. When a task matches a row, **Read the listed `references/` file** before answering — do not rely on this table alone for depth.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `da-3-1-data-sources` | Data sources as a category within data collection & acquisition | `references/da-3-1-data-sources.md` |
| `da-3-1-1-primary-vs-secondary` | Primary vs secondary data sources — provenance, fit, trade-offs | `references/da-3-1-1-primary-vs-secondary.md` |
| `da-3-1-2-internal-vs-external` | The internal-vs-external dimension of data sources | `references/da-3-1-2-internal-vs-external.md` |
| `da-3-1-3-structured-semi-structured-unstructured` | Structured, semi-structured, unstructured data types | `references/da-3-1-3-structured-semi-structured-unstructured.md` |
| `da-3-2-collection-methods` | Overview/comparison of data collection methods | `references/da-3-2-collection-methods.md` |
| `da-3-2-5-web-scraping-crawling` | Web scraping/crawling — tooling, legality, ethics | `references/da-3-2-5-web-scraping-crawling.md` |
| `da-3-2-6-apis-data-feeds` | Collecting data via APIs and structured feeds | `references/da-3-2-6-apis-data-feeds.md` |
| `da-3-2-7-web-app-analytics-instrumentation` | Event instrumentation for web and mobile apps | `references/da-3-2-7-web-app-analytics-instrumentation.md` |
| `da-3-data-collection-acquisition` | Overview/orientation for Data Collection & Acquisition | `references/da-3-data-collection-acquisition.md` |

---

## 1. Data Source Taxonomy

Three orthogonal axes characterize any source.

### 1.1 Primary vs secondary

**Primary data** is collected directly to answer the current question (surveys you designed, interviews, sensor data, A/B exposure logs). **Secondary data** was collected by someone else for a different purpose and is reused (Census/BLS, commercial panels, academic archives, third-party API exports). Strong analyses combine both. The trade-off is purpose-fit (primary) versus speed/scale/cost (secondary).

### 1.2 Structured vs semi-structured vs unstructured

- **Structured**: row/column tabular with fixed schema (relational DBs, warehouses, CSV/Parquet).
- **Semi-structured**: hierarchical/self-describing (JSON, XML, logs, NoSQL docs, Avro/Protobuf).
- **Unstructured**: free-form text, images, audio, video; requires feature extraction (OCR, ASR, embeddings) or a model interface.

Vector embeddings and LLMs reduced the cost of operating on unstructured data, but the closer a source is to structured form, the cheaper and more deterministic the analysis. Schema-on-read (data lakes) defers structure to query time; schema-on-write (warehouses) enforces it at load time.

### 1.3 Internal vs external

Internal sources (production DBs, event logs, CRM, telemetry) are more reliable and granular but may not generalize. External sources (APIs, public datasets, scraped pages, panels) broaden the population but add coverage uncertainty, licensing risk, and schema drift.

---

## 2. API Ingestion

### 2.1 REST, GraphQL, gRPC

- **REST** (HTTP+JSON): broadest compatibility, HTTP caching, OpenAPI contracts. Downside: over/under-fetching.
- **GraphQL**: client asks for exactly the fields it needs; eliminates over/under-fetch. Downside: HTTP caching is harder, rate limiting via query-cost budgets, per-field authorization.
- **gRPC** (HTTP/2 + Protobuf): code-generated clients, multiplexed streaming, 3-10x smaller payloads. Best for internal service-to-service traffic.

Common 2026 pattern: REST public, GraphQL BFF/frontend, gRPC internal. For acquisition you mostly meet REST and GraphQL.

### 2.2 Authentication

- **API key**: shared secret in a header; identifies the app, not a user; TLS only; rotate.
- **OAuth 2.0**: access + refresh tokens. Authorization Code with PKCE for user apps; Client Credentials for service-to-service. Validate scopes server-side.
- **JWT**: signed bearer token; stateless verification; keep short-lived; verify the `alg` header (avoid `alg: none`).
- **mTLS / certificate auth**: high-trust internal/financial/healthcare APIs.

Treat refresh tokens as the most sensitive secret: encrypt at rest, rotate on suspicion, log every refresh.

### 2.3 Pagination

- **Offset/limit** and **page number**: simple but break under concurrent writes.
- **Cursor-based** (opaque token): stable under writes; preferred for high-volume APIs.
- **Keyset/seek** (sort key + tiebreaker): cheap on indexed columns.

Persist the cursor after every page so a partial failure can resume.

### 2.4 Rate limiting

Fixed window, sliding window, token bucket, cost-based (GraphQL). Build clients with exponential backoff on `429`/`503`, respecting `Retry-After`. Cap retries.

### 2.5 Webhooks

Inverse of polling. Always verify the signature header (HMAC-SHA256 over the raw body) before trusting the payload; treat unsigned webhooks as untrusted input.

---

## 3. Web Scraping

Acquisition without a contract. Use only when there is no API and the legal/ethical posture is sound.

### 3.1 Tooling

- **`requests` + BeautifulSoup**: static HTML, no JS.
- **Scrapy**: full crawling framework (concurrency, throttling, retries, pipelines).
- **Playwright / Selenium**: headless browsers for JS-rendered or auth-gated pages; slower.
- **TLS-impersonation tooling** (`curl_cffi`): a signal the site does not want to be scraped.

### 3.2 Legality

As of 2026 the hiQ v. LinkedIn line: scraping publicly accessible data generally does not violate the CFAA. But the full risk surface includes CFAA (bypassing auth/access controls), Terms of Service (civil claims), copyright (bulk reproduction), GDPR/CCPA (personal data, stricter in the EU), and EU database rights.

### 3.3 Ethics

Respect `robots.txt`; set a descriptive `User-Agent` with contact info; throttle (≤1 req/sec for small sites); cache aggressively; avoid PII without a lawful basis; never bypass authentication, paywalls, or rate-limiting controls.

---

## 4. Database Extraction

### 4.1 Bulk export

`SELECT *` into CSV/Parquet/Avro. Simple for cold historical data; anti-pattern for large operational tables. Use native utilities (`mongoexport`, `pg_dump`, `mysqldump --single-transaction`, `bq extract`, Redshift UNLOAD).

### 4.2 Incremental polling (JDBC/ODBC)

Connectors (Kafka Connect JDBC, Airbyte, Fivetran, Meltano) poll on a schedule, identifying changes by `updated_at` or auto-increment `id`. Gaps: hard deletes invisible, backdated updates missed, high-frequency polling stresses the source, schema changes break connectors.

### 4.3 Log-based CDC

Read the transaction log (MySQL binlog, PostgreSQL WAL, MongoDB oplog/change streams, SQL Server CDC). Debezium is the dominant open-source platform. Advantages: captures inserts/updates/**deletes**, every intermediate state, minimal source load, sub-second latency, stable per-row ordering. Typical pipeline: initial snapshot, then stream the log from the snapshot's LSN/position; persist resume tokens/offsets for recovery.

---

## 5. Streaming Ingest

### 5.1 Kafka, Kinesis, Pub/Sub

- **Kafka** (MSK, Confluent, Redpanda): de facto standard, open protocol, strongest ecosystem, highest throughput. Best for multi-cloud and complex stream processing.
- **Kinesis Data Streams**: AWS-native, shard-based; 2026 trend favors MSK for new AWS deployments unless small/serverless.
- **Pub/Sub**: GCP-native, serverless, regional exactly-once (2024).

### 5.2 Exactly-once semantics

At-most-once / at-least-once / exactly-once. Kafka: idempotent producers + transactions API. Kinesis: KCL checkpoints + idempotent downstream. Pub/Sub: regional exactly-once API. Practical guidance: make consumers idempotent, default to at-least-once, invoke exactly-once only when duplicates are costlier than the coordination.

### 5.3 Order, partitioning, back-pressure

Partition key sets parallelism and ordering (same key → same partition → in-order). Hot partitions are the primary failure mode. Handle back-pressure at the consumer: buffer (memory), drop (loss), or pause the source (propagation).

---

## 6. ETL vs ELT and the Modern Data Stack

### 6.1 ETL vs ELT

- **ETL**: transform before load (Informatica, Talend, SSIS, Glue).
- **ELT**: load raw, transform in-warehouse (Snowflake/BigQuery/Redshift/Databricks). Default 2026 pattern; keeps raw history, decouples ingest from transformation.

### 6.2 The modern data stack

- **Ingest/EL**: Fivetran, Airbyte, Meltano (Singer), Stitch.
- **Transform/T**: dbt (needs an orchestrator; doesn't extract/load).
- **Orchestration**: Airflow, Dagster, Prefect, Mage.
- **Warehouse**: Snowflake, BigQuery, Databricks, Redshift, ClickHouse, MotherDuck.
- **Reverse ETL**: Hightouch, Census.
- **Catalog/governance**: DataHub, OpenMetadata, Atlan, Collibra.
- **Observability**: Monte Carlo, Bigeye, Lightup, Soda.

### 6.3 Selection guidance

- Small all-SaaS team: Fivetran + dbt Cloud + Snowflake + Hightouch (watch Fivetran per-MAR pricing).
- Mid-size open-source: Airbyte + dbt Core + Snowflake/BigQuery + Airflow.
- Code-first team: Meltano + dbt Core + Airflow + Snowflake/BigQuery.

---

## 7. Surveys and Primary Collection

### 7.1 Sampling frame

The operational list of population members that can actually be reached — rarely identical to the target population. This gap creates **coverage bias**. Document the frame explicitly at design time; if it doesn't match the population, no sample size or design can fix the resulting bias.

### 7.2 Response bias

Bias is systematic distortion; it does **not** shrink with sample size. Forms: nonresponse, acquiescence (yea-saying), social desirability, recall, order effects, mode effects, selection bias. Mitigations: track response rate, reverse-coded items, anonymous administration, randomize order, demographic benchmarking.

### 7.3 Practical design

Pilot with 10-20 respondents; use vertical scales for mobile; cap length (completion falls past 5-7 min); use attention checks sparingly; pre-register the analysis plan for high-stakes work.

---

## 8. Sampling Methodology

### 8.1 Probability sampling

Every unit has a known, non-zero selection probability — the only basis for valid frequentist inference.

- **SRS**: equal probability `1/N`; the reference design.
- **Stratified**: sample within mutually exclusive strata. Proportional allocation (size-proportional) vs Neyman optimal allocation (size × stdev; minimizes variance for fixed `n`).
- **Cluster**: randomly select clusters, then sample within. Loses precision vs SRS (design effect; effective sample size `n / DEFF`).
- **Systematic**: every `k`th element after a random start; biased if the frame has periodicity matching `k`.

### 8.2 Non-probability sampling

Selection probability unknown or zero; treat as exploratory unless you can model selection.

- **Convenience**: whoever is at hand.
- **Quota**: hit target subgroup counts; biased on non-quota dimensions.
- **Snowball**: respondents refer others; good for hidden populations.
- **Purposive/judgment**: researcher selects informative units; fine for case studies, never for population estimates.

Modern hybrid: **online panel + post-stratification weighting** — weight non-probability panel responses to population marginals. Reduces but does not eliminate selection bias on outcome-correlated dimensions not in the weighting variables.

<!-- cross-hub-map -->
## Cross-hub map — where every data-analytics topic lives

| Hub | Owns |
| --- | --- |
| `da-1-foundations-theory` | Data Analysis Foundations & Theory |
| `da-2-data-analysis-lifecycle` | Data Analysis Lifecycle & Process |
| `da-3-data-acquisition-sampling` | Data Acquisition, Collection & Sampling |
| `da-analytical-methods` | Data Analytical Methods (cleaning, EDA, modeling, ML, causal, time-series) |
| `da-data-engineering-platform` | Data Engineering & Analytics Platform |
| `da-applied-and-communication` | Applied Analytics, Visualization, Communication & Ethics |
