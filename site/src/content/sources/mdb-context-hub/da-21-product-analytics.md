---
title: "Product Analytics"
description: "The analytical discipline of measuring what users do inside a product, why, and whether it creates value — then feeding that back into product decisions. Distinct from generic web analytics (page-leve"
---

# Product Analytics

The analytical discipline of measuring **what users do inside a product, why, and whether it creates value** — then feeding that back into product decisions. Distinct from generic web analytics (page-level) and from instrumentation (the plumbing). Product analytics is event-centric, user-centric, and decision-oriented.

This skill covers the *analysis layer*. Leave to adjacent skills:
- **Cohort/retention curves, N-day/unbounded retention, retention math** → `da-34-cohort-retention-analytics`
- **SDK wiring, autocapture vs manual, identity stitching plumbing** → `da-3-2-7-web-app-analytics-instrumentation`
- **Experiment statistics, p-values, CUPED, sequential testing theory** → `da-12-ab-testing-causal-inference`

## Overview

A product-analytics practice answers four recurring questions: (1) Are users reaching value (activation)? (2) Do they keep coming back and going deeper (engagement/adoption)? (3) Where do they drop off (funnels/paths)? (4) Is the whole thing growing toward a single meaningful outcome (North Star)? The analytical quality of every answer is capped by the quality of the **event taxonomy** underneath it — so taxonomy and governance come first, not last.

## Core Concepts

