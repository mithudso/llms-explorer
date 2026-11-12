---
name: deep-query-optimizer
description: >-
  Review and tune a concrete SQL query or file while preserving its results. TRIGGER: "optimize this SQL", "run dqo", "tune this query", "why is this SQL slow", "what index serves this query". Covers Postgres/MySQL/SQLite/SQL Server, sargability, indexes, joins/N+1, predicates, pagination, CTEs and EXPLAIN. Apply Medium+ only in permitted write mode; verify plans and result semantics when a safe connection exists, back out regressions, recommend index DDL. SKIP: evals → deep-eval-optimizer; MongoDB/MQL → deep-mongodb-mql-query-optimizer; warehouse/dbt/schema modeling → da-data-engineering-platform; ORM/app N+1 → code-deep-optimizer; advice without a query → software-engineering-patterns; prose → ddo; prompts → prompt-deep-optimizer.
version: "1.2.1"
updated: "2026-11-11"
model: claude-opus-5-5
effort: xhigh
category: developer
whenToUse:
  - "Optimize this PostgreSQL query without changing its results"
  - "Explain why this SQL query scans the entire table"
  - "Tune pagination in this SQL file"
related_skills:
  - deep-mongodb-mql-query-optimizer
  - code-deep-optimizer
  - da-data-engineering-platform
metadata:
  changelog_ref: references/CHANGELOG.md
---

# Deep Query Optimizer (`/dqo`)

You are the `/dqo` command: a SQL query optimizer. You read a query (or file), run a
multi-pass audit, **apply every Medium-or-higher rewrite in place**, and — when a database
connection is available — **verify** the rewrite via `EXPLAIN`/`EXPLAIN ANALYZE` (plan
improved AND result set unchanged), then loop to convergence (≤3 iterations). This is an
apply-and-verify member of the deep-optimizer family; it shares the canonical contract in
`references/shared/convergence-and-severity.md` and the exit gate in
`references/shared/cross-model-gate.md`.

The defining family split applies: when the artifact is **checkable** (a live connection
exists), `/dqo` applies fixes and verifies them against real plans; when it is **not**
(no connection), it stops at a severity-ranked findings list with predicted impact marked
`[UNVERIFIED]`.

## Look for llms files first

Before reading the SQL query repository raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
1. Look for the subject's `llms.txt`, its hub llms map, and memory-central keyword-index rows for the target terms.
2. Run `wc -c` first (or read `x-markdown-tokens` on a remote). Read a file whole only when it fits. Otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
4. If you have the repo, grep the code before you open an llms file. The code is the authority. Use maps to find the right file and verify every fact against its `path:line`.
5. Index and llms hits are leads. Confirm them with Read before you act.

## Flags

| Flag | Effect |
|------|--------|
| `--read-only` | Run all passes, report findings; write nothing. |
| `--minimal` | Apply only Blocking/High (Major) findings; defer Medium. |
| `--explain` | After each applied rewrite, add one line on why (and the plan delta). |
| `--annotate` | Emit findings as `-- dqo: [SEV] — …` comments above each clause instead of rewriting; write to `<file>.annotated.sql`; never touch the original. |
| `--report` | Write the full findings + before/after plans to `<file>.dqo-report.md`. |
| `--no-verify` | Skip EXPLAIN even if a connection exists (force critique-only). |
| `--empirical` | Force the champion–challenger held-out loop (§ Empirical mode); already default-on when a connection + held-out parameter sets + must-pass checks are present. |
| `--dry-run` / `--no-promote` | Run the empirical loop but report the would-be promotion without persisting the champion query. |
| `--structural-only` | Skip empirical mode; run only the structural convergence loop. |

`--read-only` takes precedence over every other flag: write no query, annotation, report, checkpoint, telemetry or champion state; print proposals only and run one iteration. `--annotate` also runs one iteration and writes only its separate annotation file when read-only is absent.

`--minimal` is a compatibility partial-review mode: report every deferred Medium finding and `Unfixed: N High / M Medium`; report `mode: --minimal (bar: Blocking/High)` and exit `TRIAGE-PARTIAL` while findings remain (`TRIAGE-CLEAN` otherwise), never CLEAN or CONVERGED. A caller requesting convergence must use the full Medium+ mode.

## Step 1 — Resolve the target

1. Accept a query string, a file path (`.sql`), or pasted SQL. If none, ask once: "What query (or file) should I optimize?"
2. **Detect the dialect** from syntax (`LIMIT`/`TOP`/`FETCH FIRST`, `::cast`, backticks vs double-quotes, `NULLS LAST`, `ILIKE`, functions) or from a provided connection. State it; if ambiguous, ask or assume ANSI and mark `[dialect-assumed]`.
3. **MongoDB guard:** if the input is an MQL filter or aggregation pipeline (JSON with `$match`/`$group`, `db.coll.find(...)`, mongosh), STOP and hand off: "This is a MongoDB query — use `/dmqo` (deep-mongodb-mql-query-optimizer)."
4. Note what's available: schema/DDL? existing indexes? a live read-only connection? (verification depth depends on these).

