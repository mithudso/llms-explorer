---
title: "Network and Graph Analytics"
description: "Network (graph) analytics models data as nodes (vertices) connected by edges (links) and measures the resulting structure to answer questions that row/column tables cannot: who is influential, what cl"
---

# Network & Graph Analytics

## Overview

Network (graph) analytics models data as **nodes (vertices)** connected by **edges (links)** and measures the resulting structure to answer questions that row/column tables cannot: who is influential, what clusters exist, what is the shortest path, what links are likely to form. It is the analytics counterpart to graph theory — the goal is **insight from relationships**, not just storing them.

Use a graph framing when the *connections* carry the signal: social networks, fraud rings, supply chains, citation/co-authorship, recommendation, knowledge graphs, dependency graphs, transaction flows. If the question is answerable with a `GROUP BY`, you probably do not need a graph.

This skill is the network/graph node of the data-analytics curriculum (da-1 onward).

## Core Concepts

### 1. Graph representations
- **Directed vs undirected**: edges with vs without a direction (following vs friendship). **Weighted vs unweighted**: edges carry a cost/strength.
- **Adjacency matrix**: V×V matrix, O(V²) space, O(1) edge lookup — good for dense graphs and linear-algebra ops (PageRank, spectral methods).
- **Adjacency list**: per-node neighbor lists, O(V+E) space — the default for sparse real-world graphs; faster traversal.
- **Bipartite graph**: two disjoint node sets with edges only across sets (users↔products, authors↔papers).
- **Ego network**: the subgraph of one focal node ("ego"), its direct neighbors ("alters"), and edges among them — the unit of local social-structure analysis.
- **Multigraph / multi-relational**: parallel edges or typed edges (knowledge graphs).

### 2. Connectivity & paths
- **Connected components**: maximal sets of mutually reachable nodes. In directed graphs distinguish **weakly** (ignore direction) vs **strongly** connected components.
- **Shortest paths**: **BFS** for unweighted; **Dijkstra** for non-negative weights (O(E log V) with a heap on an adjacency list); **Bellman-Ford** when negative-weight edges exist (Dijkstra fails on negatives). All-pairs via repeated Dijkstra or Floyd-Warshall.
- **Diameter / eccentricity / average path length**: global reachability measures (expensive on large graphs — sample).

### 3. Centrality (who matters)
- **Degree centrality**: number of edges (in/out for directed) — local popularity, cheap.
- **Betweenness centrality**: fraction of shortest paths passing through a node — bridges/brokers/bottlenecks. Expensive (Brandes ≈ O(VE)); approximate via sampling on big graphs.
- **Closeness centrality**: inverse of mean shortest-path distance to all others.
- **Eigenvector centrality**: recursive importance — you matter if connected to nodes that matter. Can fail to converge on some directed graphs.
- **PageRank**: eigenvector centrality with a damping factor (~0.85) modeling a teleporting random surfer. Handles directed graphs reliably; the production default for influence ranking.

### 4. Community detection (what clusters)
- **Modularity (Q)**: edges-inside-communities vs expected at random, range roughly −1..1; higher = stronger structure.
- **Louvain** (Blondel et al., 2008): fast greedy modularity maximization. Ubiquitous but suffers the **resolution limit** (merges small real communities) and can produce badly/disconnected communities.
- **Leiden** (Traag, Van Eck & Waltman, 2019): adds a refinement phase; guarantees communities are connected and well-separated, faster and higher-quality — the recommended default.
- **Label propagation**: near-linear, no objective — fast but unstable/non-deterministic.
- CPM (constant Potts model) and resolution parameters address the resolution limit.

### 5. Link prediction (what edges will form)
Local proximity scores for non-adjacent pairs x,y (Γ = neighbor set):
- **Common Neighbors**: |Γ(x) ∩ Γ(y)|.
- **Jaccard Coefficient**: |Γ(x) ∩ Γ(y)| / |Γ(x) ∪ Γ(y)|.
- **Adamic-Adar**: sum of 1/log(degree) over shared neighbors — rare shared neighbors count more.
- **Preferential Attachment**: deg(x)·deg(y) — "rich get richer."
Embedding/GNN methods are the supervised upgrade.

