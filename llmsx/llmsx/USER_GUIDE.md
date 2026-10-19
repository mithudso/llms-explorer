# LLMSX Explorer — User Guide

LLMSX Explorer (`llmsx explorer`) is a terminal workbench for the llms-explorer concept
tree. Use it to browse concepts, read their facts and llms files, save useful lines to a
scratchpad, mark concepts for research, run research jobs, and commit the results.

This guide ships inside the `llmsx` package. Open it three ways:

- In the app: press `g`, or press `?` and choose **User guide**.
- In a terminal: `llmsx explorer --guide`.
- On the web: https://llms-explorer.com/explorer/guide/

## Contents

1. [Install and launch](#1-install-and-launch)
2. [The screen](#2-the-screen)
3. [Moving around](#3-moving-around)
4. [Reading a concept](#4-reading-a-concept)
5. [The llms colour scheme](#5-the-llms-colour-scheme)
6. [The scratchpad](#6-the-scratchpad)
7. [Marks, tags, links and notes](#7-marks-tags-links-and-notes)
8. [Finding unresearched concepts](#8-finding-unresearched-concepts)
9. [Research jobs and the queue](#9-research-jobs-and-the-queue)
10. [Providers and settings](#10-providers-and-settings)
11. [Library, skills, imports and capture](#11-library-skills-imports-and-capture)
12. [Learning: flashcards and quizzes](#12-learning-flashcards-and-quizzes)
13. [Bundles and exports](#13-bundles-and-exports)
14. [Sync and commit](#14-sync-and-commit)
15. [Where your data lives](#15-where-your-data-lives)
16. [Key reference](#16-key-reference)
17. [Troubleshooting](#17-troubleshooting)

## 1. Install and launch

You need Python 3.11 or newer.

```bash
python -m pip install 'llmsx[tui]'        # or the wheel from https://llms-explorer.com/downloads/#llmsx
llmsx explorer                             # inside a checkout, or clones one on first run
```

`llmsx explorer` looks for a checkout that contains `concept-tree/tree.json`, starting at
the current directory. If it finds none, it clones the repository into
`~/.llmsx/llms-explorer` and opens that.

| Option | Effect |
|---|---|
| `--repo PATH` | Open this checkout instead of searching. |
| `--no-sync` | Skip the `git pull --ff-only` on start. |
| `--guide` | Print this guide and exit. |

Browsing needs no account, no token and no network after the first clone. The explorer
sends no telemetry.

## 2. The screen

```
┌ filter / search ──────────┐ ┌ quick-action buttons ─────────────────────────┐
│ concept tree              │ │ Overview  Facts  Skill  Highlights  llms.txt …│
│ ▼ Root domain ●           │ │                                               │
│   ▶ Concept ● [marked]    │ │  the selected tab                             │
│     Frontier  (frontier)  │ │                                               │
└───────────────────────────┘ └───────────────────────────────────────────────┘
 status line
 footer: the most-used keys
```

- **Left: the outline.** The concept tree, collapsible. Researched concepts are plain text.
  Frontier concepts (named in the tree, never researched) are dim italic with
  `(frontier)`. A cyan `●` means the concept has a concept pack or a hub `.llms`
  directory. Yellow `[needs-review]` or `[further-research]` shows a mark; `#tag` shows tags;
  `queued` means a research-queue row exists.
- **Right: the detail tabs.** The tabs for the selected concept. Selecting a concept never
  opens a new screen; the tabs update in place.
- **The button row** above the tabs: ⚡ /dr, + Queue, 🐇 Rabbithole, 🧭 Family, 📚 Batch,
  🚀 Auto, 📋 Queue, 🔖 Highlight, 🤖 provider, ❓ Help, 📌 Save line and 📝 Scratchpad. The
  row scrolls sideways when the window is narrow.
- **The status line** reports counts and the result of the last action.

## 3. Moving around

| Key | Does |
|---|---|
| `↑` `↓` | In the outline, move the cursor. Elsewhere, move focus to the widget directly above or below. |
| `→` `←` | Expand or collapse the concept under the cursor. `→` on an open or leaf node moves focus to the tabs; `←` on a root moves focus to the filter. |
| `/` | Focus the filter box. Typing filters the outline by name and alias. |
| `⌘F` or `ctrl+f` | Search: type, press Enter to jump to the first match, Enter again for the next. |
| `[` `]` | Previous or next detail tab. |
| `T` | Cycle the outline filter: all, frontier, researched, tagged. |
| `r` | Reload the tree and local state from disk. |
| `Tab` / `shift+Tab` | Move focus in reading order. |
| `q` | Quit. |

**The down-arrow rule.** A widget that uses the arrow keys keeps them: the outline, the
llms line views, lists, tables, text areas and dropdown menus. On every other widget (the
filter box, a button, the tab bar, a field in a dialog), `↓` moves focus to the widget
directly below and `↑` to the widget directly above. For example, `↓` in the filter box
goes to the outline, and `↓` on a button goes to the tab bar.

## 4. Reading a concept

Select a concept with the cursor or a click. The explorer opens its **facts** first:

1. the **Facts** tab, when the concept has a concept pack;
2. otherwise the **llms-facts.txt** tab, when the hub has an `.llms` directory for it;
3. otherwise the **Facts** tab, which says no facts exist yet.

Re-rendering the same concept (after a mark, a reload or an edit) keeps the tab you are on.

| Tab | Shows |
|---|---|
| **Overview** | Summary, parent, children, skill, mark, tags, linked concepts (clickable), highlights and your local notes. |
| **Facts** | The concept pack: a one-line header (slug, parent, research date, sources, skill, mark, tags), the summary, and each facet's facts with a source link. |
| **Skill** | The concept's `SKILL.md` or reference file, when it names a skill. |
| **ref: …** | One tab per reference file of that skill. |
| **Highlights** | Snippets you saved for this concept with `h`. |
| **llms.txt, llms-full.txt, llms-small.txt, llms-facts.txt, llms-vocabulary.txt** | The hub's llms family for the concept, from `~/.global-ai-hub/llms-concepts/<slug>.llms/` or `$LLMSX_CONCEPTS_PATH`. |

A tab's file is read only when you first open that tab. Files over 200 KB are cut for
display; the file on disk stays complete. Everything shown is treated as untrusted text:
nothing in a file is executed, and markup in a file is drawn literally.

Press `e` to open the current tab's file in `$EDITOR`. Press `E` to edit the concept's
summary, aliases, children, links and tags.

## 5. The llms colour scheme

The llms tabs show the file one numbered line per row, coloured by the llms format, with a
cursor you move with `↑` `↓` `PgUp` `PgDn`.

| Part | Example | Colour |
|---|---|---|
| Title | `# Indexing` | bold magenta |
| Section | `## Facets` | bold cyan |
| Sub-section | `### Notes` | bold blue |
| Summary quote | `> An index is …` | italic green |
| List marker | `- ` `1. ` | bold yellow |
| Link name / URL | `[Doc](https://…)` | bold / underlined blue |
| Bare URL | `https://example.com` | underlined blue |
| Inline code | `` `createIndex` `` | orange |
| Source and generator tags | `[src: notes]` `[gen: p/1.1.0]` | dim cyan |
| Citation tail | `— path/file.md:12 (as of 2026-10-01)` | dim |
| Date | `2026-10-13` | green |
| Search-hit prefix | `L123:` | dim |
| Warning words | `STALE:` `Misbelief:` `TODO` `never` `must` | bold red |
| Labels | `Note:` `Default:` `Optional` `Why:` | bold yellow |
| Rules and comments | `---` `<!-- … -->` | dim |

## 6. The scratchpad

The scratchpad is one global notes file, `~/.llmsx/scratchpad.md`, shared by every
concept. Use it to collect URLs and facts while you look things up, then turn the
collection into a list.

**Save a line.**

1. Open the tab that holds the line.
2. On an llms tab, move the cursor to the line. On any other tab, skip this step.
3. Press `y`, or click **📌 Save line**.
   - On an llms tab, the cursor line is saved at once.
   - On any other tab, a picker opens with that tab's lines. Type to filter, move to a
     line, press Enter to save it. The picker stays open so you can save more; press
     `esc` to close it.

Each saved line becomes one bullet with its source:

```
- https://www.mongodb.com/docs/manual/indexes/ — Indexing · /Users/you/.global-ai-hub/llms-concepts/indexing.llms/llms.txt:42 (as of 2026-10-13)
```

A leading list marker on the line is dropped. A line whose text is already in the
scratchpad is not saved twice; the status line says so.

**Open, edit and compile.** Press `p`, or click **📝 Scratchpad**. The editor shows the
whole file. Reorder, delete or rewrite lines, then press `ctrl+s` to save. Press `ctrl+y`
(or **Copy all**) to copy the whole scratchpad to the clipboard. `esc` closes without
saving.

The scratchpad is local only. It is never committed.

## 7. Marks, tags, links and notes

| Key | Does | Writes |
|---|---|---|
| `m` | Mark the concept `needs-review`. | `concept-tree/marks.json` |
| `f` | Mark the concept `further-research`, pick a research mode, and add a queue row. | `marks.json`, `concept-tree/RESEARCH_QUEUE.md` |
| `x` | Clear the mark (tags stay). | `marks.json` |
| `t` | Edit the concept's tags (comma separated). Frontier concepts take tags too. | `marks.json` |
| `l` | Link the concept to another concept; links appear in the Overview. | `relatedConcepts` in `tree.json` |
| `n` | Edit your private notes for the concept; `ctrl+s` saves. | `~/.llmsx/notes/<slug>.md` |
| `h` | Save a highlight (a quote plus an optional note). | `~/.llmsx/highlights.json` |
| `H` | Open the highlights manager: Enter jumps to the concept, `c` copies, `d` deletes. | `highlights.json` |
| `N` | Add a local root to the outline. | `~/.llmsx/local-tree.json` |
| `M` | Move the concept under another node or a local root (local view only). | `~/.llmsx/local-tree.json` |

Every write to the repository asks for confirmation first, or goes through a dialog.

## 8. Finding unresearched concepts

A concept has **facts** when its concept pack holds at least one fact, or when its hub
`.llms` directory holds `llms-facts.txt`. Many concepts in the tree have neither: the tree
knows their family, but nobody has researched them.

Press `U` (shift+u) to mark them all:

1. The explorer counts every concept, researched or frontier, with no facts.
2. A dialog shows the count. Choose **Yes** to continue.
3. Each such concept gets the `further-research` mark with the note
   `no facts file: follow-up research`. A concept that already has a mark keeps it.
4. Each such concept that is not already queued gets a row in `RESEARCH_QUEUE.md`.

Running `U` again changes nothing until new concepts appear. Press `T` until the filter
reads `frontier` to see the unresearched edge of the tree, and press `c` to commit the
marks.

## 9. Research jobs and the queue

| Key or button | Does |
|---|---|
| **⚡ /dr** | Start deep research (`/dr`) on the selected concept now. |
| **+ Queue** | Add the concept to `RESEARCH_QUEUE.md` without running anything. |
| **🐇 Rabbithole** | Research the concept depth-first (`deep` mode). |
| **🧭 Family** | Map the concept's family with concept-family-explorer. |
| `R` | Open the research dialog: choose a mode (`dr`, `family`, `deep`, `crawl`, `full`, `queue`) and a provider. Enter submits. |
| **📚 Batch** / `ctrl+b` | Research several concepts in one run. |
| **🚀 Auto** / `a` | Autopilot: research frontier concepts one after another; when none remain, expand the most-used concept's family. Press again to stop. |
| `P` | Prefill the queue: group every frontier concept into clusters of up to 8 related concepts. |
| **📋 Queue** / `u` | Open the queue viewer. |
| `o` | Open the live job log. |

One job runs at a time. A job runs in the background and the explorer stays usable. The
job log streams every event; `esc` hides it and the job keeps running; `x` cancels;
`y` copies the log. Raw logs are kept under `~/.llmsx/jobs/`.

Before a job touches the tree, the explorer snapshots `tree.json`. After the job it
validates the tree. If the job fails, times out or is cancelled, the snapshot is restored.
`LLMSX_RESEARCH_TIMEOUT` (seconds, default 3600) caps one job.

**Queue viewer keys:** `r` run the selected row, `c` run the next cluster, `P` prefill
clusters, `a` add a concept, `x` cancel the job, `o` job log, `R` refresh, `esc` back.

**Research monitor.** The queue viewer also shows every run that holds concepts on the
research machine. That covers `/dr` runs, explorer frontier batches, research suite runs
(paused ones too) and runs started from the website. For each run it shows how many of its
concepts are finished and which ones are still checked out. A checked-out concept is
already being researched, so the website offers no research button for it. The monitor
refreshes every 30 seconds and on `R`. It reads
`https://api.llms-explorer.com/api/research/queue`, the same data as
https://llms-explorer.com/queue/. Set `LLMSX_API_URL` to read another API.

Without the provider's command-line tool installed, only `queue` is offered.

## 10. Providers and settings

Press `,` or click the **🤖 provider** button to open Settings.

- **Provider:** Anthropic Claude, Google (Gemini / AGY), OpenAI Codex, GitHub Copilot,
  Ollama (Local), or eGPU. Each provider runs through its own command-line tool.
- **Model:** an optional model override per provider.
- **API keys:** stored in `~/.llmsx/config.json` with `0600` permissions, masked on screen,
  never committed. A key in the environment (for example `ANTHROPIC_API_KEY`) also works.
  A stored key overrides a working command-line login; clear it if you see 401 errors.
- **Test Provider:** checks that the tool is installed and the credentials work.
- **Repository:** `repo_url`, `push_url` and the GitHub token used by `c`.
- **Windows…:** show or hide the outline, the detail pane, the status line, the footer,
  and the Facts, Skill, reference and llms tabs.

## 11. Library, skills, imports and capture

| Key | Opens |
|---|---|
| `L` | **Library:** the site's directory of scored llms-full files, blog posts, skills, and your imports, each with a preview. `b` bundles the row's file; `d` removes an import. |
| `S` | **Skills:** run any supported skill on a target: /dr, rabbithole, concept-family-explorer, full-suite, /lca, crawl-to-llms-txt, crawl-repo-to-llms, notes-to-llms-txt, memory-to-llms-txt and the deep optimizers. |
| `I` | **Import:** copy an llms file from a local path or an https URL into `~/.llmsx/imports/`. |
| `G` | **Ledger:** the llms access-ledger report by file, kind, project or surface. |
| `W` | **Braindump:** free capture. `ctrl+s` saves the dump verbatim; `ctrl+p` parses it with the braindump skill. |
| `J` | **Journal:** dated entries. `ctrl+n` jumps to today; `ctrl+s` saves; `ctrl+p` turns the journal into an llms family. |

## 12. Learning: flashcards and quizzes

- `F` opens **flashcards** over the selected branch. `space` flips a card; `1` means you
  knew it, `2` means show it again. Cards move through five Leitner boxes, saved in
  `~/.llmsx/flashcards.json`.
- `Q` opens a **multiple-choice quiz** built from the facts in the selected branch.

## 13. Bundles and exports

A **bundle** is a list of files to hand to an agent.

- `b` adds or removes the current tab's file. A bundled tab shows `✓` in its title.
- `B` opens the bundle: name it and export `bundle.md` (an ordered list an agent can read)
  and `bundle.json` into `~/.llmsx/bundles/<name>/`. `bundle.md` is also copied to the
  clipboard.

`X` exports the concept, its whole branch, the current file, or the bundle as markdown
into `~/.llmsx/exports/`.

## 14. Sync and commit

- `s` runs `git pull --ff-only`. The explorer also syncs on start unless you pass `--no-sync`.
- `c` shows the diff and asks before it commits and pushes. A commit stages only three
  files: `concept-tree/tree.json`, `concept-tree/marks.json` and
  `concept-tree/RESEARCH_QUEUE.md`. It never forces and never rewrites history.

The GitHub token comes from `$LLMSX_GITHUB_TOKEN` or Settings. It reaches git only
through a temporary `GIT_ASKPASS` helper, never through a URL, `.git/config` or a
committed file.

## 15. Where your data lives

`$LLMSX_HOME` defaults to `~/.llmsx`.

| Path | Holds | Committed? |
|---|---|---|
| `concept-tree/tree.json` | The concept tree. | yes (by `c`) |
| `concept-tree/marks.json` | Marks and tags. | yes (by `c`) |
| `concept-tree/RESEARCH_QUEUE.md` | The research queue. | yes (by `c`) |
| `~/.llmsx/scratchpad.md` | The scratchpad. | no |
| `~/.llmsx/notes/<slug>.md` | Notes per concept. | no |
| `~/.llmsx/highlights.json` | Highlights. | no |
| `~/.llmsx/config.json` | Settings and keys (`0600`). | no |
| `~/.llmsx/local-tree.json` | Local roots and moves. | no |
| `~/.llmsx/bundles/`, `exports/`, `imports/` | Bundles, exports, imported llms files. | no |
| `~/.llmsx/braindumps/`, `journal/` | Capture. | no |
| `~/.llmsx/flashcards.json` | Flashcard boxes. | no |
| `~/.llmsx/jobs/` | Raw job logs. | no |
| `~/.llmsx/explorer.log` | Warnings and errors. | no |

| Variable | Effect |
|---|---|
| `LLMSX_HOME` | Where local data lives. |
| `LLMSX_CONCEPTS_PATH` | Where hub `.llms` directories live (default `~/.global-ai-hub/llms-concepts`). |
| `LLMSX_GITHUB_TOKEN` | Token for push and `ls-remote`. |
| `LLMSX_RESEARCH_TIMEOUT` | Seconds one job may run (default 3600). |
| `LLMSX_API_URL` | API the queue viewer's research monitor reads (default `https://api.llms-explorer.com`). |
| `EDITOR` / `VISUAL` | Editor for `e` and `E`. |

## 16. Key reference

**Main screen**

| Key | Action | Key | Action |
|---|---|---|---|
| `↑` `↓` | move / focus above, below | `→` `←` | expand / collapse |
| `/` | filter | `⌘F` `ctrl+f` | search |
| `[` `]` | previous / next tab | `T` | cycle filter |
| `r` | reload | `q` | quit |
| `y` | save line to scratchpad | `p` | open scratchpad |
| `m` | mark needs-review | `f` | mark further-research |
| `x` | clear mark | `U` | mark every no-facts concept |
| `t` | tags | `l` | link |
| `n` | notes | `e` | open file in `$EDITOR` |
| `E` | edit node | `h` / `H` | highlight / highlights manager |
| `R` | research dialog | `a` | autopilot |
| `ctrl+b` | batch research | `P` | prefill queue clusters |
| `u` | queue viewer | `o` | job log |
| `b` / `B` | bundle toggle / bundle | `X` | export |
| `L` | library | `S` | skills |
| `I` | import | `G` | ledger |
| `W` | braindump | `J` | journal |
| `F` | flashcards | `Q` | quiz |
| `N` | new local root | `M` | move (local) |
| `s` | sync | `c` | commit and push |
| `,` | settings | `?` | key cheat sheet |
| `g` | this guide | | |

**Dialogs and screens:** `esc` closes or goes back; `ctrl+s` saves in every editor.

## 17. Troubleshooting

| Symptom | Fix |
|---|---|
| `llmsx explorer needs Textual` | Install the extra: `python -m pip install 'llmsx[tui]'`. |
| `no concept tree at …` | `--repo` must point at a checkout that contains `concept-tree/tree.json`. |
| The llms tabs say `no .llms directory` | The hub's concept packs are not on this machine. Set `LLMSX_CONCEPTS_PATH`. |
| Research offers only `queue` | The provider's command-line tool is not on `PATH`. Install it or switch provider in Settings. |
| A research job fails with 401 | A stored API key overrides a working login. Clear the key in Settings. |
| `c` refuses to push | Set a GitHub token in Settings or `LLMSX_GITHUB_TOKEN`; use **Test** in Settings. |
| A new button is not visible | The button row scrolls sideways; widen the window, or use the key (`y`, `p`). |
| Something failed silently | Read `~/.llmsx/explorer.log`. |
