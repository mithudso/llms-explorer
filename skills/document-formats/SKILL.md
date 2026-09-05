---
description: >-
  Generate/parse/edit/convert document & data-file formats in Python & Node — PDF, .docx,
  .xlsx, .pptx, CSV/TSV, JSON, .drawio, Markdown/MDX, llms.txt. TRIGGER: PDF (pdf-lib,
  pypdf, ReportLab, extract text/tables); Word (docx-js, TOC); Excel (openpyxl/pandas,
  formulas, charts); PowerPoint (PptxGenJS/python-pptx, pptx→PDF); CSV/TSV (encoding/BOM,
  formula-injection, csvkit/qsv/DuckDB); advanced JSON (streaming, Schema/Ajv/Zod, JSON
  Patch, JSONPath); draw.io (drawpyo); Markdown/CommonMark/GFM authoring+processing
  (remark, markdown-it, MDX, Pandoc); write/recreate llms.txt + llms-full.txt (spec v2).
  SKIP: analytical/ETL tabular work → da-analytical-methods /
  da-data-engineering-platform; extract FROM aging docs/live DOM →
  content-ingestion-extraction; in-browser markdown render/sanitize →
  chrome-extension-expert (references/markdown-rendering-browser.md); llms.txt for
  AI-search citations → generative-engine-optimization; one-off pandoc/pdftotext
  file→Markdown → document-conversion.
name: document-formats
title: "Document & File Formats"
category: developer
version: "1.2.2"
updated: "2026-08-30"
model: claude-sonnet-5
effort: medium
tags: [pdf, docx, xlsx, pptx, csv, json, drawio, markdown, mdx, pandoc, llms-txt, document-generation, file-formats, hub]
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
whenNotToUse:
  - "analytical or ETL processing of data where the format is incidental (use da-analytical-methods or da-data-engineering-platform)"
  - "extracting/recovering content from old docs, web DOM, or audio, or templatizing a document (use content-ingestion-extraction)"
  - "prose/structure/voice review of a written document (use writing-expert or technical-writing-craft)"
  - "MongoDB BSON schema design (use mongodb-expert)"
  - "rendering + sanitizing Markdown in a browser or extension UI (use chrome-extension-expert, references/markdown-rendering-browser.md)"
  - "whether llms.txt earns AI-search citations or share-of-voice (use generative-engine-optimization; this hub owns the file itself)"
  - "crawling or mirroring a site's pages into Markdown (use web-text-mirror; this hub assembles the result into llms.txt/llms-full.txt)"
  - "a one-off convert-this-file-to-readable-Markdown via pandoc/pdftotext (use document-conversion)"
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

This hub provides 18 on-demand reference files (7 absorbed format skills + 11 Markdown/markup references, 4 of them the llms.txt family). When a task matches a row, **Read the listed `references/` file** before answering — do not rely on this table alone for depth.

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
| `generative-engine-optimization` (standalone) | llms.txt as an AI-visibility tactic; GEO/AEO citation strategy | `references/geo-aeo-reference.md` |
| `document-conversion` (standalone) | one-off pandoc / pdftotext conversion of a file into readable Markdown | its `SKILL.md` |
| `technical-writing-craft` / `writing-expert` | prose quality, structure and voice of the written document | their own `references/` |
