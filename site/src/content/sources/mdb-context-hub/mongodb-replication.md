---
title: "Read Concern Levels"
description: "MongoDB replication provides redundancy and high availability through replica sets -- groups of mongod processes that maintain the same data set. A replica set contains one primary member that receive"
---

# MongoDB Replication Expert

## Overview

MongoDB replication provides redundancy and high availability through **replica sets** -- groups of `mongod` processes that maintain the same data set. A replica set contains one primary member that receives all writes and one or more secondary members that replicate the primary's data asynchronously via the **oplog** (operations log). Replica sets are the foundation of MongoDB's data durability, fault tolerance, and read scaling strategy.

Key guarantees of a properly configured replica set:
- **Automatic failover**: if the primary becomes unavailable, an election promotes a secondary to primary within ~12 seconds (median, with default settings).
- **Data redundancy**: every data-bearing member holds a complete copy of the data set.
- **Read scaling**: applications can distribute reads across secondaries using read preferences.
- **Tunable consistency**: write concern and read concern let applications choose their durability and consistency guarantees per operation.

---

## 1. Replica Set Architecture

### 1.1 Member Types

| Member Type | Holds Data | Can Become Primary | Votes | Visible to Clients |
|---|---|---|---|---|
| **Primary** | Yes | Is primary | 1 | Yes |
| **Secondary** | Yes | Yes (if priority > 0) | 1 (default) | Yes |
| **Arbiter** | No | No | 1 | No |
| **Hidden** | Yes | No (priority must be 0) | 0 or 1 | No (excluded from read preference) |
| **Delayed** | Yes | No (priority must be 0) | 0 (recommended) | No (should be hidden) |

**Primary**: The only member that accepts write operations. Records all writes to its oplog. At most one primary per replica set at any time.

**Secondary**: Maintains an identical copy of the primary's data set by asynchronously applying operations from the primary's oplog. Can serve read operations when read preference allows it. Can be elected primary during failover.

**Arbiter**: Participates in elections but holds no data. Provides a tiebreaking vote in even-member-count topologies. Must not run on the same system as primary or secondary members. Has exactly 1 election vote and a default priority of 0.

**Hidden Members**: Must have `priority: 0`, so they cannot become primary. Excluded from default client read routing. Use for dedicated tasks: reporting queries, backups, analytics workloads. Only reachable by direct connection.

**Delayed Members**: Maintain a time-delayed copy of the data (configured via `secondaryDelaySecs`). Must be hidden and should be non-voting. Serve as a defense against accidental data destruction -- the delayed copy preserves the state from N seconds ago.

### 1.2 Topology Limits

| Limit | Value |
|---|---|
| Maximum total members | 50 |
| Maximum voting members | 7 |
| Minimum recommended (production) | 3 data-bearing members |

### 1.3 Recommended Topologies

**Three-member replica set (P-S-S)**: One primary, two secondaries. Minimum recommended production topology. Tolerates one member failure while maintaining majority for elections and `w: "majority"` writes.

**Primary-Secondary-Arbiter (P-S-A)**: Costs less but carries availability risk. If the sole data-bearing secondary goes down, `w: "majority"` writes fail. Avoid in sharded clusters.

**Geographically distributed**: Place members across data centers. Ensure majority of voting members resides in the primary data center.

---

## 2. Elections and Failover

### 2.1 Election Triggers

Elections occur when: a new node is added; the set is initiated with `rs.initiate()`; maintenance commands run (`rs.stepDown()`, `rs.reconfig()`); secondaries lose connectivity to primary for longer than `electionTimeoutMillis` (default 10s); or the primary detects it can see only a minority of voting members.

### 2.2 Election Protocol (pv1)

MongoDB uses Raft-based consensus (pv1): heartbeats every 2 seconds; if no heartbeat within 10s member is marked inaccessible; candidate runs dry election first; first member to receive majority of votes becomes primary.

### 2.3 Priority and Votes

- Higher-priority members call elections sooner. `priority: 0` members cannot become primary.
- Maximum 7 voting members, up to 50 total members.
- Non-voting members must have `priority: 0` and `votes: 0`.

### 2.4 Election Timing

| Metric | Default Value |
|---|---|
| `electionTimeoutMillis` | 10,000 ms |
| Heartbeat interval | 2,000 ms |
| Median election time | ~12 seconds |

---

## 3. Oplog Mechanics

### 3.1 What Is the Oplog

