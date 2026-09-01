# Runbook: Local Development

## Starting Local Development Environment

1. **Start PostgreSQL**:
   ```bash
   brew services start postgresql@16
   ```

2. **Run Backend API**:
   ```bash
   cd api
   uv run uvicorn explorer_api.main:app --reload --port 8000
   ```

3. **Run Frontend**:
   ```bash
   cd site
   npm run dev
   ```

4. **Verify Health**:
   - `curl http://localhost:8000/health`
   - Open browser at `http://localhost:4321`
