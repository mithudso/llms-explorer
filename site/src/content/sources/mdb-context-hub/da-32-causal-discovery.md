---
title: "Causal Discovery and Structure Learning"
description: "Causal discovery (a.k.a. structure learning) learns the causal graph itself"
---

# Causal Discovery and Structure Learning

## Overview

**Causal discovery** (a.k.a. structure learning) learns the *causal graph itself*
from observational and/or interventional data — the edges and their directions —
rather than assuming the graph and estimating an effect. This is the upstream
problem to causal **inference**.

- **This skill (discovery):** "What is the causal structure? Which variables
  cause which?" → output is a graph (DAG, CPDAG, or PAG).
- **da-12 (inference):** "Given this DAG, what is the effect of X on Y?" → DiD,
  RDD, IV, propensity scores, synthetic control, backdoor/frontdoor adjustment.

If the user already has/assumes a DAG and wants an effect estimate, defer to
**da-12-ab-testing-causal-inference**. Use this skill only when the *structure*
is the unknown.

The hard truth of discovery: from purely observational data you usually cannot
recover a single DAG — only an **equivalence class** of DAGs (a CPDAG or PAG).
Pinning down direction requires extra assumptions (non-Gaussianity, nonlinearity),
interventions, or time order. Always communicate which edges are oriented vs.
undetermined.

## Core Concepts

### 1. Markov equivalence, CPDAGs, and what is identifiable

Two DAGs are **Markov equivalent** if they entail the same conditional
independences — they have the same skeleton (undirected edges) and the same
**v-structures / colliders** (A → C ← B with A, B not adjacent). Equivalent DAGs
cannot be distinguished by observational independence tests alone (Verma & Pearl,
1990; Andersson, Madigan & Perlman, 1997).

- A **CPDAG** (Completed Partially Directed Acyclic Graph, a.k.a. essential
  graph) represents the whole Markov equivalence class: directed edges are
  oriented in *every* member, undirected edges flip across members.
- Constraint- and score-based methods return a **CPDAG**, not a DAG. Reporting a
  single oriented DAG from such output is a common, serious error.

### 2. Foundational assumptions (state them, always)

- **Causal Markov condition:** each variable is independent of its
  non-descendants given its parents.
- **Faithfulness:** every conditional independence in the distribution is
  implied by the graph structure (no exact cancellations). Near-violations cause
  unstable orientation in finite samples (Spirtes, Glymour & Scheines, 2000).
- **Causal sufficiency:** no unmeasured common causes (latent confounders). PC
  and GES assume this; **FCI does not**.
- **Acyclicity:** most methods assume a DAG (no feedback loops).
- Identifiability hinges on these. Be explicit which the chosen method needs.

## Methodology — algorithm families

### A. Constraint-based (independence-test driven)

- **PC algorithm** (Peter–Clark; Spirtes, Glymour & Scheines, 2000): start from a
  complete undirected graph, remove edges via conditional-independence (CI) tests,
  then orient colliders and propagate (Meek rules). Output: **CPDAG**. Assumes
  causal sufficiency + faithfulness. Order-dependence fixed by **PC-stable**
  (Colombo & Maathuis, 2014). CI tests: Fisher-Z (linear-Gaussian), G²/χ²
  (discrete), KCI (kernel, nonlinear).
- **FCI** (Fast Causal Inference) and **RFCI**: drop causal sufficiency — handle
  **latent confounders and selection bias**. Output: a **PAG** (Partial Ancestral
  Graph) over a **MAG**, with edge marks ○ (unknown), → (ancestor), ↔ (latent
  common cause) (Spirtes et al., 2000; Zhang, 2008).

### B. Score-based search

- **GES** (Greedy Equivalence Search; Chickering, 2002): searches over CPDAG space
  with a two-phase forward (edge-add) / backward (edge-delete) greedy search,
  scoring with a **decomposable, consistent** score — **BIC** (continuous) or
  **BDeu** (discrete). Asymptotically returns the true equivalence class. **fGES**
  is the fast/parallel variant (TETRAD).