The oplog (`local.oplog.rs`) is a capped collection recording all write operations in idempotent format. Every member maintains its own oplog. Secondaries copy and apply entries from the primary's oplog.

### 3.2 Default Oplog Size

| Platform | Default | Min | Max |
|---|---|---|---|
| Unix/Windows (WiredTiger) | 5% free disk | 990 MB | 50 GB |
| macOS 64-bit | 192 MB | -- | -- |

### 3.3 Oplog Window

The **oplog window** is the time between the newest and oldest oplog entry. A secondary that falls behind more than the oplog window must perform a full initial sync.

```javascript
rs.printReplicationInfo()  // shows oplog size, time window, first/last timestamps
```

### 3.4 Configuring Oplog Size

```javascript
// Dynamic resize
db.adminCommand({ replSetResizeOplog: 1, size: 10240 })
// Minimum retention
db.adminCommand({ replSetResizeOplog: 1, minRetentionHours: 24 })
```

---

## 4. Write Concern

Write concern controls durability before the server acknowledges a write.

### 4.2 `w` Values

| Value | Behavior | Rollback Risk |
|---|---|---|
| `w: 0` | No acknowledgment | High |
| `w: 1` | Primary in-memory write | Moderate |
| `w: "majority"` | Majority of data-bearing voting members | None |
| `w: <n>` | Primary + (n-1) secondaries | Low |
| `w: "<tag>"` | Custom tagged write concern | Depends |

### 4.3 `j` (Journal) Option

- `j: true`: synced to on-disk journal before ack.
- `j: false`: in-memory ack only.
- With `w: "majority"`, controlled by `writeConcernMajorityJournalDefault` (default `true`).

### 4.4 `wtimeout`

Time limit (ms) for propagation. Does not undo applied writes on timeout. `0` = wait indefinitely.

### 4.5 Default Write Concern

MongoDB 5.0+: `{ w: "majority" }` for most deployments. Exception: P-S-A topologies default to `{ w: 1 }`.

### 4.7 Write Concern and Transactions

Set at transaction level, not per-operation:
```javascript
session.startTransaction({ writeConcern: { w: "majority" } });
```

---

## 5. Read Preference

| Mode | Where Reads Go | Use Case |
|---|---|---|
| `primary` | Primary only | Strongest consistency |
| `primaryPreferred` | Primary; secondary fallback | Near-fresh reads |
| `secondary` | Secondaries only | Analytics, reporting |
| `secondaryPreferred` | Secondaries; primary fallback | Read-heavy workloads |
| `nearest` | Lowest-latency member | Geo-distributed |

`maxStalenessSeconds` (min 90s) excludes secondaries lagging beyond threshold.

---

## 6. Read Concern

### 6.1 Levels

| Level | Guarantees | Rollback Risk | Transactions | Performance |
|---|---|---|---|---|
| `"local"` | Instance data; no majority guarantee | May roll back | Yes | Fastest |
| `"available"` | Like local; may return orphaned docs (sharded) | May roll back | No | Fastest |
| `"majority"` | Majority-acknowledged; durable | None | Yes | Comparable |
| `"linearizable"` | All majority-acknowledged writes before read | None | No | Slowest |
| `"snapshot"` | Majority-committed at single point in time | None (w:majority txn) | Yes | Comparable |

### 6.2 Consistency vs Availability Spectrum

```
Strongest consistency                              Highest availability
linearizable --> majority --> snapshot --> local --> available
```

### 6.4 Causal Consistency (summary)

Use `rc: "majority"` + `wc: "majority"` for causal consistency. MongoDB sets `afterClusterTime` automatically in causally consistent sessions. See §17 for full coverage.

---

## 7. Rollbacks

### 7.1 When Rollbacks Occur

A rollback reverts writes on a former primary when it rejoins after failover, when those writes had not replicated to a majority before the primary stepped down.

### 7.2 Rollback Algorithms

- **Recover-to-a-timestamp** (default, MongoDB 4.0+): reverts to consistent point, re-applies ops. No size limit.
- **Rollback via refetch** (legacy, only when `enableMajorityReadConcern=false`, fixed to `true` in 5.0+): limited to 300 MB.

### 7.3 Rollback Data Files

```bash
bsondump <dbpath>/rollback/<collectionUUID>/removed.<timestamp>.bson
```

### 7.4 Preventing Rollbacks

Use `{ w: "majority" }`. Enable journaling. Monitor replication lag. Avoid P-S-A topologies.

