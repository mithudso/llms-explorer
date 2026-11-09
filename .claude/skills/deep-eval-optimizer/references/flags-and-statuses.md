# Flags and Exit Statuses — Deep Eval Optimizer (/deo)

## Flags

| Flag | Effect |
|---|---|
| `--run` | Execute evals with a verified real harness; otherwise report EXECUTOR_UNAVAILABLE |
| `--create` | Force creation of new eval suite if none exists, using the bundled `templates/` |
| `--audit` | Read-only mode: audit existing evals across Passes A-L, report findings, write nothing |
| `--max-iter=N` | Max convergence iterations (default: 3, max: 5) |
| `--eval-type=<type>` | Target specific eval type: `functional`, `trigger`, or `all` (default: `all`) |
| `--dry-run` | Report planned execution without claiming live results |

## Exit Statuses

| Status | Meaning |
|---|---|
| `converged` | All Medium+ findings resolved across Passes A-L; eval suite verified |
| `evals-created` | Missing evals generated and verified |
| `benchmark-passed` | `--run` executed and all assertions passed >= 90% threshold |
| `benchmark-failed` | `--run` executed and assertions failed pass bar |
| `clean` | Audit found 0 Medium+ findings |

| `EXECUTOR_UNAVAILABLE` | The requested real execution harness or evidence is unavailable; no pass rate or convergence is claimed. |
