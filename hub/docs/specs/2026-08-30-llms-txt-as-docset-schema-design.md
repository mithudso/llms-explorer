# llms.txt as the hub's docset schema — implementation, methodology adaptation, single product → family

**Date:** 2026-08-30 · **Status:** design + first implementation shipped (`docset_refine export` / `family`)
**Research:** `/dr` run 2026-08-30 → `~/.claude/skills/document-formats/references/llms-txt*.md` (4 files, ~120 sources)
**Pilot:** code.claude.com → `~/.claude/skills/web-text-mirror/text-mirror/code.claude.com.llms/`

## 0. What six months of trying were fighting

The three things you were recreating by hand already have a spec, live exemplars and consumer
behaviour you can measure:

| You wanted | What exists (as of 2026-08-30) |
|---|---|
| a per-site "facts + references" file | `llms.txt` (spec v2, 2026-08-10) — a curated *index*; the facts live behind its links |
| the whole docset in one LLM-readable file | `llms-full.txt` — not in the spec; three grammars in the wild (Mintlify `# Title`/`Source:`, Anthropic YAML blocks, Cloudflare frontmatter) |
| a way to get clean markdown for any page | `.md` twins (`page.md` / `page.html.md`), `Accept: text/markdown` (Mintlify/GitBook/Fern; Cloudflare edge since 2026-02-12), docs APIs (GitHub) |
| a family / hub of products | spec-v2 nested indexes: `/docs/llms.txt` covers `/docs/`, most-specific wins — Cloudflare's `/llms.txt` → per-product `/<product>/llms.txt` is the live model |
| proof anyone reads it | Ahrefs 137k-domain logs (May 2026): 97% of files get zero AI requests, **but the `Claude-Code` UA out-fetched every retrieval bot** — agents pointed at a file read it; nothing discovers it unprompted |

The consequence for the hub: llms.txt is worth adopting as the **interchange schema for agents we control** (our own MCP tools, Claude Code, subagents), not as a GEO play. Our pipeline's own experience matches the log studies — the 1-second `llms-full.txt` fetch replaced an hours-long crawl and recovered 5,250 code fences the crawl had lost.

## 1. How to implement it (done today, on the pilot)

`docset_refine` gained two commands; `all` ends with `export`.

```
PYTHONPATH=scripts .venv/bin/python -m docset_refine export <mirror.md> [--title T] [--summary S]
  → <stem>.llms/llms.txt         spec v2: H1, blockquote, path-derived H2 sections, .md twins, changelog → ## Optional
                 llms-full.txt   Mintlify grammar, header comment names it; round-trips through llms_acquire.split_llms_full
                 llms-small.txt  reference-class pages first, ≤ ~50k tokens (the Cursor-stability ceiling)
                 llms-facts.txt  OUR extension: the fact layer (snippets / parameters / definitions / LLM units), every line source-anchored
                 manifest.json   bytes + approximate tokens (chars/4) per file — what a consumer needs to budget

PYTHONPATH=scripts .venv/bin/python -m docset_refine family <mirror1.md> <mirror2.md> … --name N --summary S --out <path>/llms.txt [--base-url https://host/llms]
  → one link per product's llms.txt with page + token counts; ## Facts links each llms-facts.txt
```

Pilot numbers (code.claude.com, 191 pages): llms.txt ≈ 10k tokens · llms-full ≈ 2.1M · llms-small ≈ 50k · llms-facts ≈ 786k (11,965 units).

