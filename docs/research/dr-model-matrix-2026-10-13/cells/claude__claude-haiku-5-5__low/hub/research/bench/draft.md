---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/claude__claude-haiku-5-5__low/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:35:31Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:32:36Z", "updatedAt": "2026-10-13T06:35:31Z"} -->

## Overview

A checkpoint copies committed frames from the WAL file back into the main database file. SQLite runs checkpoints automatically once the WAL reaches about 1000 pages, using PASSIVE mode. Applications can also call PASSIVE, FULL, RESTART or TRUNCATE explicitly through the wal_checkpoint pragma or sqlite3_wal_checkpoint_v2(). A checkpoint cannot pass a page that a current reader still needs, so a long-running read transaction stops progress and the WAL grows. Checkpoint tuning therefore matters for WAL size, read latency and write latency.

## Core Concepts

### SQLite WAL checkpointing

- A checkpoint copies committed frames from the WAL back into the database file. The WAL is reset only after all its content is transferred and synced and no reader uses it.[^c1-1][^c1-4]
- By default SQLite runs an automatic checkpoint when the WAL reaches a threshold of 1000 pages. The automatic checkpoint runs PASSIVE mode on the thread of the committing connection. The pragma wal_autocheckpoint changes the threshold, and a value of 0 or less disables it. verified-as-of: 2026-10-13[^c1-1][^c1-5]
- PASSIVE is the default checkpoint mode. It copies as many frames as it can without waiting for readers or writers, and it may leave the checkpoint unfinished when concurrent readers or writers exist. It syncs the database file only if every frame was checkpointed.[^c1-1][^c1-2][^c1-3]
- Tentative: Checkpoints do not normally truncate the WAL file. Without the journal_size_limit pragma, SQLite instead overwrites the WAL from the beginning after a reset.[^c1-1]
- Tentative: Only one checkpoint can run at a time. If another connection holds the checkpoint lock, the call returns SQLITE_BUSY.[^c1-2]

## Tools & Frameworks

- FULL and RESTART wait on the busy handler until no writer is active and readers use the latest snapshot. RESTART also waits until every reader has finished with the WAL, so the next writer restarts the log from the beginning. Both block new writers while pending, but neither blocks readers.[^c1-2][^c1-3] _(SQLite WAL checkpointing)_
- TRUNCATE works like RESTART and also truncates the WAL file to zero bytes just before a successful return. Practitioners run PRAGMA wal_checkpoint(TRUNCATE) in low-traffic windows to shrink a WAL that has grown. (two sources)[^c1-2][^c1-5] _(SQLite WAL checkpointing)_

## Methodology

_(none recorded)_

## Practical Patterns

- If automatic checkpoints are disabled, nothing stops the WAL from growing without limit. The application must then run checkpoints itself, for example during idle periods or in a separate thread or process. (two sources)[^c1-1][^c1-5] _(SQLite WAL checkpointing)_
- Tentative: Checkpoints are the only operation that syncs under synchronous=NORMAL. Running checkpoints on a separate thread keeps the main thread from blocking on sync, but transactions are then no longer durable across power loss.[^c1-1] _(SQLite WAL checkpointing)_

## Anti-Patterns

- Tentative: In the Syncthing case, automatic SQLite checkpoints block the application's own checkpointer, because checkpoints are exclusive. The same post reports that a truncating checkpoint needs no active readers or writers, and that the timer-based checkpointer may never find such a window. verified-as-of: 2026-02-06[^c1-4] _(SQLite WAL checkpointing)_

## Troubleshooting

- A long-running read transaction prevents the checkpoint from making progress. A checkpoint must stop at the first WAL page past the end mark of any current reader. If a database always has at least one overlapping reader, no checkpoint completes and the WAL grows without bound.[^c1-1][^c1-4] _(SQLite WAL checkpointing)_
- Practitioner guidance calls checkpointing a production footgun: a large checkpoint competes with foreground work and can raise p99 latency. Advice in the post is to avoid checkpointing on every request and to checkpoint on a cadence when the system is not overloaded. (two sources) verified-as-of: 2026-09-15[^c1-5][^c1-4] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): The Syncthing post says truncating the WAL needs exclusive locking, so it proposes truncation only once the WAL reaches multi-gigabyte sizes. The kunalganglani post recommends routine PRAGMA wal_checkpoint(TRUNCATE) in low-traffic windows.[^c1-4][^c1-5]
- Open (SQLite WAL checkpointing): A 2026 WAL-reset race that could drop committed frames and corrupt a database, fixed in a 3.51.x release, is reported only in secondary sources (theconsensus.dev, a youngju.dev blog). Both pages failed to fetch here (403; empty body). Unverified, so no claim cites it. Check sqlite.org release notes and the original analysis before relying on it.
- Open (SQLite WAL checkpointing): The chiark URLs mirror sqlite.org docs. They count as one organisation, not two independent sources. The sqlite.org pragma page and the sqlite3_wal_checkpoint_v2 page were not fetched directly.
- Open (SQLite WAL checkpointing): The Syncthing post reports no measurements. The kunalganglani post reports no measured checkpoint durations or WAL sizes.
- Open (SQLite WAL checkpointing): The sqlite.org docs page is undated here, so verified_as_of uses the retrieval date 2026-10-13.

## References

### SQLite WAL checkpointing

[^c1-1]: https://sqlite.org/wal.html — SQLite Write-Ahead Logging (WAL) (docs)
[^c1-2]: https://www.chiark.greenend.org.uk/doc/sqlite3/c3ref/wal_checkpoint_v2.html — SQLite C API sqlite3_wal_checkpoint_v2 (chiark mirror of sqlite.org docs) (docs)
[^c1-3]: https://www.chiark.greenend.org.uk/doc/sqlite3/pragma.html — SQLite PRAGMA reference, wal_checkpoint (chiark mirror of sqlite.org docs) (docs)
[^c1-4]: https://forum.syncthing.net/t/dealing-with-checkpoint-starvation/26121 — Dealing with checkpoint starvation (Syncthing forum, 2026-02-06) (forum)
[^c1-5]: https://www.kunalganglani.com/blog/sqlite-production-api-wal — SQLite Production API Concurrency: WAL Mode Limits (2026-09-15) (blog)
