# Publisher identity correction

Version: 1.0.0
Delta: initial implementation and verified no-model recovery.

TASK-1242 blocks the UI/UX research step TASK-1236 under TASK-1234. The dotted-token literal guard treated bare GOV.UK publisher attribution as a technical identifier. Ten valid semantic judgments could not pass the evidence-binding gate after one bounded evidence repair.

The correction recognizes only bare GOV.UK from an already selected, cited HTTPS gov.uk source whose immutable body contains the exact publisher label. Authored preflight remains strict. Backticked identifiers, arbitrary dotted names, versions, numbers, prefixed values, snapshots, offsets, source binding and extraction guards remain unchanged.

Validation:367related tests including49focused gate cases, plus9subtests; independent contract and code audit. All213 original judgments and conflict review reuse without a model call or verdict-byte change. Native recovery exited0. Raw sources and audit/attempt receipts remain private.

Remaining: checked Git delivery of this independent fix. The UI/UX full suite continues separately in PR311; do not repeat its authors or the accepted paid reviews. Preserve all unrelated work and the embedding pause.