Reading side: `llms_acquire.split_llms_full()` now handles all three published grammars plus Firecrawl
delimiters and strips the `Documentation Index` navigation blockquote; `probe()` only accepts an
llms-full.txt that actually contains pages (PayPal's redirects to its 1.5 KB index).

What is deliberately *not* done yet: serving. The files sit under `text-mirror/<stem>.llms/`; nothing
answers `GET /llms.txt` for them. See §4.

## 2. Adapting the current methodology to the schema

The pipeline already had the right shape; the schema tells us what each stage's contract should be.

| Stage | Before | Now / to do |
|---|---|---|
| **acquire** | trafilatura crawl into the `====/URL:/====` banner mirror | ladder: llms-full.txt → llms.txt + `.md` twins → `Accept: text/markdown` → docs API → structured trafilatura (done except `Accept` and docs-API rungs) |
| **canonical page format** | banner mirror (ours) | keep the banner mirror as the *internal* format (every tool reads it); treat Mintlify-grammar llms-full.txt as the *external* twin — the two are 1:1 convertible (`split_llms_full` ↔ `build_full`) |
| **refine** | clean/triage/extract/LLM units/render | unchanged; now also produces the export. Descriptions for the index come from the `definition` unit of each page — the deterministic pass pays twice |
| **index** | raw + facts collections | unchanged; `llms-facts.txt` is the human/agent-readable twin of the `<key>__facts` collection |
| **publish** | nothing | `export` files + `manifest.json` (this design); serving is §4 |
| **consume (our agents)** | `hub_query_docset`, `hub_ask` | add the llms.txt as the *orientation* document an agent reads first (the spec's "view or search, then follow links"): a `hub_docset_index(docset)` MCP tool returning llms.txt text, and `hub_query_docset` results pointing at `.md` twins |

Two methodology changes the research forces:

1. **Descriptions are the product.** Every generator that emits good indexes takes descriptions from
   page frontmatter/nav; crawl-based ones invent them with a small model and they are worse. Our
   `definition` units (H1 + first sentence) are extractive and cheap; keep them, and let the LLM pass
   (`units`) *polish* descriptions only when the extractive one is missing or under 40 chars.
2. **Size is a producer-side problem.** No consumer truncates intelligently. Publish a ladder
   (index / small / full / facts) with token counts, never one giant file — Fern dropped llms-full
   entirely; Mantine cut 2.2 MB to 45 KB; Cursor breaks above ~50–60k tokens.

## 3. Single product → concept family

**Single product** = one docset = one `<stem>.llms/` directory = one `llms.txt` whose H2 sections
come from the URL tree (a nav tree would be better; the llms-acquired mirrors carry the original
section order, which we can adopt next).

**Family** = the spec's nesting applied to *our* taxonomy:

```
/llms.txt                         ← hub-wide: one line per family (concept-tree roots / skill hubs)
/<family>/llms.txt                ← family: one line per product llms.txt + counts, ## Facts, ## Shared
/<family>/<product>/llms.txt      ← product: pages
/<family>/<product>/llms-facts.txt
```

- The **concept tree** is the family definition. A tree root (e.g. "llms.txt and LLM-readable
  documentation") or a skill hub (e.g. `document-formats`) is a family; its docsets are the products.
  `docset_refine family` takes the product mirrors and writes the family file; a `hub` command (next)
  walks `concept-tree/tree.json` and writes the root file from the families.
- **Two hops max.** Family files link indexes, never pages; a consumer reads root → family → product,
  then follows a page link. This is exactly Cloudflare's shape (`/llms.txt` ~105 entries → 9 sections →
  per-product files with 500+ `.md` links).
- **Shared material goes up, once.** Cross-product errors, auth, glossary belong in the family file's
  `## Shared`; never duplicated into product files.
- **Counts travel with links.** Every family line carries page count and approximate tokens
  (llmstxt.site's most useful column); a consumer can decide before fetching.
- **Facts are a first-class layer at every level.** `llms-facts.txt` per product, linked from the family
  file under `## Facts`; the family file can later carry a merged, deduplicated facts file for the whole
  group (the `units.dedup` embedding pass already exists).
- **Rights.** A family index of third-party products is links + descriptions — publishable. The
  per-product `llms-full.txt` of a third-party site is a stored republication — keep it internal
  (Cloudflare Content Signals `ai-train=no` is the owner's express reservation).

## 4. Next steps (in order)

1. **Serve it.** The web-text-mirror `--serve` HTTP process already exists; add routes `/llms/<stem>.llms/*`
   and `/llms.txt` (hub root) with `Content-Type: text/markdown; charset=utf-8` and
   `Link: rel="describedby"` headers, so Claude Code / MCP tools can be pointed at a URL.
2. **`hub_docset_index` MCP tool** + `hub_query_docset` hits linking `.md` twins.
3. **`docset_refine hub`** — root llms.txt from `concept-tree/tree.json` families.
4. **Nav-order sections** for llms-acquired mirrors (keep the source llms.txt's section order instead of
   deriving from URL paths).
5. **Family facts** — merged + deduped `llms-facts.txt` per family.
6. **CI check** — `llms-txt-validator --check-links` equivalent inside `docset_rollout.py cleanup`.
7. Rollout: `export` runs inside `all`, so every docset refined from now on gets its `.llms/` directory;
   run `export` alone on the 37 existing docsets once their `reference/` dirs exist.

## 5. Where the knowledge lives

- Spec, grammars, discovery, consumers, gaps: `document-formats/references/llms-txt.md`
- Generator catalog + quality practices: `…/llms-txt-generation-tooling.md`
- Dated adoption/log evidence, vendor grading: `…/llms-txt-ecosystem-evidence.md`
- Recreation ladder, lenient parsing, family pattern, rights: `…/llms-txt-recreation-and-aggregation.md`
- Concept tree: root "llms.txt and LLM-readable documentation" + 5 researched children → `document-formats`
