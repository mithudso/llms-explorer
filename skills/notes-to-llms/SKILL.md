---
name: notes-to-llms
description: >-
  Turn a disordered pile of notes, docs or exports (brain dump, markdown folder, Obsidian
  vault, Notion export, pasted research) into a spec-v2 llms.txt family: llms.txt index,
  llms-facts.txt, optional llms-full.txt and llms-small.txt, manifest.json, passing
  llms_lint.py at 0 High. Every fact keeps a resolvable source#anchor, every link a 10-25
  word description, and the index stays under 10 000 bytes or splits hub-and-spoke.
  TRIGGER: "turn these notes into an llms.txt", "make an llms family from this folder",
  "notes to llms", "build llms.txt from my Obsidian vault", "/n2l", any pile of notes
  plus a request for an agent-readable index.
  SKIP: auditing or fixing an llms file that exists, or a topical file from an
  already-graded fact pool → llms-deep-optimizer (/ldo); the grammars and spec themselves
  → document-formats; inventorying ONE document into a reference list →
  document-distiller; keeping notes as notes → note-organizer; crawling a live site →
  web-text-mirror.
version: 1.0.0
updated: 2026-09-01
model: claude-opus-5
effort: high
---

# notes-to-llms (`/n2l`)

Notes are disordered because nobody wrote them for a reader. An llms family is the
opposite artifact: a **promise list** where every line is a claim a reader can check.
This skill is the bridge, and it is `document-distiller` with the two things distillation
leaves out: **structure** (an index a reader navigates in ≤ 2 hops) and **anchors**
(a source and heading slug on every fact, that the gate can actually resolve).

Authority: `hub/scripts/llms_lint.py` is the bar, and it wins every disagreement.
`docs/site/components/02-notes-to-llms.md` is design intent for the hosted version of
this workflow, not an implemented contract; where it and the linter differ, follow the
linter. Method for an already-graded fact pool:
`skills/llms-deep-optimizer/references/facts-to-llms-howto.md`.

Reference pack, read on demand:

- `references/v2-grammar.md` — every file's grammar, every threshold, every finding code
  with its real pass, attribute and severity. **Read before writing any file.**
- `references/from-disorder-to-skeleton.md` — how to get sections and units out of a heap:
  clustering, the coverage rule, unit typing, dedupe, what to reject.

Helper: `scripts/notes_normalise.py` — stdlib, no network, no model. Tested by
`scripts/test_notes_normalise.py` (17 tests, three of which assert against `llms_lint.py`
itself rather than against a restatement of its rules).

---

## The one rule that decides everything

**A fact needs a source the linter accepts and an anchor it can resolve.** Two findings
enforce it, and both are High:

- **P7 C6** — a unit line whose source does not start with `http`, `/` or `.` counts as
  *unsourced*. A tidy-looking custom scheme such as `upload://project/note.md` is a High,
  not a source. Notes therefore get root-relative sources, `/<project>/<relpath>`, and
  `--base-url` swaps in an absolute URL when the material is served.
- **P7 R3** — an anchor that is present but not found in the mirror is unresolved, and
  above 20 % of units that is a High. `llms_lint._mirror_headings` collects anchors with
  an **ATX-only** regex into a **set**, so: setext headings must be converted (the
  normaliser does it), repeated headings share one anchor and never get a `-2` suffix, and
  a page with no headings gets **no anchor at all** — never `#top`, which resolves to
  nothing and fails.

`scripts/notes_normalise.py` handles all of that and reports what it could not fix. A unit
whose text cannot be tied to a page is **rejected, never guessed**.

---

## Workflow

Announce the route before starting. Do not skip phase 0.

### 0 · Scope

Ask only what changes the output, and only if the material does not already answer it:

1. **Subject and audience** — one sentence. It becomes the H1 and the blockquote.
2. **Rights and secrets** — may this be published? Does it contain credentials, third-party
   text, or personal remarks? This decides the source URLs, whether `llms-full.txt` may
   exist at all, and whether the `--third-party` flag is needed at the gate. Asking now
   costs one sentence; finding out at phase 5 costs the whole generation.
3. **Model passes allowed?** Deterministic-only needs no model and no network, and yields
   snippets, table parameters, definitions and changelog changes — but **no prose units**.

If the material is not actually notes (one document to inventory, or notes the user wants
kept *as notes*), stop and hand off to `document-distiller` or `note-organizer`.

### 1 · Normalise

```bash
python skills/notes-to-llms/scripts/notes_normalise.py NOTES_DIR \
    --project my-notes --out build/          # or --base-url https://example.com/u/me/notes
```

