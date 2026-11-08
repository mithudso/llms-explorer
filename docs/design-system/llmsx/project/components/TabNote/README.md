TabNote is the one-paragraph explanation of what a section tab is for, set under the lede.

Source: `site/src/pages/tree/index.astro`, style `.tab-note` in `global.css`.

## Use

- One per page, directly after the `.lede` paragraph. The consumer supplies the paragraph text with inline links and `<strong>` for the tab's own name.
- Ground `paper-raised`, 1px `line` border with a 3px `accent` left rule, `radius`, padding `sp-3` `sp-4`, text `step--1` in `ink-muted`.
- It may include the `●` haspack glyph inline (`<span class="haspack">●</span>`) to explain the tree's markers.

## Do / don't

- Do explain the page's mechanics in plain sentences: what a click does, what a marker means.
- Don't use it for warnings or status; it is the only left-ruled box on the tree page.
