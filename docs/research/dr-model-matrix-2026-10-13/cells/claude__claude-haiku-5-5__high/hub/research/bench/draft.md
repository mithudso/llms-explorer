---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/claude__claude-haiku-5-5__high/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:40:24Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:36:52Z", "updatedAt": "2026-10-13T06:40:24Z"} -->

## Overview

A checkpoint copies committed frames from the -wal file back into the main database file, then lets SQLite reuse the WAL from the start. Automatic checkpoints run PASSIVE after about 1000 pages and never block, but they do not shrink the -wal file on disk. FULL, RESTART and TRUNCATE wait for writers and readers to finish; TRUNCATE also cuts the file to zero bytes. A long-lived reader stops checkpoint progress, so the WAL can grow without bound. Checkpoint policy therefore controls WAL file size, read cost and write blocking. In 2026 the WAL-Reset bug, a race between a checkpoint and a write, corrupted databases before SQLite fixed it in 3.51.3. Tailscale's aggressive manual checkpointing raised its odds of hitting that race.

## Core Concepts

### SQLite WAL checkpointing

- When a COMMIT leaves the WAL at 1000 pages or more, or when the last connection closes, SQLite runs an automatic checkpoint. The default threshold is set by SQLITE_DEFAULT_WAL_AUTOCHECKPOINT, and PRAGMA wal_autocheckpoint = 0 disables it.[^c1-1][^c1-3]
- Automatic checkpoints and sqlite3_wal_checkpoint() use PASSIVE mode. PASSIVE never invokes the busy handler, does as much work as it can without waiting, and may stay incomplete while other connections are active.[^c1-1][^c1-2][^c1-3]
- FULL waits until no writer is active and readers are on the latest snapshot, then checkpoints all frames and syncs the database file. FULL blocks new writers but not readers. RESTART does the same work as FULL and then waits until readers use only the database file, so the next writer restarts the log from the beginning. TRUNCATE does RESTART and then truncates the log file to zero bytes.[^c1-2][^c1-3]
- A normal checkpoint does not truncate the -wal file. SQLite overwrites the WAL from the beginning because overwriting is faster than appending, so the physical file keeps its high-water size on disk after a passive restart.[^c1-1][^c1-4]
- A checkpoint must stop at the first WAL page past the end mark of any current reader. It saves its progress in the wal-index and resumes from there on a later run. A long-running read transaction therefore holds back checkpoint progress.[^c1-1][^c1-2]

## Tools & Frameworks

- FULL, RESTART and TRUNCATE are reachable through sqlite3_wal_checkpoint_v2() and through PRAGMA wal_checkpoint(mode). The PRAGMA form with no argument behaves as PASSIVE.[^c1-1][^c1-2][^c1-3] _(SQLite WAL checkpointing)_

## Methodology

- Antithesis reproduced the WAL-Reset bug in 15 minutes on SQLite 3.51.2 with a generic workload of concurrent writes and checkpoints, and found the same test clean on 3.51.3. The bug needs at least two connections from separate threads or processes. (two sources) verified-as-of: 2026-08-12[^c1-6][^c1-7] _(SQLite WAL checkpointing)_

## Practical Patterns

- Litestream runs a PASSIVE checkpoint at 1000 pages (about 4 MB) and on a one-minute timer, and never blocks the application on those. It falls back to a blocking TRUNCATE only when the WAL stays above a 121,359-page (about 500 MB) emergency threshold after a passive attempt. verified-as-of: 2026-09-28[^c1-4][^c1-1] _(SQLite WAL checkpointing)_
- Litestream recommends disabling the application's own automatic checkpoints with PRAGMA wal_autocheckpoint = 0 when another process runs checkpoints. Syncthing's report lists uncontrolled auto-checkpoints as a cause of blocked checkpointing in its own process. (two sources)[^c1-4][^c1-5] _(SQLite WAL checkpointing)_
- Tentative: Syncthing's proposed fix replaces its timer-based checkpointer with a checkpoint triggered when a pooled connection is released. Forced truncation should wait for a critical WAL size, because TRUNCATE needs an exclusive lock and can cause a feedback loop of stalled operations. The thread records no maintainer decision. verified-as-of: 2026-02-06[^c1-5] _(SQLite WAL checkpointing)_

