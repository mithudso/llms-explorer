# Market Graph Geometry and Strategy Regime Efficacy

Version: 1.0.0  
Delta: first evidence-bound synthesis of seven role outputs, causal detector specifications and a fail-closed interaction matrix.  
Research date: November 10–11, 2026.  
Status: research synthesis and proposed experiment. The commissioned strong hypothesis is **not established**. This run did not execute a backtest, estimate a new confidence interval or demonstrate a profitable strategy-state pair. Canonical gate and publication receipts are managed separately by the orchestrator.

## Research judgment

The acquired literature supplies computable descriptions of order-book state, algorithmic chart patterns, rolling topological summaries and market correlation networks. It also supplies source-specific associations and important negative observations. The packet does not establish that a named shape defines a reproducible region of positive executable strategy edge with demonstrated decay outside that region.

The most useful distinction is between four questions:

1. Can the object be defined and computed?
2. Does it describe a market state or coincide with a historical event?
3. Does it predict a future observable beyond ordinary trend, volatility and liquidity?
4. Can a specified order policy convert that prediction into net returns, and does an independently tested boundary explain its failure?

A verified answer to an earlier question does not answer a later one. This is the organizing rule for the monograph and matrix. In particular, a next-tick forecast cannot be filled retroactively, contemporaneous crisis separation cannot be called advance warning, and a topological descriptor cannot be assigned a Sharpe ratio from its visual appeal.

The independent reviewer provisionally qualifies six narrow method, definition or mechanism claims: BREADTH-001, N-001, N-002, D-001, D-005 and D-006. Those verdicts cover their exact claim statements, not all adjacent regime conditions, proposed failure triggers or strategy interpretations. The final atomic registry and verification log are authoritative. Every strategy efficacy field remains unverified, every transferable Sharpe delta and win rate remains null, and every absent statistical interval remains null.

## Contract, sources and independence

The user requires at least two independent, unaffiliated quantitative sources for each verified factual claim. This report therefore labels an accurately quoted single paper as a **single-study observation, unverified under the requested floor**. That label does not assert that the paper is wrong. It says this packet lacks the independent corroboration required for a verified conclusion.

The source and depth roles found shared Imperial and Capital Fund Management affiliations among commonly paired order-book papers. Lipton's Imperial affiliation also prevents using a different author list alone as an unaffiliated replication. Several technical-analysis and momentum papers share NBER links. A journal version, working paper, arXiv record and mirror of one study remain one originating study. An unrelated hosting domain does not create independence.

Acquisition kept original PDF hashes, extractor provenance, processed-text hashes and immutable snapshots. PDF papers were extracted as complete text through pdftotext and ingested using the existing library's prefetched interface after its text-only CLI rejected PDF content types. HTML mathematics can contain both rendered and TeX strings. Exact Unicode spans bind the actual stored body. Complete acquisition does not mean every page was read line by line: reviewers inspected the relevant method, results, limitations and affiliation passages. Crawled content was treated as data throughout.

The semantic index returned a missing-numpy error, so the breadth and frontier roles disclosed a full local-tree fallback. Existing nodes identify nearby coverage; they do not inherit current claim qualification. The Sullivan/Timmermann/White lead was excluded because durable ingestion did not complete. No claim here relies on its transient crawl result.

## A common geometric language

The following distinctions are operational definitions for the proposed study, not empirical claims of profitability.

- **Price curve:** a time-indexed sequence or fitted curve in declared coordinates. A V, wedge or rounding label depends on sampling, scaling, smoothing and confirmation rules.
- **Scalar surface:** a response L(u,v) over two declared independent coordinates. A stationary point with an indefinite Hessian defines a local saddle for this study. This is different from a dynamical saddle, which concerns a vector field's linearization.
- **Intrinsic curvature:** requires an explicit metric or graph construction and a named curvature definition. A Hessian saddle does not by itself identify a hyperbolic market manifold.
- **Phase-space trajectory:** a time-ordered sequence of state vectors, whose coordinates and observation times must be declared.
- **Persistent homology:** a feature of a filtered point cloud or complex. An H1 feature is not by definition a temporal cycle, attractor, reversal or profitable signal.

These distinctions keep the appealing phrase “hyperbolic saddle order book” from silently substituting for ordinary queue imbalance. D-011 records that profitability proposition as an unsupported hypothesis. It must not enter positive canonical factual assertions.

