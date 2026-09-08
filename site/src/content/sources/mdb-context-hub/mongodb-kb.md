---
title: "MongoDB KB Articles"
description: "This local skill provides a complete index of MongoDB's internal Knowledge Base (~2717 articles) for use in customer troubleshooting, escalation research, and code-pattern lookup."
---

# MongoDB Knowledge Base — Article Index

This local skill provides a complete index of MongoDB's internal Knowledge Base (~2717 articles) for use in customer troubleshooting, escalation research, and code-pattern lookup.

## When to use this skill

Use this skill when you need to:
- Match customer-reported symptoms to KB articles
- Find articles to share with customers (Public visibility only)
- Research known issues, error codes, or resolution procedures
- Look up MongoDB behavior for replica sets, Atlas, sharding, performance, auth, or backups
- Generate code or advice grounded in official MongoDB KB guidance
- Diagnose error codes returned by mongod, mongos, or drivers
- Troubleshoot connectivity, authentication, replication, or sharding failures
- Run diagnostic commands and interpret their output
- Investigate Atlas-specific issues (IP allowlist, VPC peering, cluster scaling)
- Analyze slow query plans and profiler output
- Prepare escalation summaries with supporting diagnostic evidence

## Primary keywords

error code, troubleshoot, KB, knowledge base, support article, replica set, connectivity, atlas, performance, index, aggregation, shard, authentication, ssl, tls, timeout, oplog, writeconcern, readpreference, backup, restore, wiredtiger, replication, failover, slow query, memory, storage, monitoring, alert, upgrade, driver, schema, ldap, kerberos, x.509, currentOp, profiler, explain, serverStatus, FTDC, flowControl, balancer, chunk migration, StaleConfig, election, rollback, initial sync, DNS SRV, SCRAM, connection pool, cursor, transaction, write conflict, document validation

## Context file

The full article index is maintained as the MongoDB KB context document (`kb-context.md`), generated
from the MongoDB KB article source and synced into the mdb-context-hub skill pack as
`skills/contexts/mongodb-kb.md`.

- **Quick Reference section:** top ~50 most broadly applicable articles, grouped by topic
- **Category Index:** all articles grouped by concept (Configuration, Security, Performance, Replication, Sharding, etc.)
- Each entry includes: article ID, title, summary, internal URL (knowledge.corp.mongodb.com), shareable URL (support.mongodb.com), products, visibility (Public/Internal), and when-to-use guidance

## Usage guidance

1. Start at the **Quick Reference** section for common support scenarios
2. For specific topics, jump to the relevant category section
3. Always check **Visibility** before sharing a URL with a customer — only share `Public` articles
4. Use the `shareableurl` (support.mongodb.com) for customer-facing links
5. Use the `internalurl` (knowledge.corp.mongodb.com) when referencing internally

---

# Error Code Quick Reference

The MongoDB server returns numeric error codes with every failed operation. Use this table to quickly identify the category and likely root cause, then search the KB for the specific article.

Reference: https://www.mongodb.com/docs/manual/reference/error-codes/

## Authentication and Authorization Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 13 | Unauthorized | Client lacks required privileges | Missing role grant; wrong authSource database |
| 18 | AuthenticationFailed | Credential verification failed | Wrong password, expired LDAP bind, SCRAM mechanism mismatch |
| 11 | UserNotFound | Specified user does not exist in the auth database | User created in wrong database; authSource mismatch in connection string |
| 214 | AuthenticationRestrictionUnmet | Client IP or connection type does not meet auth restrictions | clientSource/serverAddress restrictions on the user doc |

### SCRAM authentication troubleshooting

- **SCRAM-SHA-256 disabled**: Occurs when the user was created with only SCRAM-SHA-1 credentials but the server or client forces SHA-256. Fix: recreate the user or update credentials with `db.updateUser()`.
- **storedKey mismatch**: The password hash stored in `admin.system.users` does not match. Usually caused by password rotation without updating all nodes, or restoring a backup with stale user docs.
- **Mechanism negotiation**: Drivers negotiate SCRAM-SHA-256 first (MongoDB 4.0+). If the server only supports SCRAM-SHA-1, set `authMechanism=SCRAM-SHA-1` explicitly in the connection string.
- **LDAP bind failures**: When using LDAP proxy auth (`PLAIN` mechanism), verify the `mongod` can reach the LDAP server, the bind credentials are correct, and the LDAP user DN mapping is accurate. Check `mongod` log for `LDAP connection error` messages.
- **x.509 certificate issues**: Ensure the client certificate subject (O, OU, DC) matches the server's `tlsClusterAuthX509Attributes`, the certificate is not expired, and the CA chain is complete.

## Network and Connection Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 6 | HostUnreachable | Cannot route to the target host | Firewall rule, security group, or routing table blocking traffic |
| 7 | HostNotFound | DNS resolution failed for the hostname | Typo in hostname; missing DNS record; split-horizon DNS issue |
| 89 | NetworkTimeout | TCP connection or operation timed out | Network latency; overloaded server; connectTimeoutMS too low |
| 230 | DNSHostNotFound | SRV/TXT DNS lookup failed | Incorrect `mongodb+srv://` hostname; DNS server unreachable |
| 231 | DNSProtocolError | Malformed DNS response | Broken DNS infrastructure; incompatible record format |
| 240 | DNSRecordTypeMismatch | DNS record type does not match expected type | SRV record pointing to CNAME instead of A/AAAA record |
| 279 | ClientDisconnect | Client closed the connection before operation completed | Application crash; connection pool reclaim; load balancer idle timeout |
| 172 | TransportSessionClosed | The underlying transport session was closed | TLS handshake failure; proxy termination; mongos restart |
| 173 | TransportSessionNotFound | Referenced session does not exist on the server | Session expired (default 30 min); server restart cleared sessions |

