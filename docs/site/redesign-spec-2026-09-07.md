# Redesign spec — Home page & primary nav (2026-09-07)

Answers `docs/site/ux-audit-2026-09-07.md` (F1–F8). Implementation targets:
`site/src/pages/index.astro`, `site/src/layouts/Base.astro`, `site/src/styles/global.css`.
Tracking contract adopted verbatim from `docs/site/measurement-plan-2026-09-07.md` §2.
Every string below is final copy — build it as written.

## 1. Trade-off chosen

I optimised for **one message, one primary action, and a routed second click**, and gave up
**equal-weight completeness across the seven cards**. The audit's three highest-impact findings
(F2 value prop, F3 choice overload, F4 no primary CTA) point the same way: the page is a menu,
not an argument. So the hero carries a plain-language definition of `llms.txt` plus exactly two
buttons (`cta-design-technical-audiences`: 1 CTA → 3.8% CTR, 2 CTAs → 4.0% total, 3+ →
2.4–2.8%), and the seven cards are re-tiered 3 + 4 rather than deleted. I also chose a **persona
strip over a single message** (F1), accepting its choice cost because the audit shows three
genuinely different entry questions. The compensating discipline: the strip is three plain
links, not three cards, and its destinations are disjoint from the hero CTAs — no slot is spent
twice.

**Primary CTA = `/downloads/`, not `/tree/`.** The persona strip already routes each visitor to
*their* explore surface, so the hero's one button must be the shared, most-committing act the
strip does not cover — getting the tooling. It is also the only "apply" click with zero friction
(`npx skills add …`, no account), unlike `/playground/optimizer/`, which needs an API key with
`run` scope and would over-claim in the hero.

**Kept from the audit's "what to keep":** every live figure, the honest "N of M" framing, the
`.md` twins and `/family/` reader, the no-JS `<details>` Skills menu, and no urgency devices.

## 2. Page IA (top to bottom)

| # | Block | Purpose | Findings | Funnel |
|---|---|---|---|---|
| 1 | Header/nav (`Base.astro`) | Persistent routing; Tree, Directory, Skills promoted | F6 | all |
| 2 | `<h1>` "LLMS-Explorer" (unchanged, `Base.astro:71`) | Site identity | — | learn |
| 3 | Eyebrow | Frame without ambiguity | 10-s test | learn |
| 4 | Lede (= `description`) | Plain definition of `llms.txt` | F2 | learn |
| 5 | Supporting line (positioning) | The mechanism, as secondary | F2 | learn |
| 6 | Hero actions — 1 primary + 1 secondary `.btn` | One salient default | F4, F3 | apply / explore |
| 7 | Proof line | Live counts promoted out of card footers | F5, F7 | learn |
| 8 | "Who this is for" strip — 3 links | Self-identification | F1 | explore |
| 9 | Zone A "Explore the corpus" — 3 full-weight cards | Live-data surfaces | F3, F8 | explore |
| 10 | Zone B "Read the reference" — 4 compact cards | Depth on demand | F3, F8 | learn |
| 11 | Zone C "Apply it to your own files" — 3 links | Install / account | F4, F8 | apply |
| 12 | Site footer (`Base.astro`) | Dog-food claim | — | — |

## 3. Hero block — final copy

- **Eyebrow** (`<p class="eyebrow">`): `The llms.txt standard, in practice`
  (replaces "worked", which the audit found ambiguous).
- **h1** — **unchanged: `title = "LLMS-Explorer"`.** The h1 renders from the `title` prop
  (`Base.astro:71`) and that same const feeds `<title>… · LLMS-Explorer</title>`, the canonical
  page name in the generated `/llms.txt`, and the sitemap. The audit's own fix for F2 is a lede
  fix, not an h1 fix; changing it would ripple into generator output that is out of scope.
- **Lede / `description`** (one sentence, 153 chars — exact string, used verbatim in both the
  `description` const and `<p class="lede">`):

  `llms.txt tells AI agents what a site contains; LLMS-Explorer grades the files already published and maps every concept behind them in one browsable tree.`

- **Supporting line** (`<p class="hero-support">`):
  `The concept tree is the map; llms files are the territory; the site keeps the two in agreement.`
- **Primary CTA**: `<a class="btn" href="/downloads/" data-track="home_cta_click" data-cta-id="get-tools" data-destination="/downloads/">Get the skills and CLI</a>`
- **Secondary CTA**: `<a class="btn secondary" href="/tree/" data-track="home_cta_click" data-cta-id="browse-tree" data-destination="/tree/">Browse the concept tree</a>`

