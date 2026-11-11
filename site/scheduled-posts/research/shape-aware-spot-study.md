---
title: "An exploratory shape-aware spot study"
description: "An exploratory shape-aware spot study. An edited historical research report with its original evidence limits retained."
date: "2026-11-30"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# Shape-aware spot study

As of 2026-11-11. Historical research only. The detector and results establish no live trading edge.
All return tables are percentages on an initial $10,000 spot account, with no borrowing or shorting.

The practical result is mixed: use shape routing as a research candidate, not an established edge.
At zero commission and 2 bps execution per side, hourly shape routing beats fixed selection on five
of eight coins and continuous holding on six. Adding range-position zones does worse. At 25 bps
execution per side, every hourly shape router loses money. ZEC leads passive returns, and shape
routing leaves substantial ZEC upside uncaptured. Lower commission helps; spread can erase the gain.

## What counts as a shape, and where are we within it?

The prior research found five conceptual families: order-book saddles, liquidity-void V reversals,
rounding bowls, compression wedges and topological persistence loops. Its quoted win rates, Sharpe
deltas, profit factor and drawdown reductions failed independent source review. Two bowl citations
were copies of the same US equity overnight-drift paper. Those numbers are not used here.

This study measures **OHLC price-path proxies**. It cannot identify a true order-book saddle, establish
liquidation flow/VPIN, or compute persistent homology from an unimplemented proxy. Those three
mechanisms require additional observations or a separately implemented topological estimator.

| Observable state | Completed-bar rule, fixed before evaluating results | Position within the observed shape |
| --- | --- | --- |
| Up/down trend | Absolute net log move / sum absolute log moves >= 0.25 over 48 bars; net sign gives direction | Range position, direction, episode age |
| Range | Path efficiency < 0.25 | Lower/middle/upper third of the trailing high-low range |
| V rebound / inverted V | First half falls/rises > 2 rolling one-bar standard deviations; second half reverses > 2; range position confirms recovery | Fraction of observed drop recovered; only confirms after the turn |
| Bowl / cap | Quadratic fit of log closes, R² >= 0.80, normalized bend >= 0.15; fitted vertex in the interior | Fitted turn age, curvature sign, range position |
| Compression | Fitted high slope negative and low slope positive; end width 10–65% of start width | Position between current fitted bounds and extrapolated bars to apex |

Rules use 48 trailing completed candles. Priority is compression, bowl/cap, V/inverted V, then trend/range.
The first 47 bars are unknown. Shapes can overlap; priority assigns one primary label. R² is fit quality,
not the probability of profit. Episode age counts consecutive detected labels, not the true pattern start.
Range position and rebound fractions describe observed history, not the eventual lifecycle percentage.
An extrapolated wedge apex is a geometric estimate, not a forecast that a breakout must occur there.

Every tag has a candle timestamp and an `available_at` timestamp at its close. Decisions fill at the
following open. The saved interval files contain when each label became known, its last observed time,
bar count and start/end range position. Future poisoning and prefix replay tests prevent retroactive tags.

## Data and evaluation contract

Eight Coinbase USD markets: BTC, ETH, SOL, XRP, DOGE, ZEC, LINK and AVAX. Existing native Coinbase
hourly/daily caches supply seven assets. The explicit public fetch step obtained missing ZEC-USD
hourly and daily candles. Six-hour bars require all six hourly candles. No candle is interpolated.
Within each timeframe, every coin has exactly the same contiguous dates. The common suffix rule
trims gaps using timestamps, before seeing strategy returns. Different timeframe windows are not pooled.

The historical source pool was already explored in earlier studies. These are expanding chronological
walk-forward tests, not a new untouched final holdout. The run checks the existing holdout ledger in
read-only mode and refuses any overlap with unsealed protected dates. It does not overwrite reservations.

The first 40% trains selection; the next three 20% windows are disjoint tests. Canonical indicators
warm from prior history. Training starts after the longest 251-bar warmup and excludes two boundary
bars. Later folds may learn from earlier test windows once those windows are history. Each active
fold starts flat and pays its final exit; compound fold returns. `buy_hold` continuously holds across
all three test folds; `fold_reset_hold` supplies a separately named turnover-matched passive comparator.

Six canonical default singles: MACD, breakout, RSI, Bollinger reversion, OU reversion and ADX trend.
Three fixed half-weight exposure mixtures: MACD/RSI, breakout/OU and ADX/Bollinger. Mixtures rebalance
one shared account; they are not fictitious simultaneous full-capital books. The shape-free selector
chooses among these nine policies and cash by training net log return. The rule-based shape policy
uses MACD for rising trends/bowls, OU for ranges/V rebounds, breakout for compression, otherwise cash.

The learned shape router chooses a training-best arm per shape. The shape/zone router also conditions
on lower/middle/upper range position. A state needs 30 training bars and three observed episodes;
otherwise it uses the training-best shape-free arm. These floors do not imply independent samples.
Training scores attribute continuous-arm next-bar returns to the preceding shape. Actual routed replay
pays its own switching costs. Five fixed-seed permutations of **training labels only** provide a noise
diagnostic. They are not a calibrated significance test because shuffling removes serial dependence.

