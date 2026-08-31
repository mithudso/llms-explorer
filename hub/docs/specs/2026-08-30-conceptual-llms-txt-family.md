# Conceptual llms.txt — topical repositories, not a site's docs

**Date:** 2026-08-30 · **Status:** exploration → pilot shipped (see §8) · **Builds on:**
`2026-08-30-llms-txt-as-docset-schema-design.md` (index / small / full / facts per product, nested
family indexes) and the llms-full mirror (`llms-full/`, 766 sites, 145 real docsets).

## 0. The axis we are missing

Every llms.txt-shaped file we have is organized **by source**: the H2 sections are a site's URL tree,
the links are its pages, the facts are anchored to its pages. That answers *"what does this site say?"*

A topical repository answers *"what is known about X, across sources?"* — the organizing axis is a
**concept**, and a source is just where a claim was found. Same grammar, orthogonal axis:

| axis | index | corpus | atoms |
|---|---|---|---|
| **source** (have) | `llms.txt` — nav of one site | `llms-full.txt` | `llms-facts.txt` — units anchored to pages |
| **concept** (proposed) | `llms-concepts.txt` — nav of a concept tree | `topic pack` — a concept's reading set across sources (view, not file) | the same units, **re-keyed by concept** |
| **category** | the hub root `/llms.txt` with faceted H2s | — | — |

"Categorical" and "conceptual" are not two more rungs on the size ladder; they are the second axis. The
size ladder (small / full) still applies *within* a concept.

## 1. Categorical — already almost there, keep it a view

A category is a **bin for sources**: "developer tools", "ai ml", "infrastructure cloud" (the
llms-txt-hub categories the catalog already carries), or our own families (concept-tree roots, skill
hubs). Categorical navigation = *which docsets should I open?*

That is exactly the spec-v2 nested index the design doc already plans as `docset_refine hub` →
`/llms.txt`. Two additions make it properly categorical:

- **Facets, not a tree.** A product belongs to several categories; the spec allows the same link under
  several H2s, so emit it under each. No new file.
- **Counts on every line** (pages, tokens, facts, `updated`) so an agent budgets before fetching —
  llmstxt.site's most useful column, and our `manifest.json` already has the numbers.

```
# Global AI Hub — docsets
> 145 documentation sets mirrored locally, 37 refined. One line per docset, repeated under every
> category it belongs to. Counts are pages / approx tokens / facts.

## Developer tools
- [Claude Code](/llms/code.claude.com/llms.txt): agentic coding CLI — 191p / 2.1M tok / 11,965 facts
- [Medusa](/llms/docs.medusajs.com/llms.txt): commerce framework — 688p / 1.6M tok / —

## AI / ML
- [Claude Code](/llms/code.claude.com/llms.txt): … (same line, second facet)
- [Pydantic AI](/llms/ai.pydantic.dev/llms.txt): …

## Families (concept tree)
- [llms.txt and LLM-readable documentation](/concepts/llms-txt/llms-concepts.txt): 5 concepts researched, 3 frontier
```

Verdict: **categorical = the root index with facets.** Not a separate file type.

## 2. Conceptual — the new file: `llms-concepts.txt`

A concept is a **node of meaning**, not a bin: "connection pooling", "prompt caching", "structured
sentencing". Conceptual navigation = *what should I read, across every source, to understand X?*

We already own the two halves: `concept-tree/tree.json` (37 nodes: concept, parent, children,
skillId, researchedAt, sourcesCount) and the per-docset fact layers (`<key>__facts`: 12 unit types ×
5 origins, every unit source-anchored). Nothing joins them today except `hub_ask` at query time.

`llms-concepts.txt` is the concept tree rendered in llms.txt grammar, one per family, so **every
existing llms.txt parser reads it unchanged** (`llms_txt2ctx`, LangChain `mcpdoc`, our own reader):

