# Haiku 5.5 repeats vs one Fable 5.1 run — SQLite WAL checkpointing

Reference: `claude__claude-fable-5-1__max` — 26 claims, 17 sources (8 orgs).

## Haiku 5.5 at `medium` — 5 runs, $0.439 total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 14 | 8 | 5 | 104 | 0.09 | 10/10 |
| r2 | 13 | 9 | 6 | 98 | 0.09 | 10/10 |
| r3 | 9 | 5 | 5 | 117 | 0.09 | 9/10 |
| r4 | 11 | 7 | 6 | 123 | 0.08 | 7/10 |
| r5 | 11 | 5 | 5 | 118 | 0.09 | 10/10 |

Union of all runs: 58 raw claims → 40 unique; 9 sources (7 shared with Fable); Fable claims covered/partial/missing = 3/15/8; 6 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims covered (mean, min–max) | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 5.4 (5–6) | 3.4 | 11.6 (9–14) | 2.2/26 (2–3) | 11.4 |
| 2 | 6.8 (6–7) | 3.7 | 21 (18–24) | 2.8/26 (2–3) | 14.4 |
| 3 | 7.7 (7–8) | 3.9 | 28.6 (26–32) | 3/26 (3–3) | 16.3 |
| 4 | 8.4 (8–9) | 4 | 34.8 (33–38) | 3/26 (3–3) | 17.4 |
| 5 | 9 (9–9) | 4 | 40 (40–40) | 3/26 (3–3) | 18 |

Fable claims no Haiku run stated:

- With PRAGMA synchronous=NORMAL in WAL mode the checkpoint is the only sync point: the WAL is fsynced before each checkpoint, the database file after each comple
- A single prepared SELECT that has been stepped to a row but not stepped to SQLITE_DONE or passed to sqlite3_reset() keeps its read transaction open and alone pi
- PRAGMA journal_size_limit (default -1, no limit) truncates the -wal file down to the limit each time a transaction commits or the WAL resets; 0 always truncates
- sqlite3_wal_hook() registers a callback invoked after each WAL-mode commit with the connection, the database name and the current number of WAL pages; the callb
- Passing NULL or an empty string as zDb to sqlite3_wal_checkpoint_v2() checkpoints every attached WAL database; pnLog and pnCkpt are then undefined, SQLITE_BUSY 
- Splitting long read work into short read transactions and issuing PRAGMA wal_checkpoint(RESTART) when starvation is detected cut Syncthing's WAL on a 2.5 GB dat
- SQLite describes the WAL-reset race as unlikely in common use and says its developers never reproduced it organically, only with a test hook. Tailscale neverthe
- The 3.51.3 fix is a single extra check: the checkpointer confirms, by comparing the WAL salt, that the WAL was not reset since the checkpoint began. Canonical's

Fable sources no Haiku run cited:

- antithesis.com/blog/2026/wal-reset-bug
- canonical.com/blog/hunting-a-16-year-old-sqlite-bug-with-tla-is-dqlite-affected
- fly.io/blog/sqlite-internals-wal
- forum.syncthing.net/t/syncthing-on-sqlite-help-test/23981?page=8
- litestream.io/tips
- sqlite.org/c3ref/wal_autocheckpoint.html
- sqlite.org/c3ref/wal_hook.html
- sqlite.org/forum/info/a188951b80292831794256a5c29f20f64f718d98ed0218bf44b51dd5907f1c39
- sqlite.org/releaselog/3_51_3.html
- tailscale.com/blog/sqlite-wal-reset-bug

## Haiku 5.5 at `max` — 5 runs, $3.935 total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 32 | 21 | 7 | 2046 | 0.88 | 10/10 |
| r2 | 26 | 17 | 7 | 1907 | 0.71 | 10/10 |
| r3 | 28 | 15 | 12 | 2144 | 0.92 | 10/10 |
| r4 | 35 | 19 | 7 | 1653 | 0.72 | 10/10 |
| r5 | 28 | 14 | 10 | 2971 | 0.71 | 10/10 |

Union of all runs: 149 raw claims → 106 unique; 16 sources (11 shared with Fable); Fable claims covered/partial/missing = 7/16/3; 30 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims covered (mean, min–max) | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 8.6 (7–12) | 4.6 | 29.8 (26–35) | 7/26 (7–7) | 19 |
| 2 | 11.1 (8–15) | 5.8 | 54 (49–58) | 7/26 (7–7) | 20.9 |
| 3 | 13 (9–16) | 6.7 | 74.1 (69–78) | 7/26 (7–7) | 21.7 |
| 4 | 14.6 (13–16) | 7.4 | 91.2 (90–94) | 7/26 (7–7) | 22.4 |
| 5 | 16 (16–16) | 8 | 106 (106–106) | 7/26 (7–7) | 23 |

Fable claims no Haiku run stated:

- A single prepared SELECT that has been stepped to a row but not stepped to SQLITE_DONE or passed to sqlite3_reset() keeps its read transaction open and alone pi
- After VACUUM in WAL mode, run PRAGMA wal_checkpoint(TRUNCATE) to move the rebuilt pages into the database and shrink the -wal file; otherwise the space has only
- Splitting long read work into short read transactions and issuing PRAGMA wal_checkpoint(RESTART) when starvation is detected cut Syncthing's WAL on a 2.5 GB dat

Fable sources no Haiku run cited:

- fly.io/blog/sqlite-internals-wal
- forum.syncthing.net/t/syncthing-on-sqlite-help-test/23981?page=8
- litestream.io/tips
- photostructure.com/coding/how-to-vacuum-sqlite
- sqlite.org/c3ref/wal_hook.html
- sqlite.org/forum/info/a188951b80292831794256a5c29f20f64f718d98ed0218bf44b51dd5907f1c39

## Full gate (Opus 5.5 medium, every non-tentative claim)

| set | claims | gated | SUPPORTED | OVERSTATED | NOT-IN-SOURCE | CONTRADICTED | UNVERIFIED | $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fable-max | 26 | 22 | 22 | 0 | 0 | 0 | 0 | 0.89 |
| medium-union-dedup | 40 | 20 | 20 | 0 | 0 | 0 | 0 | 0.83 |
| medium-r1 | 14 | 12 | 12 | 0 | 0 | 0 | 0 | 0.47 |
| max-union-dedup | 106 | 24 | 24 | 0 | 0 | 0 | 0 | 1.0 |
| max-r1 | 32 | 24 | 24 | 0 | 0 | 0 | 0 | 0.82 |
