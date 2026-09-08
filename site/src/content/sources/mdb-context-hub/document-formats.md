---
title: "Markdown Linting & Quality Gates"
description: "Hub for programmatic document and data-file work — creating, parsing, editing, and converting the common office and data formats in Python and Node.js. Each former standalone format skill is now an on"
---

# Document & File Formats

Hub for **programmatic document and data-file work** — creating, parsing, editing, and converting the common office and data formats in Python and Node.js. Each former standalone format skill is now an on-demand reference file under this hub's `references/`; when a task matches a routing-table row, Read that `references/<name>.md` file before answering.

The boundary that defines this hub: it owns the **file format** — bytes in, bytes out, and the libraries that manipulate them. When the real question is the *analysis* of the data, the *extraction* of content from messy sources, or the *prose quality* of a written document, defer to the sibling hubs (da-* / content-ingestion-extraction / writing-expert).

## Sub-skill routing table (15 references)

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `pdf` | Create/parse/merge/split/sign/encrypt/validate PDF; HTML→PDF; extract text/tables; AcroForms; PDF/A·UA | `references/pdf.md` |
| `docx` | Word .docx create/read/edit; TOC/headings/letterheads; tracked changes; comments; find-and-replace; images | `references/docx.md` |
| `xlsx` | Excel .xlsx (openpyxl + pandas); formulas, formatting, charts; clean messy tabular data | `references/xlsx.md` |
| `pptx` | PowerPoint .pptx (PptxGenJS + python-pptx); slide masters/layouts/templates; charts; pptx→PDF | `references/pptx.md` |
| `csv` | Parse/generate/validate/stream CSV/TSV; encoding (BOM/UTF-8/1252); formula-injection; csvkit/qsv/DuckDB | `references/csv.md` |
| `json-advanced` | Streaming parsers; JSON Schema (Ajv/Zod/TypeBox); JSON Patch; JSONPath; MessagePack/CBOR; NDJSON; JSON5 | `references/json-advanced.md` |
| `drawio-diagrams` | Programmatic .drawio; mxGraphModel/mxCell XML; export SVG/PNG/PDF; drawpyo/maxGraph | `references/drawio-diagrams.md` |
| `markdown-authoring` | Write correct/portable Markdown; CommonMark 0.31.2 vs GFM vs Pandoc/Obsidian/MDX flavors; syntax + extensions (tables, task lists, footnotes), frontmatter (YAML/TOML), GitHub alerts `> [!NOTE]`, math `$…$` | `references/markdown-authoring.md` |
| `markdown-processing` | Parse/transform/analyze Markdown in code; marked vs markdown-it vs micromark vs unified/remark/rehype; mdast↔hast, unist-util-visit, remark/rehype plugins; md↔HTML, sanitize | `references/markdown-processing.md` |
| `mdx` | Markdown + JSX components; MDX 3 (ES2024, await, block expressions); compile/evaluate, MDXProvider; Docusaurus/Astro/Next/Storybook; untrusted-input danger | `references/mdx.md` |
| `llms-txt` | `llms.txt` / `llms-full.txt` curated markdown index for LLM consumers; CLAUDE.md/AGENTS.md agent context; honest adoption caveats | `references/llms-txt.md` |
| `markdown-pandoc` | Pandoc universal conversion (md↔docx/PDF/HTML/epub/pptx/reST); reader→AST→writer; Lua/JSON filters; templates; citations; md→PDF engines | `references/markdown-pandoc.md` |
| `markdown-docs-as-code` | Docs-as-code; SSG selection (Starlight/Astro, Docusaurus, MkDocs Material, Hugo, VitePress, Eleventy, Jekyll, Sphinx); CI gates, preview deploys | `references/markdown-docs-as-code.md` |
| `lightweight-markup` | Markdown siblings: reStructuredText/Sphinx, AsciiDoc, Org-mode, MyST, Typst, Textile/wiki; selection heuristics; convert via Pandoc | `references/lightweight-markup-languages.md` |
| `markdown-linting` | Markdown quality gates: markdownlint(-cli2), remark-lint presets, Vale prose lint, lychee link-check; pre-commit/CI | `references/markdown-linting.md` |
