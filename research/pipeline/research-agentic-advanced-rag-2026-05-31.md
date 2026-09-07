# Agentic & Advanced RAG Patterns (beyond naive RAG, 2024-2026)

**Research date:** 2026-05-31
**Scope:** The advanced and agentic patterns layered on top of naive top-k RAG — query transformation, retrieval/ranking, advanced indexing/chunking, agentic RAG (Self-RAG / CRAG / Adaptive-RAG / routing), GraphRAG, RAG evaluation, multimodal RAG, and the long-context-vs-RAG debate.
**Scope boundary:** Base RAG mechanics and vector-DB internals (HNSW/IVF, embedding models) are covered by existing `ai-datastores` and `mongodb-search-ai` references. This report deliberately stays at the *orchestration / retrieval-quality / agentic* layer and cross-references the datastore layer rather than duplicating it.

---

## Overview

"Naive RAG" — embed query, retrieve top-k chunks by cosine similarity, stuff into a single LLM call — was the dominant 2023 pattern and remains the strawman that every 2024-2026 advance is measured against. The defining 2024 paper is Barnett et al., *Seven Failure Points When Engineering a Retrieval Augmented Generation System* (CAIN 2024, arXiv:2401.05856), an experience report across three domains (research, education, biomedical) that enumerates where naive RAG breaks: (1) missing content, (2) missed top-ranked documents, (3) not-in-context (consolidation/reranking failure), (4) not-extracted (answer present but LLM misses it), (5) wrong format, (6) incorrect specificity, (7) incomplete answers. The paper's central lesson — "RAG quality is dominated by retrieval, and retrieval quality can only be validated operationally, not at design time" — frames the whole field.

The field has since organized into a rough maturity ladder, popularized by the *Modular RAG* framing and the agentic-RAG survey (Singh et al., arXiv:2501.09136):

- **Naive RAG** — keyword/dense top-k, single retrieve-then-read pass, no awareness of retrieval quality.
- **Advanced RAG** — pre-retrieval (query transformation, better chunking) and post-retrieval (reranking, compression) optimizations bolted onto a still-static pipeline.
- **Modular RAG** — composable, reconfigurable pipelines; hybrid retrieval; tool integration; routing.
- **Agentic RAG** — an LLM agent treats retrieval as a *tool* it can invoke iteratively, decides *whether/what/when* to retrieve, critiques results, and loops — replacing the static pipeline with autonomous control flow.

Two macro-debates run through 2024-2026: (a) **long-context vs RAG** — whether 1M-token windows make retrieval obsolete (consensus: no, for cost/latency/recall reasons; the frontier is *routing between* them); and (b) **eval-free vs evaluated RAG** — the field's strongest recurring lesson is that ~80% of failures trace to the ingestion/chunking/retrieval layer and are invisible without a measurement harness (Ragas and friends).

---

## Core Concepts

### 1. Naive-RAG failure points (the baseline problem)
Barnett et al.'s seven failure points are the canonical taxonomy. Practically, basic top-k underperforms because: embeddings collapse a chunk to one vector and lose exact terms (BM25 territory); fixed-size chunking severs semantic units; a single query phrasing under-recalls; no reranking means the LLM gets noise mixed with signal; and the "lost-in-the-middle" positional bias means even retrieved-and-supplied context can be ignored if buried mid-prompt. Chroma's 2025 "context rot" research reinforced that *more* retrieved context past ~8K tokens often *degrades* answers — precision beats volume.

### 2. Query transformation (pre-retrieval)
The user's literal query is rarely the optimal retrieval query. Major techniques:
- **Query rewriting** — LLM rephrases for retrieval (fix typos, expand acronyms, add context from chat history).
- **Decomposition / sub-questions** — break a complex multi-part question into atomic sub-queries, retrieve for each, synthesize. Tackles *structural* complexity.
- **Step-back prompting** (Google DeepMind, Zheng et al. 2023/2024) — generate a more abstract "step-back" question first to retrieve broader principles, then answer the specific. Tackles *informational* complexity; complementary to decomposition.
- **HyDE (Hypothetical Document Embeddings)** (Gao et al. 2022, widely adopted 2024) — have the LLM hallucinate an *answer* document, embed *that*, and retrieve neighbors. Works because a hypothetical answer lives closer in embedding space to real answer-documents than the question does. Strong in zero-shot/no-labeled-data settings.
- **Multi-query / RAG-Fusion** (Rackauckas, arXiv:2402.03367) — generate 3-5 query variants, retrieve for each, then merge with **Reciprocal Rank Fusion (RRF)**: each doc scored by sum of `1/(k + rank)` across result lists, so docs appearing high in multiple lists win. RRF is fusion-agnostic (no score normalization needed) and is also the standard merge for hybrid search.

