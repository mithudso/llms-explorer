# Docset reference extraction — diagnosis, ideas, plan

**Date:** 2026-08-30 · **Status:** design for review · **Pilot docset:** `code.claude.com`
(`~/.claude/skills/web-text-mirror/text-mirror/code.claude.com.md`)

## 1. What is actually wrong

The pipeline is `mirror → distill → index`. Each stage runs, reports `done`, and
none of them produces the thing the pipeline exists for: a **referenceable list
of facts, commands, parameters and snippets** per docset. Measured on the pilot:

### 1.1 Mirror layer (trafilatura) — lossy on exactly the material that matters

| Symptom | Evidence (code.claude.com.md, 228 pages, 4.7 MB) |
|---|---|
| Code blocks / tab panels dropped | `**macOS, Linux, WSL:**` followed by nothing; 122 fences in 37k lines; `curl -fsSL` appears twice for a site whose install page is built on it |
| Step layouts shredded | hooks page renders as `1` / `Event fires` / `The ` / `` `PreToolUse` event fires `` on separate lines |
| Site chrome kept | 22% of non-blank lines are duplicates (28,740 unique of 37,033); the pricing/desktop FAQ paragraph appears 53× |
| Link-only lines | 3,144 lines are bare `[text](url)` — 8.5% of the file |
| Non-reference pages crawled | `/blog`, `/customers/*`, `/contact-sales`, `/community` sit beside `/docs/en/*` |
| One page = 535 KB | `/docs/en/changelog` is 11% of the whole mirror and has no date structure after extraction |

The same site serves clean markdown directly. Verified live today:

