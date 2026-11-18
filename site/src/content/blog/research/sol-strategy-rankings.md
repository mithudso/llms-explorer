---
title: "Historical SOL strategy rankings and robustness checks"
description: "Historical SOL strategy rankings and robustness checks. An edited historical research report with its original evidence limits retained."
date: "2026-11-18"
category: research
tags: [research, historical-study]
evidenceStatus: unverified
evidenceNote: "Editorial review does not independently reproduce the original experiment. Results retain the source study’s dates, assumptions and limitations."
---

## Original study: SOL Strategy & Signal Rankings — Three Lists

> **Historical evidence.** This is an archival research report from August 2026, not a current performance claim or a recommendation to trade. Matching a saved output does not reproduce an experiment. The experiments were not rerun after later fixes to accounting, borrowing, metrics and selection. Results below retain the original study's assumptions and limitations.
>
> **Source availability.** References to `research/`, `backtester/` and result files identify the original research checkout. Those files and its market-data cache are not bundled with this article. Commands describe that historical environment; they are not a complete installation guide for a fresh checkout. Statements about tests passing describe the original study unless an explicit later check is identified.

**AS OF 2026-08-04.** Data runs through 2026-08-04; every figure is tied to that snapshot.
**Primary evaluation method: combinatorial purged cross-validation (CPCV)** — 8 blocks, k=2, so
**C(8,2) = 28 paths nominally**. Warm-up renders 1–2 blocks unusable for almost every
configuration, so realised path counts are lower; see "How many paths each figure actually
rests on" below. The earlier single 70/30 walk-forward is retained as List 1b, because the
disagreement between the two methods is the most instructive result here.

> **Historical simulation for research and education only. NOT investment advice**, and not a
> recommendation to trade anything. Simulated past performance does not predict future results.
> Every number below came from an executed run and can be reproduced with
> `python3 research/cpcv_sweep.py` and `python3 research/sweep.py`. No figure in this document
> was estimated; `python3 research/verify_numbers.py` enforces that mechanically.

**Method note.** The request asked for a `/dr` (deep-research) pass. Subagent fan-out is
unavailable in this environment, so the taxonomy is grounded in the local citation-backed
private reference corpus (reported as ~620 KB across 14 references)
plus first-hand measurement on real SOL data. That is a deliberate substitution, stated here
rather than made silently. Literature figures are attributed; everything else is measured.

---

## Read this before the tables

> **Read every ranking below against its multiple-testing benchmark, not against zero.**
> `python3 research/dso_audit.py` deflates these Sharpes per Bailey & Lopez de Prado
> (`backtester/core/deflated_sharpe.py`). Across the **200 single-strategy configurations** now
> evaluated (199 after collapsing the proven `bb_reversion`/`zscore` duplicate), **two clear the
> Sharpe the search alone would be expected to produce under no skill, and only one of those also
> clears the evidence floor**:
>
> - `ZEC adx_trend` — Sharpe +1.037 against a +0.905 benchmark, **DSR 0.568**, 60 trades, Q1 +0.371.
>   The only row here that survives both tests. DSR 0.568 is barely above the 0.5 coin-flip line, so
>   read it as not-yet-disconfirmed rather than as an edge.
> - `BTC ou_reversion` — DSR 0.775, but on **6 trades with Q1 exactly 0.000**, below any usable floor.
>
> `SOL hurst_switch`, ranked first on SOL daily at +0.699, does not reach its own +0.886 benchmark
> (DSR **0.416**). A high rank in the tables below is a position in a search, not evidence of an edge.

**Under CPCV, over all 25 registered strategies: 75 singles + 846 pairs + 200 triples = 1,121
configurations.** At the short horizon **not one of the 25 singles has a positive median path
Sharpe**. At the daily horizons singles PBO is **0.700** — well above the 0.500 pure-noise line,
so in-sample rank is anti-informative.

### How many paths each figure actually rests on

**Corrected 2026-08-05.** This document previously said all 1,287 configurations in the earlier text ran "each
across 28 paths". They did not, and the gap is not marginal — computed from
`results/cpcv_results.csv` and `results/cpcv_combos_results.csv`:

| Paths | Configurations | Share |
|---|---|---|
| 28 (full) | **3** | 0.3% |
| 21 | 932 | 83.1% |
| 15 | 186 | 16.6% |

**The only three configurations ever evaluated on all 28 paths are `buy_and_hold`, one per
horizon** — because it is the sole strategy with no warm-up. Every signal-based configuration
lost 1 or 2 of the 8 blocks to warm-up, and the median across the population is **21 paths**.
Two consequences worth carrying into any reading of the tables below:

1. **The benchmark is measured on more paths than anything it is compared against.** That is
   not a bug — needing no warm-up is a real property of holding the asset — but it means
   `buy_and_hold` has more overlapping evaluation paths. Path count alone does not establish a tighter uncertainty interval, because these paths are not independent.
2. **The slowest configurations rest on 15 paths**, including several that appear at the top of
   the tables: `ou_reversion`, `hurst_switch` and `vol_regime` at both daily horizons. Four of
   four of the five configurations in “How an archival SOL study chose its top five candidates” (forthcoming, planned 2026-11-19) are 15-path results. Fewer paths is a
   weaker estimate, and the `n_paths` column in every results CSV records it per row.

**Growing the candidate set from 16 to 25 strategies coincided with higher PBO; the retained comparison separates out one evaluation-geometry change.** The common CPCV block set shrank from 7 blocks to 6 when
the 250-bar-window strategies (OU, Hurst, vol-regime) were added, because they cannot warm up
before block 1 — so two variables moved together. Holding the block set fixed removes that particular confound, but strategy count and composition still change together:

| | Medium | Long |
|---|---|---|
| 16 configs, 7 blocks (the earlier run) | 0.457 | 0.457 |
| 16 configs, **6 blocks** | 0.600 | 0.550 |
| **25 configs**, 6 blocks | **0.700** | **0.700** |
| **difference with block set fixed** | **+0.100** | **+0.150** |

The fixed-block comparison changes by +0.100 / +0.150, while the full comparison moves 0.457 → 0.700. It does not isolate count from candidate composition, and attributing the entire change to search size would be unsupported.

**Under the earlier single split: 953 configurations, 595 rankable, 73 (12%) with a positive
out-of-sample Sharpe, 47 (8%) that made money.**

**The `#` column in every table below is the weakest thing in this document.** Finding 1f re-ran
all 25 singles at every CPCV block count from 6 to 12. At the long horizon the mean pairwise rank
correlation is **+0.566**, the median strategy moves **12 of 25 places**, and **six different
strategies hold first place across seven block counts**. Eight blocks is the geometry these tables
happen to use and nothing justifies it over nine. Read the tables for *which mechanisms clear zero
at all*; do not read positions off them, and do not read the top row as "the best".

The findings below matter more than any ranking. Findings 1/1b/1c are the method result — one
split cannot answer this question and PBO quantifies how little in-sample rank tells you. Finding
1f is the sharpest limit on the tables themselves. Findings 2–4 were measured under the single
split and are kept because the contrast is the lesson; finding 4 in particular shows a top-ranked
row is highly sensitive in a within-mechanism comparison; that is a robustness warning, not a proof of noise.

### 1. The split ends on the highest close in the series. One split cannot answer this.

| Leg | Daily (medium/long) | Hourly (short) |
|---|---|---|
| In-sample | 2021-06-17 → 2025-01-18, **\$39.25 → \$261.99 (+567.5%)** | 2025-08-01 → 2026-04-15, \$170.25 → \$83.66 (−51%) |
| Out-of-sample | 2025-01-19 → 2026-08-04, **\$252.34 → \$73.89 (−70.7%)** | 2026-04-15 → 2026-08-04, \$83.66 → \$73.00 (−13%) |

**Endpoint correction:** the original in-sample cell used **\$252.34 (+543%)**, but \$252.34 is the close on **2025-01-19**, the first out-of-sample date. The corrected in-sample endpoint is **\$261.99 on 2025-01-18**, giving **+567.5%** from \$39.25. The final out-of-sample \$73.89 remains the author’s historical value; the later-growing cache has a different final-bar value and was not substituted to regenerate returns.

This is worse than "near the top". The **highest close in the entire 1,875-bar series is
\$261.99, on 2025-01-18 — bar 1311, the final bar of the in-sample window.** The split falls on
the very next bar. So a 70/30 split puts essentially the entire bull market in-sample and the
entire bear leg out-of-sample. That exposes long-biased strategies to different market regimes; it does not force every possible long-biased rule to have the same performance. That column
measured **one regime**, not the future.

**This has now been replaced by CPCV.** Findings 2–4 below were measured under the old single
split and are retained because the contrast is the lesson; the CPCV rankings that supersede them
are in List 1, and they reorder almost completely.

### 1b. Under CPCV the ranking reorders completely, and buy-and-hold stays near the top.

The single split ranked `zscore_20_-2` first at the medium horizon (OOS Sharpe +0.699). Under CPCV
it falls far down the table, and the medium-horizon top two are `hurst_switch` (+0.699, 93% of
paths positive) and **`buy_and_hold` (+0.534)**. At the long horizon buy-and-hold is 6th, with five strategies ahead of it; among them are
`obv_trend_60` and `vol_regime`.

That buy-and-hold sits second and sixth across 25 strategies is the headline: *on this asset and
this history, holding the asset beat all but one medium-horizon single and all but five long-horizon singles* — and the ones ahead
of it are separated by less than their own interquartile spread.

CPCV also made the long horizon answerable at all. Under the single split only **4 of 16**
long-horizon configurations cleared the evidence floor; under CPCV **all 25 are evaluable**,
because blocks reuse the whole series instead of one 563-bar tail.

### 1c. PBO says in-sample selection is anti-informative at the daily horizons.

Probability of Backtest Overfitting (Bailey et al., via CSCV), over all 25 strategies:

| Horizon | PBO | splits | configs |
|---|---|---|---|
| Short | **0.343** | 35 | 25 |
| Medium | **0.700** | 20 | 25 |
| Long | **0.700** | 20 | 25 |

Calibrated against constructed controls in the test suite: **pure noise gives mean PBO 0.500**
(over 30 seeds) and **a genuinely ordered signal set gives 0.000**. Both daily horizons sit at
0.700: the selected in-sample winner fell below the out-of-sample candidate median in 70% of tested splits. That is a rank-based warning, not a measured dollar-profit comparison with random trading. The earlier 16-strategy run measured 0.429 / 0.457 / 0.457; the
decomposition of that rise is in *Read this before the tables* above.

Short horizon needs the same care as any low PBO: 0.343 looks encouraging, but **0 of 25** singles
have a positive median Sharpe there, so in-sample rank generalises reliably as a loser. PBO
measures rank consistency, not profitability — always read it next to the positive count.

