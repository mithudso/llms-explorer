---
title: "Editorial Micro-Typography & Type-Craft Defects"
description: "Critique-relevant, named, screenshot-detectable type-craft defects, each as"
---

# Editorial Micro-Typography & Type-Craft Defects

Critique-relevant, **named, screenshot-detectable** type-craft defects, each as
**DETECT** (the on-screen tell) → **RATE** (severity) → **FIX** (the remedy + the CSS property or
InDesign/print control). Built for the typography pass of a design critique (e.g. `/deso`). This is
the depth layer; the high-level typographic-scale / measure / line-height *rubric* lives in
`visual-design-principles-and-critique` (P2 Typography).

## Contents

- [How to use this file](#how-to-use-this-file) — the DETECT→RATE→FIX contract + severity scale
- [1. Widows, orphans, runts & stranded subheads](#1-widows-orphans-runts--stranded-subheads)
- [2. Rag quality, rivers & bad line breaks](#2-rag-quality-rivers--bad-line-breaks)
- [3. Kerning / tracking / letter-spacing](#3-kerning--tracking--letter-spacing)
- [4. Leading / line-height, vertical rhythm & baseline grid](#4-leading--line-height-vertical-rhythm--baseline-grid)
- [5. Measure (line length / characters-per-line)](#5-measure-line-length--characters-per-line)
- [6. Hyphenation & justification (H&J), justified-text gaps](#6-hyphenation--justification-hj-justified-text-gaps)
- [7. Hanging punctuation, optical margin alignment, optical vs metric kerning, optical sizing](#7-hanging-punctuation-optical-margin-alignment-optical-vs-metric-kerning-optical-sizing)
- [8. Correct glyphs — character-level type crimes](#8-correct-glyphs--character-level-type-crimes)
- [9. "Type crimes" — system-level defects](#9-type-crimes--system-level-defects)
- [Quick-scan checklist](#quick-scan-checklist)
- [CSS micro-typography cheat-sheet](#css-micro-typography-cheat-sheet)
- [When NOT to flag (disconfirming findings)](#when-not-to-flag-disconfirming-findings)
- [References](#references)

---

## How to use this file

Every defect below is one **DETECT → RATE → FIX** entry. In a critique, name the defect, point at the
on-screen tell, assign a severity, and give the concrete fix.

**Severity scale** (aligned with the `frontend-ui` critique passes — Blocker → High → Medium → Low → Nit):

- **Blocker** — breaks reading, changes meaning, or destroys brand credibility in a hero/wordmark; ship-stopper.
- **High** — clear readability/legibility loss or a glaring amateur tell in prominent type.
- **Medium** — noticeable quality/polish defect; readers feel it even if they can't name it.
- **Low** — refinement-tier; visible to a trained eye, minor cost.
- **Nit** — connoisseur's detail; fix if cheap.

**Critique discipline:** micro-typography is the domain where dogma is most tempting and most often
wrong. Most "rules" here are *guidelines with documented exceptions* — read [When NOT to flag](#when-not-to-flag-disconfirming-findings)
before rating anything High. Calibrate severity to the artifact: a one-word widow is a Blocker in a
printed annual report and a Nit in a responsive web paragraph.

**Medium where shown** means "screenshot-detectable but context-dependent" — confirm intent before flagging.

---

## 1. Widows, orphans, runts & stranded subheads

> ⚠️ **The widow/orphan labels are not standardized — name the visual position, not the label.** The
> *most common* convention (Butterick, MDN, Wikipedia, Adobe) is: **widow** = a short last line of a
> paragraph stranded alone at the **top** of the next column/page ("a past but no future"); **orphan**
> = the first line of a paragraph stranded alone at the **bottom** of a column/page ("a future but no
> past").[^widoworphan][^mdnwidows][^mdnorphans] But reputable sources *reverse* this — Fontfabric
> (2025) defines orphan=top, widow=bottom — and Wikipedia states outright there is "no consistent
> standard."[^fontfabricorphan][^widoworphan] A *third* usage (most CSS/web docs) calls the **runt**
> (§1.3) an "orphan." **In a critique, describe the tell — "a one-word last line stranded at the top
> of column 2" — rather than rely on "widow."**[^widoworphan]

### 1.1 Short last line stranded at the TOP of the next column/page (standard "widow")

- **DETECT:** A near-empty line (often one or two words) floating at the very top of a column/page, the
  bulk of its paragraph on the previous page; a white gap sits above it and the text "color" breaks.[^butterickwidow][^fontfabricorphan]
- **RATE:** **High** for a single word/part-word at a page or column top (the most distracting case —
  Butterick: widows "are more distracting" because they can be as short as one word).[^butterickwidow]
  **Medium** for a fuller last line. **Blocker** only in premium/published collateral (books, annual
  reports) where it reads as an oversight.[^fontfabricorphan]
- **FIX:** Print/word-processor: enable widow/orphan control — InDesign **Keep Options → "Keep Lines
  Together"**; Word **Paragraph → Line and Page Breaks → Widow/Orphan control**.[^butterickwidow][^fontfabricorphan]
  Or copy-edit (add/cut a word to reflow). **Do NOT insert a hard line break / carriage return** to
  fix it — it becomes a layout landmine on reflow.[^butterickhardbreak] CSS (paged/multicol only):
  `widows: 2;` (see §1.5 for the support caveat).

### 1.2 First line of a paragraph stranded at the BOTTOM of a column/page (standard "orphan")

- **DETECT:** A lone opening line at the foot of a column, the paragraph body continuing overleaf; the
  reader starts a thought then must jump.[^butterickwidow][^mdnorphans]
- **RATE:** **Medium** typically (it's at least a full line, so less ragged than a one-word widow).
  Rises to **High** in formal published layouts.[^butterickwidow]
- **FIX:** Same Keep Options / `orphans: 2;` controls as §1.1.[^adobekeep][^mdnorphans]

### 1.3 The "RUNT" — a single word / very short last line of a paragraph (not at a break)

- **DETECT:** A lone short word on a paragraph's final line, *anywhere* on the page — the paragraph
  gap below then looks mistakenly large. Distinct from a true widow because it isn't tied to a
  column/page break. (Print purists say *runt*; word processors and CSS docs call it *widow* OR
  *orphan*.)[^bookhouserunt][^widoworphan]
- **RATE:** **Low–Medium** on the web (very common, low stakes; this is the web's version of the widow
  problem); **Medium** in print body. A one- or two-letter runt is the worst-looking. Butterick:
  browsers "are happy to put a small word alone on the last line of a paragraph, which always looks
  bad."[^butterickwidow]
- **FIX:** Web (modern, preferred): `text-wrap: pretty;` on body text — pulls a word back so the last
  line has ≥2 words.[^chrometextwrap][^webkittextwrap][^mdntextwrap] Web (manual/legacy): a
  non-breaking space `&nbsp;` between the **last two words** so they wrap together; avoid `<br>` (breaks
  responsive layouts).[^butterticknbsp][^bootstrapwidow] Print: copy-edit, or subtle tracking on the
  preceding lines to absorb the word.[^fontfabricorphan]

### 1.4 Heading/subhead stranded at the BOTTOM of a column, body text on the next column/page

- **DETECT:** A bold subhead sitting as the last thing in a column, its paragraph beginning elsewhere
  — the label is severed from the content it introduces, misleading scanning.[^smashingfrag][^mdnbreak]
- **RATE:** **High** — arguably worse than a text widow because it breaks a structural label from its
  content; **Blocker** in print/PDF deliverables.
- **FIX:** CSS: `break-after: avoid;` on the heading and/or `break-inside: avoid;` on a wrapping
  container.[^mdnbreak] **Support caveat (verified-as-of 2026-06-16):** `break-after: avoid` is broadly
  available in Chromium (since ~Dec 2022) but still patchy in Safari/Firefox for some break values —
  verify in target engines.[^mdnbreak] Print: InDesign **Keep Options → "Keep with Next ___ Lines"**.[^adobekeep]

### 1.5 The CSS `widows` / `orphans` properties — behavior & support

- `orphans` = minimum lines kept at the **bottom** of a fragment before a break; `widows` = minimum
  lines kept at the **top** after a break. Both: initial value **2**, inherited, apply to block
  containers, take an `<integer>` ≥ 1.[^mdnwidows][^mdnorphans]
- **They act ONLY in fragmented contexts** (paged media / print / PDF, multi-column `columns`, or
  regions) — they do **nothing** in ordinary continuous web flow, and do **not** fix a runt in a
  single-column flowing article. Butterick lists CSS widow/orphan control as "not applicable" to
  normal web pages.[^mdnfrag][^butterickwidow]
- **Browser support (verified-as-of 2026-06-16):** supported in Blink (Chrome) and WebKit (Safari);
  **not supported in Firefox** (long-standing open bug) — treat as progressive enhancement.[^caniusewidows]

---

## 2. Rag quality, rivers & bad line breaks

### 2.1 Bad rag (lumpy / zig-zag ragged-right edge) in flush-left text

- **DETECT:** Squint or step back. **Good rag** = a soft, gentle, irregular taper where successive line
  lengths vary in *small* increments. **Bad rag** = wild swings in line length (a "hard rag"), a
  zig-zag/staircase edge, a deep "bite" out of the margin, or accidental shapes/words forming down the
  right edge.[^goodpage][^myfontsrag][^webkittextwrap]
- **RATE:** **Low–Medium** (aesthetic/readability, rarely blocking). **Medium** when the rag is so deep
  that line lengths vary wildly or accidental shapes appear.
- **FIX:** Web: `text-wrap: pretty;` — WebKit's implementation improves rag by reducing line-length
  variation across the whole paragraph (Chromium's only touches the last ~4 lines — see §2.5).[^webkittextwrap][^chrometextwrap]
  Print: InDesign **"Balance Ragged Lines"** (note: it is overridden by justification, Keep options,
  "No Break", and trailing spaces).[^adobebalance] Adjust **measure** (§5), tune hyphenation, or
  hand-insert `&nbsp;`/soft breaks.[^runragged]
- **Don't reflexively flag rag depth alone** (see [When NOT to flag](#when-not-to-flag-disconfirming-findings)): Bringhurst prefers a deeper "hard rag" over a tight rag bought with bad breaks/excess hyphenation.[^webtyporag]

### 2.2 Hyphenation ladder (consecutive lines ending in hyphens)

- **DETECT:** Two, three, or more stacked hyphens down the right edge.[^runragged][^webkittextwrap]
- **RATE:** **Medium** — adds cognitive load (the split word's halves sit far apart) and looks careless.
  The common rule is **no more than two consecutive hyphenated lines** (a ladder is typically 3+; some
  style guides flag 4+ — the threshold varies).[^runragged][^mlarivers]
- **FIX:** InDesign: "Limit Consecutive Hyphens to: 2". CSS: there is **no property to cap consecutive
  hyphens** (verified-as-of 2026-06-16) — widen the measure, use `hyphens: manual`, or go ragged.
  `text-wrap: pretty` reduces trailing consecutive hyphens.[^webkittextwrap][^chrometextwrap]

### 2.3 Rivers (vertical/diagonal channels of white running down a block)

- **DETECT:** Gaps of inter-word white space that coincidentally line up across several lines, forming
  a "river" of white. **Mostly afflict justified text and narrow measures** (and monospaced fonts),
  where word spaces are stretched.[^wikiriver][^opusriver][^creativepro_river] **The detection test:**
  turn the proof **upside down** and/or **squint to defocus** and/or view from 2–3 ft — rivers then
  stand out as light streaks against the even gray.[^wikiriver][^opusriver]
- **RATE:** **Medium** in justified body; **Low** in ragged text (rivers are rare there). Confirm at
  print resolution — rivers invisible on screen can be obvious in print, and "long rivers are unlikely
  in ordinary text," so screen-only critics over- or under-call them.[^creativepro_river]
- **FIX:** Switch from **justified to ragged-right** (removes the stretched spacing that causes rivers —
  Bringhurst's core recommendation); or widen the measure, tighten H&J word-spacing limits, add
  hyphenation, or hand-reflow.[^webtyporiver] CSS `text-wrap: pretty` does **NOT** yet fix rivers in
  any browser (WebKit: "We are not yet making adjustments to prevent rivers").[^webkittextwrap]

### 2.4 Bad line breaks (splitting things that should stay together)

- **DETECT (the tells & the rules):** a **person's name / title+name** split across lines ("Sgt." |
  "Rock"); a **number split from its unit/symbol** ("5" | "km", "$" | "10", "Fig." | "23"); a **one- or
  two-letter word stranded at a line end** (esp. after a preposition); a line ending on a dash or an
  opening parenthesis; a **phone number or URL** broken at an arbitrary point.[^butterticknbsp][^runragged]
- **RATE:** **Medium** for a broken name or number+unit (changes parsing, looks unprofessional);
  **Low–Nit** for a stranded short word; **High** if it creates genuine ambiguity (a split phone
  number/URL the reader must reassemble).
- **FIX:** A **non-breaking space `&nbsp;`** ("invisible glue") between name parts, number+unit, or
  abbreviation+reference (Word: Ctrl+Shift+Space; Pages: Opt+Space).[^butterticknbsp] **`<wbr>`** marks
  an allowed break point inside a long URL; **soft hyphen `&shy;`** marks a permitted hyphenation
  point.[^runragged][^mdntextwrap] InDesign **"No Break"** character style glues a phrase.[^adobebalance]
  Do **NOT** use a hard line break — it breaks on reflow.[^butterickhardbreak]

### 2.5 `text-wrap: pretty` / `balance` — scope, limits, support (verified-as-of 2026-06-16)

- **`text-wrap: balance`** — makes all lines of a *short* block (~≤10 lines) roughly equal length; for
  **headlines, captions, teasers**. Side effect: the block becomes narrower than its container.
  Support: Chrome 114 / Firefox 121 / Safari 17.5; **Chromium balances only the first 4 lines**,
  WebKit balances all.[^webkittextwrap][^logrockettextwrap]
- **`text-wrap: pretty`** — for **body text**, and **implementations differ sharply**: Chromium
  (Chrome 117+) re-evaluates only the **last ~4 lines** (focus: prevent short last lines / runts +
  trailing hyphens); WebKit (Safari TP, ~2025) evaluates the **whole paragraph** (prevents runts,
  improves rag, reduces hyphenation; not rivers).[^chrometextwrap][^webkittextwrap]
- **`text-wrap: pretty` does NOT fix true (paged) widows/orphans** — it only handles the *last lines*
  of a paragraph (the runt). Use the `widows`/`orphans` properties for paged contexts.[^logrockettextwrap][^mdntextwrap]

---

## 3. Kerning / tracking / letter-spacing

> **Definitions (keep them precise in critique).** **Kerning** = adjusting the space between a
> *specific pair* of letters; most fonts ship hundreds–thousands of kern pairs baked in (the font's
> GPOS `kern` feature).[^buttericckern][^wikikern] **Tracking / letter-spacing** = a *uniform*
> adjustment across a whole run.[^butterickletterspace][^wikiletterspace] Kerning fixes individual
> awkward pairs; tracking changes overall density. CSS `letter-spacing` = tracking; `font-kerning` /
> GPOS `kern` = kerning.

### 3.1 Bad / uneven kerning pairs ("keming", "rn"→"m", gaps at Va/To/LY)

- **DETECT:** Specific pairs show uneven gaps — overhang-prone pairs `T Y V W A` leave a conspicuous
  *hole* ("Va", "To", "LY", "We"), OR tight pairs collapse so `r`+`n` reads as `m` ("burn"→"bum"),
  `cl`→`d`. The classic tell is "**keming**" (the word "kerning" itself mis-kerned so "rn" looks like
  "m").[^explainkern][^wikikern]
- **RATE:** **Blocker** when mis-kerning changes the word (legible-but-wrong) or appears in a
  **logo/wordmark/hero headline**. **High** for visible uneven gaps in any large display heading (the
  larger the type, the more the eye catches gaps). **Medium/Low** for minor body unevenness; **Nit**
  for a single slightly-loose pair.[^buttericckern][^sitepointtracking]
- **FIX:** First ensure pair-kerning is on: CSS `font-kerning: normal` (forces stored kern data;
  `auto` may disable it at small sizes), or `font-feature-settings: "kern"`.[^mdnfontkerning][^cssfontkerning]
  Cross-browser caveat: Safari/WebKit historically needed `text-rendering: optimizeLegibility` to
  kern; Firefox kerns automatically ≥20px — so a headline can look kerned in one browser, not
  another.[^clagnutmanual] For the specific bad pair in display/logo work, apply **manual** correction
  (wrap the pair in a span + negative `letter-spacing`, or fix the pair in the design tool / font
  GPOS).[^clagnutmanual] Note: any non-zero `letter-spacing` disables optional ligatures.[^mdnletterspacing]
  Reality check: built-in kerning is fine for non-professionals; manual pair-kerning earns its keep
  mainly in logos and large display.[^buttericckern][^clagnutmanual]

### 3.2 ALL-CAPS / small-caps set WITHOUT added tracking

- **DETECT:** A run of capitals or small caps where letters sit too close — caps are drawn to nest
  beside lowercase, so packed together they look dense/cramped and read slower.[^butterickallcaps][^butterickletterspace]
- **RATE:** **High** for all-caps body/UI labels at small sizes (legibility + accessibility hit);
  **Medium** for an all-caps display line; **Low/Nit** for a 2–3-letter acronym.
- **FIX:** Add **5–12% letter-spacing to caps and small caps — but not to lowercase**: CSS
  `letter-spacing: 0.05em` to `0.12em` (em units so it scales). Bake it into the style:
  `text-transform: uppercase; letter-spacing: 0.08em`.[^butterickletterspace][^butterickallcaps]

### 3.3 Display / large headings left at default (loose) tracking

- **DETECT:** A big headline (~30px+/display) where letter spaces look airy/loose, so the word fails
  to read as one tight unit. Default metrics are tuned for ~9–13pt body; at display size they read
  loose.[^butterickletterspace]
- **RATE:** **Medium** (polish/hierarchy); **High** only for a brand wordmark/hero where looseness
  undercuts impact.
- **FIX:** Apply **"the larger the type, the tighter the tracking; the smaller, the looser."** Tighten
  display type with small **negative** `letter-spacing`, typically `-0.01em` to `-0.03em`.[^sitepointtracking][^figrtracking][^butterickletterspace]
  (The system font on Apple platforms does this automatically per point size; static mockups and web
  type must do it by hand.[^applehig])

### 3.4 Over-tightened body that collides letters

- **DETECT:** Body/UI text where letters touch or overlap, counters close up, words become a smear —
  an over-aggressive negative `letter-spacing`. MDN warns a large negative value makes words
  "unrecognizable."[^mdnletterspacing]
- **RATE:** **High** (direct legibility loss) → **Blocker** if it makes words unrecognizable or causes
  overlap at small sizes / for low-vision users.
- **FIX:** Return body `letter-spacing` toward `normal`/`0` (default body metrics need no extra
  spacing). Never use negative tracking to cram more text into a column.[^butterickletterspace]

### 3.5 Letter-spaced lowercase body (tracking as a crutch)

- **DETECT:** Body text with extra space between *lowercase* letters — words look spread, the rhythm
  breaks, text reads as strings of individual letters instead of word-shapes.[^kevinletterspace][^mdnletterspacing]
- **RATE:** **Medium** (readability + amateur tell); **High** at small sizes or large blocks; **Nit**
  for one short tracked sub-label.
- **FIX:** **Don't letter-space lowercase body text** — the font's built-in spacing already accounts
  for its counters/ascenders/descenders. Set `letter-spacing: normal`. (Goudy's maxim: "anyone who
  would letter-space lowercase would steal sheep" — strong guidance, not absolute; tiny tracking can
  aid *very small* lowercase <9pt.)[^kevinletterspace][^butterickletterspace] Butterick's overboard
  test: "If the spaces between letters are large enough to fit more letters, you've gone overboard."[^butterickletterspace]

---

## 4. Leading / line-height, vertical rhythm & baseline grid

> **Leading vs line-height.** "Leading" originally = the lead strips between lines of metal type;
> CSS `line-height` is its digital equivalent — but it sets an invisible box *around* the line
> (half-leading above and below), so it does not sit on the text baseline. That disconnect is the
> root cause of baseline-grid pain on the web (§4.5).[^googleleading][^damatoline]

### 4.1 Too-tight leading (lines touch; ascenders/descenders collide)

- **DETECT:** Lines crowd vertically; descenders of one line (g, y, p, j) touch/overlap the
  ascenders/caps below; the block looks dense and "clashes".[^fontfabricdesc]
- **RATE:** **Blocker/High** for multi-line body — direct legibility failure + accessibility
  regression. Apple: "If you need to display three or more lines of text, avoid tight leading even in
  areas where height is limited."[^applehig]
- **FIX:** Raise **unitless** `line-height`. Body baseline ~**1.4–1.6** (Butterick's optimal band is
  120–145% of point size; 110% is "too tight"). Use unitless values so children recompute against
  their own font-size. Bump toward the top for faces with long descenders or large x-height.[^fontfabricdesc][^pimplineheight][^buttericklinespacing][^unitlessline][^bringhurst]

### 4.2 Too-loose leading (text disintegrates into stripes)

- **DETECT:** Lines float so far apart the paragraph reads as separate horizontal stripes, not a
  cohesive block; the eye loses the line-to-line connection. Butterick: 170% is "too loose."[^buttericklinespacing]
- **RATE:** **Medium** (cohesion/aesthetics) → **High** if it breaks the perception of the paragraph as
  one block or balloons the layout.
- **FIX:** Reduce `line-height` into the body band (~1.4–1.6 / 120–145%). Design near ~1.4–1.5 (not
  above) for body so the layout still survives a user bumping line-height to 1.5 (§4.6).[^buttericklinespacing][^pimplineheight]

### 4.3 Leading not scaled with measure (long lines need more leading)

- **DETECT:** A long-measure (wide) column set with the same tight line-height as a narrow column —
  the eye struggles to find the next line's start on the return sweep.[^pimplineheight][^bringhurst][^nnglegibility]
- **RATE:** **Medium** (worse the wider the column).
- **FIX:** **"Longer lines → more leading; shorter/display → less."** Nudge `line-height` up ~0.1–0.2
  for wide columns; tighten for narrow cards/sidebars. (Bringhurst recommends more leading for longer
  measures; NN/g: maintain 1.4–1.6em, wider for longer lines.)[^pimplineheight][^bringhurst][^nnglegibility]

### 4.4 Inconsistent leading between blocks

- **DETECT:** Adjacent text blocks use visibly different line-heights for no functional reason; the
  page rhythm looks jittery.
- **RATE:** **Medium** (consistency/polish); **Low/Nit** if subtle.
- **FIX:** Drive all body-tier text from one tokenized `line-height` scale; reserve tighter values
  deliberately for headings/display (1.1–1.3). A common root cause is mixing unitless and unit'd
  line-heights so inheritance differs — standardize on **unitless**.[^unitlessline][^ultimateline]

### 4.5 Broken vertical rhythm / baseline-grid misalignment

- **DETECT:** Spacing between elements (headings, paragraphs, images, UI rows) doesn't fall on a
  consistent increment; baselines of adjacent columns don't line up; margins/padding look arbitrary.
- **RATE:** **Low–Medium** (refinement/"design QA" tier, *not* a usability blocker — and see the
  disconfirming note below before over-indexing).
- **FIX:** Snap spacing and line-heights to a shared increment — Material uses **8dp** for layout and a
  **4dp** baseline grid, with the rule that **line-height must be a multiple of the base unit** (e.g.
  15px text → 24px line-height) even if font-size strays off-grid.[^materialgrid] On the web, set body
  `line-height` to an integer multiple of the base unit and make vertical margins multiples of it; or
  use baseline-trim tooling (`leading-trim`/`text-box-trim`, the "basekick" technique) to remove the
  half-leading offset so text actually sits on the grid.[^damatoline]
- **Don't over-rate this** (see [When NOT to flag](#when-not-to-flag-disconfirming-findings)): "a
  baseline grid does not automatically create good vertical rhythm," and on the responsive web it
  often "has no meaning" — prioritize a *consistent spacing scale* (4/8px) over true baseline
  snapping.[^vanseobaseline]

### 4.6 WCAG Text Spacing anchor (verified-as-of 2026-06-16)

WCAG **2.2** SC **1.4.12 Text Spacing** (AA): a user must be able to override to at least line-height
**1.5×**, paragraph spacing **2×**, letter-spacing **0.12×**, word-spacing **0.16×** without loss of
content/function. Critical framing: "Content is **not required to use** these values" — so in a
critique, ~1.5 body line-height is a **robustness floor not to break**, not a styling mandate (though
NN/g independently recommends ~1.5–2× for comfort).[^wcagtextspacing][^dequetextspacing][^nnglegibility]

---

## 5. Measure (line length / characters-per-line)

> **The rule.** Bringhurst: "Anything from 45 to 75 characters is widely regarded as a satisfactory
> length of line… The 66-character line… is widely regarded as ideal. For multiple-column work, a
> better average is 40 to 50 characters." Butterick gives a wider working band (~45–90 incl. spaces)
> and stresses measuring in **characters per line, not inches** (point size changes chars-per-inch but
> not chars-per-line). UX sources converge on **50–75 CPL, ~66 ideal**; **~30–50 CPL on mobile**; the
> ~80-char ceiling is anchored by WCAG SC 1.4.8 (80 chars max).[^buttericklinelength][^webtypomeasure][^baymardline][^uxpinline][^wcagvisualpres]

### 5.1 Full-bleed body paragraphs spanning a wide viewport

- **DETECT:** Body copy runs the full width of a wide container/desktop viewport — lines visibly exceed
  ~90 characters; the paragraph is a wide "slab" with no max-width gutter, text touching both edges on
  a 1440px+ screen. (Count ~2 alphabets ≈ 52 chars and confirm the line runs well past it.) Too-long
  lines hurt the **return sweep** — the eye loses its place finding the next line and may re-read or
  skip ("doubling").[^baymardline][^uxpinline][^webtypomeasure]
- **RATE:** **High** (readability + engagement loss); **High/Blocker** for accessibility-sensitive
  content sites if it also trips WCAG 1.4.8's 80-char ceiling.[^baymardline][^wcagvisualpres]
- **FIX:** Constrain measure with the `ch` unit (width of "0", scales with font-size):
  `max-width: 66ch;` (~Bringhurst ideal) or `60–75ch`, centered with `margin-inline: auto`. `ch` is
  approximate, so treat 66ch as a target band. For responsiveness: `width: min(66ch, 100%)` so it never
  overflows narrow screens. Em-based widths (`width: 33em`) are the classic elastic alternative. In
  design tools, set a column width sized to ~45–75 chars (40–50 for multi-column).[^csstricksmeasure][^webtypomeasure]

### 5.2 Measure too narrow (over-constrained column)

- **DETECT:** A skinny column holding only a few words per line (well under ~40–45 chars); choppy rag;
  in justified narrow columns, big gaps and stacked hyphens (overlaps §6).
- **RATE:** **Medium** (Low/Nit for short captions or intentional sidebars).
- **FIX:** Widen toward 45–75ch (single column) / 40–50ch (multi-column). If it must stay narrow,
  prefer ragged-right over justified and enable hyphenation.[^webtypomeasure]
- **Note:** the 45–75/66 band is a strong *design convention*; the causal reading-speed story behind it
  is weaker than design advice implies (see [When NOT to flag](#when-not-to-flag-disconfirming-findings)). Flag out-of-band *extremes*, not every line ≠ 66.

---

## 6. Hyphenation & justification (H&J), justified-text gaps

> **What justification does:** to flush both edges, the engine *adds inter-word (and sometimes
> inter-letter) space* to fill the measure; browsers essentially only stretch *word* spacing. Web
> justification is weak because the browser engine is "rudimentary compared to a professional
> page-layout program." InDesign does it well via the **Adobe Paragraph Composer** (default), which
> evaluates *all lines of a paragraph together* (a Knuth-Plass-style whole-paragraph approach),
> yielding even spacing and fewer hyphens than the Single-line Composer.[^butterickjustified][^maxwelljustify][^adobecompose]

### 6.1 "Loose lines" / big ugly inter-word gaps (justified, no hyphenation)

- **DETECT:** Fully-justified body where some lines have conspicuously wide word gaps (a few long words
  stretched across the measure), gaps varying line-to-line — the classic justified-`<p>` look on the
  web. Often co-occurs with vertical **rivers** (§2.3).[^butterickjustified][^maxwelljustify][^adobecompose]
- **RATE:** **High** on the web without hyphenation; **Medium** in print/InDesign where the composer +
  H&J settings can largely fix it.
- **FIX (web):** either switch to ragged-right (`text-align: left;`, Butterick's default
  recommendation) OR, if justification is required, **always pair it with hyphenation**:
  `text-align: justify; hyphens: auto;` **and set `lang`** on `<html lang="…">` (browsers only
  hyphenate when `lang` is present and a hyphenation dictionary exists). Widen the measure to reduce
  gap pressure.[^butterickjustified][^mdnhyphens] **FIX (InDesign):** use the Paragraph Composer, turn
  on Hyphenation, and tune the H&J/Justification spacing (word/letter/glyph min–desired–max) for the
  measure.[^adobecompose]

### 6.2 Hyphenation ladder / stack

See **§2.2** (consecutive lines ending in hyphens). CSS has no property to cap consecutive hyphens.[^runragged][^mlarivers]

### 6.3 Hyphenated last word of a paragraph (and other bad breaks)

- **DETECT:** The final line/word of a paragraph is hyphenated, or a hyphen lands right before the
  paragraph ends.
- **RATE:** **Low / Nit.**
- **FIX:** InDesign Hyphenation: "Hyphenate Last Word: off", "Hyphenate Across Column: off", raise
  minimum word length / letters-before-and-after. CSS can't target this; use a manual `&shy;`/`&nbsp;`
  fix or accept it with ragged-right.[^adobecompose]

### 6.4 `hyphens` CSS support (verified-as-of 2026-06-16)

`hyphens` is Baseline "widely available" (since Sept 2023), but **dictionary- and `lang`-dependent**
(no dictionary → no hyphenation); historically Chrome required `lang` and lacked some dictionaries.
Always set `lang`.[^mdnhyphens]

---

## 7. Hanging punctuation, optical margin alignment, optical vs metric kerning, optical sizing

### 7.1 Hanging punctuation / optical margin alignment (un-hung punctuation)

- **What it is:** punctuation (quotes, bullets, hyphens, periods, commas) pushed *out past the text
  edge into the margin* so the text edge looks *optically* straight. Because punctuation has less
  visual weight than letters, leaving it inside the measure creates a visual "hole"/indentation in the
  flush edge.[^wikihanging] InDesign's **Optical Margin Alignment** also hangs serifs and overhanging
  letter edges (T, Y, A), not just punctuation.[^creativepro_hang]
- **DETECT:** A pull-quote/blockquote/bulleted paragraph whose first line begins with an opening quote
  (" or ') — making that line look *pushed in / indented* relative to the lines below, so a flush left
  edge looks subtly ragged. Same tell on the right edge with trailing commas/periods in justified text.
- **RATE:** **Low / Nit** (refinement, not functional); **Medium** only for a brand/editorial design
  where flush-edge polish is a stated goal.
- **FIX (print/InDesign):** Type ▸ Story ▸ **Optical Margin Alignment**; the font-size field controls
  overhang amount; use "Ignore Optical Margin" to exclude specific lists.[^creativepro_hang] **FIX
  (web):** `hanging-punctuation: first;` (and/or `last`/`force-end`/`allow-end`) — **BUT** (verified-as-of
  2026-06-16) `hanging-punctuation` is **Safari-only** (not Chrome or Firefox; MDN marks it "Limited
  availability / not Baseline"). Treat it as *progressive enhancement only*; the robust cross-browser
  fallback is a negative `text-indent` (or negative margin) on the quoted element, optionally behind
  `@supports not (hanging-punctuation: first)`.[^mdnhanging][^caniusehanging][^coyierhanging]

### 7.2 Optical vs metric kerning (the InDesign setting choice)

- **The choice:** **Metrics** kerning uses the kern-pair tables the *font designer* built in (best for
  text set in a single professional font; InDesign's default). **Optical** kerning *ignores* those
  tables and spaces letters by their *shapes* — useful when a font has few/no kern pairs, when mixing
  multiple typefaces in a word, or mixing sizes on a line. There's no universally "right" answer.[^adobekerntrack][^creativepro_metricvsoptical]
- **DETECT:** Display/headline text with visibly uneven letter gaps (a gappy "T o" or tight "AV"), or a
  mixed-typeface logotype with inconsistent spacing. (Deep kerning is §3 — keep this as the
  *setting-choice* lens.)
- **RATE:** **Low** (setting nuance) unless egregious in a logo/hero → **Medium**.
- **FIX:** In InDesign, keep **Metrics** for a single quality font; switch to **Optical** for
  poorly-kerned fonts, multi-font words, or mixed sizes. On the web there is no metric/optical toggle —
  `font-kerning` only turns *built-in* kerning on/off; it cannot synthesize optical kerning.[^adobekerntrack][^creativepro_metricvsoptical]

### 7.3 Optical sizing (opsz axis) — faux when one master is scaled

- **The principle:** some variable fonts carry an **`opsz` (optical size)** axis with size-specific
  designs — **text/body** sizes have lower stroke contrast, more open spacing, taller x-height;
  **display** sizes are more delicate, higher-contrast, finer-serifed. A single optical size scaled
  up/down ("faux") looks wrong.[^mdnopticalsizing][^googleopsz]
- **DETECT:** Large display headings that look too heavy/clumsy (a text cut blown up), or tiny body
  text that looks too thin/fragile (a display cut shrunk); a variable font whose headline and body
  don't show the expected contrast/spacing shift.
- **RATE:** **Low / Nit** (subtle; most visible in editorial/brand work).
- **FIX:** Let it auto-track: `font-optical-sizing: auto;` (enabled by default for fonts with an `opsz`
  axis; allowed values are only `auto` | `none`). For manual control, set
  `font-variation-settings: 'opsz' <n>` to match the rendered font-size. In design tools, pick the
  correct named optical size (Caption/Text/Display) or set the opsz slider to the point size. Support:
  `font-optical-sizing` is Baseline "widely available" (since March 2020); verify visually as some
  fonts/engines apply opsz imperfectly.[^mdnopticalsizing][^googleopsz]

---

## 8. Correct glyphs — character-level type crimes

These are **highly screenshot-detectable** and among the most common amateur tells.

### 8.1 Straight (dumb) quotes vs curly (typographer's/smart) quotes & the apostrophe

- **DETECT:** Vertical, symmetrical tick marks (`'` `"`) instead of the four directional curly glyphs
  (` ' ` ` ' ` ` " ` ` " `): opening and closing marks look identical rather than mirrored; or a
  subtler crime — a contraction/decade opening with an upward-pointing **opening** single quote where a
  downward apostrophe is required (`'70s`, `rock 'n' roll`).[^butterickquotes][^butterickapostrophe]
- **RATE:** **High** (Butterick: straight quotes "should never, ever appear in your documents" — a
  primary professionalism tell). Apostrophe-direction error = High.
- **FIX:** Opening single `&lsquo;` (' U+2018), closing single / apostrophe `&rsquo;` (' U+2019),
  opening double `&ldquo;` (" U+201C), closing double `&rdquo;` (" U+201D). The apostrophe is *always*
  the closing single quote (U+2019) and always points downward.[^butterickquotes][^butterickapostrophe]
  **Hard exception:** straight quotes/backticks in source code and some databases must stay literal
  (see [When NOT to flag](#when-not-to-flag-disconfirming-findings)).

### 8.2 Prime ′ / double-prime ″ vs apostrophe (feet/inches confusion)

- **DETECT:** Feet/inches or minutes/seconds set with **curly** quotes (`5'10"`, `8.5" × 14"` with
  comma-shaped marks). The reverse over-correction also occurs (a true apostrophe where a sloped prime
  is wanted).[^butterickfootinch]
- **RATE:** **Medium** (domain-dependent; conspicuous in specs, real-estate, recipes, dimensions).
- **FIX:** Butterick's *reliable* default for feet/inches is **straight quotes** (`'` U+0027, `"`
  U+0022) because true primes are rare in pro fonts; the typographically pure glyphs are prime
  `&prime;` (′ U+2032) and double-prime `&Prime;` (″ U+2033), sloping northeast-to-southwest. Present
  both; don't hard-fail straight quotes on measurements.[^butterickfootinch]

### 8.3 Hyphen `-` vs en dash `–` vs em dash `—`

- **DETECT:** a **hyphen used as a sentence break** (a short `-`, often spaced, or `--`/`---` doing an
  em dash's job); a **hyphen in a numeric range** (`1880-1912`) where an en dash belongs; a **slash
  where an en dash is correct**; a **crushed em dash** jammed against neighbors with no air. Dash
  *length* relative to a cap N/H is visible in a screenshot, so this is very detectable.[^butterickdashes]
- **RATE:** **Medium** (High in editorial/publishing).
- **FIX:** Hyphen `-` (U+002D) for compounds + line-break hyphenation. **En dash** `&ndash;` (– U+2013)
  for ranges ("to"/"through") and connections (Sarbanes–Oxley) — but "from" pairs with "to", not an en
  dash. **Em dash** `&mdash;` (— U+2014, ≈ width of a cap H; en dash ≈ half) for a parenthetical break
  "when a comma is too weak but a colon/semicolon/parentheses too strong."[^butterickdashes] **Spacing
  is style-dependent, not a fixed crime:** Chicago = unspaced em ("like this"); British = spaced en;
  Butterick allows spaces on screen to avoid crushing. Flag *inconsistency*, not the choice.[^butterickdashes][^cmosdashes]

### 8.4 Real small caps vs FAUX small caps

- **DETECT:** Small caps whose **vertical strokes are visibly too light/thin** relative to the
  surrounding full caps and lowercase — they look like shrunken full caps (too tall, too light, grayer/
  spindlier). Real small caps have strokes thickened so weight matches the text.[^dfhsmallcaps]
- **RATE:** **Medium** (a connoisseur's tell, but a real type crime).
- **FIX:** Use a font that *contains* true small caps and request OpenType `smcp`:
  `font-variant-caps: small-caps` (preferred) or `font-feature-settings: "smcp"`. **Caveat:**
  `font-variant: small-caps` historically *synthesized* fake small caps when the font lacked `smcp`;
  the reliable approach is to pick a font with true small caps AND set `font-synthesis: small-caps
  none` to *expose* (not hide) a missing feature. Re-verify real-vs-synthesized against the current
  target engine.[^mdnfontvariantcaps][^mdnfontsynthesis][^krycchosmallcaps]

### 8.5 Old-style vs lining figures; tabular vs proportional figures

- **DETECT (three tells):** **lining figures shouting in running text** — digits all at cap-height,
  standing out like small all-caps words amid lowercase ("look like SHOUTING"); **old-style figures in
  all-caps/UI** — lowercase-style digits with descenders sitting awkwardly next to capitals;
  **misaligned number columns** — proportional figures where tabular are needed, so price/table columns
  don't align vertically.[^mdnfontvariantnumeric][^harrellfigures]
- **RATE:** **Low–Medium** (Medium for the misaligned-column case in data tables; Low/Nit for
  figure-style mismatch in prose).
- **FIX:** `font-variant-numeric:` `oldstyle-nums` (`onum`) in running text; `lining-nums` (`lnum`) in
  all-caps + UI; `tabular-nums` (`tnum`) for columns that must align; `proportional-nums` (`pnum`) for
  flowing text. Combinable (e.g. `oldstyle-nums tabular-nums`). Requires a font that carries the
  figures. (Baseline "widely available" since Jan 2020.)[^mdnfontvariantnumeric]

### 8.6 Ligatures (fi, fl, ffi) — missing ligature & discretionary over-use

- **DETECT:** **Missing standard ligature** — in a serif/high-contrast face the **dot of the i collides
  with the hook/terminal of a preceding f** (or f crashes into l/second f) in "fi/fl/ffi/ffl," a
  visible overlap at large/display sizes; **over-use of discretionary ligatures** — ornate connected
  pairs (ct, st, swash Th) distracting in body text.[^myfontslig][^creativepro_lig][^batchelderlig]
- **RATE:** **Low** (Nit at text sizes; Medium at large display sizes where the collision is glaring).
- **FIX:** Enable common ligatures (default on) via `font-variant-ligatures: common-ligatures`
  (`liga`/`clig`); suppress discretionary with `no-discretionary-ligatures` (`dlig`); kill problem
  pairs with `none` or `font-feature-settings: "liga" 0`.[^mdnfontvariantligatures] **Special case:**
  ligatures in **programming/code fonts are a crime regardless** — a `=>` ligature shaped like ⇒
  misrepresents the code; disable in code views.[^butterickliga]

### 8.7 True bold/italic vs FAUX (synthetic) bold & italic

- **DETECT (highly detectable):** **faux italic** = mechanically slanted uprights (the roman 'a','f',
  'g' are oblique but keep their upright structure — double-story 'a' stays double-story; no true
  cursive forms; skew ≈ 14°). **faux bold** = strokes look smeared / uniformly outlined ("outlined with
  a magic marker"), clogged counters — worst is a **double-bolded** glyph (an already-bold font
  re-emboldened). Inspector tell: Safari's web-inspector Font pane warns when bolds are
  synthesized.[^alistapartfaux][^clagnutfaux]
- **Root cause:** applying `font-weight: bold`/`font-style: italic` when that cut isn't loaded, OR an
  `@font-face` rule mislabeling a bold file as `font-weight: normal` (so the browser bolds the
  bold).[^alistapartfaux][^smashingfaux][^clagnutfaux]
- **RATE:** **High** (one of the most common, most visible web type crimes).
- **FIX:** Load the real weight/style files and label `@font-face` correctly (`font-weight: 700`,
  `font-style: italic`) under one shared `font-family`. To *expose* the defect in critique, set
  `font-synthesis: none` (or granular `font-synthesis-weight: none` / `-style: none`) — the fake style
  then disappears, revealing the missing cut. (Baseline "widely available" since Jan 2022; default is
  synthesis ON.) Note: `none` has an a11y downside if the real cut isn't loaded (the style change
  silently vanishes), so it's a *diagnostic*; the *fix* is loading the real cut. For a variable font, a
  "missing weight" may be reachable via `font-variation-settings`/`font-weight` on the variable face,
  not a separate file.[^mdnfontsynthesis][^alistapartfaux][^clagnutfaux]

### 8.8 Multiplication sign × vs letter x; ellipsis … vs three periods; proper fractions

- **DETECT:** a lowercase **'x' used as a math operator/dimension** (`12 x 34`, `1920 x 1080`) instead
  of the centered, symmetric multiplication glyph; an **ellipsis** as three separate periods — jammed
  (`...`) or gapped (`. . .`) — or one that **wraps across a line**; a **faux fraction** (`1/2` on the
  baseline) instead of a proper fraction.[^butterickmath][^butterickellipses][^mdnfontvariantnumeric]
- **RATE:** **Low–Medium** (Medium for × in dimensional/data UI and the wrapping ellipsis; Low/Nit
  otherwise).
- **FIX:** Multiplication `&times;` (× U+00D7); minus `&minus;` (− U+2212, or an en dash); division
  `&divide;` (÷). Keep the letter x (U+0078) for x-ray/x-axis. Ellipsis `&hellip;` (… U+2026); if a
  house style mandates spaced periods, bind them with non-breaking spaces so they don't wrap. Proper
  fractions: `font-variant-numeric: diagonal-fractions` (`frac`) on a font that carries them, or the
  precomposed glyphs (½ U+00BD).[^butterickmath][^butterickellipses][^mdnfontvariantnumeric]

---

## 9. "Type crimes" — system-level defects

### 9.1 Stretched / condensed type (horizontal/vertical scaling)

- **DETECT:** **Distorted stroke contrast** — verticals and horizontals no longer in their designed
  proportion: stretched type shows thin verticals + normal horizontals (or vice-versa), round 'O'/'o'
  go oval/egg-shaped, a "fun-house" warp. In tools: InDesign/Illustrator Character panel **Horizontal
  or Vertical Scale ≠ 100%**; on web, `transform: scaleX()/scaleY()` on text. CreativePro: distorting
  type is "a type crime of the highest degree."[^creativepro_distort][^adobescale][^myfontscrimes]
- **RATE:** **High** (destroys letter integrity and costs legibility).
- **FIX:** Use a family's **true condensed/extended cut** (designed to keep weight contrast and
  proportions), never mechanical scaling. Reset scale to 100%.[^creativepro_distort][^adobescale]

### 9.2 Too many typefaces / "ransom note"

- **DETECT:** A single screen/page mixing **4+ unrelated families** (or many sizes/weights/colors of
  different faces) so it reads as a chaotic patchwork.[^design99crimes][^myfontscrimes]
- **RATE:** **Medium–High** (High when it destroys hierarchy/credibility).
- **FIX:** Rule of thumb **~2 families (one display + one body), max 3**, paired across a clear contrast
  (serif + sans, or script + sans).[^creativemarketrules] **Temper this:** the two/three-font rule is a
  *guideline, not a law* — flag *unintentional/clashing* multiplicity, not a deliberate, well-contrasted
  3–4-face system. The crime is incoherence, not the count (see [When NOT to flag](#when-not-to-flag-disconfirming-findings)).[^myfontspairing]

### 9.3 Fonts that clash / insufficient contrast between fonts

- **DETECT:** two families **too similar to read as intentional** (two humanist sans, two geometric
  sans) producing a "did they mean that?" wobble; OR historically/aesthetically incompatible pairings
  with no shared contrast.[^sketchdeckpair]
- **RATE:** **Low–Medium.**
- **FIX:** Pair on *clear* contrast (classification, x-height, structure) while sharing a mood;
  superfamilies or a serif/sans designed together are safe.[^sketchdeckpair]

### 9.4 Centering long body text

- **DETECT:** Multi-line paragraphs where **every line starts at a different horizontal position**
  (ragged left edge), forcing the eye to hunt for each new line. WebAIM: centered long blocks introduce
  reading overhead.[^webaimlayout]
- **RATE:** **Medium** (High for long passages / accessibility).
- **FIX:** Left-align (LTR) running text; reserve centering for short headings, captions, a date, or
  single lines.[^webaimlayout]

### 9.5 Underlining for emphasis (vs italic)

- **DETECT:** Underlined words mid-paragraph used for *emphasis* (not links) — a typewriter habit that
  on the web also collides with the link convention (looks clickable) and cuts through descenders.[^webstyleguideemphasis][^nngformatting]
- **RATE:** **Medium** (Medium-High on web because it impersonates links).
- **FIX:** Use **italic** (or bold for stronger/heading emphasis); reserve underline for hyperlinks.
  Emphasis sparingly (NN/g: bold ≤30% of text).[^webstyleguideemphasis][^nngformatting]

### 9.6 All-caps for long passages

- **DETECT:** Sentences/paragraphs (not short labels) set entirely in capitals — uniform rectangular
  word-shapes with no ascenders/descenders, defeating word-shape recognition.[^wikiallcaps][^teamwcaps]
- **RATE:** **Medium** (legibility + accessibility cost; **Low** for short headings/labels where it's
  fine).
- **FIX:** Use sentence/mixed case for any multi-word passage; limit all-caps to short
  headings/labels/acronyms; if used, add tracking (§3.2). **Temper:** the "all caps is inherently
  harder to read" claim is partly a familiarity/size effect that vanishes at large sizes — flag
  all-caps **long passages**, not short display caps (harm is real for long passages, dyslexic readers,
  and 55+ readers).[^teamwcaps][^wikiallcaps]

### 9.7 Default / system everything

- **DETECT:** Unstyled browser/app defaults — Times/Arial/system-ui body, default sizes/weights/spacing,
  straight quotes, hyphen-dashes — signaling no typographic intent.[^myfontscrimes][^design99crimes]
- **RATE:** **Low–Medium** (Nit for a quick utility; Medium for anything brand/customer-facing).
- **FIX:** Set an intentional type stack, scale, and the §8 micro-typography (curly quotes, real dashes,
  proper figures, ligatures).

### 9.8 Justification without hyphenation

Named here; the mechanics live in **§6.1** (loose lines) and rivers in **§2.3**. WebAIM: fully-justified
text impairs readability and creates "rivers of white."[^webaimlayout]

---

## Quick-scan checklist

Run top-to-bottom on a screenshot; each maps to a section above.

1. **Glyphs** (§8): straight quotes? hyphen-as-dash? faux bold/italic (smeared/slanted)? lining figures
   shouting in body? misaligned number columns? `12 x 34` instead of `×`?
2. **Faux styles** (§8.4, §8.7): small caps too light? bold smeared / italic just slanted?
3. **Kerning/tracking** (§3): uneven display pairs / "keming"? all-caps with no tracking? loose big
   headline? letter-spaced lowercase body?
4. **Leading** (§4): lines touching (too tight) or striping (too loose)? jittery block-to-block rhythm?
5. **Measure** (§5): full-bleed body wider than ~90 chars? a column narrower than ~40?
6. **Justification / rag** (§6, §2): loose lines/rivers in justified text? lumpy rag? hyphen ladder?
7. **Breaks** (§1, §2.4): one-word runt last line? widow/orphan at a column break? stranded subhead?
   broken name / number+unit / URL?
8. **Optical** (§7): un-hung opening quote making a flush edge look indented? a scaled single optical
   size?
9. **Type crimes** (§9): stretched/condensed (scale ≠ 100%)? 4+ clashing fonts? centered long body?
   underline-for-emphasis? all-caps paragraph?

## CSS micro-typography cheat-sheet

(Support stamps verified-as-of 2026-06-16.)

- **Curly quotes / dashes / ×/…** — author the real glyph/entity (§8); no CSS toggle.
- `font-kerning: normal` — force built-in pair kerning (§3.1).
- `letter-spacing: 0.05–0.12em` (caps) / `-0.01–-0.03em` (display) / `normal` (body) (§3.2–3.5).
- `line-height: <unitless ~1.4–1.6>` body; `1.1–1.3` headings; multiple of base unit for rhythm (§4).
- `max-width: 66ch` / `width: min(66ch, 100%)` — constrain measure (§5).
- `text-align: justify; hyphens: auto;` + `<html lang>` — only justify *with* hyphenation (§6); `hyphens` Baseline since Sept 2023, `lang`/dictionary-dependent.
- `text-wrap: pretty` — fix runts/rag (engine-divergent: Chromium last ~4 lines, WebKit whole paragraph); `text-wrap: balance` — even short headlines (§1.3, §2.5).
- `widows` / `orphans` — paged/multicol only; **no effect in normal web flow**; unsupported in Firefox (§1.5).
- `break-after: avoid` / `break-inside: avoid` — keep a subhead with its body (paged/multicol) (§1.4).
- `font-variant-caps: small-caps` + `font-synthesis: small-caps none` — real small caps, expose faux (§8.4).
- `font-variant-numeric: oldstyle-nums | lining-nums | tabular-nums | proportional-nums | diagonal-fractions` (§8.5, §8.8); Baseline since Jan 2020.
- `font-variant-ligatures: common-ligatures | no-discretionary-ligatures | none` (§8.6).
- `font-synthesis: none` — expose faux bold/italic (diagnostic, not the fix); Baseline since Jan 2022 (§8.7).
- `hanging-punctuation: first` — **Safari-only**; use negative `text-indent` fallback (§7.1).
- `font-optical-sizing: auto` (default) / `font-variation-settings: 'opsz' <n>` — opsz; Baseline since Mar 2020 (§7.3).

## When NOT to flag (disconfirming findings)

Micro-typography critique fails when it applies rules as dogma. Hold fire when:

1. **Widow/orphan labels** — don't assert which is "worse" or rely on the label; sources reverse the
   definitions and disagree on severity. Describe the position.[^widoworphan][^fontfabricorphan]
2. **Paged widows/orphans on the responsive web** — the *paged* widow/orphan is a print problem; the
   web's real version is the **runt**, a minor defect best fixed with `text-wrap: pretty`. Don't flag
   classic page-widow control on a flowing single-column article.[^butterickwidow][^bootstrapwidow]
3. **Rag depth alone** — a deeper "hard rag" can beat a tight rag bought with bad breaks/excess
   hyphenation (Bringhurst). Flag *accidental shapes* and *wild swings*, not depth per se.[^webtyporag]
4. **Manual kerning in body copy** — built-in/automatic kerning suffices for body and most UI; reserve
   High/Blocker kerning findings for logos, wordmarks, and large display.[^buttericckern][^clagnutmanual]
5. **Baseline-grid misalignment** — a baseline grid "does not automatically create good vertical
   rhythm" and often "has no meaning" on the responsive web; prioritize a consistent 4/8px spacing scale
   over true baseline snapping. Rate Low–Medium.[^vanseobaseline]
6. **The 45–75/66 CPL rule** — it's a strong design *convention*, but reading-speed research is mixed
   (one study read fastest at 95 CPL; the return-sweep mechanism is questioned; short lines help
   struggling/dyslexic readers). Flag out-of-band *extremes*, not every line ≠ 66.[^designregression][^uxpinline]
7. **Justified text per se** — it's a personal-preference choice, not an automatic crime; it works at
   narrow measures (newspaper columns) and in InDesign with the Paragraph Composer + hyphenation. The
   defect is *justified-on-the-web-without-hyphenation* or *justified-narrow-measure*.[^butterickjustified][^adamsjustify]
8. **`hanging-punctuation`** — Safari-only, so an un-hung quote edge is at most a Nit on the web;
   recommend the negative-`text-indent` fallback, don't rate it highly.[^mdnhanging][^coyierhanging]
9. **Tight leading** — correct for headings/display (1.1–1.3) and single-line elements (buttons, nav,
   rows, even `line-height: 1`); only flag tight leading on multi-line running text.[^applehig][^ultimateline]
10. **Curly quotes / em-dash spacing / straight-quote primes** — curly quotes are *wrong* in code and
    some databases; em/en-dash spacing is style-dependent (Chicago unspaced em vs British spaced en);
    straight quotes are Butterick's *practical* default for feet/inches. Flag *inconsistency*, not the
    legitimate choice.[^butterickquotes][^cmosdashes][^butterickfootinch]

---

## References

[^widoworphan]: Wikipedia, "Widows and orphans" — standard mnemonics; explicit "no consistent standard," runt also called widow/orphan. https://en.wikipedia.org/wiki/Widows_and_orphans (encyclopedia)
[^mdnwidows]: MDN, CSS `widows` — min lines at top of a fragment; initial 2; block containers; fragmentation-only. https://developer.mozilla.org/en-US/docs/Web/CSS/widows (docs)
[^mdnorphans]: MDN, CSS `orphans` — min lines at bottom of a fragment; initial 2; fragmentation-only. https://developer.mozilla.org/en-US/docs/Web/CSS/orphans (docs)
[^butterickwidow]: Butterick, *Practical Typography* — "Widow and orphan control": defs (widow=top, orphan=bottom), widows more distracting, all-or-nothing control, "not applicable" to web, the runt. https://practicaltypography.com/widow-and-orphan-control.html (book)
[^fontfabricorphan]: Fontfabric, "Orphan Typography" (2025) — REVERSED defs (orphan=top, widow=bottom); Keep Options fix; "orphan more jarring" view. https://www.fontfabric.com/blog/orphan-typography/ (blog/foundry)
[^butterickhardbreak]: Butterick, *Practical Typography* — "Hard line breaks": don't fix breaks/widows with hard line breaks. https://practicaltypography.com/hard-line-breaks.html (book)
[^butterticknbsp]: Butterick, *Practical Typography* — "Nonbreaking spaces": `&nbsp;` for names, titles, number/symbol+reference; avoid `<br>`. https://practicaltypography.com/nonbreaking-spaces.html (book)
[^adobekeep]: Adobe InDesign Help — Keep Options (Keep Lines Together, Keep with Next N Lines). https://helpx.adobe.com/indesign/using/text-composition.html (docs/vendor)
[^bookhouserunt]: Bookhouse / ebookpbook / printedpagestudios — the "runt" = short last line anywhere (not at a break), distinct from a widow. https://bookhouse.com.au/article/widows (blog)
[^chrometextwrap]: Chrome for Developers — `text-wrap: pretty` = re-evaluates the last ~4 lines (short-last-line + trailing-hyphen focus); perf model. https://developer.chrome.com/blog/css-text-wrap-pretty (docs/vendor)
[^webkittextwrap]: WebKit blog (Jen Simmons, 2025), "Better Typography with text-wrap: pretty" — full scope (short last lines, rag, hyphenation; NOT rivers), Chromium-vs-WebKit divergence, balance behavior, perf. https://webkit.org/blog/16547/better-typography-with-text-wrap-pretty/ (docs/vendor)
[^mdntextwrap]: MDN, CSS `text-wrap` / `<wbr>` / `&shy;` — values & wrap-control elements. https://developer.mozilla.org/en-US/docs/Web/CSS/text-wrap (docs)
[^bootstrapwidow]: Bootstrap Creative / Medium / UX Movement — responsive-web widow/runt debate; avoid `<br>`. https://www.bootstrapcreative.com/ (blog)
[^smashingfrag]: Smashing Magazine, "Breaking Boxes With CSS Fragmentation" — widows/orphans/break-* act only across fragmentation breaks; stranded subheads. https://www.smashingmagazine.com/2019/02/css-fragmentation/ (blog)
[^mdnbreak]: MDN, CSS `break-after` / `break-inside` — `avoid` to keep a heading with its body; support notes. https://developer.mozilla.org/en-US/docs/Web/CSS/break-after (docs)
[^mdnfrag]: MDN, "CSS fragmentation" — fragmentation contexts (paged, multicol, regions). https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_fragmentation (docs)
[^caniusewidows]: caniuse, "css-widows-orphans" (cross-checked Mozilla Bugzilla #137367) — Blink + WebKit supported; Firefox unsupported. https://caniuse.com/css-widows-orphans (docs/data)
[^goodpage]: The Good Page / fathom.info "It's Rag Time" — good vs bad rag (small increments vs accidental shapes). https://fathom.info/notebook/13855/ (blog)
[^myfontsrag]: MyFonts/Fonts.com Fontology, "Rags, Widows & Orphans" — rag quality. https://www.myfonts.com/pages/fontscom-learning-fontology (blog)
[^adobebalance]: Adobe InDesign community — Balance Ragged Lines, No Break; overrides (justification, Keep, trailing spaces). https://community.adobe.com/ (forum/vendor)
[^runragged]: 24ways (Mark Boulton circle), "Run Ragged" — bad-rag rules: no breaks after prepositions/dashes, ≤2 consecutive hyphens, no 2–3-letter words at line ends; `&nbsp;`/`<wbr>`/`&shy;`/`hyphens`. https://24ways.org/2013/run-ragged/ (blog)
[^webtyporag]: *The Elements of Typographic Style Applied to the Web* §2.1.3 (Bringhurst applied) — may prefer the greater variations of a hard rag over an over-hyphenated tight rag. http://webtypography.net/2.1.3 (book/online)
[^mlarivers]: MLA Style Center, "Rivers and Ladders" + Fonts.com H&J — hyphenation ladder thresholds vary (2/3/4). https://style.mla.org/rivers-and-ladders/ (blog)
[^wikiriver]: Wikipedia, "River (typography)" — rivers def; justified/narrow/monospace cause; upside-down + squint tests. https://en.wikipedia.org/wiki/River_(typography) (encyclopedia)
[^opusriver]: Opus Design / Alchetron — rivers detection (upside-down, squint, distance). https://opusdesign.us/ (blog)
[^creativepro_river]: CreativePro, "A River Runs Through It" (+ widespacer) — rivers invisible on screen yet obvious in print; "long rivers unlikely in ordinary text" (skeptic nuance). https://creativepro.com/ (blog)
[^webtyporiver]: *Elements of Typographic Style Applied to the Web* §2.x — set ragged to avoid rivers from stretched justified spacing. http://webtypography.net/ (book/online)
[^logrockettextwrap]: LogRocket / modern-css — `text-wrap: balance` vs `pretty` (use, support; `pretty` handles runts not paged widows). https://blog.logrocket.com/css-text-wrap-balance-vs-text-wrap-pretty/ (blog)
[^buttericckern]: Butterick, *Practical Typography* — "Kerning": kerning def (pair-specific), distinct from letterspacing, built-in fine for non-pros. https://practicaltypography.com/kerning.html (book)
[^wikikern]: Wikipedia, "Kerning" — keming; overhang pairs T/Y/V/A; A & V as space negatives. https://en.wikipedia.org/wiki/Kerning (encyclopedia)
[^butterickletterspace]: Butterick, *Practical Typography* — "Letterspacing": 5–12% (0.05–0.12em) caps tracking; no tracking on lowercase; default body fine; size↔tracking; "gone overboard" test. https://practicaltypography.com/letterspacing.html (book)
[^wikiletterspace]: Wikipedia, "Letter spacing" / "Spacing (typography)" — uniform adjustment def. https://en.wikipedia.org/wiki/Letter_spacing (encyclopedia)
[^explainkern]: explainxkcd 1015 + Superside — "keming" origin; rn→m, burn→bum. https://www.explainxkcd.com/wiki/index.php/1015:_Kerning (blog)
[^sitepointtracking]: SitePoint / typography.guru — larger type needs less tracking; negative tracking for headings. https://www.sitepoint.com/spaced-out-tracking-in-typography/ (blog)
[^mdnfontkerning]: MDN, CSS `font-kerning` — values auto/normal/none; `auto` may disable at small sizes. https://developer.mozilla.org/en-US/docs/Web/CSS/font-kerning (docs)
[^cssfontkerning]: CSS-Tricks Almanac, `font-kerning` — corroborates values/behavior. https://css-tricks.com/almanac/properties/f/font-kerning/ (blog)
[^clagnutmanual]: Clagnut + Art Equals Work + MDN `text-rendering` — cross-browser kerning (Safari needs optimizeLegibility, Firefox auto ≥20px); manual span+letter-spacing method; perf caveat. https://clagnut.com/blog/2370 (blog)
[^mdnletterspacing]: MDN, CSS `letter-spacing` — normal/length (em); large negative makes text unreadable; disables liga/clig. https://developer.mozilla.org/en-US/docs/Web/CSS/letter-spacing (docs)
[^butterickallcaps]: Butterick, *Practical Typography* — "All caps": always add letterspacing to caps, keep kerning on. https://practicaltypography.com/all-caps.html (book)
[^figrtracking]: Figr / Webdesigner Depot — inverse size/tracking relationship. https://figr.design/blog/tracking-design-typography-differences (blog)
[^applehig]: Apple Human Interface Guidelines — Typography: loose-vs-tight leading; avoid tight leading for 3+ lines; system font auto-adjusts tracking per point size. https://developer.apple.com/design/human-interface-guidelines/typography (docs/vendor)
[^kevinletterspace]: Kevin Powell + NCBI PMC7090332 — don't letter-space lowercase (Goudy "steal sheep," blackletter caveat); study: wider spacing helps word processing but slows fast readers. https://www.kevinpowell.co/article/letter-spacing-dos-and-donts/ (blog/paper)
[^googleleading]: Google Fonts Knowledge — leading vs line-height definition. https://fonts.google.com/knowledge/glossary/line_height_leading (docs/vendor)
[^damatoline]: damato.design "Relearning line-height" + edgdesign baseline grids — line-height boxes text (not baseline); baseline-trim/basekick remedies. https://blog.damato.design/posts/relearning-line-height/ (blog)
[^fontfabricdesc]: Fontfabric / NumberAnalytics — too-tight leading → descender/ascender clash; body 1.4–1.6. https://www.fontfabric.com/blog/ (blog)
[^pimplineheight]: Pimp My Type, "Line length & line height" — body ~1.4–1.6; longer lines need more line height. https://pimpmytype.com/line-length-line-height/ (blog)
[^buttericklinespacing]: Butterick, *Practical Typography* — "Line spacing": optimal 120–145% of point size; 110% too tight / 170% too loose. https://practicaltypography.com/line-spacing.html (book)
[^unitlessline]: MDN `line-height` + 30 Seconds of Code — unitless = multiplier of font-size; preferred for inheritance (recomputes per element). https://developer.mozilla.org/en-US/docs/Web/CSS/line-height (docs)
[^bringhurst]: *The Elements of Typographic Style Applied to the Web* (Bringhurst applied) + Wikipedia "Leading" — more leading for longer measures, sans-serif, larger x-height. http://webtypography.net/ (book/online)
[^nnglegibility]: Nielsen Norman Group, "Legibility, Readability, and Comprehension" — longer lines need wider line-height (1.4–1.6em); legibility fundamentals. https://www.nngroup.com/articles/legibility-readability-comprehension/ (docs/research org)
[^ultimateline]: Ultimate Design Tools / Material — headings 1.1–1.3; single-line elements can use line-height 1. https://ultimatedesigntools.com/tools/line-height-calculator/ (blog)
[^materialgrid]: Material Design, "Understanding layout" (m2) — 8dp layout grid, 4dp baseline grid; line-height a multiple of base unit (15px→24px). https://m2.material.io/design/layout/understanding-layout.html (docs/vendor)
[^vanseobaseline]: Vanseo Design + Imperavi UI Typography — baseline grid doesn't auto-create rhythm; little meaning in responsive web; "guide, not restraint." https://vanseodesign.com/web-design/baseline-grids-web/ (blog)
[^wcagtextspacing]: W3C, WCAG 2.2 Understanding SC 1.4.12 Text Spacing (AA) — line-height 1.5×, para 2×, letter 0.12×, word 0.16×; "content is not required to use these values." https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html (docs/standard, verified-as-of 2026-06-16)
[^dequetextspacing]: Deque University — corroborates 1.4.12 thresholds. https://dequeuniversity.com/resources/wcag2.1/1.4.12-text-spacing (docs)
[^buttericklinelength]: Butterick, *Practical Typography* — "Line length": 45–90 chars; measure in CPL not inches; point-size independence. https://practicaltypography.com/line-length.html (book)
[^webtypomeasure]: *Elements of Typographic Style Applied to the Web* §2.1.2 — verbatim Bringhurst (45–75 / 66 ideal / 40–50 multi-column); elastic em widths. http://webtypography.net/2.1.2 (book/online)
[^baymardline]: Baymard Institute, "Readability: The Optimal Line Length" — 50–75 CPL; wide lines skipped/skimmed; return-sweep difficulty. https://baymard.com/blog/line-length-readability (docs/UX research)
[^uxpinline]: UXPin, "Optimal Line Length for Readability" — NN/g + WCAG synthesis; mobile 30–50 CPL; 66 as a starting point not a law. https://www.uxpin.com/studio/blog/optimal-line-length-for-readability/ (blog)
[^wcagvisualpres]: W3C, WCAG SC 1.4.8 Visual Presentation — 80-character max (40 CJK). https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html (docs/standard)
[^csstricksmeasure]: CSS-Tricks, "Setting Line Length in CSS" — `max-width` in `ch`, `clamp()/min()` responsive. https://css-tricks.com/setting-line-length-in-css-and-fitting-text-to-a-container/ (blog)
[^designregression]: design regression / Slattery & Vasilev / Dyson & Haselgrove — disconfirming: ~95 CPL read fastest; return-sweep mechanism questioned; comprehension unaffected. https://designregression.com/article/line-length-revisited-following-the-research (blog/paper)
[^butterickjustified]: Butterick, *Practical Typography* — "Justified text": hyphenation required ("gruesomely large spaces"); left-align on web; not a professionalism signifier. https://practicaltypography.com/justified-text.html (book)
[^maxwelljustify]: Maxwell Forbes, "Don't Justify Web Text" + Design for Hackers — browsers only stretch word-spacing; gaps/rivers; ragged easier to track. https://maxwellforbes.com/posts/web-justified-text/ (blog)
[^adobecompose]: Adobe InDesign Help — "Compose / hyphenate text": Paragraph vs Single-line Composer; hyphenation for justified short measures; Limit Consecutive Hyphens. https://helpx.adobe.com/indesign/using/text-composition.html (docs/vendor)
[^mdnhyphens]: MDN, CSS `hyphens` — none/manual/auto; `lang` + dictionary required; Baseline since Sept 2023, varying support. https://developer.mozilla.org/en-US/docs/Web/CSS/hyphens (docs)
[^wikihanging]: Wikipedia, "Hanging punctuation" / "Optical margin alignment" — def, exdentation, visual-hole rationale. https://en.wikipedia.org/wiki/Hanging_punctuation (encyclopedia)
[^creativepro_hang]: CreativePro / MyFonts — "Hung Punctuation & Optical Margin Alignment" in InDesign (Story panel; hangs serifs + punctuation; font-size = overhang). https://creativepro.com/typetalk-hung-punctuation-optical-margin-alignment/ (blog)
[^mdnhanging]: MDN, CSS `hanging-punctuation` — first/last/force-end/allow-end; "Limited availability / not Baseline." https://developer.mozilla.org/en-US/docs/Web/CSS/hanging-punctuation (docs)
[^caniusehanging]: caniuse, "css-hanging-punctuation" — Safari-only support. https://caniuse.com/css-hanging-punctuation (docs/data)
[^coyierhanging]: Chris Coyier, "The hanging-punctuation property in CSS" — Safari-only; progressive enhancement; negative-text-indent fallback. https://chriscoyier.net/2023/11/27/the-hanging-punctuation-property-in-css/ (blog)
[^adobekerntrack]: Adobe InDesign Help — "Kerning and tracking": Metrics vs Optical kerning. https://helpx.adobe.com/indesign/using/kerning-tracking.html (docs/vendor)
[^creativepro_metricvsoptical]: CreativePro, "Metrics Versus Optical Kerning" — when to use each. https://creativepro.com/typetalk-metrics-versus-optical-kerning/ (blog)
[^mdnopticalsizing]: MDN, CSS `font-optical-sizing` — auto/none; opsz; display vs text rendering; Baseline since March 2020. https://developer.mozilla.org/en-US/docs/Web/CSS/font-optical-sizing (docs)
[^googleopsz]: Google Fonts Knowledge "Optical Size axis" + Type Network "The magic of optical size" — body vs display design differences. https://fonts.google.com/knowledge/glossary/optical_size_axis (docs/vendor)
[^butterickquotes]: Butterick, *Practical Typography* — "Straight and curly quotes": straight vs curly, "never, ever" rule, code-syntax exception. https://practicaltypography.com/straight-and-curly-quotes.html (book)
[^butterickapostrophe]: Butterick, *Practical Typography* — "Apostrophes": apostrophes point down (U+2019), opening-quote-vs-apostrophe error. https://practicaltypography.com/apostrophes.html (book)
[^butterickfootinch]: Butterick, *Practical Typography* — "Foot and inch marks": use straight quotes; prime escape codes `&prime;`/`&Prime;`; sloped primes. https://practicaltypography.com/foot-and-inch-marks.html (book)
[^butterickdashes]: Butterick, *Practical Typography* — "Hyphens and dashes": HTML entity table, en/em function split, spacing latitude, slash misuse. https://practicaltypography.com/hyphens-and-dashes.html (book)
[^cmosdashes]: CMOS Shop Talk, "Hyphens and Dashes: A Refresher" (2024) — Chicago = unspaced em; British = spaced en (spacing style-dependent). https://cmosshoptalk.com/2024/01/23/hyphens-and-dashes-a-refresher/ (blog)
[^dfhsmallcaps]: Design for Hackers, "Use Real Small Caps" — fake small caps too tall / strokes too light. https://designforhackers.com/blog/small-caps/ (blog)
[^mdnfontvariantcaps]: MDN, CSS `font-variant-caps` — `smcp`, small-caps fallback. https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-caps (docs)
[^mdnfontsynthesis]: MDN, CSS `font-synthesis` — none/weight/style/small-caps/position; default ON; Baseline since Jan 2022. https://developer.mozilla.org/en-US/docs/Web/CSS/font-synthesis (docs)
[^krycchosmallcaps]: Chris Krycho, "CSS Fallback for OpenType Small Caps" — `font-variant: small-caps` synthesizes fake small caps. https://v4.chriskrycho.com/2015/css-fallback-for-opentype-small-caps.html (blog)
[^mdnfontvariantnumeric]: MDN, CSS `font-variant-numeric` — value→OT-tag table (onum/lnum/tnum/pnum/frac); Baseline since Jan 2020. https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric (docs)
[^harrellfigures]: Jonathan Harrell, "Better Typography with Font Variants" — old-style vs lining vs tabular usage. https://www.jonathanharrell.com/blog/better-typography-with-font-variants/ (blog)
[^myfontslig]: MyFonts/Fonts.com, "Ligatures Part 1 (Standard)" — standard f-ligature set, collision cause. https://www.myfonts.com/pages/fontscom-learning-fontology-level-3-signs-and-symbols-ligatures-1 (blog)
[^creativepro_lig]: CreativePro, "The Ins and Outs of F-ligatures" — fi/fl collision rationale. https://creativepro.com/typetalk-the-ins-and-outs-of-f-ligatures/ (blog)
[^batchelderlig]: Ned Batchelder, "Lato's unfortunate ligatures" — ligatures jarring on fonts that don't need them. https://nedbatchelder.com/blog/201604/latos_unfortunate_ligatures.html (blog)
[^mdnfontvariantligatures]: MDN, CSS `font-variant-ligatures` — common/discretionary/none; `liga`/`clig`/`dlig`. https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-ligatures (docs)
[^butterickliga]: Butterick, *Practical Typography* — "Ligatures in programming fonts: hell no" — code-ligature ambiguity crime. https://practicaltypography.com/ligatures-in-programming-fonts-hell-no.html (book)
[^alistapartfaux]: A List Apart, "Say No to Faux Bold" (Stearns, 2012) — faux faces from @font-face misuse; faux-bold smear; double-bold. https://alistapart.com/article/say-no-to-faux-bold/ (blog)
[^clagnutfaux]: Clagnut / Richard Rutter, "Beware the faux bold" (2025) — double-bold tell; Safari inspector warning; @font-face weight fix. https://clagnut.com/blog/2438 (blog)
[^smashingfaux]: Smashing Magazine, "Avoiding Faux Weights and Styles with Google Web Fonts" (2012) — corroborates faux-face cause. https://www.smashingmagazine.com/2012/07/avoiding-faux-weights-styles-google-web-fonts/ (blog)
[^butterickmath]: Butterick, *Practical Typography* — "Math symbols": `&times;`/`&minus;`/`&divide;`; × in dimensions; x-vs-× table. https://practicaltypography.com/math-symbols.html (book)
[^butterickellipses]: Butterick, *Practical Typography* — "Ellipses": single … glyph, too-close/too-far tells, nonbreaking-space remedy. https://practicaltypography.com/ellipses.html (book)
[^creativepro_distort]: CreativePro, "Why Distorting Type Is a Crime" — "highest degree" crime; use true width cuts. https://creativepro.com/typetalk-why-distorting-type-crime/ (blog)
[^adobescale]: Adobe InDesign Help — "Scale and skew type": 100% = unscaled; scaling distorts; prefer true condensed/expanded. https://helpx.adobe.com/indesign/using/scale-skew-type.html (docs/vendor)
[^myfontscrimes]: MyFonts/Fonts.com, "Top Ten Type Crimes" — distortion, ransom-note, defaults. https://www.myfonts.com/pages/fontscom-learning-fyti-typographic-tips-top-ten-type-crimes (blog)
[^design99crimes]: 99designs, "Typography crimes to stop committing" — ransom note, all-caps, distortion. https://99designs.com/blog/tips/13-type-crimes-to-stop-committing/ (blog)
[^creativemarketrules]: Creative Market, "Typography Rules" — 2–3 font max; "second law: nobody follows the first." https://creativemarket.com/blog/typography-rules (blog)
[^myfontspairing]: MyFonts, "Busting the myths about font pairing" — two-font rule is a guideline; study the type. https://www.myfonts.com/ (blog)
[^sketchdeckpair]: SketchDeck / Tuts+ — pair on clear contrast; too-similar pairings look accidental. https://sketchdeck.com/ (blog)
[^webaimlayout]: WebAIM, "Text/Typographical Layout" — centered-text reading overhead; justification "rivers." https://webaim.org/techniques/textlayout/ (docs/accessibility)
[^webstyleguideemphasis]: Web Style Guide, "Typographic Emphasis" — italic for emphasis, underline for links, caps least effective. https://www.webstyleguide.com/wsg3/8-typography/5-typographic-emphasis.html (book/online)
[^nngformatting]: Nielsen Norman Group, "Formatting Long-Form Content" — bold/highlight ≤30%, used sparingly. https://www.nngroup.com/articles/formatting-long-form-content/ (docs/research org)
[^wikiallcaps]: Wikipedia, "All caps" — 20th-c. legibility studies + the 2007 large-size exception. https://en.wikipedia.org/wiki/All_caps (encyclopedia)
[^teamwcaps]: The Team W, "It's a Myth That All Caps Are Inherently Harder to Read" (2009/2017) — caps deficit is practice/size-dependent; harm in long passages, dyslexic, 55+. https://www.blog.theteamw.com/2009/12/23/ (blog)
[^adamsjustify]: Adams Drafting / Cutting Edge PR / Wikipedia "Typographic alignment" — when justified beats ragged (narrow newspaper columns). https://www.adamsdrafting.com/ (blog)
