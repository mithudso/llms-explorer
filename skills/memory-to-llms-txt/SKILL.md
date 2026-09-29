---
name: memory-to-llms-txt
description: >-
  Turn an agent's persistent memory store — Claude Code auto-memory (MEMORY.md index +
  frontmatter'd memory/*.md files typed user/feedback/project/reference), a `.remember/`
  time-decay pyramid (now.md/today-*.md/recent.md/archive.md/core-memories.md), a napmem-style
  memory pyramid, or an ad-hoc project MEMORY.md — into a well-formed llms.txt family (index,
  full, small, facts) so the memory becomes queryable and servable the same way any other
  docset is, instead of only readable by re-loading the whole store into context. Unlike
  notes-to-llms-txt, memory files already carry real structure (type/provenance metadata,
  explicit recency tiers, dated entries) — this skill preserves that structure as facets
  rather than re-deriving topic clusters from scratch, and flags entries whose recorded facts
  no longer match the live system (the exact failure mode this ecosystem has hit repeatedly:
  a memory recording a path/version that later moved). TRIGGER: /memory2llms, "turn my memory
  files into an llms.txt", "make MEMORY.md queryable", "export the .remember pyramid as
  llms.txt", "build a servable index of what this agent remembers", "compile the memory store
  into a docset". SKIP: the input is unstructured scratch notes/meeting dumps, not a
  maintained memory store → notes-to-llms-txt; a repo's code/docs, not its memory files →
  crawl-repo-to-llms; auditing an llms.txt family that already exists → llms-deep-optimizer.
version: "1.0.0"
updated: 2026-09-05
model: claude-sonnet-5
effort: medium
category: developer
tags: [llms, memory, structuring, extraction, docset]
keywords:
  - MEMORY.md
  - memory pyramid
  - .remember export
  - napmem export
  - agent memory to docset
  - memory drift detection
related_skills:
  - notes-to-llms-txt
  - llms-deep-optimizer
  - llms-concept-abstractor
  - project-registrar
whenToUse:
  - "turn my memory files into an llms.txt"
  - "make MEMORY.md queryable"
  - "export the .remember pyramid as llms.txt"
  - "compile the memory store into a docset"
whenNotToUse:
  - "the input is unstructured scratch notes, not a maintained memory store (use notes-to-llms-txt)"
  - "the source is a repo's code/docs, not its memory files (use crawl-repo-to-llms)"
  - "an llms.txt family already exists and just needs auditing (use llms-deep-optimizer)"
---

# Memory → llms.txt (`/memory2llms`)

A memory store is not a scratch dump: it already has real structure — a type per entry
(`user`/`feedback`/`project`/`reference`), an index linking entries to files, explicit
recency tiers (`now` vs `today` vs `archive`), and dated entries the memory system itself
already compressed once. `notes-to-llms-txt` assumes none of that exists and re-derives
topic clusters from an unstructured pile; this skill assumes the opposite — the structure
is the input's main asset, and the job is to carry it into the llms.txt grammar without
flattening it away.

```
memory store ─▶ [1] identify shape ─▶ [2] ingest w/ provenance ─▶ [3] verify against reality
                                                                          │
                                          [5] report ◀─ [4] draft + compile, hand to /ldo
```

## When not to use

- Input is unstructured scratch notes or meeting dumps with no maintained typing/recency
  structure → `notes-to-llms-txt` (its segment→cluster pipeline is the right tool for mush;
  running it on a structured memory store would throw away metadata this skill keeps).
- Source is a repo's code or docs, not its memory files → `crawl-repo-to-llms`.
- An llms.txt family already exists for this memory store and just needs a fix → `/ldo`.

## Non-negotiables

1. **Never invent a fact the memory doesn't contain.** Every `llms-facts.txt` line traces to
   a specific memory file/entry. A memory that's vague or silent on something stays silent in
   the output — same rule every sibling llms.txt-family skill in this ecosystem uses.
2. **Never silently resolve a disagreement between memory and the live system.** This is the
   single most important behavior this skill adds beyond `notes-to-llms-txt`: memory files in
   this ecosystem have a documented history of drifting from reality (a recorded path, version,
   or file that moved/changed after the memory was written — the exact bug class
   `project-registrar` exists to catch for *projects*; this skill catches it for *memory
   entries themselves*). Step 3 below is not optional. A drifted entry gets exported with its
   claim intact AND a `## Drift flags` line noting what changed and when checked — never
   silently corrected, never silently dropped.
3. **Preserve type/provenance as facets, don't re-cluster them away.** A `feedback`-type memory
   and a `project`-type memory about the same subject are different KINDS of claim (a standing
   behavioral rule vs. a point-in-time fact) — keep that distinction visible in the compiled
   family rather than merging them into one undifferentiated topic entry.
4. **Redact secrets before any output file.** Memory files accumulate incidental credentials
   (a pasted API key in a troubleshooting note, a token in a command example) at least as
   often as scratch notes do. Same scan-and-redact-to-`[REDACTED]` rule as `notes-to-llms-txt`;
   report the count in Step 5.

## Inputs

- **memory-source** (required) — a path: a `MEMORY.md` file, a `.remember/` directory, a
  napmem pyramid file (`napmem_pyramid.json` + its memory files), or a directory containing
  several of these. Read every linked file the index points to — a `MEMORY.md` that's just an
  index of one-line pointers (per this ecosystem's own auto-memory convention: name/
  description/metadata.type frontmatter, body content in the linked file) is incomplete
  without following those links.