### 6. Network motifs & bipartite projection
- **Motifs**: statistically over-represented subgraphs (feed-forward loops, triangles). Compare against a degree-preserving null model.
- **Bipartite (one-mode) projection**: collapse a two-set graph onto one set (two authors linked if they co-wrote a paper). Loses information — weight edges by shared-neighbor count / Newman weighting to avoid hub-dominated dense graphs.

### 7. Graph embeddings (nodes → vectors)
- **DeepWalk** (Perozzi et al., 2014): uniform random walks → skip-gram (Word2Vec) node vectors.
- **node2vec** (Grover & Leskovec, 2016): biased walks with return parameter p and in-out parameter q interpolating BFS-like (structural roles) vs DFS-like (community) exploration. Outperforms DeepWalk/LINE on classification and link prediction. Vectors feed downstream ML.

### 8. GNN basics for analytics
- **GCN** (Kipf & Welling, 2017): neighborhood aggregation via normalized adjacency; transductive — needs the whole graph, retrain on new nodes.
- **GraphSAGE** (Hamilton, Ying & Leskovec, NeurIPS 2017): learns aggregator functions over a sampled neighborhood → inductive, generalizes to unseen nodes, scales to large/dynamic graphs. Use GNNs when you have rich node features + a supervised target; use node2vec when you only have structure.

## Tools / Frameworks

| Tool | Backend | Best for | Notes |
| --- | --- | --- | --- |
| **NetworkX** | pure Python | prototyping, graphs up to ~10⁴–10⁵ nodes | richest API; 40–250× slower than C libs |
| **igraph** | C (Python/R) | medium-large graphs, single machine | fast, mature |
| **graph-tool** | C++/Boost + OpenMP | large graphs, parallel centrality/PageRank | fastest CPU lib when OpenMP enabled; SBM inference |
| **cuGraph (RAPIDS)** | GPU/CUDA | very large graphs, vertex-centric ops | up to ~870× over igraph; ~0.2s PageRank where igraph takes ~60s |
| **Neo4j GDS** | JVM, in-DB | enterprise graphs in a graph DB | 65+ algorithms (PageRank, Louvain, Leiden, node2vec, FastRP, link prediction) |
| **PyG / DGL** | PyTorch | GNN training (GCN, GraphSAGE) | embeddings and supervised graph ML |

Rule of thumb: prototype in NetworkX, move to igraph/graph-tool when slow, cuGraph when huge, Neo4j GDS when the graph already lives in Neo4j.

## Methodology

1. **Frame the question as a graph** — define node, edge, direction, weight. Wrong definition dooms everything downstream.
2. **Build & sanity-check** — node/edge counts, degree distribution (expect heavy tails), components, density. Restrict to the giant component when appropriate.
3. **Match analytic to question**: influence → centrality (PageRank default); clusters → community detection (Leiden default); reachability → components/shortest paths; missing links → link prediction or embeddings.
4. **Scale-match the tool** before running O(VE) measures.
5. **Validate** — compare against a null model; check modularity *and* stability across seeds; for link prediction use a temporal train/test split and AUC/precision@k.
6. **Communicate** — layouts for small graphs only (<~1k nodes); for large graphs report metrics, ranked tables, community summaries — not hairball plots.

## Practical Patterns

- **PageRank as the default influence score** on directed graphs: degree is cheap but naive; betweenness is informative but slow; PageRank is the reliable middle ground.
- **Leiden over Louvain** unless you have a hard dependency on Louvain output.
- **node2vec for structure-only data, GraphSAGE for feature-rich + supervised** targets needing inductive generalization.
- **Work on the giant connected component** — isolates distort global metrics.
- **Approximate expensive centralities** (sampled betweenness/closeness) over ~10⁵ nodes.
- **Weight bipartite projections** rather than using raw co-occurrence.
- **Tune node2vec p/q deliberately**: low q → community-flavored; high q (low p) → structural-role embeddings.

