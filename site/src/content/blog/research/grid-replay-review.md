---
title: "Did the historical grid make money?"
description: "Did the historical grid make money?. An edited historical research report with its original evidence limits retained."
date: "2026-11-26"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# Did the grid make money?

Reviewed 2026-11-07 using engine `ad6fe0830c661fa1437a0c5606118f076dd13888`.

**Yes, the resting-order ladder made money in some simulations. The evidence does not yet establish a dependable live strategy.**

## Two different grids

The strategy named `grid` in the roster increases exposure as price falls below a rolling average. It is an exposure staircase, not a set of resting buy and sell orders. Its archived single-split SOL results lost money out of sample (see `backtester/strategy_cards/grid.md`).

The extension's ladder buys at a rung and places a paired exit one rung higher. `backtester/core/gridsim.py` simulates that mechanism. The 2026-11-07 measurements below concern this ladder.

## Daily results recorded on 2026-11-07

The existing cache has 1,875 SOL daily bars from **2021-06-17 through 2026-08-04**. This was a rerun with the stated engine revision on old prices, not new market data. Each account starts with **$144**. Bounds are 85%–115% of the first close, with seven geometric rungs and $12 per rung.

| Experiment | Net account return after modelled costs | Comparison |
| --- | ---: | --- |
| One static ladder over the full history | **+32.10%** (+46.23 USD) | Holding SOL: +88.10% |
| Median of eight independent periods | **+7.67%** | 5 of 8 periods profitable; 5 of 8 beat holding |
| Worst independent period | **-34.92%** | A substantial loss despite profitable other periods |

These are **total returns for their respective periods**, not monthly or annual rates. The independent periods are about 234 days each. They reset cash and close inventory at each boundary; they do not simulate a continuous recentering policy. Holding invests the full account while the ladder retains cash, so this is not a comparison at equal market exposure or risk.

Costs are **6 bps fee plus 2 bps slippage per fill**, approximately **16 bps per buy/sell round trip**. One basis point is 0.01%. Carry is zero because this experiment is unborrowed spot. A leveraged grid would need additional borrowing and liquidation modelling.

The static ladder sits outside its bounds on **93.1%** of closes. Closed winning cycles do not tell the whole story: unsold inventory can lose more than the cycles earn. The full-account return includes that inventory and final liquidation. The $72 nominal rung budget is not the account value or measured deployed equity; do not use it as the account-return denominator.

## Is improvement feasible?

A completed cycle can earn more than its fees when price repeatedly crosses the rungs. That explains why profitable periods exist. The hard problem is keeping those gains when the market trends, jumps or leaves the range.

The next useful experiments would predeclare: a range/regime entry gate, a firm inventory budget, and a recentering/exit rule that accounts for old orders, open lots and the cost of closing or moving them. Test these on held-out periods and other assets, with stressed fees/slippage, against holding and cash at comparable risk. These are **hypotheses, not demonstrated improvements**. More parameter searching alone is not evidence of a better strategy.

## Evidence and limits

`research/results/grid_review_20261107.json` records the exact configuration, engine revision, source SHA256, slices and all nine results. An independent audit reproduced them. The older `research/results/ladder_grid_sol.csv` and its strategy-card tables preserve a different, pre-audit engine result; they should remain historical. Simulated fills and block resets do not validate the extension's live execution or recentering behavior.

## Separate 94-bar period (reviewed 2026-11-07)

The review's cache ended 2026-08-04. `research/grid_holdout.py` scores the **same predeclared ladder** (85%–115% of the first close, seven geometric rungs, $12 per rung, $144 account) on the 94 finished daily bars from 2026-08-05 through 2026-11-06. Nothing was fitted, and the 2026-11-07 bar is excluded because it was still forming. Result file: `research/results/grid_holdout_20261107.json` (records the data SHA256 and fetch command).

| | Grid | Holding SOL |
| --- | ---: | ---: |
| Review costs (6 bps fee + 2 bps slippage) | **+0.83%** ($1.20 realized, 2 round trips) | **+21.6%** |
| Twice those costs | +0.81% | +21.5% |

SOL rose from $73.97 to $90.02. Price sat above the ladder on **80 of 94 bars**, so the grid held cash while the market rallied. Mechanically annualizing +0.83% over 94 days gives about 3.3%; that is an illustration, not a forecast or a verified comparison with cash or staking. Cost sensitivity is negligible here; the shortfall is idle capital, not fees.

This is one 94-bar path in one regime. It does not refute the eight-block median of +7.67%, and it does not show the grid works. It confirms the structural point above: a ladder armed near the price earns only while price oscillates through it, and trades nothing once price leaves it. Any improvement still has to come from a regime gate or a tracking exit rule, tested on data like this that was not used to design it.

The separate period was reserved relative to this ladder review. No claim is made that its historical dates were unseen by every earlier project experiment. All engine results above are historical simulations; this publication did not replay the engine.
