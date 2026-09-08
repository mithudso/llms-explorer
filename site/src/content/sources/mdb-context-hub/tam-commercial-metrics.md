---
title: "TAM commercial metrics"
description: "This reference is the numbers-and-definitions layer for a TAM. It answers three recurring questions:"
---

# TAM Commercial Metrics

## Overview

This reference is the **numbers-and-definitions** layer for a TAM. It answers three recurring questions:
what a retention metric *is* and how to compute it, what MEDDPICC means and how to apply it to an
installed-base account, and what the *current* SaaS benchmark figures are. It carries formulas, a scoring
rubric, and dated tables — not document structure or framework selection (that lives in
`tam-operations (references/tam-expertise.md)`), and not prose drafting (that lives in `executive-comms`).

Every benchmark figure below is **dated and attributed**. Benchmarks move year to year and differ by data
set. **Verify before customer-facing use** — pull the current figure from the named source rather than
quoting this file in a deliverable.

## SaaS retention foundation (ARR → GRR → NRR)

All retention metrics measure one cohort's recurring revenue over a fixed window (usually 12 months),
comparing the **starting ARR** of customers who existed at the start of the period to what that same cohort
is worth at the end. New-logo ARR landed *during* the window is excluded — these metrics describe the
existing base only.

Four movements act on a cohort's starting ARR over the window:

| Movement | Definition | Effect |
| --- | --- | --- |
| **Expansion** | Upsell, cross-sell, seat growth, price increase within the cohort | + |
| **Contraction** | Downgrade / partial reduction (downsell, seat cuts) | − |
| **Churn** | Full cancellation of a customer | − |
| (New logos) | Customers acquired during the window | **excluded** |

**GRR** counts only the losses. **NRR** also credits expansion. GRR is always ≤ 100%; NRR can exceed 100%
when expansion outweighs losses.

## NRR (Net Revenue Retention)

Also called Net Dollar Retention (NDR) or Net ARR Retention — same metric.

### Formula

```
NRR = (Starting ARR + Expansion − Contraction − Churn) / Starting ARR
```

### Worked example

A cohort starts the year at **$1,000,000** ARR. Over 12 months: **+$180,000** expansion, **−$40,000**
contraction, **−$70,000** churn.

```
NRR = (1,000,000 + 180,000 − 40,000 − 70,000) / 1,000,000
    = 1,070,000 / 1,000,000
    = 107%
```

The same cohort's **GRR** (losses only, no expansion credit):

```
GRR = (1,000,000 − 40,000 − 70,000) / 1,000,000 = 890,000 / 1,000,000 = 89%
```

Read together: this book is **growing the existing base 7%** net, but is **losing 11%** to contraction and
churn before any expansion. A wide NRR–GRR gap means expansion is masking a leaky base — a churn problem the
expansion motion is papering over.

### Segment benchmarks (median NRR)

| Segment (by ACV) | Median NRR | Strong target | Source / date |
| --- | --- | --- | --- |
| Enterprise (ACV > $100K) | ~118% | 115%+ | Optifai Pipeline Study (N=939), 2026 |
| Mid-market (ACV $25K–$100K) | ~108% | 105–110% | Optifai Pipeline Study (N=939), 2026 |
| SMB (ACV < $25K) | ~97% | 100%+ | Optifai Pipeline Study (N=939), 2026 |

The Optifai segmentation above is cross-referenced with ChartMogul (2024) and widely re-reported by
aggregators citing SaaS Capital. SaaS Capital's own Sep 2025 read is by ACV tier rather than named segment:
median NRR **102%** for the $25K–$50K tier (top quartile 111%, bottom quartile 97%), with the explicit finding
that higher ACV correlates with higher retention. Whole-population medians span a range across data sets:
~106% (Optifai, 2025-2026) down to ~101% in compressed-market reads (Vena / industry, 2025). The single
number means little without segment, ARR stage, and pricing model — always pair NRR with its ACV tier.

Reading rule: **97% NRR is at-median for SMB but a red flag for enterprise.** SMB books churn more and expand
less on self-serve motions; holding 100%+ at SMB scale is genuinely strong. The same 97% in an enterprise
book signals a structural retention problem.

### Levers a TAM pulls to raise NRR

NRR rises by lifting expansion or cutting losses. A TAM's influence is mostly on the loss side and on
expansion readiness:

