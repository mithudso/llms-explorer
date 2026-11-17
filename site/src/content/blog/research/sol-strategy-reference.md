---
title: "An archival reference for SOL strategies and signals"
description: "An archival reference for SOL strategies and signals. An edited historical research report with its original evidence limits retained."
date: "2026-11-17"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

## Original study: SOL Trading Strategy & Signal Reference

> **Historical evidence.** This is an archival research report from August 2026, not a current performance claim or a recommendation to trade. Matching a saved output does not reproduce an experiment. The experiments were not rerun after later fixes to accounting, borrowing, metrics and selection. Results below retain the original study's assumptions and limitations.
>
> **Source availability.** References to `research/`, `backtester/` and result files identify the original research checkout. Those files and its market-data cache are not bundled with this article. Commands describe that historical environment; they are not a complete installation guide for a fresh checkout. Statements about tests passing describe the original study unless an explicit later check is identified.

> **Historical simulation for research and education only. NOT investment advice**, and not a
> recommendation to trade anything. Simulated past performance does not predict future results.
> Performance figures below are archived outputs attributed to the original author’s runs, not newly reproduced results. `SPEC-ONLY` marks mechanisms that were not run at that stage. It does not assert that every literature estimate or methodological statement was independently verified.

**Companion document:** “Historical SOL strategy rankings and robustness checks” (forthcoming, planned 2026-11-18) holds the three ranked lists.
**Original specification:** `PROMPT_STRATEGIES.md` in the source checkout; it is not bundled with this article.

---

## Method note (read first)

The request asked for a `/dr` deep-research pass. Subagent fan-out is unavailable in this
environment, so this is grounded in the **local citation-backed corpus** —
a private trading-reference collection, reported as ~620 KB across 14 references covering
technical analysis, trading styles, algorithmic/quant methods, ML-for-trading pitfalls, crypto
and DeFi venues — plus **first-hand measurement** on real SOL data. That substitution is
deliberate and stated rather than made silently. Literature claims are attributed to their
source. Literature estimates in mechanism cards are historical reference claims, not new measurements or independently verified guarantees. The dated corpus may not reflect current venue or market conditions.

**Scope is bounded deliberately.** "Every known trading strategy" is unbounded — the great
majority of named strategies are parameter permutations of a few dozen mechanisms. This
document covers **42 distinct mechanisms** across ten families (16 measured + 26 spec-only),
treating each family's mechanism once and naming variants inline rather than giving each its
own entry.

### The headline empirical result

Evaluation uses **combinatorial purged cross-validation** (8 blocks, k=2, 28 nominal paths, usually 15 or 21 usable paths after warm-up). The later phase covered **25 registered strategies**, the original 16 plus nine implemented from the earlier spec-only cards. The retained outputs contain **1,121 configurations**:

- **PBO is 0.343 / 0.700 / 0.700** (short / medium / long). Calibrated against constructed
  controls in the test suite, **pure noise gives 0.500 and a genuinely ordered signal set gives
  0.000** — so at the daily horizons in-sample rank is *anti*-informative.
- **At the short horizon not one of the 25 has a positive median path Sharpe.** The best,
  `stoch_14_3` at −0.341, still loses.
- Growing the search 16 → 25 raised PBO by **+0.100 (medium) and +0.150 (long)** once the
  coincident block-set change is held fixed. Candidate count and candidate composition both changed, so this is not an isolated causal estimate of search-size effects. Full decomposition in “Historical SOL strategy rankings and robustness checks” (forthcoming, planned 2026-11-18).
- Best rows now: `hurst_switch` (medium, +0.699, 93% of paths positive), `obv_trend_60` (long,
  +0.774, 81%), `vol_regime` (long, +0.696, 80%). All three were spec-only or untested before.
- The highest median Sharpe in the retained pair tables — `all(dual_momentum+vol_regime)`, long, **+1.345** on
  **+75.1%** — sits atop a 252-evaluable-configuration search with PBO 0.650, so it is precisely the row not
  to trust.

Under the earlier single split: 953 configurations, 595 rankable, **73 (12%) with a positive
out-of-sample Sharpe and 47 (8%) that made money**, with in-sample rank *inverted* against
out-of-sample at the medium horizon (Spearman **−0.423**). One relevant confound is that the **highest close
in the entire series (\$261.99) is bar 1311 — the final in-sample bar**, so the split separates
the bull market from the bear leg to within a single bar. Full tables and the method contrast in
“Historical SOL strategy rankings and robustness checks” (forthcoming, planned 2026-11-18).

**Consequence for reading this document:** each entry's `Measured` block quotes single-split
figures, which are evidence about *one regime transition*. Prefer the CPCV distribution in
“Historical SOL strategy rankings and robustness checks” (forthcoming, planned 2026-11-18) List 1 when deciding anything.

### Horizon definitions

| Horizon | Bars | Signal scale | Typical hold | Data |
|---|---|---|---|---|
| **Short** | 1h | fast (e.g. 12/48) | hours to ~3 days | `data/SOL_1h.csv`, 8,823 bars, 2025-08-01→2026-08-04, **2 disclosed gaps (largest 6h)** |
| **Medium** | 1d | medium (20/50) | ~1–8 weeks | `data/SOL_1d.csv`, 1,875 bars, 2021-06-17→2026-08-04, clean |
| **Long** | 1d | slow (50/200) | ~3–12 months | same daily file, slow parameters |

### Universal backtest requirements

These apply to every entry below and are enforced by the harness (`backtester/`), not left to
the strategy author:

