---
title: "Accessibility Writing"
description: "Reference for writing content that is usable by screen-reader users, low-vision users, deaf and hard-of-hearing users, users with cognitive disabilities, and users on assistive tech."
---

# Accessibility Writing

Reference for writing content that is usable by screen-reader users, low-vision users, deaf and hard-of-hearing users, users with cognitive disabilities, and users on assistive tech.

## The 8-point accessibility-writing test

1. **Headings form a proper outline.** Exactly one `<h1>` per page. No skipped levels.
2. **Every image has an alt attribute.** Decorative images use `alt=""`. Informative images get a 1–2 sentence description.
3. **Every link reads as a self-contained label.** "Click here," "read more," "learn more," and bare URLs fail.
4. **Every form control has a programmatically associated label.** `<label for>` matched to input `id`.
5. **Every icon-only button has an accessible name.** `aria-label` describing the action ("Close dialog," not "X icon").
6. **Information is never conveyed by color alone.** Status indicated by "Error: …" prefix or icon plus color.
7. **The page declares its language.** `<html lang="en">`.
8. **Time-based media has alternatives.** Video has synchronized captions and a transcript.

## 1. Alt text by image purpose

**Decorative images** — `alt=""` (empty, not missing).

**Informative images** — describe the information the image carries:
`alt="CPU usage spikes to 95% at 14:30 UTC then returns to baseline by 14:35."`

**Functional images** — describe the action or destination:
`alt="View cart"` (NOT `alt="shopping cart icon"`)

**Complex images** — short alt plus a long description:
`alt="Latency percentile chart for production over the past 24 hours."`
Plus `aria-describedby` pointing to a `<figcaption>` with full details.

## 2. Heading structure

- **One `<h1>` per page.** The page title.
- **No skipped levels going down.** After `<h2>` you may use another `<h2>` or an `<h3>`. You may not jump to `<h5>`.
- **Headings are not for styling.** Don't use `<h3>` because it looks right.
- **Descriptive headings.** "Introduction" fails WCAG 2.4.6. "How to reset your password" passes.

## 3. Link text

| Anti-pattern | Why it fails | Rewrite |
|---|---|---|
| "Click here" | No context out of place | "View the full pricing table" |
| "Read more" | All "Read more" links sound identical | "Read more about MongoDB Atlas Search" |
| "https://example.com/docs/atlas" | URLs are read aloud character by character | "Atlas documentation" |

- Don't include the word "link" in link text. Screen readers already announce that an element is a link.
- For downloadable files, include the file format: `Download the Q1 incident report (PDF, 1.2 MB)`.

## 4. Form labels

1. **`<label for>` matched to input `id`.** The most robust.
2. **Wrapped `<label>`.** Works without explicit `for`/`id`.
3. **`aria-labelledby` pointing at a visible element.**
4. **`aria-label`.** Last resort only when no visible label is possible.

## 5. Icon-only buttons

```html
<!-- Right -->
<button aria-label="Close dialog">
  <svg aria-hidden="true"><!-- X icon --></svg>
</button>
```

The `aria-label` describes what the button does ("Close dialog," "Search," "Open menu"). NOT what it looks like ("X," "Magnifying glass").

## 6. Color independence (WCAG 1.4.1)

- **Status with a prefix word.** "Error: Email is invalid." "Warning: Unsaved changes."
- **Status with an icon plus color.** A red X icon plus the word "Failed."
- **Links underlined as well as colored.**

## 7. Captions, transcripts, audio descriptions

- **1.2.2 Captions (prerecorded), Level A.** Synchronized captions for prerecorded video with audio.
- **1.2.4 Captions (live), Level AA.** Live captions for live audio.
- **1.2.5 Audio description (prerecorded), Level AA.** Audio description of prerecorded video.

## 8. Language tags

```html
<html lang="en">
  <p>The French phrase <span lang="fr">tour de force</span> means "feat of strength."</p>
```

## 9. The "skip to main content" link

```html
<body>
  <a href="#main" class="skip-link">Skip to main content</a>
  <header>...</header>
  <nav>...</nav>
  <main id="main">...</main>
</body>
```

- The skip link is the **first focusable element** on the page.
- It is **visually hidden until focused.**

## Reading-grade formulas as accessibility instruments

| Formula | Best for |
|---|---|
| Flesch-Kincaid Grade Level | General-audience web content, business writing |
| Gunning FOG Index | Business writing; enterprise plain-language audits |
| SMOG | Healthcare patient education (CDC, NIH, NCI), legal-adjacent disclosures |

## References

1. W3C WCAG 2.2: https://www.w3.org/WAI/WCAG22/quickref/
2. W3C, *Alternative Text Tutorial*: https://www.w3.org/WAI/tutorials/images/
3. W3C, *Labeling Controls Tutorial*: https://www.w3.org/WAI/tutorials/forms/labels/
4. WebAIM, *Creating Accessible Forms*: https://webaim.org/techniques/forms/advanced
5. The A11y Project, *Patterns*: https://www.a11yproject.com/patterns/
6. Section 508: https://www.section508.gov/
