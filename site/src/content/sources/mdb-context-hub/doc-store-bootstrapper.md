---
title: "Document Store Bootstrapper"
description: "Turns a folder of documents into an 'ideal doc store' with a numbered taxonomy, _meta/ indexes, archival policy, and resumable operator memory. Use for Google Drive engagement folders, customer KBs, p"
---

# Document Store Bootstrapper

Turns a folder of documents into an "ideal doc store" with a numbered taxonomy, `_meta/` indexes, archival policy, and resumable operator memory. Use for Google Drive engagement folders, customer KBs, project doc stores, and research dumps. For code repositories, use `repo-bootstrapper` instead.

## When to use this skill

- Organize a flat folder into a clean, numbered taxonomy
- Stand up a new engagement/customer/project folder to the standard
- Upgrade an existing partly-organized folder toward the ideal state
- Audit a folder and produce a gap report
- Generate or refresh `_meta/` index, manifest, and policy files
- Resume an interrupted run from `_meta/memory.md`

**When not to use:** code repositories (use `repo-bootstrapper`), single-file tasks, note-taking apps.

## Skill guidance

- Treat the target as an ideal-state doc store, not a minimally compliant one.
- Infer taxonomy from the **actual documents present** — do not invent categories with no documents.
- Preserve `.gdoc`, `.gsheet`, `.gslides`, `.gform`, `.gjam` shortcuts byte-for-byte (Drive links depend on exact filename).
- Never rename or move a load-bearing filename without explicit confirmation.
- Prefer non-destructive organization: move into folders, do not delete. Send deletion candidates to `99 Archive/`.
- For Drive-synced folders: use `mv` (not `cp`) so Drive sees a move event.
- Use `_meta/memory.md` as resumable state. If interrupted, the next run reads it and continues from the first pending step.
- Log the user's prompt and any clarifying answers to `_meta/prompts.md` **before** moving any files.

---

## Standard file manifest

Every compliant doc store must have ALL of the following inside `_meta/`:

### Workflow and operator state

