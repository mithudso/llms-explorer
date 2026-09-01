# Repository Agent Catalog

| Agent Name | Scope | Description | Tools / Commands |
|---|---|---|---|
| `code-deep-optimizer` | Entire repo | Multi-pass static code optimizer, lint, security, and verification loop. | `uv`, `ruff`, `pytest`, `npm` |
| `repo-bootstrapper` | Entire repo | Standards maintainer, doc suite generator, operations infrastructure. | `bash`, file operations |
| `llms-deep-optimizer` (`/ldo`) | `hub/`, `site/` | Analyzes and optimizes llms.txt files and docsets against standard grammars. | `scripts/llms_lint.py`, `docset_refine` |
| `llms-concept-abstractor` (`/lca`) | `concept-tree/`, `outputs/` | Extracts concept packs, structures topical hierarchies, builds vocabulary. | `concept_tree.py`, `docset_refine` |
| `api-maintainer` | `api/` | FastAPI backend, Alembic migrations, database models, Stripe billing. | `pytest`, `alembic`, `uvicorn` |
| `site-builder` | `site/` | Astro UI, Tailwind styling, 3D visualization, twin page generators. | `npm`, `astro` |
