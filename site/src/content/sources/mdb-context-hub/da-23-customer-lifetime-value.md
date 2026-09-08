---
title: "Customer Lifetime Value Modeling"
description: "Customer Lifetime Value (CLV) is the present value of the future cash flows attributed to a customer relationship. This skill covers the probabilistic 'buy-till-you-die' (BTYD) family — statistical mo"
---

# Customer Lifetime Value Modeling (Probabilistic / BTYD)

## Overview

Customer Lifetime Value (CLV) is the present value of the future cash flows attributed to a customer relationship. This skill covers the **probabilistic "buy-till-you-die" (BTYD) family** — statistical models that decompose CLV into (1) *how often* a customer transacts while active, (2) *whether/when* they silently churn, and (3) *how much* they spend per transaction — then discount the expected future stream to present value.

Two orthogonal axes define the model landscape (Fader/Hardie taxonomy):

| | **Non-contractual** (churn unobserved) | **Contractual** (churn observed at renewal) |
| --- | --- | --- |
| **Continuous time** | Pareto/NBD, BG/NBD, MBG/NBD (+ Gamma-Gamma for spend) | survival models → **da-24** |
| **Discrete time** | BG/BB (beta-geometric / beta-Bernoulli) | sBG (shifted-beta-geometric) |

Choosing the wrong quadrant is the #1 modeling error. Subscriptions/SaaS are **contractual** (you see the cancellation) → sBG / survival. Retail, e-commerce, donations are **non-contractual** (you infer churn) → Pareto/NBD family.

Authoritative source corpus: Bruce Hardie's notes (brucehardie.com), the Fader/Hardie/Lee Marketing Science papers, and the three reference implementations — `lifetimes` (Python, archived), `CLVTools` (R), and `PyMC-Marketing` (Python, Bayesian, the active successor).

## Core Concepts

