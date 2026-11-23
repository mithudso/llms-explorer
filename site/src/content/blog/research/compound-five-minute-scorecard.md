---
title: "A compound five-minute direction scorecard"
description: "A compound five-minute direction scorecard. An edited historical research report with its original evidence limits retained."
date: "2026-11-23"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# A compound five-minute direction scorecard: what each metric checks, why it is there, how to tune it, and what 30 days of evidence show

Historical implementation and simulation snapshot: **2026-11-07**. The main text describes 35 original components; the explicitly dated update describes later additions and changed formulas. Neither section is a current feature inventory. Tables retain the saved historical values; this editorial review did not rerun the sweep or start forward training.

*solmargintrader, 2026-11-07. Research note, not financial advice. Nothing described here places an order. Every figure in the results sections is recomputed from the saved sweep rows (`COMPOUND_STATE/backtests.jsonl`, run `20261107T130441Z-f7fea5b2368e`), not copied from earlier documents.*

> **Update, later on 2026-11-07 (PR "wallet sizing, click-to-toggle, unattended training…").**
> Several statements below describe the scorecard as it was when this paper was written. What
> changed, with the then-current implementation documented in `docs/COMPOUND-5M.md` and `backtester/core/scorecard.py`:
>
> * **Four new metrics** (39 components now: 32 that vote, 7 gates): `ema_trend` (price vs one EMA),
>   `volume` (unusual volume signed by the candle), `bop` (balance of power) and `zigzag` (a
>   non-repainting swing leg).
> * **Families regrouped by measured correlation** on five coins: `rsi`, `stochastic`, `cci`,
>   `bollinger` and `zscore` are one family, `stretch` (their scores correlate 0.80–0.98);
>   `ichimoku` joins `ma-trend` (+0.83–0.87); `macd` moves to `momentum` with `roc` (+0.80). The
>   family labels in section 3 are the old ones.
> * **Inversion is on by default** (`adaptive_flip = 1`): a metric whose learned record is below 50%
>   votes inverted. Inverted, each trend metric scored 50–55% on nearly every coin, and the
>   compound's losses were smaller on all five coins than with muting.
> * **Opposed and duplicate metrics** are measured and shown: the trend and stretch groups correlate
>   −0.75 to −0.93 at 5m; `vwap_side` and `vwap_reversion` are mirror images (−0.99).
> * **Wallet sizing**: live calls are sized to the public balance at the Settings Solana address.
> * **Unattended forward training**: a detached per-asset loop that records and resolves calls.
> * **VWAP metrics rescaled (2026-11-07, later).** `vwap_side` and `vwap_reversion` measured the
>   distance from the session VWAP in 5m ATRs. That distance is routinely 1–2% while one ATR is about
>   0.12%, so `vwap_reversion` sat at ±1 on 57% of SOL bars and held the compound on one side for
>   hours. Both now divide the distance by its typical size: the RMS of the distance over
>   `spread_window` bars (default 288), floored at one ATR. They saturate on about 8% of bars. Their
>   learned records restart (formula version 2). The formulas and results below are the old ones.
> * **Trend filter (`gate_trend`, default on).** An eighth gate blocks a call against the 1h trend
>   (`htf_trend` at or beyond ±0.5). It is directional: a call with the trend passes. See
>   `docs/COMPOUND-5M.md` for the measured trade-off.
> * With all of this, the default compound's out-of-sample hit rate (static → learned + invert) was
>   BTC 50.3 → 49.5%, DOGE 44.9 → 55.8%, ETH 45.6 → 52.6%, SOL 47.3 → 51.1%, ZEC 48.3 → 51.1%.
>   **Returns stayed negative on every coin.**

## Abstract

The compound scorecard asks one question: **will the next five-minute bar of a crypto perpetual close up or down?** It scores 28 metrics from -1 (down) to +1 (up), removes the double-counting between metrics that measure the same thing, reweights styles by market regime, and combines the scores into one call (UP, DOWN or FLAT) behind seven veto gates. This paper lists every metric, what it checks and why it was included, every tunable parameter with its default and range, and the evidence so far.

The evidence is negative. Across 1,420 configurations on five coins (30 days of 5-minute bars, last 30% held out), **none made money after costs in a way that survives scrutiny**: 10 of 1,420 had a positive out-of-sample return, and each of those 10 had a hit rate statistically indistinguishable from a coin flip. The compound with static weights (the configuration the saved sweep ran) lost between 17% and 63% of capital out-of-sample at 5x leverage on every coin (mean -43%). The all-transitions diagnostic is negative on all five coins (about -7 to -10 bps on four, -0.4 on ZEC): the average absolute close-to-close log return is smaller than the configured 16 bps round-trip cost. This unconditional average does not bound a selective trading policy. The one weak positive signal is a **reversion** effect in the oscillators (RSI, z-score, Stochastic, Bollinger: out-of-sample hit rates 50 to 57% across the five coins), which is the opposite direction from the catalogue's regime advice, may be partly a measurement artefact, and has not been forward tested. A later addition, **learned weights** (each metric weighted by its own capped, Bayesian-updated record), reaches this reversion tilt without anyone choosing it and lifts the compound's out-of-sample hit rate to 46.5 to 55.6%, but returns stayed negative in every row. **No forward-test record exists yet, and the planned year-long run has not completed.** These results are weak evidence about one 30-day regime, and say nothing about profitability.

## 1. Scope and question

**In scope.** `backtester/core/scorecard.py` (pure scoring and aggregation, no I/O), `backtester/core/compound.py` (historical evaluation through the engine), `soltui/compound.py` (saved configuration, live reads, forward ledger, sweeps, CLI) and the soltui **Compound 5m** tab. The metric set comes from `5minleveragestrategies.json` (the "catalogue") plus metrics added where the catalogue left a gap.

**Out of scope.** Eight catalogue entries are not five-minute direction calls and are listed in the tab with the reason: range/grid trading, scalping as a style, swing trading, dollar-cost averaging, cross-exchange, triangular and funding arbitrage, and Jupiter's unpublished long/short-flow imbalance. The registry strategies (`backtester/core/strategies/`, evaluated on daily and hourly bars with the sweep in `research/`) are a separate body of work; their overall record is that 14% of 311 rankable configurations had a positive out-of-sample Sharpe and 9% made money.

**Venue assumption.** Costs are those of Jupiter Perps: 6 bps fee and 2 bps slippage per side, 16 bps per round trip. Jupiter fills at the oracle price, so there is no bid-ask spread to capture. This matters for interpretation (section 7).

## 2. How a call is made

