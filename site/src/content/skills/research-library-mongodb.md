---
title: "research-library-mongodb"
description: "Search a shared research library, reserve concepts, and maintain versioned claims, sources and family relationships through MongoDB-backed MCP tools."
order: 25
tags: [research, mongodb, mcp, evidence, coordination]
aliasCommand: "/research-library-mongodb"
---

`research-library-mongodb` helps research agents work from the same library.
One agent can find a concept another agent researched, read its pinned sources,
inspect the remaining gaps, and continue an authorized assignment through MCP.
The agent does not need a copied corpus or a direct database connection.

It keeps the external research methodology used by [/dr](/skills/dr/),
[concept-family-explorer](/skills/concept-family-explorer/) and
[rabbithole](/skills/rabbithole/). The shared library supplies discovery,
versioned persistence and coordination; source acquisition and claim validation
still happen explicitly.

## Connect before using the workflow

Install the skill using the command on this page, then configure the research
library MCP server in the agent's own client. An operator must provide a working
server endpoint and the appropriate private capability. A reader can inspect the
managed corpus; a writer can also edit drafts and reserve work. Installing the
skill does not provision MongoDB, issue credentials or start research.

The [operator runbook](https://github.com/mithudso/llms-explorer/blob/main/hub/research-library/README.md)
and [MCP client guide](https://github.com/mithudso/llms-explorer/blob/main/hub/research-library/MCP.md)
describe installation and the exact tool contract. Treat source snapshots as
private material and store capabilities in the client's protected configuration.

## Ask for an evidence-aware investigation

```text
Use research-library-mongodb to inspect gaps around query planning. Search
broadly and within that family before proposing new concepts. Include unscored
and held frontier entries, read relevant peer sources, and report incomplete
coverage. Reserve only the concepts needed for the authorized research.
```

The agent pages the inventory and frontier, compares semantic and keyword
results, reads matching concepts, and preserves names, aliases and source pins.
Peer seeds offer useful wording and leads. They do not automatically validate a
new claim or establish an independent source origin. A degraded semantic
channel remains a coverage gap rather than proof that a candidate is novel.

## Coordinate edits without overwriting another worker

Research leases expire and require renewal. Edits also require current revisions;
changing a family relationship reserves every affected endpoint together.
Reparenting includes the child, old parent and new parent. Held work and STOP
markers stay visible without being resumed automatically.

Claims retain logical lineage and immutable versions. Sources retain exact
snapshot hashes and quotation spans when their current content changes. A
successful edit receipt means a draft was saved. Publication requires the
operator-enabled canonical process, its independent assertion gate and final
projection receipts. Descriptions and aliases remain discovery metadata, even
when canonical claims are verified.

**Use it for:** shared research discovery, queue and frontier inspection,
evidence-bound claim/source corrections, atomic family edits and coordinated
continuation across agents. The current bearer capabilities cover the whole
managed corpus; they do not provide individual-user or per-concept access rules.