- **verify-against** (optional) — a filesystem root or MCP surface to check drift against
  (e.g. `hub_pm_get` for a project the memory references, or a plain path-exists check for a
  file/tool it names). Default: best-effort filesystem checks only, no MCP calls assumed.
- **budget-tokens** (optional, default 8000) — size of `llms-small.txt`.

## Step 1 — Identify the shape

Before ingesting, classify what kind of memory store this is — it changes how Step 2 reads it:

- **Claude Code auto-memory**: a `MEMORY.md` index (one-line-per-entry, `- [Title](file.md) —
  hook`) plus per-entry files carrying `name`/`description`/`metadata.type` frontmatter
  (`user`/`feedback`/`project`/`reference`) and `[[wikilink]]`-style cross-references. Follow
  every index line to its file; follow every `[[link]]` at least one hop to build the
  cross-reference graph even if the linked memory doesn't exist yet (a `[[name]]` with no
  matching file is a *marked gap*, not an error — say so, don't silently drop the link).
- **`.remember/` time-decay pyramid**: `now.md` (buffer) → `today-*.md` (daily) → `recent.md`
  (7-day rollup) → `archive.md` (old) → `core-memories.md` (key moments), each successive tier
  already a compression of the previous. Preserve the tier as a facet on every fact (a fact
  from `core-memories.md` is a different confidence/durability class than one from `now.md`
  that hasn't been rolled up yet) rather than treating all tiers as equally current.
- **napmem-style pyramid**: a JSON pyramid file (concept/topic tracks with record counts) plus
  a retrieval agent. Query it for track/topic listings rather than trying to hand-parse the
  JSON structure blind — use the store's own retrieval tool if one exists (e.g.
  `napmem_retrieval_agent.py --stats` / `--query`) so the export reflects what the store
  itself considers queryable, not a guess at its internal schema.
- **Ad-hoc project MEMORY.md**: hand-maintained, no formal frontmatter — treat like a
  `notes-to-llms-txt` input for structure-finding purposes, but still apply this skill's
  Step 3 drift check, since these are exactly the files most likely to go stale (see
  Non-negotiable 2's precedent).

## Step 2 — Ingest with provenance

Read every file in full, in every linked/cross-referenced file, not just the index. For each
kept unit, record: source file, type (from frontmatter or inferred shape), recency tier (if
applicable), and any embedded `[[links]]` or explicit dates. Do not sample truncate a memory
file to save time — a memory index is already a compression; truncating it further loses
exactly the content the memory system worked to preserve.

## Step 3 — Verify against reality

For every fact that names a concrete, checkable thing — a file path, a version number, a
command, a tool/MCP name, a repo location — do a best-effort check against `verify-against`
or the plain filesystem: does the path still exist? Does a version file still say what the
memory claims? This is the step `notes-to-llms-txt` has no equivalent of, because scratch
notes rarely make durable claims about system state the way a memory file's whole purpose is
to. A claim that can't be checked (no filesystem/MCP access to verify it) is exported as-is,
unflagged — only checked-and-contradicted claims get a drift flag, never "unknown, so
suspicious."

## Step 4 — Draft and compile

Draft per type/tier group (not by re-clustering into new topics unless the source memory has
no typing at all, per Step 1's ad-hoc-MEMORY.md case) — title, source-anchored facts, drift
flags inline where Step 3 found them. Compile `llms.txt` (index by type/tier), `llms-full.txt`,
`llms-small.txt` (budgeted), `llms-facts.txt` — same grammar every sibling skill in this
family uses (`~/.claude/skills/llms-deep-optimizer/references/attributes.md`). Hand the
compiled family to `/ldo`, same handoff `notes-to-llms-txt` makes — this skill's draft
produces structure-preserving *content*, `/ldo`'s audit is what verifies the *shape* actually
clears the bar.

## Step 5 — Report

Memory shape identified, entries/files ingested (and any `[[link]]`s that pointed nowhere),
drift flags found (count + one line each — what was claimed, what's actually true now, when
checked), secrets redacted (count, never values), files written, `/ldo`'s verdict. If the
export found zero drift, say so plainly — an all-clear is a real, useful result, not a
non-finding to omit.

## Trigger examples

**Should trigger:**
- "Export my Claude Code memory as an llms.txt I can query instead of reloading it all."
- "Turn the .remember pyramid for this project into a servable docset."
- "Build a queryable index of what napmem knows about this codebase."

**Should NOT trigger:**
- "Organize these scattered meeting notes" (no maintained memory structure) → `notes-to-llms-txt`.
- "Crawl this repo's docs and code" (not memory files) → `crawl-repo-to-llms`.
- "Audit this llms.txt, something looks broken" (family already exists) → `/ldo`.

## Routing detail

- After compiling, this family serves the same way any hub docset does — register it with
  `hub_index_docset` (or, for a topic-scoped slice, `docset_refine topical`) so
  `hub_query_docset`/`hub_llms_serve` can answer from it instead of an agent re-reading the
  raw memory files every session.
- New skill: not yet synced to the mdb-context-hub registry or the 559-skill master
  `skills/INDEX.md` / `catalog.json` (both auto-generated) — run
  `source-command-sync-skills` after this file is reviewed, per that skill's own charter
  ("Run after creating or updating skills").
