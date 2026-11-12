# /sko document-formats — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 3 | 2 | applied scoped repairs |
| 2 | 0 | 0 | 2 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 2 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| A | Three routing rows point to absent reference files. (`Sub-skill routing table: document-conversion, google-docs-inplace-editor, google-sheets-inplace-editor`) | Medium | Remove the broken rows; keep document-conversion as an external deferral; report Google editor integration as unavailable. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/document-formats/SKILL.md
@@ -1,13 +1,13 @@
 ---
 description: >-
-  Generate/parse/edit/convert document & data-file formats in Python & Node. TRIGGER: PDF (pdf-lib, pypdf, ReportLab, text/tables); Word (docx-js, TOC); Excel (openpyxl/pandas, charts); PowerPoint (PptxGenJS/python-pptx); CSV/TSV (encoding/BOM, injection); advanced JSON (streaming, Ajv/Zod, JSON Patch); draw.io; Markdown/CommonMark/GFM (remark, MDX, Pandoc); write/recreate llms.txt + llms-full.txt (spec v2); ai.txt opt-out; robots.txt / RFC 9309 (syntax, precedence, crawl-delay, parsers) + Content-Signal extension; agents.md + /.well-known/ucp; static llms.txt vs live NLWeb/WebMCP; RSL (XML AI licensing, pay-per-crawl). SKIP: evals -> deep-eval-optimizer; tabular ETL -> da-* hubs; aging docs/live DOM extraction -> content-ingestion-extraction; in-browser markdown render -> chrome-extension-expert; llms.txt for AI search -> generative-engine-optimization; one-off pandoc -> document-conversion; EU TDM law -> eu-ai-act-tdm-opt-out.
+  Generate/parse/edit/convert document & data-file formats in Python & Node. TRIGGER: PDF (pdf-lib, pypdf, ReportLab, text/tables); Word (docx-js, TOC); Excel (openpyxl/pandas, charts); PowerPoint (PptxGenJS/python-pptx); CSV/TSV (encoding/BOM, injection); advanced JSON (streaming, Ajv/Zod, JSON Patch); draw.io; Markdown/CommonMark/GFM (remark, MDX, Pandoc); write/recreate llms.txt + llms-full.txt (spec v2); ai.txt opt-out; robots.txt / RFC 9309 (syntax, precedence, crawl-delay, parsers) + Content-Signal extension; agents.md + /.well-known/ucp; static llms.txt vs live NLWeb/WebMCP; RSL (XML AI licensing, pay-per-crawl). SKIP: evals -> deep-eval-optimizer; tabular ETL -> da-data-engineering-platform; aging docs/live DOM extraction -> content-ingestion-extraction; in-browser markdown render -> chrome-extension-expert; llms.txt for AI search -> generative-engine-optimization; one-off pandoc -> document-conversion; EU TDM law -> eu-ai-act-tdm-opt-out.
 name: document-formats
 title: "Document & File Formats"
 category: developer
-version: "1.7.0"
-updated: "2026-09-29"
-model: claude-sonnet-5
-effort: medium
+version: "1.8.0"
+updated: "2026-11-11"
+model: claude-opus-5-5
+effort: high
 tags: [pdf, docx, xlsx, pptx, csv, json, drawio, markdown, mdx, pandoc, llms-txt, ai-txt, robots-txt, content-signals, document-generation, file-formats, hub, rsl]
 keywords:
   - PDF generation pdf-lib pypdf ReportLab WeasyPrint HTML-to-PDF
@@ -52,6 +52,8 @@
   - chrome-extension-expert
   - generative-engine-optimization
   - web-text-mirror
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # Document & File Formats
@@ -67,6 +69,15 @@
 of content from messy sources, or the *prose quality* of a written document, defer to the sibling hubs
 named in the cross-hub map.

+## Look for llms files first
+
+Before reading the relevant format specification or library documentation raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.
+
 ## Routing detail

 Deferrals the description cannot carry within its 1000-character cap (they mirror `whenNotToUse`):
@@ -78,7 +89,7 @@

 ## Sub-skill routing table

