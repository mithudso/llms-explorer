---
title: "Prescriptive Analytics and Optimization"
description: "Prescriptive analytics is the fourth and highest rung of Gartner's analytics maturity ladder (descriptive → diagnostic → predictive → prescriptive). It answers 'what should be done?' rather than 'what"
---

# Prescriptive Analytics and Optimization (Decision Science)

## Overview

Prescriptive analytics is the fourth and highest rung of Gartner's analytics maturity ladder (descriptive → diagnostic → predictive → prescriptive). It answers **"what should be done?"** rather than "what happened?" or "what will happen?" by recommending (or automating) a specific action. Gartner defines it as advanced analytics that examines data to answer "what should be done?" using techniques such as **optimization, simulation, complex event processing, graph analysis, heuristics, recommendation engines, and machine learning** ([Gartner, Data & Analytics](https://www.gartner.com/en/topics/data-and-analytics)).

The mental model: **predictive feeds prescriptive.** A demand forecast (da-15) or a propensity model (da-7) produces *parameters*; prescriptive analytics wraps those parameters in a **decision model** — an objective to optimize, decision variables you control, and constraints you must respect — and returns the action that best trades off the objective against the constraints. This skill is the **optimization + decision-science** layer of the curriculum; da-6/da-7 supply the predictions it consumes.

A useful framing is the **decision = objective + decision variables + constraints + uncertainty** quadruple. Choosing a method is mostly about which of those four is hard: linear and continuous → LP; discrete choices → MILP/CP; nonlinear-but-convex → convex/QP; uncertainty dominates → stochastic/robust; many competing objectives → multi-objective; analytical model intractable → simulation.

## Core Concepts

