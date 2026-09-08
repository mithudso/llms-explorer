---
title: "Survival Analysis"
description: "Modeling the time until an event happens when some observations are incomplete (censored or truncated). This is its own discipline because ordinary regression cannot use a row that says 'this customer"
---

# Survival Analysis / Time-to-Event Analysis

Modeling the *time until an event happens* when some observations are **incomplete** (censored or truncated). This is its own discipline because ordinary regression cannot use a row that says "this customer had not churned yet when we stopped looking" — survival methods extract information from exactly those incomplete rows. Canonical textbooks: Klein & Moeschberger *Survival Analysis: Techniques for Censored and Truncated Data* (2nd ed, 2003); Therneau & Grambsch *Modeling Survival Data* (2000). Primary Python tooling: **lifelines** and **scikit-survival**; R: **survival** + **survminer**.

## When to use this skill

- The outcome is a *duration* until an event: death, machine failure, churn, loan default, conversion, hospital readmission.
- Some subjects have **not** experienced the event by end of observation (censoring), or only entered observation partway through (truncation).
- You need a survival curve, hazard ratio, median time-to-event, or cumulative incidence.

## When NOT to use this skill

- Forecasting a numeric series over calendar time → `da-15-forecasting`
- Regression/classification with fully observed outcomes → `da-6` / `da-7`
- Causal/experiment analysis with no time component → `da-12`
- A descriptive cohort retention table (no estimator, no model) → `da-21-product-analytics`
- Computing a CLV dollar figure with BG/NBD, Pareto/NBD, or Gamma-Gamma spend models → `da-23-customer-lifetime-value` (this skill covers only the time-to-churn / survival-curve half)

---

## 1. Censoring and truncation — the defining feature

The reason survival analysis exists. Get this wrong and every downstream estimate is biased.

| Mechanism | What it means | Handling |
|---|---|---|
| **Right censoring** | Event not yet observed at end of follow-up (most common case). You know `T > c`. | Standard; all estimators below assume it. |
| **Left censoring** | Event already happened before observation began, exact time unknown. `T < c`. | Use models that accept left-censored entries (lifelines `KaplanMeierFitter.fit_left_censoring`). |
| **Interval censoring** | Event happened between two inspection times. `a < T < b`. | Turnbull estimator / interval-censored regression. |
| **Left truncation** | Subjects who had the event *before entry* never appear at all (delayed entry, e.g. age-as-timescale). | Supply an `entry`/`lower_bound`; biases ignored if untreated. |
| **Right truncation** | Only subjects who *have* had the event are sampled (e.g. registry of completed events). | Specialized estimators; rare. |

Key distinction: **censoring keeps the subject but loses event-time detail; truncation removes the subject from the sample entirely** (Stats Ox lecture notes, 2020; NJIT Math 659 Ch.3, 2011; GeeksforGeeks, 2024). The standard estimators assume censoring is **non-informative** (independent of the event process).

## 2. The survival, hazard, and cumulative-hazard functions

Three interchangeable views of the same distribution; pick whichever the audience reads best.

- **Survival function** `S(t) = P(T > t)` — probability of surviving past `t`. Monotone non-increasing from 1.
- **Hazard function** `h(t) = lim Δ→0 P(t ≤ T < t+Δ | T ≥ t)/Δ` — instantaneous event rate *given survival so far*.
- **Cumulative hazard** `H(t) = ∫₀ᵗ h(u)du`, with the bridge identity `S(t) = exp(−H(t))`.

The hazard is the modeling target for most methods (lifelines Quickstart v0.30, 2025; Klein & Moeschberger Ch. 2, 2003).

## 3. Kaplan-Meier & Nelson-Aalen (non-parametric estimators)

The first thing to compute on any survival dataset — assumption-free descriptive curves.

- **Kaplan-Meier (product-limit) estimator** of `S(t)`: at each event time multiply by `(1 − dᵢ/nᵢ)`. Step function; censored subjects drop out of the risk set without a step. Report **median survival** and confidence bands.
- **Nelson-Aalen estimator** of `H(t)`: sum of `dᵢ/nᵢ`. Estimates cumulative hazard under independent right-censoring and left-truncation (lifelines NelsonAalenFitter docs, 2025).

