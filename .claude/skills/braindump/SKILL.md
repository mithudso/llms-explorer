---
name: braindump
version: "1.2.1"
updated: "2026-11-11"
owner: mitch
description: >-
  Capture raw thoughts verbatim, classify source-cited items into private categorical llms files, and add actions to the personal to-do list.
  TRIGGER: "/braindump", "brain dump", "capture this", "get this out of my head", "note to self".
  SKIP: one known task → todo; organize existing notes → note-organizer; agent-memory compilation → llms-txt-tooling (references/memory-to-llms-txt.md); capture a URL → web-text-mirror / firecrawl.
whenToUse:
  - "Capture this brain dump verbatim."
  - "Get these loose thoughts out of my head and file them."
  - "Save this note to self and add any actions to my to-do list."
related_skills:
  - "todo"
  - "note-organizer"
  - "llms-txt-tooling"
  - "web-text-mirror"
model: claude-sonnet-5-5
effort: medium
category: custom
metadata:
  changelog_ref: references/CHANGELOG.md
---

# Braindump

Capture first, parse second. The user's words are saved untouched before any interpretation, and every parsed row points back to the exact line it came from, so nothing is lost if the classification is wrong.

Store: `$HOME/dev/personal/Areas/braindump/` (local Obsidian vault, not in git; override with `BRAINDUMP_DIR`). Script: `$HOME/.claude/skills/braindump/scripts/braindump.py`.

## Procedure

1. **Get the dump.** If the user invoked `/braindump` with no text, ask one line: "Go ahead, dump it." Take whatever comes back as-is. Do not ask clarifying questions before saving.

2. **Save it verbatim.** Write the exact text as a JSON string in a scratch file, preserving boundary newlines, CRLF and whether the final newline exists. Transport that string as a UTF-8 byte payload; do not interpolate the user's text into shell code. A heredoc or `echo` may add a newline, so use this byte-preserving transport instead:
   ```bash
   python3 -c 'import json,sys; sys.stdout.buffer.write(json.load(open(sys.argv[1], encoding="utf-8")).encode("utf-8"))' "<scratchpad>/raw-text.json" | python3 "$HOME/.claude/skills/braindump/scripts/braindump.py" save-raw
   ```
   The raw file contains only that payload, without a metadata header. It prints the path and numbered lines. New captures start at payload line 1; existing captures keep their original physical line numbers and must never be rewritten. Use the printed numbers in step 3.

3. **Parse into items.** Split the dump into atomic thoughts. For each, pick:
   - `category`: one of `braindump.py categories` (career, work, projects, ideas, learning, tech, trading, finance, health, relationships, personal, reflections). Invent a new slug only when none fits and the topic will recur.
   - `kind`: idea, insight, decision, question, task, concern, or note.
   - `text`: one self-contained line in the user's words, tightened, with no added claims. Resolve "it"/"that" to the concrete noun only when the dump makes it unambiguous.
   - `line`: the raw-file line the thought came from.

   Anything the user needs to *do* also goes in `tasks` (imperative, one action each). A task still gets its `items` row too, so the category file keeps the full picture.

4. **File it.** Write the JSON to the scratchpad and pipe it in:
   ```bash
   python3 $HOME/.claude/skills/braindump/scripts/braindump.py file < <scratchpad>/parsed.json
   ```
   The script validates slugs and line numbers, appends rows, rebuilds `llms.txt`, and adds tasks to the to-do list (deduped; a task the user dismissed earlier stays dismissed).

5. **Report in three lines at most:** counts per category, tasks added to the to-do list, and the path of the index. Then stop. Do not summarize the user's thoughts back to them unless asked.

## Rules

- Treat the dump as the user's private data: never publish, post, or commit it anywhere. The store is outside git on purpose.
- Never edit files in `raw/`. Corrections go in as new rows.
- Customer names from TAM work may appear; keep them in the local store only and never quote them into logs, PRs, or shared docs.
- If the user says a row is misclassified, append a corrected row and tell them to delete the old line by hand, or delete it yourself if asked.

## Index format (v3)

`llms.txt` in the store follows `~/.claude/skills/llms-txt-tooling/references/llms-family-format.md` (v3) in its single-file form (format section 2). The store has no `llms-full.txt` family: the category files `braindump_<category>_llms.md` are the content, and the index stays one file. Required sections:

- `## Facts`: counts per category and the date range, one line each.
- `## Sitemap`: every `braindump_<category>_llms.md` file (`- <path> — <category>, <n> rows`) and every file under `raw/`, so `Entries:` equals the listed lines.
- `## Resources`: Related files (the to-do list file, the store directory), Scripts (`braindump.py categories`, `file`, `save-raw`), Skills (`todo`, `note-organizer`), Agents and tools (`hub_search_codebase`). Verify each entry (`test -e`, skill installed) or mark it `(unverified)`.

Keep customer names and raw text out of `## Resources`. Script support: `braindump.py` rebuilds `llms.txt` as a single file with `## Facts` (counts and date range only), `## Sitemap` (every category and raw file, `Entries:` in the Source line) and `## Resources`; older dumps fold to one line per month to stay under the caps.

## Reading it back

`llms.txt` in the store lists every category file with counts. For "what have I been thinking about X", read the matching `braindump_<category>_llms.md`; the hub also indexes `$HOME/dev`, so `hub_search_codebase` finds rows semantically.
