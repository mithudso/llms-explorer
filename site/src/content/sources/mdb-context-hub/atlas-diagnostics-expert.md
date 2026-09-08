---
title: "Atlas Diagnostics Expert"
description: "- SKIP (description-overflow seed, Glean 1000-char cap): WiredTiger storage-engine root-cause internals — cache-fill/eviction/checkpoint/MVCC mechanics behind a live perf symptom → mongodb-expert (ref"
---

# Atlas Diagnostics Expert

## Routing detail

- SKIP (description-overflow seed, Glean 1000-char cap): WiredTiger storage-engine root-cause internals — cache-fill/eviction/checkpoint/MVCC mechanics behind a live perf symptom → mongodb-expert (references/mongodb-wiredtiger-internals.md)

## When to use this skill

- Atlas diagnostics and triage workflows
- ts-diag usage and adjacent internal support tools
- FTDC, log, metrics, alert, and explain-plan investigation choices
- KB-backed Atlas troubleshooting guidance
- Designing or reviewing new Atlas diagnostic tooling

## When NOT to use this skill

- Data-plane query/index/schema design not live perf troubleshooting — use `mongodb-expert`
- Atlas platform config/architecture (control plane, tiers, networking, security posture) — use `mongodb-atlas-expert`
- Backups, DR, migration, or security architecture — use `mongodb-operations-expert`
- KB article lookup — use `misc-catch-all` (references/mongodb-kb.md)
- Cloning/installing/running 10gen repos — use `misc-catch-all` (references/10gen.md)

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

### Internal diagnostic workflow docs

| Doc | URL |
|-----|-----|
| The Atlas Diagnostic Snapshot service | <https://wiki.corp.mongodb.com/spaces/cs/pages/260914369/The+Atlas+Diagnostic+Snapshot+service> |
| TSE Toolbelt | <https://wiki.corp.mongodb.com/spaces/cs/pages/87470010/TSE+Toolbelt> |
| Cloud Support Home | <https://wiki.corp.mongodb.com/spaces/cs/pages/91000982/Cloud+Support+Home> |
| Atlas Diagnostic Checklist and Template | <https://wiki.corp.mongodb.com/spaces/cs/pages/96667896/Atlas+Diagnostic+Checklist+and+Template> |
| MMS API Landscape | <https://wiki.corp.mongodb.com/spaces/MMS/pages/346202846/MMS+API+Landscape> |

### Tool repositories

