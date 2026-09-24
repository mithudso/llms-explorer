# Resources and tooling — what supports `/ldo`

<!-- llms-deep-optimizer · references/resources-and-tooling.md · 2026-08-30 -->

Everything the passes call, read or cite, with what each is for. Paths are on this estate
(M5 = `~/.global-ai-hub` sole writer; other boxes receive by rsync).

**Contents**
1. MCP servers and tools
2. Hub scripts (CLI)
3. Served surfaces
4. Source files and stores
5. Knowledge references (skills)
6. External links
7. Sibling skills and where to defer
8. Environment variables

## 1. MCP servers and tools

`global_ai_hub` (stdio via `.mcp.json`; HTTP on 127.0.0.1:8787, launchd
`com.global-ai-hub.mcp-http`; localhost trust model, never expose without auth).

| Tool | Used by | For |
|---|---|---|
| `hub_docset_index(docset, file="llms.txt")` | P0 P1 P3 P4 P12 | read a hub docset's exported `llms.txt` / `llms-small.txt` / `llms-facts.txt` / `manifest.json` + served URLs |
| `hub_llms_full_list(query, status, min_pages)` | P0 P10 | find a mirrored third-party `llms-full.txt` by host; page counts for family lines |
| `hub_llms_full_read(key, offset, limit, page)` | P2 P6 P8 P12 | read a page block from the mirror (link existence, unit re-verification, link following) |
| `hub_query_docset(docset, question, top, layer="auto"|"raw"|"facts")` | P3 P11 | fetch a page's definition unit; vector probes per layer |
| `hub_list_docsets()` | P0 | resolve a stem/host to its docset key and layers present |
| `hub_index_docset(mirror, layer)` | P11 | (re)build a layer after a fix |
| `hub_delete_docset(docset, confirm)` | never by `/ldo` | listed so the optimizer knows it exists and does not call it |
| `hub_ask(question, corpora)` | P4 | federated answer to seed the question bank from real traffic |
| `hub_concept_tree` / `hub_concept_lookup` / `hub_concept_frontier` / `hub_concept_queue` | P4 P10, how-to | family membership, section names, topics still unresearched |
| `hub_route(task)` | routing | which skill/tool owns a task (learns topical llms files once registered) |
| `hub_search_symbols` / `hub_search_codebase` | tooling fixes | locate generator code when a pass fix needs a code change |

