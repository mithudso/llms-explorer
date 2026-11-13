---
name: cfe
description: Alias for concept-family-explorer. Use /cfe to map, deduplicate, score,
  and research a topic family through the shared MongoDB library.
metadata:
  version: 1.0.1
  delta: Keep commissioned prompts and continuation in MongoDB
---

# CFE alias

For authorized persisted research, save the commissioned prompt, scope, coverage ledger, and resumable continuation in MongoDB concept scope/metadata and queue continuation metadata through owned leases and current revisions. Merge existing metadata deliberately before replacement. Read-only requests do not create bookkeeping writes. Client prompt, memory, and research files are not prerequisites.

Follow [concept-family-explorer](../concept-family-explorer/SKILL.md) for this task.
It uses the shared `research-library` MCP server for all library inventory, source
cache reads, leases, family changes, queue state, claims, and continuation. Begin
with `research_status` and keep the same external evidence, scoring, and honest
coverage gates. Local files or a copied research corpus are not prerequisites.
