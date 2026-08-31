---
title: 'Glossary'
description: 'The terms of the field, one line each, in the sense this site uses them — with the contrasts that matter.'
section: reference
order: 5
sources:
  - docs/site/components/12-vocabulary.md
  - docs/site/components/03-reference.md
  - skills/llms-deep-optimizer/references/attributes.md
---

<!-- hand page · reference/glossary · 2026-08-31 · the site's generated llms-vocabulary.txt is the machine form of this page -->

One line per term, in the sense this site means. Where a word has a neighbour it is often
confused with, the contrast follows a dash. The full sense model — homonyms across families,
`aka:` and `not:` relations, the file grammar — is in the [vocabulary essay](/essays/vocabulary/);
the machine-readable form of this page is the site's own `llms-vocabulary.txt`.

## The files

- **index** (`llms.txt`): the spec-defined map — H1, blockquote, H2 link lists — small enough to sit in context; orientation and navigation, never content.
- **full** (`llms-full.txt`): every page of a docset inlined into one markdown file — not in the spec; three grammars exist.
- **small** (`llms-small.txt`): a full file cut to a budget (≤ 200,000 characters, ~50k tokens), reference pages first — pages dropped whole, never truncated.
- **facts** (`llms-facts.txt`): a hub extension — one typed, anchored claim per line, the trusted layer a retriever answers from.
- **vocabulary** (`llms-vocabulary.txt`): the lexical layer — terms, senses, synonyms and contrasts of a family, each definition anchored to a unit.
- **manifest** (`manifest.json`): the counts (bytes, tokens, pages, units, sections) and the overrides, beside the files and never linked from them.
- **twin** (`.md` twin): the clean-markdown version of an HTML page at the same route with `.md` appended — the thing an index link should point at.
- **family** file: an index that links other indexes, never pages, with counts on every line and shared material under `## Shared`.
- **split root**: an index that grew past 10 KB and became a `## Sections` list of subpath indexes — a family of one site's own sections.
- **topical file**: an llms family on the concept axis — built from a fact pool, sectioned by a concept-tree node's children — rather than from one site.
- **concept pack**: everything known about one concept across many docsets, compiled into a small llms family with every line source-anchored.

## The lines

- **link line**: `- [name](url): description` — the unit of an index; judged on whether the description carries the tokens a reader would search for.
- **description**: the text after the colon on a link line — extractive (cut from the page), 10–25 words, never model-written prose.
- **unit**: one line of a facts file — `- [type] text — url#anchor` plus optional `keywords:` and `verified-as-of:` — the unit of convergence for the optimizer.
- **unit type**: one of twelve — concept, fact, actionable, question, problem, statement, quote, idea, snippet, parameter, definition, change.
- **anchor**: the `#fragment` on a unit's URL naming the heading the claim came from — a link names a page, an anchor names a place on it.
- **origin**: how a unit was extracted — code, table, heading, changelog, or llm — carried in the JSON, not the text file.
- **pool**: the set of units (`units.jsonl`, a facts file, spoke pages) a topical or vocabulary file is built from.
- **sense**: a term × family pair (`<family-slug>.<term-slug>`) — "cookie" has one sense in web docs and another in a recipe corpus.
- **homonym**: a term with senses in more than one family; a **contranym** is a homonym whose senses oppose each other.

## The plumbing

- **describedby**: the `Link: <…/llms.txt>; rel="describedby"` header (or `<link>`) naming the index that covers a file — spec v2's discovery mechanism.
- **alternate**: `rel="alternate" type="text/markdown"` on an HTML page, pointing at its twin.
- **`X-Markdown-Tokens`**: the response header stating a markdown file's token estimate (`bytes // 4`) so a reader can budget before fetching.
- **content negotiation**: `Accept: text/markdown` returning the twin from the HTML route — Vercel's proposal, not the spec; needs `Vary: Accept`.
- **most-specific wins**: the v2 rule that a subpath `llms.txt` is authoritative for the URLs under its path over any file above it.
- **grammar** (of a full file): the page-block convention — Mintlify `# Title` / `Source:`, Anthropic YAML blocks, Cloudflare frontmatter — named in a header comment so a splitter never guesses.
- **round trip**: splitting a full file by its grammar and getting back exactly the index's page list — attribute C1.
- **banner mirror**: the hub's internal single-file mirror format (one page per banner block) that every acquisition path is normalised to before refine.
- **acquisition ladder**: the order in which a docset is obtained — existing `llms-full.txt`, then `llms.txt` + twins, then `Accept: text/markdown`, then a docs API, then a structured crawl.

## The judging

- **attribute**: one thing an llms file is judged on — an id (I1…H8), the kinds it applies to, a measure, a bar, a severity — 59 of them on the [rubric](/reference/attributes/).
- **pass**: one step of the optimizer (P0–P15), naming the attributes it judges and whether it is deterministic, model, or live — on the [passes page](/reference/passes/).
- **deterministic / model / live**: how a pass measures — a script with no model call; an LLM reading and deciding; an HTTP call or an agent exercised.
- **severity**: High (fails the CI gate), Medium (counted toward convergence), Low, Hygiene — a miss on an attribute has one.
- **convergence**: the loop state where every Medium-or-higher finding is fixed and a re-run finds none — the optimizer's stopping rule.
- **two hops**: the agent test's bar — from the index alone, seven of ten questions answered following at most two links (R5, P12).
- **steering**: text in a docs file that tells the reader what to say — forbidden (P4), pattern-rejected by the lint, found in 42.3% of a sampled wild set.
- **regeneration parity**: the check (P15) that a published file equals what the generator would emit from its inputs — a hand edit is a finding.
- **overrides**: the hand inputs a generator honours across regeneration — `title`, `summary`, `section_order`, `note` — the only place hand edits belong.
- **verified-as-of**: the date stamp on a volatile claim or line; older than 90 days at deploy and the page warns.
