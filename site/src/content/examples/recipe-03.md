---
title: "Recipe 03 — Keyword layer from Claude Code"
description: "Find an exact token — an env var, a flag, an error string — with hub_query_docset(mode=\"keyword\"), then open the page it came from. Zero model tokens."
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

Answer "where is `CLAUDE_CODE_SYNC_SKILLS` documented?" without an embedding call. The
keyword layer is an FTS5 index (BM25 ranking) built beside each docset's vector layer; a query
in `mode="keyword"` is a sub-token match over the facts layer, returns the unit's snippet and
its `url#anchor`, and costs microseconds.

## When not to use it

- The question is a paraphrase. "The variable that pulls my claude.ai skills down" contains
  none of the tokens in `CLAUDE_CODE_SYNC_SKILLS`; use hybrid
  ([recipe-04](/examples/recipe-04/)).
- The docset has no facts layer yet. Keyword still works over the raw chunks, but the hits
  are chunks, not anchored units — `layer` in the reply says which answered.
- You want the whole page. The keyword hit tells you *which* page; the read is the second
  call below.

## Steps

1. Call `hub_query_docset` with the token and `mode="keyword"`. `docset` is the store key,
   `<host-slug>__<mirror-stem-slug>` — for this mirror `codeclaudecom__codeclaudecom`, not the
   host name; a friendly name returns `no such docset`. The index is built on first use
   (`docset_indexer keyword-index` under the hood), so the first call on a docset is slower
   once.
2. Read `url` and `snippet` off the top hit — those are the fields a keyword hit carries
   (`score`, `url`, `seq`, `snippet`); `text`, `unit_type` and `origin` come back from the
   semantic and hybrid legs instead. The URL carries the anchor.
3. Open the page with `hub_llms_full_read(key, page=<url>)`. That `key` is the llms-full
   catalog key from `hub_llms_full_list` (`code.claude.com__docs`), a different namespace from
   the docset key; `page` matches by exact source URL or a case-insensitive title substring.

From a Claude Code session with the `global_ai_hub` server connected:

```
hub_query_docset(docset="codeclaudecom__codeclaudecom", question="CLAUDE_CODE_SYNC_SKILLS", mode="keyword", top=3)
```

The reply is JSON. Verbatim, run against this hub on 2026-08-31 — nothing dropped:

```json
{
  "docset": "codeclaudecom__codeclaudecom",
  "layer": "facts",
  "queried": "codeclaudecom__codeclaudecom__facts",
  "mode": "keyword",
  "results": [
    {
      "score": 15.2427,
      "url": "https://code.claude.com/docs/en/env-vars#variables",
      "seq": 8391,
      "snippet": " … Timeout in milliseconds for a mid-session skills resync when `[CLAUDE_CODE_SYNC_SKILLS]` is set (default: 30000). Bounds the download triggered when the … "
    },
    {
      "score": 14.651,
      "url": "https://code.claude.com/docs/en/env-vars#variables",
      "seq": 8392,
      "snippet": " … Timeout in milliseconds for the first query to wait for the initial skill list when `[CLAUDE_CODE_SYNC_SKILLS]` is set (default: 5000). When … "
    },
    {
      "score": 14.3472,
      "url": "https://code.claude.com/docs/en/env-vars#variables",
      "seq": 8390,
      "snippet": " … Before it runs the first query, Claude Code waits up to `[CLAUDE_CODE_SYNC_SKILLS]_WAIT_TIMEOUT_MS` for the list of your skills … "
    }
  ]
}
```

The square brackets are FTS5's `snippet()` match markers, not part of the text; the leading
and trailing ` … ` are its elision markers, so a snippet is a window around the match rather
than the whole unit.

Read the ranking honestly: all three hits are on the same page, and the variable you asked
for is *third*. Units 8391 and 8392 are `CLAUDE_CODE_SYNC_SKILLS_INSTALL_TIMEOUT_MS` and
`…_WAIT_TIMEOUT_MS`; unit 8390 is `CLAUDE_CODE_SYNC_SKILLS` itself. BM25 rewards the token in
a shorter field, so the two timeout units outscore the variable they refer to. That costs
nothing here, because all three carry the same `url#anchor` — keyword tells you *which page*,
and the anchor is identical whichever of the three you take.

Then, to open the page behind the top hit:

```
hub_llms_full_read(key="code.claude.com__docs", page="https://code.claude.com/docs/en/env-vars")
```

That returns an envelope, not raw markdown. The real fields on this call, with `text` cut
here (it is 20,000 characters):

```json
{
 "key": "code.claude.com__docs",
 "url": "https://code.claude.com/docs/llms-full.txt",
 "page_title": "Environment variables",
 "page_url": "https://code.claude.com/docs/en/env-vars",
 "total_chars": 475588,
 "truncated": true,
 "text": "Reference for environment variables that control Claude Code behavior.\n\nEnvironment variables can control Claude Code behavior such as model selection, authentication, request routing, and feature toggles. …  ← truncated here for the page; the tool returned 20,000 characters"
}
```

The `# Title` / `Source:` lines are the grammar the tool *matches* on inside `llms-full.txt`;
they are lifted into `page_title` and `page_url` rather than left in `text`, so `text` starts
at the page body. `total_chars` is the page's full length and `truncated` says whether you got
all of it — continue with `offset`, or raise `limit`.

The same two calls from the shell, for a script:

```
.venv/bin/python scripts/docset_indexer.py keyword codeclaudecom__codeclaudecom "CLAUDE_CODE_SYNC_SKILLS" --layer facts --mode phrase --top 3
```

`--mode` is `any | all | phrase | raw`; `phrase` is what an exact token wants.

## Expected output

Every hit's URL ends in the heading that documents the variable
(`/docs/en/env-vars#variables`), and the reply's `layer` names which layer answered (`facts`)
while `queried` names the collection it actually read (`…__facts`). The corresponding line in
the export's `llms-facts.txt` is typed `[parameter]` — line 11,378 of that file begins
``- [parameter] `CLAUDE_CODE_SYNC_SKILLS`: Set to `1` …`` — but keyword hits do not carry the
type, so ask for `mode="hybrid"` or `"semantic"` when you want `unit_type` on the hit. What a
keyword hit does carry is exactly `score`, `url`, `seq`, `snippet`, as above.

The full-read then lands you on that page: `page_title` comes back as `"Environment
variables"`, `page_url` as the URL you asked for, so the anchor from the hit resolves to a
heading you can see in `text`.

If `layer` says `raw`, the docset has no facts layer; the hit is still correct but is a text
chunk without an anchor. That is the signal to run `extract → export` on it.

## Cost

Measured on the hub: the FTS5 lookup is sub-millisecond after the index exists; the first
call on a docset builds the index (seconds for this family's 14,031 units). Zero model
tokens, zero embeddings. The page read is bounded by `limit`, which defaults to 20,000
characters — about 5k tokens — and is capped at 200k by the tool. The env-vars page above is
475,588 characters, so the default read came back `"truncated": true`; a shorter reference
page returns whole.

> Runnable in step 4 (playground).
