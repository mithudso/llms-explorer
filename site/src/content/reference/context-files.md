---
title: 'Context files and concept facts files: what an agent loads'
description: 'The two file shapes the hub publishes for agents to load whole, how each is filed under the concept tree, what the facts-file grammar is, and the rights position behind both.'
section: reference
order: 9
sources:
  - site/tools/gen_context.py
  - site/tools/gen_concept_facts.py
  - site/tools/twins.py
---

<!-- hand page · reference/context-files · 2026-09-25 · matches site/tools/gen_context.py and gen_concept_facts.py -->

Two things on this site are meant to be loaded whole into a context window rather than
browsed. Both are listed on [/context/](/context/) for a person and in `/context.md` for an
agent, and both are served as `text/markdown` with the `describedby` link back to `/llms.txt`.

## 1. Context files

A **context file** is one of the hub's own research reports: a dated, sourced write-up of one
subject, produced by the research skills this site publishes (`/dr`, `rabbithole`,
`concept-family-explorer`). Each is mirrored twice:

| Surface | Route | For |
|---|---|---|
| rendered page | `/sources/<hub>/<name>/` | a person; the URL a concept pack's fact cites |
| raw markdown | `/downloads/sources/<hub>/<name>.md` | an agent; the same bytes, unrendered |

They exist on this site so that a fact in a [concept pack](/reference/concept-tree/) can
name a source that resolves publicly instead of a path inside a private repository. They are
not twinned into the site's own `llms-full.txt`: three hundred reports would drown the family
this build curates, so the index lists them under `/context.md` and leaves each one a single
fetch away.

## 2. Concept facts files

A **concept facts file** is one concept's pack as a markdown list — the same facets and facts
the node page under `/tree/` renders, written to `/downloads/concepts/<slug>.md` by
`gen_concept_facts.py` on every build. The grammar:

```markdown
<!-- llms-explorer concept facts · <page URL> · pack <date> · ~<N> tokens -->
# <Concept>

> <summary>

Parent: [<parent>](<parent page>) · <facets> facets · <facts> facts · page: <page URL>

## <Facet title>
- <fact> — [source](<URL>)
  - <sub-point> — [source](<URL>) *(<note>)*

## Related concepts
- [<concept>](<page>) — <relation>

## Context files
- [<title>](/downloads/sources/<hub>/<name>.md)
```

Every fact keeps the source it was extracted with. A source that is a URL is a link; a source
that is a local path (the earliest packs cite files under a skills directory) is shown in code
and never linked, because a link to it resolves nowhere. Sub-points nest under the point that
introduces them, from the `level` the pack builder derived from the source's own list
indentation. The token estimate in the banner is the family's declared estimator (bytes ÷ 4),
placed in the file because downloads carry no per-file `X-Markdown-Tokens` header — see
[usage §2](/reference/usage/) for what a twin and a download each promise.

## 3. How a row is filed

`/context/` groups both shapes under the **roots of the concept tree**:

- a concept facts file goes under its own root, walked up `parent_slug` in `tree.json`;
- a context file goes under the root of the concept that cites it most; a file cited from two
  subtrees is listed under the heavier one and links every concept that cites it;
- anything the tree cannot place — a pack whose node is not in this snapshot, a report nothing
  cites yet — lands under a synthetic last root, *Not yet filed*, so it is visible rather than
  absent.

`context.json` is generated from the committed sources, packs and tree, never from the clock:
its `generated` stamp is the tree's, and CI diffs the committed file against a fresh run.

## 4. Reading it the one-hop way

1. Fetch `/context.md`. It lists every context file and every concept facts file with its
   absolute URL, grouped by root, in one file.
2. Search it for your term. A hit names the file.
3. Fetch that file. Stop.

When the term is a concept rather than a subject, the root `/llms.txt` already lists every
`/tree/<slug>/` page; the facts file is at `/downloads/concepts/<slug>.md` with the same slug.

## 5. Rights

Context files are the hub's own words about sources it read, with those sources cited. No
third-party full text is republished on either surface; the mirrored `llms-full.txt` files the
[directory](/directory/) grades are scored, not served. The [ethos](/reference/ethos/) page
carries the whole position.