## Write Concern and Write Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 64 | WriteConcernFailed | Write concern could not be satisfied (e.g., `wtimeout` exceeded) | Secondary too far behind; network partition; insufficient healthy members |
| 100 | UnsatisfiableWriteConcern | The requested write concern cannot be met | w > number of data-bearing members; tag set matches no member |
| 112 | WriteConflict | Two operations attempted to modify the same document concurrently | High-contention hot document; retry with exponential backoff |
| 278 | UnsatisfiableCommitQuorum | Cannot satisfy the commit quorum for index build | Not enough voting members available during index build |
| 11000 | DuplicateKey | Unique index constraint violated | Inserting a document with a duplicate `_id` or unique-indexed field |

## Replication Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 71 | ReplicaSetNotFound | No replica set with the given name exists | Wrong `--replSet` name; connecting to standalone as replica set |
| 92 | SecondaryAheadOfPrimary | A secondary reports an optime ahead of the primary | Clock skew; split-brain recovery; manual oplog manipulation |
| 93 | InvalidReplicaSetConfig | The replica set configuration document is invalid | Bad member host format; duplicate member IDs; votes/priority conflict |
| 95 | NotSecondary | Operation requires a secondary but node is not in SECONDARY state | Member is RECOVERING, STARTUP2, or ARBITER |
| 108 | InconsistentReplicaSetNames | Member reports a different replica set name | Mismatched `--replSet` flags across members |
| 113 | InitialSyncFailure | Initial sync could not complete | Source oplog too small; network interruption during sync |
| 114 | InitialSyncOplogSourceMissing | Sync source's oplog does not cover required range | Sync source was restarted or oplog rolled over during initial sync |
| 123 | NotAReplicaSet | Node is not configured as part of a replica set | Running `rs.status()` on a standalone mongod |

## Sharding Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 61 | ShardKeyNotFound | Document is missing the shard key field | Insert without shard key on non-`_id` sharded collection |
| 70 | ShardNotFound | Referenced shard does not exist in the cluster | Shard removed but metadata not fully cleaned; typo in shard name |
| 118 | NamespaceNotSharded | Operation requires a sharded collection but it is unsharded | Running shard-specific commands on an unsharded collection |
| 272 | MigrationConflict | Chunk migration conflicts with another operation | Concurrent migrations; long-running operations on the chunk |
| 283 | WouldChangeOwningShard | Update would move the document to a different shard | Modifying shard key value; requires `retryWrites: true` and a transaction on 4.2+ |

## Index Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 27 | IndexNotFound | Referenced index does not exist | Index was dropped; wrong index name or spec in hint |
| 67 | CannotCreateIndex | Index creation failed | Incompatible index options; field type conflict |
| 68 | IndexAlreadyExists | An identical index already exists | Re-running `createIndex` with same key pattern |
| 85 | IndexOptionsConflict | Index exists with same key but different options | Changing collation, sparse, or TTL on existing index |
| 86 | IndexKeySpecsConflict | Index exists with same name but different key pattern | Name collision between two different indexes |
| 276 | IndexBuildAborted | Background index build was aborted | `dropIndex` during build; `killOp` on the build operation |
| 285 | IndexBuildAlreadyInProgress | Another build for the same index is already running | Duplicate `createIndex` call; retry after checking `currentOp` |

## Transaction Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 225 | TransactionTooOld | Transaction's read timestamp is older than the oldest available snapshot | Long-running transaction exceeding `transactionLifetimeLimitSeconds` |
| 251 | NoSuchTransaction | Transaction ID not found on the server | Transaction already committed/aborted; session expired |
| 256 | TransactionCommitted | Attempted to abort a transaction that was already committed | Logic error in application retry code |
| 263 | OperationNotSupportedInTransaction | The operation cannot run inside a multi-document transaction | DDL operations, `createIndex`, `getMore` on non-transaction cursor |
| 290 | TransactionExceededLifetimeLimitSeconds | Transaction exceeded the configured lifetime limit | Default is 60 seconds; increase or break into smaller transactions |

## Cursor and Query Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 43 | CursorNotFound | Server-side cursor was killed or expired | Cursor idle > `cursorTimeoutMillis` (default 10 min); `noCursorTimeout` not set |
| 50 | MaxTimeMSExpired | Operation exceeded the `maxTimeMS` limit | Query too slow; missing index; set a higher limit or optimize |
| 143 | CursorInUse | Attempted to kill a cursor that is actively in use | Race condition in application; wait for getMore to complete |
| 175 | QueryPlanKilled | The query execution plan was invalidated | Index dropped during query; collection dropped/renamed |
| 237 | CursorKilled | Cursor was explicitly killed | `killCursors` command; `cursor.close()` called prematurely |
| 239 | SnapshotTooOld | The requested snapshot is no longer available | Reading from a timestamp older than the WiredTiger history window |