```python
from lifelines import KaplanMeierFitter
kmf = KaplanMeierFitter()
kmf.fit(durations=df["tenure"], event_observed=df["churned"], entry=df.get("entry"))
kmf.median_survival_time_; kmf.plot_survival_function()
```

Sources: lifelines Quickstart (2025); Klein & Moeschberger Ch. 4 (2003); CPSC 330 Survival lecture (2023).

## 4. The log-rank test (comparing groups)

Compares two-or-more KM curves; null = **equal survival across groups**. Chi-square test accumulating observed-minus-expected events at each event time; weights all time points equally (Wilcoxon/Tarone-Ware variants weight early times more). Gives a p-value, not an effect size — for an effect size use Cox.

```python
from lifelines.statistics import logrank_test, multivariate_logrank_test
logrank_test(durA, durB, eventA, eventB).p_value
```

Sources: lifelines.statistics (2025); STHDA (2018); Klein & Moeschberger Ch. 7 (2003).

## 5. Cox proportional-hazards model (the workhorse)

Semi-parametric: `h(t|x) = h₀(t) · exp(βᵀx)`. Baseline hazard `h₀(t)` is unspecified; `β` estimated via **partial likelihood** (Cox 1972). `exp(βⱼ)` is the **hazard ratio** — multiplicative, time-constant.

```python
from lifelines import CoxPHFitter
cph = CoxPHFitter(penalizer=0.1)
cph.fit(df, duration_col="tenure", event_col="churned")
cph.print_summary()          # coef, exp(coef)=HR, p, CI
```

Tie handling: Efron (default) or Breslow. Report HRs with CIs. Sources: lifelines CoxPHFitter (2025); Therneau & Grambsch (2000); Researchers' Guide (2021).

## 6. The proportional-hazards assumption & diagnostics

Cox is only valid if hazard ratios are **constant over time**. Always check.

- **Scaled Schoenfeld residuals**: zero slope against (a function of) time under PH.
- **Grambsch-Therneau test** (`cox.zph` in R, `cph.check_assumptions()` / `proportional_hazard_test` in lifelines): null = PH holds; small p-value flags a violation.
- **Graphical**: `ggcoxzph()` (survminer) — LOESS smooth should be flat.

**Fixes when violated**: stratify (`strata=`), add a covariate×time interaction, split follow-up into intervals, or switch to AFT. Sources: UCLA OARC (2021); Stata stcox (2015); STHDA (2018).

## 7. Parametric models: exponential, Weibull, and AFT

For a smooth curve, extrapolation, or a generative model.

- **Exponential**: constant hazard `h(t)=λ`. Memoryless baseline.
- **Weibull**: monotone increasing (`ρ>1`) or decreasing (`ρ<1`) hazard. The default parametric choice.
- **AFT**: `log(T) = βᵀx + error`; covariates accelerate/decelerate time-to-event (`exp(β)` = time ratio). More interpretable for "this doubles the expected lifetime."
- **Weibull is the only distribution expressible as both PH and AFT.** Log-logistic / log-normal AFT allow non-monotone hazards.

```python
from lifelines import WeibullAFTFitter
aft = WeibullAFTFitter().fit(df, duration_col="tenure", event_col="churned")
```

Sources: AFT model — Wikipedia (2025); CRAN eha (2024); AFT vs Cox PMC4645729 (2015).

## 8. Competing risks (cause-specific vs. Fine-Gray)

When a subject can fail from **mutually exclusive** causes, naïve KM/Cox on one cause **over-estimates its incidence** by treating competing events as censored.

- **Cause-specific hazard** (Cox per cause): rate of cause `k` among those still at risk. Best for **etiology**. Censor competing events.
- **Fine-Gray subdistribution hazard**: links covariates to the **cumulative incidence function (CIF)** — the actual probability of cause `k`, accounting for competing events. Best for **prediction / risk communication** (`sHR`). Competing-event subjects stay in the risk set with decaying weights.

