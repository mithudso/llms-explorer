# /lca pack scorecard — mongodb mql query optimization (2026-10-19)

Scope per pack: `~/.claude/skills/web-text-mirror/text-mirror/mongodb.com-docs-query-core.md` (765 mongodb.com docs pages derived from the research source library: Server manual query/index/aggregation/time-series/profiler/explain/release-notes pages, Compass, Atlas performance pages) + the run's `~/.global-ai-hub/research/<slug>/units.jsonl` claims. Keyword harvest + semantic pass (mxbai-embed-large, z≥3.0) + rule-based classification (sample-code and generic-surface suspects dropped) + compile (`--rights extractive`). Probe = deterministic question-bank coverage (10 questions written from the lexicon before reading the pack). Agent test = fresh-context Haiku reading only `llms-small.txt` (bar ≥8/10). Four parents split into 12 child packs (A×3, D×4, E×3, F×2); two D children stay over the 50k-token target because `cursor`/`count` surfaces are broad.

| Cohort | Pack | units kept | full tok | small tok | sources | children | probe small | probe full | agent test (small) | indexed |
|---|---|---|---|---|---|---|---|---|---|---|
| A | `mongodb-explain-plans-and-query-planner` | 1574 | ~144033 | ~24226 | 228 | 3 | 6/10 | 10/10 | 6/10 (24k) | concept__mongodb-explain-plans-and-query-planner (vector+FTS5) |
| B | `mongodb-compound-index-design` | 683 | ~63850 | ~16203 | 9 | 0 | 9/10 | 10/10 | 8/10 (16k) | concept__mongodb-compound-index-design (vector+FTS5) |
| C | `mongodb-special-indexes-and-index-builds` | 664 | ~62353 | ~24209 | 89 | 0 | 7/10 | 10/10 | 8/10 (24k) | concept__mongodb-special-indexes-and-index-builds (vector+FTS5) |
| D | `mongodb-query-shape-optimization` | 2446 | ~228033 | ~24240 | 348 | 4 | 9/10 | 10/10 | 6.5/10 (24k) | concept__mongodb-query-shape-optimization (vector+FTS5) |
| E | `mongodb-time-series-query-optimization` | 1032 | ~105029 | ~16237 | 8 | 3 | 10/10 | 10/10 | 7.5/10 (16k) | concept__mongodb-time-series-query-optimization (vector+FTS5) |
| F | `mongodb-query-optimization-tooling` | 927 | ~92052 | ~16181 | 6 | 2 | 9/10 | 10/10 | 6.5/10 (16k) | concept__mongodb-query-optimization-tooling (vector+FTS5) |
| G | `mongodb-advanced-explain-and-planner-changes` | 269 | ~24946 | ~16169 | 8 | 0 | 10/10 | 10/10 | 7.5/10 (16k) | concept__mongodb-advanced-explain-and-planner-changes (vector+FTS5) |
| H | `mongodb-atlas-slow-query-and-advisor-automation` | 744 | ~77022 | ~16121 | 1 | 0 | 10/10 | 10/10 | 9/10 (16k) | concept__mongodb-atlas-slow-query-and-advisor-automation (vector+FTS5) |

Family rollup: `~/.global-ai-hub/llms-concepts/mongodb-mql-query-optimization-family.llms/llms.txt` (docset_refine family, 8 products + 8 facts layers), audited by `/ldo --family` (see ldo report).

Known gaps: small-file agent tests for A, D and F stay below the 8/10 bar (E and G at 7.5) at a 24k budget — the generator's small selection leaves specific claims (plan-cache eviction triggers, countDocuments vs estimatedDocumentCount, $where) in llms-full.txt; full-file probe coverage is 10/10 for every pack. Hand-off: `/ldo` on those packs (A, D, F; optionally E, G).