- **Expansion** — drive adoption depth and new use cases so the account *qualifies* for upsell; surface
  expansion signals (usage near tier limits, new teams onboarding) to the AE early; time the play to a
  realized-value moment.
- **Churn reduction** — protect against the renewal risks below: catch health decline early, close adoption
  gaps, keep a live executive relationship, and document realized value before the renewal window opens.
- **Contraction reduction** — defend seat/usage counts by tying them to outcomes the buyer tracks; renegotiate
  rather than let a silent downgrade ride.

GRR has a hard ceiling of 100% — a TAM cannot grow GRR, only stop it leaking. NRR is the metric where TAM
adoption work shows up as upside.

## MEDDPICC

MEDDPICC is a B2B deal-qualification framework: eight elements that test whether a deal is real, winnable, and
worth forecasting. Lineage: **MEDDIC** (6 elements) was created at PTC in 1996; **MEDDICC** added Competition
as categories crowded; **MEDDPICC** added **Paper Process** for modern procurement, legal, and security
review. A TAM uses it less for net-new qualification and more to **de-risk renewals and qualify expansion**
inside the installed base.

### The eight letters

| Letter | Meaning | TAM application (installed-base adaptation) |
| --- | --- | --- |
| **M** — Metrics | Quantified business outcome the solution delivers | Realized ROI / value-to-date you can show at renewal; baseline vs. current |
| **E** — Economic Buyer | The single person who can release budget | Renewal budget owner — may have changed since the land; re-confirm |
| **D** — Decision Criteria | Standards used to compare options | Documented success criteria the renewal/expansion is judged against |
| **D** — Decision Process | Sequence of approvals to a signature | The renewal and expansion approval path inside the account |
| **P** — Paper Process | Procurement, legal, security, IT-governance steps | Renewal paperwork, re-procurement, security re-review timing |
| **I** — Identify Pain | Cost of inaction — what happens if nothing changes | The unsolved problem or risk that justifies continued / expanded spend |
| **C** — Champion | Internal advocate who sells when you are absent | Is the champion still here, promoted, or gone? Single-threaded risk |
| **C** — Competition | What the buyer also evaluates | Displacement risk, competing internal priorities, in-house / OSS alternative |

> The **TAM application** column is a customer-success adaptation, not sourced sales doctrine. Published
> MEDDPICC sources address net-new deal qualification; the renewal/expansion recast is this reference's own
> framing.

### Scoring rubric

Two common rubrics — use whichever your team standardizes on:

- **0–4 evidence scale:** 0 = unknown, 1 = assumed, 2 = stated by the buyer, 3 = tested with the buyer,
  4 = documented and confirmed.
- **Red / Yellow / Green:** Green = fully validated from the buyer; Yellow = partial, gaps remain;
  Red = unknown or guessed.

Forecast discipline: a renewal or expansion carrying **any Red** (or a 0–1) on Economic Buyer, Champion, or
Paper Process should not sit in the commit forecast until the gap is closed. Weight the elements to your
motion — e.g., for a renewal, weight Champion and Paper Process higher because a departed champion or a
surprise security re-review is what actually stalls the signature.

## SaaS benchmarks (2025-2026)

All figures dated and attributed. **Verify before customer-facing use.**

### Retention — NRR / GRR

| Metric | Figure | Segment / scope | Source / date |
| --- | --- | --- | --- |
| Median NRR (by segment) | ~118% / ~108% / ~97% | Enterprise / mid-market / SMB | Optifai Pipeline Study (N=939), 2026 |
| Median NRR (by ACV tier) | 102% (111% top q / 97% bottom q) | $25K–$50K ACV | SaaS Capital, Sep 2025 |
| Median NRR (population) | ~106% | B2B SaaS, all | Optifai, 2025-2026 |
| Median NRR (compressed) | ~101% | Industry, all | Vena, 2025 |
| Median GRR | ~90% | All SaaS | Benchmarkit (citing KeyBanc-Sapphire survey), 2025 |
| GRR quartiles | <85% / 90% / 95% | Bottom / median / top, scaling to $10M ARR | reported by DualEntry, citing Bessemer (BVP), 2025 |
| GRR target | 92–95% / 88–92% | Enterprise / mid-market | SaaS Capital, 2025 |

### Churn

