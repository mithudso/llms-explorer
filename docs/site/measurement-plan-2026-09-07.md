# Measurement plan — home/nav redesign (Plan B, item B2)

Scope: `/`, top nav, and the skills/tree discovery path. Current instrumentation
(`site/src/layouts/Base.astro:33-40`) loads gtag.js against `G-0KWFPMH6WX` with
no custom events — only `page_view` and GA4's enhanced-measurement defaults
(scroll, outbound click, file download). `astro.config.mjs` builds statically
(`build: { format: "directory" }`, no `output: "server"`) — no server-side
analytics path exists, so every metric here comes from the client-side gtag
snippet already in `<head>`.

## 1. Objectives → metrics

| Design objective | GA4 metric(s) | Source |
|---|---|---|
| Clarify purpose/value in <10s | Engagement rate on `/`; scroll ≥50% (default `scroll` fires at 90% — needs a custom 50% trigger, §2 gap) | GA4 standard report + custom event |
| Match experience to visitor identity/use case | First-click destination from `/` (which of 7 cards + 3 trailing links), new vs returning | `card_click`/`nav_click`, dimensioned by `destination` |
| Reduce friction to first interaction | `/skills/` and `/tree/` entrance rate from `/`; time-to-first-click | `card_click`/`nav_click` → GA4 funnel exploration |
| Guide learn → explore → apply | Downloads CTR from `/`; sign-in starts; path `/` → `/tree/`/`/skills/` → a reference/example page | `nav_click`, `home_cta_click`, `skills_menu_open` chained in a funnel |

Decision metrics for §4: (1) first-click-to-explore rate — share of `/` sessions whose first tracked click targets `/tree/`, `/skills/`, or `/demo/`; (2) engagement rate on `/`; (3) downloads/sign-in CTR from `/`.

## 2. Event taxonomy

All names snake_case, ≤40 chars, fired via the existing global `gtag` function already declared in `Base.astro`. One delegated `click` listener on `document`, filtered by `[data-track]`, replaces per-element handlers — cheapest to add to `Base.astro` and it auto-covers new cards without new listeners.

**Attribute contract** (put on the anchor/element itself):
```html
<a href="/tree/" data-track="card_click" data-card="tree" data-destination="/tree/">Tree</a>
<a href="/login/" data-track="nav_click" data-label="Sign in" data-destination="/login/">Sign in</a>
<a href="/downloads/" data-track="home_cta_click" data-cta-id="downloads" data-destination="/downloads/">Downloads</a>
<details class="menu"><summary data-track="skills_menu_open">Skills</summary>...</details>
```
Applied per region: the 7 cards get `card_click`; the nav bar (`Reference`, `Examples`, `Download`, `Blog`, `Donate`, `Sign in`) gets `nav_click`; the nav's Skills `<details>` gets `skills_menu_open`; `index.astro`'s three trailing body links (Skills, Downloads, Sign in) get `home_cta_click` with `cta_id` `skills`/`downloads`/`sign-in`.

**Delegated listener** (add once in `Base.astro`, after the gtag init block):
```html
<script>
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-track]');
    if (!el) return;
    const t = el.dataset.track, d = el.dataset.destination;
    if (t === 'card_click') gtag('event', t, { card: el.dataset.card, destination: d });
    else if (t === 'nav_click') gtag('event', t, { label: el.dataset.label, destination: d });
    else if (t === 'home_cta_click') gtag('event', t, { cta_id: el.dataset.ctaId, destination: d });
  });
  document.addEventListener('toggle', (e) => {
    if (e.target.matches('details.menu') && e.target.open) gtag('event', 'skills_menu_open', {});
  }, true);
</script>
```

| Event | Parameters | Fires when |
|---|---|---|
| `home_cta_click` | `cta_id` (one of `skills`, `downloads`, `sign-in`), `destination` (path) | click on `index.astro`'s three trailing body links |
| `nav_click` | `label` (nav link text), `destination` (path) | click on any top-nav link |
| `skills_menu_open` | none | the `<details class="menu">` Skills disclosure opens |
| `card_click` | `card` (one of `tree`,`directory`,`demo`,`reference`,`examples`,`blog`,`llms-txt`), `destination` (path) | click on any of the 7 home cards |

GA4 enhanced measurement only fires `scroll` at 90%; the ≥50% signal in §1 needs a 5th, non-required event (`scroll_50`, no parameters, via `IntersectionObserver` at the page midpoint) — optional here.

## 3. Baseline capture (owner fills in — no GA4 API access from this session)

Pull a 14-day window immediately **before** the redesign ships. Record here:

| Metric | Window | Value | Notes |
|---|---|---|---|
| Sessions on `/` | 14d pre-launch |  |  |
| Engagement rate on `/` | 14d pre-launch |  |  |
| Top next-page from `/` (path exploration) | 14d pre-launch |  | list top 3 |
| Bounce rate on `/` | 14d pre-launch |  |  |
| Sign-in page (`/login/`) entrances from `/` | 14d pre-launch |  |  |
| Downloads page (`/downloads/`) entrances from `/` | 14d pre-launch |  |  |

This session has no GA4 Data API or console access; whoever holds GA4 console access for `G-0KWFPMH6WX` must paste these in before ship, from the standard Pages/Screens report (filtered to `/`) and the Path Exploration report.

## 4. Validation approach

Pre/post comparison, **minimum 14 days each side** of the ship date, holding season/traffic-source mix as constant as practical (compare like weekdays, avoid comparing a launch week against a holiday week).

Decision metrics (max 3, per da-12-ab-testing-causal-inference's guidance on declaring metrics in advance — `~/.claude/skills/da-analytical-methods/references/da-12-ab-testing-causal-inference.md`):
1. **First-click-to-explore rate** — share of `/` sessions where the first `card_click`/`nav_click` targets `/tree/`, `/skills/`, or `/demo/`.
2. **Engagement rate on `/`** (GA4 standard metric).
3. **Downloads/sign-in CTR from `/`** (`home_cta_click` with `cta_id` in `downloads`/`sign-in`, divided by `/` sessions).

Threshold for "improved": **+20% relative** lift on the first-click-to-explore rate (metric 1), non-regression (no >10% relative drop) on engagement rate and CTR.

**Why not an A/B test**: the static build has no server-side/edge logic to split traffic on, and no experimentation framework (Optimizely/Statsig/GrowthBook, feature flags) is wired into this Cloudflare Pages deployment — standing one up for a single redesign decision is disproportionate. Traffic is also almost certainly below the sample sizes a randomized test needs: da-12-ab-testing-causal-inference's rule of thumb is thousands of users per arm for percentage-point effects, tens of thousands for tenths-of-a-percent (`~/.claude/skills/da-analytical-methods/references/da-12-ab-testing-causal-inference.md`, "Sample size and power analysis"). Pre/post accepts the seasonality/secular-trend confound in exchange for being achievable at this traffic level; note any concurrent change (a post going viral) when reading the post-period.

## 5. Definition of done

Instrumentation is done when:
- All four events appear in GA4 **DebugView** with correct parameter values, via the GA Debugger extension or `gtag('config', ..., {debug_mode: true})` on a staging load.
- **Manual test recipe**: open the deployed `/` page with GA Debugger (or DebugView filter) active, then click every one of the 7 cards, all 6 top-nav links (`Reference`, `Examples`, `Download`, `Blog`, `Donate`, `Sign in`), all 3 trailing body links (`Skills`, `Downloads`, `Sign in`), and open the Skills nav menu once — 17 total interactions, each landing in DebugView with the correct `card`/`label`/`destination`/`cta_id` value — then ship.
