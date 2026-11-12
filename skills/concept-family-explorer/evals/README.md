# Scoped skill evaluations

`trigger-corpus.jsonl` is the publication-safe source query and verdict history. The original global history stays private and was preserved before this scoped copy was made. Corpus verdicts are predictions, not activation measurements.

Regenerate the disposable projection from a clean checkout with `python3 <skill-dir>/evals/project_triggers.py`; verify it with `python3 <skill-dir>/evals/project_triggers.py --check`. Never edit `trigger-eval.json` as input.

The helper replays the last record for each query and honors retirement. It
selects 10 positive and 10 negative queries without deleting source history.
Within each class it prefers the newest rows marked `selected_for_standard: true`,
then fills from the newest unmarked rows. Rows with `selected_for_standard: false` are ineligible.
The projection keeps the selected rows in latest-record source order. Fewer than
10 eligible queries in either class produces an explicit error.

`evals.json` has realistic scenarios and static instruction-contract assertions. Matching policy text does not establish successful runtime behavior. Safe regression test files identify whether they execute disposable fixtures or only inspect instruction contracts.
