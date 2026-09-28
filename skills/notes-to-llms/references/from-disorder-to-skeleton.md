# From a heap of notes to sections and units

<!-- notes-to-llms · references/from-disorder-to-skeleton.md · 2026-09-01 -->

The file format is settled in `v2-grammar.md`. The hard part is that notes are organised by
*when they were written* and an llms family has to be organised by *what a reader will ask*.
This is the translation.

## 1. Read the inventory, not the notes

After `notes_normalise.py`, work from `<project>.pages.json`: one row per page (`path`,
`title`, `bytes`, `headings[]` with `anchor` and `duplicate`) and no bodies. Everything in
§4 (the skeleton) can be decided from titles, headings and sizes. Pull bodies only for the
pages you are extracting units from.

This is not just tidiness. A 200-note vault is a few hundred KB of inventory and tens of MB
of bodies; reading the inventory first is the difference between proposing a skeleton in one
pass and spending the context window on other people's meeting notes.

Three fields in the report change what you do next:

| Report field | What it means | What you do |
|---|---|---|
| `pages_without_headings` | those pages contribute **no** resolvable anchor | their units carry the bare page URL, no `#`. If they hold more than ~20 % of your units, add headings to the sources first — otherwise `P7 R3` is a High you cannot fix later |
| `duplicate_anchors` | two headings share one slug | a unit pointing there is ambiguous, not broken. Rename one heading in the source, or accept it and say so |
| `skipped_unreadable` | a file was not read at all | convert it, or name it in the report. Never let it pass silently |

## 2. Units: one claim, one line, one source

A unit is the smallest thing that can be true or false on its own.

**Good**

```
- [statement] The gateway allows 60 requests per minute per key — /my-notes/limits.md#rate-limits
- [problem] A 429 means the token bucket is empty; back off rather than retry — /my-notes/errors.md#errors
- [definition] A "burst" is the number of requests absorbed above the steady rate — /my-notes/limits.md#burst
```

**Bad, and why**

| Line | Why it fails |
|---|---|
| `- [fact] Rate limiting is important for API stability` | not checkable; belongs in the blockquote or nowhere |
| `- [statement] Limits are 60/min, bursts are 10, the bucket refills every second, though staging differs and we should revisit` | three claims and an opinion; split, drop the opinion |
| `- [fact] See the limits note` | a pointer, not a claim |
| `- [statement] The gateway allows 60 rpm — /my-notes/limits.md` | fine *only* if that page has no headings; otherwise anchor it |
| `- [statement] … — upload://my-notes/limits.md` | `P7 C6` High: the linter accepts only `http`, `/`, `.` |
| `- [statement] … — /a.md#x · also: /b.md#y` | breaks `UNIT_RE`, so the line counts as unsourced (High) |
| `- [thought] …` | `thought` is not in `UNIT_TYPES` |

**Typing.** Pick by what the reader would do with it, not by grammar:

| Type | Use for |
|---|---|
| `definition` | a term being pinned down |
| `concept` | a model or idea the rest depends on |
| `statement` | a spec, limit, default, version, guarantee |
| `parameter` | a named flag, field, env var, config key |
| `actionable` | a step someone performs |
| `snippet` | a command or code block worth keeping literally |
| `problem` | a known failure and its symptom |
| `change` | something that was true before and is not now |
| `fact` | a measured or observed number that is none of the above |
| `question` | a question the material answers (useful for the question bank) |
| `quote` | words that must be attributed verbatim |
| `idea` | a proposal that is not yet true. Mark it; do not promote it to `statement` |

**Anchoring.** The anchor is the slug of the nearest heading *above* the text, as recorded
in the inventory. Never invent one, never use `#top`, and never add a `-2` suffix to a
repeated heading: all three resolve to nothing.

**Keywords.** Add `· keywords: …` carrying the exact tokens someone would type — backtick
spans, flags, env vars, error codes, API names. A fact whose exact tokens are not in its
keywords is invisible to a cheap keyword lookup, however good the vector index is. This is
also where a corroborating second source goes, since `also:` is not a legal field.

## 3. Dedupe, and what to do with disagreement

Notes repeat themselves: the same decision recorded three times in three meetings.

