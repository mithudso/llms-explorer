---
description: >-
  Generate/parse/edit/convert document & data-file formats in Python & Node. TRIGGER: PDF
  (pdf-lib, pypdf, ReportLab, text/tables); Word (docx-js, TOC); Excel (openpyxl/pandas, charts);
  PowerPoint (PptxGenJS/python-pptx); CSV/TSV (encoding/BOM, injection); advanced JSON (streaming,
  Ajv/Zod, JSON Patch); draw.io; Markdown/CommonMark/GFM (remark, MDX, Pandoc); write/recreate
  llms.txt + llms-full.txt (spec v2); ai.txt opt-out; robots.txt / RFC 9309 (syntax, precedence,
  crawl-delay, parsers) + the Content-Signal AI-preference extension; agents.md +
  /.well-known/ucp; static llms.txt vs live NLWeb/WebMCP; RSL (XML AI-content licensing, the
  robots.txt License: directive, pay-per-crawl). SKIP: analytical/ETL tabular work → da-* hubs;
  extract FROM aging docs/live DOM → content-ingestion-extraction; in-browser markdown render →
  chrome-extension-expert; llms.txt for AI-search citations → generative-engine-optimization;
  one-off pandoc → document-conversion; EU TDM law → eu-ai-act-tdm-opt-out.
name: document-formats
title: "Document & File Formats"
category: developer
version: "1.6.1"
updated: "2026-09-02"
model: claude-sonnet-5
effort: medium
tags: [pdf, docx, xlsx, pptx, csv, json, drawio, markdown, mdx, pandoc, llms-txt, ai-txt, robots-txt, content-signals, document-generation, file-formats, hub, rsl]
keywords:
  - PDF generation pdf-lib pypdf ReportLab WeasyPrint HTML-to-PDF
  - Word docx generation docx-js tracked changes
  - Excel xlsx openpyxl pandas formulas charts
  - PowerPoint pptx PptxGenJS python-pptx slides
  - CSV TSV parsing streaming encoding formula-injection
  - advanced JSON schema validation JSON Patch JSONPath MessagePack
  - drawio diagrams mxGraphModel export SVG PNG PDF
  - file format conversion document generation
  - Markdown CommonMark GFM MDX Pandoc remark markdown-it authoring processing linting docs-as-code
  - llms.txt llms-full.txt spec v2 generators recreation adoption evidence family index
  - ai.txt Spawning AI-training opt-out TDM robots.txt-style disambiguation vs llms.txt
whenToUse:
  - "generate a PDF report, invoice, or document; convert HTML to PDF; extract text/tables from a PDF"
  - "create or edit a Word .docx (headings, TOC, tracked changes, find-and-replace)"
  - "create, read, or fix an Excel .xlsx (formulas, formatting, charts, messy data)"
  - "generate or edit a PowerPoint .pptx deck (layouts, charts, pptx→PDF)"
  - "parse, generate, stream, or sanitize CSV/TSV; fix encoding or formula-injection"
  - "stream/validate/patch/query advanced JSON (Ajv, Zod, JSON Patch, JSONPath, MessagePack, NDJSON)"
  - "generate or transform a .drawio diagram from code and export it to SVG/PNG/PDF"
  - "produce a report/invoice/memo/deck/spreadsheet/diagram as a file"
  - "author or fix Markdown/MDX (CommonMark vs GFM, frontmatter, tables, alerts, math)"
  - "convert Markdown with Pandoc, pick a docs-as-code SSG, or add markdownlint/Vale/lychee gates"
  - "write, generate, validate, or recreate an llms.txt / llms-full.txt for a site or a product family"
  - "what is ai.txt, how does it differ from llms.txt/robots.txt, or how to author/verify/serve one"
whenNotToUse:
  - "analytical or ETL processing of data where the format is incidental (use da-analytical-methods or da-data-engineering-platform)"
  - "extracting/recovering content from old docs, web DOM, or audio, or templatizing a document (use content-ingestion-extraction)"
  - "prose/structure/voice review of a written document (use writing-expert or technical-writing-craft)"
  - "MongoDB BSON schema design (use mongodb-expert)"
  - "rendering + sanitizing Markdown in a browser or extension UI (use chrome-extension-expert, references/markdown-rendering-browser.md)"
  - "whether llms.txt earns AI-search citations or share-of-voice (use generative-engine-optimization; this hub owns the file itself)"
  - "crawling or mirroring a site's pages into Markdown (use web-text-mirror; this hub assembles the result into llms.txt/llms-full.txt)"
  - "a one-off convert-this-file-to-readable-Markdown via pandoc/pdftotext (use document-conversion)"
  - "converting an existing agent skill's SKILL.md reference dump into an llms.txt family (use skill-to-llms-txt)"
