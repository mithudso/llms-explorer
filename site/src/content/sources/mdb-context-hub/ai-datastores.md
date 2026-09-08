---
title: "AI Datastores"
description: "| Need | Recommended |"
---

# AI Datastores

## Quick datastore selection

| Need | Recommended |
| --- | --- |
| Managed zero-ops at scale | Pinecone |
| Best price-performance (mid-scale) | Qdrant |
| Hybrid search (vector + keyword + metadata) | Weaviate |
| Rapid prototyping | Chroma |
| 100B+ vectors with GPU | Milvus/Zilliz |
| Already on PostgreSQL | pgvector |
| Document + vector in one collection | MongoDB Atlas Vector Search |
| Temporal fact tracking | Graphiti + Neo4j/FalkorDB |
| Agent memory (drop-in API) | Mem0 |
| Agent memory (autonomous curation) | Letta (MemGPT) |
| Sub-ms coordination + caching | Redis |
| GraphRAG with multi-hop reasoning | Neo4j + LangChain |

## Vector databases: 2026 benchmarks

| Database | p50 latency (10M vectors) | Hybrid search |
| --- | --- | --- |
| Qdrant | &lt;5ms | Yes |
| Weaviate | ~8ms | Yes (best-in-class) |
| Milvus | ~10ms | Yes |
| Pinecone Serverless | ~15ms | No (dense only) |
| pgvector | ~12ms | Via tsvector combo |
| MongoDB Atlas VS | &lt;50ms (quantized) | Yes (Atlas Search) |
| Chroma | &lt;5ms (small sets) | No |

## Self-hosted cost crossover

Self-hosted Qdrant on a $30/month VPS handles 10M+ vectors — 10x cheaper than equivalent Pinecone. The crossover where self-hosting beats Pinecone is roughly $600/month in vector DB costs.

## Hybrid storage architecture (2026 best practice)

| Memory type | Storage | Retention |
| --- | --- | --- |
| Working memory (session) | Redis | 15min–2hr |
| Episodic memory (history) | MongoDB, PostgreSQL | Weeks–months |
| Semantic memory (embeddings) | Pinecone, Qdrant, Atlas VS | Indefinite |
| Relational memory (entities) | Neo4j, FalkorDB/Graphiti | Indefinite |
