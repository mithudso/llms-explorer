---
title: "Atlas Diagnostics Expert"
description: "- SKIP (description-overflow seed, Glean 1000-char cap): WiredTiger storage-engine root-cause internals — cache-fill/eviction/checkpoint/MVCC mechanics behind a live perf symptom → mongodb-expert (ref"
---

# Atlas Diagnostics Expert

## Routing detail

- SKIP (description-overflow seed, Glean 1000-char cap): WiredTiger storage-engine root-cause internals — cache-fill/eviction/checkpoint/MVCC mechanics behind a live perf symptom → mongodb-expert (references/mongodb-wiredtiger-internals.md)

## When to use this skill

- Atlas diagnostics and triage workflows
- Internal single-pane triage tooling and adjacent internal support tools
- FTDC, log, metrics, alert, and explain-plan investigation choices
- KB-backed Atlas troubleshooting guidance
- Designing or reviewing new Atlas diagnostic tooling

## When NOT to use this skill

- Data-plane query/index/schema design not live perf troubleshooting — use `mongodb-expert`
- Atlas platform config/architecture (control plane, tiers, networking, security posture) — use `mongodb-atlas-expert`
- Backups, DR, migration, or security architecture — use `mongodb-operations-expert`
- KB article lookup — use `misc-catch-all` (references/mongodb-kb.md)

## Skill guidance

- Prefer documented Atlas diagnostic workflow before improvising.
- Call out what directly documented vs inferred when evidence thin.
- Use `misc-catch-all` (references/mongodb-kb.md) alongside when need article-level troubleshooting playbooks or customer-shareable links.

---

## Sub-skill routing table

Consolidates 8 diagnostics/performance sub-skills as on-demand references — **Read listed `references/…md` file before answering deep questions**.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `atlas-diagnostics-package` | Expert reference for @mdb-tam/atlas-diagnostics package and diagnostic-recommendation engine | `references/atlas-diagnostics-package.md` |
| `mongodb-performance-troubleshooting` | MongoDB performance diagnosis — slow queries, explain plans, high CPU, cache pressure, symptom triage | `references/mongodb-performance-troubleshooting.md` |
| `mongodb-performance-benchmarking` | MongoDB perf benchmarking and load testing — proactive methodology, tool selection (YCSB, load generation) — "how fast does it go" | `references/mongodb-performance-benchmarking.md` |
| `mongodb-performance-regression-testing` | Regression *testing* methodology — deciding, with statistical defensibility, whether a deployment got slower after a version upgrade/schema/config/driver change; baseline capture, change point detection, CI perf-gating, canary/shadow-traffic comparison, MongoDB 7.0→8.0-style upgrade regression detection — "did it get worse, or is that noise" | `references/mongodb-performance-regression-testing.md` |
| `mongodb-stress-and-resilience-testing` | MongoDB breaking-point, soak, and chaos-resilience testing — deliberately pushing past limits to find failure modes, safe non-prod execution — "where does it break" | `references/mongodb-stress-and-resilience-testing.md` |
| `mongodb-monitoring-observability` | Monitoring MongoDB Atlas and self-managed — Atlas metrics, FTDC, Prometheus/Datadog/Grafana integration, alerting | `references/mongodb-monitoring-observability.md` |
| `mongodb-capacity-planning` | MongoDB Atlas capacity planning — working-set sizing, IOPS forecasting, tier right-sizing | `references/mongodb-capacity-planning.md` |
| `mql-perf-harness` | Heuristic, index-aware performance scorer plus 50-query anti-pattern benchmark corpus | `references/mql-perf-harness.md` |

---

## Source map

### Public Atlas docs

- **Atlas metrics:** <https://www.mongodb.com/docs/atlas/review-available-metrics/>
- **Atlas alerts:** <https://www.mongodb.com/docs/atlas/configure-alerts/>
- **Performance Advisor:** <https://www.mongodb.com/docs/atlas/performance-advisor/>

### Knowledge Base references

| Article | Visibility | URL |
|---------|-----------|-----|
| `000019662` — Atlas cluster connections | Public | <https://support.mongodb.com/article/000019662> |
| `000019888` — Replication Oplog alerts and falling off the oplog | Public | <https://support.mongodb.com/article/000019888> |
| `000022299` — Cloud network latency issues in Atlas AWS clusters | Internal | — |
| `000022653` — MongoNetworkError: Client Network Socket Disconnected Before Secure TLS Connection | Public | <https://support.mongodb.com/article/000022653> |
| `000022958` — Atlas Search: Percentage of RAM consumed by vector indexes above 100% | Public | <https://support.mongodb.com/article/000022958> |
| `000023027` — MongoDB Atlas Security Best Practices | Public | <https://support.mongodb.com/article/000023027> |
| `000018973` — How is the MongoDB Atlas Disk Usage monitoring metric calculated? | Public | <https://support.mongodb.com/article/000018973> |

