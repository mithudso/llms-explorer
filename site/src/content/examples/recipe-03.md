---
title: "Recipe 03 — Keyword layer from Claude Code"
description: "Find an exact token — a header name, an env var, an error string — with hub_query_docset(mode=\"keyword\"), then open the page it came from. Zero model tokens."
section: examples
order: 3
date: "2026-08-31"
tags: ["mcp", "keyword", "fts5", "exact-token"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/mcp-server/hub_mcp_server.py"
  - "hub/scripts/docset_indexer.py"
---

## Goal

Answer "where is `X-Markdown-Tokens` documented?" without an embedding call. The keyword
layer is an FTS5 index (BM25 ranking) built beside each docset's vector layer; a query in
`mode="keyword"` is a sub-token phrase match over the facts layer, returns the unit's
snippet and its `url#anchor`, and costs microseconds.

## When not to use it

- The question is a paraphrase. "The header that says how big the page is" contains none of
  the tokens in `X-Markdown-Tokens`; use hybrid ([recipe-04](/examples/recipe-04/)).
- The docset has no facts layer yet. Keyword still works over the raw chunks, but the hits
  are chunks, not anchored units — `layer` in the reply says which answered.
- You want the whole page. The keyword hit tells you *which* page; the read is the second
  call below.

## Steps

1. Call `hub_query_docset` with the token and `mode="keyword"`. The index is built on first
   use (`docset_indexer keyword-index` under the hood), so the first call on a docset is
   slower once.
2. Read `snippet`, `unit_type`, `url` from the top hit. The URL carries the anchor.
3. Open the page with `hub_llms_full_read(key, page=<url>)` — `page` matches by exact
   source URL or a case-insensitive title substring.

From a Claude Code session with the `global_ai_hub` server connected:

```
hub_query_docset(docset="code.claude.com", question="X-Markdown-Tokens", mode="keyword", top=3)
```

reply (abridged):

```
layer: facts   mode: keyword   hits: 3
1. [parameter] X-Markdown-Tokens — response header carrying the page's token estimate (chars/4)
   https://code.claude.com/docs/en/claude-code-on-the-web#markdown-responses
2. [fact] Every markdown response carries Content-Type: text/markdown; charset=utf-8 and X-Markdown-Tokens
   https://…
```

then

```
hub_llms_full_read(key="code.claude.com", page="https://code.claude.com/docs/en/claude-code-on-the-web")
```

The same two calls from the shell, for a script:

```
.venv/bin/python scripts/docset_indexer.py keyword code.claude.com "X-Markdown-Tokens" --mode phrase --top 3
```

`--mode` is `any | all | phrase | raw`; `phrase` is what an exact token wants.

## Expected output

The top hit's URL ends in the heading that documents the header, with `unit_type`
`parameter` or `fact`, and the reply names the layer that answered (`facts`). The full-read
returns that page's markdown in the Mintlify grammar — `# Title`, `Source: <url>`, body —
so the anchor from the hit resolves to a heading you can see.

If the reply says `layer: raw`, the docset has no facts layer; the hit is still correct but
is a text chunk without an anchor. That is the signal to run `extract → export` on it.

## Cost

Measured on the hub: the FTS5 lookup is sub-millisecond after the index exists; the first
call on a docset builds the index (seconds for a 14k-unit family). Zero model tokens, zero
embeddings. The page read is bounded by the page — ~3k tokens for a typical reference
page, capped at 200k characters by the tool.

> Runnable in step 4 (playground).
