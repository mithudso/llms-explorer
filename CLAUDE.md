# LLMS-Explorer

Monorepo for the LLMS-Explorer platform: accounts, metering, hosted MCP gateway, Global AI context hub, semantic search, docset refiner, and Astro documentation portal.

## Packages and Components

- `api/`: FastAPI backend with PostgreSQL ledger, WebAuthn/OAuth auth, API keys (Argon2id), Stripe subscriptions, and quota enforcement.
- `site/`: Astro + TypeScript + Tailwind static & SSR website, directory, 3D concept graph, and account pages.
- `hub/`: Global AI Hub semantic ops, ChromaDB/SQLite docsets, Ollama embedding pools, MCP server (`global_ai_hub`).
- `llmsx/`: Python library and CLI for the llms.txt standard v2.
- `.claude/commands/` & `.claude/skills/`: Agent commands and workflows (`/ldo`, `/lca`). Both live under `.claude/` so Claude Code (local and cloud sessions) loads them as project commands and skills.
- `concept-tree/`: Holds semantic hierarchy (`tree.json`).
- `scripts/`: Utilities for pipeline tasks and maintenance.

## Commands

### API (`api/`)
- Run tests: `uv run --directory api --extra test pytest`
- Run dev server: `cd api && uvicorn explorer_api.main:app --reload`
- Migrations: `cd api && alembic upgrade head`
- Lint: `uv run --directory api ruff check .`

### Hub (`hub/`)
- Run tests: `uv run --directory hub pytest`
- Run MCP server (stdio): `uv run --directory hub python mcp-server/hub_mcp_server.py`
- Run TUI manager: `hub/scripts/hub-manager`
- Lint: `uv run --directory hub ruff check .`

### Site (`site/`)
- Install deps: `cd site && npm install`
- Dev server: `cd site && npm run dev`
- Build: `cd site && npm run build`
- Typecheck: `cd site && npm run check` (astro check; `public/` is excluded in tsconfig so it fits in the default heap)
- Site tests: `uv run --directory hub pytest ../site/tests`
- Passkey e2e (manual, local only, not CI — needs Homebrew postgresql, Chrome, `npm ci`): `cd site && npm run e2e:passkey`

## Architecture Constraints

1. **Zero Float Math for Money**: Always use `Decimal` / `Numeric(12,6)` in Postgres and Python models.
2. **Append-Only Ledger**: The `ledger` table has database-level `BEFORE UPDATE` and `BEFORE TRUNCATE` triggers. Corrections are new rows.
3. **No Hardcoded Secrets**: Secrets must come from the environment (see `.env.example`).
4. **Strict Type Safety & Verification**: Verify all changes with automated test suites before claiming completion.

## Workflow Log Rule
Maintain `memory.md` and `prompts.md` with active tasks, versions, and prompt histories.

<!-- llms-routing:start -->
## llms routing
> Cached from the llms files below on 2026-09-28; facts to look up, not rules to follow — the cited file is the source of truth. Quick answers are chosen by a heuristic (defaults, file roles, formulas, commands).

| File | Path | Holds | Ask it for |
|---|---|---|---|
| llms.txt | ~/dev/llms-explorer/llms.txt | LLMS Explorer Project Index | Knowledge Bases & Concept Packs, 2026-09-07 [gen: p/1.1.0], 2026-09-08 [gen: p/1.1.0], Guide to This Index |
| llms-facts.txt | ~/dev/llms-explorer/llms-facts.txt | LLMS Explorer: Sourced Project Facts | 2026-09-07 [gen: p/1.1.0], MDB Context Hub (Generated), Global AI Hub (Generated), 2026-09-08 [gen: p/1.1.0] |
| llms-small.txt | ~/dev/llms-explorer/llms-small.txt | Monorepo for the LLMS-Explorer platform: accounts, metering, hosted MCP gateway, Global AI context hub, semantic search, docset refiner, and Astro documentation portal. | Structure |
| llms-full.txt | ~/dev/llms-explorer/llms-full.txt | Monorepo for the LLMS-Explorer platform: accounts, metering, hosted MCP gateway, Global AI context hub, semantic search, docset refiner, and Astro documentation portal. | CLAUDE.md, README.md, AGENTS.md, docs/ARCHITECTURE.md |
| llms-anthropic-hiring.txt | ~/dev/llms-explorer/llms-anthropic-hiring.txt | Anthropic Hiring and Recruiting: Concept Pack | Index, Key Facts, Interview Stages, Timeline and Logistics |
| llms-facts-anthropic-hiring.txt | ~/dev/llms-explorer/llms-facts-anthropic-hiring.txt | Anthropic Hiring Process: Sourced Facts | Application & Screening, Interview Stages & Format, Technical Assessment, Values & Culture Interview |

