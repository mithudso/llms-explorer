# CodeQL scanner metadata follow-up

The required check on the pushed head reported clear-text logging from the static detection table through a finding type label. The SARIF path starts at that configuration list; it does not start at scanned input or a matched value.

The scanner now names that table `REDACTION_RULES` and documents the static-label boundary. All 20 labels and regex literals are unchanged. The scan function is structurally identical after identifier renaming, and its JSON schema and detection behavior stay the same.

Four new file/stdin regression methods cover all 20 detector types, exact type/line/count/redaction metadata, multiple matches on one line and clean input. They assert that neither stdout nor stderr contains matched synthetic values or source lines. These tests pass on the preimage too; no prior runtime disclosure is claimed. The full safe PDO suite passes 29 tests plus 14 subtests. Scoped Ruff and AST checks pass.

No security suppression, dismissal or check bypass was added. Required CodeQL acceptance on the next pushed head is for the parent to verify after syncing the legacy bundle. This receipt records local evidence, not remote CI acceptance. Exact hashes and SARIF bindings are in [the JSON receipt](codeql-followup.json).
