## Repository shape
Single repository. JSON registries, concept trees, metadata, plus a working
runtime: semantic indexers (`scripts/`), a per-docset vector index, and the
`global_ai_hub` MCP server (`mcp-server/`). Acts as the LLM-agnostic global AI
context hub.

## Commands
- Validate JSON: `jq . *.json` (registries must stay well-formed)
- Compile check: `.venv/bin/python -m py_compile scripts/embed_core.py scripts/docset_indexer.py mcp-server/hub_mcp_server.py`
- Host/pool check: `.venv/bin/python scripts/embed_core.py check`
- Docset ops: `.venv/bin/python scripts/docset_indexer.py {index <mirror.md> [--name K] | index <all_units.jsonl> --units --name K | query <docset> "q" [--layer auto|facts|raw] | dump <docset> [--kind auto|pages|chunks] | list [--all] | delete <docset> | keyword-index <docset> [--layer] | keyword <docset> "q" [--layer] [--mode any|all|phrase|raw] [--top N]}` — every docset has a raw layer (`<key>`) and, once refined, a facts layer (`<key>__facts`) that `query --layer auto` prefers; `dump` = text as JSONL, no vectors; `keyword-index`/`keyword` = an FTS5 (BM25) layer beside the vectors for exact-token lookups with no embedding call
- llms lint (deterministic passes of the `/ldo` skill): `.venv/bin/python scripts/llms_lint.py {detect F | check F|DIR [--kind K] [--check-links] [--fix] [--json] [--mirror M] [--third-party] | hygiene F [--fix]}` — exit 1 on any High finding (CI gate)
- Docset refine (fact layer): `PYTHONPATH=scripts .venv/bin/python -m docset_refine {clean|extract|units [--model M] [--limit N]|polish|render|export|all [--polish] [--no-units]} <mirror.md>` · `family <mirror…> --name N --summary S --out llms.txt [--base-url U]`; `export` writes `<stem>.llms/{llms,llms-full,llms-small,llms-facts}.txt` + `manifest.json` (spec v2 index, Mintlify-grammar full file, token counts; see docs/superpowers/specs/2026-08-30-llms-txt-as-docset-schema-design.md) → `<stem>.clean.md` + `<stem>.reference/{pages.json,structured.jsonl,units.jsonl,units.polished.jsonl,all_units.jsonl,reference.md,summary.json}`; the LLM pass targets `HUB_OLLAMA_URLS` (pipeline: `HUB_REFINE_LLM_URLS`, default localhost, model `HUB_REFINE_LLM_MODEL`=`qwen3.5:35b`); polish uses `claude -p` (`HUB_REFINE_POLISH_MODEL`)
- llms-full.txt mirror: `.venv/bin/python scripts/llms_full_catalog.py {compile [--seed URL] [--offline FILE] | download [--jobs N] [--max-bytes N] [--only S] [--retry-failed|--refresh] | list [--status ok|rejected|failed|missing|all] [--query S] [--min-pages N] [--json] | delete KEY | export-mirror KEY OUT.md}` — catalog of every site known to publish `llms-full.txt` (llms-txt-hub, llmstxt.site, directory.llmstxt.cloud, own docslist probe) + downloads into `llms-full/files/` (gitignored); served read-only by MCP `hub_llms_full_list` (default `min_pages=1` hides 0-page blobs) / `hub_llms_full_read`; refreshed weekly by launchd `com.global-ai-hub.llms-full-refresh` (`scripts/launchd/llms-full-refresh.sh`)
- Topical llms (concept axis): `PYTHONPATH=scripts .venv/bin/python -m docset_refine topical --from <units.jsonl|llms-facts.txt|reference.md>… --subject "<concept-tree node>" --out llms-topical/<slug>.llms/ [--base-url http://127.0.0.1:8788/t/<slug>] [--no-embed] [--register]` — sections = the subject's child concepts, every fact filed by keyword → file-affinity → embedding centroid → `## Shared`; writes `llms.txt` + `llms-facts.txt` + `manifest.json` (hand edits in `manifest.overrides`); served at `/t/<slug>/…` by `llms_serve.py`, listed under `## Topics` on the root; `--register` writes `llmsFile` on the node. Tree nodes carry `slug`/`aliases` (`scripts/concept_tree.py slugs` backfills)
- Vocabulary layer: `PYTHONPATH=scripts .venv/bin/python -m docset_refine vocabulary --from … --subject "<node>" --out llms-topical/<slug>.llms/ [--llm [--model M]] [--register]` — `llms-vocabulary.txt` + `vocabulary.json`: one line per term (canonical name, definition, `aka:`, `not:`, `differs:`, source); terms from tree node names + backtick tokens clustered by spelling; definitions extractive, `--llm` fills the rest on the local model and keeps only names present in the evidence; `--register` adds `aka:` to the tree nodes' `aliases` (add-only) so the next `topical` run matches synonyms; `--research` gathers evidence for undefined terms from the hub estate (every docset's `all_units.jsonl`, other topical `units.jsonl`, the llms-full mirror) before defining; `--queue` appends still-undefined terms to `concept-tree/RESEARCH_QUEUE.md`. Served at `/t/<slug>/llms-vocabulary.txt`
- Topical refresh (weekly, automated): `.venv/bin/python scripts/topical_refresh.py [--only SLUG] [--no-llm] [--floor F] [--dry-run]` — for every `llms-topical/*.llms/manifest.json`: topical → vocabulary `--research --llm --register --queue` → vector + FTS5 re-index; launchd `com.global-ai-hub.topical-refresh` Sunday 04:00 (`scripts/launchd/topical-refresh.sh`, after the 03:00 llms-full mirror refresh)
- Docset rollout: `.venv/bin/python scripts/docset_rollout.py {probe | apply [--group llms-full|llms|crawl|all] [--dry-run] | cleanup [--dry-run]}` — which hosts publish `llms.txt`, move a trafilatura mirror aside + reset its queue item, delete distill-era artifacts once a fact layer exists
- MCP server (stdio): `.venv/bin/python mcp-server/hub_mcp_server.py` (HTTP: `--http [port]`, 127.0.0.1:8787)
- TUI control center: `scripts/hub-manager` (queue/health/docsets/llms-full/MCP/scripts — see docs/HUB-MANAGER.md)
- Pipeline manager: `.venv/bin/python scripts/pipeline_manager.py {run [--list FILE] [--digest] [--slots-per-box N] [--local-only] | status | add URL... | retry-failed}` — stages `mirror → refine → index`; only `mirror` is placed on a box (`BoxPool`, results return by rsync); `refine` (docset_refine, LLM on the local model) and `index` always run on M5. The mirror stage prefers a site's `llms-full.txt` / `llms.txt` + page `.md` (`text_mirror.py --prefer-llms`, default on) over a trafilatura crawl
- Quiet hours (a box the hub must not saturate): `PYTHONPATH=scripts .venv/bin/python scripts/box_schedule.py status` · enforce with `scripts/quiet_hours_enforce.py {quiet|resume|status}`; suspend for a vacation with `box_schedule.py off --days N` / `off --until YYYY-MM-DD`, cancel with `on`, or press `Q` on the hub-manager Remotes tab — 192.168.4.113 is a work laptop, off-limits Mon-Fri 09:00-17:00 for BOTH crawl/distill placement and embedding traffic; launchd fires the boundaries.
- Docset replication: `PYTHONPATH=scripts .venv/bin/python scripts/replicate_docsets.py {push [--dry-run]|check|reindex-logs}` — also hourly via launchd (`com.global-ai-hub.docset-replicate`, must run on `/usr/bin/python3`, see docs/MCP.md); `push` finishes by reindexing every box's logs corpus (quiet-hours-aware, failures are non-fatal)
- Federated ask: `scripts/ask "question" [--retrieve-only] [--corpora codebase,logs,git,symbols] [--top 8]`
- semantic_ops CLIs (all `PYTHONPATH=scripts .venv/bin/python -m semantic_ops.<mod>`):
  `logs_corpus {index|query}` · `git_corpus {index|query}` · `symbols {index|query}` ·
  `router {build|route "task"}` · `blast_radius [--file F]` · `misfiled` ·
  `sweep [--targets napmem,skills]` · `digest {recrawl PATH|weekly}` ·
  `tree_maint {propose|apply FILE --accept ids}` · `coverage`
