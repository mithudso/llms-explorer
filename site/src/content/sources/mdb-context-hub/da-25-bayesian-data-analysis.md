---
title: "Bayesian Data Analysis and Probabilistic Programming"
description: "Applied Bayesian modeling: specify a generative model, fit the posterior with a probabilistic programming language (PPL), interrogate it with predictive checks and diagnostics, and compare alternative"
---

# Bayesian Data Analysis & Probabilistic Programming

Applied Bayesian modeling: specify a generative model, fit the posterior with a probabilistic programming language (PPL), interrogate it with predictive checks and diagnostics, and compare alternatives. This skill is the *workflow and tooling* layer — it assumes Bayes' theorem and the frequentist/Bayesian contrast are already understood (see da-1-3-5, da-1-4-3).

## Overview

A Bayesian model combines a **prior** `p(θ)` and a **likelihood** `p(y|θ)` into a **posterior** `p(θ|y) ∝ p(y|θ) p(θ)`. For all but trivial models the posterior is intractable analytically, so we approximate it by sampling (MCMC) or optimization (variational inference). The discipline is an iterative loop — model, fit, check, expand — formalized as the **Bayesian workflow** ([Gelman, Vehtari, Simpson et al. 2020, arXiv:2011.01808](https://arxiv.org/abs/2011.01808)).

Use Bayesian methods when you want: full uncertainty quantification (posteriors, not just point estimates), principled regularization via priors, partial pooling across groups (hierarchical models), the ability to incorporate domain knowledge, and propagation of uncertainty into predictions/decisions.

## Core Concepts

1. **The Bayesian workflow (iterative).** Build → simulate from priors → fit → diagnose computation → check against data → compare models → expand/simplify → repeat. Treats *computational failure* (divergences, bad R-hat) and *model misfit* (failed PPCs) as distinct problems ([Gelman et al. 2020](https://arxiv.org/abs/2011.01808); [Betancourt "Principled Bayesian Workflow" 2020](https://betanalpha.github.io/assets/case_studies/principled_bayesian_workflow.html); [Gabry et al. JRSS-A 2019](https://academic.oup.com/jrsssa/article/182/2/389/7070184)).

2. **Priors & prior predictive checks.** Favor **weakly-informative priors** (`Normal(0,1)` on standardized predictors, `HalfNormal`/`Exponential` on scales, `LKJ` on correlations) over flat/diffuse priors. Validate via **prior predictive check**: draw θ from prior, simulate y, confirm plausibility ([Stan Prior Choice wiki 2024](https://github.com/stan-dev/stan/wiki/Prior-Choice-Recommendations); [PyMC v5 docs 2024](https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/posterior_predictive.html)).

3. **MCMC: HMC & NUTS.** HMC uses gradients for distant, high-acceptance moves; **NUTS** auto-tunes trajectory length + step size and is the default in every modern PPL. Continuous params only — marginalize discrete ones ([Hoffman & Gelman JMLR 2014](https://jmlr.org/papers/v15/hoffman14a.html); [Betancourt arXiv:1701.02434 2017](https://arxiv.org/abs/1701.02434); [Stan Reference Manual 2024](https://mc-stan.org/docs/reference-manual/mcmc.html)).

4. **Variational inference (VI/ADVI).** Approximates the posterior by maximizing the ELBO — fast, scalable, but *underestimates* variance and can miss multimodality. **ADVI** automates it; normalizing flows enrich it. Validate against MCMC ([Kucukelbir et al. JMLR 2017](https://jmlr.org/papers/v18/16-107.html); [PyMC VI docs 2024](https://www.pymc.io/projects/docs/en/stable/api/vi.html); [NumPyro SVI docs 2024](https://num.pyro.ai/en/stable/svi.html)).

5. **Hierarchical/multilevel models.** Group-level params drawn from a shared population distribution → **partial pooling** (data-determined shrinkage toward the global mean). The biggest practical reason to go Bayesian ([Gelman & Hill 2006](http://www.stat.columbia.edu/~gelman/arm/); [McElreath *Statistical Rethinking* 2020](https://xcelab.net/rm/); [PyMC multilevel primer 2024](https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/GLM_hierarchical.html)).

6. **Posterior predictive checks (PPC).** Simulate `y_rep` from the posterior predictive, compare to observed `y` — overlaid densities, test statistics, **LOO-PIT** calibration. A model that can't reproduce key data features is misspecified ([Gabry et al. JRSS-A 2019](https://academic.oup.com/jrsssa/article/182/2/389/7070184); [ArviZ API 2024](https://python.arviz.org/en/stable/api/index.html)).

7. **Model comparison: LOO-CV (PSIS), WAIC.** Compare predictive accuracy with **PSIS-LOO** (`elpd_loo`); the **Pareto-k** diagnostic flags unreliable points (`k > 0.7` problematic). LOO preferred over WAIC for its self-diagnostics; prefer LOO over Bayes factors ([Vehtari et al. Stat&Computing 2017, arXiv:1507.04544](https://arxiv.org/abs/1507.04544); [Vehtari et al. PSIS, JMLR 2024, arXiv:1507.02646](https://arxiv.org/abs/1507.02646)).

8. **Convergence diagnostics.** Use **rank-normalized split-R-hat** (target `< 1.01`) and **bulk-ESS/tail-ESS**. HMC adds **divergent transitions** (curvature the sampler can't resolve — reparameterize/prior fix), **max-treedepth** (efficiency), and **E-BFMI < 0.3** (poor energy exploration) ([Vehtari et al. Bayesian Analysis 2021, arXiv:1903.08008](https://arxiv.org/abs/1903.08008); [Stan Warnings 2024](https://mc-stan.org/misc/warnings.html)).

9. **PPLs.** **PyMC** (Python v5+, PyTensor backend, pluggable NUTS: default/nutpie/numpyro/blackjax); **Stan** (reference HMC, via **CmdStanPy**/cmdstanr); **NumPyro** (JAX, fastest NUTS, GPU); **Bambi**/**brms** (formula GLMM interface `y ~ x + (1|g)`); **ArviZ** (backend-agnostic diagnostics on `InferenceData`) ([PyMC](https://www.pymc.io/); [CmdStanPy](https://mc-stan.org/cmdstanpy/); [NumPyro](https://num.pyro.ai/); [Bambi](https://bambinos.github.io/bambi/); [ArviZ](https://python.arviz.org/), all 2024).

10. **Bayesian regression & GLMs.** GLM link families carry over: Gaussian/Bernoulli/Poisson/Negative-Binomial; coefficient priors regularize (Normal≈ridge, Laplace≈LASSO, horseshoe for sparsity). Student-t likelihood for robust regression. Standardize predictors ([McElreath 2020](https://xcelab.net/rm/); [Bambi examples 2024](https://bambinos.github.io/bambi/notebooks/)).

11. **ArviZ — diagnostics & plotting hub.** `az.summary` (R-hat/ESS/HDI), `plot_trace`, `plot_ppc`, `loo`/`compare`/`plot_compare`, `plot_forest`, `plot_energy` (BFMI), `plot_pair` (divergences) ([ArviZ API 2024](https://python.arviz.org/en/stable/api/index.html)).

## Methodology — the loop in practice

1. **Scope & generative story.** Write the model as a data-generating process; pick the likelihood family from the outcome type first.
2. **Priors + prior predictive check.** Weakly-informative priors on standardized variables; `sample_prior_predictive`; reject absurd priors.
3. **Fit.** NUTS, ≥4 chains. `target_accept=0.8` default; raise to 0.9–0.99 on divergences. Try NumPyro/nutpie for large continuous models.
4. **Diagnose computation.** R-hat < 1.01, bulk/tail-ESS, **zero divergences**, E-BFMI > 0.3, no treedepth saturation. Fix *here* before interpreting.
5. **Posterior predictive check.** `sample_posterior_predictive` → `az.plot_ppc`, test statistics, LOO-PIT.
6. **Compare.** `az.loo` per model, `az.compare`; inspect Pareto-k.
7. **Iterate.** Expand (hierarchy/interactions/robust likelihood) or simplify; re-run.

## Practical Patterns

- **Standardize continuous predictors** (mean 0, sd 1) so default priors behave; back-transform for interpretation.
- **Non-centered parameterization for hierarchical models.** Replace `θ_g ~ Normal(μ, σ)` with `θ_g = μ + σ·z_g, z_g ~ Normal(0,1)` (the "Matt trick") — removes the funnel that causes divergences with sparse groups ([Stan User's Guide 2024](https://mc-stan.org/docs/stan-users-guide/efficiency-tuning.html#reparameterization); [Betancourt & Girolami 2015, arXiv:1312.0906](https://arxiv.org/abs/1312.0906)).
- **≥4 chains, multiple seeds**, inspect trace plots — R-hat alone misses problems.
- **Marginalize discrete parameters** so NUTS can run.
- **Use Bambi/brms for standard GLMMs**; drop to raw PyMC/Stan only for custom structure.
- **Save full `InferenceData`** (posterior + predictive + log-likelihood + sample stats) so LOO/PPCs are reproducible.

## Anti-Patterns

- **Ignoring divergences** — they bias the posterior. Reparameterize, raise `target_accept`, or tighten priors.
- **Flat/diffuse "uninformative" priors as default** — rarely uninformative on quantities of interest; prefer weakly-informative.
- **Trusting VI/ADVI without MCMC comparison** — VI understates variance.
- **Old R-hat < 1.1 as the bar** — use rank-normalized R-hat < 1.01 and check ESS.
- **Comparing on in-sample fit / DIC / raw likelihood** — use LOO/WAIC; read Pareto-k first.
- **Centered hierarchical parameterization with sparse groups** — the classic funnel generator; go non-centered.
- **Reading the posterior mean only** — report HDIs, propagate the full posterior.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Divergent transitions | Funnel / sharp curvature | Non-centered param; `target_accept` 0.9–0.99; tighten priors |
| R-hat > 1.01, low ESS | Non-convergence, multimodality | More draws; better inits; reparameterize; check label-switching |
| max-treedepth hits | Correlated posterior (inefficiency) | Raise `max_treedepth`; reparameterize; decorrelate |
| E-BFMI < 0.3 | Poor energy exploration, heavy tails | Reparameterize; regularize priors; Student-t |
| Pareto-k > 0.7 | Influential points; LOO unreliable | Moment-matching or exact refit; inspect outliers |
| PPC misses data | Wrong likelihood / missing structure | Change family (e.g. Neg-Binomial for overdispersion); add hierarchy |
| Prior predictive absurd | Priors too wide/wrong scale | Tighten; standardize; rethink units |
| VI posterior too narrow | Mean-field underestimates variance | Full-rank ADVI / flows, or use NUTS |

## References

1. Gelman et al. — *Bayesian Workflow* (2020). https://arxiv.org/abs/2011.01808
2. Vehtari, Gelman, Gabry — *LOO-CV and WAIC* (2017). https://arxiv.org/abs/1507.04544
3. Vehtari et al. — *Pareto Smoothed Importance Sampling* (JMLR 2024). https://arxiv.org/abs/1507.02646
4. Vehtari et al. — *Improved R-hat* (Bayesian Analysis 2021). https://arxiv.org/abs/1903.08008
5. Hoffman & Gelman — *The No-U-Turn Sampler* (JMLR 2014). https://jmlr.org/papers/v15/hoffman14a.html
6. Betancourt — *Conceptual Introduction to HMC* (2017). https://arxiv.org/abs/1701.02434
7. Betancourt — *Towards a Principled Bayesian Workflow* (2020). https://betanalpha.github.io/assets/case_studies/principled_bayesian_workflow.html
8. Betancourt & Girolami — *HMC for Hierarchical Models* (2015). https://arxiv.org/abs/1312.0906
9. Kucukelbir et al. — *ADVI* (JMLR 2017). https://jmlr.org/papers/v18/16-107.html
10. Gabry et al. — *Visualization in Bayesian Workflow* (JRSS-A 2019). https://academic.oup.com/jrsssa/article/182/2/389/7070184
11. Gelman et al. — *Bayesian Data Analysis* 3rd ed. (BDA3, 2013). http://www.stat.columbia.edu/~gelman/book/
12. McElreath — *Statistical Rethinking* 2nd ed. (2020). https://xcelab.net/rm/
13. Gelman & Hill — *Regression and Multilevel/Hierarchical Models* (2006). http://www.stat.columbia.edu/~gelman/arm/
14. Stan — *Prior Choice Recommendations* (2024). https://github.com/stan-dev/stan/wiki/Prior-Choice-Recommendations
15. Stan — *Reference Manual / Runtime Warnings* (2024). https://mc-stan.org/docs/reference-manual/mcmc.html
16. PyMC docs (2024). https://www.pymc.io/
17. NumPyro docs (2024). https://num.pyro.ai/
18. Bambi docs (2024). https://bambinos.github.io/bambi/
19. CmdStanPy docs (2024). https://mc-stan.org/cmdstanpy/
20. ArviZ docs (2024). https://python.arviz.org/