### 1d. The top pair survives parameter perturbation — which is a narrower result than it sounds

`all(dual_momentum+vol_regime)` has the highest median Sharpe in the retained pair tables (median Sharpe **+1.345**,
87% of paths positive, **+75.1%** median path return). It sits atop a 252-evaluable-configuration search
whose PBO is 0.650, so the obvious question is whether the number is a property of the mechanism
or of the particular parameters someone picked. `research/perturb.py` answers that by nudging every
parameter ±10% one at a time and re-running the full CPCV evaluation.

**Result: 0 of 12 perturbations flip the sign, and the median never drops below +0.904.**

| Variant | Median Sharpe | Δ | % paths + |
|---|---|---|---|
| baseline | **+1.345** | — | 87% |
| `vol_window` 60→66 | +1.435 | +0.090 | 93% |
| `formation` 24→26 | +1.294 | −0.051 | 93% |
| `trend_window` 200→180 | +1.154 | −0.191 | 80% |
| `formation` 24→22 | +1.019 | −0.327 | 87% |
| `lookback` 250→225 | +0.954 | −0.392 | 71% |
| **geometry: 9 blocks** | **+0.904** | **−0.441** | 95% |

Two things worth noticing. **The largest single move comes from the CPCV geometry, not from any
strategy parameter** — changing 8 blocks to 9 moved the median more (−0.441) than the worst
parameter nudge did (−0.392). The result is more sensitive to how you slice the data than to the
strategy's own settings, which is not what you would guess.

