---
title: "Does ZEC show a recurring chart frequency?"
description: "Does ZEC show a recurring chart frequency?. An edited historical research report with its original evidence limits retained."
date: "2026-11-29"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

# Does ZEC have a recurring chart frequency?

As of 2026-11-11. The observed day is **2026-11-10, America/New_York**. The exact original chart
timeframe/venue was not supplied; this study checks Coinbase ZEC-USD at 1m, 5m, 15m and 1h.

**A local rhythm is visible, but a stable coin-specific clock is not validated.** On the 15m close
chart, a fixed 2% reversal rule found five intervals between larger alternating turns with a median
of 270 minutes (4.5 hours). That is a **peak-to-dip half-cycle**, not peak-to-peak frequency. It would
suggest about nine hours for a full cycle, leaving fewer than three full cycles in one day. That small,
threshold-dependent observation is insufficient to establish regularity or future turning times.
Four of those five alternating gaps were 270–285 minutes; the other was 120 minutes.

![ZEC on 2026-11-10: exploratory rhythm, spectral controls and frozen historical forecasts](/downloads/research/zec-cycle-validation/zec_cycles_20261111_yesterday.png)

## What the tests say

Across 50 declared price/return tests, **0 survive the family-wise correction**.
Yesterday's strongest admissible price period is six hours on 1m, 5m and 15m data. It hits the upper
edge of a search requiring at least four cycles per window; it is not an identified natural frequency.
Even before the across-window correction, no-clock paths routinely produce a peak at least this strong.
This rejects neither every possible slow cycle nor adaptive stochastic oscillation. It fails to validate
a fixed clock within the specified search band.
The prior-week scan includes slower periods: its strongest price wavelength was about 18.7 hours,
also far below the no-clock threshold. That scan did not support a stable nine-hour rhythm either.

| Meaning | Interpretation |
| --- | --- |
| Full period | Peak-to-peak or dip-to-dip spacing |
| Half-period | Alternating peak-to-dip spacing for a symmetric oscillation |
| Local wavelength | A temporarily prominent rhythm; can change with time and scale |
| Stable clock | Period and phase selected earlier continue to predict later observations |

### Yesterday's search-aware results

Periods are minutes. `power` is the fraction of detrended variation explained by one harmonic.
`p_conservative` takes the larger of two no-clock p-values. `p_holm` adjusts every eligible
window/timeframe/series test together. These are not the probability that a cycle exists.

| interval | series | period_minutes | power | p_random_sign | p_block_permutation | p_conservative | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1m | log_price | 360.00 | 0.10 | 0.38 | 0.36 | 0.38 | 1.00 |
| 1m | log_return | 62.61 | 0.01 | 0.63 | 0.83 | 0.83 | 1.00 |
| 5m | log_price | 360.00 | 0.10 | 0.39 | 0.33 | 0.39 | 1.00 |
| 5m | log_return | 62.61 | 0.03 | 0.32 | 0.71 | 0.71 | 1.00 |
| 15m | log_price | 360.00 | 0.10 | 0.37 | 0.35 | 0.37 | 1.00 |
| 15m | log_return | 205.71 | 0.07 | 0.25 | 0.77 | 0.77 | 1.00 |

The hourly chart has only 24 observations yesterday and fails the declared 48-observation floor.
It remains in the longer-window and prediction comparisons. The three finer charts are resolutions
of the same market, not three independent confirmations.

## Are the turns equally spaced?

Turns are amplitude-defined directional changes at fixed 1% and 2% **log-price** reversal thresholds.
No minimum time separation is imposed. A pivot is shown at its actual extreme only retrospectively;
the saved `confirmed_at` records when a reversal made it knowable. Thresholds were fixed before results.
`cv` is interval standard deviation divided by its mean: zero means exactly equal intervals.
The 1m 1% peak spacing has a median of 73 minutes, but its middle half spans 49–114 minutes.
The 15m 2% alternating spacing has a 270-minute median and a 270–285-minute middle half, on only five intervals.
These different answers show why chart zoom and what counts as a meaningful swing matter.

