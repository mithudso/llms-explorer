---
title: "V2 vs V1"
description: "Compare the llms.txt proposal’s August 2026 v2 changes with the hub pipeline’s V2 artifacts, migration steps, and limits of the compatibility assessment."
date: "2026-08-31"
tags: ["spec", "pipeline", "migration", "compatibility"]
sources:
  - "docs/site/components/11-v2-vs-v1.md"
  - ".claude/skills/document-formats/references/llms-txt.md"
  - "hub/docs/specs/2026-08-30-docset-reference-extraction-design.md"
  - "hub/docs/specs/2026-08-30-llms-txt-as-docset-schema-design.md"
---

Two different things are called "v2" on this site, and they confuse everyone in the same
way. The **llms.txt spec** went from v1 to v2 on 2026-08-10, and a file written against v1 is
still valid. The **hub's pipeline** went from V1 to V2 on 2026-08-30, and the V1 artifacts are
retired. One is a proposal that loosened; the other is a toolchain that was replaced. They are
laid out side by side below because a reader with a 2025 file usually needs both answers:
"is my file still valid?" (yes) and "why did the folder layout change?" (because the old one
produced output nobody consumed).

## The spec: v1 → v2

The spec's structure did not change: an optional BOM, an H1, a blockquote, free markdown
without headings, then H2 sections holding `- [name](url): notes` lines. What changed is
which parts are required, where the file may live, and how a consumer is expected to use it.

