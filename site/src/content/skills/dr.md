---
title: "/dr — deep-research"
description: "Multi-source deep research using firecrawl and exa, synthesizing findings into cited reports with inline attribution, confidence ratings, and explicit knowledge gaps."
order: 3
tags: [research, citations]
aliasCommand: "/dr"
---

`/dr` searches the web across multiple sources (firecrawl and exa MCPs, falling back to
plain web search/fetch), synthesizes what it finds, and delivers a cited report — inline
source attribution, a confidence rating per claim, and the gaps it couldn't fill left
explicit rather than papered over.

It's the workhorse both [concept-family-explorer](/skills/concept-family-explorer/) and
[rabbithole](/skills/rabbithole/) call into for the actual per-concept research; those two
skills decide *what* to research and *when to stop* — `/dr` is what actually goes and
researches it, once a concept has been named.

**Use it for:** "research the current state of X", "deep dive into X vs Y", "due diligence
on company X", "what's the latest on X" — anything that names a concrete topic and wants a
synthesized, cited answer.

**Not for:** a quick one-fact lookup with no synthesis needed (answer directly) · mapping
which topics are worth researching in the first place (concept-family-explorer) · editing an
existing document · a subject broad enough that it needs breadth-first family-mapping before
any one topic is worth a `/dr` call.
