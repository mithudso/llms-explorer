# Opus 5.5 repeats vs one Fable 5.1 run — SQLite WAL checkpointing

Reference: `claude__claude-fable-5-1__max` — 26 claims, 17 sources (8 orgs).

## Opus 5.5 at `medium` — 5 runs, $3.274 total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 19 | 9 | 6 | 191 | 0.72 | 10/10 |
| r2 | 15 | 9 | 8 | 212 | 0.69 | 10/10 |
| r3 | 12 | 6 | 6 | 139 | 0.55 | 10/10 |
| r4 | 17 | 11 | 6 | 195 | 0.66 | 10/10 |
| r5 | 19 | 10 | 8 | 179 | 0.65 | 10/10 |

Union of all runs: 82 raw claims → 39 unique; 11 sources (8 shared with Fable); Fable claims covered/partial/missing = 1/20/5; 6 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims covered (mean, min–max) | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 6.8 (6–8) | 3.4 | 16.4 (12–19) | 0.4/26 (0–1) | 17 |
| 2 | 8.3 (7–10) | 4.2 | 25.3 (22–29) | 0.7/26 (0–1) | 19.2 |
| 3 | 9.3 (8–11) | 4.8 | 31 (27–34) | 0.9/26 (0–1) | 20.1 |
| 4 | 10.2 (9–11) | 5.4 | 35.4 (33–37) | 1/26 (1–1) | 20.6 |
| 5 | 11 (11–11) | 6 | 39 (39–39) | 1/26 (1–1) | 21 |

Fable claims no Opus 5.5 run stated:

- A single prepared SELECT that has been stepped to a row but not stepped to SQLITE_DONE or passed to sqlite3_reset() keeps its read transaction open and alone pi
- After VACUUM in WAL mode, run PRAGMA wal_checkpoint(TRUNCATE) to move the rebuilt pages into the database and shrink the -wal file; otherwise the space has only
- Splitting long read work into short read transactions and issuing PRAGMA wal_checkpoint(RESTART) when starvation is detected cut Syncthing's WAL on a 2.5 GB dat
- The 3.51.3 fix is a single extra check: the checkpointer confirms, by comparing the WAL salt, that the WAL was not reset since the checkpoint began. Canonical's
- Practical hardening for applications that drive checkpoints themselves: upgrade to SQLite 3.51.3 or later; disable auto-checkpoint on every connection if one co

Fable sources no Opus 5.5 run cited:

- canonical.com/blog/hunting-a-16-year-old-sqlite-bug-with-tla-is-dqlite-affected
- fly.io/blog/sqlite-internals-wal
- forum.syncthing.net/t/syncthing-on-sqlite-help-test/23981?page=8
- photostructure.com/coding/how-to-vacuum-sqlite
- sqlite.org/c3ref/wal_autocheckpoint.html
- sqlite.org/c3ref/wal_hook.html
- sqlite.org/forum/info/a188951b80292831794256a5c29f20f64f718d98ed0218bf44b51dd5907f1c39
- sqlite.org/releaselog/3_51_3.html
- tailscale.com/blog/sqlite-wal-reset-bug

## Opus 5.5 at `max` — 5 runs, $14.739 total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 29 | 23 | 18 | 922 | 2.99 | 10/10 |
| r2 | 35 | 19 | 19 | 840 | 2.61 | 10/10 |
| r3 | 29 | 20 | 18 | 932 | 2.69 | 10/10 |
| r4 | 32 | 27 | 17 | 760 | 2.77 | 10/10 |
| r5 | 36 | 25 | 21 | 1086 | 3.68 | 10/10 |

Union of all runs: 161 raw claims → 120 unique; 42 sources (14 shared with Fable); Fable claims covered/partial/missing = 5/20/1; 47 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims covered (mean, min–max) | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 18.6 (17–21) | 8.4 | 32.2 (29–36) | 1/26 (0–2) | 19 |
| 2 | 26.8 (24–30) | 11.5 | 59.3 (53–64) | 2/26 (0–4) | 21.2 |
| 3 | 32.5 (29–36) | 13.9 | 82.4 (77–88) | 3/26 (1–5) | 22.6 |
| 4 | 37.4 (35–40) | 16 | 102.4 (98–106) | 4/26 (3–5) | 23.8 |
| 5 | 42 (42–42) | 18 | 120 (120–120) | 5/26 (5–5) | 25 |

Fable claims no Opus 5.5 run stated:

- Splitting long read work into short read transactions and issuing PRAGMA wal_checkpoint(RESTART) when starvation is detected cut Syncthing's WAL on a 2.5 GB dat

Fable sources no Opus 5.5 run cited:

- forum.syncthing.net/t/syncthing-on-sqlite-help-test/23981?page=8
- sqlite.org/releaselog/3_51_3.html
- tailscale.com/blog/sqlite-wal-reset-bug

## Full gate (Opus 5.5 medium, every non-tentative claim)

| set | claims | gated | SUPPORTED | OVERSTATED | NOT-IN-SOURCE | CONTRADICTED | UNVERIFIED | $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fable-max | 26 | 24 | 21 | 0 | 0 | 0 | 3 | 0.84 |
| medium-union-dedup | 39 | 22 | 22 | 0 | 0 | 0 | 0 | 0.85 |
| medium-r1 | 19 | 14 | 14 | 0 | 0 | 0 | 0 | 0.7 |
| max-union-dedup | 120 | 41 | 40 | 0 | 0 | 1 | 0 | 1.49 |
| max-r1 | 29 | 23 | 23 | 0 | 0 | 0 | 0 | 0.81 |