Writes `build/my-notes.md` (the banner mirror) and `build/my-notes.pages.json`. The mirror
is deliberately `<project>.md` and not `<project>.mirror.md`: `docset_refine` derives
`<stem>.reference/` and `<stem>.llms/` from the stem, and a two-part stem produces
`my-notes.mirror.llms/`, which no documented command expects.

Read the **inventory**, not the note bodies. Report what it dropped (empty, duplicate,
unsupported suffix), which pages have no headings, and which headings share an anchor.

Convert what the script cannot read, before normalising:

```bash
pandoc -t gfm -o note.md note.docx        # .docx
pdftotext -layout note.pdf note.txt       # .pdf; then add headings by hand
```

Then re-run the normaliser and check `pages_without_headings` did not grow: conversion
routinely flattens headings, and a headingless page costs every unit on it its anchor.

### 2 · Extract units

```bash
cd hub && PYTHONPATH=scripts .venv/bin/python -m docset_refine all \
    ../build/my-notes.md --first-party [--no-units] [--polish]
```

- `--first-party` is right for a user's own notes: it keeps short pages and blog-shaped
  prose that the default boilerplate policy would strip.
- `--no-units` skips the local-model pass (deterministic only). The flag is **not**
  `--no-llm`; that flag does not exist on this subcommand.
- `--polish` (the `claude -p` pass) is opt-in, not part of the default chain.

The chain is `clean → extract → units → [polish] → render → export`, producing
`build/my-notes.reference/all_units.jsonl` — **the pool, which is what you want** — and
also `build/my-notes.llms/`, an export you should **discard**. That export is site-shaped:
`export_llms` names sections from the first URL path segment, so every root-level note
lands in one `## Overview`, and it groups facts by page rather than by section. Both fight
the rules in phase 3.

Without a hub checkout, build the pool by hand against
`references/from-disorder-to-skeleton.md` §2. One unit is one claim, ≤ 2 sentences and
≤ 400 chars, typed from `UNIT_TYPES`:

```
concept · fact · actionable · question · problem · statement
quote · idea · snippet · parameter · definition · change
```

### 3 · Build the skeleton

Sections are the H2s of the index. Derive them in this order of trust: an existing
concept-tree node → clustering the units → the reader questions the notes keep answering.

- **≤ 9 sections: keep. 10–12: merge down to ≤ 9. Over 12, or an index over 10 000 bytes:
  split hub-and-spoke.**
- Order by expected query frequency: definition/spec → how-to → reference → evidence →
  tooling. Not alphabetically, and not by folder.
- `## Shared` once for cross-cutting material; `## Optional` last.
- **Coverage: ≥ 3 facts and ≥ 1 definition per section.** Thinner is a gap: merge it, or
  keep it under `## Optional` with the count stated ("thin: 2 facts").

Show the skeleton and let the user rename, reorder and demote **before** generating. This
is the cheapest correction point in the workflow.

### 4 · Write the family

Two routes. Pick by whether the subject is already a concept-tree node.

**Route A — `docset_refine topical`** (better output; use it when you can). It assigns
facts to sections, groups the facts file under the same slugs the index anchors to (so
`llms-facts.txt#<section-slug>` answers in one hop), and writes `pool.rejected.jsonl` and
a manifest carrying `generated`, per-section fact counts and `rejected`.

```bash
cd hub && PYTHONPATH=scripts .venv/bin/python -m docset_refine topical \
    --from ../build/my-notes.reference/all_units.jsonl \
    --subject "Rate limiting" --out ../build/my-notes.llms/ [--no-embed] [--summary "…"]
```

**Prerequisite, and it is hard:** `topical` calls `ConceptTree.load()` and exits with
`no concept-tree node for '<subject>' — run concept-family-explorer or add the node first`
unless the subject is a node. Its **children become the sections**, so a childless node
collapses to a single section and defeats phase 3. Add the node with its children first,
or take route B. `--no-embed` makes assignment keyword-only (no Ollama call).

**Route B — write the files yourself** from `all_units.jsonl`, following
`references/v2-grammar.md`. Always available. Non-negotiables:

- `llms.txt` — H1; blockquote saying what it is, who it is for, and `verified-as-of`;
  `## Section` headings; `- [name](url): description` lines. **Every link gets a
  description, 10–25 words, extractive, naming the exact tokens a searcher would type.**
- `llms-facts.txt` — `- [type] text — url#anchor`, grouped under the index's section slugs.
- `manifest.json` — the real emitted shape is in `references/v2-grammar.md` §5. Do not
  invent one: the `P5 H8` drift check reads specific keys and silently passes on a manifest
  it cannot parse.