```
# llms.txt and LLM-readable documentation — concepts
> A concept map of this family. Each line is one concept with its definition and a link to its
> concept page (definition, facts from every source, skills, siblings). Concepts with no page are
> known but unresearched (frontier). Parent → child follows the H2 → bullet nesting.

## llms.txt and LLM-readable documentation
- [llms.txt spec v2](/concepts/llms-txt-spec-v2.md): the curated-index proposal — H1, blockquote, H2 link sections, Optional tail. 5 sources / 41 facts / skill document-formats
- [llms-full.txt grammars](/concepts/llms-full-grammars.md): Mintlify, Anthropic YAML, Cloudflare frontmatter; not in the spec. 4 sources / 22 facts
- [Discovery and consumers](/concepts/llms-txt-consumers.md): who fetches it — Claude-Code UA dominates; Cursor/Copilot do not. 6 sources / 19 facts

### llms-full.txt grammars
- [.md twins](/concepts/md-twins.md): page.md / Accept: text/markdown. 3 sources / 9 facts
- [Producer-side splitting](/concepts/producer-side-splitting.md): small/full ladders, token headers. 3 sources / 12 facts

## Frontier
- Content Signals in robots.txt — known, unresearched (childConcepts with no node; RESEARCH_QUEUE.md)
- ai.txt opt-out draft — known, unresearched

## Optional
- [Full family corpus](/llms/document-formats/llms-full.txt): every page of every source, 4.2M tok
```

Design choices, each pinned to a real constraint:

- **Grammar = spec v2, plus H3 for depth.** The spec defines H2 sections only; H3 is a harmless
  extension (parsers that ignore it still see a flat list). Two levels is what a consumer can hold; the
  tree's deeper nesting lives in the concept pages.
