# 06 — Concept Abstraction (`/lca` as a service)

**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | api | cli | mcp

## 1. Purpose

Abstract ONE concept out of any scope and compile everything the scope says about it — and about its neighbourhood — into a **concept pack**: a small-footprint, source-anchored, facet-grouped llms family that a reader loads instead of the sources. The skill exists (`~/.claude/skills/llms-concept-abstractor/`, alias `/lca`; copied under `skills/` on refresh); the site runs it as a job with a UI for the three human decisions it needs (lexicon approval, borderline classification review, publish target).

Canonical examples the product carries: **heart** out of a medical textbook; **indexing** across every database docset; **prompt caching** across three API docs.

## 2. User stories and flows

- *Student*: uploads a converted anatomy textbook, types "heart", approves a lexicon of 40 terms (atrium, ventricle, myocardium, systole ↔ diastole, …), gets a 30-page pack instead of a 900-page book, with every line pointing at its page.
- *DBA*: picks six database docsets from the public catalogue, types "indexing"; the harvest report shows "B-tree index" 212 hits across 5 sources, "covered query" 31; the Disagreements section shows MongoDB and Postgres defining "covered" differently, side by side.
- *API integrator*: three vendor docs, "prompt caching"; wants the `llms-small.txt` under 8k tokens for a system prompt.
- *Tree curator*: publishes the pack to the concept-tree node (09) so the node's Artifacts tab carries it and `hub_concept_lookup` returns it.

Flow: **Scope** (own docsets, catalogue entries, upload, "whole estate") → **Concept** (name + optional seed synonyms/excludes) → **Lexicon proposal** (script harvest + model expansion; user edits relations/weights, adds excludes for polysemy) → **Harvest** (keyword pass + semantic pass, zero model tokens) → **Report** (hits per term, z-score bands, keyword suspects) → **Classify + verify** (model on borderline units only) → **Pack** (facet tabs, graph, disagreements) → **Lint** (01) → **Publish** (to `/u/…`, to a tree node, to the shared catalogue).

## 3. Inputs → outputs (contracts and file grammars)

Input: `concept` (canonical name), `scope` (list of docset keys / catalogue keys / upload ids / `estate`), options: `--budget-tokens` for small, seed `synonyms`, `excludes`, `facets` subset.

Output — the pack directory `<slug>.llms/`, per the skill's `references/output-contract.md`:

| file | role |
|---|---|
| `llms.txt` | index: `## Read first` (small, full, vocabulary, facts, graph with ≈tokens) · `## Facets` (one link per non-empty facet into `llms-full.txt#<slug>` with counts) · `## Related concepts` (term: relation — n units across m sources) · `## Sources` · `## Optional` (manifest, units.jsonl, indexer command) |
| `llms-full.txt` | the catalogue: `## Vocabulary`, one H2 per facet in taxonomy order, `## Disagreements`, `## Related concepts`, `## Sources`, `## Coverage` |
| `llms-small.txt` | budgeted digest: definitions first, round-robin across facets to `--budget-tokens`; every cut facet ends with `- … N more in llms-full.txt#<facet>` |
| `llms-facts.txt` | kept units, hub facts grammar: `- [<type>] <text> — <url><#anchor>[ · keywords: a, b][ · also: url, url][ · note: …]` |
| `llms-vocabulary.txt` | term · relation · definition (from a kept unit) · aka · source; "Named, not yet defined" tail |
| `concept-graph.json` | nodes (term, relation, weight, hits, sources, note) + edges from the concept |
| `units.jsonl`, `manifest.json` | kept units with `section` (facet), `relation`, `score`, `also`; counts, lexicon summary, files bytes/tokens, rights, budget, inputs |
| `pool.jsonl`, `harvest-report.json`, `semantic.jsonl`, `semantic-report.json` | harvest working state (annotated `semantic_z`, z bands, keyword suspects) |
| `lexicon.json`, `classified.jsonl`, `bank.jsonl` | the model's inputs, kept so a refresh re-runs deterministically |

Facets (`references/facet-taxonomy.md`): definition, structure, mechanism, parameters, how-to, examples, measures, problems, comparisons, history, questions, facts, quotes. Relations (`references/relation-taxonomy.md`) with weights: self/synonym/abbreviation/variant 1.0 (core), hyponym/part 0.8, instance/measure/problem 0.7, near-synonym/contrast/antonym 0.6, hypernym/whole/prerequisite 0.4.

## 4. Architecture (mermaid diagram + existing hub code reused, by path)

```mermaid
flowchart LR
  S[scope: docsets / catalogue / upload] --> H[harvest: keyword pass (stdlib)]
  S --> SEM[semantic pass: ollama embeddings of scope, centred z, cached]
  LX[lexicon: script seed → model expansion → user edit] --> H
  LX --> SEM
  H --> POOL[(pool.jsonl + harvest-report)]
  SEM --> POOL
  POOL --> CL[model: classify borderline, verify]
  CL --> PACK[pack writer: index/full/small/facts/vocabulary/graph]
  PACK --> LINT[01] --> PUB[09 node · 13 catalogue · /u/…]
  PACK --> G3[3D graph view (09 renderer)]
```

Reused: the skill's `scripts/` (harvest, semantic pass, pack writer), `hub/scripts/docset_indexer.py` (`dump` gives scope text for docsets that exist only in the store), `hub/scripts/llms_full_catalog.py` (`read_entry` for catalogue scopes), `hub/scripts/docset_refine/vocabulary.py` grammar, `hub/scripts/embed_core.py` pool (`mxbai-embed-large`), `hub/scripts/llms_lint.py`, the json-3d-renderer for `concept-graph.json`. The model steps run the skill through the Agent SDK with the pack dir as the working state.

