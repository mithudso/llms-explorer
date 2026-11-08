llmsx is a reference site for coding agents. Its concept tree at `/tree/` is a long, collapsible outline of researched topics with a facts panel beside it. The visual system is plain CSS with no framework and no build-time theming: cool neutral paper, graphite ink, one muted steel-blue accent, a serif for headings, the system sans for body, and monospace as the signature. There is one theme (light); `html` sets `color-scheme: light`.

## Content fundamentals

- Write flat, factual sentences. State what a control does and what the reader will find, not how good it is. Real copy: "Click a concept to read its facts here." "Frontier names indicate work to investigate, not published references."
- Sentence case for headings, nav and buttons ("Research queue", "Context files", "Resources & account"). Uppercase only through the `eyebrow` and `h4` styles, never typed in caps.
- Address the reader as "you" only when giving an instruction; otherwise describe the page in the third person ("Concepts is for browsing").
- Numbers are exact and counted from data. Join facts on one line with a spaced middle dot: `52 facts in 6 facets · published reference · read reference · facts.md`. Pluralise correctly ("1 child", "6 children").
- No emoji. The only glyphs are the text marks listed under Iconography.
- The name is `llmsx`, lowercase. As a logo use the Logos group; the `brand` text style is for the name in running text. The header follows it with the note "/ toolkit for coding agents" in `body` at 0.75rem, `ink-muted`.

## Color

- Page ground is `paper`. Raised surfaces (header, tab-note, facts panel, footer, cards) are `paper-raised` with a 1px `line` border. Do not stack two raised surfaces without a `line` between them: `paper-raised` on `paper` is a 1.03:1 difference and reads only through the border.
- Text: `ink` for body and names, `ink-muted` for ledes, notes and nav, `ink-faint` for counts, meta lines and frontier names. All three pass 4.5:1 on `paper`, `paper-raised`, `code-bg` and `accent-soft`.
- Borders of controls (inputs, secondary buttons) are `control-border`, which reaches 3:1 on `paper` and `paper-raised`. `line` and `line-strong` are for decoration only.
- `accent` is the only hue. Use it for links, the haspack dot, the eyebrow, primary buttons and the 3px left rule of a tab-note. Never use it as a large background except on a button. Text on an `accent` fill is `accent-ink`. Primary button hover is `accent-hover`.
- `accent-soft` marks selection: the opened tree node (`radius-mark`), the eyebrow ground, `::selection`.
- `code-bg` grounds inline code, pre blocks and examples.
- No gradients anywhere. `color-mix()` appears once, in the header's translucent background (`paper-raised` at 88% over the page with a 10px backdrop blur).

## Typography

- Three stacks, all system fonts; the site ships no font files. `display` (Iowan Old Style, Palatino, Georgia) for `h2` to `h4`, the lede and card titles. `body` (system sans) for running text and for `h1`. `mono` for the wordmark, eyebrow, proof line, meta lines and code.
- Sizes come from the fluid `typeScale` tokens (`step--1` to `step-3`); the type styles record each step's minimum. Body line height is 1.6; the tree column tightens to 1.45 (`tree-node`).
- `h1` is sans 700 with -0.02em tracking; every other heading is serif 600 at line height 1.2.
- `h4` is uppercase with 0.04em tracking in `ink-muted`.
- The `proof` line is mono `step--1` in `ink-muted`, set between a top and bottom `line` rule with `sp-3` padding.

## Spacing and layout

- 4px base: `sp-1` 4px to `sp-8` 72px. The tree indents each level by `sp-4`. A node body sits `calc(1em + sp-1)` in, behind a 2px `line` left rule with `sp-3` padding.
- Main column is centred with a max of `main-max` (1160px) and padding `sp-7` top, `sp-5` sides, `sp-8` bottom. Prose blocks keep `measure` (42rem).
- At `bp-tree-wide` (60rem) and up the tree page is a two-column grid, `5fr` tree and `7fr` facts panel, gap `sp-5`. The panel is sticky at `panel-sticky-top` with `max-height: calc(100vh - 6rem)` and its own scroll. Below 60rem the panel is hidden and the script moves it directly under the opened name.
- At `bp-narrow` (640px) main padding drops to `sp-5` top and `sp-4` sides and the nav links wrap below the wordmark.