Both labels use the skill's Pattern 1 (action verb + outcome); neither invents urgency.

## 4. "Who this is for" self-selection strip — final copy

Renders as a `<ul class="personas">` of **links** (not buttons — buttons imply state change, and
`cta-design-technical-audiences` reserves buttons for the primary action). Each `<li>` holds one
`<a>` containing a `<strong>` label and a `<span class="p-outcome">` outcome.

| Label (`<strong>`) | Outcome (`<span class="p-outcome">`) | href | `data-cta-id` |
|---|---|---|---|
| `Publishing your first llms.txt` | `Read the rubric a file is graded against.` | `/reference/` | `persona-publish` |
| `Already publish one` | `See how the scored files rank under the same lint.` | `/directory/` | `persona-graded` |
| `Here to search the corpus` | `Watch keyword, vector and hybrid retrieval, recorded.` | `/demo/` | `persona-query` |

Every link carries `data-track="home_cta_click"` and `data-destination` equal to its href.

## 5. Proof line — final copy

One `<p class="proof">` directly under the hero actions, promoting the counts out of the card
footers (F5) and stamping the "researched"/"recorded" claims (F7). Exact template:

```astro
<p class="proof">
  {Object.keys(tree.nodes).length} concepts across {tree.roots.length} roots, mapped {tree.generated}
  · {gradeA} of {directory.count} scored llms files earn an A, linted {directory.generated}
  · {demo.questions.length} retrieval questions, recorded {demo.generated}
</p>
```

The "N of M" honesty framing is preserved verbatim; no figure is rounded or restated.
Card footers keep their own counts — the proof line duplicates, it does not remove.

## 6. Card tiers

No card loses content; only weight and order change.

**Zone A — heading `Explore the corpus`** (`<ul class="card-grid tier-1">`), in this order:
1. **Tree** 2. **Directory** 3. **Demo** — full existing content (mindmap SVG, mermaid
`<details>`, showcase list, demo hit, footers). The Tree card keeps its inline `/tree/3d/` link.

**Zone B — heading `Read the reference`** (`<ul class="card-grid tier-2">`), in this order:
4. **Reference** 5. **Examples** 6. **Blog** 7. **llms.txt** — full existing content, rendered at
reduced visual weight (§8).

**Zone C — heading `Apply it to your own files`** (`<ul class="apply-list">`), replacing the three
trailing `.signin` paragraphs, in this order:
- `Skills` → `/skills/` — existing sentence, unchanged.
- `Downloads` → `/downloads/` — existing sentence, unchanged.
- `Sign in` → `/login/` — existing sentence, unchanged (keeps `/account/`, `/keys/`, `/usage/`).

## 7. Nav changes (`Base.astro`)

```js
const NAV = [
  ["/tree/", "Tree"],
  ["/directory/", "Directory"],
  ["/skills/", "Skills"],
  ["/reference/", "Reference"],
  ["/examples/", "Examples"],
  ["/downloads/", "Downloads"],
];
```

Six primary links. `/tree/` and `/directory/` — the site's two strongest surfaces — enter the nav
for the first time. **Skills is both**: a destination in `NAV` *and* the retained
`<details class="menu">`, whose `<summary>` is renamed **`Popular skills`** and whose `SKILLS`
array is unchanged, so the no-JS mechanism survives. **Downloads** is renamed from singular
"Download" to match its page title and four-artefact scope (F6). **Donate** and **Sign in** move
to a `<span class="utility">` after the menu, in that order, followed by the existing
`llms.txt` / `.md` twin links (untracked). Blog and Demo leave the nav; both stay reachable from
Zone A/B cards.

Nav tracking: each `NAV` link, plus Donate and Sign in, gets
`data-track="nav_click" data-label="<label>" data-destination="<href>"`.
The `<summary>` gets `data-track="skills_menu_open"`.

## 8. CSS plan (`global.css`)

New selectors (tokens only — no new colour values):