## Document and Validation Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 2 | BadValue | A command argument has an invalid value | Malformed query operator; wrong option type |
| 22 | InvalidBSON | The BSON document is malformed | Corrupted document; driver serialization bug |
| 121 | DocumentValidationFailure | Document fails `$jsonSchema` or validator rules | Schema enforcement with `validationAction: "error"` |
| 116 | DocTooLargeForCapped | Document exceeds the max document size for a capped collection | Capped collection with a maxSize smaller than document |
| 241 | ConversionFailure | Type conversion failed | `$convert` or `$toInt` on an incompatible value |

## General / Resource Errors

| Code | Name | Description | Common cause |
|------|------|-------------|--------------|
| 1 | InternalError | Unclassified server-side error | Bug or edge case; check server logs for stack trace |
| 8 | UnknownError | The server encountered an unexpected error | Disk corruption; OOM kill; hardware failure |
| 146 | ExceededMemoryLimit | Operation exceeded the memory limit (default 100 MB for sorts) | Large unindexed sort; set `allowDiskUse: true` or add index |
| 262 | ExceededTimeLimit | Operation exceeded the internal time limit | Heavy server load; resource contention |

---

# Connectivity Troubleshooting

## Connection string diagnosis

### `mongodb+srv://` (DNS seed list)

1. Verify SRV record exists: `nslookup -type=SRV _mongodb._tcp.<hostname>`
2. Verify TXT record exists: `nslookup -type=TXT <hostname>`
3. The SRV record must resolve to one or more A/AAAA records (not CNAMEs)
4. Common failure: corporate DNS or VPN blocks SRV lookups -- fall back to `mongodb://` with explicit hosts

### `mongodb://` (standard)

1. Verify each host resolves: `nslookup <host>` or `dig <host>`
2. Test TCP connectivity: `nc -zv <host> 27017` (or the configured port)
3. If connecting through a load balancer or proxy, ensure it supports the MongoDB wire protocol (not HTTP)

### IPv6 vs IPv4

Node.js 17+ defaults to IPv6 DNS resolution. If the MongoDB server is IPv4-only:
- Set `family=4` in the connection URI options
- Or set the Node.js flag `--dns-result-order=ipv4first`

## Common connection failure patterns

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ECONNREFUSED` on localhost | mongod not running; wrong port | Start mongod; verify `--port` |
| `ECONNREFUSED` on remote host | Firewall blocking port 27017 | Open port in security group / iptables |
| `ETIMEDOUT` after 10-30s | Network unreachable; wrong IP; NAT misconfiguration | Verify routing; check `--bind_ip` includes the advertised address |
| `SSL handshake failed` | TLS version mismatch; expired certificate; wrong CA | Check `--tlsCAFile`, `--tlsCertificateKeyFile`; verify cert dates |
| `connection closed` immediately | `--auth` enabled but no credentials supplied | Add credentials to connection string |
| `ReplicaSetNotFound` | Wrong `replicaSet=` parameter | Match the `--replSet` name on the server |
| `Server selection timed out` | All seeds unreachable; auth failure hides behind timeout | Test each seed individually; check auth logs |
| `MongoServerSelectionError` | Read preference cannot be satisfied | Ensure secondaries are healthy; adjust `readPreference` |

## Connection pool tuning

| Parameter | Default | When to change |
|-----------|---------|----------------|
| `maxPoolSize` | 100 (Node); 100 (Java) | Increase for high-concurrency apps; decrease for connection-limited Atlas tiers |
| `minPoolSize` | 0 | Set > 0 to avoid cold-start latency |
| `maxIdleTimeMS` | 0 (infinite) | Set to prevent stale connections behind load balancers with idle timeouts |
| `connectTimeoutMS` | 10000 (10s) | Increase for high-latency cross-region connections |
| `socketTimeoutMS` | 0 (infinite) | Set to catch hung connections; use `maxTimeMS` per-query instead when possible |
| `serverSelectionTimeoutMS` | 30000 (30s) | Decrease for fast-fail behavior; increase for intermittent network |
| `heartbeatFrequencyMS` | 10000 (10s) | Lower for faster failover detection (minimum 500ms) |
| `waitQueueTimeoutMS` | 0 (infinite) | Set to prevent unbounded queue growth under pool exhaustion |

---

# Authentication Issues

## SCRAM (default mechanism)

### Mechanism selection
- MongoDB 4.0+ negotiates SCRAM-SHA-256 first, falls back to SCRAM-SHA-1
- If the user was created before 4.0 (or with `mechanisms: ["SCRAM-SHA-1"]`), the driver may fail with `AuthenticationFailed` when it tries SHA-256
- Fix: either recreate the user to include SHA-256 credentials, or force `authMechanism=SCRAM-SHA-1` in the connection string

### Common SCRAM failures

| Error message | Cause | Resolution |
|--------------|-------|------------|
| `Authentication failed` (code 18) | Wrong password or wrong `authSource` | Verify password; set `authSource=admin` (or the correct auth database) |
| `UserNotFound` (code 11) | User does not exist in the specified auth database | Check `db.getUsers()` on the correct database |
| `SCRAM-SHA-256 authentication is disabled` | Server compiled without SHA-256 support or user lacks SHA-256 credentials | Use `SCRAM-SHA-1` or update user credentials |
| `storedKey mismatch` | Password changed on one node but not replicated, or backup restored with stale credentials | Run `db.updateUser()` on the primary and let it replicate |

### Password special characters
Passwords containing `@`, `:`, `/`, `%` must be percent-encoded in the connection string:
```
mongodb://user:p%40ssw%25rd@host:27017/admin
```

## LDAP (PLAIN mechanism)

- Requires Enterprise or Atlas
- The `mongod` process must be able to reach the LDAP server on the configured port (default 389 or 636 for LDAPS)
- Set `--setParameter authenticationMechanisms=PLAIN` (in addition to SCRAM if both are needed)
- Debug with `mongoldap` tool to test LDAP connectivity and user mapping
- Common failure: LDAP bind DN does not match the `security.ldap.userToDNMapping` regex

## x.509 certificate authentication

- The client certificate's subject (O, OU, DC attributes) must differ from the cluster member certificates
- The certificate must be signed by the same CA specified in `--tlsCAFile`
- The certificate must not be expired (`openssl x509 -enddate -noout -in client.pem`)
- The user must exist in the `$external` database with a username matching the certificate subject

## Kerberos (GSSAPI)

- Requires Enterprise
- The `mongod` host must have a valid keytab and be registered as a service principal
- The client must have a valid TGT (`kinit user@REALM`)
- Clock skew > 5 minutes between KDC and mongod will cause authentication failure
- DNS must resolve both forward and reverse lookups for the mongod hostname

---

# Replication Issues

## Diagnostic commands

```javascript
// Replica set status (run on any member)
rs.status()