Caveats: separate Fine-Gray per cause → CIFs can sum > 1; **avoid multiple Fine-Gray models** — prefer cause-specific for multi-event questions. For causal effects, Fine-Gray is discouraged. Sources: Austin & Fine, Stat Med (2017); Austin et al. (2021); Statistical Horizons (2023).

## 9. Time-varying covariates

When a predictor changes during follow-up, a single baseline value is wrong. Use **long (counting-process) format**: one row per subject per interval `(id, start, stop, event, covariates)`.

```python
from lifelines import CoxTimeVaryingFitter
ctv = CoxTimeVaryingFitter()
ctv.fit(long_df, id_col="id", start_col="start", stop_col="stop", event_col="event")
```

Also the standard fix for a time-varying *coefficient* (a PH violation) — though that needs a covariate×time interaction. Sources: lifelines Time-varying regression (2025); CoxTimeVaryingFitter docs (2025); Therneau & Grambsch Ch. 3 (2000).

## 10. Discrete-time survival & churn / retention / CLV

When time is naturally **binned** and many events tie at the same bin, discrete-time survival beats continuous Cox.

- **Method**: expand to **person-period** rows, fit ordinary **logistic regression** with the period (or a flexible function of it) as predictor. Fitted per-period probabilities are the **discrete hazards**; chain into a survival/retention curve.
- **Churn / retention**: tenure = duration, churn = event, active customers = right-censored. KM gives the retention curve; Cox/AFT give "what drives churn timing"; integrating `S(t)` gives expected lifetime, the backbone of **CLV** (`CLV ≈ Σ margin·S(t)·discount`).

Survival beats a static churn classifier: it answers *when*, uses censored customers correctly, and yields retention curves and CLV directly. Sources: SAS Survival Data Mining (2012); SAS CLV (2003); Springer churn prediction (2025).

## 11. Machine-learning survival models

When effects are nonlinear/interacting/high-dimensional and accuracy beats interpretability.

- **Random Survival Forests (RSF)**: survival trees split on the **log-rank statistic**; ensemble cumulative-hazard estimate; handles nonlinearities, right-censoring, variable importance. Ishwaran et al. (2008).
- **Gradient-boosted survival**: boosts weak learners against a survival loss; often the strongest tabular baseline. scikit-survival `GradientBoostingSurvivalAnalysis` ~0.75 C-index on the standard example.
- **DeepSurv** (Katzman et al., 2018): deep net optimizing the **Cox partial-likelihood** loss; nonlinear Cox for personalized risk.
- **Evaluation**: **Harrell's concordance index (C-index)** (0.5 random, 1.0 perfect); time-dependent AUC; integrated Brier score.

```python
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import concordance_index_censored
rsf = RandomSurvivalForest(n_estimators=200).fit(X, y_structured)  # y = (event_bool, time)
```

Sources: Ishwaran et al., Ann. Appl. Stat. 2(3):841-860 (2008); scikit-survival RSF & boosting guides (2025); Katzman et al., DeepSurv, BMC Med Res Methodol / arXiv 1606.00931 (2018).

---

## Methodology (default workflow)

1. **Define the timeline**: `t=0` origin, the event, the censoring rule; check for left truncation / delayed entry.
2. **Describe**: KM curve + median survival; Nelson-Aalen for cumulative hazard; stratify by key groups.
3. **Compare groups**: log-rank (effect size deferred to Cox).
4. **Model effects**: Cox PH first; parametric/AFT for extrapolation or a smooth curve.
5. **Check assumptions**: Schoenfeld residuals / `cox.zph`; repair PH violations.
6. **Handle structure**: competing risks → cause-specific or Fine-Gray; changing covariates → time-varying; binned time → discrete-time logistic.
7. **Predict at scale**: RSF / gradient boosting / DeepSurv.
8. **Validate**: C-index, time-dependent AUC, integrated Brier, calibration; never plain accuracy.

## Practical patterns

