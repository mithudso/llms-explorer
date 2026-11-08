ConceptTree is the collapsible outline of every topic: each branch a native `<details>`, each frontier name a plain list item.

Source: `site/src/pages/tree/index.astro` (markup built at build time), styles `#tree-list` in `global.css`. This card uses the class `.tree-list` for the same rules.

## Use

- The consumer supplies the tree (roots, nodes with children, frontier names) and which nodes have a facts file. Each node is drawn once even if named under two parents.
- Each branch: `<li data-slug data-concept data-facts?><details><summary>` name, optional `●` haspack, optional count `</summary>` node body, child `<ul></details></li>`.
- Disclosure: a `▸` in `ink-faint` before each summary, rotated 90deg when open over 0.1s.
- Count: `node-count` style in `ink-faint`, "N children" or "N children · M total" when deeper concepts exist.
- Node body (narrow screens only): a mono meta line behind a 2px `line` left rule, e.g. "52 facts in 6 facets · published reference · read reference · facts.md". At 60rem and up the facts panel shows this instead.
- Frontier names: italic `ink-faint`, indented to align with branch names, suffixed "(frontier)" in upright text.
- Selected node: `accent-soft` behind the name, `radius-mark`.
- Indent per level `sp-4`; item margin `sp-1`; line height 1.45.

## Do / don't

- Do keep it working without JavaScript; the facts panel is an enhancement.
- Don't add icons per node or color by depth; the only hue is the `accent` dot and hover.
