---
title: "Worked example: the Anthropic hiring concept pack"
description: "How the Anthropic hiring concept pack in this repo was researched, structured, and source-rated — a worked example of the research-to-concept-pack workflow."
section: examples
order: 13
date: "2026-09-07"
tags: ["worked-example", "concept-pack", "research", "sourced-facts"]
sources:
  - "llms.txt"
  - "llms-anthropic-hiring.txt"
  - "llms-facts-anthropic-hiring.txt"
---

Every recipe on this site shows a retrieval technique against a hypothetical corpus. This one
shows the corpus getting built — an honest walkthrough of one real concept pack in this repo,
not a marketing pitch for the pipeline that made it.

## The question

Could this repo's own research-to-concept-pack workflow produce something worth trusting on a
real subject, not just a demo subject? The subject picked was concrete and checkable:
"what does Anthropic's hiring process actually look like, end to end?" The output lives at the
repo root as `llms-anthropic-hiring.txt` and `llms-facts-anthropic-hiring.txt`, indexed from
`llms.txt`.

## Gathering the sources

The research step used `/dr` — firecrawl search first, with scrape as the fallback when a
search snippet didn't carry enough of the page to cite confidently. Six independent sources
fed the pack: FinalRoundAI's interview guide, Glassdoor and TeamBlind candidate reports,
levels.fyi for compensation, Anthropic's own published candidate-AI-usage guidance, and a
candidate's substack account of a recent loop. Verified 2026-09-07 — the date stamped into both files, so a
reader can judge staleness without re-running anything.

## Why the pack and the facts live in separate files

`llms-anthropic-hiring.txt` is meant to be read narratively: a 10-topic index (recruiter
screen, technical assessment, system design, values interview, role variations, timeline,
compensation, preparation, culture signals, best practices), then a section per topic with
enough prose to orient a candidate. `llms-facts-anthropic-hiring.txt` is meant to be grepped
and cited: one claim per line, each ending in a `[src:]` tag. Splitting them means a single
fact can be corrected, re-sourced, or downgraded without touching the narrative that explains
it — and an agent that only needs the citation behind one number never has to load the whole
pack to find it.

## Rating confidence

The pack-level rating stamped in `llms.txt` — "High confidence" — follows a specific rule:
it holds when three or more independently produced sources agree on the same shape of the
process and none contradicts it. Here that's Anthropic's own candidate guidance,
FinalRoundAI's guide, and 200+ Glassdoor/TeamBlind candidate reports converging on the same
rounds-and-timeline picture:

> Anthropic interview process has 4-6 rounds and takes 3-6 weeks total (SWE: 3-5 weeks,
> Research: 4-7 weeks) [src: finalroundai.com, glassdoor.com]

That rating describes the pack as a whole, not every line inside it. Individual facts in
`llms-facts-anthropic-hiring.txt` carry whatever `[src:]` tags reflect their own actual
sourcing — including lines resting on a single source, like the claim that shapes the whole
pack's emphasis:

> Values and mission alignment interview is weighted equally with all technical rounds
> combined [src: finalroundai.com]

Compensation figures are quoted as sourced examples, not restated as a claim of this site's
own, because they carry that same one-source-plus-one-aggregator trail rather than the
three-way agreement behind the pack's overall rating:

> Software Engineer (L4/L5) total compensation range: $250K-$400K, with base $180K-$230K
> [src: finalroundai.com, levels.fyi]

And where only one source exists at all, the fact still ships, attributed honestly rather
than dropped or folded into the high-confidence average:

> The culture interview reveals "how people think" and is where confident, experienced
> candidates often fail [src: ridhimakhurana.substack.com]

## How an agent uses it

Index, then topic, then facts. `llms.txt` carries one entry describing the pack's scope,
audience, and confidence rating in a few lines — cheap enough to scan on every query. An agent
with a hiring question loads the concept pack's 10-line index next, jumps straight to the
matching topic section (e.g. "Compensation" for a negotiation question), and only opens
`llms-facts-anthropic-hiring.txt` when it needs the exact source behind a specific number. Most
questions never need that last hop.

## What to copy for your own subject

Name the subject concretely enough to check. Run `/dr` per topic-shaped question — if the
subject is broad enough that you don't yet know which topics matter, run
[concept-family-explorer](/skills/concept-family-explorer/) first to map the family and decide
what's worth researching before handing topics to [`/dr`](/skills/dr/). Write every claim as
one line with a `[src:]` tag in a facts file, separate from the narrative pack. Register both
under one entry in `llms.txt` with a confidence rating you can defend by counting sources out
loud — not a number that just feels right.
