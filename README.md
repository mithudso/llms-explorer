# llms-explorer

Everything from the `llms.txt` line of work on the global AI hub, gathered in one place:
the research, the `/ldo` (llms-deep-optimizer) skill, the hub code that acquires, refines,
exports, serves, lints and indexes llms files, the MCP wiring, the tests, and the outputs
produced on the estate (2026-08-30/31).

Nothing here runs on its own — the hub (`~/.global-ai-hub`) is the runtime. This repo is the
readable, diffable record of what was built and what it produced.

## Layout

| Path | What |
|---|---|
| `skills/llms-deep-optimizer/` | the `/ldo` skill: `SKILL.md` + `references/` (attribute rubric, passes P0–P15, llms-vs-skill files, resources/tooling, facts→topical how-to) |
| `skills/document-formats/references/llms-txt*.md` | the `/dr` research spokes: spec v2, generation tooling, ecosystem evidence, recreation & aggregation |
| `skills/deep-optimizer-router-SKILL.md` | the optimizer family router that routes to `/ldo` |
| `commands/ldo.md` | the `/ldo` alias |
| `hub/scripts/` | `llms_acquire.py` (acquisition ladder + grammars), `docset_refine/` (clean → extract → units → render → `export_llms` incl. hub-and-spoke split, `topical`, `vocabulary`), `llms_lint.py` (deterministic passes, CI gate), `llms_serve.py` (`/llms.txt`, `/d/…`, `/m/…`, `/t/…`), `llms_full_catalog.py` (766-site mirror), `docset_indexer.py` (vector + FTS5 keyword layers), `docset_rollout.py` (lint gate), `pipeline_manager.py` |
| `hub/mcp-server/hub_mcp_server.py` + `hub/mcp.json`, `hub/libraries/mcp-library/registry.json`, `hub/docs/MCP.md` | MCP tools: `hub_docset_index`, `hub_query_docset(mode=semantic|keyword|hybrid)`, `hub_llms_full_list/read`, … |
| `hub/scripts/launchd/` | `llms-serve`, `llms-full-refresh`, `topical-refresh` agents |
| `hub/tests/` | the hermetic tests for all of the above |
| `hub/docs/specs/`, `hub/docs/plans/` | design docs: docset reference extraction, golden baseline, llms.txt as the docset schema, the conceptual (concept-axis) llms family |
| `outputs/exports/<stem>.llms/` | 15 docsets exported as `llms.txt` (split into `<section>/llms.txt` when > 10 KB), `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, `manifest.json` |
| `outputs/llms-full-catalog/` | catalog + manifest of every site known to publish `llms-full.txt` (the 722 MB of downloaded files stay on the hub) |
| `outputs/llms-topical/` | topical (concept-axis) llms files built from fact pools |
| `research/dr-llms/` | raw `/dr` research notes, spec snapshots, golden question sets and gate results |
| `research/pipeline/` | the 2026-08-18 extraction research (rerank, RRF, dedup, boilerplate, zero-shot extraction) |
| `evals/` | persisted `/ldo` question banks |
| `concept-tree/tree.json` | the concept tree snapshot (family definitions, `llmsFile` pointers) |
| `logs/` | `prompts-hub.md` / `memory-hub.md` — the request/decision log of the hub track |

## The shape of it

- **Source axis** — per site: `llms.txt` (index, ≤ 10 KB or hub-and-spoke) → `llms-full.txt` /
  `llms-small.txt` (text ladder with token counts) → `llms-facts.txt` (typed, source-anchored
  units). Every layer is generated from the mirror; hand edits go into the generator's inputs.
- **Concept axis** — topical files (`docset_refine topical`) regroup the same units by
  concept-tree node; the hub root `/llms.txt` is the categorical view.
- **Retrieval** — every facts layer is embedded (vector) and FTS5-indexed (keyword); `hub_ask`
  fuses them; `hub_query_docset(mode="keyword")` is the no-embedding cheap path.
- **Quality bar** — `skills/llms-deep-optimizer/references/attributes.md` is the rubric;
  `llms_lint.py` runs the deterministic passes; `docset_rollout.py cleanup` is the gate
  (0 High across 15 docsets / 652 files at snapshot time).

## Running the code

Clone the hub, not this repo — paths in `hub/` are copies of `~/.global-ai-hub/scripts/…`.
`hub/tests/` run there with `.venv/bin/python -m pytest tests/ -q`.
