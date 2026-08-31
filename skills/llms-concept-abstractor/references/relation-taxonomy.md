# Relation taxonomy — what a lexicon term can be to the concept

<!-- llms-concept-abstractor · references/relation-taxonomy.md · 2026-08-31 -->

A lexicon is the recall engine: every term is a claim "units mentioning this are (partly)
about the concept", weighted by how strong that claim is. The relation decides the weight,
whether the term can qualify a unit on its own (**core**), and where its units land.

**Contents** 1. The relations · 2. Weights and the core rule · 3. Finding terms, in trust
order · 4. Expansion rounds · 5. Excludes (polysemy) · 6. Domain heads-up · 7. Worked lexicons

## 1. The relations

| relation | meaning | core | unit relation | heart | indexing (databases) |
|---|---|---|---|---|---|
| `self` | the concept's canonical name | ✓ 1.0 | about | heart | index, indexing |
| `synonym` | same meaning, different word | ✓ 1.0 | about | cardiac (adj.), cor | secondary index |
| `abbreviation` | short form / symbol | ✓ 1.0 | about | HR (heart rate — careful), ECG only if the concept is the heart's electrical activity | idx, IXSCAN |
| `variant` | spelling / inflection / plural the pattern misses | ✓ 1.0 | about | cardio-, cardiac | indexes, indices |
| `hyponym` | a narrower kind / sub-type | ✓ 0.8 | subtype | (heart as organ has few); for "valve": mitral, tricuspid | B-tree index, hashed index, compound index, partial index, TTL index, text index, 2dsphere index, wildcard index |
| `part` | a component of the concept | ✓ 0.8 | component | atrium, ventricle, myocardium, pericardium, septum, mitral valve, SA node, coronary artery | index key, index prefix, index entry, leaf page, index bounds |
| `instance` | a concrete named implementation | ✓ 0.7 | instance | — | `_id` index, `{ status: 1, date: -1 }` |
| `measure` | a metric, unit or reference value tied to it | ✓ 0.7 | measure | heart rate, cardiac output, ejection fraction, stroke volume, bpm | selectivity, cardinality, index size, `totalKeysExamined`, `indexBounds` |
| `problem` | a failure mode, disease, error, limit of it | ✓ 0.7 | problem | arrhythmia, myocardial infarction, heart failure, tachycardia, stenosis | index bloat, unused index, index intersection miss, collection scan (COLLSCAN), write amplification |
| `near-synonym` | similar but distinct — the `not:` differentiator matters | 0.6 | neighbour | cardiovascular (system, not organ), cardiac muscle (tissue) | key, lookup table, materialized view |
| `contrast` | an alternative usually discussed against it | 0.6 | contrast | (for pacemaker cells) skeletal muscle | full scan, sequential scan, `hint()` vs planner |
| `antonym` | opposite meaning | 0.6 | contrast | diastole ↔ systole (each other's antonym) | unindexed, covered ↔ fetch |
| `hypernym` | the broader class it belongs to | 0.4 | context | organ, muscle, cardiovascular system | data structure, access method, query optimization |
| `whole` | the thing it is part of | 0.4 | context | circulatory system, mediastinum | storage engine, query planner |
| `prerequisite` | needed to understand it | 0.4 | prerequisite | cardiac muscle physiology, action potential | B-tree, sorted order, query predicate |
| `dependent` | built on it | 0.4 | dependent | cardiac catheterization, echocardiography | covered query, sort optimization, ESR rule |
| `related` | co-occurs, associated, no tighter fit | 0.4 | related | lung, blood pressure | sharding key, replication lag |

Pick the *tightest* relation. "Cardiac" is a synonym (adjective form), not `related`.
"Arrhythmia" is a `problem`, not a `hyponym`. If a term fits two, the higher-weight one wins.

## 2. Weights and the core rule

A unit's score = Σ weights of the **distinct** lexicon terms it matches (+0.25 if a term is
in its heading path or anchor). Two rules decide inclusion (`harvest`):

