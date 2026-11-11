---
title: "How an archival SOL study chose its top five candidates"
description: "How an archival SOL study chose its top five candidates. An edited historical research report with its original evidence limits retained."
date: "2026-11-19"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

## Original study: Top 5 strategies — historical selection

> **Historical evidence.** This is an archival research report from August 2026, not a current performance claim or a recommendation to trade. Matching a saved output does not reproduce an experiment. The experiments were not rerun after later fixes to accounting, borrowing, metrics and selection. Results below retain the original study's assumptions and limitations.
>
> **Source availability.** References to `research/`, `backtester/` and result files identify the original research checkout. Those files and its market-data cache are not bundled with this article. Commands describe that historical environment; they are not a complete installation guide for a fresh checkout. Statements about tests passing describe the original study unless an explicit later check is identified.

**AS OF 2026-08-04.** Every figure below is read programmatically from
`research/results/cpcv_combos_results.csv`, `cpcv_results.csv` and the `perturb_long_*.csv`
files. Nothing is transcribed by hand.

> **Historical simulation for research and education only. NOT investment advice.** Simulated
> past performance does not predict future results. Read the two warnings below before the table;
> they matter more than the ranking.

## Warning 1 — ranking by backtest performance is the operation this dataset invalidates

PBO (probability of backtest overfitting) is **0.700** for singles at both daily horizons,
against a measured pure-noise line of 0.500. In this rank-based diagnostic, 0.700 means the selected in-sample winner fell below the out-of-sample candidate median in 70% of the tested splits. It is not a direct comparison of dollar profit with random trading. Spearman ρ(in-sample, out-of-sample Sharpe) is **−0.423** in the retained sweep
at the medium horizon: higher in-sample rank did not reliably identify higher out-of-sample rank in that population.

The diagnostic therefore warns against interpreting a Sharpe leaderboard as evidence of a durable edge.

## Warning 2 — the lowest PBO in the study points at the *least* profitable strategies

| Slice | PBO | best median return |
|---|---|---|
| short triples | **0.086** | +2.7% |
| short pairs | 0.229 | +2.8% |
| medium/long pairs | 0.650 | +68.9% / +75.1% |

PBO is low at the short horizon because rank is *stable* there — stably losing. The research doc
says it outright: 'in-sample rank generalises reliably as a loser.' Optimising for the best
overfitting statistic selects +2.7% strategies before funding and borrow costs. Do not do it.

## The author’s historical selection and its limits

The original author curated **seven named candidates** from the research outputs. That curated subset is not the universe with both CPCV and local perturbation evidence: the retained all-singles study covers **72 parameterized single/horizon configurations and 329 perturbations** (24 configurations per horizon, with 111 / 110 / 108 perturbations at short / medium / long). The broader retained CPCV population has **1,121 rows**.

The five below retain the author’s historical order. It is **not** an order reproduced by the printed check rule: row #4 fails median > IQR/2 while row #5 clears it. In addition, row #2 lacks perturbation evidence at its selected medium horizon.

Checks: median Sharpe > 0 · ≥70% of paths positive · median > IQR/2 · positive median return ·
≥10 trades · perturbation-tested with 0 sign flips.

| # | Configuration | Horizon | Median Sharpe | IQR | % paths + | Median ret | Trades | Perturbations | max abs Δ | Sign flips |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `all(dual_momentum+vol_regime)` | long | **+1.345** | 0.881 | 87% (of 15) | +75.1% | 52 | 12 | 0.441 | **0** |
| 2 | `any(hurst_switch+ou_reversion)` | medium | **+1.290** | 0.972 | 100% (of 15) | +68.9% | 40 | 12 (long only; unmatched) | 0.754 (long only) | **0 (long only)** |
| 3 | `any(ou_reversion+obv_trend)` | long | **+1.054** | 1.180 | 93% (of 15) | +93.6% | 90 | 8 | 0.446 | **0** |
| 4 | `obv_trend_60` | long | **+0.774** | 1.571 | 81% (of 21) | +44.6% | 98 | 2 | 0.199 | **0** |
| 5 | `vol_regime_60_0.5` | long | **+0.696** | 0.823 | 80% (of 15) | +36.1% | 54 | 6 | 0.364 | **0** |

**Perturbation binding correction:** row #2’s **12 perturbations, max abs Δ 0.754 and zero flips** belong to the **long-horizon** experiment with baseline median **+0.965** and IQR **1.049**, not the selected medium row (**+1.290**, IQR **0.972**). No matched medium-horizon perturbation output was found. Those historical values remain visible in the table but do not certify row #2.

Applying the six printed checks to the retained selected rows gives **6/6 for #1, 5/6 for #2 (matched perturbation evidence missing), 6/6 for #3, 5/6 for #4, and 6/6 for #5**. For #4, **0.774 < 1.571/2 = 0.7855**. No documented tie-break or exception explains the author’s order, so the order remains historical rather than a current recommendation.

