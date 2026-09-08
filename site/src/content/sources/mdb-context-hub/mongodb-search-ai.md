---
title: "MongoDB Atlas Search and Vector Search"
description: "```python"
---

# MongoDB Search and AI Retrieval (Atlas Search + Vector Search)

## Atlas Search (Full-Text, Lucene-based)

### Index Creation

```python
from pymongo.operations import SearchIndexModel

# Atlas Search index
search_index = SearchIndexModel(
    definition={
        "mappings": {
            "dynamic": True,  # auto-index all string fields
            # OR explicit:
            "fields": {
                "title": [
                    {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    }
                ],
                "price": [{"type": "number"}],  # for faceting/ranges
                "category": [{"type": "stringFacet"}],  # for category facets
                "createdAt": [{"type": "date"}]
            }
        }
    },
    name="default",
    type="search"
)
collection.create_search_index(model=search_index)
```

### $search Operator

```javascript
db.products.aggregate([
  {
    $search: {
      index: "default",  // optional if named "default"
      compound: {
        must: [
          { text: { query: "mongodb atlas", path: "title" } }
        ],
        should: [
          { text: { query: "cloud database", path: "description" } }
        ],
        filter: [
          { range: { path: "price", gte: 10, lte: 500 } },
          { equals: { path: "inStock", value: true } }
        ]
      },
      highlight: { path: "description" },
      sort: { score: { $meta: "searchScore" }, _id: 1 }  // stable sort for pagination
    }
  },
  {
    $project: {
      title: 1, price: 1,
      score: { $meta: "searchScore" },
      highlights: { $meta: "searchHighlights" }
    }
  },
  { $limit: 20 }
])
```

### Text Analyzers

| Analyzer | Use when |
|---|---|
| `lucene.standard` | Default; good for most English text |
| `lucene.english` | English with stemming (runs → run) |
| `lucene.keyword` | Exact string match (no tokenization) |
| `lucene.whitespace` | Split on whitespace only |
| `lucene.french`, `lucene.spanish`, etc. | Language-specific stemming |
| Custom analyzer | `nGram` for partial matching, custom filters |

### Autocomplete

```javascript
// Index definition with autocomplete analyzer
"title": [{
  "type": "autocomplete",
  "tokenization": "edgeGram",  // or nGram
  "minGrams": 2,
  "maxGrams": 10
}]

// Query
{
  $search: {
    autocomplete: { query: "mon", path: "title" }
  }
}
```

### Faceted Search

```javascript
db.products.aggregate([
  {
    $searchMeta: {  // returns only facet metadata (not documents)
      facet: {
        operator: {
          text: { query: "laptop", path: "name" }
        },
        facets: {
          categoryFacet: { type: "string", path: "category", numBuckets: 10 },
          priceRanges: {
            type: "number",
            path: "price",
            boundaries: [0, 100, 500, 1000, 5000]
          }
        }
      }
    }
  }
])
```

### Synonyms

```javascript
// Create a synonym collection
db.synonyms.insertMany([
  { mappingType: "equivalent", synonyms: ["laptop", "notebook", "computer"] },
  { mappingType: "explicit", input: ["iphone"], synonyms: ["iphone", "apple phone", "ios phone"] }
])

// Reference in index definition
"analyzers": [],
"mappings": { ... },
"synonyms": [{
  "name": "mySynonyms",
  "analyzer": "lucene.standard",
  "source": { "collection": "synonyms" }
}]

// Use in query
{ $search: { text: { query: "laptop", path: "name", synonyms: "mySynonyms" } } }
```

### Score Diagnostics (BM25 tuning)

```javascript
{
  $search: {
    text: { query: "mongodb", path: "title" },
    scoreDetails: true  // adds detailed BM25 score breakdown
  }
}
// Output includes: $meta: "searchScoreDetails"
// Shows TF, IDF, field weight contribution per matching term
```

### Pagination with Atlas Search

For deterministic pagination (not skip/limit):

