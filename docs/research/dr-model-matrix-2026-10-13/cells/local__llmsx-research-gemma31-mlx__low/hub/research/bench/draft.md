---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/local__llmsx-research-gemma31-mlx__low/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:43:33Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:36:47Z", "updatedAt": "2026-10-13T06:43:33Z"} -->

## Overview

Checkpointing is the process of transferring committed transactions from the Write-Ahead Log (WAL) file back into the main database file. This operation is critical for maintaining read performance, as read-latency increases with WAL file size, and for preventing unbounded disk usage. SQLite provides an automatic checkpoint mechanism that triggers by default when the WAL reaches 1000 pages, as well as four manual modes (PASSIVE, FULL, RESTART, and TRUNCATE) that offer varying degrees of aggressiveness in reclaiming space and handling concurrent readers. Long-lived read transactions can block checkpoints, leading to 'checkpoint starvation' and unbounded WAL growth.

## Core Concepts

### SQLite WAL checkpointing

- SQLite automatically triggers a checkpoint when the WAL file reaches a threshold of 1000 pages by default.[^c1-1][^c1-4]
- PASSIVE checkpointing is a non-blocking, best-effort operation that copies as many frames as possible without waiting for readers or writers to finish.[^c1-2][^c1-3]
- FULL checkpointing blocks (invokes the busy-handler) until all readers are reading from the most recent snapshot and no writers are active, ensuring all frames are checkpointed.[^c1-2][^c1-3]
- RESTART checkpointing behaves like FULL but additionally blocks until all readers are reading from the main database file only, ensuring the next writer starts the log from the beginning.[^c1-2][^c1-4]
- TRUNCATE checkpointing behaves like RESTART but also truncates the WAL file to zero bytes upon successful completion.[^c1-2][^c1-4]
- Read performance degrades as the WAL file size increases because readers must check the WAL for the most recent versions of pages.[^c1-1][^c1-3]
- All checkpoint modes obtain an exclusive 'checkpoint' lock; FULL, RESTART, and TRUNCATE additionally obtain an exclusive 'writer' lock.[^c1-2][^c1-3]
- The TRUNCATE mode performs an ftruncate to zero bytes rather than unlinking the WAL file from the filesystem. (two sources)[^c1-2][^c1-5]

## Tools & Frameworks

_(none recorded)_

## Methodology

_(none recorded)_

## Practical Patterns

_(none recorded)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- Long-lived read transactions maintain historical snapshots of the database, preventing checkpoints from progressing beyond the earliest active snapshot and causing WAL growth.[^c1-1][^c1-3] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

_(none recorded)_

## References

### SQLite WAL checkpointing

[^c1-1]: https://www.sqlite.org/wal.html — Write-Ahead Logging - SQLite (docs)
[^c1-2]: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — Checkpoint a database - SQLite (docs)
[^c1-3]: https://sqlite.work/read-only-connections-blocking-wal-checkpoints-and-data-visibility-in-sqlite/ — Read-Only Connections Blocking WAL Checkpoints (blog)
[^c1-4]: https://litestream.io/guides/wal-truncate-threshold/ — WAL Truncate Threshold Configuration (docs)
[^c1-5]: https://github.com/vellum-ai/vellum-assistant/issues/34986 — Vellum Assistant Issue 34986 (repo)