- **Always plot KM first** — reveals crossing curves (PH violation), plateaus (cured fraction), data problems.
- **Encode the outcome as a pair** `(event_indicator, time)` — scikit-survival needs a structured array; lifelines takes two columns.
- **Report hazard ratios with CIs** and translate: "HR 1.4 → 40% higher instantaneous churn rate."
- **Use the right time origin** (calendar / age / time-since-enrollment); left-truncate on delayed entry.
- **For churn/CLV**, integrate the survival curve for expected lifetime instead of averaging completed tenures (which ignores censored = still-active customers).

## Anti-patterns

- **Dropping censored rows** — the cardinal sin; discards most information and badly biases estimates.
- **Treating time-to-event as an OLS regression target** — censoring makes the target undefined for survivors.
- **Treating competing events as plain censoring** when estimating one cause's incidence — over-states it; use CIF / Fine-Gray.
- **Fitting Cox without checking PH** — silently corrupts every hazard ratio.
- **Reporting only a log-rank p-value** with no effect size or curve.
- **Evaluating an ML survival model with accuracy/AUC on a binarized label** instead of C-index / Brier.
- **One Fine-Gray model per cause read together** — CIFs can sum past 1; prefer cause-specific for multi-event questions.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| KM curves cross | PH violated | Stratify, time-varying coefficient, or AFT; don't trust a single HR |
| `cox.zph` p-value tiny for a covariate | Non-proportional effect | `strata=` that covariate, or add covariate×time interaction |
| Median survival `inf`/undefined | Curve never reaches 0.5 (heavy censoring) | Report RMST or a fixed-horizon survival probability |
| Cumulative incidence sums > 1 | Multiple Fine-Gray models combined | Use cause-specific hazards, or one Fine-Gray for the single cause |
| C-index ≈ 0.5 | No signal / wrong outcome encoding | Re-check `(event, time)` pairing and feature leakage |
| Cox fails to converge / huge CIs | Separation, collinearity, too few events | `penalizer=`, drop/merge covariates, ~10 events-per-variable |
| Suspiciously optimistic effects | Informative censoring / immortal-time bias | Audit follow-up start/end; align time origin with eligibility |

## References

- Klein & Moeschberger, *Survival Analysis: Techniques for Censored and Truncated Data*, 2nd ed., Springer (2003).
- Therneau & Grambsch, *Modeling Survival Data: Extending the Cox Model*, Springer (2000).
- lifelines docs — https://lifelines.readthedocs.io/en/latest/ (v0.30, 2025).
- scikit-survival user guide — https://scikit-survival.readthedocs.io/en/stable/ (2025).
- Censoring & truncation — https://www.stats.ox.ac.uk/~mlunn/lecturenotes1.pdf (2020); https://web.njit.edu/~wguo/Math%20659_2011/Math659_Chapter3.pdf (2011).
- PH test — https://stats.oarc.ucla.edu/other/examples/asa2/testing-the-proportional-hazard-assumption-in-cox-models/ (2021); https://www.stata.com/manuals14/ststcoxph-assumptiontests.pdf (2015).
- AFT — https://en.wikipedia.org/wiki/Accelerated_failure_time_model (2025); https://pmc.ncbi.nlm.nih.gov/articles/PMC4645729/ (2015).
- Fine-Gray — https://onlinelibrary.wiley.com/doi/10.1002/sim.7501 (2017); https://onlinelibrary.wiley.com/doi/full/10.1002/sim.9023 (2021); https://statisticalhorizons.com/for-causal-analysis-of-competing-risks/ (2023).
- Discrete-time / churn / CLV — https://support.sas.com/resources/papers/proceedings12/132-2012.pdf (2012); https://support.sas.com/resources/papers/proceedings/proceedings/sugi28/120-28.pdf (2003); https://link.springer.com/article/10.1057/s41270-025-00450-2 (2025).
- ML survival — Ishwaran et al. RSF https://ishwaran.org/papers/IKBL.AOAS.pdf (2008); Katzman et al. DeepSurv https://link.springer.com/article/10.1186/s12874-018-0482-1 / https://arxiv.org/abs/1606.00931 (2018).