## Anti-Patterns

- If overlapping readers keep at least one reader active at all times, no checkpoint can complete a WAL reset, and the WAL grows without bound. A Syncthing developer reported this in production: a timer-based checkpointer may never find a moment without an active reader, so truncation never happens.[^c1-1][^c1-5] _(SQLite WAL checkpointing)_
- Tentative: Tailscale ran its own checkpoints manually and very aggressively. SQLite's developers said this raised the odds of hitting the rare race. Tailscale recorded 19 corruption incidents over six months, and each one took its shard control plane offline during repair. verified-as-of: 2026-08-12[^c1-7] _(SQLite WAL checkpointing)_

## Troubleshooting

- SQLite's suggested mitigations for checkpoint starvation are reader gaps for checkpoints, or manual RESTART or TRUNCATE checkpoints, accepting that readers may block while they run.[^c1-1][^c1-2] _(SQLite WAL checkpointing)_
- The WAL-Reset bug is a rare data race between a checkpoint and a write transaction. If a write lands at the wrong moment, the checkpoint wrongly believes some WAL pages were already copied to the database. The unwritten pages leave the database corrupt, and committed data can vanish.[^c1-7][^c1-6] _(SQLite WAL checkpointing)_
- SQLite fixed the WAL-Reset bug in 3.51.3, released 2026-03-13, with backports to 3.44.6 and 3.50.7. Version 3.52.0 shipped the fix but was withdrawn because of an unrelated floating-point rounding change. The bug affected releases from 3.7.0 through 3.51.2. verified-as-of: 2026-08-25[^c1-1][^c1-7] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): Syncthing's proposal truncates only at a critical WAL size to avoid stalling operations. Litestream uses a blocking TRUNCATE once the WAL passes about 500 MB. The sources differ on the threshold at which a blocking truncate is acceptable.[^c1-5][^c1-4]
- Open (SQLite WAL checkpointing): Whether journal_size_limit shrinks the -wal file at commit or WAL-reset time. A SQLite forum excerpt says so, but I did not read the source post.
- Open (SQLite WAL checkpointing): Which exact read or write sequence triggers the WAL-Reset race. Antithesis and Tailscale do not describe it in detail, and the sqlite.org section 11 text was only summarized.
- Open (SQLite WAL checkpointing): Whether the Syncthing thread (2026-02-06) was resolved after its last post. The fetched page shows no decision.
- Open (SQLite WAL checkpointing): The consensus.dev write-up on the WAL-Reset bug returned HTTP 403 and was not read.

## References

### SQLite WAL checkpointing

[^c1-1]: https://sqlite.org/wal.html — SQLite Write-Ahead Logging (docs)
[^c1-2]: https://sqlite.org/c3ref/wal_checkpoint_v2.html — SQLite C API: sqlite3_wal_checkpoint_v2 (docs)
[^c1-3]: https://sqlite.org/pragma.html — SQLite PRAGMA statements (wal_checkpoint, wal_autocheckpoint) (docs)
[^c1-4]: https://litestream.io/guides/wal-truncate-threshold/ — Litestream guide: WAL truncate threshold (docs)
[^c1-5]: https://forum.syncthing.net/t/dealing-with-checkpoint-starvation/26121 — Syncthing forum: Dealing with checkpoint starvation (forum)
[^c1-6]: https://antithesis.com/blog/2026/wal-reset-bug/ — Antithesis: WAL reset bug (2026-08-12) (blog)
[^c1-7]: https://tailscale.com/blog/sqlite-wal-reset-bug — Tailscale: SQLite WAL-Reset bug (2026-08-12) (postmortem)
