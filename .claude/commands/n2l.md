---
description: Turn notes, documents or exports into a source-anchored llms family. Follow the skill's current format authority,
  preserve provenance and run the final lint gate. Stage-specific flags belong to the command that declares them.
argument-hint: notes dir, files, or pasted text [--project SLUG] [--base-url URL] [--subject TEXT] [--no-units] [--no-embed]
model: claude-opus-5-5
effort: high
---

Read `.claude/skills/notes-to-llms/SKILL.md` from the current repository first. Outside this repository, resolve the installed `notes-to-llms` source or its owning hub, and verify that its flags match the requested invocation. If no source is available, report the missing dependency instead of guessing. Execute the selected source against $ARGUMENTS; its instructions and flag catalog govern the run.

If $ARGUMENTS is empty, ask once for the notes directory, files or text, then continue.