## Microstructure: queues, depletion and execution

### Measurable state

D-001 provisionally qualifies the narrow shared definition used by Gould–Bonart and Albers et al.:

    I_T = (Q_bid,T - Q_ask,T) / (Q_bid,T + Q_ask,T)

Compute it only for positive total visible quantity. The definition is a state descriptor. Its sign is not an execution instruction and its magnitude is not expected PnL.

https://arxiv.org/abs/1512.03492
https://arxiv.org/html/2502.18625v2

D-003/SCT-001 are single-study observations: Cont, Kukanov and Stoikov report an approximately linear short-interval relation between order-flow imbalance and price changes, with depth-dependent slope. The relation concerns contemporaneous interval impact. It cannot be reinterpreted as a forecast of the next interval without a separate test.

https://ar5iv.labs.arxiv.org/html/1011.6402

D-004/SCT-003 are single-study observations: Huang, Lehalle and Rosenbaum specify order-flow intensities as functions of current book state inside constant-reference-price periods. A schematic candidate generator is:

    A f(q) = sum_e lambda_e(q) [f(q + delta_e) - f(q)]

This expression describes the intended state-dependent event model. Fitting an intensity function does not establish a profitable policy or a geometric saddle.

https://ar5iv.labs.arxiv.org/html/1312.0563

SCT-002 is a single-study observation: Gould and Bonart report one-tick-ahead classification information from imbalance, with tick-regime differences in their Nasdaq sample. D-002 deliberately preserves the distinction between that prediction test and Albers' Binance next-price cases. The tests, instruments and execution settings do not establish one invariant predictive boundary.

### The fill-selection barrier

D-005 provisionally qualifies the narrow observation that Huang and Albers explicitly include queue state and order priority or position in passive-execution analysis. D-006 provisionally qualifies adverse post-fill midprice drift across DeLise's Treasury-futures simulation and Albers' Binance experiment. These are a mechanism and an execution warning, not a universal expected-loss theorem.

https://arxiv.org/html/2407.16527v1
https://arxiv.org/html/2502.18625v2

D-007 and D-009 are single-study observations: Albers' examined naive two-sided quoting and simple imbalance strategies perform poorly in that experiment; favorable imbalance can put a maker at the end of the longer queue, whereas taking liquidity incurs taker fees. The paper's warning that negative fill-probability/return association does not alone force a negative unconditional expectation must remain attached. Its sample-specific results do not certify that every imbalance policy fails.

D-008 and D-010 are single-study model observations: Chávez-Casillas and Figueroa-López separate touch depletion from new in-spread orders and relax restrictive constant-spread/reset assumptions. These are useful model-boundary tests, not independently replicated profitability results.

https://arxiv.org/html/1407.5684v3

### Causal microstructure specification

Reconstruct the book from sequenced events received by T. Keep exchange, receipt, decision, submission and fill times separate. Fit imbalance response, event hazards and queue-transition parameters on preceding data. Record actual queue position, cancellations, partial fills, fees and reference-price changes.

For a proposed depth-curvature feature, define cumulative depth D_T(x) over a fixed tick band separately on each side. Freeze the normalization and derivative regularization in training. A two-coordinate liquidity surface must declare its coordinates and scalar response before testing stationary points or curvature. Hidden liquidity, replenishment, feed gaps, varying tick/spread regimes and latency are proposed robustness tests. They are not collectively verified observed decay laws merely because the main definition claim qualifies.

## Meso: chart geometry with observable confirmation

### Literature boundary

BREADTH-001 provisionally qualifies method adoption: Lo, Mamaysky and Wang and the unaffiliated Savin, Weller and Zvingelis team use kernel-based algorithmic technical-pattern recognition in U.S. equity studies. Savin adapts Lo's method, so this is evidence that the method is used and computable, not independent replication of trading efficacy.

https://web.mit.edu/wangj/www/pap/LoMamayskyWang00.pdf
https://www.biz.uiowa.edu/faculty/gsavin/papers/hsrevision_paw_10%2019%2006.pdf

SCT-004/BREADTH-005 are single-study observations: Lo's conditional-return comparisons report incremental information for some technical indicators. Their information content must remain distinct from excess net trading profits. BREADTH-004 is a single-study negative observation: the October 19, 2006 Savin manuscript reports no evidence of stand-alone head-and-shoulders profitability for its S&P 500 sample and weak corresponding evidence for Russell 2000. Keep the 1990–1999, asset-group and strategy definitions attached. This does not justify a universal “ineffective” matrix label.

