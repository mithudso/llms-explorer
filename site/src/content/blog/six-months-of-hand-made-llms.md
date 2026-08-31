---
title: "Six months of hand-made llms files"
description: "What the ecosystem's llms files actually look like when you download 608 of them, what our own V1 pipeline was producing, and why the answer to both was a facts layer instead of a better site dump."
date: "2026-09-04"
tags: [ecosystem, v1-v2, facts-layer]
sources:
  - hub/docs/specs/2026-08-30-docset-reference-extraction-design.md
  - hub/docs/specs/2026-08-30-docset-golden-baseline.md
  - research/dr-llms/00-my-fetches.md
  - docs/site/components/11-v2-vs-v1.md
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 -->

## Problem

The spec that started this ("llmstxt.org", published 2024-09-03, revised to v2 on 2026-08-10)
asks for something small: an H1, a summary, a few sections of links with a sentence each. Six
months of watching sites adopt it says most of them wrote something else. A site dump: the
entire documentation concatenated into one file, "hundreds of pages of repeating internal
links", no index worth the name, no way to open a claim at its source.

We were doing the same thing ourselves. The hub's V1 pipeline — `mirror → distill → index` —
crawled a site with trafilatura into a banner-delimited text file, ran a zero-LLM "distiller"
over it, and embedded the raw mirror. Each stage reported `done`. None produced the thing the
pipeline existed for: a referenceable list of facts, commands, parameters and snippets.

## Inputs

**The ecosystem, measured.** The hub's catalogue of sites known to publish `llms-full.txt`
(compiled from llms-txt-hub, llmstxt.site, directory.llmstxt.cloud and our own probe of the
docs list) holds 766 entries; 608 downloaded (756 MB, 47,733 pages). Of those, roughly 60 % are
zero-page blobs — a single markdown lump with no page delimiters — and the open-submission
directories put the share of SEO, agency and hotel sites with a 3 KB marketing "llms-full.txt"
at 35–40 %. Only 145 downloads are real docsets with at least one delimited page. The 120
failures that a retry pass could not recover were 404s and dead DNS, not flakes.

**The research.** Ahrefs' crawl data has 97 % of published `llms.txt` files receiving zero AI
requests; ~5–6 % of the top million sites publish one (June 2026); Google calls the format
"meta keywords". The counter-evidence is narrower and more useful: on sites that do publish,
Claude Code out-fetched every retrieval bot bar two. The files work for agents that are pointed
at them, which is the hub's use, not for search-engine visibility.

**Our own V1, measured on the pilot** (`code.claude.com`, trafilatura mirror of 228 pages,
4.74 MB):

| Symptom | Evidence |
|---|---|
| code blocks and tab panels dropped | `**macOS, Linux, WSL:**` followed by nothing; 122 fences in 37k lines; `curl -fsSL` twice on a site whose install page is built on it |
| site chrome kept | 22 % of non-blank lines are duplicates (28,740 unique of 37,033); one FAQ paragraph appears 53 times |
| link-only lines | 3,144 bare `[text](url)` lines, 8.5 % of the file |
| one page is 11 % of the mirror | `/docs/en/changelog`, 535 KB, no date structure left |
| the "distilled" output | 4.65 MB against a 4.74 MB mirror: 17,816 bullets, punctuation scrubbed, regex-bucketed, consumed by nothing |