---

## 8. Replication Lag Diagnosis

```javascript
rs.printReplicationInfo()           // oplog size and window
rs.printSecondaryReplicationInfo()  // per-secondary lag in seconds
rs.status()                         // full status, optimeDate per member
```

Common causes: slow disk I/O, secondary read overload, index builds, network congestion, large bulk writes, long transactions.

**Flow control**: limits primary write rate to keep majority-committed lag under `flowControlTargetLagSeconds` (default 10s).

---

## 9. Initial Sync

Steps: database cloning → index building → oplog buffering → oplog application → SECONDARY state.

Ensure oplog window covers sync duration. Up to 10 retry attempts; 24h transient error window.

---

## 10. Change Streams Over Replica Sets

Every change event has a resume token (`_id`). Use `resumeAfter` to resume from a token; `startAfter` to resume even after invalidate events. Tokens expire when oplog entry is truncated.

MongoDB 6.0+: `fullDocumentBeforeChange` and `fullDocument: 'updateLookup'` for pre/post images (requires `changeStreamPreAndPostImages` on collection).

---

## 11. Replica Set Maintenance

```javascript
rs.stepDown()                        // trigger election
rs.add("host:27017")                 // add member (triggers initial sync)
rs.remove("host:27017")              // remove member
rs.reconfig(cfg)                     // reconfigure (one voting member change at a time)
rs.reconfig(cfg, { force: true })    // force reconfig (last resort; can cause rollbacks)
```

Rolling maintenance: maintain secondaries first, then `rs.stepDown()` and maintain former primary.

---

## 12. Anti-Patterns

| Anti-Pattern | Why Harmful | Recommendation |
|---|---|---|
| `w: 1` for critical writes | Data can roll back | Use `w: "majority"` |
| P-S-A in sharded clusters | Loss of secondary blocks majority writes | Use P-S-S |
| Ignoring oplog window | Secondaries need full resync | Monitor; set `oplogMinRetentionHours` |
| No `maxTimeMS` with linearizable reads | Can block indefinitely | Always set `maxTimeMS` |
| Force reconfig as routine | Can cause rollbacks | Use only when majority is down |
| Not monitoring replication lag | Silent staleness | Alert at 30-60s lag |

---

## 13. Troubleshooting Checklist

**Election not completing**: verify majority reachable (`rs.status()`), check `electionTimeoutMillis`, check for network partition.

**Replication lag**: `rs.printSecondaryReplicationInfo()`, check disk I/O, index builds (`db.currentOp()`), flow control (`serverStatus.flowControl`).

**Rollback occurred**: inspect `<dbpath>/rollback/`, check write concern used, `bsondump` rolled-back BSON.

**Initial sync failing**: verify oplog window size, disk space, sync source state, network connectivity.

---

## 14. Quick Reference Commands

```javascript
rs.initiate({ _id: "myRS", members: [{ _id: 0, host: "m1:27017" }, { _id: 1, host: "m2:27017" }, { _id: 2, host: "m3:27017" }] })
rs.status()
rs.conf()
rs.printReplicationInfo()
rs.printSecondaryReplicationInfo()
rs.stepDown()
rs.add("m4:27017")
rs.remove("m4:27017")
db.adminCommand({ replSetResizeOplog: 1, size: 20480 })
rs.status().writeMajorityCount
db.adminCommand({ replSetSyncFrom: "m2:27017" })
```

---

## 15. Cross-References

- **mongodb-expert**: General MongoDB architecture and operations.
- **mongodb-atlas-expert**: Atlas-managed replica sets and Atlas-specific settings.
- **mongodb-data-lifecycle**: Change streams deep coverage, CDC architectures, pre/post images.
- **mongodb-sharding**: Sharded cluster replication, config server replica sets, chunk migration.
- **mongodb-performance-troubleshooting**: Replication lag analysis, slow oplog application.
- **mongosync**: Inter-cluster replication — Atlas Live Migration, C2C Sync, active-passive DR.

---

## 16. Read Concern Deep Dive

### 16.1 Read Concern Levels Comparison

| Level | Reads From | May Return Rolled-Back Data | Available for Transactions | Primary Only | Performance Impact |
|---|---|---|---|---|---|
| `"local"` | Any node the driver is targeting | Yes | Yes | No | Minimal (default) |
| `"available"` | Any node (sharded: chunk owner regardless of metadata) | Yes | No | No | Minimal |
| `"majority"` | Majority-committed snapshot in memory | No | Yes | No | Low |
| `"linearizable"` | Primary only; waits for in-flight writes to commit | No | No | Yes | High (can block) |
| `"snapshot"` | Consistent point-in-time snapshot | No (if txn uses `w:majority`) | Yes (multi-doc txn) | No | Moderate |