BREADTH-002 and BREADTH-003 are single-study method observations: Kim et al. describe l1 trend filtering as a batch estimator using whole history and producing piecewise-linear estimates. That supports segmentation as a descriptor. A causal implementation is a separate project requirement.

https://web.stanford.edu/~boyd/papers/pdf/l1_trend_filter.pdf

### Proposed detectors and their timestamps

| Shape | Proposed causal detector | Earliest permissible label | Required falsification |
|---|---|---|---|
| V-bottom | Prefix-fitted two-segment log-price regression with minimum leg length, negative first slope and positive recovery slope. Train decline/rebound thresholds before evaluation. | After the recovery confirmation, never at the past trough. | Repeated lows, gaps, delayed entry, volatility/reversal baselines and execution cost. |
| Rounding inflection | Trailing local polynomial or spline; normalized curvature and a sustained slope crossing. | At the current endpoint after declared confirmation bars. | Bandwidth, coordinate scaling, endpoint noise and jump sensitivity. |
| Compression wedge | Trailing upper/lower quantile envelopes with positive but shrinking width and minimum causal touches. | Compression at T; directional breakout only after an observed breach of the previously fixed envelope. | Repainting pivots, moving lines after the breach, false breaks and volatility-only explanations. |
| Trend/channel segmentation | Prefix second-difference penalization with training-selected lambda; store issued endpoint labels. | After the prefix fit finishes at T. | Full-sample revisions, lambda fragility, whipsaws and holding-time sensitivity. |

For the proposed prefix trend estimate:

    x^(T) = argmin_x 0.5 * sum_(t<=T) (y_t-x_t)^2
                         + lambda * sum_(t<T) |x_(t-1)-2x_t+x_(t+1)|

The historical strategy must use the estimate issued at its own decision time. Refitting at a later final sample and replacing earlier segment labels violates this experiment's information rule. A delayed classifier is permissible if the delay is recorded and charged; a backdated classifier is not.

No acquired paired result establishes V-bottom, rounding or wedge-specific net efficacy. Rounded-bottom and saddle candidates also fall below the user CVS floor. Their inclusion as definitions in this dossier must not promote them back into active signal research.

### Horizon and momentum distinctions

SCT-007 is a single-study observation from the **August 2010 working draft** of Moskowitz, Ooi and Pedersen: intermediate-horizon persistence and longer-horizon partial reversal are reported in its futures sample. The packet did not treat that draft as the final 2012 paper.

https://elmwealth.com/wp-content/uploads/2017/06/timeseriesmomentum.pdf

SCT-005 is a single-study observation about Daniel and Moskowitz's cross-sectional winner-minus-loser momentum: panic states after declines/high volatility coincide with crash losses and rebounds. SCT-006 is a separate single-study historical momentum hazard result. Neither establishes a V-bottom entry rule, nor can the realized future rebound label the state at an earlier trade time.

https://kentdaniel.net/papers/published/jfe_16.pdf
https://www.nber.org/system/files/working_papers/w20660/w20660.pdf

## Macro: phase space, topology and crisis descriptors

### Computable topology versus early warning

N-001 provisionally qualifies a method statement: Gidea–Katz and Ruiz-Ortiz et al. construct sliding-window point clouds and summarize persistent homology with persistence landscapes. This qualifies a computable descriptor, not directional predictability or returns.

https://arxiv.org/html/1703.04385
https://arxiv.org/html/2203.05603

For this proposed experiment, form trailing state or delay vectors using returns, volatility and volume features available by T. Fit scaling, embedding lag, dimension, metric, filtration and window length in training. All observations in the point cloud must be available at the decision time. N-008 is an unverified source equation plus an explicitly operational timestamp derivation: a source window indexed from t through t+w−1 is available only after its final observation. This does not by itself accuse the source of a backtest error.

N-004 and N-005 are single-study observations from Ismail et al. Their threshold selection uses values just before known historical crises and then covers all dates. Their reported event-classification percentages are not trade win rates. The dossier does not copy those percentages into strategy metrics or infer a causal deployment from that retrospective design.

https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2022.940133/full

N-006 is a single-study negative observation: Ruiz-Ortiz et al. report that the average turbulence index generally peaks after studied crashes start and can lag slow declines. This is important against an unconditional early-warning interpretation. It is not a proof that no topology feature can ever predict a market outcome.

