# Agent research hub — site refocus (2026-09-25)

**Status:** design, implemented in the same branch · **Owner:** Mitchell Hudson
**Supersedes** the home-page framing in `docs/site/redesign-spec-2026-09-07.md` (the tracking
contract and CSS token discipline from that spec stay in force).

## 1. What changes and why

The site today is framed as *"the llms.txt standard, in practice"*: a linter, a directory of
graded files, and a concept tree hanging off them. The ask is to reframe it as **a research
hub for agents**, built around three things it already holds but does not lead with:

| Asset | What exists | Where it is hidden today |
|---|---|---|
| Skills | 20 installable `SKILL.md` prompts, one page each, `npx skills add` | `/skills/` is a flat card list; the home page mentions it in one line of Zone C |
| Context files | 300 mirrored research reports (`src/content/sources/**`, 4.2 MB) served as pages and as raw `.md` downloads | no index page at all; reachable only from the one tree node that cites each |
| Facts | 452 concept packs, ~34k source-anchored facts, sorted into facets | rendered as HTML on `/tree/<slug>/` only — an agent has to parse a page |

**Single hop** is the design constraint: an agent that fetches one index must be able to fetch
one more URL and have the whole answer as plain markdown. Every new surface below is therefore
(a) a human page, (b) a markdown twin the site's own `llms.txt` lists, and (c) a plain `.md`
file per row where the row is the payload (a skill, a context file, a concept's facts).

Trade-off chosen: **downloads over twins for the per-row files.** `reference/usage.md` promises
that `/tree/<slug>/` rows carry no `rel="alternate"` twin because Cloudflare's 100-rule
`_headers` cap cannot carry a per-file `X-Markdown-Tokens` rule for each. That promise stays
true. The per-concept facts files live under `/downloads/concepts/<slug>.md` — the same
`public/downloads/` mechanism `gen_downloads.py` already uses for the context files — where the
existing `/*.md` header rule gives them `text/markdown` and the `describedby` link, and
`build_llms.py`'s existing `downloads/` exclusion keeps them out of `llms-full.txt`. The token
estimate an agent would read from the header is written into each file's banner comment instead.

## 2. Surfaces

### 2.1 Home (`/`) — rewritten

- **Eyebrow:** `A research hub for agents`
- **Lede** (`description`, one sentence, ≤180 chars):
  `Skills to install, context files to load, and source-anchored facts on every researched concept — each one a single fetch from this site's llms.txt.`
- **Support line:** `Files are promises: every fact names its source, every index is generated from the same tree, and nothing here needs an account to read.`
- **Hero CTAs:** primary `Install a skill` → `/skills/`; secondary `Browse the context files` → `/context/`.
- **Proof line:** skills installable · context files (with total MB) · concepts and facts · graded llms files — all live counts, with the tree's `generated` stamp.
- **Persona strip** (3 links): `Give your agent a skill` → `/skills/` · `Load a context file` → `/context/` · `Look up one concept's facts` → `/tree/`.
- **Zone A "Share and load"** (tier-1 cards): **Skills** (top skills by alias with the install line), **Context files** (largest roots with file counts), **Concepts** (mindmap kept; footer now counts facts too).
- **Zone B "Verify the territory"** (tier-2 cards): Directory, Demo, Reference, Examples, Blog, llms.txt family — content unchanged from today.
- **Zone C "Apply it"**: Downloads, Playground, Contribute, Sign in — as today.
- Tracking attributes follow the 2026-09-07 contract (`home_cta_click`, `card_click`, `nav_click`).

### 2.2 Nav (`Base.astro`)

`Skills · Context · Concepts · Directory · Reference · Downloads`, then the `Popular skills`
menu (unchanged), then utility `Contribute · Donate · Sign in`. Examples and Blog leave the nav
(both stay one hop from `/` in Zone B). `/tree/` is labelled **Concepts** — the URL does not
change, so no link or test breaks.

### 2.3 `/skills/` — grouped catalogue

`[collection]/index.astro` renders the skills collection grouped by family, derived from the
existing `tags` frontmatter (no new frontmatter field):

| Group | Rule |
|---|---|
| llms.txt families | tag `llms` or `llms-txt` |
| Deep optimizers | tag `optimization` |
| Research and mapping | tag `research`, `concept-mapping`, `concept-depth`, `taxonomy`, `orchestration` |
| Everything else | remainder |

Each card keeps title + description and adds the alias command and the one-line install
command. The other three collections render exactly as before.

### 2.4 `/context/` — new page, new twin

- **Data:** `src/data/context.json`, written by the new `tools/gen_context.py` from
  `src/content/sources/**` + `src/data/concepts/*.json` + `src/data/tree.json`. Deterministic:
  never reads the wall clock (`generated` is copied from `tree.json`), never reads
  `~/.global-ai-hub`. Committed, and regenerated by `prebuild` so it cannot drift.
- **Shape:**
  ```json
  {"generated": "…", "roots": [{"slug","concept","files":[…],"concepts":[…]}],
   "totals": {"files","bytes","concepts","facts","facets"}}
  ```
  A **file** row: `hub`, `name`, `title`, `description`, `bytes`, `route` (`/sources/<hub>/<name>/`),
  `download` (`/downloads/sources/<hub>/<name>.md`), `concepts` (slugs that cite it, most-cited first).
  A **concept** row: `slug`, `concept`, `facets`, `facts`, `download` (`/downloads/concepts/<slug>.md`).
  A file is filed under the root of the concept that cites it most; a concept under its own root
  (walked up `parent_slug`). Anything unreachable goes under a synthetic `unfiled` root so nothing
  is invisible.
- **Page:** one `<details>` per root (open when small), a table of files (title, size, cited-by
  concept links, `.md` download) and a list of the root's concept facts files. A lede states the
  rights position: these are the hub's own research reports, republished so a fact's source URL
  resolves; third-party full text is never here.
- **Twin:** `/context.md`, produced by `twins.py` through a new `PAGE_SECTIONS` entry
  (`data: "context.json"`, explains `reference/context-files.md`, index = every file's download
  URL then every concept's facts URL). That puts `/context/` into the site's `llms.txt` under
  the same rule as `/tree/`, `/directory/` and `/demo/`.
- **Explainer:** new `src/content/reference/context-files.md` (what a context file is, how it is
  filed, what the facts file format is, what the rights position is).

### 2.5 `/downloads/concepts/<slug>.md` — per-concept facts file

Written by the new `tools/gen_concept_facts.py` (prebuild) for every concept pack:

```
<!-- llms-explorer concept facts · https://llms-explorer.com/tree/<slug>/ · pack <generated> · ~N tokens -->
# <Concept>

> <summary>

Parent: [<parent>](…/tree/<parent_slug>/) · <facets> facets · <facts> facts · page: …/tree/<slug>/

## <Facet title>
- <fact text> — [source](<url>)        (nested `level` rendered as indented bullets)

## Related concepts
- [<concept>](…/tree/<slug>/) — <relation>

## Context files
- [<title>](…/downloads/sources/<hub>/<name>.md)
```

Idempotent, no wall clock. `/tree/<slug>/` gains a `↓ Facts as markdown` link beside the existing
reference-file download; the node page itself stays twin-less (§1).

### 2.6 Prose that must stay true

- `reference/usage.md` §2: add `/context.md` to the section twins, and a paragraph on the
  per-concept facts files and where their token estimate lives.
- `family.astro`, `downloads.astro`, `llms.overrides.json` `summary`/`note`: mention the context
  index and the facts files.
- `site/README.md`: the two new generators in the build chain.

## 3. Build chain

`prebuild` = `gen_downloads.py && gen_context.py && gen_concept_facts.py`. `gen_context.py`
also runs under `npm run generate`. No change to `postbuild`. CI's "committed data is current"
step gains `context.json` next to `tree.json`.

## 4. Tests

- `test_gen_context.py`: fixture with two roots, one file cited by two concepts → filed under
  the heavier root, listed under both concepts; unreachable file lands in `unfiled`; totals add
  up; output is byte-stable across two runs.
- `test_gen_concept_facts.py`: nested `level` renders as nested bullets; every fact keeps its
  source URL; no-pack node produces no file; banner carries the token estimate.
- `test_context_page.py` (needs `dist/`): `/context/` links every download in `context.json`;
  every linked download exists in `dist/`; `/context.md` twin exists and is advertised.
- `test_section_pages.py`: `GENERATED_SECTIONS` gains `context` (so `/context.md` must be built
  and `usage.md` must name it).
- `test_twins.py`: the section-twin fixture gains `context.json`.
- `test_skill_page_parity.py`, `test_tree_pages.py`: unchanged and must still pass.

## 5. Non-goals

- No change to what enters `llms-full.txt` / `llms-facts.txt` / `llms-small.txt`.
- No new frontmatter on skills; grouping is derived.
- No API, no account surface changes, no CSS colour literals.
- `/tree/` browser, 3D view, directory and demo pages are untouched apart from the facts link.
