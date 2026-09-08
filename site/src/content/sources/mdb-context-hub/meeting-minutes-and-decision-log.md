---
title: "Meeting Minutes and Decision Log"
description: "Three distinct artifacts:"
---

# Meeting Minutes and Decision Log

## Overview

Three distinct artifacts:

1. **Agenda** — written *before* the meeting. Forward-looking.
2. **Minutes** — written *during/after*. Outcomes, decisions, action items, dissent on the record. Backward-looking and durable.
3. **Decision Log / ADR** — written *when a decision is significant enough to outlive the meeting*. One decision per record, indexed, immutable once accepted.

## Core Concepts

### 1. The four load-bearing fields

Every captured decision must answer:

- **What was decided** — a single declarative sentence, not a description of the debate.
- **Why** — the one or two reasons that tipped it. Trade-offs accepted. Alternatives rejected.
- **Who owns it** — exactly one named person per action item. Co-ownership is no ownership.
- **When** — a specific date, not "soon" or "next sprint".

### 2. Agenda vs minutes — separate documents, different tense

Agenda items are intent ("discuss pricing tier rollout"). Minutes items are outcome ("decided to defer pricing tier rollout to Q3; revisit June 15 sync").

### 3. Sync vs async minutes

**Sync minutes** (live meeting): Capture only what is needed to reconstruct outcomes. Skip the back-and-forth. Aim for ~10% the length of the conversation.

**Async minutes** (Slack thread, Loom comment chain): The thread *is* the discussion. The minutes job is to write the **synthesis at the top**.

### 4. Verbatim quote vs paraphrase

**Use a verbatim quote** in three cases only:
- **On-the-record dissent**
- **A specific commitment**
- **A regulatory / legal trigger**

Everywhere else, paraphrase.

### 5. Decisions live in a log, not in the meeting file

Significant decisions should be **extracted** into a separate decision log (or ADR file) with a stable ID, indexed, and linked back to the meeting.

### 6. The ADR form for technical decisions

Michael Nygard's 2011 template: **Title · Status · Context · Decision · Consequences**

Status moves through: **proposed → accepted → deprecated → superseded by ADR-NNNN**. ADRs are never deleted or edited substantively after acceptance — they are superseded by a new ADR that links back.

### 7. Capture dissent on the record

Name the dissenter and one-sentence their objection. "Anonymous 'concerns were raised'" is useless and reads as cover.

### 8. Outcome-oriented language

Bad: "We talked about the latency issue for a while."
Good: "Decided to roll back the v2.3 caching change; Priya owns rollback PR by Wed."

Every bullet should start with a verb of outcome (decided, agreed, deferred, rejected, assigned, scheduled, escalated).

### 9. Distribute fast, freeze faster

Minutes that go out 5 days later are minutes nobody reads. Target: same-day or next-morning.

## Templates

### Template 1 — Sync meeting minutes

```markdown
# [Meeting name] — YYYY-MM-DD

**Attendees:** Name1, Name2, Name3
**Absent (invited):** Name4
**Scribe:** Name1

## Decisions
- **[D1]** Decided to ship the dashboard refactor behind a feature flag in v1.4.
  - Why: avoids blocking the marketing launch on the 18th; allows rollback in <1 min.
  - Dissent: none.

## Action items
| # | Action | Owner | Due |
|---|---|---|---|
| A1 | Open feature-flag config PR for dashboard refactor | Priya | 2026-06-03 |

## Parked / not decided
- Pricing tier change — deferred to Q3 planning sync.

## Next meeting
2026-06-10, same time. Agenda owner: Priya.
```

### Template 3 — ADR (Michael Nygard 2011 form)

```markdown
# ADR-0042: Adopt OpenTelemetry for backend tracing

- **Status:** Accepted — 2026-05-29
- **Deciders:** Anand, Lin, Mitch

## Context

We currently emit traces through a custom span library written in 2022.

## Decision

We will replace the custom span library with OpenTelemetry SDKs.

## Consequences

**Positive**
- Removes ~1.2K lines of custom code.
- Unlocks the OTel ecosystem.

**Negative**
- Migration cost estimated at 6 engineer-weeks.
```

## Anti-Patterns

- **Transcript-as-minutes** — paragraphs of "Then Bob said... then Alice responded..."
- **Anonymous dissent** ("concerns were raised")
- **Decisions buried in the discussion**
- **Action items without an owner or date**
- **Co-owned action items** — "Priya and Jordan" means neither one

## References

- Michael Nygard, "Documenting Architecture Decisions" (2011)
- Wrike, "Meeting minutes template with action items"
- Atlassian Confluence, "Meeting Notes Template"
