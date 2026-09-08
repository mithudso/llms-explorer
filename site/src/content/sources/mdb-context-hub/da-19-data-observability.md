---
title: "Data Observability"
description: "Data observability is the discipline of measuring and maintaining the health and reliability of data across its lifecycle — the ability to fully understand the state of the data in your systems, so yo"
---

# Data Observability

## Overview

**Data observability** is the discipline of measuring and maintaining the health and reliability of data across its lifecycle — the ability to fully understand the state of the data in your systems, so you can detect, triage, resolve, and prevent **data incidents** before they reach downstream consumers. The term was popularized by Monte Carlo (Barr Moses, 2019) as an explicit analog to software **observability** (the logs/metrics/traces discipline for services): instead of asking "is my service up?", data observability asks "is my data trustworthy, and if not, why?"

It is a distinct discipline, not a synonym for any of its neighbors:

- **Data quality** is the *target state* (accurate, complete, trustworthy data) and the broad discipline of achieving it. Observability is one modern *tactic* for sustaining quality at scale.
- **Data testing** (e.g. dbt tests, Great Expectations) is *assertion-based*: you declare expected conditions up front and check them. It catches the failures you anticipated.
- **Monitoring** watches individual pipeline/job metrics.
- **Observability** is broader than all three: it continuously watches the *behavior* of data and systems, surfaces *unexpected* anomalies (not just the ones you wrote tests for), and ties them to **lineage and context** so you can answer "what broke, where, who is affected, and why." Testing tells you about known-unknowns; observability surfaces unknown-unknowns.

Why it matters now: as data stacks fragment (ingestion, warehouse, transform, BI, reverse-ETL, ML/AI features), the surface area for silent failure explodes, and bad data quietly poisons dashboards, ML features, and AI products. Gartner projects ~50% of enterprises with distributed data architectures will adopt data observability tooling by 2026 (up from ~20% in 2024).

## Core Concepts

### The Five Pillars

Monte Carlo's canonical framework decomposes data health into five measurable pillars. The first four are *table-/field-level signals*; the fifth is the connective tissue.

