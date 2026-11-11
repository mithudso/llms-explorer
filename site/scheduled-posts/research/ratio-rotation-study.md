---
title: "A historical test of ratio rotation"
description: "A historical test of ratio rotation. An edited historical research report with its original evidence limits retained."
date: "2026-11-22"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

## Original study: Ratio rotation: buying the discount, measured

> **Historical evidence.** This is an archival research report from August 2026, not a current performance claim or a recommendation to trade. Matching a saved output does not reproduce an experiment. The experiments were not rerun after later fixes to accounting, borrowing, metrics and selection. Results below retain the original study's assumptions and limitations.
>
> **Source availability.** References to `research/`, `backtester/` and result files identify the original research checkout. Those files and its market-data cache are not bundled with this article. Commands describe that historical environment; they are not a complete installation guide for a fresh checkout. Statements about tests passing describe the original study unless an explicit later check is identified.

Reproduce with:

```bash
# Step zero: data/ is gitignored and regenerable, so a clean checkout has none.
python3 -m backtester.core.universe --assets BTC,ETH,SOL,DOGE,ZEC --interval 1d
# For the 6-coin panel, XRP has a known 30-month hole and needs the flag stated:
python3 -m backtester.core.universe --assets XRP --interval 1d --allow-gaps

python3 research/ratio_rotation.py --self-test        # 23 checks
python3 research/ratio_rotation.py --universes        # why the panel is 5 coins
python3 research/ratio_rotation.py --turnover-table   # the cost arithmetic
python3 research/ratio_rotation.py --demo-chain       # chained vs direct routing
python3 research/ratio_rotation.py --sweep --out rotation_5coin_1d.csv
python3 research/ratio_rotation.py --carry            # borrow-fee sensitivity
```

The fetch commands create the market-data cache. The synthetic `--self-test` and closed-form `--turnover-table` do **not** require that cache. `--universes` inspects available cached series, while `--demo-chain`, `--sweep` and `--carry` load the panel. If required panel data are missing, `load_panel` raises with the exact refetch line rather than proceeding on a partial panel.

## The question

Find a discounted pair, buy the discount, then spend the proceeds on the next
discounted pair: ETH/BTC looks cheap so buy ETH, then SOL/ETH looks cheap so buy
SOL with that ETH, and so on around the board.

Three claims are bundled together in that sentence. They are separated here
because they have three different answers.

| Claim | Verdict |
|---|---|
| Chaining hops compounds the discount | **False by arithmetic.** Costs one extra fee leg per hop and nothing else |
| Buying the relatively cheap coin beats holding | **False on this data.** All 36 reversion configurations had negative out-of-sample Sharpe |
| The inverse (buy relative strength) beats holding | **Not demonstrated.** Positive, but fails Deflated Sharpe and loses to holding ZEC |

## 1. The chain is an extra fee leg and nothing else

All series here are USD-quoted, so every cross rate is a quotient of two USD
closes and the triangle closes identically:

```
(ETH/BTC) x (SOL/ETH) = SOL/BTC        exactly, to floating point
```

`--demo-chain`, on the final bar of the panel, starting from 1 BTC:

| Route | Legs | SOL gross | SOL net | Cost |
|---|---|---|---|---|
| BTC->ETH->SOL (chained) | 2 | 864.56367573 | 863.18092717 | 15.99 bps |
| BTC->SOL (direct) | 1 | 864.56367573 | 863.87202479 | 8.00 bps |

The gross column is identical to the last digit. Routing through ETH bought
nothing and paid twice. **There is no such thing as compounding a discount across
hops** when the cross rates are internally consistent, and USD-derived cross rates
always are. What remains of the idea is not a chain but a *selection*: at each
rebalance, which single asset do I want to hold. That is what the rest of this
document measures.

The genuinely different strategy — separately quoted cross pairs whose product
departs from one — is triangular arbitrage. `backtester/guides/triangular_arbitrage.md`
already covers it and explains why this project's data cannot evaluate it. Nothing
here bears on that card's subject.

## 2. "All coins" costs 85% of the history

Rotation differs from the per-asset sweeps in a way that decides the universe: it
needs **every** asset present at bar `t` to rank them. It cannot run each coin on
its own window. So the study length is set by the shortest member.

| Universe | Bars | From |
|---|---|---|
| BTC+ETH+SOL+DOGE+ZEC | **1,875** | 2021-06-17 |
| +XRP | 1,119 | 2023-07-13 |
| +BNB | 287 | 2025-10-22 |
| +HYPE | 181 | 2026-02-05 |

The 8-asset intersection is 181 bars. BNB and HYPE are excluded on that number
alone, not on any judgement about the assets. TRX was excluded as unavailable on the study’s Coinbase data surface at the time
(`backtester/core/universe.py`). The 5-coin panel is primary and the 6-coin panel
is reported separately, because a result appearing in only one of them is a result
about the window rather than about breadth.