**`"local"`**: Returns the most recent data on the targeted node with no majority confirmation. On a secondary, data may not yet be replicated to a majority of members and could be rolled back if the current primary fails before replication completes. This is the default for find, aggregate, and getMore operations.

**`"available"`**: Identical to `"local"` on replica set members. On sharded clusters it diverges: reads are served directly from the shard that owns the chunk without consulting config servers for up-to-date routing metadata. During chunk migrations this can return orphaned documents. Avoid on sharded collections for any consistency-sensitive reads.

**`"majority"`**: Returns only data acknowledged by a majority of data-bearing voting members and written to the majority-committed oplog point. Guaranteed durable; will never be rolled back. Requires WiredTiger (only storage engine since MongoDB 5.0).

**`"linearizable"`**: Strongest single-document consistency guarantee. Reads block until the server confirms no write started before the read is still in-flight at a majority. Always targets the primary. Must be combined with `maxTimeMS`. Cannot be used with `$out`, `$merge`, or multi-document transactions.

**`"snapshot"`**: Returns data from a consistent snapshot of majority-committed data at a single point in time. Primarily used in multi-document transactions. When a transaction commits with `w: "majority"`, the snapshot guarantee is preserved end-to-end.

### 16.2 Majority Read Concern Mechanics

MongoDB maintains an internal **majority-committed optime** — the oplog timestamp up to which a majority of data-bearing voting members have confirmed replication. The primary advances this by computing the highest optime for which `floor(votingMembers/2)+1` members have reported an optime >= that value, every heartbeat cycle (~2s).

WiredTiger maintains an in-memory read snapshot pegged to the majority-committed optime. `"majority"` reads access this snapshot directly — they do not block writes and add negligible latency in steady state.

The interaction with `w: "majority"` write concern is tight: a write acknowledged at `w: "majority"` has by definition advanced the majority-commit point to at least its optime. A subsequent read with read concern `"majority"` (`rc: "majority"`) on any node will therefore see that write — this is the foundation of the causal consistency guarantee. (`rc:` is used as shorthand for "read concern level" throughout §16–17.)

### 16.3 Linearizable vs Snapshot — When to Choose Each

**Choose `"linearizable"` when**:
- You need the absolute freshest majority-committed data for a single document.
- You are building a compare-and-swap or test-and-set operation.
- Always pair with `maxTimeMS` to bound the blocking window.

```javascript
const doc = await collection.findOne(
  { _id: userId },
  { readConcern: { level: 'linearizable' }, maxTimeMS: 5000 }
);
```

**Choose `"snapshot"` when**:
- You need a consistent view across multiple documents or collections within a transaction.
- You want point-in-time consistency without the primary-only restriction of `"linearizable"`.

```javascript
const session = client.startSession();
await session.startTransaction({ readConcern: { level: 'snapshot' }, writeConcern: { w: 'majority' } });
const orders = await ordersCollection.find({}, { session }).toArray();
const inventory = await inventoryCollection.find({}, { session }).toArray();
await session.commitTransaction();
await session.endSession();
```

**Key difference**: `"linearizable"` waits for in-flight writes before responding (most current possible). `"snapshot"` reads from a fixed point in time and does not wait.

### 16.4 Read Concern in Sharding — `"available"` vs `"local"` Divergence

| Behavior | `"local"` | `"available"` |
|---|---|---|
| Waits for chunk migration metadata consistency | No | No |
| Uses routing-aware shard selection | Yes — routes via mongos metadata | No — reads directly from chunk owner, bypasses metadata |
| Can return orphaned documents | No | **Yes** — during migrations, chunk owner may hold documents already moved |
| Replica set behavior | Identical to `"available"` | Identical to `"local"` |
| Recommended for sharded collections | Yes | No |

For sharded clusters, default to `"local"` or `"majority"`. `"available"` exists primarily as a performance optimization for non-sharded workloads.

### 16.5 Default Read Concern by Operation Type

