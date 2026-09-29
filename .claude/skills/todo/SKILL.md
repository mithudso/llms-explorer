---
name: todo
version: "1.1.0"
updated: "2026-09-27"
owner: mitch
description: >-
  Personal to-do list in one markdown file: add items by hand, mark them done, list what is open,
  and sync in tasks left lingering from sessions (unfinished TaskCreate items and open rows in
  memory-central *_actions_llms.md). Braindumps feed it automatically; it two-way syncs with the
  StickySites extension's to-do list and with peer boxes over SSH. TRIGGER: "/todo",
  "add to my to-do", "remind me to", "what's on my list", "what's left across my sessions",
  "mark X done". SKIP: in-session step tracking (use TaskCreate), repo issue trackers.
---

# To-do

One file: `~/dev/personal/Areas/todo/TODO.md` (local Obsidian vault, not in git; override with `PERSONAL_TODO`). Script: `~/.claude/skills/todo/scripts/todo.py`. Tests: `python3 ~/.claude/skills/todo/scripts/test_todo.py`.

Sections: **Manual** (added by hand), **From braindumps** (tasks `/braindump` found, with the raw path:line), **From sessions** (grouped by project), **Done**.

## Commands

```bash
T=~/.claude/skills/todo/scripts/todo.py
python3 $T add "Call the dentist"        # manual add
python3 $T list                           # open items with 8-char ids
python3 $T done 3fa9c2e1                  # or a unique substring of the text
python3 $T sync                           # pull lingering session tasks now
python3 $T sync --tiers 2,3 --since-days 120     # wider net (tier 3 = raw logs, noisier)
```

## Behavior

- `/todo <text>`: run `add` with the text (tighten to one imperative line, keep the user's meaning). Confirm with the id.
- `/todo` alone or "what's on my list": run `sync`, then `list`, and show the items grouped by section. Lead with Manual and braindump items; summarize session items per project as counts plus the top few unless the user asks for all.
- "mark X done": run `done`. If several match, show the candidates and ask which.

## How items get in automatically

- **SessionEnd hook** runs `todo.py hook-session-end`, which syncs:
  - unfinished TaskCreate items (`pending`/`in_progress`) from the session that just ended, and from any other session idle for 30+ minutes;
  - open or blocked rows from `~/.llms/*_actions_llms.md`, tier 2 only (agent memory; tier 1 is standing rules from instruction files), first seen within 60 days (memory-central rebuilds these nightly).
- **Braindumps** call `todo.add_item` for every task they find.

## StickySites and peer boxes

- **StickySites** (`~/dev/stickysites`, v1.11.0+) syncs its global To-do list with TODO.md through the native-messaging host `com.mitch.todo_bridge`: on browser start, every 2 minutes, and 3 seconds after an edit. Session items show up in collapsed `Sessions · <project>` sections, braindump tasks in `From braindumps`. Encrypted lists are skipped (the file is plaintext).
  - Set up on a box: load StickySites unpacked from `~/dev/stickysites`, then run `python3 ~/.claude/skills/todo/scripts/todo.py install-native-host` and reload the extension.
- **Peers**: `todo.py peer-sync` merges TODO.md with each SSH target listed in `~/dev/personal/Areas/todo/.peers` (needs this skill on the peer). One box running peer-sync is enough.
- **Schedule**: `todo.py install-launchd` loads `com.mitch.todo-sync`, which runs `sync` then `peer-sync` every 5 minutes. Log: `~/dev/personal/Areas/todo/.todo-sync.log`.
- **Merge**: three-way against the last snapshot per replica (`.todo-sync-state.json`). A deletion on one side wins unless the other side edited the item since; a tick on either side wins; on a text conflict the local file wins.

## Rules

- Ticking a box in Obsidian is enough; the next write moves it to Done with a date.
- Deleting a line dismisses it permanently: its id stays in `.todo-seen.json`, so sync will not re-add it.
- Typing `- [ ] something` anywhere in the file by hand works: the next write adopts it and gives it an id.
- Hand edits to item text are kept, but anything that is not a checkbox line (free notes) is dropped on the next write. Put notes in a separate file.
- Never add work-customer confidential detail beyond what the source row already says.