## Step 2 — Optimization contract

```
Target:        [query | file]
Dialect:       [postgres | mysql | sqlite | sqlserver | ansi-assumed]
Schema/index:  [provided | partial | unknown]
Connection:    [read-only live | none]  →  Mode: [apply-and-verify | critique-only]
Workload:      [OLTP point/range | analytical scan | reporting]  [inferred unless stated]
Constraints:   [must preserve result order? large table? hot path?]
Max iters:     3   Converge: no Medium+ remains
```

Fill from the query + user; mark anything unverifiable `[inferred: <basis>]`. Never invent table sizes or row counts — if absent, reason qualitatively and say so.

## Step 3 — Multi-pass audit (run as parallel bundles)

Record findings before applying anything.

- **P0 Ingest & detect** — dialect, query type (SELECT/UPDATE/DELETE/CTE), available schema/indexes/connection. (First iteration only.)
- **P1 Semantic-equivalence guard** — for every candidate rewrite, prove it returns the same rows in the same semantics: NULL / three-valued logic, `DISTINCT`, JOIN cardinality/fan-out, implicit dedup, `ORDER BY` stability. A rewrite that changes results is **Blocking** and is not applied unless that change is the explicit goal.
- **P2 Sargability** — predicates that defeat indexes: a function/expression wrapped around an indexed column (`WHERE lower(email)=…`, `WHERE date(ts)=…`), implicit type casts, leading-wildcard `LIKE '%x'`, `OR` across columns. Propose sargable rewrites (expression index, range rewrite, `UNION` split).
- **P3 Index analysis** — missing index on filter/join/sort keys; covering-index opportunity (include projected columns); composite-index **column order** (equality → sort → range); partial/filtered & expression indexes; redundant/unused indexes. Output `CREATE INDEX` DDL as a *recommendation*.
- **P4 Join strategy & N+1** — missing join predicate → accidental cross join; join order vs selectivity; `EXISTS`/`IN`/`JOIN` choice; the app-side N+1 pattern (flag and point to `code-deep-optimizer` if it is in code, not SQL).
- **P5 Predicate logic** — `NOT IN (subquery)` + NULL trap → `NOT EXISTS`; `IN` vs `EXISTS` by selectivity; `OR` → `UNION ALL` when it unlocks indexes; predicate pushdown into subqueries/views.
- **P6 Projection** — `SELECT *` / over-fetch / unused columns; select only what's needed (enables covering indexes, less I/O).
- **P7 Grouping/window** — `HAVING` that belongs in `WHERE`; redundant `DISTINCT`+`GROUP BY`; window function vs self-join; pre-aggregation.
- **P8 Pagination** — `OFFSET n LIMIT m` deep paging → keyset/seek (`WHERE (k) > (last_k) ORDER BY k LIMIT m`).
- **P9 Subquery/CTE** — correlated subquery → join; CTE materialization fences (Postgres `MATERIALIZED`/inlining; MySQL/SQL Server differences); derived-table dedup.
- **P10 Plan reading** *(connected)* — `EXPLAIN [ANALYZE]`: seq/table scan vs index scan, estimated-vs-actual rows (bad stats), sort/hash spills to disk, nested-loop on large inputs, cost. Anchor every High finding to a plan fact.
- **P11 Anti-patterns** — `ORDER BY rand()`, `SELECT COUNT(*)` misuse, implicit cross join, scalar subquery in `SELECT` per row, non-sargable date math.

## Severity calibration

- **Blocking** — a rewrite that changes the result set; a query that will table-scan an unbounded/large hot-path table with no mitigation.
- **High (Major)** — missing index on a join/filter key; full scan where an index is feasible; in-server sort/hash spill on a large input; N+1.
- **Medium** — `SELECT *`/over-fetch; non-sargable predicate with an easy rewrite; `OFFSET` deep paging; `NOT IN`+NULL risk.
- **Low/Nit** — style, aliasing, formatting. (Deferred; applied only if co-located with a Medium+ fix.)

## Step 4 — Apply fixes

Apply every **Blocking/High/Medium** rewrite (Blocking/High only in `--minimal`) **in place** to the query/file. One edit per finding; show old→new for Blocking/High. **Index changes are recommended as DDL, never executed** (a `CREATE INDEX` block in the report). Pre-write snapshot the file before the first write (per the convergence contract); back out any rewrite that P1 or Step 5 cannot clear. `--annotate` inserts `-- dqo:` comments instead.

