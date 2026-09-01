# Caching & Optimization

## Caching Tiers

1. **In-Memory Caching (`functools.lru_cache`)**:
   - Plan quotas and price quotes resolution (`plans.get()`, `ledger.resolve_price()`).
2. **SQLite BM25 FTS5 Indexes**:
   - Keyword lookups across refined docsets avoid redundant vector embedding generation.
3. **ChromaDB Vector Collections**:
   - Pre-computed embeddings stored on local SSDs; queried with cosine similarity.
4. **Astro Static HTML**:
   - Pre-rendered static pages for directory sites and concept documentation.