`tam-context-hub` (when connected): `tam_search_prose` (hybrid prose index over skills —
the family's semantic-index integration), `tam_recommend_urls` / `tam_search_urls` (URL
library warm-start for a topical file's link set), `tam_concept_tree_*` (the older tree; the
hub's `concept-tree/tree.json` is authoritative on this estate).

`firecrawl` / `exa` (when connected): fresh page fetch for a dead link before declaring it
BLOCKED; `web-text-mirror` remains the zero-credit fallback.

## 2. Hub scripts (CLI)

All run from `~/.global-ai-hub` with `PYTHONPATH=scripts .venv/bin/python`.

| Script | Command shapes | Role |
|---|---|---|
| `scripts/llms_lint.py` | `detect F` · `check F [--kind K] [--check-links] [--fix] [--json]` · `full F` · `facts F [--mirror M]` · `hygiene F --fix` | every deterministic pass (P0 P1 P2 P3-det P5 P6 P7 P9-det P14); JSON findings `{pass, attr, severity, line, msg, fix}` |
| `scripts/docset_refine/__main__.py` | `export <mirror.md> [--title T] [--summary S]` · `family <m1> <m2>… --name N --summary S --out llms.txt [--base-url U]` · `topical --from F… --subject S --out DIR [--summary] [--base-url] [--no-embed] [--register]` · `units <mirror> [--force]` · `all <mirror>` | the generator; P3/P4/P10/P15 fixes are inputs to it; `topical` is build mode |
| `scripts/docset_refine/export_llms.py` | `run()`, `build_index/full/small/facts`, `family()`, `_family_link()`, `GRAMMAR_NOTE`, `SMALL_MAX_CHARS`, `CHARS_PER_TOKEN` | export internals the lint reuses (same constants, same grammar) |
| `scripts/docset_refine/clean.py` `extract.py` `units.py` `polish.py` `render.py` | module API | residue table (P6), deterministic extractors and unit schema (P7), LLM units (P8 regen) |
| `scripts/llms_acquire.py` | `acquire URL` · `probe URL` · `split_llms_full(text)` · `parse_llms_index(text)` | grammar parsing (P0 P6), ladder acquisition for missing members |
| `scripts/docset_indexer.py` | `index <mirror> [--layer raw|facts]` · `query <docset> "q" [--layer]` · `keyword <docset> "q" [--layer] [--top N]` · `keyword-index <docset>` · `dump <docset>` · `list [--all]` | vector + FTS5 keyword layers (P11) |
| `scripts/llms_serve.py` | `serve` (launchd) · module `render_root()`, `index_json()` | hub root `/llms.txt`, per-docset and per-mirror routes, headers (P13) |
| `scripts/llms_full_catalog.py` | `list_entries(status, query, min_pages)` · `read_entry(key, page=)` · `export_mirror(key, out)` · `download_all` · `compile_catalog` | the 608-file third-party mirror behind `hub_llms_full_*` |
| `scripts/pipeline_manager.py` | `run` · `status` · `add URL` · `retry-failed` | the `mirror → refine → index` pipeline that regenerates exports; `/ldo` never runs it, it queues |
| `scripts/docset_rollout.py` | `cleanup` (planned: CI link check) | estate-wide refine + the place a `check --check-links` gate belongs |
| `scripts/ask` | `ask "q" --corpora …` | federated answer (P4 seed, P11 sanity) |
| `~/.claude/skill-consolidation/convergence_check.py` | iteration N vs N−1 | the family's edit-distance/cycling detector — never estimate by hand |

## 3. Served surfaces

| URL (localhost) | Serves |
|---|---|
| `http://127.0.0.1:8788/llms.txt` | hub root index: hub docsets + mirrored sites with ≥ 1 page |
| `…/index.json` | machine listing with counts |
| `…/d/<stem>/llms.txt|llms-small.txt|llms-full.txt|llms-facts.txt|manifest.json` | a hub docset's export |
| `…/m/<key>/llms-full.txt|llms.txt|pages/<n>.md` | a mirrored third-party site |
| `…/t/<slug>/llms.txt|llms-facts.txt|manifest.json` | a topical file (`docset_refine topical`) |
| `…/c/<slug>/llms.txt|llms-full.txt|llms-small.txt|llms-facts.txt|llms-vocabulary.txt|concept-graph.json|manifest.json` | a concept pack (`llms-concept-abstractor`, `/lca`) — P13 applies; small/full are facts-style digests, lint them `--kind facts` |
| `…/health` | liveness |
| `http://127.0.0.1:8787` | MCP HTTP |

Headers emitted: `Content-Type: text/markdown; charset=utf-8`, `X-Markdown-Tokens`,
`Link: <…>; rel="describedby"`. Restart: `launchctl kickstart -k gui/$(id -u)/com.global-ai-hub.llms-serve`.

## 4. Source files and stores

| Path | What |
|---|---|
| `~/.claude/skills/web-text-mirror/text-mirror/<stem>.md` | banner mirror (`====/URL:/====` blocks) — the internal canonical page format |
| `…/text-mirror/<stem>.llms/{llms.txt,llms-full.txt,llms-small.txt,llms-facts.txt,manifest.json}` | a docset's export (target of most runs) |
| `…/text-mirror/<stem>.refine/` (`clean/`, `reference/`, `units.jsonl`) | refine intermediates; `units.jsonl` is the facts source of truth |
| `~/.global-ai-hub/llms-full/{catalog.json,manifest.json,files/<key>.txt}` | third-party llms-full mirror |
| `~/.global-ai-hub/.chroma-docsets/` + `docsets.db` | vector collections `<key>`, `<key>__facts`; raw page text; (new) FTS5 tables `kw_<key>[_facts]` |
| `~/.global-ai-hub/concept-tree/tree.json` | family definitions (P10, how-to) |
| `~/.global-ai-hub/docs/superpowers/specs/2026-08-30-docset-golden-baseline.md` | golden question set + scoring |
| `~/.global-ai-hub/docs/superpowers/specs/2026-08-30-llms-txt-as-docset-schema-design.md` | the schema decision, family layout, next steps |
| `~/.global-ai-hub/docs/superpowers/specs/2026-08-30-docset-reference-extraction-design.md` | the refine pipeline design |
| `~/.global-ai-hub/docs/superpowers/specs/2026-08-30-conceptual-llms-txt-family.md` | the concept axis: `llms-concepts.txt`, concept pages, topic packs — what a topical file instantiates |
| `~/.global-ai-hub/llms-topical/<slug>.llms/` | topical exports, served at `/t/<slug>/…` |
| `~/.claude/skill-consolidation/convergence-and-severity.md` | the family contract (severity, exits, guardrails, telemetry) |
| `~/.claude/skill-consolidation/evals/llms/<key>.eval.jsonl` | persisted P12 questions + verdicts |
| `~/.claude/skill-consolidation/backups/<key>-<ts>/` | pre-write snapshots + `run-stub.jsonl` checkpoint |
| `~/.claude/skill-consolidation/optimizer-telemetry.jsonl` | one row per run (family schema; `kind` = `llms`) |

## 5. Knowledge references (skills)

`document-formats` hub, `references/`:
- `llms-txt.md` — spec v2, grammars, discovery headers, consumers, known gaps.
- `llms-txt-generation-tooling.md` — generator catalogue; why extractive descriptions win.
- `llms-txt-ecosystem-evidence.md` — adoption + log evidence; the 50k-token ceiling; the 42% steering figure.
- `llms-txt-recreation-and-aggregation.md` — acquisition ladder, lenient parsing, family pattern, rights.

Also: `hub-architect` (where stores live, one-writer rule), `web-text-mirror` (crawl/refresh
a page), `concept-family-explorer` (map a family before building its file), `deep-research-methods`
(source grading when a fact pool is being assembled), `document-critique` (blockquote prose only).

## 6. External links

- Spec: https://llmstxt.org (v2, 2026-08-10) · https://github.com/AnswerDotAI/llms-txt
- Live exemplars: https://developers.cloudflare.com/llms.txt (family shape) · https://docs.anthropic.com/llms.txt · https://code.claude.com/docs/llms.txt
- Validators: `llms-txt-validator` (npm), `llmstxt-validator` (pypi) — strict rules folded into P1 as `validator-only` Lows
- Directories: https://llmstxt.site (counts column) · https://directory.llmstxt.cloud
- Evidence: Ahrefs llms.txt log study (May 2026); Google Search Central on llms.txt; Lighthouse agentic audit
- Method: https://www.llms-text.com/blog/how-to-create-llms-txt · https://gitdoc.ai/blog/llms-txt-ai-readable-documentation

## 7. Sibling skills and where to defer

| Situation | Defer to |
|---|---|
| The target is a SKILL.md or a hub spoke | `skill-optimizer` (`/sko`) |
| The target is a prompt inside the generator (`units`, polish) | `prompt-deep-optimizer` (`/pdo`) |
| The target is a prose document (design doc, spoke reference) | document-deep-optimizer (`/dfo`) |
| A page has moved / needs re-crawl | `web-text-mirror` |
| Family membership is unknown | `concept-family-explorer`, then `/dr` for gaps |
| Facts are stale at the concept level | `/dr --refresh <concept>` |
| The fact pool needs source grading before it becomes a file | `deep-research-methods` |

## 8. Environment variables

`HUB_LLMS_PORT` (8788) · `HUB_LLMS_HOST` (127.0.0.1) · `HUB_REFINE_LLM_URLS` (localhost Ollama)
· `HUB_REFINE_LLM_MODEL` (`qwen3.5:35b`) · `HUB_OLLAMA_URLS` (embed pool) · `HUB_EMBED_MODEL`
(`mxbai-embed-large`, 1024d — the semantic_ops model; never `nomic-embed-text`, which is
`hub.db`'s) · `HUB_LLMS_LINK_TIMEOUT` (10 s, P2) · `HUB_LLMS_LINK_CONCURRENCY` (8, P2).
