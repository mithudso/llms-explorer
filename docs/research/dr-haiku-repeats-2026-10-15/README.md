# How many Haiku 5.5 `/dr` runs equal one Fable 5.1 run? — 2026-10-15

Question: Fable 5.1 pulled more sources and validated harder than Haiku 5.5 in the
[2026-10-13 model matrix](../dr-model-matrix-2026-10-13/README.md). If Haiku ran the same concept
five times and the results were merged, would the union reach Fable's level?

Short answer: **no at `medium` effort, and only on breadth at `max` effort.**

- Five Haiku `medium` runs ($0.44 total) reach 9 sources against Fable's 17, never cite the
  postmortem/blog tier Fable found, state only 3 of Fable's 26 claims fully (18 at least
  partially), and 2 of the 5 runs shipped contradicted claims.
- Five Haiku `max` runs ($3.94 total, about the cost of the one Fable run at $3.73) reach 16
  sources (Fable 17), produce 106 unique claims (Fable 26), and 30 facts Fable did not have. But
  they state only 7 of Fable's 26 claims with Fable's specifics; 16 are partial and 3 are missing.
  No run after the first adds a fully matched Fable claim. Repeats add breadth, not depth.
- Accuracy: Fable and Haiku `max` had zero flawed claims in every gate. Haiku `medium` produced 3
  CONTRADICTED claims in 50 gated (overstated: "four checkpoint modes", "PASSIVE never shrinks the
  WAL"). More `medium` runs add those errors to the union; they do not cancel them.

The gap between Haiku and Fable on this concept is per-claim precision (conditions, exact API
semantics, numbers from postmortems), not the number of facts found. Running Haiku more times
cannot close that gap. The staged pipeline from the matrix (Sonnet discovers, Haiku extracts per
source, a validator checks every claim; see
[KNOW-660](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-660)) is the cheaper lever.

## Method

- **Concept and brief:** "SQLite WAL checkpointing" (topic "SQLite write-ahead logging (WAL)"),
  depth `standard`, the identical `dr_run.py` worker brief as every matrix cell.
- **Reference:** the matrix cell `claude__claude-fable-5-1__max` (26 claims, 15 high confidence,
  17 sources from 8 organisations, 534 s, $3.73), copied to `reference/`.
- **Repeats:** 5 fresh Haiku 5.5 cells at `medium` (the production default per
  [KNOW-641](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-641)) and 5 at `max`, each
  with its own `HUB_DIR`, run by `scripts/dr_haiku_repeats.py run` through the matrix harness
  (`scripts/dr_model_matrix.py run_cell`). All 10 ran at once; two `max` cells hit the 40-minute
  agent timeout and were re-run with a 70-minute limit.
- **Judge:** one Opus 5.5 `medium` call per effort level, no tools. It maps every Fable claim to
  the 5-run union (covered = same fact with the same specifics; partial = weaker or narrower;
  missing) and clusters duplicate union claims. Because every union claim carries its run number,
  the script computes, for k = 1..5, the mean, min and max over every k-subset of runs of union
  sources, unique claims and Fable claims covered. Prompts and verdicts: `score/<effort>/`.
- **Gates:** every cell got the matrix's fixed 10-claim blind gate (Opus 5.5 `medium`). The
  deduped 5-run union per effort, the first run per effort and the Fable reference also went
  through the gate with `--sample all` on a throwaway saturate-depth run (`gates/<name>/`). The
  gate skips claims rendered "Tentative:" (confidence low) and stopped at 20–24 verdicts even when
  83 non-tentative claims were offered, so "full gate" below means a 20–24 claim sample.

## Results

Reference: Fable 5.1 `max` — 26 claims (15 high), 17 sources, 8 orgs, 534 s, $3.73, 10/10 on the
matrix gate, 22/22 SUPPORTED on the full gate.

### Haiku 5.5 `medium` — 5 runs, $0.44 research total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 14 | 8 | 5 | 104 | 0.09 | 10/10 |
| r2 | 13 | 9 | 6 | 98 | 0.09 | 10/10 |
| r3 | 9 | 5 | 5 | 117 | 0.09 | 9/10 (1 CONTRADICTED) |
| r4 | 11 | 7 | 6 | 123 | 0.08 | 7/10 (2 CONTRADICTED, 1 UNVERIFIED) |
| r5 | 11 | 5 | 5 | 118 | 0.09 | 10/10 |

Union of 5: 58 raw claims → 40 unique; 9 sources (4 orgs), 7 shared with Fable; Fable claims
covered / partial / missing = 3 / 15 / 8; 6 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims fully covered | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 5.4 (5–6) | 3.4 | 11.6 (9–14) | 2.2/26 (2–3) | 11.4/26 |
| 2 | 6.8 (6–7) | 3.7 | 21 (18–24) | 2.8/26 (2–3) | 14.4/26 |
| 3 | 7.7 (7–8) | 3.9 | 28.6 (26–32) | 3/26 | 16.3/26 |
| 4 | 8.4 (8–9) | 4.0 | 34.8 (33–38) | 3/26 | 17.4/26 |
| 5 | 9 | 4.0 | 40 | 3/26 | 18/26 |

Fable sources no `medium` run cited in 5 tries (10 of 17): tailscale.com postmortem,
antithesis.com and canonical.com write-ups, fly.io WAL internals, the sqlite.org forum thread,
litestream.io/tips, `wal_autocheckpoint.html`, `wal_hook.html`, release log 3.51.3, Syncthing
thread page 8. The union never left the docs + one forum thread tier.

Fable claims no `medium` run stated (8): the `synchronous=NORMAL` sync points; a stepped-but-not-
reset prepared statement pinning the WAL; `journal_size_limit` semantics; `sqlite3_wal_hook()`;
NULL `zDb` in `wal_checkpoint_v2`; Syncthing's RESTART remedy and its numbers; SQLite's own
assessment of the WAL-reset race; the 3.51.3 salt-check fix.

### Haiku 5.5 `max` — 5 runs, $3.94 research total

| run | claims | high | sources | s | $ | gate-10 |
|---|---:|---:|---:|---:|---:|---|
| r1 | 32 | 21 | 7 | 2046 | 0.88 | 10/10 |
| r2 | 26 | 17 | 7 | 1907 | 0.71 | 10/10 |
| r3 | 28 | 15 | 12 | 2144 | 0.92 | 10/10 |
| r4 | 35 | — | 7 | 1653 | 0.72 | 10/10 |
| r5 | 28 | — | 10 | 2971 | 0.71 | 10/10 |

Wall time is 2–5× the matrix's single Haiku `max` run (984 s) because ten agents ran at once.

Union of 5: 149 raw claims → 106 unique (74 appear in one run only, 9 in three or more);
16 sources (8 orgs), 11 shared with Fable; Fable claims covered / partial / missing = 7 / 16 / 3;
30 facts Fable did not have.

| k runs | sources (mean, min–max) | orgs | unique claims (mean, min–max) | Fable claims fully covered | covered or partial |
|---:|---|---:|---|---|---:|
| 1 | 8.6 (7–12) | 4.6 | 29.8 (26–35) | 7/26 | 19/26 |
| 2 | 11.1 (8–15) | 5.8 | 54 | 7/26 | 20.9/26 |
| 3 | 13 (9–16) | 6.7 | 74.1 | 7/26 | 21.7/26 |
| 4 | 14.6 (13–16) | 7.4 | 91.2 | 7/26 | 22.4/26 |
| 5 | 16 | 8.0 | 106 | 7/26 | 23/26 |

Fable sources no `max` run cited (6 of 17): fly.io WAL internals, litestream.io/tips,
`wal_hook.html`, the sqlite.org forum thread, Syncthing thread page 8, photostructure.com VACUUM
guide. New sources Fable lacked: release logs 3.52.0 and 3.53.0, litestream config reference,
a Register article, an ICPADS paper page.

Fable claims no `max` run stated (3): the stepped prepared statement pinning the WAL; VACUUM
followed by `wal_checkpoint(TRUNCATE)`; Syncthing's RESTART remedy with its 2.5 GB figure.

### Full gate (Opus 5.5 `medium`, `--sample all`, tentative claims skipped)

| set | claims | gated | SUPPORTED | flaws | $ |
|---|---:|---:|---:|---|---:|
| Fable `max` | 26 | 22 | 22 | 0 | 0.89 |
| Haiku `medium` r1 | 14 | 12 | 12 | 0 | 0.47 |
| Haiku `medium` union of 5 (dedup) | 40 | 20 | 20 | 0 | 0.83 |
| Haiku `max` r1 | 32 | 24 | 24 | 0 | 0.82 |
| Haiku `max` union of 5 (dedup) | 106 | 24 | 24 | 0 | 1.00 |

The union gates sampled 20–24 claims and did not pick the three `medium` claims the per-run
gates contradicted, so the per-run gates (50 verdicts per effort) are the better accuracy
measure: `medium` 47 SUPPORTED / 3 CONTRADICTED / 1 UNVERIFIED, `max` 50 / 0 / 0.

## What the numbers say

1. **Breadth is reachable, precision is not.** Two Haiku `max` runs match Fable's source count on
   average (11.1, but 8–15 depending on which two), four runs do it reliably (13–16). A single
   Haiku `max` run already yields more unique claims than Fable. Yet the count of Fable claims
   stated with Fable's specifics is flat at 7 from k = 1 to k = 5. Fable packs a condition, an
   exact API behaviour and a number into one claim; Haiku states the headline and stops.
2. **`medium` is a different tier, not a cheaper Fable.** Five runs never reached the postmortem
   and blog sources, stated 3 of 26 Fable claims fully, and produced contradicted claims in 2 of 5
   runs. Its cost ($0.44 for five) buys a docs-page summary, not research.
3. **Repeats are mostly disjoint at `max`.** 74 of 106 unique claims came from one run only, so
   the union keeps growing almost linearly (30 → 54 → 74 → 91 → 106). That is useful breadth, but
   the 30 extras Fable lacked were read from release logs and secondary articles, not from the
   primary postmortems Fable favoured.
4. **Cost and time.** Five Haiku `max` runs cost the same as one Fable run and took five times
   the wall clock per run. Five `medium` runs cost 12% of a Fable run.

## Limits

- One concept, one Fable reference run. The matrix shows ±1 gate verdict is noise; treat the
  coverage counts as directional, not as a per-concept constant.
- The coverage judge is Opus 5.5 reading claim text only. "Covered" is strict on purpose (same
  specifics); "covered or partial" is the lenient reading. Both are reported.
- The gate's `--sample all` yielded 20–24 verdicts regardless of set size, and it skips tentative
  claims. Flaw rates on the unions are therefore sampled, not exhaustive.
- The 10-way parallel run inflated Haiku `max` wall time and may have inflated cost ($0.71–0.92
  vs $0.46 for the single matrix run). Claim counts were in the matrix's range (26 at the time).
- The Fable reference ran on 2026-10-13; the Haiku cells ran on 2026-10-15 against live pages.

## Reproduce

```bash
python3 scripts/dr_haiku_repeats.py run --efforts medium,max --repeats 5 --parallel 10
python3 scripts/dr_haiku_repeats.py score --efforts medium,max     # judge + full gates (cached)
python3 scripts/dr_haiku_repeats.py report                         # results.md / score.json
```

Raw per-cell data: `cells/<id>/result.json`, `cells/<id>/hub/research/bench/claims/*.json` and
`gate.json`. Judge prompts and verdicts: `score/<effort>/`. Full-gate runs: `gates/<name>/`.