1. **Score.** Each enabled metric returns a score in [-1, 1] for the latest *closed* bar, or *undefined* (still warming up, or a live input is missing). Undefined is never treated as zero: zero means "no opinion", undefined means "cannot say".
2. **De-duplicate families.** RSI, Stochastic and CCI measure one quantity (where the close sits in its recent range); MACD and the EMA cross share two EMAs. Averaging every enabled metric would let the family with the most members outvote a family with one, which measures how many indicators someone wrote, not how much evidence exists. With `dedupe_families = 1`, each family contributes its weighted mean once, at the weight of its heaviest member.
3. **Weight by regime.** Each bar is classified *trend* (ADX at least 25), *range* (ADX at most 18), *squeeze* (Bollinger bandwidth in its lowest 15% over a day) or *neutral*. Each metric's weight is multiplied by its style's multiplier for that regime (table in section 4.2).
3b. **Learn (on by default since the adaptive-weights change).** With `adaptive = 1`, each metric's weight is also multiplied by its own learned edge over a coin flip (section 4.5). The saved sweep in section 6 predates this and ran with static weights.
4. **Threshold with hysteresis.** A composite with absolute value at least `entry` (0.25) calls UP or DOWN. A held call stays on while the composite keeps its sign above `exit` (0.10). Hysteresis exists because every flip pays a round trip.
5. **Gate.** Any enabled gate that blocks forces FLAT and is named in the call. A gate that cannot be evaluated blocks (fails closed). If less than `min_coverage` (0.5) of the enabled weight is defined, the call is FLAT.

**Causality is tested, not assumed.** Every component is a vectorised function in which the value at bar *t* depends only on bars up to *t*. `tests/test_scorecard.py` checks *prefix invariance* for each one: the score at bar *t* computed from bars [0..t] must equal the score at bar *t* computed from the whole series. A one-bar leak (a negative shift, a centred window, a backward fill) fails that test.

## 3. The metrics

Thirty-five components: 28 that vote and 7 gates that veto. The tables give, for each, **what it checks**, **why it is included**, the score formula, and when it is expected to work and fail (from the catalogue in `scorecard.py`). Parameters are in Appendix A. "Default" means enabled in the default configuration. Metrics marked *live only* need data no venue serves historically (funding history is the exception, from the Hyperliquid cache) and are NaN in a backtest.

### 3.1 Trend and direction

**`ema_cross`** — EMA crossover (family `ma-trend`, style `trend`; default on)\
*Checks:* Whether a fast exponential average sits above or below a slow one, measured in ATRs so the score does not depend on price level.\
*Why included:* The most common trend definition; included as the baseline trend vote. It is also the ingredient other components (MACD, lifecycle, continuation) are built from, which is why they share a family.\
*Formula:* `tanh((EMA_fast - EMA_slow) / (scale * ATR))`\
*Works when:* Sustained trends; confirms direction. *Fails when:* Chop; lag makes late entries and whipsaws.

**`macd`** — MACD histogram (family `ma-trend`, style `momentum`; default on)\
*Checks:* Whether the MACD line is above or below its signal line: a change in the pace of the trend.\
*Why included:* Measures the acceleration of the same two averages, so it can turn before a plain crossover. Same family as the EMA cross: it is not independent evidence.\
*Formula:* `tanh((MACD - signal) / (scale * ATR)); MACD = EMA_fast - EMA_slow`\
*Works when:* Trend confirmation, momentum shifts. *Fails when:* Flat noisy markets; repeated crossovers whipsaw.

**`adx_dmi`** — ADX / DMI direction (family `directional`, style `trend`; default on)\
*Checks:* Whether a trend exists at all (ADX above a threshold) and which side is winning (+DI against -DI).\
*Why included:* Answers 'is there a trend to follow?' separately from 'which way?'. A direction signal in a trendless market is noise, so this one only speaks when ADX exceeds its threshold.\
*Formula:* `sign(+DI - -DI) * clip((ADX - threshold)/threshold, 0, 1)`\
*Works when:* Selecting trend vs range; filtering weak breakouts. *Fails when:* Abrupt regime changes before smoothing catches up.

**`vwap_side`** — Price vs VWAP (family `vwap`, style `trend`; default on)\
*Checks:* Whether price is above or below the rolling volume-weighted average price: which side of the day's fair value the market holds.\
*Why included:* Intraday traders anchor on VWAP; the catalogue lists it as session context.\
*Formula:* `tanh((close - VWAP) / (scale * ATR))`\
*Works when:* Intraday trend context when other evidence agrees. *Fails when:* Thin markets; incompatible sessions.

**`htf_trend`** — Higher-timeframe trend (family `higher-timeframe`, style `context`; default on)\
*Checks:* The trend on a completed higher timeframe (default 1h) so a 5m trigger is read in its context. Only closed higher-timeframe bars are used.\
*Why included:* The catalogue's execution checklist step 3: take 5m triggers in the direction of a higher-timeframe regime.\
*Formula:* `tanh((HTF close - EMA(HTF closes)) / (scale * ATR * sqrt(tf/5))), completed HTF bars only`\
*Works when:* Execution checklist step 3: a 15m/1h regime filter with a 5m trigger. *Fails when:* Turning points, where the higher timeframe lags.

**`ichimoku`** — Ichimoku cloud (family `ichimoku`, style `trend`; default off)\
*Checks:* Position relative to the displaced Ichimoku cloud, with a bonus when the tenkan is on the same side of the kijun.\
*Why included:* Named in the catalogue as a multi-timeframe trend filter. Off by default: its parameters (9/26/52) are daily-chart conventions.\
*Formula:* `+0.5 above the (displaced) cloud, +1 if also tenkan > kijun; mirrored below; 0 inside`\
*Works when:* Multi-timeframe trend filter in orderly markets. *Fails when:* Very short-term scalping; abrupt regime changes.

### 3.2 Momentum and persistence

**`roc`** — Rate of change (vol-scaled) (family `momentum`, style `momentum`; default on)\
*Checks:* Rate of change over `window` bars, divided by what a move that size would normally be (volatility-scaled).\
*Why included:* The simplest momentum measure, volatility-scaled so one parameter set works across assets.\
*Formula:* `tanh(log(C_t/C_{t-n}) / (scale * sigma_1bar * sqrt(n)))`\
*Works when:* Persistent one-way moves. *Fails when:* Mean-reverting tape; after exhaustion.

**`persistence`** — Return persistence (lag-1 autocorrelation) (family `autocorrelation`, style `adaptive`; default on)\
*Checks:* Whether recent 5m returns tend to continue or reverse (rolling lag-1 autocorrelation), applied to the last move's sign.\
*Why included:* Added so the card can tell a trending tape from a reverting one from the data, instead of choosing a style by hand. Near zero at 5m on most bars.\
*Formula:* `clip(gain * rho_1 * sign(r_t)); rho_1 = rolling lag-1 autocorrelation of 5m returns`\
*Works when:* Tells continuation from reversal tape without choosing a regime by hand. *Fails when:* Autocorrelation near zero (the usual case at 5m); then it scores near 0.

### 3.3 Oscillators (one family)

**`rsi`** — RSI (family `oscillator`, style `reversion`; default on)\
*Checks:* How overbought or oversold the close is, as a counter-trend score.\
*Why included:* The standard oscillator in the catalogue. Given its own family with Stochastic and CCI because they measure one quantity.\
*Formula:* `(50 - RSI) scaled to +-1 at the oversold/overbought levels`\
*Works when:* Range trading, pullback timing. *Fails when:* Strong trends: RSI stays overbought.

**`stochastic`** — Stochastic %K/%D (family `oscillator`, style `reversion`; default on)\
*Checks:* Where the close sits in its recent high-low range, scored against the move, with full weight when %K turns back through %D.\
*Why included:* Catalogue oscillator; the turn-back condition is there to avoid buying a falling knife.\
*Formula:* `(50 - %K) scaled; full weight only while %K turns back through %D`\
*Works when:* Pullback timing inside a trend. *Fails when:* One-way trends: signals too early.

