---
name: bench
description: "DRAFT — research in progress; not yet trigger-quality"
version: "0.0.0-draft"
updated: "2026-10-13"
category: "research-draft"
keywords: ["bench"]
tags: ["dr-draft"]
provenance: "/dr · /Users/mitch/dev/llms-explorer/docs/research/dr-model-matrix-2026-10-13/cells/claude__claude-sonnet-5-5__high/hub/research/bench"
---

# SQLite write-ahead logging (WAL)

> **DRAFT — research in progress.** 1/1 concepts complete. Last updated: 2026-10-13T06:39:31Z.

<!-- dr:progress {"skillId": "bench", "state": "research-complete", "conceptsTotal": 1, "conceptsDone": ["sqlite-wal-checkpointing"], "conceptsPending": [], "startedAt": "2026-10-13T06:36:52Z", "updatedAt": "2026-10-13T06:39:31Z"} -->

## Overview

A checkpoint copies committed frames from the -wal file back into the main database file. SQLite runs a PASSIVE checkpoint automatically when a commit leaves the WAL at 1000 pages or more, and on last connection close. Apps can also request PASSIVE, FULL, RESTART, TRUNCATE or NOOP checkpoints. A checkpoint cannot pass the end mark of any active reader, so long read transactions or never-ending overlapping readers starve it and the WAL grows without bound. A finished checkpoint lets the WAL restart from the beginning but does not shrink the physical file unless TRUNCATE or journal_size_limit applies. A 2010-era race between a checkpoint and a concurrent write (the WAL-Reset bug) was fixed in SQLite 3.51.3 and bit Tailscale, which checkpointed aggressively.

## Core Concepts

### SQLite WAL checkpointing

- SQLite runs an automatic checkpoint whenever a COMMIT leaves the WAL at 1000 pages or more, and when the last connection to the database closes. All automatic checkpoints are PASSIVE. The default threshold is 1000 pages (compile-time SQLITE_DEFAULT_WAL_AUTOCHECKPOINT); PRAGMA wal_autocheckpoint=N changes it, and zero or a negative N turns it off.[^c1-1][^c1-3]
- PRAGMA wal_checkpoint takes PASSIVE, FULL, RESTART, TRUNCATE or NOOP. PASSIVE copies as many frames as it can without waiting and never invokes the busy handler. FULL waits for writers and for readers to be on the latest snapshot, then copies every frame; new writers block while it is pending and new readers continue. RESTART does FULL and then waits until all readers use only the database file, so the next writer restarts the log at the beginning. TRUNCATE does RESTART and then truncates the WAL to zero bytes just before a successful return. NOOP copies nothing and only reports counts.[^c1-2][^c1-3]
- A completed checkpoint does not normally shrink the -wal file. It only lets SQLite overwrite the WAL from the start, so the file keeps its high-water size on disk. The physical file shrinks only after a TRUNCATE checkpoint, or when PRAGMA journal_size_limit (default -1, no limit) is set and a commit or WAL reset finds the file larger than the limit.[^c1-1][^c1-3][^c1-4]
- Tentative: With PRAGMA synchronous=NORMAL in WAL mode, writers do not sync the WAL on commit, so the checkpoint is the only operation that issues a sync. Transactions are then not durable across power loss and can roll back. SQLite says to keep the WAL small by checkpointing at regular intervals.[^c1-1]
- Tentative: When the last connection closes, that connection runs one final checkpoint and then deletes the -wal file and its shared-memory (-shm) file.[^c1-1]

## Tools & Frameworks

- Automatic checkpoints and plain sqlite3_wal_checkpoint() are always PASSIVE. FULL, RESTART and TRUNCATE exist only through sqlite3_wal_checkpoint_v2() or PRAGMA wal_checkpoint(MODE). The no-argument pragma equals sqlite3_wal_checkpoint().[^c1-1][^c1-3] _(SQLite WAL checkpointing)_
- If the busy handler returns 0 while FULL, RESTART or TRUNCATE waits for the writer lock or for readers, the call degrades to PASSIVE behaviour: it copies what it can and returns SQLITE_BUSY. In PRAGMA wal_checkpoint output the first column is 1 in that case. The second and third columns are the WAL frame count and the frames checkpointed; both are -1 when the database is not in WAL mode, and both are 0 after a successful TRUNCATE.[^c1-2][^c1-3] _(SQLite WAL checkpointing)_
- Tentative: Litestream does not rely on the application to truncate the WAL. It runs PASSIVE checkpoints and, since v0.5.15, forces a blocking TRUNCATE only when the WAL does not restart below the truncate-page-n threshold (default 121359 pages, about 500 MB). A long-lived reader can force that TRUNCATE and cause extended write outages. verified-as-of: 2026-10-13[^c1-4] _(SQLite WAL checkpointing)_

## Methodology

_(none recorded)_