The same site serves `hooks.md` as 316 KB of clean markdown with every code block intact (the
mirror's copy: 124 KB of prose fragments), an `llms.txt` of 45 KB, and an `llms-full.txt` of
8.5 MB. The crawl was reconstructing, badly, a file the site hands out for free.

## Commands

```bash
# cwd: ~/.global-ai-hub
# V1 (to 2026-08-29): what ran, for the record
.venv/bin/python scripts/pipeline_manager.py run          # mirror (trafilatura) → distill → index

# V2 (from 2026-08-30): the ladder, then the reference layer, then the export
.venv/bin/python scripts/llms_acquire.py probe https://code.claude.com   # llms-full → llms + .md twins → Accept: text/markdown → crawl
PYTHONPATH=scripts .venv/bin/python -m docset_refine clean   text-mirror/code.claude.com.md
PYTHONPATH=scripts .venv/bin/python -m docset_refine extract text-mirror/code.claude.com.md
PYTHONPATH=scripts .venv/bin/python -m docset_refine render  text-mirror/code.claude.com.md
PYTHONPATH=scripts .venv/bin/python -m docset_refine export  text-mirror/code.claude.com.md
.venv/bin/python scripts/docset_indexer.py index text-mirror/code.claude.com.reference/all_units.jsonl --units --name code.claude.com
```

## Outputs

The golden baseline is ten questions a Claude Code user actually asks (install on Windows with
PowerShell, `PreToolUse` exit codes, what `CLAUDE_CODE_SYNC_SKILLS` controls, which hook events
fire once per turn, headless JSON output in CI, `--append-system-prompt`, adding a non-official
plugin marketplace, …), each scored 0/1/2 against the top-5 retrieval hits.

| Layer | Mirror | Pages | Code fences | `curl -fsSL` lines | Score |
|---|---|---|---|---|---|
| V1 raw trafilatura | 4,744,720 B | 228 | 122 | 2 | **11 / 20** |
| V2 after `llms-full.txt` acquisition | 8,547,884 B | 191 | 5,250 | 36 | — |
| V2 facts layer (11,965 units: 5,034 parameters, 3,573 definitions, 2,624 snippets, 380 changes, 354 LLM) | — | 191 | — | — | **14 / 20** (partial LLM pass) |

The wins were specific: env-var rows, flag tables and `claude plugin marketplace add` land as
single hits with the value in them. The remaining misses were also specific — the "once per
turn" cadence is a bullet list under a heading and no deterministic pass carries lists; the
Windows install query is dominated by troubleshooting rows even though the `irm … | iex`
snippet now exists in the mirror (a keyword rerank fixes that class; see the keyword post).

The final export for the pilot: <!-- fig:code.claude.com.pages --> 191 pages,
<!-- fig:code.claude.com.units --> 14,031 units, a <!-- fig:code.claude.com.index_bytes --> 1,136-byte root index over
<!-- fig:code.claude.com.sections --> 6 spokes, <!-- fig:code.claude.com.full_tokens --> 2,097,403 tokens of full text and
<!-- fig:code.claude.com.facts_tokens --> 844,553 tokens of facts.

## What the lint found

There was no lint in V1; that is the finding. The V2 gate (`llms_lint.py`, next posts) exists
because the V1 pipeline could report three green stages and ship nothing usable. When it first
ran on the pilot export it found 2 unsourced units, 1,124 anchors that matched no heading in
the mirror, 1,593 units over 400 characters (table rows rendered as one unit) and a small file
13 characters over budget — four generator defects, each fixed in the generator rather than in
the file.

## Lessons

- A site dump is not an index: if the file is larger than the pages it describes, an agent
  gains nothing by fetching it first.
- The cheapest acquisition rung is usually the best: for the pilot, `llms-full.txt` carried
  43× the code fences the crawl had recovered.
- Zero-LLM "distillation" that only re-orders sentences produces a file the size of its input;
  the deterministic passes that do work are the ones with structure to grab (fences, tables,
  definition lists, dated changelog entries).
- Measure retrieval with questions, not with byte counts: the golden baseline moved 11 → 14 of
  20 while the mirror nearly doubled in size.
- Directory listings overstate adoption: `pages` (count of delimited page blocks) is the honest
  signal, and by that signal a quarter of the downloaded files are docsets.
- What agents fetch and what search engines index are different questions; the evidence
  supports the first use and not the second.

## Reproduce

The diagnosis and plan are `hub/docs/specs/2026-08-30-docset-reference-extraction-design.md`;
the ten questions, the before/after hits and the scoring are
`hub/docs/specs/2026-08-30-docset-golden-baseline.md` and `research/dr-llms/golden*.txt`. The
catalogue of `llms-full.txt` publishers is `outputs/llms-full-catalog/`. The V1 → V2 tables,
the migration guide and the compatibility matrix are the essay "V2 vs V1".
