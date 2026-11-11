---
title: "The historical frontier of a five-minute compound signal"
description: "The historical frontier of a five-minute compound signal. An edited historical research report with its original evidence limits retained."
date: "2026-11-24"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# Compound 5m frontier: fewer, stronger, longer calls (2026-11-07)

Historical simulation snapshot: **2026-11-07**. Fee schedules, UI features and recommendations describe that implementation. Later accounting or strategy changes are not retrospectively certified by these rows. The historical test slices were repeatedly inspected across related searches; “out-of-sample” names a chronological split, not globally untouched confirmatory evidence.

The owner's question: the reversion metrics "are doing ok in testing" (52% out-of-sample hit on SOL)
but every row says the profit is eaten by fees. How do you get around that, and is there a better
strategy nearby? This page answers both with the frontier sweep (run `20261107T202943Z`, 1,250
configurations, ten coins, the available cached 1-minute inputs) and the in-sample-only tuner
(`research/frontier_tune.py`, results in `research/results/frontier-2026-11-07.json`).
Simulation only; nothing here places an order.

## Input coverage and discontinuous accounting

The saved frontier ledger `20261107T202943Z` contains 1,250 configuration rows. Each coin has a different available calendar history and its own split at 70% of retained bars. Cross-coin medians below therefore combine different historical windows; they are not common-calendar return or Sharpe comparisons. The first/split/last timestamps describe the input, not proof that every intervening five-minute bar was evaluated.

| Coin | Input first UTC bar | OOS split UTC | Input last UTC bar | Incomplete 5m buckets % | Evaluated segments |
| --- | --- | --- | --- | ---: | ---: |
| AVAX | 2021-09-30 19:00 | 2025-04-24 08:10 | 2026-11-07 13:55 | 29.658 | 101 |
| BTC | 2019-11-09 14:00 | 2024-10-01 21:30 | 2026-11-07 14:00 | 0.025 | 21 |
| DOGE | 2021-06-03 16:10 | 2025-03-22 10:55 | 2026-11-07 14:00 | 4.487 | 17 |
| ETH | 2019-11-09 14:00 | 2024-10-01 21:05 | 2026-11-07 14:00 | 0.504 | 24 |
| HYPE | 2026-02-05 19:20 | 2026-08-17 07:05 | 2026-11-07 14:00 | 28.481 | 23 |
| LINK | 2019-11-09 14:00 | 2024-10-02 00:30 | 2026-11-07 14:00 | 10.993 | 52 |
| NEAR | 2022-09-01 16:45 | 2025-08-06 17:20 | 2026-11-07 14:00 | 37.780 | 109 |
| SOL | 2021-06-17 16:05 | 2025-03-26 16:05 | 2026-11-07 14:00 | 1.037 | 14 |
| SUI | 2023-05-18 16:10 | 2025-11-11 09:35 | 2026-11-07 14:00 | 23.628 | 36 |
| XRP | 2019-11-09 14:00 | 2025-06-30 10:00 | 2026-11-07 14:00 | 0.807 | 21 |

“Incomplete 5m buckets” is the percentage of retained five-minute buckets built from fewer than five observed one-minute candles. It is not the percentage of calendar history missing. The field does not count a completely absent bucket, measure raw minute coverage, or report the share of bars discarded in short segments. Missing minutes can distort the last observed close and omit highs/lows used by execution and liquidation checks. The table reports the saved ledger’s metadata; no new replay repaired these inputs.

The archived November 7 implementation at revision `afaae08e751a5db0d017a9dee88e2fd8e5c8a1d2` documents the accounting convention: retain partially observed buckets, leave entirely absent buckets as gaps, and evaluate contiguous runs of at least 300 bars separately. Each segment restarts indicator evaluation. Each in-sample or OOS slice starts a fresh engine account and closes its final position with modeled costs; `_stitch` concatenates finite within-slice returns and compounds them. Missing calendar intervals and between-segment price moves do not enter that stitched return stream. Its bar-based Sharpe annualization is not adjusted for missing elapsed calendar time. Continuous buy-and-hold follows a different path and reset convention; the comparison is not matched for exposure or continuity.

That archived code predates the frontier run and supports interpretation of the metadata and design. The ledger does not pin an exact implementation revision, so publication review cannot certify that every retained frontier/tuning row used precisely that code. These are source-recorded, segment-conditioned historical results, not a continuously invested account that demonstrably survived data gaps or a reconstructed executable market path. The table’s segment counts cover the input evaluation, not separate counts of OOS segments. No return or selection row below is recomputed or promoted by adding this disclosure.

