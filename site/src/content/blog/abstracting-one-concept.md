---
title: "Abstracting one concept out of many docsets"
description: "/lca pulls 'indexing' out of nine database docsets and 'prompt caching' out of three API docs: lexicon expansion, a zero-token harvest, borderline classification, a facet-grouped pack — and what the evals measured."
date: "2026-09-03"
tags: [concept-pack, lca, harvest]
sources:
  - outputs/llms-concepts/EVAL-NOTES-2026-08-31.md
  - outputs/llms-concepts/indexing--databases.llms/manifest.json
  - skills/llms-concept-abstractor/references/output-contract.md
  - docs/site/components/06-concept-abstraction.md
---

<!-- verified-as-of: 2026-08-31 · numbers from outputs/llms-concepts/EVAL-NOTES-2026-08-31.md -->

## Problem

A topical file (previous post) starts from facts that are already about the subject. The
harder case is a concept buried in scope that is mostly about something else: "heart" in an
anatomy textbook, "indexing" across a MongoDB manual and seven ORM docs, "prompt caching" in
three vendor API references. Nobody has a pool; the pool has to be found.

The naive approach — grep for the word — fails twice. It misses every unit that says
"B-tree" or "covered query" without saying "index", and it catches every `index.html`,
`z-index` and array subscript. The abstractor's answer is a lexicon: the concept plus its
synonyms, abbreviations, parts, sub-types, instances, measures, problems, contrasts and
broader terms, each with a relation weight, plus an exclude list for the polysemy. The lexicon
drives a keyword harvest and a semantic pass over embeddings of the whole scope; the model
only touches the borderline.

## Inputs

Two evaluations were run on 2026-08-31 with the skill and, for the first, a baseline agent
without it.

- **eval-1, prompt caching × 3 docsets**: the code.claude.com, openrouter.ai and
  platform.openai.com exports. The OpenAI export is degenerate (8 units from a JS-rendered
  mirror) and was kept in scope so that `## Sources` reports 0 for it honestly.
- **eval-2, indexing across database docsets, with scope discovery**: 10 inputs — the
  mongodb.com export's facts and raw mirror, seven third-party `llms-full.txt` mirrors from the
  catalogue (Prisma, Drizzle, Nile, Turso, Convex, InstantDB, MotherDuck), and the hub's indexed
  MongoDB raw layer. 65,279 units scanned; 49,744 distinct texts embedded.

## Commands

```bash
# cwd: ~/.global-ai-hub  (the skill's script; /lca wraps these steps for an agent)
S=~/.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py
.venv/bin/python $S harvest  --concept "indexing" --lexicon lexicon.json \
   --scope mongodb.com.llms/llms-facts.txt llms-full/files/prisma.io__docs.txt ... \
   --out llms-concepts/indexing--databases.llms/
.venv/bin/python $S semantic --pack llms-concepts/indexing--databases.llms/ --z-floor 3.5
# model: classify borderline units, verify a sample → classified.jsonl
.venv/bin/python $S pack     --pack llms-concepts/indexing--databases.llms/ --budget-tokens 16000
.venv/bin/python $S split    --pack llms-concepts/indexing--databases.llms/ --groups groups.json
.venv/bin/python scripts/llms_lint.py check llms-concepts/indexing--databases.llms/llms.txt
```

The harvest and semantic passes spend no model tokens; embeddings come from the local pool and
are cached on disk, so a second round with a wider lexicon re-scores without re-embedding.

## Outputs

**eval-1 (prompt caching).** Rounds: 6 terms → 209 units; 26 terms → 331 (+58 %, with leaks:
embedding dimensions, a JWT `subject_prefix`, `ephemeral` containers); 25 terms + 39 excludes →
275 keyword units + 26 semantic adds at z ≥ 3.0, of which 7 were genuine. Classification kept
194. The pack: full ≈ 19.3k tokens (1.8 % of the scanned facts text), small ≈ 8.2k on an 8k
budget (+2.5 %, inside the 5 % tolerance), 11 of 13 facets populated, a 25-term vocabulary,
0 conflicts.

