---
title: "MongoDB Atlas Search"
description: "Comprehensive reference for MongoDB Atlas Search — the Lucene-based full-text search engine embedded in Atlas. Covers the full lifecycle from index design through query construction, relevance tuning,"
---

# MongoDB Atlas Search (Lucene Full-Text)

Comprehensive reference for MongoDB Atlas Search — the Lucene-based full-text search engine embedded in Atlas. Covers the full lifecycle from index design through query construction, relevance tuning, and production deployment. Explicitly excludes Vector Search (`$vectorSearch`); see [[mongodb-search-ai]] for hybrid and semantic patterns.

## When to Use This Skill

- Building full-text search features: search bars, typeahead, faceted filtering
- Relevance-ranked results with BM25 scoring
- Complex text queries: phrase, fuzzy, wildcard, regex, proximity
- Faceted navigation (e-commerce filters, category counts)
- Autocomplete / search-as-you-type
- Multi-language content with language-specific analyzers
- Rich scoring control: boost, decay, function score

**Cluster tier requirement:** Atlas Search requires **M10 or higher**. Not available on M0 (free), M2, or M5 shared-tier clusters.

**Do NOT use Atlas Search when:**
- You need immediate consistency — indexes are eventually consistent via change streams
- Exact-match on a handful of fields — standard B-tree compound indexes are faster
- The collection is very small (< 10k docs) and a `$regex` scan is fast enough

See the full SKILL.md at ~/.claude/skills/mongodb-atlas-search/SKILL.md for complete operator reference, analyzer tables, anti-patterns, scoring, facets, autocomplete, and search node guidance.
