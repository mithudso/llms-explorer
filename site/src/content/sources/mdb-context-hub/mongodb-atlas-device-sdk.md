---
title: "MongoDB Atlas Device SDK"
description: "> DEPRECATION NOTICE — Critical Context for All Readers"
---

# MongoDB Atlas Device SDK & Edge Server

> **DEPRECATION NOTICE — Critical Context for All Readers**
>
> On **September 9, 2024**, MongoDB announced the deprecation of Atlas Device Sync + Realm SDKs. The sync service (Atlas Device Sync) reached **end-of-life on September 30, 2025**. The local Realm database library continues as an open-source project, but SDK versions 20.x and later no longer support cloud synchronization. Users who need mobile-to-cloud sync must migrate to alternatives.
>
> This skill documents the final architecture of the system because: (1) existing apps built on Realm/Device Sync still run in production and require support, (2) the Realm local database (without sync) is still viable open-source, and (3) the underlying patterns inform alternative architectures. All guidance is explicitly labeled by EOL status.

---

## When NOT to Use This Skill

Do not use this skill to guide **new greenfield project decisions**. Atlas Device Sync reached end-of-life on September 30, 2025 and is permanently shut down. Use this skill for:
- Supporting existing Realm/Device Sync production apps
- Advising on the EOL migration path for a current Realm customer
- Understanding the Realm local database (still viable open-source, sync-free)

For new mobile sync architectures, redirect to alternatives: PowerSync, Couchbase Mobile, Ditto, or custom HTTP sync over Atlas.

---

## Overview

MongoDB Atlas Device SDK was the official rebrand of the Realm SDK in 2023, completing the migration of Realm (acquired by MongoDB in 2019) into the Atlas platform family. The system comprised two layers:

1. **Realm local database** — an embedded, file-backed, reactive object store. Open-source (Apache 2.0). Continues to exist as a local database library without cloud sync.
2. **Atlas Device Sync** — a managed sync service inside Atlas App Services that bridged the on-device Realm to a MongoDB Atlas cluster via a binary WebSocket protocol. **Shut down September 30, 2025.**

**Atlas Edge Server** was a companion feature in public preview (May 2024) — a MongoDB process deployable at the edge (factory, retail, aircraft) that acted as an intermediate sync tier between device SDKs and Atlas. It was also deprecated before September 30, 2024.

---

## 1. SDK Language Matrix

MongoDB maintained official SDKs for seven language/platform targets:

| Language / SDK | Repository | Primary Platforms | Local DB | Sync Support (pre-EOL) |
|---|---|---|---|---|
| Swift | realm/realm-swift | iOS 16+, macOS 13+, tvOS 16+, watchOS 9+ | Yes | Yes (Flexible Sync) |
| Kotlin | realm/realm-kotlin | Android 8+ (API 26+), Kotlin Multiplatform | Yes | Yes (Flexible Sync) |
| Java | realm/realm-java | Android 5+ (API 21+) | Yes | Yes (Partition-Based only) |
| JavaScript / Node.js | realm/realm-js | React Native 0.71+, Node.js 18+ | Yes | Yes (Flexible Sync) |
| .NET / C# | realm/realm-dotnet | Xamarin, MAUI, .NET 6+ | Yes | Yes (Flexible Sync) |
| Flutter / Dart | realm/realm-dart | Flutter 3.10.2+ (iOS, Android, Win, macOS, Linux), Dart 3.0.2+ | Yes | Yes (Flexible Sync) |
| C++ | realm/realm-cpp | Linux, macOS, Windows (embedded-target support) | Yes | Yes (Flexible Sync) |

**Package identifiers:**
- Swift: `RealmSwift` (SPM: `realm-swift`), CocoaPods pod `RealmSwift`
- Kotlin: `io.realm.kotlin` — `library-base` (local) + `library-sync` (Device Sync)
- Java: `io.realm:realm-android` — Gradle plugin `realm-android`
- JavaScript: npm `realm` (was `realm@^12`)
- .NET: NuGet `Realm` + `Realm.Fody`
- Flutter/Dart: pub.dev `realm` (v20.x current), `realm_generator`
- C++: header-only via CPM/cmake

**Version compatibility with Atlas App Services:** Device Sync required Atlas App Services. The SDK connected to an App Services "application" identified by its App ID (e.g., `myapp-abcde`). The App Services endpoint was `https://realm.mongodb.com` with WebSocket sync over `wss://ws.realm.mongodb.com`.

