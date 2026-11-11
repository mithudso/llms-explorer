# Contributing to LLMS-Explorer

Thank you for contributing to LLMS-Explorer!

## Development Workflow

1. **Clone and Setup**:
   - Python dependencies: managed with `uv`.
   - Node/Astro frontend: `npm install` inside `site/`.
2. **Testing**:
   - Backend tests: `uv run --directory api --extra test pytest`
   - Hub tests: `HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests`
   - Frontend tests: `hub/.venv/bin/python -m pytest site/tests`
   - Frontend build: `cd site && npm run build`
3. **Linting**:
   - `uvx ruff check api`
   - `uvx ruff check hub`
4. **Submitting Changes**:
   - Ensure all tests pass.
   - Open a Pull Request with a clear summary and verification checklist.

See [development setup](docs/DEVELOPMENT.md) for isolated dependencies and private library access. The standalone [research expertise package](hub/research-expertise/README.md) has its own frozen environment, tests and linter.
