---
title: 'llms.txt: the spec and its grammars'
description: 'Spec v2, llms-full grammars, discovery, consumers.'
section: reference
order: 10
sources:
  - skills/document-formats/references/llms-txt.md
---

<!-- provenance: /dr deep-research 2026-08-30 (v2 rewrite of the 2026-05 spoke); hub: document-formats; siblings: llms-txt-generation-tooling.md · llms-txt-ecosystem-evidence.md · llms-txt-recreation-and-aggregation.md -->
verified-as-of: 2026-08-30

**Contents**
1. What it is, in one paragraph
2. The spec, v2 (verbatim structure and the rules that changed)
3. The file grammars in the wild — llms.txt, llms-full.txt (three variants), `.md` twins
4. Discovery: link relations, `Accept: text/markdown`, Lighthouse
5. How consumers actually use it (and who doesn't)
6. Spec gaps, validators, security
7. Related files: robots.txt, sitemap.xml, ai.txt, Content Signals
8. References

> **Honesty note (carry into every recommendation).** `llms.txt` is a *proposal*, not a ratified standard, now at **v2 (modified 2026-08-10)**.[^1] Google says it neither reads nor plans to read it;[^12][^13] server-log studies find 97% of files get zero AI requests.[^14] The one consumer class that demonstrably fetches it is **agents that are pointed at it** — coding agents, MCP doc tools, RAG pipelines: in Ahrefs' 137k-domain log study the `Claude-Code` user agent out-fetched every AI retrieval bot bar two (statespace-indexer, GPTBot).[^14] Design for that use, not for search visibility.

## 1. What it is, in one paragraph

A markdown file — `/llms.txt` at a site root or **at any subpath** — that gives a language model a curated, priority-ordered map of a site's LLM-friendly content: an H1, a blockquote summary, optional prose, then H2 sections of `- [name](url): description` links.[^1] The links should point at clean markdown (a `.md` twin of each page), so the index stays small enough for context and the detail is fetched only when needed.[^1] Proposed by Jeremy Howard (Answer.AI) on 2024-09-03; revised to v2 on 2026-08-10 after "thousands of sites" adopted it and documentation platforms began generating it automatically.[^1][^2]

## 2. The spec, v2

Structure, in order (verbatim from llmstxt.org):[^1]

- "An optional byte-order mark (BOM)"
- "An H1 with the name of the project or site. This is the only required section"
- "A blockquote with a short summary of the project, containing key information necessary for understanding the rest of the file"
- "Zero or more markdown sections (e.g. paragraphs, lists, etc) of any type except headings, containing more detailed information about the project and how to interpret the provided files"
- "Zero or more markdown sections delimited by H2 headers, containing 'file lists' of URLs where further detail is available" — each entry "a required markdown hyperlink `[name](url)`, then optionally a `:` and notes about the file."

The spec's own mock example:[^1]

```markdown
# Title

> Optional description goes here

Optional details go here

## Section name

- [Link title](https://link_url): Optional link details

## Optional

- [Link title](https://link_url)
```

**Placement and scope (new in v2).** "The llms.txt file spec is for files named `llms.txt`, at the root path `/llms.txt` of a website or at any subpath (e.g. `/docs/llms.txt`). A file covers the URLs under its path, and where more than one file applies, agents should use the most specific one."[^1] This is what lets a project that only controls a path (a GitHub Pages site) participate, and it is the mechanism for hub-and-spoke indexes (see sibling *recreation-and-aggregation*). The spec explicitly rejects `/.well-known/` (RFC 8615) because well-known URIs exist only at the origin root.[^1] The `.well-known` request (issue #2) is still open and Mintlify serves both locations.[^3][^4]

**`## Optional`.** v1 gave it mechanical meaning ("the URLs provided there can be skipped if a shorter context is needed"); v2 keeps it only as a convention "for secondary information" and states the context-expansion tooling "is no longer part of the proposal".[^1][^2] Do not build logic that depends on it.

**Markdown twins (widened in v2).** Provide a clean markdown version of each page at the same URL "either with `.md` appended (`page.html.md`) or with the extension replaced by `.md` (`page.md`). (URLs without file names should append `index.html.md` or `index.md` instead.)"[^1]

**What v2 changed and why** (llmstxt.org/changes):[^2] link-relation discovery added; both `.md` URL forms allowed; subpath semantics defined; `llms_txt2ctx` removed from the proposal and with it the special meaning of `Optional`; background rewritten around how agents actually use sites. Search Engine Journal's coverage notes the syntax "might still change before everything is finalized".[^5]

**Consumption expectation (v2).** "Agents are expected to view or search `llms.txt` to find the information they need, then follow the relevant links … The file itself stays small enough to fit in context. The detail lives behind the links, and is fetched only when needed."[^1] Authoring guidance in the spec: concise language, informative link descriptions, no unexplained jargon, and "test your file by asking an agent questions about your content, giving it only your llms.txt as a starting point."[^1]

## 3. The file grammars in the wild

### 3.1 llms.txt — three real shapes

| Shape | Example | Notes |
|---|---|---|
| Spec-conformant | code.claude.com/docs/llms.txt, FastHTML | H1, blockquote, H2 sections, `.md` links |
| API-first | docs.github.com/llms.txt | first H2 "How to use" lists JSON/markdown APIs (Page List, Article Body → markdown, Search) and the MCP server before any content links[^6] |
| Non-conformant prose | docs.anthropic.com/llms.txt | H1, then prose and `## Root URL` / language lists, no blockquote[^6] |

Consequence: a parser must be lenient — treat the H1 as the only invariant and everything before the first H2 as "info".

### 3.2 llms-full.txt — not in the spec, and three grammars

`llms-full.txt` (the whole docset inlined into one markdown file) appears nowhere in the v1/v2 spec text or the repo README.[^7] Mintlify says it "was developed by Mintlify in collaboration with customer Anthropic";[^8] Lab451 dates its popularisation to early 2025.[^9] There is **no single page-block grammar**; three verified variants:

| Producer | Page block | Verified sample |
|---|---|---|
| Mintlify | `# Title` / `Source: <url>` / blank / description / body; pages separated by blank lines only | code.claude.com/docs/llms-full.txt (191 pages, 8.5 MB); mintlify.com/docs/llms-full.txt[^7] |
| Anthropic platform | site H1, `---`, then per-page `## Heading` + YAML block (`title:` / `url:` / `description:`) + raw MDX | platform.claude.com/docs/llms-full.txt[^7] |
| Cloudflare | YAML frontmatter (`description:` / `title:` / `image:`), a "Documentation Index" blockquote pointing at the covering `/<product>/llms.txt`, `# Title`, a `[View as Markdown](…/index.md)` line, body | developers.cloudflare.com/llms-full.txt (57 MB)[^6] |
| Firecrawl generators | pages delimited by `<\|firecrawl-page-N-lllmstxt\|>` | create-llmstxt-py[^10] |

A robust splitter therefore needs at least: `# Title` immediately followed by `Source:` (Mintlify); a `---` YAML block carrying `url:`/`title:`; frontmatter + `View as Markdown` link (Cloudflare); and explicit delimiters.

**Size reality.** Mintlify caps a generated *index* at 100,000 characters and splits overflow into `/_llms/` sub-indexes but sets no cap on llms-full.txt;[^4] Fern **dropped** llms-full.txt because it "exceeded most model context windows, added heavy serving overhead, saw little use";[^11] Nuxt sizes its files at ~5K vs ~1M+ tokens and gates the full file to "200K+ token" tools;[^15] Mantine replaced a 2.2 MB inline file with a 45 KB link list after complaints that it "clogs the AI's context window";[^16] Cursor's moderators say indexed files above ~50–60k tokens become unstable.[^17] Anthropic's docs.anthropic.com llms-full.txt is 41.6 MB.[^6]

### 3.3 `.md` twins

Mintlify, Fern, GitBook and ReadMe all serve a `.md` twin per page and link them from llms.txt "so AI tools can fetch the Markdown version of each page directly".[^4][^11] Mintlify's twins begin with a blockquote — `> ## Documentation Index` / `Fetch the complete documentation index at: …/llms.txt` — that a consumer should strip before indexing.[^6]

## 4. Discovery

- **Link relations (spec v2).** `rel="alternate" type="text/markdown"` → the page's markdown twin; `rel="describedby"` → the llms.txt that covers it; as HTML `<link>` or an HTTP `Link:` header, which "also works for non-HTML resources … and can be added in web server or CDN configuration". Example: `Link: </docs/page.html.md>; rel="alternate"; type="text/markdown", </docs/llms.txt>; rel="describedby"`.[^1]
- **`Accept: text/markdown` content negotiation** is *not* in the spec. Vercel proposed it (2026-02-03) precisely because it "requires no site-specific knowledge";[^18] Mintlify, GitBook and Fern honour it (Mintlify adds `X-Robots-Tag: noindex, nofollow` and prepends the llms.txt blockquote);[^4][^19] **Cloudflare "Markdown for Agents"** (2026-02-12, Pro/Business/Enterprise) converts any proxied HTML at the edge and returns `Content-Type: text/markdown`, `x-markdown-tokens`, `x-original-tokens`, `Vary: Accept`, dropping ETag/Last-Modified, with a 2 MB origin cap and no advance-discovery mechanism — clients just try.[^20] Uptake is thin: one 44-day log saw 1,421 such requests, none from GPTBot/PerplexityBot/ClaudeBot.[^21] Origin implementations must add `Vary: Accept` and bypass full-page caches keyed without it.[^22]
- **Chrome Lighthouse** (13.3, May 2026; doc updated 2026-05-05) has an "Agentic browsing" category that fetches `/llms.txt`: a 404 is *Not Applicable*, a server error is flagged; sibling audits cover WebMCP, agent accessibility and layout stability.[^23]

## 5. How consumers actually use it

| Consumer | Behaviour | Evidence |
|---|---|---|
| Reference `llms_txt2ctx` | regex-parse, fetch every link, emit XML `<project title summary><docs><doc …>`; `--optional True` includes the Optional section; removed from the proposal in v2 | [^24][^2] |
| LangChain `mcpdoc` (MCP) | `list_doc_sources` + `fetch_docs`; the *agent* decides which links to follow; allowlists only the llms.txt's domain | [^25] |
| Claude Code | Anthropic publishes its docs index and points the agent at it; Ahrefs' logs show the `Claude-Code` UA out-fetching every AI retrieval bot bar two (statespace-indexer, GPTBot); no documented *automatic* lookup — it is fetched when directed | [^14][^26] |
| Cursor `@Docs` | crawls URLs; "cannot recognise llms.txt" request acknowledged (Jun 2025), no documented support; >50–60k tokens unstable; its own llms.txt once redirected to an HTML app shell | [^17][^27] |
| Windsurf, Copilot | `@docs` is a curated list; Copilot feature request unanswered as of Jul 2026 | [^28][^29] |
| ChatGPT, Perplexity, Google | no statements of use; logs ≈ 0 requests; Google: "You don't need to create new machine readable files" | [^12][^13][^14] |

Budgeting in practice is **producer-side splitting**, not consumer-side truncation: Mintlify's `/_llms/` recursion, Starlight's `llms-small.txt`, Nuxt's two sizes, Firecrawl's page delimiters, Jina Reader's `x-max-tokens`, Cloudflare's token-count headers.[^4][^15][^10][^20]

## 6. Spec gaps, validators, security

- No official validator. Community validators grade A–F and are **stricter than the spec** (blockquote required, absolute URLs, `Optional` last);[^30] the spec requires only the H1.[^1] `llms-txt-validator --check-links` gives JSON for CI; stale links are a real failure (litellm's file carried a deleted page, Aug 2026).[^31][^32]
- Open gaps (repo issues): H2 ordering carries no defined meaning; no version/provenance field (#132/#133); which language a root file is (#147); and **behavioural steering** — issue #152 (2026-08-29) found 42.3% of 100 sampled files try to shape model answers, with no security-considerations section in the spec.[^33]
- Prompt injection: a linked markdown file is untrusted input; treat everything fetched via llms.txt as data (OWASP LLM01).[^34] Ahrefs flags the same risk; no incident data found.[^14]
- Parser reference (core.py): header `^#\s*{title}\n+{summ}\n+{info}`; sections on `^##\s*(.*?$)`; links `-\s*\[{title}\]\({url}\){desc}`.[^24] JS ports: the spec page's sample `parseLLMsTxt()` and npm `llms-txt-parser` (→ `{title, overview, links[{title,url,description,section}]}`); PHP `llms-txt-php`.[^1][^35]

## 7. Related files

| File | Job | Do AI bots fetch it? |
|---|---|---|
| `robots.txt` | access control; now also carries Cloudflare **Content Signals** (`Content-Signal: search=yes, ai-input=…, ai-train=no`, 2025-09-24) | yes, thousands of times per site; Content Signals: Google says "no effects whatsoever"[^36][^37] |
| `sitemap.xml` | exhaustive inventory; no `.md` versions, no external links | yes (ClaudeBot, GPTBot, Bingbot)[^38] |
| `llms.txt` | curated navigation for agents pointed at it | ~0 speculative fetches; agents when directed[^14] |
| `ai.txt` | opt-out preferences (IETF draft) | 397 instances found May 2026[^39] |
| `agents.md` / `/.well-known/ucp` | Shopify's agent-commerce additions shipped with llms.txt to every store (May 2026) | n/a[^40] |

## References

[^1]: https://llmstxt.org/ and https://llmstxt.org/index.md — "The /llms.txt file, v2", 2024-09-03, modified 2026-08-10 (spec)
[^2]: https://llmstxt.org/changes.md — v1→v2 changes (spec)
[^3]: https://github.com/AnswerDotAI/llms-txt/issues/2 — `.well-known` proposal, open (forum)
[^4]: https://www.mintlify.com/docs/ai/llmstxt — generation, 100k-char split, `.well-known` copy, `.md` links (docs)
[^5]: https://www.searchenginejournal.com/llms-txt-v2-formal-markdown-linking-ai-agents/586119/ — v2 coverage, 2026-08-17 (blog)
[^6]: Live samples fetched 2026-08-30: https://docs.github.com/llms.txt, https://docs.anthropic.com/llms.txt (+ llms-full.txt 41.6 MB), https://developers.cloudflare.com/llms-full.txt, https://code.claude.com/docs/llms-full.txt (docs)
[^7]: https://raw.githubusercontent.com/AnswerDotAI/llms-txt/main/nbs/index.qmd (0 occurrences of llms-full); https://www.mintlify.com/docs/llms-full.txt; https://platform.claude.com/docs/llms-full.txt (spec/docs)
[^8]: https://www.mintlify.com/blog/what-is-llms-txt — "developed by Mintlify in collaboration with … Anthropic" (vendor)
[^9]: https://lab451.org/blog/llms-txt-complete-guide-2026 — llms-full not in spec; sizes (blog)
[^10]: https://github.com/firecrawl/create-llmstxt-py — page delimiters, GPT-4o-mini descriptions (readme)
[^11]: https://buildwithfern.com/learn/docs/ai-features/llms-txt — Fern dropped llms-full.txt (docs)
[^12]: https://www.searchenginejournal.com/google-says-llms-txt-comparable-to-keywords-meta-tag/544804/ — Mueller, 2025-04-17 (docs)
[^13]: https://developers.google.com/search/docs/appearance/ai-features — "no new machine readable files", 2025-12-10 (docs)
[^14]: https://ahrefs.com/blog/llmstxt-study/ — 137,210-domain log study, May 2026 logs: 97% zero requests; Claude-Code UA (study)
[^15]: https://nuxt.com/docs/4.x/guide/ai/llms-txt — ~5K vs ~1M+ tokens (docs)
[^16]: https://github.com/orgs/mantinedev/discussions/8523 — 2.2 MB → 45 KB (forum)
[^17]: https://forum.cursor.com/t/is-there-any-size-limit-for-llms-txt-indexed-as-docs/148660 — 50–60k tokens (forum)
[^18]: https://vercel.com/blog/making-agent-friendly-pages-with-content-negotiation — 2026-02-03 (blog)
[^19]: https://www.mintlify.com/blog/context-for-agents — Accept header, noindex (vendor)
[^20]: https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/ and https://developers.cloudflare.com/changelog/post/2026-02-12-markdown-for-agents/ (docs)
[^21]: https://suganthan.com/blog/cloudflare-markdown-for-agents/ — 44-day log (blog)
[^22]: https://toddmorourke.com/learn/markdown-for-agents/ — origin implementation, cache pitfall (blog)
[^23]: https://developer.chrome.com/docs/lighthouse/agentic-browsing/llms-txt — audit criteria, updated 2026-05-05 (docs)
[^24]: https://llmstxt.org/intro.html and https://github.com/AnswerDotAI/llms-txt/blob/main/llms_txt/core.py (docs/spec)
[^25]: https://github.com/langchain-ai/mcpdoc (readme)
[^26]: https://code.claude.com/docs/llms.txt (docs)
[^27]: https://forum.cursor.com/t/cursor-not-support-llms-txt-standard/108980 and https://forum.cursor.com/t/docs-cursor-com-llms-txt-serves-an-html-page-instead-of-the-llms-txt-file/167800 (forum)
[^28]: https://docs.devin.ai/windsurf/plugins/cascade/web-search (docs)
[^29]: https://github.com/orgs/community/discussions/162955 (forum)
[^30]: https://alejandrorioja.com/tools/llms-txt-validator/ and https://llmstxtvalidator.dev/ (docs)
[^31]: https://github.com/bridgetoagent/llms-txt-validator (readme)
[^32]: https://github.com/BerriAI/litellm/issues/36342 (forum)
[^33]: https://github.com/AnswerDotAI/llms-txt/issues/152 and https://github.com/AnswerDotAI/llms-txt/issues (forum)
[^34]: https://www.llms-text.com/blog/llms-txt — injection via linked markdown, OWASP LLM01 (vendor)
[^35]: https://libraries.io/npm/llms-txt-parser (docs)
[^36]: https://blog.cloudflare.com/content-signals-policy/ (docs)
[^37]: https://www.seroundtable.com/google-cloudflare-content-signals-41631.html — Mueller, 2026-07-06 (docs)
[^38]: https://www.wislr.com/articles/ai-bot-behavior-log-analysis/ (study)
[^39]: https://originality.ai/blog/llms-txt-tracking-study (study)
[^40]: https://www.shopifreaks.com/shopify-quietly-rolls-out-native-llms-txt-files-for-stores-adding-structured-data-layer-for-ai-agents/ (blog)