| URL | Result |
|---|---|
| `https://code.claude.com/docs/en/hooks.md` | 200, `text/markdown`, **316 KB with every code block intact** (the mirror's copy of this page is 124 KB of prose fragments) |
| `https://code.claude.com/docs/llms.txt` | 200, 45 KB index of every page |
| `https://code.claude.com/docs/llms-full.txt` | 200, **8.5 MB — the entire docset as markdown in one request** |
| `docs.claude.com`, `developers.openai.com`, `docs.github.com`, `pydantic.dev`, `openrouter.ai/docs`, `mongodb.com`, `developers.cloudflare.com` | `llms.txt` present |
| `tailscale.com`, `docs.python.org` | 404 — trafilatura path stays for these |

So for most of the estate the crawl was reconstructing, badly, a file the site
hands out for free.

### 1.2 Distill layer (`distill_offline.py bulk`) — no distillation happens

`~/dev/distillers/distill_offline.py` is **stdlib-only and zero-LLM by design**
(its CLAUDE.md says so). Its "extraction" is:

- `clean_and_split`: strip URLs, strip all punctuation except `.,;:!?()-`, join
  lines with spaces, split on sentence boundaries, keep anything > 20 chars.
- `_heuristic_type`: starts with a verb → `actionable`; contains a digit and
  "is/are/has" → `fact`; contains "fails/cannot/bug" → `problem`; else `statement`.

Result for the pilot: `code.claude.com_master.md` is **4.65 MB against a 4.74 MB
mirror** — 17,816 bullets, each a raw sentence with its punctuation scrubbed
(`Install it from the official marketplace: ( skill-creator plugin - Marketplace
claude-plugins-official not found : add the marketplace with plugin marketplace
add anthr…`), grouped into four buckets by regex. It is the mirror, re-ordered.

The **LLM half** of distillation — read a page, emit typed knowledge units — exists
only in the interactive `/distill` skill contract (`document-distiller`). It was
never wired into the pipeline. The pipeline runs the mechanical half alone and
calls the stage `done`.

### 1.3 Index layer — indexes the wrong thing, and the distill output is orphaned

- `stage_index` runs `docset_indexer index <mirror.md>`: it chunks the **raw
  mirror**. Nothing in `scripts/` or `mcp-server/` reads `*_master.md`; the only
  consumer of the distill stage is `queue_model` checking that
  `.<stem>_distill_index.json` exists to report the stage as complete.
- The Docsets tab's `file://` link opens the raw mirror. `hub_query_docset` returns
  raw chunks. That is the "hundreds of pages of repeating links".

Net: 38 docsets, 723 MB of mirrors, 408k chunks embedded, ~30 orphaned
`_master.md` files totalling ~90 MB, and no fact layer anywhere.

## 2. Brainstorm — every lever, and which to keep

Ranked by (value ÷ cost). ✅ keep · ➖ later · ❌ drop.

| # | Idea | Why | Verdict |
|---|---|---|---|
| A | **Acquire from `llms.txt` / `llms-full.txt` / `<page>.md`** when a site publishes them (Mintlify, Fern, Docusaurus-llms, GitBook all do). Write the result in the existing `====/URL:/====` banner format so every downstream tool keeps working. | Removes the lossy layer for most sites in one request; code blocks, tables, admonitions survive. | ✅ Phase 1 |
| B | **Fallback extractor that keeps structure** for sites without A: `trafilatura` with `include_formatting=True` (currently off), or `site_clone` HTML → markdown via a code-preserving converter. | Python docs / Tailscale have no llms.txt. | ✅ Phase 1 (fallback) |
| C | **Boilerplate strip by cross-page frequency**: a non-blank line present in > 5% of pages is chrome; drop link-only lines; drop nav bullet runs. Stdlib, deterministic, ~seconds. | 22% duplicates, 8.5% link-only in the pilot. Cheap and safe. | ✅ Phase 2 |
| D | **Page triage**: classify pages `reference / guide / changelog / marketing / index` from URL pattern + heading density; only `reference`/`guide` go to extraction; `changelog` gets its own dated-entry parser; `marketing`/`index` are dropped from the fact layer (kept in raw). | Halves LLM work; keeps `/customers/ramp` out of the facts. | ✅ Phase 2 |
| E | **Deterministic structure extraction** (no LLM): every fenced code block → snippet with its nearest heading as caption and the page URL; every table → parameter/option records; every `Heading → first paragraph` → a definition; env-var, CLI-flag, error-code and slash-command pages are already tabular — regex them into records. | Highest-precision reference material, zero tokens, and exactly what trafilatura was losing. | ✅ Phase 3 |
| F | **LLM unit extraction for prose** on the local Ollama pool (`semantic_ops.llm`, default `qwen3:8b`; the .75 GPU box can run a 14B/30B for better recall): per page, emit JSON units `{type, text, source_anchor, keywords}` using the `document-distiller` type set (concept / fact / actionable / question / problem / statement / quote / idea). Resume state + shard across boxes like `distill` does today. | This is the missing step. Deterministic passes carry the tables and code; the LLM carries the "X does Y because Z" knowledge. | ✅ Phase 4 |
| G | **Novelty / dedup on units**, not sentences: embed units with `embed_core`, drop cosine ≥ 0.9 duplicates within a docset (the pricing FAQ appears 53×). `distill_offline.py index/novelty` already does this for units — reuse it. | Keeps the fact list short. | ✅ Phase 4 |
| H | **Facts index beside the raw index**: `docset_indexer index --units facts.jsonl --name <key>__facts`; `hub_query_docset(layer="facts"\|"raw")` defaults to facts, falls back to raw. Docsets tab detail links `reference.md` and shows fact/snippet counts; `e` (refresh) reruns the refine chain. | Makes the fact layer the thing agents and humans hit first. | ✅ Phase 5 |
| I | **Quality gate**: 10 golden questions per pilot docset answered via `hub_ask` before/after; unit spot-check sample of 50 with a rubric (traceable? atomic? true to source?); compression ratio target ≤ 15% of cleaned source for the fact list. | Without it the next "done" is as hollow as the last. | ✅ Phase 0 + 6 |
| J | **Retire the bulk sentence funnel from the pipeline**: rename stage `distill` → `refine`; delete the orphaned `_master.md` files after the fact layer exists (they are regenerable). Keep `distill_offline.py`'s render/index/novelty/diff commands — they are fine; only `bulk`'s extractor is the problem. | Stops paying 90-minute stage budgets for nothing. | ✅ Phase 6 |
| K | **Skill generation from facts** (`facts.jsonl` → SKILL.md via the /dr contract) | The original end goal; needs the fact layer first. | ➖ after Phase 6 |
| L | Re-chunk raw index by heading instead of 1,500-char windows | Better raw hits, but the fact layer supersedes most of the value. | ➖ |
| M | Cloud-LLM extraction (Claude API) instead of local | Higher quality units; but 38k pages ≈ real money, and the pipeline's premise is local. Use for the pilot's quality comparison only. | ➖ optional in Phase 4 |
| N | Index the existing `_master.md` files as-is | They are the mirror re-ordered; indexing them doubles the noise. | ❌ |
| O | Fix `clean_and_split` heuristics | Polishing a sentence splitter does not produce facts. | ❌ |

## 3. Approaches

**Approach 1 — fix the source only.** A + B + C + H(raw). One or two days. The raw
index becomes clean and code-complete; queries return real docs. Still chunks,
not facts — the "list of referenceable material" is not delivered.

**Approach 2 — LLM-extract everything.** F on today's mirrors. Garbage in: the
LLM would be asked to recover install commands trafilatura already dropped. And
38k pages × ~15 s/page on `qwen3:8b` ≈ 160 GPU-hours before triage.

**Approach 3 — layered (recommended).** Clean acquisition → deterministic strip
and triage → deterministic structure extraction → LLM units for prose only →
facts index + surfaces, gated by measured quality, piloted on one docset before
touching the other 37. Each layer is independently testable and useful on its
own (Approach 1 is literally its first two phases), the LLM is pointed only at
prose that survived triage, and the token-free layers carry the reference
material trafilatura lost. This is the plan below.

## 4. Design

### 4.1 Data flow

```
site ──(A: llms-full.txt / page.md | B: structured trafilatura)──► <stem>.md   (banner format, unchanged contract)
<stem>.md ──(C strip, D triage)──► <stem>.clean.md + <stem>.pages.json  (page: url, class, headings, text)
<stem>.pages.json ──(E)──► reference/snippets.jsonl · tables.jsonl · definitions.jsonl
<stem>.pages.json ──(F on class∈{reference,guide}, G dedup)──► reference/units.jsonl
E + F ──(render)──► reference/reference.md  (grouped by page, then by type; every line ends in its source anchor)
units + snippets + tables ──(H)──► docset <key>__facts   (chroma/sqlite, same registry, backend, model rules)
```

All new artifacts live beside the mirror in `<stem>.reference/` (rsync'd back
like `.pages/` is today; gitignored runtime state). One writer per store rule
holds: only M5 indexes.

### 4.2 Unit record (one schema for E and F)

```json
{"id": "u0412", "type": "actionable", "text": "Run `claude auth login` and choose the claude.ai option.",
 "source_url": "https://code.claude.com/docs/en/remote-control", "anchor": "#re-authenticate", "page_class": "guide",
 "keywords": ["auth", "login"], "code": null, "origin": "llm|code|table|heading"}
```

`origin` says which pass produced it, so a quality problem is attributable to a
pass. `source_url + anchor` is the provenance the distillers repo already calls
sacred; nothing drops it.

### 4.3 Components (new or changed)

| Component | Change |
|---|---|
| `web-text-mirror/scripts/text_mirror.py` | `--prefer-llms` (default on): probe `llms-full.txt`, then `llms.txt` + per-page `.md`, then fall back. Emits the same banner file. `include_formatting=True` on the fallback. Live copy is `~/.claude/skills/web-text-mirror/scripts` (see hub-architect: check which copy executes). |
| `scripts/docset_refine.py` (new, stdlib + `embed_core`) | Subcommands `clean` (C+D), `extract` (E), `units` (F+G, resumable, `--shard-index/--shard-count` like distill), `render`, `all`. Reads/writes `<stem>.reference/`. |
| `scripts/pipeline_manager.py` | Stage `distill` → `refine` (`docset_refine.py all`); `index` indexes `<stem>.clean.md` as raw and `reference/*.jsonl` as `<key>__facts`. |
| `scripts/docset_indexer.py` | `index --units FILE` path: one chunk per unit, metadata carries `type/origin/source_url`; `query` filters by `layer`. |
| `mcp-server/hub_mcp_server.py` | `hub_query_docset(layer="facts")` default with raw fallback; `hub_list_docsets` shows fact counts. |
| `hub_manager` Docsets tab | detail pane: fact/snippet counts + `reference.md` link; `e` refresh = `docset_refine.py all` then reindex. |
| `semantic_ops.llm` | unchanged; `docset_refine units` uses `generate()` with the pool. Prompt lives in `docset_refine.py` as a named constant so `/pdo` can optimize it. |
| `~/dev/distillers` | `bulk` extractor deprecated in the pipeline; `render/index/novelty/diff` reused by `docset_refine`. |

### 4.4 The extraction prompt (F) — first draft, to be run through `/pdo` in Phase 4

System: "You extract atomic, source-faithful knowledge units from one
documentation page. Output JSON only." User: the page's cleaned markdown (≤ 6k
tokens; longer pages are split at H2), the page URL, and the type set with one
example each. Rules: no unit longer than 2 sentences; never invent; keep exact
command/flag/env-var spellings; a unit that restates a code block references it
by fence index instead of copying it; skip marketing sentences.