// Replication info (oplog size and window)
rs.printReplicationInfo()

// Secondary lag details
rs.printSecondaryReplicationInfo()

// Check if flow control is engaged
db.serverStatus().flowControl.isLagged

// Check oplog entries applied per second
db.serverStatus().metrics.repl.apply.ops

// View the replica set configuration
rs.conf()

// Step down the primary (triggers election)
rs.stepDown(60)  // step down for 60 seconds
```

## Member states

| State | Code | Meaning | Action |
|-------|------|---------|--------|
| PRIMARY | 1 | Accepting writes | Normal |
| SECONDARY | 2 | Replicating from primary | Normal |
| RECOVERING | 3 | Not available for reads; replaying oplog | Wait or resync if stuck |
| STARTUP2 | 5 | Running initial sync | Wait; monitor progress with `db.adminCommand({replSetGetStatus:1}).initialSyncStatus` |
| ARBITER | 7 | Vote-only member; no data | Normal for arbiters |
| DOWN | 8 | Unreachable by the reporting member | Check network and mongod process |
| ROLLBACK | 9 | Rolling back uncommitted writes after election | Wait; check `rollback/` directory after completion |
| REMOVED | 10 | Member was removed from the replica set config | Intentional removal or config error |

## Replication lag

### Diagnosis
```javascript
// Check lag on each secondary
rs.printSecondaryReplicationInfo()

// Check flow control (MongoDB 4.2+)
db.serverStatus().flowControl
// If isLagged: true, the primary is throttling writes

// Check oplog window
rs.printReplicationInfo()
// log length should be > 24 hours (recommend 72h+)
```

### Common causes and fixes

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Slow disk on secondary | `iostat` shows high await | Upgrade to SSD; separate journal disk |
| Network latency | `ping` between members > 10ms | Co-locate members in same region; use VPC peering |
| Large write batches | Oplog entries > 16 MB | Break bulk writes into smaller batches |
| Missing indexes on secondary | Profiler shows COLLSCAN on secondary reads | Build indexes on all members |
| Oplog too small | `rs.printReplicationInfo()` shows < 24h window | Resize oplog: `db.adminCommand({replSetResizeOplog: 1, size: 20480})` |
| Long-running transactions | `currentOp` shows open transactions | Reduce transaction duration; increase `transactionLifetimeLimitSeconds` |

## Oplog management

- **Minimum recommended size**: 24 hours of operations; 72 hours or more preferred
- **Check current size**: `rs.printReplicationInfo()` shows configured size and time range
- **Resize without restart** (4.0+): `db.adminCommand({replSetResizeOplog: 1, size: <MB>})`
- **Oplog can grow beyond configured size** to preserve the majority commit point
- **Keep oplog size consistent** across all data-bearing members

## Elections and failover

- Elections are triggered by: primary step-down, primary unreachable (after `electionTimeoutMillis`, default 10s), `rs.stepDown()`, priority changes, member addition/removal
- A candidate needs votes from a **majority** of voting members (e.g., 2 of 3, 3 of 5)
- **Priority 0** members cannot become primary but can vote
- **Hidden members** can vote but are not visible to driver read preferences
- **Avoid even numbers** of voting members (risk of tie); use an arbiter if needed
- **Sequential reboots**: never reboot multiple secondaries simultaneously in a 3-member set; the primary will step down due to loss of quorum

## Rollback scenarios

- Rollback occurs when a former primary had writes that were not replicated to the new primary
- **Data preserved**: rollback data is written to `<dbpath>/rollback/<ns>/<timestamp>.bson`
- **Prevent rollbacks**: use `w: "majority"` write concern (guaranteed no rollback on committed writes)
- **Large rollbacks**: the 300 MB shutdown threshold applied to the legacy "rollback via refetch" path. MongoDB 5.0+ forces majority read concern and uses "recover to a timestamp," which has no fixed rollback-size limit
- **Inspect rollback files**: `bsondump <rollback-file>.bson`

## Initial sync

- Triggered when a new member joins or a member's data is too stale
- The sync source must have an oplog covering the entire duration of the initial sync
- Monitor progress: `rs.status().members[n].initialSyncStatus` (4.4+)
- If initial sync fails repeatedly, increase oplog size on the sync source and ensure network stability
- For large datasets, consider restoring from a backup instead of initial sync (faster and less load on the source)

---

# Sharding Issues

## Diagnostic commands

```javascript
// Sharding status overview
sh.status()

