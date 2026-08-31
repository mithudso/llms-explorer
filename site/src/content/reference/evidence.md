---
title: 'Ecosystem evidence'
description: 'Who reads these files, measured.'
section: reference
order: 31
sources:
  - skills/document-formats/references/llms-txt-ecosystem-evidence.md
---

<!-- provenance: /dr deep-research 2026-08-30; hub: document-formats; parent spoke: llms-txt.md -->
verified-as-of: 2026-08-30 (every number below is dated; this domain moves monthly)

**Contents**
1. The one-line verdict
2. Adoption measurements, dated
3. Who publishes
4. Who reads — server-log studies
5. Google and the "is it dead" thread
6. Directories and registries
7. Vendor sources graded
8. References

## 1. The one-line verdict

Adoption is real and growing (≈5–10% of the general web by mid-2026, 28% among SEO-savvy sites, 8.8× year on year); *unsolicited* consumption is near zero (97% of files never get an AI request); the demonstrated use is agents that are pointed at the file — the `Claude-Code` UA out-fetched every AI retrieval bot bar two (statespace-indexer, GPTBot).[^1][^2] Publish one for agents and coding tools; do not expect citations or rankings from it.[^3]

## 2. Adoption measurements, dated

| Date | Source | Sample | Finding |
|---|---|---|---|
| Feb→May 2025 | Chris Green | Majestic Million | 15 → 105 valid files (~0.01%); ~100k crawl errors caveat[^4] |
| Jun 2025 | Originality.ai | 3M+ sites | 4,088 llms.txt[^5] |
| Jun 2025 | Rankability | Tranco top 1,000 | 0.3%[^6] |
| Jul 2025 | HTTP Archive (Burridge) | top 10k | 1.04% valid[^7] |
| Nov 2025 | SE Ranking | ~300k domains | 10.13% overall (9.88% low-traffic / 10.54% mid / 8.27% 100k+ visits)[^3] |
| Mar 2026 | Originality.ai via ppc.land | Fortune 500 | 7.4% (37/500)[^8] |
| May 2026 | Originality.ai | 3M+ sites | 36,120 llms.txt (8.8× YoY); llms-full.txt 23 → 2,463 (107×); ai.txt 397[^5] |
| May 2026 | Ahrefs | 137,210 Ahrefs-Web-Analytics domains | 28% publish a valid file (self-selected sample)[^1] |
| Jun 2026 | HTTP Archive (Burridge) | top 1k / 10k / 100k / 1M | 6.28% / 5.61% / 5.17% / 5.07% (~5.4× in 12 months)[^7] |
| Jun 2026 | Rankability | Tranco top 1,000 | 8.7% (87 files; 15 with llms-full.txt)[^6] |

Contradictions kept: top-1000 adoption reads 6.28% (HTTP Archive/Chrome list) vs 8.7% (Tranco) for the same month;[^6][^7] third parties attribute "0% in the top 1000" to SE Ranking, whose primary article gives no such figure;[^9] Ahrefs' 28% is not comparable with population figures because of sample bias;[^1] a "51.8% of a 219-host panel" claim (Presenc.ai, Aug 2026) has no supporting data on its page.[^10]

## 3. Who publishes

- **Live probe (2026-08-30):** 200 at docs.anthropic.com (72 KB; llms-full.txt 41.6 MB), docs.stripe.com (90 KB, no full), developers.cloudflare.com, vercel.com, supabase.com, docs.perplexity.ai, mintlify.com, docs.github.com, shopify.com, developers.openai.com (5.8 KB), code.claude.com/docs; 404/403 at platform.openai.com, openai.com, ai.google.dev, developers.google.com, learn.microsoft.com. The spec v2 page itself names OpenAI, Anthropic and Gemini developer docs as publishers.[^11]
- **Platform-driven adoption dominates.** Mintlify has generated the files for every hosted site since Nov 2024 (Anthropic, Cursor, Coinbase, Pinecone, Windsurf) and says it co-developed llms-full.txt with Anthropic;[^12][^13] Shopify silently added `/llms.txt`, `/llms-full.txt`, `/agents.md` and `/.well-known/ucp` to every store in the first week of May 2026 — HTTP Archive shows 78.1% of top-10k Shopify hosts vs 8.7% of WordPress.[^14][^7]
- **Top-1000 adopters (Rankability, Aug 2026):** Cloudflare, Azure, GitHub, Fastly, WordPress.org/.com, DigiCert, Adobe, Opera, Samsung, Sentry.[^6]

## 4. Who reads — server-log studies