### 3. Retrieval & ranking (post-retrieval)
- **Hybrid search (BM25 + dense)** — combine lexical (exact-term, rare tokens, IDs, code) with semantic (paraphrase, concept) retrieval; merge via RRF or weighted scores. The recurring production finding: BM25 rescues recall on exact-term queries the dense model ranked too low. This is the single highest-leverage upgrade over naive dense-only RAG.
- **Re-ranking** — a two-stage pattern: retrieve a wide candidate set (e.g., top 20-100), then rescore with a more expensive model and keep the top few:
  - **Cross-encoders** (e.g., BGE-reranker, Cohere Rerank v3.5, Jina) — jointly encode (query, doc) in one forward pass for highest quality; slow, so used only on small candidate sets. Reported 15-30% retrieval-accuracy lift over embedding-only.
  - **ColBERT / late interaction** — store a per-token embedding and compute MaxSim between query and doc tokens; sits between bi-encoders and cross-encoders on the speed/quality curve. Trade-off: per-token vectors inflate index size 1-2 orders of magnitude.
  - **Cohere Rerank** — popular managed cross-encoder API that drops on top of any first-stage retriever.
- **MMR (Maximal Marginal Relevance)** — diversity-aware selection: greedily pick chunks that are relevant *and* dissimilar to already-selected ones, reducing redundancy in the context window.

### 4. Advanced indexing / chunking
The core insight: the chunk you *match on* need not be the chunk you *feed the LLM*. Decouple them.
- **Parent-document / small-to-big** — embed small child chunks for precise matching, but return the larger parent chunk for context.
- **Sentence-window** — retrieve a single sentence, then return a window of N surrounding sentences.
- **Auto-merging / hierarchical** (LlamaIndex `AutoMergingRetriever`, `HierarchicalNodeParser`) — build a leaf→parent tree; match on leaves; if enough sibling leaves under one parent are retrieved, merge up and return the parent.
- **Semantic chunking** (LlamaIndex `SemanticSplitterNodeParser`) — split at points where consecutive-sentence embedding distance spikes, so chunks align to topic boundaries instead of arbitrary token counts. Recursive/structure-aware chunking is the recommended *default* for heterogeneous corpora.
- **Anthropic Contextual Retrieval** (Sept 2024) — the standout 2024 technique. Before embedding/indexing each chunk, prepend a 50-100 token LLM-generated blurb situating it in the whole document ("Contextual Embeddings"), and build a parallel **Contextual BM25** index over the same enriched chunks. Generated cheaply with Claude Haiku + prompt caching (~$1.02 per million doc tokens). Reported top-20 retrieval-failure reductions: contextual embeddings alone **−35%** (5.7%→3.7%); + contextual BM25 **−49%** (→2.9%); + reranking **−67%** (→1.9%). Anthropic's own guidance: under ~200K tokens just put the whole KB in the prompt with caching; use Contextual Retrieval above that.

### 5. Agentic RAG (retrieval as a tool, iterative control)
The shift from a fixed pipeline to an agent that *decides*. Singh et al.'s survey (arXiv:2501.09136) grounds it in four agentic primitives — **reflection, planning, tool use, multi-agent collaboration** — and a 7-pattern taxonomy: single-agent router, multi-agent, hierarchical, corrective, adaptive, graph-based, and agentic document workflows. The three load-bearing named systems:
- **Self-RAG** (Asai et al., ICLR 2024 Oral, arXiv:2310.11511) — *trains* the LM to emit **reflection tokens**: a `Retrieve` decision token, plus critique tokens `IsREL` (is the passage relevant), `IsSUP` (is the generation supported by it), `IsUSE` (is the output useful). The model learns *when* to retrieve and to self-critique on-demand. Lowest hallucination rate in several 2025 comparisons.
- **Corrective RAG / CRAG** (Yan et al., 2024, arXiv:2401.15884) — a lightweight **retrieval evaluator** grades retrieved docs and routes to one of three actions: *correct* (use as-is, with knowledge refinement/decompose-recompose), *incorrect* (discard and fall back to **web search**), or *ambiguous* (blend both). Self-healing retrieval; model-agnostic, bolts onto any RAG.
- **Adaptive-RAG** (Jeong et al., NAACL 2024, arXiv:2403.14403) — a trained **complexity classifier** routes each query to *no retrieval* (model knows it), *single-step retrieval* (simple factoid), or *iterative multi-step retrieval* (multi-hop). Optimizes the cost/accuracy trade-off by not over-spending on easy queries.
- **Iterative / multi-hop retrieval** — patterns like IRCoT and FLARE interleave reasoning and retrieval, retrieving again as the chain-of-thought reveals new sub-questions.
- **Routing** — at the front door, classify the query and send it to the right index, tool, or whole pipeline (vector vs graph vs SQL vs web). The backbone of single-agent-router and adaptive patterns.