**`cci`** — Commodity Channel Index (family `oscillator`, style `reversion`; default off)\
*Checks:* Distance of the typical price from its average in mean-deviation units, as a counter-trend score.\
*Why included:* A third view of the same range-position quantity; off by default because it only adds votes inside a family.\
*Formula:* `clip(-CCI / extreme)`\
*Works when:* Range extremes. *Fails when:* Trends.

### 3.4 Mean reversion

**`bollinger`** — Bollinger %B fade (family `bands`, style `reversion`; default on)\
*Checks:* Where the close sits between the bands (%B); a counter-trend score that is strongest at the bands.\
*Why included:* Catalogue mean-reversion tool; also the source of the bandwidth used for the squeeze regime.\
*Formula:* `clip(1 - 2 * %B): +1 at the lower band, -1 at the upper`\
*Works when:* Mean reversion at extreme bands. *Fails when:* A trend that walks the band.

**`zscore`** — Z-score fade (family `bands`, style `reversion`; default on)\
*Checks:* How many standard deviations the close is from its rolling mean, as a counter-trend score.\
*Why included:* The statistical form of mean reversion, with an explicit entry threshold.\
*Formula:* `clip(-z / entry), z = (P - MA_n) / SD_n`\
*Works when:* Ranges with a stable mean. *Fails when:* Strong trends; losses compound without a stop.

**`vwap_reversion`** — VWAP stretch fade (family `vwap`, style `reversion`; default off)\
*Checks:* How far price has stretched from VWAP in ATRs, scored to fade the stretch.\
*Why included:* The catalogue's VWAP mean-reversion variant; off by default because it is the mirror of `vwap_side`, and both on cancel each other.\
*Formula:* `clip(-(close - VWAP) / (stretch * ATR))`\
*Works when:* Flat VWAP ranges. *Fails when:* Trend days.

### 3.5 Breakout and structure

**`donchian`** — Donchian breakout (family `breakout`, style `breakout`; default on)\
*Checks:* Whether the close broke the prior n-bar high or low, held for a few bars.\
*Why included:* The textbook breakout: a decisive close beyond a recent extreme.\
*Formula:* `+1 when close > prior n-bar high, -1 below prior low; held for hold bars`\
*Works when:* A range resolves with a decisive close. *Fails when:* False breakouts that return inside.

**`squeeze`** — Volatility-squeeze breakout (family `volatility`, style `breakout`; default on)\
*Checks:* Compression followed by expansion: low-bandwidth regime, then a close outside a band on above-average volume.\
*Why included:* Catalogue volatility-squeeze setup: expansion tends to follow compression.\
*Formula:* `after bandwidth <= squeeze_pct percentile, close outside a band on volume > vol_mult * avg`\
*Works when:* Compression into a liquid range, then decisive expansion. *Fails when:* Compression continues; breakout without participation.

**`trend_continuation`** — 5m trend continuation (VWAP + EMA + volume) (family `composite-rule`, style `trend`; default on)\
*Checks:* The catalogue's own 5m rule: above VWAP, fast above slow EMA, and volume above average, all at once.\
*Why included:* The catalogue's concrete 5m long/short rule, scored as written so it can be tested as written.\
*Formula:* `+1 when close > session VWAP and EMA_fast > EMA_slow and volume > vol_mult * avg; mirrored`\
*Works when:* A directional liquid session already under way. *Fails when:* Flat ranges, late extensions, thin liquidity.

**`liquidity_sweep`** — Liquidity sweep / failed breakout (family `structure`, style `reversion`; default on)\
*Checks:* A stop run: price pierces the prior extreme and the close reclaims it, which is read as a failed breakout.\
*Why included:* Catalogue structure idea: stop runs that fail and reverse.\
*Formula:* `+1 when the low pierces the prior n-bar low and the close reclaims it; mirrored at highs`\
*Works when:* Well-defined ranges with equal highs/lows. *Fails when:* Genuine news or liquidation breakouts.

**`fib_pullback`** — Fibonacci pullback zone (family `structure`, style `trend`; default off)\
*Checks:* Whether price is in the 38.2% to 61.8% retracement zone of the latest swing inside a trend.\
*Why included:* Catalogue Fibonacci entry. Off by default: the swing anchor is subjective and the same idea has its own registry strategy (`fib_retracement`).\
*Formula:* `+0.7 in an uptrend when price sits in the [zone_lo, zone_hi] retracement of the swing; mirrored`\
*Works when:* Pullbacks that respect a clear swing. *Fails when:* Subjective anchors; news-driven tape.

### 3.6 Volume and flow

**`obv`** — On-balance volume trend (family `volume-flow`, style `flow`; default on)\
*Checks:* Whether cumulative signed volume is rising or falling against its own average.\
*Why included:* Catalogue volume confirmation: is volume flowing with price?\
*Formula:* `tanh((OBV - SMA(OBV)) / (scale * SMA(volume) * sqrt(n)))`\
*Works when:* Breakout confirmation, accumulation clues. *Fails when:* Fragmented or anomalous volume.

**`money_flow`** — Chaikin money flow (order-flow proxy) (family `volume-flow`, style `flow`; default on)\
*Checks:* Chaikin money flow: whether candles close near their highs or lows, weighted by volume. A proxy for buying pressure from candles alone.\
*Why included:* Stands in for the catalogue's order-flow delta, which needs trade-level taker data that is not in OHLCV. Labelled as a proxy.\
*Formula:* `clip(CMF / scale); CMF = sum(CLV * V) / sum(V). A candle-derived proxy, NOT taker delta`\
*Works when:* Persistent one-sided prints. *Fails when:* Large isolated prints; it cannot see who crossed the spread.

**`book_imbalance`** — Order-book imbalance (family `orderflow`, style `flow`; default on, weight 0.5, live only)\
*Checks:* Resting bid size against ask size near the mid price.\
*Why included:* The catalogue's order-flow imbalance, in the only form that is observable (a live book snapshot).\
*Formula:* `(bid size - ask size) / (bid + ask) within depth_bps of mid, Hyperliquid L2`\
*Works when:* A liquid book with persistent one-sided depth. *Fails when:* Spoofing; a snapshot is not flow. Live only.

### 3.7 Positioning

**`funding`** — Funding rate (contrarian) (family `positioning`, style `derivatives`; default on, weight 0.5)\
*Checks:* Whether perpetual funding is above its usual level (longs paying, crowded) or below it.\
*Why included:* Catalogue funding input. Funding extremes mark crowding. Half weight: it is slow and often uninformative at 5m.\
*Formula:* `-tanh((funding_1h - baseline) / scale): longs paying above baseline is crowding, a mild down bias`\
*Works when:* Crowded positioning before a flush. *Fails when:* Funding can stay extreme for days.

**`premium`** — Perp premium vs oracle (contrarian) (family `positioning`, style `derivatives`; default on, weight 0.5, live only)\
*Checks:* The perp's mark price against its oracle: a stretched basis.\
*Why included:* Added: a cross-venue basis signal. Live only, because no venue serves its history.\
*Formula:* `-tanh(premium / scale), Hyperliquid mark vs oracle`\
*Works when:* Stretched basis. *Fails when:* Basis can trend; live only, cannot be backtested here.

