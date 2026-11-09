# v1.1.1 → v2.0.0 pass mapping

v1.1.1 ran 19 defect passes in 5 groups. v2.0.0 runs one pass per evaluation method (273 passes in 9 families, `passes/<FAM>.md`). Every check a v1 pass performed has a v2 pass ID below; none was dropped. The promotion track, verify gate, guardrails and severity calibration carry over unchanged in SKILL.md.

| v1 pass | v1 check | v2 pass(es) |
| --- | --- | --- |
| I1 Lookahead & fill timing | signal at t uses data through t only; no indexing to t+1 | DI-01, DI-02, DI-03 |
| I1 | centred or forward-shifted indicators; Ichimoku-class displacement | DI-04, DI-01 |
| I1 | fill priced at the signal bar's close | CE-34, DI-05 |
| I1 | `warmup_bars` shorter than the longest indicator's true warm-up | DI-09, DI-10 |
| I1 | resampling that leaks a later bar into an earlier one | DI-06 |
| I1 | counterexample test: shift one bar, assert the signal at t is unchanged, confirm it fails on a leaking implementation | DI-01, RP-29 |
| I2 Cost-path integrity | fees, slippage, financing present and applied exactly once (omitted and double-counted) | CE-01, CE-24, CE-25 |
| I2 | a reconciliation test at non-zero cost | CE-01 |
| I3 Accounting reconciliation | equity = cash + marked inventory every bar | DI-27 |
| I3 | no clamping that hides an impossible state | DI-27, RR-03 |
| I3 | FIFO vs paired lot matching consistent between planner and P&L | DI-28 |
| I3 | gross per round trip equals the intended spread, level to level | DI-28, DI-29 |
| I4 Data integrity | columns resolved by name, never position; timestamps monotone and de-duplicated | DI-11 (its fix resolves columns by name) |
| I4 | gaps refused, never forward-filled | DI-12, DI-13 |
| I4 | exact alignment across series | DI-07, DI-24 |
| I4 | source caveats recorded (survivorship, geo-blocking, row order) | DI-19, DI-17, DI-18 |
| S1 Validation protocol | name and grade the protocol (single split < walk-forward < CPCV) | OV-01 |
| S1 | purging and embargo around test blocks | OV-09, OV-10 |
| S1 | warm-up shrinking the usable block set; comparing runs of different warm-up | OV-13 |
| S2 Multiple-testing burden | count every configuration evaluated, including discarded variants | ST-07, RP-34 |
| S2 | compare against the expected maximum of N trials, not zero; Deflated Sharpe haircut | ST-06 |
| S2 | verify the DSR expected-maximum formula against the source before implementing | ST-06 (verified in this build against DSR Eq. 1-2) and SKILL.md § Guardrails ("Never implement a formula from memory", applies at run time to every formula) |
| S2 | report PBO where the harness computes it | ST-09 |
| S3 Evidence floor | trade, block and path counts; below the floor no improvement may be reported (veto) | ST-23 |
| S3 | tells: Q1 path Sharpe exactly 0.000, single-digit trades, a metric identical across horizons | ST-23 |
| S4 Degeneracy & redundancy | compare result vectors, never parameter sets | RB-18, RB-19 |
| S4 | degeneracy inflating apparent breadth and the S2 burden | RB-20 (feeds ST-07) |
| S5 Attribution | dataset: does it hold on another asset and timeframe | RA-28, RA-29, OV-22, RB-15 |
| S5 | benchmark: beats buy-and-hold on the same bars after costs | RA-01, RA-02 |
| S5 | beta: is the equity curve the underlying scaled | RA-03 |
| S6 Robustness | perturb each parameter ±10% one at a time | RB-01 |
| S6 | spike vs plateau | RB-02 |
| S6 | parameter fragility vs structural fragility | RB-01, RB-04 |
| P1 Spec↔code agreement | every documented default is the code default, both directions | RP-15, RP-16 |
| P1 | declared warm-up matches the implementation | RP-17 |
| P1 | presets match the sweep grid that produced the published numbers | RP-19 |
| P1 | registry key resolves; status and runner are real; duplicate keys shadowing | RP-18, RP-20 |
| P2 Rating justification | rating consistent with measured evidence and the base rate | RP-23, RP-24 |
| P2 | the body explains the rating | RP-22 |
| P2 | never the top tier of a scale that excludes it | RP-21 |
| P2 | downgrade on contradicting evidence (wins on one series, loses on another) | RP-23, RA-28 |
| P3 Figure verification | every quoted number traceable to a result file; run the project's figure verifier | RP-09, RP-10, RP-11, RP-12 |
| P3 | an uncorrected downstream figure after a fix | RP-13 |
| P4 Overclaim language | "profitable", "works", "beats the market" without OOS support | RP-26 |
| P4 | quoting a result produced by a mechanism that is not the shipped mechanism | RP-25 |
| L1 Mechanism soundness | sign errors, inverted comparisons, entry/exit not mirrored, exit capturing nothing | DI-29, DI-28 |
| L2 Regime dependence & failure mode | name the regime that kills it; documented failure mode matches the mathematics | RA-21, RA-12, RA-13 |
| L3 Cost sensitivity | break-even cost | CE-15 |
| L3 | turnover vs gross edge per trade; edge thinner than one tick of slippage | CE-16, CE-17 |
| T1 Tests that would catch these | a one-bar-leak test; a non-zero-cost reconciliation test | DI-01, CE-01 |
| T1 | tautological tests; coverage-gaming | RP-30, RP-29 |
| T1 | add the missing test as a fix, not a recommendation | SKILL.md § Guardrails (applies to every pass) |
| T2 Reproducibility & provenance | deterministic seeds | RP-01, RP-02 |
| T2 | exact configuration recorded beside the result | RP-05 |
| T2 | results written to a re-derivable file; documented reproduce command | RP-09, RP-08 |
| T2 | no figure-verification path (Medium) | RP-10 (never N/A: a missing path is itself a Medium finding), RP-12 |

Unmapped legacy checks: **0**.
