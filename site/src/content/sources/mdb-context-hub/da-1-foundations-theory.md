---
title: "Data Analysis Foundations and Theory"
description: "Conceptual grounding for a data analysis effort. This skill answers the"
---

# Data Analysis: Foundations & Theory

Conceptual grounding for a data analysis effort. This skill answers the
*before-you-pick-a-tool* questions: what is data analysis, how does it relate to
neighboring fields, what kind of analysis is called for, what can the data
support given how it was measured, and what assumptions ride underneath. It does
not execute techniques — it scopes and frames them.

## Sub-skill routing table

This hub consolidates 37 foundations sub-skills as on-demand references — match
the task to the table and **Read the listed `references/<name>.md` before
answering deep questions**. The overview below is enough for framing and
scoping; load the reference when a question needs depth.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `da-1-1-definitions-scope` | Defines what "data analysis" means and where its boundaries sit | `references/da-1-1-definitions-scope.md` |
| `da-1-1-1-data-analysis-vs-analytics-vs-data` | Disambiguates four overlapping terms — data analysis, data analytics, data science, statistics | `references/da-1-1-1-data-analysis-vs-analytics-vs-data.md` |
| `da-1-1-2-analysis-vs-synthesis` | Distinguishes analysis (breaking a whole into parts) from synthesis | `references/da-1-1-2-analysis-vs-synthesis.md` |
| `da-1-1-3-quantitative-vs-qualitative-analysis` | Foundational distinction between quantitative and qualitative analysis | `references/da-1-1-3-quantitative-vs-qualitative-analysis.md` |
| `da-1-2-measurement-theory` | Measurement theory as the foundational layer — how numbers map to reality | `references/da-1-2-measurement-theory.md` |
| `da-1-2-1-levels-of-measurement` | Stevens' levels (scales) of measurement — nominal, ordinal, interval, ratio | `references/da-1-2-1-levels-of-measurement.md` |
| `da-1-2-1-1-nominal` | The NOMINAL level of measurement (Stevens 1946) — the lowest scale type | `references/da-1-2-1-1-nominal.md` |
| `da-1-2-1-2-ordinal` | The ordinal level of measurement — ranked categories | `references/da-1-2-1-2-ordinal.md` |
| `da-1-2-1-3-interval` | The interval level of measurement — equal differences, no true zero | `references/da-1-2-1-3-interval.md` |
| `da-1-2-1-4-ratio` | The ratio level of measurement — equal differences plus a true zero | `references/da-1-2-1-4-ratio.md` |
| `da-1-2-2-discrete-vs-continuous-variables` | Distinguishes discrete from continuous variables | `references/da-1-2-2-discrete-vs-continuous-variables.md` |
| `da-1-2-3-reliability-validity` | Reliability and validity: whether a measure is consistent and measures what it claims | `references/da-1-2-3-reliability-validity.md` |
| `da-1-2-4-operationalization-constructs` | Turning an abstract construct into something measurable | `references/da-1-2-4-operationalization-constructs.md` |
| `da-1-3-probability-theory` | Foundational probability theory as the mathematical basis for analysis | `references/da-1-3-probability-theory.md` |
| `da-1-3-1-random-variables` | The formal treatment of random variables | `references/da-1-3-1-random-variables.md` |
| `da-1-3-2-probability-mass-density-functions` | PMF and PDF | `references/da-1-3-2-probability-mass-density-functions.md` |
| `da-1-3-3-probability-distributions` | What a probability DISTRIBUTION is | `references/da-1-3-3-probability-distributions.md` |
| `da-1-3-3-1-normal` | Normal (Gaussian) distribution | `references/da-1-3-3-1-normal.md` |
| `da-1-3-3-2-binomial` | Binomial distribution | `references/da-1-3-3-2-binomial.md` |
| `da-1-3-3-3-poisson` | Poisson distribution | `references/da-1-3-3-3-poisson.md` |
| `da-1-3-3-4-exponential` | Exponential distribution | `references/da-1-3-3-4-exponential.md` |
| `da-1-3-3-5-uniform` | Uniform distribution | `references/da-1-3-3-5-uniform.md` |
| `da-1-3-4-joint-marginal-conditional-probability` | Joint, marginal, and conditional probability | `references/da-1-3-4-joint-marginal-conditional-probability.md` |
| `da-1-3-5-bayes-theorem` | Bayes' theorem | `references/da-1-3-5-bayes-theorem.md` |
| `da-1-3-6-law-of-large-numbers` | The Law of Large Numbers | `references/da-1-3-6-law-of-large-numbers.md` |
| `da-1-3-7-central-limit-theorem` | The central limit theorem | `references/da-1-3-7-central-limit-theorem.md` |
| `da-1-3-8-expectation-variance-covariance` | Expectation, variance, covariance | `references/da-1-3-8-expectation-variance-covariance.md` |
| `da-1-4-statistical-inference-foundations` | Foundations of statistical inference | `references/da-1-4-statistical-inference-foundations.md` |
| `da-1-4-1-population-vs-sample` | Population vs. sample | `references/da-1-4-1-population-vs-sample.md` |
| `da-1-4-2-sampling-distributions-standard-error` | Sampling distribution and standard error | `references/da-1-4-2-sampling-distributions-standard-error.md` |
| `da-1-4-3-frequentist-vs-bayesian-paradigms` | Frequentist and Bayesian schools | `references/da-1-4-3-frequentist-vs-bayesian-paradigms.md` |
| `da-1-4-4-estimation-theory` | Point-estimation theory | `references/da-1-4-4-estimation-theory.md` |
| `da-1-5-information-theory` | Shannon entropy, mutual information | `references/da-1-5-information-theory.md` |
| `da-1-6-epistemology-of-data` | How data come to count as knowledge | `references/da-1-6-epistemology-of-data.md` |
| `da-1-6-1-correlation-vs-causation` | Why association is not causation | `references/da-1-6-1-correlation-vs-causation.md` |
| `da-1-6-2-inductive-vs-deductive-reasoning` | Inductive, deductive, abductive reasoning | `references/da-1-6-2-inductive-vs-deductive-reasoning.md` |
| `da-1-6-3-reproducibility-replicability` | Reproducibility and replicability | `references/da-1-6-3-reproducibility-replicability.md` |