**`oi_flow`** — Open-interest change x price (family `positioning`, style `derivatives`; default on, weight 0.5, live only)\
*Checks:* Whether open interest is rising with price (new positions) or falling (an unwind).\
*Why included:* Added: positioning change is a different kind of evidence from price. Live only.\
*Formula:* `rising OI confirms the price direction; falling OI (unwind) leans against it at 0.3x`\
*Works when:* New positioning behind a move. *Fails when:* Needs several forward ticks of OI history; live only.

### 3.8 Cross-asset and lifecycle

**`btc_lead`** — BTC lead (last bar) (family `cross-asset`, style `cross-asset`; default on, weight 0.5)\
*Checks:* BTC's move on the same closed bar, relative to BTC's normal move, as a lead for the altcoin.\
*Why included:* Added: majors move together and BTC often prints first.\
*Formula:* `tanh(BTC 5m log return / (scale * sigma_BTC)), same closed bar`\
*Works when:* Majors move together; BTC often prints first. *Fails when:* Idiosyncratic SOL news.

**`trend_lifecycle`** — Trend lifecycle stage (family `lifecycle`, style `lifecycle`; default on)\
*Checks:* How old and extended the current trend is: early trends are followed, exhausted ones are faded.\
*Why included:* Added from the catalogue's lifecycle concern: late-stage trends are where followers lose.\
*Formula:* `early (age <= early_bars): +dir; mature: +0.5*dir fading with extension; exhausted: -0.5*dir`\
*Works when:* Avoiding late-stage extensions the catalogue warns about. *Fails when:* Trends that keep extending.

**`cycle_phase`** — Market-cycle phase (Wyckoff-style) (family `lifecycle-cycle`, style `lifecycle`; default on, weight 0.5)\
*Checks:* A Wyckoff-style label for the last day (markup, markdown, accumulation, distribution) from slope and range.\
*Why included:* Added: a slow context read, half weight.\
*Formula:* `markup +0.6, markdown -0.6, accumulation +0.3, distribution -0.3, transition 0`\
*Works when:* Context for which side to favour at 5m. *Fails when:* Phase labels are descriptive, slow to turn.

### 3.9 Gates (veto, never vote)

**`gate_cost`** — Cost hurdle (family `gate`, style `gate`; default on)\
*Checks:* Whether the expected move over the holding period is large enough to pay the round-trip cost.\
*Why included:* Catalogue execution checklist step 2, and the most important item in the set: on this venue the round trip costs more than the average 5m move.\
*Formula:* `block when mean|r| * sqrt(hold_bars) < multiple * round-trip bps`\
*Works when:* Execution checklist step 2: expected move must clear fees, impact and slippage. *Fails when:* It blocks most 5m bars on SOL; that is the finding, not a bug.

**`gate_liquidation`** — Liquidation distance (family `gate`, style `gate`; default on)\
*Checks:* Whether a stop of `stop_atr` ATRs stays a safe fraction of the distance to liquidation at the chosen leverage.\
*Why included:* Catalogue 'risk first': a leveraged trade needs room to be wrong before liquidation.\
*Formula:* `block when stop_atr * ATR / price > max_fraction / leverage`\
*Works when:* Every leveraged trade. *Fails when:* Gaps jump through stops before execution.

**`gate_shock`** — Shock / unstable bar (family `gate`, style `gate`; default on)\
*Checks:* Whether the last bar's range or volume is far outside normal (an unscheduled-news proxy), with a cooldown.\
*Why included:* Catalogue regime table's no-trade state for unstable or news-driven bars.\
*Formula:* `block when range > range_mult * prior ATR or volume z > vol_z, plus cooldown bars`\
*Works when:* Unscheduled news proxy: the regime table's crowded/unstable no-trade state. *Fails when:* A shock that is the start of a clean trend is skipped.

**`gate_volume`** — Thin-market filter (family `gate`, style `gate`; default on)\
*Checks:* Whether recent volume has collapsed relative to its longer average.\
*Why included:* Added: signals built on thin volume are unreliable.\
*Formula:* `block when SMA(volume, short) < min_ratio * SMA(volume, long)`\
*Works when:* Thin liquidity makes 5m signals unreliable. *Fails when:* Quiet but orderly sessions.

**`gate_events`** — Scheduled-event blackout (family `gate`, style `gate`; default on)\
*Checks:* Whether a scheduled event (CPI, FOMC, an unlock) is close.\
*Why included:* Catalogue event risk: direction is a coin flip with fat tails around scheduled releases.\
*Formula:* `block within [event - before, event + after] for each event in the events file`\
*Works when:* CPI/FOMC/unlock windows where 5m direction is a coin flip with fat tails. *Fails when:* Only as good as the events file.

**`gate_session`** — Session filter (family `gate`, style `gate`; default off)\
*Checks:* Whether the current UTC hour (or a weekend) is on a blocked list.\
*Why included:* Thin hours widen costs. Off by default because the blocked hours must be measured, not assumed.\
*Formula:* `block in the UTC hours listed in blocked_hours (aggregate settings) and optionally weekends`\
*Works when:* Thin hours where spreads widen. *Fails when:* Hours are a guess unless measured.

**`gate_news`** — Headline risk (live) (family `gate`, style `gate`; default off, live only)\
*Checks:* Whether a headline naming the asset appeared in the last few minutes (live RSS).\
*Why included:* Catalogue immediate-news risk. Treated as risk, not as a predictor: headline sentiment is not scored because there is no timestamped archive to test it on.\
*Formula:* `block when a headline naming the asset appeared within window_min (live RSS read)`\
*Works when:* Headline-driven reversals. *Fails when:* Keyword match only; no sentiment is scored. Live only.

## 4. Tunable parameters

There are four layers, from the call as a whole down to one metric. Every parameter has a default and a bounded range, and cross-parameter mistakes (an EMA fast span not below the slow span, an upside-down Fibonacci zone) are refused when saved rather than discovered at scoring time. The saved configuration lives at `COMPOUND_STATE/config.json`; the **Compound 5m** tab edits it, and `compound.save` does the same from the CLI, API and extension host.

### 4.1 Aggregation

