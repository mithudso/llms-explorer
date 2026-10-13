# Changelog

All notable changes to this project are documented in this file. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.5] — 2026-10-13

### Added

- `llmsx explorer`: a concept opens on its facts (the pack, else the hub's
  `llms-facts.txt`).
- llms-family tabs render as keyword-highlighted lines with a cursor
  (`llmsx.explorer_lines`).
- Scratchpad: `y` / 📌 Save line appends a line with its source to
  `$LLMSX_HOME/scratchpad.md`; `p` / 📝 Scratchpad edits and copies it.
- `U` marks every concept with no facts file `further-research` and queues it.
- `↓` / `↑` move focus to the widget below / above outside lists and dropdowns.
- The complete user guide ships in the package (`llmsx/USER_GUIDE.md`): `g` in
  the app, `llmsx explorer --guide`, and https://llms-explorer.com/explorer/guide/.

## [0.1.0] — 2026-09-02

Initial release.

### Added

- `llmsx tree {show,detail,search,frontier}` — read-only browser over the
  generated llms-explorer concept tree (`site/src/data/tree.json`), zero
  third-party dependencies.
- `llmsx tui` — Textual browser over the same tree (`pip install 'llmsx[tui]'`).
- `llmsx concepts {list,show,serve}` — catalog and read llms-concept-abstractor
  concept packs (`<slug>.llms/` directories), zero third-party dependencies.
- `llmsx concepts tui` — Textual browser/editor over concept packs, ported
  from the hub-manager Concepts tab (`pip install 'llmsx[tui]'`).
- `llmsx family <topic>` / `llmsx optimize <file-or-text>` — one-turn CLI
  wrappers over `llmsx.skills.run_skill` for `concept-family-explorer` and
  `llms-deep-optimizer` (`pip install 'llmsx[skills]'`).
- `llmsx.skills` — load and run a `SKILL.md` against a model, with an
  injectable client for offline testing.