- **Description = definition unit.** The extractive `definition` unit is the same thing the product index
  uses; the LLM pass polishes only when it is missing or short (the design doc's rule 1). Counts
  (`N sources / M facts / skill …`) travel on every line — the concept-tree node already has
  `sourcesCount` and `conceptsCount`.
- **Frontier is a section, not silence.** A concept with children but no node is the research queue;
  rendering it under `## Frontier` makes "known but unresearched" visible to a consumer — today only
  `hub_concept_frontier` knows.
- **Many parents.** Trees are one-parent; concepts are not (prompt caching sits under both "Claude API"
  and "inference cost"). The spec permits a link under several sections — repeat it, the same way the
  categorical root repeats a product.

## 3. The concept page — where cross-source synthesis lives

`/concepts/<slug>.md` is the conceptual twin of a product page. Its body is generated, not written:

```
# Connection pooling
> Reusing open DB connections instead of a handshake per request. Definition from postgresql docs;
> 3 other sources agree.

## Definitions
- Pool reuse open DB connections… — https://www.postgresql.org/docs/…#pooling
- (mongodb) A connection pool is a cache of open, ready-to-use… — https://www.mongodb.com/docs/…#pool

## Parameters
- [parameter] maxPoolSize (default 100) — mongodb …
- [parameter] pool_size / max_overflow — sqlalchemy …

## How-to (actionable)
- [actionable] Set PgBouncer to transaction mode for serverless… — pgbouncer …

## Problems
- [problem] pool exhaustion under N+1 … — mongodb …

## Related
- parent: Database connectivity · siblings: Read/write splitting, SDAM · skill: mongodb-connection
## Sources
- mongodb.com/docs (14 facts) · postgresql.org (9) · pgbouncer.org (6) · sqlalchemy (4)
```

The section order **is the unit-type taxonomy** (`definition`, `parameter`, `snippet`, `actionable`,
`problem`, `question`, `change`, …). That is the payoff of having typed units: a "troubleshooting view"
of a concept is `## Problems` + `## How-to`; a "reference view" is `## Definitions` + `## Parameters`.
No new extraction — a regrouping.

The hard part is **assigning units to concepts**. Three passes, cheapest first:

1. *keyword* — the concept name / synonyms appear in the unit text or its heading path (free, precise,
   low recall);
2. *embedding* — nearest concept node above a threshold, using the `<key>__facts` vectors that already
   exist (the `mxbai-embed-large` pool; same model as `semantic_ops`);
3. *LLM* — only for units whose top-2 concepts are within ε of each other, on the local model
   (`qwen3.5:35b`, batched like `units`).

Dedup across sources with the existing `units.dedup` embedding pass, but **keep the source list** — "3
sources agree" is information; a single merged line loses it.

## 4. Topic packs — the corpus rung, as a view

A concept's `llms-full` equivalent would be *every page from every source that grounds the concept*.
Storing that per concept duplicates the corpus 37 times and republishes third-party text (the rights
line in the design doc). So it is **a view, budgeted at request time**:

```
hub_concept_pack(concept, budget_tokens=50000, kinds="definition,parameter,actionable")
  → the concept page, then whole source pages in facts-density order until the budget is spent,
    each page in Mintlify grammar (# Title / Source:) so the pack is itself a valid llms-full.txt
```

Producer-side splitting, applied to a concept instead of a site: the consumer names the budget (the
Cursor-stability ceiling ~50k is a sane default) and gets a file it can read in one go. Served by
`llms_serve.py` at `/concepts/<slug>/llms-full.txt?tokens=50000`, cached per (concept, budget).

## 5. How it is used — the consumer flows

| Flow | Today | With the conceptual layer |
|---|---|---|
| **Orientation** ("where do I start on X?") | `hub_concept_lookup` → skill id + tree neighbours | read `/llms.txt` (categorical) → family `llms-concepts.txt` → concept page. Two hops, all plain markdown, any agent — not only ours |
| **Retrieval** ("what is known about X?") | `hub_ask` — RRF over corpora, LLM answer | concept page first (pre-joined, typed, source-listed), `hub_ask` for what it lacks. Cheaper, and the answer cites sources by construction |
| **Reading pack** ("load me up on X") | open N docsets by hand | `hub_concept_pack(X, budget)` → one valid llms-full.txt sized to the window |
| **Gap finding** | `hub_concept_frontier` | `## Frontier` in every family file; a concept page with `Sources: 1` is a thin-evidence flag |
| **Skill building** (`/dr`) | web research → `references/*.md` | a skill's `references/` *is* a topical repository already; emit `llms-concepts.txt` from the skill hub + `SKILL.md` as its blockquote, and the skill tree and the concept tree become one navigable surface |
| **Cross-source checking** | none | two definitions under one concept that disagree = a `## Contradictions` section (dedup pass finds near-duplicates; the ones that are *not* duplicates but share a subject are the interesting ones) |

The agents that matter are the ones we point at a file (the Ahrefs log finding: `Claude-Code` fetches
when directed, nobody discovers). So the surface is for **our** agents: MCP tools return the URL of
the concept page or pack, and Claude Code / subagents read it like any docs URL.

## 6. What to build, in order — and what not to

1. **`docset_refine concepts <family>`** → `llms-concepts.txt` + `/concepts/<slug>.md` from
   `tree.json` + the family's `<key>__facts` collections (keyword + embedding assignment; LLM pass
   opt-in). Serve under `llms_serve.py`. This is the only new artifact.
2. **Facets + counts on the hub root** (`docset_refine hub`) — the categorical layer, no new file.
3. **`hub_concept_pack`** MCP tool — the topic-corpus view, cached, budgeted.
4. Later: `## Contradictions`, skill-hub emission, family-level merged facts.

Not worth building: a stored `llms-categories.txt` (it is the root index), stored per-concept
`llms-full.txt` (duplication + rights), a new unit-extraction pass (regroup the 12 types we have).

## 7. Open questions

- Concept **identity**: the tree keys nodes by display name; a slug + aliases field is needed before
  URLs can be stable (`/concepts/<slug>.md`). Adding `aliases` to tree.json nodes is cheap now.
- Assignment **threshold**: what cosine floor keeps precision? Pilot on the "llms.txt" family, where
  the facts (11,965 from code.claude.com + the 4 references) and the 8-node tree are both fresh.
