# Run report and continuation contract

## Contents

- Human report
- JSON ledger
- Evidence receipts
- Examples and resume

## Human report

Report the following after validation. Link local artifacts and delivery receipts.

1. Scope: editable/report-only mode, source and loaded revision, matrix of routes,
   roles, states, viewports, supported platforms, chosen and excluded methods.
2. Per-sweep table: methods checked, edits, final C/H/M/L, unresolved IDs, evidence
   gaps and stop reason. Count unique root causes, not duplicated pass links.
3. Findings: ID, method IDs, locator and matrix cell, evidence, user impact,
   severity/reason, fix, status and final verification receipt.
4. Check results: exact command/action, completed exit status, source fingerprint,
   observed runtime identity and capture. Separate EXECUTED, OBSERVED, EXPERT,
   PARTICIPANT, ISOLATED and SIMULATED results. Do not print a bare PASS for a
   prediction. Explain what worked and should be preserved when evidenced.
5. Final status, coverage limitations, rollback, versioned continuation location,
   and next action for each residual. CLEAN is scoped and requires the final gate.

## JSON ledger

Create one row for EACH catalogue method, even if unselected. A method is one pass;
`applicable_cells` is its planned subset of the frozen coverage matrix. A PASS row
must check all of that subset. UNAVAILABLE is a missing prerequisite; N_A is an
observed absence of a feature, with a factual reason. OUT_OF_SCOPE is allowed only
for an unselected non-core method, with a reason recorded before repairs.

Top-level fields:

```json
{
  "schema_version": 1,
  "version": "1.0.0",
  "delta": "Initial scoped audit",
  "status": "NEEDS_EVIDENCE",
  "editable": true,
  "artifact_sha256": "fingerprint output from uio_check.py",
  "scope": {"matrix": [{"id": "home-default-390", "route": "/", "state": "default", "viewport": "390x844", "role": "visitor"}]},
  "selected": ["P01"],
  "passes": [],
  "findings": [],
  "checks": [],
  "runtime": {},
  "final_sweep_no_edits": false,
  "final_review": {}
}
```

This abbreviated example shows field shapes; an actual report must select all
core methods and contain every catalogue row. Include conditional methods where
their feature exists and requested research methods. Record absent conditional
features as selected N_A rows when inspected; preserve evidence for the absence.

Each pass row:

```json
{
  "id": "P18", "status": "PASS", "reason": "Text pairs satisfy the applicable threshold",
  "artifact_sha256": "current fingerprint",
  "applicable_cells": ["home-default-390"],
  "checked_cells": ["home-default-390"],
  "evidence": [{"path": "contrast-recheck.txt", "sha256": "file SHA-256", "kind": "EXECUTED", "captured_for": "current fingerprint"}]
}
```

Finding fields: `id`, `methods` (one or more catalogue IDs), `severity`
(Critical/High/Medium/Low/Nit), `status` (OPEN/BLOCKED/FIXED), `locator`,
`impact`, `evidence`, `fix`, and `verification` (a receipt list for FIXED findings).
An old receipt cannot close a current finding; retain it as history and reverify.

A required check records `name`, `required: true`, `completed: true`, `exit_code: 0`,
`artifact_sha256`, and `evidence`. Record manual runtime actions under runtime, with OBSERVED receipts. Required
command checks need EXECUTED receipts and their actual process exit codes.
For CLEAN include at least one required executed check, plus runtime identity and
fresh rendered/action evidence. `runtime` contains `identity`, `artifact_sha256`
and `evidence` with OBSERVED receipts; the identity records the actual loaded build, app version or server.
The final review records `grade: ISOLATED`, `reviewer`, `artifact_sha256` and
`evidence` with ISOLATED receipts. Preserve any independent review dissent as findings and resolve it.

## Evidence receipts

Every receipt contains a file path, its exact SHA-256, an evidence kind, and
`captured_for` binding the capture/action/check to the current source fingerprint.
Resolve relative paths from the report directory. Use actual captured files and
logs, not self-authored statements that a nonexistent check passed. The validator
checks existence, hashes and bindings; it cannot establish whether an observation
is truthful. A source fingerprint covers every owned source/config/dependency file
that can affect this scoped rendering. Record external data/build identity too.
For source-less REPORT_ONLY review, fingerprint the supplied evidence files.

Resume by reading the prompt and continuation record, comparing fingerprints,
loading the matrix and unresolved ledger, and restarting from the first invalidated
pass. Increment version/delta after each saved checkpoint. Never overwrite earlier
captures to make their hashes appear fresh. Never drop a selected method or an
unresolved ID simply to produce a clean report.

## Examples

- **Editable contrast repair:** P18 records computed colors and a sub-threshold
  ordinary text ratio as Medium with SC 1.4.3 and exception analysis. Repair the
  shared token immediately. Record a new render and measurement; then continue
  other passes. Run a complete no-edit sweep on the new fingerprint and an
  independent review. Only then may the scoped report become CLEAN.
- **Screenshot:** inspect visible hierarchy, grouping and type with region anchors.
  Keyboard, tree and workflow passes remain UNAVAILABLE. Produce REPORT_ONLY
  with those limits; do not claim that tab order or screen-reader behavior passed.
- **Stall:** two complete sweeps leave the same Medium ID without a successful
  repair. Preserve the source snapshot, both attempts and receipts. Report STALLED
  with that ID unresolved. A blocked or failed fix can never count as convergence.
