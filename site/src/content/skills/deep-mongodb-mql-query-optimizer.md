---
title: "deep-mongodb-mql-query-optimizer"
description: "Multi-pass optimizer for one MongoDB find filter, write filter or aggregation pipeline: index design, stage order, shard targeting and explain verification."
order: 15
tags: [mongodb, optimization, convergence-loop]
aliasCommand: "/dmqo"
---

The MongoDB member of the deep-optimizer family. It takes one query or pipeline and audits it for ESR/ERS index fit, selectivity, operator anti-patterns, `$in`/`$or` bounds, stage order, accumulator memory, covered-query chances, cursor economics and shard targeting, then rewrites every High and Medium finding. When a MongoDB MCP connection is available it confirms the result with `explain`. Index changes are recommended, never applied.

**Use it for:** "why is this aggregation slow", "what index does this query need", COLLSCAN or blocking-sort output, a slow-log line.

**Not for:** SQL (use [deep-query-optimizer](/skills/deep-query-optimizer/)) or schema redesign.