## 1. What data analysis is (and its scope)

Data analysis is the systematic process of inspecting, cleaning, transforming, and interpreting data to extract useful information, support conclusions, and aid decision-making. In practice it is bounded and goal-directed.

Distinguish four neighboring terms — they overlap but are not synonyms:

- **Data analysis** — the act of evaluating data to answer a defined question. The *process verb*.
- **Data analytics** — the broader practice/field built around analyzing data; typically about the past and present, with more elementary statistics.
- **Data science** — a wider, multidisciplinary field that *includes* analytics but reaches into ML, forecasting, and large-scale data engineering; more oriented toward predictive models.
- **Statistics** — the mathematical discipline of collecting, describing, and drawing inferences from data under uncertainty. Data analysis *uses* statistics as a toolkit.

Rule of thumb: *data analysis is the activity; analytics is the field around it; data science extends it toward modeling and engineering; statistics supplies the inferential mathematics.* State which definition you are using.

### Analysis vs. synthesis

Analysis breaks a whole into parts; synthesis recombines parts into a new integrated whole or recommendation. Name which mode you are in to avoid presenting raw decomposition as a conclusion.

### Quantitative vs. qualitative

- **Quantitative analysis** operates on numeric measurements (interval and ratio scales).
- **Qualitative analysis** operates on categorical/textual data (nominal and ordinal scales). The split is about method too, not just data type. Many efforts are mixed-method.

## 2. The four families of analysis

| Type | Question | Typical methods |
|---|---|---|
| **Descriptive** | What happened? | aggregation, reporting, summary statistics |
| **Diagnostic** | Why did it happen? | root-cause analysis, correlation, drill-down |
| **Predictive** | What is likely to happen? | forecasting, regression, ML, probability scores |
| **Prescriptive** | What should we do? | optimization, decision rules, simulation |

