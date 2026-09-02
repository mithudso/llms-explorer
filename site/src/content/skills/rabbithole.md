---
title: "rabbithole"
description: "The narrow inverse of concept-family-explorer — takes one named concept and exhausts it completely, drilling down through mechanism, edge cases, and primary sources until a pass finds nothing new."
order: 2
tags: [concept-depth, exhaustive-research, saturation]
aliasCommand: "rabbithole"
---

Where [concept-family-explorer](/skills/concept-family-explorer/) maps everything *around*
a subject, `rabbithole` moves *inward*: mechanism, sub-parts, edge cases, failure modes, the
history of how understanding of the concept changed, primary sources, and where experts
disagree — pass after pass, until a pass turns up nothing new.

## The six deepening questions

Every pass asks each of these against every claim still standing:

1. **Why is this true?** — the mechanism underneath a stated fact.
2. **What happens at the boundary or limit?** — edge cases, failure modes.
3. **What's the exception?** — cases the general claim doesn't cover.
4. **Who disagrees, and on what basis?** — expert disagreement, competing models.
5. **What did the primary source actually say, in its own words?** — drift between original
   and paraphrase.
6. **What changed over time in how this was understood?** — historical evolution.

## Saturation, measured

Each pass's claims are diffed against the accumulated list from every prior pass. The
**new-information rate** — new atomic claims this pass ÷ total claims after this pass — is
recorded per pass, and the run stops after **two consecutive passes** each score below 5%.
A single low-yield pass isn't enough to stop on; it could just be an unlucky question angle.
Two in a row, using a different subset of the six questions, is the corroborating evidence
that the concept is actually exhausted rather than merely under-questioned.

A pass whose new claims are mostly about a *different*, neighboring concept isn't
saturation — it's a sign the "concept" was really a family, and the run hands off to
concept-family-explorer instead of forcing a fake depth loop to continue.

**Use it for:** "deepen my understanding of X", "exhaust X completely", "rabbithole on X".

**Not for:** a domain or family, not one concept (concept-family-explorer) · one ordinary
research pass with no forced exhaustion loop (`/dr`) · pulling a concept's mentions out of a
corpus you already hold ([llms-concept-abstractor](/skills/llms-concept-abstractor/)).
