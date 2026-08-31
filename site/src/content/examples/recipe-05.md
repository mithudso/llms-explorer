---
title: "Recipe 05 — Index-first agent over MCP"
description: "hub_docset_index → read sections → the section's llms.txt → the page. The pattern a concept-tree node page uses to find a source without any search index."
section: examples
order: 5
date: "2026-08-31"
tags: ["mcp", "index", "agent", "sections"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/mcp-server/hub_mcp_server.py"
---

## Goal

Let an agent orient itself on a hub-hosted family the way spec v2 says an agent should:
read the index, follow at most two links. `hub_docset_index(docset)` returns the exported
`llms.txt` and, for a split family, a `sections` list; passing `file="<slug>/llms.txt"`
returns the section index; the page is then a read. No embedding, no keyword index — just
the files the exporter wrote.

## When not to use it

- You need a specific fact rather than the right page. The facts layer with keyword or
  hybrid ([recipe-03](/examples/recipe-03/), [recipe-04](/examples/recipe-04/)) is one call
  and lands on the unit.
- The family is not on the hub. For a public site, [recipe-01](/examples/recipe-01/) and
  [recipe-02](/examples/recipe-02/) do the same hops over HTTP.
- You want whole-corpus reasoning within a budget. Ask for `file="llms-small.txt"` and
  read once (~50k tokens) instead of hopping.

## Steps

1. `hub_docset_index("code.claude.com")` — the root index. The reply's `sections` field
   lists the section files for a split root.
2. Choose a section from the counts on its line (pages, tokens) and the titles it quotes.
3. `hub_docset_index("code.claude.com", file="agent-sdk/llms.txt")` — the section index,
   which links pages.
4. Open the page with `hub_llms_full_read(key, page=<url>)`, or fetch its `.md` twin from
   the served URL in the reply.

```
hub_docset_index(docset="code.claude.com")
```

```
# code.claude.com documentation
> A decision map for administrators deploying Claude Code, …
Generated from a mirror of code.claude.com by docset_refine on the hub; 191 pages. Companion files: llms-full.txt (all pages), llms-small.txt (reference pages within ~50k tokens), llms-facts.txt (extracted units).

## Sections
- [Overview](overview/llms.txt): 137 pages, ~7,460 tokens — Set up Claude Code for your organization, …
- [Agent Sdk](agent-sdk/llms.txt): 31 pages, ~1,615 tokens — How the agent loop works, Use Claude Code features in the SDK, Track cost and usage and 28 more
- [Whats New](whats-new/llms.txt): 22 pages, ~1,388 tokens — Week 13 · March 23–27, 2026, …

sections: ["overview/llms.txt", "agent-sdk/llms.txt", "whats-new/llms.txt"]
served: http://127.0.0.1:8788/d/code.claude.com/llms.txt
```

```
hub_docset_index(docset="code.claude.com", file="agent-sdk/llms.txt")
```

Other values `file` accepts: `llms-small.txt`, `llms-facts.txt`, `manifest.json` (byte and
token counts per file — the cheapest way to plan a budget), and any `<section>/llms.txt` the
reply listed. `llms-full.txt` is never returned inline; it can be millions of tokens, and the
reply gives its served URL instead.

## Expected output

Three replies: the root (~280 tokens), the section index (~1,615 tokens, 31 page links with
extractive descriptions), and the page. The agent has read about 2k tokens of navigation to
land on a 3k-token page, which is the whole point of the ladder — and the `manifest.json`
read, if you make it, tells you in advance that the alternative (`llms-full.txt`) would have
been ~2.1M tokens.

## Cost

Measured from `manifest.json`: root 280 tokens, `agent-sdk/llms.txt` 1,615 tokens,
`overview/llms.txt` 167 tokens (it is itself split into `part-N` files of 3,311 / 2,950 /
1,032 tokens). Three tool calls, zero embeddings, zero model tokens spent on retrieval; the
model spends only what it reads.

> Runnable in step 4 (playground).
