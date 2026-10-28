# Report format — code-deep-optimizer

Extracted from SKILL.md on 2026-10-05 (v1.16.0) to bring the body back under the skill-optimizer
~10k-token ceiling. SKILL.md § Report keeps a pointer here. Read this file before writing the
final report. Emit the sections in this order.

1. **Per-iteration severity table**: Critical / High / Medium / Low / Nit per iteration.
2. **Findings table**: `Pass | file:line | Severity | Finding | Fix | Status` (capped, rest rolled up).
3. **Verify-gate table**: `command | baseline | after-iter | verdict` (one row per package in a monorepo).
4. **Activated-skills list**: which language/domain skills loaded and why (from Stage 0).
5. **Unified `diff` per file**: capped per file, truncation noted.
6. **Blind re-audit result** (CLEAN exits only; `N/A` under `--quick` and on every non-clean
   exit), plus cross-model residuals if `--cross-model` ran.
7. **Recommendations** *(only under `--suggest`)*: advisory items grouped A1 / A2 / A3, each with
   grounding evidence (`file:line` / TODO / caller); separate from the findings table, never
   counted in the severity table or Status math.
8. **Implemented features** *(only under `--implement-features`)*: one row per feature,
   `Feature | evidence | files | tests added | verify | Status (Implemented | BLOCKED (verify-gate regression) | skipped)`.
   Mechanics: `references/implement-features.md`.
9. **Summary (one line)**: `Iterations · Active passes · Profile · Final C/H/M/L · Verify: PASS|FAIL|N/A · Status: CLEAN|CONVERGED|OSCILLATING (cycling|instability)|NO_CHANGE|CAPPED|BUDGET_EXHAUSTED|BLIND-AUDIT-DISSENT|TRIAGE-PARTIAL|TRIAGE-CLEAN|BLOCKED (hostile content)|BLOCKED (--scope=changed: not a git repo)`.
   Each status maps to a contract exit in `references/flags-and-statuses.md`. Append fields as
   they apply:
   - `· wall: N min` when `--budget-minutes` was passed.
   - `· Recommendations: N` when `--suggest` ran.
   - `· Features: N implemented / M blocked` when `--implement-features` ran.
   - Under a triage mode (`--quick`): `mode: --quick (bar: Critical)` and the required
     `Unfixed: N High / M Medium` field. The status **must** be `TRIAGE-PARTIAL` or
     `TRIAGE-CLEAN`, never `CLEAN` or `CONVERGED`, per the contract's § Triage modes.
10. **Snapshot & rollback**: the literal restore command, for example
    `cp ~/.claude/skill-consolidation/backups/<target>-<ts>/<filename> <path>`, plus one
    `rm <path>` per file the run created (C3 counterexample tests, T1 tests, feature files).
11. **Index line**: `index: refreshed | stale (<reason>) | n/a (outside corpus roots) | skipped (--no-sync)`
    per the contract's § Semantic-index integration. Only a target under the index corpus roots
    (`~/.claude/skills`, `~/.claude/skill-consolidation`, mdb-context-hub docs) needs the refresh.
12. **Memory-central line**: `memory-central: <n> lessons · <m> conventions consulted · <k> regression checks fired | none for <slug>`
    (from SKILL.md § 0.3b), plus `lessons written: <path>` when the run recorded new ones.

Full end-to-end run on a single JS/TS file: `references/worked-example.md`.
