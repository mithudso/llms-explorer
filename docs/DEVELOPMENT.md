# Development Guide

## Prerequisites

- Python 3.13+ with `uv`
- Node.js 20+ with `npm`
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
   cd hub
   uv sync
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
uv run --directory hub pytest

# Frontend tests & build
uv run --directory hub pytest ../site/tests
cd site && npm run build

# Linting
uv run --directory api ruff check .
uv run --directory hub ruff check .
```