## Coinbase One and costs

The source study’s 2026-11-11 reading of Coinbase terms says Coinbase One waives commission on eligible simple trades within plan limits. A spread remains.
Coinbase Advanced is excluded; official terms also describe a 1% limit-execution exception. API access
for automated trading is part of Advanced. Therefore membership does not establish fee-free bot execution.
The zero-commission runs are conditional scenarios. Execution drag is 2, 10, 25 or 50 bps **per side**;
these are assumptions, not measured account quotes. A control charges 10 bps commission plus 2 bps
execution per side. Both entry and exit pay costs, including fold exits. Membership price, plan-cap
exhaustion, rebates, tax, order-size constraints, market impact and latency are not modeled. Turnover
is saved so the owner can compare it with the actual plan cap. Spot needs no borrow/funding model.

https://help.coinbase.com/en/coinbase/other-topics/coinbase-one/account
https://help.coinbase.com/en-gb/getting-started/other/coinbase-vs-coinbase-advanced

## Measured results

The tables below use zero commission and **2 bps execution per side** unless stated otherwise.
They are generated from checksum-bound curves, not copied from the geometry dossier.

### 1h: 2026-07-20 19:00 UTC through 2026-11-06 23:00 UTC

| asset | passive_pct | fixed_pct | shape_pct | zone_pct |
| --- | --- | --- | --- | --- |
| ZEC | 141.27 | 119.30 | 95.29 | 98.74 |
| AVAX | 26.99 | -8.66 | 65.05 | 36.93 |
| SOL | 15.97 | 22.39 | 42.10 | 17.05 |
| LINK | 26.78 | 29.02 | 35.88 | 11.91 |
| XRP | 5.71 | -9.80 | 21.93 | 11.09 |
| ETH | 17.73 | 25.03 | 20.22 | 11.95 |
| DOGE | -0.10 | -2.87 | 15.21 | -15.37 |
| BTC | 16.12 | 6.82 | -13.57 | -19.19 |

### 6h: 2026-07-20 18:00 UTC through 2026-11-06 18:00 UTC

| asset | passive_pct | fixed_pct | shape_pct | zone_pct |
| --- | --- | --- | --- | --- |
| LINK | 26.50 | 16.97 | 34.75 | 15.30 |
| AVAX | 26.22 | 20.89 | 33.40 | 36.26 |
| ZEC | 139.92 | 13.48 | 19.73 | 13.48 |
| ETH | 17.20 | -7.42 | 7.95 | -11.66 |
| BTC | 15.51 | -9.93 | 4.25 | 0.64 |
| SOL | 15.85 | 7.10 | -5.52 | -0.70 |
| XRP | 5.64 | -10.91 | -10.14 | -22.79 |
| DOGE | -1.03 | -22.14 | -23.02 | -21.13 |

### 1d: 2024-11-10 00:00 UTC through 2026-11-06 00:00 UTC

| asset | passive_pct | fixed_pct | shape_pct | zone_pct |
| --- | --- | --- | --- | --- |
| ZEC | 2768.97 | 2387.10 | 1566.96 | 650.46 |
| XRP | 110.35 | 139.44 | 109.01 | 131.29 |
| SOL | -55.01 | -14.02 | 106.41 | 12.39 |
| LINK | -21.34 | 29.33 | 10.31 | -21.79 |
| BTC | -1.32 | -5.37 | 6.65 | -9.96 |
| AVAX | -72.60 | -41.28 | 2.11 | -17.32 |
| DOGE | -67.01 | -7.12 | -12.39 | -9.38 |
| ETH | -28.56 | -56.04 | -49.06 | -29.87 |

### Does conditioning improve decisions?

Counts are out of eight coins per row. Compare within each timeframe.

| interval | policy | beats_fixed | beats_hold | beats_five_nulls |
| --- | --- | --- | --- | --- |
| 1d | shape_router | 4 | 5 | 4 |
| 1d | shape_zone_router | 3 | 4 | 2 |
| 1h | shape_router | 5 | 6 | 5 |
| 1h | shape_zone_router | 2 | 3 | 1 |
| 6h | shape_router | 6 | 2 | 1 |
| 6h | shape_zone_router | 3 | 1 | 1 |

### Hourly shape-router cost sensitivity

Column suffixes are execution bps per side. `fee10_exec2` additionally charges 10 bps commission per side.

