---
title: "Conformal Prediction and Uncertainty Quantification"
description: "Conformal prediction (CP) turns any point predictor into a set predictor with a"
---

# Conformal Prediction & Uncertainty Quantification

## Overview

Conformal prediction (CP) turns any point predictor into a set predictor with a
**finite-sample, distribution-free marginal coverage guarantee**. Given a target
miscoverage rate alpha, CP outputs a prediction set C(X) such that
P(Y in C(X)) >= 1 - alpha — holding for any underlying model, any data
distribution, and any sample size, requiring only that the calibration and test
data are **exchangeable**. It is a wrapper, not a model. You keep your XGBoost,
neural net, or random forest and bolt CP on top to get honest error bars.

CP is the dominant frequentist answer to "how do I get valid uncertainty without
trusting my model's probabilities." Compared to Bayesian credible intervals
(which require a correct prior/likelihood) and the bootstrap (asymptotic, can
under-cover), CP's guarantee is exact in finite samples and model-agnostic. The
modern reference is Angelopoulos & Bates, "A Gentle Introduction to Conformal
Prediction and Distribution-Free Uncertainty Quantification" (arXiv 2107.07511,
v-series 2021-2023). The theoretical foundation is Vovk, Gammerman & Shafer,
"Algorithmic Learning in a Random World" (Springer, 2005; 2nd ed. 2022).

Use this skill when someone needs **calibrated intervals/sets on top of an
existing model**. For full Bayesian modeling use da-25; for point forecasting use
da-15.

## Core Concepts

### 1. The coverage guarantee (marginal validity)
Split-conformal gives the exact two-sided bound
1 - alpha <= P(Y_{n+1} in C(X_{n+1})) <= 1 - alpha + 1/(n+1), where n is the
calibration set size. The guarantee is **marginal** (averaged over the random
draw of calibration + test points), not conditional on a specific X or a fixed
calibration set — coverage fluctuates around the target for any one fixed
calibration set, and the spread shrinks as n grows. Distribution-free and
finite-sample, no asymptotics. Source: Angelopoulos & Bates 2023
(arxiv.org/abs/2107.07511); Lei et al. "Distribution-Free Predictive Inference
for Regression" JASA 2018; Vovk et al. 2005.

### 2. Exchangeability — the one assumption
CP requires only that (X_1,Y_1)...(X_{n+1},Y_{n+1}) are **exchangeable**: their
joint distribution is invariant to permutation. This is weaker than i.i.d. but is
violated by distribution shift and temporal/serial dependence — the two main ways
CP breaks in practice. Source: Vovk et al. 2005; Barber, Candès, Ramdas &
Tibshirani "Conformal Prediction Beyond Exchangeability" Annals of Statistics
2023 (stat.cmu.edu/~ryantibs/papers/nexcp.pdf).

### 3. Nonconformity (conformity) score
A function s(x,y) measuring how "strange" a label y is for input x given the
model — e.g. residual |y - f(x)| for regression, or 1 - softmax(true class) for
classification. CP is entirely defined by your choice of score: the score
controls **adaptivity and set shape**, while the coverage guarantee holds for
*any* score. Designing a good score (heteroscedastic-aware, class-adaptive) is
the main lever for sharpness. Source: Angelopoulos & Bates 2023.

### 4. Split / Inductive Conformal Prediction (ICP)
The workhorse. (a) Split data into proper-training + calibration. (b) Fit the
model on training. (c) Compute calibration scores s_i. (d) Set qhat = the
ceil((n+1)(1-alpha))/n empirical quantile of the calibration scores (the same
finite-sample-corrected quantile used in Methodology step 5). (e) For a
new x, output C(x) = { y : s(x,y) <= qhat }. One model fit, O(n log n)
calibration — cheap and the default for deep learning. The finite-sample
quantile correction (the +1) is what delivers exact validity. Source:
Papadopoulos et al. 2002 (inductive CP); Angelopoulos & Bates 2023;
github.com/aangelopoulos/conformal-prediction.