### 6. GraphRAG (knowledge-graph-augmented retrieval)
**Microsoft GraphRAG** (Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*, arXiv:2404.16130; OSS on GitHub) addresses naive RAG's blindness to *global* "sense-making" questions ("what are the main themes across this corpus?"). Pipeline: LLM extracts an entity-relationship **knowledge graph** from the corpus → community detection (Leiden) builds a hierarchy of clusters → LLM generates **community summaries** bottom-up. At query time, **global search** map-reduces over community summaries; **local search** traverses entity neighborhoods. Reported ~50-70% comprehensiveness gains over vector RAG on global questions. Later work (dynamic community selection) cut global-search token cost. Hybrid graph+vector (e.g., Agent-G, GeAR) combines structured KG traversal with unstructured chunk retrieval, and is the practical sweet spot — graph for multi-hop/global, vector for fuzzy local lookups.

### 7. RAG evaluation
The discipline that converts RAG from vibes to engineering. **Ragas** is the de-facto framework, splitting metrics by stage:
- **Retrieval:** *Context Precision* (are retrieved chunks relevant / ranked well), *Context Recall* (did we retrieve everything needed — requires ground-truth), *Context Entities Recall*, *Noise Sensitivity*.
- **Generation:** *Faithfulness* (is every claim grounded in retrieved context — the primary hallucination guard), *Answer/Response Relevancy*, *Factual Correctness*, *Semantic Similarity*.
- Most metrics are **LLM-as-judge**, requiring no labels except Context Recall and reference-based ones. Practical guidance: start with **Faithfulness** (catches hallucination) and **Context Recall** (tells you if retrieval architecture is fundamentally sound). Build a **golden-context set** (queries + ideal contexts + answers) to regression-test pipeline changes. Separating *retrieval* eval from *generation* eval is essential — it localizes whether a bad answer is a retrieval miss or a generation failure.

### 8. Multimodal RAG
Real documents mix text, tables, figures, and layout. Two families:
- **Caption-and-embed** — run images/tables through a VLM to produce text descriptions, then embed those (simple, lossy).
- **Vision-native / late-interaction over pages** — **ColPali** (Faysse et al., arXiv:2407.01449) embeds *rendered document-page images* directly via a VLM (PaliGemma) into ColBERT-style multi-vectors, skipping OCR/layout parsing entirely. Strong on visually-rich docs (charts, scanned PDFs). Cost: ~100× more vectors per page, so retrieval-speed/index-size is the open concern. Successors: ColQwen2, ColSmol.

### 9. Long-context vs RAG (the live debate)
With 1M-token (Gemini) and 200K-token (Claude) windows, "RAG is dead" was a 2024 talking point. The 2024-2026 evidence settled it as *nuanced*:
- Long-context LLMs *can* outperform RAG on accuracy when the whole corpus fits — but at ~30-60× latency and up to ~1,000-1,250× per-query cost, and with degradation past a model-specific length ("lost in the middle" / context rot; average multi-fact recall around 60% in some studies).
- RAG stays indispensable for large/dynamic corpora, cost-sensitive and low-latency serving, freshness, and source attribution.
- **Synthesis (the 2025 consensus):** *route* — simple/local queries → RAG; complex/global/multi-hop → long-context or GraphRAG. The two are complements, and "RAG → Context Engineering" is the reframing of late 2025: RAG is one tool in a broader context-assembly discipline.

---

## Tools / Frameworks

