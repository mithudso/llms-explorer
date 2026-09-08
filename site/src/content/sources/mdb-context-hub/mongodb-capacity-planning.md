---
title: "MongoDB Capacity Planning"
description: "Atlas capacity planning covers four primary resources: RAM (working set), IOPS, storage, and connections. Getting these right prevents both over-provisioning (wasted cost) and under-provisioning (perf"
---

# MongoDB Atlas Capacity Planning

## Overview

Atlas capacity planning covers four primary resources: RAM (working set), IOPS, storage, and connections. Getting these right prevents both over-provisioning (wasted cost) and under-provisioning (performance degradation).

## Working Set Sizing (RAM)

The working set is the set of indexes + active document data that MongoDB keeps in WiredTiger cache. When the working set fits in RAM, queries are fast. When it doesn't, cache eviction causes disk I/O spikes.

**Rule of thumb:** Atlas WiredTiger cache = 50% of RAM − 1 GB. An M30 (8 GB RAM) provides ~3 GB of WiredTiger cache.

### Estimating Working Set

```javascript
// mongosh: get index sizes
db.collection.stats().indexSizes
// or aggregated
Object.entries(db.collection.stats().indexSizes)
  .map(([name, size]) => ({ name, sizeMB: size / 1024 / 1024 }))

// Get collection size
db.collection.stats().size  // bytes of data
db.collection.stats().storageSize  // bytes on disk (compressed)
```

**Working set = frequently accessed document data + all active indexes**

Indexes must always be hot (in WiredTiger cache). If total index size > cache, performance degrades severely.

### Atlas Metrics to Watch

- **Cache Utilization (%):** > 80% signals working set doesn't fit in RAM
- **Page Faults:** > 0 steady-state = working set pressure; growing = critical
- **WiredTiger Cache Dirty Bytes:** Consistently high = eviction pressure

## IOPS Capacity

### Atlas IOPS by Tier

| Tier | Storage Type | IOPS |
|---|---|---|
| Flex | Shared | Not guaranteed |
| M10 (10 GB) | GP3 | 3000 (baseline GP3) |
| M20 (20 GB) | GP3 | 3000 |
| M30 (40 GB) | GP3 | 3000 |
| M40 (80 GB) | GP3 | 3000 |
| M50 (160 GB) | GP3 | 3000 |
| M60 (320 GB) | NVMe | ~100,000+ |
| M80, M200, M300 | NVMe | ~200,000+ |
| Any M10+ | Provisioned IOPS | Custom (expensive) |

**GP3 note:** All GP3 volumes provide 3000 IOPS baseline regardless of size. For higher IOPS, upgrade to NVMe-backed tiers (M60+) or enable Provisioned IOPS (significant cost increase).

### IOPS Forecasting

```
IOPS demand = (write ops/sec × avg document size / 4 KB) × write amplification
```

Write amplification = typically 3-5x for WiredTiger (journaling + checkpoint + compression).

**Atlas metrics to watch:**
- **Disk IOPS Utilization:** > 80% = IOPS exhaustion risk
- **Disk Queue Depth:** > 1 = IOPS saturation

## Storage Capacity

### Storage Forecasting

```javascript
// Current rate of growth
db.runCommand({ dbStats: 1, scale: 1024 * 1024 })  // MB
// Track storageSize over time to get growth rate

// Atlas metric: "Disk Usage" — daily reading
```

**Growth model:**
```
storage at T+months = current_storage × (1 + monthly_growth_rate)^months
```

Add 25% headroom for index growth and temporary operations.

### Atlas Autoscaling (Storage)

Atlas can auto-scale storage. Enable in cluster configuration → Autoscaling → Storage. Atlas automatically adds storage when utilization exceeds 90%. Note: storage autoscaling is one-directional (up only).

### Oplog Sizing

Oplog is a capped collection used for replication. Default size: 5% of available disk space (minimum 990 MB, maximum 50 GB).

**Oplog window** = how far back a secondary can fall behind before needing a full resync.

```javascript
// Check oplog window
rs.printReplicationInfo()
// "oplog first event time" to "last event time" = current window
```

**Increase oplog** if:
- Secondaries frequently fall behind (replication lag spikes)
- Maintenance windows require > current oplog window
- High write rate + slow secondaries

## Connection Capacity

