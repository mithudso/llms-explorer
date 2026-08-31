---
title: 'Changelog: spec v1 to v2, and the hub pipeline'
description: 'What changed in the llms.txt proposal on 2026-08-10, rule by rule, with the effect on an existing file — and the dated changes to the hub schema behind this site.'
section: reference
order: 6
sources:
  - docs/site/components/11-v2-vs-v1.md
  - skills/document-formats/references/llms-txt.md
---

<!-- hand page · reference/changelog · 2026-08-31 · spec rows from llmstxt.org/changes via 11-v2-vs-v1.md §3a; pipeline rows from §3b -->

Two versioned things share a name. The **llms.txt proposal** went from v1 (2024-09-03) to v2
(modified 2026-08-10). The **hub pipeline** behind this site went from V1 (site dumps, to
2026-08-29) to V2 (acquire, refine, dual index, gate — from 2026-08-30). Both tables below; the
argument for why the second matters is the [V2 vs V1 essay](/essays/v2-vs-v1/).

## The spec: v1 → v2 (2026-08-10)

| Rule | v1 | v2 | Effect on an existing file |
|---|---|---|---|
| Required elements | H1 + blockquote + sections implied | **H1 only** required; blockquote, prose and sections optional | none required; the lint still scores a missing blockquote as Medium (I2) — quality, not validity |
| Placement | `/llms.txt` at the site root | root **or any subpath**; a file covers the URLs under its path; **most-specific wins**; `/.well-known/` explicitly rejected | enables families and split roots (`<section>/llms.txt`) |
| Discovery | none | `Link: <…>; rel="describedby"` on files; `rel="alternate" type="text/markdown"` on HTML pages; as `<link>` or an HTTP header | add the two headers ([usage](/reference/usage/) §1) |
| Markdown twins | `page.html.md` | `page.html.md` **or** `page.md`; directories append `index.html.md` or `index.md` | either form passes the twin probe (N6) |
| `## Optional` | mechanical: skippable when context is short; consumed by `llms_txt2ctx` | a **convention** for secondary information; `llms_txt2ctx` and context-expansion removed from the proposal | keep it last; build nothing that depends on it |
| BOM | — | an optional byte-order mark is tolerated | the lint strips it as hygiene (P14) |
| Consumption model | expand the whole file into context | "view or search the index, then follow links"; the index stays small; detail lives behind links | the size ladder (small / full) becomes the producer's job |
| Authoring guidance | — | concise language, informative link descriptions, no unexplained jargon, "test your file by asking an agent questions … giving it only your llms.txt" | the agent test (R5, P12) is the spec's own test made numeric |

Still open in the spec repository after v2: H2 ordering carries no defined meaning; no
version or provenance field (#132, #133); which language a root file is in (#147); no
security-considerations section despite issue #152's steering finding (2026-08-29); the
`.well-known` request (#2). `llms-full.txt` remains outside the spec entirely.

## The hub pipeline: V1 → V2 (2026-08-30)

| Stage | V1 (to 2026-08-29) | V2 (from 2026-08-30) |
|---|---|---|
| Acquire | trafilatura BFS crawl → banner mirror | the ladder: `llms-full.txt` → `llms.txt` + `.md` twins → `Accept: text/markdown` → docs API → structured crawl; the banner mirror stays the internal format |
| Clean | none (raw HTML → text) | `docset_refine clean`: boilerplate lines, MDX → markdown, page classes (reference / guide / changelog / marketing / index) |
| Extract | `distill_offline.py bulk` — zero-LLM, output never consumed | `extract` (snippets, table rows → parameter, definitions, changelog → change; anchors to real headings) + `units` (local LLM, evidence rule) + `polish` |
| Export | none | `export_llms`: index (split over 10 KB) / full (Mintlify grammar) / small (≤ 200,000 chars) / facts / manifest; `topical`; `vocabulary` |
| Index | one raw vector layer | raw **and** facts vector layers, plus an FTS5 keyword layer per layer |
| Serve | `web-text-mirror --serve` (HTML) | `llms_serve.py`: `/llms.txt`, `/d/<stem>/…`, `/m/<key>/…`, `/t/<slug>/…`, with the markdown headers |
| Gate | none | `llms_lint.py` (the deterministic passes) inside `docset_rollout cleanup`; `/ldo` for the model and live passes |
| Artifacts | `<stem>.pages/`, `_master.md`, `._distill_index.json` | `<stem>.reference/{pages.json, structured.jsonl, units.jsonl, all_units.jsonl}`, `<stem>.llms/` |

## Dated changes to the hub schema

| Date | Change |
|---|---|
| 2026-08-30 | `docset_refine` gains `clean / extract / units / polish / render / export`; the reference dir layout above |
| 2026-08-30 | `export_llms` writes the four-file ladder plus `manifest.json`; index split at 10,000 bytes; `PART_PAGES = 60` |
| 2026-08-30 | `llms_lint.py` ships the deterministic passes P0–P15 and the `--json` CI output; `UNIT_RE` fixes the facts line grammar |
| 2026-08-30 | `llms_serve.py` sends `Content-Type: text/markdown`, `X-Markdown-Tokens`, `Link: rel="describedby"` |
| 2026-08-30 | `docset_refine topical` and `vocabulary`; tree nodes carry `slug` / `aliases`; `--register` writes `llmsFile` on a node |
| 2026-08-31 | `export_llms` honours `manifest.json["overrides"]` (`title`, `summary`, `section_order`, `note`) so hand inputs survive regeneration |
| 2026-08-31 | `llms_lint.py --kind vocabulary` lints the vocabulary line grammar |

## Migrating a v1 file

1. Run the lint. A file whose findings say *full file wearing the wrong name* (P0 / I6: page
   bodies inside `llms.txt`, over 100 KB) is split into `llms.txt` + `llms-full.txt`.
2. Add `.md` twins and the two `Link` relations.
3. Move skippable material to a trailing `## Optional`.
4. Over 10 KB: hub-and-spoke split.
5. Re-lint. For a v2-clean file the report reads "nothing required" and, usually, two
   recommendations: twins and headers.
