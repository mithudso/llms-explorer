---
title: "What five-minute perpetuals research establishes"
description: "What five-minute perpetuals research establishes. An edited historical research report with its original evidence limits retained."
date: "2026-11-25"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# Five-minute SOL perps: what to test and what the evidence establishes

Historical evidence synthesis: **2026-11-08**. Cohort status and venue assumptions retain that review date. No profitable Jupiter rule or validated predictor ranking was established, and this publication did not run a new market experiment.

Reviewed: 2026-11-08. This is research, not a tested trading rule.

## Finding

This suite does not establish a profitable five-minute Jupiter SOL strategy or a validated
ranking of its predictors. The relevant target is **a sufficiently large favorable move
before the adverse path forces an exit, after execution costs**. A correct forecast of the
five-minute closing direction does not answer that question.

The following order is my proposed testing priority, not a measured performance ranking.
Freeze each definition before comparing it on a predeclared chronological period reserved for that procedure.

| Priority | Candidate features | What would justify accepting the signal |
| --- | --- | --- |
| 1 | Aggressor-signed trade flow, quote-event order-flow imbalance, distance-weighted depth and replenishment | Persistent agreement between executed flow and available liquidity, with measured incremental value after costs and latency |
| 2 | SOL cross-venue innovations, BTC/ETH reference moves and SOL residual returns | A lead still available at the actual decision and fill time, beyond a target-only baseline |
| 3 | Range compression followed by breakout, relative volume and signed flow | A predeclared boundary, enough expected net movement and a surviving adverse path |
| 4 | Liquidity sweep, failed continuation and reclaim | A separately validated reversal regime, rather than assuming every extreme must reverse |
| 5 | Trend pullback and VWAP/EMA reclaim with renewed signed flow | Incremental value beyond the trend, flow and volatility features already present |

Test RSI, MACD, stochastic and Bollinger features as simple baselines and conditional inputs.
Use feature-group ablations to establish whether each adds information. Treat volatility,
spread, depth, feed freshness and execution delay as admission inputs as well as possible
model features. No entry threshold or success probability in this table has been validated.

The preserved microstructure evidence has important scope limits: contemporaneous price
impact and next-price prediction do not establish five-minute SOL profitability. The new
cross-venue research likewise distinguishes historical leadership from an executable lead;
one SOL vendor study limits its conclusion to 10–700 milliseconds. A five-minute application
requires its own latency-aware test. [1, 2]

## Costs can consume an accurate forecast

Jupiter's documented JLP-market fee schedule specifies a 0.06% base fee and an upward-rounded
linear impact rate with a 0.01% minimum when opening or closing. Additive impact, borrow,
conditional swaps and network costs are separate. These published rules are not an executable
quote or a verified historical custody-state replay. [2, 3]

**Calculated illustration:** assuming unchanged notional on entry and exit, base plus minimum
linear fees total 0.14% of notional round trip. At 25x, 50x and 100x notional-to-posted-collateral
ratios, that equals respectively 3.5%, 7% and 14% of posted collateral, before the other costs.
Increasing leverage multiplies both proportional price P&L and proportional costs; it does not
reduce the underlying price movement needed to break even.

For a deliberately simplified binary trade with gross favorable return `G`, gross adverse
return `S` and fixed round-trip cost `c`, all as fractions of notional:

```text
expected net return = p*G - (1-p)*S - c
break-even win probability = (S+c)/(G+S)
```

At `G=0.20%`, `S=0.10%` and `c=0.14%`, an 80% win probability only breaks even. This is
arithmetic, not an observed win rate or a recommended trade. Timeouts, variable costs,
nonfills and liquidation need additional outcomes. Win rate alone cannot determine profit.

## Predict the path and allow abstention

Jupiter warns that a stop can fail to execute before liquidation. A liquidation-aware label
must use the venue's oracle path and changing liquidation boundary. When both target and
stop lie inside one candle, OHLC alone can leave their order unidentified. A stop-first
convention is a conservative assumption, not an observed sequence. [2, 4]

The experiment should therefore record three separate targets:

1. The distribution of the five-minute return from an achievable entry.
2. Whether target, stop, liquidation or expiry occurs first, including ambiguous paths.
3. The realized net outcome, including unsuccessful execution attempts and expiry prices.

Estimate maximum adverse excursion and tail losses alongside direction. Reject an entry when
the estimated adverse path does not fit its actual liquidation buffer, or when expected net
value does not clear costs and uncertainty. Numerical acceptance margins remain to be learned.

Evaluate calibration **within the accepted trades**, coverage and net payoff together. The
selective-prediction literature distinguishes calibration from useful abstention; tightening a
threshold does not automatically improve accepted-population calibration. Its general methods
do not provide a five-minute SOL survival guarantee. [2]

## What would establish a useful signal

Collect synchronized trades and depth, receive timestamps, sequence gaps, Jupiter oracle
observations, fee state and submission/fulfillment timestamps. Compare always-flat, simple
momentum and oscillator baselines with the proposed feature groups. Use chronological
walk-forward selection, overlap-aware separation and an untouched final period. Record every
configuration tried. Measure coverage, conditional net expectancy, uncertainty, drawdown,
liquidation frequency and sensitivity to worse execution.

The repository's historical `oracle_net_bps` statistic averages absolute close-to-close log
returns across all time-selected transitions and subtracts fixed friction. It ignores call
coverage and intrabar liquidation paths. A negative unconditional average does not rule out
every selective policy; a positive one does not establish an executable strategy. The exact
code review and synthetic counterexample are in `five-minute-perps-suite/benchmark-scope-review.json`.
No new market backtest or live trade was performed for this synthesis.

## Evidence and continuation

- [1] Preserved prior research: `five-minute-perps-suite/inherited-evidence-receipt.json`;
  47 unchanged supported assertions with 114 checked evidence spans. This is inherited
  coverage, not a newly completed research pass.
- [2] Cohort as of 2026-11-08: `five-minute-perps-suite/accepted-gate-receipt.json`;
  research-gate/v4 accepted all 165 assertions: 125 supported factual assertions and
  40 non-assertions, including questions. The three conflicts retain explicit attribution.
  Raw snapshots and gate transcripts remain private.
- [3] Jupiter JLP fees:
  https://docs.jup.ag/user-docs/trade/perps/fees.md
- [4] Jupiter liquidation:
  https://docs.jup.ag/user-docs/trade/perps/liquidation.md
- Run completion, artifact quality, remaining gaps and delivery are recorded in
  `five-minute-perps-suite/run-report.md`. The evidence gate alone does not establish
  full-suite saturation, installation, indexing or publication completion.
