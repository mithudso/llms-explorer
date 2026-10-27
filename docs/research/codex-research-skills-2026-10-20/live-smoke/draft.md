---
name: codex-live-smoke
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-20"
category: "research-draft"
keywords: ["codex-live-smoke"]
tags: ["dr-draft"]
provenance: "/dr · /var/folders/b1/74j52b997pq42_fwh66r7cdm0000gp/T/codex-dr-live-smoke-mbs0q7yu/research/codex-live-smoke"
---

# SQLite WAL checkpointing

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-21T01:17:28Z.

<!-- dr:progress {"skillId": "codex-live-smoke", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-21T01:16:18Z", "updatedAt": "2026-10-21T01:17:28Z"} -->

## Overview

Checkpointing copies committed page changes from SQLite’s write-ahead log into the main database. It controls WAL growth and trades checkpoint work against transaction latency. Active readers can delay progress or prevent WAL reuse. Applications can tune automatic checkpoints or select manual modes with different waiting and truncation behavior. Completion status and frame counts help distinguish partial progress from a fully checkpointed log.

## Core Concepts

### SQLite WAL checkpointing

- A checkpoint transfers committed WAL changes into the main database; when multiple versions of a page are eligible, it copies the latest version.[^c1-1][^c1-4]
- Automatic checkpoints are PASSIVE and normally trigger at commits reaching 1000 WAL pages; the compile-time default and wal_autocheckpoint can change that threshold.[^c1-1][^c1-3]

## Tools & Frameworks

- PASSIVE checkpoints process available frames without waiting for readers or writers and never invoke the busy handler; concurrent activity can leave them incomplete.[^c1-2][^c1-3] _(SQLite WAL checkpointing)_
- FULL waits for the writer and sufficiently recent reader snapshots, then checkpoints all frames. RESTART additionally waits until readers no longer need the WAL; successful TRUNCATE also reduces the WAL to zero bytes.[^c1-2][^c1-3] _(SQLite WAL checkpointing)_

## Methodology

- PRAGMA wal_checkpoint returns busy status, WAL frame count and checkpointed frame count. The checkpointed count includes earlier work; successful TRUNCATE returns zero frame counts.[^c1-3][^c1-2] _(SQLite WAL checkpointing)_

## Practical Patterns

- Tentative: Automatic checkpoint work runs in the committing thread and can cause occasional slow commits. Disabling it and scheduling checkpoints separately moves that work away from the commit path.[^c1-1] _(SQLite WAL checkpointing)_
- Checkpointing normally permits WAL reuse without physically shrinking the file. Use a successful TRUNCATE checkpoint when reclaiming WAL file space is required.[^c1-1][^c1-2][^c1-4] _(SQLite WAL checkpointing)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- Long read transactions can limit checkpoint progress; continuously overlapping readers can prevent WAL reset and allow unbounded WAL growth. Reader gaps permit completion.[^c1-1][^c1-4] _(SQLite WAL checkpointing)_
- Tentative: FULL, RESTART and TRUNCATE block new writers while pending but allow readers. A busy handler that stops waiting causes partial PASSIVE-style work and SQLITE_BUSY; a competing checkpoint returns SQLITE_BUSY without invoking the busy handler.[^c1-2] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): Fly describes RESTART as blocking new readers and writers. SQLite’s API reference says RESTART blocks new writers but does not impede readers; use the API reference for lock semantics.[^c1-4][^c1-2]

## References

### SQLite WAL checkpointing

[^c1-1]: https://www.sqlite.org/wal.html — Write-Ahead Logging (docs)
[^c1-2]: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — Checkpoint a database (docs)
[^c1-3]: https://www.sqlite.org/pragma.html — Pragma statements supported by SQLite (docs)
[^c1-4]: https://www.fly.io/blog/sqlite-internals-wal/ — How SQLite Scales Read Concurrency (blog)