And the sensitivity is **typical, not exceptional**. Measuring the same ratio (max |Δ| over the
baseline's own path IQR) across seven top long-horizon configurations gives 0.13–0.72 with a median
of 0.44. This pair scores 0.44 on parameters alone, 0.50 including geometry — squarely mid-pack:

| Configuration | median Sharpe | ratio | sign flips |
|---|---|---|---|
| `obv_trend` (single) | +0.774 | **0.13** | 0/2 |
| `all(macd+vol_regime)` | +0.991 | 0.30 | 0/12 |
| `any(ou_reversion+obv_trend)` | +1.054 | 0.38 | 0/8 |
| `all(dual_momentum+vol_regime)` | +1.345 | 0.44 | 0/9 |
| `vol_regime` (single) | +0.696 | 0.44 | 0/6 |
| `any(adx_trend+ou_reversion)` | +1.162 | 0.47 | 0/10 |
| `any(hurst_switch+ou_reversion)` | +0.965 | **0.72** | 0/12 |

**Across all seven configurations and 59 perturbations, not one flipped sign.**

> **What this does not establish.** Perturbation stability and multiple testing are *different
> failure modes*. These local perturbations show sign stability and the measured sensitivity around the selected settings. They do **not** establish that the parameters were free of selection bias, or that the reported numbers are free of parameter artifacts. Configuration selection can also remain biased; PBO 0.650 is a separate rank-based warning. Neither diagnostic proves that the result will hold out of sample.

Reproduce with:

```bash
python3 research/perturb.py --horizon long --pair dual_momentum vol_regime --mode all
python3 research/perturb.py --horizon medium --single hurst_switch
```

### 1e. Perturbation stability across all 25 singles — three findings, one of them new

`research/perturb.py --all-singles` ran the ±10% check on every strategy at every horizon: **72
configurations, 329 perturbations.** `buy_and_hold` is skipped throughout — it has no parameters
to perturb, which is its own kind of robustness.

**Population ratio (max |Δ median| over the configuration's own path IQR):**

| Horizon | min | median | max | sign flips |
|---|---|---|---|---|
| Short | 0.11 | 0.26 | 0.78 | 1/111 |
| Medium | 0.04 | 0.14 | 0.86 | 21/110 |
| Long | 0.06 | 0.17 | 1.33 | 13/108 |

**Finding 1 — the five selected long-horizon pair experiments were more locally parameter-sensitive than the singles population.** Singles median ratio **0.21**; the five selected long-horizon pairs median **0.44**. Relative to pooled singles **0.21**, that ratio is about **2.1×**. The like-horizon comparison uses long singles **0.171**, giving about **2.6×**. This compares a selected pair subset with the broader singles set; it does not show that every combination is more sensitive.

PBO answers a different question and does not show a general increase from combining here: daily singles are **0.700**, daily pairs **0.650**, long triples **0.543**, and medium triples **0.886**. At short, singles/pairs/triples are **0.343 / 0.229 / 0.086**. Only medium triples have higher PBO than the same-horizon singles in these retained populations.

**Finding 2 — the two most fragile configurations of all 72 are `bb_reversion` and `zscore` at the
long horizon, both at ratio 1.33 — the only two above 1.0.** These are the pair already proven from
source to be *the same mechanism* separated by a stdev convention (finding 4). Their path IQR is a
mere 0.222, so any nudge is large relative to it. That is now **three different diagnostics on the same
configuration**: the algebra, the 46-point natural experiment, and the highest perturbation ratio
in the population. When three unrelated tests point at one row, believe them.

**Finding 3 — `obv_trend` is the standout on this test.** Long horizon: median Sharpe **+0.774**,
**81% of paths positive**, ratio **0.13** (4th most stable of 24), **0 sign flips**, and only two
perturbable parameters — fewer ways to be wrong. (**Qualified by finding 1f below:** that +0.774
is its value at 8 blocks, the geometry this document happens to use. Across block counts 6–12 its
median is +0.573 and it is *not* always first. What survives is its rank *stability*, which is the
best in the set.) Compare the medium-horizon leader `hurst_switch`: median
+0.699 and 93% of paths positive, but ratio **0.60**, near the top of the singles distribution. The
two best performers have very different robustness, and the ranking does not tell you which is
which.

**Does the ranking select parameter luck?** Spearman correlation between median Sharpe and ratio:
**−0.045 (long), −0.152 (medium), +0.328 (short)**. The long and medium values show weak sample rank association. They do not prove independence between performance and stability. **Short is +0.328: the better
performers *are* the less stable ones**, which is consistent with sensitivity contributing to the short-horizon ranking, without isolating parameter luck as its cause. Since every short-horizon median is negative, "better" there means "least bad", but
the direction is still the bad one.

Sign flips cluster where you would expect — around near-zero medians (`breakout` +0.140, `grid`
+0.095, `bb_reversion`/`zscore` +0.120). Short shows only 1 flip in 111 because every median is
solidly negative and there is no sign to lose.

```bash
python3 research/perturb.py --horizon long --all-singles     # any of short|medium|long
```

### 1f. Block count 6–12: at the long horizon the ranking is largely a slicing artifact

The perturbation run threw up an oddity — for the top pair, changing 8 blocks to 9 moved the median
more than any 10% parameter change. `research/geometry.py` measures that properly: re-rank all 25
strategies at every block count from 6 to 12 and ask whether the *ranking* survives.

| Horizon | mean pairwise Spearman | median rank movement | distinct #1s | verdict |
|---|---|---|---|---|
| Short | **+0.909** | 5 of 25 | 3 | mostly stable |
| Medium | +0.772 | 9 of 25 | 4 | mostly stable |
| **Long** | **+0.566** | **12 of 25** | **6** | **geometry-dependent** |

**The long-horizon ranking is the most geometry-sensitive in this comparison. It also has the largest number of positive single-strategy medians: 22 of 25, versus 13 at medium and none at short.** Positive medium singles and positive short combinations remain visible in their own tables.
Six different strategies hold first place across seven block counts — `macd` (6, 10),
`ou_reversion` (7), `obv_trend` (8), `rsi` (9), `hurst_switch` (11), `ts_momentum` (12). The median
strategy moves twelve of twenty-five places. Reading a position off the long-horizon leaderboard is
reading the block count.

The mechanism is straightforward once stated: slow long-horizon parameters generate few trades, so
each block's Sharpe is noisy, so the ordering is easily reshuffled. The short horizon has 8,823 bars
and hundreds of trades per configuration, and its ranking is correspondingly stable (+0.909).

**And the leaderboard-toppers are the unstable ones.** Spearman between the best rank a strategy
ever achieves and how far its rank moves is **−0.390** — better peak rank goes with *more*
movement. Strategies that held first place somewhere move a mean of **14.0** places; everyone else
**11.6**. Topping this leaderboard is partly a symptom of instability.

**What survives the test, ranked by invariance rather than by performance.** The median column
is *not* sorted; `adx_trend` (+0.604) and `rsi` (+0.593) have the two highest medians of all 25 and
both are far less stable than the rows below them:

| Strategy | median across 6–12 | spread | rank movement | top-3 in |
|---|---|---|---|---|
| `buy_and_hold` | +0.587 | **0.27** | 7 | 1/7 |
| `obv_trend` | +0.573 | 0.38 | **5** | 3/7 |
| `vol_regime` | +0.386 | 0.41 | 12 | 1/7 |
| `hurst_switch` | +0.461 | 0.42 | 19 | 2/7 |
| `adx_trend` | +0.604 | **1.38** | **23** | 2/7 |

Two things to take from that table. **`buy_and_hold` has by far the smallest spread (0.27)**, and
it reaches third of 25 on median (+0.587) while doing so — it edges `obv_trend` on median while
being twice as invariant, which is unsurprising given it has no parameters and no timing to get
wrong. And **`adx_trend` has the single highest median of all 25 (+0.604) while ranging from +0.78
to −0.60 and moving 23 of 25 places** — the clearest example in this document of a number that
means nothing. The top of the median column and the top of the stability column are not the same
strategies, which is the finding restated.

`obv_trend` is the one genuinely encouraging row: not always first, but the **most rank-stable
strategy in the set** (moves 5 places), third-smallest spread, top-3 in three of seven geometries.

**PBO is not geometry-invariant either**, which matters because it is the statistic used to
discount everything else. At the long horizon it runs 0.800 (6 blocks) → 0.700 (8) → **0.943** (10)
→ 0.830 (12); at medium, 0.445 (12) to 0.667 (11). The listed long-horizon values stay above 0.500; medium spans both sides of that reference, so
the conclusion holds in direction, but the specific figure quoted elsewhere in this document is the
8-block one and should be read as one draw from that range.

```bash
python3 research/geometry.py --horizon long --blocks 6 12 --k 2
```

> **Net effect on how to read Lists 1–3.** Two different diagnostics now raise related concerns from
> different directions: PBO says in-sample rank does not generalise, and this says the rank is not
> even stable to an arbitrary evaluation choice. Use the tables to see *which mechanisms produce
> positive medians at all*, and treat the ordering within them as noise.

### 2. In-sample rank does not predict out-of-sample rank. At the medium horizon it inverts.

Spearman rank correlation between in-sample and out-of-sample Sharpe, across rankable configs:

| Slice | n | ρ(IS Sharpe, OOS Sharpe) |
|---|---|---|
| Short horizon | 278 | +0.073 |
| Medium horizon | 220 | **−0.423** |
| Long horizon | 97 | −0.077 |
| Singles only | 50 | +0.118 |
| Pairs only | 524 | +0.337 |
| All | 595 | +0.279 |

The retained 953-row sweep yields a negative medium-horizon rank association among its 220 rankable rows. Mean Sharpe falls from **+0.735 in-sample to −0.600 out-of-sample** (medium) and **+0.775 to −0.543** (long). These descriptive summaries do not directly compare trading profit with random selection. The market regime changes at the split, which confounds attribution to overfitting alone. The source’s McLean & Pontiff comparison concerns a different study and sample; its 58% figure concerns post-publication decay, not a matched benchmark for this experiment.

### 3. "Beat the baseline" is nearly meaningless when the baseline lost 71%.

Denominators here are **all rankable configurations at that horizon** — singles, pairs, and
triples pooled. These counts are recomputed from the retained 953-row sweep, using its explicit `rankable` field; earlier versions summarized a smaller candidate population.

| Horizon | Baseline (buy & hold) OOS | Beat baseline | **Actually made money** |
|---|---|---|---|
| Short | −12.9% | 156/278 | **28/278** |
| Medium | −70.8% | 212/220 | **11/220** |
| Long | −70.8% | 85/97 | **8/97** |

212 of 220 medium-horizon configurations beat a baseline that lost about 71%, while only eleven made money. Report both comparisons.

### 4. A within-mechanism comparison: the top row is sensitive to a small threshold change

This is the strongest single piece of evidence here, and unlike finding 2 it needs **no regime
story at all**. Rows 1 and 2 of the medium-horizon table are, provably from source, *the same
mechanism* separated only by a standard-deviation convention — a **2.6% difference in entry
threshold** (see List 3 for the derivation):

| Configuration | OOS Sharpe | **OOS return** | OOS trades | OOS exposure |
|---|---|---|---|---|
| `zscore_20_-2` | +0.699 | **+41.3%** | 10 | 0.259 |
| `bb_reversion_20_2` | +0.193 | **−4.8%** | 10 | 0.298 |

**Identical trade count. A 46-percentage-point gap in outcome.** A trivial, economically
meaningless perturbation of one threshold flips the top-ranked medium-horizon strategy from
+41% to −5%. Whatever `zscore_20_-2`'s first-place ranking is measuring, it is not a property
of the mechanism.

The contrast completes the argument. Gate both with the regime filter and they become
**numerically identical** — `all(sma_regime+zscore)` and `all(sma_regime+bb_reversion)` both
score OOS Sharpe **+2.5721** on **+9.03%** over **18 trades**, matching to four decimal places,
because the gate suppresses exactly the bars where the threshold difference lived. Ungated, that
difference dominated the entire result.

> **This observation is now enforced rather than only noted.** `zscore` and `bb_reversion`
> measure 0.96–1.00 correlated, so `research/signal_redundancy.py` groups them into one
> redundancy class and the sweep builds only the representative combination —
> `all(sma_regime+bb_reversion)`. The `zscore` twin is no longer evaluated, which is why it no
> longer appears in the tables below. One caveat this pair does *not* show: identical here does
> not mean identical everywhere. Under CPCV at the short horizon the two score median path
> Sharpe **+0.549** and **+0.681**, because the short-horizon class is a looser three-member
> group (`bb_reversion`, `rsi`, `zscore`, minimum pairwise 0.837) than the medium and long
> pair (0.964 and 1.000).

**Practical rule this implies:** before believing any row in any of these tables, perturb its
parameters slightly and re-run. A material change establishes sensitivity, not by itself that the underlying mechanism is noise. This
document does not do that systematically for all 953 configurations — it should, and that is
item 7 in *What to actually do next*.

### A proposed exposure association was weak in this sample

The top-ranked rows have small returns on high Sharpe (e.g. `all(sma_regime+bb_reversion)`, OOS Sharpe 2.572 on +9.0%), which suggested a possible association with *how little the strategy was invested* during a downtrend.

The original report quoted exposure correlations **−0.05 (short), −0.09 (medium), +0.26 (long), +0.02 overall**, and Sharpe–return correlations **+0.79 to +0.84**, without identifying the population. Those are retained as **unbound historical-population figures**, not results of the retained panel.

A read-only recomputation uses **Pearson product-moment correlation** on the retained CSV rows with `rankable=True`: **n=278 short, 220 medium, 97 long; 595 pooled**. OOS Sharpe versus OOS exposure is **−0.007913 / −0.278933 / −0.022703**, and **−0.008527 pooled**. OOS Sharpe versus OOS return is **+0.773417 / +0.790314 / +0.864418**, and **+0.196979 pooled**, in the same horizon order. These descriptive associations vary by horizon. Neither a near-zero pooled correlation nor these separate-horizon values exclude nonlinear, conditional or regime-dependent exposure effects.

---

## List 1 — Single strategies and signals, ranked (CPCV — primary)

Ranked on **median path Sharpe** with 28 nominal CPCV paths (8 blocks, k=2), over **all 25 registered strategies**. Warm-up leaves **15 or 21 usable paths for most signal configurations**; only the three no-warm-up buy-and-hold rows use all 28. Three columns matter as much as the median: **IQR**, the width Q3−Q1 (a median of +0.5 and IQR 1.4 alone do not say whether Q1 is below zero); **% paths positive**, the fraction positive in the available overlapping paths; and **trades**. To say the central interval crosses zero, inspect Q1 and Q3 themselves. Tables are generated from `research/results/cpcv_results.csv`; no
figure is transcribed by hand.

> **The ordering is not a result — the `8 blocks` in that first line is.** Finding 1f re-ranks
> these same 25 strategies at block counts 6 through 12 and the order does not survive it, worst
> at the long horizon (mean pairwise Spearman **+0.566**, median strategy moving **12 of 25**
> places). The medians and the IQR/`% paths +` columns are what to read; the rank number is an
> artifact of one arbitrary evaluation choice.

## Short horizon (1h bars) — CPCV

**Not one of the 25 has a positive median path Sharpe at this horizon.** The best, `stoch_14_3` at −0.341, still loses.

| # | Strategy | Family | Median Sharpe | IQR | % paths + | Median ret | Trades |
|---|---|---|---|---|---|---|---|
| 1 | `stoch_14_3` | oscillator-reversion | **-0.341** | 2.117 | 38% | -5.2% | 240 |
| 2 | `ou_reversion_250_2.5` | mean-reversion | **-0.595** | 1.333 | 33% | -3.4% | 196 |
| 3 | `keltner_12_7_2` | breakout | **-0.961** | 2.477 | 29% | -4.9% | 88 |
| 4 | `vol_regime_24_0.5` | regime-filter | **-1.048** | 1.677 | 19% | -8.8% | 290 |
| 5 | `zscore_20_-2` | mean-reversion | **-1.152** | 1.213 | 19% | -12.5% | 294 |
| 6 | `bb_reversion_20_2` | mean-reversion | **-1.316** | 1.396 | 14% | -15.4% | 308 |
| 7 | `buy_and_hold` | baseline | **-1.456** | 2.154 | 29% | -22.9% | 16 |
| 8 | `bb_breakout_20_2` | breakout | **-1.487** | 3.114 | 29% | -11.5% | 270 |
| 9 | `obv_trend_24` | volume-flow | **-1.580** | 1.668 | 24% | -18.0% | 852 |
| 10 | `rsi_7_30_55` | oscillator-reversion | **-1.723** | 1.052 | 14% | -19.8% | 328 |
| 11 | `ichimoku_9_26_52` | trend | **-1.877** | 1.174 | 0% | -18.6% | 392 |
| 12 | `breakout_12_6` | breakout | **-1.905** | 2.809 | 14% | -16.9% | 350 |
| 13 | `grid_48_4_0.03` | mean-reversion | **-2.022** | 0.731 | 0% | -12.4% | 4304 |
| 14 | `vwap_reversion_20_0.01` | mean-reversion | **-2.189** | 0.836 | 0% | -24.3% | 398 |
| 15 | `voltarget_168_24_0.8` | risk-overlay | **-2.282** | 1.278 | 5% | -19.9% | 292 |
| 16 | `sma_regime_168` | regime-filter | **-2.282** | 1.278 | 5% | -19.9% | 292 |
| 17 | `garch_voltarget_0.94_0.8` | risk-overlay | **-2.282** | 1.278 | 5% | -19.9% | 292 |
| 18 | `ma_crossover_12_48` | trend | **-2.385** | 3.326 | 10% | -23.5% | 204 |
| 19 | `atr_sized_7_0.01` | risk-overlay | **-2.548** | 2.298 | 5% | -12.4% | 3191 |
| 20 | `ts_momentum_24` | momentum | **-2.564** | 2.018 | 0% | -24.2% | 716 |
| 21 | `ma_ribbon_5x6` | trend | **-2.767** | 2.727 | 5% | -19.5% | 4572 |
| 22 | `macd_6_13_5` | trend | **-3.083** | 2.223 | 0% | -33.4% | 1156 |
| 23 | `hurst_switch_250_0.55_0.45` | regime-filter | **-3.123** | 2.107 | 14% | -12.8% | 170 |
| 24 | `adx_trend_7_25` | regime-filter | **-3.736** | 2.496 | 5% | -27.4% | 680 |
| 25 | `dual_momentum_24_2` | momentum | **-4.633** | 2.094 | 0% | -39.2% | 728 |

> 0 of 25 evaluable have a positive median. PBO **0.343** over 35 splits of 25 configurations (common blocks [1, 2, 3, 4, 5, 6, 7]).

## Medium horizon (1d bars) — CPCV

| # | Strategy | Family | Median Sharpe | IQR | % paths + | Median ret | Trades |
|---|---|---|---|---|---|---|---|
| 1 | `hurst_switch_250_0.55_0.45` | regime-filter | **+0.699** | 1.167 | 93% | +16.7% | 24 |
| 2 | `buy_and_hold` | baseline | **+0.534** | 1.434 | 68% | +9.4% | 16 |
| 3 | `bb_breakout_20_2` | breakout | **+0.481** | 1.694 | 67% | +15.9% | 58 |
| 4 | `ou_reversion_250_2.5` | mean-reversion | **+0.412** | 0.790 | 93% | +10.5% | 26 |
| 5 | `adx_trend_14_25` | regime-filter | **+0.336** | 2.368 | 71% | +7.0% | 44 |
| 6 | `macd_12_26_9` | trend | **+0.321** | 1.277 | 67% | +3.8% | 118 |
| 7 | `rsi_14_30_50` | oscillator-reversion | **+0.238** | 0.664 | 71% | -0.0% | 18 |
| 8 | `keltner_20_14_2` | breakout | **+0.213** | 1.656 | 76% | +2.2% | 38 |
| 9 | `obv_trend_20` | volume-flow | **+0.189** | 1.536 | 67% | -9.8% | 220 |
| 10 | `breakout_20_10` | breakout | **+0.078** | 1.911 | 52% | -6.4% | 52 |
| 11 | `zscore_20_-2` | mean-reversion | **+0.036** | 0.964 | 52% | -10.0% | 50 |
| 12 | `ts_momentum_60` | momentum | **+0.025** | 1.752 | 52% | -19.4% | 142 |
| 13 | `ichimoku_9_26_52` | trend | **+0.023** | 2.055 | 57% | -10.9% | 82 |
| 14 | `voltarget_100_20_0.6` | risk-overlay | **-0.021** | 1.154 | 38% | -14.7% | 645 |
| 15 | `garch_voltarget_0.94_0.6` | risk-overlay | **-0.028** | 1.207 | 48% | -12.2% | 711 |
| 16 | `atr_sized_14_0.01` | risk-overlay | **-0.038** | 1.289 | 48% | -0.3% | 743 |
| 17 | `stoch_14_3` | oscillator-reversion | **-0.043** | 1.175 | 48% | -13.3% | 56 |
| 18 | `sma_regime_100` | regime-filter | **-0.066** | 1.522 | 48% | -16.4% | 96 |
| 19 | `bb_reversion_20_2` | mean-reversion | **-0.114** | 0.910 | 43% | -19.1% | 50 |
| 20 | `grid_50_4_0.05` | mean-reversion | **-0.152** | 0.369 | 29% | -16.7% | 599 |
| 21 | `vol_regime_20_0.5` | regime-filter | **-0.172** | 0.759 | 40% | -18.7% | 94 |
| 22 | `vwap_reversion_20_0.02` | mean-reversion | **-0.265** | 0.587 | 29% | -38.4% | 152 |
| 23 | `dual_momentum_12_1` | momentum | **-0.319** | 1.459 | 43% | -37.2% | 212 |
| 24 | `ma_crossover_20_50` | trend | **-0.334** | 2.186 | 38% | -31.7% | 38 |
| 25 | `ma_ribbon_5x10` | trend | **-0.336** | 1.957 | 43% | -29.0% | 965 |

> 13 of 25 evaluable have a positive median. PBO **0.700** over 20 splits of 25 configurations (common blocks [2, 3, 4, 5, 6, 7]).

## Long horizon (1d bars, slow parameters) — CPCV

> **This is the table whose ordering survives least, and the one with the most positive medians —
> **22 of 25**, against **13** at medium and **none** at short. The two facts are not
> independent.** Slow parameters mean few trades, so each CPCV
> block's Sharpe is noisy and the order reshuffles when the block count changes. Concretely, of
> the seven block counts 6–12, **only the 8-block geometry used here is led by the row this table
> ranks first.** The other six are led by rows this table places **fourth** (`rsi`), **fifth**
> (`hurst_switch`), **seventh** (`macd`, which leads at two of them), **eighth** (`ou_reversion`)
> and **sixteenth of twenty-five** (`ts_momentum`). Finding 1f has the mapping and the checks.
>
> Read the medians and their spread. Do not read this as a ranking.

| # | Strategy | Family | Median Sharpe | IQR | % paths + | Median ret | Trades |
|---|---|---|---|---|---|---|---|
| 1 | `obv_trend_60` | volume-flow | **+0.774** | 1.571 | 81% | +44.6% | 98 |
| 2 | `vol_regime_60_0.5` | regime-filter | **+0.696** | 0.823 | 80% | +36.1% | 54 |
| 3 | `adx_trend_30_25` | regime-filter | **+0.651** | 2.286 | 57% | +26.2% | 14 |
| 4 | `rsi_30_35_55` | oscillator-reversion | **+0.593** | 0.895 | 71% | +20.8% | 10 |
| 5 | `hurst_switch_250_0.55_0.45` | regime-filter | **+0.558** | 1.505 | 80% | +11.3% | 32 |
| 6 | `buy_and_hold` | baseline | **+0.534** | 1.434 | 68% | +9.4% | 16 |
| 7 | `macd_26_52_18` | trend | **+0.517** | 1.142 | 76% | +16.1% | 50 |
| 8 | `ou_reversion_250_3` | mean-reversion | **+0.412** | 0.806 | 73% | +10.5% | 24 |
| 9 | `dual_momentum_24_1` | momentum | **+0.358** | 1.715 | 57% | +5.5% | 156 |
| 10 | `stoch_40_5` | oscillator-reversion | **+0.316** | 0.752 | 57% | +6.3% | 34 |
| 11 | `voltarget_200_60_0.6` | risk-overlay | **+0.295** | 1.558 | 76% | +5.0% | 661 |
| 12 | `ma_crossover_50_200` | trend | **+0.290** | 1.162 | 52% | +0.0% | 16 |
| 13 | `sma_regime_200` | regime-filter | **+0.254** | 1.620 | 71% | -2.2% | 44 |
| 14 | `ichimoku_18_52_104` | trend | **+0.243** | 0.950 | 71% | +2.5% | 56 |
| 15 | `garch_voltarget_0.97_0.6` | risk-overlay | **+0.239** | 1.558 | 76% | +2.3% | 672 |
| 16 | `ts_momentum_200` | momentum | **+0.200** | 2.341 | 52% | -12.7% | 54 |
| 17 | `ma_ribbon_5x20` | trend | **+0.171** | 1.319 | 57% | -2.6% | 1030 |
| 18 | `atr_sized_30_0.01` | risk-overlay | **+0.156** | 1.715 | 67% | +0.7% | 672 |
| 19 | `breakout_60_30` | breakout | **+0.140** | 1.676 | 62% | -6.6% | 18 |
| 20 | `zscore_60_-2` | mean-reversion | **+0.120** | 0.222 | 76% | -6.0% | 24 |
| 21 | `bb_reversion_60_2` | mean-reversion | **+0.120** | 0.222 | 76% | -6.0% | 24 |
| 22 | `grid_120_4_0.1` | mean-reversion | **+0.095** | 0.869 | 52% | -2.3% | 675 |
| 23 | `keltner_50_30_2` | breakout | **-0.160** | 2.203 | 38% | -17.7% | 34 |
| 24 | `vwap_reversion_60_0.05` | mean-reversion | **-0.162** | 0.420 | 29% | -31.5% | 54 |
| 25 | `bb_breakout_60_2` | breakout | **-0.349** | 1.905 | 43% | -27.1% | 32 |

> 22 of 25 evaluable have a positive median. PBO **0.700** over 20 splits of 25 configurations (common blocks [2, 3, 4, 5, 6, 7]).

---

## Reliable triggers

Not a signal ranking either: conjunctions of conditions scored by out-of-sample directional hit rate against
the base rate. 13,510 daily hypotheses tested on SOL, 0 qualified as reliable; see `research/RELIABLE_SIGNALS.md`.

---

## Leverage tiers

Not a ranking of signals: the same 25 singles re-run at 2x, 5x and 20x on SOL daily CPCV. Out-of-sample
median Sharpe -0.45 / -0.49 / -1.57 and P(ruin) 21% / 74% / 95%. Leverage does not rescue a losing
signal; see `research/LEVERAGE-TIERS.md`.

---

## List 1b — the same singles under a single 70/30 split (retained as contrast)

**Superseded by List 1.** Kept because the disagreement between the two methods is the lesson:
the single split ranked `zscore_20_-2` first at medium and `ma_crossover_12_48` first at short;
CPCV puts them far lower. Ranked on **out-of-sample Sharpe**, in-sample beside each row.
Rows with fewer than 10 out-of-sample trades are listed but **not ranked**.

## Short horizon (1h bars, fast parameters) — 25 configurations evaluated

| # | Strategy | Family | OOS Sharpe | IS Sharpe | OOS ret | IS ret | OOS maxDD | OOS trades |
|---|---|---|---|---|---|---|---|---|
| 1 | `ma_crossover_12_48` | trend | **+0.488** | −2.490 | +3.4% | −59.7% | −11.8% | 29 |
| 2 | `zscore_20_-2` | mean-reversion | **+0.441** | −1.285 | +2.8% | −37.3% | −19.0% | 48 |
| 3 | `ou_reversion_250_2.5` | mean-reversion | **+0.089** | −0.040 | +0.0% | −3.5% | −9.4% | 33 |
| 4 | `bb_reversion_20_2` | mean-reversion | **+0.086** | −1.274 | −0.9% | −37.3% | −18.0% | 52 |
| 5 | `hurst_switch_250_0.55_0.45` | regime-filter | **+0.030** | −3.097 | −0.1% | −40.2% | −6.6% | 29 |
| 6 | `voltarget_168_24_0.8` | sma-gated | −0.519 | −2.105 | −7.0% | −51.5% | −15.2% | 49 |
| 7 | `garch_voltarget_0.94_0.8` | sma-gated | −0.519 | −2.105 | −7.0% | −51.5% | −15.2% | 49 |
| 8 | `sma_regime_168` | sma-gated | −0.519 | −2.101 | −7.0% | −51.4% | −15.2% | 49 |
| 9 | `rsi_7_30_55` | oscillator-reversion | −0.527 | −1.620 | −7.4% | −45.9% | −23.9% | 49 |
| 10 | `bb_breakout_20_2` | breakout | −0.684 | −0.901 | −6.9% | −23.6% | −15.9% | 50 |
| 11 | `stoch_14_3` | oscillator-reversion | −0.719 | −0.311 | −7.9% | −14.6% | −13.9% | 37 |
| 12 | `ichimoku_9_26_52` | trend | −0.889 | −1.557 | −10.1% | −41.8% | −17.4% | 67 |
| 13 | `ma_ribbon_5x6` | trend | −1.030 | −2.019 | −9.6% | −43.6% | −18.0% | 801 |
| 14 | `vol_regime_24_0.5` | regime-filter | −1.360 | −1.386 | −10.8% | −26.9% | −15.5% | 58 |
| 15 | `grid_48_4_0.03` | mean-reversion | −1.510 | −1.593 | −8.8% | −27.1% | −13.3% | 694 |
| 16 | `vwap_reversion_20_0.01` | mean-reversion | −1.516 | −1.777 | −17.2% | −50.5% | −23.3% | 55 |
| 17 | `atr_sized_7_0.01` | sma-gated | −1.665 | −2.039 | −10.4% | −27.2% | −13.2% | 434 |
| 18 | `ts_momentum_24` | momentum | −1.677 | −2.272 | −18.1% | −57.8% | −23.3% | 126 |
| 19 | `keltner_12_7_2` | breakout | −1.954 | +0.448 | −7.9% | +5.3% | −9.0% | 13 |
| 20 | `breakout_12_6` | breakout | −2.272 | −0.936 | −22.2% | −29.6% | −27.1% | 59 |
| 21 | `obv_trend_24` | volume-flow | −2.331 | −0.499 | −25.8% | −23.3% | −29.4% | 153 |
| 22 | `dual_momentum_24_2` | momentum | −2.739 | −4.061 | −27.3% | −76.5% | −31.6% | 130 |
| 23 | `adx_trend_7_25` | regime-filter | −3.600 | −1.991 | −28.4% | −45.7% | −29.7% | 121 |
| 24 | `macd_6_13_5` | trend | −4.621 | −2.016 | −42.4% | −56.4% | −46.0% | 205 |

_Not ranked: `buy_and_hold` (1 trade) — OOS Sharpe −0.523, OOS return −12.9%._

**Reading it:** five of twenty-four rankable short-horizon signals produced a positive
out-of-sample Sharpe, and the best of them returned +3.4% before any funding/borrow cost. Two of
the five clear zero by a rounding margin — `ou_reversion` at +0.089 on +0.0% and `hurst_switch`
at +0.030 on −0.1% are flat, not profitable. `macd_6_13_5` at −4.62 remains the clearest case of
a fast trend signal chewed up by whipsaw plus 8 bps per fill (16 bps per unchanged-notional round trip) across 205 trades.

Rows 6–8 are the redundancy finding sitting in plain sight: `voltarget`, `garch_voltarget` and
`sma_regime` post −0.519 on −7.0% over 49 trades apiece, because all three gate on
`close > sma(closes, 168)` and differ only in position size. They are one signal under three
names, which is why they now share the `sma-gated` family. `atr_sized` shares that gate too and
lands at −1.665 — its risk-normalised sizing changes the magnitude enough to move it eighteen
places without changing a single entry or exit decision.

## Medium horizon (1d bars, medium parameters) — 25 configurations evaluated

| # | Strategy | Family | OOS Sharpe | IS Sharpe | OOS ret | IS ret | OOS maxDD | OOS trades |
|---|---|---|---|---|---|---|---|---|
| 1 | `zscore_20_-2` | mean-reversion | **+0.699** | −0.170 | **+41.3%** | −64.8% | −52.0% | 10 |
| 2 | `hurst_switch_250_0.55_0.45` | regime-filter | **+0.564** | +0.669 | **+15.6%** | +64.0% | −16.3% | 10 |
| 3 | `bb_reversion_20_2` | mean-reversion | **+0.193** | −0.152 | −4.8% | −63.9% | −52.0% | 10 |
| 4 | `stoch_14_3` | oscillator-reversion | **+0.024** | +0.153 | −18.1% | −20.2% | −44.4% | 11 |
| 5 | `vol_regime_20_0.5` | regime-filter | −0.377 | −0.495 | −21.2% | −58.5% | −35.3% | 15 |
| 6 | `atr_sized_14_0.01` | sma-gated | −0.454 | +0.377 | −2.6% | +5.8% | −3.9% | 93 |
| 7 | `sma_regime_100` | sma-gated | −0.516 | +0.443 | −35.8% | +34.8% | −43.1% | 13 |
| 8 | `ichimoku_9_26_52` | trend | −0.531 | +0.967 | −33.3% | **+336.3%** | −36.7% | 11 |
| 9 | `vwap_reversion_20_0.02` | mean-reversion | −0.532 | +0.032 | −53.9% | −58.6% | −61.8% | 23 |
| 10 | `garch_voltarget_0.94_0.6` | sma-gated | −0.551 | +0.321 | −30.8% | +18.9% | −37.2% | 50 |
| 11 | `voltarget_100_20_0.6` | sma-gated | −0.569 | +0.307 | −31.1% | +15.7% | −34.8% | 73 |
| 12 | `grid_50_4_0.05` | mean-reversion | −0.590 | −0.119 | −38.9% | −36.9% | −48.5% | 100 |
| 13 | `macd_12_26_9` | trend | −0.720 | **+1.347** | −52.8% | **+1356.5%** | −59.2% | 21 |
| 14 | `bb_breakout_20_2` | breakout | −0.841 | **+1.837** | −34.9% | **+2843.6%** | −40.9% | 11 |
| 15 | `ts_momentum_60` | momentum | −0.874 | +0.959 | −51.1% | **+392.8%** | −51.3% | 25 |
| 16 | `ma_ribbon_5x10` | trend | −1.242 | +1.119 | −54.0% | **+452.0%** | −55.2% | 160 |
| 17 | `dual_momentum_12_1` | momentum | −1.303 | +1.176 | −65.3% | **+776.5%** | −71.8% | 37 |
| 18 | `obv_trend_20` | volume-flow | −1.383 | **+1.494** | −69.2% | **+1932.1%** | −69.2% | 37 |

_Not ranked (fewer than 10 OOS trades): `adx_trend_14_25` (8), `breakout_20_10` (7),
`ma_crossover_20_50` (7), `keltner_20_14_2` (6), `ou_reversion_250_2.5` (6), `rsi_14_30_50` (4),
`buy_and_hold` (1)._

**Reading it:** rows 13–18 are the exhibit, and adding nine strategies made it worse rather than
better. `bb_breakout_20_2` returned **+2,844% in-sample and −34.9% out-of-sample**; `obv_trend_20`
**+1,932% → −69.2%**; `dual_momentum_12_1` **+777% → −65.3%**; `ma_ribbon_5x10` **+452% → −54.0%**.
Every one of the six largest in-sample returns is a negative out-of-sample row. These are the
strategies a full-sample leaderboard would have crowned.

The four positive out-of-sample rows sit at 10–11 trades, exactly on the evidence floor — treat
them as "not yet disconfirmed" rather than "works". `hurst_switch` is the one new entrant among
them and the only positive row that is also positive in-sample (+0.669), which makes it the least
likely of the four to be a regime accident, and still a 10-trade sample.

## Long horizon (1d bars, slow parameters) — 25 configurations evaluated

| # | Strategy | Family | OOS Sharpe | IS Sharpe | OOS ret | IS ret | OOS maxDD | OOS trades |
|---|---|---|---|---|---|---|---|---|
| 1 | `dual_momentum_24_1` | momentum | −0.119 | +1.245 | −19.7% | +988.7% | −40.9% | 26 |
| 2 | `obv_trend_60` | volume-flow | −0.153 | +1.271 | −24.0% | +982.7% | −43.7% | 18 |
| 3 | `grid_120_4_0.1` | mean-reversion | −0.296 | +0.001 | −26.5% | −23.1% | −39.1% | 143 |
| 4 | `voltarget_200_60_0.6` | sma-gated | −0.395 | +0.975 | −23.6% | +219.9% | −27.9% | 67 |
| 5 | `garch_voltarget_0.97_0.6` | sma-gated | −0.448 | +0.919 | −25.4% | +185.3% | −27.9% | 44 |
| 6 | `atr_sized_30_0.01` | sma-gated | −0.464 | +0.983 | −2.5% | +17.2% | −3.5% | 66 |
| 7 | `ma_ribbon_5x20` | trend | −0.806 | +0.668 | −40.3% | +114.7% | −45.4% | 158 |
| 8 | `ts_momentum_200` | momentum | −1.976 | +1.098 | −77.2% | +506.2% | −77.7% | 15 |

_Not ranked (fewer than 10 OOS trades — the dominant outcome at this scale):
`hurst_switch_250_0.55_0.45` (6, OOS Sharpe +0.597), `rsi_30_35_55` (2, +0.540),
`vol_regime_60_0.5` (4, +0.287), `bb_reversion_60_2` (5, +0.225), `zscore_60_-2` (5, +0.225),
`macd_26_52_18` (7, +0.188), `ou_reversion_250_3` (6, +0.092), `breakout_60_30` (2),
`ichimoku_18_52_104` (6), `stoch_40_5` (4), `sma_regime_200` (4), `vwap_reversion_60_0.05` (7),
`buy_and_hold` (1), `adx_trend_30_25` (2), `ma_crossover_50_200` (2), `keltner_50_30_2` (6),
`bb_breakout_60_2` (5)._

**Reading it: not one rankable long-horizon _single_ has a positive out-of-sample Sharpe**
(0 of 8; 17 of 85 rankable long-horizon *pairs* do, see List 2). **Seventeen of twenty-five**
singles fail the evidence floor entirely, because slow parameters on a 563-bar out-of-sample
window simply do not generate enough trades. Expanding from 16 strategies to 25 did not improve
that ratio — it worsened it, from 12-of-16 to 17-of-25.

Note where the positive numbers are: every one of the seven configurations with a positive
out-of-sample Sharpe is in the *unranked* list, on 2 to 7 trades. `rsi_30_35_55` shows +0.540 on
**two** trades. That is the whole argument for having an evidence floor — without it, this
table's leaderboard would be sorted by sample size rather than by skill.

**The honest conclusion for the long horizon is that this dataset cannot answer the question** —
1,875 daily bars is too short to evaluate 200-day signals out-of-sample. That is a data
limitation, not a finding about the strategies.

## Spec-only tier — ranked by a priori plausibility, never measured

Not implemented, **no performance numbers**, ranked by reasoning only. Each names the data gap
that prevented measurement. Full field detail in [the sol strategy reference study](/blog/research/sol-strategy-reference/).

| Rank | Signal | Why plausibly high value for SOL | Blocking data gap |
|---|---|---|---|
| 1 | Perp funding / borrow-rate extremes | Direct positioning gauge; on Jupiter the borrow fee is utilization-driven and always positive, so extremes mark crowding | No funding/borrow-rate history |
| 2 | Realised-vol regime switch (HMM/threshold) | Conditions *which* family to run; this sweep shows trend and reversion invert between regimes | Obtainable — needs implementation, not new data |
| 3 | Cross-sectional momentum vs majors | Strongest documented anomaly family (Jegadeesh-Titman) | No peer universe fetched |
| 4 | Stablecoin-flow / exchange-netflow | Leading indicator of buying power entering the chain | No on-chain data |
| 5 | Cointegration vs ETH/BTC | Engle-Granger/Johansen spread z-score; crypto majors co-move strongly | No peer price series |
| 6 | Order-book imbalance / depth | Highest-frequency edge available | No L2 data |
| 7 | Open-interest divergence | OI rising into flat price marks leverage build-up | No OI history |
| 8 | Implied-vs-realised vol spread | Variance-risk-premium harvest | No options surface |
| 9 | Staking-ratio / validator-flow | SOL-specific float dynamics | No on-chain data |
| 10 | Social/dev-activity sentiment | Documented 1–2 day decay; noisy | No sentiment feed |

---

## List 2 — Most likely pairs to backtest

**This is a hypothesis-generation list, not a findings list.** With ~45 mechanisms there are
~990 possible pairs; ranking that space by measured performance is textbook data-snooping and
its top rows would be predominantly noise. Ranking is therefore by **a priori
complementarity** — does the partner see something the primary is structurally blind to —
with measured results attached where the pair was actually run.

**The original smaller phase reported 140 pairs per horizon (420 total). The retained 25-strategy single-split population contains 272 / 294 / 280 evaluated pairs at short / medium / long horizons (846 total), all cross-family by construction.**
Combining two trend signals mostly measures the same thing twice, so same-family pairs were
never generated.

## Ranked by mechanical complementarity

| # | Pair | Why they are complementary (mechanism) | Measured |
|---|---|---|---|
| 1 | **regime filter + mean-reversion** (`sma_regime` + `zscore`) | Mean-reversion's fatal mode is buying dips in a downtrend; the regime filter is the only thing that answers "is there a downtrend". Directly patches the primary's failure. | ✅ Best measured short-horizon pair: **OOS Sharpe +2.572** (IS −1.407), +9.0% on 18 trades |
| 2 | **trend + volume confirmation** (`ma_crossover` + `obv_trend`) | Price-based trend cannot distinguish a move on real participation from a drift on none; OBV combines the sign of price changes with volume; it can add participation information but is not price-blind. | ✅ Evaluated at all horizons |
| 3 | **breakout + volatility-squeeze filter** (`bb_breakout` + low-bandwidth gate) | Breakouts fail most when volatility is already expanded; the squeeze condition selects for contraction-before-expansion. | ⚠️ Squeeze gate implemented but not swept (`squeeze_lookback` defaults to off) |
| 4 | **oscillator + mean-reversion** (`stochastic` + `bb_reversion`) | Two different formulations of "stretched": one on momentum, one on price distance. Agreement is intended to raise precision; this rationale alone does not show that it does. | ⚠️ **OOS Sharpe +0.618** short (IS −0.383), 36 trades. The `zscore` variant of this pair scored +1.258 and is no longer built; on a 36-trade sample the two are one result reported twice — see the small-sample caveat below the pair tables |
| 5 | **trend + breakout** (`ts_momentum` + `breakout`) | Trend confirms direction, breakout times entry; addresses trend-following's late-entry problem. | ✅ **OOS +0.100** medium, 10 trades |
| 6 | **momentum + oscillator brake** (`macd` + `stochastic`) | Stops momentum from adding exposure into an already-exhausted move. | ✅ **OOS +0.391** medium (IS +0.223), 10 trades |
| 7 | **breakout + reversion exit** (`breakout` + `bb_reversion`, `any` mode) | Breakout for entry, reversion for the exit the breakout rule handles badly. | ❌ **OOS Sharpe +0.174 on −11.8%** medium, 16 trades — positive Sharpe, negative money. The `zscore` variant scored +0.584 on +30.8%; measured as combinations the two are **0.968 correlated**, so the 42-point gap is 16-trade noise rather than two different strategies. Neither number should be trusted at that sample size |
| 8 | **vol-target overlay + any directional signal** (`voltarget` × …) | Changes exposure size rather than selecting a new direction. Return and signal orthogonality remain untested; a directional core can still produce correlated returns. | ⚠️ Swept as a single, not yet as a wrapper |
| 9 | **reversion + volume** (`vwap_reversion` + `obv_trend`) | Distinguishes a discount with accumulation from one with distribution. | ✅ **OOS +0.186** long, 12 trades |
| 10 | **regime filter + grid** (`sma_regime` + `grid`) | Grid is short-volatility and long the range assumption; its catastrophic mode is a sustained trend, which is precisely what a regime filter vetoes. | ❌ Not swept — grid is in the candidate set but this specific pairing was not isolated |

### Measured pair results, for reference

Top rankable pairs per horizon. **Note the pattern: high out-of-sample Sharpe alongside
negative in-sample Sharpe** — the reverse of overfitting, and a direct consequence of the
regime inversion at the split. These results are regime-dependent. Negative in-sample and positive out-of-sample Sharpe do not rule out selection bias.

**Short (272 evaluated, 245 rankable, 27 with positive OOS Sharpe):**

| Pair | OOS Sharpe | IS Sharpe | OOS ret | OOS trades |
|---|---|---|---|---|
| `all(sma_regime+bb_reversion)` | +2.572 | −1.691 | +9.0% | 18 |
| `all(vol_regime+bb_reversion)` | +2.489 | −0.702 | +8.4% | 18 |
| `all(sma_regime+ou_reversion)` | +1.786 | −0.882 | +5.0% | 14 |
| `all(vol_regime+ou_reversion)` | +1.539 | −0.139 | +4.2% | 14 |
| `any(ma_crossover+bb_breakout)` | +1.240 | −1.283 | +12.3% | 33 |

**Medium (294 evaluated, 194 rankable, 15 with positive OOS Sharpe):**

| Pair | OOS Sharpe | IS Sharpe | OOS ret | OOS trades |
|---|---|---|---|---|
| `all(hurst_switch+bb_reversion)` | +0.564 | +0.363 | +15.6% | 10 |
| `all(hurst_switch+vwap_reversion)` | +0.564 | −0.000 | +15.6% | 10 |
| `all(macd+stochastic)` | +0.391 | +0.223 | +9.9% | 10 |
| `any(hurst_switch+breakout)` | +0.304 | +0.777 | +6.9% | 17 |

**Long (280 evaluated, 85 rankable, 17 with positive OOS Sharpe):**

| Pair | OOS Sharpe | IS Sharpe | OOS ret | OOS trades |
|---|---|---|---|---|
| `all(dual_momentum+stochastic)` | +1.169 | +0.242 | +23.8% | 10 |
| `all(dual_momentum+bb_reversion)` | +0.784 | −0.858 | +18.3% | 11 |
| `all(ma_ribbon+ou_reversion)` | +0.719 | +0.084 | +16.3% | 20 |
| `all(dual_momentum+vwap_reversion)` | +0.668 | −0.737 | +18.1% | 15 |

> Two of the short-horizon rows this table used to lead with — `all(sma_regime+zscore)` at
> +2.572 and `all(stochastic+zscore)` at +1.258 — no longer exist. Each was the `zscore` twin of
> a `bb_reversion` combination, and only the representative one is now built. The top row is
> unchanged in value because the surviving twin scored identically (+2.572 on +9.0% over 18
> trades); what changed is that it is listed once.
>
> The medium rows repay a second look: `all(hurst_switch+bb_reversion)` and
> `all(hurst_switch+vwap_reversion)` are **not** a twin pair — `vwap_reversion` is in no
> redundancy class here — yet they post identical Sharpe, return and trade count. Two signals
> that were never measured as interchangeable can still produce one book once a gate suppresses
> the bars where they differ, which is a limit of pairwise redundancy testing rather than a
> failure of it.

> **What twin combinations actually show — an exhibit in small-sample fragility.**
> Members of a redundancy class are interchangeable *as signals*, at 0.80+ correlation on their
> own exposure vectors. Whether the combinations built from them behave the same is a separate
> question, so it was measured separately (`signal_redundancy.py --combinations`). The results
> look alarming and are not:
>
> | combination | `zscore` variant | `bb_reversion` variant | measured as combinations |
> |---|---|---|---|
> | `all(sma_regime+…)` short | +2.572 on +9.0% | +2.572 on +9.0% | corr **1.000** |
> | `all(stochastic+…)` short | +1.258 on +9.7% | +0.618 on +4.1% | — |
> | `any(breakout+…)` medium | +0.584 on **+30.8%** | +0.174 on **−11.8%** | corr **0.968**, agreement **0.977** |
>
> Read the last row carefully. Those two combinations hold the **same position 97% of the time**,
> and still finish 42 percentage points apart with opposite signs on money. The gap is produced
> by the remaining 3% of bars — across a **sixteen-trade** out-of-sample sample.
>
> So this is not evidence that collapsing the class throws away a different strategy. It is
> evidence about what a 16-trade result is worth: two books that are 97% identical can be
> separated by +30.8% and −11.8% purely by which handful of trades landed where. Any row in this
> document sitting near the 10-trade evidence floor should be read with that number in mind.
>
> The gate collapses twins only when they are measured redundant **as combinations**, not merely
> for sharing a class. Against a rule that collapsed on member correlation alone that keeps
> 46 more configurations across the three horizons, and leaves PBO unchanged in all six
> horizon/size cells — the class rule moved it in two. The search size is still printed next to every gate, because the
> denominator is what makes any top row interpretable.

> The earlier smaller-population summary reported eight positive medium-horizon pairs with 10–21 out-of-sample trades. The retained 25-strategy population has **15** positive rankable medium-horizon pairs, with **10–18** out-of-sample trades.
> At that sample size, and with 272-294 configurations searched per horizon, the Harvey-Liu-Zhu
> bar (t > 3.0) is not remotely cleared by any of them. Treat this table as a shortlist of
> **experiments worth running properly**, on more data and more out-of-sample paths.

---

## List 3 — Most likely multi-signal combinations (3+)

Same framing, more emphatically: the triple space is ~14,000 cross-family combinations. This
sweep deliberately bounded it to combinations drawn from the **top-6 out-of-sample singles per
horizon** — which is itself a selection step, and one that borrows information from the
out-of-sample window. **That makes the measured triple numbers below optimistically biased,
and they are reported only because omitting them would hide the search that happened.**

**The retained single-split output has 32 triples**: 14 short, 14 medium and 4 long. The discussion below also preserves the earlier, superseded 52-triple exploration (32 short, 20 medium, 0 long) to disclose the search that occurred. Its retired rows and counts are historical, not the current retained population.

## Ranked by a priori structure

| # | Combination | Structural rationale | Measured |
|---|---|---|---|
| 1 | **regime filter + mean-reversion + oscillator confirm** (`sma_regime` + `zscore`/`bb_reversion` + `rsi`) | The full defensive stack: regime says *whether*, reversion says *where*, oscillator says *when*. Each covers a distinct failure of the others. | ❌ **No longer evaluated, so there is no current figure for it.** Under the family-label gate this was the top short-horizon triple at **+2.555** out-of-sample (IS −1.569), +8.9%, 17 trades. But `rsi` and `bb_reversion` measure **0.841** correlated on this horizon (`rsi`/`zscore` **0.837**), so the oscillator was not confirming the reversion — it was repeating it. The measured gate excludes both variants; row 2 is the best surviving triple. See `research/signal_redundancy.py`. |
| 2 | **trend + reversion + regime** (`ma_crossover` + `zscore` + `sma_regime`) | Deliberately mixes opposed families under a regime switch, so one is live when the other is wrong. | ✅ `all(ma_crossover+zscore+sma_regime)` **OOS +1.435** (IS +1.026), +2.4%, 11 trades (short) |
| 3 | **trend + breakout + volume** (`ma_crossover` + `bb_breakout` + `obv_trend`) | Three candidate confirmations of one directional thesis; independence is unproven: slope, range expansion, participation. The combination is intended to filter entries and may reduce trade count. | ⚠️ Partially — `vote(ma_crossover+sma_regime+bb_breakout)` OOS +0.295, 607 trades |
| 4 | **vol-target × (trend + regime)** | Sizing overlay on a directional core; should improve drawdown without changing hit rate. | ❌ Not swept as a wrapper |
| 5 | **regime + reversion + volume** | Adds "is the dip being accumulated" to the row-1 stack. | ❌ Not swept |
| 6 | Any triple using **`vote` mode across 3 opposed families** | Continuous exposure scaling with agreement, rather than the binary all/none of `all`. | ✅ Swept; **0 of 10 rankable medium triples had positive OOS Sharpe** |

### What the earlier, superseded triple exploration showed

- **Short horizon:** 10 of 24 rankable triples positive. Best two (`all(bb_reversion+sma_regime+rsi)`
  and `all(zscore+sma_regime+rsi)`) are **numerically identical at +2.555**, and the reason is
  a defect in my own strategy set, provable from the source rather than guessed:

  ```
  bb_reversion entry :  close < mean - 2*sd(ddof=0)   <=>  (close-mean)/sd_0 <  -2
  zscore       entry :  (close-mean)/sd(ddof=1) <= -2 <=>  (close-mean)/sd_1 <= -2
  where sd_1 = sd_0 * sqrt(n/(n-1)) = sd_0 * sqrt(20/19) ~ 1.026 * sd_0
  ```

  It is the **same inequality**, differing only in the standard-deviation convention — which
  makes the z-score entry about 2.6% stricter. The exits are exactly equivalent
  (`close > mid` ⟺ `z > 0`). So `zscore_20_-2` and `bb_reversion_20_2` are one mechanism
  entered at two marginally different thresholds, not two signals.

  **That is a warning, not a discovery.** Two rows in List 1 and several "cross-family" pairs
  are double-counting one mechanism, so the diversity implied by the configuration counts is
  overstated. Family labels are not a substitute for measuring pairwise signal correlation,
  which this sweep does not do — see item 3 in *What to actually do next*. It also means the
  two identical `+2.555` triples are one result reported twice, not independent corroboration.
- **Medium horizon: 0 of 10 rankable triples had a positive out-of-sample Sharpe.** Best was
  `vote(zscore+stochastic+sma_regime)` at **−0.002**. Adding a third signal did not help.
- **Long horizon:** no triples ran — insufficient rankable singles.

### The honest summary on combinations

More signals reduced trade count toward the evidence floor faster than they improved
out-of-sample Sharpe. The `all` mode's precision gain is real but buys it with sample size,
which is exactly the wrong trade when out-of-sample evidence is already thin. **Nothing in
List 3 is demonstrated. The top rows are the experiments most worth running on more data.**

---

## Lists 2 & 3 under CPCV — the combination result

**The retained 25-strategy CPCV outputs contain 272 / 294 / 280 pairs and 60 / 70 / 70 triples at short / medium / long horizons.** Earlier text used 334 pairs per horizon; that denominator does not match the retained files.
The positive-median counts below coexist with mixed PBO comparisons. Daily pairs have lower PBO than daily singles (**0.650 versus 0.700**); long triples are lower still (**0.543**), whereas medium triples are higher (**0.886**). Short pairs and triples are also below short singles (**0.229 / 0.086 versus 0.343**). These separate candidate populations do not establish that combining generally worsens rank generalisation.

> **The block-count caveat applies here too, and the one measurement I have says it bites harder.**
> Finding 1f swept block counts across the 25 *singles*; I did not repeat that sweep over the
> 846 pairs and 200 triples, so the aggregate figures below are for 8 blocks only and their
> ordering has not been tested for geometry stability. What I do have is a single measured point
> from finding 1d: moving the top pair from 8 blocks to 9 changed its median Sharpe by
> **−0.441**, a larger move than any ±10% parameter perturbation produced (**−0.392** at worst).
> Combinations gate each other and so trade less than their components, which is the same
> few-trades mechanism that makes the long-horizon singles unstable — expect these orderings to
> be *less* geometry-stable than List 1's, not more. Treat every rank below as unranked.

| Configuration type | PBO (short) | PBO (medium) | PBO (long) |
|---|---|---|---|
| Singles (25) | 0.343 | **0.700** | **0.700** |
| **Pairs** (272/294/280) | 0.229 | **0.650** | **0.650** |
| **Triples** (60/70/70) | 0.086 | **0.886** | **0.543** |

Recall the constructed-control calibration: **mean PBO 0.500 for pure noise and 0.000 for the ordered signal set**. PBO is the fraction of tested splits where the in-sample winner lands below the out-of-sample candidate median. A daily value above 0.500 means that rank event occurred in more than half the splits; it is not an expected-profit or expected-Sharpe comparison with a random-selection policy.

And the trap is baited harder than before:

| | positive median Sharpe |
|---|---|
| Long pairs | **211 of 252 (83.7%)** |
| Long triples | **45 of 47 (96%)** |
| Medium pairs | 177 of 260 (68.1%) |

The highest median Sharpe in the retained pair tables is `all(dual_momentum+vol_regime)` at the long
horizon: median Sharpe **+1.345**, 87% of paths positive, **+75.1%** median path return. It is
also, by the PBO of 0.650 sitting above it, exactly the row you should not trust — it is the top
of a 252-evaluable-configuration search whose ranking is anti-informative. That tension is the finding.

## List 2 under CPCV — pairs

**SHORT** — 272 evaluated, 262 evaluable, **8** with positive median Sharpe. **PBO = 0.229.**

| # | combination | families | median Sharpe | IQR | % paths + | median ret | trades |
|---|---|---|---|---|---|---|---|
| 1 | `all(vol_regime+ou_reversion)` | regime-filter+mean-reversion | **+0.944** | 2.244 | 71% | +1.4% | 68 |
| 2 | `all(ma_crossover+ou_reversion)` | trend+mean-reversion | **+0.919** | 2.168 | 71% | +1.6% | 94 |
| 3 | `all(vol_regime+bb_reversion)` | regime-filter+mean-reversion | **+0.834** | 2.726 | 71% | +1.9% | 84 |
| 4 | `all(ou_reversion+obv_trend)` | mean-reversion+volume-flow | **+0.688** | 3.779 | 52% | +1.4% | 104 |
| 5 | `all(sma_regime+bb_reversion)` | sma-gated+mean-reversion | **+0.549** | 2.866 | 62% | +1.6% | 112 |
| 6 | `all(ichimoku+ou_reversion)` | trend+mean-reversion | **+0.400** | 3.146 | 57% | +0.7% | 56 |
| 7 | `all(sma_regime+ou_reversion)` | sma-gated+mean-reversion | **+0.268** | 1.834 | 52% | +0.4% | 92 |
| 8 | `all(adx_trend+stochastic)` | regime-filter+oscillator-reversion | **+0.126** | 1.778 | 52% | +0.2% | 150 |

_Top 8 of 262 evaluable._

> The two rows that used to sit at #1 and #6 — `all(vol_regime+zscore)` at +1.091 and
> `all(sma_regime+zscore)` at +0.681 — are gone, not demoted. Each was the `zscore` twin of a
> `bb_reversion` row still in the table, and the measured gate now builds only one of each pair.
> Removing them cost the table its highest median Sharpe: the best surviving short-horizon pair
> is +0.944, down from +1.091. That is the point rather than a regression — the +1.091 row was
> one bet listed twice, and its rank was propped up by its own duplicate.

**MEDIUM** — 294 evaluated, 260 evaluable, **177** with positive median Sharpe. **PBO = 0.650.**

| # | combination | families | median Sharpe | IQR | % paths + | median ret | trades |
|---|---|---|---|---|---|---|---|
| 1 | `any(hurst_switch+ou_reversion)` | regime-filter+mean-reversion | **+1.290** | 0.972 | 100% | +68.9% | 40 |
| 2 | `all(stochastic+ou_reversion)` | oscillator-reversion+mean-reversion | **+1.156** | 0.584 | 93% | +30.1% | 18 |
| 3 | `any(bb_breakout+ou_reversion)` | breakout+mean-reversion | **+1.052** | 1.198 | 87% | +67.1% | 76 |
| 4 | `any(macd+ou_reversion)` | trend+mean-reversion | **+0.996** | 0.929 | 87% | +84.3% | 100 |
| 5 | `any(macd+hurst_switch)` | trend+regime-filter | **+0.925** | 1.083 | 93% | +72.6% | 118 |
| 6 | `any(hurst_switch+bb_breakout)` | regime-filter+breakout | **+0.924** | 1.380 | 87% | +48.3% | 72 |
| 7 | `all(ma_ribbon+hurst_switch)` | trend+regime-filter | **+0.881** | 1.238 | 93% | +7.9% | 25 |
| 8 | `any(hurst_switch+stochastic)` | regime-filter+oscillator-reversion | **+0.875** | 1.080 | 87% | +53.5% | 58 |

_Top 8 of 260 evaluable._ `all(ma_ribbon+hurst_switch)` survives here even though `ma_ribbon` and
`ma_crossover` measure 0.846 correlated as standalone signals: paired with `hurst_switch` the two
combinations are not the same experiment, so both are built. An earlier class-based rule dropped
this row on the strength of the member correlation alone.

**LONG** — 280 evaluated, 252 evaluable, **211** with positive median Sharpe. **PBO = 0.650.**

| # | combination | families | median Sharpe | IQR | % paths + | median ret | trades |
|---|---|---|---|---|---|---|---|
| 1 | `all(dual_momentum+vol_regime)` | momentum+regime-filter | **+1.345** | 0.881 | 87% | +75.1% | 52 |
| 2 | `any(adx_trend+ou_reversion)` | regime-filter+mean-reversion | **+1.162** | 1.423 | 67% | +87.6% | 34 |
| 3 | `any(ou_reversion+obv_trend)` | mean-reversion+volume-flow | **+1.054** | 1.180 | 93% | +93.6% | 90 |
| 4 | `all(macd+vol_regime)` | trend+regime-filter | **+0.991** | 0.957 | 87% | +42.0% | 34 |
| 5 | `any(hurst_switch+ou_reversion)` | regime-filter+mean-reversion | **+0.965** | 1.049 | 93% | +42.6% | 46 |
| 6 | `all(dual_momentum+stochastic)` | momentum+oscillator-reversion | **+0.937** | 1.089 | 95% | +23.4% | 66 |
| 7 | `any(vol_regime+rsi)` | regime-filter+oscillator-reversion | **+0.927** | 0.868 | 100% | +57.9% | 60 |
| 8 | `any(hurst_switch+obv_trend)` | regime-filter+volume-flow | **+0.919** | 1.534 | 100% | +63.1% | 88 |

_Top 8 of 252 evaluable._

## List 3 under CPCV — triples

Drawn from a **fixed a-priori set of seven** (one per family), chosen before any CPCV number was
seen, so these carry no selection bias from the singles ranking. Unchanged from the 16-strategy
run, which keeps them comparable across both sweeps.

**SHORT** — 60 evaluated, 52 evaluable, **5** with positive median Sharpe. **PBO = 0.086.**

| # | combination | families | median Sharpe | IQR | % paths + | median ret | trades |
|---|---|---|---|---|---|---|---|
| 1 | `all(ma_crossover+sma_regime+zscore)` | trend+sma-gated+mean-reversion | **+1.907** | 2.680 | 76% | +2.7% | 62 |
| 2 | `all(sma_regime+zscore+obv_trend)` | sma-gated+mean-reversion+volume-flow | **+1.844** | 2.091 | 81% | +2.3% | 42 |
| 3 | `all(sma_regime+rsi+obv_trend)` | sma-gated+oscillator-reversion+volume-flow | **+0.950** | 2.734 | 67% | +1.8% | 68 |
| 4 | `all(ts_momentum+sma_regime+zscore)` | momentum+sma-gated+mean-reversion | **+0.708** | 2.138 | 71% | +0.5% | 26 |
| 5 | `all(ma_crossover+ts_momentum+zscore)` | trend+momentum+mean-reversion | **+0.239** | 1.847 | 62% | +0.2% | 44 |
| 6 | `all(ts_momentum+sma_regime+rsi)` | momentum+sma-gated+oscillator-reversion | **-0.104** | 2.363 | 48% | -0.2% | 58 |
| 7 | `all(ma_crossover+sma_regime+rsi)` | trend+sma-gated+oscillator-reversion | **-0.458** | 1.902 | 38% | -0.9% | 88 |
| 8 | `all(ma_crossover+zscore+obv_trend)` | trend+mean-reversion+volume-flow | **-0.485** | 3.945 | 29% | -0.1% | 22 |

_Top 8 of 52 evaluable._

> **This table is the record of a wrong turn, kept because the wrong turn is
> instructive.** An intermediate gate collapsed every combination that merely *contained* a
> member of a redundancy class. Under it this table showed **1** positive triple instead of 5,
> and PBO rose from **0.086** to **0.229** — which read as "deduplication exposes a noisier
> ranking, the low figure was measuring how well a configuration predicts its own duplicate".
>
> That reading was wrong, and measuring the combinations directly is what showed it. `zscore` and
> `rsi` are interchangeable *as standalone signals* on this horizon (minimum pairwise 0.837), but
> the triples built from them are **not** the same experiment — a third member changes which bars
> either may act on. Collapsing them discarded 16 distinct configurations, and the PBO rise was an
> artifact of that over-collapsing, not a property of duplicates. With redundancy measured on the
> combinations themselves, PBO returns to **0.086** and the five positives return with it.
>
> In this experiment, the combination-based deduplication left PBO unchanged in all **six horizon/size cells**. That is an observed result, not a universal correctness test: valid deduplication can change a rank-based statistic when candidate multiplicities change. A PBO change alone does not establish that a deduplication rule is wrong.

**MEDIUM** — 70 evaluated, 51 evaluable, **38** with positive median Sharpe. **PBO = 0.886.**

| # | combination | families | median Sharpe | IQR | % paths + | median ret | trades |
|---|---|---|---|---|---|---|---|
| 1 | `all(sma_regime+breakout+obv_trend)` | regime-filter+breakout+volume-flow | **+0.380** | 1.880 | 52% | +9.6% | 82 |
| 2 | `all(ts_momentum+breakout+obv_trend)` | momentum+breakout+volume-flow | **+0.369** | 1.582 | 71% | +9.1% | 88 |
| 3 | `vote(breakout+zscore+obv_trend)` | breakout+mean-reversion+volume-flow | **+0.367** | 1.305 | 62% | +8.6% | 1373 |
| 4 | `vote(breakout+rsi+zscore)` | breakout+oscillator-reversion+mean-reversion | **+0.349** | 1.192 | 62% | +7.7% | 1090 |
| 5 | `vote(rsi+zscore+obv_trend)` | oscillator-reversion+mean-reversion+volume-flow | **+0.339** | 1.013 | 62% | +7.4% | 1312 |
| 6 | `vote(ts_momentum+breakout+zscore)` | momentum+breakout+mean-reversion | **+0.326** | 1.336 | 57% | +5.4% | 1252 |
| 7 | `vote(ts_momentum+rsi+obv_trend)` | momentum+oscillator-reversion+volume-flow | **+0.311** | 1.455 | 57% | +5.3% | 1372 |
| 8 | `vote(ts_momentum+zscore+obv_trend)` | momentum+mean-reversion+volume-flow | **+0.307** | 1.076 | 62% | +5.2% | 1438 |

_Top 8 of 51 evaluable._

**LONG** — 70 evaluated, 47 evaluable, **45** with positive median Sharpe. **PBO = 0.543.**

| # | combination | families | median Sharpe | IQR | % paths + | median ret | trades |
|---|---|---|---|---|---|---|---|
| 1 | `vote(rsi+zscore+obv_trend)` | oscillator-reversion+mean-reversion+volume-flow | **+0.732** | 0.945 | 81% | +20.4% | 1215 |
| 2 | `vote(breakout+rsi+obv_trend)` | breakout+oscillator-reversion+volume-flow | **+0.590** | 1.413 | 81% | +20.0% | 1158 |
| 3 | `vote(sma_regime+rsi+obv_trend)` | regime-filter+oscillator-reversion+volume-flow | **+0.589** | 1.501 | 76% | +19.0% | 1283 |
| 4 | `vote(ma_crossover+rsi+obv_trend)` | trend+oscillator-reversion+volume-flow | **+0.581** | 1.486 | 81% | +18.5% | 1381 |
| 5 | `vote(ts_momentum+rsi+obv_trend)` | momentum+oscillator-reversion+volume-flow | **+0.564** | 1.695 | 71% | +21.4% | 1364 |
| 6 | `vote(sma_regime+zscore+obv_trend)` | regime-filter+mean-reversion+volume-flow | **+0.512** | 1.702 | 76% | +17.6% | 1398 |
| 7 | `all(ma_crossover+sma_regime+obv_trend)` | trend+regime-filter+volume-flow | **+0.507** | 1.397 | 81% | +18.0% | 42 |
| 8 | `all(rsi+zscore+obv_trend)` | oscillator-reversion+mean-reversion+volume-flow | **+0.475** | 1.012 | 57% | +0.7% | 10 |

_Top 8 of 47 evaluable._
---

## What the original study proposed next

Ranked by expected information gain per unit of work, which is a different question from
"which strategy won":

1. ~~Replace the single 70/30 split with CPCV.~~ **Done** — `backtester/core/cpcv.py`, and it
   changed the answer: buy-and-hold went from mid-table to first at the medium horizon, and the
   long horizon became evaluable at all (16/16 versus 4/16). PBO 0.43–0.46 now quantifies what
   the single split could only hint at.
2. **Get more assets. Longer daily history was not obtainable from this environment** —
   Coinbase's backward pagination walked to **2021-06-17** and could make no further progress,
   which is consistent with that being its SOL-USD listing date. *Evidence limit, stated
   precisely:* that conclusion comes from the pagination loop terminating, not from a direct
   observation of an empty response for an earlier window — a direct probe of 2020-04→2021-06 was
   attempted and could not complete, because outbound HTTP to every venue with 2020 SOL history
   (Binance geo-blocked; Kraken, OKX, Gate, KuCoin, Bybit unreachable) hangs from this network.
   **Re-test before treating 2021-06-17 as a hard floor.** CPCV largely absorbed the need
   regardless: it fixed the long-horizon evidence problem the extra history was meant to fix. A
   **peer universe** remains the higher-value data addition, because it unlocks the
   cross-sectional-momentum and cointegration families that are currently spec-only.
3. **Measure pairwise signal correlation before calling a pair orthogonal.** The identical
   `+2.555` triples prove family labels are not enough.
4. **Add funding/borrow-rate history.** It is the highest-ranked spec-only signal and it is
   also a direct input to the perp cost model already implemented in `backtester/core/perps.py`.
5. **Test the vol-target overlay as a wrapper**, not as a standalone strategy. It is the one
   candidate here intended to change sizing rather than direction; statistical orthogonality would still need testing.
6. **Apply a deflated Sharpe ratio** to any survivor, accounting for the 953 trials already run.
7. **Add a parameter-perturbation stability check to the sweep itself.** Finding 4 shows a 2.6%
   threshold change moving an out-of-sample return by 46 percentage points. Every ranked row
   should be re-run at ±10% on each parameter and reported with the spread; rows whose result
   is not stable under that perturbation should be excluded from ranking the way thin-evidence
   rows already are.

## Reproducing every number

```bash
python3 research/cpcv_sweep.py                  # List 1 (primary): CPCV + PBO
python3 research/cpcv_sweep.py --groups 8 --k 2  # tune the block/path geometry
python3 research/sweep.py                       # List 1b/2/3: the single-split sweep
python3 research/verify_numbers.py              # assert every figure here matches the results
python3 -m unittest discover -s backtester/tests -t .   # original report listed 103 tests; not rerun for publication
```

`verify_numbers.py` extracts every performance figure from this document and from
[the sol strategy reference study](/blog/research/sol-strategy-reference/) and asserts each one appears in `results/sweep_results.csv` within rounding
tolerance. The read-only publication check verified **1,084 parsed figures** against the archived outputs and exits non-zero on any mismatch — so the
claim "no number was estimated" is enforced mechanically rather than promised.

Outputs land in `research/results/`: `sweep_results.csv` (one row per configuration),
`tables.md` (generated tables), `configuration_counts.json` (the denominators).

**Cost model for every number above:** 6bps taker fee + 2bps slippage per fill, charged on
notional at the fill price; signal at bar *t* fills at bar *t+1*'s open; spot mode, no leverage.
Hourly results additionally carry 2 disclosed data gaps (largest 6h, around Oct 2025).

> Educational and research use only. NOT investment advice. Nothing here is evidence that any
> listed strategy is profitable; the measured evidence is that on this asset and window, almost
> none of them were.
