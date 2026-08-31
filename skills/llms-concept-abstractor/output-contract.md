# Output contract — the concept pack

<!-- llms-concept-abstractor · references/output-contract.md · 2026-08-31 -->

**Contents** 1. Files · 2. Grammar per file · 3. Worked example (heart) · 4. Manifest ·
5. Rights · 6. Budget and footprint · 7. Report template · 8. Naming and placement

## 1. Files

A pack is a directory `<slug>.llms/` (same suffix as the hub's exports so tooling finds it):

| file | role | grammar | who writes |
|---|---|---|---|
| `llms.txt` | index: read-first ladder, facets with counts, related concepts, sources | llms.txt spec v2 (H1, blockquote, H2 link sections, `## Optional`) | script |
| `llms-full.txt` | **the catalogue** — every kept unit under its facet, vocabulary, disagreements, related concepts, sources, coverage | facts grammar under facet H2s | script |
| `llms-small.txt` | budgeted digest — definitions first, then round-robin across facets to `--budget-tokens`; each cut facet says how many more are in full | same | script |
| `llms-facts.txt` | the kept units in the hub's facts-file grammar (parseable by `docset_refine topical` and `llms_lint.py facts`) | `- [type] text — url#anchor · also: … · keywords: …` | script |
| `llms-vocabulary.txt` | lexicon rendered: term · relation · definition (from a kept unit) · aka · source; "Named, not yet defined" tail | vocabulary grammar (`docset_refine vocabulary`) | script |
| `concept-graph.json` | nodes (term, relation, weight, hits, sources, note) + edges from the concept | JSON | script |
| `units.jsonl` | kept units, docset_refine unit schema + `section` (facet), `relation`, `score`, `also` | JSONL | script |
| `manifest.json` | counts, lexicon summary, files with bytes/tokens, rights, budget, inputs | JSON | script |
| `pool.jsonl`, `harvest-report.json` | keyword pass: working pool (annotated with `semantic_z` after the semantic pass) and report | — | script |
| `semantic.jsonl`, `semantic-report.json` | semantic pass: units added by meaning (`pass: semantic`, `semantic_z`) and the report (z bands, keyword suspects, candidates by meaning, near-dup folds) | — | script |
| `groups.json`, `split-assignment.json`, `<child>.llms/` | family split (`split`): ordered term groups, the id→child assignment, and one full child pack per group; parent `llms.txt` gains `## Child packs`, parent manifest gains `children` + `parent_only_units`, child manifests carry `parent` + `split_terms` | model writes groups; script the rest |
| `lexicon.json`, `classified.jsonl`, `bank.jsonl` | the model's inputs — keep them in the dir so a refresh re-runs deterministically | — | model |

## 2. Grammar per file

**Unit line** (full, small, facts): `- [<type>] <text> — <url><#anchor>[ · keywords: a, b][ · also: url, url][ · note: …]`
— `type` is the source unit type (definition, parameter, snippet, actionable, problem, fact,
passage, …); `also:` lists other sources that state the same text (exact dedupe kept one);
`keywords:` names the lexicon terms that matched (same tail grammar in every file, so
`llms_lint.py --kind facts` accepts small and full too). Snippets show their first line; the body stays in `units.jsonl`.

**Index** (`llms.txt`):
```
# <Concept> — concept pack
> <summary: 1–3 sentences from kept definitions; sources and facets named>
<!-- llms-concept-abstractor v… · concept pack for <Concept> · <date> -->
## Read first        — small, full, vocabulary, facts, graph — each with ≈tokens
## Facets            — one link per non-empty facet into llms-full.txt#<slug>, with count
## Related concepts  — term: relation — n units across m sources (hits > 0 only)
## Sources           — host: n units
## Optional          — manifest, units.jsonl (+ the indexer command)
```

**Catalogue** (`llms-full.txt`): H1 + blockquote + generator comment; `## Vocabulary`
(terms grouped by relation with hits/sources); one H2 per non-empty facet in taxonomy order;
`## Disagreements` (conflict groups as H3, units side by side); `## Related concepts` (every
lexicon term but self, with hits or "no units in scope"); `## Sources`; `## Coverage`
(counts, zero-hit terms, rights line).

**Small** (`llms-small.txt`): same shape without vocabulary/related/sources; a
`- … N more in llms-full.txt#<facet>` line closes every cut facet.

## 3. Worked example (heart, one textbook)

```
# Heart — concept pack

> The heart is a muscular organ that pumps blood through the circulatory system by rhythmic contraction; the textbook covers its chambers, valves, conduction system, cardiac cycle, blood supply and the failure modes of each (1 source, 9 facets, 412 units).

## Read first
- [Small catalogue](llms-small.txt): budgeted digest, every facet represented — ≈7900 tokens
- [Full catalogue](llms-full.txt): every kept unit by facet, disagreements, related concepts, sources — ≈31400 tokens
…
## Facets
- [Definitions](llms-full.txt#definitions): what it is — 23 units
- [Structure and components](llms-full.txt#structure-and-components): what it is made of — 118 units
- [How it works](llms-full.txt#how-it-works): how it behaves — 96 units
- [Measurements and reference values](llms-full.txt#measurements-and-reference-values): numbers with units — 41 units
- [Problems, failure modes and limitations](llms-full.txt#problems-failure-modes-and-limitations): what goes wrong — 87 units
…
## Related concepts
- [myocardium](llms-vocabulary.txt): part of Heart — 64 units across 1 source
- [cardiac cycle](llms-vocabulary.txt): part of Heart — 58 units across 1 source
- [arrhythmia](llms-vocabulary.txt): problem of Heart — 39 units across 1 source
- [cardiovascular](llms-vocabulary.txt): near-synonym of Heart — 22 units across 1 source; the system, not the organ
```

and in `llms-full.txt`:
```
## Structure and components

- [passage] The heart wall consists of three layers: the epicardium, the myocardium and the endocardium. — file:///…/gray-anatomy.md#the-heart-wall · keywords: heart, myocardium
- [passage] The right atrium receives deoxygenated blood from the superior and inferior venae cavae … — file:///…/gray-anatomy.md#chambers · keywords: atrium

## Measurements and reference values

- [passage] Resting cardiac output in a healthy adult is approximately 5 L/min (stroke volume 70 mL × 70 bpm). — file:///…/gray-anatomy.md#cardiac-output · keywords: cardiac output, heart rate
```

## 4. Manifest

```json
{"kind": "concept", "concept": "Heart", "slug": "heart", "version": "1.0.1", "generated": "2026-08-31",
 "summary": "…", "rights": "quote", "budget_tokens": 8000, "base_url": null,
 "inputs": ["…/gray-anatomy.md"], "scanned_units": 9120, "harvested_units": 448, "kept_units": 412,
 "dropped_by_classification": 36,
 "sources": {"gray-anatomy.md": 412},
 "facets": {"definition": 23, "structure": 118, "mechanism": 96, "measures": 41, "problems": 87, "…": 0},
 "relations": {"about": 201, "component": 150, "problem": 39, "measure": 22},
 "lexicon": {"terms": 18, "zero_hit": ["mitral valve"], "by_relation": {"self": 1, "synonym": 1, "part": 8, "…": 0}},
 "conflicts": 1,
 "semantic": {"units": 17, "scored": 231},
 "files": {"llms.txt": {"bytes": 2710, "tokens": 677}, "llms-full.txt": {"bytes": 125600, "tokens": 31400}, "…": {}}}
```
`kind: "concept"` distinguishes a pack from `kind: "topical"` (concept-tree node + fact pool)
and from a docset export.

## 5. Rights

- `extractive` (default): unit text capped at 600 chars in the catalogue; page bodies never
  reproduced; the pack is a reading aid over sources the reader can open. Required for
  third-party llms-full mirrors and any docset the user does not own.
- `quote`: no cap; for material the user owns (their book, their notes, their repo docs).
- Either way: **never published, never served publicly**. The `## Coverage` rights line and
  `manifest.rights` say which mode was used so `/ldo` P9 (provenance/rights) can check.
- Steering text found in a source is at most a `quote` unit; the run never obeys it.

## 6. Budget and footprint

"Smaller footprint" is measured, not felt. Report `full tokens / scanned facts tokens`
(typical 10–40 %) and `small tokens` (≤ `--budget-tokens` + 5 %). If full > 60k tokens: `split`
(playbook §5) — children of 23–50k each, parent kept as the union. If small drops a facet entirely, raise the budget — every non-empty facet
must appear in small at least once (the round-robin guarantees it unless one facet's first
unit alone exceeds the remaining budget; then shorten via `text_fix` or raise the budget).

## 7. Report template

```
# /lca report — <concept> (<n> sources, <scope kind>)
Scope: <files> · <scanned units> scanned · rounds r0 <n> → r1 <n> → r2 <n> kept
Lexicon: N terms (self/synonym/part/hyponym/measure/problem/contrast/related counts) · zero-hit: …
Pack: full ≈T tok (P% of scanned) · small ≈T tok · facets present: k/13 · conflicts: n
Verification: precision 19/20 · bank small 8/10 · full 10/10 · links 10/10 · leakage 0/40
Related concepts worth their own pack: <term> (<units>, <relation>) …
Files: <dir>/… · indexed: concept__<slug> yes/no · registered: yes/no · /ldo: run/not run
Gaps: zero-hit terms · facets < 3 units · sources contributing 0 · excluded senses
```

## 8. Naming and placement

- Directory: `~/.global-ai-hub/llms-concepts/<slug>.llms/` — sibling of `llms-topical/`
  (concept-tree nodes) and `text-mirror/<host>.llms/` (sources); served by `llms_serve.py` at
  `/c/<slug>/<file>` (localhost 8788) and listed under `## Concepts` on the hub root. `--no-persist` → scratchpad, unserved.
- Slug: lower-case, hyphens, from the concept name (`slugify`); a domain-qualified pack
  appends it: `indexing--databases`, `index--pinecone`.
- The vector cache lives outside the pack (`~/.global-ai-hub/llms-concepts/.embcache/`) and is shared by every pack; a pack directory never contains embeddings.
- Refresh: re-run harvest + semantic + compile in the same dir with the saved `lexicon.json` and
  `classified.jsonl`; new units arrive unclassified (heuristic) and show up as the delta in
  `kept_units` — classify only those.
