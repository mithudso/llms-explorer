---
title: "Which layer answers which question"
description: "The decision table for the cookbook: match the shape of your question to the cheapest llms layer that answers it, then open the recipe."
section: examples
order: 0
date: "2026-08-31"
tags: ["cookbook", "decision-table", "cost"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "outputs/exports/code.claude.com.llms/manifest.json"
---

Every llms family has a ladder of layers — index, split root, small, full, facts, topical,
vocabulary — and beside them two retrieval modes over the facts, keyword and vector. The
cheapest layer that answers your question is the right one. This table matches the shape of
a question to that layer and to the recipe that shows it. Recipes are copy-only in this step:
the code illustrates, the cost line states what was measured or estimated, and each recipe
closes with the note that it becomes runnable in the playground step.

## The table

| question shape | layer | cost class | recipe |
|---|---|---|---|
| Orientation before any retrieval: what does this site cover, where do I start | `llms.txt` (≤ 10 KB) then ≤ 2 hops to a `.md` twin | ~3k tokens, 3 requests, 0 embeddings | recipe-01 |
| Orientation on a site whose index split into sections (`## Sections` present) | split root: root index → `<slug>/llms.txt` → page | ~3–5k tokens, 3–4 requests | recipe-02 |
| An exact token: an env var, a flag, a header name, an error string | keyword layer (`mode="keyword"`, FTS5/BM25) over `llms-facts.txt` | microseconds, 0 model tokens, 0 embeddings | recipe-03 |
| A paraphrased question, or mixed / unsure whether the words match the source | hybrid (`mode="hybrid"`, RRF over keyword + vector), or vector alone (`layer="facts"`) | 1 embedding, 0 generation tokens | recipe-04 |
| An agent that must find the right page from an MCP client without a search index | index-first via `hub_docset_index` → `sections` → section index → page | ~2k tokens read per hop, 0 embeddings | recipe-05 |
| A scripted check or query from a shell or a CI step | the `llmsx` CLI (today: the hub scripts it wraps) | seconds; 0 model tokens for lint / keyword | recipe-06 |
| Citation-grade answers inside your own RAG store | `llms-facts.txt` units, one document each, `url#anchor` as metadata | 1 embedding per unit at ingest; ~845k tokens for a 191-page site | recipe-07 |
| Keeping a published file honest on every push | the lint as a GitHub Action gate (exit 1 on High) | ~10 s per file; network only with `--check-links` | recipe-08 |
| Serving the files so agents and the lint can find them | headers: `text/markdown`, `X-Markdown-Tokens`, `Link: rel="describedby"`, `rel="alternate"` on HTML | one config block; verify with `curl -I` | recipe-09 |
| Whole-corpus reasoning, offline and private, within a token budget | a local hub: Ollama + indexer + keyword layer + `llms_serve.py`; `llms-small.txt` for budgeted reads | one machine; ~50k tokens per small read, 0 API spend | recipe-10 |
| One concept across many sources, disagreements visible | a topical file (`/t/<slug>/`) built from a fact pool | minutes to build; `--no-embed` for 0 embeddings | recipe-11 |
| Disambiguation: which sense of a word this family means, and its aliases | `llms-vocabulary.txt` senses and `aka:` expansion before FTS5 | free: string match, 0 model tokens | recipe-12 |

## How to read it

- **Start at the top.** The first three rows are almost always enough. An index read plus
  two hops answers "what is here"; a keyword lookup answers "what is the exact flag". Only
  when the words in your question may not be the words in the source do you pay for an
  embedding.
- **Cost class is honest, not precise.** Token counts are chars/4, the same estimator the
  hub writes into `manifest.json`. Where a recipe has a measured figure it says *measured*;
  where it does not, it says *estimated*. The CI in a later step replaces every estimate with
  a run.
- **Two shapes have no recipe of their own.** *Whole-corpus reasoning* against a hosted
  family is `hub_docset_index(docset, file="llms-small.txt")` (recipe-05 shows the call);
  a *full-file read* is `hub_llms_full_read(key, page=…)` for one page at a time (recipe-03
  shows it). Both are one call, not a recipe.
- **Every layer's numbers, for one real family.** From
  `outputs/exports/code.claude.com.llms/manifest.json` (191 pages, acquired from the
  publisher's `llms-full.txt`): root index ~280 tokens; the three section indexes ~167,
  ~1,615 and ~1,388 tokens; `llms-small.txt` ~49,785 tokens; `llms-full.txt` ~2,097,403
  tokens; `llms-facts.txt` 14,031 units, ~844,553 tokens. The gap between the first line and
  the last is the whole argument for reading the index first.

## When the table is the wrong tool

If the question is "is this file any good", none of these rows apply — that is the
[lint](/reference/passes/), not a retrieval. If the question is "what do many sites say
about X", the source-axis rows do not apply either; recipe-11 and the [CLLMS
essay](/essays/cllms-vs-proprietary/) cover the concept axis. And if the corpus is not
published as an llms family at all, the first step is to make one (recipe-10 in miniature,
`docset_refine export` at scale), after which every row above starts to work.