| Selector | Purpose | Tokens |
|---|---|---|
| `.hero-support` | positioning line under the lede | `--ink-muted`, `--step-0` |
| `.hero-actions` | flex row, `gap: var(--sp-3)`, `flex-wrap: wrap` | `--sp-3`, `--sp-5` |
| `.proof` | promoted live counts, no longer faint | `--font-mono`, `--step--1`, `--ink-muted`, `--line`, `--sp-3` |
| `.personas` | `list-style:none; display:grid; grid-template-columns: repeat(auto-fit, minmax(13rem,1fr))` | `--sp-3`, `--sp-5` |
| `.personas a` | block, bordered, `text-decoration:none`, `color: var(--ink)`; hover `border-color: var(--accent)` | `--paper-raised`, `--line`, `--radius`, `--sp-3` |
| `.personas .p-outcome` | second line of each branch | `--step--1`, `--ink-muted` |
| `.zone` | section wrapper | `--sp-7` |
| `.zone > h2` | zone heading | `--step-1`, `--font-display` |
| `.card-grid.tier-1` | `minmax(18rem, 1fr)` so three cards hold the row | existing grid |
| `.card-grid.tier-2` | `minmax(13rem, 1fr)`; `.tier-2 .card { box-shadow: none; padding: var(--sp-3); }`; `.tier-2 .example { font-size: 0.8rem; }` | `--sp-3` |
| `.apply-list` | `list-style:none; padding:0`, `border-top: 1px solid var(--line)` | `--line`, `--sp-3`, `--step--1`, `--ink-muted` |
| `.site-nav .utility` | right-grouped Donate / Sign in | `--sp-4`, `--line` |

Changed: `.signin` (`global.css:322`) has no consumer outside `index.astro`, so it is deleted and
`.apply-list` replaces it. `.btn` / `.btn.secondary` are used as-is — `--accent` is the site's established
link colour, not an urgency signal, so the CTA skill's caution about orange does not apply.

Responsive (extend the existing `@media (max-width: 640px)` block):
`.hero-actions { flex-direction: column; align-items: stretch; }`,
`.hero-actions .btn { justify-content: center; }`,
`.personas { grid-template-columns: 1fr; }`,
`.proof { font-size: 0.78rem; }`.

## 9. Tracking contract

One delegated listener in `Base.astro` (written by B6) reads these attributes.

| Element | `data-track` | Attributes → GA4 params |
|---|---|---|
| Hero primary / secondary | `home_cta_click` | `data-cta-id` (`get-tools`, `browse-tree`), `data-destination` |
| Persona strip (×3) | `home_cta_click` | `data-cta-id` (`persona-publish`, `persona-graded`, `persona-query`), `data-destination` |
| Zone C links (×3) | `home_cta_click` | `data-cta-id` (`skills`, `downloads`, `sign-in`), `data-destination` |
| Card title links (×7) | `card_click` | `data-card` (`tree`, `directory`, `demo`, `reference`, `examples`, `blog`, `llms-txt`), `data-destination` |
| `NAV` links + Donate + Sign in (×8) | `nav_click` | `data-label`, `data-destination` |
| `<summary>Popular skills</summary>` | `skills_menu_open` | none (fires on `toggle`, `open === true`) |

Expected DebugView interaction count for the manual recipe: **24** (8 `nav_click`,
7 `card_click`, 8 `home_cta_click`, 1 `skills_menu_open`) — supersedes the measurement plan's
pre-redesign count of 17.

## 10. Acceptance checklist

1. `description` in `index.astro` is one sentence, 153 chars, ≤180, and matches §3 exactly.
2. `title` is still `"LLMS-Explorer"`; `Base.astro:71` is unedited apart from nav/tracking.
3. Exactly two `.btn` elements exist above the proof line — one `.btn`, one `.btn.secondary`.
4. All five live figures render on the page (`tree.nodes`, `tree.roots`, `gradeA`,
   `directory.count`, `demo.questions.length`) plus the three `generated` stamps.
5. All seven original cards are present with their worked examples intact; none deleted.
6. Every original destination is linked from `/` or the nav: `/tree/`, `/tree/3d/`, `/directory/`,
   `/demo/`, `/reference/`, `/examples/`, `/blog/`, `/family/`, `/skills/`, `/downloads/`,
   `/login/`, `/donate/`.
7. `NAV` has exactly six entries, in the §7 order; the `<details class="menu">` and its `SKILLS`
   array still work with JavaScript disabled.
8. No new colour literals in `global.css`; every new rule uses existing tokens.
9. At ≤640px the hero buttons stack full-width and the persona strip is a single column.
10. `index.astro` still passes `twin={null}`, and the mindmap fallback chain (`index.astro:25-27`)
    is unchanged.
11. `uv run --directory hub pytest ../site/tests` passes.
12. `cd site && npm run build` passes.
