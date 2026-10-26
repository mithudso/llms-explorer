# Representation, temporal provenance and embedding revisions

Research date: 2026-10-22. Parent run: concept-knowledge-strategies-20261022.
This dossier contains three separate narrow depth runs. It proposes experiments
and additive contracts. It records no new embeddings and makes no production change.

## Result and evidence limits

The best next representation change is to bind every searchable unit to the
exact canonical statement or source span from which it came, and bind every
vector to the exact text and encoding revision used to compute it. Add
effective-time annotations where an application question needs them. Test richer
retrieval representations after those identities can be audited.

All three depth runs reached their six-pass cap while useful gaps remained.
Their status is **BUDGET_EXHAUSTED**, not depth saturation. Their authored
conclusions and schema-valid claim bundles are ready for the parent's separate
evidence gate and persistence workflow. A supported generic mechanism is not a
measured retrieval improvement in this project.

## 1. Bitemporal claim provenance

**Boundary.** This run covers the effective and recorded time of assertions,
immutable source/statement versions, historical query lenses and correction
semantics. Temporal database replacement, general truth maintenance and
dependency replay remain sibling research.

**Mechanism.** Store two different questions explicitly: when did an assertion
apply, and when did this system accept or revise it? A retrospective correction
then creates a new recorded view of the same effective period. A historical
publication can retain the view available when it was produced, while today's
answer can use the corrected view. The [XTDB time model](https://docs.xtdb.com/about/time-in-xtdb.html)
shows independent query lenses. [Fowler's original explanation](https://martinfowler.com/articles/bitemporal-history.html)
also explains why captured action inputs can satisfy some audit requirements
without a complete bitemporal property history.

**History and identity.** Temporal database work established the distinction
between valid and transaction time well before current knowledge graphs. The
[Jensen/Snodgrass temporal glossary](https://www2.cs.arizona.edu/~rts/pubs/TRmerged.pdf)
also explains uncertain dates, differing perspectives and transaction histories
that cross database boundaries. [PROV-DM](https://www.w3.org/TR/prov-dm/) supplies
a complementary identity model: entities, activities and agents, with separate
revision and quotation relations. Its [constraints specification](https://www.w3.org/TR/prov-constraints/)
treats provenance validation as consistency; it does not turn a consistent
provenance graph into proof of factual truth.

**Failure conditions.** A source publication date, source fetch time, claim
verification time and fact effective time can differ. Inferring the last from
the first three would invent precision. Keep unknown effective dates unknown.
Do not silently resolve conflicting source perspectives by selecting whichever
was fetched later. These are project design inferences from the temporal model,
rather than a claim that a temporal store automatically resolves disagreement.

Historical storage also does not recalculate every affected answer.
[XTDB v1 explicitly separates temporal history from cascading corrections](https://v1-docs.xtdb.com/concepts/bitemporality/).
Historical retention has operational limits: [XTDB's quickstart documents
deliberate hard deletion](https://docs.xtdb.com/quickstart/sql-overview.html).
A retention policy and a derived-output invalidation policy therefore belong
beside any assertion history.

**Comparison with this project.** The audited canonical claim IDs, immutable
source snapshots and publication artifacts already solve much of the version
identity problem. The missing question is whether callers need a claim's
effective interval as well as the artifact's recorded time. A new graph or
temporal database is not established as necessary. The first proposed addition
is an optional assertion envelope:

- Stable concept owner and immutable statement-version ID.
- Source snapshot/evidence IDs and the assertion-producing activity.
- Recorded-at time, supersedes/retracts links and verification status.
- Optional valid-from/valid-to with explicit unknown values and date precision.
- A source/version applicability condition, distinct from a wall-clock interval.

This envelope is a proposed project contract. Existing version-specific claims
can often use a software version interval more faithfully than an inferred date.

**Experiment and falsification.** Build a fixture with a late correction, a
future-effective update, a retracted source, an unknown effective date and two
credible sources that disagree. Ask both “what do we believe now about date D?”
and “what could the published artifact at time T justify about date D?” Compare
the current immutable-artifact baseline with the optional assertion envelope.
Require exact historical evidence identity and no invented dates. Measure
correct answers, unsupported temporal assumptions, storage cost and annotation
effort. If artifacts already answer every required query and the added envelope
does not improve those scores, keep the existing mechanism.

**Unresolved.** The project has not yet established how many actual user tasks
need bitemporal questions. A full storage migration would be premature without
that workload evidence.

## 2. Context-preserving multi-granularity embeddings

**Boundary.** This run compares self-contained atomic units, chunk-specific
textual context and contextual token pooling. Summary hierarchies, graph
community summaries, token-level late interaction and model training are
handoffs.

**Mechanism and history.** [Dense X Retrieval](https://arxiv.org/html/2312.06648v3)
studies the indexing unit and defines a proposition as a minimal fact with enough
context to stand alone. [Anthropic's contextual retrieval](https://www.anthropic.com/research/contextual-retrieval)
instead adds chunk-specific explanatory text before both dense and lexical
indexing. [Late Chunking](https://arxiv.org/html/2409.04701v3) encodes document
tokens together and pools token spans afterwards. These change different
stages; their shared goal does not make them interchangeable.
[Voyage's contextualized chunk API](https://www.mongodb.com/docs/voyageai/models/contextualized-chunk-embeddings.md)
is a current implementation that accepts document groups and returns a vector
for each chunk.

**Counterevidence.** Dense X evaluates Wikipedia and audits generated
propositions for unsupported content and missing standalone context. Its corpus
and model results do not establish a win for technical concept evidence.
Anthropic reports limited benefit from generic document summaries compared
with chunk-specific context. Late Chunking reports that irrelevant surrounding
text can make contextualization unhelpful; its overlap ablation also provides
no universal overlap advantage. These findings justify conditional experiments,
not an unconditional “more context is better” rule.

**Project inference.** The existing atomic facts are already a proposition-like
baseline. Preserve their exact evidence and compare deterministic concept,
heading and applicability context before paying for generated context. Retrieve
a compact claim or chunk; expand its parent passage when the question needs a
qualifier or cross-sentence explanation. Keep generated context separate from
the canonical evidence text so it cannot silently become a cited assertion.
This last separation is a proposed evidence-safety contract.

The inspected system also has two different length controls: docset chunks
use a 1,200-character target with 200-character overlap, while website concept
embedding inputs are capped at 2,000 characters. The parent audit found that
1,304 of 1,518 constructed website pack texts exceeded that cap. This measures
the opportunity for truncation, not the number of relevant facts lost or a
retrieval-quality regression. Candidate text length, actual encoded length and
evidence position must be measured together.

**Controlled comparison.**

| Arm | Index representation | What it isolates |
|---|---|---|
| A | Current plain claim/chunk text | Existing baseline |
| B | Same units with deterministic concept, heading and version context | Structural context |
| C | Same units with verified chunk-specific generated context | Generated context beyond B |
| D | Same units with suitable contextual token pooling | Encoding mechanism |
| E | Claim candidates with bounded parent-passage expansion | Retrieval unit versus answer context |
| F | Claim, passage and concept representations with a shared answer token budget | Additional granularity |

Run these against fixed exact-name, paraphrase, exception, temporal/version and
multi-concept question strata. Keep the embedding model constant between A–C,
the source snapshot constant throughout, and reranking disabled initially.
Then add the same reranker to winning arms. Report evidence recall, nDCG,
citation entailment, answer correctness, retrieved token count, latency and
indexing cost. Equal k is not an equal information budget when one arm returns
claims and another returns passages.

**Falsification.** Reject an arm if its apparent gain disappears at the same
answer token budget, if it raises unsupported qualifier omissions, if generated
context causes source attribution errors, or if the marginal benefit does not
justify its measured operating cost. All quality effects remain unmeasured
locally, and the embedding pause remains in force.

## 3. Revision-bound embedding index migration

**Boundary.** This run covers representation identity, independent index
revisions, validation, cutover and rollback. It does not choose a new vector
database or execute a re-embedding job.

**Mechanism.** A vector belongs to a particular encoded-text and model contract,
rather than merely to a concept ID. [Voyage's migration guide](https://www.mongodb.com/docs/voyageai/tutorials/migrate-embedding-model.md)
warns that equal dimensions do not prove compatible relevance geometry, while
documenting a compatible model-family exception. Compatibility therefore needs
an explicit provider guarantee or a measured contract. The
[SentenceTransformer API](https://www.sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html)
also exposes model revision, task prompts, normalization, precision and
dimension truncation. A model name alone cannot describe every encoding input.

**Routing versus data correctness.** [Qdrant collection aliases](https://qdrant.tech/documentation/concepts/collections/)
and [Elasticsearch aliases](https://www.elastic.co/docs/manage-data/data-store/aliases)
permit atomic routing changes. Elasticsearch also documents partial alias action
failures, so successful cutover requires checking the operation result.
[Current Elasticsearch reindex documentation](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-reindex)
does not copy destination schema configuration. Its
[8.19 procedure](https://www.elastic.co/guide/en/elasticsearch/reference/8.19/docs-reindex.html)
describes a source snapshot rather than continuous change replay.

The important late finding is in [Qdrant's migration tutorial](https://qdrant.tech/documentation/tutorials-operations/embedding-model-migration/):
a delete that misses a point absent from the new collection can be undone by
later backfill. Retaining the old index is also insufficient for a current
rollback after old writes stop. Its
[incremental update recipe](https://qdrant.tech/documentation/tutorials-operations/incremental-embedding-updates/)
separates location identity from normalized text hashes. These mechanisms
support tracking both identities rather than using a stable concept key as
proof that its vector remains current.

**Proposed revision manifest.** Bind an index revision to:

- Canonical artifact ID and exact encoded-text hash.
- Unit ID, unit granularity, source revision and text projection policy.
- Model provider, immutable model revision where available, compatibility family,
  output dimensions, task prompt and preprocessing/chunking revision.
- Vector normalization, precision and index distance configuration.
- Query encoder settings and cache namespace.
- Build completeness receipt, exclusion policy and evaluation receipt.

The manifest is a project design inference. It can be implemented as a sidecar
for a static index; it does not require a new database.

**Baseline gap.** The inspected website refresh updates vector metadata while
leaving existing vectors frozen, without exact text/artifact hashes binding each
vector. The docset path chooses its query model from docset metadata, but the
federated query-vector cache uses only query text as its cache key. The latter
is a migration hazard if several model contracts share the cache. These are
observed contract gaps; no current retrieval-quality loss was established.

**Experiment and rollout proposal.** While embeddings remain paused, inventory
existing revisions and classify text/artifact binding as known, mismatched or
unknown. Do not manufacture historical input hashes from today's text. After
separate authorization to compute vectors, create a candidate index from one
pinned artifact and preserve the active revision. Run identical held-out
queries through each revision's own matching query encoder. Compare semantic
quality with the evaluation worker's fixed strata and test deterministic
contract mismatch rejection independently.

Cutover should select one configuration object containing index revision,
query encoder and cache namespace. Exercise rollback to the old object in a
fixture. Validate IDs, content hashes and exclusions; equal row counts alone
can conceal offsetting omissions and duplicates. Prefer a static pinned-artifact
build for this repository. If a future service needs concurrent writes, specify
ordered changes, tombstones, replay watermarks and reconciliation before calling
dual writes complete.

**Falsification and keep-current condition.** Keep the active revision if the
candidate does not beat the predefined quality/cost rule, if its encoded corpus
is incomplete, if the same query can reuse a cache entry from another contract,
or if a rollback fixture cannot restore a coherent old query/index pair.
Migration correctness and retrieval superiority are separate acceptance tests.

## Measured depth record

The rate is accepted new atomic claims divided by all accepted claims after
that pass. Counts precede the separate runtime evidence gate. Source retrieval
was batched across concepts; each concept has its own scope and deduplication.
A zero pass appears only where the source review produced restatements.

| Concept | Seed claims | Pass 1 | Pass 2 | Pass 3 | Pass 4 | Pass 5 | Pass 6 | Final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Bitemporal provenance | 0 | 2/2, 100% | 5/7, 71.4% | 4/11, 36.4% | 1/12, 8.3% | 2/14, 14.3% | 1/15, 6.7% | 15 |
| Context-preserving units | 3 | 3/6, 50% | 3/9, 33.3% | 3/12, 25% | 1/13, 7.7% | 0/13, 0% | 2/15, 13.3% | 15 |
| Embedding migration | 4 | 2/6, 33.3% | 2/8, 25% | 1/9, 11.1% | 2/11, 18.2% | 1/12, 8.3% | 6/18, 33.3% | 18 |

All three verdicts are **BUDGET_EXHAUSTED**. None has two consecutive passes
below 5%. The migration curve rose when the final pass uncovered concurrent
mutation hazards and content identity mechanisms. One additional narrow pass
on ordered replay/tombstones would likely be useful, but belongs to its
declared sibling rather than being silently absorbed.

The private handoff contains per-concept claims JSON, atomic claim IDs and
pass ledgers listing literal search strings, opened sources, accepted claims
and rejected restatements. Raw page extracts and source text remain private.
The claim schema checks passed for 48 claims across the three concepts.

## Open research queue

The next research questions are temporal dependency invalidation, uncertain
effective-date semantics, hierarchical summary retrieval, late interaction,
ordered mutation replay with tombstones, and embedding drift detection.
Prioritize them only after their expected effect on the project's held-out
tasks is established. They were surfaced without broadening these three runs.

