# LLMS-Explorer site — design specs

Design only (2026-08-31); nothing here is implemented. Start with `00-platform-design.md`, then
the component you care about. Every component file uses the same 12-section skeleton
(purpose → flows → contracts → architecture → surfaces → UI → data → tiering → acceptance →
security/rights → dependencies → open questions).

| # | Component | File |
|---|---|---|
| 00 | Platform: product, principles, architecture, stores, jobs, surfaces, tiering, build order | `00-platform-design.md` |
| 01 | llms linter / optimizer (`/ldo`) | `components/01-llms-linter.md` |
| 02 | Notes/docs → LLMS | `components/02-notes-to-llms.md` |
| 03 | Reference: formatting, reasoning, usage, ethos | `components/03-reference.md` |
| 04 | Blog: implementation write-ups | `components/04-blog.md` |
| 05 | Conceptual/topical LLMS vs proprietary — "the most correct idea overwrites" | `components/05-conceptual-vs-proprietary.md` |
| 06 | Concept abstraction (`/lca`) | `components/06-concept-abstraction.md` |
| 07 | Deepen: a frontier research wave on a concept (`/dr`) | `components/07-deepen.md` |
| 08 | Concept family explorer (`concept-family-explorer`) | `components/08-concept-family-explorer.md` |
| 09 | **Concept family tree explorer** — MCP, 3D visualizer, TUI (9a), CLI/API/web (9b) — the titular app | `components/09-concept-family-tree-explorer.md` |
| 10 | Directory of known llms files + conformance | `components/10-directory.md` |
| 11 | V2 vs V1 (spec and hub pipeline) | `components/11-v2-vs-v1.md` |
| 12 | LLMS vocabulary files | `components/12-vocabulary.md` |
| 13 | MCP server: local or hosted, contribute | `components/13-mcp-server-hosting.md` |
| 14 | Coding examples: how and when to use an LLMS | `components/14-coding-examples.md` |
| 15 | Accounts and billing | `components/15-accounts-and-billing.md` |
| 16 | Semantic indexing + LLMS: introduction and demo | `components/16-semantic-indexing-intro.md` |
| 17 | Semantic indexer: models, what happens, reproduce it | `components/17-semantic-indexer.md` |

Sources these specs are grounded in: `skills/llms-deep-optimizer/references/*`,
`skills/document-formats/references/llms-txt*.md`, `hub/docs/specs/*`, `hub/scripts/*`,
`hub/mcp-server/hub_mcp_server.py`, `outputs/*`, the `llms-concept-abstractor` skill
(`~/.claude/skills/llms-concept-abstractor/`), `concept-family-explorer`, and
github.com/mithudso/json-3d-renderer.