## Practical Patterns

- Mitigations for checkpoint starvation: keep read transactions short, finish or reset every statement, leave reader gaps so a checkpoint can finish, run checkpoints from the connection pool at release time to find quiet moments, and use RESTART or TRUNCATE (which block) only once the WAL passes a critical size. SQLite warns that RESTART and TRUNCATE can make readers wait. (two sources)[^c1-1][^c1-5] _(SQLite WAL checkpointing)_

## Anti-Patterns

- Only one checkpoint runs at a time per database. Every mode takes an exclusive checkpoint lock, and if another connection or process already holds it the call returns SQLITE_BUSY without invoking the busy handler. An application that runs its own timer-based checkpointer while auto-checkpoint stays on can therefore collide with commit-triggered passive checkpoints. (two sources)[^c1-2][^c1-5] _(SQLite WAL checkpointing)_
- Tailscale took manual control of checkpointing and ran it very aggressively, which raised its odds of hitting the WAL-Reset race. It logged 19 corruption incidents over about six months from August 2025, each needing a shard's control plane stopped for repair. SQLite's own view is that the race is unlikely in ordinary use, so frequent manual checkpoints from several connections are the risky pattern. (two sources) verified-as-of: 2026-08-12[^c1-6][^c1-7] _(SQLite WAL checkpointing)_

## Troubleshooting

- Each reader fixes an end mark at the last valid commit when its read transaction begins, and a checkpoint cannot copy past the oldest reader's end mark. A long-running read transaction therefore stalls checkpoint progress. If at least one reader is always active (overlapping readers with no gap), no checkpoint completes and the WAL grows without bound.[^c1-1][^c1-5] _(SQLite WAL checkpointing)_
- Tentative: Syncthing hit checkpoint starvation in February 2026: transactions open for hours stopped the checkpointer from reclaiming WAL pages, and constant database activity left no moment without readers or writers for a TRUNCATE. The developers treated a WAL of multiple gigabytes as the point to act. The thread proposed fixes but recorded none as adopted. verified-as-of: 2026-02-06[^c1-5] _(SQLite WAL checkpointing)_
- The WAL-Reset bug is a data race between a checkpoint and a write transaction when two or more connections on the same WAL database write or checkpoint at the same instant. The checkpointer can wrongly treat WAL pages as already copied to the database file, which loses data and can corrupt the file. SQLite says it is likely present in every version from 3.7.0 (2010-07-21) through 3.51.2 (2026-01-09). The fix is in 3.51.3 (2026-03-13), with backports to 3.44.6 and 3.50.7. 3.52.0 first carried the fix but was withdrawn over an unrelated false-corruption regression on expression indexes. verified-as-of: 2026-10-13[^c1-1][^c1-6][^c1-7] _(SQLite WAL checkpointing)_

## Disagreements & Open Questions

- Disagreement (SQLite WAL checkpointing): SQLite and Antithesis call the WAL-Reset race rare and unlikely in common use; Tailscale reports 19 corruption incidents in six months. The sources reconcile this by Tailscale's very aggressive manual checkpointing.[^c1-7][^c1-6]
- Disagreement (SQLite WAL checkpointing): Age of the bug: SQLite dates it to 3.7.0 (2010-07-21); Tailscale says at least 16 years. Consistent, but different framing.[^c1-1][^c1-6]
- Open (SQLite WAL checkpointing): Exact Tailscale checkpoint interval: a secondary report says every 250 ms; Tailscale's own post gives no number.
- Open (SQLite WAL checkpointing): Whether the SQLite wal2 branch (two alternating WAL files) is still unreleased; only seen in a search snippet, not fetched.
- Open (SQLite WAL checkpointing): Whether Syncthing adopted a connection-pool checkpointer; the thread only proposed it.
- Open (SQLite WAL checkpointing): Exact date of the Tailscale post; Antithesis post is dated 2026-08-12.

## References

### SQLite WAL checkpointing

[^c1-1]: https://www.sqlite.org/wal.html — Write-Ahead Logging (SQLite) (docs)
[^c1-2]: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — sqlite3_wal_checkpoint_v2 (docs)
[^c1-3]: https://www.sqlite.org/pragma.html — SQLite PRAGMA statements (docs)
[^c1-4]: https://litestream.io/guides/wal-truncate-threshold/ — Litestream: WAL Truncate Threshold Configuration (docs)
[^c1-5]: https://forum.syncthing.net/t/dealing-with-checkpoint-starvation/26121 — Syncthing forum: Dealing with checkpoint starvation (forum)
[^c1-6]: https://tailscale.com/blog/sqlite-wal-reset-bug — How Tailscale helped find the SQLite WAL-Reset bug (postmortem)
[^c1-7]: https://antithesis.com/blog/2026/wal-reset-bug/ — Antithesis: WAL-Reset bug (blog)
