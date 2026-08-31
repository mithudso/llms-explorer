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

The [directory](/directory/) lists the mirrored `llms-full.txt` files we can score — 145 of
the 608 we have fetched, from a catalog of 766 known files — with a conformance grade beside
each one. This page says exactly what that grade is, what it is not, which files are left out,
and what the directory does with the text it fetched.

**Contents**
1. What the directory measures
2. How a grade is derived
3. The rubric groups on a score card
4. Which files are left out
5. What the directory does not do
6. How a site is added
7. How a site is corrected or removed

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

## Which files are left out

Three exclusions, in the order they bite.

**Not fetched.** The catalog holds 766 keys; 608 of them have a file on disk. The rest either
failed to download (120) or were rejected as not being an llms file at all (38). Nothing without
a local copy can be scored.

**Fetched but not page-structured.** `gen_directory.py` scores only rows whose mirrored file
splits into at least one page — a `# Title` heading with a `Source:` line under it. 145 of the
608 do. The other 463 are still markdown documentation, and the catalog deliberately keeps them
with `pages: 0` rather than rejecting them, but a linter that walks pages has nothing to walk,
so they are absent from the directory rather than graded badly in it.

That exclusion is not neutral, and the directory page says so: a file with no page grammar would
fail several content-fidelity attributes it is never charged for, so the published grade spread
describes the scorable subset and not the population of files people publish.

**Two attributes, on every card.** `S2` (an `llms-small.txt` sibling) and `H8` (a
`manifest.json`) are dropped from both the counts and the findings list, per the section above.
A card's "0 High · 2 Medium" is therefore the linter's output minus those two, not its whole
output; each site page repeats this beside its counts.

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
stale grade until the next run — see below for how to ask for one.

## How a site is added

The directory is generated, never hand-edited. `site/tools/gen_directory.py` reads the
hub's catalog of known files and writes `src/data/directory.json`; the pages render that
file. A site enters the catalog when the hub's crawler finds it publishing an
`llms-full.txt` — so the way onto the directory is to publish one and let it be found.

## How a site is corrected or removed

Every entry names a real organisation and prints a public letter grade against it, so there is a
way off the list and a way to fix a wrong one.

**Write to us** by opening an issue at
[github.com/mithudso/llms-explorer](https://github.com/mithudso/llms-explorer/issues) — say
which entry, and what is wrong.

- **The grade is stale.** The hub re-fetches its mirror on a weekly refresh and the directory is
  regenerated on the next site build, so a fixed file corrects itself within a week. Ask and we
  will re-fetch and re-score that one file sooner.
- **The grade is wrong** — the linter misread a conforming file. That is a bug in
  `hub/scripts/llms_lint.py`, not a judgement to appeal: send the file's URL and we will fix the
  rule and re-score everything it touched.
- **The entry is wrong** — wrong name, wrong site, wrong URL. Same route; these come from the
  catalog and are cheap to correct.
- **You want the entry gone.** Ask, and it goes: we drop the row and stop fetching that file, no
  reason required. Removal is from this directory, which is the only thing we control — your
  file stays wherever you publish it.

We never republished the text in the first place (see above), so removal is a matter of dropping
one row and the page it generated.