The table's random-sign CV reference uses the first 199 surrogate paths. It is descriptive, not a
multiple-comparison-adjusted peak-spacing test. Rows with too few intervals are absent; reference
paths with too few intervals are also omitted. Do not interpret a reference quantile as significance.

| interval | threshold | kind | intervals | median_minutes | q25_minutes | q75_minutes | cv | null_cv_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1m | 0.01 | peak | 17 | 73.00 | 49.00 | 114.00 | 0.61 | 0.86 |
| 1m | 0.01 | dip | 17 | 76.00 | 46.00 | 110.00 | 0.64 | 0.84 |
| 1m | 0.01 | alternating | 35 | 26.00 | 15.00 | 59.50 | 0.84 | 1.14 |
| 1m | 0.02 | peak | 6 | 161.00 | 99.25 | 230.25 | 0.82 | 0.85 |
| 1m | 0.02 | dip | 5 | 147.00 | 51.00 | 347.00 | 0.85 | 0.78 |
| 1m | 0.02 | alternating | 12 | 78.00 | 32.75 | 152.25 | 0.90 | 1.14 |
| 5m | 0.01 | peak | 7 | 115.00 | 77.50 | 210.00 | 0.96 | 0.81 |
| 5m | 0.01 | dip | 8 | 107.50 | 73.75 | 300.00 | 0.74 | 0.77 |
| 5m | 0.01 | alternating | 16 | 55.00 | 32.50 | 81.25 | 1.05 | 1.07 |
| 5m | 0.02 | peak | 4 | 272.50 | 208.75 | 386.25 | 0.52 | 0.83 |
| 5m | 0.02 | dip | 3 | 395.00 | 280.00 | 397.50 | 0.42 | 0.73 |
| 5m | 0.02 | alternating | 8 | 120.00 | 95.00 | 265.00 | 0.59 | 1.09 |
| 15m | 0.01 | peak | 5 | 180.00 | 165.00 | 330.00 | 0.74 | 0.63 |
| 15m | 0.01 | dip | 4 | 240.00 | 86.25 | 393.75 | 0.76 | 0.62 |
| 15m | 0.01 | alternating | 10 | 90.00 | 48.75 | 232.50 | 0.82 | 0.94 |
| 15m | 0.02 | alternating | 5 | 270.00 | 270.00 | 285.00 | 0.29 | 0.98 |

## Does a cycle identified earlier predict later prices?

Each fold uses the preceding three elapsed days to select a period, fit phase/amplitude and linear
trend, then freezes all coefficients before the next disjoint six-hour window. There is no within-test
phase refitting. Compare it with an earlier-fitted linear trend and simply retaining the last observed
price. There are 29 windows per resolution, ending at 2026-11-11 06:00 America/New_York.
Earlier test observations can become training history for a later fold. This is historical replay,
not a prospective trial or profit backtest. It tests this fixed harmonic model, not every cycle model.

Ratios below one improve on the comparator; ratios above one worsen its mean squared log-price error.

| interval | folds | cycle_vs_last_price_mse | cycle_vs_linear_mse | beats_last_price | beats_linear |
| --- | --- | --- | --- | --- | --- |
| 15m | 29 | 4.53 | 1.16 | 6 | 8 |
| 1h | 29 | 3.85 | 1.16 | 7 | 10 |
| 1m | 29 | 4.60 | 1.14 | 6 | 9 |
| 5m | 29 | 4.54 | 1.14 | 6 | 9 |

At 5m, the cycle forecast beats last-price persistence on only 6/29 windows, and its aggregate error
is about 4.54 times larger. It is also worse than extrapolating the earlier linear trend. That gives
no support for scheduling trades from an unchanged period and phase. No trading rule or P&L is inferred.