- Whether `## Frontier` should also list *derived* frontier — concepts that many units mention but no
  node names (the `cluster` primitive can propose them; `tree_maint propose` already does something
  close).

## 8. Pilot (shipped 2026-08-31)

`docset_refine topical` implements §2–§4's first rung as the `llms-deep-optimizer` how-to's
planned surface (`facts-to-llms-howto.md` §1–§9): the topical dir's `llms.txt` **is** the
`llms-concepts.txt` of §2 (H2 = the subject's child concepts, `## Optional` carries frontier and
thin sections), `llms-facts.txt` sections **are** the concept pages of §3 (typed units per concept,
`also:` for corroborating sources), served at `/t/<slug>/` with the root's `## Topics`.

Pilot on "llms.txt and LLM-readable documentation" from the 4 `document-formats` spokes:
140 facts / 76 sources (7 rejected: dangling footnotes), sections 26 / 20 / 47 / 42 / 2 (the last
thin → `## Optional`), shared 3; types statement 117, problem 10, actionable 7, definition 6.
What the pilot taught:

- **Table rows are facts.** The spokes carry most claims in tables; the first run skipped them
  (76 facts). Each row is one claim (`cell — cell — cell`) anchored to its footnote.
- **The spoke is the strongest assignment signal.** A `/dr` reference is written for one concept;
  matching the pool file's stem to the section slug/alias (`FILE_PRIOR`) fixed the skew (evidence
  1 → 42) before embeddings were needed. Keyword overlap alone fails when every section name shares
  the subject's tokens ("llms.txt").
- **Markdown residue is noise.** Bold markers and blockquote prefixes leak from prose into
  descriptions; stripped at record time (`_clean_md`), backticks kept (they are keywords).
- Not yet: near-dedupe (embedding), LLM pass on low-margin assignments, `## Contradictions`,
  `hub_concept_pack`, keyword (FTS5) indexing of the facts file — the how-to's §7 — and `/ldo` as
  the acceptance gate.

## 9. `/ldo` run on the pilot (2026-08-30) — what the acceptance gate found

Run: 5 iterations, all fixes in the generator (P15 parity byte-identical each time), pre-write
snapshot + per-iteration copies in `~/.claude/skill-consolidation/backups/topical__llms-txt-20260830-230349/`.
Exit **BLIND-AUDIT-DISSENT**: both blind audits corroborated Medium+ findings; the second ran on
iteration 4 and its residuals below are unverified by a third audit (the gate runs at most twice).

Scores: index P12 10/10 → 9/10 (the one partial is a source gap — no spoke states *why*
extractive descriptions beat generated ones); facts P12 8/10 → 9/10; P11 keyword 10/10 every
iteration; P13 200 / markdown / `describedby` / `X-Markdown-Tokens`; deterministic passes 0 High
0 Medium from iteration 1 on. Final: 168 units / 79 sources, index 6.1 KB, facts 74 KB.

What the loop fixed in the generator (each a real defect a reader hit): relative facts links
(P2 High); table rows as labelled claims with escaped/in-backtick pipes respected; lead-in
sentences whose bullets inherit the footnote; the list-marker strip eating leading digits
(`10–50` → `–50`); composite footnotes (`[^7]: a and b`) keeping every URL, host-named URL
first within the citing footnote only; `also:` deduped and uncapped; ≤2-sentence / ≤400-char
units with quote-, backtick- and bracket-aware sentence splitting and pronoun-led sentences
glued to their antecedent; `### <source heading>` groups (unnumbered) inside sections; fuzzy
spoke↔section matching (recreation 2 → 40 facts); extractive I2 blockquote (what the subject
is, who the index is for); `section_order` override; link titles from the URL path; 25-word
descriptions cut at sentence/clause boundaries with balanced brackets/quotes; **D5 rule** — a
link's description must come from a unit that names the target vendor (or no other vendor),
else the link is dropped (35 → 27 index lines); `verified-as-of` per unit; a `units.jsonl`
sidecar so the vector + FTS5 layers index exactly what is served.

