# Repository Agent Catalog

## Task completion

Follow [the task delivery rule](docs/agent-task-completion.md). Completed work must
be verified, committed, pushed, opened as a PR, and merged into the remote default
branch without another routine permission request. Preserve other active work.

| Agent Name | Scope | Description | Tools / Commands |
|---|---|---|---|
| `code-deep-optimizer` | Entire repo | Multi-pass static code optimizer, lint, security, and verification loop. | `uv`, `ruff`, `pytest`, `npm` |
| `repo-bootstrapper` | Entire repo | Standards maintainer, doc suite generator, operations infrastructure. | `bash`, file operations |
| `llms-deep-optimizer` (`/ldo`) | `hub/`, `site/` | Analyzes and optimizes llms.txt files and docsets against standard grammars. | `scripts/llms_lint.py`, `docset_refine` |
| `llms-concept-abstractor` (`/lca`) | `concept-tree/`, `outputs/` | Extracts concept packs, structures topical hierarchies, builds vocabulary. | `concept_tree.py`, `docset_refine` |
| `api-maintainer` | `api/` | FastAPI backend, Alembic migrations, database models, Stripe billing. | `pytest`, `alembic`, `uvicorn` |
| `site-builder` | `site/` | Astro UI, plain CSS styling, 3D visualization, twin page generators. | `npm`, `astro` |

<!-- llms-routing:pointer --> See `## llms routing` in CLAUDE.md for the llms files and quick answers.

## Research scout handoffs

Before `/dr` queue discovery or `concept-family-explorer` frontier discovery,
check private candidate leads under `$HOME/.global-ai-hub/research/.scouts/`.
Use `.claude/skills/research-scout/scripts/scout.py find` with the exact concept
and parent when known. Read `.claude/skills/research-scout/references/handoff.md`
before consuming a bundle. Scout output is unverified: recheck the live
inventory, acquire readable source text, and keep the research workflow's
origin, claim, CVS and completion gates. Read the scout's consumer reference:
the Codex research adapter loads bounded seeds automatically; Claude uses the
scout research bridge. Other headless runners still need an explicit seed handoff.