related_skills:
  - da-data-engineering-platform
  - da-analytical-methods
  - content-ingestion-extraction
  - technical-writing-craft
  - chrome-extension-expert
  - generative-engine-optimization
  - web-text-mirror
  - document-conversion
---

# Document & File Formats

Hub for **programmatic document and data-file work**: creating, parsing, editing, and converting
the common office and data formats in Python and Node.js. Each former standalone format skill is now
an on-demand reference file: when a task matches a row in the routing table below, **`Read` that
`references/<name>.md` file before answering** — the routing descriptions are a dispatch index, not the
depth itself.

The boundary that defines this hub: it owns the **file format**: bytes in, bytes out, and the
libraries that manipulate them. When the real question is the *analysis* of the data, the *extraction*
of content from messy sources, or the *prose quality* of a written document, defer to the sibling hubs
named in the cross-hub map.

## Routing detail

Deferrals the description cannot carry within its 1000-character cap (they mirror `whenNotToUse`):
prose, structure or voice of the written document → `writing-expert` / `technical-writing-craft`;
MongoDB BSON schema design → `mongodb-expert`; crawling a site into a Markdown mirror →
`web-text-mirror` (this hub then assembles the mirror into `llms.txt` / `llms-full.txt`).

<!-- ROUTING TABLE: document-formats: auto-generated; edit the When-to-load cells by hand, regenerate only the row set -->

## Sub-skill routing table

