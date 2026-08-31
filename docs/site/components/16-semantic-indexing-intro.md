# 16 — Semantic indexing with llms files: introduction and live demo

**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | api | cli | mcp

## 1. Purpose

Explain — and let the reader feel — why an `llms.txt` index, a facts layer, a vector index and a
keyword index together beat any one of them alone, using the hub's own design and numbers. The
page is content (a long-form introduction with the reasoning and the pitfalls) plus a live demo
where a question is run against a public docset three ways at once: keyword (FTS5/BM25), vector
(embeddings), and fused (RRF) — with latency, cost and the exact anchors each leg returned. It is
the "why" page that components 01, 02, 06 and 17 point at when they mention layers, probes or
modes.

## 2. User stories and flows

- **Newcomer**: "I have an llms.txt; why do I also need an index?" → reads the ladder
  (orientation → retrieval → citation), sees the demo answer an exact-token question that the
  vector leg misses and a paraphrase the keyword leg misses.
- **Engineer evaluating**: types `CLAUDE_CODE_SYNC_SKILLS` and "why split a big file" against
  `code.claude.com`, toggles raw vs facts layer, sees the facts layer win on the golden question
  and the keyword leg return in single-digit ms with no model call.
- **Skeptic**: reads the traps (embedding-model dimension split, chunk boundaries, agents that
  ignore the index) with the measured evidence, not claims.
- **Builder**: clicks "reproduce this" → lands on component 17's guide with the same docset and
  question pre-filled.

Flow: `read → pick docset → ask → compare legs → toggle layer/model → copy MCP call → go to 17`.

## 3. Inputs → outputs (contracts and file grammars)

