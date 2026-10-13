---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/agy__gemini-3.8-flash__low/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:39:49Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:36:47Z", "updatedAt": "2026-10-13T06:39:49Z"} -->

## Overview

SQLite write-ahead logging (WAL) appends modified database pages sequentially to a separate -wal file, avoiding in-place modifications to the main database file. Checkpointing transfers these committed frames back into the main database file and resets or truncates the log. SQLite triggers passive checkpoints automatically when the WAL hits a configurable threshold (defaulting to 1,000 pages) or when connections close. However, checkpoints cannot overwrite frames pinned by active read transactions, making checkpointer starvation a key operational risk under continuous concurrent read workloads.

## Core Concepts

### SQLite WAL checkpointing

- SQLite checkpointing copies committed database pages from the write-ahead log (-wal) file back to the primary database file, allowing the log space to be reused or truncated.[^c1-1][^c1-2]
- By default, SQLite automatically executes a passive checkpoint whenever a write transaction commit expands the WAL file to 1,000 pages or more.[^c1-1][^c1-2]

## Tools & Frameworks

- SQLite provides sqlite3_wal_checkpoint_v2 with modes PASSIVE, FULL, RESTART, and TRUNCATE to programmatically control blocking behavior and file size resetting.[^c1-1][^c1-2] _(SQLite WAL checkpointing)_

## Methodology

_(none recorded)_

## Practical Patterns

- Litestream holds an intentional indefinite read transaction on SQLite to pause automatic checkpointing while it copies WAL frames into an external shadow log for continuous replication.[^c1-2][^c1-3] _(SQLite WAL checkpointing)_

## Anti-Patterns

- Passive checkpoints cannot advance past frames pinned by active readers, causing WAL file growth and potential starvation if long-running read transactions overlap indefinitely.[^c1-1][^c1-2][^c1-3] _(SQLite WAL checkpointing)_

## Troubleshooting

_(none recorded)_

## Disagreements & Open Questions

- Open (SQLite WAL checkpointing): Whether upcoming SQLite WAL extensions (such as WAL2 / concurrent WAL branches) will eliminate single-checkpointer reader pinning bottlenecks.

## References

### SQLite WAL checkpointing

[^c1-1]: https://www.sqlite.org/wal.html — Write-Ahead Logging (docs)
[^c1-2]: https://fly.io/blog/how-sqlite-scales-read-concurrency/ — How SQLite Scales Read Concurrency (blog)
[^c1-3]: https://litestream.io/how-it-works/ — How Litestream Works (docs)