**eval-2 (indexing).** Rounds: 1,886 → 2,331 (38 terms) → 2,982 (39 terms + the extra raw
layer) → 2,947 after 16 more excludes → 2,699 after exact and near-duplicate folding (249
folded). 43 excludes in the end (`llms.txt` index, `index.*` files and routes, array index,
`z-index`, …). Zero-hit terms: none. The union pack came out at ≈ 180.7k tokens (4.3 % of
≈ 4.2M scanned), so the split rule fired: five child packs — index types (565 units),
lifecycle and health (414), ORM index definitions (328), query planner / explain / covered
queries (284), search and vector indexes (254) — each with its own ≈ 8.2k-token small file;
the union small is 16.2k on a 16k budget.

| Run | Model tokens | Wall time | Grade |
|---|---|---|---|
| eval-1 with skill | 336,335 | 718 s | 7/7 |
| eval-1 baseline (ordinary tools) | 376,182 | 571 s | 3/7 |
| eval-2 with skill (scope discovery) | 496,462 | 2,281 s | 6/6 |

The baseline produced ~170 statements with a 71-URL legend and inline `[Cn]` tags, wrote four
ad-hoc Python helpers, read pages in full, ran no precision or agent test, and left nothing
reusable. It also cost more tokens.

## What the lint found

- Index: 0 High on both packs.
- Facts, eval-2: 1 High — `P7 C6` on 415 lines whose source is a `file://` path (the Convex and
  InstantDB mirrors are local files, not URLs). Documented as expected in the skill's
  verification reference (V10) rather than suppressed: the lint is right that a `file://`
  anchor is not a promise a reader can follow, and the fix is publishing those mirrors.
- Verification (eval-2): traceability 10/10 by hand and 2,115/2,115 programmatically; precision
  20/20 after one drop; leakage 0/40 after two fixes; probe hit rate 10/10 on small, full and
  semantic; fresh-context agent test 10/10 on small and 10/10 on full — with the agent noting
  that Postgres `EXPLAIN` / `Seq Scan` / "index-only scan" wording is absent from the whole
  scope, so those questions were answered from MongoDB and SQLite terms.
- Gaps the pack reports about its own scope: the `history` facet holds 2 units; the MotherDuck
  mirror is a routing bundle, not docs; in eval-1, the per-model minimum-cacheable-length table
  did not survive facts extraction, and `cached_tokens` / `prompt_cache_key` never appeared.

## Lessons

- On a broad concept with a rich lexicon the semantic pass is a precision instrument, not a
  recall one: at z ≥ 3.5, 283 of the 284 candidates were already keyword hits, and the z ≥ 3.0
  adds were off-topic.
- Excludes must filter the scope before embedding, not after: a semantic add that bypasses the
  exclude list reintroduces the polysemy the lexicon just removed (fixed in v1.1.1).
- An export with fewer than 20 facts is degenerate; keep it in scope for an honest zero and
  stop investigating it.
- A budget overrun under 5 % is acceptable and should be reported, not hidden: the round-robin
  cut a wanted OpenRouter TTL unit and said so.
- A pack over roughly 100k tokens is a family, not a file — split by ordered term groups into
  child packs and let the parent index link them.
- Two packs appending to a shared vector cache at once corrupt it; the fix is a file lock plus
  a load-time alignment check that trims to the consistent prefix.

## Reproduce

The finished packs, their manifests, harvest reports and eval notes are under
`outputs/llms-concepts/` in this repository (`indexing--databases.llms/` and its five children,
`prompt-caching.llms/`, `EVAL-NOTES-2026-08-31.md`). The output contract — every file, its
grammar and a worked "heart" example — is `skills/llms-concept-abstractor/references/output-contract.md`.
