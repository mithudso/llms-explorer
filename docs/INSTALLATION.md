# Installation Guide

## System Requirements

- **Operating System**: macOS (Apple Silicon or Intel) or Linux (Ubuntu 22.04+)
- **Python**: Version 3.13 or 3.14 (managed via `uv`)
- **Node.js**: Version 20 LTS
- **Database**: PostgreSQL 16+

## Step-by-Step Installation

1. **Clone repository**:
   ```bash
   git clone git@github.com:mithudso/llms-explorer.git
   cd llms-explorer
   ```

2. **Install `uv`** (if not present):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Initialize API**:
   ```bash
   cd api
   uv sync --extra test
   cd ..
   ```

4. **Initialize Hub**:
   ```bash
   cd hub
   uv sync
   cd ..
   ```

5. **Initialize Site**:
   ```bash
   cd site
   npm ci
   cd ..
   ```

6. **Database Migration**:
   ```bash
   cd api
   export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/explorer_dev"
   uv run alembic upgrade head
   cd ..
   ```
