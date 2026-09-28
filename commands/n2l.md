---
description: Notes → LLMS — turn a disordered pile of notes, docs or exports into a spec-v2 llms.txt family (index, facts, optional full/small/vocabulary, manifest) that passes llms_lint.py at 0 High, with every fact carrying a resolvable source#anchor
argument-hint: notes dir, files, or pasted text [--project SLUG|--base-url URL|--subject "…"|--sections a,b,c|--no-llm|--publish]
---

Read `~/.claude/skills/notes-to-llms/SKILL.md` (or `skills/notes-to-llms/SKILL.md` in this
repo) and execute it against $ARGUMENTS, flags included. The SKILL.md is the single source
of truth; do not re-specify its steps here.

If $ARGUMENTS is empty, ask once for the notes directory, files or text, then continue.
