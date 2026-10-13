---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/claude__claude-opus-5-5__low/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:42:21Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:40:53Z", "updatedAt": "2026-10-13T06:42:21Z"} -->

## Overview

A checkpoint copies committed transactions from the -wal file back into the main database file. By default SQLite runs a PASSIVE auto-checkpoint when a COMMIT pushes the WAL past 1000 pages, and when the last connection closes. Applications can disable auto-checkpoints and checkpoint explicitly with PRAGMA wal_checkpoint or sqlite3_wal_checkpoint_v2 in PASSIVE, FULL, RESTART, or TRUNCATE mode. Checkpointing matters because the WAL is only rewound after a checkpoint reaches its end while no reader still uses it. Long-lived or overlapping read transactions, and statements that are never reset, cause checkpoint starvation and unbounded WAL growth. The experimental wal2 branch targets the continuous-writer case.

## Core Concepts

### SQLite WAL checkpointing

- By default SQLite auto-checkpoints when a COMMIT leaves the WAL at 1000 pages or more, and when the last connection closes; the threshold is changeable via PRAGMA wal_autocheckpoint or SQLITE_DEFAULT_WAL_AUTOCHECKPOINT.[^c1-1][^c1-3]
- Auto-checkpoints are PASSIVE: they copy as many frames as possible without waiting and never invoke the busy handler, so they can make little progress under contention.[^c1-2][^c1-1]
- FULL waits (via busy handler) for writers to finish and readers to reach the latest snapshot, then checkpoints all frames; RESTART additionally waits until readers no longer use the WAL so the next writer rewinds it; TRUNCATE additionally truncates the WAL to zero bytes. These modes block new writers but not new readers while waiting.[^c1-2][^c1-1]
- A normal checkpoint does not shrink the WAL file; the file is rewound and overwritten from the start unless journal_size_limit is set or a TRUNCATE checkpoint runs.[^c1-1][^c1-3]

## Tools & Frameworks

_(none recorded)_

## Methodology

_(none recorded)_

## Practical Patterns

- Operators under heavy load pair default auto-checkpoints with a separate maintenance task that checks WAL size and issues TRUNCATE checkpoints. (two sources)[^c1-7][^c1-1] _(SQLite WAL checkpointing)_
- The wal2 branch alternates between two WAL files so continuous writers no longer cause unbounded growth, but long-running readers can still prevent full checkpoints; it is not in mainline SQLite. (two sources) verified-as-of: 2024-01-13[^c1-5][^c1-6] _(SQLite WAL checkpointing)_

## Anti-Patterns

- Checkpoint starvation: if at least one read transaction is always open, checkpoints never reach the end of the WAL and the WAL grows without bound; fixes are reader gaps or periodic RESTART/TRUNCATE checkpoints.[^c1-1][^c1-3][^c1-6] _(SQLite WAL checkpointing)_

## Troubleshooting

- Tentative: If the busy handler gives up during FULL/RESTART/TRUNCATE, the call degrades to PASSIVE behaviour and returns SQLITE_BUSY; a concurrent checkpoint in another connection returns SQLITE_BUSY immediately.[^c1-2] _(SQLite WAL checkpointing)_
- A prepared statement that is stepped but never reset or finalized keeps its transaction open and is a common cause of a WAL that never shrinks; forcing PRAGMA wal_checkpoint and checking file size diagnoses it. (two sources)[^c1-3][^c1-4] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): Secondary tutorials disagree on whether RESTART blocks readers; the official API doc says it blocks new writers, not readers, but waits on existing readers.[^c1-2]
- Open (SQLite WAL checkpointing): Whether wal2 or begin-concurrent will merge into mainline SQLite.
- Open (SQLite WAL checkpointing): Forum and Guix sources were seen via search snippets, not deep-read.

## References

### SQLite WAL checkpointing

[^c1-1]: https://sqlite.org/wal.html — SQLite Write-Ahead Logging (docs)
[^c1-2]: https://sqlite.org/c3ref/wal_checkpoint_v2.html — sqlite3_wal_checkpoint_v2 (docs)
[^c1-3]: https://sqlite.org/forum/forumpost/6038b31ddb?t=c — SQLite Forum: Growing WAL-File (forum)
[^c1-4]: https://sqlite.org/forum/forumpost/7d292adea1?t=c — SQLite Forum: Growing WAL-File (reply) (forum)
[^c1-5]: https://sqlite.org/src/doc/wal2/doc/wal2.md — SQLite wal2 branch design (docs)
[^c1-6]: https://brandur.org/atoms/gqljwm2 — brandur.org: SQLite wal2 (blog)
[^c1-7]: https://yhetil.org/guix/87zgpp971n.fsf@gnu.org/ — Guix mailing list: periodic TRUNCATE checkpoint (forum)
