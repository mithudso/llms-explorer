---
title: "MongoDB Realm Mobile Sync"
description: "> CRITICAL: Atlas Device Sync reached end-of-life September 30, 2025."
---

# MongoDB Realm and Atlas Device Sync (EOL)

> **CRITICAL: Atlas Device Sync reached end-of-life September 30, 2025.**
> All Device Sync and Device SDK features were shut down on that date.
> This skill provides historical context for customers still migrating away.

## What Was Realm / Atlas Device Sync

Realm was a mobile-first database SDK with:
- **Realm Database (local):** Embedded object database for iOS/Android (still available as standalone open-source)
- **Atlas Device Sync:** Cloud sync between Realm local database and MongoDB Atlas (EOL Sep 30 2025)
- **Device SDKs:** Swift, Kotlin, Java, Flutter, React Native, .NET, JavaScript (web)

## EOL Timeline

| Date | Event |
|---|---|
| January 2023 | Atlas Device Sync deprecation announced |
| September 30, 2025 | Atlas Device Sync shut down |
| September 30, 2025 | All Device SDK sync features ceased |
| Ongoing | Realm Database (local, no sync) remains open-source |

## What Was Flexible Sync (Last Supported Mode)

Flexible Sync replaced Partition-Based Sync as the final architecture:
- Subscriptions defined per-client based on query (e.g., `realm.query<Task>().where("userId == $0", userId)`)
- Server-side rules enforced permissions on which documents each client could sync
- Offline-first: writes to local Realm database, synced when online

## Migration Paths (Post-EOL)

| Original use case | Recommended replacement |
|---|---|
| Mobile app offline-first with MongoDB | Custom sync layer (WebSocket / SSE / polling) + MongoDB driver |
| iOS app with Realm local database | Continue using Realm Database (standalone, no sync) or SQLite/SwiftData |
| Android app with Realm local database | Continue using Realm Database or Room/SQLite |
| Flutter offline-first | ObjectBox, Drift (SQLite), or Isar Database |
| React Native offline-first | WatermelonDB, MMKV + custom sync, or PouchDB + CouchDB |
| Multi-device real-time sync | Firebase Realtime Database, Supabase Realtime, or custom WebSocket layer |

## Realm Database (Local — Still Available)

The local Realm Database (without sync) remains available as open-source:
- [realm-swift](https://github.com/realm/realm-swift) — iOS/macOS Swift/Objective-C
- [realm-kotlin](https://github.com/realm/realm-kotlin) — Android/Kotlin Multiplatform
- [realm-js](https://github.com/realm/realm-js) — Node.js, React Native
- [realm-dotnet](https://github.com/realm/realm-dotnet) — .NET/Xamarin

Use Realm local database for: fast local embedded storage without cloud sync requirements.

## Common Migration Scenarios

### Migrating Change Listeners to MongoDB Change Streams

What was a Realm change listener:
```swift
// Old Realm sync pattern
let tasks = realm.objects(Task.self)
let token = tasks.observe { changes in
    // Handle changes
}
```

Replace with a MongoDB change stream consumer in your backend:
```javascript
// Backend: publish changes to mobile clients via SSE or WebSocket
const changeStream = db.tasks.watch(
  [{ $match: { "fullDocument.userId": userId } }],
  { fullDocument: "updateLookup" }
);
for await (const change of changeStream) {
  sse.send(change);  // Push to mobile client via SSE
}
```

### Migrating Offline-First Writes

```javascript
// Mobile: write to local store (MMKV, SQLite, etc.)
localDB.insert({ _id: uuid(), taskName: "Buy milk", synced: false });

// Background sync worker: push unsynced records to Atlas
const unsynced = localDB.query("SELECT * FROM tasks WHERE synced = 0");
for (const record of unsynced) {
  await mongodbApi.post('/tasks', record);
  localDB.update(record.id, { synced: 1 });
}
```

### Migrating Atlas App Services Authentication

Atlas App Services Authentication providers were also EOL'd September 30, 2025. Migrate to:
- **Auth0** — drop-in OIDC replacement with mobile SDKs
- **Firebase Auth** — Google's mobile auth platform
- **AWS Cognito** — AWS-native mobile auth
- **Clerk** — Modern developer auth platform

## Deprecation References

- [Atlas Device Sync EOL Forum Post](https://www.mongodb.com/community/forums/t/atlas-device-sync-end-of-life-and-deprecation/296687)
- [Realm SDK Migration Guide](https://www.mongodb.com/docs/atlas/app-services/deprecation/)
- [Realm Database GitHub (standalone)](https://github.com/realm/realm-swift)

## See Also

For active MongoDB skills:
- `mongodb-change-streams` — Real-time event streaming from MongoDB to applications
- `mongodb-atlas-triggers-functions` — Server-side event processing (still active)
- `mongodb-atlas-app-services` — Full EOL context and migration guidance