---

## Atlas diagnostics operating model

### Core principle

Move from **curated summary** to **raw evidence**:

1. Start with a fast curated view (an internal single-pane triage tool, Atlas UI summaries, Performance Advisor, alerts, metrics)
2. Gather focused artifacts (logs, FTDC, explain plans, profiler samples)
3. Use specialized internal analyzers when first-pass evidence is insufficient
4. Package findings into repeatable escalation record using Atlas Diagnostic Checklist and Template

### What the internal docs establish directly

- An internal single-pane-of-glass tool is the first stop for Atlas project and cluster triage.
- Atlas UI investigation still required for disk usage, IOPS, node state, query targeting, scan-and-order, oplog window, upgrade/election context.
- Logs and FTDC are core raw artifacts behind deeper troubleshooting.

---

## Diagnostic surfaces

| Surface | Best use | Primary inputs | Primary outputs |
|---------|----------|----------------|-----------------|
| Internal triage tool | Fast Atlas case triage | case/project/cluster context | Project snapshot, cluster snapshot, quick diagnostics, links to logs/FTDC/UI |
| Atlas UI | Validation and operator investigation | project/cluster/node pages | Live metrics, node state, alerts, activity, downloadable artifacts |
| Atlas alerts | Symptom confirmation and notification history | alert config + project/cluster state | Alert conditions, severity, timeline |
| Atlas metrics | Resource and workload diagnosis | cluster/node metric selection, time range | Charts for CPU, memory, cache, storage, IOPS, latency, connections |
| Performance Advisor | Query/index triage | slow query logs, cluster role access | Index suggestions, query targeting, docs scanned/returned, sample query shapes |
| FTDC analyzers | Low-level time-series diagnosis | FTDC bundles/files | Rule hits, time-series views, summaries |
| Log analyzers | Log-centric troubleshooting | mongod/mongos logs | Filtered views, summaries, visualizations, pattern extraction |
| Explain analyzers | Search/vector explain interpretation | explain JSON | Visualizations, bottleneck analysis, markdown reports |

---

## Atlas Diagnostic Checklist

**Purpose:** Structured manual validation before escalation.

**Inputs:** Project ID, node URI, cluster/node pages, logs/FTDC download links, observed symptoms and timestamps

**Outputs:** Escalation-ready summary with cluster size, node status, storage, IOPS, CPU, oplog, query-targeting, restart attempts

**What it checks:**
- Disk usage and write-blocking risk
- Disk IOPS saturation
- Connection pressure
- Whether writes still accepted
- Node down / recovering / upgrade state
- Query targeting and scan-and-order behavior
- Oplog window / fall-off risk
- CPU pressure and OOM indicators

**Thresholds:** Query targeting `>100` red flag; `>1000` urgent. Scan-and-order stay near `0`; `>25` warrants investigation.

**Cautions:** Some node downtime during upgrades expected. Sanitize customer data before sharing log excerpts.

Beyond the checklist and the Atlas UI/metrics/Performance Advisor surfaces above, MongoDB support engineers also use a set of internal-only diagnostic tools (FTDC analyzers, log analyzers, Atlas Search explain-plan tooling, and an internal debugging-tool gateway) — not detailed here since they aren't publicly available.

---

## Atlas metrics quick reference

- **High cache usage** → working set or write pressure
- **High disk latency / queue depth** → storage bottleneck
- **High connections** → tier limits or pooling problem
- **High execution time** → query/index investigation

Atlas alerting RBAC-gated at org/project scope; severity levels: Critical, Error, Warning, Info. Alert state is diagnostic evidence, not just notification plumbing.

Performance Advisor works from slow-query evidence and suggests indexes based on query shape. Index recommendations still need read-vs-write tradeoff review before applying.

---

## KB-guided troubleshooting posture

Use KB for **repeatable symptom-to-playbook mapping**, especially when need customer-safe article or want to confirm known Atlas issue shape. Check visibility before sharing links externally.

Useful KB categories for Atlas diagnostics:
- Connection and TLS issues
- Oplog sizing / falling off the oplog
- Disk-usage interpretation
- Search/vector alert interpretation
- Network latency investigations

---

## Standards for building new Atlas diagnostic tooling

