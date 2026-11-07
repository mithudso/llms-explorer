# Work log

Append-only. Newest entries at the bottom.

---

## [2026-11-07] setup | docs/ wiki scaffolded

- Categories: concepts - architecture - subsystems - decisions - reference - operations - history
- Baseline commit: `ddec12f6`
- Created: `docs/{CLAUDE,index,log}.md`, `raw/`, 4 `.claude/commands/docs-*`,
  and `.claude/scripts/docs-lint.py`

## [2026-11-07] setup | started in grow mode

- Wrote one page from the code: [[site-design-tokens]], covering `site/src/styles/`, `site/src/layouts/Base.astro`, `site/src/pages/tree/index.astro`, `site/src/components/TreeBrowser.astro` and `SearchBox.astro`.
- Existing flat documents in `docs/` were left as they are; nothing was split or moved.
- `release-commands:` left empty: the site deploys through Cloudflare Pages on push, with no local release command.

## [2026-11-07] update | logo and contrast fixes on the site

- [[site-design-tokens]] rewritten: header lockup, `site/tools/gen_brand_icons.mjs`, `--control-border`, darker `--ink-faint`. Removed traps that the change fixed (`#264c66` literal, undefined `--fg-muted`, contrast misses).