// Balancer state
sh.getBalancerState()        // enabled or disabled
sh.isBalancerRunning()       // actively migrating?

// Recent balancer activity
use config
db.changelog.find({what: /moveChunk/}).sort({time: -1}).limit(5)

// Chunk distribution for a collection
db.chunks.aggregate([
  {$match: {ns: "mydb.mycoll"}},
  {$group: {_id: "$shard", count: {$sum: 1}}}
])

// Check for jumbo chunks
db.chunks.find({jumbo: true})

// Orphaned documents
db.runCommand({cleanupOrphaned: "mydb.mycoll"})

// Flush routing metadata on mongos
db.adminCommand({flushRouterConfig: 1})
```

## Balancer issues

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| Balancer not running | `sh.getBalancerState()` returns false | `sh.startBalancer()` |
| Balancer running but no migrations | Check `config.changelog` for errors | Review mongos and shard logs for migration errors |
| Migrations failing with lock timeout | Log shows `LockTimeout` during moveChunk | Stop conflicting operations; adjust `_secondaryThrottle` |
| Uneven distribution persists | `sh.status()` shows skewed chunk counts | Check for jumbo chunks; verify shard key cardinality |
| Balancer window too narrow | Migrations don't complete in the scheduled window | Widen the balancer window or remove the schedule |

## Chunk migration failures

- **Lock timeout**: The balancer cannot acquire an exclusive lock on the collection. Stop long-running operations or schedule migrations during low-traffic windows.
- **Insufficient disk space**: The destination shard must have free space at least equal to the chunk size.
- **Replication lag on destination**: If secondaries on the destination shard lag, migration waits for `_secondaryThrottle` to be satisfied.
- **Orphaned documents**: After a failed migration, orphaned documents may remain. Run `cleanupOrphaned` to remove them.

## StaleConfig errors

- Occur when a `mongos` has outdated routing metadata
- The driver automatically retries most StaleConfig errors
- Persistent StaleConfig: run `db.adminCommand({flushRouterConfig: 1})` on the affected mongos
- After adding/removing shards or resharding, all mongos instances should refresh their metadata

## Jumbo chunks

- A chunk is marked `jumbo` when it exceeds the configured chunk size (default 128 MB) and cannot be split
- Jumbo chunks cannot be migrated by the balancer, causing uneven distribution
- **Diagnosis**: `db.getSiblingDB("config").chunks.find({jumbo: true})`
- **Fix**: manually split the chunk with `sh.splitAt()` or `sh.splitFind()`, then clear the jumbo flag: `db.getSiblingDB("config").chunks.updateOne({_id: <chunkId>}, {$unset: {jumbo: 1}})`
- **Root cause**: low-cardinality shard key producing many documents with the same key value

## Shard key issues

- **Monotonically increasing keys** (e.g., ObjectId, timestamp): all inserts go to the last shard, creating a hot shard. Use hashed shard key or compound key with a high-cardinality prefix.
- **Low cardinality keys**: few unique values lead to jumbo chunks that cannot be split. Choose a key with high cardinality.
- **Missing shard key in queries**: queries without the shard key in the filter perform scatter-gather across all shards. Always include the shard key prefix in frequent queries.
- **Changing shard key values** (4.2+): updates that modify the shard key value may move documents between shards. Requires `retryWrites: true` and uses a distributed transaction internally.

---

# Performance Troubleshooting

## Diagnostic workflow

```
1. Check current operations:     db.currentOp({secs_running: {$gt: 5}})
2. Review slow query log:        db.setProfilingLevel(1, {slowms: 100})
3. Analyze query plan:           db.coll.find({...}).explain("executionStats")
4. Check server resource usage:  db.serverStatus()
5. Review collection stats:      db.coll.stats()
6. Check index usage:            db.coll.aggregate([{$indexStats: {}}])
7. Monitor lock contention:      db.serverStatus().globalLock
8. Review WiredTiger cache:      db.serverStatus().wiredTiger.cache
```

## Slow query diagnosis

### Enable profiler
```javascript
// Level 0: off; Level 1: slow ops only; Level 2: all ops
db.setProfilingLevel(1, {slowms: 100})

// Query the profiler
db.system.profile.find().sort({ts: -1}).limit(10)

