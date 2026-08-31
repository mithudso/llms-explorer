---
title: 'Generation tooling'
description: 'Generators compared; why extractive descriptions win.'
section: reference
order: 30
sources:
  - skills/document-formats/references/llms-txt-generation-tooling.md
---

# llms.txt generation tooling — platforms, static-site plugins, crawl-based generators, CMS plugins

<!-- provenance: /dr deep-research 2026-08-30; hub: document-formats; parent spoke: llms-txt.md -->
verified-as-of: 2026-08-30 (tool versions, maintenance status and platform features are volatile — re-verify before recommending)

**Contents**
1. Pick by situation
2. Docs platforms (built-in)
3. Static-site-generator plugins
4. Crawl-based generators (sites you do not own)
5. CMS and site builders
6. Edge content negotiation
7. Quality practices that generators get wrong
8. References

## 1. Pick by situation

| You have… | Use | Emits |
|---|---|---|
| Docs on Mintlify / GitBook / ReadMe / Fern | nothing — it is automatic | llms.txt (+ full on Mintlify/GitBook) + `.md` twins |
| Docusaurus, MkDocs, VitePress, Starlight, Sphinx, Nuxt | the framework plugin (table §3) | llms.txt + llms-full.txt (+ `.md`, `llms-small.txt` on Starlight) |
| A live site you do not own | crawl-based generator (§4) — `create-llmstxt-py`, `dotenvx/llmstxt`, or your own sitemap→markdown pipeline | llms.txt (+ full) with **extracted or AI-written** descriptions |
| WordPress | Yoast ≥25.3 / Rank Math / AIOSEO (§5) | llms.txt only (AIOSEO Pro adds full + markdown posts) |
| Webflow / Framer | host a hand-written file | whatever you upload |
| Any Cloudflare-proxied HTML site | "Markdown for Agents" toggle (§6) | on-the-fly markdown on `Accept: text/markdown`, no llms.txt |

## 2. Docs platforms

| Platform | Emits | Descriptions from | Notes |
|---|---|---|---|
| **Mintlify** | llms.txt, llms-full.txt, `.md` per page, `/.well-known/` copies, `/_llms/` split indexes | frontmatter `description` (truncated at 300 chars), nav order from `docs.json`; optional `markdown.instructions` agent text | index capped at 100,000 chars → recursive `/_llms/<group>.md`; default language/version only; hidden/noindex pages excluded; hand-written root files override; auth sites list public pages or require auth[^1] |
| **Fern** | llms.txt (root **and per-subdirectory**), `.md` per page; **no llms-full.txt** | frontmatter `description`, fallback `subtitle`; adds OpenAPI/AsyncAPI links | dropped llms-full because it "exceeded most model context windows, added heavy serving overhead, saw little use"[^2] |
| **GitBook** | llms.txt (Jan 2025), llms-full.txt + `.md` per page (Jun 2025), `/sitemap.md`, `Accept: text/markdown` | auto from page structure | zero-config; no curation controls documented; full export "will be more expensive"[^3][^4] |
| **ReadMe** | llms.txt (default on, all plans), `.md` per page; **no llms-full** | project title + guide/API hierarchy | a custom file from the repo root disables auto-updates; hidden pages excluded[^5] |
| **GitDoc** (vendor claim) | llms.txt + llms-full.txt "for the pages you mark as priority", regenerated in the build | sidebar/nav | vendor blog, 2026-05-22[^6] |

## 3. Static-site-generator plugins