| Study | Window / sample | Finding |
|---|---|---|
| Ahrefs (2026-06-15) | May 2026 logs, 137,210 domains | **97% of valid files got zero requests**; of requests, 96% bots, 77% of those non-AI (SEO auditors 21.7%); named AI bots 19.5%; AI training crawlers 5.3% (GPTBot 4.51%, ClaudeBot 0.8%); AI retrieval 1.1% (OAI-SearchBot 0.74%); **0 AI requests to non-existent files** (nobody probes speculatively); the `Claude-Code` UA out-fetched every AI retrieval bot bar statespace-indexer and GPTBot[^1] |
| OtterlyAI (2026-02-05) | 90 days, one site | 84 of 62,100 AI-bot requests hit /llms.txt (0.1%)[^15] |
| Wislr (Feb–Mar 2026) | 48 days, one site | 12,099 bot requests; robots.txt fetched hundreds of times (OAI-SearchBot 180, ClaudeBot 175); sitemap.xml too; **llms.txt 0**[^16] |
| EZY Research (Apr–Jul 2026) | 83 sites, 12 weeks | robots vs llms: GPTBot 3,990/7, ClaudeBot 3,120/9, PerplexityBot 775/0, Googlebot 5,125/67, **Meta-ExternalAgent 172/193** (the only bot fetching it more than robots.txt)[^17] |
| Hacker News thread (Feb 2026) | anecdotal logs | only OVH/GCP-hosted tools (WebPageTest, BuiltWith), no ChatGPT/Claude UAs[^18] |
| Cloudflare `Accept: text/markdown` (Mar–Apr 2026) | 44 days, one Worker | 1,421 requests: headless Chrome 639, "Claude" (Anthropic infra) 500, axios 211; no GPTBot/PerplexityBot/ClaudeBot[^19] |

Citation impact: SE Ranking's 300k-domain model (Spearman + XGBoost + SHAP, 2025-11-07) found **no relationship** between having an llms.txt and LLM citation frequency — removing the variable improved model accuracy.[^3] Correlational; which LLMs' citations were measured is unspecified.

## 5. Google and the "is it dead" thread

- John Mueller, r/TechSEO, 2025-04-17: "AFAIK none of the AI services have said they're using LLMs.TXT (and you can tell when you look at your server logs that they don't even check for it). To me, it's comparable to the keywords meta tag."[^20]
- Gary Illyes, Search Central Deep Dive APAC, Jul 2025: Google "doesn't support LLMs.txt and isn't planning to"; AI Overviews use normal indexing.[^21]
- Google Search Central "AI features and your website" (updated 2025-12-10): "You don't need to create new machine readable files, AI text files, or markup to appear in these features" — use robots.txt, `nosnippet`/`max-snippet`, `Google-Extended`.[^22]
- Ambiguity: Search Central briefly hosted its own `developers.google.com/search/docs/llms.txt` in late Nov 2025, then 404'd it without comment;[^23] Chrome Lighthouse 13.3 (May 2026) added an "Agentic Browsing" audit that checks for the file (404 = Not Applicable; server error flagged).[^24]
- Proponents' rebuttals: unlike meta keywords, the linked content must exist; standards take years; agents "drop into" content rather than crawl; `.md` alternates save bandwidth (Carolyn Shelby, SEL 2025-07-09 — no metrics).[^25] Mintlify cites Profound data that Microsoft/OpenAI bots fetch llms.txt and Vercel's "10% of signups from ChatGPT" — anecdotal.[^12][^13] Howard's proposal targeted inference-time use by coding tools, not GEO; "it's dead" measures a goal it never claimed.[^9][^26]
- Consensus phrase across 2026 analyses: **"not dead, but not a citation lever."**[^9][^5]

## 6. Directories and registries

Self-submitted, overlapping, unverified — lower bounds, not measurements:[^27][^28][^29][^30]

| Directory | Size | Notes |
|---|---|---|
| directory.llmstxt.cloud | "4,000 websites listed" (49M llms.txt tokens / 325M llms-full tokens) | named in spec v2 |
| llmstxthub.com | ~2,650 entries, 15–16 categories (David Dias) | named in spec v2 |
| llmstxt.site | ~1,000+ (≈170 in May 2025); columns product / website / llms.txt / llms-full.txt / **token counts**; `/submit` | named in spec v2 |
| SecretiveShell/Awesome-llms-txt | 784 link lines (counted 2026-08-30) | GitHub |
| llms-text.com | "780+ verified implementations" | vendor's own directory |

None publishes an llms.txt-of-llms.txt; llmstxt.site's token-count column is the most useful signal for consumers budgeting context.[^29]

## 7. Vendor sources graded

