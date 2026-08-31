# Agent D — consumption, recreation, aggregation (2026-08-30; 26 queries, 7 negation)

## D1 consumers
- llms_txt2ctx: reference consumer; regex-parses, fetches every link, emits XML `<project title summary>`; FastHTML builds llms-ctx.txt (no Optional) and llms-ctx-full.txt (with). v2 dropped it from the proposal → reference behaviour, not a product. FACT/QUALIFIED.
- LangChain mcpdoc (MCP): `list_doc_sources` + `fetch_docs`; auto-allowlists only the llms.txt's domain; targets Cursor, Windsurf, Claude Desktop, Claude Code; exists because built-in retrieval "can be opaque" — the AGENT decides which links to follow. FACT.
- Cursor @Docs: crawls URLs; Jun 2025 request "cannot recognise llms.txt" got "seems like something we should support", no follow-up; Jan 2026 mod: files > 50–60k tokens unstable → split a 4 MB llms-full by section; whether @Docs follows links inside llms.txt unanswered; docs.cursor.com/llms.txt once redirected to an HTML app shell (consumers ingested React markup). FACT/QUALIFIED.
- Windsurf Cascade: @docs = curated list "we are confident we can read with high quality"; @web arbitrary; chunked; llms.txt only as its own index. FACT.
- GitHub Copilot: Jun 2025 community request, no staff reply as of Jul 2026. FACT.
- Claude Code: Anthropic publishes code.claude.com/docs/llms.txt as the page-discovery index; Ahrefs: Claude-Code UA out-fetched every retrieval bot; bots never speculatively request it; no documented automatic lookup — fetched when directed. TENTATIVE on automation.
- ChatGPT/Perplexity/Google: no statements of use; logs show ~0. FACT (negation).
- Browser-agent frameworks (Stagehand, Browser Use): nothing documented. TENTATIVE/unsupported.

## D2 Optional + budgeting
- v2: Optional = convention for secondary links. llms_txt2ctx = binary `--optional` (two pre-expanded files). Real budgeting is PRODUCER-side splitting: Mintlify 100k-char cap → `/_llms/<group>.md` recursive sub-indexes (never drops pages); Cursor: split at ~50–60k tokens; Firecrawl llms-full delimits pages with `<|firecrawl-page-N-lllmstxt|>`; Jina Reader `x-max-tokens`, `x-markdown-chunking`; Cloudflare returns `x-markdown-tokens` / `x-original-tokens`; Godot declined llms-full (Jan 2025) citing context bloat. FACT.

## D3 negotiation + twins
- Cloudflare "Markdown for Agents" shipped 2026-02-12: `Accept: text/markdown` → edge HTML→Markdown, `Content-Type: text/markdown`, `x-markdown-tokens`, `x-original-tokens`, `Vary: Accept`, strips ETag/Last-Modified/Content-Encoding, YAML frontmatter from meta + JSON-LD, drops nav/header/footer/scripts; HTML ≤ 2 MB; Pro/Business/Enterprise; no advance discovery — clients just try. FACT.
- 44-day Worker log (Mar–Apr 2026): 1,421 Accept: text/markdown requests — headless Chrome 639, "Claude" (Anthropic infra) 500, axios 211; NO GPTBot/PerplexityBot/ClaudeBot sent the header. FACT.
- Discovery: spec v2 twins; Mintlify links every page with .md; Cloudflare per-product files link …/index.md; origin implementations add `<link rel="alternate" type="text/markdown">` + `Vary: Accept` and must bypass full-page caches keyed without Accept. FACT.

## E1 recreation tools
- Firecrawl `/llmstxt` (v1.6.0 alpha): URL → async job → llms.txt (+ optional full); maxUrls 1–100 (default 10), 1 credit/URL, public pages, 5,000-URL cap; UNMAINTAINED after 2025-06-30 → Python repo. Hosted: llmstxt.firecrawl.dev/{url} and /full. FACT.
- create-llmstxt-py (successor): /map → scrape (batches of 10, failures skipped, no retry) → GPT-4o-mini writes 3–4-word title + 9–10-word description per page → llms.txt; llms-full concatenates under `<|firecrawl-page-N-lllmstxt|>`; default 20 URLs; memory issues on large sites; AI-summarised descriptions; sections NOT inferred (flat list). FACT.
- dotenvx/llmstxt: sitemap.xml → bullets; --include-path/--exclude-path globs; --replace-title regex (titles EXTRACTED from HTML). FACT.
- Jina Reader r.jina.ai: headless Chrome/curl → Readability → Turndown; headers x-respond-with, x-target-selector, x-retain-links, x-max-tokens, x-markdown-chunking; anonymous rate-limited; per-page cleaner, no site mode. FACT.
- SEO generators (SEOmator "5,000 pages"): robots→sitemap discovery, fallback paths, index-sitemap expansion, LLM title+description; vendor-claimed. QUALIFIED.
- Pitfalls: nav chrome inflates tokens without Readability-class extraction; JS-rendered invisible to non-browser fetchers; HTML app-shell redirects masquerade as llms.txt; llms-full > 50–60k tokens destabilises IDE indexers; failed scrapes silently dropped.