### 4.5 Error handling

- Acquisition: a site with `llms.txt` but failing page `.md` fetches falls back per
  page, never per site. A `llms-full.txt` under 1 KB is treated as absent.
- Refine: every pass is idempotent and resumable (state file keyed by page URL +
  content hash); a failed LLM page is recorded and retried, and the run reports
  `units_failed` like `index` reports `failed_chunks`; > 5% failed → stage fails.
- Index: stage-then-swap already exists for the raw collection; the facts
  collection uses the same path.

### 4.6 Testing

Hermetic tests per pass with a 3-page fixture mirror (banner format): strip
removes the repeated footer, triage classes the URLs, extract yields the fenced
block with its heading, units parsing tolerates a malformed LLM reply, render
keeps every anchor. Live acceptance in Phase 0/6: the golden-question set.

## 5. Plan

Estimates are focused effort; the pilot is `code.claude.com` throughout.

### Phase 0 — baseline (½ day)
1. Write 10 golden questions for the pilot (install on Windows; hook exit codes;
   `CLAUDE_CODE_SYNC_SKILLS`; sandbox fallback; …) and record today's `hub_ask`
   answers + sources. This is the before/after yardstick.
2. Record baseline numbers: mirror size, unique-line ratio, fences, index chunks.
- Exit: `docs/superpowers/specs/…-baseline.md` with answers scored 0/1/2.

