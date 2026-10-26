# Retrieval strategy depth dossiers

Research date: 2026-10-22. These two concepts have separate claim inventories and novelty accounting. Both stopped at the default six deepening passes. Neither demonstrated depth saturation. Canonical persistence and independent claim verification are separate completion steps handled by the parent run.

Source-binding review withheld E12 from the canonical claim bundle because the
publisher PDF and same-origin alternative could not be retrieved as a pinned
snapshot. Its authored finding remains in the acquisition record below, but it
must not be counted as a promoted or gate-supported claim. The final candidate
bundles contain 21 fusion claims and 21 evaluation claims. The pass curves
describe the original research inventory before this separate verification step.

The project recommendation is an inference: first establish correct record identity, a real lexical baseline, and task-stratified held-out judgments. Then compare fusion methods at fixed candidate and context budgets. Published benchmark gains below are external results. No project relevance lift, new embeddings, production retrieval change, or reranker deployment is claimed.

## Candidate-depth-aware hybrid rank fusion

### Boundary

IN: ranked candidate lists, truncation depth, record identity at fusion, RRF damping and missing-list behavior, rank versus score combination, exact-match channel qualification, the boundary between fusion and reranking, and adaptive depth within RRF.

OUT: training embedding models, selecting a vector database, graph traversal algorithms, query decomposition policies, and a full cross-encoder survey. These become adjacent research items rather than additional claims inside this run.

### Definition and mechanism

