---
description: >-
  Narrow inverse of concept-family-explorer: take ONE already-named concept and exhaust it
  completely — drill straight down through its mechanism, sub-parts, edge cases, failure
  modes, historical evolution, primary sources, and expert disagreements — running repeated
  deepening passes until a pass adds no meaningfully new information. CFE asks "what am I
  missing AROUND this subject" (breadth); this skill asks "what am I missing INSIDE this one
  concept" (depth). TRIGGER: /rabbithole, "deepen my understanding of X", "exhaust X
  completely", "go as deep as possible on X", "rabbithole on X", "don't stop until there's
  nothing left to learn about X", "give me everything there is to know about X". SKIP:
  subject is a family/domain, not one concept → concept-family-explorer; concept already
  named and just needs one research pass, no exhaustion loop → /dr; abstracting a concept's
  mentions OUT of an existing docset/corpus you already hold → llms-concept-abstractor;
  reorganizing the skill tree → skill-tree-architect.
name: rabbithole
version: "1.0.0"
updated: "2026-09-01"
model: claude-opus-5
effort: high
category: meta
tags: [concept-depth, exhaustive-research, saturation, orchestration]
keywords:
  - deepen
  - rabbithole
  - exhaust a concept
  - go deeper
  - depth-first research
  - narrow inverse of concept-family-explorer
  - everything about one thing
  - primary sources
  - edge cases and failure modes
related_skills:
  - concept-family-explorer
  - deep-research
  - llms-concept-abstractor
  - skill-tree-architect
  - full-suite
whenToUse:
  - "deepen my understanding of <concept>"
  - "exhaust <concept> completely — go as deep as you can"
  - "rabbithole on <concept>"
  - "give me everything there is to know about <concept>, however deep that goes"
  - "keep researching <concept> until another pass finds nothing new"
whenNotToUse:
  - "the subject is a domain or family, not one concept (use concept-family-explorer)"
  - "one ordinary research pass is enough, no exhaustion loop wanted (use /dr)"
  - "the concept's mentions already sit inside a corpus you hold and you want them pulled out (use llms-concept-abstractor)"
  - "you want the skill tree reorganized, not a concept researched (use skill-tree-architect)"
---

# Rabbithole (`/rabbithole`, "deepen")

`concept-family-explorer` maps everything **around** a subject and stops at the first
useful pass over each neighbor. This skill does the opposite: it takes **one** concept CFE
would treat as a single node, and instead of moving outward to siblings, it moves **inward** —
mechanism, sub-parts, edge cases, failure modes, the history of how understanding of it
changed, primary sources, and where experts disagree — pass after pass, until a pass turns up
nothing new. It is depth-first where CFE is breadth-first; the two compose (CFE finds the
node worth this treatment, this skill exhausts it, CFE's frontier re-expansion can pick up
any sibling this run surfaces).

```
concept ─▶ [1] scope & boundary ─▶ [2] pass 0: broad draft ─▶ [3] pass N: deepen
                                                                     ▲        │
                                                     [4] new-info rate ◀──────┘
                                                            │
                                                     [5] saturated? ──no─▶ back to [3]
                                                            │ yes
                                                            ▼
                                              [6] compile dossier ─▶ [7] handoffs + report
```

## When not to use

- Subject is a domain, family, or "what am I missing about X" question → `concept-family-explorer`.
- One ordinary research pass is what's wanted, no forced exhaustion loop → `/dr` directly.
- The concept's mentions already live inside a corpus you hold (docs, notes, a textbook) and
  you want them pulled out and organized → `llms-concept-abstractor`.
- Skill tree needs reorganizing, no new research → `skill-tree-architect`.

## Inputs