### Phase 1 — clean acquisition (1 day)
1. `text_mirror.py --prefer-llms`: fetch `llms-full.txt` → split on its page
   headers into banner pages; else `llms.txt` → per-page `.md`; else current path
   with `include_formatting=True`. Same output file, same contract.
2. Re-mirror the pilot; diff: fences, unique-line ratio, size.
3. Probe all 38 seed hosts for `llms.txt` and record the result in the queue
   item (`acquire: llms-full|llms|trafilatura`).
- Exit: pilot mirror has the hooks page's code blocks; `docset_indexer index`
  still parses it; tests for the splitter.

### Phase 2 — strip + triage (1 day)
1. `docset_refine.py clean`: cross-page line-frequency strip (> 5% of pages),
   link-only line drop, nav-run drop; per-page `class` by URL rules + heading
   density; changelog parser (date → entries).
2. Emit `<stem>.clean.md` (banner format, so the raw index can use it) and
   `<stem>.pages.json`.
- Exit: pilot unique-line ratio > 95%; `/customers/*` classed `marketing`;
  changelog yields dated entries; tests.

### Phase 3 — deterministic reference extraction (1 day)
1. `docset_refine.py extract`: snippets (fence + language + nearest heading +
   URL), tables → records, `H2/H3 → first paragraph` definitions; special-case
   parsers for env-vars, CLI flags, slash commands, hook events, error codes.