### 1. The buy-till-you-die (BTYD) framework
A customer is "alive" until an unobserved dropout, transacting stochastically while alive. Models pair a **counting process** (transactions while alive) with a **timing process** (lifetime/dropout), each with cross-customer heterogeneity. First introduced by Schmittlein, Morrison & Colombo, "Counting Your Customers: Who Are They and What Will They Do Next?", *Management Science* 33(1):1–24 (1987) (https://pubsonline.informs.org/doi/10.1287/mnsc.33.1.1). Lineage: Retina.ai "History of BTYD" (2023).

### 2. Pareto/NBD
The original non-contractual continuous-time model. **NBD** (Poisson–gamma mixture) for transaction counts while alive; **Pareto** (exponential–gamma mixture) for the unobserved lifetime. Four parameters (r, α, s, β). Powerful but numerically awkward (Gaussian hypergeometric functions), which motivated BG/NBD. (Schmittlein et al. 1987; CLVTools `pnbd`; PyMC-Marketing Pareto/NBD notebook.)

### 3. BG/NBD ("Counting Your Customers the Easy Way")
The workhorse. Replaces Pareto's continuous dropout with a **beta-geometric** story: a customer flips a coin to churn *immediately after each transaction* (prob. p, beta-distributed across customers); active counts are NBD. Far easier to fit (estimable in Excel), nearly identical predictive accuracy. Fader, Hardie & Lee, *Marketing Science* 24(2):275–284 (2005) (http://brucehardie.com/papers/018/fader_et_al_mksc_05.pdf). **Quirk:** in BG/NBD a customer cannot churn until *after* their first repeat purchase, so it understates one-and-done customers — which MBG/NBD fixes.

### 4. MBG/NBD (Modified BG/NBD)
Adds a dropout opportunity at time zero (right after the first purchase), so customers who never repeat can be "dead". Expected-repeat estimates nearly match BG/NBD, but alive/dead classification of zero-repeat customers is more realistic. Batislam, Denizel & Filiztekin, *IJRM* 24(3) (2007); implemented as `ModifiedBetaGeoModel`.

### 5. Gamma-Gamma monetary model
Separately models **spend per transaction** (frequency models only predict counts). Assumptions: (a) value varies randomly around the customer's mean; (b) mean spend varies across customers but not over time; (c) spend is independent of the transaction process — **verify frequency and monetary value are roughly uncorrelated before trusting it.** Fit only on repeat purchasers. Fader, Hardie & Lee, "RFM and CLV: Using Iso-Value Curves", *JMR* 42(4):415–430 (2005) (https://www.brucehardie.com/papers/rfm_clv_2005-02-16.pdf).

### 6. RFM as model inputs (sufficient statistics)
BTYD models need only per-customer **Recency, Frequency, and "T"** — R and F are *sufficient statistics* for the likelihood. Conventions (easy to get wrong):
- **frequency** = number of *repeat* purchases (total − 1).
- **recency** = time between **first and last** purchase (NOT time since last purchase, the marketing-RFM convention).
- **T** = customer "age" = first purchase to end of observation.
- **monetary_value** = average value of repeat transactions.

### 7. Discounted Expected Residual Transactions (DERT) → CLV
CLV (non-contractual) = **(expected spend from Gamma-Gamma) × DERT**, where DERT is the present value of all expected future transactions discounted to the end of the calibration period (integral from T to ∞). Use a **continuously-compounded** discount rate (e.g. 15%/yr ≈ 0.0027/week). Fader/Hardie originally called this DET. (RFM-CLV 2005; CLVTools `pnbd_DERT`; Fader/Hardie note 033.)

### 8. sBG — shifted-beta-geometric (contractual / discrete churn)
**Subscriptions/contractual** settings: each period a customer renews with prob. θ or cancels with 1−θ; θ is fixed per customer, beta-distributed across the base. Projects observed retention into a full survival curve and explains the **observed rise in aggregate retention over time** as a heterogeneity sorting effect, not behavior change. Fader & Hardie, "How to Project Customer Retention", *J. Interactive Marketing* 21(1):76–90 (2007); extended in "Customer-Base Valuation in a Contractual Setting", *Marketing Science* 29(1):85–93 (2010).

### 9. BG/BB — discrete-time non-contractual
Discrete-time analog of Pareto/NBD: transactions per period are Bernoulli (buy/no-buy) instead of Poisson, paired with a beta-geometric dropout — for "transaction opportunities" data (annual donations, periodic catalog buyers). Closed-form. Fader, Hardie & Shang, *Marketing Science* 29(6):1086–1108 (2010); lifetimes `BetaGeoBetaBinomFitter`.

### 10. Predictive vs. historical CLV
**Historical CLV** sums realized past margin (backward-looking). **Predictive CLV** forecasts future value via models (BTYD, ML, or naive ARPU/churn). The naive `ARPU ÷ churn` shortcut assumes a single constant retention rate — biased low when retention is heterogeneous (Fader/Hardie 2010). Prefer model-based predictive CLV with uncertainty intervals.

### 11. Cohort-based CLV
Group customers by acquisition period and track value per cohort. Reveals retention dynamics and acquisition-quality drift a base-wide average masks; pairs with sBG on multicohort data. (Keep retention-curve fitting itself in **da-34**; here it is a CLV input/segmentation lens.)

### 12. CAC:LTV ratio (unit economics)
LTV:CAC measures payback on acquisition spend. Rules of thumb: **~3:1 healthy target** (B2C SaaS ≈ 2.5:1, B2B SaaS ≈ 4:1); below 2:1 = unsustainable; above ~5:1 = likely under-investing. CAC payback: healthy 6–12 months, elite < 3 months. Use a **margin-based, discounted** predictive LTV — gross-revenue LTV inflates the ratio.

## Tools / Frameworks

| Tool | Lang | Notes |
| --- | --- | --- |
| **PyMC-Marketing** | Python | **Active successor**; Bayesian (MCMC), full uncertainty. `BetaGeoModel`, `ParetoNBDModel`, `ModifiedBetaGeoModel`, `ShiftedBetaGeoModel`, `BetaGeoBetaBinomModel`, `GammaGammaModel`; `rfm_summary()` preprocessor. |
| **lifetimes** | Python | Cam Davidson-Pilon; **archived / maintenance-only**, MLE fitters. Migrate new work to PyMC-Marketing. |
| **CLVTools** | R | S4 API, covariates, `pnbd`/`bgnbd`/`ggomnbd`/`gg`, built-in DERT/DECT. |
| **BTYD / BTYDplus** | R | Classic R packages; closed-form Pareto/NBD, BG/NBD, BG/BB. |

## Methodology (non-contractual continuous: common case)

1. **Confirm the quadrant.** Non-contractual + continuous → proceed. Contractual → sBG/survival. Discrete opportunities → BG/BB.
2. **Build RFM summary** (`rfm_summary()` / lifetimes `summary_data_from_transaction_data`). Watch the recency definition.
3. **Fit a frequency/dropout model** (BG/NBD default; MBG/NBD if many one-and-done; Pareto/NBD as benchmark).
4. **Check the model**: holdout calibration, tracking plot, `P(alive)` distribution.
5. **Fit Gamma-Gamma on repeat purchasers**; first verify low corr(frequency, monetary).
6. **Compute discounted CLV** = E[spend] × DERT over a finite horizon, continuously-compounded discount rate.
7. **Validate** on a holdout window by RFM decile.
8. **Segment / act**: rank by predicted CLV and `P(alive)`; feed CAC:LTV.

## Anti-Patterns

- **Wrong quadrant** (Pareto/NBD on a subscription business, or sBG on e-commerce).
- **Marketing-RFM recency** ("days since last purchase" instead of "first-to-last span") — silent severe bias.
- **Gamma-Gamma without the independence check.**
- **Naive ARPU ÷ churn as ground truth** — biased low under heterogeneity.
- **Un-discounted / infinite-horizon CLV** — inflates value and LTV:CAC.
- **Fitting Gamma-Gamma on all customers** instead of repeat purchasers only.
- **Trusting `lifetimes` for new long-lived projects** — it's archived.

## Troubleshooting

- **`P(alive)` implausibly high for everyone** → BG/NBD with many one-and-done customers; switch to MBG/NBD.
- **Optimizer fails / NaN log-likelihood (Pareto/NBD)** → numerical instability in hypergeometric terms; use log-sum-exp-patched BTYD or BG/NBD.
- **Gamma-Gamma returns absurd spend** → filter to frequency > 0; use *average repeat* value, not total.
- **Holdout over-predicted** → calibration window caught a promo spike; re-split or model seasonality outside BTYD.
- **CLV explodes** → infinite horizon or zero discount rate; cap horizon, set continuously-compounded rate.

## References

1. Schmittlein, Morrison & Colombo, *Management Science* 33(1):1–24 (1987) — https://pubsonline.informs.org/doi/10.1287/mnsc.33.1.1
2. Fader, Hardie & Lee, BG/NBD, *Marketing Science* 24(2):275–284 (2005) — http://brucehardie.com/papers/018/fader_et_al_mksc_05.pdf
3. Fader, Hardie & Lee, RFM and CLV / Gamma-Gamma + DERT, *JMR* 42(4):415–430 (2005) — https://www.brucehardie.com/papers/rfm_clv_2005-02-16.pdf
4. Fader & Hardie, Gamma-Gamma note 025 — https://www.brucehardie.com/notes/025/gamma_gamma.pdf
5. Fader & Hardie, sBG / "How to Project Customer Retention", *J. Interactive Marketing* 21(1):76–90 (2007)
6. Fader & Hardie, "Customer-Base Valuation in a Contractual Setting", *Marketing Science* 29(1):85–93 (2010) — http://brucehardie.com/papers/022/fader_hardie_mksc_10.pdf
7. Fader, Hardie & Shang, BG/BB, *Marketing Science* 29(6):1086–1108 (2010) — http://www.brucehardie.com/papers/020/fader_et_al_mksc_10.pdf
8. Batislam, Denizel & Filiztekin, MBG/NBD, *IJRM* 24(3) (2007)
9. Fader & Hardie, "What's Wrong With This CLV Formula?" note 033 — http://www.brucehardie.com/notes/033/what_is_wrong_with_this_CLV_formula.pdf
10. PyMC-Marketing CLV docs (v0.15.x, 2024–2025) — https://www.pymc-marketing.io/en/stable/notebooks/clv/clv_quickstart.html
11. CLVTools (R) — https://www.clvtools.com/
12. lifetimes (Python, archived) — https://github.com/CamDavidsonPilon/lifetimes
13. Phoenix Strategy Group, LTV:CAC SaaS benchmarks — https://www.phoenixstrategy.group/blog/ltvcac-ratio-saas-benchmarks-and-insights
