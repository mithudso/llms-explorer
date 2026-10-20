# Sonnet 5.5 repeats vs one Fable 5.1 run — SQLite WAL checkpointing

Reference: `claude__claude-fable-5-1__max` — 26 claims, 17 sources (8 orgs).

## Sonnet 5.5 at `medium` — 5 runs, $1.326 total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 9 | 6 | 5 | 96 | 0.22 | 10/10 |
| r2 | 13 | 7 | 5 | 131 | 0.29 | 10/10 |
| r3 | 12 | 7 | 5 | 229 | 0.3 | 10/10 |
| r4 | 11 | 8 | 7 | 117 | 0.24 | 10/10 |
| r5 | 12 | 6 | 6 | 132 | 0.28 | 10/10 |

Union of all runs: 57 raw claims → 20 unique; 12 sources (6 shared with Fable); Fable claims covered/partial/missing = 1/20/5; 3 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims covered (mean, min–max) | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 5.6 (5–7) | 3.6 | 11.4 (9–13) | 0.4/26 (0–1) | 14.4 |
| 2 | 7.8 (6–10) | 4.5 | 15 (13–18) | 0.7/26 (0–1) | 17.9 |
| 3 | 9.4 (8–11) | 5.1 | 17.2 (15–19) | 0.9/26 (0–1) | 19.3 |
| 4 | 10.8 (10–12) | 5.6 | 18.8 (17–20) | 1/26 (1–1) | 20.2 |
| 5 | 12 (12–12) | 6 | 20 (20–20) | 1/26 (1–1) | 21 |

Fable claims no Sonnet 5.5 run stated:

- A checkpoint copies committed WAL frames into the main database file. When several frames hold versions of the same page, only the newest version is written; su
- After VACUUM in WAL mode, run PRAGMA wal_checkpoint(TRUNCATE) to move the rebuilt pages into the database and shrink the -wal file; otherwise the space has only
- Passing NULL or an empty string as zDb to sqlite3_wal_checkpoint_v2() checkpoints every attached WAL database; pnLog and pnCkpt are then undefined, SQLITE_BUSY 
- Litestream holds a long-running read transaction between its own checkpoints so no other process can checkpoint and restart the WAL before it has copied the fra
- The 3.51.3 fix is a single extra check: the checkpointer confirms, by comparing the WAL salt, that the WAL was not reset since the checkpoint began. Canonical's

Fable sources no Sonnet 5.5 run cited:

- antithesis.com/blog/2026/wal-reset-bug
- canonical.com/blog/hunting-a-16-year-old-sqlite-bug-with-tla-is-dqlite-affected
- fly.io/blog/sqlite-internals-wal
- litestream.io/how-it-works
- litestream.io/tips
- photostructure.com/coding/how-to-vacuum-sqlite
- sqlite.org/c3ref/wal_autocheckpoint.html
- sqlite.org/c3ref/wal_hook.html
- sqlite.org/forum/info/a188951b80292831794256a5c29f20f64f718d98ed0218bf44b51dd5907f1c39
- sqlite.org/releaselog/3_51_3.html
- tailscale.com/blog/sqlite-wal-reset-bug

## Sonnet 5.5 at `max` — 5 runs, $10.23 total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 30 | 18 | 18 | 861 | 2.09 | 10/10 |
| r2 | 39 | 25 | 14 | 875 | 2.14 | 10/10 |
| r3 | 32 | 19 | 17 | 854 | 1.87 | 10/10 |
| r4 | 42 | 17 | 21 | 923 | 1.89 | 10/10 |
| r5 | 29 | 17 | 21 | 997 | 2.25 | 10/10 |

Union of all runs: 172 raw claims → 84 unique; 35 sources (13 shared with Fable); Fable claims covered/partial/missing = 16/9/1; 24 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims covered (mean, min–max) | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 18.2 (14–21) | 8.2 | 34.2 (29–41) | 13.2/26 (12–14) | 21.2 |
| 2 | 24.3 (20–27) | 9.5 | 52.9 (47–60) | 14.8/26 (14–15) | 23.2 |
| 3 | 28.6 (27–32) | 10.4 | 66.4 (62–72) | 15.4/26 (15–16) | 24 |
| 4 | 32 (31–35) | 11.2 | 76.4 (74–81) | 15.8/26 (15–16) | 24.6 |
| 5 | 35 (35–35) | 12 | 84 (84–84) | 16/26 (16–16) | 25 |

Fable claims no Sonnet 5.5 run stated:

- Splitting long read work into short read transactions and issuing PRAGMA wal_checkpoint(RESTART) when starvation is detected cut Syncthing's WAL on a 2.5 GB dat

Fable sources no Sonnet 5.5 run cited:

- fly.io/blog/sqlite-internals-wal
- forum.syncthing.net/t/syncthing-on-sqlite-help-test/23981?page=8
- sqlite.org/forum/info/a188951b80292831794256a5c29f20f64f718d98ed0218bf44b51dd5907f1c39
- tailscale.com/blog/sqlite-wal-reset-bug

## Full gate (Opus 5.5 medium, every non-tentative claim)

| set | claims | gated | SUPPORTED | OVERSTATED | NOT-IN-SOURCE | CONTRADICTED | UNVERIFIED | $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fable-max | 26 | 24 | 22 | 0 | 0 | 0 | 2 | 0.83 |
| medium-union-dedup | 20 | 19 | 19 | 0 | 0 | 0 | 0 | 0.63 |
| medium-r1 | 9 | 12 | 12 | 0 | 0 | 0 | 0 | 0.58 |
| max-union-dedup | 84 | 51 | 49 | 0 | 0 | 0 | 2 | 1.35 |
| max-r1 | 30 | 22 | 22 | 0 | 0 | 0 | 0 | 0.73 |
