# CFE: concept-family mapping, scoring and research

Read [mongo-protocol.md](mongo-protocol.md) and [evidence.md](evidence.md).
CFE chooses which gaps to research and when to stop. It delegates each bounded
research brief to [dr.md](dr.md). Keep mapping, research, qualification and
artifact/index completion as separate outcomes.

Defaults: threshold `3.2/5`, `maxRounds=3` frontier re-expansions after Round 0,
no concept-count cap, and no implicit wall-clock cap. Honor explicit
`--threshold`, `--max-rounds`, `--max-concepts` and `--budget-minutes`. Count
concepts, not cluster calls, against an explicit concept budget.

## Map and inventory

Frame all five neighborhoods: parent/super-domain, siblings, children/subconcepts,
adjacent/crossover, and frontier/emerging. Name 5–12 candidates per neighborhood
before scoring. Five per neighborhood is the minimum for a frontier-saturation
claim; sparse maps remain map-bounded. Cross-cutting concepts can occupy multiple
neighborhoods while retaining one canonical identity. Add novel/contrarian
angles and current contested developments from readable evidence.

Author 5–10 competency questions for this family. Store each question and the
concept/claim coverage that answers it. A mapped terminal row alone does not
answer a competency question.

Complete the run-start inventory and four-channel dedup in mongo-protocol.md.
Tag every candidate HAVE, STALE or GAP. A matching fresh node is HAVE; a node
older than 90 days is STALE and becomes a lower-priority refresh candidate.
Missing exact/alias coverage is a provisional GAP until all channels are checked.
Record placement disagreements as a separate handoff; do not silently reparent
another owner's curated concept. Every candidate, including aliases, low scores,
unscored/review, held, skipped and failed rows, stays in the ledger.

## Score and freeze selection

Give every gap five evidence-grounded 0–5 scores and rationale:

| Axis | Decision criterion | Weight |
| --- | --- | --- |
| Relevance | Proximity to the subject's actual core and dependency graph | 0.25 |
| Usefulness | Expected practical benefit if this concept becomes available | 0.25 |
| Novelty | Real gap against existing qualified coverage | 0.20 |
| Interest | Likelihood of repeated use or useful cross-domain connections | 0.15 |
| Viability | Readable primary sources and a researchable bounded scope | 0.15 |

`CVS = .25*Relevance + .25*Usefulness + .20*Novelty + .15*Interest + .15*Viability`.
Verify arithmetic deterministically before dispatch. `Viability <= 1` or
`Novelty = 0` forces SKIP regardless of the composite. Otherwise CVS at or above
this run's threshold selects RESEARCH, or REFRESH for a stale covered concept.
Break ties by Viability, Relevance, then Interest. Keep the original/global
decision intact when a run-local threshold changes selection.

A prior below-threshold SKIP younger than 90 days can be reused only for the same
subject or a true parent subject, unchanged inventory tag and a score still below
the current threshold. A lower threshold or changed inventory requires a fresh
decision. Unscored candidates remain explicit review rows; never drop them.

Freeze the complete ranked selection before research. Preserve explicit count
budget exclusions separately. `--dry-run` stops with the complete scored plan,
no Mongo writes, leases, research, judges or artifacts. `--expand-frontier`
without `--research` stops after saving the authorized unverified plan.

## Dispatch and expand

Group selected concepts by parent, product surface and shared authoritative
sources. Split source-sharing cohorts into subgroups of at most eight concepts;
that subgroup size does not truncate the complete queue. Retrieve a shared URL
once and link its relevant passages to each concept separately. Parent facts
retain their accepted provenance; children research their distinct deltas.

Fan out up to three concurrent DR runs for clustered briefs. Four concurrent
runs are allowed only when every brief is a single concept. Queue the remainder
and start the next as a slot clears. A single selected concept may run inline.
Recheck exact/alias coverage, qualification and ownership immediately before
each dispatch; a sibling return may already have filled it. Retain such rows as
accounted covered skips. Propagate remaining explicit budgets into each brief.

Persist every in-flight return completely before stopping a batch. Save accepted
gate/artifact references and unfinished projection phases independently. Record
failed gaps and reasons rather than deleting them. Re-expand only from evidence
created or inspected this run: qualified child proposals, accepted skill/source
references, mechanisms and open questions. Dedup and score every new candidate.
Store each round's `new above-threshold gaps / cumulative candidates scored`.
Memory-only candidate generation never counts as an evidence-grounded empty round.

## Stop verdicts

Check budgets before asserting saturation. An ordinary reached time/count/round
cap is `BUDGET_EXHAUSTED`, even when the queue is small. If the blind review has
already produced corroborated dissent, retain `SATURATION-DISSENT` at the cap;
do not erase that observed gap with a generic budget verdict. Save every outstanding viable
row with CVS and next action; drain persistence for all in-flight returns. Skip
optional optimization/rebalance when time is exhausted and mark that work owed.
Required preservation and reporting still run.

`SATURATED-COVERAGE` means only coverage of the mapped family: every candidate is
HAVE, qualified/researched, explicit SKIP or logged failed, no rows are undecided,
and every competency question resolves to HAVE or qualified researched evidence.
Failures remain failures in the report. This verdict says nothing about unnamed
concepts beyond the map.

`SATURATED-FRONTIER` requires all of the following:

1. A Round-0 map with at least five names in every neighborhood.
2. At least one productive round, including Round 0, with a concept researched
   through DR.
3. Two consecutive evidence-grounded re-expansions with zero new gaps above
   threshold, with the measured per-round rates recorded.
4. A passed blind saturation gate after those rounds. Give one fresh-context
   reviewer only the subject and five-neighborhood candidate names, without
   scores, decisions or run history. Score and corroborate its proposals.

Corroborated above-threshold dissent re-enters the queue for at most one
additional round within the remaining budgets, then gets one final blind gate.
Persistent dissent, or no budget left for corroborated dissent, exits
`SATURATION-DISSENT` with exact open gaps. Do not spend beyond a cap or claim
saturation over dissent. With no isolated dispatch, label an in-context gate
explicitly; it is weaker evidence and must not masquerade as a fresh blind gate.
A planning-only or nonproductive run cannot establish frontier saturation.

## Finish and resume

Audit only changed skills and affected hubs for routing, capability quality,
evidence/citation parity and injection; preserve unrelated skills. Keep recorded
question coverage and queue lineage. Use trusted finalization and compilation
for qualified content, not direct graph edits as a completion shortcut.

Resume the saved scored table and frozen queue. Scoped rechecks may remove newly
covered items from dispatch while retaining them in accounting. Retry persistence
or compilation directly when research is already accepted. An optimization phase
resumes optimization; it does not regenerate the map or redo paid discovery.
Report all candidate counts and scores, processed/failed/held/unscored/excluded
rows, competency-question coverage, rounds/budgets, measured rates, blind-gate
outcome, changed-skill audits and separate gate/artifact/index receipts.
