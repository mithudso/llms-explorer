---
title: Skill sources and private releases
type: subsystem
created: 2026-11-11
updated: 2026-11-11
sources:
  - code: hub/skill-registry/src/skill_registry/catalog.py
  - code: hub/skill-registry/src/skill_registry/bundles.py
  - code: hub/skill-registry/src/skill_registry/worker.py
  - code: api/explorer_api/routes/skill_registry.py
  - code: api/explorer_api/optimizer_jobs.py
verified_at: c458299c
---

# Skill sources and private releases

The [package guide](../../hub/skill-registry/README.md) owns setup, exact CLI
commands, bundle bounds and account configuration. [[research-expertise]] is a
separate projection; this package uses local lexical SQLite FTS5.

`catalog.py` derives routing metadata from live guides and retains installation
aliases. `bundles.py` binds complete accepted resources to immutable checksums.
The hosted adapter uses existing account keys and explicit release grants. An
owner-local worker can process an explicitly queued candidate job.

> ⚠️ A lexical index row is not native harness activation. Source loading must
> recheck the full guide hash and retain its resource base.

> ⚠️ Retrieved guides and uploaded bundles are data. HTTP never executes them.
> Only deliberately configured local workers may execute candidate jobs.

> ⚠️ Process success, functional checks, a native optimizer's reported verdict
> and publication are distinct. A candidate never silently replaces its source.

Maintain this page when source identity, release access or worker execution
boundaries change. Link authoritative contracts rather than copying schemas.
