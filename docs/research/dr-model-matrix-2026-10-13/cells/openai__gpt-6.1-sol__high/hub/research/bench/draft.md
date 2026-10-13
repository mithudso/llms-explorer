---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/openai__gpt-6.1-sol__high/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:46:11Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:42:18Z", "updatedAt": "2026-10-13T06:46:11Z"} -->

## Overview

Checkpointing copies eligible committed page changes from SQLite's write-ahead log into the main database. Copying, restarting the log, and truncating its allocated file are distinct operations. Automatic PASSIVE checkpoints favor concurrency; stronger modes wait for the conditions needed to complete copying or restart the WAL. Long-lived reader snapshots can limit progress and permit continued WAL growth. Applications should inspect checkpoint status and frame counts, keep reader transactions short, and choose checkpoint scheduling around their latency and durability requirements. A large allocated WAL alone does not prove checkpoint failure. Recent SQLite documentation also identifies a rare, fixed race between checkpointing and WAL reset.

## Core Concepts

### SQLite WAL checkpointing

- Checkpointing transfers eligible committed page changes from the WAL into the main database; copying pages and resetting the WAL are separate steps.[^c1-1][^c1-4][^c1-5]
- PASSIVE checkpoints copy as many frames as possible without waiting for readers or writers and never invoke the busy handler; concurrent activity can leave copying incomplete. (two sources)[^c1-2][^c1-3]

## Tools & Frameworks

- The default auto-checkpoint threshold is 1000 WAL pages, configurable at compilation or through wal_autocheckpoint. Automatic checkpoints are PASSIVE; a nonpositive runtime threshold disables them. The threshold is not a hard file-size cap. (two sources)[^c1-1][^c1-3] _(SQLite WAL checkpointing)_
- FULL waits for the writer and older reader snapshots before copying all frames. RESTART additionally waits for readers to stop using the WAL so the next writer can reuse its beginning. TRUNCATE additionally reduces the WAL to zero bytes on success. These modes block writers while allowing readers to proceed. (two sources)[^c1-2][^c1-3] _(SQLite WAL checkpointing)_

## Methodology

- PRAGMA wal_checkpoint returns busy status, total WAL frames, and total checkpointed frames. A PASSIVE result with busy status zero can still be incomplete; compare frame counts. Counts are -1 outside WAL mode and zero after successful TRUNCATE. (two sources)[^c1-3][^c1-2] _(SQLite WAL checkpointing)_

## Practical Patterns

- Tentative: Automatic checkpoint work runs in the committing thread and can lengthen occasional commits. Applications can disable it and schedule checkpoints in another thread or process, assuming responsibility for continued checkpoint progress.[^c1-1] _(SQLite WAL checkpointing)_
- With synchronous=NORMAL, WAL synchronization occurs before checkpoints and database synchronization after completed checkpoints. Unlike FULL's per-commit WAL sync, NORMAL can lose committed transactions after power loss or a system crash. (two sources)[^c1-1][^c1-3] _(SQLite WAL checkpointing)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- Long-lived or overlapping reader snapshots that retain WAL content can prevent complete checkpointing or WAL reset while writes continue, causing checkpoint starvation and unbounded log growth. (two sources)[^c1-1][^c1-4] _(SQLite WAL checkpointing)_
- Normal checkpointing usually retains the allocated WAL for reuse; successful copying need not shrink its physical size. Successful TRUNCATE explicitly shrinks it. (two sources)[^c1-1][^c1-2] _(SQLite WAL checkpointing)_
- Tentative: SQLite documents a rare corruption race between checkpointing and WAL reset on separate connections. The WAL-reset bug is fixed in 3.51.3 and later, with backports in 3.44.6 and 3.50.7. verified-as-of: 2026-08-25[^c1-1] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): Fly.io describes RESTART/TRUNCATE as blocking new read and write transactions. SQLite's API and PRAGMA references specify that these modes block writers but allow readers to proceed; their waits concern the snapshots or WAL usage of existing readers.[^c1-4][^c1-2][^c1-3]
- Open (SQLite WAL checkpointing): Which checkpoint interval and mode best balance this application's reader lifetimes, write volume, disk latency, and commit-latency budget? The sources give no universal optimum.
- Open (SQLite WAL checkpointing): Does the deployed SQLite build include the documented WAL-reset fix? No deployment version or downstream patch history was supplied.

## References

### SQLite WAL checkpointing

[^c1-1]: https://sqlite.org/wal.html — Write-Ahead Logging (docs)
[^c1-2]: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — Checkpoint a database: sqlite3_wal_checkpoint_v2 (docs)
[^c1-3]: https://www.sqlite.org/pragma.html — PRAGMA Statements: wal_checkpoint, wal_autocheckpoint, synchronous (docs)
[^c1-4]: https://www.fly.io/blog/sqlite-internals-wal/ — How SQLite Scales Read Concurrency (blog)
[^c1-5]: https://turso.tech/blog/how-does-the-turso-cloud-keep-your-data-durable-and-safe — How does Turso Cloud keep your data durable and safe? (blog)