| Plugin | Emits | Input | Descriptions / ordering | Maturity & limits |
|---|---|---|---|---|
| `docusaurus-plugin-llms` (rachfop) | llms.txt, llms-full.txt, optional per-page `.md`, versioned + `customLLMFiles` | source tree at `postBuild` | frontmatter → first heading → site fallback; `includeOrder` globs | 144★, MIT; not run in `docusaurus start`; image rewrite only for bundled assets[^7] |
| `@signalwire/docusaurus-plugin-llms-txt` | llms.txt, `.md`, optional full | **built HTML** (rehype/remark) | manual `sections[].description`, `autoSectionDepth` | v1.2.2, ~10 months stale; ENOENT / "processed 0 documents" bug[^8][^9] |
| Docusaurus core | none | — | — | issue #10899 open since Feb 2025[^10] |
| `mkdocs-llmstxt` (pawamoy) | llms.txt, `.md`, optional `full_output` | built HTML → BeautifulSoup → Markdownify | `sections:` dict with per-file descriptions | 130★, v0.5.x, **maintenance mode, seeking maintainer**; needs `site_url`; mkdocstrings `show_source` mangles tables/code in the full file[^11][^12] |
| `vitepress-plugin-llms` (okineadev) | llms.txt, llms-full.txt, `.md` | VitePress source | frontmatter `description`; `<llm-only>` / `<llm-exclude>` tags | 394★; used by Vite, Vue, Vitest, Rolldown; relative URLs break under redirects/domain moves[^13] |
| `starlight-llms-txt` (delucis) | llms.txt, llms-full.txt, **llms-small.txt** | Astro Starlight | `projectName`, `description`, `details`, `optionalLinks`, `customSets`, `promote`/`demote`; `minify` strips asides | 110★, docs updated Aug 2026; needs `site`[^14] |
| `sphinx-llms-txt` (jdillard) | llms.txt (markdown), llms-full.txt (**reStructuredText**) | Sphinx build | toctree titles; `llms_txt_summary`, `llms_txt_exclude`, `llms_txt_full_max_size` | v0.7.1; full file is RST; points to NVIDIA `sphinx-llm`[^15] |
| `nuxt-llms` / Nuxt Content | llms.txt (~5K tokens), opt-in llms-full.txt (~1M+ tokens) | Nuxt Content, runtime hooks | `sections` in `nuxt.config` | first-party; full file explicitly for 200K+-context tools[^16] |
| Next.js / Nextra | hand-rolled `app/llms.txt/route.ts` (force-static or dynamic); `next-llms-txt` adds per-page `.md` endpoints | components | "reads and parses readable text" | discussion #80692 unresolved; no Nextra built-in found (tentative)[^17][^18] |
| `llms-txt-action` (demodrive-ai) | llms.txt, llms-full.txt, `.md` | built HTML dir + sitemap.xml | local/offline or cloud LLM summaries via LiteLLM (default GPT-4o) | 16★; needs `--dirty` with `mkdocs gh-deploy`[^19] |

## 4. Crawl-based generators (sites you do not own)

| Tool | What it does | Limits |
|---|---|---|
| Firecrawl `/llmstxt` API + llmstxt.firecrawl.dev | URL → async job → llms.txt (+ full); `maxUrls` 1–100 (default 10), 1 credit/URL, public pages only, 5,000-URL alpha cap | **deprecated in favour of the main endpoints** (page carries no date; still up); users pointed to the Python repo[^20][^21] |
| `create-llmstxt-py` (Firecrawl, 320★) | `/map` → scrape each page to markdown (batches of 10; failures skipped, no retry) → GPT-4o-mini writes a 3–4-word title + 9–10-word description → flat llms.txt; llms-full.txt concatenates under `<\|firecrawl-page-N-lllmstxt\|>` | default 20 URLs; memory issues on large sites; **sections are not inferred**; descriptions are AI-written and unreviewed[^22] |
| `dotenvx/llmstxt` (147★, BSD-3) | sitemap.xml → `- [Title](url): description` bullets; `--include-path` / `--exclude-path` globs; `--replace-title` regex | llms.txt only; titles extracted from HTML; description derivation undocumented[^23] |
| Jina Reader `r.jina.ai/<url>` | headless Chrome or curl engine → Readability → Turndown; headers `x-respond-with`, `x-target-selector`, `x-retain-links`, `x-max-tokens`, `x-markdown-chunking` | per-page cleaner, no site/llms.txt mode; anonymous traffic rate-limited[^24] |
| Screaming Frog v24.3 | per-page `.md` via a Readability.js + Turndown custom-JS snippet; llms.txt via n8n/CSV converters | no native llms.txt export; thin pages return nothing; JS rendering slow[^25][^26] |
| `plainsignal/llmstxt` Chrome extension | llms.txt + one `.md` per page + zip from sitemap or rendered DOM; meta description as blockquote | 10★, HTTPS only[^27] |
| SEO-tool generators (SEOmator etc.) | robots.txt → sitemap discovery, index-sitemap expansion, LLM-written title+description per URL | vendor-claimed mechanics only[^28] |
| llms-text.com generator/validator | crawls a domain and exports llms.txt + llms-full.txt ("deep-crawls up to 50 subpages"); validator checks syntax, links, UTF-8, headers | vendor; its guidance: 10–20 evergreen URLs, 4–7 H2s, 10–20-word descriptions, index under 10 KB, `Content-Type: text/plain|text/markdown; charset=utf-8`, HTTP 200 (no redirect/auth), `Link: <…/llms.txt>; rel="describedby"` header[^29][^30] |

## 5. CMS and site builders

