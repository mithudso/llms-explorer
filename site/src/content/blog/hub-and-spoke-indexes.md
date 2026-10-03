---
title: "Hub-and-spoke indexes"
description: "How saved llms.txt exports split into nested indexes, what the generator preserves, and which historical lint results remain unverified."
date: "2026-09-08"
tags: [export, split, index]
sources:
  - hub/scripts/docset_refine/export_llms.py
  - .claude/skills/llms-deep-optimizer/references/llms-vs-skill-files.md
  - outputs/exports/developers.cloudflare.com.llms/manifest.json
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 · figures from site/src/data/figures.json -->

## Problem

The spec wants an index small enough that an agent reads it before deciding where to go. The
rubric's bar is about 10 KB (`S1`; High above 100 KB). A
<!-- fig:developers.cloudflare.com.pages --> 1,943-page product tree with a
one-line description per page is, unavoidably, half a megabyte of index. Both facts are true
at once. Truncating it, dropping descriptions, or listing only the "main" pages breaks
the index's promise that every page is reachable from it.

The [v2 proposal](https://llmstxt.org/) allows `llms.txt` at a published site's subpath. It covers
the URLs under that path; where several indexes apply, the most specific wins. The hub uses
a similar hierarchy for navigation: a root points at section indexes, each with the v2 file
structure. These exports retain upstream vendor URLs, so their local folders do not establish
coverage over those vendor paths. Synthetic `part-N` directories are navigation buckets.
The hub calls the result hub-and-spoke, and after 2026-08-30 the exporter produces it automatically.

## Inputs

The four docsets whose single-file index exceeded 100 KB on the first export (all four `S1`
High), plus the smaller ones whose root was between 10 and 100 KB. The manifest of each records
the split:

| Docset | Pages | Root index (bytes) | Spokes |
|---|---|---|---|
| developers.cloudflare.com | <!-- fig:developers.cloudflare.com.pages --> 1,943 | <!-- fig:developers.cloudflare.com.index_bytes --> 9,241 | <!-- fig:developers.cloudflare.com.sections --> 243 |
| developer.paypal.com | <!-- fig:developer.paypal.com.pages --> 1,507 | <!-- fig:developer.paypal.com.index_bytes --> 4,104 | <!-- fig:developer.paypal.com.sections --> 193 |
| docs.claude.com | <!-- fig:docs.claude.com.pages --> 666 | <!-- fig:docs.claude.com.index_bytes --> 1,977 | <!-- fig:docs.claude.com.sections --> 73 |
| docs.langchain.com | <!-- fig:docs.langchain.com.pages --> 529 | <!-- fig:docs.langchain.com.index_bytes --> 1,508 | <!-- fig:docs.langchain.com.sections --> 15 |
| code.claude.com | <!-- fig:code.claude.com.pages --> 191 | <!-- fig:code.claude.com.index_bytes --> 1,136 | <!-- fig:code.claude.com.sections --> 6 |
| mongodb.com | <!-- fig:mongodb.com.pages --> 82 | <!-- fig:mongodb.com.index_bytes --> 3,624 | <!-- fig:mongodb.com.sections --> 30 |

## Commands

```bash
# cwd: ~/.global-ai-hub
# export decides: single index if the rendered size is ≤ INDEX_SPLIT_BYTES (10,000), else split
PYTHONPATH=scripts .venv/bin/python -m docset_refine export text-mirror/developers.cloudflare.com.md

# walk a split root: the root lists sections, each section is its own spec-v2 index
head -40 text-mirror/developers.cloudflare.com.llms/llms.txt
cat text-mirror/developers.cloudflare.com.llms/cache/llms.txt
cat text-mirror/developers.cloudflare.com.llms/cache/how-to/llms.txt

# the served form, with headers: any depth resolves
curl -sI http://127.0.0.1:8788/d/developers.cloudflare.com/cache/how-to/llms.txt | grep -i 'content-type\|x-markdown-tokens\|^link'

# lint: P2 verifies every relative spoke target exists (P10's family checks run under /ldo)
.venv/bin/python scripts/llms_lint.py check text-mirror/developers.cloudflare.com.llms/ --mirror text-mirror/developers.cloudflare.com.md
```

## Outputs

`build_split_index(pages, title, summary, defs, …)` groups pages by their first URL path
segment. The root keeps the H1 and blockquote and writes one line per section:
`- [Cache](cache/llms.txt): 47 pages · ≈ 12k tokens · Overview, Concepts, How-to …` — the
counts and three sample titles are what a consumer needs to decide before fetching. `## Optional`
(changelogs) stays on the root, last. Each spoke is `# <title> — <section>` plus a blockquote
plus one H2 of page links with descriptions. This is a navigation hierarchy; the retained
upstream URLs need not fall under the export directory's path. A spoke that is itself over
budget splits again on the next path segment, and a section with no further path structure
splits into `part-N` files of 60 pages (`PART_PAGES`). Nothing is dropped: the root and its
reachable spokes retain the complete page list, including the root's optional links.

For Cloudflare the <!-- fig:developers.cloudflare.com.sections --> 243 spokes total about
587 KB, for PayPal <!-- fig:developer.paypal.com.sections --> 193 spokes about 355 KB, for the
Claude platform docs <!-- fig:docs.claude.com.sections --> 73 spokes about 141 KB, the size of those tables of contents,
now behind a root an agent can read in one call. `code.claude.com` shows the `part-N` case:
its `overview` section has no deeper paths, so the stored export uses `overview/part-1`,
`overview/part-61`, and `overview/part-121`. These suffixes identify starting page positions
in that export; do not infer a consecutive part number from them.

The server resolves a spoke at any depth with the same headers as the root (`text/markdown`,
`X-Markdown-Tokens`, `Link: rel="describedby"` pointing at the covering index), and the lint's
`P2` follows every relative target and fails if one is missing.

## What the lint found

- Before: `S1` High on four docsets (index over 100 KB). After: 0 High from `S1` anywhere.
- Spokes between 10 and 17 KB remain `S1` Medium on sections of about sixty pages with long
  descriptions. Accepted; the alternative is single-page spokes, which cost a hop per page.
- One High left on the estate after the split, on PayPal's `validation-errors/llms.txt`: three
  of five links carry no description because those pages have no definition unit. The fix
  belongs to the generator (H1 + first sentence as fallback), and until it lands the finding
  stays red rather than being edited away.
- `P10` (family and nesting) is a `/ldo` pass outside the CLI gate. Its URL-containment
  check must distinguish published site paths from export navigation folders; synthetic parts
  do not imply that their upstream URLs lie under those folders. The historical `P10` receipt
  is not retained here. In the CLI, `P2` walks relative targets and fails High when one does not
  exist; that verifies reachable files, not authority over the linked vendor URLs.

The last point is the one `/ldo` is strict about. An index is a promise list, not prose. A
description that reads better but drops the flag name got worse; a hand edit the generator
cannot reproduce is a Medium finding (`P15`, regeneration parity) because the next export erases
it. So the optimizer never "improves the writing" of an index; it changes the generator's inputs
— section order, title, summary, the definition extractors, and regenerates.

## Lessons

- Split, never truncate: an index that omits pages fails the first question about an omitted
  page, and nobody will know why.
- The root line needs counts: page and token totals per section let an agent choose a spoke
  without opening it.
- A spoke can be fetched on its own as a curated index. The spec's subpath coverage applies
  when the index is published under the corresponding page origin and path; local export
  nesting alone establishes navigation.
- Recursion handles deep trees and `part-N` handles flat ones; both must be lint-verified by
  following the links, not by counting files.
- Hand edits do not survive regeneration; anything a person wants to say about an index goes
  into the overrides the generator honours (title, summary, section order).
- A remaining High that is a generator gap should stay visible in the gate output until the
  generator changes; hiding it in the file is the failure mode the gate exists to catch.

## Reproduce

`hub/scripts/docset_refine/export_llms.py` (`build_index`, `_split`, `build_split_index`,
`INDEX_SPLIT_BYTES`, `PART_PAGES`) is vendored here with `hub/tests/test_docset_refine.py`. The
split roots and every spoke for the docsets above are under `outputs/exports/<stem>.llms/`; open
`llms.txt` and follow a relative link. These are saved exports. The inspected generator names
parts from their starting page offsets: with `PART_PAGES = 60`, they are Part 1, Part 61,
Part 121, and so on. Their token counts are character-based estimates, not tokenizer measurements. Recipe 02 in the examples cookbook walks a split root by
hand, and the note on why an llms file is not a skill file is
`.claude/skills/llms-deep-optimizer/references/llms-vs-skill-files.md`.
