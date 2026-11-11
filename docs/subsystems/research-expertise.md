---
title: Local research expertise
type: subsystem
created: 2026-11-11
updated: 2026-11-11
sources:
  - code: hub/research-expertise/src/research_expertise/store.py
  - code: hub/research-expertise/src/research_expertise/capture.py
  - code: hub/research-expertise/src/research_expertise/mcp_server.py
verified_at: 3dd863b0
---

# Local research expertise

The standalone [package guide](../../hub/research-expertise/README.md) owns setup,
commands, projection scope and migrations. Its [MCP contract](../../hub/research-expertise/MCP.md)
owns tool schemas and capture behavior. [Testing guidance](../TESTING.md) names
the frozen environment and offline checks.

Canonical packs remain the authoring source. Neo4j stores exact passages and
explicit navigation; CPU embeddings support semantic retrieval. Captures save
source snapshots before indexing and retain old revisions.

> ⚠️ Exact quotation matching checks integrity. It does not prove entailment or
> grant native research acceptance. Imported passages remain unreviewed.

> ⚠️ The official Neo4j MCP can read projection rows without the application
> freshness predicate. Use bounded expertise retrieval for current source citations.

> ⚠️ Legacy hub indexing/Ollama and this CPU projection are separate workloads.
> Dependency installation or documentation refresh must not restart paused jobs.

Maintain this page when the projection or capture boundary changes. Link exact
contracts instead of copying their schemas and counts.