// Check for COLLSCAN (full collection scan)
db.system.profile.find({planSummary: "COLLSCAN"}).sort({ts: -1})
```

### Interpret explain output

Key fields in `explain("executionStats")`:
| Field | Good value | Bad value |
|-------|-----------|-----------|
| `executionStats.totalKeysExamined` | Close to `nReturned` | Much larger than `nReturned` |
| `executionStats.totalDocsExamined` | Close to `nReturned` | Much larger than `nReturned` (inefficient) |
| `winningPlan.stage` | `IXSCAN`, `FETCH` | `COLLSCAN` (no index used) |
| `executionStats.executionTimeMillis` | < 100ms | > 1000ms |
| `rejectedPlans` | Empty | Many rejected plans (plan cache pollution) |

**Examined-to-returned ratio**: If `totalDocsExamined / nReturned > 10`, the query is scanning too many documents. Add a covering index or refine the query filter.

### Common slow query patterns

| Pattern | Symptom | Fix |
|---------|---------|-----|
| Missing index | COLLSCAN in explain | Create index matching query filter and sort |
| Non-selective index | High keysExamined vs nReturned | Add more fields to index; use compound index |
| Large in-memory sort | `hasSortStage: true` + high memory use | Add sort fields to index (ESR rule) |
| Regex without anchor | `/pattern/` scans entire index | Use `^prefix` regex; or text index for search |
| `$lookup` on large collections | Slow aggregation stages | Add index on `foreignField`; consider embedding |
| Unbounded `find()` | Returning millions of documents | Add `.limit()`; use pagination with `$gt` on indexed field |
| Large `$in` arrays | Slow index scanning | Break into smaller `$in` arrays; consider redesigning schema |
| Over-projection | Returning entire large documents | Use `.projection({field: 1})` to return only needed fields |

## currentOp analysis

```javascript
// Find long-running operations (> 5 seconds)
db.currentOp({
  active: true,
  secs_running: {$gt: 5},
  op: {$ne: "none"}
})

// Find operations waiting for locks
db.currentOp({waitingForLock: true})

// Find operations waiting for flow control
db.aggregate([
  {$currentOp: {}},
  {$match: {waitingForFlowControl: true}}
])

// Kill a specific operation
db.killOp(<opId>)
```

## WiredTiger cache monitoring

```javascript
const wt = db.serverStatus().wiredTiger.cache;

// Cache utilization (should be < 80% of configured cache size)
print("Cache used:", Math.round(wt["bytes currently in the cache"] / 1024 / 1024), "MB");
print("Cache configured:", Math.round(wt["maximum bytes configured"] / 1024 / 1024), "MB");
print("Dirty bytes:", Math.round(wt["tracked dirty bytes in the cache"] / 1024 / 1024), "MB");
print("Pages evicted:", wt["pages evicted by application threads"]);
// If "pages evicted by application threads" is growing, the cache is under pressure
```

## Memory and resource issues

| Indicator | Check with | Healthy | Concerning |
|-----------|-----------|---------|------------|
| Resident memory | `db.serverStatus().mem.resident` | < total RAM - 2GB | Approaching total RAM |
| Page faults | `db.serverStatus().extra_info.page_faults` | Low / stable | Rapidly increasing |
| Connections | `db.serverStatus().connections.current` | < 80% of maxConns | Approaching maxConns |
| Available connections | `db.serverStatus().connections.available` | > 20% of maxConns | < 100 |
| Tickets available | `db.serverStatus().queues.execution` (8.0+); `wiredTiger.concurrentTransactions` (≤7.0) | > 10 per type | 0 (all tickets exhausted) |
| Disk IOPS | OS-level `iostat` | < 80% capacity | Sustained 100% utilization |

---

# Atlas-Specific Issues

## IP access list (allowlist)

- Every client IP must be in the project's IP Access List (Network Access in Atlas UI)
- `0.0.0.0/0` allows access from anywhere (not recommended for production)
- Dynamic IPs (home ISP, serverless functions) require either `0.0.0.0/0` or a static IP solution (NAT gateway, VPN, bastion host)
- Changes to the IP access list take effect within 1-2 minutes
- Atlas shared-tier (M0/M2/M5) does not support VPC peering; must use IP access list

## VPC / network peering

- Available on M10+ dedicated clusters
- After creating a peering connection, you must also add the peered VPC CIDR to the IP Access List
- The peering connection establishes network-level routing, but Atlas still enforces IP-based access control
- For AWS: ensure the VPC route table includes a route to the Atlas CIDR
- For GCP: VPC peering is automatic with network peering; no route table changes needed
- For Azure: ensure the VNet address space does not overlap with the Atlas CIDR
- **Private endpoints** (AWS PrivateLink, Azure Private Link, GCP Private Service Connect) are preferred over peering for production

## Atlas connection troubleshooting checklist

1. Verify cluster is deployed and status is "Active" in the Atlas UI
2. Confirm the database user exists and has the correct roles
3. Check the IP Access List includes the client's current public IP
4. Test DNS resolution: `nslookup <cluster-hostname>.mongodb.net`
5. Test TCP connectivity: `nc -zv <cluster-hostname>.mongodb.net 27017`
6. Verify the connection string uses `mongodb+srv://` with the correct cluster hostname
7. For VPC peering: confirm the peering connection status is "Active" and CIDR is in the access list
8. For private endpoints: confirm the endpoint status is "Available" in both Atlas and the cloud provider
9. Check TLS: Atlas requires TLS by default; ensure `tls=true` in the connection string (or `ssl=true` for older drivers)
10. Check driver compatibility: verify the driver version supports the MongoDB server version on the Atlas cluster

