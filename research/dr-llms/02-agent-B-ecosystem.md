# Agent B — ecosystem, adoption, criticism (2026-08-30; 22 queries, 6 negation)

## Who publishes
- Live probe 2026-08-30: 200 at docs.anthropic.com (72 KB; llms-full 41.6 MB), docs.stripe.com (90 KB, no full), developers.cloudflare.com, vercel.com, supabase.com, docs.perplexity.ai, mintlify.com, docs.github.com, shopify.com; 404/403 at platform.openai.com, openai.com, ai.google.dev, developers.google.com, learn.microsoft.com. (NB: spec v2 says developers.openai.com/llms.txt and ai.google.dev/gemini-api/docs/llms.txt exist — subpath/different hosts; orchestrator verified developers.openai.com/llms.txt = 200, 5.8 KB.)
- Platform-driven: Mintlify auto since Nov 2024 (Anthropic, Cursor, Coinbase, Pinecone, Windsurf), co-developed llms-full with Anthropic. Shopify silently shipped llms.txt, llms-full.txt, agents.md, /.well-known/ucp to every store first week May 2026; HTTP Archive: 78.1% of top-10k Shopify hosts vs WordPress 8.7%.
- Top-1000 adopters (Rankability Aug 2026): Cloudflare, Azure, GitHub, Fastly, WordPress, DigiCert, Adobe, Opera, Samsung, Sentry. Fortune 500: 7.4% (37/500, Mar 2026) QUALIFIED.
- Directories (self-submitted, overlapping): directory.llmstxt.cloud "4,000 websites" (49M llms.txt tokens / 325M llms-full tokens); llmstxthub.com 2,650 entries / 16 categories (David Dias); llmstxt.site ~1,000+ (~170 in May 2025); SecretiveShell/Awesome-llms-txt 784 link lines; llms-text.com "780+ verified". Lower bounds, not measurements.

## Adoption over time
| Date | Source | Sample | Finding |
|---|---|---|---|
| Feb→May 2025 | Chris Green | Majestic Million | 15 → 105 valid (~0.01%) |
| Jun 2025 | Originality.ai | 3M+ sites | 4,088 |
| Jun 2025 | Rankability | Tranco top 1,000 | 0.3% |
| Jul 2025 | HTTP Archive (Burridge) | top 10k | 1.04% valid |
| Nov 2025 | SE Ranking | ~300k domains | 10.13% (9.88% low / 10.54% mid / 8.27% high-traffic) |
| Mar 2026 | Originality.ai via ppc.land | Fortune 500 | 7.4% |
| May 2026 | Originality.ai | 3M+ | 36,120 llms.txt (8.8x YoY); llms-full 23→2,463 (107x); ai.txt 397 |
| May 2026 | Ahrefs | 137,210 AWA domains | 28% valid (SEO-savvy, self-selected) |
| Jun 2026 | HTTP Archive | top 1k/10k/100k/1M | 6.28% / 5.61% / 5.17% / 5.07% (~5.4x in 12 mo) |
| Jun 2026 | Rankability | Tranco top 1,000 | 8.7% (87; 15 llms-full) |
Contradictions kept: top-1000 6.28% vs 8.7% same month (different lists); "0% in top 1000" attributed to SE Ranking is not in its primary; Presenc.ai 51.8% (219-host panel) unverifiable.

## Criticism
- Mueller (r/TechSEO, 2025-04-17): "none of the AI services have said they're using LLMs.TXT (… they don't even check for it) … comparable to the keywords meta tag". Illyes (Jul 2025): Google doesn't support and isn't planning to. Google "AI features and your website" (2025-12-10): no new files/markup needed. FACT.
- Ambiguity: Search Central briefly hosted its own llms.txt (Nov 2025) then 404'd; Chrome Lighthouse 13.3 (May 2026) "Agentic Browsing" category checks llms.txt (404 = N/A; server error = flagged). FACT.
- Ahrefs log study (2026-06-15; May 2026 logs; 137k domains): 97% of valid files got ZERO requests; of requests 96% bots, 77% non-AI (SEO auditors 21.7%); named AI bots 19.5%; training crawlers 5.3% (GPTBot 4.51%, ClaudeBot 0.8%); AI retrieval 1.1% (OAI-SearchBot 0.74%); 0 AI requests to non-existent files (no speculative probing); Claude-Code UA out-fetched every retrieval bot → agents read it when pointed at it. FACT.
- Other logs: OtterlyAI (90 d, Feb 2026) 84/62,100 AI-bot requests (0.1%); Wislr (Feb–Mar 2026) 12,099 bot requests, robots.txt hundreds, llms.txt 0; EZY (83 sites, Apr–Jul 2026) robots vs llms: GPTBot 3,990/7, ClaudeBot 3,120/9, PerplexityBot 775/0, Googlebot 5,125/67, Meta-ExternalAgent 172/193 (only bot fetching it MORE than robots); HN Feb 2026: only WebPageTest/BuiltWith UAs.
- Citation impact: SE Ranking (2025-11-07, XGBoost+SHAP): no relationship with LLM citation frequency; removing the variable improved model accuracy. FACT (correlational).
- Proponents: Shelby (SEL 2025-07-09): linked content must exist (unlike meta keywords); standards take years; agents "drop into" content; pairs with .md alternates. Mintlify (May 2025): Profound data that MS/OpenAI bots fetch llms.txt/llms-full; Vercel "10% signups from ChatGPT" (anecdotal). Howard targeted inference-time agent use, not GEO — "it's dead" measures a goal it never claimed.
- Net consensus: "not dead, but not a citation lever"; prompt-injection risk flagged (Ahrefs), no incident data.

