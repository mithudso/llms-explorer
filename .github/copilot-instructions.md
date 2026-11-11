## Default Execution Strategy

When executing tasks in this codebase, adhere strictly to the following standards:

1. **Read Before Editing**: Read relevant source, instructions and continuation records. Never invent commands or paths.
2. **Verify Before Completion**: Run automated tests (`uv run --directory api --extra test pytest`, `HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests`, `npm run build` in `site/`) and linters before claiming any task is complete.
3. **Architecture Integrity**:
   - `api/`: FastAPI + SQLAlchemy Async + Postgres ledger/billing/auth service. Follow strict type safety, zero float math for money (`Decimal` / `Numeric(12,6)`), append-only ledger guarantees.
   - `site/`: Astro + TypeScript static & SSR pages. Maintain build cleanliness, run postbuild generation scripts.
   - `hub/`: Global AI Hub semantic ops, ChromaDB/SQLite docsets, Ollama embedding pools, MCP server.
   - `llmsx/`: Python tooling and specifications for llms.txt.
4. **Security & Secrets**: Never hardcode secrets or write them to repository files. Respect trust boundaries, Argon2id password hashing, and WebAuthn relying party constraints.
5. **Clean Diffs & Conventions**: Minimize unrelated whitespace changes; preserve docstrings and architectural notes.

6. **Workflow Log**: Store each user request in `prompts.md`; update versioned
   `memory.md` with completed work, active ownership and concrete next steps.

## Build, Test, and Validation Commands

Use [development setup](../docs/DEVELOPMENT.md) for isolated dependencies and
[testing guidance](../docs/TESTING.md) for the owning package's exact commands.
The hub uses requirements files; the standalone expertise package uses its own
frozen lockfile. Preserve paused indexing/inference and unrelated changes.

## High-level Architecture

[The component catalog](../docs/COMPONENTS.md) describes the API, site, hub,
llmsx and research expertise package. Canonical research packs remain authoritative;
Neo4j and semantic indexes are derived projections.

## Key Conventions

- Use exact source spans and immutable hashes for evidence.
- Keep capture integrity separate from semantic qualification.
- Preserve existing research receipts and publication exclusions.
- Use the owning package's isolated test environment.
- Keep stdout clean for stdio MCP; diagnostics go to stderr.
- Verify installed behavior separately from source tests when changing it.
