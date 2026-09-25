# How-to: a topical llms file from a pool of uncategorized facts

<!-- llms-deep-optimizer · references/facts-to-llms-howto.md · 2026-08-30 -->

Goal: given a heap of facts about a subject (units from one or many docsets, notes, research
spokes, distilled mirrors), produce a **topical** `llms.txt` + `llms-facts.txt` (+ optional
`llms-full.txt`) that meets every bar in `attributes.md`, is indexed for semantic AND keyword
lookup, and is navigable in ≤ 2 hops — the same storage/retrieval/navigation standard a
single-product export gets, but organised by concept instead of by site.

**Contents**
0. What "fact" and "pool" mean here
1. Normalise the pool
2. Grade and dedupe
3. Discover the topic skeleton
4. Assign facts to topics
5. Choose the link targets
6. Write the files
7. Index both ways
8. Run `/ldo` and the agent test
9. Register and serve
10. Keep it fresh
Appendix A — worked example (llms.txt family)
Appendix B — question bank shape

## 0. What "fact" and "pool" mean here

A **fact** is one unit line in the hub's shape:

```
- [type] text — <url-or-path>#<anchor> · keywords: a, b, c · verified-as-of: YYYY-MM-DD
```

(the first three fields are exactly what `export_llms.build_facts` renders from a
`units.jsonl` record — `{id, type, text, source_url, anchor, page_class, keywords, code,
origin}`; `keywords` and `verified-as-of` are optional trailing fields.) `type ∈
docset_refine.UNIT_TYPES` = {concept, fact, actionable, question, problem, statement, quote,
idea, snippet, parameter, definition, change}; a spec/limit claim is a `statement`, a how-to
step an `actionable`, a known failure a `problem`. A fact
with no source is a claim, not a fact; it can enter the pool only as `BLOCKED: unsourced` and
never reaches the file (P7 High). A **pool** is any mix of: `*.refine/units.jsonl` from docsets,
lines from `llms-facts.txt` files, bullet notes, `/dr` reference spokes (each footnoted sentence
becomes a fact with the footnote's URL), distilled mirrors (`*.distilled.md`).

## 1. Normalise the pool

`docset_refine topical` (shipped 2026-08-30, `scripts/docset_refine/topical.py`) does §1–§6 in
one command; the sections below explain what it does and where to intervene.

```
PYTHONPATH=scripts .venv/bin/python -m docset_refine topical \
  --from ~/.claude/skills/web-text-mirror/text-mirror/llmstxt.org.reference/all_units.jsonl \
  --from ~/.claude/skills/web-text-mirror/text-mirror/developers.cloudflare.com.llms/llms-facts.txt \
  --from ~/.claude/skills/document-formats/references/llms-txt.md \
  --subject "llms.txt and LLM-readable documentation" \
  --out ~/.global-ai-hub/llms-topical/llms-txt.llms/ [--summary S] [--base-url /t/llms-txt] [--no-embed] [--register]
```

`--from` accepts `units.jsonl`, `llms-facts.txt` lines, and `/dr` reference spokes (every
sentence carrying a `[^n]` footnote becomes a fact anchored to the footnote URL). Each record
becomes `{id, type, text, source, anchor, keywords[], origin, also[], file}`; a type outside
`UNIT_TYPES` is coerced to `statement`. Lines that fail the grammar or carry no source are
written to `pool.rejected.jsonl` with the reason — fix or drop; never guess a source.

## 2. Grade and dedupe

1. **Source grade** (deep-research-methods hierarchy): spec/standard > vendor docs > primary
   measurement (logs, studies) > reputable secondary > blog/opinion. Record `grade` on the
   record; a topical file may include lower grades but the description (§6) must say so
   ("community practice", "vendor claim").
2. **Exact dedupe** on normalised text (case, whitespace, trailing period).
3. **Near-dedupe** with the pool embedding model (`embed_core`, `mxbai-embed-large`):
   cosine ≥ 0.93 → keep the higher-graded, fresher record; add the loser's source as
   `also:` so the fact carries two anchors (corroboration is retrievable evidence, not
   noise).
4. **Contradictions**: near-dup pairs that disagree on a number/version → keep both, type
   them `constraint`, stamp each with its `verified-as-of`, and flag for `/dr --refresh`.

`docset_refine units --dedup` already implements 2–3 for a single docset; run it over the
merged pool with `--pool`.

## 3. Discover the topic skeleton

The skeleton is the set of H2 sections. Get it from three sources, in this order of trust:

1. **Concept tree** — `hub_concept_lookup("<subject>")` → its `childConcepts` are the
   candidate sections; frontier children (known, unresearched) become `## Optional` entries or
   `BLOCKED: unresearched` rows. Run `concept-family-explorer` first if the subject has no
   node.
2. **Clustering the pool** — `semantic_ops.cluster` over fact embeddings (k ≈ √n, cap 12);
   name each cluster by its top TF-IDF keywords + the most central `definition` unit. Clusters
   that map onto tree children merge with them; new clusters are proposed as tree children
   (`hub_concept_queue` to record them).
3. **Reader questions** — the question bank (Appendix B) or `hub_ask` history: every
   question should land in exactly one section. A question with no home → a missing section;
   a section no question lands in → merge it or demote to `## Optional`.

Order sections by expected query frequency (definition/spec → how-to → reference → evidence
→ tooling → optional). Aim for 5–9 sections; > 12 → split hub-and-spoke (a family: root file
links per-topic `llms.txt` files).

## 4. Assign facts to topics

Each fact gets exactly one section (embedding nearest-centroid, then a model pass on the 10%
lowest-margin assignments). Cross-cutting facts (glossary, errors, versions) go to a
`## Shared` section once — never duplicated. Within a section, order: `definition`/`concept` first, then
`statement`/`parameter`, then `actionable`/`snippet`, then `fact`/`problem`/`change`.

Coverage check (R7 inverted): every section must have ≥ 3 facts and ≥ 1 definition; a
section with < 3 facts is a research gap → `hub_concept_queue` it and keep the section under
`## Optional` with a note ("thin: 2 facts, queued for research").

## 5. Choose the link targets

The index needs links, and links need pages. For a topical file the pages are:

1. **The sources themselves** — the canonical URL each fact anchors to. Group by URL: the
   URLs with the most facts in a section are that section's primary links (D2: the description
   names the exact tokens the facts carry).
