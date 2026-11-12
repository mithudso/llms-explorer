# Scoped evaluation inputs

`trigger-corpus.jsonl` is this repository source's authoritative publication-safe
query and verdict history. `trigger-eval.json` is a disposable projection.
Original global history stays in the private run snapshot. Predictions are not
measured activation or held-out promotion.

From a clean checkout, run `python3 <skill-dir>/evals/project_triggers.py` to
regenerate the projection. Add `--check` to verify parity without writing.

The helper replays the last record for each query and honors retirement. It
selects 10 positive and 10 negative queries without deleting source history.
Within each class it prefers the newest rows marked `selected_for_standard: true`,
then fills from the newest unmarked rows. Rows with `selected_for_standard: false` are ineligible.
The projection keeps the selected rows in latest-record source order. Fewer than
10 eligible queries in either class produces an explicit error.

Append or retire source rows before regenerating; do not edit the projection as
input. The functional file uses `{ "skill_name": "...", "evals": [...] }`.
Its author `expected_output` fields must be withheld from independent reviewers.
