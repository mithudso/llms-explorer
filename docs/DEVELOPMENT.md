# Development Guide

## Prerequisites

- Python 3.13+ with `uv`
- Node.js 22.18+ with `npm`
- PostgreSQL 16 (for `api/` tests and local development)
- Ollama (optional, for local embedding / generation models)

## Environment Setup

1. Copy `.env.example` to your environment:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/explorer_dev"
   export SESSION_SECRET="a-very-long-secret-key-at-least-32-characters"
   export STRIPE_SECRET_KEY="sk_test_..."
   export STRIPE_WEBHOOK_SECRET="whsec_..."
   ```

2. Setup API virtual environment:
   ```bash
   cd api
   uv sync --extra test
   ```

3. Setup Hub virtual environment:
   ```bash
   uv venv hub/.venv --python 3.13
   uv pip install --python hub/.venv/bin/python -r hub/requirements-dev.txt -r hub/mcp-server/requirements.txt
   ```

4. Setup Frontend dependencies:
   ```bash
   cd site
   npm install
   ```

## Running Services

- **API**:
  ```bash
  cd api
  uv run uvicorn explorer_api.main:app --reload --port 8000
  ```

- **Frontend**:
  ```bash
  cd site
  npm run dev
  ```

- **Hub Manager (TUI)**:
  ```bash
  ./hub/scripts/hub-manager
  ```

## Running Verification

```bash
# Backend tests
uv run --directory api --extra test pytest

# Hub tests
HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests

# llmsx tests
uv run --directory llmsx pytest

# Frontend tests & build
hub/.venv/bin/python -m pytest site/tests
cd site && npm run build

# Linting
uvx ruff check api
uvx ruff check hub
```

The hub requirements include the private `mithudso/ollama-client` and
`mithudso/llms-txt` libraries. Installation needs authorized Git access. The hub's
`pyproject.toml` contains tool configuration, not an installable `[project]`;
`uv sync` cannot install its requirements. Installing dependencies does not
authorize starting indexing, inference or paused background jobs.

## Standalone research expertise

```sh
uv sync --directory hub/research-expertise --frozen
uv run --directory hub/research-expertise --frozen pytest -q
uv run --directory hub/research-expertise --frozen ruff check src tests install.py
```

These offline unit tests use temporary packs and fake embeddings. Neo4j, model
downloads and production corpus writes are not prerequisites. Installation,
capture, reingestion and model migration are separate operations documented in
[the package guide](../hub/research-expertise/README.md).
