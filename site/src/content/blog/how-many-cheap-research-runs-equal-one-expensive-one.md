---
title: "How many cheap research runs equal one expensive one?"
description: "Three experiments, one concept, 47 Claude research runs: repeats buy breadth that keeps growing and precision that stops after the first run or two; Sonnet max and Fable max turn out to be peers per run at half the price. Why 100 shallow concepts are not worth one deep one."
date: "2026-10-20"
tags: [research, evaluation, models, cost]
sources:
  - docs/research/dr-model-matrix-2026-10-13/README.md
  - docs/research/dr-haiku-repeats-2026-10-15/README.md
  - docs/research/dr-model-repeats-2026-10-20/README.md
  - scripts/dr_model_matrix.py
  - scripts/dr_haiku_repeats.py
---

<!-- verified-as-of: 2026-10-20 · every number below is read from the committed result.json, score.json and gate-result.json files under docs/research/ -->

## The question

Every concept pack in this estate is written by a `/dr` research run: an agent reads the
web, writes claims with sources, and a separate blind gate re-fetches the cited pages and
marks each claim SUPPORTED, UNVERIFIED, NOT-IN-SOURCE or CONTRADICTED. The run has two dials
that set its price: the model and the effort level. Fable 5.1 at `max` costs about $3.70 a
concept. Haiku 5.5 at `medium` costs nine cents.

The obvious question is whether the cheap dial, turned several times, adds up to the
expensive one. If five Haiku runs on the same concept, merged, equal one Fable run, the
frontier queue of several hundred unresearched concepts gets forty times cheaper. If they do
not, it matters *what* is missing, because "more claims" and "better claims" are not the
same thing, and a queue manager that pays for the wrong one is wasting money either way.

This post reports three experiments on one concept, 47 Claude research runs in all, and ends
with the buying rule they imply. Everything is reproducible from the two scripts in the
sources list; the raw per-run data is committed.

## The setup

One concept throughout: **"SQLite WAL checkpointing"** (topic "SQLite write-ahead logging"),
depth `standard`. It is a good test concept because the answer space has a shape. There is a
docs tier (`wal.html`, the pragma pages, the C API), a postmortem tier (Tailscale's WAL-reset
outage, Antithesis's and Canonical's reproductions, the 3.51.3 fix), and an internals tier
(`wal.c`, the wal-index format, the wal2 design doc). A shallow run stops at the first tier.

- **Brief:** the identical worker brief from `dr_run.py` for every cell.
- **Isolation:** each run has its own `HUB_DIR`; nothing leaks between cells.
- **Reference:** the Fable 5.1 `max` run from the first experiment — 26 claims, 17 sources from
  8 organisations, 534 s, $3.73, 10/10 on the gate.
- **Gate:** Opus 5.5 at `medium`, no tools except fetching the cited page, 10 sampled claims
  per run and every non-tentative claim for the merged unions.
- **Coverage judge (experiments 2 and 3):** one Opus 5.5 call that maps each of the 26 Fable
  claims to a candidate's merged claims as *covered* (same fact, same specifics: numbers,
  versions, names, conditions), *partial* (headline right, a specific dropped) or *missing*.
  It also clusters duplicate candidate claims, so "unique claims" below means clusters.

"Covered" is the strict measure and the one that matters for a pack someone will query.
Fable's claims tend to pack a condition, an exact API behaviour and a number into one
sentence: *with `synchronous=NORMAL` in WAL mode the checkpoint is the only sync point, so a
transaction can roll back after power loss.* A user with a production WAL problem needs that
conjunction, not its three headlines.

## Experiment 1: one run per model and effort

Twelve Claude cells, one run each (the full matrix also had OpenAI, Antigravity and local
lanes; this post keeps to Claude).