- **concept** (required) — one named concept, not a domain. If a domain/family is given,
  say so and suggest `concept-family-explorer` instead (or narrow it: "the family is too
  broad to rabbithole directly — which single concept inside it should I exhaust first?").
- **maxPasses** (optional, default 6) — hard cap on deepening passes regardless of
  saturation, since a genuinely deep concept (e.g. "consensus algorithms") could otherwise
  run indefinitely.
- **budgetMinutes** (optional) — wall-clock cap, same contract as `concept-family-explorer`.
- **seedMaterial** (optional) — a corpus, docset, or file the user already has; used as
  Pass 0 evidence before any web research, so passes don't re-derive what's already on disk.

## Workflow

### Step 1 — Scope and boundary

State what is explicitly IN scope (the concept's own mechanism, internals, history,
variants, primary sources) and what is explicitly OUT (siblings, parent domain, adjacent
fields — those are CFE's job, not this skill's). Getting this boundary wrong is the most
common failure: without it, "deepen X" quietly turns into "map the family around X," which
duplicates CFE and never saturates because breadth has no natural stopping point the way
depth does.

### Step 2 — Pass 0: broad draft

One ordinary research pass (reuse `/dr`'s research step, or read `seedMaterial` first if
given): mechanism in plain terms, the sub-parts/phases it decomposes into, the two or three
most-cited primary sources, the obvious edge cases. This draft is the baseline every later
pass is measured against — write it down as a flat list of atomic claims (one fact per line),
not prose, so Step 4's new-information count is countable.

### Step 3 — Deepen (pass 1..N)

Each pass re-reads the accumulated claim list and asks, of **every** claim still standing:
"why is that true," "what happens at the boundary/limit," "what's the exception," "who
disagrees and on what basis," "what did the earliest/primary source actually say, in its own
words, versus how it's now paraphrased." Follow each answer to its own primary source when
one exists. A pass that only rephrases existing claims produces zero new atomic facts and
counts as empty — depth means new claims, not longer sentences about old ones. See
`references/depth-passes.md` for the six question types in full, with worked examples of a
genuine deepening ("why does TCP slow-start use exponential *then* linear growth" →
surfaces the congestion-avoidance threshold, a new mechanism) versus a fake one (restating
"TCP is reliable" three ways).

### Step 4 — Measure new-information rate

Diff this pass's claim list against the accumulated one. **New-information rate** = new
atomic claims this pass ÷ total claims after this pass. Record the rate per pass — the
declining curve is the evidence exhaustion is real, not assumed. Full formula and the
two-consecutive-empty-passes rule: `references/saturation.md`.

### Step 5 — Saturation test

Stop when **any** holds:

- **Depth saturation** — two consecutive passes each score new-information rate < 5%.
- **Budget exhausted** — `maxPasses` or `budgetMinutes` hit; report as a soft stop, not
  saturation, and say how many more passes looked likely to still pay off.
- **Boundary breach detected** — a pass keeps generating sibling/adjacent concepts instead
  of deeper claims about the same one (a sign the concept was actually a family) → stop,
  say so, hand off to `concept-family-explorer` with this run's claim list as its seed
  inventory rather than forcing a fake depth loop to continue.

Otherwise return to Step 3.

### Step 6 — Compile the dossier

Write the final claim list as a structured dossier: definition, mechanism (with the
sub-parts a Step 3 pass surfaced), history/evolution, edge cases and failure modes,
disagreements (side by side, never averaged — same non-negotiable as `llms-concept-abstractor`),
primary sources cited per claim. If the concept sits in the concept tree, this dossier is
what backs its node's depth (as opposed to CFE's breadth-only stub); write it back via the
same concept-tree tools CFE uses, tagged as a depth-pass rather than a coverage pass so CFE
doesn't re-count it as a sibling gap filled.

### Step 7 — Handoffs and report

Report per-pass new-information rate (the declining curve), total passes run, saturation
verdict (`SATURATED-DEPTH` / `BUDGET_EXHAUSTED` / `BOUNDARY-BREACH → handed to CFE`), the
compiled dossier's location, and any sibling/adjacent concepts surfaced along the way as a
handoff list for `concept-family-explorer` — this skill never chases them itself.

## Quality rules

1. **Depth, not breadth.** The moment a pass wants to talk about a sibling concept instead
   of going deeper into this one, that's a boundary breach (Step 5) — hand off, don't absorb.
2. **Countable claims, not prose.** New-information rate is meaningless against paragraphs;
   keep the accumulated dossier as atomic, diffable claims until Step 6's final compile.
3. **Primary sources over paraphrase.** A pass that only re-reads secondary summaries of the
   same primary source produces no new depth even if the words are new.
4. **Disagreements are data.** Where credible sources conflict, both sides go in the
   dossier, never silently resolved.
5. **Saturation is evidence.** Report the declining new-information curve; a flat "ran out
   of ideas" is not the same claim as "two passes in a row found nothing new," and only the
   second one is the real stop condition.

## Trigger examples

**Should trigger:**
- "Deepen my understanding of the TCP congestion-avoidance algorithm — go as far as it goes."
- "Rabbithole on the halting problem until there's nothing left to learn."
- "Exhaust everything about MongoDB's WiredTiger checkpoint mechanism."

**Should NOT trigger:**
- "What am I missing about distributed systems in general?" → `concept-family-explorer`.
- "Research CRDTs and make a skill" (one pass, no forced exhaustion) → `/dr`.
- "Pull everything these three docsets say about caching" → `llms-concept-abstractor`.
