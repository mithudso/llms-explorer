---
title: "MongoDB Atlas Online Archive"
description: "Online Archive automatically moves documents matching an archival rule out of the live Atlas cluster into Atlas-managed object storage, while keeping those documents queryable through the cluster's FD"
---

# MongoDB Atlas Online Archive

## Overview

Online Archive automatically moves documents matching an archival rule out of the live Atlas cluster into Atlas-managed object storage, while keeping those documents queryable through the cluster's FDI endpoint (transparent to the application).

## Requirements
- Dedicated cluster M10+ (not available on M0/Flex/Serverless)
- MongoDB 5.0+ on the source cluster

## Archive Rule Types

### DATE (most common)
```json
{
  "criteria": {
    "type": "DATE",
    "dateField": "createdAt",
    "dateFormat": "ISODATE",
    "expireAfterDays": 90
  }
}
```

`dateFormat` options: `"ISODATE"` (default ISODate), `"EPOCH_MILLISECONDS"`, `"EPOCH_SECONDS"`

### CUSTOM Query
```json
{
  "criteria": {
    "type": "CUSTOM",
    "query": "{ \"status\": \"completed\", \"updatedAt\": { \"$lt\": {...} } }"
  }
}
```

## Partition Fields Strategy

Partition fields organize archived data into S3 prefix paths for efficient filtering. Critical for query performance. Choose fields commonly used in query filters:

```json
{
  "partitionFields": [
    { "fieldName": "region",     "order": 0 },
    { "fieldName": "createdAt",  "order": 1 },
    { "fieldName": "customerId", "order": 2 }
  ]
}
```

**Rules:**
- Maximum 2 partition fields per archive rule
- First field MUST match the `dateField` (for DATE criteria) or be the most selective filter field (for CUSTOM criteria)
- Order matters: highest-selectivity filter field should be first
- Supported partition pruning operators: `$eq`, `$gt`, `$lt`, `$gte`, `$lte`, `$ne`, `$in`
- Fields NOT in partitionFields trigger full archive scan when queried

## Archive Job Timing & Processing

- Runs every **5 minutes**
- Max throughput: **2 GB per 5-minute interval**
- Max file size: **100 MB per archive file**
- Documents deleted from live cluster AFTER successful write to object storage
- Schedule window: Archive jobs can be limited to off-hours to reduce production impact

## Query Routing

When querying via the cluster's FDI endpoint:
- Recent data → live cluster (fast, indexed)
- Archived data → Online Archive object storage (slower, partition-based)
- Combined queries → both, results merged transparently

Applications do not need to change query patterns after data is archived — same connection string, same MQL.

## Cost Model

| Cost Component | Rate |
|---|---|
| Archive Storage | ~80-90% cheaper than dedicated cluster storage |
| Query Processing (archive) | $5.00/TB (same as Data Federation) |
| Data Returned | Standard cloud egress |

**$5/TB cost applies when QUERYING archived data.** Storage itself is much cheaper than cluster storage (NVMe/GP3).

**Minimum:** 10 MB per archive query (no benefit from very small queries).

## Restore / Rehydration

Archive data is immutable (append-only). To restore to the live cluster:

```javascript
// Restore archived data back to the live cluster via $merge
db.archivedCollection.aggregate([
  { $match: { createdAt: { $gte: cutoffDate } } },   // Filter from archive
  { $merge: { into: { db: "mydb", coll: "orders" }, // Rehydrate into live cluster
              on: "_id",
              whenMatched: "keepExisting",
              whenNotMatched: "insert" } }
])
```

## Deciding: Online Archive vs TTL vs Manual S3 Export

| Approach | Use when |
|---|---|
| Online Archive | Data needs to remain queryable via MQL after tiering; auto-managed pipeline |
| TTL Index | Data can be permanently deleted after expiry (no need to query it) |
| Manual S3 export via `$out` | Full control over format; downstream Spark/Athena/BigQuery consumption |

## Limitations

- **No updates/deletes on archived data:** Archive is immutable object storage; `updateMany` or `deleteMany` against archived documents will not affect them
- **No Atlas Search on archived data:** Full-text `$search` doesn't work on archived data
- **No indexes on archived data:** All archived queries use partition pruning only
- **$sample not random:** Returns first N documents, not a statistical random sample
- **No transactions crossing live+archive:** Cannot span a transaction across live and archived documents
- **Maximum query timeout:** 6 hours (inherits from Data Federation limit)

## Troubleshooting

### Archive Not Moving Data
1. Check Atlas → Online Archive → [collection] → Activity tab for job status and errors
2. Verify `dateField` name is exact (case-sensitive) and matches documents
3. Confirm correct `dateFormat` — `ISODATE` requires actual ISODate values, not Unix epoch integers
4. Confirm cluster tier is M10+ and MongoDB version 5.0+

### Archive Backlog Growing
1. Archive jobs process 2 GB per 5-minute window
2. If data accumulates faster than 2 GB/5 minutes, backlog will grow
3. Mitigation: narrow the archive rule to reduce concurrent archiving volume, or contact MongoDB for higher throughput

### Slow Archive Queries
1. Partition fields not aligned with query filter → full archive scan
2. Check `partitionFields` match the most common query filter fields
3. Run `explain()` on the FDI endpoint to check `nPartitionsScanned`

### MACC / Cost Tracking
Archive storage costs appear on the Atlas invoice under Tools & Services → Online Archive. Query processing costs under Data Federation. Monitor in Atlas Billing → Current Invoice.

## Anti-Patterns

- **Choosing partition fields that don't match query patterns:** Full archive scan on every query → high $5/TB cost
- **Using CUSTOM criteria without an index on the filter field:** Archive job itself will do slow scans to find matching documents — add an index on filter fields
- **Querying archived data without partition-aligned filters:** Always include a partition field in `$match` when querying archive
- **Expecting consistency between live and archive:** Documents are copied to archive and then deleted from live — there is no transactional guarantee between the two
- **Using Online Archive as a backup system:** Archive only stores the final document state at archival time — not a substitute for backup snapshots with PITR

## References

- [Online Archive Documentation](https://www.mongodb.com/docs/atlas/online-archive/)
- [Configure an Online Archive](https://www.mongodb.com/docs/atlas/online-archive/configure-online-archive/)
- [Query Archived Data](https://www.mongodb.com/docs/atlas/online-archive/query-online-archive/)
- [Online Archive Billing](https://www.mongodb.com/docs/atlas/billing/online-archive/)
