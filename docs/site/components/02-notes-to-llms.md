# 02 — Notes → LLMS

**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | api | cli

## 1. Purpose

Turn disparate material — notes, docs, exports, a folder of markdown, a PDF, a Notion or Obsidian dump — into a usable llms family (`llms.txt` index, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, `manifest.json`, optionally a topical index and `llms-vocabulary.txt`) that passes the same bar as a site export. The method is `skills/llms-deep-optimizer/references/facts-to-llms-howto.md`; the engine is `hub/scripts/docset_refine/`. The user brings text; the pipeline supplies structure, anchors, descriptions and the size ladder.

## 2. User stories and flows

- *Solo dev*: drops 40 markdown notes about their internal API; gets an index by topic, a facts file every unit of which points back to the note and heading it came from, and a zip to commit next to the code.
- *Team lead*: uploads a Notion export of runbooks, picks the concept-tree node "incident response" as the skeleton, publishes to `/u/<team>/runbooks.llms/` and points Claude Code at the served URL.
- *Researcher*: pastes a reading list plus PDFs; the wizard clusters facts into sections, they rename two sections and demote "old drafts" to `## Optional`.

Wizard flow: **Upload** → **Detect** (kind per file, page count, empty/duplicate files) → **Skeleton** (auto-cluster / concept-tree node / write sections) → **Preview index** (sections, link lines, descriptions) → **Generate** (jobs: extract → units → polish → render → export/topical/vocabulary) → **Lint gate** (01, 0 High required to publish) → **Deliver** (zip / publish to `/u/…` / push to the user's GitHub repo / keyword+vector index for 16/17).

## 3. Inputs → outputs (contracts and file grammars)

Inputs: `.md` `.txt` `.docx` `.pdf` `.html`, URLs (fetched through the acquisition ladder in `llms_acquire.py`: `llms-full.txt` → `llms.txt` + `.md` twins → page fetch), pasted text, Obsidian vault zip, Notion export zip, a folder zip. Everything is normalised into the hub's banner mirror grammar (`==========` / `URL: <source>` / `==========` / body) — the internal canonical page format every refine tool reads.

**Anchoring rule for unsourced material.** Notes have no URLs, but every unit must have a source (P7 C6 High otherwise). The source of an uploaded page is `upload://<upload_id>/<path>` and the anchor is the slug of the nearest real heading above the unit (extract's `real_headings` rule); a file without headings anchors to `#top`. When the user publishes, `upload://` sources are rewritten to the served page URL (`https://…/u/<user>/<slug>.llms/pages/<n>.md`) so links resolve for readers. A unit whose text cannot be tied to an uploaded page is rejected (`pool.rejected.jsonl`, reason `unsourced`), never guessed.

Outputs: `<slug>.llms/` with `llms.txt` (spec v2; hub-and-spoke split when > 10 KB via `build_split_index`), `llms-full.txt` (mintlify grammar, header comment names it), `llms-small.txt` (≤ ~50k tokens, reference-class first), `llms-facts.txt` (`- [type] text — url#anchor`), `manifest.json` (bytes/tokens per file, `sections`, `dropped_empty_pages`), optionally `llms-vocabulary.txt` + `vocabulary.json`, plus `pages/<n>.md` twins for publish. Unit types are `docset_refine.UNIT_TYPES` (concept, fact, actionable, question, problem, statement, quote, idea, snippet, parameter, definition, change).

## 4. Architecture (mermaid diagram + existing hub code reused, by path)

```mermaid
flowchart TD
  U[uploads / URLs / paste] --> N[normalise → banner mirror]
  N --> C[clean.py: boilerplate, MDX, classes]
  C --> E[extract.py: snippets, parameters, definitions, changes]
  E --> L[units.py: LLM units (qwen local, evidence rule)]
  L --> P[polish.py: claude -p]
  P --> R[render.py: all_units.jsonl]
  R --> X[export_llms.py: index/full/small/facts/manifest (+split)]
  R --> T[topical.py: sections from a skeleton]
  R --> V[vocabulary.py]
  X --> G[01 lint gate]
  G --> D[zip / publish /u/… / GitHub push]
  D --> I[17 index: vector + FTS5]
```

Reused: `hub/scripts/docset_refine/{clean,extract,units,polish,render,export_llms,topical,vocabulary}.py` and `__main__.py` (`all`, `export`, `topical --from … --subject … --out …`, `family`), `hub/scripts/llms_acquire.py`, `hub/scripts/docset_indexer.py` (`index`, `index --units`, `keyword-index`), `hub/scripts/llms_lint.py`. New: converters (docx/pdf/Notion/Obsidian → markdown pages with headings preserved), the skeleton chooser (cluster names from `semantic_ops.cluster` over unit embeddings; tree nodes from 09), and the publish/GitHub push step.

## 5. API / CLI / MCP surface

```
POST /api/uploads                         multipart → {upload_id, files: [{path, kind, pages, empty}]}
POST /api/notes/preview                   {upload_id, skeleton: {mode: auto|tree|manual, node?, sections?}} → proposed index (sections + link lines + descriptions), counts
POST /api/notes/generate                  {upload_id, skeleton, options: {llm_units, polish, vocabulary, split}} → {job_id}
GET  /api/jobs/{id}                       stages: normalise → clean → extract → units → polish → render → export → lint
GET  /api/jobs/{id}/artifacts             zip, per-file, lint report
POST /api/notes/{slug}/publish            → /u/<user>/<slug>.llms/ (requires lint 0 High), optional github: {repo, path, branch}
```

CLI: `llmsx notes build DIR|FILES… --subject "…" [--tree-node N | --sections a,b,c] [--no-llm] [--publish]`; local mode runs `docset_refine all` + `export` directly.

## 6. UI (pages, states, empty/error states)

- **Upload**: drag-drop; table of detected files with kind (markdown / pdf / docx / html / notion / obsidian), page count, warnings (empty, duplicate by hash, > size cap). Empty files are dropped and listed (`dropped_empty_pages`).
- **Skeleton**: three cards — *Auto-cluster* (k ≈ √n sections named by top keywords + central definition), *Concept-tree node* (search 09; sections = its children), *Write sections* (editable list). Coverage panel: each section needs ≥ 3 facts and ≥ 1 definition; thin sections are flagged and offered as `## Optional`.
- **Preview**: the index rendered as it will ship, descriptions editable inline (edits go to `manifest.overrides`, not the file, so regeneration keeps them), section reorder by drag, `## Optional` demotion.
- **Generate**: stage progress with counts (pages, units by origin, LLM units, dedup merges), cost so far.
- **Gate**: the 01 scorecard; publish disabled until 0 High; Medium findings listed with "fix in preview" links.
- **Deliver**: download zip, publish (served URL + `Link rel=describedby`), push to GitHub (OAuth, PR or direct commit), "index for search" toggle (17).
- Errors: unreadable PDF (offer OCR later — out of scope), zip > cap, no headings anywhere (anchors fall back to `#top`, warned), skeleton with 0 assignable units.

## 7. Data model and storage

```
uploads(id, user_id, sha256, bytes, files json, created_at, expires_at)
notes_projects(id, user_id, slug, upload_id, skeleton json, overrides json, status, published_at)
jobs / job_events / artifacts                      shared (see 15 and 01)
pages(project_id, n, source_path, title, text)     the banner mirror pages, served as pages/<n>.md after publish
units(project_id, id, type, text, source, anchor, keywords json, origin, section)   = all_units.jsonl
```

Refine intermediates (`<stem>.clean.md`, `<stem>.reference/`) live on the worker's disk under the project id and are garbage-collected 30 days after the last generate.

## 8. Tiering, metering and billing hooks

| Stage | Free | Paid |
|---|---|---|
| Upload + normalise + clean + extract (deterministic) | ≤ 5 MB / 200 pages per project, 3 projects | ≤ 500 MB, unlimited projects |
| LLM units (`units.py`, local qwen) | off | metered per local-model token |
| Polish (`claude -p`) | off | metered per Claude token |
| Vocabulary `--llm` | off | metered |
| Export / topical / lint | yes | yes |
| Publish + serve | 1 project, 10 MB | per plan |
| Vector + keyword index | keyword only | both (embeddings metered) |

The preview shows an estimate (pages × sections × prompt sizes) before generate.

## 9. Acceptance bar (measurable)

- A 40-note markdown upload produces an index ≤ 10 KB (or split), every facts line anchored (`llms_lint.py facts` 0 High), ≥ 95 % of pages with ≥ 1 unit (R7), descriptions on 100 % of links (D1).
- Round trip: `llms-full.txt` splits back through `llms_acquire.split_llms_full` into the same page count.
- Regeneration with the same inputs and overrides is byte-stable except timestamps (P15).
- Agent test (01 P12) on the generated index ≥ 8/10 on the project's question bank.
- Deterministic path end-to-end for 200 pages < 2 min on one worker.

## 10. Security, rights, privacy

- Uploads are private by default and encrypted at rest; `expires_at` 30 days unless the project is published.
- Publishing makes the pages public: an explicit checkbox confirms the user has the right to publish; the provenance banner names the generator and date; third-party URLs the user pasted are index-only (no full text republished) unless they attest ownership.
- Secrets: P9 P5 runs before publish; hits block publishing until redacted.
- GitHub push uses a scoped OAuth token (contents:write on one repo), revocable.

## 11. Dependencies on other components (by number)

01 (gate), 09 (tree nodes as skeletons, `--register` writes `llmsFile` on the node), 12 (vocabulary file), 13 (publish to the shared catalogue), 15 (metering), 16/17 (indexing the result), 14 (the examples page links generated projects).

## 12. Open questions and assumptions

- Assumed converters: `pandoc` for docx, `pdftotext`/`pymupdf` for PDF (headings by font size heuristics), Notion/Obsidian handled as markdown trees with wikilinks rewritten to page twins.
- Open: whether `upload://` sources should be replaced by a stable content hash URL (`/p/<sha256>#anchor`) even before publish so unpublished zips are still self-consistent — leaning yes.
- Open: minimum viable OCR for scanned PDFs (out of v1).
- Assumed clustering uses the embed pool model (`mxbai-embed-large`) and never `nomic-embed-text` (the hub.db model — mixing returns nothing).
