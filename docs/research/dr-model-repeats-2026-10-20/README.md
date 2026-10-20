# Do repeated Sonnet 5.5 or Opus 5.5 `/dr` runs equal one Fable 5.1 run? — 2026-10-20

Follow-up to the [Haiku repeats study](../dr-haiku-repeats-2026-10-15/README.md), which found
that five Haiku 5.5 runs on "SQLite WAL checkpointing" reach Fable 5.1's breadth but never its
per-claim precision. Same concept, same brief, same Fable reference, same harness
(`scripts/dr_haiku_repeats.py --model … --out …`), same Opus 5.5 judge — now with five Sonnet 5.5
and five Opus 5.5 runs at `medium` and at `max`.

Two questions:

1. Do several Sonnet or Opus runs match one Fable run?
2. The cheaper models find *more* facts but less precise ones. Is "more, shallower" worth it —
   are 100 low-value concepts worth one high-value concept?

## Short answers

**1. Sonnet `max`: yes on breadth after one run, about 60 % on precision after two, and no number
of runs closes the rest.** One Sonnet `max` run ($2.05, 14 min) states 13 of Fable's 26 claims with
Fable's specifics and 21 at least partially, from 18 sources (Fable: 17). Two runs — the same spend
as one Fable run — reach 15 and 23. Five runs ($10.23) plateau at 16 / 25. The 9–11 claims that
stay "partial" are Fable's compound claims (a condition, an exact API behaviour and a number in one
sentence) with one specific dropped. The same shape as the Haiku gap, at half the size.

**Opus `max`: widest and deepest reading of any model, but it writes atomic claims, so the strict
judge under-counts it.** Five Opus runs cite 42 sources (Fable 17) including raw `wal.c`,
`walformat.html`, the wal2 design doc and Rails' SQLite adapter source, and produce 120 unique
claims with 47 facts Fable lacked. Under the study's strict rule ("one candidate claim states the
whole Fable claim") they cover only 5 of 26 — twice, in two independent judge passes. Under a joint
rule ("the listed claims together state every specific") that rises to 12 of 26; Sonnet stays at
14–16 under either rule, Haiku at 4–7. Opus spreads Fable's six-specific claims across three of its
own; the facts are there, the packaging differs.

**`medium` is the same tier for every model.** Five Sonnet or Opus `medium` runs cover 1 of 26
Fable claims fully; five Haiku `medium` runs covered 3. Doubling or quintupling `medium` buys
docs-page restatements, not research.

**Accuracy is not where the tiers differ at `max`.** 150 per-run gate verdicts across the three
models' `max` cells: 150 SUPPORTED. The full gates on the deduped unions found 0 flaws in Sonnet's
51, 1 CONTRADICTED in Opus's 41 (a "rollback journal is faster above ~100 MB transactions" claim
whose wording is close to `wal.html`'s own; possibly a gate false positive), 0 in Haiku's 24.

