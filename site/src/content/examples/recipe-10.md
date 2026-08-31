---
title: "Recipe 10 — A local hub in miniature"
description: "Ollama, the docset indexer, a keyword layer and llms_serve.py on one machine: the whole retrieval stack for one family, offline and private."
section: examples
order: 10
date: "2026-08-31"
tags: ["local", "ollama", "indexer", "serve"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "docs/site/components/17-semantic-indexer.md"
  - "hub/scripts/docset_indexer.py"
  - "hub/scripts/llms_serve.py"
---

## Goal

Run everything the hosted hub does for one family on a laptop: acquire a site into a
mirror, export its llms family, build the vector and keyword layers, and serve the files
with the right headers. Nothing leaves the machine; the only model is a local embedding
model. This is the same code the hub runs, in the order the pipeline runs it.

## When not to use it

- The family is already on the hub and you can reach it. The MCP tools
  ([recipe-05](/examples/recipe-05/)) skip all of this.
- You need the model passes (`units`, `polish`). They want a local generation model
  (`qwen3.5:35b` by default) and hours; the deterministic export below needs neither.
- You want many sites. The pipeline manager places mirror jobs across a box pool; this
  recipe is one machine, one family.

## Steps

1. **Embedding model.** Install Ollama and pull the docset model. It is
   `mxbai-embed-large` (1024d); do not substitute `nomic-embed-text`, which the hub
   reserves for its file corpus and which produces vectors nothing here can read.

   ```
   ollama pull mxbai-embed-large
   export HUB_OLLAMA_URLS=http://127.0.0.1:11434
   export HUB_EMBED_MODEL=mxbai-embed-large
   ```

2. **Acquire.** Prefer the site's own llms files; fall back to a crawl. Both write one
   banner mirror. `llms_acquire.py` is the llms-first half and ships with the hub (stdlib
   only, no venv needed):

   ```
   python3 scripts/llms_acquire.py https://code.claude.com/docs mirrors/code.claude.com.md
   ```

   It prints `{"method": "llms-full"|"llms"|null, "pages": n, "failed": n}`; `method: null`
   means the site publishes neither and you need the crawl fallback,
   `text_mirror.py --prefer-llms`, which lives in the `web-text-mirror` skill
   (`~/.claude/skills/web-text-mirror/scripts/`) rather than under `hub/scripts/`.

3. **Export.** Clean, extract, render, export — no model tokens.

   ```
   PYTHONPATH=scripts .venv/bin/python -m docset_refine all --no-units mirrors/code.claude.com.md
   ```

   → `mirrors/code.claude.com.llms/{llms,llms-full,llms-small,llms-facts}.txt` + `manifest.json`.

4. **Index both layers.** The raw layer from the mirror, the facts layer from the extracted
   units, then a keyword index beside each.

   ```
   .venv/bin/python scripts/docset_indexer.py index mirrors/code.claude.com.md --name code.claude.com
   .venv/bin/python scripts/docset_indexer.py index mirrors/code.claude.com.reference/all_units.jsonl --units --name code.claude.com
   .venv/bin/python scripts/docset_indexer.py keyword-index code.claude.com --layer facts
   .venv/bin/python scripts/docset_indexer.py keyword-index code.claude.com --layer raw
   ```

   `--name` sets the store key verbatim, so the local family is `code.claude.com` and its
   facts twin `code.claude.com__facts`. Without it the key is derived —
   `<host-slug>__<stem-slug>`, which is why the hosted family in
   [recipe-03](/examples/recipe-03/) answers to `codeclaudecom__codeclaudecom`.

5. **Serve.** Markdown headers on every response, the family under `/d/<stem>/`.

   ```
   .venv/bin/python scripts/llms_serve.py --host 127.0.0.1 --port 8788
   ```

6. **Query.** All three modes, no network.

   ```
   .venv/bin/python scripts/docset_indexer.py keyword code.claude.com "CLAUDE_CODE_SYNC_SKILLS" --layer facts --mode phrase
   .venv/bin/python scripts/docset_indexer.py query   code.claude.com "how do I get my claude.ai skills onto this machine?" --layer facts
   curl -sI http://127.0.0.1:8788/d/code.claude.com/llms.txt
   ```

## Expected output

After step 3, `manifest.json` lists every file with bytes and tokens (for this site: 191
pages, an index of 1,136 bytes / 280 tokens, small at 49,785 tokens, full at 2,097,403, and
14,031 units). After step 4, `docset_indexer.py list` shows `code.claude.com` and
`code.claude.com__facts` with their counts. After step 5:

```
HTTP/1.0 200 OK
Content-Type: text/markdown; charset=utf-8
X-Markdown-Tokens: 284
Link: <http://127.0.0.1:8788/d/code.claude.com/llms.txt>; rel="describedby"
```

`X-Markdown-Tokens` is the server's own `len(bytes) // 4`, so it can differ by a token or two
from the manifest's count for the same file — 284 against 280 here.

The keyword query prints the `CLAUDE_CODE_SYNC_SKILLS` parameter unit with its `url#anchor`
(`…/docs/en/env-vars#variables`), exactly as the hosted tool does in
[recipe-03](/examples/recipe-03/).

## Cost

Estimated on a laptop: the pull is ~670 MB once; export is seconds; indexing is one
embedding per chunk and per unit — for this family ~14k units plus ~2k raw chunks, on the
order of 10–20 minutes on Apple silicon, a couple of minutes on a GPU host. Serving and
keyword queries are free. Disk: the mirror and family total ~12 MB; the Chroma collections a
few hundred MB.

> Runnable in step 4 (playground).
