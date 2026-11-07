SiteHeader is the sticky top bar with the llmsx logo, the four primary sections, a Concept tree shortcut and the Resources & account menu.

Source: `site/src/layouts/Base.astro`, styles `.site-header` and `.site-nav` in `global.css` and `lx-polish.css`.

## Use

- One per page, inside `<header class="site-header">`. It stays at `top: 0` with `z-index: 60`, a `paper-raised` ground at 88% opacity and a 10px backdrop blur, and a 1px `line` bottom border.
- The consumer supplies the nav items as `[href, label, title]` and the current route. The link whose route matches gets `aria-current="page"` (set in `ink`, weight 600). `/tree/` marks "Context libraries" as current.
- The brand link holds the lockup as an inline `<svg class="brand-logo">` (28px tall, `aria-hidden`; the link's `aria-label` names it), then `<span class="brand-note"> / toolkit for coding agents</span>`. The mark is `accent` (`accent-hover` on hover), the glyph `accent-ink`, the wordmark `ink`. The note hides below 800px.
- "Concept tree" carries `.tree-shortcut`: a `line-strong` left divider and `sp-3` padding.
- The menu is a native `<details class="menu">`, so it opens without JavaScript. Its items are links with a `.menu-note` line under each.

## Do / don't

- Do keep nav labels in sentence case and under three words.
- Don't swap the inline lockup for an `<img>`; inline paths take their colours from the tokens.
- On phones the links wrap to a second row and each target is 44px tall.
