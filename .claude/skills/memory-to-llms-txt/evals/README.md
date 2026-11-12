# Evaluation inputs

`trigger-corpus.jsonl` is this repository skill's authoritative, publication-safe query and verdict history. `trigger-eval.json` is disposable. Full prior global corpus history stays in the enclosing run's private evidence store. Predictions are not measured activations.

From this `evals/` directory, run `python3 project_triggers.py` to regenerate
the disposable projection. Add `--check` to verify parity without writing. The
helper needs no private files. Never edit `trigger-eval.json` as input.

The helper replays the last record for each query and honors retirement. It
selects 10 positive and 10 negative queries without deleting source history.
Within each class it prefers the newest rows marked `selected_for_standard: true`,
then fills from the newest unmarked rows. Rows with `selected_for_standard: false` are ineligible.
The projection keeps the selected rows in latest-record source order. Fewer than
10 eligible queries in either class produces an explicit error.

`evals.json` contains realistic workflow cases. Structural and negative assertions require a blind prediction or an actual isolated case run. Deterministic source-helper regressions are reported separately; passing them does not establish a completed live crawl/import/index workflow.
