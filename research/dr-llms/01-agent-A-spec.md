# Agent A — spec & formats (researched 2026-08-30; 17 queries, 8 negation)

- v2 spec titled "The /llms.txt file, v2", published 2024-09-03, date-modified 2026-08-10 (commits "discoverability", "v2", "changes"). FACT.
- Structure in order: optional BOM (new in v2); H1 (only required); blockquote summary; free-form non-heading sections; H2 "file list" sections, entries `- [name](url)` + optional `: notes`. FACT.
- `## Optional`: v1 "the URLs provided there can be skipped if a shorter context is needed"; v2 "by convention, for secondary information" + Changes: "no longer carry mechanical semantics". FACT.
- Location: v1 root "(or, optionally, in a subpath)"; v2 defines scoping: covers URLs under its path; most specific wins; rejects /.well-known/ (RFC 8615) because path-only publishers (GitHub Pages) can't use it; issue #2 (.well-known) still open; W3C strategy issue #506 flags collisions; Mintlify ALSO serves /.well-known/llms.txt. QUALIFIED on the well-known controversy.
- Markdown-only rationale unchanged v1→v2.
- llms-full.txt: Mintlify says co-developed with Anthropic; NOT in spec text (0 occurrences in v1/v2/README); Lab451: "not part of the official spec", popularized early 2025; spec's own full-context analogue was FastHTML's llms-ctx-full.txt (XML). TENTATIVE/contested origin.
- llms-full grammars (verified): Mintlify = `# Title` / `Source: <url>` / blank / description / body, pages separated by blank lines only; Anthropic platform.claude.com/docs/llms-full.txt = site H1, `---`, per-page `## Heading` + YAML block (title/url/description) + raw MDX. Two grammars → no single standard. FACT. (Orchestrator adds a third: Cloudflare frontmatter blocks.)
- Sizes: Mintlify caps llms.txt at 100,000 chars (split to /_llms/), no cap for llms-full; W3C: llms-full may exceed context windows; Lab451: llms.txt 1–10 KB, llms-full 100 KB–several MB. QUALIFIED.
- Twins: v1 `.md` appended (`index.html.md`); Answer.AI blog said `index-commonmark.md` (inconsistency); v2 allows `page.html.md` OR `page.md`, `index.html.md` OR `index.md`. Discovery: `rel="alternate" type="text/markdown"`, `rel="describedby"`, via <link> or `Link:` header. FACT.
- `Accept: text/markdown` content negotiation is NOT in the spec; Vercel proposed it 2026-02-03 (rejects separate .md URLs: negotiation "requires no site-specific knowledge"); Mintlify serves markdown on that header and prepends an llms.txt blockquote. QUALIFIED.
- Anthropic llms.txt: `.md` links, ends with pointer to llms-full.txt, no Optional section.
- Reference impl: `pip install llms-txt`; `llms_txt2ctx llms.txt > llms.md` (`--optional True`); `parse_llms_file()` → title, summary, info, sections; `create_ctx()` → XML `<project title summary><docs><doc title desc>`; core.py regexes: header `^#\s*{title}\n+{summ}\n+{info}`, sections `^##\s*(.*?$)`, links `-\s*\[{title}\]\({url}\){desc}`; `mk_ctx()` skips the section literally named `Optional` when optional=False. Package CHANGELOG to 0.0.6 (adds llms_txt2html). v2 removed the tool from the proposal. FACT.
- JS: llmstxt.org sample parseLLMsTxt(); npm `llms-txt-parser` 1.0.2 (Jun 2025) → {title, overview, links[{title,url,description,section}]}; PHP `llms-txt-php`. QUALIFIED.
- Validators: none official; community validators (alejandrorioja, llms-txt.io, llmstxtvalidator.dev) grade A–F and are STRICTER than spec (blockquote required, absolute URLs, Optional last). FACT/QUALIFIED.
- Spec gaps: H2 ordering meaning (none); non-Optional section semantics (none); no version/provenance field (issues #132/#133 propose); multilingual (#147, Aug 2026); behavioural "guidance to the model" — issue #152 (2026-08-29): 42.3% of 100 sampled files try to shape model answers; no security-considerations section. QUALIFIED.
- Multiple files per site: issue #18 (Nov 2024) → v2 most-specific rule. FACT.
- SEJ 2026-08-17: syntax "might still change before everything is finalized". Repo Apache-2.0, 2.6k stars, 73 open issues (Aug 2026).

## References (A)
1. https://raw.githubusercontent.com/AnswerDotAI/llms-txt/main/nbs/index.qmd — v2 source — spec
2. https://github.com/AnswerDotAI/llms-txt — repo — spec
3. https://www.answer.ai/posts/2024-09-03-llmstxt.html — announcement — blog
4. https://raw.githubusercontent.com/AnswerDotAI/llms-txt/f030fe84.../nbs/index.qmd — v1 text — spec
5. https://llmstxt.org/changes.html — v1→v2 — spec
6. https://llmstxt.org/ — v2 rendered — spec
7. https://github.com/AnswerDotAI/llms-txt/issues/2 — .well-known — forum
8. https://github.com/w3c/strategy/issues/506 — W3C — forum
9. https://www.mintlify.com/docs/ai/llmstxt — Mintlify docs — docs
10. https://www.mintlify.com/blog/what-is-llms-txt — co-developed claim — blog
11. https://lab451.org/blog/llms-txt-complete-guide-2026 — not in spec; sizes — blog
12. https://www.mintlify.com/docs/llms-full.txt — live sample — docs
13. https://platform.claude.com/docs/llms.txt + /docs/llms-full.txt — Anthropic samples — docs
14. https://www.searchenginejournal.com/llms-txt-v2-formal-markdown-linking-ai-agents/586119/ — v2 coverage — blog
15. https://vercel.com/blog/making-agent-friendly-pages-with-content-negotiation — Accept: text/markdown — blog
16. https://www.mintlify.com/blog/context-for-agents — Mintlify negotiation — blog
17. https://llmstxt.org/intro.html — CLI/API — docs
18. https://github.com/AnswerDotAI/llm-ctx — companion — docs
19. https://github.com/AnswerDotAI/llms-txt/blob/main/llms_txt/core.py — parser — spec
20. https://www.fastht.ml/docs/llms-ctx.txt — XML sample — docs
21. https://raw.githubusercontent.com/AnswerDotAI/llms-txt/main/CHANGELOG.md — versions — docs
22. https://llmstxt.org/llmstxt-js.html — JS sample — docs
23. https://libraries.io/npm/llms-txt-parser — npm parser — docs
24. https://alejandrorioja.com/tools/llms-txt-validator/ — validator — docs
25. https://llmstxtvalidator.dev/ — validator — docs
26. https://github.com/AnswerDotAI/llms-txt/issues — issues — forum
27. https://github.com/AnswerDotAI/llms-txt/issues/152 — 100-file study — forum
28. https://github.com/AnswerDotAI/llms-txt/issues/18 — multiple files — forum
29. https://www.searchenginejournal.com/google-says-llms-txt-comparable-to-keywords-meta-tag/544804/ — Mueller — blog
30. https://ahrefs.com/blog/what-is-llms-txt/ — criticism — blog