- **GIES** (Hauser & Bühlmann, 2012): GES extended to **interventional data** —
  searches over interventional Markov equivalence classes, exploiting experiments
  to orient more edges.

### C. Permutation / ordering search

- **GRaSP** and **BOSS** (Lam, Andrews & Ramsey, 2022): search over variable
  *orderings*; more accurate and scalable than GES on many benchmarks, available
  in causal-learn and TETRAD.

### D. Functional causal models (FCMs) — orient beyond the equivalence class

By assuming a functional form, these identify a **unique DAG**, not just a CPDAG.

- **LiNGAM** — Linear, Non-Gaussian, Acyclic Model (Shimizu, Hoyer, Hyvärinen &
  Kerminen, 2006, JMLR 7:2003–2030): linear SEM with non-Gaussian noise → full
  causal order is **identifiable**. **ICA-LiNGAM** uses ICA; **DirectLiNGAM**
  (Shimizu et al., 2011) is regression-based and avoids ICA local optima.
- **ANM** — Additive Noise Models (Hoyer, Janzing, Mooij, Peters & Schölkopf,
  2008/2009): Y = f(X) + N with N ⟂ X. Nonlinear f breaks the X↔Y symmetry →
  cause/effect direction identifiable.
- **Post-Nonlinear (PNL)** model (Zhang & Hyvärinen, 2009): Y = g(f(X) + N) — most
  general identifiable FCM. In causal-learn.

### E. Continuous-optimization / gradient methods

Reframe combinatorial DAG search as smooth optimization with a differentiable
acyclicity constraint — scales and integrates with deep learning.

- **NOTEARS** (Zheng, Aragam, Ravikumar & Xing, NeurIPS 2018): the acyclicity
  breakthrough — `h(W) = tr(e^{W∘W}) − d = 0` is a smooth, exact characterization
  of acyclicity, solved via augmented Lagrangian. Originally linear; NOTEARS-MLP
  extends to nonlinear.
- **GOLEM** (Ng, Ghassami & Zhang, NeurIPS 2020): likelihood-based score with soft
  acyclicity — faster and more accurate than NOTEARS in the linear-Gaussian/EV
  setting.
- **DAG-GNN** (Yu et al., ICML 2019): VAE/GNN variant for nonlinear and discrete
  data.
