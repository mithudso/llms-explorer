# Scoped evaluation inputs

`trigger-corpus.jsonl` is this source bundle's authoritative publication-safe
query and verdict history. `trigger-eval.json` is a disposable projection. Full
prior global history stays in the enclosing run's private evidence store.
Predictions are not measured activation or held-out promotion.

From this `evals/` directory, run `python3 project_triggers.py` to regenerate
the disposable projection. Add `--check` to verify parity without writing. The
helper needs no private files. Never edit `trigger-eval.json` as input.

The helper replays the last record for each query and honors retirement. It
selects 10 positive and 10 negative queries without deleting source history.
Within each class it prefers the newest rows marked `selected_for_standard: true`,
then fills from the newest unmarked rows. Rows with `selected_for_standard: false` are ineligible.
The projection keeps the selected rows in latest-record source order. Fewer than
10 eligible queries in either class produces an explicit error.

`evals.json` contains realistic functional cases. Deterministic source checks and
isolated helper regressions do not establish successful live workflow behavior.
Structural and negative assertions require an independent prediction or an actual
isolated case run. Withhold author `expected_output` fields from independent judges.