### 5. Full / Transductive Conformal Prediction
The original formulation: for each candidate label y, refit (or re-score) the
model with (x_{n+1}, y) appended and test that point's conformity rank against
all others. Uses **all** data (no calibration split, so more statistically
efficient on small data) but costs one refit per candidate label per test point —
usually intractable except with closed-form/leave-one-out shortcuts. First
proposed by Gammerman, Vovk & Vapnik 1998. Source: Vovk et al. 2005; Vovk
"Transductive Conformal Predictors" 2013 (alrw.net/articles/08.pdf).

### 6. Conformalized Quantile Regression (CQR)
Wraps a quantile regressor (estimating lower/upper conditional quantiles
q_lo, q_hi) with conformal calibration. Score is the signed exceedance
E_i = max(q_lo(x_i) - y_i, y_i - q_hi(x_i)); conformalize E to get qhat and output
[q_lo(x) - qhat, q_hi(x) + qhat]. Inherits **heteroscedastic adaptivity** from
quantile regression and **valid coverage** from CP — intervals widen where the
data is noisy, producing shorter intervals than residual-based CP. Source: Romano,
Patterson & Candès, "Conformalized Quantile Regression" NeurIPS 2019
(arxiv.org/abs/1905.03222); github.com/yromano/cqr.

### 7. Classification sets — APS and RAPS
- **APS (Adaptive Prediction Sets):** score accumulates sorted softmax mass until
  the true class is included; produces sets that adapt to difficulty (bigger sets
  on hard examples). Source: Romano, Sesia & Candès, "Classification with Valid
  and Adaptive Coverage" NeurIPS 2020.
- **RAPS (Regularized APS):** adds a regularization penalty that discourages
  including low-probability tail classes, yielding 5-10x smaller, more stable sets
  than APS while keeping the coverage guarantee. Source: Angelopoulos, Bates,
  Malik & Jordan, "Uncertainty Sets for Image Classifiers using Conformal
  Prediction" ICLR 2021 (arxiv.org/abs/2009.14193);
  github.com/aangelopoulos/conformal_classification.
- **LAC / naive softmax score** (1 - p_true) gives the smallest sets but worse
  conditional coverage; APS/RAPS trade size for adaptivity.

### 8. Mondrian / group-conditional conformal
Partition (X x Y) into disjoint categories (e.g. by class, sex, region) and run a
separate conformal calibration **per category**, giving group-conditional coverage
P(Y in C(X) | group=g) >= 1 - alpha for each g. Only requires exchangeability
within each category. Limitation: groups must be **non-overlapping**; overlapping
or continuous attributes need newer methods (Kandinsky CP 2025; Gibbs et al.
conditional-guarantee CP 2023). Source: Vovk et al. 2005 (Mondrian CP);
MAPIE Mondrian docs (mapie.readthedocs.io); Ding et al. "Class-Conditional
Conformal Prediction with Many Classes" NeurIPS 2023.

### 9. Weighted conformal & covariate shift
Under covariate shift (P_test(X) != P_train(X) but P(Y|X) unchanged),
exchangeability fails and CP under/over-covers. **Weighted conformal** reweights
calibration scores by the likelihood ratio w(x) = dP_test(x)/dP_train(x) (the
"weighted exchangeability" notion) to restore validity when w is known or
estimable from unlabeled test data. Source: Tibshirani, Barber, Candès & Ramdas,
"Conformal Prediction Under Covariate Shift" NeurIPS 2019
(arxiv.org/abs/1904.06019); extended to feedback shift in Fannjiang et al. PNAS
2022.

### 10. Time series — EnbPI and ACI
Serial dependence breaks exchangeability, so two main adaptations exist:
- **EnbPI (Ensemble batch Prediction Intervals):** Xu & Xie, ICML 2021
  (proceedings.mlr.press/v139/xu21h). Uses leave-one-out ensemble residuals,
  no data split, assumes stationary strongly-mixing errors; gives approximate
  marginal coverage asymptotically.
- **ACI (Adaptive Conformal Inference):** Gibbs & Candès, NeurIPS 2021
  (arxiv.org/abs/2106.00170). Online update of the effective miscoverage level
  alpha_t after each observation; stable under arbitrary distribution shift and
  guarantees long-run coverage regardless of dependence. Variants: AgACI / DtACI,
  Zaffran et al. ICML 2022 (arxiv.org/abs/2202.07282); SPCI, Xu & Xie 2023.

