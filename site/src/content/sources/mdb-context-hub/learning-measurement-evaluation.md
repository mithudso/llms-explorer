---
title: "Learning Measurement & Training Evaluation"
description: "Reference for measuring training and enablement program effectiveness across the full evaluation stack — from post-workshop smile sheets to executive ROI reports and cross-system xAPI analytics."
---

# Learning Measurement & Training Evaluation

Reference for measuring training and enablement program effectiveness across the full evaluation stack — from post-workshop smile sheets to executive ROI reports and cross-system xAPI analytics.

See `references/learning-measurement-context.md` for the full deep-reference with worked examples, decision tables, and vendor comparisons.

## Evaluation Framework Overview

Three frameworks dominate training program evaluation. They are complementary, not competing:

| Framework | Primary Question | Output |
|---|---|---|
| Kirkpatrick Four Levels | Did participants react, learn, change behavior, get results? | Evidence at each level |
| New World Kirkpatrick | Were the right conditions built in from the start? | Required Drivers + leading indicators |
| Phillips ROI (Level 5) | Did the financial benefits exceed the fully-loaded cost? | ROI % and BCR |

**When to use each:** Kirkpatrick levels 1–4 apply to any formal training; New World Kirkpatrick adds the pre-design planning discipline; Phillips Level 5 is appropriate for 5–10% of programs — those that are high-cost, strategically critical, and directly tied to measurable business KPIs.

## Kirkpatrick's Four Levels

### Level 1: Reaction
Measures whether participants found training favorable, engaging, and relevant. Relevance is the most predictive sub-component.

**Limitation:** A 2009 study (n=335) found no statistically significant correlation between Level 1 scores and Level 3 behavior change. Alliger & Janak (1989) found the Level 1→Level 2 causal link produced only r=.23.

### Level 2: Learning
Measures acquisition of knowledge, skills, attitude, confidence, and commitment (5 components per the New World Model).

### Level 3: Behavior
Measures whether participants apply what they learned on the job. Most organizations skip formal Level 3 evaluation — Kennedy et al. (2013) found 40%+ report it is not required by management.

### Level 4: Results
Measures whether targeted organizational outcomes occurred. Requires pre-established KPI baselines and isolation methodology.

## The New World Kirkpatrick Model

### Shared Accountability Model
L1/L2 = L&D accountability; L3/L4 = shared accountability between L&D, managers, and the business.

### Required Drivers (Level 3 Addition)
Post-training reinforcement systems management must provide: coaching, job aids, work review, recognition. [TENTATIVE: ~85% vs ~15% application figures are from Kirkpatrick-affiliated sources — treat as directional.]

### Leading Indicators (Level 4 Bridge)
Short-term observations signaling whether critical behaviors are on track to produce results.

### Backward Design Mandate
Plan evaluation in reverse: L4 KPI → L3 behaviors → L2 objectives → L1 design.

## Phillips ROI Methodology (Level 5)

```
BCR  = Program Benefits / Program Costs
ROI% = [(Benefits − Costs) / Costs] × 100
```

Isolation methods (descending reliability): control group → trend-line → forecasting model → manager estimates → participant estimates.

Apply to ~5–10% of programs: high-cost, strategically critical, tied to measurable KPI, with a viable isolation method.

## xAPI, SCORM, and cmi5

| Standard | Requires LMS | Mobile | Offline | Custom Data |
|---|---|---|---|---|
| SCORM 1.2/2004 | Yes | No | No | No |
| xAPI | No | Yes | Yes | Yes |
| cmi5 | Yes | Yes | Yes | Yes |

xAPI adoption ~17% (verified-as-of: 2026-06-16) despite 10+ years. SCORM still dominant at 81.7%.

## Training Transfer

Baldwin & Ford (1988): transfer depends on trainee characteristics, training design, and work environment. Supervisor support is the single strongest driver (ρ=.51, *Human Factors* 2019).

LTSI (Holton, Bates & Ruona, 2000): 16-factor validated instrument for diagnosing transfer barriers.

## L&D Dashboard Design

Three audiences: Executive (ROI, time-to-proficiency), Manager (behavior change, team completion), L&D ops (engagement analytics).

Top metrics: time-to-productivity, 30/60/90-day retention, manager reinforcement score, application rate, completion rate (process only — not performance).

## Evaluation Edge Cases

- **Skip evaluation** for cohorts under ~20 or one-time deliveries where overhead exceeds value.
- **Retrospective evaluation**: use trend-line data, untrained comparison cohort, or SME estimates with documented confidence reduction.
- **ROI report structure**: Executive summary → Methodology → Financial detail → Intangibles → Sensitivity analysis.
- **xAPI/LRS privacy**: anonymize actor IDs for PII; GDPR applies in EU; FERPA applies to educational institutions.

## Quick Reference Decision Guide

```
High-cost / strategic program?
├── Yes → Levels 1–4; Level 5 if isolation feasible; plan backward
└── No  → Levels 1–2; add L3 if behavior change is the goal

Can you isolate the effect?
├── Control group → Level 5 ROI defensible
├── Trend-line    → Level 5 plausible with caveats
├── Estimates     → Level 4 + conservative estimate
└── No            → Level 4 direction + intangibles only

xAPI ambitions?
├── Native xAPI authoring → cmi5 if LMS supports it, else SCORM
├── Mobile/offline/cross-platform → xAPI + LRS; plan data governance
├── Simple completion+score → SCORM 1.2
└── Government/regulated → xAPI (IEEE/ISO status matters for RFPs)
```