| Model | Effort | Research s | Claims | High-conf | Sources | Gate | $ |
|---|---|---:|---:|---:|---:|---|---:|
| Haiku 5.5 | low | 174 | 12 | 5 | 5 | 10/10 | 0.08 |
| Haiku 5.5 | high | 211 | 15 | 11 | 7 | 9/10 | 0.12 |
| Haiku 5.5 | max | 984 | 26 | 16 | 10 | 10/10 | 0.46 |
| Sonnet 5.5 | low | 66 | 8 | 1 | 3 | 9/10 | 0.24 |
| Sonnet 5.5 | high | 158 | 14 | 7 | 7 | 10/10 | 0.45 |
| Sonnet 5.5 | max | 948 | 39 | 24 | 16 | 10/10 | 2.43 |
| Opus 5.5 | low | 87 | 9 | 5 | 7 | 9/10 | 0.40 |
| Opus 5.5 | high | 161 | 15 | 8 | 8 | 10/10 | 0.77 |
| Opus 5.5 | max | 919 | 28 | 22 | 16 | 10/10 | 3.12 |
| Fable 5.1 | low | 166 | 13 | 10 | 6 | 10/10 | 1.69 |
| Fable 5.1 | high | 257 | 21 | 10 | 9 | 10/10 | 2.04 |
| Fable 5.1 | max | 534 | 26 | 15 | 17 | 10/10 | 3.73 |

Two things stood out. Effort buys breadth, not accuracy: low to `max` raised claims two to
five times and sources two to three times, and the gate rate stayed at 90–100 % throughout.
No Claude cell produced a CONTRADICTED claim at any effort (the contradictions in the full
matrix came from the Gemini and local lanes). And at `max`, Sonnet found the most claims,
Fable the most sources, and Fable was fastest.

A gate that samples 10 claims cannot see depth, though. Haiku `max` at 26 claims and Fable
`max` at 26 claims both score 10/10. Whether they are the *same* 26 claims is the next
experiment.

## Experiment 2: five Haiku runs against one Fable run

Five fresh Haiku 5.5 runs at `medium` (the production default) and five at `max`, merged,
judged against the 26 Fable claims. The judge tags every merged claim with its run number, so
the harness can compute, for k = 1..5, the mean over every k-subset of runs.

| k runs | `medium`: sources | unique claims | Fable covered | covered or partial | `max`: sources | unique claims | Fable covered | covered or partial |
|--:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5.4 | 11.6 | 2.2 / 26 | 11.4 | 8.6 | 29.8 | 7 / 26 | 19.0 |
| 2 | 6.8 | 21.0 | 2.8 | 14.4 | 11.1 | 54.0 | 7 | 20.9 |
| 3 | 7.7 | 28.6 | 3.0 | 16.3 | 13.0 | 74.1 | 7 | 21.7 |
| 4 | 8.4 | 34.8 | 3.0 | 17.4 | 14.6 | 91.2 | 7 | 22.4 |
| 5 | 9 | 40 | 3 | 18 | 16 | 106 | 7 | 23 |

Five Haiku `max` runs cost $3.94 — the price of the one Fable run — and reach Fable's source
count (16 vs 17) and four times its unique claim count (106 vs 26). The count of Fable claims
stated with Fable's specifics is **7 from k = 1 to k = 5**. Not one repeat added a fully
matched claim. The 16 partials are the compound claims with one piece missing; the 3 missing
ones are the stepped-but-not-reset prepared statement that pins the WAL, VACUUM followed by
`wal_checkpoint(TRUNCATE)`, and Syncthing's RESTART remedy with its 2.5 GB figure.

`medium` is a different tier, not a cheaper `max`. Five runs never left the docs pages plus
one forum thread, stated 3 of 26 Fable claims fully, and two of the five shipped CONTRADICTED
claims ("four checkpoint modes", "PASSIVE never shrinks the WAL"). Repeats at `medium` add
those errors to the union; they do not cancel them.

## Experiment 3: five Sonnet and five Opus runs

Same design, run a week later: five Sonnet 5.5 and five Opus 5.5 runs at `medium` and at
`max`, 20 runs, all 20 at 10/10 on the per-run gate.

