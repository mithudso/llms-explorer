---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/openai__gpt-6.1-sol__low/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:45:05Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:42:18Z", "updatedAt": "2026-10-13T06:45:05Z"} -->

## Overview

Checkpointing copies committed page changes from SQLite’s write-ahead log into the main database. It controls WAL growth and affects write latency, read costs, and disk synchronization. Copying pages, making the WAL reusable, and shrinking its physical file are separate outcomes. Active reader snapshots can prevent progress or reuse, so checkpoints can be partial. Automatic checkpoints use a configurable size threshold and passive behavior. Applications can choose stronger checkpoint modes, but must inspect their return status rather than assume completion. Workload-specific scheduling should balance checkpoint overhead against WAL growth; historical application thresholds are examples, not universal tuning recommendations.

## Core Concepts

### SQLite WAL checkpointing

- Checkpointing copies page changes from the WAL into the main database; when a page has multiple eligible versions, the latest relevant version is copied.[^c1-1][^c1-3]
- Checkpoint completion does not ordinarily imply that the physical WAL file shrinks; SQLite commonly reuses allocated WAL storage, while successful TRUNCATE explicitly shrinks it.[^c1-1][^c1-2][^c1-3]

## Tools & Frameworks

- The standard automatic checkpoint threshold is 1000 pages, subject to compile-time or runtime configuration; automatic checkpoints are PASSIVE and may remain incomplete.[^c1-1][^c1-2] _(SQLite WAL checkpointing)_
- Tentative: PASSIVE checkpoints do not wait for readers or writers and never invoke the busy handler. FULL waits for the writer and sufficiently recent reader snapshots, then checkpoints all frames and synchronizes the database.[^c1-2] _(SQLite WAL checkpointing)_
- RESTART additionally waits until readers use only the database file so the next writer can restart the WAL; TRUNCATE additionally reduces the WAL to zero bytes on successful completion.[^c1-2][^c1-3] _(SQLite WAL checkpointing)_

## Methodology

_(none recorded)_

## Practical Patterns

- Tentative: Automatic checkpoint work can make the triggering commit slower. Moving scheduled checkpoints to a separate thread or process can move that work away from the committing thread.[^c1-1] _(SQLite WAL checkpointing)_
- Tentative: Mozilla’s historical places.sqlite discussion separated blocking FULL checkpoints from journal_size_limit and later deferred the blocking-checkpoint change because synchronous queries could encounter SQLITE_BUSY; this is an application-specific integration concern.[^c1-4] _(SQLite WAL checkpointing)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- An active reader snapshot can limit checkpoint progress, and readers still using the WAL can prevent its reset; overlapping readers can therefore cause checkpoint starvation and continued WAL growth.[^c1-1][^c1-2][^c1-3] _(SQLite WAL checkpointing)_
- Tentative: FULL, RESTART, and TRUNCATE can return SQLITE_BUSY when the busy handler stops waiting. A competing checkpoint can also cause SQLITE_BUSY without invoking that handler.[^c1-2] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): The WAL overview describes RESTART/TRUNCATE as ensuring completion, and the Fly article describes forcing a restart. The detailed API contract scopes those descriptions: lock contention or a busy handler that stops waiting can produce SQLITE_BUSY and partial progress.[^c1-1][^c1-2][^c1-3]
- Open (SQLite WAL checkpointing): Checkpoint scheduling and size thresholds require workload measurements; the historical Mozilla thresholds do not establish a universal policy.

## References

### SQLite WAL checkpointing

[^c1-1]: https://www.sqlite.org/wal.html — Write-Ahead Logging (docs)
[^c1-2]: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — Checkpoint a database (docs)
[^c1-3]: https://www.fly.io/blog/sqlite-internals-wal/ — How SQLite Scales Read Concurrency (blog)
[^c1-4]: https://bugzilla.mozilla.org/show_bug.cgi?id=658305 — Use journal_size_limit on places.sqlite (forum)
