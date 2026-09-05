---
title: "Semantic indexing: two legs and a fusion"
description: "A docset can be asked a question by token or by meaning, and the two ways fail in opposite directions. What each leg costs, where each breaks, why reciprocal-rank fusion is the default, and how to read the recorded run at /demo/."
date: "2026-08-31"
tags: ["retrieval", "bm25", "embeddings", "rrf", "hybrid", "demo"]
sources:
  - "docs/site/components/16-semantic-demo.md"
  - "docs/superpowers/specs/2026-08-30-docset-golden-baseline.md"
  - "hub/mcp-server/hub_mcp_server.py"
  - "hub/scripts/docset_indexer.py"
  - "site/tools/gen_demo.py"
---

Retrieval arguments usually run on assertion: someone says embeddings understand meaning,
someone else says keyword search is fine, and neither side shows a query. The demo at
[`/demo/`](/demo/) is the same eleven questions run three ways against one indexed docset,
with the hits and the timings kept. This essay is what to look for in it.

## The two legs

A docset in the hub is indexed twice over the same units.

The **keyword leg** is SQLite FTS5 with BM25 ranking. A question becomes an OR of its terms,
the index returns the rows that contain them, and BM25 ranks by term rarity against document
length. It is exact: `CLAUDE_CODE_SYNC_SKILLS` matches the row that literally contains
`CLAUDE_CODE_SYNC_SKILLS`, and no row that does not. It costs no model call — sub-millisecond
on a single rare token in the recorded run, and tens of milliseconds on a six-word question,
because cost scales with how many terms have to be unioned.

The **vector leg** embeds the question with the same model the docset was indexed with and
ranks units by cosine similarity. It matches on meaning, so a question that shares no words
with its answer still finds it. Its cost is one embedding call and is almost independent of
the question: in the recording every vector query *after the first* lands in the same narrow band
whether the question is one token or nine words. The first pays the one-off cost of opening the
connection to the embedding host — 124 ms against a median of 15 — and is marked as such on the
demo page; read it as a connection cost, not a retrieval cost.

Their failure modes are mirror images. BM25 cannot find a page that phrases the answer
differently. Embeddings dilute a lone identifier into a low-signal vector, and a docset full
of near-identical config rows gives it many almost-equally-good answers. This is why the
exact-token probes in `/ldo` pass P11 exist at all: they are the class that a vector index
quietly gets wrong.

## Fusing them

The hub's default is neither leg alone. `hub_query_docset(mode="hybrid")` runs both and fuses
them with **reciprocal-rank fusion**: each hit scores `1 / (60 + rank)` in each list it
appears in, and the scores add, keyed by `(url, seq)`. No score from either leg survives the
fusion — only the ranks — which is the point. BM25 scores and cosine similarities are not on
a comparable scale, and any attempt to weight one against the other is a knob nobody can
tune honestly. Rank agreement needs no scale: a unit that both legs put near the top beats
a unit that only one leg loves.

The recording shows the mechanism working in the least glamorous way. The two legs agreed on
the top hit for only two of the eleven questions; for two others the fused winner was the top
hit of *neither* leg — a unit each leg ranked second or third, promoted past two disagreeing
favourites because both legs voted for it.

## What the recording shows

Read [`/demo/`](/demo/) with three questions in mind.

- **Does the cheap leg already answer it?** For the exact-token probes it usually does, first
  hit, with the value in the snippet — and it does so without touching a model. An agent that
  reaches for an embedding call to look up an environment variable is paying for nothing.
- **Where does the paraphrase leg earn its cost?** Look at the hook questions. BM25 ranks a
  *Debug hooks* prose row first because it contains every word in the question; the vector leg
  puts the exit-code table row first, which is the answer. That is the whole case for
  embeddings in one comparison.
- **What did fusion change?** The `legs` count on a hybrid hit says how many legs found it.
  Hits with two legs are the ones the fusion is built to promote; a hybrid list of all
  one-leg hits means the legs never agreed, and the fusion is doing nothing but interleaving.

Two honest caveats. The timings are a single run on a single laptop with one local embedding
host, so the ratios between the legs are the finding and the absolute milliseconds are not (and
the first query pays the connection cost noted above). And this is a
recording, dated on the page — it is not a live endpoint, and it will not be one until the
query API arrives.

## Run it yourself

Everything on the demo page comes from one command against an indexed docset, so the same
comparison can be run over yours. The keyword index is built on first use; the facts layer is
preferred automatically when a docset has one.

```
# the cheap leg — FTS5/BM25, no model call
docset_indexer.py keyword <docset> "CLAUDE_CODE_SYNC_SKILLS"

# the meaning leg — one embedding call, then cosine
docset_indexer.py query <docset> "which hook events fire once per turn" --layer auto

# both, fused — what hub_query_docset serves by default
hub_query_docset(docset=..., question=..., mode="hybrid")
```

The recording itself is regenerated with `site/tools/gen_demo.py`, which is the one generator
in this site that reads a live hub and therefore the one that never runs in CI: it is run by
hand on a box that has the indexes, and its output is committed. See
[the reference](/reference/) for the surrounding commands.