| `max` | $ / run | 1 run: Fable covered | ≥ partial | sources | 5-run union: covered | ≥ partial | sources | unique claims | facts Fable lacked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Haiku 5.5 | 0.79 | 7.0 | 19.0 | 8.6 | 7 | 23 | 16 | 106 | 30 |
| Sonnet 5.5 | 2.05 | **13.2** | 21.2 | 18.2 | 16 | 25 | 35 | 84 | 24 |
| Opus 5.5 | 2.95 | 1.0 | 19.0 | 18.6 | 5 | 25 | **42** | **120** | **47** |
| Fable 5.1 | 3.73 | 26 | 26 | 17 | — | — | — | — | — |

The Haiku `$ / run` is from its ten-way parallel batch; its single matrix cell cost $0.46.

**Sonnet.** One `max` run states half of Fable's claims with Fable's specifics and already
beats Fable on breadth: 18 sources, 34 claims. Two runs, which is the same spend as one Fable
run, reach 15 of 26 covered and 23 at least partial. Five runs plateau at 16 and 25. The
residue is the same shape as Haiku's — Fable's compound claims with one specific dropped —
at half the size. Sonnet's extras are not restatements either: `wal.c`'s `iCallback` rule for
when the auto-checkpoint hook fires, Antithesis's 15-minute reproduction on 3.51.2, Phil
Eaton's `mxFrame = 360 → 0` trace, Firefox's 1.5 MiB `SQLITE_DEFAULT_JOURNAL_SIZE_LIMIT`,
Android's `db_wal_autocheckpoint`.

**Opus** is the surprise in the table. Five runs read 42 sources — raw `wal.c`,
`walformat.html`, the wal2 design doc, Rails' `sqlite3_adapter.rb`, Litestream issue #547,
SQLite forum posts — and wrote 120 unique claims with 47 facts Fable never had. And the judge
scored it 5 of 26 covered. A second, independent judge pass said 5 again (Haiku 6, Sonnet 15,
so the judge is stable to ±1). The number is real. It is also misleading.

### Why Opus scores low: claim granularity

Mean claim length over the five `max` runs: Fable 425 characters, Sonnet 402, Opus 360,
Haiku 230. Opus writes atomic claims. Fable's auto-checkpoint claim has six specifics
(PASSIVE; runs in the committing thread; at 1000 pages; `SQLITE_DEFAULT_WAL_AUTOCHECKPOINT`;
about 4 MB at 4096-byte pages; per connection, ≤ 0 disables). Three Opus claims together
state all six. No single one does. The judge rule was "at least one candidate claim states the
whole fact", so it marked the claim partial.

A third judge pass with a joint rule — the listed claims, *taken together*, state every
specific — gives Haiku 4, Sonnet 14, Opus **12**. Sonnet is stable under both rules because
it writes compound claims the way Fable does. Opus doubles. Haiku drops, because its partials
were missing the specifics, not splitting them.

| 5-run `max` union | strict, pass 1 | strict, pass 2 | joint |
|---|---:|---:|---:|
| Haiku 5.5 | 7 | 6 | 4 |
| Sonnet 5.5 | 16 | 15 | 14 |
| Opus 5.5 | 5 | 5 | 12 |

Judge self-preference (Opus judging Opus) would have pushed the other way, so bias is not the
explanation. The lesson for anyone building a coverage judge is that the strict rule measures
"did the candidate write the reference's claim", not "did it find the reference's facts", and
the two diverge as soon as models granulate differently. Report both.

### The mirror test: is Fable actually the deepest?

Everything above asks one question — how much of Fable did the other model reproduce — and
Fable scores 26/26 by construction. A reviewer pointed out that this design cannot show Fable
is the best run, only that it is the yardstick. So the judge was run the other way: Fable's 26
claims as the candidate, each model's output as the reference, same strict rule.

| Reference | Reference claims | Fable states fully | partial | missing | Reference states Fable fully (from above) |
|---|---:|---:|---:|---:|---:|
| Haiku `max`, run 1 | 32 | **22** | 9 | 1 | 7 / 26 |
| Sonnet `max`, run 1 | 30 | **14** | 14 | 2 | ~13 / 26 |
| Opus `max`, run 1 | 29 | **13** | 11 | 5 | 1 / 26 strict (atomic claims) |
| Haiku 5-run union | 106 | 66 | 31 | 9 | 7 / 26 |
| Sonnet 5-run union | 84 | 19 | 56 | 9 | 16 / 26 |
| Opus 5-run union | 120 | 34 | 75 | 11 | 5 strict, 12 joint |

