---
title: "todo"
description: "One markdown to-do list that fills itself: add items by hand, tick them off, and let it pull in the tasks your agent sessions and braindumps left behind — every row cited to where it came from."
order: 0
tags: [capture, todo, personal-memory]
aliasCommand: "/todo"
---

Every agent session leaves tasks on the floor: the `TaskCreate` items that were still
pending when the window closed, the "next step" rows an agent wrote into memory and nobody
read again. `todo` is one plain `TODO.md` that collects them. Add an item by hand with
`/todo call the dentist`; ask `/todo` alone and it syncs first, then lists what is open,
grouped by where each item came from.

## What it does

- **Add, list, done** — three commands over one file, each item with an eight-character id
  you can tick by id or by any unique substring of its text.
- **Sync in lingering work** — unfinished task-list items from ended sessions and open rows
  in the memory-central `*_actions_llms.md` files, so the list is the union of every
  session's leftovers, not one session's memory.
- **Braindumps feed it** — every task [braindump](/skills/braindump/) finds lands here,
  with the raw `path:line` it was parsed from.
- **Hand edits win** — ticking a box in Obsidian, deleting a line, or typing a new
  `- [ ]` by hand is all the sync understands. Deleted lines stay deleted.
- **Two-way sync** — with the StickySites browser extension's to-do list through a native
  messaging host, and with peer machines over SSH, three-way merged against the last snapshot.

## Sections

`TODO.md` holds four sections: **Manual**, **From braindumps**, **From sessions** (one group
per project), and **Done**, where ticked items move with the date they were closed.

**Use it for:** "add to my to-do", "what's left across my sessions", "remind me to",
"mark X done".