## Atlas-specific operational issues

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| Cluster scaling in progress | Connections dropping during vertical scale | Wait for operation to complete; use retryable writes |
| Auto-scaling triggers | Performance degrades then recovers | Review auto-scaling settings; set appropriate min/max tiers |
| Atlas Search index building | Search queries return incomplete results | Wait for index build to complete (check Atlas UI) |
| Serverless instance cold start | First query after idle period is slow | Provision always-on compute (dedicated tier) for latency-sensitive workloads |
| Atlas maintenance window | Brief connection interruptions | Schedule during low-traffic periods; use retryable writes and reads |
| Cloud provider outage | Cluster unreachable | Multi-region clusters provide automatic failover; verify region configuration |
| Atlas audit log gaps | Missing events in audit feed | Check if audit filter excludes the event type; verify log delivery destination |

---

# Diagnostic Commands Reference

## Server and instance diagnostics

```javascript
// Full server status (very large output)
db.serverStatus()

// Selective server status (recommended)
db.serverStatus({
  repl: 1,
  metrics: 1,
  wiredTiger: 1,
  connections: 1,
  opcounters: 1,
  locks: 1
})

// Build information
db.adminCommand({buildInfo: 1})

// Host system info
db.adminCommand({hostInfo: 1})

// Current connections and auth state
db.adminCommand({connectionStatus: 1, showPrivileges: true})

// Connection pool statistics (for outgoing connections)
db.adminCommand({connPoolStats: 1})

// Command-line options the server was started with
db.adminCommand({getCmdLineOpts: 1})
```

## Database and collection diagnostics

```javascript
// Database statistics
db.stats()

// Collection statistics
db.collection.stats()

// Collection storage details with index sizes
db.collection.stats({indexDetails: true})

// Total data size across all collections
db.stats().dataSize

// Index usage statistics
db.collection.aggregate([{$indexStats: {}}])

// Validate collection data and indexes
db.collection.validate({full: true})

// List all indexes on a collection
db.collection.getIndexes()
```

## Operation monitoring

```javascript
// All active operations
db.currentOp({active: true})

// Slow operations (> N seconds)
db.currentOp({active: true, secs_running: {$gt: 10}})

// Operations by namespace
db.currentOp({ns: "mydb.mycoll"})

// Operations by type
db.currentOp({op: "query"})  // query, insert, update, remove, command

// Kill a long-running operation
db.killOp(<opId>)

// Top: per-collection operation timings
db.adminCommand({top: 1})

// Recent log messages
db.adminCommand({getLog: "global"})
db.adminCommand({getLog: "startupWarnings"})
```

## Replication diagnostics

```javascript
rs.status()                           // Replica set member states and health
rs.conf()                             // Replica set configuration
rs.printReplicationInfo()             // Oplog size and time range
rs.printSecondaryReplicationInfo()    // Lag per secondary
db.serverStatus().flowControl         // Flow control metrics
db.serverStatus().metrics.repl        // Replication metrics
db.getReplicationInfo()               // Programmatic oplog info
```

## Sharding diagnostics

```javascript
sh.status()                           // Cluster overview
sh.getBalancerState()                 // Is balancer enabled?
sh.isBalancerRunning()                // Is balancer currently active?
db.adminCommand({balancerStatus: 1})  // Detailed balancer status
db.adminCommand({listShards: 1})      // All shards in the cluster

// Config database queries
use config
db.shards.find()                      // Shard definitions
db.chunks.find({ns: "db.coll"})       // Chunk distribution
db.changelog.find().sort({time: -1}).limit(10)  // Recent balancer events
db.mongos.find()                      // Connected mongos instances
db.settings.find()                    // Cluster settings (chunk size, balancer)
```

## FTDC (Full-Time Diagnostic Data Capture)

- Enabled by default on all MongoDB deployments
- Captures `serverStatus`, `replSetGetStatus`, and other metrics every 1 second
- Stored in `<dbpath>/diagnostic.data/`
- Analyze with `mongod --ftdc` tools or third-party tools like `keyhole`, `mdiag`
- For Atlas: download FTDC data from the Atlas UI under the cluster's "..." menu
- FTDC does not capture query shapes or slow queries -- use the profiler for those

## Log analysis

### Log structure (MongoDB 4.4+ structured logging)

MongoDB 4.4+ uses structured JSON logging. Key fields:
- `t.$date`: timestamp
- `s`: severity (F, E, W, I, D1-D5)
- `c`: component (ACCESS, COMMAND, CONTROL, NETWORK, QUERY, REPL, SHARDING, STORAGE, etc.)
- `id`: message ID (stable across versions)
- `ctx`: context (connection ID, thread name)
- `msg`: human-readable message
- `attr`: structured attributes (query shape, duration, planSummary, etc.)

### Key log messages to watch

| Component | Message ID | Meaning |
|-----------|-----------|---------|
| COMMAND | 51803 | Slow operation (exceeds `slowOpThresholdMs`) |
| REPL | 21234 | Transition to new replica set state |
| REPL | 21359 | Rollback started |
| ELECTION | 21450 | Election started |
| ACCESS | 20249 | Authentication failed |
| NETWORK | 22944 | Connection accepted |
| NETWORK | 22984 | Connection ended |
| SHARDING | 22104 | Chunk migration started |
| STORAGE | 22430 | WiredTiger cache eviction |
| INDEX | 20437 | Index build started |