## Vendor pages (credibility)
- llms-text.com sites-using: adopters check out on probe; "780+" uncorroborated; low for numbers.
- llms-text.com what-is: GEO-pillar + ChatGPT/Perplexity consumption claims CONTRADICTED by every log study; unattributed benchmarks; low.
- gitdoc.ai (2026-05-22): GitBook "41% of docs requests from AI agents" unverified; permission/inventory/navigation distinction and curation advice sound and consistent with Ahrefs' agent-directed finding.

## Relation to neighbours
- robots.txt = access control, the only file every AI bot fetches; sitemap.xml = inventory (also fetched by ClaudeBot/Bingbot/GPTBot); llms.txt = curated navigation for agents pointed at it; ai.txt tiny opt-out (397). Cloudflare Content Signals (2025-09-24): `search`/`ai-input`/`ai-train` inside robots.txt, managed robots.txt on 3.8M domains; Mueller 2026-07-06: "no effects whatsoever … just adds bloat". GEO vendors (2026): llms.txt = "cheap standards-track insurance / agent-readiness", not a visibility tactic; schema (FAQPage/ClaimReview) claims of citation lift are TENTATIVE.

## References (B)
1. https://seranking.com/blog/llms-txt/ — 300k study — study
2. https://ahrefs.com/blog/llmstxt-study/ — 137k log study — study
3. https://www.rankability.com/data/llms-txt-adoption/ — Tranco series — study
4. https://caseyrb.com/blog/state-of-llms-txt-adoption/ — HTTP Archive tiers — study
5. https://www.chris-green.net/post/million-websites-in-search-of-llms-txt — Majestic Million — study
6. https://inite.ai/en/blog/is-llms-txt-dead-2026 — synthesis — blog
7. https://www.searchenginejournal.com/google-says-llms-txt-comparable-to-keywords-meta-tag/544804/ — Mueller — docs
8. https://searchengineland.com/google-says-normal-seo-works-for-ranking-in-ai-overviews-and-llms-txt-wont-be-used-459422 — Illyes — docs
9. https://developers.google.com/search/docs/appearance/ai-features — Google guidance — docs
10. https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/ — Originality 8.8x — blog
11. https://ahrefs.com/blog/what-is-llms-txt/ — no provider supports — blog
12. https://www.mintlify.com/blog/the-value-of-llms-txt-hype-or-real — anecdotes — vendor
13. https://www.mintlify.com/blog/what-is-llms-txt — rollout — vendor
14. https://www.shopifreaks.com/shopify-quietly-rolls-out-native-llms-txt-files-for-stores-adding-structured-data-layer-for-ai-agents/ — Shopify — blog
15. https://directory.llmstxt.cloud/ — 4,000 — vendor
16. https://llmstxthub.com/ — 2,650 — vendor
17. https://github.com/SecretiveShell/Awesome-llms-txt — 784 — forum
18. https://www.llms-text.com/blog/sites-using-llms-txt — vendor
19. https://originality.ai/blog/llms-txt-tracking-study — 36,120 — study
20. https://presenc.ai/research/state-of-llms-txt-2026 — vendor
21. https://www.365i.co.uk/news/2025/12/09/google-llms-discover-ai-mode-2025/ — sighting — blog
22. https://searchengineland.com/google-llms-txt-chrome-lighthouse-478246 — Lighthouse — docs
23. https://otterly.ai/blog/the-llms-txt-experiment/ — study
24. https://www.wislr.com/articles/ai-bot-behavior-log-analysis/ — study
25. https://www.ezy.ai/research/do-ai-bots-read-llms-txt — study
26. https://news.ycombinator.com/item?id=47058870 — forum
27. https://searchengineland.com/no-llms-txt-is-not-the-new-meta-keywords-458199 — blog
28. https://www.llms-text.com/blog/what-is-llms-txt — vendor
29. https://gitdoc.ai/blog/llms-txt-ai-readable-documentation — vendor
30. https://blog.cloudflare.com/content-signals-policy/ — docs
31. https://www.seroundtable.com/google-cloudflare-content-signals-41631.html — docs
