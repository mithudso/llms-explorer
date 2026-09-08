---
title: "Cohort and Retention Analytics"
description: "Retention answers the single most important growth question: do users who join"
---

# Cohort & Retention Analytics

## Overview

Retention answers the single most important growth question: do users who join
keep coming back? Acquisition without retention is a leaky bucket — you pour
users in the top and they fall out the bottom, so growth stalls no matter how
much you spend. This skill covers the math and methods for measuring retention
across **cohorts** (groups of users grouped by a shared start or behavior),
reading **retention curves**, doing **growth accounting** (decomposing user and
revenue change into its parts), and the SaaS revenue-retention metrics
(NRR/GRR). It is the methods layer beneath product-led and SaaS growth.

Scope boundary: this skill is the **measurement** of who stays and by how much.
For funnels/activation/North-Star use `da-21-product-analytics`; for
probabilistic CLV (BG/NBD, gamma-gamma) use `da-23-customer-lifetime-value`;
for hazard-rate/survival modeling use `da-24-survival-analysis`; for
experiment-driven lift use `da-12-ab-testing-causal-inference`.

## Core Concepts

### 1. Acquisition vs behavioral cohorts

- **Acquisition (time) cohort** — users grouped by *when* they first signed up
  or activated (same day/week/month). Answers *when* users churn and lets you
  compare cohort quality over time. It does not tell you *why*
  ([Amplitude, Cohort Retention Analysis, 2024](https://amplitude.com/blog/cohorts-to-improve-your-retention)).
- **Behavioral cohort** — users grouped by *what they did* (completed
  onboarding, used a key feature, invited a teammate), independent of join
  date. Answers *which behaviors correlate with retention* — the input to
  finding your activation/aha moment
  ([Amplitude, Guide to Behavioral Cohorting, 2024](https://amplitude.com/blog/guide-to-behavioral-cohorting);
  [Amplitude Docs, Behavioral Cohorts](https://amplitude.com/docs/analytics/behavioral-cohorts)).
- Workflow: use acquisition cohorts to *detect* a retention problem, behavioral
  cohorts to *diagnose and fix* it (find the behavior that separates retained
  from churned users)
  ([Chameleon, Cohort Analysis 101, 2024](https://www.chameleon.io/blog/cohort-analysis)).

### 2. Retention-curve shapes

A retention curve plots % of a cohort still active against periods-since-start.
Canonical shapes ([Amplitude, Retention Curve](https://amplitude.com/explore/analytics/retention-curve);
[Churnkey, Retention Curves, 2024](https://churnkey.co/blog/retention-curves/);
[Product Growth, Retention Curves Guide](https://productgrowth.in/resources/guides/retention-curves-guide/)):

- **Declining** — slopes to zero; no group finds lasting value → no PMF.
- **Flattening** — steep early drop, then levels off at a **retention floor**
  (the long-term stable %). A flattening curve is the classic *signal of
  product/market fit*: a stable set of users is hooked.
- **Smile** — drops, flattens, then rises as churned users resurrect (often
  via network effects or re-engagement). The aspirational shape (Slack, Airbnb).
- **Dead-on-arrival** — near-vertical drop to ~0 by period 2; users tried it
  once and never returned.

The **retention floor** (where the curve flattens) is your real long-term
retention. Improving the *floor* (curve flattens higher) compounds far more
than improving early-period retention that still decays to the same floor.

### 3. Retention definitions: N-day, unbounded, bracket, rolling

Choosing the definition changes the numbers dramatically — always state which
you use ([Amplitude, 3 Ways to Measure Retention, 2024](https://medium.com/@amplitudeHQ/3-ways-to-measure-user-retention-2af5e4e82a45);
[Mixpanel Docs, Retention](https://docs.mixpanel.com/docs/analysis/reports/retention);
[Amplitude, N-Day Retention for Mobile Games](https://amplitude.com/blog/n-day-retention-for-mobile-games)):

- **N-day (classic / bounded)** — % of cohort active on *exactly* day N. Strict;
  best for daily-use products. Day-2 retention = 50% means 50% came back
  specifically on day 2.
- **Unbounded ("rolling" in Mixpanel's loose sense)** — % active on day N *or
  any day after*. Always ≥ N-day. Good for infrequent-use products. Note: this
  is **not** a true moving average despite the "rolling" label.
- **Bracket / range** — % active within a custom window (Day 0; Days 1–7; Days
  8–14). A flexible generalization of N-day; matches a product's natural cadence.
- **Rolling retention (classic survival sense)** — % active on day N or later,
  used to estimate a survival/lifetime curve; conceptually same as unbounded.
- **Bounded vs unbounded asymmetry:** bounded undercounts weekly/monthly-cadence
  products; unbounded inflates if you never re-baseline. Match the metric to the
  product's expected frequency.

### 4. Retention ↔ engagement

Retention is **binary** (active or not in a period) and is the *output*;
**engagement depth** (frequency × breadth of actions) is the leading indicator.
Deeper engagement → habit → retention → sustainable growth — Reforge frames
retention/engagement as "the power plant of the growth model"
([Reforge, Retention is the Silent Killer](https://www.reforge.com/blog/retention-engagement-growth-silent-killer);
[Reforge, Growth Loops are the New Funnels](https://www.reforge.com/blog/growth-loops);
[Conor Dewey, Reforge Recap: Engagement + Retention](https://www.conordewey.com/blog/reforge-engagement-retention)).
Practical move: don't just track the retained/churned flag — track *how deeply*
retained users engage, because depth predicts long-term value and is the lever
you pull to raise the retention floor.

### 5. Growth accounting (users)

Decompose period-over-period active users into additive components. The
**fundamental identity** ([Social Capital / Jonathan Hsu, Diligence Part 1, 2017](https://medium.com/swlh/diligence-at-social-capital-part-1-accounting-for-user-growth-4a8a449fddfc);
[Amplitude, Growth Accounting, 2024](https://amplitude.com/blog/growth-accounting)):

```
MAU(t) = MAU(t-1) + new(t) + resurrected(t) - churned(t)
```

- **new** — first-ever active this period.
- **retained** — active last period AND this period (carried over).
- **resurrected** — active in some past period, inactive last period, active now.
- **churned** — active last period, inactive now (enters as a negative).

**User Quick Ratio (QR)** = (new + resurrected) / churned. Users gained per user
lost. QR > 1 means growing; rule of thumb QR ≥ ~1.5 is healthy
([Hsu, Diligence Part 1, 2017](https://medium.com/swlh/diligence-at-social-capital-part-1-accounting-for-user-growth-4a8a449fddfc);
[The SaaS CFO, SaaS Quick Ratio, 2024](https://www.thesaascfo.com/saas-quick-ratio/)).

### 6. Growth accounting (revenue / MRR)

Same identity applied to dollars ([Social Capital / Hsu, Diligence Part 2, 2017](https://medium.com/swlh/diligence-at-social-capital-part-2-accounting-for-revenue-growth-551fa07dd972);
[Lenny Rachitsky, Bottom-Up SaaS Metrics](https://www.lennysnewsletter.com/p/the-most-important-bottom-up-saas-69d)):

```
MRR(t)   = new(t) + retained(t) + resurrected(t) + expansion(t)
MRR(t-1) = retained(t) + churned(t) + contraction(t)
```

- **expansion** — existing customers paying more (upsell/seats).
- **contraction** — existing customers paying less (downgrade) but not zero.
- **churned** — dropped to zero.

**SaaS Quick Ratio** = (new MRR + expansion MRR) / (churned MRR + contraction
MRR). Mamoon Hamid (Social Capital) popularized a target of **QR ≥ 4** for
early-stage SaaS — $4 of growth for every $1 lost
([The SaaS CFO, 2024](https://www.thesaascfo.com/saas-quick-ratio/);
[Cobloom, SaaS Quick Ratio](https://www.cobloom.com/blog/saas-quick-ratio-how-to-measure-your-startups-revenue-health)).

### 7. DAU/WAU/MAU and stickiness

- **DAU / WAU / MAU** — unique active users in a 1-day / 7-day / 30-day window
  ([Mixpanel, MAU Benchmarks, 2026](https://mixpanel.com/blog/mau/);
  [Gainsight, DAU/MAU Guide](https://www.gainsight.com/essential-guide/product-management-metrics/dau-mau/)).
- **Stickiness ratio = DAU/MAU** (× 100) ≈ how many days/month an average
  monthly user shows up; DAU/MAU = 20% ≈ 6 days/month. Use **WAU/MAU** for
  products not meant for daily use
  ([Statsig, Understanding DAU/MAU](https://www.statsig.com/perspectives/understanding-daumau-key-metrics-for-product-success)).
- Benchmarks: daily-habit/social aim for DAU/MAU > 50%; B2B SaaS averages ~30%;
  <20% can be fine for infrequent products
  ([CleverTap, DAU vs MAU, 2024](https://clevertap.com/blog/dau-vs-mau-app-stickiness-metrics/)).

### 8. Churn rate vs retention rate (and the asymmetry)

- Single-period complements: **Retention = 1 − Churn**
  ([Churnkey, Churn vs Retention](https://churnkey.co/blog/churn-rate-vs-retention-rate/);
  [Orb, Churn vs Retention](https://www.withorb.com/blog/churn-rate-vs-retention-rate);
  [Maxio, Retention vs Churn](https://www.maxio.com/saaspedia/retention-rate-vs-churn-rate)).
- **The compounding asymmetry:** churn compounds multiplicatively — 5%/mo churn
  ≈ 0.95¹² ≈ 54% retained after a year, NOT 1 − (5%×12). Always state the period
  and never linearly annualize.
- Customer (logo) churn ≠ revenue churn — a small customer and a whale count the
  same in logo churn but very differently in revenue churn. Track both.

### 9. Revenue / dollar retention — NRR & GRR

Cohort the *revenue* of a customer group and measure it a year later
([Drivetrain, GRR](https://www.drivetrain.ai/strategic-finance-glossary/what-is-gross-revenue-retention-formula-benchmarks);
[Orb, NRR vs GRR](https://www.withorb.com/blog/nrr-vs-grr);
[SaaS Capital, Good Retention Rate, 2025](https://www.saas-capital.com/blog-posts/what-is-a-good-retention-rate-for-a-private-saas-company/)):

```
GRR = (Starting ARR − churn − contraction) / Starting ARR              # ≤ 100%, no expansion
NRR = (Starting ARR − churn − contraction + expansion) / Starting ARR  # can exceed 100%
```

- **GRR** measures pure leak prevention (best-in-class 90–100%).
- **NRR** measures retention *plus* expansion — NRR > 100% means a cohort grows
  in revenue with zero new logos (the "negative net churn" holy grail).
- Benchmarks (private B2B SaaS, ~2024): median NRR ~100–106%; enterprise (>$100K
  ACV) ~118%; SMB (<$25K ACV) ~97%; best-in-class NRR > 120–130%; median GRR
  ~88–90% ([Optifai, B2B NRR Benchmarks](https://optif.ai/learn/questions/b2b-saas-net-revenue-retention-benchmark/);
  [Ordway, NRR Guide](https://ordwaylabs.com/resources/guides/net-revenue-retention-guide/)).

### 10. Sean Ellis test & power-user curve

- **Sean Ellis (40%) test** — survey: *"How would you feel if you could no
  longer use [product]?"* If ≥ 40% say **"very disappointed,"** you likely have
  product/market fit
  ([FitSignal, Sean Ellis 40% Test](https://www.fitsignal.com/blog/sean-ellis-40-percent-test);
  [LearningLoop, Sean Ellis Score](https://learningloop.io/glossary/sean-ellis-score);
  [StartupArchive, Sean Ellis on PMF](https://www.startuparchive.org/p/sean-ellis-on-how-to-tell-if-you-have-product-market-fit)).
- **Power-user curve (L28 / L30)** — histogram of users by active days in the
  month (1 of 30 … 30 of 30), coined by the Facebook growth team ("Ln" = active
  n of last 30). A right-skewed "smile" with a heavy right tail signals strong
  engagement a single DAU/MAU average hides
  ([a16z / Andrew Chen, Power User Curve, 2018](https://a16z.com/the-power-user-curve-the-best-way-to-understand-your-most-engaged-users/);
  [andrewchen.com](https://andrewchen.com/power-user-curve/)).
- Use together: Sean Ellis = attitudinal PMF; flattening curve + heavy-tailed
  power-user curve + healthy stickiness = behavioral PMF.

### 11. Building cohort tables in SQL

Canonical three-step pattern ([Holistics, Cohort Retention with SQL](https://www.holistics.io/blog/calculate-cohort-retention-analysis-with-sql/);
[Cube, Cohort Retention Recipe](https://cube.dev/docs/product/data-modeling/recipes/cohort-retention);
[O'Reilly, SQL for Data Analysis ch.4](https://www.oreilly.com/library/view/sql-for-data/9781492088776/ch04.html)):

1. **Assign each user a cohort** (their first-activity period).
2. **Compute period offset** for every activity (`period − cohort_period`).
3. **Pivot/aggregate** counts per (cohort, offset) and divide by cohort size.

```sql
WITH first_activity AS (          -- 1. cohort assignment
  SELECT user_id,
         DATE_TRUNC('month', MIN(event_date)) AS cohort_month
  FROM events GROUP BY user_id
),
activity AS (                     -- 2. period offset per active month
  SELECT e.user_id, fa.cohort_month,
         DATE_TRUNC('month', e.event_date) AS active_month,
         (DATE_PART('year',  e.event_date) - DATE_PART('year',  fa.cohort_month)) * 12
       + (DATE_PART('month', e.event_date) - DATE_PART('month', fa.cohort_month)) AS month_number
  FROM events e
  JOIN first_activity fa USING (user_id)
),
sizes AS (
  SELECT cohort_month, COUNT(DISTINCT user_id) AS cohort_size
  FROM first_activity GROUP BY cohort_month
)
SELECT a.cohort_month, a.month_number,           -- 3. retention table
       COUNT(DISTINCT a.user_id) AS active_users,
       ROUND(100.0 * COUNT(DISTINCT a.user_id) / s.cohort_size, 1) AS retention_pct
FROM activity a JOIN sizes s USING (cohort_month)
GROUP BY a.cohort_month, a.month_number, s.cohort_size
ORDER BY a.cohort_month, a.month_number;
```

- For **zero-activity periods** (gaps), build a date spine with
  `generate_series`/recursive CTE, `LEFT JOIN` activity, and `COALESCE(...,0)`
  so missing months render as 0 rather than vanishing
  ([Holistics, 2024](https://www.holistics.io/blog/calculate-cohort-retention-analysis-with-sql/)).
- Self-joins read more clearly for **N-day** retention; window functions are
  terser but harder to review. Pick legibility for shared analytics code.

## Tools / Frameworks

- **Amplitude / Mixpanel** — built-in N-day/unbounded/bracket retention,
  behavioral cohorts, stickiness, power-user curves. Read the docs for the
  *exact* retention definition each uses before comparing dashboards.
- **SQL warehouse (BigQuery / Snowflake / Postgres)** — `DATE_TRUNC`,
  `DATE_DIFF`/`DATE_PART`, `generate_series`, window functions; the portable
  ground truth behind any BI tool.
- **Reforge / Lenny's Newsletter / a16z (Andrew Chen)** — growth loops,
  retention/engagement engine, power-user curve.
- **Social Capital "8-ball" growth accounting** — the canonical
  new/resurrected/churned decomposition and quick ratio.
- **BI layer (Looker/Cube/Metabase)** — cohort retention as a reusable model;
  Cube ships a retention recipe.

## Methodology

1. **Define the active event** explicitly (login? key action? value moment?).
   Everything downstream depends on this.
2. **Pick the retention definition** (N-day vs unbounded vs bracket) to match
   product usage frequency. State it on every chart.
3. **Build acquisition cohorts**, plot curves, find the **retention floor**.
4. **Segment by behavioral cohort** to find the activation behavior that lifts
   the floor.
5. **Run growth accounting** (users and MRR) to see whether growth is new-driven
   or retention-driven; compute the quick ratio.
6. **Layer revenue retention** (NRR/GRR) for monetized products.
7. **Validate PMF** with flattening curve + power-user tail + Sean Ellis test.

## Practical Patterns

- Lead every retention chart with the **definition + active-event + cohort
  granularity**; otherwise numbers are uncomparable.
- Optimize the **retention floor (curve shape)**, not just Day-1 — a higher
  asymptote compounds.
- Report **NRR and GRR together**: NRR can mask churn that expansion papers
  over; GRR exposes the underlying leak.
- Use **WAU/MAU** (not DAU/MAU) for weekly-cadence products so stickiness isn't
  artificially low.
- Decompose growth with the **8-ball / growth-accounting** view in every
  business review so "we grew 10%" reveals new vs resurrected vs reduced churn.

## Anti-Patterns

- **Linearly annualizing churn** (5%/mo ≠ 60%/yr). Compound it.
- **Comparing N-day to unbounded** numbers as if equivalent — unbounded is
  always higher.
- **Reporting only NRR** and hiding gross churn behind expansion.
- **A single DAU/MAU average** masking a bimodal power-user split — show the
  histogram.
- **Day-1-retention obsession** while the curve still decays to the same floor.
- **Ignoring the survivorship of recent cohorts** — the newest cohort has no
  long-tail data yet; don't compare its Day-30 to an old cohort's before 30 days
  have elapsed.

## Troubleshooting

- **Retention "improved" suspiciously** → check whether the active-event
  definition or the retention type (bounded↔unbounded) changed.
- **Recent cohorts look worse** → likely **right-censoring**, not real decline;
  only compare offsets that have fully matured for all cohorts shown.
- **NRR > 100% but business feels shaky** → inspect GRR and logo churn;
  expansion from a few whales can hide broad SMB churn.
- **Curve never flattens** → no PMF in that segment; re-segment by behavioral
  cohort to find a sub-population that *does* flatten.
- **SQL retention has gaps/jumps** → you're missing zero-activity periods; add a
  date spine + `COALESCE`.
- **Stickiness looks terrible** → wrong window; switch DAU/MAU → WAU/MAU for
  infrequent products.

## References

- Amplitude — Cohort Retention Analysis (2024): https://amplitude.com/blog/cohorts-to-improve-your-retention
- Amplitude — Guide to Behavioral Cohorting (2024): https://amplitude.com/blog/guide-to-behavioral-cohorting
- Amplitude Docs — Behavioral Cohorts: https://amplitude.com/docs/analytics/behavioral-cohorts
- Amplitude — Retention Curve: https://amplitude.com/explore/analytics/retention-curve
- Amplitude — 3 Ways to Measure Retention (2024): https://medium.com/@amplitudeHQ/3-ways-to-measure-user-retention-2af5e4e82a45
- Amplitude — N-Day Retention for Mobile Games: https://amplitude.com/blog/n-day-retention-for-mobile-games
- Amplitude — Growth Accounting (2024): https://amplitude.com/blog/growth-accounting
- Mixpanel Docs — Retention: https://docs.mixpanel.com/docs/analysis/reports/retention
- Mixpanel — MAU Definition & 2026 Benchmarks: https://mixpanel.com/blog/mau/
- Churnkey — Retention Curves (2024): https://churnkey.co/blog/retention-curves/
- Churnkey — Churn Rate vs Retention Rate: https://churnkey.co/blog/churn-rate-vs-retention-rate/
- Product Growth — Retention Curves Guide: https://productgrowth.in/resources/guides/retention-curves-guide/
- Chameleon — Cohort Analysis 101 (2024): https://www.chameleon.io/blog/cohort-analysis
- Reforge — Retention is the Silent Killer: https://www.reforge.com/blog/retention-engagement-growth-silent-killer
- Reforge — Growth Loops are the New Funnels: https://www.reforge.com/blog/growth-loops
- Conor Dewey — Reforge Recap: Engagement + Retention: https://www.conordewey.com/blog/reforge-engagement-retention
- Social Capital / Jonathan Hsu — Diligence Part 1: Accounting for User Growth (2017): https://medium.com/swlh/diligence-at-social-capital-part-1-accounting-for-user-growth-4a8a449fddfc
- Social Capital / Jonathan Hsu — Diligence Part 2: Accounting for Revenue Growth (2017): https://medium.com/swlh/diligence-at-social-capital-part-2-accounting-for-revenue-growth-551fa07dd972
- Lenny Rachitsky — Most Important Bottom-Up SaaS Metrics: https://www.lennysnewsletter.com/p/the-most-important-bottom-up-saas-69d
- The SaaS CFO — SaaS Quick Ratio (2024): https://www.thesaascfo.com/saas-quick-ratio/
- Cobloom — SaaS Quick Ratio: https://www.cobloom.com/blog/saas-quick-ratio-how-to-measure-your-startups-revenue-health
- Gainsight — DAU/MAU Guide: https://www.gainsight.com/essential-guide/product-management-metrics/dau-mau/
- Statsig — Understanding DAU/MAU: https://www.statsig.com/perspectives/understanding-daumau-key-metrics-for-product-success
- CleverTap — DAU vs MAU (2024): https://clevertap.com/blog/dau-vs-mau-app-stickiness-metrics/
- Orb — Churn vs Retention Rate: https://www.withorb.com/blog/churn-rate-vs-retention-rate
- Orb — NRR vs GRR: https://www.withorb.com/blog/nrr-vs-grr
- Maxio — Retention vs Churn: https://www.maxio.com/saaspedia/retention-rate-vs-churn-rate
- Drivetrain — Gross Revenue Retention: https://www.drivetrain.ai/strategic-finance-glossary/what-is-gross-revenue-retention-formula-benchmarks
- SaaS Capital — Good Retention Rate (2025): https://www.saas-capital.com/blog-posts/what-is-a-good-retention-rate-for-a-private-saas-company/
- Optifai — B2B SaaS NRR Benchmarks: https://optif.ai/learn/questions/b2b-saas-net-revenue-retention-benchmark/
- Ordway — NRR Guide: https://ordwaylabs.com/resources/guides/net-revenue-retention-guide/
- FitSignal — Sean Ellis 40% Test: https://www.fitsignal.com/blog/sean-ellis-40-percent-test
- LearningLoop — Sean Ellis Score: https://learningloop.io/glossary/sean-ellis-score
- StartupArchive — Sean Ellis on PMF: https://www.startuparchive.org/p/sean-ellis-on-how-to-tell-if-you-have-product-market-fit
- a16z / Andrew Chen — The Power User Curve (2018): https://a16z.com/the-power-user-curve-the-best-way-to-understand-your-most-engaged-users/
- andrewchen.com — The Power User Curve: https://andrewchen.com/power-user-curve/
- Holistics — Calculate Cohort Retention with SQL (2024): https://www.holistics.io/blog/calculate-cohort-retention-analysis-with-sql/
- Cube — Cohort Retention Recipe: https://cube.dev/docs/product/data-modeling/recipes/cohort-retention
- O'Reilly — SQL for Data Analysis, ch.4 Cohort Analysis: https://www.oreilly.com/library/view/sql-for-data/9781492088776/ch04.html
