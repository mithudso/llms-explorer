# The 19 passes of /dso, in detail

Read this before the Step-3 dispatch. `SKILL.md` carries the pass index and the group summaries; the
per-pass checks, precedents, and severity specifics live here.

Every precedent cited below is a real defect from the codebase this skill was written against, not a
hypothetical. That is why each one earns a pass.

## Dispatch and grouping

**Dispatch rule.** Collect all findings from all passes **before any write**. Where an Agent tool is
available *and the invoking context permits it*, groups may dispatch as parallel bundles; otherwise
run them sequentially. Every pass emits a row even when `N/A (reason)` — never silently dropped.

### Group 1 — Simulation integrity (is the number real?)
Critical-capable. Run first; a finding here invalidates everything downstream.

- **I1 Lookahead & fill timing.** A signal at bar *t* may use data only through *t*. Hunt: indexing
  that reaches `t+1`; centred or forward-shifted indicators; displacement (Ichimoku-class) where the
  cloud plotted at *t* was computed from *t+n*; a fill priced at the same bar's close after the
  signal; `warmup_bars` shorter than the longest indicator's true warm-up; resampling that leaks a
  later bar into an earlier one. **Counterexample mechanic:** write a test that shifts one input bar
  forward and asserts the signal at *t* is unchanged; confirm it fails against a leaking
  implementation before fixing.
- **I2 Cost-path integrity.** Fees, slippage, and any financing/borrow/carry cost present in the
  P&L path and applied **exactly once**. Check both directions: omitted *and* double-counted.
  Confirm at least one reconciliation test runs at **non-zero** cost — a suite that only tests the
  zero-cost path cannot see a cost bug.
- **I3 Accounting reconciliation.** Equity equals cash plus marked inventory at every bar. No
  clamping that hides an impossible state (`max(0, equity)` masking a negative). Lot matching
  (FIFO vs paired) consistent between the planner and the P&L. Gross per round trip equals the
  intended spread, measured level-to-level, not fill-to-fill.
- **I4 Data integrity.** Columns resolved by **name**, not position. Gaps refused rather than
  forward-filled (filling flatters every volatility and reversion statistic). Timestamps monotone
  and de-duplicated. Alignment across series exact. Source caveats recorded (survivorship,
  geo-blocking, a source whose row order is not what it appears).

### Group 2 — Statistical honesty (does the number mean anything?)
- **S1 Validation protocol.** Name the protocol and grade it: single split < walk-forward <
  combinatorial purged CV. Purging and embargo present around test blocks? Does warm-up shrink the
  usable block set, and is that accounted for when comparing runs of different warm-up lengths?
- **S2 Multiple-testing burden.** Count configurations actually evaluated — including variants tried
  and discarded, which are usually uncounted. Is the candidate compared against **zero** or against
  the **expected maximum** of that many trials? Report the burden explicitly; recommend a Deflated
  Sharpe Ratio haircut where N is large. **Do not reproduce the DSR expected-maximum formula from
  memory — verify it against the source before implementing, and say so.** Report PBO if the harness
  computes it.
- **S3 Evidence floor.** Trade count, block count, path count. A handful of trades cannot separate
  edge from luck at any useful confidence. Tells that the floor was breached: a Q1 path Sharpe of
  exactly `0.000` (most paths took no trade at all), trade counts in single digits, a metric
  identical across horizons. **Below the floor, a result is not eligible to be reported as an
  improvement** — this is a veto, not a caveat.
- **S4 Degeneracy & redundancy.** Compare **result vectors** (equity curves, per-bar exposure),
  never parameter sets. Identical or near-identical outputs across nominally different strategies
  mean one strategy wearing several names — usually a constraint binding on every bar. Precedent:
  three "different" volatility strategies returned numerically identical hourly rows. Degeneracy
  inflates apparent search breadth, which inflates the S2 burden while adding no diversity.
- **S5 Attribution.** Before crediting the strategy, rule out the alternatives: the **dataset**
  (does the result hold on another asset and another timeframe?), the **benchmark** (does it beat
  buy-and-hold on the same bars, after costs?), and **beta** (is the equity curve just the
  underlying scaled?). Precedent: 25/25 configurations positive on BTC daily and 0/25 on SOL hourly
  — the dataset explained more than the strategy. A top-ranked strategy fell from 1st to 23rd purely
  by changing timeframe.
- **S6 Robustness.** Perturb each parameter (±10% is a reasonable default) one at a time and re-run.
  A reported point that collapses under a small nudge is a spike, not a plateau — the parameters were
  fit to noise. Distinguish parameter fragility from structural fragility.

### Group 3 — Claim & provenance integrity
- **P1 Spec↔code agreement, both directions.** Every documented default is the code's actual
  default; every code parameter is documented; declared warm-up matches the implementation; presets
  match the sweep grid that produced the published numbers; the registry key resolves; the declared
  status and runner are real. Check for **duplicate keys silently shadowing** one another. A spec
  whose numbers have drifted from the code is worse than no spec: it is a confident wrong claim.
- **P2 Rating justification.** Any claimed likelihood-of-success must be consistent with the
  measured evidence *and* with the base rate, and the body must explain the rating. **Never write
  the top tier of a rating scale that deliberately excludes it.** Downgrade on contradicting
  evidence; a strategy that wins on one series and loses on another is not a winner.
- **P3 Figure verification.** Every quoted number traceable to a result file. Run the project's own
  figure verifier if one exists. An untraceable figure is Critical — a transcription slip is
  indistinguishable from a fabrication to a reader.
- **P4 Overclaim language.** "Profitable", "works", "beats the market" without out-of-sample support
  behind them. **The specific trap: quoting a result produced by a mechanism that is not the shipped
  mechanism.** Precedent from this codebase — a simulator that re-centred a grid unconditionally
  produced +7.5%; the shippable version could only re-centre under a safety gate that fired once in
  1,875 bars and made placement *worse*. Same word, different mechanism, invalid number.

### Group 4 — Strategy logic & economics
- **L1 Mechanism soundness.** Does the rule express the stated hypothesis? Sign errors; inverted
  comparisons; entry and exit that are not mirror images when they should be; an exit placed where
  it captures nothing (a sell at the level it was bought at captures zero and pays two fees).
- **L2 Regime dependence & failure mode.** Name the regime that kills it and check the documented
  failure mode is the one the mathematics implies — a resting grid converts a sustained trend into a
  maximum-size losing position, and that must be stated rather than discovered.
- **L3 Cost sensitivity.** Compute the break-even cost: at what fee plus slippage does the edge
  vanish? Relate turnover to gross edge per trade. A strategy whose edge is thinner than one tick
  of realistic slippage has no edge.

### Group 5 — Tests & reproducibility
- **T1 Tests that would actually catch these.** Is there a test that fails on a one-bar leak? One
  that reconciles the book at **non-zero** cost? Check for **tautological tests** — a test comparing
  a function to itself, or asserting a value it just computed the same way. Reject coverage-gaming.
  Add the missing test as a fix, not as a recommendation.
- **T2 Reproducibility & provenance.** Deterministic seeds; the exact configuration recorded beside
  the result; results written to a file a reader can re-derive from; a documented command that
  reproduces the run. Absence of a figure-verification path is a Medium finding.

**Skip protocol:** any pass may report `N/A (reason)` or `partial`, never silently dropped. The
Summary line names the active pass count (e.g. `17 of 19 passes active`).

