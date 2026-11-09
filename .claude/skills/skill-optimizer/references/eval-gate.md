# Eval gate (Step 6.3)

Every run reports eval results. A run without them cannot exit `converged`. It exits `EVALS-MISSING`. This gate reuses Pass F (evals exist), Pass H (trigger eval) and the `deep-eval-optimizer` hand-off. It adds no parallel harness.

## What runs, in order

1. **Ensure files exist.**
   - `<skill-dir>/evals/evals.json`: at least 2–3 realistic cases with verifiable `assertions`, in the Step 2.3 schema.
   - `<skill-dir>/evals/trigger-eval.json`: 20 queries (10 positives, 10 near-miss negatives), derived from the canonical corpus per Pass H.

   If a file is missing, Step 5 creates it per Step 2.3, Pass F and Pass H. Under `--read-only` (no writes) or `--meta` (Pass F skipped), do not create it: report it as `missing (proposed)`.
2. **Trigger eval.** Use the final iteration's Pass H result. If the skill-creator harness ran, its level is `measured`; otherwise it is `predicted`. The harness runs on the final iteration or when `--eval=measured` is passed, with two exceptions:
   - Under `--read-only`, it does not run, because it writes files.
   - Under `--max-iter=1 --no-sync`, it runs only with `--eval=measured`. An orchestrator that wants measured rates passes `--eval=measured` on its last call.

   If Pass H did not run in the loop (`--meta` without `--eval`), run it once at `predicted`.
3. **Behavior evals.** Grade every case in `evals/evals.json`:
   - `deterministic`, `schema`, `count` assertions: check them against files on disk with a script or command (`python3`, `jq`, `wc`). Level `static`.
   - `structural` and `negative` assertions, and any assertion that needs output from executing the case: a blind subagent grades them. It receives only the case `prompt` and `files`, the final `SKILL.md` and `references/`, and the assertion text. Level `predicted`.
   - `/sko` never runs `/deo` itself: `/deo --run` rewrites the skill and its evals and commits them, which would bypass Step 6 verification. If `--eval=measured` is passed or the caller asks for measured behavior rates, report the behavior row at `static`/`predicted` and add the follow-up command `/deo <skill-path> --run --eval-type=functional` to the report, to run after `/sko` exits.
4. **Report** both rows of the Step 8 eval results table (`references/report-format.md`). If the behavior evals used more than one level, give the count per level. Under `--meta` the behavior row is `n/m static`, where `m` counts only the `deterministic`, `schema` and `count` assertions; list `structural` and `negative` assertions as `not graded (--meta)`.

## Status rule

| Situation | Exit status |
|---|---|
| Both eval files exist, trigger and behavior evals ran, rates reported | normal (`converged` etc.) |
| An eval file is missing after Step 5, or the trigger or behavior evals could not run at any level | `EVALS-MISSING` |
| `--read-only` or `--meta` and a file is missing | `EVALS-MISSING` (proposed file in the diff preview) |
| Evals ran and a threshold missed (pos < 9/10, fp > 1/10, any behavior assertion failed) | Medium finding in the report. Step 6.3 runs after the loop, so it does not loop back; the run exits with the status a remaining Medium finding gets, never `converged`. A trigger miss inside the loop is Pass H's own Medium finding and follows the loop rules |

Under `--meta`, run the existence check, the predicted trigger eval and the static assertions only. Run the skill-creator harness only when `--eval` or `--eval=measured` is passed.
Orchestrators that pass `--max-iter=1 --no-sync` still get the gate on each iteration. `EVALS-MISSING` tells them the run did not converge.

`EVALS-MISSING` replaces only `converged`. If another non-clean status applies (for example `BLIND-AUDIT-DISSENT` or `BUDGET_EXHAUSTED`), report that status and append `+EVALS-MISSING`.