The four form a maturity progression but are not strictly sequential per project. "Diagnostic" maps loosely onto **exploratory** work, but don't conflate the marketing taxonomy with Tukey's exploratory/confirmatory split.

## 3. The analysis lifecycle / process

The de facto reference is **CRISP-DM** (six phases you can revisit):

1. **Business Understanding** — define the question and success criteria.
2. **Data Understanding** — collect, describe, explore, verify quality.
3. **Data Preparation** — select, clean, construct, integrate, format.
4. **Modeling** — choose technique, build, assess.
5. **Evaluation** — check against business goal; review process.
6. **Deployment** — deliver, monitor, report.

The phases are iterative, not a one-way pipeline. A lighter generic framing — define → collect → clean → analyze → interpret → communicate — works for non-mining work.

## 4. Exploratory vs. confirmatory analysis

- **Exploratory Data Analysis (EDA)** — Tukey's approach for summarizing a dataset's main characteristics, often with graphics, to *generate* hypotheses and check assumptions. Techniques: box plots, stem-and-leaf, histograms, scatter plots.
- **Confirmatory Data Analysis (CDA)** — classical hypothesis testing: pick a model *before* examining the data, then assess inference precision.

Researchers need *both*. **Critical pitfall:** running exploratory and confirmatory analysis on the same data introduces systematic bias (double-dipping). Reserve a holdout or fresh sample for confirmation.

## 5. Measurement theory and levels of measurement

Stevens' four levels (1946):

| Level | Distinguishes | Permissible central tendency | Example |
|---|---|---|---|
| **Nominal** | categories only (=, ≠) | mode | dog/cat/rabbit |
| **Ordinal** | rank order | median | 1st/2nd/3rd |
| **Interval** | equal differences, no true zero | mean, median, mode | Celsius, dates |
| **Ratio** | equal differences + true zero | adds geometric/harmonic means | mass, length, duration |

Nominal and ordinal are categorical/qualitative; interval and ratio are continuous/quantitative.

**Common pitfalls:** computing a mean of ordinal codes (median is safer); treating an arbitrary numeric label as quantitative; forgetting interval scales lack a true zero (ratios are meaningless). **Know the controversy:** Velleman & Wilkinson (1993) and Luce (1997) contested Stevens' typology. Treat the level of measurement as a useful first filter, not an iron law.

## 6. The role of theory and assumptions

Data does not interpret itself. Every analysis rides on assumptions: representative sample, measurements meaning what labels claim, model preconditions holding. Two practices:

- **State assumptions explicitly** and tie each to the analysis family and measurement level.
- **Match method to question and to data.** Misalignment — a prescriptive recommendation on descriptive data, or a mean on ordinal categories — is the most common foundational error.

## Quick decision checklist

1. **Term check** — analysis, analytics, data science, or statistics? State the definition.
2. **Family** — descriptive, diagnostic, predictive, or prescriptive?
3. **Mode** — exploratory or confirmatory? Don't mix on the same data.
4. **Lifecycle** — which CRISP-DM phase; what's next?
5. **Measurement** — what level is each variable; which statistics are licensed?
6. **Assumptions** — what must be true; have I checked?

<!-- cross-hub-map -->
## Cross-hub map — where every data-analytics topic lives

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `da-1-foundations-theory` | Data Analysis Foundations & Theory (hub) | `references/da-1-1-definitions-scope.md`, … |
| `da-2-data-analysis-lifecycle` | Data Analysis Lifecycle & Process (hub) | `references/da-2-1-1-crisp-dm.md`, … |
| `da-3-data-acquisition-sampling` | Data Acquisition, Collection & Sampling (hub) | `references/da-3-1-data-sources.md`, … |
| `da-analytical-methods` | Data Analytical Methods (cleaning, EDA, modeling, ML, causal, time-series) | `references/da-5-exploratory-data-analysis.md`, … |
| `da-data-engineering-platform` | Data Engineering & Analytics Platform | `references/da-13-data-engineering-and-pipelines.md`, … |
| `da-applied-and-communication` | Applied Analytics, Visualization, Communication & Ethics | `references/da-8-data-visualization.md`, … |
