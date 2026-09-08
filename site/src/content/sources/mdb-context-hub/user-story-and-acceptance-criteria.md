---
title: "User Story and Acceptance Criteria"
description: "This skill takes a feature idea and produces backlog items the team can groom, estimate, and ship. Covers Mike Cohn's user-story template, the INVEST quality bar (Bill Wake, 2003), Given/When/Then acc"
---

# User Story and Acceptance Criteria

## Overview

This skill takes a feature idea and produces backlog items the team can groom, estimate, and ship. Covers Mike Cohn's user-story template, the INVEST quality bar (Bill Wake, 2003), Given/When/Then acceptance criteria in Gherkin form, splitting strategies (vertical-slice principle and SPIDR), and the separation between *acceptance criteria* (per-story, varies) and *definition of done* (team-wide, stable).

## Core Concepts

### 1. The Mike Cohn user-story template

```
As a <role>, I want <capability> so that <benefit>.
```

**`As a <role>`** — the user, not the system. "As a user" is the most common failure mode. Name a specific actor type: "As a job seeker", "As an on-call TAM", "As a paid subscriber on the Pro tier."

**`I want <capability>`** — the *what*, written goal-first, agnostic to *how*.

**`so that <benefit>`** — the *why*. The benefit clause is the most-skipped and most-valuable.

### 2. INVEST — the quality bar

**I — Independent.** The story can be built, demoed, and shipped without waiting on another story.

**N — Negotiable.** The story is a placeholder for a conversation, not a contract.

**V — Valuable.** The story delivers value to a real user or stakeholder.

**E — Estimable.** The team has enough context to size it.

**S — Small.** Fits comfortably inside an iteration. Heuristic: ≤ 50% of one developer's iteration capacity.

**T — Testable.** A definite test exists for "done."

### 3. Given / When / Then — Gherkin acceptance criteria

```
Given <some context>
When <some action>
Then <some observable outcome>
```

**`And` and `But`** chain steps in the same phase.

**Rules:**
- 3–5 steps per scenario.
- 1–3 acceptance criteria per story.
- Each criterion tests a *distinct* aspect.
- Concrete values, not generics: "Given a charge of $20.00" not "Given a valid charge."

### 4. The vertical slice rule

A user story must be a *thin vertical slice through the architecture* — a sliver that touches every layer and delivers end-to-end value.

**Horizontal (wrong):**
- Story 1: Build the UI for case filtering.
- Story 2: Build the API endpoint for case filtering.
- Story 3: Add the database index for case filtering.

**Vertical (right):**
- Story 1: Filter cases by severity (S1 only, no UI persistence).
- Story 2: Filter cases by status, with severity already shipped.

### 5. SPIDR — five ways to split a story

**S — Spike.** Time-box a research task to remove uncertainty blocking estimation.

**P — Path.** Split by user path. "Pay with credit card" / "Pay with Apple Pay."

**I — Interface.** Split by client or platform. "Filter cases on desktop" / "Filter cases in mobile app."

**D — Data.** Split by data scope. "Filter cases for active accounts only" first; "including archived accounts" later.

**R — Rules.** Relax business rules in the first slice. "Refunds, with no approval workflow" first; "Refunds with manager-approval workflow" later.

### 6. Acceptance criteria vs Definition of Done

**Acceptance Criteria (AC):**
- Specific to *this* story.
- Authored by the product owner with the team.
- Vary between stories.
- Answer: "What must this story do for the user to accept it?"

**Definition of Done (DoD):**
- A team-wide standard that applies to *every* story.
- Stable across sprints.
- Answers: "What must any item meet to be called done?"

A story is **done** when *both* its acceptance criteria are met *and* the team's definition of done is satisfied.

## Templates

### Template — user story with acceptance criteria

```
**Title:** Filter case list by severity

**Story:**
As an on-call TAM,
I want to filter the case list by severity (S1 / S2 / S3 / S4),
so that during a busy on-call shift I can triage S1s first
without scrolling through lower-severity cases.

**Acceptance Criteria:**
1. Given the case list shows ≥ 1 case at each of S1–S4,
   When I select "S1 only" in the severity filter,
   Then only S1 cases are visible
     And the count badge shows the number of visible S1 cases.

2. Given I have applied a severity filter,
   When I reload the page,
   Then the same filter is reapplied
     And the URL contains the filter as a query parameter.

**Out of scope (not in this story):**
- Filtering by status or owner.
- Multi-select severity.

**Estimate:** 5 points
```

### Example — story split using SPIDR

```
Original (too big, ~21 points):
"As an admin, I want to manage subscription plans."

Split via Path + Rules:
Story A (5 pts) — read-only plan list
Story B (8 pts) — create new plan (USD only; no proration)
Story C (5 pts) — edit plan name (only)
Story D (8 pts) — edit plan price with proration
Story E (3 pts) — deactivate a plan
```

### Definition of Done (team-wide)

```markdown
# Team Definition of Done

- [ ] Acceptance criteria met (verified by the PM or designate).
- [ ] Unit tests written for new logic; ≥ 80% coverage on changed files.
- [ ] Code reviewed by ≥ 1 other engineer.
- [ ] CHANGELOG.md updated (or marked N/A in the PR).
- [ ] User-facing docs updated (if UI or API surface changed).
- [ ] No new lint warnings; no new TypeScript `any`.
- [ ] Deployed to staging; smoke test passing.
- [ ] Accessibility audit clean for UI changes.
```

## Anti-Patterns

- **"As a user, I want..."** — every story starts the same way, tells you nothing.
- **Solution-shaped capability clauses** — "I want a dropdown in the top-right corner."
- **No `so that` clause** — strips out the prioritization signal.
- **Horizontal-layer stories** ("Build the backend for X") — each is independently unshippable.
- **Acceptance criteria that restate the story.**
- **20-criterion acceptance lists** — the story is too big. Split.
- **Conflating Acceptance Criteria with Definition of Done.**
- **Forcing bugs / tech-debt / spikes into user-story syntax.**

## Decision Heuristics

- **"As a user" or a specific role?** Always specific.
- **Story or epic?** If the story has > 1 sprint of work or > 5 acceptance criteria, it's an epic. Split via SPIDR.
- **Gherkin or checklist for AC?** Gherkin when multi-step interactions or branching. Checklist when criteria are independent observable facts.
- **Put it in AC or in DoD?** Specific to this story → AC. Applies to every story → DoD.

## References

- Mike Cohn, "User Stories and User Story Examples" — Mountain Goat Software
- Bill Wake, "INVEST in Good Stories, and SMART Tasks" — XP magazine, 2003
- Mike Cohn, "SPIDR: Five Simple but Powerful Ways to Split User Stories"
- Cucumber, "Gherkin Reference" — https://cucumber.io/docs/gherkin/reference/
- Scrum.org, "Definition of Done vs Acceptance Criteria"