| Repo | Purpose |
|------|---------|
| [10gen/ts-diag](https://github.com/10gen/ts-diag) | Atlas diagnostic snapshot service and CLI |
| [10gen/alexandria](https://github.com/10gen/alexandria) | FTDC analysis and rules engine |
| [10gen/ts-search-explain-helper](https://github.com/10gen/ts-search-explain-helper) | Search explain-plan visualization and AI analysis |
| [10gen/mongolyser](https://github.com/10gen/mongolyser) | Electron app for MongoDB performance and log analysis |
| [10gen/atlas-tools](https://github.com/10gen/atlas-tools) | Support tooling installed on Atlas nodes |
| [10gen/support-tools](https://github.com/10gen/support-tools) | Umbrella repo for internal TS tooling |
| [10gen/devprod-mcp-router](https://github.com/10gen/devprod-mcp-router) | MCP gateway for internal debugging backends |
| [10gen/ts-ftdc-requestor](https://github.com/10gen/ts-ftdc-requestor) | FTDC retrieval service |

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

1. Start with fastest curated view (`ts-diag`, Atlas UI summaries, Performance Advisor, alerts, metrics)
2. Gather focused artifacts (logs, FTDC, explain plans, profiler samples)
3. Use specialized analyzers (`alexandria`, `t2`, SearchPlanIQ, `mtools`, Mongolyser) when first-pass insufficient
4. Package findings into repeatable escalation record using Atlas Diagnostic Checklist and Template

### What the internal docs establish directly

- `ts-diag` is **single-pane-of-glass first stop** for Atlas project and cluster triage.
- Atlas UI investigation still required for disk usage, IOPS, node state, query targeting, scan-and-order, oplog window, upgrade/election context.
- Logs and FTDC are core raw artifacts behind deeper troubleshooting.

---

## Diagnostic surfaces

| Surface | Best use | Primary inputs | Primary outputs |
|---------|----------|----------------|-----------------|
| ts-diag web | Fast Atlas case triage | case/project/cluster context | Project snapshot, cluster snapshot, quick diagnostics, links to logs/FTDC/UI |
| ts-diag CLI | Atlas API-backed project/cluster inspection from terminal | case/profile, project/org/cluster identifiers | Text/JSON/markdown output |
| Atlas UI | Validation and operator investigation | project/cluster/node pages | Live metrics, node state, alerts, activity, downloadable artifacts |
| Atlas alerts | Symptom confirmation and notification history | alert config + project/cluster state | Alert conditions, severity, timeline |
| Atlas metrics | Resource and workload diagnosis | cluster/node metric selection, time range | Charts for CPU, memory, cache, storage, IOPS, latency, connections |
| Performance Advisor | Query/index triage | slow query logs, cluster role access | Index suggestions, query targeting, docs scanned/returned, sample query shapes |
| FTDC analyzers | Low-level time-series diagnosis | FTDC bundles/files | Rule hits, time-series views, summaries |
| Log analyzers | Log-centric troubleshooting | mongod/mongos logs | Filtered views, summaries, visualizations, pattern extraction |
| Explain analyzers | Search/vector explain interpretation | explain JSON | Visualizations, bottleneck analysis, markdown reports |

---

## Tool catalog

### ts-diag

**Purpose:** Internal Atlas Diagnostic Snapshot service for Atlas project and cluster triage. Presents curated project/cluster summaries and Quick and Easy Diagnostics.

**Access/install/run:**
- Web: <https://ts-diag.cloud-ops.prod.corp.mongodb.com/> or `go/tsdiag`
- CLI: `ts-diag` (requires Atlas CLI profiles and employee Okta auth; VPN / Cloudflare WARP for CLI auth)
- Dev: Go `1.24.2+` and `GOPRIVATE=github.com/10gen/*`

**CLI subcommands:** `snapshot`, `api`, `atlasinfo`, `dbaccess`, `downloadlogs`, `event`, `instancehardware`, `lastping`, `logcollection`, `maint`, `metrics`, `networkinfo`, `plans`, `searchnodes`, `web`, `whoami`

**Inputs:** Atlas case number, Atlas CLI profile, org/project/cluster identifiers, Atlas Admin API paths

**Outputs:** Project snapshot, cluster snapshot, quick diagnostics, links to logs/FTDC/Atlas UI

**Cautions:**
- Quick diagnostics are triage accelerator, not replacement for logs, FTDC, or Atlas UI validation
- Access is RBAC-gated internally

### Atlas UI + Atlas Diagnostic Checklist

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

### Alexandria

**Purpose:** Fast FTDC analysis on Prometheus-style query model; known-issue detection via rules plus ad hoc FTDC querying.

**Install/run:**
- GitHub releases for binaries, or Kanopy-hosted web app
- Build: `go build ./...` or `make`
- CLI: `alexandria diagnostic.data/*` or `alexandria -query '...' diagnostic.data/*`

**Inputs:** FTDC directories, FTDC tar archives, Prometheus-like query expressions, optional tags/rules

**Outputs:** Markdown findings, JSON output, CSV-style query output, rule hits and summaries

**What it checks:** Memory issues, storage/disk bottlenecks, replication lag/flow control/majority issues, network stall patterns, stuck transactions, WiredTiger contention/dirty rollback patterns

**Cautions:** Some rules are MongoDB-version-specific and pass if metrics absent. Strongest for FTDC-driven diagnosis.

### t2

**Purpose:** FTDC and metric time-series inspection at lower level than first-pass summary tools.

**Access:** Desktop application from GitHub (TSE Toolbelt)

**What it checks:** Trending and timing relationships in FTDC data; follow-up after ts-diag or checklist-based suspicion

**Evidence note:** Corpus docs light — use as specialized FTDC lens.

### mtools

**Purpose:** Log analysis and local repro helpers.

**Install:** `pip3 install --user 'mtools[all]'`; workaround: `pip install mtools[all] --user --ignore-installed six`

**Inputs:** `mongod` / `mongos` logs, local repro scenarios for `mlaunch`

**Outputs:** Log summaries, filtered log views, query plots and log visualizations

### SearchPlanIQ (ts-search-explain-helper)

**Purpose:** Atlas Search and Vector Search explain-plan analysis with visualization and AI-assisted interpretation.

**Install/run:**
- `uv pip install -e .`
- `uv run python -m searchplaniq.app`
- Open `http://localhost:5001`

**Inputs:** `$search`, `$vectorSearch`, and hybrid explain plans

**Outputs:** Flame graphs, treemaps, Sankey diagrams, execution summaries, markdown reports, extracted JSON

**What it checks:** Search-stage bottlenecks, segment timing and selectivity, explain-plan shape and probable hot spots

**Cautions:** Includes LLM-assisted analysis — validate hypotheses against underlying explain data. README calls out security and PII handling guidance as required reading.

### Mongolyser

**Purpose:** General MongoDB performance and health analysis desktop app.

**Install/run:** Download executables from GitHub releases, or `npm i && npm run electron:start`

**Inputs:** Profiler data, logs, oplog/write-load patterns, index and sharding state

**What it checks:** Query profiling, performance assessment, log analysis, query pattern analysis, write-load/oplog behavior, connection analysis, index analysis, sharding and chunk analysis, cache visualization

**Evidence note:** README-level docs — prefer more specialized tools when narrower workflow already established.

### ts-ftdc-requestor

**Purpose:** FTDC retrieval and storage service for Atlas-to-S3 workflows. Primarily artifact-acquisition, not analyzer.

**Evidence note:** Lightly documented — treat as infrastructure around FTDC workflows.

### devprod-mcp-router

**Purpose:** Unified MCP gateway/entrypoint to internal debugging backends (Evergreen, Git, Jira, Confluence, Backstage, Build Baron).

**Install/run:** Install `devprod-mcp-proxy` from gateway download page or via `go install`; connect AI clients over stdio to gateway URL

**Note:** Not Atlas diagnostic engine — makes adjacent CI, repo, wiki, and infra debugging surfaces easier from AI tooling.

---

## Recommended workflow by symptom class

### Cluster health / outage / node-down

1. Start in `ts-diag` for project and cluster snapshot.
2. Validate node state, activity feed, and metrics in Atlas UI.
3. Use Atlas Diagnostic Checklist to confirm storage, IOPS, oplog, CPU, and whether writes still accepted.
4. Pull logs and FTDC if symptom not immediately explained.
5. Escalate with checklist/template if HELP engagement criteria met.

### Query / index / slow-operation issues

1. Start with Performance Advisor and Namespace / profiler views.
2. Check query targeting, docs scanned, docs returned, sample query shapes.
3. For Atlas Search / Vector Search explains, use SearchPlanIQ.
4. Use KB references for recurrent patterns and customer-shareable guidance.

### Memory / storage / cache / replication issues

1. Review Atlas metrics for memory, cache, disk usage, latency, and queue depth.
2. Use `ts-diag` QED output as hinting layer.
3. Pull FTDC and analyze with Alexandria and/or t2.
4. Use oplog and storage KB articles when symptoms match those playbooks.

### Log-heavy incidents

1. Acquire logs from Atlas / ts-diag.
2. Use `mtools` for structured filtering and visualization.
3. Use Mongolyser when broader multi-signal interactive workflow helpful.

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

- `ts-diag` purpose, access paths, and CLI/API orientation
- Atlas Diagnostic Checklist thresholds and escalation posture
- Alexandria FTDC workflow and rule-driven analysis
- `mtools` install guidance
- SearchPlanIQ startup flow and explain-analysis focus
- Mongolyser feature list and Electron startup flow
- Atlas metrics / alerts / Performance Advisor high-level behavior
- Internal API/auth/RBAC/privacy constraints from MMS API Landscape

### Lightly documented or partly inferred

- Exact `t2` operating details
- `atlas-tools` script-by-script behavior
- `ts-ftdc-requestor` runtime usage details
- Whether given internal tool currently recommended, maintained, or only historically available

When extending this context, read tool's current README or operator guide before making prescriptive claims.

<!-- cross-hub-map -->
## Cross-hub map — where every MongoDB topic lives

All MongoDB knowledge split across **four hubs** (plus `misc-catch-all` for KB-article lookups via references/mongodb-kb.md and repo install/run via references/10gen.md). If task's deep material **not** in this hub's Sub-skill routing table, it is reference file under sibling hub — **activate that hub or Read its `references/<name>.md` directly**.

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `mongodb-expert` | Core data plane + **engine internals**: CRUD/MQL, aggregation, indexes, query performance, schema design, transactions, change streams, time-series, geospatial, views, BSON, error codes, connection strings, driver internals, **WiredTiger cache/eviction/checkpoint internals**, mongosh, database tools, multi-tenancy, sharding, replication, Compass | `references/mongodb-wiredtiger-internals.md`, `mongodb-indexes-deep.md`, `mongodb-sharding.md`, `mongodb-replication.md` |
| `mongodb-atlas-expert` | Atlas **cloud platform**: control plane, Atlas Search, Vector Search, Stream Processing, Charts, Data Federation, App Services, Triggers, Online Archive, Flex, networking, IAM/RBAC, Terraform, AKO | `references/mongodb-atlas-search.md`, `mongodb-atlas-vector-search.md` |
| `atlas-diagnostics-expert` | Live **diagnostics & performance**: ts-diag, FTDC, performance-troubleshooting symptom triage, benchmarking, regression detection/testing methodology, stress/soak/chaos-resilience testing, monitoring/observability, capacity planning | `references/mongodb-performance-troubleshooting.md`, `mongodb-performance-regression-testing.md`, `mongodb-stress-and-resilience-testing.md` |
| `mongodb-operations-expert` | **Ops & data movement**: backup/restore, DR, Ops Manager, upgrades, migration, mongosync, relational migrator, CDC, data lifecycle, security architecture, encryption, compliance, cost, Kafka/Spark connectors | `references/mongosync.md`, `mongodb-backup-restore.md` |

**High-overlap routing notes:**
- Performance **symptom triage** (high CPU, cache pressure, slow queries, latency spikes) starts at `atlas-diagnostics-expert`, but **storage-engine root-cause internals** (WiredTiger cache fill / dirty trigger / eviction threads / reconciliation / checkpoints) owned by `mongodb-expert` — cross-load `mongodb-expert/references/mongodb-wiredtiger-internals.md` (and `mongodb-wiredtiger.md`) for depth.
- Migration symptoms vs migration **execution**: live-cluster diagnosis → `atlas-diagnostics-expert`; migration/mongosync runbook → `mongodb-operations-expert`.
- Atlas Search/Vector **query syntax & index design** → `mongodb-atlas-expert`; slowness *triage* of running search → `atlas-diagnostics-expert`.
- **Host-OS memory tuning** for self-managed `mongod` host (transparent hugepages disable — THP/`defrag=never`, `vm.swappiness=1`, swap sizing, kernel OOM killer and `oom_score_adj`, NUMA placement / interleave for WiredTiger cache, `vm.max_map_count`) lives under the `devops-infra` router's `devops-linux-internals` sub-hub → cross-load `devops-linux-internals/references/linux-memory-numa.md`. This skill owns MongoDB-side cache-pressure *symptom triage*; that reference owns Linux memory/NUMA mechanisms and sysctls beneath it.