- Tests: `.venv/bin/python -m pytest tests/ -q` (~560 hermetic tests)
- Lint: `.venv/bin/python -m ruff check .` (scoped to scripts/hub_manager + tests via pyproject.toml)

## Runtime architecture
- `scripts/hub_lib.py` + `hub_sqlite.py` + `idle-indexer.py` / `hub-daemon.py`: file-corpus index in `hub.db` (watch_dirs.txt).
- `scripts/embed_core.py`: weighted multi-host Ollama pool — `HUB_OLLAMA_URLS`, default linux GPU box (192.168.4.75)=4 > M3 Mac (192.168.4.113)=3 > this machine/M5 localhost=1; `HUB_EMBED_MODEL` default `mxbai-embed-large`.
- `scripts/docset_indexer.py`: web-text-mirror docsets → ChromaDB collections (`.chroma-docsets/`, registry `.chroma-docsets/docsets.db`, which also stores each docset's raw page text under both backends so a box without the source mirror can still text-search it), key `<host>__<stem>`. Syncthing is gone (removed 2026-08-27): `.chroma-docsets/` is replicated to the other boxes by a one-way rsync push (`scripts/replicate_docsets.py`, M5 sole writer, auto-runs when a queue drains); pipeline results return by rsync-over-ssh. See docs/MCP.md.
- `mcp-server/hub_mcp_server.py`: 17 `hub_*` tools over the above (incl. the `llms-full/` mirror via `hub_llms_full_list`/`_read`) (incl. `hub_ask` federated answer, `hub_search_symbols`, `hub_route`) + distillers kickoff + llm-memory-pyramid search. Localhost trust model; never expose off-box without adding auth.
- `scripts/semantic_ops/`: shared primitives (`fuse` RRF, `corpus` adapters, `rerank`, `llm` pooled generate, `vecstore`, `cluster`, `snapdiff`) + features: `ask` (federated answer), corpora `logs_corpus`/`git_corpus`/`symbols`, `fix_recall`, `blast_radius`, `sweep`, `misfiled`, `digest`, `tree_maint`, `router`, `coverage`. See docs/superpowers/plans/2026-08-21-semantic-leverage-roadmap.md.
- Embedding-model split (load-bearing): `hub.db` vectors are hub_lib's config model (`nomic-embed-text`, 768d) — query it via `hub_lib.fetch_embedding`; every `semantic_ops` store uses the `embed_core` pool model (`mxbai-embed-large`, 1024d). Mixing them silently returns nothing.
- Runtime state (hub.db*, docsets.db*, .chroma-docsets/, .venv/, logs) is gitignored — never commit it.

## Key conventions
- All JSON strictly formatted for machine readability.
- Concept trees maintain consistent structural links for correct traversal.
- Metadata includes timestamps.
- Config via env vars, never hardcoded (see docs/MCP.md for the full env table).
- `skills/` is a NESTED git repo (separate history) — commit skill changes there.

## MCP servers
`global_ai_hub` — see `docs/MCP.md` (tool inventory, env config, examples) and
`mcp-server/README.md` (run/restart/setup). Wiring: `.mcp.json` at repo root.
Registry entry: `libraries/mcp-library/registry.json`.

## Workflow log rule
The logs are split by track, because they were the only files both tracks wrote and every cross-track push collided there:
**hub** (this repo's code/infra) -> `prompts-hub.md` + `memory-hub.md`; **TAM** (customer engagement work, whose deliverables live outside the repo) -> `prompts-tam.md` + `memory-tam.md`.
Append every user request to YOUR track's prompt log (format: `## Prompt vN - <ISO timestamp>\n- User request:\n  - <text>`), numbering from that file's own max — numbers are unique per file, not globally.
Keep your track's memory log current with active task / status / changed files, and bump the patch version in any canonical version file on every change.
Never write the other track's log; that is what keeps the two histories mergeable.