RRF computes a sum of reciprocal rank contributions, conventionally `1/(k + rank)` for each contributing list. It removes the need to align raw score magnitudes. It also discards score margins. Candidate depth determines which documents can contribute; the rank constant controls relative rank influence. These are separate controls. A finite-list implementation and a method that rescored the entire candidate union can behave differently even when both are called RRF. The original definition gives each document one rank per input ranking. [Original RRF paper](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf), [Bruch et al.](https://arxiv.org/html/2210.11934v2), [Elastic implementation reference](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion).

### Atomic claim inventory

All single-URL claims retain low confidence under the research schema. F01 has corroborating primary sources. The IDs below are local audit handles; canonical claim IDs are assigned during persistence.

| ID | Atomic finding | Primary evidence |
|---|---|---|
| F01 | RRF adds reciprocal rank contributions from the input rankings; raw score magnitudes do not enter its formula. | [Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) |
| F02 | The RRF rank constant differs from a nearest-neighbor count or a candidate-depth limit. | [Relevance scoring in hybrid search using Reciprocal Rank Fusion](https://learn.microsoft.com/azure/search/hybrid-search-ranking) |
| F03 | In truncated-list RRF, an item absent from one input list contributes zero from that list. | [Improving information retrieval in the Elastic Stack: Hybrid retrieval](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid) |
| F04 | Cormack et al. fixed k=60 during a pilot and retained it during later validation. | [Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) |
| F05 | Elastic's 2023 BEIR subset experiment favored k=20 and candidate depth 1000 for the tested dense retrievers. | [Improving information retrieval in the Elastic Stack: Hybrid retrieval](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid) |
| F06 | Bruch et al. found tuned convex score combination superior to RRF in their in-domain and out-of-domain experiments. | [An Analysis of Fusion Functions for Hybrid Retrieval](https://arxiv.org/html/2210.11934v2) |
| F07 | OpenSearch's six-dataset comparison reported RRF nDCG@10 averaging 3.86% below its score-based hybrid comparator. | [Introducing reciprocal rank fusion for hybrid search](https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/) |
| F08 | Elasticsearch separates the per-retriever rank window from the final response size. | [Reciprocal rank fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) |
| F09 | Bruch et al.'s min-max normalization uses the minimum and maximum scores in the retrieved candidate union. | [An Analysis of Fusion Functions for Hybrid Retrieval](https://arxiv.org/html/2210.11934v2) |
| F10 | Bruch et al. compute missing candidate scores and approximate otherwise unknown ranks within the candidate union. | [An Analysis of Fusion Functions for Hybrid Retrieval](https://arxiv.org/html/2210.11934v2) |
| F11 | Increasing the RRF rank constant flattens relative differences between high and low ranks. | [Reciprocal rank fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) |
| F12 | Bruch et al. exclude near-zero score variance from their empirical normalization analysis and identify it as a challenge for some normalizers. | [An Analysis of Fusion Functions for Hybrid Retrieval](https://arxiv.org/html/2210.11934v2) |
| F13 | The original RRF definition models each input ranking as a permutation, with one rank per document. | [Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) |
| F14 | The original RRF experiments include a TREC-3 case where CombMNZ outscored RRF, so the paper does not show universal dominance. | [Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) |
| F15 | Elasticsearch requires a fixed rank window for stable RRF pagination; changing that window can change previously seen ordering. | [Reciprocal rank fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) |
| F16 | Exact-term matching depends on indexed field analysis; Elasticsearch's standard text analyzer removes most punctuation and lowercases tokens. | [Term query](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-term-query) |
| F17 | Bruch et al.'s normalization rank-equivalence result for one query does not by itself establish equivalent learned weights across all queries. | [An Analysis of Fusion Functions for Hybrid Retrieval](https://arxiv.org/html/2210.11934v2) |
| F18 | Azure documents a fused RRF score bound that increases with the number of query lists being fused. | [Relevance scoring in hybrid search using Reciprocal Rank Fusion](https://learn.microsoft.com/azure/search/hybrid-search-ranking) |
| F19 | Azure semantic reranking runs after RRF and reports its score separately from the fusion score. | [Relevance scoring in hybrid search using Reciprocal Rank Fusion](https://learn.microsoft.com/azure/search/hybrid-search-ranking) |
| F20 | The EAHR preprint bounds unread RRF contributions and requests deeper channel ranks while they can change complete-list top-K membership or order. | [Exact Adaptive Hybrid Retrieval Without Fixed Top-L Cutoffs](https://arxiv.org/abs/2608.07152) |
| F21 | EAHR's reported anti-correlated cases exhaust both input lists; its authors do not guarantee a speedup on every request. | [Exact Adaptive Hybrid Retrieval Without Fixed Top-L Cutoffs](https://arxiv.org/abs/2608.07152) |

### History, disagreement, and failure boundaries

The 2009 paper's pilot choice of 60 and Elastic's later preference for 20 with depth 1000 are results under different retrieval and evaluation protocols. Neither establishes a universal project default. Bruch's experiments compute missing scores and estimate ranks within a candidate union, while Elastic's finite-list formulation gives an absent-list item zero. This is a material protocol difference when comparing their conclusions. [Original paper](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf), [Elastic experiment](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid), [Bruch study](https://arxiv.org/html/2210.11934v2).

RRF's simplicity and score-scale independence do not imply superior relevance. The original tables already contain a stronger CombMNZ result for one TREC collection; the later OpenSearch comparison also favors score-based fusion on its tested quality metric. Preserve both findings with their protocols. [Original tables](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf), [OpenSearch experiment](https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/).

The recent EAHR preprint addresses fidelity to complete-list weighted RRF by bounding unread contributions and adapting depth. Its own adverse cases can exhaust both lists. Exact agreement with a fusion target is different from improved human relevance, so this is a follow-up experiment after simpler defects are resolved. [EAHR preprint](https://arxiv.org/abs/2608.07152).

### Project applicability and simplest credible baseline

The verified project baseline is recorded in [current-system.md](../current-system.md) and [diagnostics.json](../diagnostics.json). The current `semantic_ops` fusion combines semantic corpora using RRF with constant 60. It has no BM25 candidate adapter. The reranker uses embedding cosine similarity rather than a query-document cross-encoder. URL-valued document references can collapse distinct chunks. Repeated entries from one list can accumulate multiple terms. The parent run reproduced an ordering change and snippet loss with duplicate records. This establishes a mechanism defect in that controlled fixture; it does not measure its prevalence or user relevance cost.

The website's lexical-first concatenation and earliest-facts truncation form a separate baseline. Do not describe the site and semantic CLI as one hybrid stack.

Recommended project inference: preserve separate `claim_id` or `chunk_id`, `source_version_id`, and `concept_id`. Deduplicate by retrieval-unit identity inside each list before adding one contribution per list. Preserve different useful chunks from one URL; apply any source-diversity cap later and measure the loss of evidence coverage. Add a lexical-only candidate baseline before claiming hybrid search. Evaluate exact identifier lookup separately from analyzed text matching, since analysis can change punctuation and case. [Exact-term semantics](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-term-query).

### Controlled experiments and decision rules

1. **Identity and duplicate replay.** Freeze ranked lists and record payloads. Compare current behavior with once-per-list chunk identity. Include repeated chunk IDs, two different chunks from one URL, mirrored sources, tied scores, missing references, and shuffled list order. Measure score contributions, retained evidence units, and deterministic ordering. This can run without embeddings.
2. **Lexical baseline.** Compare exact ID/symbol lookup, current website lexical behavior, and a BM25 candidate generator over the same public claim/chunk snapshot. Pin tokenizer, identifier handling, fields, filter policy, and final result count. Judge exact and paraphrase tasks separately.
3. **Fusion ablation.** On already stored candidate lists, if available, sweep proposed depths 20/50/100/200 and proposed rank constants 20/60/100. Keep the final result count and candidate union fixed when isolating the fusion formula. Separately vary channel candidate depth when measuring recall effects. Compare each single channel, current RRF, corrected RRF, and normalized convex score combination with its weight tuned only on development topics. Treat those numbers as proposed settings.
4. **Rerank ablation.** First measure candidate-union evidence recall. Next hold the candidate pool fixed and compare no reranker with a specified reranker. The project's cosine reranker and a cross-encoder are distinct treatments. Any run that needs new query embeddings remains unrun while the embeddings pause persists.
5. **EAHR follow-up.** For a small replay corpus, compare fixed-depth output to an exhaustive complete-list RRF oracle. Report exact top-K agreement, work performed, and worst-case cost. Human relevance remains a separate endpoint.

Keep the existing fusion if a corrected implementation and lexical addition produce no held-out task benefit at the chosen resource budget. Prefer score combination if it wins on held-out judgments and remains stable after corpus updates. Prefer RRF if calibration transfers poorly or labels are too scarce, provided it meets task quality requirements. Investigate adaptive depth only if fixed cutoffs materially change the desired ordering or omit required evidence.

What would change this recommendation: an audit showing stable distinct chunk identities and unique once-per-list contributions everywhere; a lexical baseline that adds no judged relevant evidence; or held-out measurements showing a different bottleneck dominates.

## Task-stratified retrieval evaluation

### Boundary

IN: task and information-need definitions, corpus and judgment identity, representative topics, held-out tuning, pooled assessment, judgment holes and bias, task-specific retrieval metrics, generation/citation checks, judge validity, uncertainty, latency, and experimental confounds.

OUT: a complete benchmark catalog, online exploration policies, training relevance judges, and broad monitoring infrastructure. Temporal truth assessment and evidence-set coverage are identified as dedicated follow-ups.

### Definition and mechanism

A test collection binds a corpus, information needs, and judgments. Stratification retains separate results for distinct information needs instead of hiding them inside one mean. Pooling reduces labeling effort but requires auditing unjudged results and relevance criteria. Rank-aware metrics, evidence recall, and end-to-end answer/citation checks answer different questions. A benchmark result does not automatically transfer to another corpus, representation, query mix, or judgment protocol. [TREC protocol](https://trec.nist.gov/howto.html), [BEIR study](https://arxiv.org/html/2104.08663), [NIST measures](https://trec.nist.gov/pubs/trec15/appendices/CE.MEASURES06.pdf), [ALCE](https://arxiv.org/abs/2305.14627).

### Atomic claim inventory

Each finding has one cited URL and retains low confidence in the schema, even when the broader evaluation pattern appears across independent research groups.

| ID | Atomic finding | Primary evidence |
|---|---|---|
| E01 | TREC test collections contain a document corpus, information needs, and relevance judgments. | [How to TREC](https://trec.nist.gov/howto.html) |
| E02 | BEIR evaluates retrieval over heterogeneous tasks and domains rather than one homogeneous question-answering setting. | [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663) |
| E03 | BEIR found no retrieval approach consistently strongest on every included dataset. | [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663) |
| E04 | TREC pooling combines top results from multiple runs for relevance assessment. | [How to TREC](https://trec.nist.gov/howto.html) |
| E05 | Traditional pooled evaluation often scores unjudged documents as nonrelevant. | [Overview of TREC 2021](https://trec.nist.gov/pubs/trec30/papers/Overview-2021.pdf) |
| E06 | BEIR's manual TREC-COVID hole annotation increased measured scores for non-lexical approaches. | [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663) |
| E07 | A TREC-8 study found near-identical system rankings after adding relevance judgments for modern neural retrieval results. | [Can Old TREC Collections Reliably Evaluate Modern Neural Retrieval Models?](https://arxiv.org/abs/2201.11086) |
| E08 | BEIR selected nDCG because it accommodates binary and graded relevance while respecting rank. | [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663) |
| E09 | trec_eval reciprocal rank measures the first relevant retrieved document and suits a user needing one result. | [trec_eval reciprocal-rank implementation](https://github.com/usnistgov/trec_eval/blob/main/m_recip_rank.c) |
| E10 | TREC separates the development period from evaluation data released without relevance labels. | [How to TREC](https://trec.nist.gov/howto.html) |
| E11 | Recall divides retrieved relevant items by all relevant items; precision and recall ignore their order. | [Common Evaluation Measures](https://trec.nist.gov/pubs/trec15/appendices/CE.MEASURES06.pdf) |
| E12 | Smucker et al. found significance tests disagreed more as topic samples shrank from 50 toward 10. | [Agreement Among Statistical Significance Tests for Information Retrieval Evaluation at Varying Sample Sizes](https://ciir-publications.cs.umass.edu/getpdf.php?id=885) |
| E13 | BEIR's TREC-COVID hole assessors did not know which retrieval system supplied each judged result. | [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663) |
| E14 | NIST requires the document collection and relevance-judgment set to match when evaluating a run. | [TREC Data: English Relevance Judgements](https://trec.nist.gov/data/reljudge_eng.html) |
| E15 | Upadhyay et al. report successful LLM hole filling in simulations that remove relevance judgments from three TREC DL datasets. | [LLMs Can Patch Up Missing Relevance Judgments in Evaluation](https://arxiv.org/abs/2405.04727) |
| E16 | Soboroff argues that model-generated relevance labels make the model's judgments the evaluation target, limiting the evaluation's validity. | [Don't Use LLMs to Make Relevance Judgments](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958495) |
| E17 | The TREC 2024 RAG assessment study found UMBRELA-based system rankings highly correlated with manual rankings across 77 submitted runs. | [A Large-Scale Study of Relevance Assessments with Large Language Models: An Initial Look](https://arxiv.org/abs/2411.08275) |
| E18 | ALCE evaluates generated text on separate fluency, correctness, and citation-quality dimensions. | [Enabling Large Language Models to Generate Text with Citations](https://arxiv.org/abs/2305.14627) |
| E19 | RAGAS separates relevant focused retrieval, faithful use of context, and generation quality as distinct evaluation dimensions. | [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) |
| E20 | MultiHop-RAG includes queries, answers, and supporting evidence so evidence retrieval and reasoning given evidence can be evaluated separately. | [MultiHop-RAG: Benchmarking Retrieval-Augmented Generation for Multi-Hop Queries](https://arxiv.org/abs/2401.15391) |
| E21 | Bruch et al. reduce evaluation cutoff for small corpora because recall at 1000 approaches one across methods. | [An Analysis of Fusion Functions for Hybrid Retrieval](https://arxiv.org/html/2210.11934v2) |
| E22 | The original BEIR neural retrieval experiments use only the first 512 word pieces of each document. | [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models](https://arxiv.org/html/2104.08663) |

### Disagreements and edge cases

Pooling has conditional evidence on both sides. BEIR's additional TREC-COVID annotations improve the measured standing of non-lexical systems; the TREC-8 neural rejudgment study finds nearly unchanged system ordering. Audit the local judgment pool and unjudged rate rather than treating all old pools as biased or all missing labels as harmless. [BEIR](https://arxiv.org/html/2104.08663), [TREC-8 study](https://arxiv.org/abs/2201.11086).

LLM relevance assessment has an unresolved disagreement between measurement validity and empirical run-ranking agreement. Soboroff argues that a model-created target limits what the evaluation can establish. Upadhyay and colleagues report favorable simulated hole filling and later in-situ TREC results. The latter is stronger evidence than a simulation alone, but it measures run-level agreement under that collection's protocol. It does not verify individual labels or task-specific errors in this project. [Validity argument](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958495), [hole-filling study](https://arxiv.org/abs/2405.04727), [in-situ study](https://arxiv.org/abs/2411.08275).

Recommended inference: use human judgments as the local held-out reference. If automated judging helps expand a pool, preserve its labels separately, measure agreement by task and disputed case type, and report sensitivity to human-only judgments. Do not merge an automatic score into the human reference without labeling the change.

### Project task strata and judgments

| Project task | Judgment target | Primary proposed measures | Required negative or difficult cases |
|---|---|---|---|
| Exact concept, symbol, or claim | Correct stable record and requested version | Success@1 and MRR@10; wrong-version rate | Punctuation, case, aliases, identical titles, near-identical symbols |
| Rephrased concept question | Relevant evidence despite vocabulary mismatch | nDCG@10 and evidence Recall@K | Synonyms, abbreviations, same words with a different meaning |
| Multi-concept or multi-evidence question | Every required evidence group, including bridge evidence | Evidence-group recall and complete-set success within the context budget | One excellent hit with missing other required evidence |
| Conflict, supersession, or freshness question | Both relevant positions, provenance, and applicable version | Conflict-pair coverage, correct-current-version rate, harmful stale-selection rate | High-overlap stale claims and mirrored assertions |
| Discover missing coverage | Useful absence finding or justified abstention | Human-reviewed gap precision, false-gap rate, abstention quality | Relevant material with different names, evidence genuinely absent |

These metrics and strata are project proposals rather than published project results. A multi-evidence item should permit alternate valid evidence sets. Separate “supports the answer,” “mentions the topic,” “contradicts the answer,” and “superseded but relevant to the question” in the assessor rubric. Relevance is task-dependent; a contradictory record can be necessary evidence.

### Evaluation protocol and confound controls

1. Assemble topics from real project work plus independently authored difficult cases. Preserve the topic family's identity; keep paraphrases and near-duplicate information needs in the same development or held-out split. Record the intended task before reviewing system output.
2. Freeze corpus snapshot hashes, retrieval units, publication exclusions, source versions, query text, tokenizer, and judgments. Verify that every judged ID resolves to the same frozen text. Add an explicit no-answer stratum.
3. Pool candidate results from exact, lexical, and available replayed semantic channels. Randomize presentation and hide the producing system. Double-assess a calibration subset and disputed labels; retain disagreement before adjudication. Track the unjudged fraction at each evaluation cutoff.
4. Tune candidate depth, fusion constants/weights, filters, and context selection only on development topics. Test once on held-out topic families. Report per-query and per-stratum deltas as well as an aggregate weighted to the observed task mix.
5. Isolate changes: fixed corpus and chunks for retrieval algorithms; fixed retrievers and candidate union for fusion; fixed candidate pool for reranking; fixed ranked list and token budget for context packing; fixed context/model/prompt for generation. Vary the embedding model only as its own later treatment. The embedding pause remains in force.
6. Report Success@1/MRR for lookup, nDCG for graded ordering, judged evidence recall for candidate sets, and complete evidence-set success for multi-evidence tasks. Report citation entailment and coverage, answer correctness, and appropriate abstention separately. Explain the relevance gain mapping, tie handling, and zero-relevant-topic treatment used by the evaluator.
7. Report paired topic-level uncertainty and the full delta distribution. Choose the smallest useful improvement before testing. Small strata need more independent topics before strong conclusions; bootstrap or a low p-value does not create new independent information. Use a paired randomization check for the primary metric and document the test implementation.
8. Measure p50/p95/p99 latency, cold and warm cache, evaluation and indexing cost, per-query model calls, index bytes, and maintenance effort on fixed hardware/concurrency. Record all changed inputs, including preprocessing and document truncation.

While the pause persists, perform lexical experiments and offline rank-list replay without new embeddings. Semantic end-to-end tests, embedding-dependent evaluation metrics, and the cosine reranker must be marked NOT-RUN rather than silently activated.

### Decision thresholds and remaining uncertainty

Before any candidate promotion, choose a minimum useful quality gain, resource ceiling, and allowed regression tolerance per important task. A proposal is successful only if held-out uncertainty and failure review support the gain and exact/current-version tasks stay within tolerance. Avoid universal numeric thresholds borrowed from another benchmark.

The first practical gate should reject identity defects, incompatible corpus/qrels, train/test leakage, and unsupported citations. A later experiment can decide whether BM25, hybrid fusion, different chunks, or a new embedding model earns its maintenance cost. This ordering is a project inference; no full relevance benchmark has yet run.

What would change the recommendation: existing trustworthy task-stratified judgments that already cover these cases; sufficient evidence that the task mix is materially different; or a judge validation showing reliable local labels across hard strata and contradictory/temporal evidence.

## Depth accounting and provenance

Pass0 reused the local RAG skill, the existing Atlas fusion/BM25 concept pack, the shared source library, and primary-source scouting. Ten atomic claims per concept were written before the six explicit deepening passes. Unsourced universal skill defaults and lift numbers were rejected as facts.

| Deepening pass | Fusion new / total | Fusion novelty | Evaluation new / total | Evaluation novelty |
|---|---:|---:|---:|---:|
| 1 | 2 / 12 | 16.67% | 2 / 12 | 16.67% |
| 2 | 1 / 13 | 7.69% | 2 / 14 | 14.29% |
| 3 | 1 / 14 | 7.14% | 3 / 17 | 17.65% |
| 4 | 1 / 15 | 6.67% | 2 / 19 | 10.53% |
| 5 | 2 / 17 | 11.76% | 1 / 20 | 5.00% |
| 6 | 4 / 21 | 19.05% | 2 / 22 | 9.09% |

Verdict for both concepts: **BUDGET_EXHAUSTED** at maxPasses=6. Two consecutive rates strictly below 5% were not observed. The increase in the final fusion pass reflects newly discovered adaptive-depth evidence, not a saturated concept. One or two more targeted passes on adaptive-depth assumptions and on temporal/contradiction judgment design would likely remain useful.

Every pass considered the six rabbithole questions against the standing claim inventory. Private ledgers retain the reviewed IDs, question-specific follow-ups, literal search queries, newly retained IDs, and source-read outputs. Source bodies and exact support material remain private.

Fusion evidence covers the original Waterloo/Google research, Pinecone/Berkeley fusion research, Elastic's own experiment and implementation, OpenSearch's own experiment, Microsoft's implementation, and a separate adaptive-depth author. Evaluation evidence covers NIST protocols and studies, UKP's BEIR work, the statistical-testing author group, Princeton's ALCE work, RAGAS authors, and MultiHop-RAG authors. Mirrors and multiple URLs from the same group are not counted as independent origins. The joint UMBRELA study overlaps NIST/BEIR author networks and is not an additional independent confirmation of those groups.

Adjacent follow-up queue: evidence-set identity and source-diverse context selection; temporal relevance and contradiction rubrics; query-intent routing; cross-encoder evaluation; and adaptive exact fusion's exhaustive fallback cost. These are handed back to the family map and do not increase the two concepts' claim counts.

