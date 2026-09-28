---
name: braindump
version: "1.0.0"
updated: "2026-09-27"
owner: mitch
description: >-
  Quick capture of raw thoughts: saves the dump verbatim, parses it into categorical llms files
  (braindump_<category>_llms.md with an llms.txt index, every row cited to raw path:line), and
  pushes any tasks found into the personal to-do list. TRIGGER: "/braindump", "braindump",
  "brain dump", "capture this", "get this out of my head", "note to self", a stream of loose
  thoughts the user wants kept. SKIP: repo/agent memory (memory-central, auto-memory), adding a
  single known task (use /todo), URL capture (web-text-mirror / firecrawl).
---

# Braindump

Capture first, parse second. The user's words are saved untouched before any interpretation, and every parsed row points back to the exact line it came from, so nothing is lost if the classification is wrong.

Store: `~/dev/personal/Areas/braindump/` (local Obsidian vault, not in git; override with `BRAINDUMP_DIR`). Script: `~/.claude/skills/braindump/scripts/braindump.py`.

## Procedure

1. **Get the dump.** If the user invoked `/braindump` with no text, ask one line: "Go ahead, dump it." Take whatever comes back as-is. Do not ask clarifying questions before saving.

2. **Save it verbatim.** Pipe the exact text through a quoted heredoc so nothing is expanded:
   ```bash
   python3 ~/.claude/skills/braindump/scripts/braindump.py save-raw <<'DUMP'
   <user's text, unchanged>
   DUMP
   ```
   It prints the raw file path, then the file with line numbers. Use those numbers in step 3.

3. **Parse into items.** Split the dump into atomic thoughts. For each, pick:
   - `category`: one of `braindump.py categories` (career, work, projects, ideas, learning, tech, trading, finance, health, relationships, personal, reflections). Invent a new slug only when none fits and the topic will recur.
   - `kind`: idea, insight, decision, question, task, concern, or note.
   - `text`: one self-contained line in the user's words, tightened, with no added claims. Resolve "it"/"that" to the concrete noun only when the dump makes it unambiguous.
   - `line`: the raw-file line the thought came from.

   Anything the user needs to *do* also goes in `tasks` (imperative, one action each). A task still gets its `items` row too, so the category file keeps the full picture.

4. **File it.** Write the JSON to the scratchpad and pipe it in:
   ```bash
   python3 ~/.claude/skills/braindump/scripts/braindump.py file < <scratchpad>/parsed.json
   ```
   The script validates slugs and line numbers, appends rows, rebuilds `llms.txt`, and adds tasks to the to-do list (deduped; a task the user dismissed earlier stays dismissed).

5. **Report in three lines at most:** counts per category, tasks added to the to-do list, and the path of the index. Then stop. Do not summarize the user's thoughts back to them unless asked.

## Rules

- Treat the dump as the user's private data: never publish, post, or commit it anywhere. The store is outside git on purpose.
- Never edit files in `raw/`. Corrections go in as new rows.
- Customer names from TAM work may appear; keep them in the local store only and never quote them into logs, PRs, or shared docs.
- If the user says a row is misclassified, append a corrected row and tell them to delete the old line by hand, or delete it yourself if asked.

## Reading it back

`llms.txt` in the store lists every category file with counts. For "what have I been thinking about X", read the matching `braindump_<category>_llms.md`; the hub also indexes `~/dev`, so `hub_search_codebase` finds rows semantically.

## Placement (mandatory last step)

Every run that writes an llms family ends here, so the map of what was written lands where an agent looks first and the files stay in query-first order:

- Run `python3 ~/.global-ai-hub/scripts/llms_routing.py install <project-dir> --from <output-dir>` (in the llms-explorer checkout: `hub/scripts/llms_routing.py`). It writes the `## llms routing` block — routing table, quick answers, indexes — between `<!-- llms-routing:start -->` / `<!-- llms-routing:end -->` in `CLAUDE.md` (else `AGENTS.md`; both → block in `CLAUDE.md`, pointer in `AGENTS.md`; neither → a minimal `CLAUDE.md`). Idempotent; re-run after every regeneration. Outside any project directory it prints `skipped placement: no project directory`.
- Run `python3 ~/.global-ai-hub/scripts/llms_routing.py reorder <output-dir>/llms.txt`: inside each H2 section the entries whose target file the access ledger (`llms_ledger.py rank`) has seen go first, most read first; the rest keep their authored order. Sections, `llms-small.txt` and `llms-full.txt` are never reordered. With no ledger data it says `ordering: role order (no ledger data)`.
- Placement rule: defaults, file roles, formulas and commands are quick answers in `CLAUDE.md`/`AGENTS.md` (cached, cited, data not rules); everything else stays in the llms files, which remain the source of truth.
