# code-deep-optimizer — changelog

Moved out of SKILL.md frontmatter 2026-09-09: it was 2,546 bytes, 47% of the always-loaded
frontmatter, with no bearing on execution.

## 2026-09-09 v1.8.0 -> 1.9.0 — contract-compliance pass

Applied from a /p audit (1 Critical, 6 High, 8 Medium found). Amended
`~/.claude/skill-consolidation/convergence-and-severity.md` to add a registered **triage mode**
construct, legalizing `--quick`'s Critical-only bar instead of leaving it as a unilateral
exception to the profile invariant; registered cdo's small profile in the contract's table.
In this file: promoted the injection guard from a Guardrails bullet to a non-skippable Stage 0.5
gate propagated verbatim into every per-file subagent brief; adopted the contract's
streaming-checkpoint crash recovery (cdo fans out to 50 files and was the only heavy sibling
without it); gave `--quick` a verify baseline so FAIL can be attributed; fixed the
`min(16, cores-2)` concurrency underflow to `max(1, ...)`; added a flag-interaction table whose
first rule closes the `--no-verify` + default-on-empirical hole that left promotion ungated;
renamed `--structural-only` to `--no-empirical` (alias kept) to stop colliding with
skill-optimizer's `--meta` idiom; surfaced empirical mode's champion persistence at invocation;
moved this changelog out of frontmatter and collapsed SKIP guidance from three places to two.
`--minimal` was considered and declined — `--quick` plus full mode is the intended surface.

## Earlier

```
2026-09-04 v1.7.0->1.8.0 — added `--quick` fast path: 1 iteration, Critical-only findings, single end-of-run verify check (no baseline/bisect loop), skips Stage 0 formal activation ceremony, advisory track, empirical mode, and the blind re-audit gate. For low-stakes/prototype code where an 18-pass audit is disproportionate — not for anything shipping to production. Paired with an auto-optimize-dispatcher.sh hook fix: throwaway/sandbox/prototype-named files no longer get the full-convergence nag by default.
2026-07-20 sko v1.6.1->1.7.0 — Pass H 10/10 pos, 9/10->10/10 neg (predicted); 1 High + 8 Medium fixed across 2 iters: champion-challenger contract path restored (symlink at ~/.claude/skill-consolidation/), references synced 16->18-pass (map +S5/T4 rows, worked-example 14/18), cold-spoke citations hub-aware, SQL hot-spot SKIP edge -> deep-query-optimizer, O-seeded security-review + dmqo; exit BLIND-AUDIT-DISSENT (1 residual Medium: worked-example no-manifest wording vs npm-test verify baseline).
2026-06-23 sko v1.5.0->1.6.0 — Pass H 10/10 pos, 0/15 neg (predicted); 2 Medium fixed: added advisory model/effort frontmatter (Step 4.6 -> claude-opus-4-8 / xhigh, long-horizon agentic tier); trimmed changelog 8->5 entries (family 5-cap). No content/routing/over-ceiling/hygiene findings.
2026-06-23 v1.4.0->1.5.0 — Empirical mode now default-on (gated auto-promote + persist) per § Default policy in the shared contract: when a test/benchmark eval set + must-pass checks are present the champion–challenger loop runs without a trigger, auto-promotes through the unchanged gate (held-out margin + must-pass veto = suite green + API unchanged), and persists the champion across runs (prior champion archived for rollback); mandatory holdout rotation/budget/noise to prevent reusable-holdout overfitting; honest guarantee = monotonically non-decreasing on the holdout, not "better every run"; opt out --dry-run/--no-promote/--structural-only; loud no-eval fallback. Per operator request.
2026-06-23 v1.3.0->1.4.0 — added Empirical mode (champion–challenger held-out loop) section + --empirical flag, citing the new shared contract ~/.claude/skill-consolidation/champion-challenger.md; calibration: score = pass rate on a held-out test/benchmark subset (or perf metric), must-pass veto = full pre-existing suite green + no new lint/type errors + public API unchanged (reuse Verify-gate baseline). Orthogonal to the fix-track passes — no pass-count change. Per operator request.
```
