# Orchestrator fetch log + notes (2026-08-30)

## Fetched this run (citation-existence log)
- https://llmstxt.org/ (HTML) + https://llmstxt.org/index.md (v2 spec, full text, 13.6 KB) + https://llmstxt.org/changes.md (v2 changes) + https://llmstxt.org/llms.txt (its own index) + https://llmstxt.org/intro.html.md (python lib docs)
- https://developer.chrome.com/docs/lighthouse/agentic-browsing/llms-txt (Lighthouse audit; updated 2026-05-05)
- https://www.mintlify.com/docs/ai/llmstxt (generator docs; 100k-char split into /_llms/)
- https://www.llms-text.com/blog/what-is-llms-txt, /how-to-create-llms-txt, /sites-using-llms-txt, /llms-txt (Michael Vereb, 2025-07-25; vendor)
- https://gitdoc.ai/blog/llms-txt-ai-readable-documentation (vendor, 2026-05-22; fetched via curl, WebFetch 403)
- Live samples: https://developers.cloudflare.com/llms-full.txt (frontmatter page format), https://docs.github.com/llms.txt (API-first index), https://docs.anthropic.com/llms.txt (non-standard: no blockquote, prose sections), https://code.claude.com/docs/llms-full.txt (Mintlify `# Title` + `Source:` blocks, 191 pages, 8.5 MB)

## Spec v2 (llmstxt.org, published 2024-09-03, modified 2026-08-10) — FACT (primary)
- Placement: `/llms.txt` at root OR any subpath; "A file covers the URLs under its path, and where more than one file applies, agents should use the most specific one." → this is the nesting/family mechanism.
- Order: optional BOM; H1 (only required); blockquote summary; free-form non-heading sections; H2 "file list" sections, each entry `- [name](url): optional notes`.
- `## Optional`: "by convention, for secondary information: links an agent can skip when a shorter context is needed" — v2 REMOVED its mechanical semantics (see changes).
- Markdown twins: `page.html.md` (append) OR `page.md` (replace ext); directories → `index.html.md` / `index.md`.
- Discovery: `rel="alternate" type="text/markdown"` → page's markdown; `rel="describedby"` → covering llms.txt; as HTML <link> or HTTP `Link:` header (works for non-HTML and can be set at CDN). Example header: `Link: </docs/page.html.md>; rel="alternate"; type="text/markdown", </docs/llms.txt>; rel="describedby"`.
- Consumption expectation (v2): agents view/search llms.txt, then follow links to LLM-friendly content; file stays small; detail behind links.
- Guidelines: concise; informative link descriptions; no unexplained jargon; test by giving an agent only the llms.txt.
- Directories named: llmstxt.site, directory.llmstxt.cloud, llmstxthub.com. Integrations named: Mintlify, GitBook, Yoast, AIOSEO, Wix, vitepress-plugin-llms, docusaurus-plugin-llms, Drupal llm_support, llms-txt-php, PagePilot, server-llm-txt (MCP).
- Rationale vs .well-known (RFC 8615): path-scoped files let a GitHub-Pages project participate; robots.txt = access; sitemap.xml = exhaustive, no .md versions, no external URLs, too big.
- Claims: "thousands of sites"; OpenAI (developers.openai.com/llms.txt), Anthropic (docs.anthropic.com/llms.txt), Gemini (ai.google.dev/gemini-api/docs/llms.txt) publish one; Lighthouse audits.

## v2 changes (llmstxt.org/changes.md, Aug 2026) — FACT
- Discoverability via link relations added; both .md URL forms allowed; subpath semantics defined (most specific wins); `llms_txt2ctx` context-expansion tooling REMOVED from the proposal; `Optional` keeps no mechanical meaning.

## Python lib (llmstxt.org/intro.html.md) — FACT (docs; now legacy per v2)
- `pip install llms-txt`; CLI `llms_txt2ctx llms.txt > llms.md` (`--optional True`); `parse_llms_file(text)` → keys title, summary, info, sections.

## Lighthouse (developer.chrome.com, updated 2026-05-05) — FACT
- "Agentic browsing" category; flags only on server error fetching /llms.txt; 404 = Not Applicable (optional); expects the spec format ("concise Markdown summary of your site's purpose and key links"); sibling audits: WebMCP, accessibility for agents, layout stability.

## Mintlify (docs) — FACT (vendor docs)
- Auto-generates llms.txt + llms-full.txt at docs root; llms.txt: H1, blockquote from docs.json, optional `markdown.instructions` agent instructions, sections with links (+ `.md` extension), OpenAPI/AsyncAPI links, external links under Optional; llms-full.txt = each page as title, source URL, description, full markdown; llms.txt cap 100,000 chars → split into `/_llms/` sub-indexes with breadcrumbs/page counts; custom llms.txt/llms-full.txt at project root override; auth sites: files require auth or list public pages only.
- Observed format (code.claude.com/docs/llms-full.txt): `# <Title>\nSource: <url>\n\n<markdown>` per page; per-page `.md` twins start with a `> ## Documentation Index / Fetch the complete documentation index at: …/llms.txt` blockquote.

## Cloudflare llms-full.txt observed format — FACT (live sample)
- Per page: YAML frontmatter (`---\ndescription:\ntitle:\nimage:\n---`), then `[Skip to content]`, then `> Documentation Index …/<product>/llms.txt` blockquote, then `# Title`, "Last updated …|Copy as Markdown|[View as Markdown](<url>/index.md)|[Agent setup]"; per-product llms.txt at `/<product>/llms.txt` (subpath scheme). 57 MB total.

## GitHub docs llms.txt — FACT (live sample)
- Index points to JSON/markdown APIs (Page List API, Article Body API returns markdown, Search API) + MCP server, before content sections — "API-first llms.txt" pattern.

## Anthropic docs llms.txt — FACT (live sample)
- Non-conforming shape: H1, then prose "This file provides an overview…", `## Root URL`, language list… (no blockquote). Shows that consumers must be lenient.

## llms-text.com (Vereb, 2025-07-25; vendor, low credibility for numbers)
- Recommends 10–50 (elsewhere 10–20) evergreen pages, 4–7 H2s, 10–20-word descriptions; Content-Type text/plain or text/markdown; HTTP 200 (no redirects/auth); UTF-8; `Link: <…/llms.txt>; rel="describedby"` header; validator + generator products; "llms-small.txt" mentioned; llms-full "deep-crawls up to 50 subpages" (their generator's cap); unattributed benchmark claims (114% tokens, 10-15% accuracy, 67.1%); code snippets for Next.js route handler, Astro endpoint, WordPress functions.php rewrite, Cloudflare Worker; prompt-injection risk via linked markdown (OWASP LLM01).
## gitdoc.ai (Llada, 2026-05-22; vendor)
- GitBook: 41% of docs page requests from AI agents (unverified); robots=permission / sitemap=inventory / llms.txt=navigation; curate 10–20 pages: quickstart, auth, top-level reference (one per resource), errors, changelog; exclude marketing, individual changelog entries, SEO dupes, login-gated; description quality example (bad: "Authentication docs." good: "API key creation, OAuth 2.0 scopes, token rotation, IP allowlisting. Required before any API call."); regenerate in the build to avoid drift; llms-full for "priority" pages.