![Changing wavelengths and future prediction errors](/downloads/research/zec-cycle-validation/zec_cycles_20261111_stability.png)

## Methods, data and limits

- Public native Coinbase Exchange ZEC-USD 1m/5m/15m/1h candles were fetched for 2026-10-20 through
  2026-11-11 11:40 UTC. Only candles completed by the fixed cutoff are analyzed. Raw hashes and exact
  coverage are retained. The minute feed has 119 timestamp gaps overall and four missing candles yesterday.
- Use actual timestamps in nested harmonic regression. Both price and sine/cosine bases are residualized
  against intercept and linear trend. No interpolation or synthetic zero-return candle fills a gap.
  Native larger candles are independent venue aggregates; they need not contain a trade in every minute.
- Frequency candidates are up to 128 unique log-spaced Fourier indices from four cycles/window to six
  bars/cycle. Daily eligible ranges are 6min–6h at 1m, 30min–6h at 5m and 90min–6h at 15m. The prior-week
  analysis admits longer cycles. A daily result at the six-hour boundary deserves extra caution.
- The declared family includes seven calendar days ending yesterday and a prior-seven-day aggregate,
  four resolutions and both detrended log prices and log returns. At least 48 observations and 95%
  expected coverage are required. Holm correction permits dependent windows; it does not make them independent.
- Each of two null models has 1,999 replicates. Random signs preserve centered return magnitudes and
  their temporal volatility pattern. Permuting blocks of up to four returns preserves short local sequences but
  rearranges their order. Both nulls retain the actual sample timestamps. Each replicate repeats the
  complete frequency search. Empirical upper-tail p-values use the plus-one correction.
- These are two specified no-clock null models, not an exhaustive model of crypto markets. Stronger
  long-memory processes, changing regimes and market-wide effects remain possible. One coin cannot
  establish that any rhythm is intrinsic to it. Longer cycles need more elapsed history.
- Yesterday was selected because the owner noticed a pattern. This is an exploratory check of that
  observation, not an untouched confirmatory sample. Threshold/timeframe choices must remain visible.
- No live services, Oracle policy, paper accounts or protected holdout reservations were changed.

## Verification and reproduction

The original study records eight unit tests that recover a known clock despite missing observations, compare the spectrum with independent
nested regression, reject linear-trend artifacts, verify Holm adjustment and surrogate properties, and
prove pivot-confirmation and forecast causality. A separate fixed-seed calibration rejected 0/50 Gaussian
random-walk controls at the unadjusted 5% level. That small calibration is a sanity check, not a size guarantee.
NumPy/pandas/matplotlib run in an isolated environment; Endor package-risk tooling was unavailable, so no
package-security verdict is claimed. Context7 was unavailable because its API key was rejected.

From the repository root, use a fresh output directory:

```bash
python -m unittest research.tests.test_zec_cycles -v
python -m research.zec_cycles --input-dir RESEARCH_ARCHIVE/zec-cycles-20261111/input --output RESEARCH_ARCHIVE/zec-cycles-20261111/reproduction
```

The primary run is `RESEARCH_ARCHIVE/zec-cycles-20261111/run-v1`.
Its manifest inventories every input/output hash. Compact tests, spacing, forecasts, coverage, pivots,
plots and manifest are committed under `research/results/zec_cycles_20261111_*`.
The related shape study remains separate: `research/SHAPE-AWARE-SPOT.md` and the retained evidence review.
A cycle detector or Ehlers autocorrelation indicator can describe
changing wavelengths; its existence does not establish that an apparent wavelength predicts the next turn.

Publication note: `RESEARCH_ARCHIVE`, `SERVICE_HOME` and `COMPOUND_STATE` denote the original retained study archives or state directories. `$STUDY_REPO`, `$STUDY_PYTHON` and `$MARKET_DATA_DIR`, where shown, must point to the matching study checkout, environment and data. These private artifacts are not bundled with this article. Historical acceptance statements above describe the original study; publication review did not rerun experiments or operate services.
