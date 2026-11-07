---
title: Site design tokens and the concept tree page
type: subsystem
created: 2026-11-07
updated: 2026-11-07
sources:
  - code: site/src/styles/global.css
  - code: site/src/styles/lx-polish.css
  - code: site/src/layouts/Base.astro
  - code: site/src/pages/tree/index.astro
  - code: site/src/components/TreeBrowser.astro
  - code: site/src/components/SearchBox.astro
verified_at: ddec12f6
---

# Site design tokens and the concept tree page

The site is styled with plain CSS and no framework. All tokens are CSS custom properties
on `:root` in `site/src/styles/global.css:16`: 12 colours, three font stacks, five fluid
type steps (`--step--1` to `--step-3`), eight spacing steps (`--sp-1` to `--sp-8`, 4px
base), one radius, one shadow and `--measure`. There is one theme; `html` sets
`color-scheme: light` (`site/src/styles/global.css:61`).

`site/src/layouts/Base.astro:2` imports the base stylesheet, then the polish stylesheet on the next line.
The polish file adds a sticky translucent header, a wider main column, pill stats and
rounded cards on top of the base rules.

The concept tree at `/tree/` is built at build time in `site/src/pages/tree/index.astro`.
Each concept is a `<details>` inside `#tree-list`, so the tree opens without JavaScript.
`site/src/components/TreeBrowser.astro` adds the facts panel beside it. The panel fetches
`/downloads/concepts/<slug>.md` and renders it. `site/src/components/SearchBox.astro` adds
semantic search above the tree.

A Design System artifact was extracted from these files on 2026-11-07. Its source files
are in `docs/design-system/llmsx/project/` (tokens, brand README, seven component cards).
The extra token names it uses (`accent-hover`, `radius-sm`, `radius-panel`, `layout`
values) are recorded literals from the CSS, not variables the site declares.

> ⚠️ `site/src/styles/lx-polish.css` loads after `site/src/styles/global.css` and overrides some of its values: `main`
> max-width becomes 1160px (`site/src/styles/lx-polish.css:7`), and `.eyebrow`, `.lede`
> and `.site-footer` are restyled. Reading the base stylesheet alone gives the wrong final value
> for these.

> ⚠️ The 60rem breakpoint that puts the facts panel beside the tree is declared twice. It
> appears in CSS (`site/src/styles/global.css:482`) and in
> `window.matchMedia("(min-width: 60rem)")` (`site/src/components/TreeBrowser.astro:73`).
> If you change one, change the other, or the panel is hidden while the script expects it
> to be visible.

> ⚠️ The facts panel builds its DOM with `createElement` and text nodes only
> (`site/src/components/TreeBrowser.astro:67`). Facts files are research text written by
> runs and people. Do not switch it to `innerHTML`.

> ⚠️ The tree payload is embedded in a `<script type="application/json">` block, with `<`
> escaped to `<` (`site/src/pages/tree/index.astro:109`). Concept names are
> untrusted text, and a literal `</script>` in one would end the element.

> ⚠️ The primary button hover colour `#264c66` is a literal, not a variable
> (`site/src/styles/global.css:270`). A palette change has to edit it by hand.

> ⚠️ The search box uses `var(--fg-muted, inherit)`
> (`site/src/components/SearchBox.astro:228`), but `--fg-muted` is declared nowhere, so
> the status line inherits `--ink`.

> ⚠️ Contrast is lower than the comment at `site/src/styles/global.css:19` says.
> `--ink-faint` on `--paper` measures 4.63:1, not about 4.9:1. `--ink-faint` on `--code-bg`
> is 4.34:1, below 4.5:1. The search input border (`--line`, 1.18:1) and the secondary
> button border (`--line-strong`, 1.49:1) are below the 3:1 floor for control borders.

> ⚠️ When a token in `site/src/styles/global.css` changes, the copy in
> `docs/design-system/llmsx/project/tokens.json` goes stale. Update it and republish the
> artifact. The artifact link is in `memory.md` under v0.22.135.
