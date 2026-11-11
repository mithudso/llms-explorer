# LLMSX

The toolkit for AI coding agents: terminal workbenches, bounded convergence skills and source-linked context libraries.

Choose a skill, run a local workbench or download a portable .llms context pack. Inspect the examples, source links and limits before use.

- Website: https://llmsx.org/
- Agent skills: https://llmsx.org/skills/
- Terminal workbenches (`llmsx`, `skillsx`, `ghx`): https://llmsx.org/apps/
- Agent context libraries: https://llmsx.org/context/
- Concept tree: https://llmsx.org/tree/
- Guides and empirical research: https://llmsx.org/workflows/ and https://llmsx.org/blog/
- Full offering map and requirements: https://llmsx.org/toolkit/

```sh
npx skills add https://github.com/mithudso/llms-explorer/tree/main/.claude/skills/code-deep-optimizer --skill code-deep-optimizer
```

The explicit directory selects the source prompt shown on the website. Check the
skill's prerequisites and stopping conditions before running it. Public context
packs require no model or credentials; advanced corpus rendering is an optional
integration with separate repository access.

## Monorepo Structure

| Component | Description |
|---|---|
| `api/` | FastAPI backend handling PostgreSQL ledger, WebAuthn/OAuth auth, API keys, and metering. |
| `site/` | Astro + TypeScript frontend (plain CSS): directory, 3D concept graph, and browser account portals. |
| `hub/` | Global AI Hub semantic operations, docset refiner, vector/keyword indexing, and MCP server. |
| `hub/research-expertise/` | Standalone canonical research capture, Neo4j graph and CPU semantic retrieval through a bounded MCP interface. |
| `hub/skill-registry/` | Standalone source-bound skill lookup, immutable private/team releases and bounded optional optimizer workers. |
| `llmsx/` | Python library and CLI for parsing, validating, and generating `llms.txt` standard v2 files. |
| `concept-tree/` | Canonical hierarchical topic data (`tree.json`) that powers the 3D graph and topical navigation. |
| `native/speculative-mlx/` | Optional Apple Silicon/CGO verifier sidecar; separate hardware/runtime prerequisites and qualification limits. |
| `scripts/` | Python and shell utilities for tasks like tree merging, indexing, and snapshot refreshing. |
| `docs/` | Complete documentation suite detailing architecture, components, and workflows. |
| `.claude/commands/` & `.claude/skills/` | Pre-configured agent instructions (`/ldo`, `/lca`) and semantic skills. |

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
uv venv hub/.venv --python 3.13
uv pip install --python hub/.venv/bin/python -r hub/requirements-dev.txt -r hub/mcp-server/requirements.txt
# Launch TUI
hub/scripts/hub-manager
```

### Verifying the Setup
```bash
# Verify API
uv run --directory api --extra test pytest

# Verify Hub
HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests

# Verify llmsx
uv run --directory llmsx pytest

# Verify Site
cd site && npm run build
```

## Documentation
- [Maintained documentation wiki](docs/index.md): navigation and source verification rules.
- [Research expertise](hub/research-expertise/README.md): local capture, graph/semantic retrieval and MCP.
- [Skill registry](hub/skill-registry/README.md): lexical lookup, pinned bundles, hosted account access and optional local workers.
- `docs/ARCHITECTURE.md`: High-level system design.
- `docs/DEVELOPMENT.md`: Prerequisites and environment setup.
- `docs/COMPONENTS.md`: Catalog of all subsystems.
- `docs/TESTING.md`: Test suite strategies.
- `docs/codebase-overview.md`: Map of the entire repository.
