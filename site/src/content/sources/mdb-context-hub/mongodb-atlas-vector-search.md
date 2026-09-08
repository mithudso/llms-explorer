---
title: "MongoDB Atlas Vector Search"
description: "```python"
---

# MongoDB Atlas Vector Search and RAG

## 1. Vector Index Definition and HNSW Parameters

### Index Type

```python
from pymongo.operations import SearchIndexModel

index_model = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine",    # euclidean | cosine | dotProduct
                # Optional HNSW tuning:
                # "efConstruction": 200,   # Build quality (default: 150)
                # "maxConnections": 32,    # Graph connectivity (default: 16)
                # Optional quantization:
                # "quantization": "scalar",  # scalar | binary
            },
            # Optional filter fields (for pre-filtering):
            { "type": "filter", "path": "category" },
            { "type": "filter", "path": "year" },
        ]
    },
    name="vector_index",
    type="vectorSearch"
)
db.collection.create_search_index(model=index_model)
```

### Similarity Functions

| Function | Use when |
|---|---|
| `cosine` | Embeddings not L2-normalized; semantic text similarity |
| `dotProduct` | Embeddings ARE L2-normalized (e.g., OpenAI ada-002, Voyage AI) — same as cosine but faster |
| `euclidean` | Geometric distance matters; spatial data |

### HNSW Tuning Parameters

| Parameter | Default | Effect |
|---|---|---|
| `efConstruction` | 150 | Build-time quality; higher = better recall + slower index build |
| `maxConnections` (m) | 16 | Graph connectivity; higher = better recall + more memory |
| Index build is O(N log N) | | Doubling m doubles memory; start with defaults |

**Recommendation:** Start with defaults. Only tune if ANN recall < 0.90 in production.

### Quantization

- **Scalar quantization (int8):** Reduces index size by ~4x; recall typically >95% vs full float
- **Binary quantization:** Reduces by ~32x; recall ~90%; useful when memory is the constraint

## 2. $vectorSearch Operator

### ANN (Approximate Nearest Neighbor)

```python
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_embedding,  # list[float]
            "numCandidates": 150,           # candidate pool (>= limit, typically 10x limit)
            "limit": 5,                     # final results to return
            "filter": { "category": "electronics" }  # pre-filter (must have filter field in index)
        }
    },
    {
        "$project": {
            "title": 1,
            "score": { "$meta": "vectorSearchScore" }
        }
    }
]
results = list(collection.aggregate(pipeline))
```

**numCandidates:** Controls recall-latency tradeoff. Higher = better recall + slower. Rule of thumb: 10-20x the `limit`. Hard minimum equals `limit`.

### ENN (Exact Nearest Neighbor)

```python
{
    "$vectorSearch": {
        "index": "vector_index",
        "path": "embedding",
        "queryVector": query_embedding,
        "exact": True,        # ENN mode — no numCandidates
        "limit": 5
    }
}
```

ENN guarantees perfect recall but O(N) scan. Use only for: small collections (<100K docs), high-accuracy requirements, offline batch evaluation. Do not use in production at scale.

## 3. Hybrid Search ($rankFusion / $scoreFusion)

Combines semantic vector search with keyword full-text search.

### $rankFusion (Reciprocal Rank Fusion — recommended)

```javascript
db.articles.aggregate([
  {
    "$rankFusion": {
      "input": {
        "pipelines": {
          "vector": [
            { "$vectorSearch": {
              "index": "vector_index",
              "path": "embedding",
              "queryVector": queryEmbedding,
              "numCandidates": 150,
              "limit": 20
            }}
          ],
          "fullText": [
            { "$search": {
              "index": "search_index",
              "text": { "query": userQuery, "path": "title" }
            }},
            { "$limit": 20 }
          ]
        }
      },
      "combination": { "weights": { "vector": 0.6, "fullText": 0.4 } }
    }
  },
  { "$limit": 5 }
])
```

RRF is robust to score magnitude differences between vector and full-text scores. Better than `$scoreFusion` when scores are on different scales.

### $scoreFusion (weighted score combination)

```javascript
{ "$scoreFusion": {
  "input": {
    "pipelines": {
      "vector": [...],
      "fullText": [...]
    },
    "combination": {
      "method": "linear",
      "weights": { "vector": 0.5, "fullText": 0.5 }
    }
  }
}}
```

## 4. Voyage AI Auto-Embedding

Atlas Vector Search + Voyage AI auto-embedding lets you skip the embedding pipeline entirely — Atlas embeds at index-build time and at query time.

