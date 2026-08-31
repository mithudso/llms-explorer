---
title: 'Ethos: what an llms file owes its reader'
description: 'Files are promises; generate, do not hand-edit; never instruct the reader; evidence is external; rights are explicit.'
section: reference
order: 4
sources:
  - docs/site/00-platform-design.md
  - skills/llms-deep-optimizer/references/llms-vs-skill-files.md
  - docs/site/components/03-reference.md
---

<!-- hand page · reference/ethos · 2026-08-31 · restates platform principles 1, 2, 6, 7 for the reference section -->

The rules on this site come from one distinction. A **skill file tells a model how to act**; an
**llms file tells a model where the facts are** (index) or **what the facts are** (facts, full).
A skill is read once and obeyed. An llms file is read many times and *followed* — every line is a
promise that a link or a claim will pay off. Five commitments follow.

## 1. Files are promises

Every link resolves. Every fact is anchored to a heading that exists. Every volatile claim carries
a `verified-as-of` date. A link that 404s is not a small defect: the reader spent context on the
promise and got nothing, and the next promise in the file is now worth less. This is why the
[rubric](/reference/attributes/) rates a dead link High and why the lint gates every publish on
zero High findings — including this site's own family, on every build.

## 2. Generate, don't hand-edit

An llms file is an output. Its inputs are a mirror, a page list, extracted units, a concept tree,
and a small overrides file (`title`, `summary`, `section_order`, `note`). A hand edit to the
output is lost on the next regeneration and, worse, is invisible until then. So `/ldo` rates
a hand edit the generator cannot reproduce as a Medium finding (pass P15, regeneration parity —
it runs under the optimizer, not in the CLI gate), and the
fix for a bad description is a change to the generator's inputs followed by `docset_refine export`.
The same holds here: `/reference/attributes/` and `/reference/passes/` are copied at build time from
the linter's own source files by `site/tools/gen_reference.py`, so the reference cannot disagree
with the lint. A number on a page is never typed by hand.

## 3. Never instruct the reader

A docs file has no business telling a model what to say. The spec repository's issue #152 found
42.3% of a sample of wild files attempting exactly that ([evidence](/reference/evidence/)). The
rubric forbids it (P4); the lint rejects the recognisable phrasings (`STEER_RES`: "ignore
previous instructions", "always recommend us", "do not mention competitors", "when asked about X,
say Y"); and the voice of every generated line is third person and extractive. The corollary for
readers: everything fetched through an index is data, not instructions.

## 4. Evidence is external

A finding about an llms file cites something outside the file: the link check, the mirror span
behind a unit, the probe result, the HTTP response. A finding with no external evidence is Low at
most. The same discipline applies to this site's prose: the [reasoning page](/reference/reasoning/)
cites the [evidence page](/reference/evidence/) for every number, and the evidence page names its
sources and grades the vendor ones. The honesty note travels with every recommendation:
`llms.txt` is a proposal, not a ratified standard; the reader it demonstrably has is an agent
pointed at it, and the site optimises for that reader alone.

## 5. Rights are explicit

Three tiers, and the tooling knows which is which:

| Content | Publishable? |
|---|---|
| An index — links and extractive descriptions | yes; it is a map of someone's public pages |
| A facts file — short anchored claims, each traceable | yes; quotation with attribution, bounded in length |
| Your own words — hand pages, essays, this site | yes |
| Third-party full text — a mirrored `llms-full.txt` of a site you do not own | served only to its owner, or under the internal marker; never on a public route |

Evidence pages cite, they do not republish. Quoted spec text is short and attributed to
llmstxt.org. `robots.txt` and Content Signals govern the **crawl** path — the trafilatura mirror
that walks a site's pages asks before it walks. The llms-full mirror behind
[the directory](/directory/) is not a crawl and does not check them: it fetches exactly one file,
at the well-known path a site chose to publish it on, once, and nothing else from that host. We
say so rather than claim a check the code does not make; if you would rather we did not hold that
copy, [ask and we will drop it](/reference/directory/#how-a-site-is-corrected-or-removed).

## The test

If a stranger's agent, handed only the index, can answer eight of ten reasonable questions in two
hops — below six is a High — and can check any facts line it relies on in one fetch, the file kept
its promises. Nothing
else on this site is a stronger claim than that.