## 3. Cost sets the holding period before any search runs

A rotation moves 2.0 of weight and pays two one-way legs: 16 bps at `CostConfig`
defaults (6 bps fee + 2 bps slippage).

| Avg hold (bars) | Rotations/yr | Annual drag |
|---|---|---|
| 1 | 365 | 44.3% |
| 3 | 122 | 17.7% |
| 5 | 73 | 11.0% |
| 10 | 36.5 | 5.7% |
| 30 | 12.2 | 1.9% |
| 90 | 4.1 | 0.7% |

This is arithmetic about the cost model that no parameter search can argue with,
and it is why lookbacks below 20 daily bars are not searched. Not searching them
is not a favour to the strategy — it lowers the trial count the Deflated Sharpe
has to correct for, which is the mechanism that let `trend` survive in
“Nine coins, seven strategies, ~2,400 configs — and one survivor that still loses” (`SWEEP-9COIN.md`, unavailable historical reference; original outputs not retained) ("it passed by searching less").

## 4. The premise is inverted: buying the discount reliably lost

The original long-only panel uses 72 configurations (6 windows x 2 top-k x 2 directions x 3 hysteresis margins),
walk-forward 70/30, all 72 clearing `MIN_OOS_ROTATIONS=10`.

Out-of-sample Sharpe by direction:

| Direction | Median | Best | Worst |
|---|---|---|---|
| `momentum` (buy relative strength) | **+1.042** | +1.771 | +0.762 |
| `reversion` (buy the discount) | **-0.399** | **-0.061** | -0.838 |

**The best of all 36 reversion configurations still has a negative
out-of-sample Sharpe.** The retained original long-only CSV also shows **negative compounded out-of-sample monthly return for all 36**. This model calculates Sharpe on net simple returns with zero risk-free rate. The 6-coin panel repeats the author-reported Sharpe pattern:
reversion median -0.751, momentum median +1.421.

This is the clearest result in the study, and it runs directly against the
premise. On this universe and window, the coin that is cheap against its peers
kept getting cheaper. The two directions are the same machine with one sign
flipped, so this is not a claim that the machine works — it is a claim about which
sign of it does not.

## 5. The momentum side does not survive its controls either

Best row: `window=30, top_k=1, momentum, margin=0.0` — out-of-sample Sharpe
**1.771**, +12.93%/month, 113 rotations, max drawdown -61.8%.

That number is meaningless without the same slice's controls, and getting this
wrong was a real bug in the first run of this module: strategy rows were ranked on
the last 30% while controls were printed over all 1,875 bars, making the strategy
look far better than a matched comparison allows. Corrected, on the **identical
563-bar out-of-sample slice**:

| | Monthly | Sharpe | Max DD |
|---|---|---|---|
| **Best strategy row** | **+12.93%** | **1.771** | -61.8% |
| `hold_ZEC` | **+13.71%** | 1.765 | -71.8% |
| `equal_weight` | -0.35% | 0.273 | -50.7% |
| `random_p90` (n=50, matched turnover) | +1.93% | 0.686 | — |
| `random_p50` (n=50, matched turnover) | -1.62% | 0.215 | — |
| `hold_BTC` | -2.46% | -0.469 | -53.1% |
| `hold_ETH` | -2.89% | -0.147 | -67.6% |
| `hold_SOL` | -6.42% | -0.650 | -75.8% |
| `hold_DOGE` | -8.44% | -0.844 | -81.4% |

**The strategy lost to simply holding ZEC** — 12.93%/month against 13.71%/month,
with 113 rotations and numerically close Sharpe values (1.771 vs 1.765). No uncertainty interval or test of their difference was supplied.

The allocation record helps explain the result descriptively:

| Asset | Share of invested bars |
|---|---|
| ZEC | 34.3% |
| ETH | 22.4% |
| BTC | 21.5% |
| SOL | 13.3% |
| DOGE | 8.5% |

ZEC returned **+979%** on this slice; every other coin lost 37-80%. The rule put
34% of its time in ZEC against a 20% equal-weight baseline — a real 1.7x tilt, and
the honest positive finding of the study — then diluted it with 66% in assets that
were falling, netting out *below* the single asset it had partially identified.

## 6. It fails Deflated Sharpe on both universes

| | 5-coin | 6-coin |
|---|---|---|
| Configurations | 72 | 72 |
| Best OOS Sharpe (annual) | 1.771 | 2.029 |
| Per-observation Sharpe | 0.0927 | 0.1062 |
| Expected max of N trials | **0.1058** | **0.1467** |
| Deflated Sharpe | 0.379 | 0.230 |
| Survives | **No** | **No** |

In both cases the best row's Sharpe is **below** the expected maximum of that many
trials under the archived Deflated Sharpe assumptions. The search failed that adjusted evidence screen; this is not a literal coin-flip experiment or proof that no possible edge exists.

