---
name: note-organizer
title: "Note Organizer — raw notes to coherent structure"
description: >-
  Reorganize a pile of raw, messy notes — a brain dump, meeting-notes chaos, scattered reading notes, a mixed capture inbox — into a coherent, useful structure, losing and inventing nothing. Diagnoses what the notes are and what the owner needs, then applies the right PKM shape: Zettelkasten atomic notes + Map of Content, PARA-style actionability sort, or one restructured doc. TRIGGER: "organize these notes", "make sense of this dump", "sort my meeting notes", "clean up my notes", "turn this mess into something coherent", "dedupe/restructure my notes", or any handed-over file/text that is clearly a raw note dump. SKIP: live note capture/transcription (notes must already exist) → content-ingestion-extraction; drafting new prose → writing-expert; choosing or setting up a PKM system/tool → research-note-taking-pkm; inventorying ONE doc into a reference list → document-distiller; extracting from webpages/external sources → content-ingestion-extraction; saving session state → remember.
category: custom
version: 1.2.1
updated: 2026-07-04
model: claude-sonnet-5
effort: medium
whenToUse:
  - "organize, clean up, or declutter this pile of messy notes"
  - "sort my meeting / standup notes into actions, problems, decisions, and wins"
  - "turn my scattered reading notes into linked atomic notes with an index (MOC)"
  - "make sense of my capture inbox / brain dump — what's actionable?"
  - "dedupe and restructure these notes without losing anything"
keywords:
  - organize notes
  - note dump
  - brain dump
  - meeting notes
  - capture inbox
  - restructure
  - dedupe
  - atomic notes
  - map of content
  - actionability sort
tags:
  - notes
  - knowledge-management
  - organization
  - writing
---

# Note Organizer

Turn raw notes into an organized, coherent artifact. The job has three parts:
**diagnose** what the notes are and what they're for, **choose** the right
organizing shape, **transform** the content into it — without losing or
inventing anything.

Why diagnosis comes first: the correct output shape depends entirely on what
the notes are. Reading notes want atomic concept notes that accrete; a dump
full of commitments wants an actionability sort; a one-topic brainstorm wants
one clean document. Applying the wrong shape produces tidy-looking output
that's useless — the classic failure is turning an action list into an essay,
or shattering a coherent argument into confetti "atomic notes".

## Non-negotiable content rules

These hold for every mode. They matter more than any structural choice:

1. **Nothing is lost.** Every substantive item from the input appears in the
   output, or in an explicit `Unsorted / Parking lot` section at the end.
   Never silently drop a line because it's unclear — unclear items are exactly
   the ones the owner can't afford to lose.
2. **Nothing is invented.** Reorganize, merge, retitle, and restate — but do
   not add facts, decisions, action items, or interpretations that are not in
   the source. If a note is ambiguous, keep it and flag it (`⚑ unclear:`)
   rather than guessing what it meant.
3. **Restate, but stay traceable.** Prefer clear restatement over verbatim
   fragments (a note you can read cold beats a cryptic scrawl), but keep exact
   wording for anything where precision matters: quotes, figures, names,
   dates, commitments, error messages, code snippets, citations.
4. **Duplicates merge, conflicts surface.** Two notes saying the same thing
   become one. Two notes *contradicting* each other stay side by side with a
   `⚡ conflict:` marker — resolving the contradiction is the owner's call.

## Step 1 — Intake and inventory

Read all the input (pasted text, file, or folder). Break it into **items** —
the smallest units that stand alone: a thought, fact, decision, task, question,
quote, reference, or event. A bullet is usually an item; a paragraph may be one
item or several.

Tag each item with what it *is*. These signals are cheap to spot and drive
everything downstream:

