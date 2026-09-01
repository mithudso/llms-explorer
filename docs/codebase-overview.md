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
  - `routes/`: Sub-routers for `auth`, `keys`, `usage`, `billing`, `mcp`, `trees`, `proposals`, `artifacts`.
- `alembic/`: Database migrations.
- `tests/`: 232 hermetic unit and integration tests.

## 2. `site/` — Astro Frontend & Explorer Portal

- `src/pages/`: Astro routing pages (`index.astro`, `directory/`, `tree/`, `account.astro`, `keys.astro`, `login.astro`, `usage.astro`).
- `src/components/`: Reusable Astro/React components (Account navigation, 3D Canvas, Search).
- `src/layouts/`: Base HTML page layouts.
- `tools/`: Build scripts (`twins.py`, `build_llms.py`).
- `tests/`: 139 Python tests verifying rendered pages and data pipelines.

## 3. `hub/` — Global AI Hub & Semantic Operations

- `mcp-server/`: `hub_mcp_server.py` exposing 18 MCP tools.
- `scripts/`:
  - `embed_core.py`: Weighted Ollama embedding pool manager.
  - `docset_indexer.py`: Vector and BM25 indexer.
  - `pipeline_manager.py`: Documentation crawl/mirror pipeline coordinator.
  - `hub_manager/`: Terminal UI management console.
  - `docset_refine/`: Documentation cleaner and fact extractor.
  - `semantic_ops/`: Semantic analysis modules (RRF fusion, ask, symbols, router).
- `tests/`: 265 unit and integration tests.

## 4. `llmsx/` — Standard Library & Specification

- `llmsx/`: Python parser, AST visitor, and generator for llms.txt standard v2.
- `tests/`: Spec compliance tests.

## 5. `commands/` & `skills/`

- `commands/`: CLI command workflows (`lca.md`, `ldo.md`).
- `skills/`: Agent skill packages (`llms-deep-optimizer`, `llms-concept-abstractor`, `document-formats`).