---

## 2. Realm Object Model

### 2.1 Defining Objects

**Swift (`@Persisted` wrapper, SDK 10+):**
```swift
class Task: Object {
    @Persisted(primaryKey: true) var _id: ObjectId = ObjectId.generate()
    @Persisted var title: String = ""
    @Persisted var completed: Bool = false
    @Persisted var tags: List<String>
    @Persisted var assignee: User?
}
class Subtask: EmbeddedObject {
    @Persisted var name: String = ""
    @Persisted var done: Bool = false
}
```

**Kotlin:**
```kotlin
class Task : RealmObject {
    @PrimaryKey var _id: ObjectId = ObjectId.create()
    var title: String = ""
    var tags: RealmList<String> = realmListOf()
}
class Subtask : EmbeddedRealmObject { var name: String = "" }
```

**Flutter/Dart:**
```dart
@RealmModel()
class _Task {
  @PrimaryKey() late ObjectId id;
  late String title;
  bool completed = false;
  List<String> tags = [];
}
```
Generate: `dart run realm generate`

### 2.2 Supported Property Types

| Realm Type | Swift | Kotlin | JavaScript |
|---|---|---|---|
| Boolean | `Bool` | `Boolean` | `bool` |
| String | `String` | `String` | `string` |
| Date | `Date` | `RealmInstant` | `date` |
| ObjectId | `ObjectId` | `ObjectId` | `objectId` |
| UUID | `UUID` | `RealmUUID` | `uuid` |
| Decimal128 | `Decimal128` | `BsonDecimal128` | `decimal128` |
| Mixed/Any | `AnyRealmValue` | `RealmAny` | `mixed` |
| List | `List<T>` | `RealmList<T>` | `T[]` |
| Set | `MutableSet<T>` | `RealmSet<T>` | `set<T>` |
| Dictionary | `Map<String,T>` | `RealmDictionary<T>` | `dictionary<T>` |

### 2.3 Primary Keys

- `@PrimaryKey` (Kotlin) / `primaryKey: true` in `@Persisted` (Swift) / `@PrimaryKey()` (Dart)
- For Device Sync: field **must** be named `_id`
- Primary keys are immutable once written to a synced realm

### 2.4 Relationships

| Type | Mechanism |
|---|---|
| To-one optional | Nullable object property |
| To-many | `RealmList<T>` |
| Unique set | `RealmSet<T>` |
| Key-value | `RealmDictionary<T>` (string keys only) |
| Backlink | `@Backlinks` (Swift) / `linkingObjects()` (Kotlin) — computed, not stored |
| Embedded | `EmbeddedObject` — lifecycle bound to parent, no independent `_id` |

### 2.5 Schema Migration

```swift
let config = Realm.Configuration(schemaVersion: 4, migrationBlock: { migration, oldVersion in
    if oldVersion < 3 { migration.renameProperty(onType: "Task", from: "name", to: "title") }
    if oldVersion < 4 { migration.enumerateObjects(ofType: "Task") { _, new in new!["completed"] = false } }
})
```

Strategies: incremental block (production), `deleteRealmIfMigrationNeeded` (dev only), additive fields (no block needed).

---

## 3. Atlas Device Sync — Flexible Sync

> **Status: EOL September 30, 2025.**

### 3.1 Architecture

```
Device (Realm DB) ←─WebSocket TLS 443─→ App Services Sync Server ←─→ MongoDB Atlas
     ↕ local writes / change log               ↕ conflict resolution + fan-out
```

### 3.2 Flexible Sync vs Partition-Based Sync

| Feature | Flexible Sync | Partition-Based |
|---|---|---|
| Data selection | RQL query subscriptions | Partition key match |
| Cross-collection queries | Supported | Not supported |
| Status | Recommended (was) | Legacy |

### 3.3 Subscriptions

```swift
// Swift — add/update subscriptions
try await realm.subscriptions.update {
    subs.append(QuerySubscription<Task>(name: "my-tasks") { $0.assigneeId == user.id })
}
```

```kotlin
// Kotlin — shorthand (SDK 1.10+)
val tasks = realm.query<Task>("assigneeId == $0", user.id)
    .subscribe(name = "my-tasks", updateExisting = true)

// Manual SubscriptionSet API
realm.subscriptions.update {
    add(realm.query<Task>("assigneeId == $0", user.id), name = "my-tasks")
}
```