Residuals (audit #2, on iteration 4; iteration 5 addressed the D5 index cases mechanically
but is unaudited): ~8% of units are cross-vendor synthesis sentences anchored to the
first-cited host — a sentence like "Cloudflare … ; Mintlify … ; Fern …" cites one footnote and
cannot be split per vendor without a model; hub-authored observations ("Live probe
2026-08-30 …") anchored to the spec URL because the spoke cites `[^1]` there; pronouns whose
antecedent is the previous sentence ("Vercel proposed it"); duplicate claims restated across the
four spokes below the 0.93 near-dedupe threshold. All are the LLM re-anchoring / claim-splitting
pass the how-to plans, not deterministic fixes. Also for the `/ldo` skill owner:
`llms_lint.py`'s `UNIT_RE` does not accept the how-to's `· also:` field (the generator now
orders tails `keywords → verified-as-of → also` to pass it), and `test_script_help` fails on
`llms_lint.py`'s missing Usage section.

## 10. The lexical layer — `llms-vocabulary.txt` (built 2026-08-31)

A third layer beside the two axes: one line per term of the niche — canonical name, definition,
`aka:` (synonyms), `not:` (contrasts), `differs:` (the clause that separates them), source URL.
Neither index nor facts; it is what makes both findable. `docset_refine vocabulary --from … --subject
… --out <topical dir> [--llm [--floor F]] [--register]` → `llms-vocabulary.txt` + `vocabulary.json`,
served at `/t/<slug>/llms-vocabulary.txt`.

Sources, in trust order: (1) tree node names + aliases; (2) backtick tokens used ≥ 2× in the pool,
clustered by spelling (`LLMs-Full.txt` / `llms full txt` → one term, most frequent surface
canonical, the rest `aka:`), markdown-syntax examples filtered; (3) `definition` units and
"X is/are …" sentences → definitions, contrast cues (not / unlike / vs / rather than) → `not:`,
"(also called X)" → `aka:` only when it follows the term itself; (4) `--llm`: the local model
writes a missing definition/differentiator from ≤ 6 evidence units, kept only when its content
tokens are **grounded** in that evidence (`--floor`, default 0.6) and every contrast/alias name
literally occurs there; model-proposed aliases additionally need an alias cue next to them.

Pilot on the llms.txt family (45 terms from 168 units):

| grounding floor | defined | of which model | wrong on spot-check | `aka:` | aliases registered |
|---|---|---|---|---|---|
| deterministic only | 1 | 0 | 0 | 15 (spelling variants) | — |
| 0.6 (default) | 7 | 6 | 0 | 3 | 0 |
| 0.45 | 21 | 20 | 1 ("llms.txt is a file used to describe language models") | 3 | 0 |
| ungrounded (first run) | 38 | 37 | several; "Documentation Index" registered as an alias of the subject | 15 | 2 |

Served file: floor 0.45 with the grounding score on every model line (`origin: llm (grounded
0.48, verify before citing)`), so the reader sees the confidence instead of a clean-looking guess.

**Measured effect on assignment: none.** With grounding enforced no `aka:` survives the cue test,
so `--register` adds no aliases and the topical re-run is identical (keyword 30 · file-prior 122 ·
embed 9 · shared 7, before and after). The ungrounded first run did register aliases — and one
of them (`llms-full.txt` on the grammars node) fuzzy-matched the `llms-txt` spoke and moved all
21 spec facts into the wrong section. Two conclusions: (a) aliases are load-bearing for
assignment, so they must come from evidence, not paraphrase, and the spoke match now uses the
node slug only (aliases match a spoke stem exactly or not at all); (b) this pool is *about*
llms.txt, not a glossary of it — 38 of 45 terms are "named, not yet defined", which is the
research queue for a dedicated `/dr` glossary pass or a hand-written `llms-vocabulary.txt` that
the builder then treats as source #0. The feedback loop the design promised (vocabulary →
aliases → better assignment) is wired and safe; it needs a richer vocabulary source to pay off.