## 1. The 52% hit rate was never an edge

On SOL (90,316 recent 5m bars) RSI, Bollinger, z-score, CCI, stochastic and VWAP reversion call the next
bar right 51.3-51.9% of the time, and their average signed move is **-0.23 to +0.16 bps per call**. The
wins are smaller than the losses. That holds from the next bar's open as well as close-to-close, so it is
not a fill-timing artifact, and it holds at every holding period from 5 minutes to 4 hours. The best raw
number anywhere was liquidity_sweep held 1 hour: **+1.25 bps** against a **13 bps** round trip. No fee
trick turns zero gross into profit: the fees are not the problem, the missing gross edge is.

## 2. How a call can beat the fees

The historical cost scenario charges 13 bps per round trip on Hyperliquid (4.5 bps taker + 2 bps slippage, each side). A 5m bar moves
6-23 bps. The levers, in the order they matter here:

1. **Trade only the strongest readings.** `entry_quantile` (new) takes a call only when |composite| is in
   the top (1 - q) of its own trailing two weeks: q = 0.98 keeps the strongest 2%.
2. **Hold long enough for the move to dwarf the toll.** `hold` (new) keeps a position N bars after entry
   (only a blocking gate ends it early). One round trip then pays for an hour or a day of movement.
3. **Do not lever a long hold.** At 5x a 24-hour hold is mostly volatility drag: `htf_trend` top 2%
   held 24 h on SOL made **+20%** out-of-sample at 1x and **-53%** at 5x, same calls, same costs.
4. **Pay maker fees where the strategy allows it.** The study records a Hyperliquid maker fee of 1.5 bps (0 above
   $500M/14 days); taker 4.5. Resting limit orders fill only when price comes to you, which is adverse
   selection; the repo has never measured the fill rate, so no number here assumes maker fills.
5. **Lower configured friction.** The historical model used 13 bps for Hyperliquid versus 16 bps for Jupiter. These are assumptions, not current executable venue quotes.

Every Compound backtest row now carries **net bps 1h / 24h**: what each call earned held that long from
the next bar's open, after one round trip. That column is the direct answer to "can this metric pay its
fees if I hold it?".

## 3. The frontier sweep: every metric, strongest 2%, held 1 h / 4 h / 24 h, 1x

Out-of-sample = the last 30% of each coin's history. Medians across the ten coins.