Fable dominates Haiku in both directions: it states 22 of Haiku's 32 claims exactly, Haiku
states 7 of Fable's 26. Fable and Sonnet are **peers**: each states about half of the other's
claims with the other's specifics and nearly all of them at least partially, and Sonnet's run
cost $2.05 to Fable's $3.73. Against Opus, Fable misses 5 of 29 claims outright — more than
Opus misses of Fable's under the joint rule — and against the five-run unions Fable states most
Sonnet and Opus claims only partially, which means those unions carry specifics Fable's run
does not. Fable's real edge is that it is the fastest `max` run (534 s against 900–1,000) and
the most compact: 26 compound claims that say what 30–40 of the others' say.

That changes the buying rule below. Fable is not "the precise one"; Sonnet at `max` is as
precise per run at 55 % of the price, and two Sonnet runs beat one Fable run on every axis
measured here.

### `medium` at every model

Five Sonnet `medium` runs ($1.33 total) and five Opus `medium` runs ($3.27) each cover 1 of
26 Fable claims fully. Haiku `medium` covered 3. All three stop at the docs tier; none reached
the Tailscale, Antithesis or Canonical write-ups in five tries. Sonnet's five `medium` runs
collapsed to 20 unique claims — the same 20 facts, five times — while Opus's gave 39, so Opus
`medium` repeats are more disjoint but no deeper.

## What grows and what does not

Across all three models at `max`, the sources and unique-claim curves climb almost linearly
with k. Repeats are near-disjoint: Sonnet's 172 raw claims dedupe to 84, Opus's 161 to 120,
Haiku's 149 to 106. That is useful breadth.

Every "covered" curve flattens by k = 2 or 3. Haiku's is flat from k = 1. The thing that
answers a precise question — the conjunction of condition, API and number — is set by the
model on its first pass through the sources and does not accumulate. A model that drops the
`synchronous=NORMAL` condition once drops it every time.

Accuracy is not where the tiers differ at `max`. 150 per-run gate verdicts across the three
models' `max` cells: 150 SUPPORTED. The full gates on the merged unions found 0 flaws in
Sonnet's 51 sampled claims, 1 CONTRADICTED in Opus's 41 (a "rollback journal is faster above
~100 MB transactions" claim whose wording is close enough to `wal.html`'s own that it may be a
gate false positive), 0 in Haiku's 24. The accuracy gap is between `medium` and `max`, not
between models.

## Are 100 cheap concepts worth one deep one?

The cheap runs find more. The question the frontier manager has to answer is whether more,
shallower concepts are worth the same as fewer, deeper ones — whether value is additive. Three
findings say it is not.

