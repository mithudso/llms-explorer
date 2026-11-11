# Gemini Assistant Instructions for LLMS-Explorer

Adhere to the following repo rules:
1. **Caveman Mode**: Extreme brevity, technical density, diffs only for code changes, no conversational filler.
2. **Verify Always**: Run `uv run --directory api --extra test pytest`, `HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests`, and `cd site && npm run build` to verify changes.
3. **Ledger Guarantees**: Preserve Postgres `Numeric(12,6)` precision and append-only database triggers.