### Correlation-network curvature

N-002 provisionally qualifies a contemporaneous historical observation: Sandhu et al. and Samal et al. find increased average Ollivier–Ricci curvature in crisis periods for their respective graph constructions. The sign is attached to that curvature definition and those samples. Do not transfer it to Forman curvature, a price-chart curvature or a future-risk estimate.

https://arxiv.org/html/1505.05182
https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2020.624373/full

N-003 is a single-study counterinterpretation: Sánchez García and Gherghe argue that their studied construction is an ex-post crisis descriptor rather than an indicator of tendencies toward a crisis. This does not contradict the narrower historical co-movement claim in N-002; it challenges the predictive interpretation.

https://arxiv.org/html/2405.07134

### Dynamical reconstruction and novelty triage

N-007 is a single methodological-source observation: Schreiber and Schmitz explain that rejection of a stationary linear surrogate null can reflect nonstationarity or nonlinearity, and nonlinearity alone does not establish deterministic chaos. A phase portrait therefore needs explicit surrogate nulls and observation assumptions before it can support an attractor interpretation.

https://arxiv.org/html/chao-dyn/9909037

The proposed volatility-volume manifold, recurrence network and information-geometric distances remain computable research specifications where defined. They do not acquire efficacy from mathematical sophistication. Catastrophe theory additionally needs identified state equations, controls and stability quantities. The frontier downgraded the catastrophe, information-geometry and streaming-liquidity-PH leads under the user's threshold. No dormant lead is called a discovered trading signal.

## Strategy–shape interaction synthesis

The machine-readable matrix contains 14 shape/regime rows. Its effective and ineffective arrays remain empty. Candidate arrays identify tests to run; they are not recommendations or established effects. In-boundary Sharpe delta, win rate and confidence interval are null, and out-of-boundary decay is null where not established.

| Strategy class | Candidate geometric interaction | What the packet supports | Missing test before efficacy |
|---|---|---|---|
| Trend following | Piecewise trend channels, confirmed recovery, wedge breakout, macro risk filters. | Algorithmic segmentation and source-specific horizon/momentum observations. | Incremental held-out net edge beyond simple momentum/volatility, with causal boundaries and independent replication. |
| Mean reversion | Confirmed V/rounding, range/channel, equilibrium-spread tube. | Proposed causal definitions; no qualifying shape-specific profitability pair. | Stationarity/break tests, delayed entry cost, unconditional baseline, borrow/funding where relevant. |
| Breakout | Compression wedge, neckline or prior channel boundary. | Computable pattern-recognition methods; source-specific chart observations. | Frozen pre-breach boundaries, false-break rates, spread/slippage and multiple-testing correction. |
| Statistical arbitrage | Equilibrium-spread tube, cross-asset network, phase-space neighborhood. | Candidate research designs; no acquired paired efficacy result for these geometric mappings. | Training-only basket selection, out-of-sample stability, factor/momentum controls, borrow and capacity. |
| Market making | Queue depletion, visible imbalance, depth response and proposed surface metrics. | Scoped queue/execution mechanisms and adverse-fill warnings. | Joint fill/return policy evaluation with actual queue position, latency, costs, inventory utility and venue replication. |

A verified adverse-fill mechanism does not prove every market maker is unprofitable. A source-specific poor strategy result does not prove an entire strategy class ineffective. The example +1.4 Sharpe delta and 68% win rate were schema examples and were not adopted.

## Experiment needed to adjudicate the strong hypothesis

Define an available-information filtration F_T and freeze a detector g(F_T), state boundary and strategy policy in each chronological training fold. The target is a strategy-state interaction in **future executable net outcomes**, after controls for ordinary trend, volatility, spread, liquidity and asset effects. Test whether geometry adds information rather than merely renaming those variables.

Use chronological outer evaluation and chronological inner tuning. Purge labels whose outcome horizons overlap evaluation boundaries; use a dependence-appropriate embargo. Keep point-in-time universes, delisted assets, publication vintages and realistic observation timestamps. Never random-split overlapping windows or assume a bar-close signal fills at the same close.

Compare against the unconditional strategy, simple-state conditioning, geometry ablations, frequency-matched random labels and suitable stochastic/dependence-aware nulls. Log all asset, shape, smoothing, threshold, lag, holding-time and strategy variants for multiplicity control. Reserve later periods and separate venues/assets for replication.

