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
| `skills/llms-concept-abstractor/` | the `/lca` skill: abstract ONE concept out of any docsets/resources into a concept pack (`SKILL.md` + `references/` relation & facet taxonomies, harvest playbook, output contract, verification + `scripts/concept_abstract.py` keyword harvest · semantic index (ollama, cached) · compile · probe · query) |
| `commands/lca.md` | the `/lca` alias |
| `skills/notes-to-llms/` | the `/n2l` skill: a disordered pile of notes or docs into a spec-v2 llms family that lints 0 High (`SKILL.md` + `references/` v2 grammars & bars, skeleton/unit playbook + `scripts/notes_normalise.py`, stdlib banner-mirror normaliser giving every note a stable `upload://` source and every heading a resolvable anchor) |
| `commands/n2l.md` | the `/n2l` alias |
| `skills/document-formats/references/llms-txt*.md` | the `/dr` research spokes: spec v2, generation tooling, ecosystem evidence, recreation & aggregation |
| `skills/deep-optimizer-router-SKILL.md` | the optimizer family router that routes to `/ldo` |
| `commands/ldo.md` | the `/ldo` alias |
| `hub/scripts/` | `llms_acquire.py` (acquisition ladder + grammars), `docset_refine/` (clean → extract → units → render → `export_llms` incl. hub-and-spoke split, `topical`, `vocabulary`), `llms_lint.py` (deterministic passes, CI gate), `llms_serve.py` (`/llms.txt`, `/d/…`, `/m/…`, `/t/…`, `/c/…` concept packs), `llms_full_catalog.py` (766-site mirror), `docset_indexer.py` (vector + FTS5 keyword layers), `docset_rollout.py` (lint gate), `pipeline_manager.py` |
| `hub/mcp-server/hub_mcp_server.py` + `hub/mcp.json`, `hub/libraries/mcp-library/registry.json`, `hub/docs/MCP.md` | MCP tools: `hub_docset_index`, `hub_query_docset(mode=semantic|keyword|hybrid)`, `hub_llms_full_list/read`, … |
| `hub/scripts/launchd/` | `llms-serve`, `llms-full-refresh`, `topical-refresh` agents |
| `hub/tests/` | the hermetic tests for all of the above |
| `hub/docs/specs/`, `hub/docs/plans/` | design docs: docset reference extraction, golden baseline, llms.txt as the docset schema, the conceptual (concept-axis) llms family |
| `outputs/exports/<stem>.llms/` | 15 docsets exported as `llms.txt` (split into `<section>/llms.txt` when > 10 KB), `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, `manifest.json` |
| `outputs/llms-full-catalog/` | catalog + manifest of every site known to publish `llms-full.txt` (the 722 MB of downloaded files stay on the hub) |
| `outputs/llms-topical/` | topical (concept-axis) llms files built from fact pools |
| `outputs/llms-concepts/` | concept packs built by `/lca` during its evals (prompt caching × 3 docsets; indexing across 10 DB inputs + 5 child packs), plus the eval notes and benchmark |
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
  concept-tree node; concept packs (`/lca`, `llms-concepts/<slug>.llms/`) abstract one arbitrary
  concept out of any scope with a lexicon + semantic index; the hub root `/llms.txt` is the
  categorical view.
- **Retrieval** — every facts layer is embedded (vector) and FTS5-indexed (keyword); `hub_ask`
  fuses them; `hub_query_docset(mode="keyword")` is the no-embedding cheap path.
- **Quality bar** — `skills/llms-deep-optimizer/references/attributes.md` is the rubric;
  `llms_lint.py` runs the deterministic passes; `docset_rollout.py cleanup` is the gate
  (0 High across 15 docsets / 652 files at snapshot time).

## Self-supported checkout

`hub/` keeps the hub's own layout (`scripts/`, `mcp-server/`, `tests/`, `.mcp.json`,
`pyproject.toml`, `requirements-dev.txt`), so the code runs from here without the hub:

```
sh hub/bootstrap.sh                # venv + deps + the llms test suite
cd hub && .venv/bin/python scripts/llms_lint.py check ../outputs/exports/code.claude.com.llms/
cd hub && .venv/bin/python scripts/llms_serve.py --help
cd hub && .venv/bin/python mcp-server/hub_mcp_server.py   # MCP over stdio (point HUB_* env at ../outputs)
```

`outputs/llms-full/files/` carries the mirror itself (608 files); anything over GitHub's
100 MB limit is listed in `outputs/llms-full/SKIPPED.txt` instead.

## Refresh

`scripts/refresh_snapshot.sh` rsyncs every subtree above from the live hub (`HUB_DIR`,
`CLAUDE_DIR`, `MIRROR_DIR` env override the defaults), commits when anything changed and
pushes. It runs automatically: daily at 04:30 via launchd
(`com.llms-explorer.snapshot-refresh`, wrapper in `hub/scripts/launchd/`) and whenever the
hub's pipeline queue drains (`pipeline_manager._refresh_snapshot`). `SNAPSHOT.txt` carries
the last refresh time. `--no-push` copies and commits only.