## Borders, radii, shadows

- Borders carry structure; shadows are rare. Hairlines are 1px `line`; stronger dividers are `line-strong` or a 2px top rule.
- Radii: `radius-mark` 3px (selection), `radius-sm` 4px (code, eyebrow), `radius` 6px (buttons, tab-note, menus), `radius-panel` 8px (facts panel, cards), `radius-zone` 10px (zones, footer).
- `shadow-card` on cards and the open dropdown only. `shadow-card-hover` on card-grid hover. The tree, tab-note and facts panel have no shadow.

## Iconography

- No icon set and no images on the tree page. Marks are text glyphs in the current font:
  - `▸` disclosure arrow before every branch, `ink-faint`, rotated 90deg when open.
  - `●` haspack dot after a concept that has a facts file, `accent`, 0.7em.
  - `▾` after the "Resources & account" menu summary.
  - `·` middle dot as a list separator in meta and proof lines.
- The logo is in the Logos group. Its mark is a tree glyph in a rounded square: a root node, a stem, and two branches. The filled node stands for a published reference (the `●` on `/tree/`) and the ring for a frontier name. The wordmark is `llmsx` drawn as monoline paths, so it renders the same without any font installed.
- Use `llmsx-lockup.svg` on `paper` and `paper-raised`, and `llmsx-lockup-reversed.svg` on `ink`. Use `llmsx-mark.svg` alone where space is square (app icons, avatars), and `llmsx-favicon.svg` at 32px and below; its heavier strokes keep the ring visible at 16px.
- Clear space around the mark is a quarter of its width. The mark is never smaller than 16px; the lockup is never shorter than 24px.
- Do not recolour the mark outside `accent`, `ink` and `paper`, set the wordmark in a font instead of using the paths, or add the ring node as a decoration elsewhere.
- On the site the header carries the lockup inline at 28px tall, its mark filled with `accent` (`accent-hover` on hover), its glyph `accent-ink` and its wordmark `ink`. `/favicon.svg` is `llmsx-favicon.svg`.

## Motion

- Hover and disclosure only: the `▸` arrow rotates over 0.1s; card borders and shadows transition over 0.15s. Nothing animates on load.

## States and accessibility

- Focus ring: `outline: 2px solid focus; outline-offset: 2px` on links, buttons, inputs; 3px offset on `summary`. `focus` is 8.5:1 on `paper`.
- Buttons and nav targets are at least `target-min` (44px) tall on phones.
- Current nav item: `aria-current="page"`, `ink`, weight 600. Link hover thickens the underline from 1px to 2px.
- The tree uses native `<details>`/`<summary>`, so it opens without JavaScript. The facts panel is `aria-live="polite"`.
- Contrast: every text token passes 4.5:1 on every ground it is used on, and `control-border` passes 3:1. These were fixed on the site on 2026-11-07 (`ink-faint` darkened from #667080; `control-border` added).

## Components

The tree page is built from seven parts, each a card in this system: SiteHeader, TabNote, ProofLine, SearchBox, ConceptTree, FactsPanel, SiteFooter. Their CSS is in `components/bundle.css`, copied from `site/src/styles/global.css`, `lx-polish.css` and `SearchBox.astro` with literals replaced by tokens. There is no JavaScript bundle; previews are static renditions of the markup the Astro pages emit.

## Not synced

- Fonts: none to fetch; all three families are system stacks.
- Assets: the Logos group was drawn for this system on 2026-11-07. The site uses it for the header lockup, `favicon.svg`, `favicon.ico`, the apple-touch icon, the web manifest icons and the social card (`og-image.png`).
- Components not carded (not on `/tree/`): `.btn` and `.btn.secondary` (primary values are in the tokens), `.card` / `.card-grid`, personas, zones, home-page sections, the 3D tree (`Tree3D.astro`).
- Route: read-only. The site has no component library, so nothing was built.
