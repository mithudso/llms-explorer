---
title: Skill sources and private releases
type: subsystem
created: 2026-11-11
updated: 2026-11-12
sources:
  - code: hub/skill-registry/src/skill_registry/catalog.py
  - code: hub/skill-registry/src/skill_registry/bundles.py
  - code: hub/skill-registry/src/skill_registry/worker.py
  - code: hub/skill-registry/src/skill_registry/mongo_store.py
  - code: hub/skill-registry/src/skill_registry/mongo_mcp.py
  - code: hub/skill-registry/src/skill_registry/prompt_hook.py
  - code: api/explorer_api/routes/skill_registry.py
  - code: api/explorer_api/optimizer_jobs.py
verified_at: c458299c
---

# Skill sources and private releases

The [package guide](../../hub/skill-registry/README.md) owns setup, exact CLI
commands, bundle bounds and account configuration. [[research-expertise]] is a
separate projection. The local catalog uses SQLite FTS5. The optional MongoDB
distribution uses Atlas keyword search and native Voyage automated embeddings.

`catalog.py` derives routing metadata from live guides and retains installation
aliases. `bundles.py` binds complete accepted resources to immutable checksums.
The hosted adapter uses existing account keys and explicit release grants. An
owner-local worker can process an explicitly queued candidate job.

`mongo_store.py` projects canonical sources into `ESRE-TAM.skills` using
`MONGODB_URI2`. It preserves source identities and installation aliases.
`skills_versions` holds immutable release snapshots; `skills_resources` holds
content-addressed resource chunks. The release hash binds the guide and resource
manifest. [The operations guide](../../hub/skill-registry/README.md#mongodb-distribution-and-voyage-skill-search)
describes setup and [the MCP contract](../../hub/skill-registry/MCP.md#mongodb-distribution-mcp)
describes bounded remote access.

The dedicated MongoDB MCP exposes read tools over stdio or authenticated
Streamable HTTP. Clients need its HTTPS URL and read token. They can load a skill
and its references without installing skill files or receiving database
credentials. The prompt hook supplies bounded candidate metadata and leaves
skill selection to the agent. It does not execute a retrieved workflow.

> ⚠️ A lexical index row is not native harness activation. Source loading must
> recheck the full guide hash and retain its resource base.

> ⚠️ Retrieved guides and uploaded bundles are data. HTTP never executes them.
> Only deliberately configured local workers may execute candidate jobs.

> ⚠️ Process success, functional checks, a native optimizer's reported verdict
> and publication are distinct. A candidate never silently replaces its source.

Maintain this page when source identity, release access or worker execution
boundaries change. Link authoritative contracts rather than copying schemas.
