---
title: "full-suite"
description: "Maps a concept family, researches selected gaps and compiles per-concept and rollup llms-family files, reporting source, index and coverage limits separately."
order: 5
tags: [orchestration, llms-txt, saturation]
aliasCommand: "/full-suite"
---

`full-suite` is the top of the stack: it runs
[concept-family-explorer](/skills/concept-family-explorer/) to map a subject's family,
researches the selected gaps under its source and budget rules, and then — where the family-explorer alone
would stop at a mapped tree — compiles the result into the full llms-family set (llms.txt,
llms-full, llms-small, llms-facts, llms-vocabulary) at both the per-concept and rollup
level, with keyword (FTS5) and semantic (embedding) indexes, and registers everything in
every reachable concept tree. The report distinguishes saturation from a capped or blocked
run and records unavailable indexes or registrations.

A cheap, low-effort frontrunner scout pre-checks candidate domains for an existing
llms.txt/llms-full.txt before the expensive passes run, seeding both `/dr` and
concept-family-explorer's warm-start cache so the full run doesn't re-derive what a target
site already publishes.

**Use it for:** "do a full suite on X", "fully exhaust X", "give me everything on X" — when
the deliverable is the complete artifact set, not just a map or a report.

**Not for:** one named concept with no family-mapping needed (`/dr`) · a concept map with no
llms packs wanted (concept-family-explorer) · fixing one existing llms file
([llms-deep-optimizer](/skills/llms-deep-optimizer/)) · abstracting one concept out of a
corpus you already hold ([llms-concept-abstractor](/skills/llms-concept-abstractor/)) · a
cited report with no artifacts (`deep-research`) · rebalancing an existing tree with no new
research ([skill-tree-architect](/skills/skill-tree-architect/)).
