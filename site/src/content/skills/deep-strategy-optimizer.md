---
title: "deep-strategy-optimizer"
description: "Audit-and-fix convergence optimizer for trading strategies and their backtests: 19 passes over simulation integrity, statistical honesty, claim provenance, and economics — where 'no promotion' is the expected result."
order: 16
tags: [trading, backtests, statistics, optimization]
aliasCommand: "/dso"
---

The strategy member of the family, built around one premise: most backtest edges are
artifacts. Nineteen passes audit a strategy, its card, and the research behind it —
simulation integrity (lookahead, cost path, accounting, data), statistical honesty
(protocol grade, multiple-testing burden, evidence floor, degeneracy, attribution),
claim provenance, economics, and tests.

Medium+ fixes are applied and verified against the project's own suites, looping to
convergence. The opt-in `--promote` mode runs a gated champion–challenger climb on
held-out cross-validation blocks — where **no promotion is the expected outcome**, and
a promotion has to earn its way past the gate rather than past the operator's
optimism.

**Use it for:** "run dso", "optimize this strategy", "is this backtest honest",
pre-deployment audit of a strategy card and its evidence.

**Not for:** the backtest *code*'s general quality
([code-deep-optimizer](/skills/code-deep-optimizer/)) · market research with no
strategy artifact yet · portfolio advice.