## Anti-Patterns

- **Treating any join table as a graph.** If a `GROUP BY` answers it, a graph adds cost, not insight.
- **Trusting Louvain communities as connected.** Up to ~25% badly connected in the original study. Use Leiden or verify.
- **Ignoring the modularity resolution limit** — don't over-interpret community count without a resolution sweep.
- **Exact betweenness on million-node graphs in NetworkX** — won't finish; sample or use graph-tool/cuGraph.
- **Adjacency matrix for sparse graphs** — O(V²) memory blows up; use adjacency lists.
- **Dijkstra with negative weights** — silently wrong; use Bellman-Ford.
- **Plotting a 100k-node hairball** — summarize with metrics and community-level rollups.
- **Comparing motif/community counts without a null model.**
- **Using transductive GCN on a growing graph** — use GraphSAGE.

## Troubleshooting

- **Eigenvector centrality won't converge** → directed graph with sinks; use PageRank or `eigenvector_centrality_numpy`.
- **Everything is one giant community** → resolution limit; lower the resolution parameter, switch to Leiden/CPM.
- **Community results change every run** → expected for Louvain/label propagation; fix the seed, take consensus, or use Leiden.
- **Centrality job never finishes** → O(VE)-class; sample, restrict to giant component, or move to C/GPU backend.
- **Link prediction AUC ≈ 0.5** → no temporal split (leakage) or too sparse; try embedding features.
- **node2vec embeddings look random** → walks too short/few, or p/q untuned.
- **Out of memory building the graph** → dense matrix; switch to edge list / sparse (CSR) or igraph/cuGraph.

## References

- NetworkX docs — centrality, components, shortest paths, link prediction. https://networkx.org/documentation/stable/ (2024)
- Brandes. "A Faster Algorithm for Betweenness Centrality." J. Math. Sociology (2001).
- Page, Brin et al. "The PageRank Citation Ranking." Stanford (1999).
- Blondel et al. "Fast unfolding of communities in large networks" (Louvain). (2008). https://arxiv.org/abs/0803.0476
- Fortunato & Barthélemy. "Resolution limit in community detection." PNAS (2007). https://arxiv.org/abs/physics/0607100
- Traag, Van Eck & Waltman. "From Louvain to Leiden." Scientific Reports (2019). https://arxiv.org/abs/1810.08473
- Liben-Nowell & Kleinberg. "The Link Prediction Problem for Social Networks." (2007). https://www.cs.cornell.edu/home/kleinber/link-pred.pdf
- Arthur. "Modularity and Projection of Bipartite Networks" (2019). https://arxiv.org/pdf/1908.02520
- Perozzi, Al-Rfou & Skiena. "DeepWalk." KDD (2014).
- Grover & Leskovec. "node2vec: Scalable Feature Learning for Networks." KDD (2016). https://cs.stanford.edu/~jure/pubs/node2vec-kdd16.pdf
- Kipf & Welling. "Semi-Supervised Classification with GCNs." ICLR (2017).
- Hamilton, Ying & Leskovec. "Inductive Representation Learning on Large Graphs" (GraphSAGE). NeurIPS (2017). https://cs.stanford.edu/people/jure/pubs/graphsage-nips17.pdf
- Neo4j Graph Data Science docs. https://neo4j.com/docs/graph-data-science/current/ (2024)
- igraph documentation. https://igraph.org/ (2024)
- graph-tool performance. https://graph-tool.skewed.de/performance.html (2024)
- RAPIDS cuGraph. https://docs.rapids.ai/api/cugraph/stable/ (2024)
- Benchmark of popular graph/network packages. https://www.timlrx.com/blog/benchmark-of-popular-graph-network-packages-v2/ (2020)