- **Caveat:** Reisach, Seiler & Weichwein (NeurIPS 2021, "Beware of the Simulated
  DAG") showed continuous-optimization methods can exploit **varsortability** —
  marginal-variance artifacts of synthetic data scaling. **Standardize data** and
  don't trust synthetic-benchmark wins blindly.

### F. Time-series causal discovery

- **Granger causality**: X Granger-causes Y if past X improves prediction of Y
  beyond Y's own past. Predictive, not structural; fails with latent confounders /
  instantaneous effects / nonlinearity. Use only as a baseline.
- **PCMCI / PCMCI+** (Runge et al., *Science Advances* 2019; PCMCI+ in UAI 2020):
  two-stage — a PC-style condition-selection step, then **Momentary Conditional
  Independence (MCI)** tests controlling for autocorrelation and indirect links.
  PCMCI+ adds contemporaneous links. Implemented in **Tigramite**; pairs with any
  CI test (ParCorr, GPDC, CMI). **LPCMCI** handles latent confounders.
- **VAR-LiNGAM** (Hyvärinen et al., 2010): combines a VAR model with LiNGAM to
  recover both lagged and instantaneous causal effects.

## Tools / Frameworks

- **causal-learn** (py-why, Python; Zheng et al., 2024; docs
  https://causal-learn.readthedocs.io/): the reference Python toolkit — PC, FCI,
  GES, GRaSP, BOSS, LiNGAM family, ANM, PNL, CD-NOD, plus CI tests and graph
  utilities. Default first choice for general discovery.
- **gCastle** (Huawei Noah's Ark Lab; Zhang et al., 2021): gradient-based focus
  (NOTEARS, GOLEM, DAG-GNN, GraN-DAG, ...), PyTorch + GPU, data simulators, and a
  built-in metrics module (SHD, FDR, TPR, F1, NNZ).
- **Tigramite** (Runge; https://github.com/jakobrunge/tigramite): the standard for
  time-series discovery (PCMCI, PCMCI+, LPCMCI, RPCMCI).
- **pcalg** (R; Kalisch et al., *JSS* 2012): mature PC/FCI/RFCI/GES with IDA effect
  estimation.
- **DoWhy** (py-why; https://www.pywhy.org/dowhy/): primarily inference, but its
  GCM module and `dowhy.causal_discovery` wrap discovery; good for the
  discover-then-refute workflow.
- **CausalNex** (QuantumBlack): NOTEARS-based structure learning + Bayesian-network
  reasoning, with expert-knowledge constraints (tabu edges, required edges).
- **TETRAD / py-tetrad**: large library of search algorithms and the
  knowledge/background-constraint framework.

## Practical Patterns

1. **Always inject background knowledge.** Forbidden edges, required edges, and
   tiered time order (a cause can't follow its effect) dramatically reduce the
   equivalence class. Every major tool supports knowledge/tabu constraints — use
   them.
2. **Match method to assumptions and data type:**
   - Possible latent confounders → **FCI / RFCI** (get a PAG), not PC/GES.
   - Linear + non-Gaussian noise → **DirectLiNGAM** (gets a full DAG).
   - Nonlinear, continuous → **ANM / PNL**, or NOTEARS-MLP / DAG-GNN.
   - Discrete/categorical → score-based with **BDeu**, or G²-test PC.
   - High-dim time series → **PCMCI+**.
   - Have interventions/experiments → **GIES** or interventional NOTEARS.
3. **Standardize/scale continuous variables** before continuous-optimization
   methods to avoid varsortability artifacts.
4. **Bootstrap for edge stability.** Resample, re-run discovery, and report
   edge-presence and orientation frequencies rather than one point graph.
5. **Discover → refute → estimate.** Use discovery to *propose* a graph, validate
   with domain experts and refutation/sensitivity checks, then hand the validated
   DAG to **da-12** for effect estimation. Discovery output is a hypothesis, not
   ground truth.
6. **Evaluate with the right metric:**
   - **SHD** (Structural Hamming Distance): count of edge insert/delete/reverse
     ops to match the truth — lower is better; compare against the CPDAG, not a
     DAG, when methods return equivalence classes.
   - **SID** (Structural Intervention Distance; Peters & Bühlmann, 2015): counts
     intervention-distribution errors — closer to what matters for downstream
     effect estimation than SHD.
   - Also F1 / precision / recall on the skeleton, FDR, TPR.

## Anti-Patterns

- **Reporting a single DAG when the method returns a CPDAG/PAG.** Undirected /
  circle-marked edges are genuinely undetermined; orienting them implies
  assumptions you didn't make.
- **Treating Granger causality as structural causality.** It's lagged prediction;
  silent on confounders and contemporaneous effects.
- **Trusting synthetic-benchmark performance of NOTEARS-family methods** without
  standardizing data (varsortability — Reisach et al., 2021).
- **Ignoring latent confounders.** Running PC/GES when unmeasured common causes are
  plausible yields confident but wrong edges. Use FCI or sensitivity analysis.
- **Skipping faithfulness/sufficiency disclosure.** Stakeholders must know the
  result is conditional on assumptions that can't be verified from data alone.
- **Using discovery output directly for policy.** Discovery proposes; it does not
  prove. Validate before acting.
- **Doing effect estimation here.** Backdoor adjustment, IV, DiD, propensity
  scores, synthetic control → **da-12-ab-testing-causal-inference**.

## Troubleshooting

- **Too many undirected edges in the CPDAG:** expected with observational-only
  data. Add background knowledge, use an FCM method (LiNGAM/ANM) if assumptions
  hold, or collect interventional data.
- **Unstable edges across runs/bootstraps:** likely faithfulness near-violations,
  small n, or wrong CI test. Increase data, switch CI test (e.g., KCI for
  nonlinearity), use PC-stable.
- **PC gives different graphs depending on variable order:** use **PC-stable**
  (Colombo & Maathuis, 2014).
- **Dense, implausible graph from NOTEARS:** increase the L1 sparsity penalty,
  standardize data, threshold small weights; consider GOLEM.
- **Nonlinear relationships missed:** linear methods (Fisher-Z PC, linear NOTEARS,
  LiNGAM) can't see them — use KCI tests, ANM/PNL, NOTEARS-MLP, or DAG-GNN.
- **Time-series links look confounded by autocorrelation:** that's exactly what
  **PCMCI** (MCI step) controls for; plain Granger does not.

## References

1. Spirtes, Glymour & Scheines, *Causation, Prediction, and Search*, 2nd ed., 2000 — PC, FCI foundations.
2. Andersson, Madigan & Perlman (1997) — characterization of Markov equivalence / CPDAGs.
3. Chickering (2002) — Greedy Equivalence Search (GES). https://jmlr.org/papers/v3/chickering02b.html
4. Hauser & Bühlmann (2012) — GIES (interventional GES). https://jmlr.org/papers/v13/hauser12a.html
5. Shimizu, Hoyer, Hyvärinen & Kerminen (2006) — LiNGAM, JMLR. https://www.jmlr.org/papers/v7/shimizu06a.html
6. Shimizu et al. (2011) — DirectLiNGAM, JMLR. https://jmlr.org/papers/volume12/shimizu11a/shimizu11a.pdf
7. Hoyer et al. (2008/2009) — nonlinear additive noise models (ANM), NeurIPS.
8. Zhang & Hyvärinen (2009) — Post-Nonlinear (PNL) model. https://arxiv.org/abs/1205.2599
9. Zheng, Aragam, Ravikumar & Xing (2018) — NOTEARS, NeurIPS. https://arxiv.org/abs/1803.01422
10. Ng, Ghassami & Zhang (2020) — GOLEM, NeurIPS. https://arxiv.org/abs/2006.10201
11. Yu et al. (2019) — DAG-GNN, ICML. https://arxiv.org/abs/1904.10098
12. Reisach, Seiler & Weichwein (2021) — "Beware of the Simulated DAG", NeurIPS. https://arxiv.org/abs/2102.13647
13. Colombo & Maathuis (2014) — order-independent PC-stable, JMLR. https://jmlr.org/papers/v15/colombo14a.html
14. Lam, Andrews & Ramsey (2022) — GRaSP / BOSS. https://proceedings.mlr.press/v180/lam22a.html
15. Zhang (2008) — augmented FCI orientation rules for PAGs, AIJ.
16. Runge et al. (2019) — PCMCI, *Science Advances*. https://www.science.org/doi/10.1126/sciadv.aau4996
17. Runge (2020) — PCMCI+, UAI. https://proceedings.mlr.press/v124/runge20a.html
18. Hyvärinen et al. (2010) — VAR-LiNGAM, JMLR. https://jmlr.org/papers/v11/hyvarinen10a.html
19. Peters & Bühlmann (2015) — Structural Intervention Distance (SID). https://arxiv.org/abs/1306.1043
20. Zheng et al. (2024) — causal-learn, JMLR; docs https://causal-learn.readthedocs.io/
21. Zhang et al. (2021) — gCastle toolbox. https://arxiv.org/abs/2111.15155
22. Kalisch et al. (2012) — pcalg, JSS. https://www.jstatsoft.org/article/view/v047i11
23. Tigramite — https://github.com/jakobrunge/tigramite ; DoWhy — https://www.pywhy.org/dowhy/ ; CausalNex docs.
