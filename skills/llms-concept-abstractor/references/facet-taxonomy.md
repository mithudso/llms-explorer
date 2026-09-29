# Facet taxonomy — how a concept pack is sectioned

<!-- llms-concept-abstractor · references/facet-taxonomy.md · 2026-08-31 -->

A facet is *what kind of thing* a unit says about the concept. The facet order is the section
order of `llms-full.txt`, `llms-small.txt` and `llms-facts.txt`, chosen so a reader who stops
early has the most load-bearing material: what it is → what it is made of → how it works →
how to set it → how to do things → examples → numbers → what goes wrong → alternatives →
history → open questions → the rest.

**Contents** 1. The facets · 2. Unit type → facet · 3. Per-domain readings · 4. Classification
rules for the model · 5. The conflict rule · 6. `classified.jsonl`

## 1. The facets

| facet key | section title | holds |
|---|---|---|
| `definition` | Definitions | sentences that say what the concept (or a part/sub-type) *is*; "X is a …", "X refers to …" |
| `structure` | Structure and components | what it consists of, its parts, layers, fields, anatomy, architecture |
| `mechanism` | How it works | behaviour, sequence, cause → effect, algorithm, physiology, lifecycle |
| `parameters` | Parameters and configuration | settings, options, fields, defaults, limits, flags, dosages, reference specs |
| `how-to` | How-to and procedures | steps, recommendations, "to do X, …", best practices, clinical procedures |
| `examples` | Examples and snippets | code, commands, worked examples, sample requests/responses, case studies |
| `measures` | Measurements and reference values | numbers with units, normal ranges, benchmarks, prices, sizes |
| `problems` | Problems, failure modes and limitations | errors, limits, risks, diseases, anti-patterns, deprecations, caveats |
| `comparisons` | Comparisons and alternatives | X vs Y, when to prefer, trade-offs, differences from a near-synonym |
| `history` | Changes and history | version changes, release notes, discovery/history, deprecations by date |
| `questions` | Open questions | questions the sources raise and do not answer |
| `facts` | Facts and statements | true-of-the-concept claims that fit no facet above; the default bucket |
| `quotes` | Quotes | verbatim passages worth keeping as-is (attributed) |

## 2. Unit type → facet (heuristic defaults in the script)

| unit type (docset_refine / distiller) | facet |
|---|---|
| `definition` | `definition` only if the text is a definitional sentence; otherwise the cue chain (extractor `definition` units are "Heading — first paragraph", often not definitions) |
| `parameter` | `parameters` |
| `snippet`, `example` | `examples` |
| `table` | `measures` |
| `actionable`, `step` | `how-to` |
| `problem` | `problems` |
| `question` | `questions` |
| `change` | `history` |
| `quote` | `quotes` |
| `comparison` | `comparisons` |
| `concept`, `fact`, `statement`, `idea`, `passage` | cue chain: comparisons → problems → how-to → structure → measures → mechanism → definition → `facts` |

The cue chain is deliberately coarse; it exists so `--no-llm` packs are usable, not so the
model can skip Step 5.

## 3. Per-domain readings

| facet | medicine / biology | software / databases | law / policy |
|---|---|---|---|
| structure | anatomy, histology, layers | architecture, components, schema, fields | elements of an offence, clauses |
| mechanism | physiology, pathophysiology, cycle | algorithm, protocol, request lifecycle | procedure, how a rule operates |
| parameters | dosages, normal values, staging criteria | config keys, defaults, limits, API fields | thresholds, deadlines, amounts |
| how-to | clinical procedure, examination technique | setup, migration, tuning steps | filing steps, compliance steps |
| measures | reference ranges, prevalence, mortality | benchmarks, sizes, prices, latencies | penalties, fees, statutory numbers |
| problems | diseases, complications, contraindications | errors, anti-patterns, limits, deprecations | exceptions, penalties, pitfalls |
| comparisons | differential diagnosis, X vs Y tissue | X vs Y feature, when to prefer | jurisdiction differences |

## 4. Classification rules for the model (Step 5)

- Read `view` output; change only what is wrong. Untouched units keep the heuristic — that is
  by design, so a 10 % sample plus the targeted buckets is a complete pass.
- **Targeted buckets, in order**: `score < 1.0` (keep/drop), `facts` (re-facet), `comparisons`
  + `problems` (about the concept or about the contrast term? — a unit about *full scans* that
  never touches indexing gets `keep: false`), `definition` (is it a definition or a section
  lede?), then the sample.
- A unit about a **part** or **sub-type** is kept with `relation: component|subtype` — the pack
  is the concept *and its neighbourhood*; the relation column keeps them separable.
- A unit about a **contrast** term alone is dropped unless it states the difference from the
  concept (then `comparisons`, `relation: contrast`).
- Multi-facet units: pick the facet a reader would look under first; do not duplicate.
- Never rewrite text. `text_fix` exists to trim a long quote to the relevant sentence, and
  the trimmed text must be a contiguous substring of the original.
- `note:` is for reader-facing disambiguation ("MongoDB sense", "pre-8.0 behaviour"), ≤ 12
  words, written from the unit's own page context.
- When a unit is about a *different* concept that shares the name (Pinecone "index" in an
  indexing pack about databases), drop it and, if it recurs, propose an exclude or a second pack.

## 5. The conflict rule

Two kept units **conflict** when they make incompatible claims about the same referent:
same parameter/default, same measurement, same definition, same recommendation — and the
difference is not explained by version, vendor, or edition stated in the units or their
page. Conflicts get the same `conflict: "c<n>"` id and render side by side under
`## Disagreements` with their sources; neither is dropped or "corrected". Version-qualified
or vendor-qualified differences are **not** conflicts — they are `note:` material
("MongoDB default 64 MB; Postgres 8 kB page"). Report the count; a pack with unresolved
conflicts is still a good pack — it tells the reader where the sources disagree.

## 6. `classified.jsonl`

```jsonl
{"id": "s01u003548", "facet": "how-to"}
{"id": "s01u000921", "facet": "problems", "relation": "about", "note": "batch mode caveat"}
{"id": "s03u003385", "keep": false}
{"id": "s01u003545", "conflict": "c1"}
{"id": "s03u003390", "conflict": "c1", "note": "OpenRouter states 10-minute TTL"}
{"id": "s01u004663", "text_fix": "Place `cache_control: {\"type\": \"ephemeral\"}` on the last tool in your `tools` array."}
```

Fields: `id` (required) · `keep` (default true) · `facet` (one of §1) · `relation` (about,
component, subtype, instance, measure, problem, neighbour, contrast, prerequisite,
dependent, context, related) · `conflict` · `note` · `text_fix`. Unknown fields are ignored.