**Content outline** (static pages under `/learn/semantic-indexing/`, each with a `.md` twin and a
place in the site's own `llms.txt` under `## Learn`):

1. *Three questions, three tools* — orientation (which page?), retrieval (which span?), citation
   (which line, with anchor?). Why one file cannot do all three.
2. *The layers* — index (`llms.txt`, ≤ 10 KB, two hops), text ladder (`llms-full.txt` /
   `llms-small.txt` ≤ ~50k tokens), facts (`llms-facts.txt` — `- [type] text — url#anchor …`),
   vector store (`<key>` raw chunks, `<key>__facts` units with `unit_type`/`origin` metadata),
   keyword store (FTS5 `kw` table, same keys).
3. *Chunking and units* — raw layer: `CHUNK_CHARS = 1200` with overlap, fragments < 40 chars
   dropped; facts layer: one embedding per unit (13,976 units for `code.claude.com`), so a hit
   is a claim, not a window.
4. *The keyword leg* — SQLite FTS5, `unicode61 remove_diacritics 2`; every term double-quoted so
   `CLAUDE_CODE_SYNC_SKILLS` and `--append-system-prompt` match as phrases of their sub-tokens;
   modes `any` (OR), `all` (AND), `phrase`, `raw` (caller's MATCH syntax); BM25 rank; snippet.
   Zero model tokens, microseconds.
5. *The vector leg* — `mxbai-embed-large` (1024d) for every semantic_ops store; cosine over
   stored vectors; the query is embedded with the model recorded for that docset
   (`docset_model()`), never the environment default.
6. *The trap* — the hub's own file index (`hub.db`) uses `nomic-embed-text` (768d); mixing models
   returns nothing, silently: the store now refuses cross-dimension queries with an error instead.
7. *Fusion* — reciprocal-rank fusion (`semantic_ops.fuse.rrf`, k = 60) keyed by `(url, seq)`; a
   hit both legs agree on outranks a hit only one leg found, with a `legs` count; optional
   cross-encoder rerank (`semantic_ops.rerank`) as an opt-in second stage.
8. *Measuring it* — the golden-question baseline (`hub/docs/specs/2026-08-30-docset-golden-baseline.md`):
   the facts layer must score ≥ the raw layer or the refine is rejected; the `/ldo` probes P11
   (10/10 exact-token keyword hits, facts ≥ raw on golden) and P12 (agent given only the index
   answers ≥ 8/10 in ≤ 2 hops; facts-only ≥ 7/10).
9. *What it costs* — embedding 14k units ≈ 4 min on the pool; a keyword index ≈ 2 s; a keyword
   query ≈ 1 ms; a vector query ≈ 1 embedding call; a hybrid query = both.
10. *When to use which* — table (exact token → keyword; paraphrase → vector; unknown → hybrid;
    citation-grade → facts layer; whole-corpus reasoning → small/full within budget).

**Demo contract** — request `POST /api/demo/query`:
```json
{"docset": "codeclaudecom__codeclaudecom", "question": "CLAUDE_CODE_SYNC_SKILLS",
 "layer": "facts", "top": 5, "legs": ["keyword", "vector", "hybrid"], "model": null}
```
Response:
```json
{"docset": "…", "layer": "facts", "queried": "codeclaudecom__codeclaudecom__facts",
 "legs": {
   "keyword": {"ms": 2, "tokens": 0, "hits": [{"score": 8.55, "url": "…/env-vars#variables", "seq": 8391, "snippet": "…"}]},
   "vector":  {"ms": 180, "tokens": 12, "model": "mxbai-embed-large", "hits": [{"score": 0.71, "url": "…", "seq": 8391, "text": "…", "unit_type": "parameter", "origin": "table"}]},
   "hybrid":  {"ms": 184, "hits": [{"score": 0.0328, "legs": 2, "url": "…", "seq": 8391, "text": "…"}]}
 },
 "cost_usd": 0.0000, "cached": false}
```
Hit shapes are exactly `docset_indexer.SqliteStore.query()` / `keyword_query()` / the MCP `_rrf()` rows.

## 4. Architecture (mermaid diagram + existing hub code reused, by path)

```mermaid
flowchart LR
  page[/learn/semantic-indexing<br/>Astro content + island] --> api[explorer-api<br/>POST /api/demo/query]
  api --> kw[FTS5 kw table<br/>docsets.db]
  api --> emb[embed_core pool<br/>Ollama mxbai-embed-large]
  emb --> vec[Chroma / SqliteStore<br/>&lt;key&gt;__facts]
  kw --> fuse[_rrf k=60]
  vec --> fuse
  fuse --> api
  api --> cache[(query cache<br/>docset+question+layer, 24 h)]
```

Reused: `hub/scripts/docset_indexer.py` (`resolve_layer`, `SqliteStore.query`, `keyword_query`,
`fts_match`, `docset_model`), `hub/scripts/embed_core.py` (pool, `embed_texts`, model split),
`hub/mcp-server/hub_mcp_server.py` (`hub_query_docset` modes and `_rrf` — the demo calls the same
functions in-process, so the page shows exactly what the MCP tool returns),
`hub/scripts/semantic_ops/fuse.py` and `rerank.py` for the optional rerank toggle,
`hub/docs/specs/2026-08-30-docset-golden-baseline.md` for the golden set shown in step 8. New:
the Astro island, `explorer-api/demo.py` (fan-out to the three legs with timers, cost line, cache),
the public-docset allowlist.

## 5. API / CLI / MCP surface

| Surface | Call | Notes |
|---|---|---|
| REST | `POST /api/demo/query` | body per §3; anonymous allowed (rate-limited); `legs` subset; `model` only from the allowlist (17) |
| REST | `GET /api/demo/docsets` | public docsets with layers present, unit counts, golden set available? |
| REST | `GET /api/demo/golden/<docset>` | the golden questions + expected anchors (for the "run the baseline" button) |
| CLI | `llmsx query <docset> "<q>" --mode keyword|semantic|hybrid --layer facts|raw` | same API |
| MCP | `hub_query_docset(docset, question, top, layer, mode)` | already exists (13); the page shows the equivalent call for every demo run |

Rate limits: anonymous 30 queries/10 min/IP and 200/day/IP; keyword-only legs are not counted
(no model cost); signed-in free tier 200/day (15 §5, master D6); paid unmetered up to fair use. Cache hits are free
and not counted.

## 6. UI (pages, states, empty/error states)

- `/learn/semantic-indexing` — long-form article (outline §3) with the demo island embedded
  after step 4 and again after step 7; sticky "try it" button.
- Demo island: docset picker (public allowlist: `code.claude.com`, `developers.cloudflare.com`,
  `docs.langchain.com`, `pydantic.dev`, `docs.github.com`, the llms.txt topical family), question
  input with example chips (an exact token, a paraphrase, a cross-section question), layer toggle
  raw/facts, model toggle (default model; others from 17 when indexed), rerank toggle. Result:
  three columns (keyword · vector · fused), each with latency, tokens, cost, hits as anchored cards
  (`url#anchor`, unit type chip, snippet/text, score); agreement highlighting (a hit present in
  both legs gets the `legs = 2` badge); "show the MCP call" and "show the CLI call" drawers;
  "run the golden set" → table of question / expected anchor / keyword hit? / vector hit? /
  fused rank.
- States: loading per leg (they resolve independently — keyword first); embedding pool busy →
  vector column shows "queued (quiet hours on the M3 box)" with the keyword column already
  filled; docset without a facts layer → facts toggle disabled with the reason; rate-limited →
  sign-in CTA with the cached result still shown; empty hits → "no unit contains these tokens;
  try the vector leg" / "nothing semantically close; try the exact token".

## 7. Data model and storage

Read-only over the hub stores: `docsets.db` (`docsets`, `chunks`, `pages`, `kw` tables),
`.chroma-docsets/` collections. New, small:

```
demo_docsets(key pk, public bool, title, layers jsonb{raw,facts,kw_raw,kw_facts}, golden_ref text)
demo_queries(id pk, docset_key, question_hash, layer, mode, legs jsonb, ms jsonb, tokens int, cost_usd numeric, cached bool, user_id null, ip_hash, created_at)
demo_cache(docset_key, question_hash, layer, model, response jsonb, created_at, pk(docset_key,question_hash,layer,model))  -- 24 h TTL
```
`demo_queries` feeds the "what people ask" panel (top questions per docset, anonymised) and the
cost dashboard (15). No user text is kept beyond the hash unless the user is signed in and opts
into history.

## 8. Tiering, metering and billing hooks

| Feature | Tier | Metered unit |
|---|---|---|
| Article, `.md` twin | free | — |
| Keyword leg | free, unlimited within rate limit | — (no model) |
| Vector / hybrid leg on the default model | free within §5 limits (master D7) | embedding tokens (logged, not billed at free tier) |
| Other embedding models, rerank | signed-in; paid beyond 100/day | embedding tokens + rerank calls |
| Golden-set run (10 questions × 3 legs) | signed-in | 10 embeddings |
| Query history | signed-in | — |

The ledger row per demo query records model, input tokens, unit cost and margin exactly as
component 15 defines, even when the tier makes it free — the dashboard must show true cost.

## 9. Acceptance bar (measurable)

- The demo returns the keyword leg in < 50 ms p95 and the full hybrid response in < 1.5 s p95
  on the public docsets (cache cold), < 100 ms cached.
- The three published example questions behave as the article claims, verified by a nightly test:
  `CLAUDE_CODE_SYNC_SKILLS` → keyword hit #1 = `…/env-vars#variables`, vector top-5 misses it or
  ranks it lower; "why split big files" → vector hit within top-3 from the llms.txt topical facts,
  keyword misses; a mixed question → fused rank 1 has `legs = 2`.
- Golden set on `code.claude.com`: facts layer ≥ raw layer (the baseline rule) shown live.
- The article itself passes component 01's lint as part of the site family (0 High) and every
  claim with a number cites a hub artefact (manifest, spec, log) — reviewed with the
  document-critique loop before publish.
- Accessibility: the three-column result collapses to tabs under 900 px; keyboard operable.

## 10. Security, rights, privacy

- Only allowlisted public docsets are queryable anonymously; a user's own docsets require their
  key (13/15). Questions are not stored in clear for anonymous users (hash + aggregates only).
- The demo never returns page bodies from third-party full text — hits are units (facts layer)
  or chunks capped at 1,200 chars with their source URL, consistent with component 10's rights
  rule; the "open page" link goes to the origin site's `.md` twin when it exists.
- Prompt-injection surface: user questions go to the embedding model only (never to a
  generating model) on this page; the keyword leg escapes MATCH syntax (`fts_match` quoting)
  unless `mode=raw`, which is disabled in the demo.
- Rate limits by IP hash and account; cache keys exclude user identity.

## 11. Dependencies on other components (by number)

- **01** linter — P11/P12 probe definitions the article explains; the site family lint.
- **03** reference — grammar pages for each layer linked from step 2.
- **13** MCP hosting — the "show the MCP call" drawer targets the hosted server.
- **15** accounts/billing — rate limits, ledger rows, history opt-in.
- **17** semantic indexer — model allowlist, "reproduce this" hand-off, benchmark harness.
- **02 / 06 / 09** — every artefact they produce is indexed both ways; they link here for the why.

## 12. Open questions and assumptions

- Assumed the public allowlist (6 docsets) is rights-clean for unit-level display; anything
  outside it (mirrored third-party full text) stays out of the demo.
- Assumed 24 h cache TTL and the anonymous limits; tune from `demo_queries`.
- Open: show a fourth "rerank" column by default or keep it a toggle (cost: one cross-encoder
  call per hit) — proposed toggle, off.
- Open: whether the demo should also run the *agent* leg (P12: give a model only the index and
  let it navigate) — valuable but metered heavily; proposed as a signed-in "watch an agent
  navigate" button in a later iteration.
- Assumed numbers quoted (13,976 units, ~4 min embed, 2 s keyword index) are refreshed from
  manifests at build time, never hard-coded in the article.
- Settled: step 2 ships this component's demo payload as build-time JSON (`site/src/data/demo.json`),
  recorded rather than live, not the `/api/*` routes of §5 — master §12 **D9**. The routes stand for
  step 3 and serve the same shape.