| Platform | Emits | Descriptions | Limits |
|---|---|---|---|
| Yoast SEO ≥25.3 (2025-06-10) | llms.txt only, regenerated weekly | custom excerpt only — **no description otherwise**; 5 latest posts/pages/CPT (≤12 months, cornerstone first) + top-5 taxonomies | 5-item cap; markdown chars escaped; a static file wins over the dynamic one[^31][^32] |
| Rank Math | llms.txt only | "intro text"; post types/taxonomies, limit default 100; custom lines | no full[^33] |
| AIOSEO | llms.txt (free); llms-full.txt + markdown post conversion (Pro) | site title/tagline; per-post-type limits, exclusions | paywall[^34] |
| `website-llms-txt`, `llms-full-txt-generator` | llms.txt (+ full) | titles + SEO-plugin descriptions; honour noindex | one shipped a broken-access-control CVE fix[^35] |
| Joost de Valk "Markdown Alternate" | `<link rel="alternate" type="text/markdown">` + `.md` URLs per post | — | negotiation, not an index[^36] |
| Webflow / Framer | host an uploaded file (Framer: Pro/Enterprise "Hosting → Files"); a Framer marketplace plugin scans the CMS | manual | no generation[^37][^38] |
| Shopify (Apr–May 2026, silent) | auto `/llms.txt`, `/agents.md`, `/sitemap_agentic_discovery.xml`, `/.well-known/ucp` on every store | boilerplate: H1 store name, `/collections/all`, contact, UCP + MCP endpoints | `templates/llms.txt.liquid` **replaces, does not merge**; no changelog; 78.1% of top-10k Shopify hosts vs WordPress 8.7%[^39][^40][^41] |

## 6. Edge content negotiation

Cloudflare "Markdown for Agents" (2026-02-12; Pro/Business/Enterprise; zone toggle under AI Crawl Control): on `Accept: text/markdown` the edge converts HTML → markdown (body + meta-derived YAML frontmatter + JSON-LD, nav/header/footer/scripts dropped) and returns `Content-Type: text/markdown; charset=utf-8`, `x-markdown-tokens`, `x-original-tokens`, `Vary: Accept`; ETag/Last-Modified/Content-Encoding stripped; origin HTML ≤ 2 MB (raised from 1 MB); a chunked-encoding silent pass-through was fixed Jul 2026.[^42][^43][^44] It produces no llms.txt — pair it with a hand-written index. Checkly measured a 99.7% token reduction on its own docs (single site).[^45]

## 7. Quality practices that generators get wrong