> Log message IDs are version-specific. Only `51803` (COMMAND slow op) is reliably stable across versions; confirm the others against the target deployment's MongoDB version before relying on them.

### Filtering logs with jq

```bash
# Find slow operations
cat mongod.log | jq 'select(.c == "COMMAND" and .attr.durationMillis > 1000)'

# Find authentication failures
cat mongod.log | jq 'select(.c == "ACCESS" and .s == "E")'

# Find replication state changes
cat mongod.log | jq 'select(.c == "REPL" and .msg | test("transition"))'

# Find network errors
cat mongod.log | jq 'select(.c == "NETWORK" and .s == "E")'
```

---

# Escalation and Support Workflow

## When to escalate

- Customer is experiencing data loss or corruption
- A node is in an unrecoverable state (repeated crash loop, ROLLBACK that never completes)
- Performance degradation with no identifiable root cause after profiler and explain analysis
- Cluster-wide issues affecting availability (elections every few minutes, split-brain)
- Atlas-specific issues that cannot be resolved through the UI or API (stuck scaling operations, billing anomalies)

## Information to collect for escalation

1. **MongoDB version**: `db.adminCommand({buildInfo: 1}).version`
2. **Topology**: standalone / replica set / sharded cluster; number of members; Atlas tier
3. **Server status snapshot**: `db.serverStatus()` (full output)
4. **Replica set status**: `rs.status()` (if applicable)
5. **Sharding status**: `sh.status()` (if applicable)
6. **FTDC data**: from `<dbpath>/diagnostic.data/` or Atlas download
7. **Log excerpts**: relevant log lines with timestamps (use structured JSON format)
8. **Profiler output**: `db.system.profile.find().sort({ts: -1}).limit(20)` for slow query issues
9. **Explain plans**: `db.coll.find({...}).explain("executionStats")` for query performance issues
10. **Timeline**: when the issue started, any recent changes (deployments, config changes, scaling)
11. **Impact**: number of users affected, error rates, latency percentiles
12. **Reproduction steps**: if the issue is reproducible

## Support escalation templates

### Connectivity issue template
```
Subject: Connectivity failure — [cluster-name]

Environment: Atlas M30 / Self-managed 7.0.x
Topology: 3-node replica set, region: us-east-1
Driver: Node.js v6.x / Java Sync v5.x / Python v4.x

Symptoms:
- Error: [exact error message]
- First observed: [timestamp]
- Frequency: [constant / intermittent / periodic]

Steps taken:
1. Verified IP access list
2. Tested DNS resolution: [results]
3. Tested TCP connectivity: [results]
4. Checked server logs: [relevant log excerpts]

Attachments: FTDC data, server logs, connection string (redacted)
```

### Performance issue template
```
Subject: Slow query performance — [collection-name]

Environment: Atlas M50 / Self-managed 8.0.x
Collection size: [doc count, data size, index count]
Query pattern: [the query or aggregation pipeline]

Symptoms:
- Average latency: [before] -> [now]
- Profiler output: [attached or inline]
- Explain plan: [attached or inline]

Steps taken:
1. Ran explain("executionStats"): [key findings]
2. Checked index usage: [$indexStats results]
3. Checked server resources: [cache utilization, connections, tickets]

Attachments: explain output, profiler entries, serverStatus snapshot
```

---

# References

- MongoDB Error Codes: https://www.mongodb.com/docs/manual/reference/error-codes/
- Connection Troubleshooting (Node.js Driver): https://www.mongodb.com/docs/drivers/node/current/connect/connection-troubleshooting/
- Connection Troubleshooting (Java Driver): https://www.mongodb.com/docs/drivers/java/sync/current/connection/connection-troubleshooting/
- Troubleshoot Replica Sets: https://www.mongodb.com/docs/manual/tutorial/troubleshoot-replica-sets/
- Troubleshoot Sharded Clusters: https://www.mongodb.com/docs/manual/tutorial/troubleshoot-sharded-clusters/
- Monitor Slow Queries: https://www.mongodb.com/docs/manual/tutorial/monitor-slow-queries/
- Database Profiler: https://www.mongodb.com/docs/manual/tutorial/find-slow-queries-with-database-profiler/
- Explain Slow Queries: https://www.mongodb.com/docs/manual/tutorial/explain-slow-queries/
- Diagnostic Commands: https://www.mongodb.com/docs/manual/reference/command/nav-diagnostic/
- serverStatus Reference: https://www.mongodb.com/docs/manual/reference/command/serverstatus/
- replSetGetStatus Reference: https://www.mongodb.com/docs/manual/reference/command/replsetgetstatus/
- Atlas FAQ Networking: https://www.mongodb.com/docs/atlas/reference/faq/networking/
- Atlas Connection Troubleshooting: https://www.geeksforgeeks.org/mongodb/troubleshooting-mongodb-atlas-connection-errors/
- Monitoring Self-Managed Deployments: https://www.mongodb.com/docs/manual/administration/monitoring/
- Exit Codes and Statuses: https://www.mongodb.com/docs/manual/reference/exit-codes/
- Query Performance: https://www.mongodb.com/docs/manual/administration/query/
- MongoDB Replication Internals: https://github.com/mongodb/mongo/blob/master/src/mongo/db/repl/README.md
