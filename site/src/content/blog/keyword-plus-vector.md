---
title: "Keyword plus vector: the cheap path"
description: "FTS5 adds token-phrase search without new embedding calls, while reciprocal-rank fusion combines keyword and vector rankings without independently verifying facts."
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
`irm … | iex` snippet was in the mirror. Cosine similarity does not guarantee that the literal-token line ranks first; this baseline showed cases where it did not.

The obvious fix is a lexical index. The constraint was cost: the facts layer is 56,489 units
across the estate, every one already embedded, and a second vector model was out of the
question. So the second index had to avoid new embedding calls and live in the same store. Building and querying it still use local CPU, disk, and maintenance effort.

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
order, adjacent). With the default tokenizer, case and punctuation are normalized: this is a token phrase, not a byte-for-byte match. [SQLite’s FTS5 documentation](https://www.sqlite.org/fts5.html#unicode61_tokenizer) describes that behavior. `mode="all"` joins the quoted terms with
`AND`, `any` with `OR`, `phrase` quotes the whole query, and `raw` passes the caller's own FTS5
syntax through.

The hybrid mode fuses the two legs with reciprocal-rank fusion keyed on `(url, seq)`. A unit receives the sum of `1 / (60 + rank)` from the lists that contain it, boosting agreement between rankings. It reports a `legs` count so callers can see retrieval agreement. Both legs search the same corpus; two hits are not independent corroboration of a fact. The keyword rows
travel in `docsets.db`, so the other boxes receive them on the next replication push without
re-embedding anything.

The dated run log reports that the lexical leg addresses these exact-token misses:
`CLAUDE_CODE_SYNC_SKILLS` (question 3), `--append-system-prompt` (question 7) and the
`plugin marketplace add` command (question 8) each land the defining row first in keyword mode.
Question 1 (Windows install) remains a ranking problem in the vector leg and is the case the
hybrid mode exists for.

## What the lint found

The lint's `P11` (retrieval readiness) is a live pass: it probes the facts file with the exact
tokens its own descriptions name and expects a hit. Before the keyword layer, a `P11` probe
for `X-Markdown-Tokens` or `describedby` against the llms.txt topical file depended on the
embedding treating a hyphenated header name as meaningful; after it, the probe is a BM25
lookup that can hit deterministically when the expected rows are indexed and the tokenized query matches them. It checks retrieval readiness, not the truth of the retrieved claim. `P3`/`D2` (descriptions name the exact tokens the reader
will search for) is the producer-side half of the same rule: lexical retrieval needs the expected tokens in the indexed text. Semantic retrieval can match related wording, but it does not guarantee an exact-token hit.

## Lessons

- Quote every term before handing it to FTS5; the sub-token phrase is what the user meant, and
  punctuation in an unquoted term can otherwise change the expression or make it invalid. Raw mode is for callers who intentionally write FTS5 syntax.
- A second retrieval leg should share the store and the ids of the first, or fusion has nothing
  to join on; `(url, seq)` was already the unit key, so RRF needed no new embedding calls, although fusion still does local work.
- Keyword lookups are the right default for exact-token questions — variable names, flags,
  error strings, header names — and cost no embedding call.
- Hub vectors and docset vectors use different models (768-d `nomic-embed-text` in `hub.db`,
  1,024-d `mxbai-embed-large` in the docset stores); querying one with the other's embeddings
  makes cosine comparison invalid. The current SQLite backend raises `embedding model mismatch` when all stored vectors have the wrong dimension; the keyword query needs no embedding vector.
- Fusion should report its legs: agreement between retrieval methods helps rank a candidate, but every retrieved claim still needs source verification.

## Reproduce

`hub/scripts/docset_indexer.py` (`fts_match`, `SqliteStore.keyword_query`,
`ChromaStore.keyword_query`) is vendored here with `hub/tests/test_docset_keyword.py`. Recipes
03 (keyword via MCP) and 04 (hybrid via MCP) in the examples cookbook show the call shapes;
recipe 07 covers the facts-to-RAG path and the embedding-model trap.