- **Orchestration:** LangChain / LangGraph (agentic RAG graphs, CRAG/Self-RAG/Adaptive-RAG reference implementations), LlamaIndex (chunking node-parsers, auto-merging/sentence-window retrievers, query engines, agentic workflows), Haystack, DSPy (programmatic/optimized RAG pipelines).
- **Indexing / vector + hybrid:** Weaviate, Qdrant, Milvus/Zilliz, Elasticsearch/OpenSearch (BM25 + dense + RRF), pgvector, **MongoDB Atlas Vector Search + $search** (hybrid via `$rankFusion`/RRF) — see `ai-datastores` / `mongodb-search-ai` for the datastore layer.
- **Re-ranking:** Cohere Rerank (v3.5), BGE-reranker, Jina Reranker, ColBERT/RAGatouille, Voyage rerank.
- **Contextual Retrieval:** Anthropic cookbook implementation (Claude Haiku + prompt caching); ports in Together AI, Instructor.
- **GraphRAG:** Microsoft GraphRAG (OSS), Neo4j + LLM KG builder, LlamaIndex PropertyGraphIndex.
- **Multimodal:** ColPali / ColQwen2 (illuin-tech, nomic-ai forks), VLM captioning pipelines.
- **Evaluation:** **Ragas** (primary), TruLens, DeepEval, Arize Phoenix, LangSmith eval, Chroma's context-rot benchmarks.

---

## Practical Patterns

1. **Default production stack:** hybrid (BM25 + dense) retrieval → RRF fusion → cross-encoder rerank → top-3-5 chunks, kept under ~8K assembled tokens. This alone fixes most of Barnett's failure points 2-3.
2. **Decouple match-chunk from context-chunk:** embed small (children/sentences), serve large (parents/windows/auto-merged). Removes the "precise-but-fragmented vs complete-but-vague" trade-off.
3. **Add context before you embed:** Contextual Retrieval (LLM-generated chunk blurbs) + Contextual BM25 — cheap with prompt caching, −49% retrieval failures, −67% with rerank.
4. **Transform the query, not just the index:** rewrite + decompose + (HyDE for zero-shot / step-back for abstraction). Multi-query + RRF when recall is the bottleneck.
5. **Make retrieval a tool, then let the agent loop:** CRAG-style grade-and-fallback (web search on poor retrieval), Adaptive-RAG complexity routing to avoid over-retrieving easy queries, Self-RAG-style self-critique on faithfulness.
6. **Use GraphRAG for global/sense-making questions; keep vector RAG for local lookups; hybridize.**
7. **Route long-context vs RAG by query type and corpus size; never assume one wins.** Under ~200K tokens, consider just prompt-stuffing with caching.
8. **Evaluate continuously:** golden-context set + Ragas (Faithfulness + Context Recall first); measure *retrieval* and *generation* separately so you know which half to fix.
9. **Order context deliberately:** put strongest evidence at the start and end of the prompt to dodge lost-in-the-middle.

---

## Anti-Patterns

- **Eval-free RAG** — shipping without a retrieval/generation measurement harness; you can't tell if a chunking/embedding/rerank change helped. The field's #1 mistake.
- **Dense-only, no lexical** — skipping BM25/hybrid; silently under-recalls exact terms, IDs, codes, rare names.
- **No re-ranking** — feeding raw top-k embeddings to the LLM; noise dilutes signal (rerank lifts accuracy 15-30%).
- **Over-chunking / fixed-size chunking** — splitting every N tokens, severing sentences and semantic units; ~80% of RAG failures originate in the ingestion/chunking layer.
- **Context stuffing / "more is better"** — dumping 50K tokens of retrieved text; degrades answers past ~8K (context rot) and triggers lost-in-the-middle.
- **Lost-in-the-middle ignorance** — placing key evidence mid-prompt and assuming the model reads it.
- **Treating naive top-k as sufficient** — ignoring all seven of Barnett's failure points and blaming the LLM for retrieval defects.
- **Assuming long context kills RAG** — paying ~1000× cost/latency to stuff a corpus that a routed RAG path would answer cheaper and often more accurately.
- **Unbounded agentic loops** — agentic RAG without iteration caps / cost guardrails; reflection and multi-hop can spiral.

---

## Suggested sub-concepts (future child concepts)

1. Naive-RAG failure taxonomy & "context rot" / lost-in-the-middle
2. Query transformation (rewrite, decomposition, HyDE, step-back, multi-query/RAG-Fusion + RRF)
3. Hybrid search & re-ranking (BM25+dense, cross-encoders, ColBERT late interaction, Cohere Rerank, MMR)
4. Advanced indexing/chunking (parent-document, sentence-window, auto-merging, semantic chunking, Anthropic Contextual Retrieval)
5. Agentic RAG control (retrieval-as-tool, Self-RAG, CRAG, Adaptive-RAG, iterative/multi-hop, routing)
6. GraphRAG & knowledge-graph-augmented retrieval (community summarization, hybrid graph+vector)
7. RAG evaluation (Ragas, retrieval-vs-generation eval, golden-context sets)
8. Multimodal RAG (ColPali / vision-native page retrieval) + long-context-vs-RAG routing