This hub provides 28 on-demand reference files (7 absorbed format skills + 16 Markdown/markup and agent-discovery references, 9 of them the llms.txt / ai.txt / robots.txt / agent-commerce family). When a task matches a row, **Read the listed `references/` file** before answering — do not rely on this table alone for depth.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `pdf` | Create, parse, merge, split, watermark, encrypt, sign, validate, convert PDF (Python + Node); HTML→PDF; extract text/tables; AcroForms; PDF/A·PDF/UA | `references/pdf.md` |
| `docx` | Create, read, edit, manipulate Word .docx (docx-js + XML); TOC/headings/letterheads; tracked changes; comments; find-and-replace; images | `references/docx.md` |
| `xlsx` | Create, read, edit, fix Excel .xlsx (openpyxl + pandas); formulas, formatting, charts; clean/restructure messy tabular data | `references/xlsx.md` |
| `pptx` | Create, read, edit PowerPoint .pptx (PptxGenJS + python-pptx); slide masters/layouts/templates; charts/tables; pptx→PDF | `references/pptx.md` |
| `csv` | Parse, generate, validate, convert, stream CSV/TSV; encoding (BOM/UTF-8/1252); formula-injection (CWE-1236); csvkit/qsv/miller/DuckDB | `references/csv.md` |
| `json-advanced` | Streaming parsers; JSON Schema (Ajv/Zod/TypeBox); JSON Patch (RFC 6902); JSONPath; MessagePack/CBOR/BSON; NDJSON; JSON5/JSONC | `references/json-advanced.md` |
| `drawio-diagrams` | Programmatic .drawio creation/parse/transform; mxGraphModel/mxCell XML; export SVG/PNG/PDF; drawpyo/maxGraph; CI/CD diagram gen | `references/drawio-diagrams.md` |
| `markdown-authoring` | Write correct/portable Markdown; CommonMark 0.31.2 vs GFM vs Pandoc/Obsidian/MDX flavors; core syntax + GFM extensions (tables, task lists, footnotes, strikethrough), frontmatter (YAML/TOML), GitHub alerts `> [!NOTE]`, math `$…$`; portability cheat-sheet | `references/markdown-authoring.md` |
| `markdown-processing` | Parse/transform/analyze Markdown in code; choose marked vs markdown-it vs micromark vs unified/remark/rehype; the unist/mdast↔hast model, unist-util-visit, write remark/rehype plugins; md↔HTML, sanitize, recipes | `references/markdown-processing.md` |
| `mdx` | Markdown + JSX components; MDX 3 (ES2024, top-level await, block expressions); compile/evaluate, components prop / MDXProvider; Docusaurus/Astro/Next/Storybook; untrusted-input danger | `references/mdx.md` |
| `llms-txt` | `llms.txt` / `llms-full.txt`: spec v2 (subpath scoping, `Link:` rel discovery, `Optional` demoted), the three llms-full.txt grammars, `.md` twins, `Accept: text/markdown`, Lighthouse audit, who actually reads it, spec gaps and injection risk | `references/llms-txt.md` |
| `llms-txt-generation-tooling` | pick a generator: Mintlify/Fern/GitBook/ReadMe built-ins; Docusaurus/MkDocs/VitePress/Starlight/Sphinx/Nuxt plugins; crawl-based (`create-llmstxt-py`, `dotenvx/llmstxt`, Jina Reader, Screaming Frog); WordPress (Yoast/Rank Math/AIOSEO), Shopify, Webflow/Framer; Cloudflare Markdown for Agents; description/section/size/CI quality practices | `references/llms-txt-generation-tooling.md` |
| `llms-txt-ecosystem-evidence` | dated adoption numbers (HTTP Archive, Ahrefs 137k-domain logs, SE Ranking 300k, Originality.ai, Rankability), server-log studies (97% zero requests; Claude-Code out-fetches retrieval bots), Google/Mueller/Illyes statements, directories, vendor sources graded | `references/llms-txt-ecosystem-evidence.md` |
| `llms-txt-recreation-and-aggregation` | recreate llms.txt/llms-full.txt for a site you do not own (rights + Content Signals, the clean-markdown acquisition ladder, index authoring, lenient multi-grammar parsing) and scale to a product FAMILY via spec-v2 nested indexes (Cloudflare hub-and-spoke pattern) with CI/size discipline | `references/llms-txt-recreation-and-aggregation.md` |
| `markdown-pandoc` | Pandoc universal conversion (md↔docx/PDF/HTML/epub/pptx/reST/…); reader→AST→writer; Lua/JSON filters; templates; citations (--citeproc); md→PDF engines | `references/markdown-pandoc.md` |
| `markdown-docs-as-code` | Docs-as-code workflow; static-site-generator selection (Starlight/Astro, Docusaurus, MkDocs Material, Hugo, VitePress, Eleventy, Jekyll, Sphinx); CI gates, preview deploys | `references/markdown-docs-as-code.md` |
| `lightweight-markup-languages` | Markdown siblings & when to pick them: reStructuredText/Sphinx, AsciiDoc, Org-mode, MyST, Typst, Textile/wiki; selection heuristics; convert via Pandoc | `references/lightweight-markup-languages.md` |
| `markdown-linting` | Markdown quality gates: markdownlint(-cli2) rules/config, remark-lint presets, Vale prose lint, lychee link-check; pre-commit/CI integration | `references/markdown-linting.md` |
| `ai-txt` | `ai.txt`: Spawning's 2023 AI-training/TDM opt-out (5-way name collision incl. a Guardian proposal, IETF draft `draft-car-ai-txt-wellknown-00`, an arXiv DSL paper, `aitxt.ing`); differentiation vs robots.txt/llms.txt; near-zero adoption (Hoffmann et al. SIGCOMM CCR 2026, ~4M Tranco domains); authoring/serving/verification | `references/ai-txt.md` |
| `robots-txt` | `robots.txt` / RFC 9309: ABNF grammar, `*`/`$` as MUST-level special characters, octet longest-match precedence + SHOULD-level allow-wins tie-break, 500 KiB parsing floor, 24h cache, 4xx-means-allow-all vs 5xx-complete-disallow, the four unadjudicated errata; what the RFC does NOT define (Crawl-delay, most-specific-user-agent, empty `Disallow`, 429/451/BOM); Googlebot vs Bingbot divergence; parsers (google/robotstxt, Protego vs `urllib.robotparser`), testing, misconceptions | `references/robots-txt.md` |
| `robots-txt-content-signals` | the AI-preference layer inside robots.txt: Cloudflare's Content Signals Policy (2025-09-24) — `Content-Signal: search=yes, ai-input=…, ai-train=no`, verbatim signal definitions, absence-is-not-permission, the `content-use` fourth signal, path-scoped signals, the 3.8M-domain managed robots.txt; evidence on whether crawlers obey it (Mueller's "no effects whatsoever", Cloudflare vs Perplexity, the user-triggered-fetch loophole); IETF AIPREF `Content-Usage` which Updates RFC 9309 | `references/robots-txt-content-signals.md` |
| `agents-md` | `agents.md`: the 4-way name collision (repo-root AGENTS.md coding convention vs Shopify's web-root `/agents.md` vs shop.app vs coincidental `.md` page renditions); what Shopify's managed file specifies; the `agents.md.liquid` restricted-Liquid template chain; per-store rollout and replace-not-merge overrides; why `/llms.txt` now mirrors it; indirect prompt-injection surface | `references/agents-md.md` |
| `nlweb-and-agentic-discovery` | NLWeb / MCP / WebMCP as *dynamic* agent surfaces vs a *static* llms.txt, and when each is warranted: what NLWeb is (schema.org+RSS query layer; repo moved microsoft/NLWeb→nlweb-ai 2025-07-30; dormant `main`, no releases, expired nlweb.ai TLS); its MCP binding pinned to revision `2024-11-05`; measured static-vs-dynamic trade-offs (llms-full.txt token sizes, per-query RAG cost, >50 LLM calls/query, the Mintlify accuracy null result); WebMCP (W3C CG draft + Chrome origin trial, tool-surface poisoning); the agentic-web layer model and a trigger-based decision framework | `references/nlweb-and-agentic-discovery.md` |
| `ucp-protocol` | Universal Commerce Protocol: the Google-launched Apache-2.0 agentic-commerce standard; governance reality (Google proxy vote to Dec 2028, Google CLA, no Linux Foundation); services/capabilities/extensions and reverse-domain naming; four transports (REST core, MCP, A2A, Embedded); the nine-step negotiation and intersection algorithm; the live `/.well-known/ucp` manifest; RFC 9421 signing; why UCP defines no trust tiers | `references/ucp-protocol.md` |
| `rsl-really-simple-licensing` | **RSL (Really Simple Licensing)**: the XML content-licensing standard (launched 2025-09-10, v1.0 Recommendation 2025-12-10) — governance and the RSL Collective, the `<rsl>`/`<content>`/`<license>` model, the usage/user/geo vocabularies (`ai-train`/`ai-input`/`ai-index`/`search`/`ai-all`), the eight payment types with `<amount>`/x402, and the five discovery mechanisms incl. the `robots.txt` `License:` directive | `references/rsl-really-simple-licensing.md` |
| `rsl-deployment-and-anti-patterns` | Deploy RSL end to end: `license.xml`, the `License:` line, the `application/rsl+xml` media type, `max-age`, per-subdomain scoping; the five-rung ladder from bare declaration to EMS encryption; the validator and Relax NG schema; a curl verification checklist; twelve anti-patterns and a troubleshooting table | `references/rsl-deployment-and-anti-patterns.md` |
| `rsl-vs-adjacent-standards` | The five-layer AI-permissions stack: RSL vs robots.txt/RFC 9309, IETF AIPREF (`Content-Usage`), Cloudflare Content Signals and pay-per-crawl, W3C TDMRep, C2PA/CAWG, CC Signals, `llms.txt` and `ai.txt`; why `License:` is an unregistered extension and `application/rsl+xml` is not IANA-registered | `references/rsl-vs-adjacent-standards.md` |
| `rsl-adoption-and-legal-weight` | Does RSL work? Measured deployment (130-domain sweep: 3 independent publishers; 1 of 9 founding supporters), no AI-company commitment, the Medium/Stack Overflow/Guardian conformance defects; legal force — *Ziff Davis v. OpenAI* (robots.txt is not a DMCA §1201 control), hiQ assent, EU DSM Art. 4(3); criticism and the antitrust question | `references/rsl-adoption-and-legal-weight.md` |

**Multi-row tasks:** Read the row for the OUTPUT format first, then the row for the input: md→PDF is `markdown-pandoc` (engine choice) then `pdf` (post-processing); pptx→PDF stays in `pptx`; "generate an llms.txt from a crawled site" is `llms-txt-recreation-and-aggregation` then `llms-txt`. If no row matches, do not answer from this table; use the cross-hub map below.

<!-- cross-hub-map -->

## Cross-hub map — where every document-formats topic lives

This family is split across these hubs. If a task's deep material is **not** in this hub's Sub-skill
routing table, it is a reference file under a sibling hub below: **activate that hub or `Read` its
`references/<name>.md` directly**. Every former standalone skill in this family is now a reference under one
of these hubs (nothing was deleted).

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `document-formats` | Document & File Formats (PDF, Word, Excel, PowerPoint, CSV, JSON, draw.io, Markdown) | `references/pdf.md`, `references/docx.md`, `references/xlsx.md`, `references/pptx.md`, `references/markdown-authoring.md`, `references/markdown-processing.md`, … |
| `da-analytical-methods` / `da-data-engineering-platform` | analysis or ETL of the data once it is out of the file | their own `references/` |
| `content-ingestion-extraction` | getting content OUT of aging docs, live DOM, audio; templatizing a document | `references/doc-archaeology.md`, `references/dom-scraping-resilience.md` |
| `chrome-extension-expert` | rendering + sanitizing Markdown inside a browser/extension UI | `references/markdown-rendering-browser.md` |
| `web-text-mirror` (standalone) | crawling a site into a single Markdown mirror (the input this hub turns into llms.txt / llms-full.txt) | its `SKILL.md` |
| `cloudflare-platform` (standalone) | configuring the Cloudflare products around robots.txt — AI Crawl Control, pay-per-crawl / HTTP 402, Web Bot Auth (RFC 9421), BotBase (this hub owns the `Content-Signal:` directive itself) | its `references/` |
| `generative-engine-optimization` (standalone) | llms.txt as an AI-visibility tactic; GEO/AEO citation strategy | `references/geo-aeo-reference.md` |
| `document-conversion` (standalone) | one-off pandoc / pdftotext conversion of a file into readable Markdown | its `SKILL.md` |
| `technical-writing-craft` / `writing-expert` | prose quality, structure and voice of the written document | their own `references/` |