| Metric | Figure | Scope | Source / date |
| --- | --- | --- | --- |
| Annual logo churn (median) | ~3.5% | B2B SaaS | Recurly Churn Report, 2025 |
| Monthly logo churn | 3–5% / 1.5–3% / 1–2% | SMB / mid-market / enterprise | Vena, 2025 |
| Revenue churn (implied) | ~7–10% annual | = 100% − GRR | Derived from GRR sources, 2025 |

### Expansion

| Metric | Figure | Scope | Source / date |
| --- | --- | --- | --- |
| Expansion as % of new ARR | 40–50% | SaaS at scale | Vena / industry, 2025 |
| Expansion ARR share | ~58% / ~67% | $50M–$100M / >$100M ARR cos | as reported by industry summaries citing 2025 SaaS Benchmarks (High Alpha / Poyar), Nov 2025 |

A TAM reading: at scale, **expansion drives the majority of new ARR** — which is exactly the revenue a TAM's
adoption and renewal work influences. Growth gets easier as retention rises because you are not refilling a
leaking bucket before you can grow.

## Anti-patterns / common mistakes

- **Quoting one NRR median without the segment.** 97% is healthy for SMB and a crisis for enterprise; a bare
  "good NRR is 110%" is wrong for most segments.
- **Confusing NRR and GRR.** NRR can exceed 100%; GRR cannot. If someone reports "retention of 115%," they
  mean NRR — GRR above 100% is a definitional error.
- **Letting expansion mask churn.** A high NRR with a low GRR is a leaky base hidden by upsell. Always read
  the two together; the gap is the churn signal.
- **Treating MEDDPICC as net-new only.** The biggest renewal/expansion risk is usually a departed champion or
  an unscoped paper process — qualify those before forecasting the renewal.
- **Forecasting a renewal with a Red on Economic Buyer or Champion.** Single-threaded, budget-unconfirmed
  renewals slip; the rubric exists to keep them out of commit.
- **Quoting a stale benchmark in a deliverable.** Every figure here carries a date; re-pull the current
  number from the named source before it goes customer-facing.
- **Benchmark without a recommendation.** A number with no prescriptive next step is not a TAM insight.

## References

- SaaS Capital — "What is a Good Retention Rate for a Private SaaS Company in 2025?" (Sep 18, 2025):
  https://www.saas-capital.com/blog-posts/what-is-a-good-retention-rate-for-a-private-saas-company/
- Benchmarkit — "2025 SaaS Performance Metrics" (2025):
  https://www.benchmarkit.ai/2025benchmarks
- Bessemer Venture Partners — GRR quartile benchmarks, scaling to $10M ARR (2025):
  https://www.dualentry.com/blog/gross-revenue-retention-grr
- Optifai — "B2B SaaS Net Revenue Retention Benchmark" — segment NRR (Enterprise/Mid-market/SMB), Pipeline
  Study N=939, cross-referenced with ChartMogul Subscription Growth Benchmark (2024, N=2,100), 2025-2026:
  https://optif.ai/learn/questions/b2b-saas-net-revenue-retention-benchmark/
- Vena Solutions — "2025 SaaS Churn Rate: Benchmarks, Formulas and Calculator" — monthly logo churn by segment,
  expansion as % of new ARR (2025):
  https://www.venasolutions.com/blog/saas-churn-rate
- Recurly — Churn Report, median annual B2B SaaS logo churn ~3.5% (2025), as reported via Vena (2025):
  https://www.venasolutions.com/blog/saas-churn-rate
- Growth Unhinged (Kyle Poyar / High Alpha) — "2025 SaaS Benchmarks Report" (800+ cos, Nov 12, 2025):
  https://www.growthunhinged.com/p/2025-saas-benchmarks-report
- Weflow — "MEDDPICC Sales Methodology: Framework, Scorecard, and Implementation Guide" (2025):
  https://www.weflow.ai/blog/meddpicc
- Arpedio — "MEDDPICC: A Practitioner's Guide to the Sales Qualification Framework" (2025):
  https://arpedio.com/resources/guides/meddpicc
- Force Management — "MEDDIC vs. MEDDPIC" (origin and PTC history):
  https://www.forcemanagement.com/blog/meddic-vs.-meddpic-the-meaning-difference-and-benefits-of-each-for-sales-qualification-force-management
