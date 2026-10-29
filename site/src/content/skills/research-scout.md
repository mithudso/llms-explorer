---
title: "research-scout"
description: "Find source leads for the pending research queue and propose frontier concepts, then hand them to /dr and concept-family-explorer in private, resumable files."
order: 24
tags: [research, source-discovery, antigravity, concept-mapping]
aliasCommand: "/research-scout"
---

`research-scout` gives Antigravity or another lookup agent a bounded discovery
task before deeper research begins. It searches for useful documentation,
papers, source repositories, postmortems and issue discussions. It records why
each page may help, whether the agent could read it, and what remains unknown.

## Start with a small cohort

Ask the agent:

```text
Use research-scout to scout the next four MongoDB queue concepts and propose related frontier concepts. Save source leads and continuation notes using the skill's private handoff format. Spend at most 20 minutes. Leave claim validation and frontier acceptance to /dr and concept-family-explorer.
```

The helper reads the repository and hub tree/queue snapshots, groups siblings,
and preserves exact concept and parent names. It also supports frontier-only
scouting and an existing family as the starting point for new proposals.

## A durable handoff

Each run goes under `$HOME/.global-ai-hub/research/.scouts/` by default, outside
the public checkout. It keeps a versioned `scout.json`, a readable `handoff.md`,
the original prompt and continuation notes. Queries, source access gaps and
candidate concepts survive an interrupted session. The helper's `check`,
`render` and `find` commands validate, summarize and locate those bundles.

The JSON contains **unverified source leads**. A `ready` bundle means the scout
finished its selected batch; it does not establish researched status or full
frontier coverage. Scout output never marks queue rows complete or changes a
concept tree.

The research orchestrator reads relevant bundles. The Codex adapter adds bounded
source seeds automatically, while Claude uses the scout's research bridge to
pass them to slim workers. Other runners need an explicit handoff. `/dr` still
acquires readable text, checks relevance and source
origins, and validates its claims. [Concept-family-explorer](/skills/concept-family-explorer/)
still checks inventory, aliases, placement, novelty and viability before
accepting a frontier proposal. No speed or research-quality benchmark is claimed.
