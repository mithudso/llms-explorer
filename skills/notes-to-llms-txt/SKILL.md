---
name: notes-to-llms-txt
description: >-
  Turn disorganized notes — a scratch file, a run of meeting notes, a mixed-topic dump with
  todos and facts and half-finished thoughts tangled together — into a well-formed llms.txt
  family (index, full, small, facts). Segments the mess into atomic units, clusters them by
  topic (notes are rarely about one thing), drafts a source-anchored entry per topic, compiles
  the family in the same grammar `llms-deep-optimizer` judges, then hands the draft to
  `llms-deep-optimizer` so the output actually clears the bar rather than stopping at "has
  headings now." TRIGGER: /notes2llms, "turn my notes into an llms.txt", "structure these
  meeting notes as llms.txt", "clean up this scratch file into an llms family", "organize my
  notes into llms.txt", "my notes are a mess, make them navigable". SKIP: the notes are
  already about one well-scoped concept, not a mixed dump → llms-concept-abstractor; an
  llms.txt file already exists and just needs auditing/fixing → llms-deep-optimizer; the
  request needs new research, not organizing what's already written down → /dr.
version: "1.0.0"
updated: "2026-09-01"
model: claude-sonnet-5
effort: medium
category: developer
tags: [llms, notes, structuring, extraction]
keywords:
  - disorganized notes
  - meeting notes to llms.txt
  - scratch file cleanup
  - notes structuring
  - topic segmentation
  - source-anchored facts
related_skills:
  - llms-deep-optimizer
  - llms-concept-abstractor
  - concept-family-explorer
whenToUse:
  - "turn my notes into an llms.txt"
  - "structure these meeting notes as llms.txt"
  - "clean up this scratch file into an llms family"
  - "my notes are a mess, make them navigable"
whenNotToUse:
  - "the notes are already about one well-scoped concept, not a mixed dump (use llms-concept-abstractor)"
  - "an llms.txt file already exists and just needs auditing (use llms-deep-optimizer)"
  - "the request needs new research, not organizing existing notes (use /dr)"
---

# Notes → llms.txt (`/notes2llms`)

Raw notes are multi-topic, unordered, and mix genres — a fact next to a todo next to a
half-formed question next to a name. `llms-concept-abstractor` assumes you already know the
one concept to pull out; `llms-deep-optimizer` assumes structure already exists to audit.
This skill sits before both: it takes the mess as-is, finds the topics actually in it, and
drafts a first llms.txt family good enough for `/ldo` to take the rest of the way.

```
notes ─▶ [1] ingest ─▶ [2] segment ─▶ [3] cluster by topic ─▶ [4] draft per topic
                                                                       │
                                              [6] report ◀─ [5] compile + hand to /ldo
```

## When not to use

- Notes are already scoped to one concept → `llms-concept-abstractor` (it does the
  lexicon/harvest/classify work this skill skips by assuming single-topic input).
- An llms.txt family already exists and needs auditing, not drafting from scratch → `/ldo`.
- The ask needs genuinely new research, not organizing what's already written → `/dr`.

## Non-negotiables

1. **Never invent a fact the notes don't contain.** Every line in `llms-facts.txt` traces to
   a specific note/paragraph; a gap in the notes is a gap in the output, not something to
   fill from general knowledge.
2. **Never silently merge conflicting notes.** Two entries that disagree (a date changed, a
   decision reversed) go side by side under `## Disagreements`, same rule `llms-concept-
   abstractor` and `llms-deep-optimizer` both use — averaging or picking one silently drops
   information a reader needed.
3. **Redact anything that looks like a credential or secret before it reaches any output
   file.** Meeting notes and scratch files routinely contain API keys, passwords, and
   tokens someone pasted in passing. Scan every unit for secret-shaped strings (long
   high-entropy tokens, `key=`/`password=`/`token=` patterns, connection strings) before
   Step 4 drafting; redact to `[REDACTED]` in every output file, and say how many were
   redacted in the Step 6 report. This is not optional even when the run is private — output
   families from this skill are the kind of file that gets pasted into a public repo or
   contributed to a shared library later, and a secret that survives to that point is a
   credential leak, not a formatting slip.

