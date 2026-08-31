# 10 — Directory of known llms files and their conformance

**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | api | cli | mcp

## 1. Purpose

A browsable, searchable directory of every site known to publish an `llms.txt` / `llms-full.txt`,
each scored against the current standard (spec v2 + the `/ldo` attribute rubric) by actually
fetching the files and running the linter on them. The directory answers "who publishes, in what
grammar, how well, and is it still alive" — and lets an owner claim a site, get a badge, and be
re-scored on push. The seed is the hub's existing 766-entry catalogue; the new part is the
per-site conformance score, its history, ownership, and the dog-food export of the directory itself
as an llms family.

## 2. User stories and flows

- **Browser**: "Show me every developer-tools site with an A-grade `llms.txt`" → facet by category,
  sort by score, open the site card (score card by attribute group, grammar, size ladder, freshness).
- **Agent author**: "Which sites have a facts-grade full file I can point Claude Code at?" → filter
  `has llms-full ∧ grammar ≠ none ∧ pages ≥ 10`, copy the `/m/<key>/llms.txt` URL.
- **Site owner**: claim `docs.example.com` → prove ownership by adding a token line → site shows
  the verified badge, owner gets lint-on-push (webhook or scheduled probe), the score history, and
  the fix diffs the linter proposes (component 01 in `--fix` mode, never applied to their site).
- **Contributor**: submit a URL → probe runs → entry appears as `unverified` until the weekly
  refresh confirms it twice.
- **Maintainer** (me): retire dead sites (404 for 3 consecutive weekly probes), merge duplicate keys,
  override a category, mark a rights restriction.

Flow, one site: `submit/seed → probe ladder → fetch (bounded) → lint (01) → score → publish card →
weekly re-probe → history point → retire on 3× dead`.

## 3. Inputs → outputs (contracts and file grammars)

**Inputs**
- Catalogue seed: `hub/scripts/llms_full_catalog.py` `catalog.json` — list of
  `{key, url, name, site, category, description, sources[]}` (766 entries: llms-txt-hub,
  llmstxt.site, directory.llmstxt.cloud, own docslist probe); `manifest.json` per key: download
  `status ∈ {ok, failed, rejected, missing}`, `pages`, bytes, fetched-at. Today: 608 ok, 145 with
  ≥ 1 real page.
- Probe results per site (`hub/scripts/llms_acquire.py` `probe()` + `_roots()` ladder, extended):
  `llms.txt` (200?, bytes, kind per `llms_lint.detect_kind`), `llms-full.txt` (present ∧ contains
  pages — PayPal's redirect-to-index case is `rejected`), `.md` twins (probe 3 sampled page URLs
  as `page.md` and `page.html.md`), `Accept: text/markdown` on an HTML page, `Link:` headers
  (`rel="describedby"`, `rel="alternate" type="text/markdown"`), `X-Markdown-Tokens`.
- Lint findings: `llms_lint.py check --json` per fetched file →
  `{pass, attr, severity, line, msg, fixable}` with `counts` (see component 01).

**Outputs**
- **Site record** (§7) with a **conformance score** 0–100 and grade A–F.
- **Score card**: per attribute group I (identity), N (navigation), D (descriptions), C (content
  fidelity), P (provenance/trust), S (size), R (retrieval readiness — only when we can index it),
  F (family), H (hygiene/serving) — each group = 100 − weighted deductions (High 25, Medium 8,
  Low 2, capped at 100), overall = weighted mean (N, D, C, P at 1.5; I, S, H at 1.0; R, F at 0.5
  when applicable, else excluded).