---

## References (with URLs)

**Primary papers (arXiv / conference):**
- Barnett et al., *Seven Failure Points When Engineering a RAG System* (CAIN 2024) — https://arxiv.org/abs/2401.05856
- Singh et al., *Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG* — https://arxiv.org/html/2501.09136v4
- Asai et al., *Self-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection* (ICLR 2024) — https://arxiv.org/pdf/2310.11511 ; project: https://selfrag.github.io/ ; code: https://github.com/AkariAsai/self-rag
- Yan et al., *Corrective Retrieval Augmented Generation (CRAG)* — https://arxiv.org/abs/2401.15884
- Jeong et al., *Adaptive-RAG* (NAACL 2024) — https://arxiv.org/abs/2403.14403
- Rackauckas, *RAG-Fusion: a New Take on Retrieval-Augmented Generation* — https://arxiv.org/abs/2402.03367 ; code: https://github.com/Raudaschl/rag-fusion
- Edge et al. (Microsoft), *From Local to Global: A Graph RAG Approach to Query-Focused Summarization* — https://arxiv.org/abs/2404.16130
- Faysse et al., *ColPali: Efficient Document Retrieval with Vision Language Models* — https://arxiv.org/abs/2407.01449
- *Long Context vs. RAG for LLMs: An Evaluation and Revisits* — https://arxiv.org/html/2501.01880v1
- *A Survey of RAG-Reasoning Systems in LLMs* — https://arxiv.org/pdf/2507.09477
- *Reasoning RAG via System 1 or System 2 (industry survey)* — https://arxiv.org/html/2506.10408v1

**Vendor / authoritative:**
- Anthropic, *Introducing Contextual Retrieval* — https://www.anthropic.com/news/contextual-retrieval
- Anthropic, *Contextual embeddings cookbook* — https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide
- Microsoft Research, *GraphRAG announcement* — https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/
- Microsoft Research, *GraphRAG: dynamic community selection* — https://www.microsoft.com/en-us/research/blog/graphrag-improving-global-search-via-dynamic-community-selection/ ; docs: https://microsoft.github.io/graphrag/
- Ragas metrics docs — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/
- ColPali repos — https://github.com/illuin-tech/colpali ; https://huggingface.co/blog/manu/colpali
- Databricks, *Long Context RAG Performance of LLMs* — https://www.databricks.com/blog/long-context-rag-performance-llms
- Weaviate, *RAG and GraphRAG* — https://weaviate.io/blog/graph-rag ; *Chunking strategies* — https://weaviate.io/blog/chunking-strategies-for-rag

**Practitioner / framework / synthesis:**
- LlamaIndex / Sophia Yang, *Advanced RAG 01: Small-to-Big Retrieval* — https://medium.com/data-science/advanced-rag-01-small-to-big-retrieval-172181b396d4
- Towards Data Science, *Advanced RAG Retrieval: Cross-Encoders & Reranking* — https://towardsdatascience.com/advanced-rag-retrieval-cross-encoders-reranking/
- Towards Data Science, *Hybrid Search and Re-Ranking in Production RAG* — https://towardsdatascience.com/hybrid-search-and-re-ranking-in-production-rag/
- dmflow, *Six Advanced Query Transformation Architectures* — https://www.dmflow.chat/en/blog/rag-query-transformation-guide-6-advanced-architectures
- RAGFlow, *From RAG to Context: a 2025 year-end review* — https://ragflow.io/blog/rag-review-2025-from-rag-to-context
- PremAI, *Building Production RAG (2026 Guide)* — https://blog.premai.io/building-production-rag-architecture-chunking-evaluation-monitoring-2026-guide/
- Qdrant, *Best Practices in RAG Evaluation* — https://qdrant.tech/blog/rag-evaluation-guide/
- AgenticRAG-Survey (asinghcsu) — https://github.com/asinghcsu/AgenticRAG-Survey
- TianPan, *Long-Context vs RAG production decision framework* — https://tianpan.co/blog/2026-04-09-long-context-vs-rag-production-decision-framework