**The "more" was mostly not more.** Haiku `max`'s 30 extras over Fable split, on reading, into
about half restatements the judge failed to cluster ("PASSIVE is the default" and "fixed in
3.51.3", each stated four or five ways) and half facts read from release logs and secondary
articles. The genuinely new ones — the 3.44.6 and 3.50.7 backports, Eaton's August 2026
reproducer — also appear in Sonnet's and Opus's extras. Opus's 47 extras, by contrast, come
from `wal.c`, the wal-index format and Litestream's issue tracker: facts no one asks a docs
page for. A count of extras is a poor proxy for value. Source tier is a better one.

**The part that does not scale is the part that answers questions.** A hundred headlines do
not sum to one conjunction. After five Haiku runs the union states the headline of 23 Fable
claims and the full conjunction of 7, and the 7 did not move. For a concept someone will query
with a production problem, the pack with the conjunction is the only one that pays.

**A low-value pack costs after the run.** Every stored claim competes in `hub_query_docset`
ranking, every volatile claim needs re-verification, and the cheap tier is where the
contradicted claims came from (Haiku `medium`: 3 in 50). A pack on a concept nobody queries is
negative value: index noise plus maintenance, no retrieval. That is what the Concept Viability
Score gate (`--min-cvs 3.2`) already encodes — relevance, usefulness, novelty, interest and
viability — and why the frontier manager holds sub-gate names back instead of researching
them cheaply.

So no: one `max`-grade pack on a concept that passes the gate is worth more than a hundred
`medium` packs on concepts that do not. Value per concept behaves like *max()* over the packs
that answer a given question, not like a sum.

Breadth is worth paying for in exactly one place: discovery. Opus reading 42 sources and
surfacing `wal2`, `SQLITE_DBCONFIG_DEFENSIVE`, `setlk_timeout` and Litestream's v0.5
checkpoint takeover is how the next gate-passing concept gets *found*. That output should feed
CVS scoring, not the concept tree.

## The buying rule

| Need | Buy |
|---|---|
| Any gated concept: breadth and per-claim precision at least equal to one Fable run | **2 × Sonnet `max`** per concept, merged — about $4, the same as one Fable run, and ahead of it in both directions of the judge |
| The same at lowest latency, or a compact pack | 1 × Fable `max`, ~$3.7, 534 s — fastest `max` run, fewest and densest claims |
| Frontier discovery and source hunting across a family | 1 × Opus `max` per family, ~$3, fed into CVS scoring |
| Full-page extraction with every claim validated | the staged pipeline: Sonnet discovers, Haiku extracts per source, Opus validates every claim — 135 claims, 10/10, $4.15 |
| Never | repeats of any model at `medium` to "add up" to `max` |

Per dollar at one run: Haiku returns 38 unique claims and 11 sources, Sonnet 17 and 9, Opus 11
and 6, Fable 7 and 5. Per claim the other model also states exactly, Sonnet and Fable cost
about the same (16 and 14 cents) — and the mirror test says the two runs are peers — so two
Sonnet `max` runs is the new default for the research queue, Fable the pick when wall-clock
matters, and Opus the pick when the job is finding what to research next. That is also what
`/dr`, `/rabbithole` and `concept-family-explorer` now do by default.

## Limits

One concept and one Fable reference run; the matrix shows ±1 gate verdict is noise, so treat
coverage counts as directional. The judge reads claim text only; three forward passes and two
reverse passes are reported, and the strict rule is biased against atomic claim styles. The
reverse passes compare Fable's single run against single runs and against five-run unions; a
Sonnet-vs-Opus or Sonnet-vs-Sonnet pairing was not run. Pages drifted between the reference run
on 10-13 and the repeats on 10-20 — the Tailscale post was unfetchable the second week, so the
Fable reference lost two or three SUPPORTED verdicts to UNVERIFIED on re-gating, and the later
runs could read a week of newer coverage. The full gate stops at 22–51 verdicts, so union flaw
rates are sampled. Total spend across the three experiments, Claude lanes only, was roughly
$80 of research and about $30 of judging and gating.

## Reproduce

```bash
python3 scripts/dr_model_matrix.py run && python3 scripts/dr_model_matrix.py report
python3 scripts/dr_haiku_repeats.py run --efforts medium,max --repeats 5 --parallel 10
python3 scripts/dr_haiku_repeats.py --model claude-sonnet-5-5 --out docs/research/dr-sonnet-repeats-2026-10-20 run --efforts medium,max --repeats 5
python3 scripts/dr_haiku_repeats.py --model claude-opus-5-5   --out docs/research/dr-opus-repeats-2026-10-20   run --efforts medium,max --repeats 5
```

Then `score` and `report` on each. Raw data — `result.json`, claims files, gate verdicts,
judge prompts and verdicts — is under `docs/research/dr-model-matrix-2026-10-13/`,
`dr-haiku-repeats-2026-10-15/`, `dr-sonnet-repeats-2026-10-20/`,
`dr-opus-repeats-2026-10-20/` and the combined write-up in `dr-model-repeats-2026-10-20/`.