| Parameter | Default | Range | What it controls |
|---|---|---|---|
| `entry` | 0.25 | 0.01–1 | abs(composite) needed to call UP or DOWN |
| `exit` | 0.1 | 0.0–1 | a held position stays on while abs(composite) >= exit (same sign) |
| `min_coverage` | 0.5 | 0.0–1 | share of enabled weight that must be defined to call |
| `dedupe_families` | 1 | 0–1 | 1 = each family votes once |
| `regime_weighting` | 1 | 0–1 | 1 = scale styles by regime |
| `adx_period` | 14 | 2–100 | ADX lookback used to classify the regime |
| `trend_adx` | 25 | 5–80 | ADX at or above this is a trend regime |
| `range_adx` | 18 | 1–60 | ADX at or below this is a range regime |
| `squeeze_pct` | 15 | 1–50 | Bollinger bandwidth percentile that counts as a squeeze |
| `squeeze_lookback` | 288 | 20–5000 | bars over which that percentile is taken (288 = one day) |
| `allow_short` | 1 | 0–1 | 0 = long or flat only |
| `adaptive` | 1 | 0–1 | 1 = weight each metric by its own learned edge over a coin flip |
| `adaptive_prior` | 100 | 0–100000 | pseudo-calls at 50% every metric starts with; larger = slower to trust a streak |
| `adaptive_window` | 4032 | 12–1000000 | only calls from the last N bars count, so the record is capped; 4032 = two weeks of 5m |
| `adaptive_halflife` | 0 | 0–1000000 | 0 = every call in the window counts equally; N = calls also fade, counting half after N bars |
| `adaptive_flip` | 0 | 0–1 | 1 = invert a metric that is reliably WRONG instead of muting it |
| `tune` | 0 | 0–1 | 1 = each metric moves its numbers to a neighbouring setting once that neighbour is proving more accurate |
| `tune_confidence` | 0.95 | 0.5–0.9999 | posterior probability a neighbour must beat the current settings by before a move |
| `tune_min_calls` | 300 | 10–1000000 | decayed calls a neighbour needs before it can be adopted |
| `tune_step` | 0.25 | 0.05–1.0 | neighbours sit at x(1 - step) and x(1 + step) of each number |
| `tune_cooldown` | 576 | 1–1000000 | bars to wait after a move (576 = two days of 5m) |

Practical notes. `entry` and `exit` set how often the card trades: lowering `entry` to 0.15 roughly doubled the number of calls in the sweep and made results worse on every coin (section 6.3), because more calls means more round trips. `min_coverage` matters when live-only metrics are enabled: with them missing, a card that reads 40% of its weight is FLAT rather than a confident call from a minority of the evidence.

### 4.2 Regime multipliers

Weights are multiplied by these per (regime, style). A style not listed keeps 1.0.

| Regime | trend | momentum | reversion | breakout |
|---|---|---|---|---|
| trend | 1.5 | 1.3 | 0.3 | 1.0 |
| range | 0.5 | 0.6 | 1.5 | 0.6 |
| squeeze | 0.8 | 1.0 | 0.6 | 1.6 |
| neutral | 1.0 | 1.0 | 1.0 | 1.0 |

These come from the catalogue's regime table: continue in trends, fade in ranges, expect expansion out of compression. **Section 6.2 shows this table points the wrong way at the five-minute horizon in the data tested.** It is a tunable for that reason; `regime_weighting = 0` turns it off.

### 4.3 Execution

| Parameter | Default | Range | What it controls |
|---|---|---|---|
| `leverage` | 5.0 | 1.0–250.0 | perp leverage for P&L and the liquidation gate |
| `fee_bps` | 6.0 | 0.0–100.0 | per side; Jupiter base fee 0.06% |
| `slippage_bps` | 2.0 | 0.0–100.0 | per side; Jupiter impact floor 1 bp + adverse execution |

Leverage does not change which direction is called, only the size of the outcome and the liquidation gate's distance: the same calls at 1x, 5x and 20x lose about 11%, 43% and 86% on average (section 6.3). Fees and slippage are per side and are applied by the engine's perp cost model, together with borrow and liquidation.

### 4.4 Per-metric parameters and weights

Each metric has its own parameters (Appendix A), an `enabled` flag and a `weight`. Three guidance points. The first is reasoning from how the card works; the other two follow from the sweep's design:

* **Hold-related parameters probably matter more than indicator periods (reasoning, not a sweep finding).** `gate_cost.hold_bars` and the `hold` parameters of `donchian`, `squeeze`, `trend_continuation` and `liquidity_sweep` decide how many bars one round trip is spread over. A 5-minute call pays 16 bps whether it holds one bar or ten.
* **Do not tune on the held-out slice.** The sweep reports how many configurations have been scored on that exact out-of-sample window across all runs (the multiple-testing denominator). Every additional run on the same window spends it again.
* **Disabling a metric is a stronger move than re-tuning it.** Family de-duplication already stops redundant metrics from stacking; enabling more oscillators adds votes, not information.

### 4.5 Learned weights and evidence-gated tuning

With `adaptive = 1` a metric "calls" a bar when its absolute score reaches `entry`; once the next bar closes, the call is right or wrong. Each metric's hit probability has a Beta prior of `adaptive_prior / 2` right and `adaptive_prior / 2` wrong pseudo-calls (50 and 50 by default) and is updated by every resolved call. The weight multiplier is **2 x hit - 1**: zero at 50%, so a metric with no demonstrated skill gets no say, rather than a metric at 55% and one at 47% differing only slightly. A metric that is reliably wrong is muted, or inverted with `adaptive_flip = 1`.

* **Why a cap.** Only calls inside the last `adaptive_window` bars count (4,032, two weeks of 5m). Without a cap, five months of history would make each new miss move a weight by a meaningless amount; with it, a miss moves a weight as much in month five as in week two, and a metric that stops working loses its weight within two weeks. `adaptive_halflife` optionally fades calls inside the window (off by default).
* **No look-ahead.** A call at bar *t* is counted only after bar *t+1* has closed; the prefix-invariance test runs with adaptive weighting on.
* **Tuning (`tune = 1`, off by default).** Each metric also runs shadow copies at x(1 - `tune_step`) and x(1 + `tune_step`) of each number, and moves to a neighbour only when the posterior says it is more accurate with probability above `tune_confidence` (0.95) after `tune_min_calls` (300) calls, then waits `tune_cooldown` bars (576, two days). Moving after every miss would chase noise, because about half of all 5m outcomes are coin flips.

The tunable parameters are in section 4.1: `adaptive`, `adaptive_prior`, `adaptive_window`, `adaptive_halflife`, `adaptive_flip`, `tune`, `tune_confidence`, `tune_min_calls`, `tune_step`, `tune_cooldown`.

## 5. Evaluation protocol

* **Data.** The study’s “30-day” label covers 2026-07-06 00:00 to 2026-08-06 00:00 UTC (31 elapsed calendar days) of 5-minute bars (8,927 to 8,929 bars per coin). SOL is native 5m; BTC, ETH, DOGE and ZEC are aggregated from 1-minute bars. All are Coinbase series.
* **Split.** First 70% in-sample, last 30% out-of-sample (2,678 bars per coin, from 2026-07-27 16:50 UTC). The descriptive rankings use the last split, so that repeatedly inspected split is not an untouched final confirmation.
* **Costs.** 6 bps fee plus 2 bps slippage per side, 16 bps per round trip, applied to every fill.
* **Forecast statistics** (per configuration, per split): hit rate among calls, a z-score against a coin flip (standard errors from 50%), gross and net basis points per call if held one bar, calibration (up-rate by composite bucket), and the **oracle**: mean absolute close-to-close log return over every time-selected transition minus a fixed round-trip cost. The oracle includes no-call periods and ties, ignores call coverage, and does not model next-open execution or liquidation paths.
* **Engine statistics:** total return, drawdown, trades, time in market, fees, borrow and liquidations, from the repository's backtest engine with the leveraged perp cost model.
* **Weights in the saved sweep.** Static (`adaptive` absent, equivalent to 0): the sweep predates learned weights. Section 6.6 reports the learned-weight comparison, taken from `docs/COMPOUND-5M.md` and not recomputed here.
* **Configurations.** 284 labels per coin (each metric alone at its defaults, then one-parameter perturbations, then the compound and eight variants of it), 1,420 rows in total.