## 5. API / CLI / MCP surface

```
POST /api/abstract/lexicon     {concept, scope[], seeds?, excludes?} → proposed lexicon [{term, relation, weight, evidence}]  (metered: model expansion)
POST /api/abstract/harvest     {concept, scope[], lexicon} → {job_id}   (embeddings metered, no model tokens)
GET  /api/abstract/{job}/report        harvest-report + semantic-report
POST /api/abstract/{job}/classify      {overrides?} → runs classify + verify + pack write (metered)
GET  /api/abstract/{job}/pack           file list with bytes/tokens; each file served with llms headers
POST /api/abstract/{job}/publish        {target: user|node:<slug>|catalogue}
```

CLI: `llmsx abstract "indexing" --scope docs.mongodb.com,docs.postgresql.org --budget-tokens 8000 [--seed …] [--exclude …] [--no-llm]`. Local mode invokes `/lca` directly.

MCP (13): `explorer_concept_pack(slug)` read; `explorer_abstract(concept, scope)` metered job.

## 6. UI (pages, states, empty/error states)

- **Scope picker**: tabs *My docsets* / *Public catalogue* (search by host, category, page count) / *Upload* / *Estate*; shows token size of the scope and the embedding cost for the semantic pass.
- **Lexicon editor**: table (term, relation dropdown, weight, evidence snippet, hits after harvest); add/remove; excludes list for polysemy ("cookie" → exclude "snack", "monster"); "core" badge on relations that qualify a unit alone.
- **Harvest report**: bars per term (hits, sources), z-score bands (strong / borderline / rejected), "keyword suspects" (matched by string, rejected by meaning), candidates found by meaning only.
- **Pack view**: facet tabs in taxonomy order with counts; unit rows with type chip, text, source link, `also:` sources; Disagreements as side-by-side cards; Related concepts with hits; Coverage panel (zero-hit terms, rights line); small-budget slider that re-cuts `llms-small.txt`.
- **Graph**: `concept-graph.json` in the 3D renderer (focus mode on the concept; edge weight = relation weight; node size = hits).
- **Publish**: choose target; tree-node publish requires 01 lint 0 High and writes the pack path onto the node.
- States: scope too large for tier; concept with zero hits (suggest synonyms from the vocabulary layer 12); harvest cached from a previous run (offered for reuse when scope unchanged); model step failed evidence rule (units listed as dropped).

## 7. Data model and storage

```
abstractions(id, user_id, concept, slug, scope json, lexicon json, status, budget_tokens, pack_path, published_to json, created_at)
harvest_cache(scope_hash, model, embeddings blob path, created_at)     -- the semantic pass cache, shared across a user's runs
jobs / job_events / artifacts                                          -- shared
```

Pack files under `/u/<user>/<slug>.llms/`; a node-published pack is also referenced from the tree node (`conceptPack` pointer, not content).

## 8. Tiering, metering and billing hooks

| Step | Free | Paid |
|---|---|---|
| Keyword harvest over own uploads / public catalogue | scope ≤ 2 MB, 3 runs/day | scope ≤ 200 MB |
| Semantic pass | off | embeddings metered (local model, cheap), cached per scope |
| Lexicon expansion, borderline classification, verification | off (script lexicon only) | Claude tokens metered |
| Pack view, download, 3D graph | yes | yes |
| Publish to tree node / catalogue | no | yes (moderated) |

Estimate shown before harvest (scope size → embedding tokens) and before classify (borderline units × prompt size).

## 9. Acceptance bar (measurable)

- The three canonical examples reproduce the skill's evals (`skills/llms-concept-abstractor/evals/evals.json`) with the same or better recall; every kept unit source-anchored (01 P7 0 High).
- Harvest of a 6-docset scope completes without model tokens; classify touches only borderline units (report shows the count).
- `llms-small.txt` respects `--budget-tokens` within 2 %; every cut facet carries its "N more" line.
- Disagreements section non-empty when sources conflict on a definition (seeded test: "covered query").
- Graph renders in the 3D view with the concept as focus and ≤ 200 nodes.

## 10. Security, rights, privacy

- Third-party catalogue scopes: the pack republishes excerpts; `manifest.rights` records each source's status; publishing a pack whose sources are not the user's is allowed only as index + facts (short units) — the full catalogue stays private (same rule as 13).
- Uploads private; harvest cache keyed by user.
- Model steps obey the evidence rule (every returned name must appear in the units) — no invented terms enter a lexicon.

## 11. Dependencies on other components (by number)

01 (lint gate), 09 (tree node publish, 3D renderer), 12 (vocabulary grammar and synonym suggestions), 13 (catalogue scopes, publish), 15 (metering), 16/17 (embedding pool, scope text via the store), 08 (a pack's related concepts feed the family explorer).

## 12. Open questions and assumptions

- Assumed the whole-estate scope is owner-only (operator's docsets), not a public feature.
- Open: default `--budget-tokens` for small (8k vs the ladder's 50k) — leaning 8k for packs.
- Open: whether lexicon edits should persist as reusable "lexicon templates" per concept across users (privacy-neutral, useful) — leaning yes, opt-in.
- Assumed the semantic pass uses the same embed model as 17 so its cache is shared with indexing.