One dissenting number, reported rather than buried: CSCV puts **PBO = 0.0**, which
indicates stable ranking under that diagnostic, not the absence of every form of overfitting. It should not be read as independent evidence of profitability here. PBO
measures whether in-sample rank predicts out-of-sample rank, and when 36 of the 72
configurations are near-clones that move together, stable rank can arise without a profitable edge. That is a possible explanation, not an isolated causal test. “Nine coins, seven strategies, ~2,400 configs — and one survivor that still loses” (`SWEEP-9COIN.md`, unavailable historical reference; original outputs not retained) recorded the same shape — DSR and the other
diagnostics ask different questions and neither implies the other.

In the retained **72-row original long-only panel**, **28 rows** have negative `decay_sharpe`, meaning their out-of-sample Sharpe exceeds in-sample. All **28 are momentum rows** (28 of 36); **none of the 36 reversion rows** has negative decay. The original “every row” statement was incorrect. A favorable late-window regime for those momentum rows is one hypothesis—one coin ran 10x while the rest fell—not an isolated explanation or evidence about all configurations. Later neutral-book rows are excluded from this original-panel count.

## 7. Leverage: a cost curve, not a carry trade

`--carry`, best config, out-of-sample slice:

| Leverage | Monthly | Max DD | Ruined | Naive scaled monthly |
|---|---|---|---|---|
| 1x | +12.93% | -61.8% | no | +12.93% |
| 2x | +2.29% | -94.8% | no | +25.86% |
| 3x | -12.68% | -99.8% | no | +38.78% |
| 5x | -100.00% | -100.0% | **yes** | +64.64% |

The gap between the first and last columns is the cost of the money. 2x leverage
turns +12.93%/month into +2.29%; 3x turns it negative; 5x is a total loss. This
matches [the leveraged perpetuals economics study](/blog/research/leveraged-perpetuals-economics/): at these borrow rates the financing dominates
everything.

Sharpe is deliberately omitted from that table's reading. If the same fully costed return series scales linearly by positive leverage, with no liquidation or ruin barrier, mean and standard deviation scale together and **Sharpe is invariant by arithmetic**. Actual liquidation and nonlinear costs can violate those conditions. A near-constant Sharpe in this model is therefore insufficient to assess leverage risk. `monthly_pct` and `max_drawdown` are the
informative columns. This is asserted in the self-test, as a check of that model’s linear-scaling assumptions, not as a general law of leveraged trading.

### What was NOT measured, and why

The user asked about funding/basis carry. **This study cannot answer that**, and
the distinction matters more than it looks:

- `backtester/core/perps.py` models a **borrow fee** — both sides pay it, and it
  is floored at zero.
- A **funding rate** changes sign with the long/short imbalance, and *receiving*
  it when it is negative is the entire carry trade.

No funding-rate history is cached in this repository, so the sign-flipping series
that a carry strategy harvests does not exist here. Modelling it as a borrow fee
would answer a different question while appearing to answer this one.

**Data that would make it evaluable** (in the spirit of `triangular_arbitrage.md`):
per-interval realised funding rates per venue and per pair, timestamped to the
funding interval rather than the bar; open-interest imbalance, since that is what
drives the sign; and the venue's actual fee tier. With those, the testable claim is
whether a cross-sectional long-negative-funding / short-positive-funding book earns
its costs — a genuinely different strategy from anything measured above.

## Verdict

| Component | Status |
|---|---|
| Chained routing | Refuted by arithmetic; costs one extra leg per hop |
| Buy-the-discount rotation | **Measured, reliably negative** — best of 36 configs is Sharpe -0.061 |
| Buy-the-strength rotation | Positive but fails DSR on both universes and loses to holding ZEC |
| Funding-basis carry | **Not evaluable** — data absent |

The strategy family is not recommended. The single defensible positive is the 1.7x
ZEC tilt, and it was not large enough to overcome holding ZEC outright.

## Caveats

- **One window, one venue.** 2021-06-17..2026-08-04, Coinbase USD closes, daily
  bars. The out-of-sample slice contains one dominant idiosyncratic move (ZEC
  +979%), and a single asset driving the result is exactly the condition under
  which conclusions do not generalise.
- **Timing convention.** Weights at `t` are computed from closes through `t`,
  charged turnover at `t`, and earn bar `t+1` — i.e. execution at the close just
  observed. `--fill-delay` adds bars of lag as a robustness check.
- **No shorting.** Long-only, fully invested when not in warm-up. The reversion
  result being uniformly negative implies the short side is worth testing, and it
  was not.
- **Parameters are not refit per universe**, following `cross_asset_cpcv.py`'s
  reasoning: the 6-coin panel uses the same grid, so a difference between panels is
  evidence about the window, not about the assets.
- **The cross-rate identity check in `--self-test` is not evidence.** It is a
  quote-convention guard that is true by construction on USD-quoted series, and it
  fails only when a leg has been inverted.