## E2 seeding + ranking
- Seeds: sitemap.xml (dotenvx), /map crawl (Firecrawl); Mintlify/Cloudflare/Anthropic generate from the docs NAV TREE. Vendors describe rank-then-cut heuristics (Core → Product → Documentation → Resources → Support → Blog → Company → Legal → Other; 50–200 links) — no primary algorithm. Mintlify: order by "frequency, not importance" — first 20% of links answer 80% of questions. QUALIFIED.

## E3 rights/etiquette
- Cloudflare Content Signals (2025-09-24, CC0): `Content-Signal: search=yes, ai-input=…, ai-train=no` in robots.txt; `ai-input` covers RAG/grounding/real-time; managed default search=yes, ai-train=no, ai-input unset; framed as express reservations under EU Directive 2019/790 Art. 4. A recreated llms-full.txt is a STORED republication (closer to ai-train/redistribution than transient ai-input). robots.txt is a polite request, not law, but ignoring it invites blocking; verbatim republication of substantial content = canonical copyright risk; extraction for analysis is the defensible pattern. Etiquette: public index (links + short descriptions), private full-text mirror. FACT/QUALIFIED.

## E4 aggregation
- Spec v2 nesting = the mechanism. Cloudflare = live hub-and-spoke: developers.cloudflare.com/llms.txt ~120 entries in 7 categories, each linking per-product …/<product>/llms.txt (workers/llms.txt ~25 sections, 500+ .md links). Mintlify /_llms/ = automated recursive version. Anthropic platform.claude.com/llms.txt ~650 .md links, 11 languages, single-domain, does NOT link code.claude.com (sibling products = separate roots). Vercel/Stripe group one file by product area; Supabase splits by language. Directories: llmstxt.site columns product/website/llms.txt/llms-full/TOKEN COUNTS, /submit; llmstxthub ~2,650 sites/15 categories; neither publishes an llms.txt-of-llms.txt. FACT.

## Recreation pipeline (from cited sources)
1. Check /llms.txt, nested /<path>/llms.txt (most specific), .md twins, `Accept: text/markdown` (expect Vary: Accept, x-markdown-tokens).
2. robots.txt → sitemap + Content-Signal; respect ai-input/ai-train=no.
3. Seed from sitemap.xml (expand index sitemaps; globs) or /map.
4. Fetch clean markdown: negotiated → .md twin → Readability+Turndown (r.jina.ai, x-target-selector); browser engine for JS sites.
5. Title + ~10-word description per page via small model, or extract <title>/meta.
6. Group by URL path/product; hot 20% first; changelog/legal → Optional.
7. Cap index ~100k chars / ≤50–60k tokens; spill to sub-indexes hub-and-spoke.
8. Emit llms-full with per-page delimiters + token counts; keep internal unless rights allow.

## References (D)
1. https://llmstxt.org/intro.html — docs
2. https://llmstxt.org/ — docs
3. https://github.com/langchain-ai/mcpdoc — readme
4. https://forum.cursor.com/t/is-there-any-size-limit-for-llms-txt-indexed-as-docs/148660 — forum
5. https://forum.cursor.com/t/cursor-not-support-llms-txt-standard/108980 — forum
6. https://github.com/orgs/community/discussions/162955 — forum
7. https://docs.devin.ai/windsurf/plugins/cascade/web-search — docs
8. https://ahrefs.com/blog/llmstxt-study/ — blog
9. https://www.searchenginejournal.com/google-says-llms-txt-comparable-to-keywords-meta-tag/544804/ — blog
10. https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents — docs
11. https://developers.cloudflare.com/changelog/post/2026-02-12-markdown-for-agents/ — vendor
12. https://suganthan.com/blog/cloudflare-markdown-for-agents/ — blog
13. https://toddmorourke.com/learn/markdown-for-agents/ — blog
14. https://www.mintlify.com/docs/ai/llmstxt — docs
15. https://docs.firecrawl.dev/features/alpha/llmstxt — docs
16. https://github.com/firecrawl/create-llmstxt-py — readme
17. https://github.com/firecrawl/llmstxt-generator — readme
18. https://github.com/jina-ai/reader — readme
19. https://github.com/dotenvx/llmstxt — readme
20. https://seomator.com/free-llms-txt-generator — vendor
21. https://blog.cloudflare.com/content-signals-policy/ — vendor
22. https://www.scrapingbee.com/blog/is-web-scraping-legal/ — blog
23. https://developers.cloudflare.com/llms.txt — docs
24. https://developers.cloudflare.com/workers/llms.txt — docs
25. https://platform.claude.com/llms.txt — docs
26. https://www.mintlify.com/blog/real-llms-txt-examples — blog
27. https://llmstxt.site/ — vendor
28. https://llmstxthub.com/ — vendor
29. https://code.claude.com/docs/llms.txt — docs
30. https://github.com/godotengine/godot-docs/issues/10549 — forum
31. https://forum.cursor.com/t/docs-cursor-com-llms-txt-serves-an-html-page-instead-of-the-llms-txt-file/167800 — forum