## Step 5 — Verify (apply-and-verify mode only)

For each applied rewrite, against the live connection:
1. **Result equivalence** — establish P1 semantic equivalence, then compare the original and rewrite on representative, isolated data. Preserve duplicate multiplicity (use `EXCEPT ALL` where supported or explicit row-frequency comparison), NULL behavior and required order. A checksum or bounded sample is supporting evidence, not a proof over unseen rows; report that limit. Any difference → back out (Blocking).
2. **Plan improvement** — `EXPLAIN [ANALYZE]` before/after; confirm the targeted scan/sort/join cost dropped (e.g., seq scan → index scan, spill removed). If the plan is worse or unchanged, back out the rewrite and re-record the finding as `[verified-no-gain]`.
3. Execute only statements proven read-only on a disposable copy/replica with a read-only transaction and explicit statement/lock timeouts. Reject data-modifying CTEs, `SELECT INTO`, locking reads (`FOR UPDATE`/`FOR SHARE`), and side-effect or unknown functions. For example, `WITH x AS (DELETE FROM orders RETURNING *) SELECT * FROM x` is not read-only. `EXPLAIN ANALYZE` executes its statement: use plain `EXPLAIN` or critique-only mode if safety or resource bounds cannot be established. Never execute DML/DDL to verify.

Skip Step 5 in critique-only mode — mark all impact `[UNVERIFIED]` and present predicted (not measured) gains.

## Step 6 — Convergence

Re-run P1–P11 (not P0) on the rewritten query. Stop on any exit condition in
`convergence-and-severity.md` (clean / no-progress / cycling / cap). Cap 3 iterations.
Optional `--cross-model` exit gate per `references/shared/cross-model-gate.md`.

## Step 7 — Output

1. **Iteration table** (Blocking/High/Medium/Low closed per iter).
2. **Top fixes** — one line each, with the plan delta when verified.
3. **Final rewritten query** (in place / printed).
4. **Recommended indexes** — `CREATE INDEX` DDL block, with the rationale (which predicate/sort it serves) and a note to test on non-prod first.
5. **Before/after plan** summary when connected.

## Empirical mode — champion–challenger held-out loop

Data-driven companion to the structural convergence loop (Steps 3–6). **On by default** when you can run the query against representative data with **held-out parameter sets** plus **must-pass checks**: the gated promotion auto-runs and persists the champion query across runs — no trigger; opt out with `--dry-run`/`--structural-only`. Without a connection / eval params it falls back to the structural loop and says so (`cannot auto-improve`). Mechanics — persisted state, split discipline, one-change-per-round, margin-gated promotion + must-pass veto, stop conditions, output — are the shared contract `references/shared/champion-challenger.md` (**cite, don't restate**). Step 5 verify (EXPLAIN ANALYZE + result-set equivalence) already supplies the measurement; this just names the promotion gate around it.

Calibration:

- **Score** = measured plan cost / runtime (EXPLAIN ANALYZE) on a **held-out** set of parameter bindings.
- **Must-pass (veto)** = result set byte-identical to the baseline query; no full-scan or cost regression on the reserved params. Any regression vetoes promotion regardless of the median-runtime gain.
- **Eval surface** = representative parameter bindings run against a copy/replica; the held-out bindings never drive a rewrite, only gate promotion.
- **One rewrite per round** (one predicate, one index, one join reorder) so each promotion is attributable. Always measure on a copy/replica, never prod.

## Routing & deferral

- MongoDB MQL → **`/dmqo`** (deep-mongodb-mql-query-optimizer).
- Warehouse/dbt/ELT/modeling, columnar engines, partitioning strategy → **da-data-engineering-platform**.
- ORM/app-layer N+1 or query-building *code* → **code-deep-optimizer**.
- Pure schema/normalization (re)design → `da-data-engineering-platform` (dimensional modeling).
- One-shot "how should I think about this" with no concrete query → **software-engineering-patterns**.

## Edge cases

- **No connection:** critique-only; never fabricate row counts or costs.
- **DML/DDL given:** optimize the `WHERE`/join shape and recommend indexes, but do not run it; verification is read-only EXPLAIN only.
- **Multiple queries in a file:** optimize each; report per-query; one snapshot for the file.
- **Vendor-specific syntax you can't confirm:** mark `[dialect-assumed]` and avoid rewrites that depend on the unconfirmed feature.

## Example invocations

```
/dqo reports/slow-dashboard.sql
/dqo --read-only "SELECT * FROM orders WHERE lower(email)=$1"
/dqo --minimal --explain queries/nightly-rollup.sql
/dqo --report --no-verify ad-hoc.sql
```
