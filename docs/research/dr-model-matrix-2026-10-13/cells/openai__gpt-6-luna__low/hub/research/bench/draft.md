---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/openai__gpt-6-luna__low/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:39:28Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:36:47Z", "updatedAt": "2026-10-13T06:39:28Z"} -->

## Overview

In SQLite write-ahead logging, a checkpoint copies committed frames from the WAL into the main database, allowing the WAL to be reused and keeping recovery and reads manageable. SQLite normally runs passive auto-checkpoints at a configurable page threshold, currently documented as 1000 pages by default. Passive checkpoints do not wait for readers or writers and may stop before completion. A reader holding an older snapshot can prevent a checkpoint from advancing past that reader's end mark, so sustained overlapping reads can delay WAL reset and permit growth. FULL, RESTART, and TRUNCATE modes wait more aggressively; TRUNCATE additionally reduces the WAL file to zero bytes after successful completion. Checkpoint frequency trades write latency against WAL size and read costs, so the default is a policy choice rather than a fixed best setting for every workload.

## Core Concepts

### SQLite WAL checkpointing

- A checkpoint copies committed WAL content back into the main database; SQLite's normal checkpoint process preserves the committed database state while moving those page changes out of the log.[^c1-1][^c1-6]
- SQLite documents automatic checkpointing at 1000 WAL pages by default, triggered by a commit that reaches the threshold; the threshold can be changed or auto-checkpointing disabled. The current pragma documentation was updated 2026-10-04. verified-as-of: 2026-10-04[^c1-1][^c1-2][^c1-6]
- Automatic checkpoints use PASSIVE mode. A passive checkpoint does as much work as possible without waiting for readers or writers, and can leave frames uncheckpointed when concurrent activity prevents completion.[^c1-1][^c1-2][^c1-3]

## Tools & Frameworks

- The APSW Python wrapper exposes Connection.wal_checkpoint(dbname, mode), defaults the mode to PASSIVE, and returns WAL frame and checkpointed-frame counts, providing a wrapper-level way to invoke and inspect SQLite checkpointing.[^c1-7][^c1-3] _(SQLite WAL checkpointing)_

## Methodology

- SQLite distinguishes FULL, RESTART, and TRUNCATE checkpoint modes: FULL waits for writers and readers to reach the latest snapshot and blocks new writers; RESTART also waits until readers no longer use the WAL; TRUNCATE adds zero-length truncation on success.[^c1-3][^c1-2][^c1-7] _(SQLite WAL checkpointing)_

## Practical Patterns

_(none recorded)_

## Anti-Patterns

- A successful checkpoint usually recycles the WAL for reuse rather than truncating it, so a large on-disk WAL file alone does not show that no frames were checkpointed; TRUNCATE mode reduces the file to zero bytes only after successful completion.[^c1-1][^c1-2][^c1-3] _(SQLite WAL checkpointing)_

## Troubleshooting

- A reader holding an older WAL snapshot can prevent a checkpoint from advancing beyond that reader's end mark; persistent overlapping readers can therefore prevent completion and WAL reset, allowing the WAL to grow without bound.[^c1-1][^c1-4][^c1-5] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Open (SQLite WAL checkpointing): The best checkpoint interval depends on workload and storage latency; the sources do not prescribe a universally optimal threshold.

## References

### SQLite WAL checkpointing

[^c1-1]: https://www.sqlite.org/wal.html — Write-Ahead Logging (docs)
[^c1-2]: https://www.sqlite.org/pragma.html — Pragma statements supported by SQLite (docs)
[^c1-3]: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — Checkpoint a database (docs)
[^c1-4]: https://www.sqlite.org/fileformat.html — Database File Format (docs)
[^c1-5]: https://www3.sqlite.org/matrix/wal.html — Write-Ahead Logging (docs)
[^c1-6]: https://www.vldb.org/pvldb/vol11/p513-park.pdf — SQLite/SSL: A SQLite-Based DBMS for Flash Storage (paper)
[^c1-7]: https://rogerbinns.github.io/apsw/connection.html — Connections to a database — APSW 3.54.0.0 (docs)
