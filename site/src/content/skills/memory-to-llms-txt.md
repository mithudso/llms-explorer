---
title: "memory-to-llms-txt"
description: "Turns an agent's persistent memory store — Claude Code auto-memory, a .remember/ time-decay pyramid, a napmem-style pyramid, or an ad-hoc project MEMORY.md — into a well-formed llms.txt family, preserving type/recency structure as facets and flagging entries that have drifted from reality."
order: 18
tags: [llms, memory, structuring, drift-detection]
aliasCommand: "/memory2llms"
---

A memory store isn't a scratch dump — it already has real structure: a type per entry
(user/feedback/project/reference), an index linking entries to files, explicit recency
tiers (`now` vs `today` vs `archive`), dated entries the memory system itself already
compressed once. [notes-to-llms-txt](/skills/notes-to-llms-txt/) assumes none of that
exists and re-derives topic clusters from an unstructured pile; `memory-to-llms-txt`
assumes the opposite — the structure *is* the input's main asset, and the job is carrying
it into the llms.txt grammar without flattening it away.

## How it works

1. **Identify the shape** — Claude Code auto-memory (`MEMORY.md` index + frontmatter'd
   entry files), a `.remember/` pyramid (`now.md` → `today-*.md` → `recent.md` →
   `archive.md` → `core-memories.md`), a napmem-style pyramid queried through its own
   retrieval tool, or an ad-hoc project `MEMORY.md` with no formal typing.
2. **Ingest with provenance** — every linked/cross-referenced file, not just the index;
   record source, type, recency tier, and any `[[wikilinks]]` per unit.
3. **Verify against reality** — the step this skill has that
   [notes-to-llms-txt](/skills/notes-to-llms-txt/) doesn't need: for every fact naming a
   checkable thing (a path, a version, a command), a best-effort check against the live
   system. A memory is a durable claim about system state in a way a scratch note rarely
   is, and durable claims go stale — a path that moved, a version that shipped since the
   note was written.
4. **Draft by type/tier**, not by re-clustering into new topics — a `feedback`-type entry
   and a `project`-type entry about the same subject are different *kinds* of claim (a
   standing rule vs. a point-in-time fact), and collapsing that distinction away loses
   real information.
5. **Compile and hand off** to [llms-deep-optimizer](/skills/llms-deep-optimizer/) for the
   multi-pass audit, same handoff `notes-to-llms-txt` makes.

A drifted entry is never silently corrected or dropped — it's exported with its original
claim intact plus a `## Drift flags` line naming what changed and when it was checked.
Same redaction discipline as its sibling: anything secret-shaped is scrubbed to
`[REDACTED]` before any output file, since a memory export is exactly the kind of thing
that ends up queryable by more than just its author later.

**Use it for:** "make MEMORY.md queryable", "export the .remember pyramid as llms.txt",
"build a servable index of what this agent remembers".

**Not for:** unstructured scratch notes or meeting dumps with no maintained typing
([notes-to-llms-txt](/skills/notes-to-llms-txt/)) · a repo's code or docs rather than its
memory files ([crawl-repo-to-llms](/skills/crawl-repo-to-llms/)) · an llms.txt family that
already exists and just needs a pass
([llms-deep-optimizer](/skills/llms-deep-optimizer/)).
