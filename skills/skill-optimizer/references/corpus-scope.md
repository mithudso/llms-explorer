# Source corpus and write scope

Resolve one authoritative trigger corpus before generating a projection.

1. For an installed user-level target, use the existing
   `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`.
2. For an explicitly selected repository target, use its
   `evals/trigger-corpus.jsonl`. Before creating it, read any existing user-level
   corpus and preserve its rows and provenance in the run snapshot. Replay its
   applicable queries. Repository scope does not authorize modifying that file.
3. If the target is read-only or the owner forbids corpus writes, keep the
   selection and predictions in memory. Do not create a corpus or projection.

Record the selected path, source hashes, skill identity and corpus version in the
run receipt. Append new query/verdict records with the current description hash,
skill version and evaluation level. Retain history. If the skill's scope changes,
retire an affected query with a dated reason instead of deleting it.

Each query row includes `query` and Boolean `should_trigger`. Rows that record a
prediction also include `predicted_trigger`, `level: predicted`, and a reason.
Project only the selected active queries as
`[{"query": "...", "should_trigger": true}]` in `evals/trigger-eval.json`.
The projection carries no authority over source history.

The 20-query audit is exploratory. It does not satisfy the larger held-out
promotion requirements in `shared/champion-challenger.md`.