| Rule | v1 | v2 (2026-08-10) | Effect on an existing file |
|---|---|---|---|
| Required elements | H1 + blockquote + sections implied | **H1 only** is required; blockquote, prose and sections are optional | none is invalidated; the lint still scores a missing blockquote as Medium (I2) — a quality finding, not a validity one |
| Placement | `/llms.txt` at the site root | root **or any subpath** (`/docs/llms.txt`); a file covers the URLs under its path; where several apply, **the most specific wins** | enables families and split roots (`<section>/llms.txt`) |
| Discovery | none | `rel="describedby"` links to the index; `rel="alternate" type="text/markdown"` identifies a twin | add discovery links through HTML or HTTP headers as applicable (see the [serving reference](/reference/usage/#1-serving)) |
| Markdown twins | `page.html.md` | `page.html.md` **or** `page.md`; directories append `index.html.md` or `index.md` | either form passes the twin probe |
| `## Optional` | mechanical: "can be skipped if a shorter context is needed", consumed by `llms_txt2ctx` | a **convention** for secondary information; `llms_txt2ctx` and its context-expansion mechanics are no longer part of the proposal | keep it last; build nothing that depends on it |
| BOM | — | an optional BOM is tolerated | the lint strips it as hygiene (P14) |
| Consumption expectation | expand the file into context | "view or search the index, then follow the relevant links"; the index stays small; detail lives behind links | the size ladder (small / full) becomes the producer's job |
| `/.well-known/` | — | explicitly rejected: well-known URIs exist only at the origin root, which defeats subpath scoping | serve at the root or the subpath, not under `.well-known` |

The one-sentence summary: v2 made the file *smaller in obligation and larger in reach*. Less
is required, more places may hold one, and the reader is now told to search-and-follow rather
than to inhale. The consumption sentence is the important one for producers. If an agent is
expected to read the index and then fetch two pages, the index has to be small enough to read
and descriptive enough to choose from — which is why the lint measures both.

## The pipeline: V1 → V2

The hub's V1 pipeline produced site dumps. It crawled with trafilatura, wrote one banner
mirror per site, distilled that mirror with a zero-LLM bulk pass, and indexed the raw text in
one vector layer. The distilled output was never consumed: the working notes describe it as
"hundreds of pages of repeating internal links". V2 keeps the banner mirror as the internal
format and replaces everything around it.

| Stage | V1 (to 2026-08-29) | V2 (from 2026-08-30) |
|---|---|---|
| Acquire | trafilatura BFS crawl → banner mirror | `llms_acquire.py` tries the site’s `llms-full.txt`, then its `llms.txt` and absolute HTTP(S) links fetched once as text; if neither yields pages, the caller owns the crawl fallback. The banner mirror stays the internal format |
| Clean | none (raw HTML → text) | `docset_refine clean`: boilerplate lines, MDX → markdown, page classes (reference / guide / changelog / marketing / index) |
| Extract | `distill_offline.py bulk` — zero-LLM, output never consumed | `extract` (code snippets, table rows → `parameter`, definitions, changelog `change` units; anchors to real source headings) + `units` (local LLM under the evidence rule) + `polish` (Claude) |
| Export | none | `export_llms`: index (split above 10 KB) / full (Mintlify grammar) / small (≤ ~50k tokens) / facts / `manifest.json`; `topical`; `vocabulary` |
| Index | one raw vector layer (`nomic-embed-text` in `hub.db` for files; `mxbai-embed-large` for docsets) | raw **and** facts vector layers, plus an FTS5 keyword layer beside each (`docset_indexer keyword-index`) |
| Serve | `web-text-mirror --serve` (HTML) | `llms_serve.py`: `/llms.txt`, `/d/<stem>/…` (with sections), `/m/<key>/…`, `/t/<slug>/…`, markdown headers on every response |
| Gate | none | `llms_lint.py` (the deterministic passes P0–P3, P5–P7, P9, P14) inside `docset_rollout cleanup`; `/ldo` for the model, live and family passes |
| Artifacts | `<stem>.pages/`, `_master.md`, `._distill_index.json` | `<stem>.reference/{pages.json, structured.jsonl, units.jsonl, all_units.jsonl}` and `<stem>.llms/` |

The wider acquisition ladder — `Accept: text/markdown` negotiation and docs-API stages — is a proposed design, not behavior implemented in this `llms_acquire.py`. Its index path rejects HTML targets and does not recursively follow section or family indexes.

"V2" for the pipeline is a naming choice made on this site; the code carries no version
constant. Dating it (2026-08-30) is more honest than numbering it, and the tables here do
that.

The measured shape of one V2 export, from `outputs/exports/code.claude.com.llms/manifest.json`
(191 pages, acquired from the publisher's own `llms-full.txt`): the root index is 1,136 bytes
(~280 tokens) and splits into three section indexes; `llms-small.txt` is 199,155 chars
(~49,785 tokens, just under the budget); `llms-full.txt` is ~2.1M tokens; `llms-facts.txt`
held 14,031 units (~845k tokens) in the reported 2026-08-30 snapshot. The checked-in manifest has since changed; these historical fact counts are not a current manifest reading. The V1 notes report no comparable export metrics.

## Migration

For a **publisher** with a v1 file:

1. From this repository, run `python3 hub/scripts/llms_lint.py check <file> --check-links`. A dedicated `llmsx migrate` command is a proposed interface, not a shipped command; use the lint findings to choose the steps below.
2. If the report says *full file wearing the wrong name* — page bodies inside `llms.txt`, a
   file over 100 KB (I6) — split it into `llms.txt` + `llms-full.txt`. `docset_refine export`
   does this from a mirror; by hand, the index keeps the link lines and the full file takes
   the bodies in the Mintlify grammar (`# Title` / `Source: <url>` / blank / body).
3. Add `.md` twins for linked pages (either form) and discovery links in HTML or HTTP headers as applicable (H3).
4. Move skippable material — changelog, legal, old posts — to a trailing `## Optional` (N4).
5. If the index is over 10 KB: hub-and-spoke split. `## Sections` in the root, one
   `<slug>/llms.txt` per section, counts on every section line.
6. Re-lint. The bar is 0 High.

For a **hub user** with V1 folders: build and check the reference and exported artifacts first. Preview retirement with `docset_rollout cleanup --dry-run`, inspect the listed files, and preserve a backup before executing cleanup. The current implementation uses adjacent `<stem>.reference/summary.json` as its guard. It removes matched legacy files *inside* `<stem>.pages/`, leaves the directory itself, and skips `._` files. That guard does not establish a usable indexed fact layer; the lint runs after deletion in a non-dry run.

For most 2025 files the report's first line is "nothing required". The recommendations that
follow are the twins and the headers, because those are what v2 added for consumers to find
the file at all.

## Compatibility matrix

Rows are producer choices; columns are consumers. This is a 2026-08-30 compatibility assessment. For index rows, the acquisition column describes the direct index path when no usable `llms-full.txt` is found; linked indexes are not recursively expanded. Repository code supports the scoped acquisition and lint claims; the vendor/client columns are expectations that require a configured fetch tool and fresh consumer tests. No consumer-test receipts are included, so they should not be read as verified product guarantees.

| producer choice | Claude Code (`WebFetch` / hub MCP) | Cursor | generic MCP client | `llms_acquire` | lint | Lighthouse agentic audit |
|---|---|---|---|---|---|---|
| v1 file at root | works | works | works | works | works (I2 Medium if no blockquote) | works |
| v2 file at root | works | works | works | works | works | works |
| v2 file at a subpath only | works if given the URL | degraded — no root discovery | works if given the URL | works — the ladder probes the given path | works | degraded — expects the root |
| split root (`## Sections`) | works — follows section links | works — one extra hop | works | degraded — no index recursion; relative targets are skipped | works — `check DIR` walks sections | works |
| family file (links only indexes) | works | works | works | degraded — absolute targets become page text; no recursion | works (F1 requires index targets) | not evaluated |
| `llms-full.txt`, Mintlify grammar | works via `hub_llms_full_read(page=…)` | degraded for large files (the reported ~50k threshold is unverified) | works | works — `split_llms_full` parses page blocks | works | not evaluated |
| `llms-full.txt`, YAML-block or Cloudflare frontmatter grammar | works | large-file behavior unverified | works | works — splitter recognizes YAML/body structures | works | not evaluated |
| `llms-full.txt` served **as** `llms.txt` | degraded — the index is unreadable at that size | breaks | degraded | degraded — the index path does not detect and split a full file | **High** (I6) | breaks |
| no `.md` twins | works — fetches HTML | works | works | degraded for HTML-only targets — no `Accept` probe; caller owns crawl | High (N6, with `--check-links`) | degraded |
| no `Link` headers | works | works | works | works | Low (H3) | degraded |

Read down a column to see what a given consumer needs; read across a row to see what a given
choice may cost. Serving a full file under the index’s name impairs several consumers and fails the size lint; the acquisition index path does not automatically detect and split it. Publish it under `llms-full.txt` for the full-file path.

## What breaks

Honest list of what does not survive the two transitions.

On the **spec** side, nothing a v1 file relied on is invalidated, but two things stop
meaning what they meant:

- **`## Optional` is no longer mechanical.** A consumer that skipped it "when context is
  short" was implementing v1's `llms_txt2ctx`; that tool is out of the proposal. Keep the
  section, keep it last, and do not put reference material in it — but expect nothing to
  skip it for you.
- **"Expand into context" is no longer the reading model.** A file designed to be inhaled
  whole (long descriptions, page bodies, every URL on the site) is now a full file wearing an
  index's name. Under v2 it is expected to be searched and followed, so it has to be small.

On the **pipeline** side:

- **Some V1 artifacts are retired by cleanup.** With the `summary.json` guard, it removes matching legacy files inside `<stem>.pages/`; it leaves that directory and skips `._` files. Update callers of retired files to read `<stem>.reference/` and `<stem>.llms/`, and check the dry-run list for your actual paths.
- **The raw vector layer is no longer the default answer.** `query --layer auto` prefers the
  facts layer when one exists. A query that used to return a text chunk now returns a
  source-anchored unit; callers that parsed the chunk shape need the unit shape.
- **The two embedding models do not mix.** `hub.db` file vectors are `nomic-embed-text`
  (768d); every docset and semantic-ops store is `mxbai-embed-large` (1024d). This was true
  in V1 too, but V2 added stores, so there are more places to get it wrong. Mixing them
  makes cosine comparison invalid. The current SQLite backend raises `embedding model mismatch` when every stored vector has a different dimension; use each docset’s recorded model rather than relying on an empty result.
- **Serving moved from HTML to markdown-with-headers.** `web-text-mirror --serve` returned
  HTML; `llms_serve.py` returns `text/markdown; charset=utf-8` with `X-Markdown-Tokens` and
  `Link: rel="describedby"`. A client that scraped the HTML view has to read markdown.

What does *not* break, and is worth saying plainly: every v1 `llms.txt` still parses, still
lints, and still answers questions for an agent handed its URL. The migration guide above is
a list of recommendations for one, not repairs.