- A provenance banner as an HTML comment (`P9 P1`); neither generator writes one, so on
  route A inject it through `overrides.note`.
- `llms-full.txt` only if the user owns the text, and never without `llms-small.txt`
  beside it (`P5 S2` Medium). Both come from `docset_refine export`, not from `topical`.

Hand edits go in `manifest.json`'s `overrides` (`title`, `summary`, `section_order`,
`note`), **never into the generated files**, or the next regeneration discards them.

### 5 · Gate

```bash
hub/.venv/bin/python hub/scripts/llms_lint.py check build/my-notes.llms/ \
    --mirror build/my-notes.md --json [--third-party]
```

`--mirror` is what turns the anchor check (P7 R3) from `na` into a real verdict; run it
without and the anchors are unproven. `check` exits 1 on any unfixed High, which is the CI
and publish gate. Read `counts` and `findings[].{severity,pass,attr,line,msg}`.

**0 High is the bar.** Fix every High and every Medium you can, then hand off to `/ldo` for
the model and live passes (navigation, facts truth, serving headers, agent usability).

**If the Highs cannot be cleared** — most often more than 20 % of units unresolved because
too many pages lost their headings in conversion — do not ship. Report the run as
`evidence-limited`, name the blocking finding and the pages responsible, and offer the two
real fixes: restore headings in those sources, or drop their units.

### 6 · Report

Fill this in; do not improvise the shape:

```
Inputs      N files → P pages (E empty, D duplicate, S unsupported: <list>)
Anchors     H headings · A pages with none · C repeated slugs
Units       U total (by type: …) · R rejected (<reason: count>, see pool.rejected.jsonl)
Family      K sections · index B bytes · F facts · full/small: yes|no
Gate        High: 0 · Medium: m · Low: l  (llms_lint exit 0|1)
Route       A (topical) | B (hand-written) · model passes: on|off
Left out    <every dropped page and rejected unit, or "nothing">
```

A silent loss is the failure mode this whole workflow exists to prevent, so `Left out` is
never blank when anything was dropped.

### Re-runs

More notes arrive: re-run phase 1 over the whole pile (never a subset — the inventory and
the dedupe are whole-corpus), then `docset_refine units` again, which is resumable and
re-extracts only what changed. Keep the same `--project`, so sources and anchors are
stable, and keep `manifest.json` in place, so `overrides` survive. Regeneration from the
same inputs and overrides is byte-stable except timestamps (`P15`).

---

## Anti-patterns

| Tempting | Why it fails |
|---|---|
| Inventing a plausible URL for an unsourced claim | P7 R3 checks the anchor resolves; a fabricated source is worse than a rejected unit |
| A custom `upload://` or `notes://` scheme | P7 C6 High: the linter accepts only `http`, `/`, `.` |
| Anchoring a headingless page to `#top` | `#top` is in no page's anchor set, so every such unit is unresolved |
| `- [statement] X — url · also: url2` | breaks `UNIT_RE`, so the line is counted unsourced (High). Corroborate via `keywords:` or a second unit |
| Shipping `docset_refine export`'s index | folder-shaped: sections come from URL path segments, facts group by page |
| Writing prose descriptions that read well | The index is a promise list; descriptions are extractive and name exact tokens |
| Putting note bodies inside `llms.txt` | That is `llms-full.txt` wearing the wrong name: `P5 S1` High over 100 000 bytes |
| One section per source folder | Sections are topics a reader asks about, not the layout the notes happened to have |
| Fixing a generated file by hand | Regeneration discards it; use `overrides` |
| Skipping `--mirror` on the lint run | Anchor resolution reports `na`; you have not tested the thing that matters most |
| Dropping unreadable files quietly | Convert them, or name them in the report |

## Definition of done

- `llms_lint.py check <dir> --mirror <mirror>` exits 0 with **0 High**.
- 100 % of index links carry a description; ≥ 95 % inside the 10–25 word band.
- 100 % of unit lines carry a source the linter accepts; unresolved anchors under 20 %,
  and every headingless page's units carry no anchor rather than a broken one.
- Index ≤ 10 000 bytes, or split hub-and-spoke with counts on every family line.
- Every section has ≥ 3 facts and ≥ 1 definition, or sits under `## Optional` saying why.
- Regenerating from the same inputs and overrides is byte-stable except timestamps.
- The report is filled in, and `Left out` accounts for every dropped page and rejected unit.
