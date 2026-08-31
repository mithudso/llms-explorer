# 14 — Coding examples (how and when to use an LLMS)

**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | cli | mcp | api

## 1. Purpose

A cookbook that answers *when* to reach for which layer and *how*, with runnable examples
tested in CI against this repo's `outputs/`. Each recipe states its goal, when **not** to use
it, the expected output, and the cost (tokens, time), so a reader can pick the cheapest layer
that answers their question.

## 2. User stories and flows

- *Agent builder*: "My agent needs to answer questions about a docs site cheaply" → decision
  table → recipe (index two-hop or keyword layer) → copy, run against `outputs/exports/...`.
- *Platform engineer*: "How do I serve my files right?" → nginx/Cloudflare snippet → verify with 01.
- *Data engineer*: "Feed facts into my RAG" → the facts-ingest recipe.
- *CI owner*: "Gate my docs on the lint" → GitHub Action recipe.

## 3. Inputs → outputs (content outline)

**Decision table** (page 1): question shape → layer → cost class.

| You need | Use | Why | Cost |
|---|---|---|---|
| Orientation before any retrieval | `llms.txt` (≤ 10 KB) then ≤ 2 hops | it is the map; small enough for context | ~2.5k tokens |
| An exact token (env var, flag, header, error string) | keyword layer (`mode="keyword"`, FTS5/BM25) | no embedding call; exact sub-token phrase match | µs, 0 model tokens |
| A paraphrased question | vector layer (`layer="facts"`) | meaning, not spelling | 1 embedding |
| Mixed / unsure | `mode="hybrid"` (RRF) | both legs, agreement surfaces | 1 embedding |
| Whole-corpus reasoning within a budget | `llms-small.txt` (≤ ~50k tokens) or `llms-full.txt` | consumers break above ~50k; small is reference-first | 50k–2M tokens |
| Citation-grade answers | `llms-facts.txt` lines with `url#anchor` | every claim anchored, checkable | per hit |
| A concept across many sources | topical file (`/t/<slug>/`) or concept pack (06) | concept axis, deduped, disagreements visible | per pack |
| Disambiguation | `llms-vocabulary.txt` senses (12) | which "cookie" | free |

**Recipes** (each: goal · when not · code (illustrative) · expected output · cost):

1. **Two hops with `requests`** — GET `/llms.txt`, parse `- [name](url): notes` lines with the
   same regex as `llms_lint.py::LINK_RE`, pick by description tokens, GET the `.md` twin,
   answer. Not for exact tokens (use 3). Output: page markdown + the two URLs. ~3k tokens.
2. **Split root** — detect `## Sections`, follow `<slug>/llms.txt`, then the page; shows the
   counts on the section line deciding before fetching.
3. **Keyword layer from Claude Code** — `hub_query_docset(docset, "X-Markdown-Tokens",
   mode="keyword")`; shows `snippet` and `url#anchor`; then `hub_llms_full_read(key, page=n)`
   to open the page. Not for paraphrase. 0 model tokens.
4. **Hybrid** — same with `mode="hybrid"`; explains `legs == 2`.
5. **Index-first agent** — `hub_docset_index(docset)` → read `sections` → `hub_docset_index(docset, file="<slug>/llms.txt")` → page; the pattern 09's node page uses.
6. **`llmsx` CLI** — `llmsx lint`, `llmsx query --mode keyword`, `llmsx export`, `llmsx tree show`.
7. **Facts into a RAG store** — parse `llms-facts.txt` with `UNIT_RE`, one document per unit,
   metadata `{type, url, anchor, keywords, verified_as_of, page_title}`; embed with
   `mxbai-embed-large` (1024d); note the model-split trap (never mix with `nomic` 768d).
8. **GitHub Action lint gate** — `llmsx lint ./docs/llms.txt --check-links --json`; fail on High; annotate lines from the JSON `line` field.
9. **Serving with the right headers** — nginx `location ~ \.md$ { types { text/markdown md; } add_header Link '<…llms.txt>; rel="describedby"'; }`; Cloudflare Transform Rule for `rel="alternate" type="text/markdown"` on HTML; verify with `curl -I`.
10. **Local hub in miniature** — Ollama + `docset_indexer.py index` + `keyword-index` + `llms_serve.py` on one machine; mirrors 17's description.
11. **Building a topical file** — `docset_refine topical --from … --subject … --out …` then `/ldo --agent-test` (from `facts-to-llms-howto.md`).
12. **Reading a vocabulary** — expand a query through `aka:` before FTS5.

Each recipe page ends with **Cost measured** (tokens/time from the CI run) and **When this is
the wrong tool**.

## 4. Architecture

```mermaid
flowchart LR
  E[examples/<nn>-<slug>/{README.md, run.py|run.sh, expected.json}] --> T[CI: run against outputs/exports + a local llms_serve]
  T --> R[results.json: tokens, time, pass]
  E --> C[Astro pages: code + expected + measured cost]
  R --> C
```

Runnable examples live in `examples/` (later); each has `run.*` that prints JSON, and
`expected.json` with the assertion (e.g. keyword hit url endswith `/env-vars#variables`). CI
starts `hub/scripts/llms_serve.py` on a random port against `outputs/exports`, builds the FTS5
index for the fixture docset with `HUB_DOCSET_BACKEND=sqlite`, runs every example, records
tokens (chars/4 for local, API usage for Claude) and wall time into `results.json`, and the
site renders those numbers — never hand-typed. Model-backed recipes run against local Ollama
in CI; Claude-backed ones are skipped in CI and marked "measured on <date>".

## 5. API / CLI / MCP surface

`GET /examples/<slug>.md`, `GET /api/examples.json` (list + last measured cost),
`llmsx examples list|run <slug>`. MCP: the recipes reference 13's tools; no new tools.

## 6. UI

Cookbook index (decision table on top, recipes filtered by layer / surface / cost class);
recipe page (goal, when-not, tabs Python / CLI / MCP where applicable, expected output block,
measured cost badge with date, "run in the playground" for free recipes — a sandbox calling
the public API with the fixture docset). Empty/error: a recipe whose CI run failed shows a
"last run failed" badge and the log link, never a stale success.

## 7. Data model and storage

`examples/**` + `build/examples/results.json`; no database.

## 8. Tiering, metering and billing hooks

Pages free. Playground runs of keyword/index recipes free (fixture docset, rate-limited);
vector/hybrid playground runs metered (one embedding each); Claude-backed recipes are
copy-only.

## 9. Acceptance bar

- All 12 recipes present with `run.*` + `expected.json`; CI green on the fixture docset (`code.claude.com.llms` + its facts layer).
- Every recipe's measured cost is ≤ the cost class in the decision table.
- Snippets on the site are the literal files in `examples/` (included at build), so a diff in code is a diff on the page.

## 10. Security, rights, privacy

Playground executes only server-side recipes against the fixture docset with fixed queries
(no arbitrary code); API keys never appear in snippets (env vars). Examples use
`outputs/exports` we own or public docs sites.

## 11. Dependencies

01 (lint recipe), 03 (serving guide), 12 (vocabulary recipe), 13 (MCP tools), 15 (metered playground), 17 (local indexer recipe).

## 12. Open questions and assumptions

- Assumed a playground is worth the sandbox; if not, recipes stay copy-only.
- Token accounting for local models uses chars/4 (the hub's `CHARS_PER_TOKEN`); a tokenizer-based count would be more honest and is left open.
