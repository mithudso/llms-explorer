# prompt-deep-optimizer — tooling and caps

Operational reference for `SKILL.md`: the deterministic helper and the canonical numbers. Read it at Step 1a.3 (routing), Step 5 (exits), and Step 6f (self-check).

## Tooling — `scripts/pdo_tools.py`

Every mechanical step in this skill runs through one stdlib-only helper, so its result is a value you did not author. Invoke with the full path; a step it owns is a step you must not re-derive by eye, and its output overrides your own reading.

```
python3 ~/.claude/skills/prompt-deep-optimizer/scripts/pdo_tools.py <subcommand>
```

| Subcommand | Used at | Replaces |
|---|---|---|
| `tokens <path\|->` | Step 1a.3 | Eyeballing the ~600 / ~4,000-token routing boundaries. Returns `profile` and `routing`. |
| `editdist <prev> <curr>` | Step 5 cond. 4 | Estimating edit distance; the documented fallback when `convergence_check.py` is absent. |
| `scan <path\|->` | Step 4 redaction | Spotting secrets and PII by reading. Reports type and line, never the value. |
| `backup <path> --run-id <id>` | `--write` runs | An unbacked in-place write. Refuses to clobber an existing backup. |
| `selfcheck --manifest <file>` | Step 6f | Grading your own run. Returns `self_check: N/8` and names each failure. |

All five print JSON and carry `"evidence": "EXECUTED"`, which is what lets Step 6's evidence table grade the gate honestly. `selfcheck` exits 2 on failure, so an outer loop can branch on it.

## Budget and caps

Canonical source for every count in this skill. Prose elsewhere cites this table; when a number here changes, this is the only place to change it.

| Name | Value | Meaning |
|---|---|---|
| Passes | 16 (A–P) | Every pass emits a row each iteration, `N/A` and `partial` included. |
| Groups | 5 (3 under `profile: small`) | Parallel-dispatch bundles. Group 5 carries 4 passes because 16 does not divide by 5. |
| Iteration cap | 5 (3 under `profile: small`) | Step 5 condition 5. `--max-iter=N` replaces it, clamped 1–10. |
| Cap raise | 3 → 5 | Small profile only. Evaluated **once**, at the iteration-3 boundary, against the iteration 2→3 Medium+ delta; if met, the cap is 5 for the rest of the run. |
| Default budget | 20 minutes wall clock | Step 5 condition 7 runs **by default**, not only under `--budget-minutes`. `--budget-minutes=N` overrides; `--budget-minutes=0` disables. |
| Subagent round-trips | 1 per group per iteration | No mid-iteration retry. A second consecutive error escalates that group to sequential. |
| Drift re-do limit | 3 consecutive failures | Step 5 condition 6. |
| Corroboration threshold | iterations ≥ 2 | Step 3. |
| Small-artifact threshold | ~600 tokens (~2,400 chars) | Mirrors the `/ph`–`/phe` routing bound. Under `profile: small`, effort drops to `high` as well as the group count to 3 — a small prompt does not earn `xhigh`. |
| Long-prompt inline limit | ~4,000 tokens (~16,000 chars) | Above this, ask for a file path rather than inline text. |