### 1. Event taxonomy & tracking plans
A taxonomy is the hierarchical naming + classification scheme for events and properties so a platform can produce comparable insights. Design it deliberately before instrumenting.
- **Object-Action naming**: pick objects (`Song`), define actions (`Played`, `Paused`), agree a tense (past tense recommended), produce `Song Played`. Alternatively `verb_noun` snake_case (`checkout_completed`). Pick one and enforce it. ([Amplitude event taxonomy](https://amplitude.com/explore/data/event-taxonomy), 2024; [Avo naming conventions](https://www.avo.app/docs/data-design/best-practices/naming-conventions), 2025; [Heap naming conventions](https://www.heap.io/blog/naming-conventions-and-their-place-in-analytics), 2024)
- **Parameterize, don't proliferate**: one `Add to Cart` event with a `campaign` property — never `Add to Cart Summer Sale` as a separate event. ([Amplitude data planning playbook](https://amplitude.com/docs/data/data-planning-playbook), 2025)
- **Tracking plan** = the central contract: every event, its properties, data types, owner, trigger, and examples. The spreadsheet is the legacy form; dedicated tools (Avo) version-control it. ([Amplitude tracking practices](https://amplitude.com/blog/analytics-tracking-practices), 2024)
- **Goldilocks granularity**: too few events = blind spots; too many = noise and maintenance debt. Track events that map to decisions.

### 2. North Star metric (NSM) framework
A single metric that best captures the value customers get, that product/marketing can influence, and that leads revenue.
- The NSM is an **output/outcome** — you should *not* be able to move it directly. You move it through **3–5 inputs** that teams influence day-to-day. ([Amplitude North Star Playbook](https://amplitude.com/books/north-star/about-north-star-framework), 2024)
- A **metric tree** decomposes NSM → inputs → initiatives, so every team sees how their work ladders up. ([Amplitude NSM & inputs](https://amplitude.com/books/north-star/amplitudes-north-star-metric-and-inputs), 2024)
- Good NSM = leading indicator of value (e.g. "weekly active collaborators"), not a vanity output (e.g. raw signups or revenue itself). ([Amplitude good vs bad NSM](https://amplitude.com/blog/good-bad-north-star-metric), 2024)

### 3. Funnel & conversion analysis
Map an ordered multi-step flow, measure step-to-step conversion, diagnose the biggest drops.
- Three parts: **define** the ordered steps → **measure** conversion between steps → **diagnose** the leakiest step (session replay, segmentation, qual). ([Statsig funnel analysis](https://www.statsig.com/perspectives/funnel-analysis-product-analytics), 2025; [UXCam conversion funnel guide](https://uxcam.com/blog/conversion-funnel-analysis/), 2026)
- Keep funnels to **4–7 ordered steps**; longer funnels hide where the real loss is. ([Count funnel conversion](https://count.co/metric/funnel-conversion-analysis), 2025)
- Choose a **conversion window** deliberately (e.g. 7-day signup→activation). The window changes the number — state it.
- **Segment the funnel** (source, device, plan, cohort) — an aggregate funnel almost always masks a segment-specific cliff. ([Userpilot conversion funnel](https://userpilot.com/blog/conversion-funnel-analysis/), 2025)

### 4. Activation & the "aha moment"
Activation = the set of early actions that **correlate with later retention**. The "aha moment" is when the user internalizes core value; the activation metric is its measurable proxy.
- Find it empirically: test event *groups* and *frequencies* (e.g. "watched ≥5 replays" beat "watched 1"). PostHog's activation metric was "set a replay filter ≥1 and watched ≥5 replays" because it maximized retention. ([PostHog activation metrics](https://posthog.com/product-engineers/activation-metrics), 2024)
- The **magic number** is a frequency threshold within a time window (Facebook's "7 friends in 10 days" archetype). Validate with odds-ratio/correlation against retention, not eyeballing. ([Amplitude aha moment](https://amplitude.com/blog/aha-moment), 2024; [Statsig spot aha moment](https://www.statsig.com/perspectives/spot-product-aha-moment-analytics), 2024)
- Correlation ≠ cause: a high-retention behavior may be a *symptom* of an already-engaged user. Treat the activation metric as a hypothesis to test via experiment, not a law.

### 5. Feature adoption (breadth / depth / time / duration)
- **Adoption rate** = users who used the feature ÷ active users × 100. ~24–28% is a healthy core-feature band. ([Userpilot feature adoption metrics](https://userpilot.com/blog/feature-adoption-metrics/), 2025; [Artisan benchmarks](https://www.artisangrowthstrategies.com/blog/feature-adoption-metrics-top-benchmarks-2025), 2025)
- **Breadth** = how many users reach it (reach). **Depth** = how intensively they use it once there (value delivery). Low depth = value problem, not discovery problem.
- **Time to adopt** = speed to value after first exposure; adoption typically builds over **30–90 days** — don't kill a feature on week-one numbers. **Duration** = whether usage persisted into a habit. ([Plane measuring feature adoption](https://plane.so/blog/measuring-feature-adoption-and-usage-metrics-funnels-and-examples), 2025; [Appcues adoption metrics](https://www.appcues.com/blog/success-with-product-adoption-metrics), 2024)

### 6. Engagement & stickiness (DAU/WAU/MAU)
- DAU/WAU/MAU = unique users in 1/7/30-day windows. **Stickiness = DAU/MAU** (≈ days used per month / 30). ([Gainsight DAU/MAU](https://www.gainsight.com/essential-guide/product-management-metrics/dau-mau/), 2024)
- Benchmarks are **product-shape dependent**: social/messaging 50–80%, productivity 40–60%, fintech/e-commerce 10–30%. Don't compare across categories. ([Mixpanel MAU benchmarks](https://mixpanel.com/blog/mau/), 2026; [Statsig DAU/MAU](https://www.statsig.com/perspectives/understanding-daumau-key-metrics-for-product-success), 2025)
- Use **WAU/MAU** for async products (content, newsletters, docs) where daily use isn't the natural cadence. ([Userpilot DAU/WAU/MAU](https://userpilot.com/blog/dau-wau-mau/), 2025)

### 7. Session & path analysis
- **Session** = a visit; ends after an inactivity timeout (commonly 30 min on web). **Session duration** is a depth metric that complements frequency metrics. ([Amplitude session duration](https://amplitude.com/glossary/terms/session-duration), 2024)
- Direction of "good" is **context-dependent**: long sessions = engagement for content; long sessions = friction for transactional/banking apps. GA4 now favors *engaged time per session* over raw duration (handles background tabs). ([GA4BigQuery sessions deep dive](https://ga4bigqueryblog.com/2025/08/25/understanding-sessions-in-google-analytics-4-ga4-a-deep-dive/), 2025; [PostHog session metrics](https://posthog.com/tutorials/session-metrics), 2024)
- **Path analysis** = aggregated flows of the actual sequences users take (not a predefined funnel). Use it for *discovery* ("what do users do before converting / before churning?"), then formalize findings into funnels. Amplitude folds Pathfinder into **Journeys**, which adds drop-off and per-user paths that raw path charts lack. ([Amplitude Journeys](https://amplitude.com/docs/analytics/charts/journeys/journeys-understand-paths), 2025)

### 8. Metric frameworks: AARRR vs HEART
- **AARRR (Pirate Metrics)** — Acquisition, Activation, Retention, Revenue, Referral. Lifecycle/growth lens: *"is the business growing?"* ([Amplitude pirate metrics](https://amplitude.com/blog/pirate-metrics-framework), 2024; [PostHog AARRR funnel](https://posthog.com/product-engineers/aarrr-pirate-funnel), 2024)
- **HEART (Google, 2010)** — Happiness, Engagement, Adoption, Retention, Task success. UX-quality lens: *"is the experience good?"* Each dimension pairs with Goals-Signals-Metrics. ([Productcompass analytics playbook](https://www.productcompass.pm/p/the-product-analytics-playbook-aarrr), 2025; [Ideaplan HEART vs AARRR](https://www.ideaplan.io/compare/heart-vs-aarrr), 2025)
- Pick by question: AARRR for growth orgs/PLG; HEART for UX-led orgs. NSM sits above both as the single rallying output. ([Hyperact product metrics frameworks](https://www.hyperact.co.uk/blog/product-metrics-frameworks), 2025)

### 9. Experimentation operations (the ops layer, not the stats)
- Running product experiments at scale needs *operational* glue: feature flags ↔ analytics ↔ experiment readouts sharing one event pipeline so metrics auto-populate. Modular stacks (separate flag/analytics/experiment products) add setup friction. ([PostHog vs Statsig](https://posthog.com/blog/posthog-vs-statsig), 2025; [Statsig vs PostHog](https://www.statsig.com/vs/posthog), 2025)
- Operational essentials: pre-registered primary metric tied to the tracking plan, automated power/sample-size estimation, guardrail metrics, and a defined readout cadence. (Statistical validity itself → `da-12-ab-testing-causal-inference`.) ([ProductQuant PostHog experiments](https://productquant.dev/blog/setup-posthog-ab-experiments/), 2025)

### 10. Governance & data quality
- Bad data silently corrupts every metric above. Govern with: a versioned tracking plan, schema validation **before** events hit production, and ongoing **observability** comparing live events vs the plan to catch schema drift. ([Avo data observability](https://www.avo.app/data-observability), 2025)
- Assign **owners** per event/property; route changes through review (branch reviews, Slack notifications). ([Avo actionable ownership](https://www.avo.app/blog/introducing-actionable-data-ownership), 2025)
- Schedule **quarterly taxonomy reviews** with PM + analytics + marketing to retire dead events and absorb new needs. ([Amplitude tracking practices](https://amplitude.com/blog/analytics-tracking-practices), 2024)

## Tools / Frameworks

| Tool | Strength | Notes (2025–26) |
|---|---|---|
| **Amplitude** | Behavioral cohorts, governance, metric trees, Journeys | Best for analysis depth + cross-functional scale; MTU pricing. ([Amplitude best tools](https://amplitude.com/compare/best-product-analytics-tools), 2026) |
| **Mixpanel** | Fast event analytics, clean funnels/reports | Relaunched experimentation + added flags/replay late 2025; event-based pricing. ([Cotera comparison](https://cotera.co/articles/product-analytics-platform-comparison), 2026) |
| **PostHog** | All-in-one for dev-led teams (analytics + flags + experiments + replay + warehouse) | Modular, open-source, self-host option. ([PostHog alternatives](https://posthog.com/blog/posthog-alternatives), 2025) |
| **Heap** | Autocapture — records everything, define events retroactively | Fast start, less upfront taxonomy discipline. ([PostHog Heap alternatives](https://posthog.com/blog/best-heap-alternatives), 2025) |
| **June** | Pre-built SaaS company-level reports on top of Segment | Lightweight, B2B-oriented; thinner than the majors for deep analysis. |
| **Avo** | Tracking-plan governance + Inspector observability | Sits *upstream* of the analytics tool to guarantee data quality. ([Avo](https://www.avo.app/), 2025) |
| **Statsig** | Experimentation-first unified pipeline | Strong ops/experiment scale; CUPED/sequential built in. ([Statsig vs PostHog](https://www.statsig.com/vs/posthog), 2025) |

**Frameworks summary:** Taxonomy (Object-Action) → NSM + inputs (metric tree) → lifecycle lens (AARRR) or UX lens (HEART) → activation/aha → adoption (breadth/depth/time) → funnels & paths → governance loop.

## Methodology (end-to-end)

1. **Frame the decision** — what product question are we answering? (Don't start from "what can we track?")
2. **Define the taxonomy** — Object-Action events + properties, owners, in a versioned tracking plan.
3. **Pick the NSM + 3–5 inputs**; draw the metric tree.
4. **Instrument & validate** (hand to instrumentation/governance) — verify live events match the plan.
5. **Establish activation** — find the aha-moment metric empirically; validate against retention.
6. **Build core funnels** (4–7 steps, stated window) and run **path analysis** to discover real journeys.
7. **Measure adoption & engagement** — adoption rate, breadth/depth, DAU-WAU-MAU/stickiness, segmented.
8. **Experiment** to move inputs; read out against pre-registered metrics.
9. **Review quarterly** — prune the taxonomy, re-validate the NSM, refresh benchmarks.

## Practical Patterns

- **Segment before you conclude.** Every aggregate metric (funnel, stickiness, adoption) hides a segment story. Break by source, plan, platform, cohort.
- **Tie each metric to a decision.** If no decision changes based on a metric, stop tracking it.
- **Activation metric = retention's leading indicator.** Optimize activation to move retention upstream of churn.
- **Discover with paths, confirm with funnels.** Paths surface the unknown; funnels measure the known.
- **State your windows.** Conversion window, active-user window, adoption window — all change the number.
- **NSM is an output you steer via inputs**, never a dial you turn directly.

## Anti-Patterns

- **Vanity NSM.** Picking raw revenue or total signups as the North Star — not a leading value indicator. ([Amplitude good vs bad NSM](https://amplitude.com/blog/good-bad-north-star-metric), 2024)
- **Event sprawl / inconsistent names.** `Song Played` vs `Song_Played` from different teams destroys comparability. Parameterize and govern. ([Heap naming](https://www.heap.io/blog/naming-conventions-and-their-place-in-analytics), 2024)
- **Funnel theater.** Reporting drop-off % without diagnosing *why* the leak happens.
- **Cross-category benchmark abuse.** Comparing a fintech app's 22% DAU/MAU to a social app's 60% as if underperforming.
- **Killing features on week-one adoption** before the 30–90 day adoption curve plays out.
- **Treating session duration as universally "more is better."** Wrong for transactional products.
- **Correlation-as-causation on the aha moment.** Shipping a forced onboarding step because a behavior correlated with retention, without an experiment.

## Troubleshooting

- **Numbers differ between two tools/dashboards** → almost always different windows, dedup logic, or event definitions. Reconcile against the tracking plan first.
- **Stickiness dropped overnight** → check for a taxonomy/SDK change (broken event) before concluding behavior changed; use observability (Avo Inspector) to spot schema drift. ([Avo data observability](https://www.avo.app/data-observability), 2025)
- **Funnel conversion looks impossibly high/low** → check the conversion window and whether steps are strictly ordered vs "any order".
- **NSM flat while inputs move** → inputs may be mis-chosen (don't actually drive the output) — re-derive the metric tree.
- **Feature "failing"** → separate breadth from depth: low reach is a discovery/onboarding fix; low depth is a value/UX fix.
- **Path analysis is unreadable** → too many distinct events; collapse to a smaller event set or anchor on a start/end event.

## References

- Amplitude — Event taxonomy (https://amplitude.com/explore/data/event-taxonomy), 2024
- Amplitude — Data planning playbook (https://amplitude.com/docs/data/data-planning-playbook), 2025
- Amplitude — Analytics tracking practices (https://amplitude.com/blog/analytics-tracking-practices), 2024
- Avo — Naming conventions (https://www.avo.app/docs/data-design/best-practices/naming-conventions), 2025
- Heap — Naming conventions (https://www.heap.io/blog/naming-conventions-and-their-place-in-analytics), 2024
- Amplitude — North Star framework (https://amplitude.com/books/north-star/about-north-star-framework), 2024
- Amplitude — NSM & inputs (https://amplitude.com/books/north-star/amplitudes-north-star-metric-and-inputs), 2024
- Amplitude — Good vs bad NSM (https://amplitude.com/blog/good-bad-north-star-metric), 2024
- Statsig — Funnel analysis in product analytics (https://www.statsig.com/perspectives/funnel-analysis-product-analytics), 2025
- UXCam — Conversion funnel analysis guide (https://uxcam.com/blog/conversion-funnel-analysis/), 2026
- Count — Funnel conversion analysis (https://count.co/metric/funnel-conversion-analysis), 2025
- Userpilot — Conversion funnel analysis (https://userpilot.com/blog/conversion-funnel-analysis/), 2025
- PostHog — How we found our activation metric (https://posthog.com/product-engineers/activation-metrics), 2024
- Amplitude — The aha moment (https://amplitude.com/blog/aha-moment), 2024
- Statsig — Spot your product's aha moment (https://www.statsig.com/perspectives/spot-product-aha-moment-analytics), 2024
- Userpilot — Feature adoption metrics (https://userpilot.com/blog/feature-adoption-metrics/), 2025
- Artisan — Feature adoption benchmarks 2025 (https://www.artisangrowthstrategies.com/blog/feature-adoption-metrics-top-benchmarks-2025), 2025
- Plane — Measuring feature adoption (https://plane.so/blog/measuring-feature-adoption-and-usage-metrics-funnels-and-examples), 2025
- Appcues — Product adoption metrics (https://www.appcues.com/blog/success-with-product-adoption-metrics), 2024
- Gainsight — DAU/MAU guide (https://www.gainsight.com/essential-guide/product-management-metrics/dau-mau/), 2024
- Mixpanel — MAU definition & 2026 benchmarks (https://mixpanel.com/blog/mau/), 2026
- Statsig — Understanding DAU/MAU (https://www.statsig.com/perspectives/understanding-daumau-key-metrics-for-product-success), 2025
- Userpilot — DAU/WAU/MAU explained (https://userpilot.com/blog/dau-wau-mau/), 2025
- Amplitude — Session duration glossary (https://amplitude.com/glossary/terms/session-duration), 2024
- GA4BigQuery — Understanding sessions in GA4 (https://ga4bigqueryblog.com/2025/08/25/understanding-sessions-in-google-analytics-4-ga4-a-deep-dive/), 2025
- PostHog — Session metrics tutorial (https://posthog.com/tutorials/session-metrics), 2024
- Amplitude — Journeys / paths (https://amplitude.com/docs/analytics/charts/journeys/journeys-understand-paths), 2025
- Amplitude — Pirate metrics (AARRR) (https://amplitude.com/blog/pirate-metrics-framework), 2024
- PostHog — AARRR pirate funnel (https://posthog.com/product-engineers/aarrr-pirate-funnel), 2024
- Productcompass — Product analytics playbook (https://www.productcompass.pm/p/the-product-analytics-playbook-aarrr), 2025
- Ideaplan — HEART vs AARRR (https://www.ideaplan.io/compare/heart-vs-aarrr), 2025
- Hyperact — Product metrics frameworks (https://www.hyperact.co.uk/blog/product-metrics-frameworks), 2025
- PostHog — PostHog vs Statsig (https://posthog.com/blog/posthog-vs-statsig), 2025
- Statsig — Statsig vs PostHog (https://www.statsig.com/vs/posthog), 2025
- ProductQuant — PostHog A/B experiments setup (https://productquant.dev/blog/setup-posthog-ab-experiments/), 2025
- Avo — Data observability (https://www.avo.app/data-observability), 2025
- Avo — Actionable data ownership (https://www.avo.app/blog/introducing-actionable-data-ownership), 2025
- Amplitude — Best product analytics tools 2026 (https://amplitude.com/compare/best-product-analytics-tools), 2026
- Cotera — Product analytics platform comparison (https://cotera.co/articles/product-analytics-platform-comparison), 2026
- PostHog — Best Heap alternatives (https://posthog.com/blog/best-heap-alternatives), 2025
- PostHog — PostHog alternatives (https://posthog.com/blog/posthog-alternatives), 2025