- `score ≥ --min-score` (0.6).
- **core rule** (default on): at least one matched term has weight ≥ 0.7, *or* ≥ 2 distinct
  terms matched. A unit that only says "full scan" is about full scans; a unit that says
  "full scan" *and* "selectivity" is about indexing even without the word. Turn off with
  `--no-require-core` when recall matters more (small scope, exploratory round 0).

Override a weight per term (`"weight": 0.9`) when a normally weak relation is decisive in
this corpus — e.g. `related: "hint()"` in MongoDB docs is really about indexing.

## 3. Finding terms, in trust order

1. **The user** — `--aliases`, `--exclude`, the phrasing of the request.
2. **The concept tree** — `hub_concept_lookup(concept)`: parent → `hypernym`, children →
   `hyponym`/`part`, siblings → `contrast`/`near-synonym`; `aliases` → `synonym`.
3. **Earlier packs and topical files** — `llms-concepts/*/concept-graph.json`,
   `llms-topical/*/vocabulary.json` (`aka:` → synonym, `not:` → near-synonym/contrast).
4. **The corpus** — round-0 harvest with the bare name; read the `candidates` list of
   `harvest-report.json` (co-occurrence lift ≥ 2×) and 10–20 `view` lines; the corpus's
   own vocabulary is the highest-recall source and needs no verification.
5. **Semantic neighbours** — `hub_query_docset(docset, "<concept>", mode="semantic", top=20)`
   on an indexed docset; the hits' backtick tokens and heading words are candidates.
6. **Your own knowledge** — roots, abbreviations, identifier conventions. Cheapest to add,
   least trustworthy: every knowledge term must earn ≥ 1 hit by round 1 or be removed (a
   zero-hit term in the final lexicon is allowed only when it is a *reported gap* the user
   should know about, e.g. "the docs never mention `partial index`").

## 4. Expansion rounds

```
round 0: self + user aliases + tree/pack seeds            → harvest → report
round 1: + classified candidates (≥ 2× lift, ≥ 3 uses)    → harvest → report   (usually +40–150 % units)
round 2: + semantic-supplement terms, tightened excludes   → harvest → report   (usually +5–20 %)
stop: a round adds < 5 % new kept units, or --rounds reached
```

Log `kept_units` per round; the growth curve goes in the report. A lexicon that stops growing
while `candidates` still lists strong terms is a sign of a *second concept* in the corpus
(split the pack) or of a synonym family you have not recognised (read the units).

Candidate triage, fast: a candidate is a **part/hyponym** when it appears inside the
concept's own pages (URL contains the slug); a **problem** when it co-occurs with
error/failure cues; a **measure** when it carries numbers/units; a **contrast** when it
appears in comparison cues (vs, unlike, instead of); otherwise `related`. Anything that is a
product/vendor name is an `instance` or an exclude, never a synonym.

## 5. Excludes (polysemy)

`exclude` phrases disqualify a unit before scoring. Add one per foreign sense you can name:
"heart of the matter", "at heart", "learn by heart" · "index finger", "llms.txt index",
"index.html", "index fund", "consumer price index" · "browser cache", "CDN cache". Check
leakage with `view --facet facts --min-score 0.6 --limit 40`: if > 2 of 40 are a foreign sense,
add the exclude and, if the sense shares the exact word, raise `--min-score` to 0.8 so the
bare name alone no longer qualifies.

## 6. Domain heads-up

- **Medicine / biology**: adjective forms and roots carry most mentions (cardi-, myo-,
  -itis, -pathy, -megaly); diseases are `problem`; anatomical sub-structures are `part`;
  measurements have reference ranges → `measure`; textbooks put the concept in chapter
  headings, so heading matches (+0.25) are reliable.
- **Software / databases**: identifiers, flags, env vars, API fields, error strings are exact
  tokens (`--min-score` can be low, matches are precise); vendor-specific names are
  `instance`; CamelCase and snake_case variants go in `aka`; "vs" pages are `contrast` gold.
- **Law / finance**: statute numbers and defined terms are `variant`/`abbreviation`;
  Latin phrases are `synonym`; exceptions and penalties are `problem`.
