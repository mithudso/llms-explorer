# Contributing to LLMS-Explorer

Thank you for contributing to LLMS-Explorer!

## Development Workflow

1. **Clone and Setup**:
   - Python dependencies: managed with `uv`.
   - Node/Astro frontend: `npm install` inside `site/`.
2. **Testing**:
   - Backend tests: `uv run --directory api --extra test pytest`
   - Hub tests: `uv run --directory hub pytest`
   - Frontend tests: `uv run --directory hub pytest ../site/tests`
   - Frontend build: `cd site && npm run build`
3. **Linting**:
   - `uv run --directory api ruff check .`
   - `uv run --directory hub ruff check .`
4. **Submitting Changes**:
   - Ensure all tests pass.
   - Open a Pull Request with a clear summary and verification checklist.
