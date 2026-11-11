# Codebase Overview

This document maps the entire repository structure by directory and module.

## Root Directory

- `CLAUDE.md`: Main repo developer instructions, commands, architecture constraints.
- `AGENTS.md`: Catalog of repo-local agents.
- `GEMINI.md`: Gemini CLI rules and guidelines.
- `memory.md`: Versioned task and active state log.
- `prompts.md`: Ordered log of user prompts and instructions.
- `README.md`: Project introduction and quick-start.
- `LICENSE`: MIT license.
- `CONTRIBUTING.md`: Contribution guide.
- `CODE_OF_CONDUCT.md`: Contributor Code of Conduct.
- `.env.example`: Safe template for environment variables.
- `.editorconfig`, `.gitattributes`, `.gitignore`: Repository formatting and source control policies.

## 1. `api/` — Backend API & Metering Gateway

- `explorer_api/`
  - `main.py`: FastAPI application factory (`create_app()`), CORS, TrustedHost middleware, health/ready probes.
  - `models.py`: SQLAlchemy database models (Users, ApiKeys, Credits, LedgerEntry, Plans, Subscriptions, Jobs, Trees, etc.).
  - `db.py`: Async database engine and session factory creation.
  - `settings.py`: Pydantic settings loading from environment variables.
  - `auth.py`: WebAuthn passkey ceremony handling, OAuth flows, signed session cookies.
  - `keys.py`: API key generation, Argon2id hashing, prefix lookups, spend limits.
  - `ledger.py`: Append-only spend recording, balance debiting, quota checks.
  - `billing.py`: Stripe webhook processing, checkout sessions, customer portal.
  - `plans.py`: Tier limits, pricing, and quota definitions.
  - `trees.py`: Tree manipulation and storage isolation.
  - `moderation.py`: Proposal and artifact moderation.
  - `artifacts.py`: Public and private artifact storage and retrieval.
  - `routes/`: Sub-routers for `auth`, `keys`, `usage`, `billing`, `mcp`, `trees`, `proposals`, `artifacts`, `contribute`, `skills`.
- `alembic/`: Database migrations.
- `tests/`: Hermetic API unit and integration tests.

## 2. `site/` — Astro Frontend & Explorer Portal

- `src/pages/`: Astro routing pages (`index.astro`, `directory/`, `tree/`, `account.astro`, `keys.astro`, `login.astro`, `usage.astro`, `contribute.astro`, `proposals.astro`, `moderate.astro`, `/api/contribute` reader).
- `src/components/`: Reusable Astro components (Account navigation, 3D Canvas, Search).
- `src/layouts/`: Base HTML page layouts.
- `tools/`: Build scripts (`twins.py`, `build_llms.py`).
- `tests/`: Python tests for rendered pages and data pipelines.

## 3. `hub/` — Global AI Hub & Semantic Operations

- `mcp-server/`: `hub_mcp_server.py`; registrations define the current tools.
- `scripts/`:
  - `embed_core.py`: Weighted Ollama embedding pool manager.
  - `docset_indexer.py`: Vector and BM25 indexer.
  - `pipeline_manager.py`: Documentation crawl/mirror pipeline coordinator.
  - `hub_manager/`: Terminal UI management console.
  - `docset_refine/`: Documentation cleaner and fact extractor.
  - `semantic_ops/`: Semantic analysis modules (RRF fusion, ask, symbols, router).
- `tests/`: Hub unit and integration tests.

## 4. `llmsx/` — Standard Library & Specification

- `llmsx/`: Python parser, AST visitor, and generator for llms.txt standard v2.
- `tests/`: Spec compliance tests.

## 5. `.claude/commands/` & `.claude/skills/`

- `.claude/commands/`: CLI command workflows (`lca.md`, `ldo.md`).
- `.claude/skills/`: Agent skill packages (`llms-deep-optimizer`, `llms-concept-abstractor`, `document-formats`).

## 6. `concept-tree/` & `scripts/`

- `concept-tree/`: Holds the semantic concept hierarchy data (`tree.json`).
- `scripts/`: Various standalone utility scripts (e.g., `build_concept_packs.py`, `merge_concept_trees.py`, `refresh_snapshot.sh`).

## Research expertise and lifecycle

- `hub/research-expertise/`: Independently locked Python package and tests.
  - `src/research_expertise/capture.py`: Source-grounded canonical writes.
  - `src/research_expertise/store.py`: Neo4j, CPU embedding cache and retrieval.
  - `src/research_expertise/mcp_server.py`: Bounded MCP contract.
  - `src/research_expertise/explorer.py`: Private data snapshot viewer.
  - `install.py`: Stable installed application outside temporary worktrees.
- `scripts/research_gate.py`, `research_artifact.py`, `research_provenance.py`,
  `research_claims.py`, `research_transaction.py`: Native evidence and commit contracts.
- `scripts/research_site_sync.py`: Website projection and freshness.
- `tests/test_research_*.py`: Native lifecycle regression checks.

The package guide and [wiki entry](subsystems/research-expertise.md) describe
command ownership and preserve the distinction between capture and validation.

## Skill registry and optimizer broker

- `hub/skill-registry/`: independently locked Python package with its own README
  and offline tests; it does not depend on Neo4j, Ollama or a terminal UI.
  - `src/skill_registry/catalog.py`: source inventory, installation aliases and FTS5.
  - `bundles.py`, `publication.py`, `client.py`: complete release validation,
    no-clobber installation and pinned authenticated retrieval.
  - `jobs.py`, `worker.py`, `remote_worker.py`: optional bounded candidate work,
    cancellation, leases and external worker attestations.
  - `cli.py`, `mcp_server.py`, `service.py`: entrypoints and shared service boundary.
- `api/explorer_api/routes/skill_registry.py`: account-scoped immutable releases.
- `api/explorer_api/optimizer_jobs.py` and `routes/optimizer_jobs.py`: hosted broker
  over existing Job/JobEvent tables; no HTTP uploaded-code execution.
- `.github/workflows/skill-registry.yml`: standalone lint/tests using its frozen lock.

See [[skill-registry]] for source authority and worker-boundary traps.

## Native speculative verifier

- `native/speculative-mlx/`: optional independent Go/CGO module.
- `main.go`, `main_test.go`: native block-verification sidecar and its tests.
- `README.md`: hardware/library discovery, protocol, cache boundaries and
  explicitly limited qualification evidence.
- `llmsx/llmsx/speculative/`: Python coordinator and opt-in CLI integration.

These hardware-facing runtimes require their own preflight and acceptance;
repository bootstrap does not start them.