1. **Freshness** — Is the data up to date? How recently was a table updated, and does the update cadence match expectations? Stale tables (e.g. a daily table that didn't load by 9 AM) are the most common, most user-visible incident.
2. **Volume** — Is the amount of data as expected? Row-count completeness over time. Sudden drops (a partial load) or spikes (a duplicate load / fan-out bug) signal problems.
3. **Schema** — Has the structure changed? Added/removed/retyped columns, dropped or renamed tables. Schema drift from upstream producers is a leading root cause of breakage ("who changed this column type?").
4. **Distribution / Quality** — Is the data within expected ranges at the field level? Null rates, uniqueness, value ranges, category cardinality, percent-zero, format conformance. This pillar is where field-level *data-quality* signals live.
5. **Lineage** — The map of upstream sources and downstream consumers for every asset, ideally to **column level**. Lineage is the holistic pillar: it turns a freshness/volume/schema/distribution anomaly into an *impact assessment* ("which 14 dashboards and 2 ML features depend on this broken table, and what upstream job caused it"). Lineage powers both root-cause (upstream) and blast-radius (downstream) analysis.

### Data Downtime

**Data downtime** is the period when data is partial, erroneous, missing, or otherwise wrong. It is the headline reliability metric and is modeled as:

> Data downtime ≈ **N × (TTD + TTR)**

where **N** = number of incidents, **TTD** = time-to-detection, **TTR** = time-to-resolution. Observability programs drive downtime down by reducing all three: fewer incidents (shift-left/contracts), faster detection (automated monitors vs. "an exec noticed the dashboard was wrong"), faster resolution (lineage-accelerated root cause).

### Data SLAs / SLOs / SLIs

Borrowed from SRE and applied to **data products**:

- **SLI** (indicator) — the actual measurement: e.g. % of days the table landed by 9 AM; null rate of `customer_email`; row-count vs. 7-day baseline.
- **SLO** (objective) — the internal target on an SLI: e.g. "freshness ≤ 6h for 99.5% of loads"; "null rate of key columns < 0.1%".
- **SLA** (agreement) — the *external, formal* commitment to stakeholders/consumers, often with consequences/escalation if breached. A data SLA bundles measurable targets for **freshness, availability, volume, and quality** of a data product.
- Common starting target: **99.9%** ("three nines") ≈ 43.8 min downtime/month; pick SLOs per data product's criticality, not one blanket number.

### Data Incident Management

Treating data issues with the rigor of software incidents. The lifecycle: **detection → triage/severity → ownership → resolution → retrospective**. Key practices: explicitly *declared* incidents (a human or system declares it, giving a clean basis for uptime/SLA math), severity levels tied to blast radius (use lineage), an on-call/owner model for data assets, blameless postmortems, and tracking **MTTD/MTTR** trends. Incident data is the empirical basis for SLAs — you can't promise reliability you don't measure.

### Anomaly Detection on Pipelines

Observability detection ranges from simple to ML-driven:

- **Rule/threshold monitors** — fixed bounds ("row count must be > 1M"). Cheap, explicit, but brittle on seasonal data: they false-alarm at peaks and miss off-peak drops.
- **Statistical / time-series monitors** — learn a baseline from history and flag deviations (z-score/IQR on a metric's history, moving averages, STL/Prophet-style seasonal decomposition). Handle daily/weekly seasonality, trend, and growth.
- **ML/automated monitors** — platform-trained models that auto-tune per table, adapt to growth/seasonality, and self-onboard new assets without one-by-one config. Teams report ~40–60% fewer false positives vs. static thresholds.
- Practical guidance: each metric/anomaly type may warrant a different method; reserve ML for high-cardinality, seasonal, or numerous assets and keep cheap thresholds for hard invariants (e.g. PK uniqueness). Watch timezone/DST shifts — they silently break seasonal models. (See **da-16-anomaly-detection** for the underlying algorithms; this skill covers their *application to pipeline/table health*.)

### Lineage & OpenLineage / Marquez

- **OpenLineage** is the open standard (LF AI & Data) for collecting lineage metadata, modeling **Run / Job / Dataset** entities with consistent naming; it instruments jobs *as they run* and supports **column-level** lineage (notably via the Spark integration, with facets for inputs/outputs).
- **Marquez** is the reference implementation/metadata server that collects, aggregates, and visualizes the lineage graph; it added column-level lineage and job-to-job lineage. Integrations exist for Airflow, dbt, Spark, etc.
- Column-level lineage enables fine-grained root cause and **sensitive-data tracking** (where does PII flow?), valuable for governance/compliance.

### Shift-Left & Data Contracts

The 2024–2026 evolution of the discipline: stop catching issues only *after* the warehouse load ("shift right") and move checks *earlier* — into dbt runs, CI/CD, and at the producer boundary.

- **Data contracts** formalize the producer↔consumer interface: schema, freshness SLA, volume expectations, semantic/quality thresholds, and versioning. They prevent incidents at the source rather than detecting them downstream, and bridge testing (pre-merge assertions) with observability (runtime monitoring).
- **Shift-left** emphasizes prevention and "design for trust from the start," pairing producer-side contracts with leadership-visible quality dashboards.

## Tools / Frameworks

| Tool | Type | Strength / niche |
| --- | --- | --- |
| **Monte Carlo** | Commercial platform | Coined the category; broad ML monitoring of all five pillars, end-to-end lineage, incident management; warehouse/lake/BI coverage |
| **Bigeye** | Commercial platform | Automation-first: auto-monitors every table/job, 70+ metrics, ML anomaly detection, cross-table/join-based rules; minimal per-monitor config |
| **Anomalo** | Commercial platform | Unsupervised ML deep-data checks (validates *values*, not just metadata); root-cause and segmentation; strong for AI/ML data |
| **Soda** (Soda Core OSS + Soda Cloud) | OSS scanner + cloud | Lightweight YAML checks (**SodaCL**), 25+ built-in metrics, SQL-defined custom checks, time-series monitoring & alerting; pragmatic CI-friendly scanning |
| **Great Expectations (GX)** | OSS library | Declarative **Expectations** (300+ in the gallery), Python/JSON, human-readable Data Docs; best for expressive assertion testing and validation |
| **Elementary** | dbt-native OSS + cloud | Installs as a dbt package; anomaly-detection tests (row count, null rate, avg, etc.), test-result history, self-hosted report; default starting point for dbt teams |
| **OpenLineage** | Open standard | Vendor-neutral lineage metadata spec (Run/Job/Dataset), column-level via Spark |
| **Marquez** | OSS metadata server | Reference OpenLineage implementation; lineage collection + visualization |

Selection heuristics: **dbt-centric stack →** Elementary (then Soda/GX for extra checks). **Need vendor-neutral lineage →** OpenLineage + Marquez. **Enterprise, many sources, want automated full-coverage ML monitoring + incident mgmt →** Monte Carlo / Bigeye / Anomalo. **Lightweight, CI-embedded checks in code →** Soda Core or Great Expectations.

## Methodology

1. **Inventory & prioritize assets.** You can't (and shouldn't) monitor everything equally. Rank tables/data products by downstream blast radius (use lineage) and business criticality. Define **tiers**.
2. **Establish lineage.** Stand up column/table lineage (OpenLineage+Marquez or a platform) so every later step has impact context.
3. **Baseline the five pillars.** Turn on freshness, volume, schema monitors broadly (cheap, high ROI); add distribution/quality monitors on key fields of high-tier assets.
4. **Set SLIs → SLOs → SLAs per tier.** Define indicators, internal objectives, and (for the top tier) external agreements with consumers.
5. **Choose detection per metric.** Thresholds for hard invariants; statistical/ML monitors for seasonal/high-cardinality metrics.
6. **Wire incident management.** Route alerts to owners, set severities by blast radius, declare incidents, track TTD/TTR.
7. **Shift left.** Add data contracts and CI/dbt checks at producer boundaries to cut incident count (N) at the source.
8. **Measure & iterate.** Track data downtime (N×(TTD+TTR)), false-positive rate, SLO attainment; retune monitors and prune noise.

## Practical Patterns

- **Lineage-first triage.** When a metric breaks, walk lineage *up* for root cause and *down* for blast radius before touching code.
- **Tier your coverage.** Broad cheap metadata monitors (freshness/volume/schema) everywhere; expensive value-level + ML monitors only on tier-1 assets.
- **Freshness SLO as the first win.** It's the most common, most visible incident and the cheapest to monitor — start here to build trust in the program.
- **Contract the producer boundary.** A schema/freshness contract on the most unstable upstream source prevents the largest class of incidents.
- **Declare incidents explicitly.** Gives clean SLA/uptime math and a paper trail for postmortems.
- **Co-locate observability with transformation.** dbt-native (Elementary) keeps monitors versioned alongside the models that produce the data.
- **Track the false-positive rate as a first-class metric.** Alert fatigue kills observability programs faster than missed incidents.

## Anti-Patterns

- **Treating observability as "more dbt tests."** Tests cover known-unknowns; observability must also surface unknown-unknowns via anomaly detection + lineage. Don't conflate the two.
- **Static thresholds on seasonal data.** Guarantees false alarms at peaks and misses during troughs; use seasonal/ML monitors for cyclical metrics.
- **Monitoring everything equally.** Untiered, full-coverage value-level monitors produce overwhelming noise and cost; nobody acts on the alerts.
- **No lineage.** Without lineage, every incident is a manual archaeology dig; triage time (and TTR) balloons.
- **Detection without resolution ownership.** Alerts with no owner, severity, or incident process just become a noisy dead-letter channel.
- **SLAs you don't measure.** Promising freshness/quality with no SLIs/incident tracking is theater.
- **Shift-right only.** Catching everything post-load means consumers see bad data first; push contracts/CI checks upstream.
- **Ignoring timezone/DST in seasonal models.** Silent drift in seasonal baselines → spurious anomalies.

## Troubleshooting

- **Flood of false-positive alerts** → metrics are seasonal/trending under static thresholds, or monitors lack enough history to baseline. Switch to seasonal/ML monitors, widen training windows, and add DST/timezone handling.
- **Incidents found by consumers, not monitors** → coverage gap. Add freshness/volume monitors on the affected lineage path; this is a TTD problem.
- **Long TTR** → missing/incomplete lineage. Stand up column-level lineage so root cause and blast radius are immediate.
- **Schema-drift breakage recurs from one source** → reactive monitoring only; add a producer-side **data contract** + CI check (shift-left).
- **"Is this a quality or an observability problem?"** → If you can write the assertion up front, it's a test (GX/dbt/Soda check). If you need to detect a deviation you didn't anticipate and trace its impact, it's observability.
- **OpenLineage events missing column lineage** → confirm the integration emitting them supports column facets (Spark integration is the most complete); not all integrations emit column-level yet.
- **Tool sprawl** → consolidate: dbt shops standardize on Elementary + one platform; vendor-neutral lineage standardizes on OpenLineage to avoid lock-in.

## References

- Monte Carlo — *What Is Data Observability? 5 Key Pillars* (montecarlo.ai, updated 2025/2026). https://montecarlo.ai/blog-what-is-data-observability/
- Barr Moses / Monte Carlo — *Introducing the 5 Pillars of Data Observability* (Medium / Towards Data Science, 2021; foundational). https://medium.com/data-science/introducing-the-five-pillars-of-data-observability-e73734b263d5
- TechTarget — *5 pillars of data observability bolster the data pipeline* (2024). https://www.techtarget.com/searchdatamanagement/tip/Pillars-of-data-observability-bolster-data-pipeline
- Monte Carlo — *12 Data Quality Metrics That Actually Matter* (data downtime, TTD/TTR) (2024). https://www.montecarlodata.com/blog-data-quality-metrics/
- dbt Labs — *What are data SLAs? Best practices for reliable pipelines* (2024). https://www.getdbt.com/blog/data-slas-best-practices
- Bigeye — *The complete guide to understanding data SLAs* (2024). https://www.bigeye.com/blog/the-complete-guide-to-understanding-data-slas
- SYNQ — *Why incidents must be the basis of data reliability SLAs* (2024). https://www.synq.io/blog/2024-03-incident-management
- SYNQ — *Data Observability Guide 2025*. https://www.synq.io/blog/data-observability-guide
- incident.io — *SLOs, SLAs, and SLIs: a complete guide* (2024/2025). https://incident.io/blog/slo-sla-sli
- Atlassian — *SLA vs SLO vs SLI* (2024). https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli
- OpenLineage — *Getting Started* + standard docs (2024/2025). https://openlineage.io/getting-started/
- OpenLineage — GitHub (open standard for lineage metadata). https://github.com/OpenLineage/OpenLineage
- Marquez Project — *Trying Out the New Column Lineage Feature* (2024). https://marquezproject.ai/blog/column-lineage-demo/
- Atlan — *Marquez (WeWork): Architecture, Features & Use Cases (2025)*. https://atlan.com/marquez-wework-open-source/
- Branch Boston — *Great Expectations vs Deequ vs Soda compared* (2024/2025). https://branchboston.com/great-expectations-vs-deequ-vs-soda-data-quality-testing-tools-compared/
- DataKitchen — *The 2026 Open-Source Data Quality and Data Observability Landscape*. https://datakitchen.io/blog/the-2026-open-source-data-quality-and-data-observability-landscape/
- Elementary — *How anomaly detection works* (docs, 2024/2025). https://docs.elementary-data.com/data-tests/how-anomaly-detection-works
- Elementary — GitHub (dbt-native observability). https://github.com/elementary-data/elementary
- Atlan — *Top 14 Data Observability Tools in 2026: Features & Pricing* (Bigeye, Anomalo, etc.). https://atlan.com/know/data-observability-tools/
- Conduktor — *Data Quality vs Data Observability: Key Differences* (2025). https://www.conduktor.io/glossary/data-quality-vs-data-observability-key-differences
- Metaplane — *Data quality vs data observability: how they differ but work together* (2024/2025). https://www.metaplane.dev/blog/data-quality-vs-data-observability
- Gable — *The Shift Left Data Manifesto* (data contracts) (2024/2025). https://www.gable.ai/blog/shift-left-data-manifesto
- Sifflet — *Data Observability: Five Years In, Why the Old Playbook Fails* (2025). https://www.siffletdata.com/blog/data-observability-five-years-in-why-the-old-playbook-doesnt-work-anymore
- VictoriaMetrics — *Anomaly Detection Handbook* (seasonality, thresholds, ML) (2024). https://victoriametrics.com/blog/victoriametrics-anomaly-detection-handbook-chapter-1/
- Promethium — *Data Observability Metrics That Matter in 2026: Core KPIs*. https://promethium.ai/guides/data-observability-metrics-that-matter-2026/
- Better Stack — *MTTR and other incident metrics explained* (2024). https://betterstack.com/community/guides/incident-management/mttr-and-other-incident-metrics/