Queryable fields must be declared in App Services UI — only top-level primitives, lists, sets eligible.

### 3.4 Sync Session Management

```swift
let session = realm.syncSession!
session.suspend(); session.resume()
// Connection states: .disconnected / .connecting / .connected
```

### 3.5 Offline-First Behavior

1. Reads/writes succeed immediately against local Realm file
2. Writes append to internal upload queue
3. On reconnect: upload queue replayed to server, server changes replayed locally
4. Conflicts resolved by sync engine before applying
5. Automatic reconnection with exponential backoff

### 3.6 Asymmetric Sync (Data Ingest)

Write-only mode for high-volume insert-only workloads (IoT telemetry, GPS, audit events). Objects are deleted from device after sync; cannot be queried/updated.

```kotlin
class SensorReading : AsymmetricRealmObject {
    @PrimaryKey var _id: ObjectId = ObjectId.create()
    var deviceId: String = ""
    var temperature: Double = 0.0
    var timestamp: RealmInstant = RealmInstant.from(System.currentTimeMillis() / 1000, 0)
}
realm.write { insert(SensorReading().apply { deviceId = "s-001"; temperature = 23.4 }) }
```

---

## 4. Atlas Edge Server

> **Status: Deprecated before September 30, 2024.**

Middle tier between Device SDK clients and Atlas for intermittent-WAN environments.

**Architecture:**
```
[Device SDK clients] ←─LAN Device Sync─→ [Edge Server (mongod+sync)] ←─WAN─→ [MongoDB Atlas]
```

**vs Direct Atlas Sync:**

| Factor | Direct Atlas | Via Edge Server |
|---|---|---|
| WAN requirement | Always | Optional |
| Local latency | Atlas region | Sub-millisecond |
| WAN outage | Apps offline | Apps continue |

**Deployment (Docker):**
```yaml
services:
  edge-server:
    image: mongodb/mongodb-atlas-edge-server:latest
    environment: { APPSERVICES_APP_ID: your-app-id, REGISTRATION_TOKEN: your-token }
    ports: ["27021:27021", "27020:27020"]
```

**SDK connection to Edge Server:**
```swift
let app = App(id: "your-app-id", configuration: AppConfiguration(baseURL: "http://192.168.1.10:27021"))
```

**Admin API (port 27020):** `GET /api/edge/v1.0/info`, `GET /api/edge/v1.0/connection`, `POST /api/edge/v1.0/pause|resume`

---

## 5. Migration Paths

### 5.1 Realm API → Atlas Device SDK API

| Area | Old | New |
|---|---|---|
| Swift property | `@objc dynamic var title: String = ""` | `@Persisted var title: String = ""` |
| Swift primary key | `override static func primaryKey()` | `@Persisted(primaryKey: true)` |
| Swift concurrency | Callback-based | `async/await` (RealmSwift 10.x, Xcode 13+) |
| Kotlin class | `open class Task : RealmObject()` | `class Task : RealmObject` |
| Kotlin sync config | `SyncConfiguration.defaultConfig(user, partitionValue)` | `SyncConfiguration.Builder(user, schema).build()` |

### 5.2 Migrating Off Device Sync (EOL)

| Alternative | Notes |
|---|---|
| Realm local DB only (v20.x+) | Remove sync; offline-only use case |
| Custom HTTP sync over Atlas | Full control; significant engineering |
| Couchbase Mobile | Closest architectural match; migration tooling available |
| PowerSync | Supports MongoDB Atlas as upstream |
| Ditto | P2P sync; strong for low-connectivity |
| WatermelonDB | JS/React Native focus |

### 5.3 Timeline

| Date | Event |
|---|---|
| 2019 | MongoDB acquires Realm |
| Feb 2023 | Realm SDK renamed to Atlas Device SDK |
| May 2024 | Atlas Edge Server enters public preview |
| Sep 9, 2024 | Deprecation announced |
| Pre-Sep 30, 2024 | Atlas Edge Server deprecated |
| Sep 30, 2025 | Atlas Device Sync EOL; sync shut down |

---

## 6. Authentication Providers

