---
title: "Recommender Systems and Learning-to-Rank Analytics"
description: "A recommender system predicts, for each user, which items from a (often huge) catalog they are most likely to engage with, then orders a small slate to show. As a data-analysis discipline it sits at t"
---

# da-38 — Recommender Systems & Learning-to-Rank Analytics

## Overview

A **recommender system** predicts, for each user, which items from a (often huge) catalog they are most likely to engage with, then **orders** a small slate to show. As a data-analysis discipline it sits at the intersection of three problems: (1) *modeling* preference from sparse interaction data, (2) *ranking* candidates under a relevance objective, and (3) *evaluating* both offline and online while fighting the bias the system itself creates.

**Scope boundaries (read first):**

- **vs da-7 (machine learning):** da-7 covers generic supervised/unsupervised model training, regularization, and hyperparameter tuning. da-38 covers the *recommendation- and ranking-specific* objectives (BPR/WRMF losses, NDCG-aware LambdaMART), the retrieve-then-rank funnel, and recsys evaluation. Use da-7 for "train a classifier"; use da-38 for "rank items for a user."
- **vs da-27 (network/graph analytics):** da-27 owns graph structure metrics (centrality, community detection, link prediction *as graph analysis*, GNNs as graph models). da-38 references GNN-for-recsys and bipartite user-item graphs only at the *recommendation* level; graph-structure questions belong to da-27.
- **vs da-12 (A/B testing & causal inference):** da-12 owns general experiment design and causal estimators. da-38 owns the *recsys-specific* online-eval wrinkles: interleaving, feedback-loop confounding, and off-policy/counterfactual evaluation (IPS, doubly-robust) of a ranking policy.
- **vs rag-architecture / vector search:** semantic retrieval with no personalization or ranking-quality objective is RAG; ranked personalization is da-38.

## Core Concepts

### 1. Problem framing: feedback, the feedback loop, and cold-start
- **Explicit vs implicit feedback.** *Explicit* = ratings/likes (sparse, signed). *Implicit* = clicks, views, dwell, purchases (abundant but **positive-only and ambiguous** — a non-click is not a dislike). Implicit dominates production and forces *positive-unlabeled* modeling: model **confidence** that an interaction is a preference, not a rating value.
- **Popularity bias & the feedback loop.** A deployed recommender only logs feedback on items it *showed*, chosen because they scored high — so the next training set over-represents popular/previously-recommended items (**exposure bias**). Unchecked, a self-reinforcing loop narrows the catalog and creates **filter bubbles**. Breaking it needs exploration and/or de-biasing (propensity weighting).
- **Cold-start, three flavors.** *User* (new user), *item* (new item), *system* (brand-new product). Mitigations: content/side features, hybrid models, factorization machines, popularity fallbacks, bandit exploration, and (2025-26) LLM/semantic-ID content grounding for long-tail items.

### 2. Collaborative filtering (CF) — neighborhood methods
CF predicts preference purely from the user-item interaction matrix, no content.
- **User-user CF:** find similar users (cosine/Pearson on co-rated items). Sensitive to sparsity; similarities go stale.
- **Item-item CF:** precompute item-item similarity ("users who interacted with X also interacted with Y"). More stable than user-user, scales better, Amazon's production workhorse, still a strong baseline.
- **Limitations:** cold-start, sparsity, popularity skew, no side features — motivating latent-factor models.

### 3. Matrix factorization (MF)
Factor R ≈ **P·Qᵀ** into low-rank user (P) and item (Q) latent factors; prediction = pᵤ·qᵢ.
- **SVD / funkSVD.** Not literal SVD — learns factors by **SGD on observed entries only** with L2 regularization plus user/item **bias terms**. SVD++ adds implicit signal.
- **ALS.** Fix P, solve Q in closed form, alternate. Parallel → standard for large distributed (Spark) training.
- **Implicit-feedback MF / WRMF (Hu-Koren-Volinsky 2008).** Treat all entries; weight observed interactions by **confidence** cᵤᵢ = 1 + α·rᵤᵢ; fit preference (0/1) with weighted ALS. What `implicit`'s `AlternatingLeastSquares` does.
- **BPR — Bayesian Personalized Ranking (Rendle 2009).** **Pairwise ranking** objective for implicit feedback: maximize σ(x̂ᵤᵢ − x̂ᵤⱼ) over sampled (user, pos, neg) triples. Optimizes ranking (AUC), not rating error — better top-N fit than pointwise MF.

### 4. Content-based, hybrid, and factorization machines
- **Content-based:** recommend items similar to liked ones via item features → good for item cold-start, over-specializes (no serendipity).
- **Hybrid:** combine CF + content (weighted, switching, feature-augmented, cascade). Solves cold-start, keeps collaborative signal.
- **Factorization Machines (FM, Rendle 2010):** model all pairwise feature interactions with low-rank factorized weights — generalizes MF to arbitrary side features, natively handles cold-start. **FFM (field-aware)** gives each feature a latent vector per *field* — strong for CTR. **DeepFM** shares an embedding between a wide FM (low-order) and a deep DNN (high-order), no manual crosses — standard CTR/ranking model.

