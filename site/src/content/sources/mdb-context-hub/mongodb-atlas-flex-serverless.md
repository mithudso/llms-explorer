---
title: "MongoDB Atlas Flex and Serverless Tiers"
description: "MongoDB Atlas Flex tier (GA: February 6, 2025) is the successor to both the shared tier (M2/M5) and the serverless tier. As of January 22, 2026, M2/M5 clusters and Serverless instances are end-of-life"
---

# MongoDB Atlas Flex Clusters and Serverless Instances

## Overview

MongoDB Atlas Flex tier (GA: February 6, 2025) is the successor to both the shared tier (M2/M5) and the serverless tier. As of January 22, 2026, M2/M5 clusters and Serverless instances are end-of-life and no longer supported — all existing instances were automatically migrated. Flex is now the entry-level paid cluster in Atlas.

## Tier Landscape (2025–2026)

| Tier | Cost | Storage | Connections | Network | Use Case |
|------|------|---------|-------------|---------|----------|
| M0 (Free) | $0 | 512 MB | 500 | Public IP only | Exploration |
| Flex | $8–$30/mo | 5 GB (hard cap) | 500 | Public IP only | Dev, staging, MVP |
| M10 Dedicated | ~$57/mo | 10 GB+ | 1,500 | VPC Peering + PrivateLink | Production |

## Flex Pricing Model

Ops-per-second tiered hourly model capped monthly — no per-document billing:
- Base: 100 ops/sec + 5 GB storage → $8/month
- 200 ops/sec → $15/month
- 300 ops/sec → $21/month  
- 400 ops/sec → $26/month
- 500 ops/sec → $30/month (hard cap — no runaway billing)

Billed hourly, prorated. Burst to 500 ops/sec for 1 hour does not cost $30.

**Key differences from Serverless:** Fixed-price cap (no unbounded billing), no cold starts, always warm.

## Flex Technical Limits

| Resource | Limit |
|----------|-------|
| Max connections | 500 |
| Max ops/sec | 500 (read + write combined) |
| Max storage | 5 GB (hard cap, cannot configure) |
| Max collections | 500 total |
| Sort in-memory | 32 MB |
| Aggregation stages | 50 max |
| MongoDB version | Minimum 8.0; auto-upgrade only |

## Unsupported Features on Flex
- Private Endpoints (AWS PrivateLink, Azure Private Link, GCP PSC)
- VPC/VNet Peering
- Continuous Backup / PITR (daily snapshot only)
- Database Auditing
- Customer Key Management (BYOK)
- Performance Advisor, Real-Time Performance Panel, Auto-indexing
- `allowDiskUse` for aggregations
- `$where`, `mapReduce` (no server-side JavaScript)
- Sharded clusters (replica sets only)

## Supported Features on Flex (Added vs. old M2/M5)
- Atlas Search (full-text Lucene)
- Atlas Vector Search (HNSW — with resource contention caveat)
- Change Streams
- Atlas Triggers and App Services
- Full driver compatibility

**Vector Search caveat:** `mongod` and `mongot` share the same node on Flex. Resource contention causes higher query latency. Upgrade to M10+ with dedicated Search Nodes before production.

## Flex vs. Dedicated Decision Matrix

**Stay on Flex if ALL true:**
- Peak throughput < 500 ops/sec
- Data < 5 GB
- Connections < 500
- No private networking requirement
- No PITR backup requirement
- No BYOK encryption requirement
- Development, staging, prototype, or low-traffic production

**Move to Dedicated (M10+) when ANY trigger:**
- Approaching 500 ops/sec consistently
- Data exceeds 5 GB
- Need private endpoints or VPC peering
- Need PITR (compliance requirement)
- Need BYOK encryption at rest
- Atlas Vector Search going to production
- SLA requires predictable low-latency
- Need > 500 concurrent connections
- Need custom MongoDB version pinning

**Cost break-even:** Flex max = $30/mo; M10 = ~$57/mo. For light workloads (<100 ops/sec, <1 GB): Flex saves 85%+ vs. M10.

## EOL Timeline

| Date | Event |
|------|-------|
| February 2025 | Flex GA; new M2/M5 and Serverless creation disabled |
| March 2025 | Atlas auto-migrated Serverless instances |
| January 22, 2026 | EOL: M2/M5 and Serverless fully deprecated |

## Tooling Migration

### Atlas CLI
```bash
atlas clusters create my-flex-cluster --provider AWS --region US_EAST_1 --tier FLEX
atlas clusters upgrade my-flex-cluster --tier M10  # one-way upgrade
```

### Terraform
```hcl
resource "mongodbatlas_flex_cluster" "example" {
  project_id = var.project_id
  name       = "my-flex-cluster"
  provider_settings = {
    backing_provider_name = "AWS"
    region_name           = "US_EAST_1"
  }
}
```
Note: Do NOT use `MongoDB::Atlas::FlexCluster` in CloudFormation — use `MongoDB::Atlas::Cluster` instead.

### Kubernetes Operator
Upgrade to AKO 2.12.0+. Use `spec.flexSpec` in `AtlasDeployment` CRD. To upgrade Flex → Dedicated: `spec.upgradeToDedicated: true`.

## Migration Path: Flex → Dedicated
- **One-way:** Cannot downgrade dedicated → Flex
- **Downtime:** Upgrading Flex → M10+ incurs downtime
- **Snapshots not migrated:** Download existing Flex snapshots before upgrading

## Serverless History (Deprecated)

Serverless used RPU (Read Processing Unit) / WPU (Write Processing Unit) per-document billing. Caused runaway charges for unindexed queries. Cold starts after ~5 minutes idle (30-60 second reconnect delay). Replaced by Flex due to unpredictable billing, cold start latency, and feature gaps.

## Anti-Patterns

- **Flex for production with PrivateLink requirement:** Must use M10+ for private endpoints
- **Production Vector Search on Flex:** Resource contention causes latency spikes
- **Expecting PITR on Flex:** Daily snapshots only
- **Pinning MongoDB version on Flex:** Flex auto-upgrades — use dedicated for version pinning
- **Overbuilding M10 for dev/staging:** Flex handles dev/staging at 1/7th the cost

## Free Tier (M0) vs. Flex

M0 auto-pauses after 30 days idle (cold start on resume). Flex never pauses — more suitable for always-on dev/staging environments.

## References

1. [MongoDB Atlas Flex Tier Blog](https://www.mongodb.com/blog/post/dynamic-workloads-predictable-costs-mongodb-atlas-flex-tier)
2. [Atlas Flex Cluster Limitations](https://www.mongodb.com/docs/atlas/reference/flex-limitations/)
3. [Migrate from M2/M5/Serverless to Flex](https://www.mongodb.com/docs/atlas/flex-migration/)
