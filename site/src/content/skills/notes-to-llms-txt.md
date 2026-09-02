---
title: "notes-to-llms-txt"
description: "Turns disorganized notes — a scratch file, a run of meeting notes, a mixed-topic dump — into a well-formed llms.txt family, by segmenting, clustering by topic, and drafting a source-anchored entry per topic."
order: 8
tags: [llms, notes, structuring]
aliasCommand: "/notes2llms"
liveDemo: "/playground/notes-to-llms/"
---

Raw notes are multi-topic, unordered, and mix genres — a fact next to a todo next to a
half-formed question next to a name. `notes-to-llms-txt` sits upstream of both
[llms-concept-abstractor](/skills/llms-concept-abstractor/) (which assumes you already know
the one concept to pull out) and [llms-deep-optimizer](/skills/llms-deep-optimizer/) (which
assumes structure already exists to audit): it takes the mess as-is, finds the topics
actually in it, and drafts a first llms.txt family good enough for the optimizer to take the
rest of the way.

## How it works

1. **Ingest** every source in full — no sampling.
2. **Segment** into atomic units (bullet, paragraph, heading-scoped block), tagging each
   unit's genre: fact, todo, decision, question, name/entity mention, or noise.
3. **Cluster** the surviving units by topic — notes are rarely about one thing, so clustering
   goes by subject, not by which file or meeting a unit came from.
4. **Draft** an entry per topic with enough content: title, description, source-anchored
   facts, verbatim links, open questions left as questions rather than smoothed into facts.
5. **Compile and hand off** to `llms-deep-optimizer` for the real multi-pass audit.

Every fact traces to a specific note; a gap in the notes is a gap in the output, never
filled from general knowledge. Anything secret-shaped — API keys, passwords, connection
strings pasted into a meeting note in passing — is redacted before it reaches any output
file, since these output families are exactly the kind of thing that ends up pasted into a
shared repo or a public library later.

Try a bounded, single-pass version live on the
[notes-to-llms playground page](/playground/notes-to-llms/).

**Use it for:** "turn my notes into an llms.txt", "structure these meeting notes",
"my notes are a mess, make them navigable".

**Not for:** notes already scoped to one concept (llms-concept-abstractor) · an llms.txt
that already exists and just needs auditing (llms-deep-optimizer) · a request that needs new
research, not organizing what's already written down (`/dr`).