| Provider | Credential |
|---|---|
| Anonymous | `Credentials.anonymous()` |
| Email/Password | `Credentials.emailPassword(email, password)` |
| API Key | `Credentials.userAPIKey(key)` |
| Custom JWT | `Credentials.jwt(token)` |
| Google OAuth | `Credentials.google(authCode:)` |
| Apple Sign-In | `Credentials.apple(idToken:)` |
| Facebook | `Credentials.facebook(accessToken:)` |
| Custom Function | `Credentials.function(payload:)` |

**Token management:**
- Access tokens expire after 30 minutes; SDK auto-refreshes using refresh token
- Refresh tokens expire after 60 days (configurable); user must re-authenticate on expiry
- Stored in browser `localStorage`/`sessionStorage` (Web SDK) or device secure keystore (mobile)

**Identity linking:**
```swift
try await anonymousUser.linkUser(credentials: .emailPassword(email: "u@example.com", password: "pw"))
// Same user._id retained; anonymous data preserved
```

---

## 7. Conflict Resolution

### 7.1 Operational Transformation

Uses OT (not CRDT). Last-write-wins for scalars by server timestamp. List operations preserve intent of both writes where possible.

Custom resolvers are not supported at field level. Influence conflict behavior via:
1. **Asymmetric sync** — no conflict possible (write-only)
2. **Embedded objects** — parent subtree treated atomically
3. **Server-side Atlas Triggers** — reactive post-sync reconciliation
4. **Schema design** — append to lists rather than update indexes

### 7.2 Client Reset Strategies

| Strategy | Behavior | Data Loss Risk |
|---|---|---|
| `recoverUnsyncedChanges` (default) | Re-applies local changes after fresh server state download | Low |
| `recoverOrDiscardUnsyncedChanges` | Recovery attempted; discards on failure | Medium |
| `discardUnsyncedChanges` | Local replaced with server state | High |
| `manual` | App controls the reset | None |

```swift
var config = user.flexibleSyncConfiguration(
    clientResetMode: .recoverOrDiscardUnsyncedChanges(
        beforeReset: { realm in /* backup */ },
        afterReset: { before, after in /* merge critical data */ }
    )
)
```

### 7.3 Conflict Design Patterns

- Append to lists rather than update indexed positions
- Use `@MapTo` (Java/legacy Kotlin) or `@PersistedName` (modern Kotlin SDK) for canonical Atlas field names
- Prefer embedded objects for sub-documents (atomic parent update)
- High-frequency telemetry → asymmetric sync (no conflict surface)

---

## 8. Performance and Battery

### 8.1 Memory: Lazy Loading

Realm objects are live, memory-mapped — zero-copy pointer arithmetic. Property access reads only accessed pages. Keep results as `Results<T>` / `RealmResults<T>` for UI binding; avoid materializing to `Array`/`List` unless serializing.

### 8.2 Transactions

One `realm.write {}` = one ACID commit. Batch all related writes in a single transaction:
```swift
try realm.write { for item in items { realm.add(item) } }  // 1 flush vs N flushes
```

### 8.3 Thread Model

Realm instances are per-thread. Cross-thread options:
- **Frozen objects** — `.freeze()` returns immutable snapshot; safe to pass across threads; no auto-update
- **ThreadSafeReference** — pass reference, resolve on target thread's Realm instance
- **Config** — always thread-safe; open new Realm from config on each background thread

### 8.4 Sync Optimization

- Pause sync during bulk local ops: `session.suspend()` / `session.resume()`
- Fine-grained subscriptions — never `objects('Task')` on large collections without a predicate
- `downloadBeforeOpen: .never` for immediate open from cache
- `shouldCompactOnLaunch` (Swift) / `compactOnLaunch()` (Kotlin) to reduce file size

---

## 9. Data Access Patterns

### 9.1 Live Queries

```swift
token = realm.objects(Task.self).filter("completed == false").observe { changes in
    switch changes {
    case .update(_, let deletions, let insertions, let modifications): /* update table view */
    default: break
    }
}
// token.invalidate() in deinit
```

```kotlin
realm.query<Task>("completed == false").asFlow().collect { changes ->
    when (changes) {
        is InitialResults, is UpdatedResults -> adapter.submitList(changes.list)
    }
}
```

### 9.2 Offline-First Pattern

```
UI ↕ live queries → Realm (local cache) ←── sync ──→ Atlas (source of truth)
                                                           ↓
                                                   Atlas Charts / Search / Aggregation
```

