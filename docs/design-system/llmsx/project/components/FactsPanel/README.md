FactsPanel shows the opened concept's facts file beside the tree: title, trail, links, the facts rendered from Markdown, and its children.

Source: `site/src/components/TreeBrowser.astro` (built with `createElement` and text nodes, never `innerHTML`), styles `.facts-panel` and `.tree-layout` in `global.css`.

## Use

- Layout: in `.tree-layout`, a `5fr` tree column and a `7fr` panel with gap `sp-5` at 60rem and up. The panel is `position: sticky` at `panel-sticky-top` and scrolls inside `calc(100vh - 6rem)`. Below 60rem the script moves it under the opened name.
- The consumer supplies the concept (name, trail of ancestors, meta line, facts URL) and the fetched facts Markdown. Headings level 2 render as `h3`, level 3+ as `h4`; the file's own H1 is skipped.
- Ground `paper-raised`, 1px `line` border, `radius-panel`, padding `sp-3` `sp-4`, text `step--1`. `aria-live="polite"`.
- Trail: each ancestor from the root is a `.facts-step` text button in `accent`, joined by " › ".
- Empty and status lines (`.facts-empty`, `.facts-trail`, `.facts-links`) are `ink-faint`. Copy: "Click a concept to read its facts here." "Loading facts…" "No facts file yet. Its children are listed below; a ● marks the ones that have facts."
- A concept without facts may show "Research this concept": `.facts-research-btn`, `accent` fill, `paper` text, `radius`, padding 0.35em 0.9em; disabled at 0.6 opacity.
- Links in facts text open only for `http(s)` or root-relative URLs; archived `/sources/` links render as text.

## Do / don't

- Do keep confidence and verification notes inline in the fact text, as the facts file writes them.
- Don't render facts Markdown as HTML.