2. **Hub-served twins** — when a source is a hub docset page, link the served `.md`
   (`http://127.0.0.1:8788/d/<stem>/…` for internal files; the public URL for publishable
   ones). Third-party full text stays internal (P3).
3. **The facts file itself, by anchor** — `llms-facts.txt#<section-slug>` so a reader can
   jump to the claims without opening any page (this is what makes the topical file answer in
   one hop).
4. **Sibling spokes** — the `document-formats/references/*.md` prose for method questions.

Every link: `- [name](url): what you find there, with the exact tokens (D2), 10–25 words`.
Descriptions are extractive: the section's definition unit, or the page's H1 + first sentence.
No link without a description (D1).

## 6. Write the files

```
<topic>.llms/
  llms.txt         H1 = subject; blockquote = what it is + who it is for + verified-as-of;
                   H2 sections from §3, links from §5, ## Shared, ## Optional last
  llms-facts.txt   H1 = subject; H2 per section (same slugs as the index anchors);
                   unit lines from §4, provenance banner, verified-as-of per volatile unit
  llms-full.txt    OPTIONAL: Mintlify-grammar page blocks for hub-owned sources only
  llms-small.txt   OPTIONAL: when full exists; reference-class first, ≤ 50k tokens
  manifest.json    bytes, tokens (chars/4), pages, units, sections, sources, generated, overrides
```

Provenance banner (first lines of facts/full, HTML comment in the index):
`<!-- generated by docset_refine topical v1 · from N sources / M docsets · YYYY-MM-DD · verified-as-of YYYY-MM-DD -->`.

Generator command: the `topical` invocation in §1 writes all of the above; `--no-embed` keeps
assignment keyword-only (no Ollama call) for a quick draft, `--register` stamps `llmsFile` onto
the subject's concept-tree node (§9).

Hand edits (a better section name, a summary) go into `manifest.json.overrides`, not into the
files, so regeneration keeps them (P15).

## 7. Index both ways

```
# vector (facts layer)  — mxbai-embed-large, collection topical__<slug>__facts
PYTHONPATH=scripts .venv/bin/python scripts/docset_indexer.py index <topic>.llms/llms-facts.txt --layer facts --key topical__<slug>
# keyword (FTS5, BM25)  — tables kw_topical__<slug>_facts in docsets.db
PYTHONPATH=scripts .venv/bin/python scripts/docset_indexer.py keyword-index topical__<slug> --layer facts
```