Open immediately from cache, sync in background:
```swift
// NOTE: try! for brevity — use try/catch in production
let realm = try! await Realm(configuration: config, downloadBeforeOpen: .never)
```

### 9.3 SwiftUI Integration

```swift
struct TaskListView: View {
    @ObservedResults(Task.self, filter: NSPredicate(format: "completed == false")) var tasks
    var body: some View {
        List { ForEach(tasks) { task in Text(task.title) }.onDelete { $tasks.remove(atOffsets: $0) } }
    }
}
```

### 9.4 React Native (`@realm/react`)

```javascript
import { RealmProvider, useQuery } from '@realm/react';
// Wrap app in <RealmProvider schema={[TaskSchema]}>
function TaskList() {
    const tasks = useQuery(Task, c => c.filtered('completed == false').sorted('dueDate'));
    return <FlatList data={tasks} renderItem={/* ... */} />;
}
```

---

## 10. Flutter/Dart SDK

### 10.1 Setup

```yaml
dependencies:
  realm: ^20.0.0
dev_dependencies:
  realm_generator: ^20.0.0
  build_runner: ^2.4.0
```
Dart 3.0.2+, Flutter 3.10.2+

### 10.2 Model and Code Generation

```dart
@RealmModel()
class _Task {
  @PrimaryKey() late ObjectId id;
  late String title;
  bool completed = false;
  List<String> tags = [];
  @Backlink(#owner) late Iterable<_Subtask> subtasks;
}
```
```bash
dart run realm generate          # one-time
dart run realm generate --watch  # watch mode
```
Commit generated `*.realm.dart` files.

### 10.3 CRUD

```dart
// Insert
realm.write(() => realm.add(Task(ObjectId(), 'Buy groceries')));
// Update
realm.write(() => task.completed = true);
// Delete
realm.write(() => realm.delete(task));
// Batch
realm.write(() { for (final item in items) { realm.add(item); } });
```

### 10.4 Queries (RQL — same across all SDKs)

```dart
final tasks = realm.all<Task>().query('completed == false SORT(dueDate ASC)');
final mine = realm.all<Task>().query(r'ownerId == $0', [userId]);
```

### 10.5 Live Streams

```dart
realm.all<Task>().query('completed == false').changes.listen((changes) {
    print('Inserted: ${changes.inserted}, Modified: ${changes.modified}');
});
```

### 10.6 Flexible Sync (EOL Reference)

```dart
final config = Configuration.flexibleSync(user, [Task.schema]);
final realm = await Realm.open(config);
await realm.subscriptions.update((subs) {
    subs.add(realm.all<Task>().query(r'ownerId == $0', [user.id]), name: 'user-tasks');
});
await realm.subscriptions.waitForSynchronization();
```

### 10.7 Platform Notes

- **iOS:** CocoaPods v1.11+ required; `pod install` after adding realm
- **Android:** AAR included automatically; no manual NDK config needed
- **macOS/Win/Linux:** Pre-compiled x64 binaries; Apple Silicon supported from realm v10+
- **Dart isolates:** Open a new Realm instance per isolate from the same configuration

---

## References

- [Atlas Device SDK Docs](https://www.mongodb.com/docs/atlas/device-sdks/)
- [Client Resets](https://www.mongodb.com/docs/atlas/app-services/sync/error-handling/client-resets/)
- [Authentication Providers](https://www.mongodb.com/docs/atlas/app-services/authentication/)
- [realm pub.dev](https://pub.dev/packages/realm)
- [realm-dart GitHub](https://github.com/realm/realm-dart)
- [realm-kotlin GitHub](https://github.com/realm/realm-kotlin)
- [Atlas Device Sync EOL Forum Post](https://www.mongodb.com/community/forums/t/atlas-device-sync-end-of-life-and-deprecation/296687)
- [PowerSync Migration Guide](https://docs.powersync.com/migration-guides/atlas-device-sync)

## See Also

- [[mongodb-realm-mobile-sync]] — Legacy Realm patterns, Partition-Based Sync, CRDT details, production pitfalls
- [[mongodb-atlas-app-services]] — App Services platform: auth, rules, triggers — including post-EOL status
- [[mongodb-atlas-triggers-functions]] — Atlas Triggers and Functions that remain active post-September 2025
