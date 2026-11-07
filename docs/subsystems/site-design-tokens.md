---
title: Site design tokens, logo and the concept tree page
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
  - code: site/tools/gen_brand_icons.mjs
  - code: site/public/site.webmanifest
  - code: site/public/favicon.svg
  - code: site/public/favicon.ico
  - code: site/public/og-image.png
  - code: site/public/404.html
verified_at: 6d2ad1f6
---

# Site design tokens, logo and the concept tree page

The site is styled with plain CSS and no framework. All tokens are CSS custom properties
on `:root` in `site/src/styles/global.css:16`: 15 colours, three font stacks, five fluid
type steps (`--step--1` to `--step-3`), eight spacing steps (`--sp-1` to `--sp-8`, 4px
base), one radius, one shadow and `--measure`. There is one theme; `html` sets
`color-scheme: light` (`site/src/styles/global.css:65`).

`site/src/layouts/Base.astro:2` imports the base stylesheet, then the polish stylesheet on
the next line. The polish file adds a sticky translucent header, a wider main column,
pill stats and rounded cards on top of the base rules.

The concept tree at `/tree/` is built at build time in `site/src/pages/tree/index.astro`.
Each concept is a `<details>` inside `#tree-list`, so the tree opens without JavaScript.
`site/src/components/TreeBrowser.astro` adds the facts panel beside it. The panel fetches
`/downloads/concepts/<slug>.md` and renders it. `site/src/components/SearchBox.astro` adds
semantic search above the tree.

## Logo and icons

The llmsx logo (tree mark plus monoline wordmark) lives in
`docs/design-system/llmsx/project/assets/Logos/`. The header in
`site/src/layouts/Base.astro` carries the lockup as an inline SVG, coloured by the
`.brand-logo` rules in `site/src/styles/global.css` from `--accent`, `--accent-hover`,
`--accent-ink` and `--ink`. `site/tools/gen_brand_icons.mjs` renders the favicon, the
apple-touch icon, the manifest icons and the 1200x630 social card into `site/public/`
from the logo SVGs. Its outputs are committed; it is not part of `npm run build`.
`Base.astro` links them and sets the `og:` and `twitter:` meta tags.

## Contrast

`--ink-faint` (#616a79) passes 4.5:1 on `--paper`, `--paper-raised`, `--code-bg` and
`--accent-soft`. `--control-border` (#808996) is the border of inputs and secondary
buttons and passes 3:1 on `--paper` and `--paper-raised`. `--line` and `--line-strong`
are decorative only. A Design System artifact mirrors these values in
`docs/design-system/llmsx/project/tokens.json`.

> ⚠️ `site/src/styles/lx-polish.css` loads after `site/src/styles/global.css` and overrides
> some of its values: `main` max-width becomes 1160px
> (`site/src/styles/lx-polish.css:7`), and `.eyebrow`, `.lede` and `.site-footer` are
> restyled. Reading the base stylesheet alone gives the wrong final value for these.

> ⚠️ The 60rem breakpoint that puts the facts panel beside the tree is declared twice. It
> appears in CSS (`site/src/styles/global.css:497`) and in
> `window.matchMedia("(min-width: 60rem)")` (`site/src/components/TreeBrowser.astro:73`).
> If you change one, change the other, or the panel is hidden while the script expects it
> to be visible.

> ⚠️ The facts panel builds its DOM with `createElement` and text nodes only
> (`site/src/components/TreeBrowser.astro:67`). Facts files are research text written by
> runs and people. Do not switch it to `innerHTML`.

> ⚠️ The tree payload is embedded in a `<script type="application/json">` block with every
> less-than sign escaped as a JSON unicode escape (`site/src/pages/tree/index.astro:109`).
> Concept names are untrusted text, and a literal closing script tag in one would end the
> element.

> ⚠️ Do not use `--line` or `--line-strong` as the border of a control. Both are below the
> 3:1 floor (1.2:1 and 1.5:1 on `--paper`); use `--control-border`.

> ⚠️ The header lockup is inline SVG paths, not an `<img>`, so its colours follow the
> tokens. The same paths are in `llmsx-lockup.svg` and in the design system's SiteHeader
> preview. If the logo changes, update all three, then rerun
> `node site/tools/gen_brand_icons.mjs` for the icons and the social card.

> ⚠️ `site/tools/gen_brand_icons.mjs` needs Playwright, which is not a site dependency.
> In a cloud session run it with `NODE_PATH=$(npm root -g)`; locally, install Playwright
> first.

> ⚠️ When a token in `site/src/styles/global.css` changes, the copy in
> `docs/design-system/llmsx/project/tokens.json` goes stale. Update it and republish the
> artifact. The artifact link is in `memory.md` under v0.22.135.