2. `render` → `reference.md` grouped by page.
- Exit: pilot yields every env var on `/docs/en/env-vars` as a record; snippet
  count ≈ fence count; tests.

### Phase 4 — LLM units for prose (2 days + GPU time)
1. `docset_refine.py units`: page → prompt → JSON units, `origin: llm`; resumable
   state; sharded over boxes via the existing `BoxPool` placement; quiet-hours
   aware (reuse `box_schedule`).
2. Dedup with `embed_core` (cosine ≥ 0.9) — reuse `distill_offline novelty`.
3. Run `/pdo` on the prompt once 20 pages of output exist; compare `qwen3:8b`
   vs a 14B/30B model on the .75 box on the same 20 pages (unit count,
   spot-check score); optional Claude-API run on the same 20 for a ceiling.
- Exit: pilot `units.jsonl` ≤ 15% of cleaned prose size; 50-unit spot check
  ≥ 90% "traceable + true"; failed pages < 5%.

### Phase 5 — facts index + surfaces (1 day)
1. `docset_indexer index --units` → `<key>__facts`; `query --layer`.
2. `hub_query_docset(layer=)`, `hub_list_docsets` fact counts.
3. Docsets tab: detail shows facts/snippets + `reference.md` link; `e` refresh
   runs `docset_refine.py all` then reindexes both layers.
4. `pipeline_manager`: stage `distill` → `refine`.
- Exit: golden questions re-run via `hub_ask` — score improves; the tab opens
  `reference.md`, not the raw dump.

### Phase 6 — quality gate, rollout, cleanup (2–3 days elapsed, mostly machine time)
1. Rollout order: sites with `llms-full.txt` first (cheapest, best), then `llms.txt`,
   then trafilatura sites. Use `c` (expand) / `C` on the Queue tab — it already
   reruns every stage.
2. Per docset: automated gate (unique-line ratio, unit ratio, failed %) must pass
   before `<key>__facts` swaps in.
3. Delete orphaned `*_master.md` (regenerable) and drop the `bulk` funnel from the
   pipeline path; note it in `~/dev/distillers/CLAUDE.md`.
4. Replicate: `.reference/` dirs ride the existing rsync push.
- Exit: `hub_list_docsets` shows a fact count for every docset; `_master.md` gone.

### Later
- K: `facts.jsonl → SKILL.md` generator (the original docs-to-skill goal).
- L: heading-aware raw chunking.

## 6. Decisions — CONFIRMED 2026-08-30

1. **Local Ollama for the bulk unit pass, Claude (`claude -p`) for a polish pass** over the extracted units (grammar/truncation fixes, drop marketing/untrue units) — polish is manual / `p` on the Docsets tab, not on the pipeline path.
2. `hub_query_docset` defaults to `layer="auto"` → facts when present, raw fallback.
3. `marketing` / `index` pages are dropped from the fact layer (and from the clean mirror).
4. `distill_offline.py bulk` leaves the pipeline path; stage `distill` → `refine`.
5. Both: pilot on code.claude.com AND roll the llms.txt acquisition out estate-wide in parallel.

Implementation plan: `docs/superpowers/plans/2026-08-30-docset-reference-extraction.md`.

### Original questions (kept for the record)

1. **Local-only extraction** (Ollama pool, `qwen3:8b` default, bigger model on the
   GPU box for comparison) vs allowing Claude API for the prose pass.
   Recommendation: local, with a 20-page API ceiling run for calibration only.
2. **Where the fact layer is exposed by default**: `hub_query_docset` defaults to
   `facts` with raw fallback (recommended), or stays raw with `facts` opt-in.
3. **Triage strictness**: drop `marketing`/`index` pages from the fact layer
   entirely (recommended) or keep them at low weight.
4. **Retire `distill_offline.py bulk` from the pipeline** (recommended) or keep it
   as a parallel artifact.
5. **Pilot first, then rollout** (recommended) or rollout the acquisition fix
   (Phase 1) estate-wide immediately since it is independent and cheap.
