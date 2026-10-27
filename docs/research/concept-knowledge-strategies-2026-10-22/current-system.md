# Verified current system

Read-only implementation inventory, 2026-10-22. Counts describe this session's
snapshot. Other active research can change them. The hub and repository trees
are separate inventories: the hub scan contained 1,845 nodes; the repository
snapshot contained 1,840.

## Existing strengths

- `scripts/research_gate.py:37` enumerates full structured claims. The gate
  hashes exact statement versions, selects risky claims and a deterministic
  ordinary sample, and binds judgments to immutable source snapshots and exact
  Unicode spans. It rejects stale judgments and unresolved dissent.
- `scripts/research_artifact.py:17` gives canonical artifacts immutable hashes,
  stable slug-derived concept IDs, version-specific claim IDs, evidence IDs, and
  distinct `SUPPORTED`, `NOT-SAMPLED`, and `LEGACY-UNBOUND` states.
- `scripts/research_provenance.py:62` retains immutable source versions and
  explicit origin/derivation metadata. When ownership is undeclared, the
  organization/host value is explicitly a proxy for independent origin.
- `scripts/codex_dr_artifacts.py:166` compiles private and scrubbed public
  projections from canonical artifacts. Merge validation protects existing tree
  placement and pack ownership. `scripts/research_transaction.py:35` journals
  preimages and restores them after failed promotion.
- `scripts/research_site_sync.py:149` preserves frozen vectors and binary row
  alignment. It refreshes keyword coverage and explicitly excludes new concepts
  from semantic coverage. It reports `new_embeddings: 0`.

These mechanisms already separate canonical knowledge from disposable indexes.
The recommended architecture should extend their contracts.

## Retrieval is different on each surface

| Surface | Observed behavior | Relevant implementation |
|---|---|---|
| Private source library | SQLite FTS5 BM25; heading-aware approximately 1,400-character chunks, hard target about 2,600; heading boost 3; source/domain/tag/URL filters and per-source limits | Shared `source_library.py:96`, `:131`, `:419`, `:952`; repository wrapper `scripts/research_library.py:25` |
| Standalone docsets | Separate lexical and semantic queries; paragraph packing at 1,200 characters and oversized-paragraph windows with 200-character overlap; facts twin indexes atomic units | `hub/scripts/docset_indexer.py:51`, `:109`, `:144`, `:279`, `:673`, `:787` |
| Federated hub | Semantic corpus fan-out, RRF with k=60, cosine re-embedding of up to 50 candidate snippets, default top eight; 400-character snippets and 6,000-character final context | `hub/scripts/semantic_ops/corpus.py:199`, `ask.py:60`, `fuse.py:16`, `rerank.py:13` |
| Website | Concept vectors from MiniLM, dimension 384; input is concept, summary and earliest facts capped at 2,000 characters. Keyword body is capped at 2,500. All query terms must occur; title matches receive extra weight; lexical hits precede semantic hits and display is capped at eight | `site/tools/gen_search_index.mjs:34`, `scripts/research_site_sync.py:153`, `site/src/scripts/concept-search.ts:3`, `site/src/components/SearchBox.astro:150` |

The federated reranker is an embedding cosine reranker, not a cross-encoder.
Its default corpus list has no BM25 adapter. Calling that surface hybrid
lexical/dense retrieval would misdescribe the implementation.

## Snapshot scale

| Inventory | Count |
|---|---:|
| Public concept packs / keyword entries | 1,518 |
| Frozen website semantic rows | 1,018 |
| Explicit website semantic exclusions | 500 |
| Semantic binary bytes | 1,563,648 = 1,018 × 384 × 4 |
| Private source-library sources / FTS chunks | 9,742 / 130,417 |
| Registered docsets | 143: 138 Chroma, 5 SQLite |
| Registered docset chunks | 443,839; registry values are not physical-count validation |
| Hub tracked files / distinct hash embeddings | 468,237 / 192,458 |

All registered docsets recorded `mxbai-embed-large`; stored hub-file embeddings
recorded `nomic-embed-text`. Those existing model names are inventory facts,
not a recommendation to keep or replace either model.

## Demonstrated mechanisms and their practical limits

1. **Website text truncation.** 1,304 of 1,518 constructed pack texts exceed
   the 2,000-character embedding-input cap. 1,225 exceed the 2,500-character
   keyword cap. The largest constructed text has 528,934 characters. Facts
   beyond those prefixes are omitted from those index inputs. This establishes
   representation loss, not its task-level relevance cost.
2. **Auxiliary prose is outside semantic claim judgments.**
   `research_gate.claim_rows` reads `claims`. Canonical artifacts also retain
   summaries, disagreements, and open questions. Hashing those sections binds
   their wording after the gate; it does not establish factual entailment. This
   reproduces the limitation recorded in Stele KNOW-796.
3. **Frozen vectors can outlive changed text.**
   `research_site_sync.py:167` updates title/summary metadata while retaining
   existing vector bytes. It does not bind a vector to the current claim or
   source-text hash. The pause explains the choice; future migration needs
   explicit freshness metadata.
4. **Federated model configuration has a migration risk.**
   `semantic_ops/corpus.py:51` caches query vectors by query string and uses the
   default pool model rather than the individual docset model. The standalone
   query honors the recorded model (`docset_indexer.py:793`). Current docset
   models match, so this is a configuration-triggered risk, not evidence of
   present mixed-model corruption.
5. **Page identity collapses chunk evidence during fusion.**
   `DocsetCorpus` assigns the page URL to `Hit.ref` and keeps chunk sequence only
   in metadata (`corpus.py:136`). `fuse.py:16` sums every occurrence keyed by
   `(source, ref)` and retains the first snippet. Same-page chunks can increase
   a page score within one rank list while their distinct evidence disappears.
   The ranking effect can be reproduced without embeddings; its relevance cost
   needs judged queries.
6. **Content deduplication loses file locations in one loader.**
   `hub_sqlite.py:70` reverses the path-to-hash mapping into hash-to-one-path.
   Shared content is valid to deduplicate; this return shape does not retain all
   corresponding locations.
7. **The embedding pause is a workflow policy.** The research site completion
   path produces zero embeddings. Embedding core, docset query/indexing,
   federated reranking, and website semantic generation remain callable. This
   research invokes none of those embedding paths.

## Evaluation already available

`scripts/research_system_benchmark.py:172` measures claim support, atomicity,
uniqueness, mechanisms, depth, provisional reference coverage, tokens, and time.
It does not isolate concept retrieval or embedding changes. An existing
code-symbol/docstring experiment records recall@1/5/10 and MRR@10 on a different
task. Both are useful precedents; neither establishes which retrieval strategy
wins on concept evidence, stale claims, or multi-concept questions.

The remaining uncertainty is measured quality: representative relevance labels,
held-out concept tasks, answer support/completeness, latency, maintenance cost,
and the incremental value of each proposed component.
