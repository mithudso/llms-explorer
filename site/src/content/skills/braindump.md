---
title: "braindump"
description: "Capture a stream of loose thoughts verbatim, then break it into categorised llms files an agent can load — ideas, facts, questions, decisions — with every task pushed to your to-do list and every row cited back to the raw line."
order: 0
tags: [capture, notes, personal-memory, llms]
aliasCommand: "/braindump"
---

Say what is in your head and nothing else. `braindump` saves the text untouched first —
before any interpretation — and only then parses it. Each parsed row points back to the exact
line of the raw dump it came from, so a wrong classification loses nothing: the original is
one hop away.

## What it does

- **Capture first, parse second** — the raw dump is written to disk verbatim before a single
  word is classified.
- **Categorised llms files** — the dump is split into `braindump_<category>_llms.md` files
  (ideas, facts, questions, decisions, tasks, people, references) with an `llms.txt` index
  over them, so an agent loads only the category it needs.
- **Tasks go to the to-do list** — every actionable line is pushed to
  [todo](/skills/todo/) with its `path:line`, so nothing said in passing is lost.
- **Meeting notes and voice memos** — the same pipeline turns a page of meeting notes into
  files that are usable as context the next time the subject comes up.
- **Cited rows** — every line in every generated file ends with the raw path and line number
  it was parsed from, the same convention memory-central uses.

Braindumps accumulate into a personal corpus: the categorised files are the long-term memory
a future session loads, and the `llms.txt` index is how it finds the right one.

**Use it for:** "braindump", "capture this", "get this out of my head", "note to self", a
stream of loose thoughts you want kept.