**Path counts are 15 or 21, not 28.** C(8,2) is 28 nominally, but warm-up renders 2 blocks
unusable for these slow configurations (1 for `obv_trend_60`), so each percentage above is over
15 or 21 paths as marked — verified 2026-08-05 from `results/cpcv_top5_sol_doge_zec_1d.csv`,
whose `n_paths` column contains no value of 28. Four of these five rest on fifteen overlapping paths. These are not fifteen independent trials, and path fractions are descriptive rather than independent-trial confidence estimates.

**Benchmark that must stay in view:** `buy_and_hold`, zero parameters, medium/long median Sharpe
**+0.534**, 68% of paths positive, +9.4% median return. It ranked **2nd of 25** at the medium
horizon and 6th at long. Any strategy here that does not clearly beat it is not worth its
complexity, and holding the asset beat all but one medium-horizon single and all but five long-horizon singles in the 25-strategy set.

### Honourable mentions — also perturbation-tested, not in the five

- `any(adx_trend+ou_reversion)` (long) — median +1.162, 67% paths, 10 perturbations, max abs Δ 0.675, 0 flips. Its max abs Δ is below the retained long-horizon Hurst/OU experiment’s **0.754**, whose normalized ratio is **0.719**, versus **0.474** for ADX/OU. It is not the highest on either metric in that seven-experiment set.
- `all(macd+vol_regime)` (long) — median +0.991, 87% paths, 12 perturbations, max abs Δ 0.283, 0 flips.

## The mechanism-level finding, which outranks any individual row

`ou_reversion` and `vol_regime` are not five separate results. `ou_reversion` appears as the
partner in a majority of top combinations across every horizon, and `vol_regime` in the rest.
The transferable claim is **not** 'trade these five configurations' — it is:

1. **A slow mean-reversion signal (`ou_reversion`, 250-bar) is the most productive *partner*
   mechanism in this study.** It is what the top pairs have in common. **Qualified 2026-08-05:**
   its value is partner-dependent. `any(ou_reversion+obv_trend)` transferred to DOGE and ZEC;
   `any(hurst_switch+ou_reversion)` collapsed on DOGE (0 of 15 paths positive).
2. ~~**A volatility- or Hurst-based regime gate is the second.**~~ **DOWNGRADED 2026-08-05 —
   contradicted by the cross-asset test** (“Testing whether SOL findings transferred across assets” (forthcoming, planned 2026-11-20)). The two configurations
   containing `vol_regime` (#1 and #5) suffered the largest degradations off SOL, and
   `vol_regime_60_0.5` goes negative on **both** DOGE and ZEC. As a medium-horizon single,
   `vol_regime` is positive on only 3 of 5 assets and one of those is +0.019. **`obv_trend`
   replaces it as the transfer-supported second mechanism**: it is the only member appearing in
   both surviving configurations (#3, #4) and, as a single, is positive on all five assets with
   path fractions of 86% on DOGE (highest of the 25) and 90% on ZEC (third, behind `rsi` at 100%
   and `keltner` at 95%).
3. **The five selected long-horizon pair perturbation experiments have ~2.6× the median normalized sensitivity of the long-horizon singles population**: singles median ratio **0.171** versus selected pairs **0.44**. This describes those selected experiments, not every combination or the unmatched medium row #2.
   (Corrected 2026-08-05: the earlier phrasing paired that 2.6× multiple with the *pooled*
   singles median of 0.208 across all three horizons, which yields 2.1×, not 2.6×. Both numbers
   are real; the mismatched pairing was not.) The retained daily PBO comparison goes in the other direction: **pairs 0.650 versus singles 0.700**. It does not show that combining raised PBO, and neither the selected sensitivity comparison nor the PBO comparison establishes a general causal effect of combining.

## What this does not establish

- Perturbation stability measures local sensitivity around the selected settings. It does not prove the parameters were free of selection bias. It also cannot answer whether a configuration was selected advantageously from the candidate population; PBO 0.650 remains a warning about that selection step.
- One asset (SOL), one history. BTC and ETH runs already sank the last surviving moderate result;
  `cpcv_all25_btc_eth_1d.csv` is the record. **Answered 2026-08-05, and the answer is bad for
  this table:** all five configurations were re-run unchanged on DOGE and ZEC, and **all ten
  transfers degraded with none improving** (median −0.821 DOGE, −0.753 ZEC). Only **#3 and #4**
  stayed positive on all three assets — so the ordering 1–5 above should not be read as a
  preference ranking, because the two configurations at the top of it are among the worst
  transfers. On ZEC, zero-parameter `buy_and_hold` (+0.659) beat all five. Full write-up:
  “Testing whether SOL findings transferred across assets” (forthcoming, planned 2026-11-20); reproduce with
  `python3 research/cross_asset_cpcv.py --top5 --assets DOGE,ZEC`.
- For `all(dual_momentum+vol_regime)`, changing **CPCV geometry** from 8→9 blocks moved the median by **−0.441**, more than that pair’s largest reported ±10% parameter move (**−0.392**). This is a comparison for that pair, not a claim that geometry exceeds every strategy’s parameter sensitivity; the separate long-horizon Hurst/OU perturbation reaches **0.754**.
- As of the original report on 2026-08-04, the author stated that the project had placed no live orders. This is not a claim about subsequent project activity.
