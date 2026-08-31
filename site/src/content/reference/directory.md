---
title: 'The directory and its grades'
description: 'What the directory measures, how the A–F grade is derived, and why the mirrored text is never republished.'
section: reference
order: 33
sources:
  - site/tools/gen_directory.py
  - hub/scripts/llms_lint.py
---

<!-- provenance: generated-directory companion; generator: site/tools/gen_directory.py; scorer: hub/scripts/llms_lint.py -->
verified-as-of: 2026-08-31

The [directory](/directory/) lists every site we know of that publishes an
`llms-full.txt`, with a conformance grade beside each one. This page says exactly what
that grade is, what it is not, and what the directory does with the text it fetched.

**Contents**
1. What the directory measures
2. How a grade is derived
3. The rubric groups on a score card
4. What the directory does not do
5. How a site is added

## What the directory measures

One thing only: the output of `llms_lint` run over a copy of that site's
`llms-full.txt`, with `kind="full"`. The linter is the same one that gates this site's
own family — the [attribute rubric](/reference/attributes/) is the whole of its
judgement, and every finding on a score card names the attribute it came from.

The file is linted through a link named `llms-full.txt` in a directory of its own, so
the linter sees the filename and the neighbourhood a real published file has, rather
than our flat mirror where hundreds of unrelated sites share one parent.

Two attributes are skipped, because a single mirrored file cannot answer them and
charging a site for that would measure our storage layout instead of its file: `S2`
wants an `llms-small.txt` sibling and `H8` a `manifest.json`. A site may well publish
both; we simply never fetched them.

## How a grade is derived

The grade is arithmetic over the High and Medium counts, and nothing else. No
weighting, no opinion, no manual override:

| Grade | Condition |
|---|---|
| `A` | 0 High, 0 Medium |
| `B` | 0 High, 1–2 Medium |
| `C` | 0 High, 3 or more Medium |
| `D` | exactly 1 High |
| `F` | 2 or more High |

Low and hygiene findings are listed on the score card but never move the grade: they
are the linter's smallest observations — a missing grammar comment, trailing
whitespace — and a file can be entirely fit for use while carrying a dozen of them.

A grade is therefore a statement about *conformance to the rubric on the day the file
was fetched*, not about whether the documentation behind it is any good. A superb docs
site with no provenance banner grades `B`; an empty file with perfect furniture could
grade `A`.

## The rubric groups on a score card

Each site page splits its High and Medium findings across the nine rubric groups, keyed
by the first letter of the attribute id:

| Key | Group |
|---|---|
| `I` | Identity and shape |
| `N` | Navigation |
| `D` | Descriptions |
| `C` | Content fidelity |
| `P` | Provenance and trust |
| `S` | Size and budget |
| `R` | Retrieval readiness |
| `F` | Family / nesting |
| `H` | Hygiene and serving |

A card with everything in `P` is a file that is fine but anonymous. A card with weight
in `C` is a file whose pages do not carry what they claim to.

## What the directory does not do

It does not republish anybody's text. The hub mirrors each file so it can be scored,
and that copy stays in the hub: every directory page links the source's own file at the
source's own URL. Only the score travels onto this site.

It does not rank sites against each other, score documentation quality, or record
anything a site did not publish at a public URL. And it is a snapshot: each page prints
the date its copy was fetched, and a site that has since fixed its file will carry a
stale grade until the next run.

## How a site is added

The directory is generated, never hand-edited. `site/tools/gen_directory.py` reads the
hub's catalog of known files and writes `src/data/directory.json`; the pages render that
file. A site enters the catalog when the hub's crawler finds it publishing an
`llms-full.txt` — so the way onto the directory is to publish one and let it be found.