| asset | fee10_exec2 | zero_10 | zero_2 | zero_25 | zero_50 |
| --- | --- | --- | --- | --- | --- |
| AVAX | 27.27 | 34.06 | 65.05 | -6.99 | -9.66 |
| BTC | -29.06 | -24.95 | -13.57 | -43.05 | -59.38 |
| DOGE | -2.49 | 1.73 | 15.21 | -25.98 | -56.43 |
| ETH | -6.95 | -3.86 | 20.22 | -21.92 | -42.21 |
| LINK | 2.75 | 5.70 | 35.88 | -30.00 | -62.13 |
| SOL | 14.33 | 18.60 | 42.10 | -16.39 | -48.48 |
| XRP | -10.06 | -3.33 | 21.93 | -32.89 | -56.88 |
| ZEC | 41.94 | 50.63 | 95.29 | -9.95 | -42.12 |

### Which policies behaved better inside each hourly shape?

Descriptive, hindsight-ranked **next-bar P&L attribution**, pooled across eight correlated coins. These are not trade returns or recommendations. Bars overlap in their 48-bar detection windows.

| shape | best_single | single_bps | best_mixture | mixture_bps | bars_per_policy |
| --- | --- | --- | --- | --- | --- |
| bowl | adx_trend | 5.89 | mean_breakout_ou_reversion | 2.64 | 1174 |
| cap | rsi | 3.60 | mean_macd_rsi | 2.04 | 987 |
| compression | macd | 1.63 | mean_macd_rsi | 1.09 | 488 |
| inverted_v | breakout | -0.15 | mean_breakout_ou_reversion | -0.29 | 2269 |
| range | rsi | 0.22 | mean_macd_rsi | 0.22 | 11253 |
| trend_down | rsi | 7.64 | mean_macd_rsi | 5.27 | 1090 |
| trend_up | adx_trend | 10.29 | mean_adx_trend_bb_reversion | 5.14 | 1655 |
| v_rebound | macd | 3.72 | mean_macd_rsi | 1.84 | 2052 |

Full conditional results include per-coin inside/outside mean bps, bar/episode counts and log-return contributions.
Positions can predate a label change. Neither a conditional mean nor the best hindsight row establishes a causal effect.
The strategy/coin/timeframe/cost search is extensive; there is no multiplicity-adjusted significance claim.
The six-hour training segment after warmup is especially small. No shape router consistently wins across all assets.
Adding position zones increases selection complexity and can reduce performance. A favorable zero-fee result does
not prove membership offsets leverage; removing commission changes costs, while leverage/shorting change exposure.

## Which coins were profitable again?

The older common-window minute study's passive leaders were **ZEC +145.7537%** and **HYPE +74.6592%**
(February–August 2026). Its positive active VWAP-reversion cells included **DOGE +17.8762%**, **SOL +3.8742%**
and **ETH +0.1807%**. That single-pass minute sweep had gaps and no held-out selection.
The daily CPCV breadth leaders were **BTC 24/24 rankable singles positive** and **ZEC 24/25**, followed by
ETH 18/24, DOGE 16/25 and SOL 13/25. Breadth of positive median Sharpe is not a return ranking.
The recent ZEC Volty daily adaptive study earned **+22.688%**, versus **+1783.710% passive**; every fixed
training winner lost out of sample. These are different experiments, not interchangeable coin league tables.

For this study, read the within-timeframe tables above: ZEC is the strongest passive coin in each tested
window. Shape routing can improve some other coins while giving up part of ZEC's buy-and-hold gain.
None of these rankings establishes the most profitable coin for the next period.

## Reproduction and artifacts

The runner never places orders or changes installed Oracle/paper policies. All raw input hashes, canonical
engine/strategy hashes, versions, windows, scenarios and output hashes are in the committed manifest.
Full bars, tags, shape intervals, per-bar decisions, selections and equity curves live in the run folder.
The compact committed results retain all policy returns, conditional inside/outside attribution and snapshots.
Snapshots describe the final **historical** candle, not the live market.

The source taxonomy is `research-library/market-graph-geometry/dossier.md`,
with related claim and strategy-matrix files in that directory. Historical comparison sources are
`research/CROSS-ASSET-TRANSFER.md`, `research/results/minute_sweep_x1_common.csv` and
`docs/VOLTY-ZEC-STUDY.md`. The retained independent audit rejects the earlier geometry efficacy claims while retaining its taxonomy as hypotheses.

```bash
python -m unittest research.tests.test_shape_study -v
python -m research.shape_study --data-dir "$MARKET_DATA_DIR" --zec-dir RESEARCH_ARCHIVE/shape-spot-20261111/input --output RESEARCH_ARCHIVE/shape-spot-20261111/reproduction
```

Use a fresh output directory. The runner refuses to overwrite completed evidence.
The exact primary run is `RESEARCH_ARCHIVE/shape-spot-20261111/run-v3`.
Prior exploratory runs are retained separately and do not certify the final source.

Publication note: `RESEARCH_ARCHIVE`, `SERVICE_HOME` and `COMPOUND_STATE` denote the original retained study archives or state directories. `$STUDY_REPO`, `$STUDY_PYTHON` and `$MARKET_DATA_DIR`, where shown, must point to the matching study checkout, environment and data. These private artifacts are not bundled with this article. Historical acceptance statements above describe the original study; publication review did not rerun experiments or operate services.