## 6. Results so far

### 6.1 The all-bars diagnostic is negative in this thirty-day sample


| | BTC | DOGE | ETH | SOL | ZEC |
|---|---|---|---|---|---|
| mean absolute 5m move (bps) | 6.2 | 8.7 | 8.6 | 8.5 | 15.6 |
| net per one-bar trade if always right (bps) | -9.8 | -7.3 | -7.4 | -7.5 | -0.4 |
| out-of-sample share of up bars | 48.7% | 47.0% | 48.7% | 45.6% | 48.8% |

At the assumed 16 bps round-trip cost, this direction-perfect, close-to-close average is
negative on all five coins, including ZEC. `forecast_stats.oracle_net_bps` averages every
time-selected transition, including FLAT/no-call periods and ties. It does not condition
on a strategy's selected events. A negative all-bars average therefore cannot rule out a
selective one-bar policy with different conditional outcomes. Holding through several bars
is another way to amortize the toll; neither possibility is validated by this diagnostic.
Actual next-open fills, costs and intrabar survival must be evaluated for the selected
policy. See `research/five-minute-perps-suite/benchmark-scope-review.json` for the reviewed
metric definition and a synthetic counterexample. These figures retain their historical
sample and configured costs; they are not live venue quotes.

### 6.2 Which metrics have any directional information

Out-of-sample hit rate of each metric alone at its defaults, with its z-score in parentheses (standard errors from 50%; |z| below about 2 is not distinguishable from chance on one coin). `n/a` means the metric had no defined calls (funding history exists only for some coins; `btc_lead` cannot score BTC itself).


| Metric | Family | BTC | DOGE | ETH | SOL | ZEC | Mean hit |
|---|---|---|---|---|---|---|---|
| `rsi` | oscillator | 51.3% (+1.1) | 56.5% (+5.1) | 51.5% (+1.3) | 51.4% (+1.2) | 52.0% (+1.7) | 52.6% |
| `zscore` | bands | 51.7% (+1.5) | 55.3% (+4.6) | 51.8% (+1.6) | 51.3% (+1.2) | 51.8% (+1.6) | 52.4% |
| `bollinger` | bands | 51.0% (+0.9) | 54.5% (+4.0) | 52.4% (+2.1) | 50.8% (+0.7) | 52.0% (+1.8) | 52.1% |
| `stochastic` | oscillator | 50.8% (+0.7) | 53.9% (+3.4) | 52.6% (+2.4) | 50.3% (+0.3) | 51.9% (+1.8) | 51.9% |
| `liquidity_sweep` | structure | 52.8% (+1.2) | 54.5% (+1.6) | 49.2% (-0.3) | 52.9% (+1.1) | 49.2% (-0.3) | 51.7% |
| `cycle_phase` | lifecycle-cycle | 51.3% (+1.2) | 52.5% (+2.0) | 50.7% (+0.6) | 51.6% (+1.4) | 50.8% (+0.7) | 51.4% |
| `persistence` | autocorrelation | 50.8% (+0.7) | 48.3% (-1.4) | 50.5% (+0.4) | 50.2% (+0.1) | 50.0% (-0.0) | 49.9% |
| `money_flow` | volume-flow | 50.6% (+0.5) | 48.0% (-1.8) | 50.2% (+0.2) | 47.9% (-1.8) | 49.5% (-0.5) | 49.2% |
| `trend_lifecycle` | lifecycle | 49.8% (-0.2) | 47.3% (-2.5) | 50.0% (+0.0) | 50.1% (+0.1) | 48.8% (-1.2) | 49.2% |
| `vwap_side` | vwap | 49.9% (-0.1) | 48.2% (-1.8) | 49.5% (-0.5) | 48.8% (-1.1) | 48.2% (-1.8) | 48.9% |
| `btc_lead` | cross-asset | n/a | 48.9% (-0.8) | 47.9% (-1.5) | 48.9% (-0.8) | 49.0% (-0.7) | 48.7% |
| `funding` | positioning | 45.8% (-1.5) | n/a | 52.9% (+1.2) | 47.1% (-1.4) | n/a | 48.6% |
| `macd` | ma-trend | 48.7% (-1.2) | 47.3% (-2.4) | 48.2% (-1.6) | 49.8% (-0.2) | 48.9% (-1.0) | 48.6% |
| `obv` | volume-flow | 48.9% (-1.0) | 46.9% (-2.7) | 48.8% (-1.1) | 49.3% (-0.6) | 48.2% (-1.6) | 48.4% |
| `roc` | momentum | 48.1% (-1.7) | 46.4% (-3.1) | 47.6% (-2.1) | 49.8% (-0.2) | 49.9% (-0.1) | 48.3% |
| `ema_cross` | ma-trend | 48.7% (-1.2) | 45.8% (-3.9) | 48.6% (-1.4) | 48.5% (-1.4) | 48.0% (-1.9) | 47.9% |
| `htf_trend` | higher-timeframe | 47.9% (-2.0) | 47.2% (-2.6) | 47.8% (-2.0) | 46.6% (-3.2) | 49.2% (-0.7) | 47.8% |
| `donchian` | breakout | 50.8% (+0.4) | 45.2% (-2.3) | 44.7% (-2.5) | 47.2% (-1.3) | 50.2% (+0.1) | 47.6% |
| `adx_dmi` | directional | 48.2% (-1.2) | 46.2% (-1.9) | 48.0% (-1.3) | 46.6% (-1.9) | 47.6% (-1.3) | 47.3% |
| `trend_continuation` | composite-rule | 48.5% (-0.8) | 44.5% (-3.0) | 45.9% (-2.4) | 46.4% (-2.0) | 50.7% (+0.4) | 47.2% |
| `squeeze` | volatility | 53.9% (+1.0) | 39.6% (-2.6) | 40.1% (-2.4) | 45.6% (-1.1) | 49.7% (-0.1) | 45.8% |

**The pattern.** Four counter-trend metrics (`rsi`, `zscore`, `bollinger`, `stochastic`) are above 50% on all five coins, with `rsi` on DOGE at 56.5% (z = +5.1) and `zscore` at 55.3% (z = +4.6). The trend metrics (`ema_cross`, `htf_trend`, `trend_continuation`, `adx_dmi`, `roc`, `macd`, `obv`) are below 50% on nearly every coin, `htf_trend` and `ema_cross` significantly so on several. At this horizon, in this window, fading the last move was weakly right and following it was weakly wrong. The same sign appears in-sample (RSI 51.6 to 54.4%, EMA cross 46.9 to 48.2%), which is consistent with one regime rather than with a real edge. The catalogue's regime table (more weight on trend metrics in trends) therefore pushes the default compound toward the metrics that did worst.

### 6.3 The compound and its variants

Static weights, out-of-sample, mean across the five coins (the "best coin" column is the highest single return; every value is negative).


