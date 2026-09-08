---
title: "Atlas Maintenance Windows"
description: "Comprehensive reference for monitoring MongoDB deployments — from Atlas built-in dashboards through third-party integrations, CLI tools, and low-level FTDC diagnostics."
---

# MongoDB Monitoring and Observability

Comprehensive reference for monitoring MongoDB deployments — from Atlas built-in dashboards through third-party integrations, CLI tools, and low-level FTDC diagnostics.

**When to use this skill:** When answering questions about Atlas metrics, alert configuration, third-party monitoring integrations (Datadog, New Relic, Prometheus), FTDC diagnostics, slow query analysis, replication lag, connection pool behavior, or Atlas maintenance windows and planned operations.

**When not to use:** For Atlas Search index tuning (use `mongodb-search-ai`), Atlas cost optimization (use `mongodb-cost-optimization`), or backup/restore planning (use `mongodb-backup-restore`).

**Required roles for most monitoring operations:** `clusterMonitor` role on the `admin` database (self-managed), or Atlas `Project Read Only` / `Project Data Access Read Only` (Atlas UI). Third-party integrations (Datadog, Prometheus, New Relic) require Atlas `Project Owner` or `Organization Owner` to configure.

**Jump to:** [Quick Reference Tool Matrix](#quick-reference-tool-selection-matrix)

---

## 1. Atlas Cloud Monitoring — Built-in Metrics and Dashboard Customization

Atlas provides real-time and historical metrics for every cluster tier M10 and above. Free/shared-tier clusters have reduced metric granularity (5-minute resolution vs. 1-minute for dedicated tiers).

### Key metric categories available in Atlas UI

- **Opcounters** — insert, query, update, delete, getmore, command rates (ops/sec)
- **CPU / System** — process CPU, system CPU, I/O wait broken by read/write
- **Memory** — resident, virtual, mapped, cache (WiredTiger block cache, dirty bytes)
- **Disk I/O** — IOPS read/write, I/O utilization, disk queue depth
- **Network** — bytes in/out, number of requests
- **Connections** — current, available, total created
- **Replication** — oplog window hours, replication headroom, replication lag per secondary
- **Query targeting** — scanned/returned ratio (key indicator of missing indexes)
- **Tickets** — WiredTiger concurrent read/write tickets in use vs. available

### Dashboard customization

Atlas dashboards are pre-built per cluster but allow:
- Pin metric charts to a custom "Metrics" view for side-by-side comparison across nodes
- Toggle between individual node view (per-host) and cluster aggregate view
- Adjust time range (1h, 8h, 24h, 48h, 1w, custom)
- Use the **Real-Time Performance Panel** (RTPP) for 1-second granularity on live traffic — available on M10+ in the Atlas UI under the cluster's **Real Time** tab

The RTPP shows: opcounters, read/write tickets, connections, network, logical size, and an interactive `currentOp` view showing the slowest in-flight operations per namespace.

---

## 2. Ops Manager and Cloud Manager — Self-Managed Deployments

> **Deep reference:** see `mongodb-ops-manager` for full coverage of App DB sizing/HA, Backup Daemon placement, automation goal-state, air-gap/Local Mode, Kubernetes Operator, federation, and Live Migration to Atlas. This section covers the monitoring agent surface only.

**MongoDB Ops Manager** is the on-premises deployment of MongoDB's management platform for teams running MongoDB in their own data centers or private clouds. **MongoDB Cloud Manager** is the hosted SaaS version of the same platform — it provides identical monitoring, automation, and backup capabilities without requiring you to host the Ops Manager application yourself. Both share the same agent architecture described below.

### Core agents

| Agent | Role |
|---|---|
| **Automation Agent** | Deploys, configures, upgrades, and scales MongoDB processes via Ops Manager directives |
| **Monitoring Agent** | Collects real-time metrics from every managed `mongod`/`mongos`, ships to Ops Manager every 10 seconds |
| **Backup Agent** | Coordinates snapshot-based and oplog-based continuous backup |

### Monitoring agent behavior

- Runs as a daemon alongside your MongoDB processes
- Polls `serverStatus`, `replSetGetStatus`, `dbStats`, `collStats`, `currentOp` (filtered) at configurable intervals
- Stores time-series data in Ops Manager's own MongoDB backing store (separate from your application data)
- Sends alerts through Ops Manager's alert notification system — same alert types as Atlas

### Ops Manager / Cloud Manager dashboards

Both platforms replicate Atlas-style metric dashboards inside the web UI. The topology view shows replica set health, node states (PRIMARY/SECONDARY/ARBITER), and replication lag per member. The **Hardware** tab surfaces CPU, disk IOPS, and memory at host level for correlation with MongoDB behavior.

---

## 3. Atlas Alerts — Types, Channels, and Tuning

### Alert scope levels

- **Project-level alerts** — apply to all clusters in a project (e.g., CPU > 80% on any node)
- **Cluster-level alerts** — scoped to a specific cluster
- **Billing alerts** — monthly spend thresholds, data transfer thresholds

### Alert condition categories

| Category | Examples |
|---|---|
| Host / Node | CPU %, memory %, disk utilization %, disk IOPS |
| Replication | Replication lag > N seconds, oplog window < N hours |
| Connections | Connections > N (absolute or % of max) |
| Query performance | Slow queries, query targeting ratio |
| Indexes | Index build failures |
| Backup | Last successful snapshot age, restore failures |
| Atlas Search | Search index build failures |
| Billing | Monthly spend threshold, data transfer threshold exceeded |

### Notification channels

| Channel | Configuration |
|---|---|
| **Email** | One or more email addresses; configurable delay before sending |
| **Slack** | OAuth or webhook URL; route to specific channels |
| **PagerDuty** | PagerDuty integration key; supports routing rules/escalation policies |
| **Webhook** | HTTP POST to any endpoint; payload is JSON with alert details |
| **Datadog** | Forwards Atlas alert events as Datadog events alongside metrics |
| **OpsGenie** | OpsGenie API key |
| **VictorOps (Splunk On-Call)** | Routing key |
| **SMS / Phone** (via Twilio-backed Atlas feature) | Limited to some plan tiers |

### Alert tuning best practices

- **Set delay intervals** (e.g., "notify if condition persists for 5 minutes") to suppress transient spikes — CPU can spike briefly during flushes without being actionable
- **CPU alert baseline**: M10–M30 should alert at 75%; M50+ with sustained IOPS-heavy workloads often benefit from 85% thresholds with short delay
- **Replication lag**: alert at 10–15 seconds for most OLTP workloads; 60 seconds for batch-heavy pipelines
- **Oplog window**: never let it drop below 4 hours; alert at 48 hours to give time to investigate before backup windows are at risk
- **Connection count**: alert at 80% of the cluster's `maxIncomingConnections`; calculate max from `db.adminCommand({getCmdLineOpts:1})` or Atlas connection string parameters

---

## 4. Custom Metrics

### Atlas Custom Metrics

Atlas supports custom metric alerts via the **Atlas Administration API** (`/api/atlas/v2/groups/{groupId}/alertConfigs`). The `metricName` field accepts any metric Atlas exposes — including metrics not shown by default in the UI. Full metric name catalog: `https://www.mongodb.com/docs/atlas/reference/alert-conditions/`

### $currentOp polling for application-level insight

For application-level custom metrics, poll `$currentOp` on a schedule. Note: run this query from an admin-context connection — the `$all` field was deprecated in MongoDB 4.0 and removed in favor of the admin-context `currentOp` command directly:

```javascript
// Poll every 30 seconds via a dedicated monitoring connection (admin auth required)
const ops = await db.admin().command({ currentOp: 1 });

const slowOps = ops.inprog.filter(op =>
  op.secs_running > 1 &&
  op.ns &&
  !op.ns.startsWith('local.') &&
  !op.ns.startsWith('admin.')
);

slowOps.forEach(op => {
  metrics.gauge('mongodb.slow_op.seconds', op.secs_running, {
    ns: op.ns, op: op.op, plan: op.planSummary
  });
});
```

Key fields: `secs_running`, `op`, `ns`, `planSummary`, `waitingForLock`, `msg`, `locks`.

### Application-level metrics to track

- Query latency percentiles (p50, p95, p99) per collection
- Error rates by MongoDB error code
- Connection pool `waitQueueSize` — rising queue = pool exhaustion signal
- Retry attempt counts — spike in retries indicates transient elections or network partitions

---

## 5. Datadog Integration

### Setup

Atlas Datadog integration requires M10+ clusters and a Datadog API key. Configure via Atlas UI: **Project → Integrations → Datadog**. Select region (`US1`, `US3`, `US5`, `EU1`, `AP1`, `US1_FED`) to match your Datadog account region.

### Key metrics shipped to Datadog

| Metric | Description |
|---|---|
| `mongodb.atlas.connections.current` | Active connections |
| `mongodb.atlas.system.cpu.norm.guest` | Normalized CPU |
| `mongodb.atlas.cache.usage.dirty` | WiredTiger dirty cache bytes |
| `mongodb.atlas.repl.headroom` | Replication headroom (oplog - lag) |
| `mongodb.atlas.query.targeting.scannedObjectsPerReturned` | Scan ratio |

### Datadog Database Monitoring (DBM) for Atlas

Separate from the metrics integration — requires Datadog Agent with MongoDB integration. Provides query-level explain plan capture, wait event analysis, query normalization and fingerprinting. Configure via `conf.d/mongo.d/conf.yaml` with a `clusterMonitor` role user.

---

## 6. New Relic Integration

Configure via Atlas UI: **Project → Integrations → New Relic**. Metrics ship under `MongoDBAtlas.*` namespace. Primary value: **APM-to-database correlation** — New Relic links slow transaction traces in application code directly to slow MongoDB operations when using the New Relic APM agent.

For self-managed MongoDB, use `nri-mongodb` with the New Relic Infrastructure agent (`EXTENDED_METRICS: true`, `COLLECTION_METRICS: true`).

---

## 7. Prometheus Integration

### Atlas managed endpoint (M10+ only)

Enable via Atlas UI: **Project → Integrations → Prometheus**. Scrape URL: `https://cloud.mongodb.com/prometheus/v1.0/groups/{groupId}/metrics`. Auth: HTTP Basic with Atlas programmatic API key pair.

```yaml
scrape_configs:
  - job_name: 'mongodb-atlas'
    scrape_interval: 60s
    scrape_timeout: 55s
    scheme: https
    basic_auth:
      username: '<atlas_public_api_key>'
      password: '<atlas_private_api_key>'
    static_configs:
      - targets: ['cloud.mongodb.com']
    metrics_path: '/prometheus/v1.0/groups/<groupId>/metrics'
```

### Self-managed Prometheus

Use `mongodb_exporter` (Percona) on port 9216. Search "MongoDB Overview Percona" in the Grafana dashboard library for a production-ready starting point.

---

## 8. FTDC (Full Time Diagnostic Capture)

FTDC is MongoDB's always-on internal diagnostic system (enabled by default since MongoDB 3.2). It is the first artifact MongoDB Support requests for any performance investigation.

**Samples every second:** full `serverStatus`, `replSetGetStatus`, oplog metadata, system CPU/memory, WiredTiger internal stats.
**Samples every 200ms:** lighter CPU/I/O subset for sub-second spike reconstruction.

**Location:** `<dbPath>/diagnostic.data/` — files rotate at ~10 MB. Atlas retains FTDC automatically; for self-managed, copy the entire directory while `mongod` is live (safe — FTDC uses its own write path).

### Analysis tools

| Tool | Usage |
|---|---|
| **Keyhole** | `keyhole --ftdc diagnostic.data/` — human-readable reports + Grafana output |
| **mongodb/ftdc Go library** | Low-level BSON parsing |
| **mtools `mloginfo`** | Correlates mongod logs with FTDC |

### FTDC diagnostic questions

- Checkpoint stall? → WiredTiger checkpoint duration spike
- CPU saturated? → system CPU counters at 100%
- Connection spike before incident? → `connections.current` time series
- Replication lag gradual or sudden? → `replSetGetStatus.members[].optimeDate` delta
- Cache eviction pressure? → cache dirty % over time

---

## 9. mongotop / mongostat / db.currentOp

### mongostat

```bash
mongostat --uri "mongodb+srv://user:pass@cluster.mongodb.net" --discover --rowcount 60
```

Key columns: `insert/query/update/delete` (ops/sec), `dirty` (WT dirty cache %), `used` (WT cache %), `qrw/arw` (queue/active read-write), `conn`, `repl`.

**When to use:** quick snapshot of server load; real-time cache utilization; spotting queue buildup.

### mongotop

```bash
mongotop --uri "mongodb+srv://user:pass@cluster.mongodb.net" 5
```

Shows per-collection `total`/`read`/`write` ms per interval. **When to use:** identify hottest collection during a performance issue.

### db.currentOp()

```javascript
db.adminCommand({ currentOp: true, active: true, secs_running: { $gt: 2 }, ns: { $not: /^local\./ } })
db.adminCommand({ killOp: 1, op: <opid> })
```

**When to use:** real-time slow op investigation; finding lock waiters (`waitingForLock: true`).

---

## 10. Slow Query Monitoring

### Atlas Profiler and Performance Advisor

- **Cluster → Profiler** tab: near-real-time slow queries (~2 min pipeline latency)
- **Cluster → Performance Advisor**: automatic index recommendations ranked by avg execution time × frequency
- Default slow threshold: **100ms** (configurable to 0ms)

### system.profile

```javascript
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find({ millis: { $gt: 500 } }).sort({ ts: -1 }).limit(20)
```

Key fields: `millis`, `planSummary` (IXSCAN vs COLLSCAN), `keysExamined`, `docsExamined`, `queryHash`. **Caution:** profiling level 2 has measurable overhead — use level 1 with tuned `slowms` in production.

### Threshold guidance

| Workload | Recommended threshold |
|---|---|
| OLTP (< 10ms target) | 20–50ms |
| Mixed OLTP/analytics | 100ms (default) |
| Analytics-heavy | 200–500ms |
| Bulk load / maintenance | 1000ms |

---

## 11. Replication Lag Monitoring

```javascript
rs.printSecondaryReplicationInfo()

// Programmatic — use optimeDate (JS Date), NOT optime.ts (BSON Timestamp)
const status = db.adminCommand({ replSetGetStatus: 1 })
const primary = status.members.find(m => m.stateStr === 'PRIMARY')
status.members.filter(m => m.stateStr === 'SECONDARY').forEach(sec => {
  console.log(`${sec.name}: lag ${primary.optimeDate.getTime() - sec.optimeDate.getTime()}ms`)
})
```

### Root causes

1. Secondary under-resourced (upgrade tier or distribute reads)
2. Flow control (MongoDB 4.2+) — check `replSetGetStatus.flowControl.isLagged`
3. Chained replication — check `rs.status().syncSourceHost`
4. Long-running transactions on secondary
5. Network partition/bandwidth saturation

### Lag alert thresholds

| Deployment type | Warning | Critical |
|---|---|---|
| OLTP, strict secondary reads | 5s | 15s |
| General purpose | 15s | 60s |
| Analytics/reporting secondaries | 60s | 300s |

---

## 12. Connection Metrics

### Key counters

```javascript
const ss = db.adminCommand({ serverStatus: 1 })
ss.connections.current       // active now
ss.connections.available     // remaining capacity
ss.connections.totalCreated  // monotonic cumulative
ss.wiredTiger.concurrentTransactions.read.out   // active read tickets
ss.wiredTiger.concurrentTransactions.write.out  // active write tickets
```

### Pool exhaustion signals

| Signal | What to look for |
|---|---|
| `connections.available` → 0 | Imminent refusal |
| `totalCreated` rate high | Pool churn |
| Driver `waitQueueSize` rising | Application waiting for slot |
| `ServerSelectionTimeoutError` | Pool exhausted before timeout |
| `Too many open files` | ulimit -n hit |

### Atlas connection limits by tier

| Tier | Max connections |
|---|---|
| M10 | 1,500 |
| M20/M30 | 3,000 |
| M40 | 6,000 |
| M50 | 16,000 |
| M60 | 32,000 |
| M80 | 64,000 |
| M200+ | 128,000 |

Connections are per-node. A 3-node M30 replica set has 9,000 total across all nodes.

### Tuning recommendations

- Single `MongoClient` per process (most common leak: new client per request)
- Lambda/serverless: `maxPoolSize=5–10`, `maxIdleTimeMS=60000`
- Enable `waitQueueTimeoutMS` to surface exhaustion quickly rather than hanging

---

## Quick Reference: Tool Selection Matrix

| Question | Tool |
|---|---|
| What is the server doing right now? | `mongostat` + Atlas RTPP |
| Which collection is hottest? | `mongotop` |
| What specific operation is slow right now? | `db.currentOp()` |
| What slow queries ran in the past hour? | Atlas Profiler / `system.profile` |
| Why was the server slow at 2am? | FTDC + Keyhole |
| Is replication healthy? | `rs.printSecondaryReplicationInfo()` |
| Are connections running out? | `serverStatus.connections` + Atlas alerts |
| Correlate MongoDB to app performance? | Datadog DBM or New Relic APM |
| Long-term trending (weeks/months)? | Prometheus + Grafana or Datadog dashboards |
| Billing and cluster-level spend? | Atlas billing alerts |
| Atlas Search index health? | Atlas UI → Search tab → Index Metrics |
| Self-managed cluster automation + monitoring? | Ops Manager or Cloud Manager |
| When is maintenance scheduled / what window is configured? | `atlas maintenanceWindows describe` / Atlas UI Project Settings → §13 |
| How do I defer upcoming maintenance? | Atlas UI Defer button or `atlas maintenanceWindows defer` → §13 |

---

## 13. Atlas Maintenance Windows and Planned Operations

### Free and shared tier clusters (M0, M2, M5)

**M0, M2, and M5 clusters do not support configurable maintenance windows.** Atlas manages all maintenance entirely, with no operator control over timing. These clusters may be restarted at any time. Upgrade to M10 or higher for maintenance window control.

This is a common point of confusion — the project-level maintenance window setting applies only to dedicated-tier clusters (M10+).

### Maintenance window configuration

Atlas maintenance windows are configured at the **project level** and apply to all dedicated-tier (M10+) clusters within that project.

**Location:** Atlas UI → **Project Settings** → **Maintenance Window**

**Default behavior:** When no custom window is configured, Atlas selects the window (commonly Tuesday 10:00–12:00 UTC for many regions). Configure an explicit window aligned with your lowest-traffic period for production workloads.

**Configuring a custom window:**
- Choose day of week (Sunday through Saturday; Sunday=1 in the API/CLI, matching the integer table below)
- Choose start hour in UTC (0–23); the window is exactly 1 hour
- Changes take effect immediately and persist until cleared

**Important scope limitation:** Project-scoped, not per-cluster. To set different windows for dev vs. prod clusters, place them in separate Atlas projects.

**Atlas CLI commands:**
```bash
atlas maintenanceWindows describe --projectId <projectId>
atlas maintenanceWindows update --dayOfWeek 1 --hourOfDay 2 --projectId <projectId>
atlas maintenanceWindows clear --projectId <projectId>
```

Day-of-week values: Sunday=1, Monday=2, Tuesday=3, Wednesday=4, Thursday=5, Friday=6, Saturday=7.

### What triggers maintenance

| Trigger | Follows Maintenance Window? |
|---|---|
| MongoDB patch version upgrade (e.g., 7.0.8 → 7.0.9) | Yes |
| Atlas infrastructure / hardware updates | Yes |
| Feature releases requiring restart | Yes |
| Critical security patch (CVE) | No — Atlas may override window |
| Major version upgrade (e.g., 6.0 → 7.0) | No — separately scheduled by operator |
| Cluster tier scaling (scale up/down) | No — operator-initiated, immediate rolling restart |
| Storage scaling | No — operator-initiated |
| Cluster pause / resume | No — operator-initiated |

Emergency security patches bypass the maintenance window entirely. Atlas notifies project and organization owners via email, but the window configuration does not constrain it.

### How Atlas performs rolling maintenance

1. **Secondaries first** — one at a time, waiting for each to rejoin and catch up before proceeding.
2. **Primary last** — triggers a replica set election.
3. **Election window** — typically 10–30 seconds; writes temporarily unavailable, reads fall back to secondaries.
4. **mongos nodes (sharded clusters only)** — restarted last. Skip for replica-set-only deployments.

**Application impact:** Drivers with retryable writes handle the election transparently. Applications without retryable writes may see one transient write failure.

**Alert during maintenance:** The **"Primary election"** alert fires during every maintenance restart. Configure a lower-urgency channel for this alert type or correlate it with the maintenance window time.

**Total duration:** 3-node replica set: 5–15 min. Sharded clusters: multiply per-shard restart time by shard count (30–60 min for large topologies).

### Deferring maintenance

**Rules:**
- Deferral postpones by exactly **7 days**, once only per scheduled event
- After one deferral, maintenance executes at the rescheduled time — no further deferral
- **Critical security patches cannot be deferred** — attempting to defer returns an error

```bash
atlas maintenanceWindows defer --projectId <projectId>
# API:
POST /api/atlas/v2/groups/{groupId}/maintenanceWindow/defer
```

### Querying the maintenance window via API

```bash
curl -u "{publicKey}:{privateKey}" --digest \
  "https://cloud.mongodb.com/api/atlas/v2/groups/{groupId}/maintenanceWindow" \
  -H "Accept: application/vnd.atlas.2023-01-01+json"
```

Response fields: `dayOfWeek` (1–7, absent if no custom window), `hourOfDay` (0–23 UTC), `startASAP` (maintenance queued for next opportunity), `autoDeferOnceEnabled`.

### Emergency and critical security patches

- Same-day or next-day notice for critical CVEs; 24–48 hours for lower-severity updates
- Notifications sent to all Project Owners and Organization Owners
- Cannot be deferred; rolling restart procedure still used to minimize impact
- Monitor **Activity Feed** (Atlas UI → Project → Activity) for maintenance start/completion timestamps

### Minimizing application impact

| Option | Recommended value | Reason |
|---|---|---|
| `retryWrites` | `true` (default since driver 4.2) | Transparent retry on primary election |
| `retryReads` | `true` | Retry reads on network errors and primary changes |
| `serverSelectionTimeoutMS` | `30000` | Elections take 10–30s; 3000ms causes premature timeout |
| `connectTimeoutMS` | `10000` | Standard connection timeout |
| `socketTimeoutMS` | `0` (disabled) | Short socket timeouts interfere with long ops |

**Why `serverSelectionTimeoutMS=30000` matters:** With 3000ms, a 12-second election causes `ServerSelectionTimeoutError` before the new primary is elected.

**Post-election warm-up:** First queries to the new primary may be slower (30–60s) while connections re-establish and the WiredTiger cache warms.

### Atlas maintenance for sharded clusters

Sequence: config server replica set (CSRS) → shard replica sets (sequentially) → mongos routers (parallel, stateless).

**Balancer:** suspended during maintenance; in-progress migrations complete, no new ones start.

**Duration estimate:** per-shard restart time × shard count + CSRS + mongos. A 4-shard cluster at 10 min/shard ≈ 40–50 min for shards alone.

### Customer communication template

Replace all `[bracketed]` placeholders before sending.

```
Subject: Planned database maintenance — [Day, Month DD YYYY]

Maintenance window: [Day of week, YYYY-MM-DD] [HH:MM]–[HH:MM] UTC
Expected impact:    < 30 second connection interruption during primary election.
                    No data loss will occur.
Action required:    None. Retryable writes handle this automatically.
                    Non-retryable operations may see one transient error.

Questions after [HH:MM] UTC: contact [support channel / Slack #channel].
```

**Placeholder guide:** `[HH:MM]–[HH:MM] UTC` = configured 1-hour window (e.g., "02:00–03:00 UTC"). Always include: specific UTC time window, < 30s impact (not full restart duration), explicit no-data-loss statement, retryable writes note, escalation path.