- **Directory export** `outputs/directory.llms/` — the directory as an llms family:
  `llms.txt` (H1, blockquote, `## Categories` → `<category>/llms.txt` split per spec-v2 nesting,
  `## Optional` → retired sites), `<category>/llms.txt` (one line per site:
  `- [Name](https://site/llms.txt): grade A · mintlify full · 191 pages · verified 2026-08-31 —
  <description>`), `llms-facts.txt` (one `[statement]` unit per site per probe fact, anchored to
  the site's own `llms.txt` URL), `manifest.json`. Linted by 01 before publish (0 High).

**Grammar of a directory facts line** (hub facts grammar):
`- [statement] docs.example.com publishes llms-full.txt in the mintlify grammar (191 pages, 2.1M tokens) — https://docs.example.com/llms-full.txt · keywords: mintlify, llms-full · verified-as-of: 2026-08-31`

## 4. Architecture (mermaid diagram + existing hub code reused, by path)

```mermaid
flowchart LR
  seed[catalog.json 766] --> probe[probe worker<br/>llms_acquire.probe + header checks]
  submit[/api/directory/submit] --> probe
  probe --> fetch[bounded fetch<br/>llms_full_catalog.download_all rules]
  fetch --> lint[llms_lint.py check --json<br/>kind, grammar, findings]
  lint --> score[scorer<br/>attribute groups → 0–100, A–F]
  score --> pg[(Postgres<br/>sites, probes, scores, claims)]
  pg --> api[explorer-api /api/directory/*]
  api --> web[Astro pages: list, facets, site card, history]
  api --> mcp[hub_llms_full_list / _read (13)]
  pg --> export[directory.llms/ export<br/>export_llms.build_index + build_facts]
  export --> serve[llms_serve.py /t/directory/…]
  weekly[launchd com.global-ai-hub.llms-full-refresh] --> probe
```

Reused as-is: `hub/scripts/llms_full_catalog.py` (`compile_catalog`, `download_all`, `list_entries`,
`read_entry`, `export_mirror`), `hub/scripts/llms_acquire.py` (`probe`, `split_llms_full`,
`parse_llms_index`), `hub/scripts/llms_lint.py` (`detect_kind`, `check`), `hub/scripts/llms_serve.py`
(`/m/<key>/llms-full.txt`, generated `/m/<key>/llms.txt`, `/m/<key>/pages/<n>.md`),
`hub/scripts/docset_refine/export_llms.py` (`build_index`, `build_split_index`, `build_facts`) for
the dog-food export. New: `explorer-api/directory/{probe,score,claims}.py`, the scorer, Postgres
tables, the Astro pages. The weekly refresh stays the hub's launchd job; the site consumes its
manifest rather than re-downloading.

## 5. API / CLI / MCP surface

| Surface | Call | Notes |
|---|---|---|
| REST | `GET /api/directory?q=&category=&grade=&has=full,twins,headers&sort=score&page=` | public, cached 10 min |
| REST | `GET /api/directory/<key>` | site record + latest score card + probe facts |
| REST | `GET /api/directory/<key>/history` | `[{probed_at, score, grade, high, medium}]` |
| REST | `GET /api/directory/<key>/findings` | latest lint findings (index + generated index; full-file findings as counts only unless owner) |
| REST | `POST /api/directory/submit {url}` | rate-limited; creates `unverified` entry, queues probe |
| REST | `POST /api/directory/<key>/claim` → `{token}`; `POST …/claim/verify` | token must appear in the site's `llms.txt` as `<!-- llms-explorer-verify: <token> -->` or in a `Link` header; also accepts DNS TXT `_llms-explorer.<host>` |
| REST | `POST /api/directory/<key>/rescore` | owner or maintainer; metered (§8) |
| REST | `GET /api/directory/<key>/badge.svg?style=` | A–F badge, `Cache-Control: max-age=86400` |
| CLI | `llmsx dir search <q>`, `llmsx dir show <key>`, `llmsx dir claim <host>`, `llmsx dir rescore <key>` | thin wrappers |
| MCP | `hub_llms_full_list(query, status, min_pages, min_grade)` (add `min_grade`), `hub_llms_full_read(key, page)` (owner-scoped for third-party full text, see §10), new `hub_directory_score(key)` | via component 13 |
| Served | `/t/directory/llms.txt`, `/t/directory/<category>/llms.txt`, `/t/directory/llms-facts.txt` | the dog-food family |

## 6. UI (pages, states, empty/error states)

- `/directory` — search box, facets (category from the catalogue's 30-odd labels; grade; grammar;
  has: index / full / small / facts / twins / headers; freshness), table with name, grade chip,
  grammar, pages, last probed. Empty search → "no sites match; submit one" CTA. Probe backlog
  banner when > 50 sites are `queued`.
- `/directory/<key>` — header (name, site link, grade badge, claimed/unverified), score card
  radar per attribute group, "what we found" list (kind detected, grammar, size ladder, twins,
  headers, steering/secret counts, freshness), score history sparkline, top findings (High/Medium
  with attribute id → link into reference 03), "copy MCP/agent URLs", owner panel (claim, rescore,
  webhook, lint-on-push log). States: `queued`, `probing`, `scored`, `dead (n/3)`, `retired`,
  `rights-restricted` (owner asked not to be listed → name only, no files).
- `/directory/submit` — URL form → immediate probe summary or "already listed".
- Error states: probe timeout → "unreachable since <date>" with retry; lint crash on a malformed
  file → grade `F` with the P0 finding, never a 500.

## 7. Data model and storage

Postgres (site metadata + scores); files stay on the hub (`llms-full/files/<key>.txt`, gitignored
there, mirrored into this repo under `outputs/llms-full/files/`).

```
sites(key pk, host, name, site_url, category, description, sources[], status enum(seed,unverified,live,dead,retired,restricted),
      owner_user_id null, claimed_at, created_at, updated_at)
probes(id pk, site_key fk, probed_at, llms_txt jsonb{status,bytes,kind,grammar}, llms_full jsonb{status,bytes,pages,grammar},
       twins jsonb{md,html_md,accept}, headers jsonb{describedby,alternate,tokens}, duration_ms, error)
scores(id pk, site_key fk, probe_id fk, scored_at, overall int, grade char, groups jsonb{I,N,D,C,P,S,R,F,H}, high int, medium int,
       low int, findings_ref text)              -- findings JSON stored on disk: directory/findings/<key>/<probe_id>.json
claims(id pk, site_key fk, user_id fk, token, method enum(comment,header,dns), verified_at null, revoked_at null)
submissions(id pk, url, user_id null, ip_hash, created_at, site_key null, outcome)
```

Retention: keep every score row (history is the product), keep only the last 4 findings files per
site. Dead-site rule: 3 consecutive weekly probes with no `llms.txt` and no `llms-full.txt` →
`dead`; 4 more → `retired` (listed under `## Optional` in the export, hidden by default).

## 8. Tiering, metering and billing hooks

| Feature | Tier | Metered unit |
|---|---|---|
| Browse, search, site card, history, badge | free | — |
| Submit a site | free (5/day/user, 20/day/IP) | — |
| Claim a site | free | — |
| Rescore on demand | owner: 10/day free, then per-probe; anonymous: not offered | probe (fetch + lint, no model tokens) |
| Lint-on-push webhook | paid tier | probe per push, capped 100/day |
| Fix diffs for your own files (01 `--fix` preview) | paid tier | per lint run |
| Full-file findings detail for a third-party site | maintainer only | — |
| Directory API bulk (`page_size > 100`, JSON dump) | API key, paid | request |

No model tokens are spent by the directory itself; the only cost is probe bandwidth and lint CPU,
so the score is free to compute and the metering exists to stop abuse, not to earn.

## 9. Acceptance bar (measurable)

- Seed import: every one of the 766 catalogue keys has a `sites` row; 608 `ok` manifests produce a
  score within one weekly cycle; probe p95 < 30 s per site; the weekly run finishes in < 2 h.
- Scoring is deterministic: same fetched bytes → same score (test with 20 frozen fixtures, incl.
  a mintlify full, an anthropic-yaml full, a cloudflare-frontmatter full, a firecrawl full, an
  index-that-is-a-full-file, a steering file, a placeholder-key file).
- Grade distribution sanity on the seed: not all A, not all F; `platform.openai.com`-style
  no-description indexes land ≤ C; `developers.cloudflare.com`'s split root lands ≥ B.
- Claim flow: token verification succeeds via comment, header and DNS in the test harness; a
  revoked claim removes the badge within one probe.
- Dog food: `outputs/directory.llms/` lints 0 High with component 01; root index ≤ 10 KB
  (categories split); every listed site link resolves in the weekly `--check-links` run or the
  site is flagged dead.
- Search returns in < 200 ms p95 for the 766-row table (Postgres FTS or trigram; no vector).

## 10. Security, rights, privacy

- Third-party **full text is never republished** on the public site. The card shows counts,
  grammar, page titles and the *generated* index (`/m/<key>/llms.txt`: titles + `Source:` URLs
  only). `hub_llms_full_read` over the hosted MCP returns full pages only for the maintainer or
  the verified owner; anonymous callers get page metadata. Local users of the hub keep the
  existing behaviour (their own mirror, internal marker).
- Owner opt-out: a verified owner can set `restricted` → name + link only, no scores shown
  publicly (scores still computed for their own panel). Cloudflare Content Signals
  `ai-train=no` on the source is recorded and shown; it does not affect linting (we read, we do
  not train), but it blocks mirroring into `outputs/`.
- Probes identify as `llms-explorer-probe/1.0 (+https://<domain>/directory/about)`, obey
  `robots.txt` with our own UA (the hub's fixed `get_robots`), ≤ 1 request/s per host, ≤ 8
  concurrent hosts, 10 s timeout, 1 retry.
- Findings for P5 (secrets) are shown to owners only and never in the public findings feed
  (exposing a leaked key location is worse than the leak). P4 steering findings are public.
- Claim tokens are 128-bit random, single-use, expire in 7 days; DNS method uses a separate
  token. Submissions store an IP hash (salted, 30-day retention), never raw IPs.
- No cookies on public directory pages beyond the platform session; badge SVG is served without
  tracking parameters.

## 11. Dependencies on other components (by number)

- **01** llms-linter — scoring runs its deterministic passes; findings schema is 01's.
- **03** reference — attribute ids on the score card link into the rubric pages.
- **09** concept tree — a site's docset (when indexed) links to the tree nodes it feeds.
- **13** MCP hosting — `hub_llms_full_list/_read` scoping and the new `hub_directory_score`.
- **15** accounts/billing — claims, owner tier, rescore metering.
- **17** semantic indexer — an owner can turn a scored site into an indexed docset (R-group
  attributes only score when an index exists).

## 12. Open questions and assumptions

- Assumed the group weights and deduction values (High 25 / Medium 8 / Low 2); calibrate on the
  seed so the median public site lands around C and known-good exemplars (Anthropic, Cloudflare)
  land A/B — to be tuned before launch, recorded in `directory/scoring.md`.
- Assumed the catalogue's `category` labels are usable as facets; they came from three
  directories with different vocabularies — a mapping table (and a `## Categories` split) is
  needed; unresolved until the seed is inspected.
- Open: should R-group (retrieval readiness) ever count for a third-party site we do not index?
  Proposed: excluded unless the owner opts in to indexing (17).
- Open: whether to expose a public JSON dump of the whole directory (CC-BY?) — leaning yes for
  metadata + scores, never for mirrored text.
- Assumed the weekly cadence is enough for freshness; owners with lint-on-push get faster updates.
- Assumed dead/retired thresholds (3 / 7 weeks); adjustable.
