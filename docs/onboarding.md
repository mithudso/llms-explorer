# Contributor Onboarding

Welcome to LLMS-Explorer! Follow this guide to set up your environment in under 10 minutes.

## 1. Install Tools

Ensure you have installed:
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js 20](https://nodejs.org/) & npm
- [PostgreSQL](https://www.postgresql.org/) (optional if running tests, `conftest.py` locates `initdb`)

## 2. Clone and Bootstrap

```bash
git clone git@github.com:mithudso/llms-explorer.git
cd llms-explorer

# API setup
cd api && uv sync --extra test && cd ..

# Hub setup
cd hub && uv sync && cd ..

# Frontend setup
cd site && npm ci && cd ..
```

## 3. Run Checks

```bash
# Verify everything passes
uv run --directory api --extra test pytest
uv run --directory hub pytest
cd site && npm run build
```