- **Descriptions are the product.** Every platform generator draws the one-liner from frontmatter `description`; crawl tools scrape `<meta>` or have a small model invent it; WordPress generators are weakest (Yoast emits none without a custom excerpt; Yoast/Rank Math "list content but don't really prioritize it").[^1][^22][^31][^46] Treat AI-written descriptions as drafts to edit, and audit the *page list*, not just the output. The spec's own test: give an agent only the llms.txt and ask it questions.[^47]
- **Sections and order come from config or nav, never inferred by crawlers.** mkdocs `sections:`, signalwire `sections[]` + `autoSectionDepth`, Starlight `customSets` + `promote`/`demote`, docusaurus `includeOrder`; Mintlify uses `docs.json` order. Mintlify's editorial rule: order by "frequency, not importance" — the first 20% of links should answer 80% of questions.[^11][^14][^7][^1][^48]
- **`## Optional`** (convention only in v2): changelogs, legal, old posts, deep appendices; never pricing or the API reference.[^49]
- **Size budgets are producer-side.** Split large indexes (Mintlify 100k chars → `/_llms/`), ship a small variant (Starlight `llms-small.txt`, Nuxt's ~5K-token file), cap the full file (`llms_txt_full_max_size`), or drop it (Fern). No cross-vendor numeric budget exists; "index under 10 KB" is a vendor number.[^1][^14][^15][^2][^30]
- **Regenerate in the build; check links in CI.** Custom/static files freeze updates (ReadMe, Yoast); dead links happen (litellm's index carried a deleted page); `llms-txt-validator --check-links` and `npx llms-txt-check` exist for pipelines.[^5][^31][^50][^51]
- **Serve `.md` twins and honour `Accept: text/markdown`** where the platform allows; add `Vary: Accept` and bypass full-page caches keyed without it.[^1][^52]
- **Counter-evidence to weigh before spending effort:** 97% of files get zero AI requests; Google has no implementation. Generation pays off for developer docs consumed by coding agents, not for general SEO.[^53][^54]

## References

[^1]: https://www.mintlify.com/docs/ai/llmstxt (docs)
[^2]: https://buildwithfern.com/learn/docs/ai-features/llms-txt (docs)
[^3]: https://gitbook.com/docs/ai-and-search/llm-ready-docs (docs)
[^4]: https://gitbook.com/docs/changelog/june-2025/24-june-performance-upgrades-llms-full.txt-and-.md-support-text-alignment-and-more (docs)
[^5]: https://docs.readme.com/main/docs/LLMstxt (docs)
[^6]: https://gitdoc.ai/blog/llms-txt-ai-readable-documentation — 2026-05-22 (vendor)
[^7]: https://github.com/rachfop/docusaurus-plugin-llms (readme)
[^8]: https://github.com/signalwire/docusaurus-plugins/tree/main/packages/docusaurus-plugin-llms-txt (readme)
[^9]: https://github.com/signalwire/docusaurus-plugins/issues/5 (forum)
[^10]: https://github.com/facebook/docusaurus/issues/10899 (forum)
[^11]: https://github.com/pawamoy/mkdocs-llmstxt (readme)
[^12]: https://github.com/mkdocstrings/python/issues/299 (forum)
[^13]: https://github.com/okineadev/vitepress-plugin-llms (readme)
[^14]: https://delucis.github.io/starlight-llms-txt/configuration/ (docs)
[^15]: https://sphinx-llms-txt.readthedocs.io/en/latest/ (docs)
[^16]: https://nuxt.com/docs/4.x/guide/ai/llms-txt (docs)
[^17]: https://next-llms-txt.vercel.app/ (docs)
[^18]: https://github.com/vercel/next.js/discussions/80692 (forum)
[^19]: https://github.com/demodrive-ai/llms-txt-action (readme)
[^20]: https://docs.firecrawl.dev/features/alpha/llmstxt (docs)
[^21]: https://github.com/firecrawl/llmstxt-generator (readme)
[^22]: https://github.com/firecrawl/create-llmstxt-py (readme)
[^23]: https://github.com/dotenvx/llmstxt (readme)
[^24]: https://github.com/jina-ai/reader (readme)
[^25]: https://www.screamingfrog.co.uk/blog/generate-markdown-at-scale/ (vendor)
[^26]: https://n8n.io/workflows/3219-generate-ai-ready-llmstxt-files-from-screaming-frog-website-crawls/ (vendor)
[^27]: https://github.com/plainsignal/llmstxt (readme)
[^28]: https://seomator.com/free-llms-txt-generator (vendor)
[^29]: https://www.llms-text.com/blog/how-to-create-llms-txt — Michael Vereb, 2025-07-25 (vendor)
[^30]: https://www.llms-text.com/blog/llms-txt — 2025-07-25 (vendor)
[^31]: https://developer.yoast.com/features/llms-txt/functional-specification/ (docs)
[^32]: https://developer.yoast.com/changelog/yoast-seo/25.3/ (docs)
[^33]: https://rankmath.com/kb/llms-txt/ (docs)
[^34]: https://aioseo.com/docs/how-to-create-an-llms-txt-using-all-in-one-seo/ (docs)
[^35]: https://wordpress.org/plugins/website-llms-txt/ (vendor)
[^36]: https://joost.blog/markdown-alternate/ (blog)
[^37]: https://university.webflow.com/videos/optimize-your-site-for-llms-with-llms-txt (docs)
[^38]: https://www.framer.com/help/articles/llms-txt-framer/ (docs)
[^39]: https://honeybound.co/blog/shopify-llms-txt-agents-md (blog)
[^40]: https://imakemvps.com/blog/llms-txt-generator-for-shopify (blog)
[^41]: https://caseyrb.com/blog/state-of-llms-txt-adoption/ — HTTP Archive, Jun 2026 (study)
[^42]: https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/ (docs)
[^43]: https://developers.cloudflare.com/changelog/post/2026-02-12-markdown-for-agents/ (docs)
[^44]: https://community.cloudflare.com/t/cloudflare-fundamentals-content-encoding-support-for-markdown-for-agents-and-other-improvements/893536 (forum)
[^45]: https://www.checklyhq.com/blog/state-of-ai-agent-content-negotation/ (blog)
[^46]: https://weventure.de/en/blog/llms-txt (blog)
[^47]: https://llmstxt.org/ (spec)
[^48]: https://www.mintlify.com/blog/real-llms-txt-examples (vendor)
[^49]: https://dev.to/lab451/complete-llmstxt-guide-for-2026-57d (blog)
[^50]: https://github.com/BerriAI/litellm/issues/36342 (forum)
[^51]: https://github.com/bridgetoagent/llms-txt-validator (readme)
[^52]: https://toddmorourke.com/learn/markdown-for-agents/ (blog)
[^53]: https://ahrefs.com/blog/llmstxt-study/ (study)
[^54]: https://www.searchenginejournal.com/google-says-llms-txt-is-purely-speculative-for-now/577576/ (blog)
