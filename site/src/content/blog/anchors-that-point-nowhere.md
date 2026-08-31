---
title: "Anchors that point nowhere"
description: "1,124 of 11,965 units on the pilot were anchored to headings the site never renders — MDX <Step> and <Tab> titles that cleaning had turned into headings. The fix anchors every unit to the nearest real source heading."
date: "2026-09-05"
tags: [extract, anchors, lint]
sources:
  - hub/scripts/docset_refine/extract.py
  - hub/scripts/llms_lint.py
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 -->

## Problem

A facts line is a promise: `- [type] text — url#anchor` says that if you open the URL at that
anchor you will find the text. The first end-to-end lint of the code.claude.com export broke
that promise 1,124 times out of 11,965. The units were real, the pages were real, the text was
on the page — and the `#anchor` did not exist, because the heading it slugified was not a
heading on the site.

The cause was upstream of extraction. Mintlify-style docs are written in MDX with `<Step
title="…">`, `<Tab title="…">` and `<Accordion title="…">` components. `docset_refine clean`
converts those to markdown and, reasonably, turns each `title` into a heading so the structure
survives. The site itself renders them as component chrome without an `id`, so a link to
`#install-git-for-windows-optional` opens the page at the top. The extractors then anchored to
the nearest heading above each unit — which was very often one of those.

A second, smaller finding rode along: 2 units carried no source at all, and 1,593 units were
longer than 400 characters because a wide table row had been rendered as a single unit.

## Inputs

- The pilot mirror `code.claude.com.md` (191 pages, acquired from `llms-full.txt`) and its
  export `code.claude.com.llms/`.
- `llms_lint.py check code.claude.com.llms/ --mirror code.claude.com.md`, whose `P7` pass
  resolves every anchor against the headings in the raw mirror (`R3`).
- After the fix, the whole refined estate: 15 docsets re-extracted, 13 facts layers
  re-embedded (56,489 units, about 25 minutes on the embedding pool) plus an FTS5 keyword row
  for each.

## Commands

```bash
# cwd: ~/.global-ai-hub
# before: measure
.venv/bin/python scripts/llms_lint.py check text-mirror/code.claude.com.llms/ \
  --mirror text-mirror/code.claude.com.md --json | jq '.findings[] | select(.attr=="R3")'

# after the extractor change: regenerate (render merges units.jsonl; export rebuilds the family)
PYTHONPATH=scripts .venv/bin/python -m docset_refine extract text-mirror/code.claude.com.md
PYTHONPATH=scripts .venv/bin/python -m docset_refine render  text-mirror/code.claude.com.md
PYTHONPATH=scripts .venv/bin/python -m docset_refine export  text-mirror/code.claude.com.md
.venv/bin/python scripts/llms_lint.py check text-mirror/code.claude.com.llms/ --mirror text-mirror/code.claude.com.md

# estate-wide: re-extract every refined docset, re-embed the facts layers, add the keyword rows
for m in text-mirror/*.clean.md; do s=${m%.clean.md}.md; PYTHONPATH=scripts .venv/bin/python -m docset_refine extract "$s" && PYTHONPATH=scripts .venv/bin/python -m docset_refine render "$s" && PYTHONPATH=scripts .venv/bin/python -m docset_refine export "$s"; done
.venv/bin/python scripts/docset_indexer.py index text-mirror/code.claude.com.reference/all_units.jsonl --units --name code.claude.com
.venv/bin/python scripts/docset_indexer.py keyword-index codeclaudecom__codeclaudecom --layer facts
```

## Outputs

The change is one function and one rule. `extract.real_headings(pages)` reads the *raw* mirror
once and returns, per URL, the set of heading slugs that exist on the source page (skipping
fenced code, where a `#` is a comment). Every extractor — snippets, table rows, definitions,
changelog entries — then anchors to the nearest heading above the unit *that is in that set*.
A `<Step>` title still becomes a heading in the cleaned text (the structure is useful for
reading), but it is never an anchor.

Alongside it:

- `_clip(text, 400)` on snippet, parameter and change units; definitions capped at two
  sentences and 300 characters. The full row text stays in `units.jsonl`; the facts line shows
  the clipped form.
- `build_small` now fills its 200,000-character budget exactly and asserts on it (the banner
  had not been counted, hence the 13-character overshoot).
- The lint's unit regex no longer mis-parses a ` · ` inside the unit text as the start of a
  tail field.

After regeneration the pilot's facts file has 0 unsourced units and 100 % of anchors resolving;
the same is true for the fifteen re-extracted docsets. The cost was one estate-wide re-extract
and re-embed, because anchors are part of the stored unit, not a rendering detail.

## What the lint found

Before: `P7 C6` High (2 unsourced lines), `R3` Medium (1,124 unresolved anchors), `C6` Medium
(1,593 non-atomic units), `S3` Low (small file over budget by 13 characters).

After: `R3` clean on every docset that has a mirror beside it. One operational finding came
out of running the gate estate-wide: `R3` re-parses the mirror to collect headings, and a
20 MB mirror was being re-parsed once per spoke index (243 times for Cloudflare). The heading
map is now `lru_cache`d per mirror path; the gate runs in seconds instead of minutes.

## Lessons

- An anchor is a claim about the *rendered* page, so it must be derived from the source page,
  not from the cleaned text; any transformation that adds headings must be excluded from anchor
  derivation.
- Fix generator defects in the generator: hand-editing 1,124 lines would have lasted until the
  next export.
- A unit's anchor is stored, not computed at render time, so an anchoring bug costs a full
  re-extract and re-embed of the estate — budget for it.
- Clip at extraction, keep the full text in the record: a 1,200-character table row is a bad
  facts line and a good `units.jsonl` entry.
- Lint passes that touch the mirror need caching once the export is a family of hundreds of
  files.
- Exact budgets deserve an assert; "about 200,000 characters" hid a 13-character overshoot for
  a day.

## Reproduce

`hub/scripts/docset_refine/extract.py` (`real_headings`, `_anchor`, `_real_for`) and
`hub/scripts/llms_lint.py` (`pass_facts`, `_mirror_headings`) are vendored in this repository;
`hub/tests/test_docset_refine.py` and `hub/tests/test_llms_lint.py` carry the cases. Any export
under `outputs/exports/` can be checked with `llms_lint.py check <stem>.llms/ --mirror
<stem>.md` once you have the mirror; without `--mirror`, `R3` reports `na` rather than passing.