Why both: the vector layer answers paraphrased questions ("how do I stop a big file breaking
Cursor" → the 50k-token constraint); the keyword layer answers exact-token questions
(`X-Markdown-Tokens`, `rel="describedby"`) in microseconds with no embedding call, and it is
the layer that makes a lookup *cheap*. `hub_ask` fuses them with RRF; `hub_query_docset`
exposes each. A fact whose exact tokens are not in `keywords` is invisible to the cheap path
(R4) — §1's normaliser extracts backtick spans, flags, env vars and API names automatically.

Probe it before calling it done:

```
scripts/docset_indexer.py keyword topical__<slug> "describedby"        # must hit the discovery fact
scripts/docset_indexer.py query   topical__<slug> "why split big files" --layer facts
```

## 8. Run `/ldo` and the agent test

```
/ldo ~/.global-ai-hub/llms-topical/llms-txt.llms/llms.txt --agent-test --check-links
```

The run applies every pass; the agent test (P12) is the acceptance bar: 10 bank questions,
≥ 8 answered from the index in ≤ 2 hops and ≥ 7 from the facts file alone. Verdicts persist
to `~/.claude/skill-consolidation/evals/llms/topical__<slug>.eval.jsonl` and replay next run.

## 9. Register and serve

- `llms_serve.py` serves `llms-topical/<slug>.llms/` at `/t/<slug>/…` and lists it on the root
  `/llms.txt` under `## Topics`, with counts (`--base-url /t/<slug>` makes the index links match).
- Add a concept-tree link: `topical --register` stamps `llmsFile: "/t/<slug>/llms.txt"` on the
  subject node (a pointer, not content — the tree stays a tree).
- Add a router row so `hub_route` sends lookup questions here and method questions to the
  skill spoke (`semantic_ops.router build`).
- Optional: publish the index (links + descriptions) to a public host; keep facts/full
  internal when any source is third-party.

## 10. Keep it fresh

- Sources are docsets → the weekly refine regenerates units; re-run `topical` and `/ldo`
  from the pipeline's post-refine hook (P15 catches drift).
- `verified-as-of` older than 90 days on a volatile unit → `/dr --refresh <concept>` queue.
- New tree children → new section candidates; `hub_concept_frontier` lists them.
- Telemetry row per run (`optimizer-telemetry.jsonl`, `kind: llms`, `target: topical`) so
  the trend of probe hit-rate and agent-test score is visible.

## Appendix A — worked example (the llms.txt family)

Pool: 4 `document-formats` spokes (~120 footnoted claims), `llmstxt.org` mirror units,
`developers.cloudflare.com` facts (llms.txt pages only), `llms-text.com` + `gitdoc.ai` blog
mirrors. After §2: ~310 facts, 41 near-dups merged, 3 contradictions kept (adoption %).

Skeleton (§3, from tree children + clusters):
1. Specification and grammar · 2. Discovery and serving (headers, twins) · 3. llms-full and
size ladders · 4. Generating from a site (tooling) · 5. Recreating for third-party sites
(acquisition ladder, rights) · 6. Families and nesting · 7. Evidence: who reads it ·
## Shared (glossary, validators) · ## Optional (history, directories, vendor grades).

Index excerpt:

```
# llms.txt and LLM-readable documentation

> The llms.txt family: the spec, how files are served and discovered, size ladders, generation and
> recreation tooling, family nesting, and the measured evidence on who reads them. For agents and
> pipelines building or consuming these files. verified-as-of 2026-08-30.

## Specification and grammar
- [llms.txt spec v2](https://llmstxt.org/llms.txt): H1 required; blockquote; H2 link lists `- [name](url): notes`; subpath files scope to their path, most-specific wins.
- [Grammars of llms-full.txt](llms-facts.txt#llms-full-and-size-ladders): Mintlify `# Title`/`Source:`, Anthropic YAML blocks, Cloudflare frontmatter + `[View as Markdown]`, Firecrawl delimiters.
…
## Shared
- [Glossary and validators](llms-facts.txt#shared): index/full/small/facts, `.md` twin, describedby; `llms-txt-validator`, `llmstxt-validator` strict rules.
## Optional
- [Directories and vendor grades](llms-facts.txt#optional): llmstxt.site, directory.llmstxt.cloud; vendor support matrix as of 2026-08.
```

Facts excerpt:

```
## Discovery and serving
- [statement] A page advertises its markdown twin with `Link: <page.md>; rel="alternate"; type="text/markdown"` — source: https://llmstxt.org/#discovery · keywords: Link, alternate, text/markdown · verified-as-of: 2026-08-30
- [fact] In the Ahrefs 137k-domain log study, the Claude-Code user agent fetched llms.txt more than every retrieval bot except statespace-indexer and GPTBot — source: https://ahrefs.com/blog/llms-txt-study#results · keywords: Claude-Code, GPTBot, user agent · verified-as-of: 2026-08-30
```

## Appendix B — question bank shape

`~/.claude/skill-consolidation/evals/llms/<key>.eval.jsonl`, one JSON per line:

```
{"q":"What header tells an agent a page has a markdown twin?","expect":"rel=alternate type=text/markdown","section":"discovery-and-serving","kind":"exact-token","hops":1,"verdict":null}
{"q":"Why publish a small variant beside llms-full?","expect":"consumers break above ~50k tokens","section":"llms-full-and-size-ladders","kind":"paraphrase","hops":2,"verdict":null}
```

10 per file minimum, ≥ 4 `exact-token` (they exercise the keyword layer), ≥ 4 `paraphrase`
(vector), ≥ 2 cross-section. Verdicts are written by P12; the bank is replayed and topped up
each run, never rewritten wholesale.

## See also

- `docs/superpowers/specs/2026-08-30-conceptual-llms-txt-family.md` — the concept axis
  (`llms-concepts.txt` per family, concept pages regrouping units, budgeted topic packs) that a
  topical file is one instance of; categorical = the root index with facets, not a file type.
- `scripts/docset_refine/topical.py` — the generator; `tests/test_topical.py` — its contract.
