---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/claude__claude-sonnet-5-5__low/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:37:59Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:36:52Z", "updatedAt": "2026-10-13T06:37:59Z"} -->

## Overview

A checkpoint copies committed WAL frames back into the main database file. SQLite runs a PASSIVE checkpoint automatically when a commit leaves the WAL at 1000 pages or more. Manual modes FULL, RESTART and TRUNCATE wait for writers and readers to varying degrees. Long-running readers cause checkpoint starvation, so the WAL grows without bound. A checkpoint normally reuses the WAL file rather than shrinking it, so size reduction needs TRUNCATE or journal_size_limit. A rare WAL-reset bug affecting 3.7.0 through 3.51.2 was fixed in 3.51.3.

## Core Concepts

### SQLite WAL checkpointing

- SQLite auto-checkpoints when a COMMIT leaves the WAL at 1000 pages or more, and when the last connection closes. Automatic checkpoints and sqlite3_wal_checkpoint() use PASSIVE mode. (two sources)[^c1-1][^c1-2]
- PASSIVE checkpoints as many frames as possible without waiting for readers or writers and never invokes the busy handler. FULL waits for no active writer and all readers on the latest snapshot. RESTART also waits until readers use only the database file. TRUNCATE is RESTART plus truncating the WAL to zero bytes. (two sources)[^c1-2][^c1-1]
- A checkpoint normally does not shrink the WAL file; it restarts overwriting from the start. The file is truncated only when the journal_size_limit pragma is set, or by a successful TRUNCATE checkpoint (which reports pnLog and pnCkpt as 0). (two sources)[^c1-1][^c1-2]

## Tools & Frameworks

_(none recorded)_

## Methodology

_(none recorded)_

## Practical Patterns

- Tentative: If a FULL, RESTART or TRUNCATE checkpoint's busy handler returns 0 before the writer lock is acquired or while waiting on readers, the call degrades to PASSIVE behaviour and returns SQLITE_BUSY. If another process is checkpointing, it returns SQLITE_BUSY without calling the handler.[^c1-2] _(SQLite WAL checkpointing)_
- Mitigations for starvation: schedule manual RESTART or TRUNCATE checkpoints in reader gaps, keep read transactions short, and finalize or reset statements. (two sources)[^c1-1][^c1-3] _(SQLite WAL checkpointing)_

## Anti-Patterns

_(none recorded)_

## Troubleshooting

- A checkpoint cannot reset the WAL while any reader still needs it. If a reader always overlaps, no checkpoint completes and the WAL grows without bound (checkpoint starvation).[^c1-1][^c1-3] _(SQLite WAL checkpointing)_
- Tentative: Syncthing saw unbounded WAL growth from long vacuum transactions, constant read/write load, and automatic checkpoints colliding with its timer checkpointer. The proposed fix triggers checkpoints from connection-pool release logic.[^c1-3] _(SQLite WAL checkpointing)_
- Tentative: A WAL-reset bug affects likely all versions 3.7.0 through 3.51.2 and is fixed in 3.51.3 (2026-03-13), with backports 3.44.6 and 3.50.7. It needs two or more connections writing or checkpointing at the same instant. SQLite calls it rare and says upgrading is recommended but not an emergency. verified-as-of: 2026-08-24[^c1-1] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Open (SQLite WAL checkpointing): wal.html text says FULL and RESET, apparently a typo for RESTART.
- Open (SQLite WAL checkpointing): Independent sources beyond SQLite and Syncthing not fully read; SQLite forum threads on WAL not shrinking were only seen in search snippets.

## References

### SQLite WAL checkpointing

[^c1-1]: https://sqlite.org/wal.html — Write-Ahead Logging (docs)
[^c1-2]: https://sqlite.org/c3ref/wal_checkpoint_v2.html — sqlite3_wal_checkpoint_v2 (docs)
[^c1-3]: https://forum.syncthing.net/t/dealing-with-checkpoint-starvation/26121 — Dealing with checkpoint starvation (forum)