### 11. Calibration vs sharpness
Two orthogonal quality axes. **Calibration/validity** = the set actually covers at
the nominal rate (a 90% interval contains Y ~90% of the time). **Sharpness/
efficiency** = sets are as small/tight as possible. CP *guarantees* marginal
calibration by construction; sharpness depends on the model and score and is the
thing you optimize. Gneiting's maxim: maximize sharpness subject to calibration.
Report average set size / interval width alongside empirical coverage. Source:
Gneiting et al. JRSS-B 2007; Angelopoulos & Bates 2023.

### 12. Conformal Risk Control (beyond coverage)
Generalizes CP from miscoverage to **any monotone bounded loss** (false-negative
rate, F1, recall), controlling E[loss] <= alpha. Useful for multilabel,
segmentation, and structured outputs. Source: Angelopoulos, Bates et al.
"Conformal Risk Control" 2022/ICLR 2024
(people.eecs.berkeley.edu/~angelopoulos/publications/downloads/conformal-risk.pdf).

## Tools / Frameworks

- **MAPIE** (Model Agnostic Prediction Interval Estimator) — scikit-learn-native,
  the standard for tabular regression/classification; split/CV+/jackknife+, CQR,
  APS/RAPS, Mondrian, conformal risk control. mapie.readthedocs.io. Use this
  first for sklearn workflows.
- **crepes** — lightweight, clean conformal regressors & predictive systems
  (Boström); good for normalized/Mondrian regression and conformal predictive
  distributions. github.com/henrikbostrom/crepes.
- **TorchCP** — PyTorch-native, GPU-accelerated; deep classifiers, regressors,
  GNNs, LLMs; APS/RAPS/SAPS, CQR, time-series CP. JMLR 2025
  (arxiv.org/abs/2402.12683). Use for deep learning.
- **PUNCC** (Deel), **Fortuna** (AWS), **nonconformist** (the original, now
  largely superseded) — alternatives; nonconformist is NumPy-only and unmaintained.
- Reference implementations: github.com/aangelopoulos/conformal-prediction
  (notebooks for every method), yromano/cqr, aangelopoulos/conformal_classification.

## Methodology (split-conformal recipe)

1. **Define the task & alpha.** Pick target coverage 1-alpha (e.g. 0.9). Decide
   regression (intervals) vs classification (sets), and whether you need marginal
   or group-conditional coverage.
2. **Three-way split.** proper-train / calibration / test. Calibration n>=~1000
   for stable 90% intervals; n>=~ a few hundred minimum. Never reuse training
   data for calibration.
3. **Fit the base model** on proper-train only.
4. **Choose a score.** Regression: residual (simple) or CQR (heteroscedastic).
   Classification: LAC (small sets) or APS/RAPS (adaptive). The score is your
   sharpness lever.
5. **Calibrate.** Compute scores on calibration set; take the finite-sample-
   corrected quantile qhat = quantile(scores, ceil((n+1)(1-alpha))/n).
6. **Predict.** C(x) = {y : s(x,y) <= qhat}.
7. **Evaluate on test:** empirical marginal coverage (should ~ 1-alpha), average
   set size / interval width (sharpness), and **size-stratified / group coverage**
   to expose conditional-coverage failures.
8. **Handle violations.** Covariate shift -> weighted CP. Time series -> EnbPI/ACI.
   Heterogeneous subgroups -> Mondrian/CQR.

## Practical Patterns

- **Default stack:** sklearn model + MAPIE split or CV+ with CQR is the 80% case
  for tabular regression. For deep classifiers use TorchCP + RAPS.
- **CV+ / jackknife+** (Barber et al. Annals 2021) when data is scarce and you
  can't afford a calibration split — gives slightly weaker (1-2alpha) guarantees
  but uses all data.
- Always **report coverage AND average width/size** — coverage alone hides a
  useless predictor that returns the whole label space.
- **Stratify coverage checks** by feature bins / class / group; marginal coverage
  can be 90% while a subgroup sits at 60%.
- For **online/streaming**, use ACI and monitor the running coverage; let alpha_t
  self-correct.
- Use a **fixed random seed for the split** and, where possible, average over
  multiple splits (or use CV+) to reduce calibration-set variance.

## Anti-Patterns

- **Calibrating on training data.** Reusing fit data destroys validity — scores
  are optimistically small and you under-cover. Always hold out calibration.