| Configuration | Mean hit rate | Calls per coin | Trades per coin | Mean OOS return | Best coin |
|---|---|---|---|---|---|
| compound (static weights, other defaults) | 46.6% | 328 | 165 | -43.5% | -16.8% |
| compound, regime_weighting=0 | 44.3% | 172 | 142 | -40.3% | -18.8% |
| compound, dedupe_families=0 | 46.2% | 274 | 154 | -38.6% | -11.3% |
| compound, entry=0.15 | 47.3% | 544 | 231 | -57.7% | -27.7% |
| compound, entry=0.35 | 45.0% | 159 | 130 | -35.6% | -13.2% |
| compound, entry=0.5 | 38.9% | 32 | 67 | -20.1% | -6.8% |
| compound, no-gates | 46.9% | 879 | 332 | -65.9% | -56.4% |
| compound, leverage=1 | 46.6% | 328 | 315 | -11.1% | -3.6% |
| compound, leverage=20 | 46.6% | 328 | 165 | -85.6% | -53.3% |

Readings. (1) Every variant lost money on every coin. (2) Turning regime weighting off moved the mean return only from -43% to -40% while lowering the hit rate (46.6% to 44.3%): no clear effect, which fits a mis-signed multiplier table sitting on top of weak metrics. (3) **Removing the gates made things much worse** (-66% mean against -43%): the cost and shock gates are doing real work by refusing bars, and 'no-gates' is the configuration most like an unfiltered trader. (4) Raising `entry` reduces trading and loses less (-20% at 0.5), which is a statement about cost drag, not about accuracy: at `entry` 0.5 the hit rate fell to 38.9% on 32 calls per coin. (5) Higher leverage deepens losses in these saved variants: the identical 328 calls per coin cost 11% at 1x, 43% at 5x and 86% at 20x.

### 6.4 The 10 positive configurations

Ten of 1,420 had a positive out-of-sample return: four `funding` variants, three `adx_dmi` variants, two `htf_trend` variants on ZEC and one `squeeze` variant. Nine of the ten had hit rates between 48% and 53% (the exception is a `squeeze` row with three calls), all had z-scores within 1.2 of a coin flip, and **seven of the ten lost in-sample**. The extensive search and weak directional statistics make selection bias plausible; no calibrated null calculation establishes that luck should produce exactly ten winners. None is qualified for promotion.

### 6.5 Calibration

Calibration asks whether a stronger composite means a higher chance of an up bar. For BTC's default compound, out-of-sample:


| Composite bucket | Bars | Share up |
|---|---|---|
| -1.00 to -0.50 | 77 | 49.4% |
| -0.50 to -0.25 | 371 | 48.5% |
| -0.25 to -0.10 | 427 | 49.4% |
| -0.10 to +0.10 | 795 | 49.2% |
| +0.10 to +0.25 | 502 | 50.6% |
| +0.25 to +0.50 | 433 | 46.9% |
| +0.50 to +1.00 | 70 | 40.0% |

The share of up bars is between 47% and 51% in every bucket except the last, and is **lowest (40%) in the strongest-positive bucket** (70 bars, too few to read). A well-calibrated scorecard would show up-rate rising with the composite; this one does not.

### 6.6 Learned weights

From `docs/COMPOUND-5M.md`, measured on the same 30 days and not recomputed here: out-of-sample hit rate of the default compound.

| | BTC | DOGE | ETH | SOL | ZEC |
|---|---|---|---|---|---|
| static weights (`adaptive = 0`) | 48.5% | 44.0% | 45.6% | 46.3% | 48.9% |
| learned weights (`adaptive = 1`, two-week record) | 46.5% | 55.6% | 52.0% | 50.2% | 51.6% |
| learned plus tuning at 0.65 confidence / 50 calls | 47.4% | 56.2% | 53.4% | 52.1% | 51.4% |

Learning fixes the direction problem on four of five coins: it mutes the trend metrics and leans on reversion without anyone choosing. Tuning at the default 0.95 bar moved one metric once across five coins and 30 days: neighbouring settings are nearly the same signal, so the data rarely proves one better. A looser bar moves the hit rate by about a point either way, inside the noise, and several bars were tried, which is itself selection; tuning therefore stays off by default. **Returns stayed negative in every row.** A better hit rate does not beat a 16 bps round trip on a 6 to 9 bps move. Note the caveat that applies to every learned row: the weights were learned from the same 30 days they are measured on (each call uses only the record before it), so this is a within-sample adaptation test, not a held-out one.

### 6.7 Forward testing and the full suite

