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

Ask a question in your own words — "which environment variable downloads my claude.ai skills
automatically?" — and get the unit about `CLAUDE_CODE_SYNC_SKILLS` even though the question
never says the token. `mode="hybrid"` embeds the question once, runs the vector leg over the facts
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
3. A `legs: 2` hit is the answer. A `legs: 1` hit that carries `unit_type` came from the
   vector leg alone — the source phrased it differently from you. A `legs: 1` hit with no
   `unit_type` and a `[bracketed]` `snippet` came from the keyword leg alone — you shared
   tokens with it; read the snippet before you trust it.

```
hub_query_docset(
  docset="codeclaudecom__codeclaudecom",
  question="which environment variable downloads my claude.ai skills automatically?",
  mode="hybrid", top=5,
)
```

The reply is JSON. Verbatim, run against this hub on 2026-08-31 — nothing elided. The `…`
ending the first hit's `text` is the extractor's own truncation marker, stored in the unit,
not an edit of ours:

```json
{
  "docset": "codeclaudecom__codeclaudecom",
  "layer": "facts",
  "queried": "codeclaudecom__codeclaudecom__facts",
  "mode": "hybrid",
  "results": [
    {
      "score": 0.03151,
      "url": "https://code.claude.com/docs/en/env-vars#variables",
      "seq": 8390,
      "text": "`CLAUDE_CODE_SYNC_SKILLS`: Set to `1` to download your enabled claude.ai skills into `~/.claude/skills/synced/` and resync every 10 minutes. Before it runs the first query, Claude Code waits up to `CLAUDE_CODE_SYNC_SKILLS_WAIT_TIMEOUT_MS` for the list of your skills. The downloads themselves finish in the background, and Claude waits for a skill's download when it invokes that skill. The…",
      "unit_type": "parameter",
      "origin": "table",
      "legs": 2
    },
    {
      "score": 0.01639,
      "url": "https://code.claude.com/docs/en/skills#where-synced-skills-load",
      "seq": 4961,
      "text": "Confirm the skills load in a local session — Start an interactive session, without `CLAUDE_CODE_SYNC_SKILLS` set, and run `/skills`. The menu lists the downloaded skills under `claude.ai sync`.",
      "unit_type": "definition",
      "origin": "heading",
      "legs": 1
    },
    {
      "score": 0.01639,
      "url": "https://code.claude.com/docs/en/skills#where-synced-skills-load",
      "seq": 4959,
      "snippet": " … Claude Code [downloads] only the [skills] you enabled, and it needs your [claude.ai] sign-in to download them.",
      "legs": 1,
      "text": " … Claude Code [downloads] only the [skills] you enabled, and it needs your [claude.ai] sign-in to download them."
    },
    {
      "score": 0.01613,
      "url": "https://code.claude.com/docs/en/cloud-environments#what-carries-over-from-your-setup",
      "seq": 7927,
      "text": "Your user `~/.claude/skills/`, `~/.claude/agents/`, `~/.claude/commands/`: Available in cloud sessions=No; Why=Live on your machine, not in the repo. Commit them to the repo's `.claude/` directory instead. Cloud sessions automatically load skills you enable on claude.ai",
      "unit_type": "parameter",
      "origin": "table",
      "legs": 1
    },
    {
      "score": 0.01587,
      "url": "https://code.claude.com/docs/en/features-overview#compare-similar-features",
      "seq": 2766,
      "text": "**Loads**: CLAUDE.md=Every session, automatically; Skill=On demand",
      "unit_type": "parameter",
      "origin": "table",
      "legs": 1
    }
  ]
}
```

Hits are not uniform, and the shape tells you which leg produced them. A hit the vector leg
saw carries `unit_type` and `origin`; a hit only the keyword leg saw (seq 4959) carries a
`snippet` with FTS5's `[…]` match markers, has that snippet copied into `text`, and has no
`unit_type` at all. Sort on `legs` before you sort on anything else.

`docset` is the store key (`<host-slug>__<mirror-stem-slug>`), not the host name — the same
rule as [recipe-03](/examples/recipe-03/).

The same from the shell is two commands and a fuse, which is why the MCP tool exists:

```
.venv/bin/python scripts/docset_indexer.py query   codeclaudecom__codeclaudecom "which environment variable downloads my claude.ai skills automatically?" --layer facts
.venv/bin/python scripts/docset_indexer.py keyword codeclaudecom__codeclaudecom "environment variable claude.ai skills download" --layer facts --mode any
```

## Expected output

The top hit has `legs: 2` and the same URL the keyword recipe found — and neither leg put it
first on its own. Re-run the same question in `mode="semantic"` and `mode="keyword"` and the
unit (seq 8390) comes back **5th** in the vector leg, behind three units that talk about
skills without naming the variable, and **2nd** in the keyword leg, behind a sentence that
happens to repeat "downloads" and "skills". The fusion is what promotes it: RRF with `k = 60`
scores it `1/(60+5) + 1/(60+2) = 0.03151`, which is exactly the `score` in the reply, and
nearly twice the next hit's `0.01639`. Agreement across two mediocre rankings beat either
ranking's own winner — that is the whole argument for hybrid.

The lower hits show what each leg contributes on its own: the vector leg surfaces the prose
definitions and the table rows that mean the same thing (seq 4961, 7927, 2766), the keyword
leg surfaces the sentence that shares the tokens (seq 4959). `legs` is added by the fusion, so
it is present only in `mode="hybrid"`.

Phrasing moves the answer. Ask the same thing as "how do I get my claude.ai skills onto this
machine automatically?" and the env-vars unit drops out of the top 5 entirely — the fusion
returns the `#skills-synced-from-claudeai` section heading with `legs: 2` instead, which is
the right *page* and the wrong *line*. Naming the kind of thing you want ("environment
variable") is worth more to the vector leg than any amount of politeness.

The reply does not name the embedding model — the tool picks the model the docset was indexed
with (`store.docset_model(key)`), never the environment default, which is what keeps a 1024-d
`mxbai-embed-large` docset from being queried with a 768-d `nomic-embed-text` vector. If a
docset was indexed with a different model the query raises an embedding-dimension mismatch
rather than returning nonsense.

## Cost

Measured: one embedding call (the question, ~20 tokens through `mxbai-embed-large` on the
pool's nearest host — tens of milliseconds on the GPU box, hundreds on a laptop), plus the
keyword lookup (sub-millisecond). Zero generation tokens. The fusion is arithmetic.

> Runnable in step 4 (playground).