- **Signal at bar *t* reads only data ≤ *t*; the fill happens at bar *t+1*'s open.** Enforced
  structurally: strategies receive a `BarWindow` whose accessors return `arr[:i+1]`, through the documented accessors. This limits ordinary strategy access but is not a security sandbox for arbitrary Python or NumPy code. The original test suite includes a deliberately cheating strategy that is expected to raise.
- **Rolling statistics use trailing windows only.** Never full-sample normalisation — the most
  common form of look-ahead (Type 1 in the local corpus's four-mechanism taxonomy).
- **Costs on the fill:** 6bps taker fee + 2bps slippage on notional, at the executed price.
- **Warm-up produces no trades.** The first tradeable bar is the first at which every indicator
  is fully defined.
- **70/30 walk-forward**, with the out-of-sample slice starting `warmup` bars early so
  indicators warm from trailing in-sample bars (reading earlier history is not look-ahead;
  starting cold would discard real out-of-sample data).
- **Evidence floor:** fewer than 10 out-of-sample trades ⇒ listed, never ranked.

### Data available vs not

**Available:** OHLCV at 1h and 1d for SOL-USD (Coinbase, keyless). **Not available, so any
mechanism needing it is `SPEC-ONLY` with the gap named:** order-book/L2 depth, trade prints,
funding-rate or borrow-rate history, on-chain flows (DEX volume, active addresses, staking),
a cross-sectional peer universe, options-implied volatility, social sentiment.

---

## TIER 1 — MEASURED (16 mechanisms)

Implemented in `backtester/core/strategies/`, registered, executed. Real output attached.
Symbols: `C` = close series, `H`/`L` = high/low, `V` = volume, `n` = window length,
`c_t` = close at bar *t*.

---

The measured cards and their comparative labels below preserve the **original 16-mechanism stage**. “Best”, “top” and counts such as “eight positive pairs” in those older cards refer to that stage or an explicitly retired pairing, not the later 25-strategy population summarized above. The later retained population has 15 positive rankable medium-horizon pairs. The “Works when”, “Fails when” and “Pairs with” fields below are mechanism hypotheses and historical reference guidance. They do not establish profitability, causal independence, or an optimal combination. Literature percentages are the original collection’s attributed estimates unless an archived result file is named.

## 1. Buy & Hold — `baseline` · MEASURED

**What it is.** Fully invested from the first tradeable bar, forever.
**Looks for.** Nothing. It is the null hypothesis every other row must beat.

**Equation.**
```
target_exposure_t = 1.0            for all t
```

**Data.** Close only. Any interval. 2 bars minimum. **Available.**
**Deps.** None. **Warm-up.** 0 bars.

**Works when.** The asset appreciates over the holding period. Structurally unbeatable on
return (though not on drawdown) in a monotonic bull market.
**Fails when.** Any sustained drawdown — it has no exit. Measured max drawdown on full-sample
SOL daily: **−96.27%**.

**Backtest notes.** This is the harness's known-answer test: with zero costs and `fill_delay=0`,
total return must equal `last_close/first_close − 1` exactly. If that identity breaks, the
accounting is wrong and no other row in this document means anything.
**Pairs with.** Nothing — it is the baseline. Any strategy that cannot beat it is a
cost-generating machine.

**Implementation.** `core/strategies/buy_and_hold.py`.
**Measured.** Full-sample daily: **+87.61%**, Sharpe 0.617, maxDD −96.27%, 1 trade.
Walk-forward: **IS +565.2% (Sharpe 1.030) → OOS −70.8% (Sharpe −0.651)**.

---

## 2. Moving-Average Crossover — `trend` · MEASURED

**What it is.** Long while a fast simple moving average sits above a slow one.
**Looks for.** Persistent directional drift — the premise that trends continue.

**Equation.**
```
SMA(n)_t = (1/n) * sum_{k=0}^{n-1} c_{t-k}
target_t = 1  if SMA(f)_t > SMA(s)_t   else 0        (f < s)
```

**Data.** Close only. 1h or 1d. Minimum `s` bars. **Available.**
**Deps.** None. **Warm-up.** `s` bars (50 medium / 200 long).

**Works when.** Trends persist longer than the slow window. Best in low-noise, high-autocorrelation regimes.
**Fails when.** Range-bound chop — every oscillation produces a whipsaw pair of fills. Cost
scales with crossover frequency, so the fast/slow ratio is a cost decision as much as a signal one.
It is also structurally **late**: confirmation requires the averages to already have crossed.

**Backtest notes.** Whipsaw sensitivity means results are highly parameter-dependent; report the
parameter scale, not just "MA crossover". The `--rebalance-threshold` deadband matters here.
**Pairs with.** Volume confirmation (`obv_trend`) to filter unparticipated drifts; a
regime filter to suppress counter-trend entries; breakout for earlier entry.

**Implementation.** `core/strategies/ma_crossover.py`.
**Measured.** **Best short-horizon single: OOS Sharpe +0.488** (IS −2.490), +3.4% on 29 trades.
Medium (20/50): IS +735.6% → **OOS −52.3%**, 7 OOS trades (below evidence floor).

---

## 3. MACD — `trend` · MEASURED

**What it is.** Momentum of the gap between two EMAs, against its own EMA.
**Looks for.** Acceleration in trend, earlier than a raw MA cross.

**Equation.**
```
EMA(s)_t   = a*c_t + (1-a)*EMA(s)_{t-1},   a = 2/(s+1)
MACD_t     = EMA(fast)_t - EMA(slow)_t
Signal_t   = EMA(sig) applied to the MACD series
Hist_t     = MACD_t - Signal_t
target_t   = 1 if MACD_t > Signal_t else 0
```

**Data.** Close only. **Available.** **Deps.** EMA recursion; the signal line is an EMA *of the
MACD line*, so a short history of MACD values is needed (see `indicators.ema_series`).
**Warm-up.** `slow + 3*sig` bars.

**Works when.** Directional moves with steady acceleration.
**Fails when.** Choppy conditions produce constant sign flips. **This is the worst measured row
in the entire sweep at the short horizon** — `macd_6_13_5` scored **OOS Sharpe −4.621** across
205 trades under fast-parameter whipsaw and 8 bps per fill, or 16 bps for an unchanged-notional round trip.

**Backtest notes.** Naïvely recomputing the MACD history each bar is O(signal·cap · slow·cap) and
dominated total sweep runtime; the single-pass `ema_series` reduces it to O(cap·slow + count).
Worth knowing if you extend this.
**Pairs with.** An oscillator brake (`stochastic`) to stop it adding into exhausted moves —
measured as one of only eight positive medium-horizon pairs.

**Implementation.** `core/strategies/signals.py::MacdCross`.
**Measured.** Medium (12/26/9): **IS +1,356.5% (Sharpe 1.347) → OOS −52.8% (Sharpe −0.720)**,
21 OOS trades. One of the starkest decay rows in the sweep.

---

## 4. Time-Series Momentum — `momentum` · MEASURED

**What it is.** Long when the trailing *n*-bar return is positive.
**Looks for.** The sign of past return predicting the next period — the Moskowitz/Ooi/Pedersen
time-series form, distinct from cross-sectional momentum (which needs a peer universe).

**Equation.**
```
ROC(n)_t = c_t / c_{t-n} - 1
target_t = 1 if ROC(n)_t > threshold  else 0        (threshold default 0)
```

**Data.** Close only. **Available.** **Deps.** None. **Warm-up.** `n+1` bars.

**Mechanism hypothesis.** Persistent returns can support momentum rules. The source cites Jegadeesh & Titman (1993), an equity cross-sectional momentum study; it does not establish that this single-asset rule or its holding period inherits those results.
**Fails when.** **Momentum crashes** — the corpus documents these as the family's defining risk:
sharp reversals that hit hardest exactly when the signal is most crowded. A single-asset version
has no cross-sectional diversification to soften that.

**Backtest notes.** Highly sensitive to the formation window; 24 bars hourly and 60/200 daily
behave like different strategies. Do not tune the window on the same data you report.
**Pairs with.** A breakout for entry timing; an oscillator to avoid adding at exhaustion.

**Implementation.** `core/strategies/signals.py::TsMomentum`.
**Measured.** Long (200): **IS +506.2% (Sharpe 1.098) → OOS −77.2% (Sharpe −1.976)** — the
worst rankable long-horizon row. Medium (60): IS +392.8% → OOS −51.1%.

---

## 5. Slow-MA Regime Filter — `regime-filter` · MEASURED

**What it is.** Fully long above a slow moving average, flat below it.
**Looks for.** A one-line answer to "is this a bull or bear regime".

**Equation.**
```
target_t = 1 if c_t > SMA(n)_t  else 0              (n = 100 or 200)
```

**Data.** Close only. **Available.** **Deps.** None. **Warm-up.** `n` bars.

**Works when.** Regimes are persistent. Its value is less in returns than in *avoiding* the
worst drawdowns — the most-cited overlay for that purpose.
**Fails when.** Price oscillates around the average, producing repeated entries and exits at
the worst possible points. Also late by construction at regime turns.

**Backtest notes.** This is the strategy every more elaborate signal should be measured
against: if an eight-parameter system cannot beat "price above its 200-day average", the extra
parameters are not earning their keep.
**Pairs with.** **This is the single most valuable partner in the whole set.** Mean-reversion's
fatal mode is buying dips inside a downtrend, and the regime filter is the only component here
that answers "is there a downtrend". Measured as the top short-horizon pair and top triple.

**Implementation.** `core/strategies/signals.py::Sma200Regime`.
**Measured.** Standalone medium (100): IS +34.8% → **OOS −35.8%**, 13 OOS trades.
**As a partner** it is transformative: `all(sma_regime+bb_reversion)` reached **OOS Sharpe
+2.572** (short) versus +0.086 for `bb_reversion` alone. The `zscore` twin of that pair scored
identically and is no longer built — the two measure 0.96–1.00 correlated and now share one
redundancy class.

---

## 6. Donchian Channel Breakout — `breakout` · MEASURED

**What it is.** Long on a new *n*-bar high; flat on an *m*-bar low. The Turtle mechanism.
**Looks for.** Range expansion — the start of a new trend leg.

**Equation.**
```
Upper_t = max(H_{t-n} .. H_{t-1})       # EXCLUDES the current bar
Lower_t = min(L_{t-m} .. L_{t-1})
enter if c_t > Upper_t ;  exit if c_t < Lower_t
```

**Data.** High, Low, Close. **Available.** **Deps.** None. **Warm-up.** `max(n,m)+1` bars.

**Works when.** Volatility expands out of contraction, and the trend that follows runs far
enough to pay for the false starts.
**Fails when.** False breakouts dominate. The Turtles' documented win rate was **30–35%** — the
profile depends entirely on a few large winners, so **missing a handful of big moves per year
ruins the year**. That makes short backtest windows especially unreliable for this family.

**Backtest notes.** The channel **must exclude the current bar** — including the current high
makes the comparison nearly always false and silently guts the strategy. Corpus-documented
false-breakout filters worth testing: require two consecutive closes beyond the level; require
the breakout candle body to exceed 70% of its range; require above-average volume.
**Pairs with.** Volume (a genuine breakout shows participation); a volatility-squeeze filter;
a reversion rule for the exit that a pure breakout rule handles poorly.

**Implementation.** `core/strategies/breakout.py`.
**Measured.** Full-sample medium: +620.7%, Sharpe 0.935. Walk-forward: **IS +860.2%
(Sharpe 1.265) → OOS −7.5%**, only 7 OOS trades — **below the evidence floor**, which is
exactly the low-trade-count problem the Turtle profile predicts.
`any(breakout+zscore)` was the best measured medium pair at **+0.584** out-of-sample on +30.8%, but it
is no longer built: `zscore` and `bb_reversion` share a redundancy class and only the
representative combination survives. Its sibling `any(breakout+bb_reversion)` scores **+0.174 on
−11.8%**. Measured as combinations the two are **0.968 correlated on 0.977 agreement** — the same
position 97% of the time — so that 42-point spread is what a **sixteen-trade** sample does to a
result, not two different strategies. Treat neither figure as informative.

---

## 7. Bollinger Band Breakout — `breakout` · MEASURED

**What it is.** Long a close above the upper band; optional squeeze pre-filter.
**Looks for.** Statistically unusual strength, optionally after a volatility contraction.

**Equation.**
```
mid_t   = SMA(n)_t
sd_t    = population stdev of last n closes (ddof=0)
upper_t = mid_t + k*sd_t ;  lower_t = mid_t - k*sd_t
bandwidth_t = (upper_t - lower_t) / mid_t                  # the squeeze measure
enter if c_t > upper_t  [and bandwidth_t <= quantile(bandwidth history, q)]
exit  if c_t < mid_t
```

**Data.** Close (High/Low not required). **Available.** **Deps.** None.
**Warm-up.** `n + squeeze_lookback` bars.

**Works when.** Expansion follows contraction — the squeeze gate is the mechanism that tries to
select for that.
**Fails when.** Volatility is already elevated, so the band is wide and a breach means little.
Closing-price dispersion does not directly measure an intrabar high–low range; a gap can also change that dispersion. Keltner’s ATR basis explicitly uses high, low and previous close, so the two band definitions measure different properties.

**Backtest notes.** This implementation uses **population** stdev (ddof=0). A ddof=1 implementation gives different bands. No universal claim about every charting package is required.
**Pairs with.** The squeeze filter (built in, `squeeze_lookback`, **not swept** — off by
default); volume confirmation; a trend filter for direction.

**Implementation.** `core/strategies/signals.py::BollingerBreakout`.
**Measured.** Medium: **IS +2,843.6% (Sharpe 1.837) → OOS −34.9% (Sharpe −0.841)**.
**The largest in-sample number in the entire sweep, and it lost money out-of-sample.** If you
read one row in this document as a warning about full-sample leaderboards, read this one.

---

## 8. Keltner Channel Breakout — `breakout` · MEASURED

**What it is.** Breakout of an ATR-width channel around an EMA.
**Looks for.** A breakout using true range, which explicitly includes the distance from the previous close.

**Equation.**
```
TR_t  = max(H_t - L_t, |H_t - c_{t-1}|, |L_t - c_{t-1}|)
ATR_t = Wilder smoothing of TR with period p:  ATR_t = (ATR_{t-1}*(p-1) + TR_t)/p
enter if c_t > EMA(s)_t + m*ATR_t ;  exit if c_t < EMA(s)_t
```

**Data.** High, Low, Close. **Available.** **Deps.** EMA + Wilder ATR. **Warm-up.** `3*max(s,p)+1`.

**Works when.** Trending markets with expanding true range.
**Fails when.** Same chop problem as any breakout. Its advantage over Bollinger is specifically
**range definition** — true range includes high, low and previous close; closing-price dispersion measures a different property and can also respond to gaps.

**Backtest notes.** ATR is also the corpus-documented sizing and stop unit: stops at
**1.5–2 ATR**, position sized so 1 ATR of adverse move equals ~1% of account. That risk-overlay
use is arguably more valuable than the entry signal, and is **not** tested here.
**Pairs with.** Trend confirmation; volume.

**Implementation.** `core/strategies/signals.py::KeltnerBreakout`.
**Measured.** Medium: IS +880.7% (Sharpe 1.391) → **OOS −26.4%**, 6 OOS trades (below floor).
Short: **OOS Sharpe −1.954** on 13 trades despite positive IS.

---

## 9. RSI Mean-Reversion — `oscillator-reversion` · MEASURED

**What it is.** Buy when Wilder's RSI is oversold; exit when it recovers past a midline.
**Looks for.** Short-term exhaustion of selling pressure.

**Equation.**
```
gain_t, loss_t   = max(dC_t,0), max(-dC_t,0)
avgGain, avgLoss = Wilder smoothing with period p
RS   = avgGain / avgLoss
RSI  = 100 - 100/(1 + RS)
enter if RSI < oversold ;  exit if RSI > exit_level        (stateful hold between)
```

**Data.** Close only. **Available.** **Deps.** Wilder smoothing. **Warm-up.** `p+1` bars.

**Works when.** Range-bound, mean-reverting conditions.
**Fails when.** **In a strong trend RSI stays overbought or oversold for weeks — the reading
becomes a trend-continuation indicator, not a reversal signal.** The corpus is explicit that
mean-reversion families show attractive 60–80% win rates that conceal rare catastrophic losses:
*"picking up nickels in front of a steamroller."*

**Backtest notes.** Judge on the tail, not the win rate. A 75%-win-rate equity curve with one
−60% trade is not a good strategy, and average-based metrics will hide it. Report max drawdown
and the worst single trade.
**Pairs with.** A regime filter (mandatory in my view — it patches the exact failure mode);
volume to distinguish accumulation from distribution.

**Implementation.** `core/strategies/rsi.py`.
**Measured.** Medium: IS −9.6% → OOS −21.9%, only 4 OOS trades (below floor). Short (period 7):
**OOS Sharpe −0.527**. `all(sma_regime+rsi)` reached **OOS +1.456** — the filter did the work.

---

## 10. Stochastic Oscillator with Turn-Up Confirmation — `oscillator-reversion` · MEASURED

**What it is.** Long when %K is oversold **and** already above %D (turning up).
**Looks for.** Position within the recent range, plus evidence the turn has begun.

**Equation.**
```
%K_t = 100 * (c_t - min(L_{t-k+1..t})) / (max(H_{t-k+1..t}) - min(L_{t-k+1..t}))
%D_t = SMA(d) of %K
enter if %K < oversold AND %K > %D ;  exit if %K > exit_level
```

**Data.** High, Low, Close. **Available.** **Deps.** None. **Warm-up.** `k+d+1` bars.

**Works when.** Ranging markets. The `%K > %D` condition is the meaningful addition — buying
oversold *alone* is how you get run over in a downtrend.
**Fails when.** Sustained trends, same as RSI. Whipsaws on the %K/%D cross in noisy data.

**Backtest notes.** Guard the degenerate case: when the *k*-bar range is zero, %K is undefined;
this implementation returns the neutral 50 rather than dividing by ~0.
**Pairs with.** Momentum, as a brake (`all(macd+stochastic)` was measured positive);
z-score, as a second formulation of a “stretched” condition; independence is unproven.

**Implementation.** `core/strategies/signals.py::StochasticOversold`.
**Measured.** Medium: **OOS Sharpe +0.024** (IS +0.153), 11 OOS trades. The original 16-mechanism card described it as one of three positive medium-horizon singles. The retained 25-strategy phase has **four** positive rankable medium-horizon singles, including this row; the value is close to zero, without a supplied significance test.

---

## 11. Bollinger Mean-Reversion — `mean-reversion` · MEASURED

**What it is.** Buy a close below the lower band; exit on reversion to the mid.
**Looks for.** Statistically extreme downside deviation.

**Equation.**
```
enter if c_t < mid_t - k*sd_t ;  exit if c_t > mid_t
```

> **Defect to know about.** This is **the same inequality** as the z-score entry below,
> differing only in the stdev convention: `sd(ddof=0)` here vs `sd(ddof=1)` there, a factor
> `sqrt(n/(n-1)) ≈ 1.026` at n=20. The exits are exactly equivalent (`c > mid` ⟺ `z > 0`).
> **These are one mechanism at two thresholds, not two signals** — and because both are in the
> sweep, several "cross-family" pairs and two identical `+2.555` triples are double-counting it.
> Verified from source, not assumed. See “Historical SOL strategy rankings and robustness checks” (forthcoming, planned 2026-11-18) List 3.

**Data.** Close only. **Available.** **Deps.** None. **Warm-up.** `n` bars.

**Works when.** Range-bound regimes with a stable mean.
**Fails when.** **The mean itself shifts.** The corpus names regime change as the primary
killer: shorting overbought in a secular bull, or buying oversold in a secular bear, compounds
losses. Measured full-sample medium: **−65.64%**.

**Backtest notes.** Bound the hold. The Ornstein-Uhlenbeck **half-life** gives the natural cap:
exit at 2–3× half-life regardless of signal. A 30-day half-life cutoff is a horizon-specific heuristic, not a universal boundary between tradeable and untradeable series. **This implementation has no such cap** — a real gap.
**Pairs with.** Regime filter (essential); volume.

**Implementation.** `core/strategies/signals.py::BollingerReversion`.
**Measured.** Medium: IS −63.9% → **OOS +0.193 Sharpe** (−4.8% return), 10 OOS trades.
`all(sma_regime+bb_reversion)`: **OOS Sharpe +2.572** (short).

---

## 12. Z-Score Mean-Reversion — `mean-reversion` · MEASURED

**What it is.** Buy when price is *z* sample-standard-deviations below its trailing mean.
**Looks for.** Normalised distance from fair value — the same construction used for
cointegration spreads, applied to raw price.

**Equation.**
```
z_t = (c_t - mean(c_{t-n+1..t})) / stdev_sample(c_{t-n+1..t})     # ddof=1
enter if z_t <= entry_z (-2.0) ;  exit if z_t >= exit_z (0.0)
```

**Data.** Close only. **Available.** **Deps.** None. **Warm-up.** `n` bars.

**Works when.** Stationary or range-bound series. **Raw-price stationarity was not established here**, which is the
central theoretical weakness — the corpus applies this to a *cointegrated spread*, where
stationarity is tested, not to a single price. This entry is the degenerate single-asset case.
**Fails when.** Trending markets — z-score simply keeps making new lows.

**Backtest notes.** Zero-dispersion windows must return 0, not divide by ~0 and emit a huge
spurious score. Properly, test the series for stationarity (ADF) before trusting this at all.
**Pairs with.** Regime filter (measured best-in-class); breakout for the exit
(`any(breakout+zscore)` was the top medium pair).

**Implementation.** `core/strategies/signals.py::ZScoreReversion`.
**Measured.** **Top-ranked medium single: OOS Sharpe +0.699, OOS return +41.3%** (IS −64.8%),
10 OOS trades — exactly at the evidence floor, so read as "not yet disconfirmed", not "works".
Short: **OOS +0.441**, 48 trades.

---

## 13. Rolling VWAP Reversion — `mean-reversion` · MEASURED

**What it is.** Buy a discount to volume-weighted average price; exit on reversion.
**Looks for.** Deviation from the price where volume actually transacted.

**Equation.**
```
TP_t   = (H_t + L_t + c_t)/3                          # typical price
VWAP_t = sum(TP_i * V_i, i in window) / sum(V_i, i in window)
enter if c_t < VWAP_t * (1 - discount) ;  exit if c_t >= VWAP_t
```

**Data.** High, Low, Close, **Volume**. **Available.** **Deps.** None. **Warm-up.** `n` bars.

**Works when.** Intraday/short-horizon reversion toward a volume-weighted anchor.
**Fails when.** Trending markets. Note this is **rolling**, not session-anchored — crypto has no
session open, so it is a fair-value-deviation signal rather than the execution benchmark VWAP
normally serves as. That is a meaningful reinterpretation, not a detail.

**Backtest notes.** A zero-volume window must fall back to an unweighted mean rather than
dividing by zero. Exchange-reported crypto volume is unreliable across venues; single-venue
volume (as here) is at least internally consistent.
**Pairs with.** OBV, to distinguish a discount being accumulated from one being distributed
(`all(vwap_reversion+obv_trend)` measured **OOS +0.186** long).

**Implementation.** `core/strategies/signals.py::VwapReversion`.
**Measured.** Medium: **OOS −53.9%** (Sharpe −0.532), 23 OOS trades. Short: **OOS Sharpe −1.516**.
Consistently among the worst measured rows.

---

## 14. On-Balance Volume Trend — `volume-flow` · MEASURED

**What it is.** Long while cumulative signed volume is above its own moving average.
**Looks for.** Accumulation vs distribution — whether volume is arriving on up-bars or down-bars.

**Equation.**
```
OBV_t = OBV_{t-1} + sign(c_t - c_{t-1}) * V_t
target_t = 1 if OBV_t > SMA(n) of OBV  else 0
```

**Data.** Close + **Volume**. **Available.** **Deps.** None. **Warm-up.** `n+2` bars.

**Works when.** Volume genuinely leads price. OBV uses the sign of price changes as well as volume. It can add volume-weighted directional information, but is not price-blind or statistically independent of price signals.
**Fails when.** Volume data is unreliable or venue-fragmented (a real crypto problem). OBV is
also a running cumulative sum, so it is **path-dependent and level-arbitrary** — only its slope
relative to its own average carries information.

**Backtest notes.** Because OBV is cumulative from an arbitrary origin, its absolute level is
meaningless and any comparison must be to its own history. Splitting the series (as walk-forward
does) restarts the accumulation — a subtlety worth being aware of when comparing legs.
**Pairs with.** Any price-based trend or breakout signal. This is its highest and best use.

**Implementation.** `core/strategies/signals.py::ObvTrend`.
**Measured.** Medium: **IS +1,932.1% (Sharpe 1.494) → OOS −69.2% (Sharpe −1.383)**.
Long: IS +982.7% → OOS −24.0%, and `any(rsi+obv_trend)` was the **best long-horizon pair
(OOS +0.226)** — though at −8.8% return, meaning low well-behaved exposure, not profit.

---

## 15. Volatility-Targeted Trend — `risk-overlay` · MEASURED

**What it is.** Trend entry, sized inversely to realised volatility. Continuous exposure.
**Looks for.** Constant *risk* rather than constant *notional*.

**Equation.**
```
sigma_t = stdev(log returns over n bars) * sqrt(periods_per_year)
target_t = min(1, target_vol / sigma_t)   if c_t > SMA(trend)_t   else 0
```

**Data.** Close only. **Available.** **Deps.** None. **Warm-up.** `max(trend,vol)+1` bars.

**Works when.** Volatility is persistent (it is, in crypto — volatility clusters). Changes the
*shape* of the equity curve rather than the direction of the bet.
**Fails when.** Volatility spikes and price rises together — it de-risks into strength. Also
reacts with a lag equal to the vol window.

**Backtest notes.** **This should be tested as a wrapper around other signals, not as a
standalone strategy — and that is exactly what was not done here.** It is the only candidate in
the set intended to alter exposure sizing rather than select a different direction. That does not make its returns statistically orthogonal to direction. The
untested wrapper configuration is the most obvious gap in this sweep.
**Pairs with.** Everything, multiplicatively. See “Historical SOL strategy rankings and robustness checks” (forthcoming, planned 2026-11-18) List 2 #8.

**Implementation.** `core/strategies/signals.py::VolTargetTrend`.
**Measured.** Medium: IS +15.7% → **OOS −31.1%**, 73 OOS trades. Short: OOS −0.519, numerically
near-identical to `sma_regime_168` — because when `sigma < target_vol` the cap binds at 1.0 and
it degenerates into the plain regime filter.

---

## 16. Long-Only Grid — `mean-reversion` · MEASURED

**What it is.** Staircase accumulation as price falls below a rolling anchor.
**Looks for.** Range-bound oscillation to harvest.

**Equation.**
```
anchor_t   = SMA(n)_t
drawdown_t = 1 - c_t/anchor_t
rungs_t    = min(floor(drawdown_t / step) + 1, levels)     if drawdown_t > 0 else 0
target_t   = rungs_t / levels
```

**Data.** Close only. **Available.** **Deps.** None. **Warm-up.** `n` bars.

**Works when.** Genuine ranges. Heavily used in crypto because it feels good in a chop.
**Fails when.** **A sustained downtrend — it is short volatility and long the range assumption,
so it reaches maximum exposure exactly when it is most wrong.** This is the most instructive
failure mode in the set: the strategy's own mechanism converts a trend into a maximum-size
losing position.

**Backtest notes.** Grid results are dominated by whether the test window contained a range or a
trend, so a single-window backtest of a grid is close to meaningless. Also generates enormous
trade counts (measured **694 short / 143 long**), making it unusually cost-sensitive.
**Pairs with.** A regime filter, which vetoes precisely the condition that ruins it. **This
pairing was not swept** and is the highest-value untested pair in List 2 (#10).

**Implementation.** `core/strategies/signals.py::GridLong`.
**Measured.** Medium: **OOS −38.9%** (Sharpe −0.590), 100 OOS trades. Short: **OOS Sharpe −1.510**
across 694 trades. Long: OOS −26.5%, 143 trades.

---

## TIER 2 — SPEC-ONLY (26 mechanisms, numbered 17–42)

**Not implemented and not run. No performance figures — none are given below, deliberately.**
Each entry names the equation, what it needs, and the specific data gap that prevented
measurement. Ordered by family.

## Momentum & trend

**17. Cross-sectional momentum.** Rank a universe by trailing return, hold the top decile.
`R_i = c_i,t/c_i,t-n - 1`; long top-k by rank. The most-documented anomaly family (Jegadeesh &
Titman 1993, cited by the original reference collection). **Gap: no peer universe fetched.** Would also
require survivorship-free constituent history — the corpus estimates survivorship bias inflates
long-only equity backtest returns by **1.5–2.0% annually**.

**18. Dual-momentum / 12-1.** Trailing 12-period return excluding the most recent period, to
skip the short-term reversal effect. **Gap: implementable now** — needs code, not data.

**19. Moving-average ribbon / triple-MA.** Multiple MAs; exposure scales with the fraction in
correct order. Variant of #2, low marginal information.

**20. ADX-filtered trend.** Use Wilder's ADX (`DI+`/`DI-` from directional movement) to gate a
trend signal on trend *strength*. `ADX > 25` conventionally means trending.
**Gap: implementable now.**

**21. Ichimoku cloud.** Multi-component (Tenkan/Kijun/Senkou) trend-and-support system.
Mechanically a bundle of MA crossovers plus a displaced channel; the displacement is a
look-ahead trap if implemented carelessly — the "future cloud" is plotted forward and must
never be read as a current signal.

## Mean-reversion & statistical

**22. Pairs trading / cointegration vs ETH or BTC.** The rigorous version of #12.
Engle-Granger two-step: regress `X = beta*Y + eps`, ADF-test the residual for stationarity; if
`p < 0.05` a cointegrating relation exists. `Spread = X - beta*Y`, trade its z-score: enter
±2.0, exit toward 0, stop ±3.0. Johansen is preferred for 3+ assets (order-invariant).
Practitioner heuristic: require cointegration across 3-, 6-, and 12-month rolling windows.
**Gap: no peer price series.** Primary risk is convergence failure — the relation breaks and the
spread keeps diverging.

**23. Ornstein-Uhlenbeck half-life sizing.** Fit `dX = theta*(mu - X)dt + sigma*dW`;
`half_life = ln(2)/theta`. Cap holds at 2–3× half-life. **Gap: implementable now** — and it is
the missing piece in #11/#12 (neither has a hold cap).

**24. Kalman-filtered dynamic hedge ratio.** Let `beta` evolve as a state variable rather than
fixing it per window. Addresses the corpus-noted instability of static hedge ratios.
**Gap: no peer series.**

**25. Variance-ratio / Hurst exponent regime test.** `H < 0.5` mean-reverting, `H > 0.5`
trending. A *meta*-signal that selects which family to run. **Gap: implementable now — and
this is the highest-value unimplemented item in this tier**, because the entire measured sweep
shows trend and reversion inverting between regimes.

**26. Volatility-regime HMM.** Two-or-three-state hidden Markov model on realised volatility,
switching the active strategy family. **Gap: implementable now.**

## Volatility & options

**27. Implied-vs-realised vol spread.** Harvest the variance risk premium when
`IV - RV` is historically wide. **Gap: no options surface for SOL.**

**28. ATR-normalised position sizing.** Size so 1 ATR of adverse move equals a fixed % of
equity; stops at 1.5–2 ATR. **Gap: implementable now** — a risk overlay, arguably higher value
than most entry signals here, and untested.

**29. GARCH(1,1) volatility forecast.** `sigma2_t = omega + alpha*eps2_{t-1} + beta*sigma2_{t-1}`.
Feeds vol-targeting with a forecast instead of a trailing estimate. **Gap: implementable now.**

**30. Volatility-of-volatility / vol-term-structure.** Requires an options surface. **Gap: no data.**

## Crypto-native / on-chain

**31. Perp funding-rate extremes.** On most venues funding is a signed transfer whose extremes
mark crowded positioning. **On Jupiter specifically there is no funding rate — there is a
borrow fee**, `hourlyBorrowRate = max_rate * utilization`, charged on notional to **both** sides
and floor-bounded at zero. So the tradeable signal there is **utilization**, not funding sign.
**Gap: no borrow-rate/utilization history.** Highest-ranked spec-only signal.

**32. Open-interest divergence.** OI rising while price is flat marks leverage build-up and
liquidation risk. **Gap: no OI history.**

**33. Liquidation-cascade proximity.** Estimate clustered liquidation levels from OI and
leverage distribution; fade or follow the cascade. **Gap: no OI or position data.**

**34. Exchange net-flow / stablecoin flow.** Stablecoins moving onto exchanges as a proxy for
incoming buying power. **Gap: no on-chain data.**

**35. Staking-ratio / validator flow.** SOL-specific float dynamics — a rising staked fraction
reduces liquid supply. **Gap: no on-chain data.**

**36. DEX-vs-CEX price dislocation.** Cross-venue basis as both a signal and an arbitrage.
**Gap: no DEX quote history.** Would additionally need MEV-aware execution modelling (private
RPC or intent protocols) to be realistic.

**37. JLP-vs-SOL relative value.** JLP is ~68% crypto and realises roughly **0.42–0.53× SOL's
short-horizon volatility** (corpus, hourly percentiles). Trading the ratio is a
volatility-dampened SOL expression. **Gap: no JLP price history fetched.**

**38. MVRV / NUPL / on-chain valuation ratios.** Market value vs realised value as a
cycle-position gauge. **Gap: no on-chain cost-basis data.**

## Microstructure

**39. Order-book imbalance.** `(bid_vol - ask_vol)/(bid_vol + ask_vol)` at depth *k*. The
highest-frequency edge available. **Gap: no L2 data.**

**40. Trade-flow imbalance / aggressor ratio.** Signed trade prints. Requires tick data.
**Gap: no trade prints.** Note that Kyle/Glosten-Milgrom adverse-selection dynamics mean naïve
flow-following is systematically picked off.

**41. Avellaneda-Stoikov market making.** Optimal quotes around a reservation price with
inventory penalty. **Gap: needs L2 + a venue with maker rebates; also fundamentally an
execution strategy, not a directional signal, so this harness is the wrong shape for it.**

## Sentiment & alt-data

**42. Social/dev-activity sentiment.** Corpus documents social-sentiment alpha horizons of
**1–2 days with fast decay**, and bot-noise/sarcasm as principal difficulties. **Gap: no feed.**

---

## Cross-cutting: how to backtest any of these honestly

Distilled from the corpus's pitfall taxonomy, in the order these actually bite:

1. **Look-ahead, four mechanisms.** (1) *Data leakage* — full-sample normalisation is the
   classic; use expanding/rolling windows. (2) *Point-in-time failure* — restated data at
   historical dates. (3) *Survivorship* — 1.5–2.0% annual inflation in long-only equity
   backtests. (4) *Label leakage* — the label spans future bars; needs purge/embargo.
2. **Purged, embargoed CV.** Purge training observations whose label windows overlap the test
   fold; embargo the first *h* observations after it. **CPCV** samples all valid train/test
   combinations to give a *distribution* of backtest paths — the fix for the single-split
   problem that dominates every result in this document.
3. **Multiple testing.** 953 configurations were evaluated here. Harvey-Liu-Zhu: raise the
   t-stat bar from 2.0 to **3.0+**. Bailey et al.: PBO rises with the size of the search.
   Deflated Sharpe adjusts for trial count, skew, and kurtosis. The source collection attributes **26% / 58%** decay figures across 97 published factors to McLean & Pontiff. These refer to out-of-sample / post-publication comparisons, respectively, not “in-sample / out-of-sample” returns; the study’s own results remain separate.
4. **Signal quality before strategy performance.** Information Coefficient (rank correlation of
   prediction with realised return) is the cleaner primitive: useful equity signals run
   **IC 0.02–0.08**, and **ICIR = mean(IC)/std(IC) > 0.5** is considered usable.
   Grinold-Kahn: `IR = IC * sqrt(Breadth)` — which is why single-asset strategies are
   structurally disadvantaged regardless of signal quality.
5. **Cost realism.** Costs on the fill, never netted at the end. Slippage as flat bps
   understates crash conditions. For leveraged SOL, the Jupiter borrow fee dominates: a
   measured 10× run burned **\$722 of borrow fees against \$211 of trading fees**.
6. **Sample-size floors.** Both trade count (10 minimum here, and 30+ would be better) and
   window length. Seventeen of twenty-five long-horizon singles failed the floor — that is a
   statement about the data, not the strategies.

## Leverage tiers (registered wrappers)

`lev_low` (2x), `lev_medium` (5x) and `lev_high` (20x) run any registered long/flat strategy as a
Jupiter-Perps position with borrow carry, fees, maintenance margin and intrabar liquidation. They are
wrappers, not signals; cards in `backtester/strategy_cards/lev_*.md`. SOL daily CPCV result: P(ruin)
21% at 2x, 74% at 5x, 95% at 20x. See `research/LEVERAGE-TIERS.md`.

## Reliable triggers (registered: `trigger_trade`)

`research/triggers.py` mines conjunctions of up to three causal conditions (MACD, RSI zones, MA slope,
Bollinger touches, z-scores, volume spikes, OBV/balance proxies, ATR expansion, consecutive candles, gaps,
funding extremes, drawdown) for how often the next 1 to 10 bars go the predicted way, against the base rate,
with a fixed later validation period, FDR control, stability and cross-asset gates. `trigger_trade` trades one
(entry next open, exit at the horizon or a MAE-derived stop). Result on SOL: no trigger qualified as reliable
out of sample. See `research/RELIABLE_SIGNALS.md`; card `backtester/strategy_cards/trigger_trade.md`.

## Reproducing everything

```bash
python3 -m backtester.core.fetch --asset SOL --interval 1d --start 2021-01-01
python3 -m backtester.core.fetch --asset SOL --interval 1h --start 2025-08-01 --allow-gaps
python3 research/sweep.py
python3 research/cpcv_sweep.py                           # CPCV + PBO (List 1, primary)
python3 research/verify_numbers.py                       # parsed archived figures checked against results
python3 -m unittest discover -s backtester/tests -t .    # original report listed 409 tests; not rerun for this publication
```

> Educational and research use only. **NOT investment advice.** Nothing in this document is
> evidence that any listed mechanism is profitable. The measured evidence is that on this asset
> and this window, 8% of 595 rankable configurations made money, and in-sample rank did not
> predict out-of-sample rank.
