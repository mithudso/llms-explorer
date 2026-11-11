# Contributor Onboarding

Welcome to LLMS-Explorer! Follow this guide to set up your environment in under 10 minutes.

## 1. Install Tools

Ensure you have installed:
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js 22.18+](https://nodejs.org/) & npm
- [PostgreSQL](https://www.postgresql.org/) (optional if running tests, `conftest.py` locates `initdb`)

## 2. Clone and Bootstrap

```bash
git clone git@github.com:mithudso/llms-explorer.git
cd llms-explorer

# API setup
cd api && uv sync --extra test && cd ..

# Hub setup
uv venv hub/.venv --python 3.13
uv pip install --python hub/.venv/bin/python -r hub/requirements-dev.txt -r hub/mcp-server/requirements.txt

# Frontend setup
cd site && npm ci && cd ..
```

## 3. Run Checks

```bash
# Verify everything passes
uv run --directory api --extra test pytest
HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests
cd site && npm run build
```

See [development setup](DEVELOPMENT.md) for private library prerequisites and the
separately locked [research expertise package](../hub/research-expertise/README.md).
