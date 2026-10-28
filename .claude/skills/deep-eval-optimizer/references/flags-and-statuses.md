# Flags and Exit Statuses — Deep Eval Optimizer (/deo)

## Flags

| Flag | Effect |
|---|---|
| `--run` | Execute the evals (trigger test and functional benchmark) after auditing/optimizing |
| `--create` | Force creation of new eval suite if none exists, using `~/dev/evals/templates/` |
| `--audit` | Read-only mode: audit existing evals across Passes A-L, report findings, write nothing |
| `--max-iter=N` | Max convergence iterations (default: 3, max: 5) |
| `--eval-type=<type>` | Target specific eval type: `functional`, `trigger`, or `all` (default: `all`) |
| `--dry-run` | Run benchmark runner without spawning live subagents |

## Exit Statuses

| Status | Meaning |
|---|---|
| `converged` | All Medium+ findings resolved across Passes A-L; eval suite verified |
| `evals-created` | Missing evals generated and verified |
| `benchmark-passed` | `--run` executed and all assertions passed >= 90% threshold |
| `benchmark-failed` | `--run` executed and assertions failed pass bar |
| `clean` | Audit found 0 Medium+ findings |