| File | Purpose |
|------|---------|
| `_meta/memory.md` | Versioned operator log: plan, status, done, pending, resumption instructions |
| `_meta/prompts.md` | Versioned record of every user prompt and clarifying answer, in order |
| `_meta/CLAUDE.md` | Claude Code instructions for working in this doc store (taxonomy, policies, do/don't) |

### Taxonomy and standards

| File | Purpose |
|------|---------|
| `_meta/taxonomy.md` | Numbered folder taxonomy (00–99), purpose of each folder, what belongs where |
| `_meta/standards.md` | Naming conventions, filename hygiene, language conventions, date formats |
| `_meta/archive-policy.md` | Rules for what goes to `99 Archive/`: age, duplication, "Copy of …" markers |

### Indexes

| File | Purpose |
|------|---------|
| `_meta/INDEX.md` | Human-readable index: one-line description and key documents per folder |
| `_meta/manifest.json` | Machine-readable per-document manifest for LLM retrieval (path, kind, mtime, tags) |
| `_meta/glossary.md` | Acronyms, entities, system names, customer-specific terminology |

### Reference

| File | Purpose |
|------|---------|
| `_meta/contacts.md` | Stakeholders, owners, escalation paths (for engagement/customer folders) |
| `_meta/known-gaps.md` | Missing documents, stale items, orphan symlinks, TODOs |
| `README.md` (root) | One-page overview: what this folder is, taxonomy summary, where to look first |

---

## Standard taxonomy

Numerically prefixed so folders sort predictably. Adapt labels to the domain; keep the numbering scheme and reserved slots.

| Slot | Folder | Contents |
|------|--------|----------|
| 00 | `00 Overview` | Engagement/project context, master plan, contacts |
| 01 | `01 Notes & Updates` | Running notes, weekly updates, status |
| 02 | `02 Initiatives` | Multi-doc workstreams, project-style initiatives |
| 03 | `03 Account Reviews` | Periodic account/project reviews |
| 04 | `04 Meetings & Prep` | Meeting prep, agendas, transcripts pointer |
| 05 | `05 Cases & Retros` | Case analyses, postmortems, retros |
| 06 | `06 Reference` | Reusable reference docs, restore procedures, KB content |
| 07 | `07 Reports` | Generated/shared reports |
| 08 | `08 Office Hours` | Office hours presentations and prep |
| 09 | `09 Scripts & Artifacts` | Scripts, HTML dashboards, exported artifacts |
| 10 | `10 Symlinks` | Drive shortcut symlinks and external pointers |
| 99 | `99 Archive` | Stale items, duplicates, "Copy of …" files |
| — | `_meta` | All standard metadata, indexes, and operator state |

Empty slots are permitted but must be documented in `_meta/taxonomy.md` with a rationale, or removed if unused.

---

## Naming and archive rules

**Filename hygiene**
- Preserve `.gdoc`, `.gsheet`, `.gslides`, `.gform`, `.gjam` shortcuts exactly.
- Strip trailing whitespace on rename; never on move.
- Date prefixes use `YYYY-MM-DD `.
- Never rename load-bearing artifacts (scripts referenced by tooling, Drive-linked shortcuts).

**Date formats** — absolute dates only (`2026-05-20`), never relative (`Thursday`, `last week`).

**Language** — US English in all `_meta/` files. Short, declarative sentences.

**Archive policy (default — override in `_meta/archive-policy.md`)**
- Move to `99 Archive/` when ALL of: last modified > 180 days ago OR explicitly superseded, AND not currently referenced by an active initiative or open case.
- Always archive files starting with `Copy of `, `(1)`, or `– copy`.
- Use `99 Archive/<year>/` subfolders when volume warrants.

**Symlinks** — Drive shortcuts go in `10 Symlinks/`. Broken symlinks go in `10 Symlinks/_broken/` and are listed in `_meta/known-gaps.md`.

---

## Execution phases

Run in order. Phases 3–6 may run in parallel agents.

| Phase | Action |
|-------|--------|
| 0 — Intake | Resolve absolute path; read existing `_meta/memory.md`; if `Status: in_progress`, resume from first Pending item. Ask clarifying questions only if scope/archive aggressiveness/symlink handling are undecided. |
| 1 — Log prompt | Append user prompt + clarifying answers to `_meta/prompts.md`. Create `_meta/memory.md` if missing; set status `in_progress`. |
| 2 — Inventory | List folder. Classify each item: doc, shortcut, script, artifact, subfolder, junk (`.DS_Store`). |
| 3 — Create taxonomy | Create numbered folders that will receive content. Skip empty slots; document skips in `_meta/taxonomy.md`. |
| 4 — Create `_meta/` | Write all Standard File Manifest files using the templates below. |
| 5 — Move documents | Move each top-level file into the correct numbered folder. Use `mv` for Drive folders. |
| 6 — Archive | Walk for archive candidates per `_meta/archive-policy.md`. Move to `99 Archive/`. |
| 7 — Build indexes | Generate `_meta/INDEX.md` and `_meta/manifest.json` from the final layout. |
| 8 — Close out | Set `_meta/memory.md` Status to `complete`. Write final summary: counts moved, archived, gaps recorded. |

---

## Audit checklist

Run against `path/_meta/` and the folder layout:

**`_meta/memory.md`** — versioned format, status field, Done/Pending/Resumption sections, owner and target path.

**`_meta/taxonomy.md`** — every numbered top-level folder explained; empty folders justified or removed; "what goes where" mapping.

**`_meta/INDEX.md`** — one entry per folder; top 5 key docs listed; last-refreshed date in header.

**`_meta/manifest.json`** — valid JSON; one entry per non-trivial document (exclude `.DS_Store`, hidden files); each entry has `path`, `kind`, `mtime`, `tags[]`.

**`README.md`** — names the folder and purpose; links to `_meta/INDEX.md` and `_meta/taxonomy.md`; last-refreshed date.

---

## File templates

### `_meta/memory.md`
```markdown
# <Folder Name> Organization - Memory File

Version: <semver>
Last updated: <YYYY-MM-DD>
Owner: <name> (<email>)
Target folder: <absolute path>

## Status
<in_progress | complete>

## Plan version <semver>
Top-level taxonomy:
- 00 …
- 01 …
- _meta …

## Done
- …

## Pending
- …

## Resumption
Re-read this file, list the folder contents, continue from the first pending step.
```

### `_meta/manifest.json`
```json
{
  "version": 1,
  "generated_at": "<YYYY-MM-DDTHH:MM:SSZ>",
  "root": "<absolute path>",
  "documents": [
    {
      "path": "00 Overview/Master Plan.gsheet",
      "kind": "gsheet",
      "is_shortcut": true,
      "mtime": "2026-05-13T16:27:00Z",
      "tags": ["overview", "master-plan"]
    }
  ]
}
```

### `_meta/CLAUDE.md`
```markdown
# Claude Code instructions for <Folder Name>

This folder is managed under the `doc-store-bootstrapper` skill.

Before doing any work:
1. Read `_meta/memory.md` for current state.
2. Read `_meta/taxonomy.md` for what belongs where.
3. Read `_meta/standards.md` for naming and archive rules.
4. Log new prompts to `_meta/prompts.md` before moving files.

Do not:
- Delete files. Move to `99 Archive/` instead.
- Rename `.gdoc` / `.gsheet` / `.gslides` shortcuts (Drive links break).
- Invent taxonomy categories with no documents.

Resumption: read `_meta/memory.md` and continue from the first item in Pending.
```

---

## Bootstrap invocation

> Bootstrap the folder at `<absolute path>` to the `doc-store-bootstrapper` standard. Follow the Execution Phases in `~/.claude/skills/doc-store-bootstrapper/SKILL.md`. Capture my prompt to `_meta/prompts.md` before moving any files. Use `_meta/memory.md` for resumable state.
