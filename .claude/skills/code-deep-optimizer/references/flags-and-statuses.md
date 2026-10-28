# Flags and exit statuses — code-deep-optimizer

> Reference for the `code-deep-optimizer` skill. SKILL.md § Flags keeps the one-line flag
> table; this file holds the interaction rules (resolved before the run starts) and the mapping
> from every Summary `Status` value to the shared contract's exit conditions. See SKILL.md
> "## Invocation" and "## Convergence loop".

## Flag interactions (resolve before the run starts)

Flags are not freely composable. Resolve these first, state every resolution in the work log as
`flag ignored: X (superseded by Y)`, and surface it in the report.

| Combination | Resolution |
| --- | --- |
| `--no-verify` + empirical mode | **`--no-verify` forces `--no-empirical`.** The must-pass veto is defined as the § Verify gate baseline; with no baseline the veto is vacuous and promotion would be ungated. Never run the champion–challenger loop without the veto. |
| `--no-verify` + `--verify-end` | Mutually exclusive; `--no-verify` wins. |
| `--quick` + `--empirical` | `--empirical` ignored; quick mode skips empirical mode by definition. |
| `--quick` + `--suggest` | `--suggest` ignored; quick mode skips the advisory track. |
| `--quick` + `--max-iter=N` | `--quick` wins; always exactly 1 iteration. |
| `--quick` + `--no-verify` | `--no-verify` wins. Report `Verify: N/A (--no-verify)` and drop quick mode's regression-attribution claim, since there is no baseline to attribute against. |
| `--quick` + `--verify-end` | `--verify-end` ignored. Quick mode keeps its single baseline run so a `FAIL` stays attributable; `--verify-end` would remove that baseline. |
| `--read-only` / `--report` + empirical mode | Empirical loop runs but never persists: implies `--dry-run`. A read-only run writes no champion. |
| `--read-only` / `--report` + C3 counterexample | The failing test C3 would write is emitted in the report as a repro sketch plus the proposed test body, never written to disk. The same rule covers every T1 test and S5 log the run would add: prescribed diffs only. |
| `--annotate` + empirical mode | `--annotate` forces `--no-empirical`: a comments-only run produces no fix candidates to promote, so no champion may be climbed or persisted. |
| `--quick` + `--annotate` | Composable: annotate the Critical rows only; every other finding is recorded as noticed-not-fixed per the triage rules. |
| `--annotate` + `--read-only` | `--annotate` writes inline comments **into the file** and is therefore a write mode; under `--read-only` the comments are emitted in the report instead. |
| `--annotate` + verify gate | Comments cannot change behavior, so the gate runs the syntax check (`node --check` / `py_compile` / equivalent) once after the writes and skips the suite; a suite run would verify nothing the syntax check does not. |
| `--scope=changed` outside a git repo | The run stops before Stage 0 with `BLOCKED (--scope=changed: not a git repo)`; re-run with `--scope=<paths>` or no scope flag. |
| `--no-sync` on any run | Suppresses only the post-run prose-index refresh (`references/report-format.md`, item 11). cdo has no registry-sync step, so nothing else changes. |
| `--implement-features` + `--quick` | `--implement-features` ignored; quick mode is a triage, not an improvement run. |
| `--implement-features` + `--read-only` / `--report` | `--implement-features` ignored; read-only mode cannot write feature code. Identified improvements are emitted in the report as prescribed diffs only. |
| `--implement-features` + `--annotate` | `--implement-features` ignored; annotate mode writes comments, not implementations. |
| `--implement-features` + `--no-verify` | **`--implement-features` forces verify gate ON.** Feature additions without build/test verification are unsafe; `--no-verify` is overridden for the feature-implementation phase. |
| `--implement-features` + empirical mode | Sequenced, not merged: the empirical loop runs first on the structural result; the feature phase runs after it and outside champion–challenger, because a feature addition fails the public-API-unchanged veto by design. |
| `--implement-features` + `--suggest` | Composable: `--suggest` emits the Recommendations section as usual; `--implement-features` additionally implements all identified features. Advisory A1/A2/A3 findings that overlap with implemented features are marked `Implemented` in the report. |

## Flag semantics (the two flags whose one-line table row is not enough)

- **`--annotate`.** Writes one review comment per Medium+ finding instead of the fix, in the file's
  own comment syntax, on the line above the finding's anchor, shaped
  `cdo <PASS> <Severity>: <finding>. Fix: <one line>` (e.g. `// cdo S2 High: catch {} swallows the
  fetch error. Fix: log at error level and skip the id.`). It is a write mode: the pre-write
  snapshot still runs, and the verify gate runs the syntax check only (see the interaction table).
- **`--scope=changed`.** In-scope files are the union of `git diff --name-only HEAD` (staged and
  unstaged changes against the current commit) and untracked files that `.gitignore` does not
  exclude; deleted files drop out. Outside a git repo (`git rev-parse --is-inside-work-tree` fails)
  the run stops before Stage 0 with `BLOCKED (--scope=changed: not a git repo)`.

## Exit-status vocabulary

The Summary line's `Status` field maps onto the seven canonical exit conditions in
`~/.claude/skill-consolidation/convergence-and-severity.md` § Convergence loop. cdo keeps its
own status names because hooks and orchestrators already read them; this table is the mapping,
so no reader has to guess which exit fired.

| Status | Contract exit | Meaning in cdo |
| --- | --- | --- |
| `CLEAN` | 1 Clean | Zero Critical/High/Medium findings on the latest pass, and the blind re-audit gate corroborated nothing. |
| `CONVERGED` | 2 No progress | The latest iteration's Medium+ count is at or above the previous iteration's; outstanding findings are reported. |
| `OSCILLATING (cycling)` | 3 Content cycling | An applied finding re-flagged at the same {pass, severity, location}. Model-judged, per the contract. |
| `OSCILLATING (instability)` | 5 Loop instability | The iteration introduced as many Medium+ findings as it closed, or more. |
| `NO_CHANGE` | 4 Stable rewrite | `convergence_check.py` reports edit distance between consecutive versions under 2%. |
| `CAPPED` | 6 Iteration cap | The cap was reached with Medium+ findings outstanding: 5, or 3 under the small profile (raised to 5 when Medium+ findings dropped by at least 50% in the prior iteration), or the `--max-iter=N` ceiling. |
| `BUDGET_EXHAUSTED` | 7 Budget expired | `--budget-minutes` elapsed; the current iteration's writes finished first, then the run exited. The Summary appends `· wall: N min`. |
| `BLIND-AUDIT-DISSENT` | 1 Clean, gate refused | The blind re-audit still corroborated Medium+ findings after one extra iteration; they are listed, not applied. |
| `TRIAGE-PARTIAL` / `TRIAGE-CLEAN` | none (triage mode) | `--quick` only, per the contract's § Triage modes; neither asserts convergence. `TRIAGE-CLEAN` when every Critical finding was Applied (or none existed) and the run reports `Unfixed: 0 High / 0 Medium`; `TRIAGE-PARTIAL` when any Unfixed count is above 0 or any Critical row is `BLOCKED`. |
| `BLOCKED (--scope=changed: not a git repo)` | none (halted before Stage 0) | The scope flag needs a git repo and `git rev-parse` failed; no pass ran, no snapshot was taken. |
| `BLOCKED (hostile content)` | none (halted) | Every in-scope file halted under § Stage 0.5's halt condition, so no pass completed. Per-file halts inside an otherwise normal run keep the run's normal status and appear as `BLOCKED` rows in the findings table. |

Exits 2 through 6 are not gated by the blind re-audit (the contract gates only Clean); each already
reports the findings the loop proved it could not close.