### Atlas Connection Limits by Tier

| Tier | Max Connections |
|---|---|
| M0 (Free) | 500 |
| Flex | 500 |
| M10 | 1,500 |
| M20 | 3,000 |
| M30 | 3,000 |
| M40 | 6,000 |
| M50 | 16,500 |
| M60 | 16,500 |
| M80 | 33,000 |

**Per-node limits:** The above are per-node limits. A 3-node replica set has 3× per-node connections available (reads can go to secondaries).

### Connection Pool Sizing

Client applications should use connection pooling. Default pool size in most drivers = 100 connections per MongoClient.

```
max_connections_needed = (application_instances × connection_pool_size) + 20% headroom
```

For serverless/Lambda: set `maxPoolSize: 5-10` per function to prevent connection floods.

## Cluster Tier Selection Guide

### Starting Point (choose based on working set)

| Working Set | Recommended Tier | Connections |
|---|---|---|
| < 1 GB | Flex ($8-30/mo) | 500 |
| 1-3 GB | M10 ($57/mo) | 1,500 |
| 3-7 GB | M20 ($100/mo) | 3,000 |
| 7-15 GB | M30 ($190/mo) | 3,000 |
| 15-30 GB | M40 ($380/mo) | 6,000 |
| 30-60 GB | M50 ($745/mo) | 16,500 |
| > 60 GB | M60+ / Sharding | 16,500+ |

## Atlas Autoscaling (Compute)

Enable in cluster configuration → Autoscaling → Compute.

Atlas auto-scales up based on:
- Average CPU > 75% over the past hour
- Memory utilization > 90%

Atlas auto-scales down based on:
- Average CPU < 25% over the past 24 hours

Configure min/max tier bounds to control costs.

## Sharding Triggers

Consider sharding when **ALL** of the following are true:
- Single M60+ cluster is consistently maxed on CPU or IOPS
- Working set won't fit in even the largest single Atlas tier
- The workload has a natural shard key with good cardinality

**Do NOT shard prematurely:** Sharding adds operational complexity and scatter-gather query overhead. Exhaust vertical scaling options first.

## Performance Advisor

Atlas Performance Advisor (M10+ only) automatically analyzes slow queries (> 100ms by default) and recommends indexes.

```bash
# Atlas CLI
atlas clusters advancedSettings describe myCluster
atlas performanceAdvisor slowQueryLogs list --clusterName myCluster
atlas performanceAdvisor suggestedIndexes list --clusterName myCluster
```

## Growth Signals from Atlas Metrics

| Metric | Signal | Action |
|---|---|---|
| Cache Utilization > 80% | Working set outgrowing RAM | Upgrade tier or add indexes |
| Page Faults > 0 (steady) | Hot data paging to disk | Urgent tier upgrade needed |
| Disk IOPS > 80% | IOPS exhaustion risk | Upgrade to NVMe tier |
| Disk usage > 75% | Running out of storage | Enable autoscaling or manual expansion |
| Connections > 80% of limit | Connection exhaustion risk | Upgrade tier or optimize pool sizing |
| Replication Lag > 30s | Secondary behind primary | Investigate write rate, disk IOPS, network |

## Common Sizing Mistakes

- **Sizing for peak without autoscaling:** Most apps have 5-10x peak-to-baseline ratios; use autoscaling
- **Ignoring index memory:** Indexes must be hot; total index size often exceeds "active document" working set estimate
- **Underestimating connection count in serverless environments:** Lambda × 100 connections/pool = connection flood
- **Sizing storage on current data only:** Model 12-month projected growth + retention policies
- **Choosing M10 for Vector Search in production:** mongot and mongod share resources; upgrade to M30+ with dedicated Search Nodes
- **Not setting a connection pool max in containerized apps:** Each container starts 100 connections; multiply by container count

## References

- [Atlas Cluster Sizing](https://www.mongodb.com/docs/atlas/scale-cluster/)
- [Atlas Autoscaling](https://www.mongodb.com/docs/atlas/cluster-autoscaling/)
- [Atlas Performance Advisor](https://www.mongodb.com/docs/atlas/performance-advisor/)
- [Atlas Connection Limits](https://www.mongodb.com/docs/atlas/reference/atlas-limits/#connection-limits-and-cluster-tier)