| configuration (ten coins) | in-sample median Sharpe | OOS median Sharpe | OOS median return | OOS > 0 | beat buy & hold |
| --- | --- | --- | --- | --- | --- |
| RSI alone, every call, 5x (the old view) | -11.50 | -14.46 | -100.0% | 0/10 | 0/10 |
| Bollinger alone, every call, 5x | -14.00 | -17.85 | -100.0% | 0/10 | 0/10 |
| Compound, every call, 5x | -17.21 | -20.96 | -100.0% | 0/10 | 0/10 |
| htf_trend: top 2%, held 1 h, 1x | +0.03 | +0.57 | +15.5% | 8/10 | 7/10 |
| htf_trend: top 2%, held 4 h, 1x | +0.01 | +0.54 | +14.6% | 8/10 | 7/10 |
| htf_trend: top 2%, held 24 h, 1x | +0.11 | +0.49 | +9.3% | 6/10 | 5/10 |
| mom_skip: top 2%, held 1 h, 1x | -0.23 | -0.32 | -17.9% | 2/10 | 7/10 |
| mom_skip: top 2%, held 4 h, 1x | -0.12 | -0.40 | -19.1% | 1/10 | 5/10 |
| mom_skip: top 2%, held 24 h, 1x | +0.52 | -0.56 | -32.1% | 3/10 | 5/10 |
| rsi: top 2%, held 1 h, 1x | -1.36 | -3.20 | -93.3% | 0/10 | 1/10 |
| rsi: top 2%, held 4 h, 1x | -1.57 | -2.91 | -94.2% | 0/10 | 0/10 |
| rsi: top 2%, held 24 h, 1x | -1.08 | -2.26 | -93.3% | 0/10 | 0/10 |
| bollinger: top 2%, held 1 h, 1x | -4.24 | -5.96 | -99.8% | 0/10 | 0/10 |
| bollinger: top 2%, held 4 h, 1x | -2.73 | -3.79 | -98.9% | 0/10 | 0/10 |
| bollinger: top 2%, held 24 h, 1x | -2.31 | -2.97 | -97.7% | 0/10 | 0/10 |
| zscore: top 2%, held 1 h, 1x | -2.10 | -3.68 | -97.6% | 0/10 | 0/10 |
| zscore: top 2%, held 4 h, 1x | -1.97 | -3.00 | -97.3% | 0/10 | 0/10 |
| zscore: top 2%, held 24 h, 1x | -1.40 | -2.12 | -95.3% | 0/10 | 0/10 |
| cci: top 2%, held 1 h, 1x | -4.25 | -6.06 | -99.9% | 0/10 | 0/10 |
| cci: top 2%, held 4 h, 1x | -2.68 | -3.94 | -99.4% | 0/10 | 0/10 |
| cci: top 2%, held 24 h, 1x | -2.36 | -3.19 | -99.0% | 0/10 | 0/10 |
| vwap_reversion: top 2%, held 1 h, 1x | -2.69 | -3.53 | -98.2% | 0/10 | 0/10 |
| vwap_reversion: top 2%, held 4 h, 1x | -2.06 | -2.83 | -97.2% | 0/10 | 0/10 |
| vwap_reversion: top 2%, held 24 h, 1x | -1.80 | -2.42 | -93.7% | 0/10 | 1/10 |
| liquidity_sweep: top 2%, held 1 h, 1x | -5.62 | -8.73 | -100.0% | 0/10 | 0/10 |
| liquidity_sweep: top 2%, held 4 h, 1x | -2.84 | -4.25 | -99.3% | 0/10 | 0/10 |
| liquidity_sweep: top 2%, held 24 h, 1x | -2.33 | -3.42 | -98.3% | 0/10 | 0/10 |
| ou_reversion: top 2%, held 1 h, 1x | -2.15 | -2.72 | -88.7% | 0/10 | 0/10 |
| ou_reversion: top 2%, held 4 h, 1x | -1.51 | -2.17 | -85.9% | 1/10 | 0/10 |
| ou_reversion: top 2%, held 24 h, 1x | -1.09 | -1.62 | -84.7% | 0/10 | 1/10 |
| vr_regime: top 2%, held 1 h, 1x | -3.25 | -4.71 | -72.3% | 0/10 | 1/10 |
| vr_regime: top 2%, held 4 h, 1x | -2.42 | -3.59 | -68.0% | 0/10 | 1/10 |
| vr_regime: top 2%, held 24 h, 1x | -1.80 | -2.50 | -76.8% | 0/10 | 0/10 |
| pairs_spread: top 2%, held 1 h, 1x | -0.28 | -0.55 | -44.2% | 0/10 | 3/10 |
| pairs_spread: top 2%, held 4 h, 1x | -0.30 | -0.54 | -42.3% | 1/10 | 3/10 |
| pairs_spread: top 2%, held 24 h, 1x | -0.25 | -0.41 | -38.5% | 1/10 | 4/10 |
| keltner: top 2%, held 1 h, 1x | -5.08 | -6.37 | -99.5% | 0/10 | 0/10 |
| keltner: top 2%, held 4 h, 1x | -3.47 | -3.96 | -98.9% | 0/10 | 0/10 |
| keltner: top 2%, held 24 h, 1x | -2.68 | -2.52 | -97.0% | 0/10 | 0/10 |
| consec_run: top 2%, held 1 h, 1x | -4.19 | -7.01 | -99.0% | 0/10 | 0/10 |
| consec_run: top 2%, held 4 h, 1x | -2.60 | -3.58 | -98.2% | 0/10 | 0/10 |
| consec_run: top 2%, held 24 h, 1x | -1.78 | -2.39 | -97.2% | 0/10 | 0/10 |

Median buy-and-hold over the same out-of-sample windows: -22.0% (range -62% to +49%).

**What survived:** one metric family. `htf_trend` (the coin's 15-minute close against an EMA of 15-minute
closes, scaled by ATR) taking only its strongest 2% of readings, held 1-4 hours, unlevered, was profitable
out-of-sample on 8 of 10 coins and beat buying and holding on 7. **Read it with three caveats:**
its in-sample Sharpe was about zero (+0.01 to +0.11), so nothing in the training years pointed to it;
the out-of-sample stretch fell for most coins (median buy-and-hold -22%), a regime that may favor trend-following short exposure, without establishing a general effect; and 1,250 configurations were tried, so the best of
them would look good by luck alone.