1. Prefer **public Atlas Admin APIs** first; use private/internal only when capability not exposed publicly.
2. Decide consumer model up front: internal UI, CLI/programmatic tool, or agent-facing system. One API shape not fit every consumer.
3. Use supported auth patterns: service accounts / OAuth, Digest for legacy Admin APIs, or approved internal auth flows.
4. Make RBAC explicit — role annotations required, not implied.
5. Add intentional rate limiting for fan-out or expensive diagnostic endpoints.
6. Keep telemetry privacy-safe — avoid logging request/response bodies due to PII risk.
7. Favor versioned and better-governed public APIs when long-term tool stability matters.
8. Treat logs, FTDC, sample queries, and explains as potentially sensitive customer data; minimize storage and exposure.
9. Preserve TS operational pattern: summary surface first, raw artifacts second, specialized analyzers third.

---

## Evidence boundaries

### Directly documented

- Atlas Diagnostic Checklist thresholds and escalation posture
- Atlas metrics / alerts / Performance Advisor high-level behavior
- Internal API/auth/RBAC/privacy constraints (not detailed here)

### Lightly documented or partly inferred

- Internal diagnostic-tool operating detail (not covered here — those tools aren't publicly available)
- Whether a given internal tool is currently recommended, maintained, or only historically available

When extending this context, read tool's current README or operator guide before making prescriptive claims.

<!-- cross-hub-map -->
## Cross-hub map — where every MongoDB topic lives

All MongoDB knowledge split across **four hubs** (plus `misc-catch-all` for KB-article lookups via references/mongodb-kb.md). If task's deep material **not** in this hub's Sub-skill routing table, it is reference file under sibling hub — **activate that hub or Read its `references/<name>.md` directly**.

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `mongodb-expert` | Core data plane + **engine internals**: CRUD/MQL, aggregation, indexes, query performance, schema design, transactions, change streams, time-series, geospatial, views, BSON, error codes, connection strings, driver internals, **WiredTiger cache/eviction/checkpoint internals**, mongosh, database tools, multi-tenancy, sharding, replication, Compass | `references/mongodb-wiredtiger-internals.md`, `mongodb-indexes-deep.md`, `mongodb-sharding.md`, `mongodb-replication.md` |
| `mongodb-atlas-expert` | Atlas **cloud platform**: control plane, Atlas Search, Vector Search, Stream Processing, Charts, Data Federation, App Services, Triggers, Online Archive, Flex, networking, IAM/RBAC, Terraform, AKO | `references/mongodb-atlas-search.md`, `mongodb-atlas-vector-search.md` |
| `atlas-diagnostics-expert` | Live **diagnostics & performance**: FTDC, performance-troubleshooting symptom triage, benchmarking, regression detection/testing methodology, stress/soak/chaos-resilience testing, monitoring/observability, capacity planning | `references/mongodb-performance-troubleshooting.md`, `mongodb-performance-regression-testing.md`, `mongodb-stress-and-resilience-testing.md` |
| `mongodb-operations-expert` | **Ops & data movement**: backup/restore, DR, Ops Manager, upgrades, migration, mongosync, relational migrator, CDC, data lifecycle, security architecture, encryption, compliance, cost, Kafka/Spark connectors | `references/mongosync.md`, `mongodb-backup-restore.md` |

**High-overlap routing notes:**
- Performance **symptom triage** (high CPU, cache pressure, slow queries, latency spikes) starts at `atlas-diagnostics-expert`, but **storage-engine root-cause internals** (WiredTiger cache fill / dirty trigger / eviction threads / reconciliation / checkpoints) owned by `mongodb-expert` — cross-load `mongodb-expert/references/mongodb-wiredtiger-internals.md` (and `mongodb-wiredtiger.md`) for depth.
- Migration symptoms vs migration **execution**: live-cluster diagnosis → `atlas-diagnostics-expert`; migration/mongosync runbook → `mongodb-operations-expert`.
- Atlas Search/Vector **query syntax & index design** → `mongodb-atlas-expert`; slowness *triage* of running search → `atlas-diagnostics-expert`.
- **Host-OS memory tuning** for self-managed `mongod` host (transparent hugepages disable — THP/`defrag=never`, `vm.swappiness=1`, swap sizing, kernel OOM killer and `oom_score_adj`, NUMA placement / interleave for WiredTiger cache, `vm.max_map_count`) lives under the `devops-infra` router's `devops-linux-internals` sub-hub → cross-load `devops-linux-internals/references/linux-memory-numa.md`. This skill owns MongoDB-side cache-pressure *symptom triage*; that reference owns Linux memory/NUMA mechanisms and sysctls beneath it.
