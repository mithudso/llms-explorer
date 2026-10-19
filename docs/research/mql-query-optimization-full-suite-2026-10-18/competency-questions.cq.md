# Competency questions — mongodb-mql-query-optimization

Written by concept-family-explorer (via /full-suite) on 2026-10-18. One bullet per question; append-only across rounds.

- A query shows COLLSCAN in explain() — which index should I create, in which key order, and how do I confirm the new plan? → Explain Plan Interpretation / Compound Indexes and ESR Rule
- docsExamined is 50× nReturned on an indexed query — why, and how do I tighten the bounds? → Index Selectivity and Covering Queries / Multikey Indexes and Array Query Bounds
- The planner keeps picking the wrong index — how do I force or pin a plan so it survives restarts on MongoDB 8.0? → Query Planning and Plan Cache / Query Settings and Persistent Index Hints (8.0) / hint() and Index Forcing
- How do I find the slowest query shapes across the cluster without turning on the profiler? → Query Shapes, Query Hash and $queryStats / Slow Query Monitoring
- A sort fails with the in-memory sort limit — how do I make it index-backed? → Blocking Sort and Index-Backed Sort
- Deep skip/limit pagination is slow at page 500 — what pattern replaces it? → Pagination Patterns (skip/limit vs range/keyset)
- My $or / $in query runs a SUBPLAN with several IXSCANs — is that good or bad, and when does it fall back to COLLSCAN? → $in/$or Index Bounds and Union Plans
- Which indexes are unused and safe to drop, and how do I test a drop without risk? → Index Analysis with $indexStats and Unused-Index Detection / Hidden Indexes
- A time-series query is slow despite an index on metaField — what is happening in bucket unpacking? → Secondary Indexes on Time Series / Time-Series Bucket Unpacking and $match Pushdown
- A query on a sharded collection fans out to every shard — how do I make it targeted and read that from explain on mongos? → Sharded Query Targeting and Scatter-Gather