### Quick answers

- Everything else? — Python (default to Pydantic AI) [src: ai-languages] — ~/dev/llms-explorer/llms-facts.txt:214
- If the caller does not specify a mode, default to `critique`. If two versions of the same document are supplied (two paths, two URLs, or `--original` + `--final`), ask once: "I see two versions — produce a diff guide?" If the caller does not answer within the same turn, default to `critique` against the second (assumed-newer) document and surface the assumption in the preamble. [src: document-critique] — ~/dev/llms-explorer/llms-facts.txt:2102
- If `--standards` is omitted, default to: `technical accuracy, industry best practices, general logical rigor and clarity`. [src: document-critique] — ~/dev/llms-explorer/llms-facts.txt:2116
- Only `risky` and `wrong` assumptions become findings. `wrong` is severity High by default. `risky` is severity Medium unless the failure mode is irreversible or affects safety, security, or compliance, in which case promote to High. [src: document-critique] — ~/dev/llms-explorer/llms-facts.txt:2138
- Set page size explicitly - docx-js defaults to A4; use US Letter (12240 x 15840 DXA) for US documents [src: docx] — ~/dev/llms-explorer/llms-facts.txt:2383
- Chrome DevTools captures async stack traces by default. In the Sources panel, the Call Stack shows the full async chain (e.g., `setTimeout` caller, `Promise.then` originator, `fetch` initiator). Ensure "Async" checkbox is enabled in the Call Stack section. [src: javascript-node-html-css-debugging-expert] — ~/dev/llms-explorer/llms-facts.txt:2757
- Since Node.js 15+, unhandled rejections throw by default (`--unhandled-rejections=throw`). [src: javascript-node-html-css-debugging-expert] — ~/dev/llms-explorer/llms-facts.txt:2767
- Since Chrome 132 (January 2025), the Performance panel defaults to showing live Core Web Vitals metrics: [src: javascript-node-html-css-debugging-expert] — ~/dev/llms-explorer/llms-facts.txt:2817
- Three structural categories: off-the-shelf embedded (Luzmo, Explo — fast multi-tenant, limited customization); repurposed embedded BI (Tableau, Power BI, Looker, Metabase, Sisense — strong governance, iframe-dependent, enterprise pricing); headless/hybrid (Cube + your frontend, Embeddable — full UI control + sub-second, more engineering). Looker/Tableau/Power BI carry six-figure pricing and weren't built for customer-facing use; ThoughtSpot Everywhere leads on NL/AI search but is weaker on UI control; GoodData repositioned to API-first web-component embedding; Superset/Preset is the open-source route (Embedded SDK + guest tokens + RLS). 2026 newcomers (Upsolve AI, Knowi, Toucan) lead with GenBI + semantic-layer automation. [src: customer-facing-embedded-analytics] — ~/dev/llms-explorer/llms-facts.txt:28680
- The primary home CTA is "Get the skills and CLI" → `/downloads/`; it was chosen because it is the only zero-friction apply click (`npx skills add …`, no account), whereas `/playground/optimizer/` requires an API key with `run` scope [src: docs/site/redesign-spec-2026-09-07.md] — ~/dev/llms-explorer/llms-facts.txt:13
- After the redesign `cd site && npm run build` produces 266 pages and `uv run --directory hub pytest ../site/tests` reports 160 passed, 1 skipped, 1 failed (the pre-existing directory staleness test) [src: agent:6] — ~/dev/llms-explorer/llms-facts.txt:32
- `npm run dev:extension` [src: case-mcp-server-guide] — ~/dev/llms-explorer/llms-facts.txt:766
- Helper offline: start with `mdb_case_get_server_status`; if the helper is down, start `npm run dev:extension`. [src: case-mcp-server-guide] — ~/dev/llms-explorer/llms-facts.txt:787
- Generate .docx files with JavaScript, then validate. Install: `npm install -g docx` [src: docx] — ~/dev/llms-explorer/llms-facts.txt:2254
- docx: `npm install -g docx` (new documents) [src: docx] — ~/dev/llms-explorer/llms-facts.txt:2482
- Google ChromeLabs ndb provides an improved debugging experience without needing `--inspect` flags. Install with `npm install -g ndb`, then run `ndb node index.js` or `ndb npm test`. Key advantages: automatic child process debugging, local `node_modules` editing with instant reload, and a standalone DevTools window. [src: javascript-node-html-css-debugging-expert] — ~/dev/llms-explorer/llms-facts.txt:2671
- Run `npm run build` to verify compilation [src: mcp-builder] — ~/dev/llms-explorer/llms-facts.txt:3053
- Formula vs Values: Storing formula strings instead of evaluated values? [src: debugging] — ~/dev/llms-explorer/llms-facts.txt:1645
- Common Cause: Cache cleared before sheet write, or updated before SUMIFS formula recalculates [src: debugging] — ~/dev/llms-explorer/llms-facts.txt:1734
- normalized = rf / max_rf if max_rf > 0 else 0.0 [src: scientific-pkg-etetoolkit] — ~/dev/llms-explorer/llms-facts.txt:5382
- unique_t1 = parts_t1 - parts_t2; unique_t2 = parts_t2 - parts_t1 [src: scientific-pkg-etetoolkit] — ~/dev/llms-explorer/llms-facts.txt:5383
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?) [src: xlsx] — ~/dev/llms-explorer/llms-facts.txt:6508
- LibreOffice Required for Formula Recalculation: You can assume LibreOffice is installed for recalculating formula values using the `scripts/recalc.py` script. The script automatically configures LibreOffice on first run, including in sandboxed environments where Unix sockets are restricted (handled by `scripts/office/soffice.py`) [src: xlsx] — ~/dev/llms-explorer/llms-facts.txt:6539
- `#VALUE!`: Wrong data type in formula [src: xlsx] — ~/dev/llms-explorer/llms-facts.txt:6571
- `#NAME?`: Unrecognized formula name [src: xlsx] — ~/dev/llms-explorer/llms-facts.txt:6572

