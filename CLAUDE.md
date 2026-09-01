# LLMS-Explorer

Monorepo for the LLMS-Explorer platform: accounts, metering, hosted MCP gateway, Global AI context hub, semantic search, docset refiner, and Astro documentation portal.

## Packages and Components

- `api/`: FastAPI backend with PostgreSQL ledger, WebAuthn/OAuth auth, API keys (Argon2id), Stripe subscriptions, and quota enforcement.
- `site/`: Astro + TypeScript + Tailwind static & SSR website, directory, 3D concept graph, and account pages.
- `hub/`: Global AI Hub semantic ops, ChromaDB/SQLite docsets, Ollama embedding pools, MCP server (`global_ai_hub`).
- `llmsx/`: Python library and CLI for the llms.txt standard v2.
- `commands/` & `skills/`: Agent commands and workflows (`/ldo`, `/lca`).

## Commands

### API (`api/`)
- Run tests: `uv run --directory api --extra test pytest`
- Run dev server: `cd api && uvicorn explorer_api.main:app --reload`
- Migrations: `cd api && alembic upgrade head`
- Lint: `uv run --directory api ruff check .`

### Hub (`hub/`)
- Run tests: `uv run --directory hub pytest`
- Run MCP server (stdio): `uv run --directory hub python mcp-server/hub_mcp_server.py`
- Run TUI manager: `hub/scripts/hub-manager`
- Lint: `uv run --directory hub ruff check .`

### Site (`site/`)
- Install deps: `cd site && npm install`
- Dev server: `cd site && npm run dev`
- Build: `cd site && npm run build`
- Site tests: `uv run --directory hub pytest ../site/tests`

## Architecture Constraints

1. **Zero Float Math for Money**: Always use `Decimal` / `Numeric(12,6)` in Postgres and Python models.
2. **Append-Only Ledger**: The `ledger` table has database-level `BEFORE UPDATE` and `BEFORE TRUNCATE` triggers. Corrections are new rows.
3. **No Hardcoded Secrets**: Secrets must come from the environment (see `.env.example`).
4. **Strict Type Safety & Verification**: Verify all changes with automated test suites before claiming completion.

## Workflow Log Rule
Maintain `memory.md` and `prompts.md` with active tasks, versions, and prompt histories.