- **Trusting marginal coverage as conditional coverage.** CP guarantees marginal,
  not P(Y in C | X=x); a model can be 90% overall and badly miscalibrated per
  subgroup. Use Mondrian / size-stratified checks.
- **Ignoring exchangeability.** Applying vanilla CP to time series or shifted test
  data silently breaks the guarantee. Use ACI/EnbPI or weighted CP.
- **Optimizing the score for coverage.** Coverage is guaranteed regardless — tune
  the score for *sharpness*, not coverage.
- **Tiny calibration sets.** n in the tens makes the realized coverage swing wildly
  around the target; the +1/(n+1) slack and quantile granularity dominate.
- **Confusing CP with calibrated probabilities.** CP gives valid *sets*, not
  calibrated softmax scores; Platt/temperature scaling is a different (and
  complementary) tool.
- **Reusing the calibration set to also select alpha or the model.** That is
  double-dipping; it invalidates the guarantee.

## Troubleshooting

- **Empirical coverage below target:** check for data leakage (calibration overlaps
  training), non-exchangeability (shift/time), or too-small n. Verify the quantile
  used the (n+1) finite-sample correction.
- **Coverage fine but intervals huge:** the base model is weak or the score is
  non-adaptive; switch residual->CQR, LAC->APS/RAPS, or improve the model. Width
  is a model problem, not a CP problem.
- **Good marginal coverage, bad subgroup coverage:** move to Mondrian/
  group-conditional CP or CQR; report stratified coverage.
- **Time-series coverage drifts over time:** exchangeability violated — use ACI
  (online alpha_t update) or EnbPI; plot rolling coverage.
- **Coverage degrades after deployment:** likely covariate shift — estimate the
  likelihood ratio and apply weighted conformal, or recalibrate on fresh data.
- **Classification sets sometimes empty or all-classes:** empty sets are valid
  under some scores (force-inclusion of the top class if a non-empty set is
  required); full-label sets signal an uninformative model or too-small alpha.

## References

- Angelopoulos & Bates, "A Gentle Introduction to Conformal Prediction and
  Distribution-Free Uncertainty Quantification," arXiv:2107.07511 (2021-2023) —
  arxiv.org/abs/2107.07511. The canonical practical intro.
- Vovk, Gammerman & Shafer, "Algorithmic Learning in a Random World," Springer
  (2005; 2nd ed. 2022). Theoretical foundation.
- Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, "Distribution-Free Predictive
  Inference for Regression," JASA (2018) — split conformal for regression.
- Romano, Patterson & Candès, "Conformalized Quantile Regression," NeurIPS (2019)
  — arxiv.org/abs/1905.03222.
- Romano, Sesia & Candès, "Classification with Valid and Adaptive Coverage" (APS),
  NeurIPS (2020).
- Angelopoulos, Bates, Malik & Jordan, "Uncertainty Sets for Image Classifiers
  using Conformal Prediction" (RAPS), ICLR (2021) — arxiv.org/abs/2009.14193.
- Tibshirani, Barber, Candès & Ramdas, "Conformal Prediction Under Covariate
  Shift," NeurIPS (2019) — arxiv.org/abs/1904.06019.
- Barber, Candès, Ramdas & Tibshirani, "Predictive inference with the jackknife+,"
  Annals of Statistics (2021); and "Conformal Prediction Beyond Exchangeability,"
  Annals of Statistics (2023).
- Xu & Xie, "Conformal Prediction Interval for Dynamic Time-Series" (EnbPI), ICML
  (2021) — proceedings.mlr.press/v139/xu21h.
- Gibbs & Candès, "Adaptive Conformal Inference Under Distribution Shift" (ACI),
  NeurIPS (2021) — arxiv.org/abs/2106.00170.
- Zaffran et al., "Adaptive Conformal Predictions for Time Series" (AgACI), ICML
  (2022) — arxiv.org/abs/2202.07282.
- Angelopoulos, Bates et al., "Conformal Risk Control," ICLR (2024).
- Tooling: MAPIE (mapie.readthedocs.io), crepes (github.com/henrikbostrom/crepes),
  TorchCP (arXiv:2402.12683, JMLR 2025), aangelopoulos/conformal-prediction.