### 5. Modern deep recommenders
- **Two-tower retrieval.** Separate **user/query tower** and **item tower** into a shared embedding space; relevance = dot product. Item embeddings precomputed and indexed in an ANN/vector store → sub-linear nearest-neighbor lookup → dominant **candidate-generation** architecture (TorchRec's headline target).
- **Neural CF (NCF):** replace the MF dot product with an MLP — more expressive (though a tuned dot product is a strong baseline).
- **Sequential / session-based:** **GRU4Rec** (RNN over session events); **SASRec** (*causal* left-to-right self-attention, next-item); **BERT4Rec** (*bidirectional* self-attention, masked-item cloze training). **Caveat:** with the *same* loss, SASRec generally matches or beats BERT4Rec at lower cost — BERT4Rec's edge often came from its training objective, not bidirectionality.
- **LLM-augmented & generative recommenders (2025-2026).** **Semantic IDs**: quantize an item's content embedding (RQ-VAE) into a short code that reflects content → generalizes to **cold-start/long-tail** and slots into an LLM vocabulary (YouTube, Spotify gains). **Generative retrieval**: an LLM *generates* the next item's semantic ID instead of scoring a candidate set. **LLMs as data augmenters / rerankers** and knowledge-guided RAG (ColdRAG) for cold-start — watch LLM-reranker exposure/coverage issues.

### 6. Learning-to-rank (LTR)
Directly optimize the *order* of a candidate list given relevance labels/features.
- **Pointwise** — predict each item's relevance independently; ignores list context. Weakest ranking fidelity.
- **Pairwise** — learn from item pairs. **RankNet** (neural, pairwise cross-entropy) is the archetype; its loss correlates only loosely with NDCG.
- **Listwise** — optimize the whole list. **ListNet** uses Plackett-Luce permutation probability; **LambdaRank/LambdaMART** weight pairwise gradients by **ΔNDCG**, directly targeting NDCG. **LambdaMART** (LambdaRank gradients + gradient-boosted trees) is the workhorse — XGBoost (`rank:ndcg`), LightGBM, RankLib. Pairwise-vs-listwise is *how the loss treats the list*, not the model family.
- **Retrieval → ranking → re-ranking funnel.** (1) **candidate generation** — cheap, high-recall, millions→hundreds (two-tower+ANN, item-item, popularity); (2) **ranking** — expensive, high-precision scorer (DeepFM/LambdaMART/DLRM); (3) **re-ranking** — business rules, diversity (MMR), freshness, fairness, exploration on the top slate. Each stage trades recall for precision.

### 7. Offline evaluation
Evaluate on held-out interactions (time-based split more honest than random).
- **Accuracy @k:** **Precision@k**, **Recall@k**, **Hit Rate@k**, **MAP** (order-aware), **MRR** (rank of first relevant — best when one correct answer, e.g. next-item), **NDCG@k** (graded, position-discounted — the headline metric). Empirically cluster: {Recall}, {MRR, NDCG, HR}, {Precision, MAP}.
- **Beyond-accuracy:** **Coverage**, **Diversity** (intra-list dissimilarity), **Novelty** (non-popularity), **Serendipity** (relevant *and* surprising). Optimizing accuracy alone degrades these.
- **Offline/online gap.** Offline metrics measure fit to *logged* (biased) behavior. Higher offline NDCG does **not** guarantee online lift; too much novelty can hurt novice users. Treat offline as a *filter*, beware sampled-negative distortion and random-split leakage.

### 8. Online evaluation & off-policy estimation
- **A/B testing** is the gold standard, but recommenders create **feedback loops** that contaminate populations over time — keep tests short, watch novelty/interference.
- **Interleaving** mixes two rankers into one list per user and attributes clicks → far more sensitive than A/B (Airbnb search).
- **Counterfactual / off-policy evaluation (OPE):** **IPS** (weight by 1/propensity — unbiased but high variance, clip it); **Direct Method** (reward model — low variance, biased if misspecified); **Doubly Robust** (DM+IPS — unbiased if *either* model is correct, lower variance; standard for large action spaces).

### 9. Production concerns
- **Two-stage serving** (candidate gen vs ranking); embeddings in a **vector/ANN store**, features in a **feature store** (Feast) shared across train/serve to prevent skew.
- **Real-time features & embeddings:** session/recency features computed at request time; huge embedding tables sharded (TorchRec).
- **Exploration vs exploitation:** **contextual bandits** (LinUCB, **Thompson sampling**) inject controlled exploration to break feedback loops; ε-greedy/random injection in re-ranking mitigates filter bubbles. Caveat (RecSys 2025): in pure offline eval, greedy models often *appear* to beat bandits — a structural eval bias.
- **Fairness & filter bubbles:** monitor provider-side exposure fairness, popularity bias, diversity; randomization/fairness constraints in re-ranking.

## Tools & Frameworks

| Tool | Niche |
| --- | --- |
| **implicit** | Fast WRMF (ALS) + BPR for implicit feedback; Python. Production baseline. |
| **LightFM** | Hybrid FM blending CF + content/metadata; great for cold-start; WARP/BPR losses. |
| **Surprise** | Classic explicit-rating CF (SVD, SVD++, KNN); teaching/prototyping. |
| **TorchRec** | PyTorch lib for large-scale models — sharded embedding tables across GPUs, two-tower/DLRM. |
| **NVIDIA Merlin** (NVTabular, HugeCTR) | End-to-end GPU recsys: feature prep → train retrieval+ranking → Triton serving. |
| **RecBole** | Research framework, 100+ algorithms, unified benchmarking. |
| **Vespa** | Serving engine fusing ANN retrieval + tensor ranking + business logic. |
| **Feast** | Feature store for consistent train/serve features. |
| **Amazon Personalize / Vertex AI Recommendations** | Managed/turnkey — live in weeks, less control. |
| **XGBoost / LightGBM (`rank:*`), RankLib** | LambdaMART / LTR. |

## Methodology
1. **Frame the problem.** Implicit/explicit? Top-N, CTR, or next-item? Decides loss (BPR/WRMF vs pointwise vs LambdaMART) and metric (Recall@k/NDCG vs MRR).
2. **Baseline first.** Popularity + item-item CF + WRMF/BPR — many "deep" wins vanish against a tuned MF baseline.
3. **Split honestly.** Time-based (leave-last-out per user); avoid leakage; beware sampled-negative metrics.
4. **Add structure as needed.** Side features → FM/LightFM/DeepFM; sequence → SASRec; cold-start → content + semantic IDs.
5. **Build the funnel** at scale: two-tower retrieval → DeepFM/LambdaMART ranker → diversity/fairness/exploration re-rank.
6. **Evaluate in layers:** offline → off-policy (IPS/DR) → interleaving → A/B. Never ship on offline alone.
7. **Close the loop safely:** log propensities, add exploration, monitor popularity bias and exposure fairness.

## Anti-Patterns
- **Trusting offline NDCG as ground truth** — confirm online.
- **Treating implicit non-interactions as negatives** — they're unlabeled; use confidence weighting (WRMF) or sampled pairwise negatives (BPR).
- **Random split for sequential/temporal data** — leaks the future.
- **Assuming BERT4Rec > SASRec** — loss, not bidirectionality, drove the gap.
- **Optimizing accuracy only** — tanks coverage/diversity/serendipity and feeds the feedback loop.
- **Raw IPS with no clipping** — variance explodes; clip or use doubly-robust.
- **Deep model with no MF/CF baseline** — can't claim a win without the bar.

## References
- Hu/Koren/Volinsky (2008), *CF for Implicit Feedback Datasets* (WRMF). https://dl.acm.org/doi/10.1145/1864708.1864726
- Rendle et al. (2009), *BPR*. https://arxiv.org/pdf/1205.2618
- He et al. (2016), *Fast MF for Online Recommendation with Implicit Feedback*. https://dl.acm.org/doi/10.1145/2911451.2911489
- Guo et al. (2017), *DeepFM*. https://arxiv.org/pdf/1703.04247
- *Two-Tower Model for Recommendation* (Shaped). https://www.shaped.ai/blog/the-two-tower-model-for-recommendation-systems-a-deep-dive
- Sun et al. (2019), *BERT4Rec*. https://arxiv.org/pdf/1904.06690
- Petrov & Macdonald (2023), *is BERT4Rec really better than SASRec?* https://arxiv.org/pdf/2309.07602
- Spotify Research (2025), *Semantic IDs for Generative Search and Recommendation*. https://research.atspotify.com/2025/9/semantic-ids-for-generative-search-and-recommendation
- *Semantic IDs for Joint Generative Search and Recommendation* (RecSys 2025). https://dl.acm.org/doi/10.1145/3705328.3759300
- ColdRAG (2025). https://arxiv.org/html/2505.20773v2
- *From RankNet to LambdaMART*. https://en.heth.ink/Ranking/
- XGBoost *Learning to Rank*. https://xgboost.readthedocs.io/en/latest/tutorials/learning_to_rank.html
- *Evaluating Recommender Models: Offline vs. Online* (Shaped). https://www.shaped.ai/blog/evaluating-recommender-models-offline-vs-online-evaluation
- *10 metrics to evaluate recommender and ranking systems* (Evidently). https://www.evidentlyai.com/ranking-metrics/evaluating-recommender-systems
- *Widespread Flaws in Offline Evaluation of Recommender Systems* (2023). https://arxiv.org/pdf/2307.14951
- *Interleaving and Counterfactual Evaluation for Airbnb Search Ranking* (KDD 2025). https://arxiv.org/html/2508.00751v1
- *Doubly Robust OPE with Large Action Spaces*. https://www.researchgate.net/publication/372961616
- *Introducing TorchRec* (PyTorch). https://pytorch.org/blog/introducing-torchrec/
- *Recommender Systems: Lessons From Building and Deployment* (Neptune). https://neptune.ai/blog/recommender-systems-lessons-from-building-and-deployment
- *Exploitation Over Exploration* (RecSys 2025). https://dl.acm.org/doi/10.1145/3705328.3748166