- **Multi-vendor scopes**: the same concept under different names per vendor (MongoDB
  "compound index" / Postgres "multicolumn index") — both `synonym`, with `note:` naming
  the vendor so the vocabulary file explains the mapping.

## 7. Worked lexicons

```json
{"concept": "Heart", "slug": "heart",
 "terms": [
  {"term": "heart", "relation": "self", "aka": ["hearts"]},
  {"term": "cardiac", "relation": "synonym", "aka": ["cardio", "cardio-"]},
  {"term": "myocardium", "relation": "part", "aka": ["myocardial", "heart muscle"]},
  {"term": "atrium", "relation": "part", "aka": ["atria", "atrial"]},
  {"term": "ventricle", "relation": "part", "aka": ["ventricles", "ventricular"]},
  {"term": "pericardium", "relation": "part", "aka": ["pericardial"]},
  {"term": "mitral valve", "relation": "part", "aka": ["bicuspid valve"]},
  {"term": "sinoatrial node", "relation": "part", "aka": ["SA node", "sinus node", "pacemaker"]},
  {"term": "coronary artery", "relation": "part", "aka": ["coronary arteries", "coronary"]},
  {"term": "cardiac cycle", "relation": "part", "aka": ["systole", "diastole"]},
  {"term": "cardiac output", "relation": "measure", "aka": ["stroke volume", "ejection fraction"]},
  {"term": "heart rate", "relation": "measure", "aka": ["bpm", "pulse rate"]},
  {"term": "arrhythmia", "relation": "problem", "aka": ["tachycardia", "bradycardia", "fibrillation"]},
  {"term": "myocardial infarction", "relation": "problem", "aka": ["heart attack", "MI"]},
  {"term": "heart failure", "relation": "problem", "aka": ["congestive heart failure", "CHF"]},
  {"term": "cardiovascular", "relation": "near-synonym", "note": "the system, not the organ"},
  {"term": "circulatory system", "relation": "whole"},
  {"term": "lung", "relation": "related", "aka": ["pulmonary"], "weight": 0.3}
 ],
 "exclude": ["heart of the matter", "at heart", "by heart", "heartfelt"]}
```

```json
{"concept": "Indexing", "slug": "indexing",
 "terms": [
  {"term": "index", "relation": "self", "aka": ["indexes", "indices", "indexing", "indexed"]},
  {"term": "secondary index", "relation": "synonym"},
  {"term": "B-tree", "relation": "hyponym", "aka": ["btree", "B+tree"]},
  {"term": "compound index", "relation": "hyponym", "aka": ["composite index", "multicolumn index"]},
  {"term": "partial index", "relation": "hyponym", "aka": ["filtered index"]},
  {"term": "unique index", "relation": "hyponym"},
  {"term": "TTL index", "relation": "hyponym"},
  {"term": "text index", "relation": "hyponym", "aka": ["full-text index"]},
  {"term": "hashed index", "relation": "hyponym", "aka": ["hash index"]},
  {"term": "index key", "relation": "part", "aka": ["index prefix", "key pattern"]},
  {"term": "covered query", "relation": "dependent", "aka": ["index-only scan", "covering index"], "weight": 0.8},
  {"term": "selectivity", "relation": "measure", "aka": ["cardinality"]},
  {"term": "IXSCAN", "relation": "abbreviation", "aka": ["index scan"]},
  {"term": "COLLSCAN", "relation": "contrast", "aka": ["collection scan", "full table scan", "sequential scan"]},
  {"term": "explain plan", "relation": "related", "aka": ["explain()", "EXPLAIN ANALYZE", "totalKeysExamined"], "weight": 0.6},
  {"term": "hint", "relation": "related", "aka": ["hint()"], "weight": 0.7},
  {"term": "ESR rule", "relation": "dependent", "aka": ["equality sort range"], "weight": 0.8},
  {"term": "index bloat", "relation": "problem", "aka": ["unused index", "index build", "write amplification"]},
  {"term": "query planner", "relation": "whole", "aka": ["query optimizer"]}
 ],
 "exclude": ["index finger", "llms.txt index", "index.html", "index.md", "index fund", "table of contents"]}
```
