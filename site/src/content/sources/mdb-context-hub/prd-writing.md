---
title: "PRD Writing"
description: "A Product Requirements Document (PRD) is a PM-owned artifact that defines what a product team will build and why, before engineering proposes how. PRDs sit upstream of RFCs, design docs, and implement"
---

# PRD Writing

## Overview

A Product Requirements Document (PRD) is a PM-owned artifact that defines **what** a product team will build and **why**, before engineering proposes **how**. PRDs sit upstream of RFCs, design docs, and implementation specs.

A PRD captures **validated decisions**. It does not perform validation. Validation happens through customer interviews, prototypes, user testing, and data analysis — the PRD records the conclusions.

## Core Concepts

### 1. Problem-first structure (Lenny's hierarchy)

A modern PRD opens with the problem, not the solution. Sections proceed in this order:

1. **Problem** — what user/business pain are we solving, with evidence
2. **Users** — who is affected, segment size, current workarounds
3. **Goals** — desired outcomes and what success looks like
4. **Proposed solution** — at a high level (often a prototype link)
5. **Success metrics** — measurable definition of done
6. **Open questions / risks** — what's unresolved
7. **Non-goals** — what we are explicitly NOT doing
8. **Rollout / milestones** — MVP → v1 → roadmap

### 2. The Cagan four-section minimum

Marty Cagan's classic PRD structure: **Purpose**, **Features**, **Release Criteria**, **Rough Timing**.

### 3. MVP vs v1 vs roadmap scoping discipline

- **MVP** — minimum viable: smallest scope that lets us learn whether the proposed solution works.
- **v1 (GA)** — broadly shippable: meets release criteria, addresses the core user need.
- **Roadmap (vNext)** — follow-on work that the PRD acknowledges but does not commit to.

**Anti-pattern:** Writing one undifferentiated feature list and labeling it "the PRD." Always tag each feature with its scope.

### 4. Shape Up "pitch" as a fixed-appetite alternative

Basecamp's Shape Up framework replaces the PRD with a **pitch**: problem, **appetite** (2 or 6 weeks of fixed budget), solution sketch (fat marker, not Figma), **rabbit holes** (risks to bound), and **no-gos** (explicit exclusions).

**Key inversion:** In Shape Up, **scope is the variable; time is fixed.**

### 5. Non-goals as a first-class section

Engineers and reviewers consistently raise questions like "what about X?" A **Non-Goals** section answers these preemptively:

> Non-goals (v1):
> - Mobile app support — desktop only
> - Bulk import — single-record only
> - Real-time sync — daily batch acceptable

### 6. Success metrics: leading vs lagging

- **Leading indicators** — observable within 1–4 weeks (adoption %, feature engagement, task completion rate)
- **Lagging indicators** — observable in 1–2 quarters (retention, revenue, NPS, churn)

Always include at least one leading indicator that the team can act on during the first month post-launch.

### 7. PRD is not RFC, not spec, not plan

- **PRD** (this skill) — PM-owned. WHAT to build, for WHOM, WHY now.
- **RFC / Design doc** — engineering-owned. HOW we propose to build it.
- **Spec** — engineering-owned. The contract. API shapes, behavior rules.
- **Plan / Task list** — engineering-owned. Sequenced units of work.

### 8. The "designed-by-committee" failure mode

If a PRD accumulates feedback from N stakeholders and the author tries to honor every comment, the doc becomes incoherent. The PM is the **author**, not a scribe.

Healthy pattern: collect feedback, summarize disagreements explicitly, **make a call**, and record the call with one-sentence rationale.

## Templates

### Modern PRD skeleton (Cagan + Lenny hybrid)

```markdown
# [Feature Name] — PRD

**Owner:** [PM name] · **Status:** Draft / In Review / Approved
**Last updated:** YYYY-MM-DD · **Target ship:** Quarter/Year

## TL;DR (3 sentences max)
[One sentence: the problem. One: the solution. One: the metric of success.]

## Problem
[User pain or business gap, with evidence: support volume, NPS verbatims,
analytics, sales-loss reasons.]

## Users
- Primary segment: [who, how many, current workaround]
- Secondary segment: [who, how many]
- Out of scope: [explicit segments NOT served by v1]

## Goals
## Non-goals (v1)
## Proposed solution
## Behavior (prose section, for non-UI logic)
## Success metrics
## Rollout

## Release criteria (Cagan)
- Performance: [SLO]
- Accessibility: [WCAG level]
- Security: [review completed]

## Risks and open questions
## Decisions log
## Sign-off
- [ ] Product (name, date)
- [ ] Engineering (name, date)
- [ ] Design (name, date)
```

### Shape Up pitch skeleton

```markdown
# Pitch: [Feature]

## Problem
## Appetite
[Small batch (2 weeks) | Big batch (6 weeks)]

## Solution
[Fat-marker sketch. Not high-fidelity.]

## Rabbit holes
## No-gos
```

## Anti-Patterns

1. **Solution-first opening** — leading with "we will build X" before establishing why.
2. **Designed-by-committee text** — incorporating every comment without making a call.
3. **PRD as discovery substitute** — writing a 12-page PRD to "figure out" what users want.
4. **Spec-creep** — PRD drifts into API shapes or schema choices.
5. **No non-goals** — every reviewer asks "what about X?"
6. **Lagging-metric-only success** — no signal during the launch window.
7. **Stale doc** — PRD written once and never updated.

## References

1. Marty Cagan, "Revisiting the Product Spec," Silicon Valley Product Group
2. Lenny Rachitsky, "Examples and templates of 1-Pagers and PRDs" — Lenny's Newsletter
3. Ryan Singer, "Write the Pitch," *Shape Up* (Basecamp)
