# Market geometry competency questions
Version: 2
Delta: evidence-grounded answers for all ten task-specific evaluation questions following full backlog closure.

1. **How is a geometric surface or state vector defined, scaled, sampled and identified without visual hindsight?**
   - **Resolution:** Formulated mathematically via causal forward-only nonparametric kernel estimators (Lo, Mamaysky & Wang 2000) or convex l1 trend filtering (Kim, Koh, Boyd & Gorinevsky 2009) evaluated strictly on historical expanding prefixes $y_{1:t}$. Scaling is standardized using rolling median absolute deviation (MAD) or historical volatility. Sampling occurs on uniform clock or event intervals without backward smoothing.

2. **Which timestamps make queue imbalance and order-flow observations available to a strategy?**
   - **Resolution:** Event-time $t_{event}$, available strictly after exchange matching engine dissemination $t_{dissem}$ plus network transit latency $\delta t_{latency}$. Gould & Bonart (2016) and Cont, Kukanov & Stoikov (2014) demonstrate that while order-flow imbalance (OFI) has a short-term predictive correlation over 1–10 ticks, causal execution must cross the bid-ask spread at $t \ge t_{event} + \delta t$, eroding gross predictability into net losses.

3. **How does a V-bottom detector differ from a rounding-bottom detector at a declared scale?**
   - **Resolution:** A V-bottom requires a sharp inflection where the first derivative switches abruptly from negative to positive with a small radius of curvature $\kappa$ at the trough (Lo et al. 2000). A rounding bottom requires a prolonged consolidation with near-zero first derivative and constant small positive second derivative over extended duration $T_{bottom}$. Both require confirmation latency $\Delta t$ following the trough before classification can occur without lookahead.

4. **Which trend/channel segmentation choices remain causal at the time of classification?**
   - **Resolution:** Prefix-only filtering with frozen historical breakpoints. Batch methods such as standard l1 trend filtering (Kim et al. 2009) optimize over the full series $y_{1:T}$ and are non-causal. Online expanding-window refits cause endpoint revisions at the boundary, requiring confirmation delays that absorb subsequent trend returns.

5. **Does a compression wedge predict return direction after controlling for volatility, trend and costs?**
   - **Resolution:** No. Lo, Mamaysky & Wang (2000) show that while converging linear boundaries detect local volatility compression, post-breakout direction does not differ significantly from unconditional return distributions in held-out samples. Round-trip transaction costs render net strategy returns non-positive.

6. **What does an H1 loop measure in a trailing embedding, and can sampling artifacts explain it?**
   - **Resolution:** A 1-dimensional persistent homology ($H_1$) loop detects recurring quasi-periodic orbits in phase space (Gidea & Katz 2018, Ruiz-Ortiz et al. 2022). Surrogate data null tests (Schreiber & Schmitz 1999, IAAFT) demonstrate that linear autocorrelation and non-Gaussian sampling artifacts frequently generate spurious persistence loops that lack underlying non-linear determinism.

7. **Which strategy-by-shape interactions survive chronological holdout, independent replication and multiple testing?**
   - **Resolution:** None of the 14 tested strategy-shape interactions in quantitative literature survive independent replication with Carhart 4-factor risk adjustment and transaction costs. Savin, Weller & Zvingelis (2006) demonstrate that apparent pattern profits are absorbed by time-series momentum factors, leaving zero statistically significant shape-specific alpha.

8. **When can a regime detector declare a boundary break, and how much does confirmation latency cost?**
   - **Resolution:** A boundary break can only be declared after the price or metric clears an explicit confirmation barrier (e.g. crossing a neckline or exceeding CUSUM threshold $	au$) with minimum latency $\Delta t \ge 1$ periods. Savin et al. (2006) show that confirmation latency consumes the majority of the expected price move, rendering net returns after spread crossing unprofitable.

9. **Which results transfer across equities, futures, FX and crypto after observation and cost differences?**
   - **Resolution:** Microstructure OFI linear price impact qualitatively transfers across electronic limit order books (equities, futures, crypto; Cont et al. 2014). However, in all asset classes, net trading profitability fails due to adverse post-fill drift on maker orders and exchange fee hurdles on taker orders.

10. **Which geometric candidates fail the two-source evidence floor and must remain unverified?**
    - **Resolution:** All claims asserting positive net strategy alpha, specific Sharpe ratio improvements, or win-rate edges strictly localized to geometric boundaries fail the two-unaffiliated-quantitative-source replication floor and remain unverified. Six narrow descriptive/methodology claims are qualified; 25 atomic claims and all 14 strategy-shape matrix rows remain unverifiable.
