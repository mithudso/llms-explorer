---
title: "Postmortem Writing"
description: "A postmortem is a learning artifact disguised as an incident report. It must satisfy three audiences simultaneously: the engineers who need to understand what failed, the leadership who need to evalua"
---

# Postmortem Writing

## Overview

A postmortem is a learning artifact disguised as an incident report. It must satisfy three audiences simultaneously: the engineers who need to understand what failed, the leadership who need to evaluate organizational risk, and the people who lived through the incident.

## Core Concepts

### 1. Blameless framing in prose — the system, not the human

Three substitutions do most of the work:
- **Names → roles.** "Alice deployed the bad change" → "The release engineer deployed change #4821."
- **Judgments → actions.** "Bob failed to notice the alert" → "The on-call engineer did not see the alert because it was routed to a paused channel."
- **Causal verbs → enabling conditions.** "X caused Y" → "X created conditions under which Y became possible."

**The single most damaging phrase:** "should have." Replace it with "the system did not surface the information that would have enabled X."

### 2. Timeline reconstruction in UTC

- **UTC timestamps**, always.
- **Source for each event**: which dashboard, which log line, which Slack message.
- **Actor + action + observable result**, in that order.
- **Decision points called out explicitly**, with the information the decider had at the time.

| UTC time | Actor | Action | Observable / source |
|---|---|---|---|
| 14:30 | Deploy bot | Released change #4821 to prod | GitHub Actions log |
| 14:32 | Alerting | Fired `api-5xx-elevated` SEV2 | PagerDuty #4821 |
| 14:38 | On-call | Initiated rollback of change #4821 | GitHub Actions log |
| 14:46 | Rollback complete | Error rate returned to 0.2% | Datadog |

### 3. Contributing factors vs root cause

Real incidents have a root cause plus contributing factors. Structure the analysis as:
- **Triggering event** (the proximate change).
- **Root cause** (the latent defect the trigger exposed).
- **Contributing factors**, categorized:
  - Technical (missing monitoring, single points of failure)
  - Process (insufficient testing, communication gaps)
  - Environmental (time pressure, on-call fatigue)

### 4. Five Whys discipline

Apply iteratively: "Why did the API return 503s? Because the database connection pool was exhausted." Continue until you reach an organizational or design-level factor.

Allow branching. A single chain of whys is rare. Multiple parallel chains converging on multiple contributing factors is common.

### 5. Action items with owners, dates, severity, and traceability

A defensible action item has:
- **Owner**: a single named person (not a team).
- **Due date**: a real calendar date.
- **Severity / priority**: P0/P1/P2 calibrated to actual risk reduction.
- **Traceability**: which contributing factor it addresses.
- **Definition of done**: how the writer will know the action is complete.

### 6. "What went well" without performative positivity

Three sub-sections:
- **What worked**: the alert fired correctly, the rollback procedure was executable.
- **What we got lucky on**: things that worked but only by accident.
- **What we want to preserve**: practices that should be formalized.

### 7. Hindsight bias — naming it and writing around it

Linguistic markers of hindsight bias to delete in revision:
- "Clearly..." (it was not clear at the time).
- "Obviously..." (it was not obvious to anyone in the moment).
- "Should have noticed..." (replace with "the available signals did not surface X").

### 8. The hourglass structure for postmortems

1. **The top (inverted pyramid summary, 4–6 paragraphs).** The verdict first: what broke, when, who was affected, severity, root cause class.
2. **The turn (one sentence).** "Here is how the incident unfolded, in chronological order."
3. **The bottom (chronological narrative).** The timeline.

## Full postmortem skeleton

```markdown
# Postmortem: <one-line description>

| Incident ID | INC-0421 |
| Severity | SEV1 |
| Date | 2026-05-22 |
| Duration | 14:32 – 14:46 UTC (14 min) |
| Authors | @mitch.hudson |

## Executive summary (read this first — 60 seconds)
A change deployed at 14:30 UTC introduced a query pattern that saturated
the API connection pool. From 14:32 to 14:46 UTC, approximately 14% of API
requests in us-east-1 returned 503 errors. Five action items have been opened, two are P0.

## Customer impact
## Timeline (UTC)
## What happened — narrative
## Root cause and contributing factors
## What went well
## Action items

| ID | Description | Owner | Due | Priority | Addresses |
|---|---|---|---|---|---|
```

## Blameless rewrite cheat sheet

| Before (blamey) | After (blameless) |
| --- | --- |
| Alice deployed a bad change | Change #4821 was deployed at 14:30 UTC |
| Bob failed to notice the alert | The pool-saturation alert did not exist; only the lagging 5xx alert fired |
| The team should have caught this in review | The review checklist did not include load-test sign-off |

## Anti-Patterns

- **Single-root-cause syndrome**: "the root cause was X" with no contributing factors.
- **Wishlist action items**: "we should also rewrite the deployment system."
- **Hindsight prose**: "obviously the team should have noticed..."
- **The publish-and-forget**: no review date, no owner for action items.

## References

- [Google SRE Book — Chapter 15: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)
- [Etsy — Debriefing Facilitation Guide (Allspaw, Evans, Schauenberg)](https://extfiles.etsy.com/DebriefingFacilitationGuide.pdf)
- [Atlassian — Postmortems: Enhance Incident Management Processes](https://www.atlassian.com/incident-management/handbook/postmortems)