**Mirror test (added after review): Fable is the yardstick, not the deepest run.** Every
score above asks how much of Fable the candidate reproduced, so Fable is 26/26 by
construction. Judged the other way (Fable's 26 claims as candidate, strict rule), Fable states
22 of Haiku r1's 32 claims, **14 of Sonnet r1's 30**, 13 of Opus r1's 29 (missing 5), and
only 19 of Sonnet's 84-claim union and 34 of Opus's 120. Fable and Sonnet `max` are peers per
run — each states about half of the other exactly — at $3.73 vs $2.05. Fable's edge is speed
(534 s vs 900–1,000) and compactness. See [§ Mirror test](#mirror-test-fable-as-the-candidate).

**2. No — concept value is not additive, and the "more" is mostly not more.** See
[§ Are 100 cheap concepts worth one deep one?](#are-100-cheap-concepts-worth-one-deep-one).

## Method

Identical to the Haiku study except for the candidate model:

- Concept "SQLite WAL checkpointing", depth `standard`, the `dr_run.py` worker brief from
  `scripts/dr_model_matrix.py`; reference = matrix cell `claude__claude-fable-5-1__max`
  (26 claims, 17 sources from 8 orgs, 534 s, $3.73, run 2026-10-13).
- 5 cells per effort (`medium`, `max`) per model, each in its own `HUB_DIR`, run on 2026-10-20 in
  two batches of 10 concurrent agents. Every cell finished inside the 90-minute limit; no re-runs.
- Judge: one Opus 5.5 `medium` call per effort maps every Fable claim to the 5-run union
  (covered / partial / missing) and clusters duplicate claims. k-subset means for k = 1..5 are
  computed from that single judgment. Added for this study: a second strict pass on each `max`
  union and a third pass with a joint-coverage rule ([judge-passes.json](judge-passes.json)).
- Gates: the matrix's fixed 10-claim blind gate per cell, plus the full gate (`--sample all`) on
  each deduped union, each first run and the Fable reference, re-run against live pages.

Raw data: [`dr-sonnet-repeats-2026-10-20/`](../dr-sonnet-repeats-2026-10-20/results.md) and
[`dr-opus-repeats-2026-10-20/`](../dr-opus-repeats-2026-10-20/results.md) (per-cell
`result.json`, claims files, gate verdicts, judge prompts and verdicts).

## Results at `max`

Reference: Fable 5.1 `max` — 26 claims, 17 sources, 8 orgs, $3.73.

### Per run (mean of 5) and per union (k = 5), strict judge

| model | $/run | s/run | claims/run | sources/run | Fable covered k=1 | ≥partial k=1 | Fable covered k=5 (pass 1 / pass 2 / joint) | ≥partial k=5 | union sources (orgs) | unique claims | extras |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|
| Haiku 5.5 | 0.79 | 2144 | 29.8 | 8.6 | 7 | 19 | 7 / 6 / 4 | 23 | 16 (8) | 106 | 30 |
| Sonnet 5.5 | 2.05 | 902 | 34.2 | 18.2 | 13.2 | 21.2 | 16 / 15 / 14 | 25 | 35 (12) | 84 | 24 |
| Opus 5.5 | 2.95 | 908 | 32.2 | 18.6 | 1.0 | 19 | 5 / 5 / 12 | 25 | 42 (18) | 120 | 47 |

Haiku wall time is from the 10-way parallel run on 2026-10-15 (its single matrix cell took 984 s).

### How coverage grows with k (strict judge, mean over all k-subsets)

| k | Sonnet covered | Sonnet ≥partial | Sonnet sources | Opus covered | Opus ≥partial | Opus sources | Haiku covered | Haiku ≥partial | Haiku sources |
|--:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 13.2 | 21.2 | 18.2 | 1.0 | 19.0 | 18.6 | 7 | 19.0 | 8.6 |
| 2 | 14.8 | 23.2 | 24.3 | 2.0 | 21.2 | 26.8 | 7 | 20.9 | 11.1 |
| 3 | 15.4 | 24.0 | 28.6 | 3.0 | 22.6 | 32.5 | 7 | 21.7 | 13.0 |
| 4 | 15.8 | 24.6 | 32.0 | 4.0 | 23.8 | 37.4 | 7 | 22.4 | 14.6 |
| 5 | 16 | 25 | 35 | 5 | 25 | 42 | 7 | 23 | 16 |

Every curve for "covered" flattens by k = 2–3. Every curve for sources and unique claims keeps
climbing almost linearly: repeats are near-disjoint at `max` for all three models (Sonnet: 172 raw
→ 84 unique; Opus: 161 → 120; Haiku: 149 → 106).

### Cost-matched: what one Fable run's $3.73 buys elsewhere

| spend ≈ $3.73 | Fable covered (strict) | ≥partial | sources | unique claims |
|---|---:|---:|---:|---:|
| 1.0 × Fable `max` | 26 | 26 | 17 | 26 |
| 1.8 × Sonnet `max` (k ≈ 2) | ~15 | ~23 | ~24 | ~53 |
| 1.3 × Opus `max` (k ≈ 1) | 1–2 (12 joint at k=5) | ~19 | ~19 | ~32 |
| 4.7 × Haiku `max` (k ≈ 5) | 7 | 23 | 16 | 106 |

Per dollar at k = 1: Haiku 38 unique claims and 11 sources per $; Sonnet 17 and 9; Opus 11 and 6;
Fable 7 and 5. Per *Fable-grade* claim (strict covered) at k = 1: Sonnet $0.16, Fable $0.14,
Haiku $0.11, Opus not measurable under the strict rule.

### Why Opus scores low on the strict judge

Mean claim length over the five `max` runs: Fable 425 characters, Sonnet 402, Opus 360, Haiku 230.
Fable's F4 ("automatic checkpoints are PASSIVE, run in the committing thread, at 1000 pages =
`SQLITE_DEFAULT_WAL_AUTOCHECKPOINT` ≈ 4 MB at 4096-byte pages, per connection, ≤ 0 disables")
is stated completely by Opus claims H2 + H66 + H127 together, and by none of them alone. The
strict rule marks it partial; the joint rule marks it covered. Judge self-preference (Opus
judging Opus) would push the other way, so bias does not explain the gap; claim granularity does.
Sonnet writes compound claims the way Fable does, which is why its strict and joint scores agree.

Consequence for the harness: the strict rule measures "did the candidate write Fable's claim",
not "did the candidate find Fable's facts". Report both rules when comparing models that
granulate differently.

### Mirror test: Fable as the candidate

Same judge, same strict rule, direction reversed: Fable's 26 claims are the candidate and each
model's output is the reference (`score/max-reverse-r1/` for run 1, `score/max-reverse/` for
the deduped 5-run union).

| Reference | ref claims | Fable covers | partial | missing | Fable extras vs ref | forward (ref covers Fable, strict) |
|---|---:|---:|---:|---:|---:|---:|
| Haiku `max` r1 | 32 | 22 | 9 | 1 | 20 | 7 / 26 |
| Sonnet `max` r1 | 30 | 14 | 14 | 2 | 8 | 12–14 / 26 (k=1 range) |
| Opus `max` r1 | 29 | 13 | 11 | 5 | 9 | 0–2 / 26 strict |
| Haiku union (5) | 106 | 66 | 31 | 9 | 6 | 7 / 26 |
| Sonnet union (5) | 84 | 19 | 56 | 9 | 4 | 16 / 26 |
| Opus union (5) | 120 | 34 | 75 | 11 | 4 | 5 strict / 12 joint |

Reading: Fable dominates Haiku both ways. Fable and Sonnet are symmetric at one run each
(14/30 vs ~13/26 strict; 28/30 vs ~21/26 at least partial). Fable misses 5 of Opus r1's claims
outright. Against the unions Fable is mostly "partial", i.e. the unions carry specifics Fable's
run lacks. Fable's distinct advantages are wall-clock (534 s) and density (26 compound claims
covering what 30–40 of the others' claims say). Judge cost for the six reverse passes: $2.33.

## Results at `medium`

| model | $/run | claims/run | sources/run | union covered / partial / missing | union unique claims | union sources |
|---|---:|---:|---:|---|---:|---:|
| Haiku 5.5 | 0.09 | 11.6 | 5.4 | 3 / 15 / 8 | 40 | 9 |
| Sonnet 5.5 | 0.27 | 11.4 | 5.6 | 1 / 20 / 5 | 20 | 12 |
| Opus 5.5 | 0.65 | 16.4 | 6.8 | 1 / 20 / 5 | 39 | 11 |

All three `medium` tiers stop at the SQLite docs plus one or two secondary pages. None reached the
Tailscale, Antithesis or Canonical postmortems in five tries. Per-run gates: Sonnet and Opus
`medium` 50/50 SUPPORTED each; Haiku `medium` 47/50 with 3 CONTRADICTED. Sonnet's five `medium`
runs collapsed to 20 unique claims — the five runs re-found the same 20 facts — while Opus's five
gave 39, so Opus `medium` repeats are more disjoint but no deeper.

## Are 100 cheap concepts worth one deep one?

The question treats value as additive: 100 × small ≥ 1 × large. Three findings in this and the
Haiku study say it is not.

**1. "More" was mostly not more.** Haiku `max`'s 30 extras over Fable split, on reading, into
about half restatements the judge failed to cluster ("PASSIVE is the default", "fixed in 3.51.3",
each stated four to five ways) and half facts read from release logs and secondary articles.
The genuinely new ones (3.44.6 and 3.50.7 backports, Phil Eaton's August 2026 reproducer) are also
in Sonnet's and Opus's extras. Opus's 47 extras, by contrast, come from `wal.c`, `walformat.html`,
the wal2 design doc, Rails' adapter defaults and Litestream's issue tracker — things no one asks
a docs page for. Count of extras is a poor proxy for value; source tier is a better one.

**2. The part that does not scale with repeats is the part that answers questions.** Fable's
compound claims pin a condition, an API and a number together ("`synchronous=NORMAL` → the
checkpoint is the only fsync → transactions can roll back after power loss"). A user with a
production WAL problem needs exactly that conjunction. Haiku's union states the headline of
18 of those claims and the full conjunction of 7, after five runs, and the count did not move from
k = 1 to k = 5. A hundred headlines do not sum to one conjunction.

**3. Low-value concepts carry a cost after the run.** Every stored claim competes in
`hub_query_docset` ranking, every volatile claim needs re-verification, and the cheap tiers are
where the contradicted claims came from (Haiku `medium`: 3 in 50). A pack on a concept nobody
queries is negative value: index noise plus maintenance, no retrieval. That is what the Concept
Viability Score gate (`--min-cvs 3.2`, PR #199) already encodes — relevance × usefulness ×
novelty × interest × viability — and why the frontier manager holds sub-gate names back.

So: one Fable-grade pack on a concept that passes the CVS gate is worth more than 100 `medium`
packs on concepts that do not. Value per concept is closer to *max()* over the packs that answer a
given question than to a sum.

Where breadth **is** worth paying for: discovery. Opus `max` reading 42 sources and surfacing
`wal2`, `SQLITE_DBCONFIG_DEFENSIVE`, `setlk_timeout` and Litestream's v0.5 checkpoint takeover is
how the next CVS ≥ 3.2 concept gets *found*. That is a frontier-scan job, and its output should
feed CVS scoring, not the concept tree directly.

**Practical rule from the three studies**

| need | buy |
|---|---|
| any gated concept: breadth and precision ≥ one Fable run | **2 × Sonnet `max`**, merged (~$4, Fable's price; ahead of Fable in both judge directions) |
| lowest wall-clock, or a compact pack | 1 × Fable `max` ($3.7, 534 s) |
| frontier discovery / source hunting on a family | 1 × Opus `max` per family ($3), feed into CVS |
| never | repeats of any model at `medium` to "add up" to `max` |

Two Sonnet `max` runs is the default for the research queue (`/dr`, `/rabbithole`,
`concept-family-explorer` switched to it on 2026-10-20); Fable when wall-clock matters; Opus
for finding what to research next. The earlier draft of this table reserved Fable for
"precision-critical" concepts on the strength of the one-way comparison; the mirror test does
not support that.

## Limits

- One concept, one Fable reference. The 2026-10-13 matrix shows ±1 gate verdict is noise; treat
  coverage counts as directional. Sonnet's 13.2 ± 1 at k = 1 and Opus's 5 → 12 shift between
  judge rules are the robust findings; single-digit differences are not.
- The judge reads claim text only. Three passes (two strict, one joint) are reported; the strict
  rule is biased against atomic claim styles, see above.
- Pages drifted between the reference run (10-13) and these runs (10-20): the Tailscale blog
  post was unfetchable on 10-20, so Fable's reference lost 2–3 SUPPORTED verdicts to UNVERIFIED
  in the re-run full gate, and Sonnet/Opus could read seven days of newer coverage. No model
  cited `tailscale.com/blog/sqlite-wal-reset-bug` on 10-20.
- Ten concurrent agents per batch; costs per run ($2.05 Sonnet, $2.95 Opus) are within 20 % of the
  single matrix cells ($2.43, $3.12), so concurrency did not inflate cost the way it did for Haiku.
- The full gate's `--sample all` still stops at 22–51 verdicts; union flaw rates are sampled.
- Stele was unreachable during this session; findings are recorded here and in the repo memory,
  not yet in the graph.

## Reproduce

```bash
python3 scripts/dr_haiku_repeats.py --model claude-sonnet-5-5 --out docs/research/dr-sonnet-repeats-2026-10-20 run --efforts medium,max --repeats 5 --parallel 10 --agent-timeout 5400
python3 scripts/dr_haiku_repeats.py --model claude-opus-5-5   --out docs/research/dr-opus-repeats-2026-10-20   run --efforts medium,max --repeats 5 --parallel 10 --agent-timeout 5400
python3 scripts/dr_haiku_repeats.py --model claude-sonnet-5-5 --out docs/research/dr-sonnet-repeats-2026-10-20 score && python3 scripts/dr_haiku_repeats.py --model claude-sonnet-5-5 --out docs/research/dr-sonnet-repeats-2026-10-20 report
python3 scripts/dr_haiku_repeats.py --model claude-opus-5-5   --out docs/research/dr-opus-repeats-2026-10-20   score && python3 scripts/dr_haiku_repeats.py --model claude-opus-5-5   --out docs/research/dr-opus-repeats-2026-10-20   report
```

The extra judge passes (`score/max-judge2/`, `score/max-judge3-joint/`) were produced by calling
`dr_haiku_repeats._judge` with the strict prompt again and with the joint-coverage prompt from
[judge-passes.json](judge-passes.json). Total spend: research $29.6, judges and gates ≈ $13.
