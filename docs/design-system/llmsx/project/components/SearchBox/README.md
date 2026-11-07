SearchBox is the semantic and keyword search field above the concept tree, with a live status line and a result list.

Source: `site/src/components/SearchBox.astro`. The source styles target the ids `#semantic-search-input`, `#semantic-search-status` and `#semantic-search-results`; this card uses the classes `.search-input`, `.search-status`, `.search-results` for the same rules.

## Use

- The consumer supplies the search metadata (slug, concept, summary) and the vector index; the component loads the embedding model on first focus.
- Input: full width, `step-0`, padding 0.6em 0.8em, 1px `line` border, radius 0.4em.
- Status: `step--1`, `role="status"`, `aria-live="polite"`, reserves 1.2em so the layout does not jump.
- Results: an unstyled list with a 1px `line` rule under each item; each item is a link to the concept and a `.search-summary` line.

## Do / don't

- Do keep the placeholder as an example of what to type: "Search concepts — try a name, question, or phrase…".
- The input border (`line`, 1.2:1 on `paper`) is below the 3:1 control-border floor in the source. A consumer building a new surface should use `line-strong` or darker; this card keeps the source value.