## Inputs

- **notes** (required) — pasted text, a file path, or a directory of files. Read all of it;
  don't sample.
- **hint** (optional) — a topic or two the user already knows are in there, to seed
  clustering; never a reason to skip discovering topics they didn't mention.
- **budget-tokens** (optional, default 8000) — size of `llms-small.txt`, same meaning as
  `llms-concept-abstractor`'s flag.

## Step 1 — Ingest

Read every source in full. Note the rough shape (one long scratch file vs. many dated
meeting-note files vs. a chat export) — it affects Step 2's unit boundaries (a meeting-note
file usually has natural per-meeting boundaries already; a scratch file doesn't).

## Step 2 — Segment into atomic units

Split into the smallest units that still make sense alone: a bullet, a paragraph, a
heading-scoped block. Tag each unit's apparent genre — **fact**, **todo**, **decision**,
**question**, **name/entity mention**, **noise** (calendar boilerplate, signatures,
timestamps with nothing else). Drop `noise` units; count them for the Step 6 report rather
than silently discarding without a trace.

## Step 3 — Cluster by topic

Group the surviving units by subject. Notes are rarely about one thing — a single meeting-
notes file might cover three customers and a personal todo; cluster by what the unit is
*about*, not by which file or meeting it came from. Merge clusters that are really the same
topic under different names (a customer mentioned by company name in one place and by
project codename in another); keep clusters distinct when they only share a keyword but
differ in subject (two different "onboarding" processes for two different customers).

A cluster with only one or two surviving units is too thin for its own llms.txt entry —
fold it into `## Miscellaneous` in the index rather than forcing a topic that doesn't
support one.

## Step 4 — Draft per topic

For each cluster with enough content, draft an entry: title, one-line description, the
kept facts (source-anchored to the originating note/unit), any URLs found verbatim (never
constructed or guessed), open questions and todos listed as such rather than smoothed into
facts. `llms-facts.txt` lines carry their source anchor the same way `llms-concept-
abstractor`'s do — see that skill's `references/output-contract.md` for the exact grammar
so this skill's draft and `/ldo`'s judgment of it agree on shape.

## Step 5 — Compile and hand to `/ldo`

Write `llms.txt` (topic index), `llms-full.txt`, `llms-small.txt` (budgeted per
`budget-tokens`), `llms-facts.txt` — same file grammar `llms-deep-optimizer` judges
(`~/.claude/skills/llms-deep-optimizer/references/attributes.md`); don't invent a different
shape only to have `/ldo` flag it. Then run `/ldo` on the compiled family — this skill's
draft turns chaos into *structure*; `/ldo`'s multi-pass audit is what turns structure into
something that actually passes the bar (links resolve, facts are anchored, size ladder
holds). Report both stages; don't claim the family "is done" before `/ldo` has run on it.

## Step 6 — Report

Topics found (and how many were folded into Miscellaneous), units kept vs. dropped as
noise, secrets redacted (count, never the values), files written, `/ldo`'s verdict on the
compiled family. A run that skips the `/ldo` handoff must say so explicitly rather than
implying the family is finished.

## Trigger examples

**Should trigger:**
- "Here's three weeks of scattered meeting notes — turn this into an llms.txt I can actually navigate."
- "My project scratch file is a disaster, structure it into an llms family."
- "Clean up these notes and give me something the team can reference."

**Should NOT trigger:**
- "Pull everything these docs say about connection pooling" (single concept, existing corpus) → `llms-concept-abstractor`.
- "Audit this llms.txt, something's broken" (structure already exists) → `/ldo`.
- "Research CRDTs from scratch" (no existing notes to organize) → `/dr`.