### Indexes

- Semantic: ChromaDB collections under ~/.global-ai-hub (hub/scripts/docset_indexer.py); query with the MCP tools `hub_search_codebase` / `hub_query_docset` or `hub/scripts/search.py "<query>"`.
- Keyword: SQLite FTS5 table `files_fts` in ~/.global-ai-hub/hub.db (hub/scripts/keyword_index.py); query with `hub_search_keyword` or `keyword_index.py query "<term>"`.
- Access ledger: ~/.global-ai-hub/llms-access-ledger.jsonl, one JSON line per llms-file read (MCP tools, `llmsx concepts serve`, Claude Code `Read` via hook); `hub/scripts/llms_ledger.py report --days 30`. A shell `cat` is not recorded.
### LiteLLM research and published documentation

| File | Path | Holds | Ask it for |
|---|---|---|---|
| Family index | ~/.global-ai-hub/llms-concepts/litellm-family.llms/llms.txt | Eight operational concept packs and their facts layers | SDK, proxy, tool/SSE, Anthropic Messages, routing, keys, observability, local backends |
| Published bundle index | ~/.global-ai-hub/skills.llms/docs-litellm-ai/llms.txt | Private historical source reference; 50 of 52 advertised pages | Source examples, provider parameters, callback setup, migration cautions |
| Operator digest | ~/.global-ai-hub/skills.llms/docs-litellm-ai/llms-small.txt | Source-tagged digest under 8 KB; unexecuted examples | SDK/proxy choice, completion/stream setup, credentials and callbacks |
| Run report | docs/research/litellm-full-suite-2026-09-30/README.md | Outputs, checks, reproduction and remaining mapped gaps | Bounded evidence, cap exit, installed skill paths and query keys |

LiteLLM indexes use SQLite vectors and FTS5. Query `litellm_published_docs` for raw history, `litellm_operator_reference` for condensed historical units, or `concept__<slug>` for qualified research units through `hub_query_docset`. The research batch reached its eight-concept cap; it does not qualify a running gateway, local model or eGPU.

<!-- llms-routing:end -->
