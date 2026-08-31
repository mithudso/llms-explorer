# Agent C — generation tooling (2026-08-30; 36 queries, 12 negation)

## Tools (tool — kind — emits — input — descriptions — maturity — limitation)
- Mintlify — docs platform — llms.txt + llms-full.txt + .md per page + /.well-known/ copies + /_llms/ split — docs.json nav — frontmatter description (300-char truncation), nav order; hand-written root files override — live Nov 2024 — 100k-char index cap; default language/version only; hidden/noindex excluded.
- Fern — docs platform — llms.txt (root + per-subdir) + .md per page; NO llms-full ("exceeded most model context windows, added heavy serving overhead, saw little use") — frontmatter description / subtitle; adds OpenAPI/AsyncAPI links.
- GitBook — llms.txt (Jan 2025) + llms-full + .md per page (Jun 2025) + /sitemap.md + Accept: text/markdown — zero-config, no curation controls; full export "more expensive".
- ReadMe — llms.txt default on (all plans) + .md per page; NO llms-full — custom file from repo root disables auto-updates; hidden pages excluded.
- docusaurus-plugin-llms (rachfop, 144★, MIT) — llms.txt + llms-full + optional per-page .md, versions, customLLMFiles — source tree at postBuild — frontmatter → first heading → site fallback; includeOrder globs — not in `start`; image rewrite bundled-only.
- @signalwire/docusaurus-plugin-llms-txt v1.2.2 — llms.txt + .md + optional full — BUILT HTML (rehype/remark) — manual sections[].description, autoSectionDepth — stale (~10 months), ENOENT/0-documents bug.
- Docusaurus core — none (issue #10899 open since Feb 2025).
- mkdocs-llmstxt (pawamoy, 130★, v0.5.x, MAINTENANCE MODE) — llms.txt + .md + optional full_output — built HTML → BeautifulSoup → Markdownify — sections: dict with per-file descriptions — needs site_url; mkdocstrings show_source mangles tables/code.
- vitepress-plugin-llms (okineadev, 394★; used by Vite, Vue, Vitest, Rolldown) — llms.txt + full + .md — frontmatter description; <llm-only>/<llm-exclude> tags — relative URLs break under redirects.
- starlight-llms-txt (delucis, 110★, docs updated Aug 2026) — llms.txt + llms-full + llms-small.txt — projectName/description/details/optionalLinks/customSets/promote/demote; minify strips asides; exclude affects small only — needs site.
- Next.js/Nextra — hand-rolled app/llms.txt/route.ts; next-llms-txt adds per-page .md; discussion #80692 unresolved; no Nextra built-in (TENTATIVE).
- sphinx-llms-txt (jdillard, v0.7.1) — llms.txt (MD) + llms-full (RST!) — toctree titles; llms_txt_summary/exclude/full_max_size — points to NVIDIA sphinx-llm.
- nuxt-llms / Nuxt Content (first-party) — llms.txt (~5K tokens) + opt-in full (~1M+ tokens, "200K+ context tools only") — sections in nuxt.config.
- Firecrawl /llmstxt API (v1.6.0 alpha) + llmstxt.firecrawl.dev (537★) + create-llmstxt-py (320★) — llms.txt + full — live crawl maxUrls 1–100, 5,000 alpha cap — GPT-4o-mini 3–4-word title + 9–10-word description — API DEPRECATED after 2025-06-30 (still up) — 1 credit/URL; AI descriptions unreviewed.
- dotenvx/llmstxt (147★, BSD-3) — llms.txt only — sitemap.xml — titles/meta; --title/--description/--include-path/--exclude-path/--replace-title — no full.
- demodrive-ai/llms-txt-action (16★) — llms.txt + full + .md — built HTML + sitemap — local/offline or cloud LLM summaries via LiteLLM (default GPT-4o) — needs --dirty with mkdocs gh-deploy.
- Screaming Frog (v24.3, Apr 2026) — per-page .md via Readability.js+Turndown custom JS; llms.txt via n8n/CSV converters — no native export; thin pages empty; JS rendering slow.
- plainsignal/llmstxt Chrome ext (10★) — llms.txt + .md per page + zip — sitemap or rendered DOM — Turndown; meta description as blockquote — HTTPS only.
- Yoast SEO ≥25.3 (2025-06-10) — llms.txt only, regenerated weekly — custom excerpt only (else NO description); 5 latest posts/pages/CPT (≤12 mo, cornerstone first) + top-5 taxonomies — 5-item cap; static file wins.
- Rank Math — llms.txt only — intro text; post types/taxonomies limit 100; custom lines.
- AIOSEO — llms.txt (free) + llms-full + Markdown post conversion (Pro).
- website-llms-txt / llms-full-txt-generator (WP) — titles + SEO descriptions; honour noindex; one had a broken-access-control CVE fix.
- Webflow / Framer — host an uploaded file only (Framer Pro/Enterprise Hosting → Files); Framer marketplace plugin scans CMS.
- Shopify (Apr–May 2026, silent) — auto /llms.txt + /agents.md + /sitemap_agentic_discovery.xml on all stores — boilerplate (H1 store name, /collections/all, contact, UCP + MCP endpoints); templates/llms.txt.liquid REPLACES, does not merge.
- llms-txt (AnswerDotAI PyPI) — NO generator; parse_llms_file, create_ctx, llms_txt2ctx → XML; nbdev tutorial: hand-write llms.txt, pysym2md for apilist.txt.
- Cloudflare Markdown for Agents (2026-02-12; Pro/Business/Ent) — on-the-fly HTML→MD on Accept: text/markdown; x-markdown-tokens; Vary: Accept; ≤2 MB origin (was 1 MB); chunked-encoding pass-through fixed Jul 2026; drops ETag/Last-Modified.

## llms-text.com how-tos (vendor, 2025-07-25)
- Funnels to its Generator + Validator. Steps: curate 10–20 evergreen URLs; H1 + blockquote + 4–7 H2s; 10–20-word descriptions; .md twins; root, UTF-8, 200; `Link: <…/llms.txt>; rel="describedby"` header (QUALIFIED: v2 spec now ALSO specifies rel="describedby" — orchestrator note); snippets for Next.js, Astro, WordPress, static, Workers. blog/llms-txt: keep index < 10 KB (~2,500 tokens); Optional as "programmatic breakpoint"; omitting descriptions "drastically reduces efficacy"; "114% fewer tokens" is arithmetically incoherent → marketing.

## Quality practices
- Descriptions: SSG/platform generators use frontmatter description (Mintlify 300-char truncation; Fern subtitle fallback; docusaurus → first heading); crawl tools scrape meta or LLM-invent (Firecrawl GPT-4o-mini; llms-txt-action optional); WordPress weakest (Yoast: none without custom excerpt; "list content but don't prioritize"). Treat AI descriptions as drafts; audit the source page LIST.
- Sections/ordering: config maps (mkdocs sections:, signalwire sections[]+autoSectionDepth, starlight customSets/promote/demote, docusaurus includeOrder); nav order default (Mintlify).
- Optional: changelogs, legal, old posts, deep appendices; never pricing/API reference (community guidance).
- Size: Fern dropped llms-full; Mantine 2.2 MB inline → 45 KB link list after Dec 2025 complaint ("clogs the AI's context window"); Nuxt ~5K vs ~1M+ tokens gated to 200K+ tools; Mintlify /_llms/ split; Starlight llms-small; sphinx full_max_size. No cross-vendor numeric budget; "<10 KB index" only vendor number.
- Sync/CI: build-hook plugins regenerate every build; custom/static files freeze updates (ReadMe, Yoast); stale links real (litellm's llms.txt carried a deleted /intro page, Aug 2026); `npx llms-txt-check` / `llms-txt-validator --check-links` JSON for CI; Shopify silent rollout broke agency workflows.
- .md twins + negotiation: Mintlify/Fern/GitBook/ReadMe serve .md; Mintlify/GitBook/Fern honour Accept: text/markdown (Mintlify adds X-Robots-Tag: noindex, nofollow + prepended llms.txt blockquote); WordPress "Markdown Alternate" plugin (Joost de Valk) adds rel=alternate + .md URLs; one site 1,421 Accept requests/44 days (35% Claude UA); Checkly 99.7% token reduction on its own docs.
- Negation: 97% zero requests (Ahrefs); Google no implementation; generation justified mainly for developer docs consumed by coding agents.

## References (C)
1. https://www.mintlify.com/docs/ai/llmstxt — docs
2. https://www.mintlify.com/blog/context-for-agents — vendor
3. https://buildwithfern.com/learn/docs/ai-features/llms-txt — docs
4. https://gitbook.com/docs/ai-and-search/llm-ready-docs — docs
5. https://gitbook.com/docs/changelog/june-2025/24-june-performance-upgrades-llms-full.txt-and-.md-support-text-alignment-and-more — docs
6. https://docs.readme.com/main/docs/LLMstxt — docs
7. https://github.com/rachfop/docusaurus-plugin-llms — readme
8. https://github.com/signalwire/docusaurus-plugins/tree/main/packages/docusaurus-plugin-llms-txt — readme
9. https://github.com/signalwire/docusaurus-plugins/issues/5 — forum
10. https://github.com/facebook/docusaurus/issues/10899 — forum
11. https://github.com/pawamoy/mkdocs-llmstxt — readme
12. https://github.com/mkdocstrings/python/issues/299 — forum
13. https://github.com/okineadev/vitepress-plugin-llms — readme
14. https://delucis.github.io/starlight-llms-txt/configuration/ — docs
15. https://next-llms-txt.vercel.app/ — docs
16. https://github.com/vercel/next.js/discussions/80692 — forum
17. https://sphinx-llms-txt.readthedocs.io/en/latest/ — docs
18. https://nuxt.com/docs/4.x/guide/ai/llms-txt — docs
19. https://docs.firecrawl.dev/features/alpha/llmstxt — docs
20. https://github.com/firecrawl/create-llmstxt-py — readme
21. https://github.com/firecrawl/llmstxt-generator — readme
22. https://github.com/dotenvx/llmstxt — readme
23. https://github.com/demodrive-ai/llms-txt-action — readme
24. https://www.screamingfrog.co.uk/blog/generate-markdown-at-scale/ — vendor
25. https://n8n.io/workflows/3219-generate-ai-ready-llmstxt-files-from-screaming-frog-website-crawls/ — vendor
26. https://github.com/plainsignal/llmstxt — readme
27. https://developer.yoast.com/features/llms-txt/functional-specification/ — docs
28. https://developer.yoast.com/changelog/yoast-seo/25.3/ — docs
29. https://rankmath.com/kb/llms-txt/ — docs
30. https://aioseo.com/docs/how-to-create-an-llms-txt-using-all-in-one-seo/ — docs
31. https://wordpress.org/plugins/website-llms-txt/ — vendor
32. https://university.webflow.com/videos/optimize-your-site-for-llms-with-llms-txt — docs
33. https://www.framer.com/help/articles/llms-txt-framer/ — docs
34. https://honeybound.co/blog/shopify-llms-txt-agents-md — blog
35. https://www.tilio.co.uk/blog/shopify-is-adding-llms-txt-to-millions-of-stores — blog
36. https://imakemvps.com/blog/llms-txt-generator-for-shopify — blog
37. https://llmstxt.org/intro.html — docs
38. https://llmstxt.org/nbdev.html — docs
39. https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/ — docs
40. https://developers.cloudflare.com/changelog/post/2026-02-12-markdown-for-agents/ — docs
41. https://community.cloudflare.com/t/cloudflare-fundamentals-content-encoding-support-for-markdown-for-agents-and-other-improvements/893536 — forum
42. https://www.llms-text.com/blog/how-to-create-llms-txt — vendor
43. https://www.llms-text.com/blog/llms-txt — vendor
44. https://weventure.de/en/blog/llms-txt — blog
45. https://www.mintlify.com/library/best-llms-txt-platforms — vendor
46. https://dev.to/lab451/complete-llmstxt-guide-for-2026-57d — blog
47. https://github.com/orgs/mantinedev/discussions/8523 — forum
48. https://github.com/BerriAI/litellm/issues/36342 — forum
49. https://github.com/bridgetoagent/llms-txt-validator — readme
50. https://joost.blog/markdown-alternate/ — blog
51. https://suganthan.com/blog/cloudflare-markdown-for-agents/ — blog
52. https://www.checklyhq.com/blog/state-of-ai-agent-content-negotation/ — blog
53. https://ahrefs.com/blog/llmstxt-study/ — blog
54. https://www.searchenginejournal.com/google-says-llms-txt-is-purely-speculative-for-now/577576/ — blog
