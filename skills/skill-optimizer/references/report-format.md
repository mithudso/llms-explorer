# Step 8 report format

The exact shape of the `/sko` Step 8 report. The `SKILL.md` body keeps a one-line pointer here to stay within the Pass J token budget. Output the sections in this order.

**Convergence table** (required):

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | n | n | n | applied n fixes |
| 2 | n | n | n | applied n fixes |
| 3 | 0 | 0 | n | converged, stopped |

Beneath it, report Pass L's pre-loop sweep in a separate **Hygiene row** (`Hygiene: n fixed`); hygiene fixes are excluded from the Medium+ totals above. When `--budget-minutes` was passed, a budget exit uses `budget, stopped` as the final-row Action and the report notes wall time.

**Findings table**, capped at 20 rows with the rest rolled up:

| Pass | Finding | Level | Action taken |
|---|---|---|---|

**Trigger-eval results** (Pass H):

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | n/10 | ≥ 9/10 | ✓ / ✗ |
| should-not-trigger rate | n/10 | ≤ 1/10 | ✓ / ✗ |

Label the table with the eval mode, either `eval: measured` or `eval: predicted (<reason>)`. Never conflate the two.

**Unified diff preview.** One fenced `diff` block per file modified, showing only the changed hunks (`diff -u baseline current` semantics; cap each file's diff at 80 lines and indicate truncation).

**Routing verification** (Step 7), one row per skill written:

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| <target-id> | indexed / stale / unroutable | yes / no | yes / no | n |

When the gate withheld the rebuild, the table carries `rebuild withheld: N High findings remain` for each withheld skill. A legacy `context.md` target carries `n/a (not indexable)`.

**Compress outcome** (Step 7.5), one line: `compress: done (n → m lines)` or `compress: skipped (<reason>)`. Omit the line entirely when `--compress` was not passed.

**Prose-index daemon** (Step 7.6), one line: `prose-index: daemon up` or `prose-index: daemon down (operator action)`.

**Index refresh** (Step 7.7), one line: `index: refreshed (N skills)` or `index: skipped (<reason>)`.

**Degraded tally** (Step 7.8), one line naming each post-sync outcome that did not land, plus the resulting exit status. For example: `degraded: 2 of 4 post-sync outcomes missing (index skipped, routing stale), exit DEGRADED`, or `degraded: none, exit converged`.

**Model/effort recommendation** (Step 4.6), one line: `model: <id> · effort: <level> (tier: <matched tier>; <heuristic | caller-pinned>): <one-sentence rationale>`.

**Snapshot & rollback.** One line carrying the literal restore command, per the contract's pre-write snapshot guardrail: `cp ~/.claude/skill-consolidation/backups/<skill>-<ts>/<filename> <path>`.

**Telemetry.** Append telemetry rows per the canonical telemetry schema (the contract's Telemetry section; fail-safe, so a write error never blocks the run), and flag any wasted iteration (iteration 3 or later that closed zero Medium+ findings) in the summary.

**One-line summary.** "X high, Y medium, Z low findings across N iterations (profile: <small | standard>). M sections rewritten. Registry rebuild: <success | skipped | withheld: N High remain | failed>. Routing: <indexed | stale | unroutable>. Exit: <converged | DEGRADED | …>." Append wall time when `--budget-minutes` was passed.

**Modified-sections list.** Every H2 in `SKILL.md` and every top-level key in `manifest.yaml` that was changed.

**Trigger-eval queries used**, collapsed by default and expanded only if the caller requests them.

If no Medium+ findings exist, say so in one line and skip the rest.
