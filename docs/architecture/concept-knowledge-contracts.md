# Concept knowledge contracts

Implemented by TASK-840 after the research recorded in TASK-816. These changes preserve the canonical artifact and exact evidence-span architecture. They do not generate embeddings or deploy the website.

## Research assertions

New Codex runs record `gate_contract_version: 3` and use `research-gate/v3`. The independent judge reads each complete summary, disagreement and open question. These units are mandatory even when the ordinary claim sample is zero. This avoids relying on another model to extract all factual assertions from prose. The judge checks disagreement attributions and factual premises inside questions. `SUPPORTED` requires pinned source spans establishing the full assertion. A pure question can receive `NO-FACTUAL-ASSERTION`; structured claims cannot receive that verdict.

Canonical artifacts store each auxiliary assertion's full text, source URLs, identity, verdict and evidence IDs. Editing prose after its gate invalidates completion. Artifact verification also rejects prose that differs from its stored judgment. Coverage reports distinguish structured claims from auxiliary assertions. Marginal supported-fact counts include structured claims only.

Version-2 gates remain readable and retain their original claim-only meaning. Old research is not silently upgraded to full-prose validation. New contracts apply to new runs; active version-2 runs keep their existing contract. The shared Claude runtime remains unchanged. The repository's generated Codex adapters carry the new behavior.

## Temporal claim history

A claim may add this optional metadata:

```json
{
  "temporal": {
    "valid_from": "2026-10-01",
    "valid_to": null,
    "applicability_version": "v4",
    "recorded_at": "2026-10-22T14:00:00Z"
  }
}
```

`valid_to` is exclusive. Calendar dates have day precision; timestamps require an ISO date, a `T` separator and a timezone. An absent or null field means unknown. Fetch time, verification time and observation time do not establish an applicability interval. The gate checks asserted applicability against evidence.

Temporal metadata participates in immutable statement identity. Changing applicability creates a different claim version. Claims without this field keep their earlier IDs. Existing immutable artifacts retain historical versions. Units, reader facts and canonical downloads preserve temporal metadata alongside evidence IDs. This adds history without replacing the existing storage system or inventing dates for legacy evidence.

## Retrieval and lexical coverage

A docset unit's fusion identity includes the docset, URL, chunk sequence and full-text hash. Equal page URLs no longer collapse distinct chunks or chunk versions. Dense and BM25 hits use the same identity. RRF gives a unit one contribution per input list; duplicate hits neither inflate its score nor consume another rank. The default `k=60` is unchanged. Query history retains the unit identity.

Federated retrieval includes the existing file and docset FTS5 indexes. Keyword retrieval does not generate embeddings. The website keyword index includes every distinct token from every fact. Its token vocabulary preserves the client's existing membership-based ranking while avoiding repeated prose in the download. Publication scrubbing runs before indexing. Literal operator-denylist prose receives the same treatment as sensitive addresses and URLs.

The refreshed committed corpus contains 1,518 concepts. Its complete lexical vocabulary occupies 6,221,932 bytes. All 1,018 existing semantic rows retain their original vector bytes; 500 concepts remain explicitly deferred from semantic indexing. These repairs demonstrate identity and coverage correctness. They do not establish a measured relevance gain or select a new fusion method or model.

## Embedding revisions and query compatibility

New docset writes bind the exact UTF-8 input hash, unit ID, captured source-artifact hash, encoder configuration and vector content. The source hash comes from the same captured file bytes used to parse the input. SQLite stores bindings with chunks and the encoder in an additive registry table. Chroma stores bindings with its chunk metadata and uses the same registry. Existing rows retain unknown provenance until explicitly rebuilt. Metadata-only refreshes do not manufacture historical input hashes.

For Ollama, `HUB_EMBED_MODEL_REVISION` pins the default model's full digest. `HUB_EMBED_MODEL_REVISIONS` accepts a JSON map for multiple models. Pinned embedding calls use only configured hosts reporting that digest for the requested model. The provider exposes these digests through its documented [list-models endpoint](https://docs.ollama.com/api/tags). Unversioned aliases remain explicitly revision-unknown. Digest checks observe provider metadata before a request; operators should keep pinned model tags immutable during indexing.

Federated and standalone docset queries select the recorded model. Queries reject incompatible model revisions and dimensions. Their cache namespace includes query text, model, model revision, encoder configuration, pool configuration and cache revision. Unversioned model aliases share concurrent work but do not retain persistent query-vector cache entries.

The website generator requires both `--allow-embeddings` and `--model-revision` with a pinned 40-character model commit. It records the exact code-point-capped input, canonical artifact or pack hash, pooling, normalization, preprocessing, query settings and vector bytes. The browser uses that model commit and checks the vector payload hash. Frozen syncs preserve vector bytes and distinguish unknown provenance, current bindings and stale bindings. Current input hashes are separate from historical encoded-input hashes.

When the embedding pause is explicitly lifted, generate a candidate using separate `--out-bin` and `--out-meta` paths. Evaluate it with its matching query encoder. Publish the metadata and binary from the same reviewed commit. Roll back both files together. Legacy website vectors remain available under the existing model-name compatibility behavior; their new metadata explicitly records that the exact historical model revision and input are unknown.

## Verification

Regression tests use pinned synthetic evidence and fixed vectors. They cover full-prose selection, historical receipts, temporal identity and projections, duplicate fusion votes, repeated page URLs, late facts, model and revision cache separation, provider digest drift, text/vector tampering, Unicode input hashes and browser compatibility checks. No test downloads a model or generates production embeddings.

Final local results on 2026-10-22:

- Research, adapter and privacy suites: **201 passed**, plus **4 subtests passed**.
- Site suite after the production build: **284 passed**.
- Hub suite: **549 passed**, with one existing scope-test failure. `test_scope_include_unscored_and_zero_threshold_restore_the_old_behaviour` reports `250 != 333`. The same failure reproduces on untouched upstream commit `7bb68955` in a separate checkout.
- Production site build, site type checking, project-wide Ruff, generated-adapter synchronization and whitespace checks passed.
- The final changed-file privacy scan found **0 findings**. The semantic binary has no diff from upstream.
