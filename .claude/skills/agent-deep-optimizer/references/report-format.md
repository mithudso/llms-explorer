# Step 8 report format

The exact shape of the `/ado` Step 8 report. Output the sections in this order.

**Convergence table** (required):

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | n | n | n | applied n fixes |
| 2 | 0 | 0 | n | converged, stopped |

Beneath it: a **Schema row** (`schema: n findings, h High folded into iteration 1 (ado_tools.py schema, EXECUTED)`), a **Roster row** (`roster: N agents, ~T tokens of descriptions (budget 15,000); shadowing: none | <names>`), and, when `--budget-minutes` was passed, the wall time.

**Findings table**, capped at 20 rows with the rest rolled up:

| Pass | Finding | Level | Evidence | Action taken |
|---|---|---|---|---|

**Delegation-eval results** (Pass O):

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-delegate rate | n/10 | ≥ 9/10 | ✓ / ✗ |
| should-not-delegate rate | n/10 | ≤ 1/10 | ✓ / ✗ |

Label the table `eval: measured (trigger_runner.py, <hybrid | bm25-only>)` or `eval: predicted (<reason>)`. Never conflate the two.

**Load check** (Step 6, when run), one line: `smoke: ready (exit 0, $x.xx, 12s)` / `smoke: failed (<stderr tail>)` / `smoke: skipped (<reason>)`.

**Unified diff preview.** One fenced `diff` block per file modified (target, each peer, each eval file), changed hunks only, capped at 80 lines per file with truncation noted. Under `--read-only` label each block `proposed (read-only, not applied)`.

**Routing verification** (Step 7), one row per agent written (target and every Pass C peer):

| Agent | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| <name> | indexed / stale / unroutable | yes / no | yes / no | n |

When the gate withheld the rebuild, the row carries `rebuild withheld: N High findings remain`.

**Keyword router** (Pass P), one line: `router: routed (ROUTES + rules row present)` / `router: not routed (operator action proposed: <regex>)` / `router: n/a (not an auto-delegation agent)`.

**Compress outcome** (Step 7.5), one line, only when `--compress` was passed.

**Prose-index daemon** (Step 7.6), one line: `prose-index: daemon up` or `prose-index: daemon down (operator action)`.

**Degraded tally** (Step 7.8), one line naming each post-sync outcome that did not land, plus the exit status.

**Model/effort recommendation** (Step 4.6), one line: `model: <alias-or-id> · effort: <level> (tier: <tier>; <heuristic | caller-pinned>; id source: <models.md | models overview | harness roster | alias>): <one-sentence rationale>`, followed by `startup context ≈ <n> tokens (body + preloads + CLAUDE.md)`.

**Snapshot & rollback.** One line carrying the literal restore command from `ado_tools.py backup`: `cp ~/.claude/skill-consolidation/backups/agent-deep-optimizer-<ts>/<name>.md <path>`.

**Version control.** One line: `git: committed <sha>` / `git: uncommitted (operator action: commit ~/.claude/agents/<name>.md)` / `git: n/a (plugin target)`.

**Telemetry.** Append rows per the canonical telemetry schema (contract § Telemetry; `artifact_type: "agent"`, fail-safe). Under `--read-only`, emit the fields in the report without writing a ledger. Flag any wasted iteration (iteration ≥ 3 that closed zero Medium+ findings).

**One-line summary.** "X high, Y medium, Z low findings across N iterations (profile: <small | standard>). M sections rewritten. Registry rebuild: <success | skipped | withheld | failed>. Routing: <indexed | stale | unroutable>. Smoke: <ready | skipped | failed>. Exit: <converged | DEGRADED | …>."

**Modified-sections list.** Every frontmatter key and every H2 in the body that changed, plus each peer file touched.

**Delegation-eval queries used**, collapsed by default.

If no Medium+ findings exist, omit the empty findings table and diff previews. Retain eval mode/results, routing verification, post-sync outcomes, degraded tally, exit status, and snapshot/telemetry outcomes. A content-clean result never hides operational degradation.
