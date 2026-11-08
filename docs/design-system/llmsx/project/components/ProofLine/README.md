ProofLine is the single mono line of exact counts that summarises the data behind a page.

Source: `site/src/pages/tree/index.astro`, style `.proof` in `global.css`.

## Use

- The consumer supplies the counts and an optional trailing link. Items are joined by a spaced middle dot `·`.
- Mono `step--1` in `ink-muted`, between a top and bottom 1px `line` rule, `sp-3` padding block, no horizontal padding.
- Counts are computed at build time from the same data the page renders; never round or estimate.

## Do / don't

- Do end with the snapshot date when the data is a snapshot.
- Don't bold numbers or color them; the line is read, not scanned for emphasis.