For passive policies, evaluate fill probability jointly with fill-conditioned return rather than multiplying unrelated estimates. Include queue position, partial fills, cancellations, maker/taker fees, rebates, inventory, funding and latency. For relative-value strategies include borrow, funding, structural breaks and basket-selection history. Report independent sample blocks, turnover, drawdown, tail loss, fill rates and capacity with any Sharpe estimate.

A positive in-boundary result alone does not establish the user's “strictly within” condition. Failure to reject zero outside a boundary does not demonstrate no edge. Predeclare an economically meaningful equivalence margin and a dependence-aware confidence-interval method. Numerical intervals must come from the cited experiment or a separately executed replication; subjective confidence labels are not statistical intervals.

All procedures in this section are **proposed controls**, not results from an executed backtest.

## Ontology, viability and coverage

The map begins with 30 candidates across all five CFE neighborhoods: parent domains, siblings, children, adjacent concepts and frontier methods. Three paper-grounded expansion probes add ten candidates. The local inventory links existing nearby microstructure, momentum/reversal, short-horizon strategy and volatility-conditioned guides rather than claiming every parent is new.

The user CVS is the equal-weight mean of empirical testability, theoretical grounding and signal potential on a 1–5 scale; equal weights are an explicit assumption because the user specified dimensions without weights. The canonical CFE score is separate and uses its prescribed five-axis weights and hard gates. Neither score is an estimated alpha or probability of trading success.

Forty candidates were scored, six fall below the user floor, and 28 remain active questions after both selection gates. The canonical arithmetic checker passed. The productive probe rates were 4/34 (11.76%), 3/37 (8.11%) and 3/40 (7.50%). These are discovery rates, not strategy performance.

The family is **MAP-BOUNDED-NOT-SATURATED**. No two consecutive empty expansion rounds occurred; the ten competency questions are mapped rather than resolved. The depth role reached its default six-deepening-pass cap with rates 40%, 28.57%, 22.22%, 0%, 10% and 0%, so it reports **BUDGET_EXHAUSTED**, not depth saturation. Source acquisition and monograph inclusion do not complete the 28 open questions.

Priority continuation topics are kernel-bandwidth fragility, prefix endpoint revisions, lambda sensitivity, confirmation latency, raw versus risk-adjusted returns, geometry uplift beyond basic covariates, queue execution and topology stability under sampling changes. Current scores and exact remaining items are preserved in the frontier artifacts.

## Seven-role execution record and persistence boundary

| Role | Work performed | Boundary |
|---|---|---|
| Source & Seed Pioneer | Foundational primary-paper discovery, library ingestion, immutable evidence and initial concepts. | Failed Sullivan ingest excluded; shared affiliations retained. |
| Depth Specialist | Focused queue/depletion mechanism reviews, independent execution counterevidence and six deepening passes. | Default pass cap; no saddle efficacy or saturation. |
| Breadth Specialist | Full local inventory fallback, five-neighborhood map, causal definitions and three grounded probes. | Mapping is not completed per-concept research. |
| Empirical & Falsification Auditor | Independent exact-text/independence/semantic review and bounded evidence repairs. | Descriptor support does not confer strategy efficacy; final gate remains separate. |
| Novelty Scout | Full-text topology, curvature and surrogate-method acquisition with computability/causality screening. | Retrospective/ex-post evidence retained; no novelty-to-alpha inference. |
| Persistence/Sync Curator | Monograph, relationship formatting and explicit remaining-work record, relieving synthesis load. | Orchestrator serializes canonical writes, public projections, git and landing receipts. |
| Frontier Evaluator | Forty two-system CVS assessments, aliases, pruning and three measured productive probes. | Twenty-eight questions remain; no frontier saturation. |

Raw text, quotes, snapshots, complete prompt and runtime records stay in the private research repository. Public projections must come from current canonical claims and a valid bound gate. The orchestrator records actual commits and absolute publication paths in landing receipts after delivery; this document does not assert a merge, website deployment or qualified full-suite completion.

Embedding/Ollama/indexing services remain intentionally paused. Keyword compilation, semantic indexing, skill installation/audits, tree synchronization and website generation have distinct completion states; none follows merely from writing this dossier. Exact outstanding actions and any actual gate/publication blocker belong in the remaining-work record and final continuation memory.
