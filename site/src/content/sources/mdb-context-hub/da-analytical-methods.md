---
title: "ML Model Monitoring"
description: "The analytical-methods stage of the data-analysis discipline — the techniques"
---

# Data Analysis: Analytical Methods

The analytical-methods stage of the data-analysis discipline — the techniques
that turn a prepared dataset into findings, predictions, and decisions. This is
the "do the analysis" layer that sits between data acquisition and
communication: cleaning and exploring data, fitting statistical and ML models,
running experiments and causal estimates, forecasting, detecting anomalies,
engineering features, and the specialized modeling disciplines (CLV, survival,
Bayesian, conformal/UQ, causal discovery, prescriptive optimization,
recommenders).

It does not re-derive the underlying probability and inference theory (that is
`da-1-foundations-theory`) and it does not own the surrounding process,
platform, or communication stages — see the cross-hub note below.

## How to use this hub

This hub consolidates **16 analytical-methods sub-skills as on-demand
references** under `references/`. Treat the routing table as an index, not as
the answer:

1. Identify which method the task calls for.
2. Find the matching row below.
3. **Read the listed `references/<name>.md` before giving a deep answer** — the
   table lines are deliberately shallow and exist only to route. For
   multi-method tasks (e.g. EDA → feature engineering → modeling → evaluation),
   read each relevant reference in sequence.

## Sub-skill routing table

This hub absorbs 16 former standalone skills as on-demand reference files. When
a task matches a row, **Read the listed `references/` file** before answering —
do not rely on this table alone for depth.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `da-4-data-cleaning-preparation` | Cleaning and preparing raw data — missing values, outliers, types, dedup, normalization, the disciplined transform into analysis-ready data | `references/da-4-data-cleaning-preparation.md` |
| `da-5-exploratory-data-analysis` | Exploratory Data Analysis — the Tukey-rooted discipline of looking at data with summaries and graphics to surface structure and check assumptions | `references/da-5-exploratory-data-analysis.md` |
| `da-6-statistical-modeling` | Statistical (inference-first) modeling — linear regression (OLS, Gauss-Markov, diagnostics), logistic regression, GLMs, mixed/hierarchical models | `references/da-6-statistical-modeling.md` |
| `da-7-machine-learning` | Machine learning — the ML taxonomy (supervised / unsupervised / reinforcement), model selection, cross-validation, regularization, evaluation metrics | `references/da-7-machine-learning.md` |
| `da-12-ab-testing-causal-inference` | A/B testing and causal inference — randomized experiments (sample size, power), DiD, IV, regression discontinuity, propensity-score methods | `references/da-12-ab-testing-causal-inference.md` |
| `da-15-forecasting` | Forecasting and time-series modeling — ARIMA/ETS, Prophet, backtesting, going deeper than the time-series foundations | `references/da-15-forecasting.md` |
| `da-16-anomaly-detection` | Anomaly / outlier detection — statistical (z-score, IQR), distance/density, isolation forest, and time-series anomaly methods for the working analyst | `references/da-16-anomaly-detection.md` |
| `da-17-feature-engineering-and-feature-stores` | Feature engineering taxonomy (numerical transforms, encoding, datetime, interactions, target encoding), automated FE, and feature-store operations | `references/da-17-feature-engineering-and-feature-stores.md` |
| `da-23-customer-lifetime-value` | Probabilistic / statistical Customer Lifetime Value (CLV) modeling — BG/NBD, Gamma-Gamma, and related expected-value methods | `references/da-23-customer-lifetime-value.md` |
| `da-24-survival-analysis` | Survival / time-to-event modeling — Kaplan-Meier, Cox proportional hazards, censoring, a discipline distinct from ordinary regression | `references/da-24-survival-analysis.md` |
| `da-25-bayesian-data-analysis` | Applied Bayesian data analysis and probabilistic-programming workflow — priors, posteriors, MCMC, posterior predictive checks | `references/da-25-bayesian-data-analysis.md` |
| `da-31-conformal-prediction-uq` | Conformal prediction and distribution-free uncertainty quantification — prediction sets/intervals with finite-sample coverage guarantees | `references/da-31-conformal-prediction-uq.md` |
| `da-32-causal-discovery` | Causal discovery / structure learning — learning the causal DAG itself from data (constraint-, score-, and functional-based methods) | `references/da-32-causal-discovery.md` |
| `da-33-prescriptive-analytics` | Prescriptive analytics / decision science — turning predictions and data into optimized decisions via optimization, decision rules, and simulation | `references/da-33-prescriptive-analytics.md` |
| `da-38-recommender-systems-and-ranking` | Recommender systems and learning-to-rank — collaborative/content filtering, matrix factorization, ranking models and evaluation | `references/da-38-recommender-systems-and-ranking.md` |
| `da-42-ml-model-monitoring` | Monitoring ML models in production — drift taxonomy (data/concept/prediction/feature) and detection tests (PSI, KS, KL/JS, Wasserstein), streaming detectors (ADWIN/DDM/Page-Hinkley), performance estimation without labels (NannyML CBPE/DLE), train-serve skew, slice/fairness drift, retraining triggers, and the tooling landscape (Evidently, Arize, Fiddler, WhyLabs, Alibi Detect, SageMaker, Vertex) | `references/da-42-ml-model-monitoring.md` |

