---
title: "MongoDB Migration Patterns"
description: "| Tool | From → To | Downtime | Best for |"
---

# MongoDB Migration Patterns

## Migration Tool Selection

| Tool | From → To | Downtime | Best for |
|---|---|---|---|
| Atlas Live Migration | Self-managed → Atlas | Minimal (minutes) | MongoDB 4.4+ → Atlas |
| mongosync | MongoDB → MongoDB | Near-zero | Cluster-to-cluster sync |
| Relational Migrator | RDBMS → MongoDB | Depends on strategy | Oracle/MySQL/PostgreSQL/SQL Server/DB2 |
| mongodump/mongorestore | MongoDB → MongoDB | Full (offline) | Small datasets, cold migrations |
| mongoexport/mongoimport | Any → MongoDB | Full (offline) | JSON/CSV interchange |

## Atlas Live Migration (Self-Managed → Atlas)

### Process
1. Pre-migration check: Atlas validates source cluster compatibility
2. Initial sync: Atlas pulls all documents from source
3. Oplog tailing: Atlas continuously applies changes from source oplog during sync
4. Cutover: When lag < 30 seconds, initiate cutover — stop writes, confirm lag = 0, switch connection strings

### Requirements
- Source MongoDB: 4.4–8.0; must be a replica set (not standalone)
- Atlas cluster must be M10+ in same major version or one version ahead
- Source must be accessible from Atlas servers

### Atlas CLI Migration
```bash
atlas liveMigrations create --clusterName targetCluster --projectId <id> \
  --migrationHosts source.example.com:27017 --ssl --caFile /path/to/ca.pem

atlas liveMigrations cutover --clusterName targetCluster --projectId <id>
```

## mongosync — Cluster-to-Cluster Sync

mongosync is MongoDB's cluster-to-cluster synchronization tool.

```bash
# Start mongosync
./mongosync \
  --cluster0 "mongodb+srv://user:pass@source.mongodb.net" \
  --cluster1 "mongodb+srv://user:pass@dest.mongodb.net"

# Initialize sync
curl -X POST http://localhost:27182/api/v1/start \
  -H "Content-Type: application/json" \
  -d '{"source": "cluster0", "destination": "cluster1"}'

# Monitor progress
curl http://localhost:27182/api/v1/progress

# Commit (finalize)
curl -X POST http://localhost:27182/api/v1/commit
```

### mongosync Limitations
- Source and destination must be compatible versions
- Destination must be empty at start
- No filtering (syncs all databases except admin, local, config)
- No support for standalone source (must be replica set)

### Cutover Procedure
1. Monitor `lagTimeSeconds` until < 10 seconds
2. Stop writes to source cluster
3. Wait until `lagTimeSeconds: 0` and `state: COMMITTED`
4. Call `commit` API
5. Update application connection strings to destination

## Relational Migrator

MongoDB Relational Migrator is a free GUI tool for migrating RDBMS schemas and data to MongoDB.

### Supported Source Databases
Oracle 11g+, MySQL 5.7+, PostgreSQL 11+, SQL Server 2016+, DB2 11.5+, Sybase/ASE 16.0+, YugabyteDB

### Migration Strategy Options
- **Embedded documents:** Denormalize related tables into embedded arrays/documents (recommended for 1:1 or bounded 1:many)
- **Referenced documents:** Keep normalized references (for many:many or unbounded arrays)

### Pre-Migration Analysis
Key checks:
- Unique index violations in source → become duplicate documents
- NULL handling: SQL NULL → MongoDB absence (not `null` by default)
- DECIMAL precision: Map to Decimal128 for financial data (not Double)
- Date/time columns: RDBMS timestamps → MongoDB Date with UTC conversion

### Snapshot vs CDC Migration
- **Snapshot only:** Full copy; requires application downtime during migration
- **Snapshot + CDC:** Initial snapshot + ongoing change tracking; minimal downtime cutover

## Zero-Downtime Migration Runbook

### Phase 1: Pre-Migration (Days Before)
1. Source assessment: document count, storage size, index count, write rate
2. Schema analysis: run Relational Migrator pre-migration advisor
3. Network validation: confirm Atlas can reach source
4. Pilot migration: migrate subset of non-critical collections

### Phase 2: Initial Sync
1. Start mongosync or Atlas Live Migration
2. Monitor initial sync progress
3. Monitor source cluster performance (migration reads impact production)
4. Validate document counts periodically

### Phase 3: Cutover
1. Announce maintenance window
2. Drain writes (stop scheduled jobs, maintenance tasks)
3. Confirm sync lag < 10 seconds
4. Stop application writes (brief read-only or maintenance page)
5. Confirm sync lag = 0
6. Update connection strings in application config/secrets
7. Restart applications pointing to Atlas
8. Resume writes
9. Verify: check application health, error rates, latency

### Phase 4: Validation
```javascript
// Document count comparison
db.orders.countDocuments()  // Compare source vs destination

// Sample document validation
db.orders.aggregate([
  { $sample: { size: 100 } },
  { $project: { _id: 1, orderId: 1, amount: 1, status: 1 } }
])
```

## Common Migration Anti-Patterns

- **Migrating without pilot testing:** Always test with a non-critical collection first
- **Not sizing oplog for migration duration:** If migration takes > oplog window, migration restarts from scratch
- **Underestimating initial sync time:** 1 TB at 100 MB/s = ~3 hours; plan for 2-3x actual transfer time
- **Not testing application compatibility before cutover:** Atlas has different defaults (w: majority, retryWrites: true, TLS required)
- **Ignoring DBA user differences:** Create all required database users in Atlas before cutover
- **Single-attempt cutover with no rollback plan:** Keep source live for 48 hours post-cutover

## References

- [Atlas Live Migration Documentation](https://www.mongodb.com/docs/atlas/import/live-import/)
- [mongosync Documentation](https://www.mongodb.com/docs/cluster-to-cluster-sync/)
- [MongoDB Relational Migrator](https://www.mongodb.com/docs/relational-migrator/)
