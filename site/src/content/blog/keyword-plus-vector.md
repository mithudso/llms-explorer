---
title: "Keyword plus vector: the cheap path"
description: "An FTS5 (BM25) table beside the embeddings: exact tokens like CLAUDE_CODE_SYNC_SKILLS or --append-system-prompt cost no embedding call, and a reciprocal-rank hybrid fixes the queries the vector layer ranks below troubleshooting rows."
date: "2026-09-06"
tags: [retrieval, fts5, hybrid]
sources:
  - hub/scripts/docset_indexer.py
  - hub/docs/specs/2026-08-30-docset-golden-baseline.md
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 -->

## Problem

Embeddings are good at "how do I run this headless in CI" and bad at `--append-system-prompt`.
The golden baseline showed it plainly: the query "what does `CLAUDE_CODE_SYNC_SKILLS` control"
surfaced the right pages but the sentence defining the variable sat below rows about skills in
general; the Windows install query was dominated by troubleshooting rows even after the
`irm … | iex` snippet was in the mirror. A retriever that only has cosine similarity cannot
prefer the line that contains the literal token.

The obvious fix is a lexical index. The constraint was cost: the facts layer is 56,489 units
across the estate, every one already embedded, and a second vector model was out of the
question. So the second index had to be free to build, free to query, and live in the same
store.

## Inputs

- `.chroma-docsets/docsets.db`, the registry SQLite file that already stores each docset's raw
  page text and facts units under both backends (Chroma or plain SQLite), so a box without the
  source mirror can still text-search it.
- The facts layers of 13 refined docsets (56,489 units) and their raw layers.
- Ten golden questions with their `--layer auto` scores as the yardstick.

## Commands

```bash
# cwd: ~/.global-ai-hub
# build the keyword table for one docset's facts layer (no embedding call)
.venv/bin/python scripts/docset_indexer.py keyword-index codeclaudecom__codeclaudecom --layer facts

# query it: any-term OR (default), all-term AND, exact phrase, or raw FTS5 syntax
.venv/bin/python scripts/docset_indexer.py keyword codeclaudecom__codeclaudecom "CLAUDE_CODE_SYNC_SKILLS" --layer facts --mode any --top 5
.venv/bin/python scripts/docset_indexer.py keyword codeclaudecom__codeclaudecom "append-system-prompt" --layer facts --mode phrase

# the same through MCP (the pipeline's index stage now builds the kw rows for every layer)
#   hub_query_docset(key, q, mode="keyword")   # BM25 only
#   hub_query_docset(key, q, mode="hybrid")    # RRF over the vector and keyword legs
```

## Outputs

The keyword layer is one FTS5 virtual table, `kw(docset, url, seq, text)`, created beside the
vector rows in `docsets.db`. `keyword_query` runs
`SELECT url, seq, snippet(kw, …), bm25(kw) FROM kw WHERE docset=? AND kw MATCH ? ORDER BY
bm25(kw)`; the `ChromaStore` delegates to its registry `SqliteStore` so both backends answer
the same way.

The part that took thought is `fts_match`. FTS5 treats `-`, `_` and `.` as operators or
separators, so a naïve `MATCH '--append-system-prompt'` is a syntax error and `X-Markdown-Tokens`
becomes three loose tokens. Every user term is therefore double-quoted, which turns a token
like `--append-system-prompt` into a *phrase* of its sub-tokens (`append` `system` `prompt`, in
order, adjacent) — exactly what a reader means by it. `mode="all"` joins the quoted terms with
`AND`, `any` with `OR`, `phrase` quotes the whole query, and `raw` passes the caller's own FTS5
syntax through.

The hybrid mode fuses the two legs with reciprocal-rank fusion keyed on `(url, seq)` — the
same unit reached by both legs scores higher than a unit reached by one — and reports a `legs`
count on each hit so a caller can see whether a result was corroborated. The keyword rows
travel in `docsets.db`, so the other boxes receive them on the next replication push without
re-embedding anything.

On the golden set the misses that the lexical leg addresses are exactly the exact-token ones:
`CLAUDE_CODE_SYNC_SKILLS` (question 3), `--append-system-prompt` (question 7) and the
`plugin marketplace add` command (question 8) each land the defining row first in keyword mode.
Question 1 (Windows install) remains a ranking problem in the vector leg and is the case the
hybrid mode exists for.

## What the lint found

The lint's `P11` (retrieval readiness) is a live pass: it probes the facts file with the exact
tokens its own descriptions name and expects a hit. Before the keyword layer, a `P11` probe
for `X-Markdown-Tokens` or `describedby` against the llms.txt topical file depended on the
embedding treating a hyphenated header name as meaningful; after it, the probe is a BM25
lookup and hits deterministically. `P3`/`D2` (descriptions name the exact tokens the reader
will search for) is the producer-side half of the same rule: if the index does not contain the
token, no index can be searched for it.

## Lessons

- Quote every term before handing it to FTS5; the sub-token phrase is what the user meant, and
  the unquoted form is either an error or a wildcard.
- A second retrieval leg should share the store and the ids of the first, or fusion has nothing
  to join on; `(url, seq)` was already the unit key, so RRF cost nothing.
- Keyword lookups are the right default for exact-token questions — variable names, flags,
  error strings, header names — and cost no embedding call.
- Hub vectors and docset vectors use different models (768-d `nomic-embed-text` in `hub.db`,
  1,024-d `mxbai-embed-large` in the docset stores); querying one with the other's embeddings
  silently returns nothing, and the keyword layer is immune to that class of mistake.
- Fusion should report its legs: a hit reached by both legs is evidence, a hit reached by one
  is a candidate.

## Reproduce

`hub/scripts/docset_indexer.py` (`fts_match`, `SqliteStore.keyword_query`,
`ChromaStore.keyword_query`) is vendored here with `hub/tests/test_docset_keyword.py`. Recipes
03 (keyword via MCP) and 04 (hybrid via MCP) in the examples cookbook show the call shapes;
recipe 07 covers the facts-to-RAG path and the embedding-model trap.
