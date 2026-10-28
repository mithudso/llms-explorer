# prompt-deep-optimizer — tooling, caps, glossary, notes

Operational reference for `SKILL.md`: the deterministic helper, the canonical numbers, the flag-interaction table, the glossary, and the exit-condition notes. Read it at Step 1a.3 (routing), Step 5 (exits), and Step 6f (self-check).

## Tooling — `scripts/pdo_tools.py`

Every mechanical step in this skill runs through one stdlib-only helper, so its result is a value you did not author. Invoke with the full path; a step it owns is a step you must not re-derive by eye, and its output overrides your own reading.

```
python3 ~/.claude/skills/prompt-deep-optimizer/scripts/pdo_tools.py <subcommand>
```

| Subcommand | Used at | Replaces |
|---|---|---|
| `tokens <path\|-> [--one-off] [--fragment]` | Step 1a.3 | Eyeballing the ~600 / ~4,000-token routing boundaries. Returns `band`, `profile`, and `routing`. `--one-off` enables the under-threshold handoff; `--fragment` disables the small profile. Without the flags it assumes a production prompt in full mode. |
| `editdist <prev> <curr>` | Step 5 cond. 4 | Estimating edit distance; the documented fallback when `convergence_check.py` is absent. |
| `scan <path\|->` | Step 4 redaction | Spotting secrets and PII by reading. Reports type and line, never the value. |
| `backup <path> [--run-id <id>] [--iter N --from <file>]` | `--write` runs; Step 5 per-iteration copies | An unbacked in-place write. Copies the file to `~/.claude/skill-consolidation/backups/prompt-deep-optimizer-<run-id>/<basename>` (the contract's `<skill>-<YYYYMMDD-HHMMSS>` central form; `--run-id` defaults to the current timestamp) and prints `backup_path` plus the restore command; `--iter N --from <scratch>` copies the iteration-N candidate (a scratch file, never the untouched target) into the same run dir as `<basename>.iterN`, for `convergence_check.py`. Refuses to clobber an existing copy. |
| `selfcheck --manifest <file>` | Step 6f | Grading your own run. Returns `self_check: N/8` and names each failure. |

All five print JSON and carry `"evidence": "EXECUTED"`, which is what lets Step 6's evidence table grade the gate honestly. `selfcheck` exits 2 on failure, so an outer loop can branch on it.

**Degraded paths (helper missing or exiting non-zero).** Record `degraded: <subcommand> by hand` in the Summary line and:

- `tokens` → `ceil(chars ÷ 4)` by hand, applying the one-off and fragment conjuncts yourself.
- `editdist` → the helper is itself the fallback for `convergence_check.py`; with both gone, Step 5 cond. 4 cannot fire (`degraded: condition 4 cannot fire`).
- `scan` → manual review against the same pattern classes; state that the floor was manual.
- `backup` → no degraded path: refuse `--write` and report the rewrite instead.
- `selfcheck` → report `self-check: N/A (helper missing)`; the run is not certified. (Exit 2 is not a degraded path: it is a failing result to repair and re-run.)

## Budget and caps

Canonical source for every count in this skill; it restates the shared contract `~/.claude/skill-consolidation/convergence-and-severity.md` (iteration caps, artifact-size profile, budget contract) for this skill. Prose elsewhere cites this table. On any disagreement the contract wins, then this table, and the citing prose is the bug.

| Name | Value | Meaning |
|---|---|---|
| Passes | 16 (A–P) | Every pass emits a row each iteration, `N/A` and `partial` included. `partial` counts as active. |
| Groups | 5 (3 under `profile: small`) | Parallel-dispatch bundles. Group 5 carries 4 passes because 16 does not divide by 5. |
| Iteration cap | 5 (3 under `profile: small`) | Step 5 condition 5. `--max-iter=N` replaces it, clamped 1–10. |
| Cap raise | 3 → 5 | Small profile only. Evaluated **once**, at the iteration-3 boundary: if Medium+ findings fell by ≥50% from iteration 2 to 3, the cap is 5 for the rest of the run. |
| Default budget | 20 minutes wall clock | Step 5 condition 7 runs **by default** (registered deviation, see § Exit-condition notes). `--budget-minutes=N` overrides; `--budget-minutes=0` disables. |
| Subagent round-trips | 1 per group per iteration | No mid-iteration retry. A second consecutive error escalates that group to sequential. |
| Drift re-do limit | 3 drift failures in one iteration | Step 5 condition 6: the first rewrite drifts, the re-do drifts, the second re-do drifts → `DRIFT_DEADLOCK`. |
| Corroboration threshold | iterations ≥ 2 | Step 3. |
| Small-artifact threshold | ~600 tokens (~2,400 chars) | Mirrors the `/ph`–`/phe` routing bound. Under `profile: small`, effort drops to `high` as well as the group count to 3: a small prompt does not earn `xhigh`. |
| Long-prompt inline limit | ~4,000 tokens (~16,000 chars) | Above this, ask for a file path rather than inline text. |
| Empirical default margin | `2/n_holdout` | `references/champion-challenger.md` § Split discipline. A smaller explicit `--margin` runs as `--dry-run`. |

## Flag interactions

Resolve conflicts by this table, never by guessing a precedence.

| Flags | Rule |
|---|---|
| `--structural-only` + `--eval=` / `--holdout=` / `--must-pass=` | Structural wins; eval data is ignored; Summary line notes `empirical: skipped (--structural-only)`. |
| `--dry-run` or `--no-promote` + `--write` | `--write` writes the structural loop's shipped candidate only; the champion is never persisted; the write-back footer says so. |
| `--margin=<n>` below `2/n_holdout` | Runs as `--dry-run`; every number is labeled exploratory. |
| `--max-iter=1` + Step 6a0 dissent | No extra iteration is available; exit `BLIND-AUDIT-DISSENT` listing the findings. |
| `--max-iter=N` outside 1–10 | Clamped; `max-iter clamped N→M` in the Summary line. |
| `--budget-minutes=0` + `--max-iter` | Caps alone bound the run; `budget: disabled by flag`. |
| `--write` + inline or variable target, or any Critical/High `BLOCKED` at exit | `--write` refused; the rewrite is reported with the reason. |
| `--cross-model` without a completed Step 4 redaction | Gate skipped: `cross-model gate: skipped (content not cleared for cross-model egress)`. |

## Glossary

- **stable prefix**: the portion of a prompt whose text does not vary across calls (instructions, persona, schema). Placed before any dynamic slot so prompt caching can reuse it.
- **edit-distance**: the total count of character insertions, deletions, and substitutions needed to convert one prompt into another. Used in Step 5 cond. 4; measured in UTF-8 characters of the longer prompt.
- **intent drift**: a rewrite that would cause the model to take a different action, produce a different output shape, or enforce different constraints than the original (not merely use different wording), unless the delta is finding-justified (traceable to an Applied Medium+ finding or a pre-approved Pass E/O default insert) and declared in Step 6a's deliberate-deltas block. Detected in Step 6a by comparing the per-version 5-field checklists; any undeclared field difference is drift.
- **fragment**: a partial prompt: a single tool description, a single section of a larger system prompt, or any text missing two or more of Step 1b's four completeness markers (persona statement, explicit task, output contract, length > ~200 tokens).

## Exit-condition notes

- **Status vocabulary.** `CLEAN`, `NO_CHANGE`, `STALLED`, `OSCILLATING`, `CAPPED`, `DRIFT_DEADLOCK`, `BUDGET_EXHAUSTED`, `BLIND-AUDIT-DISSENT`. The manifest carries the bare token; qualifiers (`OSCILLATING (cycling)`, `OSCILLATING (stable-rewrite)`, `OSCILLATING (cycling + stable-rewrite)`, `STALLED, shipped iteration 2 rewrite …`) live in the Summary line, and `selfcheck` reads only the leading token.
- **Condition 2 naming.** Earlier versions reported the no-progress exit as `CONVERGED`, which reads as a pass and was misinterpreted by downstream consumers of the `Status` field. `STALLED` is the current token; treat `CONVERGED` from an older run or an outer orchestrator as its synonym.
- **Condition 2 vs the contract's "loop instability".** The canonical contract numbers "no progress" and "loop instability" as separate exits. Both reduce to the same `curr-medium ≥ prev-medium` comparison that `convergence_check.py` computes from the same `--prev-medium N --curr-medium N` flags, so this skill states them as one exit rather than two independently-triggerable ones. Check the contract's per-skill note before assuming every family member keeps them split.
- **Condition 3 threshold (registered deviation).** The contract words cycling as "an identical finding re-flagged after already being applied" and leaves the stop count to each skill. pdo excludes a single recurrence from the rewrite and stops only at two or more, because one BLOCKED finding recurring is the normal shape of a run waiting on the user (see worked-examples Path C); one recurrence would otherwise end every such run at iteration 2.
- **Condition 7 default (registered deviation).** The contract tracks budget only when `--budget-minutes` is passed. pdo arms a 20-minute default because a 16-pass × 5-iteration run at `xhigh` is expensive and an unbounded default was the reason the condition exists; `--budget-minutes=0` restores the contract's behaviour.
- **Corroboration surface (registered stricter deviation).** The contract accepts "a second read of the flagged span" as corroboration for iterations ≥ 2. pdo accepts only a deterministic check or an isolated subagent, because a same-context re-read is the claim restated; the stricter rule can only demote, never promote, a finding.
- **Tiebreak.** `convergence_check.py` ranks its verdicts clean > stable-rewrite > no-progress; Step 5 defers to that order for conditions 1/2/4 and applies lowest-numbered-wins only across the model-judged and caller-side conditions.

All deviations are pdo-local; the contract file is not edited.
