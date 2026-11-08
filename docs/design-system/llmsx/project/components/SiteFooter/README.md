SiteFooter is the closing band with the one-line site description and the policy and source links.

Source: `site/src/layouts/Base.astro`, styles `.site-footer` in `global.css` and `lx-polish.css`.

## Use

- One per page. Max width `nav-max`, centred, `paper-raised` ground, 1px `line` border, `radius-zone`, 18px padding, text `step--1` in `ink-faint`, centred.
- The consumer supplies the link list; links wrap with a 0.5rem by 1.3rem gap. "This page as Markdown" appears only when the page has a Markdown twin.

## Do / don't

- Do keep the description to one sentence.
- Don't add social icons or a newsletter form here.