| Item type | Typical signals |
| --- | --- |
| **Action** | imperative verb, "TODO", "need to", "@name", deadline, checkbox |
| **Decision** | "we agreed", "going with", "decided", chosen option |
| **Fact / claim** | declarative statement, figure, definition |
| **Idea** | "what if", "maybe we could", speculative phrasing |
| **Question** | literally a question, "?", "not sure whether" |
| **Problem** | "blocked", "broken", "degraded", "still failing", risk language, "!!!" |
| **Win** | "fixed", "shipped", "confirmed working", resolved blocker, positive outcome |
| **Reference** | URL, book/paper title, author name, "see X" |
| **Event / log** | timestamps, "met with", narrative past tense |

## Step 2 — Diagnose the corpus

From the inventory, answer two questions:

**What is this?** (dominant content)
- Mostly references + claims tied to sources → *reading / research notes*
- Mostly actions + decisions + events → *operational dump* (meetings, projects)
- Mostly ideas circling one theme → *brainstorm*
- Genuinely mixed, many topics, no dominant type → *capture inbox*

**What does the owner need from it?** Infer from the request and content: a
knowledge base to build on, a to-do state to act from, a document to write
next, or just order restored. When the request states a goal ("I need to write
this up", "what do I owe people?"), that goal overrides the content-based
guess. If the intent is genuinely undecidable *and* the choice would produce
very different outputs, ask one short question; otherwise pick the best fit
and say what you assumed.

## Step 3 — Choose the shape

| Diagnosis | Shape | Why |
| --- | --- | --- |
| Reading / research notes | **Atomic notes + MOC** | Concept-oriented atomic notes accrete: the next reading lands on the same concept note. A Map of Content (index note linking the atomic notes, grouped by theme) provides navigation. |
| Operational dump | **Actionability sort (PARA-style)** | Sort by *what to do about it*, not by topic: **Actions** (by project, owners/deadlines kept), **Problems** (unresolved bad state), **Decisions** (the record), **Wins** (resolved/shipped/confirmed good news), **Ideas**, **Questions**, **Reference** (facts worth keeping), **Archive** (superseded/stale). Actionability is unambiguous where topic taxonomies aren't. |
| Brainstorm (one theme) | **Single restructured doc** | One coherent markdown doc: one-paragraph summary up top, ideas clustered into named themes, strongest first, duplicates merged, open questions at the end. Splitting a single train of thought into atomic notes destroys it. |
| Capture inbox | **Triage first, then per-bucket** | Sort items into the three buckets above, then apply each bucket's shape. Small buckets (< ~5 items) stay as a simple list — don't build scaffolding for five lines. |

Two thresholds worth respecting (they come from PKM practice and prevent
over-engineering):

- **MOC threshold:** build a Map of Content only when ~10+ atomic notes
  cluster. Below that, a linked list at the top of one file is enough.
- **Atomicity is about clear edges, not brevity.** One *idea* per note — an
  idea you could link to from elsewhere. Don't chop a coherent 3-paragraph
  argument into three stubs; don't leave four unrelated claims fused in one
  note. Give each note a claim-like title that states the idea ("Retrieval
  practice beats re-reading", not "Learning notes 3").

## Step 4 — Transform

Common moves, all modes:

- **Claim-like titles.** Headings and note titles state content, not category:
  "Q3 launch slips two weeks" beats "Meeting notes".
- **Merge duplicates** into the strongest phrasing; keep any detail unique to
  either copy.
- **Extract actions faithfully**: verb + owner (if stated) + deadline (if
  stated). Do not assign owners or dates the source doesn't contain.
- **Collect questions** — they're future work, and they vanish when buried.
- **Keep provenance where it's cheap**: if the input had dates, speakers, or
  source names, carry them along (`(2026-03-14 standup)`, `(Ahrens ch. 2)`).
- **Every mode ends with `Unsorted / Parking lot`** when any item resists
  classification — this is how rule 1's "nothing is lost" is enforced in
  practice. Omit the section only when it would be empty.

Mode specifics:

- **Atomic notes + MOC**: one file per concept when writing to a folder
  (kebab-case filenames from the claim-titles, `[[wikilinks]]` between related
  notes); when returning a single response, one `##` section per atomic note
  plus the MOC at top. Factor by *concept*, not by source — two sources on one
  concept merge into one note with both cited. Items that don't merit a
  concept note (stray actions, unclear fragments) collect in an
  `Unsorted / Parking lot` note linked from the MOC.
- **Actionability sort**: output order is Actions → Problems → Decisions →
  Wins → Ideas → Questions → Reference → Archive → Parking lot, because
  that's the order of urgency. Group actions by project. **Problems** hold
  unresolved bad state (blockers, regressions, risks) — they usually drive
  actions, so cross-reference the action that addresses each one; a problem
  buried in Reference is the most expensive thing this skill can lose.
  **Wins** hold resolved/shipped/confirmed-good outcomes — they close the
  loop on earlier problems and give the owner the "what went right" read.
  Ideas and questions get their own sections — they are neither actionable
  nor archival, and burying them in Reference loses them. **Event/log**
  items fold into the items they contextualize as provenance (the date or
  speaker on an action or decision); a standalone event worth keeping lands
  in Reference. **Archive** is populated during dedup/merge, not by a Step 1
  tag: an item lands there when a later item in the same input supersedes it
  (a reversed decision, a replaced draft, an estimate overtaken by an
  actual). If the later item *contradicts* rather than supersedes, that's a
  `⚡ conflict` — keep both, don't archive either. Never let a commitment
  land in Archive. As with all sections, omit any that would be empty.
- **Single doc**: summary paragraph first (write it last), then themed
  sections ordered by strength/centrality, then `## Open questions`, then
  `## Parking lot` for the stragglers.

## Step 5 — Deliver

1. **Lead with the diagnosis** (2–4 lines): what the notes are, what shape
   was chosen and why, and anything assumed. This is the owner's chance to
   redirect before reading the whole artifact — and it makes a wrong guess
   cheap to fix.
2. **Then the organized output.** Pasted-text input → organized markdown in
   the reply. File/folder input → write files next to the input (a sibling
   `organized/` directory for multi-file output, or `<name>-organized.md` for
   a single doc) and summarize what was written. Ask before overwriting
   anything.
3. **End with counts**: items in → notes/sections out, duplicates merged,
   items folded into another item (a reference attached to a decision, a
   source citation absorbed into a concept note), flags raised (`⚑ unclear`,
   `⚡ conflict`), items parked. Every input item must be accounted for by
   exactly one of: appears in output, merged as duplicate, folded into
   another item, or parked. If the numbers don't reconcile, something was
   dropped; go back and find it.

## Example (abbreviated)

Input (pasted):

```
standup 3/14 - alice says api migration blocked on auth team
TODO ping auth team re: tokens
new pricing page copy due friday (bob)
idea: what if we cache the whole config at startup
decided: going with postgres for the event store
postgres decision - see also kleppmann ch 11
TODO ping auth team about token scopes
```

Output starts:

> **Diagnosis:** Operational dump (standup capture) — actions, a problem, a
> decision, one idea. Shape: actionability sort. "friday" left unresolved and
> flagged — the source doesn't say which Friday.
>
> ## Actions
> - Ping auth team about token scopes — *(dedup: appeared twice)*
> - Pricing page copy — owner: Bob, due Friday ⚑ unclear: which Friday
>
> ## Problems
> - API migration blocked on auth team *(Alice, 3/14 standup)* — addressed by
>   the token-scopes action above
>
> ## Decisions
> - Postgres for the event store *(3/14; ref: Kleppmann ch. 11)*
>
> ## Ideas
> - Cache whole config at startup
>
> **Counts:** 7 items in → 5 out (1 dup merged, 1 ref attached), 1 flag, 0 parked.
> *(No Wins/Questions/Reference/Archive/Parking-lot items — sections omitted.)*

For deeper method background (Zettelkasten, PARA, progressive summarization,
MOC practice), consult the `research-note-taking-pkm` skill if it's installed —
this skill is self-contained without it.