-This hub provides 28 on-demand reference files (7 absorbed format skills + 16 Markdown/markup and agent-discovery references, 9 of them the llms.txt / ai.txt / robots.txt / agent-commerce family). When a task matches a row, **Read the listed `references/` file** before answering — do not rely on this table alone for depth.
+This hub provides 28 on-demand reference files for office/data formats, Markdown/markup and agent-discovery standards. When a task matches a row, **Read the listed `references/` file** before answering — do not rely on this table alone for depth.

 | Sub-topic | When to load | Reference file |
 | --- | --- | --- |
@@ -87,7 +98,6 @@
 | `xlsx` | Create, read, edit, fix Excel .xlsx (openpyxl + pandas); formulas, formatting, charts; clean/restructure messy tabular data | `references/xlsx.md` |
 | `pptx` | Create, read, edit PowerPoint .pptx (PptxGenJS + python-pptx); slide masters/layouts/templates; charts/tables; pptx→PDF | `references/pptx.md` |
 | `csv` | Parse, generate, validate, convert, stream CSV/TSV; encoding (BOM/UTF-8/1252); formula-injection (CWE-1236); csvkit/qsv/miller/DuckDB | `references/csv.md` |
-| `document-conversion` | pandoc / poppler (pdftotext) — convert PDFs, Word docs, EPUBs into LLM-readable Markdown | `references/document-conversion.md` |
 | `json-advanced` | Streaming parsers; JSON Schema (Ajv/Zod/TypeBox); JSON Patch (RFC 6902); JSONPath; MessagePack/CBOR/BSON; NDJSON; JSON5/JSONC | `references/json-advanced.md` |
 | `drawio-diagrams` | Programmatic .drawio creation/parse/transform; mxGraphModel/mxCell XML; export SVG/PNG/PDF; drawpyo/maxGraph; CI/CD diagram gen | `references/drawio-diagrams.md` |
 | `markdown-authoring` | Write correct/portable Markdown; CommonMark 0.31.2 vs GFM vs Pandoc/Obsidian/MDX flavors; core syntax + GFM extensions (tables, task lists, footnotes, strikethrough), frontmatter (YAML/TOML), GitHub alerts `> [!NOTE]`, math `$…$`; portability cheat-sheet | `references/markdown-authoring.md` |
@@ -111,8 +121,6 @@
 | `rsl-deployment-and-anti-patterns` | Deploy RSL end to end: `license.xml`, the `License:` line, the `application/rsl+xml` media type, `max-age`, per-subdomain scoping; the five-rung ladder from bare declaration to EMS encryption; the validator and Relax NG schema; a curl verification checklist; twelve anti-patterns and a troubleshooting table | `references/rsl-deployment-and-anti-patterns.md` |
 | `rsl-vs-adjacent-standards` | The five-layer AI-permissions stack: RSL vs robots.txt/RFC 9309, IETF AIPREF (`Content-Usage`), Cloudflare Content Signals and pay-per-crawl, W3C TDMRep, C2PA/CAWG, CC Signals, `llms.txt` and `ai.txt`; why `License:` is an unregistered extension and `application/rsl+xml` is not IANA-registered | `references/rsl-vs-adjacent-standards.md` |
 | `rsl-adoption-and-legal-weight` | Does RSL work? Measured deployment (130-domain sweep: 3 independent publishers; 1 of 9 founding supporters), no AI-company commitment, the Medium/Stack Overflow/Guardian conformance defects; legal force — *Ziff Davis v. OpenAI* (robots.txt is not a DMCA §1201 control), hiQ assent, EU DSM Art. 4(3); criticism and the antitrust question | `references/rsl-adoption-and-legal-weight.md` |
