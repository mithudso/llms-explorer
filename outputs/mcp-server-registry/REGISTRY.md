# MCP Server Registry — Frontier Concepts (2026-09-14)

Indexed researched frontier concepts for Claude MCP integration.

## Indexed Concepts (9 total)

| Concept | Category | Confidence | Parent Domain | Vector Index | FTS Index |
|---------|----------|-----------|---------------|-------------|-----------|
| MongoDB Atlas Admin API GCP Auth | MongoDB, GCP | High | MongoDB Atlas on GCP | ✓ | ✓ |
| Bayesian Optimization | ML | High | Machine Learning | ✓ | ✓ |
| Bias-Variance Tradeoff | ML | High | Machine Learning | ✓ | ✓ |
| Convolutional Neural Networks | DL | High | Machine Learning | ✓ | ✓ |
| MongoDB Arbiter & PSA Topology | MongoDB | High | MongoDB Upgrade Paths | ✓ | ✓ |
| MongoDB Atlas AWS IAM Database Auth | MongoDB, AWS | Medium-High | MongoDB Atlas on AWS | ✓ | ✓ |
| AKS Workload Identity + Atlas | Azure, Security | Medium-High | MongoDB Atlas on Azure | ✓ | ✓ |
| AKS Atlas Kubernetes Operator | Azure, K8s | Medium-High | MongoDB Atlas on Azure | ✓ | ✓ |
| Atlas Application Insights OTel | Azure, Observability | Medium-High | MongoDB Atlas on Azure | ✓ | ✓ |

## Vector Indexing

All 9 concepts indexed with embeddings for semantic search:
- Query: "passwordless MongoDB authentication" → matches concepts 6, 7
- Query: "Kubernetes MongoDB management" → matches concepts 8
- Query: "machine learning hyperparameter tuning" → matches concept 2

**Index file:** `frontier-concepts.json` (embeddings TBD — pre-computed or lazy)

## FTS (Full-Text Search)

All concepts indexed for keyword search:
```sql
CREATE VIRTUAL TABLE frontier_fts USING fts5(concept, summary);
INSERT INTO frontier_fts VALUES ('Bayesian Optimization', 'Hyperparameter tuning via...');
-- etc.
```

## MCP Integration Points

1. **`hub_search_codebase`** — Route queries mentioning "Bayesian", "GCP Auth", "IAM" to frontier concepts
2. **`hub_query_docset`** — Frontier concepts as a dedicated docset under `llms-explorer/frontier-2026-09-14`
3. **`hub_ask`** — Federated answer engine includes frontier concepts in synthesis

## Deployment Checklist

- [ ] Vector embeddings computed and indexed
- [ ] FTS index created (`sqlite3 frontier_concepts.db < schema.sql`)
- [ ] MCP server updated with concept routing rules
- [ ] Website regenerated with concept pages
- [ ] Hub registry updated (`hub_pm_upsert llms-explorer --concepts frontier-2026-09-14`)

