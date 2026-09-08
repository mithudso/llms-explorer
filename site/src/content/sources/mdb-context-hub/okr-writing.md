---
title: "OKR Writing"
description: "OKRs (Objectives and Key Results) are a goal-setting framework. The form is deceptively simple — one inspirational Objective, three to five measurable Key Results — but most OKRs in the wild are broke"
---

# OKR Writing

## Overview

OKRs (Objectives and Key Results) are a goal-setting framework. The form is deceptively simple — one inspirational Objective, three to five measurable Key Results — but most OKRs in the wild are broken. They are project plans wearing OKR clothing.

Three disciplines:
1. The Objective is **qualitative, inspirational, time-bound**.
2. Each Key Result is **measurable** — a numerator over a denominator, by a date.
3. The KR measures an **outcome** (value delivered), not an **output** (work done) and never an **input** (effort spent).

## Core Concepts

### 1. The OKR equation: "I will [Objective] as measured by [Key Results]"

### 2. The measurable-KR test: numerator, denominator, deadline

Every KR must answer:
- **Numerator** — what is being counted?
- **Denominator** — relative to what?
- **Deadline** — by when?

- **Fails:** "Improve onboarding." (no numerator, no denominator, no deadline)
- **Fails:** "Reach 1000 users." (no denominator, no deadline)
- **Passes:** "Grow week-1 activation rate from 28% to 45% by 2026-09-30."

### 3. OKR vs KPI — different jobs

- **KPI** (Key Performance Indicator) — a steady-state health metric you watch *all the time*. KPIs run forever.
- **OKR** — a change goal for a *bounded period*. Says "we are choosing to push this number from X to Y this quarter."

**A KPI can become a KR** if you decide to push it — but the KR must specify the from-to delta and the deadline.

### 4. Input → Output → Outcome hierarchy

- **Input** — effort, headcount, money spent. ("hired 5 engineers") — never a KR.
- **Output** — work produced, artifacts shipped. ("shipped the new dashboard") — almost never a KR.
- **Outcome** — change in the world, value delivered. ("dashboard adoption reached 60% of paying teams") — this is what KRs measure.

Felipe Castro's "so what?" test: read the KR and ask "so what?" If the answer is another metric (the outcome), the original was an output.

### 5. Ambitious-but-not-impossible: the 70% rule

For **aspirational / stretch** OKRs:
- Pick a target where your confidence of hitting 100% is about **5 out of 10** (50/50 at draft time).
- Score around **0.7** on average at the end of the quarter is healthy.
- Consistently scoring 1.0 means you sandbagged. Scoring < 0.4 means you set fantasy targets.

For **committed** OKRs (operational must-haves — SLAs, compliance deadlines), the target is 1.0 and anything less is a problem.

### 6. The rollup pattern across org levels

- Company sets 3–5 Objectives for the quarter.
- Each team picks ~3 Objectives that contribute to the company set.
- An individual contributor may have 1–2 personal Objectives that map to a team Objective.

**Key insight:** roughly half of OKRs should be set bottom-up. Pure top-down OKRs kill engagement.

### 7. Mid-quarter check-in: traffic-light language

- **Green** — on track, no help needed.
- **Yellow** — at risk, here is what would unblock me.
- **Red** — will not hit current target. Either re-plan or formally revise the KR.

### 8. End-of-cycle scoring (0.0 to 1.0)

For each KR, compute the actual / target on its native scale:

- Started at 28%, target 45%, ended at 38%. Progress = (38 − 28) / (45 − 28) = 10/17 ≈ **0.59**.

### 9. Common bad-OKR patterns

- **"Ship feature X by date Y"** — that is a task, not a KR. The KR is the *outcome* the feature is supposed to produce.
- **"Do our normal job well"** — operational baselines are KPIs, not OKRs.
- **Activity counts** — "publish 12 blog posts" measures effort, not outcome.
- **Sandbagged targets** — KRs you are 95% confident in.
- **Too many KRs** — more than 5 per Objective is a wishlist.
- **Set-and-forget** — OKRs scored only at quarter end.

## Templates

### Template — Single OKR

```markdown
## Objective
[Qualitative, inspirational, time-bound. One sentence. Why this matters.]

## Type
[ ] Committed (target = 1.0)
[ ] Aspirational / stretch (expected score ≈ 0.7)

## Key Results
1. [Move metric X from A to B by DATE]
2. [Move metric Y from A to B by DATE]
3. [Move metric Z from A to B by DATE]

## How we'll know we got it wrong
[One sentence — the leading indicator that says "stop, replan".]
```

### Example — Bad → Good rewrites

| Bad | Why bad | Good |
|---|---|---|
| "Launch the new dashboard." | Output, not outcome; no metric, no deadline. | "Reach 60% weekly active usage of the new dashboard among paying teams by 2026-09-30." |
| "Improve customer happiness." | No numerator/denominator/deadline. | "Lift CSAT among top-50 enterprise accounts from 7.4 to 8.5 by 2026-09-30." |
| "Hire 10 engineers." | Input, not outcome. | "Reduce p95 API latency from 350ms to <200ms by 2026-09-30." |

## References

- John Doerr, [whatmatters.com](https://www.whatmatters.com/faqs/okr-meaning-definition-example)
- Christina Wodtke, [The Art of the OKR](https://cwodtke.com/the-art-of-the-okr/)
- Felipe Castro, "An OKR should measure the outcome, not the work"