1. **Exact dedupe** on normalised text (case, whitespace, trailing period).
2. **Near-dedupe**: keep the fresher, better-sourced one. Put the loser's URL in
   `keywords:` so the claim still carries its corroboration.
3. **Contradiction**: two units disagreeing on a number or a version. **Keep both**, stamp
   each with its `verified-as-of`, and flag it. Silently picking one is how a stale note
   becomes the published truth.
4. **Superseded**: an old claim the notes explicitly replace. Type the old one `change` and
   put it under `## Optional`, or drop it and say you dropped it.

`docset_refine units` does 1–2 for one mirror, on by default (`--no-dedup` turns it off);
`topical` does them over a merged pool, using the embed pool unless `--no-embed`. Neither
takes a `--pool` flag: for `topical` the pool is one or more repeated `--from` paths.

## 4. The skeleton

Sections are the H2s of the index. Three sources, in this order of trust:

1. **An existing concept-tree node**, when the subject has one: its children are the
   candidate sections, and using them keeps this file consistent with everything else. This
   is also the hard prerequisite for `docset_refine topical` (route A in the skill) — it
   exits if the subject is not a node, and a node with no children collapses to one section.
2. **Clustering the units** — k ≈ √n capped at 12, named from each cluster's top keywords
   plus its most central `definition` unit. With a hub checkout that is
   `semantic_ops.cluster` over `embed_core.embed_texts` embeddings; without one, cluster by
   keyword overlap. Worse, but not useless.
3. **The questions the notes keep answering.** Write 10 a reader would arrive with. Every
   question must land in exactly one section. A question with no home is a missing section;
   a section no question lands in should be merged or demoted.

Then:

- **≤ 9 sections: keep. 10–12: merge down to ≤ 9. Over 12, or an index over 10 000 bytes:
  split hub-and-spoke.**
- **Order by expected query frequency**: definition/spec → how-to → reference → evidence →
  tooling → optional. Not alphabetically, and not by folder.
- **`## Shared` once** for cross-cutting material (glossary, error codes, versions), never
  duplicated across sections.
- **`## Optional` last**, and it is a convention only: nothing mechanical consumes it.
- **Coverage: ≥ 3 facts and ≥ 1 definition per section.** Thinner is a research gap, not a
  section: merge it, or keep it under `## Optional` with the count stated.

Name sections after what a reader is looking for ("Rate limits and backoff"), not after
where the material came from ("Q3 meeting notes") and not after an abstraction the notes do
not support ("Governance").

## 5. Choosing link targets

The index needs links, and links need destinations. For notes there are three:

1. **The pages themselves.** Group by page: the pages carrying the most units in a section
   are that section's primary links.
2. **`llms-facts.txt#<section-slug>`.** This is what lets a reader answer without opening
   any page, and it is what makes the family navigable in one hop. Every section links its
   own facts anchor — which only works if the facts file is grouped **by section**, using
   the same slugs. `docset_refine topical` does that; `export_llms.build_facts` groups by
   page instead, which is why the skill tells you to discard that export.
3. **Anything external the notes cite** — index-only. Do not republish third-party bodies.

Descriptions are **extractive**: the section's definition unit, or the page's title plus its
first real sentence. Aim inside the 10–25 word band. Remember that the gate only catches a
literal restatement of the link name (`P3 D2`), so a lazy description passes lint and still
fails the reader — that judgement is yours.

## 6. What to reject

Write rejections to `<out>/pool.rejected.jsonl` in the shape `topical` already uses —
`{"file": …, "line": "<first 120 chars>", "reason": …}` — and report the count. Reject:

- **`unsourced`**: cannot be tied to a page. The most important rejection there is.
- **`not-a-claim`**: an aspiration, a to-do, a mood.
- **`private`**: a personal remark, a named judgement of someone, anything the note's
  author would not publish.
- **`secret`**: a credential. Drop the unit and name the source note so the user can
  rotate it. Never rewrite it as "redacted" and ship the line.

Rejecting is cheap and reversible. A fabricated source is neither.

## 7. Before you call it done

Run the ten questions from §4.3 against the generated index. The bar borrowed from `/ldo`
P12: **≥ 8 of 10 answerable from the index in ≤ 2 hops, ≥ 7 from the facts file alone.**

If it fails, the problem is almost always the skeleton rather than the units. Go back to §4
before touching a single line of the facts file.
