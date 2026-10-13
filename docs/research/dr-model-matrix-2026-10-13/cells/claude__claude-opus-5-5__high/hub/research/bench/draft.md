---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/claude__claude-opus-5-5__high/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:44:54Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:42:12Z", "updatedAt": "2026-10-13T06:44:54Z"} -->

## Overview

A checkpoint copies committed transactions from the -wal file back into the main SQLite database file. It also lets the WAL restart from the beginning. By default every connection runs a PASSIVE auto-checkpoint after a commit that leaves 1000 or more frames in the WAL. Applications can call sqlite3_wal_checkpoint_v2() or PRAGMA wal_checkpoint with one of five modes: PASSIVE, FULL, RESTART, TRUNCATE or NOOP. The modes trade blocking for guarantees. If readers always overlap, PASSIVE checkpoints cannot finish, and the WAL grows without bound. This failure is called checkpoint starvation. A checkpoint does not shrink the -wal file unless journal_size_limit is set or TRUNCATE mode runs. Checkpoint frequency trades read performance against write throughput. Production tools such as Litestream and Syncthing build tiered passive-first strategies to bound WAL size.

## Core Concepts

### SQLite WAL checkpointing

- A checkpoint moves transactions from the WAL file back into the main database file. The last connection to close a database runs one final checkpoint and then deletes the WAL file and the shared-memory wal-index file.[^c1-1][^c1-2]
- Every new database connection has auto-checkpoint enabled with a threshold of 1000 pages (or the compile-time SQLITE_DEFAULT_WAL_AUTOCHECKPOINT). The check runs after a commit, on the thread that did the COMMIT. All automatic checkpoints are PASSIVE. Setting PRAGMA wal_autocheckpoint to zero or a negative value disables it.[^c1-4][^c1-3][^c1-1]
- PASSIVE checkpoints as many frames as possible without waiting for readers or writers and never invokes the busy handler. FULL waits for no writer and for all readers to be on the latest snapshot, then checkpoints all frames; it blocks new writers but not readers. RESTART does FULL and then waits until no reader uses the WAL, so the next writer restarts the log from the beginning. TRUNCATE does RESTART and then truncates the WAL file to zero bytes. NOOP checkpoints nothing and only returns the counters.[^c1-2][^c1-3]
- Every checkpoint takes an exclusive checkpoint lock. If another connection is already checkpointing, the call returns SQLITE_BUSY immediately without invoking the busy handler. FULL, RESTART and TRUNCATE also take the writer lock; if the busy handler gives up, the call degrades to PASSIVE behaviour and returns SQLITE_BUSY.[^c1-2][^c1-3]
- A normal checkpoint does not shrink the -wal file. SQLite reuses the file from the beginning because overwriting is faster than appending. Only a TRUNCATE checkpoint or a journal_size_limit (default -1, meaning no limit; checked at each WAL reset) reduces the file's on-disk size.[^c1-1][^c1-3][^c1-5]

## Tools & Frameworks

- sqlite3_wal_autocheckpoint() is a wrapper around sqlite3_wal_hook(). Registering a custom callback with sqlite3_wal_hook() disables the built-in auto-checkpoint, and calling sqlite3_wal_autocheckpoint() replaces any custom hook.[^c1-4][^c1-1] _(SQLite WAL checkpointing)_
- PRAGMA wal_checkpoint returns one row with three integers: busy (1 if a FULL, RESTART or TRUNCATE checkpoint was blocked), the number of frames in the WAL, and the number of frames checkpointed. The C API returns the same counts through *pnLog and *pnCkpt, or -1 when the database is not in WAL mode.[^c1-3][^c1-2] _(SQLite WAL checkpointing)_
- Tentative: Litestream uses three checkpoint tiers: a PASSIVE checkpoint at 1000 WAL pages (min-checkpoint-page-count), a PASSIVE checkpoint every 1 minute (checkpoint-interval), and an emergency tier at 121,359 pages (about 500 MB, truncate-page-n). Since v0.5.15 the emergency tier tries PASSIVE first and forces a blocking TRUNCATE only if the WAL stays above the threshold. verified-as-of: 2026-10-13[^c1-5] _(SQLite WAL checkpointing)_

## Methodology

_(none recorded)_

## Practical Patterns

