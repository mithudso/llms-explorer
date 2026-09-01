## Default Execution Strategy

When executing tasks in this codebase, adhere strictly to the following standards:

1. **Verify Before Completion**: Run automated tests (`uv run --directory api --extra test pytest`, `uv run --directory hub pytest`, `npm run build` in `site/`) and linters before claiming any task is complete.
2. **Architecture Integrity**:
   - `api/`: FastAPI + SQLAlchemy Async + Postgres ledger/billing/auth service. Follow strict type safety, zero float math for money (`Decimal` / `Numeric(12,6)`), append-only ledger guarantees.
   - `site/`: Astro + TypeScript static & SSR pages. Maintain build cleanliness, run postbuild generation scripts.
   - `hub/`: Global AI Hub semantic ops, ChromaDB/SQLite docsets, Ollama embedding pools, MCP server.
   - `llmsx/`: Python tooling and specifications for llms.txt.
3. **Security & Secrets**: Never hardcode secrets or write them to repository files. Respect trust boundaries, Argon2id password hashing, and WebAuthn relying party constraints.
4. **Clean Diffs & Conventions**: Minimize unrelated whitespace changes; preserve docstrings and architectural notes.
