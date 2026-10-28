# Empirical mode — champion–challenger calibration for code

Extracted from SKILL.md on 2026-10-05 (v1.16.0). SKILL.md § Empirical mode keeps the default,
the opt-outs, and the pointer here. The loop mechanics (persisted state, split discipline,
one-change-per-round, margin-gated promotion with must-pass veto, stop conditions, output) are the
shared contract `~/.claude/skill-consolidation/champion-challenger.md`. Cite it; do not restate it.

## Engagement

- **On by default** when the code ships with a test/benchmark eval set plus must-pass checks.
- It persists the champion across runs at
  `~/.claude/skill-consolidation/champions/<target-slug>/champion.json`. The prior champion is
  archived beside it as `champion.<ts>.json`.
- Opt out with `--no-empirical`. Run without persisting with `--dry-run` / `--no-promote`.
  `--read-only` implies `--dry-run`. `--no-verify` and `--annotate` force `--no-empirical`.
- With no eval set plus must-pass, fall back to the structural loop and say so
  (`cannot auto-improve`).
- It is a separate loop, not a pass, and is orthogonal to the fix-track passes. Run the
  structural loop first for a clean champion, then climb.

## Calibration

- **Score** = pass rate on a **held-out** test/benchmark subset, or a perf metric
  (latency/throughput) when the objective is performance.
- **Must-pass (veto)** = the full pre-existing suite stays green, no new lint/type errors, and the
  public API is unchanged. Reuse the § Verify gate baseline set as the veto.
- **Eval surface** = a reserved test subset or benchmark harness that never drives an edit and
  only gates promotion.
- **One change per round**, so each promotion is attributable. The held-out subset is never used
  to choose the fix.
- `--implement-features` runs after this loop and outside it, because a feature addition fails the
  public-API veto by design (`references/implement-features.md`).