| Page | Author / date | Claims | Grade |
|---|---|---|---|
| llms-text.com/blog/sites-using-llms-txt | Michael Vereb, 2025-07-25 | "780+ verified"; names Anthropic, Cloudflare, Supabase, Vercel, ElevenLabs, Firecrawl, Mintlify, Cursor, Aptos, GitBook, Wix; "no e-commerce adoption" | adopters check out on live probe; count uncorroborated — low for numbers, fine for examples[^31] |
| llms-text.com/blog/what-is-llms-txt | same | "foundational pillar of GEO"; ChatGPT/Perplexity/Cursor/Windsurf/Claude Code consume it; "up to 114% more tokens" (incoherent arithmetic), "10–15% accuracy" — unattributed | GEO and ChatGPT/Perplexity-consumption claims contradicted by every log study — low[^32] |
| llms-text.com/blog/llms-txt, /how-to-create-llms-txt | same | MIME/200/UTF-8 rules; `Link: …; rel="describedby"`; "under 10 KB"; framework snippets; funnels to its generator/validator | useful mechanics (the `describedby` relation is now in spec v2), vendor numbers — medium[^33][^34] |
| gitdoc.ai/blog/llms-txt-ai-readable-documentation | Yadian Llada / GitDoc, 2026-05-22 | GitBook: 41% of docs page requests from AI agents (unverified); permission / inventory / navigation distinction; curate 10–20 pages (quickstart, auth, per-resource reference, errors, changelog); regenerate in the build; llms-full for priority pages | sound guidance, unverified headline stat, product promotion — medium[^35] |

## References

[^1]: https://ahrefs.com/blog/llmstxt-study/ — 137,210-domain log study, 2026-06-15 (study)
[^2]: https://caseyrb.com/blog/state-of-llms-txt-adoption/ — HTTP Archive, 2026-06-20 (study)
[^3]: https://seranking.com/blog/llms-txt/ — 300k-domain adoption + citation model, 2025-11-07 (study)
[^4]: https://www.chris-green.net/post/million-websites-in-search-of-llms-txt (study)
[^5]: https://originality.ai/blog/llms-txt-tracking-study (study)
[^6]: https://www.rankability.com/data/llms-txt-adoption/ (study)
[^7]: https://caseyrb.com/blog/state-of-llms-txt-adoption/ (study)
[^8]: https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/ (blog)
[^9]: https://inite.ai/en/blog/is-llms-txt-dead-2026 (blog)
[^10]: https://presenc.ai/research/state-of-llms-txt-2026 (vendor)
[^11]: https://llmstxt.org/ — v2, modified 2026-08-10 (spec); live probes 2026-08-30
[^12]: https://www.mintlify.com/blog/the-value-of-llms-txt-hype-or-real (vendor)
[^13]: https://www.mintlify.com/blog/what-is-llms-txt (vendor)
[^14]: https://www.shopifreaks.com/shopify-quietly-rolls-out-native-llms-txt-files-for-stores-adding-structured-data-layer-for-ai-agents/ (blog)
[^15]: https://otterly.ai/blog/the-llms-txt-experiment/ (study)
[^16]: https://www.wislr.com/articles/ai-bot-behavior-log-analysis/ (study)
[^17]: https://www.ezy.ai/research/do-ai-bots-read-llms-txt (study)
[^18]: https://news.ycombinator.com/item?id=47058870 (forum)
[^19]: https://suganthan.com/blog/cloudflare-markdown-for-agents/ (blog)
[^20]: https://www.searchenginejournal.com/google-says-llms-txt-comparable-to-keywords-meta-tag/544804/ (docs)
[^21]: https://searchengineland.com/google-says-normal-seo-works-for-ranking-in-ai-overviews-and-llms-txt-wont-be-used-459422 (docs)
[^22]: https://developers.google.com/search/docs/appearance/ai-features (docs)
[^23]: https://www.365i.co.uk/news/2025/12/09/google-llms-discover-ai-mode-2025/ (blog)
[^24]: https://searchengineland.com/google-llms-txt-chrome-lighthouse-478246 and https://developer.chrome.com/docs/lighthouse/agentic-browsing/llms-txt (docs)
[^25]: https://searchengineland.com/no-llms-txt-is-not-the-new-meta-keywords-458199 (blog)
[^26]: https://ahrefs.com/blog/what-is-llms-txt/ (blog)
[^27]: https://directory.llmstxt.cloud/ (vendor)
[^28]: https://llmstxthub.com/ (vendor)
[^29]: https://llmstxt.site/ (vendor)
[^30]: https://github.com/SecretiveShell/Awesome-llms-txt (forum)
[^31]: https://www.llms-text.com/blog/sites-using-llms-txt (vendor)
[^32]: https://www.llms-text.com/blog/what-is-llms-txt (vendor)
[^33]: https://www.llms-text.com/blog/llms-txt (vendor)
[^34]: https://www.llms-text.com/blog/how-to-create-llms-txt (vendor)
[^35]: https://gitdoc.ai/blog/llms-txt-ai-readable-documentation (vendor)
