---
title: "deep-query-optimizer"
description: "Multi-pass review-and-fix optimizer for SQL: dialect detection, sargability, index design, join/N+1 analysis, and EXPLAIN-verified rewrites that back out any regression."
order: 15
tags: [sql, optimization, explain, indexes]
aliasCommand: "/dqo"
---

The SQL member of the family. Detects the dialect (Postgres, MySQL, SQLite, SQL
Server), audits sargability, index design, joins and N+1 patterns, predicate logic,
projection, pagination, subqueries/CTEs, and the EXPLAIN plan itself, then applies
every Medium+ rewrite in place.

When a database connection exists, verification is empirical: `EXPLAIN` /
`EXPLAIN ANALYZE` must show the plan improved *and* the result set unchanged — a
rewrite that fails either test is backed out. It also recommends index DDL where the
plan shows the query is paying for a missing index.

**Use it for:** "optimize this SQL", "run dqo", "tune this query", "why is this query
slow", index-design review on a hot path.

**Not for:** MongoDB MQL/aggregation (mongodb-expert's query optimizer spoke) ·
application-code N+1 fixes beyond the query itself
([code-deep-optimizer](/skills/code-deep-optimizer/)).