```javascript
// First page
{
  $search: {
    index: "default",
    text: { ... },
    sort: { score: { $meta: "searchScore" }, _id: 1 },  // _id for tiebreaking
    searchAfter: null  // no cursor for first page
  }
}

// Subsequent pages (use PIT + searchAfter)
{
  $search: {
    text: { ... },
    sort: { score: { $meta: "searchScore" }, _id: 1 },
    searchAfter: lastPageCursor  // { $binary: "..." } from previous result
  }
}
// Get cursor from: { $meta: "searchSequenceToken" }
```

## Atlas Vector Search

See `mongodb-atlas-vector-search` for the complete reference. Key summary:

```javascript
// $vectorSearch operator
{
  $vectorSearch: {
    index: "vector_index",
    path: "embedding",
    queryVector: embeddingArray,  // [0.1, 0.3, ...]
    numCandidates: 150,           // candidate pool (>= limit)
    limit: 10,
    filter: { category: "electronics" }  // pre-filter (must be in index)
  }
}
```

## Hybrid Search ($rankFusion)

Combine Atlas Search (BM25) with Vector Search (HNSW) results:

```javascript
db.products.aggregate([
  {
    $rankFusion: {
      input: {
        pipelines: {
          fullText: [
            { $search: { text: { query: "fast laptop", path: "name" } } },
            { $limit: 20 }
          ],
          semantic: [
            { $vectorSearch: {
              index: "vector_idx",
              path: "embedding",
              queryVector: semanticEmbedding,
              numCandidates: 200, limit: 20
            }}
          ]
        }
      },
      combination: {
        weights: { fullText: 0.4, semantic: 0.6 }
      }
    }
  },
  { $limit: 10 }
])
```

## Auto Embedding (Voyage AI)

Skip the external embedding pipeline:

```javascript
// Index: Atlas embeds the `content` field automatically using Voyage AI
{
  "fields": [{
    "type": "vector",
    "path": "embedding",
    "numDimensions": 1024,
    "similarity": "cosine",
    "embeddingDefinition": {
      "provider": "voyageAI",
      "model": "voyage-3-large",
      "inputField": "content"
    }
  }]
}

// Query: no need to compute embedding externally
{ $vectorSearch: { ..., "queryString": "user's search query" } }
```

## Search Node Architecture

For production, use dedicated Search Nodes to isolate Atlas Search / Vector Search workloads from OLTP:
- `S20_HIGHCPU_NVME`, `S30_HIGHCPU_NVME`, etc.
- Zero-downtime migration: enable Search Nodes → Atlas replications in background → automatic traffic switch
- See `mongodb-atlas-search-nodes` for sizing guide

## When to Use Atlas Search vs Text Indexes

| Aspect | Atlas Search | Text Indexes |
|---|---|---|
| Relevance ranking | BM25 (sophisticated) | Simple tf-idf |
| Analyzers | 20+ language analyzers, custom | English + basic |
| Autocomplete | Yes (edgeGram, nGram) | No |
| Facets | Yes ($searchMeta) | No |
| Highlighting | Yes | No |
| Synonyms | Yes | No |
| Performance at scale | Dedicated Search Nodes | COLLSCAN risk on large |
| Setup complexity | Higher (index required) | Lower |

**Always prefer Atlas Search for production full-text search.** Text indexes are only appropriate for very small collections or simple dev prototypes.

## Anti-Patterns

- **Dynamic true + all fields queried:** Dynamic mapping indexes everything, making the index large. Use explicit mappings for production.
- **No search node for production Vector Search:** Resource contention with OLTP causes latency spikes
- **numCandidates too low:** `numCandidates: limit` = minimal recall; use 10-20× limit
- **Missing filter fields in vector index:** `filter` in `$vectorSearch` requires the field to be declared as `type: "filter"` in the index definition; otherwise falls back to post-filter (much less efficient)

## References

- [Atlas Search Documentation](https://www.mongodb.com/docs/atlas/atlas-search/)
- [$search Aggregation Stage](https://www.mongodb.com/docs/atlas/atlas-search/aggregation-stages/search/)
- [$rankFusion](https://www.mongodb.com/docs/atlas/atlas-search/aggregation-stages/rankFusion/)
- [Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/)
- [Voyage AI Auto-Embedding](https://www.mongodb.com/docs/atlas/atlas-vector-search/auto-embedding/)