| Operation | Default Read Concern | Can Override? |
|---|---|---|
| `find` | `"local"` | Yes |
| `aggregate` | `"local"` | Yes |
| `findOne` | `"local"` | Yes |
| `countDocuments` | `"local"` | Yes |
| `getMore` | Inherits cursor's original concern | No (set at cursor open) |
| Multi-document transaction | `"snapshot"` | Yes (set at `startTransaction`) |
| `watch` (change stream) | `"majority"` | Configurable |
| `distinct` | `"local"` | Yes |

### 16.6 Code Examples — Setting Read Concern

**Node.js (MongoDB Driver 6.x)**:
```javascript
// Per-operation
const docs = await collection.find({ status: 'active' }, { readConcern: { level: 'majority' } }).toArray();

// Client-level default
const client = new MongoClient(uri, { readConcernLevel: 'majority' });

// Transaction-level
const session = client.startSession();
await session.startTransaction({ readConcern: { level: 'snapshot' }, writeConcern: { w: 'majority' } });
```

**Python (PyMongo 4.x)**:
```python
from pymongo import ReadConcern, WriteConcern, MongoClient
client = MongoClient(uri)
db = client.mydb

# Per-operation via get_collection
coll = db.get_collection('orders', read_concern=ReadConcern(level='majority'))

# Transaction-level
with client.start_session() as session:
    with session.start_transaction(read_concern=ReadConcern('snapshot'), write_concern=WriteConcern(w='majority')):
        orders = list(db.orders.find({}, session=session))
```

**Java (MongoDB Driver 5.x)**:
```java
MongoCollection<Document> coll = db.getCollection("orders").withReadConcern(ReadConcern.MAJORITY);

ClientSession session = client.startSession();
TransactionOptions txnOptions = TransactionOptions.builder()
    .readConcern(ReadConcern.SNAPSHOT).writeConcern(WriteConcern.MAJORITY).build();
session.withTransaction(() -> {
    List<Document> orders = db.getCollection("orders").find(session).into(new ArrayList<>());
    return null;
}, txnOptions);
session.close();
```

---

## 17. Causal Consistency and Client Sessions

### 17.1 What Causal Consistency Means

Causal consistency guarantees that operations within a session (or across sessions sharing causal tokens) observe a logically consistent sequence of writes:

| Guarantee | Description |
|---|---|
| **Read your own writes** | After a write in a session, all subsequent reads see the write. |
| **Monotonic reads** | Reads never return older data than a previous read in the same session. |
| **Monotonic writes** | Writes are applied in the order they were issued. |
| **Writes follow reads** | A write after a read is guaranteed to occur after the read's observed state. |

MongoDB implements causal consistency through two logical clocks in every server response:
- **`$clusterTime`**: A hybrid logical clock (HLC) providing total ordering across the replica set. Every server response includes the current `$clusterTime`.
- **`operationTime`**: The optime of the most recent operation in the session. Clients send it as `afterClusterTime` on the next read.

When a read is issued with `afterClusterTime: T`, the server waits until its majority-committed optime >= T before executing, ensuring the read sees all writes up to time T.

### 17.2 Session Setup and Lifecycle

**Node.js driver session API**:
```javascript
const client = new MongoClient(uri);
await client.connect();

const session = client.startSession({ causalConsistency: true });
try {
  const db = client.db('mydb');

  const result = await db.collection('accounts').findOneAndUpdate(
    { _id: userId },
    { $inc: { balance: -100 } },
    { session, returnDocument: 'after' }
    // writeConcern must be set at client/collection level or transaction level, not per-operation
  );

  const account = await db.collection('accounts').findOne(
    { _id: userId },
    { session, readConcern: { level: 'majority' } }
  );

  console.log(session.clusterTime);   // current cluster time
  console.log(session.operationTime); // optime of last operation
} finally {
  await session.endSession();
  await client.close();
}
```

**Key session methods**:
- `session.advanceClusterTime(clusterTime)` — advance session cluster time (for cross-service token passing).
- `session.advanceOperationTime(operationTime)` — advance operation time (same purpose).
- `session.endSession()` — always call in a `finally` block.

### 17.3 Why Read Concern `"majority"` Is Required for Causal Consistency

With `"local"` read concern, `afterClusterTime` still runs but data returned may include not-yet-majority-committed writes that could be rolled back, breaking the causal chain.

With `"majority"`, data is from the permanent majority-committed snapshot. The causal chain holds because both write (`w: "majority"`) and read (`rc: "majority"`) anchor to the same majority-commit point.

`"linearizable"` also satisfies causal consistency but adds primary-only and in-flight-write-wait constraints — overkill for most causal use cases.