The forward tester exists (one call per closed 5-minute bar, resolved when the next bar closes, written to `COMPOUND_STATE/forward/<ASSET>.jsonl`). **At the study snapshot, the author recorded no forward ledger on the study machine**, so there is no live out-of-sample evidence at all. The full suite (`research/full_suite.py`: a year of 5-minute data for the universe, then every registry and compound backtest) has not been run to completion. Both are required before any of section 6 is more than a 30-day observation. The author’s November 7 progress notes said live SOL calls showed learned weights and gave weight only to the reversion metrics (from the project's progress notes; not re-verified for this paper).

## 7. Threats to validity

1. **One regime.** Thirty days is one market. The reversion pattern could vanish, or invert, in a trending month.
2. **Multiple testing.** 1,420 configurations were scored on one 30-day window, and the saved file contains the identical sweep twice (two run ids, same configuration hashes), which must not be counted as 2,840 independent trials. Every new run ranked on the same out-of-sample slice spends it again; the tool reports the cumulative count per window.
3. **Overlapping calls.** Calls on consecutive bars share information, so z-scores overstate independence. The reported z-scores use an independence approximation and no search correction; they do not establish adjusted significance, and the direction or size of a dependence correction was not estimated.
4. **Possible bid-ask bounce.** These are Coinbase closes, which alternate between bid and ask prints and create negative autocorrelation that cannot be traded. Jupiter fills at the oracle price, which has no bounce. If part of the reversion edge is bounce, it is not capturable at the venue the cost model assumes. This is a hypothesis, not a measurement; it has not been tested against oracle-priced bars.
5. **Aggregated bars.** Four of five coins are built from 1-minute bars, which could differ subtly from native 5-minute bars.
6. **Costs are assumed.** The 16 bps round trip is a configured fee and slippage proxy, not a current executable venue quote; the repository's cost model does not include price-impact fees, keeper latency or priority fees, each of which makes results worse.
7. **Metrics not testable here.** `premium`, `oi_flow`, `book_imbalance` and `gate_news` need live data; funding history covers only some coins. Their value is unmeasured, not zero.
8. **Hit rate is not profit.** Profit depends on win and loss magnitudes, execution costs and survival before exit. A profitable policy can win fewer than half its trades with asymmetric payoffs. The negative unconditional oracle average does not rule out selective one-bar calls or require a longer holding period; those alternatives need separate conditional expectancy and path tests.

## 8. Conclusions and next steps

What has been established: the machinery is causal (prefix-invariance tested), the costs are explicit, the gates measurably reduce losses, and the catalogue's regime guidance does not hold in this sample. Learned weights recover the reversion tilt automatically, which supports building the next step on the metrics' own track records rather than on the catalogue's regime table. What has **not** been established is any profitable configuration. The honest status is "no evidence of edge; weak evidence of short-horizon mean reversion in oscillators on one 30-day window".

In order of value:

1. Run the forward tester unattended on SOL so that evidence accrues on data the sweeps never saw (`python3 -m soltui.compound forward --asset SOL --loop`).
2. Run `research/full_suite.py` for a year of 5-minute data and re-test the reversion pattern across regimes before reading anything into it.
3. Test the reversion effect on oracle-priced bars, or against bid and ask, to separate bounce from signal.
4. Evaluate holding periods of several bars (the cost-gate path) rather than one-bar calls, scored by net basis points over the hold.
5. Treat any configuration that passes as a hypothesis for the registry's CPCV and deflated-Sharpe machinery, not as a result.

## Appendix A. Parameter reference

Defaults and bounds are those recorded at the historical snapshot, except explicitly marked later additions. Ranges are inclusive. A parameter's range is the refusal boundary when a configuration is saved.

| Metric | Parameters (default, min–max) |
|---|---|
| `ema_cross` | `fast` 9 (2–200); `slow` 21 (3–400); `scale` 0.5 (0.05–10); `atr` 14 (2–200) |
| `macd` | `fast` 12 (2–200); `slow` 26 (3–400); `signal` 9 (2–100); `scale` 0.25 (0.01–10); `atr` 14 (2–200) |
| `adx_dmi` | `period` 14 (2–100); `threshold` 20 (5–60) |
| `vwap_side` | `mode` 0 (0–1); `window` 48 (5–2000); `spread_window` 288 (20–5000, added later); `scale` 1.0 (0.05–10); `atr` 14 (2–200) |
| `htf_trend` | `tf_minutes` 60 (10–1440); `span` 20 (2–200); `scale` 1.0 (0.05–10); `atr` 14 (2–200) |
| `ichimoku` | `tenkan` 9 (2–100); `kijun` 26 (3–200); `senkou` 52 (4–400) |
| `roc` | `window` 12 (1–500); `vol_window` 96 (10–2000); `scale` 1.0 (0.05–10) |
| `persistence` | `window` 96 (10–2000); `gain` 5.0 (0.5–50) |
| `rsi` | `period` 14 (2–200); `oversold` 30 (1–49); `overbought` 70 (51–99); `mode` 0 (0–1) |
| `stochastic` | `k` 14 (2–200); `d` 3 (1–50); `oversold` 20 (1–49) |
| `cci` | `period` 20 (2–200); `extreme` 150 (50–400) |
| `bollinger` | `window` 20 (2–500); `k` 2.0 (0.5–5) |
| `zscore` | `window` 48 (5–2000); `entry` 2.0 (0.5–5) |
| `vwap_reversion` | `mode` 0 (0–1); `window` 48 (5–2000); `spread_window` 288 (20–5000, added later); `stretch` 2.0 (0.2–10); `atr` 14 (2–200) |
| `donchian` | `window` 20 (2–500); `hold` 3 (1–50) |
| `squeeze` | `window` 20 (5–500); `k` 2.0 (0.5–5); `lookback` 288 (20–5000); `squeeze_pct` 20 (1–50); `recent` 6 (1–100); `vol_mult` 1.5 (0.5–10); `hold` 3 (1–50) |
| `trend_continuation` | `fast` 9 (2–200); `slow` 21 (3–400); `vol_window` 20 (2–500); `vol_mult` 1.2 (0.5–10); `hold` 2 (1–50) |
| `liquidity_sweep` | `lookback` 24 (3–500); `hold` 2 (1–50) |
| `fib_pullback` | `swing` 48 (5–2000); `trend` 50 (5–1000); `zone_lo` 0.382 (0.1–0.9); `zone_hi` 0.618 (0.15–0.95) |
| `obv` | `window` 20 (2–500); `scale` 1.0 (0.05–10) |
| `money_flow` | `window` 20 (2–500); `scale` 0.25 (0.02–1) |
| `book_imbalance` | `depth_bps` 10 (1–200); `scale` 0.5 (0.05–1) |
| `funding` | `scale_bps` 0.5 (0.05–50); `baseline_bps` 0.125 (-5–5) |
| `premium` | `scale_bps` 5.0 (0.5–100) |
| `oi_flow` | `minutes` 15 (5–240); `scale_pct` 0.5 (0.05–10) |
| `btc_lead` | `vol_window` 96 (10–2000); `scale` 2.0 (0.1–20) |
| `trend_lifecycle` | `fast` 9 (2–200); `slow` 21 (3–400); `early_bars` 12 (1–500); `exhausted_atr` 3.0 (0.5–20); `atr` 14 (2–200) |
| `cycle_phase` | `window` 288 (24–10000); `slope_bars` 48 (2–2000); `flat_pct` 0.5 (0.01–10) |
| `gate_cost` | `window` 48 (5–2000); `hold_bars` 3 (1–100); `multiple` 1.0 (0.1–10) |
| `gate_liquidation` | `stop_atr` 1.5 (0.2–20); `max_fraction` 0.5 (0.05–1); `atr` 14 (2–200) |
| `gate_shock` | `range_mult` 3.0 (1–20); `vol_z` 4.0 (1–20); `vol_window` 96 (10–2000); `cooldown` 3 (0–100); `atr` 14 (2–200) |
| `gate_volume` | `short` 12 (1–500); `long` 288 (10–10000); `min_ratio` 0.3 (0.01–2) |
| `gate_events` | `before_min` 15 (0–1440); `after_min` 30 (0–1440) |
| `gate_session` | `weekend` 0 (0–1) |
| `gate_news` | `window_min` 30 (5–1440) |

## Appendix B. Reproducing this

```bash
# the sweep behind section 6 (about 1,420 configurations; needs the cached 30-day bars).
# The saved rows used static weights; since adaptive weights became the default, add the
# aggregate setting adaptive=0 to reproduce them.
"$STUDY_PYTHON" -m soltui.compound sweep --perturb --aggregate-grid

# one live call with every metric explained (public data, no keys, no orders)
"$STUDY_PYTHON" -m soltui.compound signal --asset SOL

# forward test, one call per closed bar
"$STUDY_PYTHON" -m soltui.compound forward --asset SOL --loop
"$STUDY_PYTHON" -m soltui.compound status --asset SOL

# a year of 5m data and every backtest
"$STUDY_PYTHON" research/full_suite.py --plan
```

Run id behind the tables: `20261107T130441Z-f7fea5b2368e` (rows in `COMPOUND_STATE/backtests.jsonl`, which holds the same sweep twice). Related documents: `docs/COMPOUND-5M.md` (user guide), `docs/short-horizon-leverage-concept-family.md` (venue economics), `research/RANKED_LISTS.md` (registry strategies).

### Historical evidence availability

The original table-generation scratch script was not committed. The saved sweep ledger and study implementation are required to reconstruct the tables; this publication is not a self-contained replication package. “Works when” entries explain the catalogue’s intended mechanism, not independently demonstrated conditional profit. The displayed costs and venue mechanics retain the original study assumptions. Reproduction and unattended-training commands below describe separate operations requiring that study package; none ran during publication review.

Publication note: `RESEARCH_ARCHIVE`, `SERVICE_HOME` and `COMPOUND_STATE` denote the original retained study archives or state directories. `$STUDY_REPO`, `$STUDY_PYTHON` and `$MARKET_DATA_DIR`, where shown, must point to the matching study checkout, environment and data. These private artifacts are not bundled with this article. Historical acceptance statements above describe the original study; publication review did not rerun experiments or operate services.
