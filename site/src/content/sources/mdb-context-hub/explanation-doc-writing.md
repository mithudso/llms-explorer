---
title: "Diátaxis Explanation Quadrant"
description: "An explanation doc is a discussion. Its purpose is not to instruct, not to enumerate, and not to walk a reader through a goal. Its job is to leave the reader with a clearer mental model — of why the s"
---

# Explanation Doc Writing — Diátaxis Explanation Quadrant

## Overview

An explanation doc is **a discussion**. Its purpose is not to instruct, not to enumerate, and not to walk a reader through a goal. Its job is to leave the reader with a clearer **mental model** — of why the system is shaped this way, what alternatives existed, what trade-offs were made.

**The single most-violated rule: explanation is not a proposal.** It describes the world as it is — choices already made, designs already shipped, reasoning already settled. If you are arguing for a change, you are writing an **RFC**, not an explanation.

## Core Concepts

### 1. The reader's question is "why", not "how" or "what"

*"Why does the cache invalidate on write rather than on read?"*
*"Why is the default replication factor 3?"*
*"Why do we use append-only logs here when most systems would update in place?"*

If the reader's question is "how do I configure replication factor", they need a how-to. Explanation answers the **shape-of-the-world** questions.

### 2. Build the mental model, then layer the detail

Lead with the analogy or the one-sentence essence. *"Think of the write-ahead log as a journal: every change is written there first, and only later applied to the data files."* Then add the next layer: *"This means a crash in the middle of an update never leaves the data file half-written."*

### 3. Show alternatives and why they were not chosen

A decision without alternatives is not a decision; it's a proclamation. The explanation doc names the roads not taken: *"We considered an LSM-tree here, but the workload is read-heavy and the write-amplification penalty was not worth the write throughput gain."*

### 4. History earns trust

A short history paragraph — *"v1 used Redis for the queue; we hit head-of-line blocking under load in 2024 and moved to Kafka in v2"* — gives the reader context that no amount of current-state description can replicate.

### 5. Discuss, don't prescribe

Explanation uses words like *because*, *however*, *the trade-off is*, *one consequence is*. It avoids *do this*, *use this*, *configure this*.

### 6. Cite the boundary of the explanation

*"This doc covers our write-path; for read-path discussion see [the read-path doc]"*

### 7. Distinguish from RFCs and ADRs

- **RFC** = proposing a change before it ships. Argumentative voice. Open to debate.
- **ADR** (Architecture Decision Record) = a small, dated note of a decision made.
- **Explanation doc** = the broader discussion of how and why the system is the way it is.

### 8. Stay evergreen

Explanation docs should age slowly. Captures the durable reasoning: invariants, trade-offs, philosophy.

## Template — "How <X> works" / concept doc

```markdown
# How <X> works

<One-paragraph essence: the analogy or the one-sentence mental model.>

## Why <X> exists

<The problem <X> was designed to solve.>

## The mental model

<2–4 paragraphs building the model. Diagram if useful.>

## How it fits with the rest of the system

<Where <X> sits relative to neighboring components.>

## Trade-offs and alternatives considered

We chose <X> over <Y> because <reason>. <Y> would have given us <advantage>
but cost us <disadvantage>.

## History

<Short paragraph: how <X> evolved.>

## Where this discussion ends

This doc covers <scope>. For:
- *How to <task> with <X>* — see [the how-to](…).
- *The full <X> API* — see [reference](…).
```

## Anti-Patterns

### AP-1 — The "explanation" that is secretly a tutorial
> "To understand caching, let's build a simple cache..."
If the reader is creating files, you are running a tutorial.

### AP-2 — Prescriptive sneak-in
> "You should always set `replication=3` because…"
That's a how-to recommendation. Recast: *"Replication factor 3 trades disk and write-bandwidth for the ability to tolerate single-node failure."*

### AP-3 — No alternatives named
A doc that explains a choice without ever naming what was rejected reads as a sales pitch.

### AP-4 — Drift into RFC territory
Argumentative voice, open questions, "we are considering moving to…" — that's an RFC.

## References

1. [Explanation — Diátaxis](https://diataxis.fr/explanation/)
2. [Explanation — Divio Documentation](https://docs.divio.com/documentation-system/explanation/)
3. Michael Nygard, "Documenting Architecture Decisions" (2011)