### 17.4 Causal Consistency Across Multiple Clients

```javascript
// Service A: write and return causal tokens
async function transferFunds(fromId, toId, amount) {
  const session = client.startSession({ causalConsistency: true });
  try {
    await db.collection('accounts').updateOne(
      { _id: fromId },
      { $inc: { balance: -amount } },
      { session }
      // writeConcern must be set at client/collection level, not per-operation
    );
    return { clusterTime: session.clusterTime, operationTime: session.operationTime };
  } finally {
    await session.endSession();
  }
}

// Service B: advance session from tokens, then read
async function getAccountBalance(accountId, causalTokens) {
  const session = client.startSession({ causalConsistency: true });
  try {
    session.advanceClusterTime(causalTokens.clusterTime);
    session.advanceOperationTime(causalTokens.operationTime);
    const account = await db.collection('accounts').findOne(
      { _id: accountId },
      { session, readConcern: { level: 'majority' } }
    );
    return account.balance;
  } finally {
    await session.endSession();
  }
}
```

**When this pattern is essential**: writing via one API service then reading via another; sequential user actions where step 2 must see step 1; reading your own writes from a secondary.

### 17.5 Python Driver — Causal Consistency Session

```python
from pymongo import MongoClient, ReadConcern, WriteConcern

client = MongoClient(uri)

with client.start_session(causal_consistency=True) as session:
    db = client.mydb
    db.accounts.update_one(
        {'_id': user_id}, {'$inc': {'balance': -100}},
        session=session, write_concern=WriteConcern(w='majority')
    )
    account = db.accounts.find_one(
        {'_id': user_id}, session=session, read_concern=ReadConcern('majority')
    )
    cluster_time = session.cluster_time
    operation_time = session.operation_time

# Cross-service: advance session to externally-supplied tokens
# (db = client.mydb is still accessible here — Python has no block scoping)
with client.start_session(causal_consistency=True) as session2:
    session2.advance_cluster_time(cluster_time)
    session2.advance_operation_time(operation_time)
    result = db.accounts.find_one(
        {'_id': user_id}, session=session2, read_concern=ReadConcern('majority')
    )
```

### 17.6 Implicit vs Explicit Sessions

Every MongoDB operation uses a session, even if you do not create one explicitly.

| Session Type | Description | Causal Consistency | Transaction Support |
|---|---|---|---|
| **Implicit** | Driver creates automatically per operation; not shared across calls | No | No |
| **Explicit** | Application creates via `startSession()`; passed explicitly to operations | Yes (opt-in) | Yes |

**Key implications**:
- Implicit sessions provide no causal ordering guarantees between operations.
- Explicit sessions maintain `clusterTime` and `operationTime` across all operations.
- Multi-document transactions always require an explicit session.
- Explicit sessions are lightweight — negligible cost for the duration of a request-response cycle. **Exception**: sessions with an active transaction hold a WiredTiger snapshot and should be kept short to avoid cache pressure (see §17.7). Always call `endSession()`.
- Implicit sessions are fine for fire-and-forget writes where read-your-writes is not required.

```javascript
// WRONG: may be served from different points in time
await collection.insertOne({ _id: 1, value: 'a' });   // implicit session A
const doc = await collection.findOne({ _id: 1 });      // implicit session B — may miss the insert

// CORRECT: explicit session
const session = client.startSession({ causalConsistency: true });
try {
  await collection.insertOne({ _id: 1, value: 'a' }, { session });
  const doc = await collection.findOne({ _id: 1 }, { session, readConcern: { level: 'majority' } });
} finally {
  await session.endSession();
}
```

### 17.7 Common Pitfalls

(`rc:` = read concern level shorthand used below.)

| Pitfall | Symptom | Fix |
|---|---|---|
| Using `rc: "local"` with causal sessions | Reads may miss own writes on secondaries after failover | Use `rc: "majority"` in causally consistent sessions |
| Not calling `endSession()` | Server-side session leak; exhausted session pool over time | Always use try/finally or context managers |
| Passing `clusterTime` without `operationTime` | Partial causal state; reads may skip some writes | Always pass both tokens together |
| Using implicit sessions for read-your-writes | Race condition: write on connection 1, read on connection 2 before replication | Use explicit session spanning both operations |
| Long-lived active transactions holding snapshots | Increased WiredTiger cache pressure from old snapshots | Keep transaction sessions short; commit or abort promptly |
