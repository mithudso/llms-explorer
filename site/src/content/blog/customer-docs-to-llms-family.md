---
title: "Turning a customer's docs into an llms family"
description: "A product docset becomes index / full / small / facts, split hub-and-spoke at 10 KB — Cloudflare, PayPal, Claude and LangChain, with the real byte and token counts."
date: "2026-09-01"
tags: [export, split, customer]
sources:
  - outputs/exports/developers.cloudflare.com.llms/manifest.json
  - outputs/exports/developer.paypal.com.llms/manifest.json
  - outputs/exports/docs.claude.com.llms/manifest.json
  - outputs/exports/docs.langchain.com.llms/manifest.json
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 · figures from site/src/data/figures.json (gen_figures.py) -->

## Problem

A documentation site is the wrong shape for an agent. It is hundreds or thousands of HTML
pages, each wrapped in navigation, each linking to the others, none of them saying which page
answers a given question. An agent pointed at it either crawls everything (expensive and slow)
or guesses a page from the URL (usually wrong). What it needs is a family of files: a small
index that says where things are, a full file it can grep, a budgeted file it can load whole,
and a facts file it can retrieve from — every line pointing back at a page and a heading.

Four public docsets were run through the hub's export in the last two days of August 2026.
They were chosen because they are large, they publish their own `llms.txt` or `llms-full.txt`
(so the acquisition ladder's cheapest rung applies), and they differ in shape: Cloudflare is a
product tree, PayPal is an API reference, Claude's platform docs are a mix, LangChain is small.
This post is the numbers, the commands, and what the lint said.

## Inputs

| Docset | Pages | Acquired via | Deterministic units |
|---|---|---|---|
| developers.cloudflare.com | <!-- fig:developers.cloudflare.com.pages --> 1,943 | `llms-full.txt` (57 MB upstream, 2,000-page cap) | <!-- fig:developers.cloudflare.com.units --> 25,142 |
| developer.paypal.com | <!-- fig:developer.paypal.com.pages --> 1,507 | structured crawl (its `llms-full.txt` redirects to a 1.5 KB `llms.txt`) | <!-- fig:developer.paypal.com.units --> 38,710 |
| docs.claude.com (served from platform.claude.com) | <!-- fig:docs.claude.com.pages --> 666 | `llms.txt` + page `.md` twins | <!-- fig:docs.claude.com.units --> 13,432 |
| docs.langchain.com | <!-- fig:docs.langchain.com.pages --> 529 | `llms-full.txt` | <!-- fig:docs.langchain.com.units --> 12,933 |

"Deterministic units" are the snippets, table rows (parameters), definitions and changelog
entries that `docset_refine extract` pulls out without a model. No LLM pass ran on these four;
this is the zero-token layer only.

Two of the four needed a detour. PayPal's `llms-full.txt` is a redirect to its short index, so
the probe (which now requires real `Source:`-delimited pages) fell through to a crawl, and its
pages have no `.md` twins. Claude's `llms.txt` at `docs.claude.com` lists pages hosted on
`platform.claude.com`, so the docset key changed mid-run and the stale four-page docset had to
be deleted afterwards.

## Commands

```bash
# cwd: ~/.global-ai-hub
# 1. Which rung of the acquisition ladder does each host support?
.venv/bin/python scripts/docset_rollout.py probe

# 2. Queue the four hosts and run mirror → refine → index on this box only
.venv/bin/python scripts/pipeline_manager.py add \
  https://developers.cloudflare.com https://developer.paypal.com \
  https://docs.claude.com https://docs.langchain.com
.venv/bin/python scripts/pipeline_manager.py run --local-only --crawlers 2 --max-pages 2000

# 3. (What the refine stage runs per docset, if you want it by hand — no model tokens)
PYTHONPATH=scripts .venv/bin/python -m docset_refine all --no-units \
  ~/.claude/skills/web-text-mirror/text-mirror/developers.cloudflare.com.md

# 4. Lint the export directory against its mirror
.venv/bin/python scripts/llms_lint.py check \
  ~/.claude/skills/web-text-mirror/text-mirror/developers.cloudflare.com.llms/ \
  --mirror ~/.claude/skills/web-text-mirror/text-mirror/developers.cloudflare.com.md
```

`--local-only` matters: the remote boxes in the pool do not have `llms_acquire.py`, so a
placement there would fall back to a trafilatura crawl and reconstruct, badly, a file the site
hands out for free.

## Outputs

Every docset produced `<stem>.llms/{llms.txt, llms-full.txt, llms-small.txt, llms-facts.txt,
manifest.json}` plus one `<section>/llms.txt` per section once the root index crossed the
10 KB split threshold.

| Docset | Root index (bytes) | Spoke indexes | Full (tokens) | Facts (tokens) |
|---|---|---|---|---|
| developers.cloudflare.com | <!-- fig:developers.cloudflare.com.index_bytes --> 9,241 | <!-- fig:developers.cloudflare.com.sections --> 243 | <!-- fig:developers.cloudflare.com.full_tokens --> 4,162,267 | <!-- fig:developers.cloudflare.com.facts_tokens --> 1,889,300 |
| developer.paypal.com | <!-- fig:developer.paypal.com.index_bytes --> 4,104 | <!-- fig:developer.paypal.com.sections --> 193 | <!-- fig:developer.paypal.com.full_tokens --> 2,921,259 | <!-- fig:developer.paypal.com.facts_tokens --> 1,680,485 |
| docs.claude.com | <!-- fig:docs.claude.com.index_bytes --> 1,977 | <!-- fig:docs.claude.com.sections --> 73 | <!-- fig:docs.claude.com.full_tokens --> 7,493,540 | <!-- fig:docs.claude.com.facts_tokens --> 768,209 |
| docs.langchain.com | <!-- fig:docs.langchain.com.index_bytes --> 1,508 | <!-- fig:docs.langchain.com.sections --> 15 | <!-- fig:docs.langchain.com.full_tokens --> 1,552,458 | <!-- fig:docs.langchain.com.facts_tokens --> 738,488 |

The small file is the same size everywhere by construction: `build_small` fills an exact
200,000-character budget (about 50k tokens, the ceiling at which editor agents stay stable) and
asserts on it. The root index is under 10 KB on all four because the sections were pushed out
into spokes; the spokes together are the real index — for Cloudflare, 243 files totalling about
587 KB, which is the honest size of a 1,943-page table of contents with a description per page.

Every unit in the facts file is one line, `- [type] text — url#anchor`, and every anchor
resolves to a heading in the mirror (see the anchors post for why that was not true a day
earlier).

## What the lint found

Before the split landed, all four docsets carried a High: `S1` (index over 100 KB — an index
that is itself a site dump). After `build_split_index`, the estate gate reported:

- Cloudflare, Claude, LangChain: 0 High. Spoke indexes between 10 and 17 KB (about sixty pages
  with long descriptions each) remain `S1` Medium and are accepted; splitting further would
  produce single-page indexes.
- PayPal: one High left, on `validation-errors/llms.txt` — 3 of 5 links have no description,
  because those pages carry no definition unit the extractor can turn into one. This is a
  generator gap (a description fallback from the page's H1 and first sentence is the fix), not
  a lint false positive.
- PayPal also trips `P5` (secrets) on a real-looking RSA private key printed in its own docs.
  The lint keeps that High on purpose: whether to publish a third party's key material in a
  facts file is a human decision, not a regex's.

Facts files pass `P7` (every line typed from the twelve allowed types, every line sourced) and
`R3` (anchors resolve against the mirror) on all four.

## Lessons

- A site that publishes `llms-full.txt` can be refined in one pass with zero model tokens; the
  deterministic extractors alone yield 6–25 units per page on these four sites.
- The 10 KB index rule is a split rule, not a truncation rule: no page is dropped, the root
  gets one line per section with page and token counts, and the spokes are spec-v2 indexes in
  their own right (most-specific-wins nesting).
- "No description" Highs point at pages with no definition unit; fixing them is generator work
  (fallback text), and hand-editing the index would be erased on the next export.
- A probe must require real page blocks, not a 200 status: PayPal's redirect-to-index would
  otherwise have been recorded as an `llms-full` host and produced a four-page docset.
- Pool placement rules are part of correctness: a box without the acquisition ladder produces
  a different (worse) mirror for the same URL.
- The small file's size is a budget, not a measurement; its token count is the same on every
  docset and tells you nothing about the docset.

## Reproduce

The exports live in this repository under `outputs/exports/<stem>.llms/`; each `manifest.json`
carries the byte and token counts quoted above (the blog's figures are regenerated from them at
build time by `site/tools/gen_figures.py`). To rebuild from scratch, run the commands block on a
hub checkout, then `llms_lint.py check <stem>.llms/ --mirror <stem>.md` — it exits 1 while a High
remains. Recipe 02 in the examples cookbook walks a split root by hand.
