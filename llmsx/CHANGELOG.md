# Changelog

All notable changes to this project are documented in this file. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
