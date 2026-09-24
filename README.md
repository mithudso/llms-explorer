# LLMS-Explorer

An integrated platform providing documentation exploration for LLMs, semantic search indexing, accounts/metering infrastructure, and an interactive web portal.

## Monorepo Structure

| Component | Description |
|---|---|
| `api/` | FastAPI backend handling PostgreSQL ledger, WebAuthn/OAuth auth, API keys, and metering. |
| `site/` | Astro + TypeScript + Tailwind frontend: directory, 3D concept graph, and account portals. |
| `hub/` | Global AI Hub semantic operations, docset refiner, vector/keyword indexing, and MCP server. |
| `llmsx/` | Python library and CLI for parsing, validating, and generating `llms.txt` standard v2 files. |
| `concept-tree/` | Canonical hierarchical topic data (`tree.json`) that powers the 3D graph and topical navigation. |
| `scripts/` | Python and shell utilities for tasks like tree merging, indexing, and snapshot refreshing. |
| `docs/` | Complete documentation suite detailing architecture, components, and workflows. |
| `commands/` & `.claude/skills/` | Pre-configured agent instructions (`/ldo`, `/lca`) and semantic skills. |

## Quick Start

### Backend (API)
```bash
cd api
uv sync --extra test
uv run uvicorn explorer_api.main:app --reload --port 8000
```

### Frontend (Site)
```bash
cd site
npm install
npm run dev
```

### Global AI Hub
```bash
cd hub
uv sync
# Launch TUI
./scripts/hub-manager
```

### Verifying the Setup
```bash
# Verify API
uv run --directory api --extra test pytest

# Verify Hub
uv run --directory hub pytest

# Verify llmsx
uv run --directory llmsx pytest

# Verify Site
cd site && npm run build
```

## Documentation
- `docs/ARCHITECTURE.md`: High-level system design.
- `docs/DEVELOPMENT.md`: Prerequisites and environment setup.
- `docs/COMPONENTS.md`: Catalog of all subsystems.
- `docs/TESTING.md`: Test suite strategies.
- `docs/codebase-overview.md`: Map of the entire repository.