-| `google-docs-inplace-editor` | Reviews, edits, and maintains Google Docs in place, preserving existing content, tabs, structure, and | `references/google-docs-inplace-editor/google-docs-inplace-editor.md` |
-| `google-sheets-inplace-editor` | Creates and updates Google Sheets workbooks, tabs, ranges, values, formulas, and formatting while | `references/google-sheets-inplace-editor/google-sheets-inplace-editor.md` |

 **Multi-row tasks:** Read the row for the OUTPUT format first, then the row for the input: md→PDF is `markdown-pandoc` (engine choice) then `pdf` (post-processing); pptx→PDF stays in `pptx`; "generate an llms.txt from a crawled site" is `llms-txt-recreation-and-aggregation` then `llms-txt`. If no row matches, do not answer from this table; use the cross-hub map below.

```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/document-formats/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "document-formats",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "md-pdf",
+      "prompt": "Generate a PDF from this Markdown and explain the selected engine.",
+      "expected_output": "Load output/engine-relevant references before processing; do not use a missing routing-table file.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "md-pdf-order",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "md→PDF is `markdown-pandoc`",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "pdf-file",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "references/pdf.md",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "llms-authoring",
+      "prompt": "Generate llms.txt and llms-full.txt from my existing readable site mirror.",
+      "expected_output": "Use the recreation/aggregation and format references; distinguish file authorship from claims about search visibility.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "recreation",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "references/llms-txt-recreation-and-aggregation.md",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "visibility-boundary",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "llms.txt as an AI-visibility tactic",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/evals/trigger-eval.json
+++ .claude/skills/document-formats/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "merge these three PDFs and stamp a watermark on each page",
+    "should_trigger": true
+  },
+  {
+    "query": "generate a .docx report with a table of contents",
+    "should_trigger": true
+  },
+  {
+    "query": "read this xlsx, fix the broken formulas, and write it back out",
+    "should_trigger": true
+  },
+  {
+    "query": "build a PowerPoint deck from this data and export it to PDF",
+    "should_trigger": true
+  },
+  {
+    "query": "my CSV has a BOM and Excel keeps mangling it",
+    "should_trigger": true
+  },
+  {
+    "query": "stream-parse a 4GB JSON file and validate it against a JSON Schema",
+    "should_trigger": true
+  },
+  {
+    "query": "generate a draw.io architecture diagram from a YAML config",
+    "should_trigger": true
+  },
+  {
+    "query": "GFM tables and footnotes that render on GitHub and in Obsidian",
+    "should_trigger": true
+  },
+  {
+    "query": "generate an llms.txt for my docs site",
+    "should_trigger": true
+  },
+  {
+    "query": "how do I recreate llms-full.txt for a site that doesn't publish one",
+    "should_trigger": true
+  },
+  {
+    "query": "load these CSVs into DuckDB and build an incremental dbt model",
+    "should_trigger": false
+  },
+  {
+    "query": "scrape the pricing table off this live page with a content script",
+    "should_trigger": false
+  },
+  {
+    "query": "get Perplexity and ChatGPT search to cite my product pages",
+    "should_trigger": false
+  },
+  {
+    "query": "rewrite this README so the setup steps read clearly and drop the passive voice",
+    "should_trigger": false
+  },
+  {
+    "query": "render user-submitted markdown safely in my React app",
+    "should_trigger": false
+  },
+  {
+    "query": "audit our runbook folder for stale links and decide what to archive",
+    "should_trigger": false
+  },
+  {
+    "query": "build a Kafka to Flink streaming pipeline that writes Parquet",
+    "should_trigger": false
+  },
+  {
+    "query": "does llms.txt actually help my site show up in AI Overviews?",
+    "should_trigger": false
+  },
+  {
+    "query": "write the API reference docs for our new endpoints",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/document-formats/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+# Changelog
+
+2026-11-11 sko v1.7.0->v1.8.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 3 Medium findings fixed in reviewed scope; global sync and blind review deferred.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 4; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/document-formats/SKILL.md | canonical (explicit repository target) | aa89e9837fda | audited and changed in isolated worktree | 306cb29f7840 |
| $HOME/.claude/skills/document-formats/SKILL.md | installed copy | aa89e9837fda | report only; preserve divergence; root-coordinated ownership review | aa89e9837fda |
| $HOME/.global-ai-hub/skills/document-formats/SKILL.md | installed copy | aa89e9837fda | report only; preserve divergence; root-coordinated ownership review | aa89e9837fda |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| document-formats | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-opus-5-5 · effort: high (tier: flagship; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/document-formats/baseline/SKILL.md" ".claude/skills/document-formats/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

3 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

Modified sections: frontmatter routing/model/version metadata; Look for llms files first.

A-P dispositions:

| Pass | Disposition |
|---|---|
| A | Reviewed entrypoint correctness and operative supporting files; fixed anchored contradictions/broken pointers. Large unchanged reference facts are not independently revalidated. |
| B | Reviewed claimed scope, stage ordering and output promises; preserved research evidence/budget/STOP boundaries. |
| C | Strict YAML parsed with duplicate-key rejection; checked target-local introduced links and hub table file existence. |
| D | Reviewed procedural clarity and concrete examples; retained domain terms and source-qualified claims. |
| E | Applied only scoped routing/progressive-disclosure repairs; retained author workflow and purpose. |
| F | Created three realistic functional scenario cases; static instruction-contract checks ran at 6/6. Scenario outputs were not executed. |
| G | Manifest parsed, version/date updated, advisory model provenance recorded; no claim that prior model IDs are invalid. |
| H | 20-query corpus replay/generated first, projection derived afterward; author predictions 10/10 positive, 0/10 false positives. No measured activation. |
| I | Local keyword/referrer discovery and explicit peer boundaries reviewed. Global semantic ranking/collision rates remain unverified because services are paused. |
| J | Description 959 characters; body estimate 3530 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: none; entrypoint routes/existence checked.
Unread supporting files: references/agents-md.md, references/ai-txt.md, references/csv.md, references/docx.md, references/drawio-diagrams.md, references/json-advanced.md, references/lightweight-markup-languages.md, references/llms-txt-ecosystem-evidence.md, references/llms-txt-generation-tooling.md, references/llms-txt-recreation-and-aggregation.md, references/llms-txt.md, references/markdown-authoring.md, references/markdown-docs-as-code.md, references/markdown-linting.md, references/markdown-pandoc.md, references/markdown-processing.md, references/mdx.md, references/nlweb-and-agentic-discovery.md, references/pdf.md, references/pptx.md, references/robots-txt-content-signals.md, references/robots-txt.md, references/rsl-adoption-and-legal-weight.md, references/rsl-deployment-and-anti-patterns.md, references/rsl-really-simple-licensing.md, references/rsl-vs-adjacent-standards.md, references/ucp-protocol.md, references/xlsx.md.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| no-missing-table-references | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| merge these three PDFs and stamp a watermark on each page | trigger | trigger | true |
| generate a .docx report with a table of contents | trigger | trigger | true |
| read this xlsx, fix the broken formulas, and write it back out | trigger | trigger | true |
| build a PowerPoint deck from this data and export it to PDF | trigger | trigger | true |
| my CSV has a BOM and Excel keeps mangling it | trigger | trigger | true |
| stream-parse a 4GB JSON file and validate it against a JSON Schema | trigger | trigger | true |
| generate a draw.io architecture diagram from a YAML config | trigger | trigger | true |
| GFM tables and footnotes that render on GitHub and in Obsidian | trigger | trigger | true |
| generate an llms.txt for my docs site | trigger | trigger | true |
| how do I recreate llms-full.txt for a site that doesn't publish one | trigger | trigger | true |
| load these CSVs into DuckDB and build an incremental dbt model | skip | skip | true |
| scrape the pricing table off this live page with a content script | skip | skip | true |
| get Perplexity and ChatGPT search to cite my product pages | skip | skip | true |
| rewrite this README so the setup steps read clearly and drop the passive voice | skip | skip | true |
| render user-submitted markdown safely in my React app | skip | skip | true |
| audit our runbook folder for stale links and decide what to archive | skip | skip | true |
| build a Kafka to Flink streaming pipeline that writes Parquet | skip | skip | true |
| does llms.txt actually help my site show up in AI Overviews? | skip | skip | true |
| write the API reference docs for our new endpoints | skip | skip | true |
| pull the transcript from my Granola meeting notes | skip | skip | true |

</details>
