# Attributed disagreements in auxiliary prose

Version: 1.0.0
Delta: carry explicitly authored disagreement attribution into the existing v4 gate and bind it to the exact prose identity.

The gate previously extracted a disagreement's text and cited URLs but omitted its authored conflict positions and evidence. The semantic reviewer therefore received an assertion without the attribution that the author supplied. The strict preflight also skipped auxiliary prose. A source repair could not correct this transport failure.

`auxiliary_rows` now includes a deep copy of an explicit, non-null disagreement `conflict` and its authored `evidence` in that assertion's identity. The existing strict preflight validates its attributed status, every position and the complete assertion against exact source snapshots. Missing, incomplete, mismatched or unresolved evidence fails before a paid review. Changing attribution or its evidence creates a new assertion version. It cannot inherit a stale positive judgment.

Ordinary summaries, open questions and disagreements without explicit conflict metadata keep their existing identities. Evidence-only legacy disagreements also keep their existing identities. The change preserves the existing v2/v3/v4 contracts, exact reuse rules and dissent history. Authored metadata does not establish semantic support: the native judgment and complete conflict review remain required.

Functional regressions cover three attributed positions, top-level evidence, source and quote tampering, incomplete extraction, missing attribution, object isolation, old identity fixtures, stale judgments, canonical artifact verification and public quote privacy. The maintained sync copies the helper into the research skill. CI explicitly runs the new regression suite. Source quotes and private evidence stay outside public projections.

Verification passes 350 focused tests plus six subtests, including 29 new functional cases, Ruff and all 28 maintained mirror files. Independent review found no actionable defect. A separate read-only audit preserves all 481 assertion records across 32 accepted v4 scopes, 34 canonical artifacts and 54 sealed attempts. It checks 3,184 protected files and 334 snapshots without changes. The actual repaired question retains 31 exact validated judgments, carries all three attributed positions and needs one fresh assertion judgment plus a complete new conflict review.

Qualification of a research question, remote code delivery and verification of the loaded runtime remain separate checks. This repair grants no research acceptance, broad-gap retirement, empty-frontier round or saturation credit.