## Cross-hub note

This hub is the *methods* stage of a six-hub data-analytics family. Route
elsewhere when the task is not "run the analysis":

- **Theory beneath a method** (distributions, Bayes' theorem, CLT, estimation
  theory, levels of measurement, correlation vs. causation) →
  `da-1-foundations-theory`.
- **Process / lifecycle** (CRISP-DM, problem framing, success metrics,
  stakeholder handoff) → `da-2-data-analysis-lifecycle`.
- **Getting the data** (sources, collection methods, sampling design) →
  `da-3-data-acquisition-sampling`.
- **Pipelines and platform** (ETL, warehousing, OLAP, semantic layer,
  governance, observability) → `da-data-engineering-platform`.
- **Showing and applying the result** (visualization, reporting, applied/domain
  analytics, ethics and privacy) → `da-applied-and-communication`.
- **Writing up findings** (stakeholder narratives, KB articles, runbooks,
  executive summaries) → `technical-writing-craft` (structured docs) or
  `content-and-marketing-writing` (TAM replies, customer-facing narratives).

When a request spans stages, start in the hub that owns the *decision the user
is currently making* and hand off explicitly.

## Cross-hub map — where every data-analytics topic lives

This family is split across these hubs. If a task's deep material is **not** in this hub's Sub-skill
routing table, it is a reference file under a sibling hub below — **activate that hub or `Read` its
`references/<name>.md` directly**. Every former standalone skill in this family is now a reference under one
of these hubs (nothing was deleted).

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `da-1-foundations-theory` | Data Analysis Foundations & Theory (hub) | `references/da-1-1-definitions-scope.md`, `references/da-1-1-1-data-analysis-vs-analytics-vs-data.md`, `references/da-1-1-2-analysis-vs-synthesis.md`, `references/da-1-1-3-quantitative-vs-qualitative-analysis.md`, … |
| `da-2-data-analysis-lifecycle` | Data Analysis Lifecycle & Process (hub) | `references/da-2-1-process-frameworks.md`, `references/da-2-1-1-crisp-dm.md`, `references/da-2-1-2-kdd.md`, `references/da-2-1-3-semma.md`, … |
| `da-3-data-acquisition-sampling` | Data Acquisition, Collection & Sampling (hub) | `references/da-3-1-data-sources.md`, `references/da-3-1-1-primary-vs-secondary.md`, `references/da-3-1-2-internal-vs-external.md`, `references/da-3-1-3-structured-semi-structured-unstructured.md`, … |
| `da-analytical-methods` | Data Analytical Methods (cleaning, EDA, modeling, ML, causal, time-series) | `references/da-4-data-cleaning-preparation.md`, `references/da-5-exploratory-data-analysis.md`, `references/da-6-statistical-modeling.md`, `references/da-7-machine-learning.md`, … |
| `da-data-engineering-platform` | Data Engineering & Analytics Platform (pipelines, OLAP, modeling, governance) | `references/da-10-tools-and-languages.md`, `references/da-13-data-engineering-and-pipelines.md`, `references/da-14-streaming-analytics.md`, `references/da-18-semantic-layer-headless-bi.md`, … |
| `da-applied-and-communication` | Applied Analytics, Visualization, Communication & Ethics | `references/da-8-data-visualization.md`, `references/da-9-reporting-communication.md`, `references/da-11-ethics-and-privacy.md`, `references/da-21-product-analytics.md`, … |