**What did not:** every listed reversion-family configuration had a negative median return, but a few had one positive coin (for example OU held 4 h). RSI top 2% held 1 h had a median return of about -93%.
Selectivity and longer holds made them lose more slowly, not win. The six new research metrics
(`keltner`, `mom_skip`, `vr_regime`, `ou_reversion`, `consec_run`, `pairs_spread`) are in the scorecard,
off by default, and none earned a vote: `mom_skip` held 24 h had the best in-sample Sharpe (+0.52)
and lost out-of-sample (-0.56), the textbook overfit.

## 4. Training-only tuning after an exploratory frontier search

`research/frontier_tune.py` picked candidates by **in-sample** Sharpe only (positive on at least 5 of 10
coins), tuned each on in-sample only (hold 2-48 h x entry quantile 0.90-0.995 x first parameter x0.5/1/2),
then searched related strategies, and reported out-of-sample once. 1,227 configurations per coin in total
(frontier plus tuning plus related): that is the multiple-testing denominator.

| configuration | in-sample median Sharpe | OOS median Sharpe | OOS > 0 | beat buy & hold |
| --- | --- | --- | --- | --- |
| `htf_trend` top 2%, held 24 h (in-sample pick, untuned) | +0.11 | +0.49 | 6/10 | 5/10 |
| `htf_trend` tuned on in-sample: top 0.5%, held 48 h | +0.44 | +0.31 | 6/10 | 6/10 |
| `mom_skip` top 2%, held 24 h (best in-sample of all frontier rows) | +0.52 | -0.56 | 3/10 | 5/10 |
| `mom_skip` tuned on in-sample: top 2%, held 12 h | +0.64 | -0.61 | 2/10 | 5/10 |
| **`mom_skip` at htf_trend's tuned settings: top 0.5%, held 48 h** (best in-sample of the related set) | +0.60 | **+0.75** | **8/10** | 6/10 |
| blend `mom_skip` + `htf_trend`, top 2%, held 30 h | -0.01 | -0.10 | 1/10 | 4/10 |

**Tuning did not help.** The in-sample-best setting of `htf_trend` did worse out-of-sample (+0.31) than the
untuned one (+0.49), and tuning `mom_skip` made it worse too. That pattern is consistent with overfitting; this run does not identify its cause.

**The related search found one candidate worth watching**: momentum with a skip
(`log(C[t-6] / C[t-48])` scaled by volatility), taking only its strongest 0.5% of readings and holding
48 hours, unlevered. Out-of-sample per coin (return vs buy-and-hold, trades):

| coin | return | buy & hold | trades | max drawdown |
| --- | --- | --- | --- | --- |
| ETH | +188% | -8% | 118 | -27% |
| XRP | +81% | -46% | 84 | -22% |
| SOL | +61% | -36% | 98 | -25% |
| AVAX | +52% | -62% | 57 | -31% |
| NEAR | +41% | +49% | 69 | -49% |
| DOGE | +34% | -58% | 100 | -49% |
| SUI | +23% | -59% | 61 | -30% |
| BTC | +19% | +25% | 124 | -19% |
| HYPE | -23% | +31% | 13 (too few to rank) | -25% |
| LINK | -48% | -2% | 142 | -53% |

Why not to fund it yet: it was the best of about forty related configurations chosen on in-sample data,
after 1,227 configurations per coin; the out-of-sample years mostly fell, which favours a signal that can
go short; drawdowns of 20-53% at 1x; and it beat buy-and-hold on 6 of 10, not all. The honest next step
is a **forward paper test**: run it unattended on live closed bars and compare after a few hundred calls.

## 5. What to do with this

- Use the **Frontier** button (Compound 5m > Backtest) on any coin to repeat the sweep with fresh data.
- Read **net bps 1h / 24h** and **buy & hold** before believing a hit rate.
- Keep long holds unlevered; the illustrated SOL 24 h case lost at 5x despite gaining at 1x; this does not establish a universal leverage rule.
- Reversion metrics at 5m are not a strategy on these costs; the scorecard keeps them because the
  learned weights can still use them as one vote among many, not because they pay alone.

Reproduce: `python -m soltui.compound sweep --assets BTC,ETH,SOL,XRP,HYPE,DOGE,LINK,NEAR,SUI,AVAX --frontier
--workers 8`, then `python research/frontier_tune.py --run-id <that run> --top 3 --min-coins 5`.