```python
# Index definition with auto-embedding
index_model = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "embedding",         # Atlas auto-populates this field
                "numDimensions": 1024,
                "similarity": "cosine",
                "embeddingDefinition": {
                    "provider": "voyageAI",
                    "model": "voyage-3-large",  # voyage-3-lite | voyage-3 | voyage-3-large
                    "inputField": "content"     # source text field
                }
            }
        ]
    },
    type="vectorSearch"
)

# Query (no embedding step needed)
pipeline = [{
    "$vectorSearch": {
        "index": "vector_index",
        "path": "embedding",
        "queryString": "user's question",   # auto-embedded at query time
        "numCandidates": 150,
        "limit": 5
    }
}]
```

**Voyage 4 model family (as of 2026):**
- `voyage-4-large`: 1024 dims, best quality
- `voyage-4-lite`: 512 dims, fastest + most economical
- `voyage-4-finance`: Finance-domain specialized
- `voyage-4-code`: Code and programming specialized

## 5. RAG Architecture Patterns

### Basic RAG

```
User query
  → Embed query (embedding model)
  → $vectorSearch against Atlas (top K chunks)
  → Inject retrieved chunks into LLM prompt
  → LLM generates answer
```

### Parent-Document Retrieval

Index small chunks for precise retrieval, but return the parent document for full context:

```python
# Index: small chunks (256-512 tokens) with parentId reference
# $vectorSearch retrieves top K chunks
# $lookup on parent collection to fetch full parent document
pipeline = [
    { "$vectorSearch": { "index": "chunk_index", ..., "limit": 5 }},
    { "$lookup": {
        "from": "documents",
        "localField": "parentId",
        "foreignField": "_id",
        "as": "parent"
    }},
    { "$unwind": "$parent" }
]
```

### Metadata Filtering for Multi-Tenant RAG

```python
# Filter vector search by tenant ID before ANN
{
    "$vectorSearch": {
        "filter": { "tenantId": current_user.tenant_id },
        "queryVector": ...,
        "numCandidates": 150,
        "limit": 5
    }
}
# tenantId must be declared as a filter field in the index definition
```

## 6. Performance Tuning

### Recall vs Latency Tradeoff

```python
# High recall (slower): numCandidates = 20x limit
{ "numCandidates": 200, "limit": 10 }  # recall ~0.99

# Balanced: numCandidates = 10x limit
{ "numCandidates": 100, "limit": 10 }  # recall ~0.95

# Low latency (acceptable for many apps): numCandidates = 5x limit
{ "numCandidates": 50, "limit": 10 }   # recall ~0.90
```

### Dedicated Search Nodes

Vector Search in production should use dedicated Search Nodes to avoid resource contention with OLTP queries. HNSW graphs must fit in RAM for fast ANN.

- 1M vectors × 1536 dims × float32 ≈ 6 GB raw; with HNSW graph ≈ 9-12 GB
- Use S30_HIGHCPU_NVME or larger for production vector workloads
- Use Storage-Optimized tiers when index exceeds RAM

## 7. Anti-Patterns

- **Wrong similarity metric:** Using `euclidean` with normalized embeddings (should use `dotProduct`); using `cosine` with unnormalized embeddings and comparing absolute distances
- **No filter fields declared in index but using `filter` in $vectorSearch:** Causes full ANN scan before filtering, not pre-filter → worst of both worlds
- **numCandidates too low:** Values close to `limit` severely degrade recall
- **ENN in production at scale:** O(N) scan; destroys query latency for collections > 100K docs
- **Not sizing Search Nodes for vector workload:** Embedded mongot on shared cluster causes OLTP latency spikes
- **Dimension mismatch:** `numDimensions` in index must match exactly what the embedding model outputs
- **Querying without the vector index active:** Atlas returns an error or falls back to collection scan; wait for index build to complete

## References

- [Atlas Vector Search Documentation](https://www.mongodb.com/docs/atlas/atlas-vector-search/)
- [$vectorSearch Aggregation Stage](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/)
- [Hybrid Search with $rankFusion](https://www.mongodb.com/docs/atlas/atlas-search/aggregation-stages/rankFusion/)
- [Voyage AI Auto-Embedding](https://www.mongodb.com/docs/atlas/atlas-vector-search/auto-embedding/)
- [Atlas Vector Search Quantization](https://www.mongodb.com/docs/atlas/atlas-vector-search/quantization/)
