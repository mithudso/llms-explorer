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

1. `hub_docset_index("codeclaudecom__codeclaudecom")` — the root index. `docset` is the store
   key (`<host-slug>__<mirror-stem-slug>`); a host name returns
   `{"docset": …, "error": "no such docset"}`. The reply's `sections` field lists every section
   file the export wrote, including the `part-N` files a large section is chopped into.
2. Choose a section from the counts on its line (pages, tokens) and the titles it quotes.
3. `hub_docset_index("codeclaudecom__codeclaudecom", file="agent-sdk/llms.txt")` — the section
   index, which links pages.
4. Open the page with `hub_llms_full_read(key, page=<url>)`, or fetch its `.md` twin from
   the served URL in the reply.

```
hub_docset_index(docset="codeclaudecom__codeclaudecom")
```

The reply is a JSON envelope around the file. Verbatim, run against this hub on 2026-08-31 —
the whole `text` field, nothing elided:

```json
{
 "docset": "codeclaudecom__codeclaudecom",
 "file": "llms.txt",
 "served_at": "http://127.0.0.1:8788/d/code.claude.com/llms.txt",
 "llms_full_url": "http://127.0.0.1:8788/d/code.claude.com/llms-full.txt",
 "chars": 1121,
 "truncated": false,
 "text": "# code.claude.com documentation\n\n> A decision map for administrators deploying Claude Code, covering API providers, managed settings, policy enforcement, usage monitoring, and data handling.\n\nGenerated from a mirror of code.claude.com by docset_refine on the hub; 191 pages. Companion files: llms-full.txt (all pages), llms-small.txt (reference pages within ~50k tokens), llms-facts.txt (extracted units).\n\n## Sections\n\n- [Overview](overview/llms.txt): 137 pages, ~7,460 tokens — Set up Claude Code for your organization, Orchestrate teams of Claude Code sessions, Manage multiple agents with agent view and 134 more\n- [Agent Sdk](agent-sdk/llms.txt): 31 pages, ~1,615 tokens — How the agent loop works, Use Claude Code features in the SDK, Track cost and usage and 28 more\n- [Whats New](whats-new/llms.txt): 22 pages, ~1,388 tokens — Week 13 · March 23–27, 2026, Week 14 · March 30 – April 3, 2026, Week 15 · April 6–10, 2026 and 19 more\n\n## Optional\n\n- [Claude Code changelog](https://code.claude.com/docs/en/changelog.md): Release notes for Claude Code, including new features, improvements, and bug fixes by version.",
 "sections": [
  "agent-sdk/llms.txt",
  "overview/llms.txt",
  "overview/part-1/llms.txt",
  "overview/part-121/llms.txt",
  "overview/part-61/llms.txt",
  "whats-new/llms.txt"
 ]
}
```

`chars` is 1,121, and so is `len(text)` — it counts the characters you were handed, not the
file's size. `manifest.json` calls the same file 1,136 `bytes`, and the 15-byte gap is
arithmetic, not drift: the section lines contain three `—` (3 bytes each), three `–` (3) and
three `·` (2), so `3×2 + 3×2 + 3×1 = 15` bytes that are not characters. Budget against
`tokens` in `manifest.json`; read `chars` only as "how much of the file did this reply
contain", which is why it is paired with `truncated`.

`sections` has six entries against three lines in the index: `overview` is 137 pages, so the
exporter split it further into `part-1`, `part-61` and `part-121`, and `overview/llms.txt` is
itself an index over those three. That is the hop the `## Sections` list does not show, and the
reason to read `sections` rather than parse the links.

```
hub_docset_index(docset="codeclaudecom__codeclaudecom", file="agent-sdk/llms.txt")
```

Same envelope, same `sections` list, a different file — real fields from that call, with
`text` cut after its first link:

```json
{
 "docset": "codeclaudecom__codeclaudecom",
 "file": "agent-sdk/llms.txt",
 "served_at": "http://127.0.0.1:8788/d/code.claude.com/agent-sdk/llms.txt",
 "llms_full_url": "http://127.0.0.1:8788/d/code.claude.com/llms-full.txt",
 "chars": 6461,
 "truncated": false,
 "text": "# code.claude.com documentation — Agent Sdk\n\n> 31 page(s) of code.claude.com documentation under Agent Sdk. Part of the index one level up (../llms.txt).\n\n## Agent Sdk\n\n- [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop.md): Understand the message lifecycle, tool execution, context window, and architecture that power your SDK agents.\n … 30 more link lines truncated for this page …"
}
```

`sections` comes back unchanged on every call — it describes the family, not the file you
asked for — so an agent can hop without re-reading the root.

Other values `file` accepts: `llms-small.txt`, `llms-facts.txt`, `manifest.json` (byte and
token counts per file — the cheapest way to plan a budget), and any `<section>/llms.txt` the
reply listed. `llms-full.txt` is never returned inline; it can be millions of tokens, and the
reply gives its served URL instead.

## Expected output

Three replies: the root (280 tokens), the section index (1,615 tokens, 31 page links with
extractive descriptions), and the page. The agent has read about 2k tokens of navigation to
land on a 3k-token page, which is the whole point of the ladder — and the `manifest.json`
read, if you make it, tells you in advance that the alternative (`llms-full.txt`) would have
been 2,097,403 tokens. Picking `overview` instead costs one extra hop: its index is 167 tokens
and points at the three `part-N` files.

## Cost

Measured from `manifest.json`: root 280 tokens, `agent-sdk/llms.txt` 1,615 tokens,
`overview/llms.txt` 167 tokens (it is itself split into `part-N` files of 3,311 / 2,950 /
1,032 tokens). Three tool calls, zero embeddings, zero model tokens spent on retrieval; the
model spends only what it reads.

> Runnable in step 4 (playground).