### 1. Predictive → prescriptive distinction
Descriptive/diagnostic give hindsight; predictive/prescriptive give foresight, and **human involvement decreases** as you move toward prescriptive (which can drive automated action). Prescriptive consumes a prediction and adds a *decision rule or optimization* on top ([EAG, 4 types of analytics](https://eaginc.com/understanding-data-analytics/); [Qlik](https://www.qlik.com/blog/embrace-the-future-moving-from-descriptive-to-prescriptive-analytics); [Gartner glossary](https://www.gartner.com/en/topics/data-and-analytics)).

### 2. Linear programming (LP)
Continuous variables, linear objective and constraints. Solved at a polytope vertex by simplex or interior-point. Canonical teaching cases: **blending** (min-cost mix meeting specs) and **product-mix** (max profit s.t. resource limits). LP is the substrate everything else extends ([SciPy linprog](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html); [PuLP](https://coin-or.github.io/pulp/); [Real Python LP](https://realpython.com/linear-programming-python/)).

### 3. Mixed-integer programming (MILP / ILP)
Some/all variables integer or **binary** (yes/no: open a facility, assign a job, select an item). NP-hard; solved by **branch-and-bound / branch-and-cut** with LP relaxations. Binary variables unlock assignment, knapsack, facility location, scheduling, routing. For pure integer problems OR-Tools recommends **CP-SAT**; for mixed continuous+integer it recommends SCIP or a commercial solver ([OR-Tools MIP](https://developers.google.com/optimization/mip); [Gurobi](https://www.gurobi.com/resources/); [SciPy milp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)).

### 4. Convex optimization (QP / SOCP / SDP)
Nonlinear but **convex** → any local optimum is global; solvers reliable and fast. Includes least-squares, quadratic programming (e.g., **Markowitz portfolio**), second-order cone, semidefinite programs. **Disciplined Convex Programming (DCP)** is the rule system CVXPY uses to *verify* convexity before solving — build expressions from functions with known curvature ([CVXPY DCP](https://www.cvxpy.org/tutorial/dcp/index.html); [CVXPY intro](https://www.cvxpy.org/tutorial/intro/index.html); [Boyd & Vandenberghe](https://web.stanford.edu/~boyd/cvxbook/)).

### 5. Constraint programming (CP / CP-SAT)
Declarative: state variables, domains, and combinatorial **constraints** (`AllDifferent`, no-overlap, cumulative); solver searches via propagation + SAT/backtracking. Excels at feasibility-heavy combinatorial problems — **scheduling, rostering, timetabling**. OR-Tools **CP-SAT** is the flagship and has repeatedly won the MiniZinc Challenge ([OR-Tools CP](https://developers.google.com/optimization/cp); [CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver); [OR-Tools, Wikipedia](https://en.wikipedia.org/wiki/OR-Tools)).

### 6. Optimization under uncertainty: stochastic & robust
- **Stochastic programming with recourse**: first-stage (here-and-now) and second-stage **recourse** (wait-and-see corrective) decisions; optimize *expected* cost over scenarios. Classic: newsvendor / two-stage capacity-then-adjust.
- **Robust optimization**: optimize the **worst case** over an uncertainty set (no distribution needed) — more conservative.
- **Distributionally robust (DRO)**: hedge over a *set of distributions*; between stochastic and robust.
- **Chance constraints**: hold a constraint with probability ≥ 1−α ([NEOS Guide](https://neos-guide.org/guide/types/stochastic/); [SIAM J. Optimization, DR Two-Stage SP](https://epubs.siam.org/doi/10.1137/20M1370227); [Birge & Louveaux](https://link.springer.com/book/10.1007/978-1-4614-0237-4)).

### 7. Multi-objective optimization (Pareto)
Competing objectives (cost vs. service, risk vs. return) yield a **Pareto front** of non-dominated tradeoffs. Scalarization: **weighted-sum** (simple, misses non-convex regions) and **epsilon-constraint** (optimize one, bound others — recovers non-convex fronts). Population methods like **NSGA-II** (non-dominated sorting + crowding distance) approximate the whole front in one run; `pymoo` implements both ([pymoo](https://pymoo.org/); [NSGA-II](https://pymoo.org/algorithms/moo/nsga2.html); [Blank & Deb](https://arxiv.org/pdf/2002.04504)).

### 8. Decision analysis (trees, EVPI, utility)
For discrete decisions under uncertainty with few alternatives:
- **Decision trees** alternate decision and chance nodes; fold back by **expected monetary value (EMV)**.
- **EVPI** = (expected value *with* perfect information) − (best EMV *without*) — max you'd pay for perfect info; **EVSI** is the sample-info analogue (Bayesian update).
- **Utility theory**: replace dollars with a **utility function** to encode risk attitude (concave = risk-averse); maximize *expected utility*, not EMV ([Wikipedia, EVPI](https://en.wikipedia.org/wiki/Expected_value_of_perfect_information); [Analytica](https://docs.analytica.com/index.php/Expected_value_of_information_--_EVI,_EVPI,_and_ESVI); [TreeAge](https://www.treeage.com/help/Content/31-Analyzing-Decision-Trees/9-Expected-value-perfect-information-EVPI.htm)).

### 9. Simulation for decisions
When the system is too complex for a closed-form model:
- **Discrete-event simulation (DES)**: entities flowing through resources/queues over event-driven time (`SimPy`; Arena/AnyLogic commercially) — staffing, throughput, capacity.
- **Monte Carlo**: propagate input distributions to an output *distribution* and risk metrics (P10/P50/P90).
- **Simulation-optimization**: wrap a simulation as the objective for an optimizer when no analytic form exists.
- **Queueing theory** (M/M/1, M/M/c, Little's Law `L = λW`) gives analytic baselines for waiting-line/staffing decisions ([DES with SimPy, TDS](https://towardsdatascience.com/object-oriented-discrete-event-simulation-with-simpy-53ad82f5f6e2/); [OR and simulation, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1569190X08000439); [SimLLM, arXiv 2026](https://arxiv.org/html/2601.06543v1)).

### 10. Decision intelligence (DI)
Gartner's operationalizing umbrella: a discipline that **explicitly models decisions as reusable assets**, linking data → analytics → action and closing the loop with outcome feedback. **Decision Intelligence Platforms (DIPs)** compose data, analytics, decision modeling, and AI to support/augment/automate decisions. Per the 2024 Gartner Market Guide, ~33% of surveyed organizations had already deployed DI ([Gartner DI glossary](https://www.gartner.com/en/information-technology/glossary/decision-intelligence); [Market Guide for DI Platforms](https://www.gartner.com/en/documents/5599159); [FICO](https://www.fico.com/blogs/what-decision-intelligence-software-and-should-you-invest-it)).

## Tools / Frameworks

| Tool | Layer | Best for | Notes |
| --- | --- | --- | --- |
| **SciPy.optimize** (`linprog`, `milp`) | low-level | small LP/MILP, NumPy pipelines | `milp` (HiGHS) accepts ≤, ≥, =; `linprog` is ≤ only |
| **PuLP** | modeling | quick LP/MILP, teaching | writes LP/MPS; calls CBC, GLPK, HiGHS, CPLEX, Gurobi, OR-Tools |
| **Pyomo** | modeling | large/structured LP, MILP, NLP, MINLP, stochastic | algebraic; NEOS + many solvers; nonlinear |
| **Google OR-Tools** | modeling+solver | CP-SAT scheduling, vehicle routing, assignment | CP-SAT best-in-class for combinatorial/ILP |
| **CVXPY** | modeling | convex (QP/SOCP/SDP), DCP-verified, portfolio | also DQCP, MICP, geometric programming |
| **Gurobi / CPLEX** | solver | large commercial LP/MILP/QP, speed | licensed (free academic); industry standard |
| **pymoo** | framework | multi-objective / Pareto, NSGA-II | scalarization + EA + visualization |
| **SimPy** | simulation | discrete-event / queueing in pure Python | process-based DES; pair with Monte Carlo |

**Selection heuristic:** convex/continuous nonlinear → CVXPY; combinatorial / scheduling / routing → OR-Tools CP-SAT; plain LP/MILP prototyping → PuLP; large or nonlinear/stochastic algebraic models → Pyomo; performance at scale → Gurobi; many objectives → pymoo; no analytic model → SimPy + an outer optimizer.

## Methodology

1. **Frame the decision, not the prediction.** Name the *objective* (one unit), *decision variables* (what you control), *constraints* (what limits you), *uncertainty* (what you don't know). If you can't write these four, it isn't yet an optimization problem.
2. **Classify the problem** → pick the method family (LP / MILP / convex / CP / stochastic / robust / multi-objective / simulation).
3. **Source parameters** from predictive/statistical models (da-6/da-7/da-15); keep the parameter pipeline separate from the decision model.
4. **Build small, validate, scale.** Prototype on a tiny instance; check feasibility and shadow prices before scaling to a production solver.
5. **Quantify the value of certainty** before buying data: compute **EVPI/EVSI**; run **sensitivity / shadow-price** analysis on LP/MILP.
6. **Stress-test under uncertainty.** Re-solve across scenarios (stochastic) or over an uncertainty set (robust); report the *distribution* of outcomes via Monte Carlo.
7. **Close the loop (DI).** Deploy, capture realized outcomes, feed back to refit parameters and re-tune.

## Practical Patterns

- **Blending / diet**: LP, min cost s.t. composition specs → PuLP or SciPy.
- **Product mix / capacity**: LP, max margin s.t. resource limits; read shadow prices for the bottleneck.
- **Assignment / matching**: binary MILP (Hungarian for the pure case) → OR-Tools.
- **Knapsack / selection**: binary MILP, max value s.t. budget → CP-SAT.
- **Scheduling / rostering**: CP-SAT with `NoOverlap` / cumulative + interval vars.
- **Vehicle routing (VRP/CVRP/VRPTW)**: OR-Tools routing library with capacity/time-window dimensions.
- **Inventory / newsvendor**: stochastic — balance overage vs. underage; critical-ratio quantile of demand is the optimal order.
- **Portfolio**: convex QP (Markowitz) in CVXPY; multi-objective (return vs. risk) → efficient frontier.
- **Staffing / call center**: queueing baseline (Erlang-C) → DES (SimPy) → simulation-optimization for shift design.

## Anti-Patterns

- **Optimizing a forecast instead of a decision.** A prediction with no objective/constraints/action is still predictive analytics (→ da-15/da-7).
- **Forcing nonlinearity into LP** or ignoring non-convexity. Linearize deliberately (piecewise, big-M) or move to convex/MINLP.
- **Big-M too large.** Loose big-M wrecks MILP relaxations and numerics; pick the tightest valid bound.
- **Weighted-sum for non-convex Pareto fronts.** Silently misses regions; use epsilon-constraint or NSGA-II.
- **Single-scenario "optimal" plans.** Deterministic optimization on a point forecast is brittle; use stochastic/robust or Monte Carlo stress.
- **Trusting a local optimum as global** on non-convex/MINLP without saying so. Report the optimality gap.
- **Decision tree with made-up probabilities** and no EVPI. If the recommendation flips under plausible probabilities, you need more info.
- **Ignoring solver status.** Optimal vs. feasible/time-limit vs. infeasible vs. unbounded are different answers — check the status code.

## Troubleshooting

- **Infeasible.** Relax/soften constraints (slack with penalty); use IIS/conflict refiner (Gurobi, CP-SAT); usual culprit is over-tight equalities or unit mismatches.
- **Unbounded.** Missing upper bound or sign error in objective; add realistic bounds.
- **MILP too slow.** Tighten big-M, add cuts/symmetry-breaking, warm-start, set a MIP gap, or switch MILP → CP-SAT.
- **CVXPY "not DCP".** Expression has unknown/wrong curvature; rewrite with DCP atoms (`cp.quad_form`, `cp.norm`, `cp.log_sum_exp`).
- **Numerical issues.** Rescale variables/coefficients to similar magnitudes; avoid mixing 1e-6 and 1e9.
- **Simulation too noisy.** More replications, common random numbers, report confidence intervals.
- **Stochastic model explodes.** Reduce scenarios via scenario reduction / sample average approximation (SAA).

## References

1. Gartner — Data & Analytics + prescriptive definition, 2025. https://www.gartner.com/en/topics/data-and-analytics
2. Gartner — Decision Intelligence glossary, 2024-2025. https://www.gartner.com/en/information-technology/glossary/decision-intelligence
3. Gartner — Market Guide for Decision Intelligence Platforms, 2024. https://www.gartner.com/en/documents/5599159
4. Google OR-Tools — MIP, CP, CP-SAT, Routing, 2024. https://developers.google.com/optimization
5. CVXPY — DCP tutorial + intro, 2024-2025. https://www.cvxpy.org/tutorial/dcp/index.html
6. Boyd & Vandenberghe — Convex Optimization (Cambridge, 2004). https://web.stanford.edu/~boyd/cvxbook/
7. Pyomo — official documentation. https://www.pyomo.org/documentation
8. PuLP — COIN-OR docs, 2024. https://coin-or.github.io/pulp/
9. SciPy — linprog / milp (HiGHS), v1.17, 2025. https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html
10. Gurobi — Mathematical Optimization resources, 2024-2025. https://www.gurobi.com/resources/
11. NEOS Guide — Stochastic Programming, 2024. https://neos-guide.org/guide/types/stochastic/
12. SIAM J. Optimization — Distributionally Robust Two-Stage SP. https://epubs.siam.org/doi/10.1137/20M1370227
13. Birge & Louveaux — Introduction to Stochastic Programming (Springer, 2nd ed., 2011). https://link.springer.com/book/10.1007/978-1-4614-0237-4
14. pymoo — NSGA-II docs; Blank & Deb, 2020. https://pymoo.org/ , https://arxiv.org/pdf/2002.04504
15. Wikipedia / Analytica / TreeAge — EVPI, EVSI, decision-tree analysis, 2024. https://en.wikipedia.org/wiki/Expected_value_of_perfect_information
16. DES with SimPy (TDS) + OR/simulation (ScienceDirect) + SimLLM (arXiv 2026). https://towardsdatascience.com/object-oriented-discrete-event-simulation-with-simpy-53ad82f5f6e2/
17. Qlik / EAG — descriptive→prescriptive maturity, 2024. https://www.qlik.com/blog/embrace-the-future-moving-from-descriptive-to-prescriptive-analytics