- Checkpoint frequency trades read performance against write performance. Read performance degrades as the WAL grows, so frequent checkpoints help readers. Infrequent checkpoints amortise sync and seek cost over more writes, which helps write throughput. (two sources)[^c1-1][^c1-8] _(SQLite WAL checkpointing)_
- A common pattern is to disable auto-checkpoint on request connections and run checkpoints from a separate thread or process. With synchronous=NORMAL, only checkpoints issue fsync, so moving checkpoints off the main thread removes sync stalls from it. (two sources)[^c1-1][^c1-6] _(SQLite WAL checkpointing)_
- Tentative: Large checkpoints that land on the request path can spike p99 latency. Practitioners advise against checkpointing per request and suggest TRUNCATE checkpoints in low-traffic windows or after batch jobs, with busy_timeout around 5000 ms. verified-as-of: 2026-09-15[^c1-8] _(SQLite WAL checkpointing)_
- Tentative: The experimental wal2 journal mode, on a separate SQLite branch, uses two WAL files (-wal and -wal2) that writers alternate between, so one file can be checkpointed while the other takes writes. This bounds WAL size even if the checkpointer never runs uninterrupted. Only builds from that branch can open a wal2 database; others return SQLITE_NOTADB. verified-as-of: 2026-10-13[^c1-7] _(SQLite WAL checkpointing)_

## Anti-Patterns

- Checkpoint starvation: a checkpoint cannot copy past frames that an open read transaction still needs, and the WAL cannot be reset while any reader uses it. If readers always overlap, no checkpoint completes and the WAL grows without bound. SQLite suggests leaving reader gaps or using RESTART or TRUNCATE checkpoints.[^c1-1][^c1-6][^c1-5] _(SQLite WAL checkpointing)_
- A forced TRUNCATE checkpoint waits for all active readers and holds the writer lock, so long-lived read transactions turn it into a writer stall. Litestream recommends truncate-page-n: 0 plus disk monitoring for applications with long reads. (two sources) verified-as-of: 2026-10-13[^c1-5][^c1-2] _(SQLite WAL checkpointing)_

## Troubleshooting

- If auto-checkpoint stays enabled alongside an application checkpointer, the two compete for the exclusive checkpoint lock. Syncthing identified this as one cause of its WAL starvation and proposed triggering checkpoints when the connection pool releases a connection instead of on a timer. (two sources) verified-as-of: 2026-02-06[^c1-6][^c1-2] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): A 2026 practitioner blog presents wal_autocheckpoint=1000 as preventing unbounded WAL growth. SQLite's own docs say auto-checkpoints are PASSIVE and cannot complete while readers always overlap, so the default threshold alone does not prevent checkpoint starvation.[^c1-8][^c1-1][^c1-4]
- Disagreement (SQLite WAL checkpointing): SQLite docs suggest RESTART or TRUNCATE checkpoints as a remedy for starvation. Litestream warns that a forced TRUNCATE under long-lived readers stalls writers and recommends disabling its emergency TRUNCATE tier for long-read apps.[^c1-1][^c1-5]
- Open (SQLite WAL checkpointing): Whether the wal2 branch (or the related begin-concurrent/hctree work) has moved toward trunk or a release since 2020-era statements that it was not production-ready; the fetched wal2 doc gives no status.
- Open (SQLite WAL checkpointing): Whether Syncthing merged its proposed pool-release checkpoint trigger and in which version; the forum thread lists proposals only.
- Open (SQLite WAL checkpointing): No measured latency data was found for FULL/RESTART/TRUNCATE checkpoint stalls; the p99 claim is unquantified.

## References

### SQLite WAL checkpointing

[^c1-1]: https://sqlite.org/wal.html — SQLite Write-Ahead Logging (updated 2026-08-25) (docs)
[^c1-2]: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — sqlite3_wal_checkpoint_v2 (docs)
[^c1-3]: https://www.sqlite.org/pragma.html — SQLite PRAGMA statements (docs)
[^c1-4]: https://www.sqlite.org/c3ref/wal_autocheckpoint.html — sqlite3_wal_autocheckpoint (docs)
[^c1-5]: https://litestream.io/guides/wal-truncate-threshold/ — Litestream WAL Truncate Threshold Configuration (docs)
[^c1-6]: https://forum.syncthing.net/t/dealing-with-checkpoint-starvation/26121 — Syncthing forum: Dealing with checkpoint starvation (2026-02-06) (forum)
[^c1-7]: https://sqlite.org/src/doc/wal2/doc/wal2.md — SQLite wal2 branch doc (docs)
[^c1-8]: https://www.kunalganglani.com/blog/sqlite-production-api-wal.md — SQLite Production API Concurrency: WAL Mode Limits (2026-09-15) (blog)
