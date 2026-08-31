---
title: "Recipe 04 — Hybrid: keyword and vector fused"
description: "For a paraphrased or uncertain question, mode=\"hybrid\" runs the keyword and vector legs and fuses them with reciprocal-rank fusion; legs == 2 tells you both agreed on a hit."
section: examples
order: 4
date: "2026-08-31"
tags: ["mcp", "hybrid", "rrf", "vector"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/mcp-server/hub_mcp_server.py"
  - "hub/scripts/semantic_ops/fuse.py"
---

## Goal

Ask a question in your own words — "how do I know how big a markdown page will be before
I fetch it?" — and get the unit about `X-Markdown-Tokens` even though the question never
says the token. `mode="hybrid"` embeds the question once, runs the vector leg over the facts
layer, runs the keyword leg over the same layer, and fuses the two rankings with reciprocal
rank fusion. A hit that appears in both legs carries `legs: 2`; that agreement is the
cheapest confidence signal the hub has.

## When not to use it

- The question *is* the token. Hybrid pays for an embedding the keyword leg does not need;
  use [recipe-03](/examples/recipe-03/).
- You want to read, not find. Once you have the URL the read is `hub_llms_full_read`.
- The docset has neither layer indexed. Hybrid over nothing returns nothing; index first
  ([recipe-10](/examples/recipe-10/)).

## Steps

1. Call `hub_query_docset` with the natural-language question and `mode="hybrid"`. Leave
   `layer="auto"` so the facts layer answers when it exists.
2. Sort by the fused score the reply already applied; look at `legs` on each hit.
3. A `legs: 2` hit is the answer. A `legs: 1` hit from the vector leg alone means the
   source phrased it differently from you; from the keyword leg alone means you happened to
   share a rare token — check the snippet.

```
hub_query_docset(
  docset="code.claude.com",
  question="how do I know how big a markdown page will be before I fetch it?",
  mode="hybrid", top=5,
)
```

reply (abridged):

```
layer: facts   mode: hybrid   embedding: mxbai-embed-large   hits: 5
1. legs: 2  [parameter] X-Markdown-Tokens — response header carrying the page's token estimate (chars/4)
   https://code.claude.com/docs/en/claude-code-on-the-web#markdown-responses
2. legs: 1 (vector)  [fact] llms-small.txt keeps reference pages within ~50k tokens …
   https://…
3. legs: 1 (keyword) [snippet] curl -I … | grep -i markdown
   https://…
```

The same from the shell is two commands and a fuse, which is why the MCP tool exists:

```
.venv/bin/python scripts/docset_indexer.py query   code.claude.com "how big is a markdown page before I fetch it" --layer facts
.venv/bin/python scripts/docset_indexer.py keyword code.claude.com "markdown page size" --mode any
```

## Expected output

The top hit has `legs: 2` and the same URL the keyword recipe found. The lower hits show
what each leg contributes on its own: the vector leg surfaces the *small* budget (meaning,
not spelling), the keyword leg surfaces a code snippet that shares a token. The reply names
the embedding model; if it names `nomic-embed-text` for a docset, something is misconfigured
— docsets are `mxbai-embed-large` (1024d), and the two do not mix.

## Cost

Measured: one embedding call (the question, ~20 tokens through `mxbai-embed-large` on the
pool's nearest host — tens of milliseconds on the GPU box, hundreds on a laptop), plus the
keyword lookup (sub-millisecond). Zero generation tokens. The fusion is arithmetic.

> Runnable in step 4 (playground).
