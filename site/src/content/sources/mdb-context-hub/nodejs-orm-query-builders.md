---
title: "Node.js & TypeScript ORMs and Query Builders"
description: "This reference is about the SQL data-access layer in TypeScript/Node.js: the"
---

# Node.js & TypeScript ORMs and Query Builders

## Overview

This reference is about the **SQL data-access layer in TypeScript/Node.js**: the
library that sits between your code and a relational database (PostgreSQL, MySQL,
SQLite, SQL Server) and the patterns — migrations, N+1, transactions, pooling —
that apply no matter which library you pick.

The field splits along one axis: **how much abstraction over SQL** you want.

- **Full ORM** (Prisma, TypeORM, Sequelize, MikroORM): models/entities, a
  relation graph, change tracking, and a high-level query API. You think in
  objects; the library writes SQL and maps rows back.
- **Query builder** (Kysely; Drizzle's SQL-like API): a thin, type-safe wrapper
  over SQL itself. You think in `select`/`from`/`join`; you get autocomplete and
  compile-time column checking but **no relation/identity abstraction**.
- **Raw driver** (`pg`, `mysql2`, `better-sqlite3`): you write SQL strings. Maximum
  control, zero type-safety, most boilerplate.

Drizzle straddles the line — it markets as an ORM but is closer to a typed query
builder with an *opt-in* relational API. The single most consequential decision
is ORM-vs-builder-vs-driver; everything else (migrations, transactions) is then a
detail of the chosen tool. For **MongoDB** (Mongoose/ODM and document modeling)
this file does not apply — see `mongodb-expert`. For the **driver-level** pool
internals of one specific database, see that driver's own docs.

## Core concepts

### 1. Prisma — schema-first ORM with a generated client

Prisma's center of gravity is a single declarative file, **`schema.prisma`**:
`datasource`, `generator`, and `model` blocks define the data model in Prisma's
own DSL (not TS). `prisma generate` reads it and emits **Prisma Client** — a
fully typed, autocompleting query API generated into `node_modules`.

- **Migrations**: `prisma migrate dev` (development — diffs the schema, creates a
  SQL migration, applies it, regenerates the client) vs `prisma migrate deploy`
  (production/CI — applies already-committed migrations, never generates new ones).
  `prisma db push` skips migration files for prototyping; `prisma db pull`
  introspects an existing DB into the schema.
- **Type-safety**: the client is generated *from* the schema, so model shapes,
  `select`/`include` projections, and `where` filters are all statically typed —
  a projection returns exactly the selected fields.
- **The engine model** (important & changing): historically Prisma shipped a
  **Rust query engine** binary that the JS client talked to. Prisma is removing
  it — **v7 (Nov 2025) makes a Rust-free client the default**, using TS
  **driver adapters** over the native Node driver. This changes pooling defaults
  (now the driver's, not Prisma's) and improves edge/serverless fit.
- **Relation queries**: `include` / `select` with nested writes; `findMany`,
  `create`, nested `connect`/`createMany`. Prisma can emulate relations in the
  app layer via **relation mode** (`prisma` vs `foreignKeys`) when the DB can't
  enforce FKs (e.g. PlanetScale).
- **Fits**: teams wanting maximum DX, type-safety, and a managed migration story;
  Postgres/MySQL apps. **Doesn't fit**: cases needing hand-tuned SQL control, or
  (pre-v7) edge runtimes where the engine binary was a problem.

### 2. Drizzle ORM — SQL-first, no codegen, no runtime engine

Drizzle defines the schema **in TypeScript** (`pgTable`/`mysqlTable`/`sqliteTable`
+ column builders); that TS file is the single source of truth for both queries
and migrations. Its design claims: **zero dependencies, no code-generation step,
no runtime ORM engine** — a thin layer over the native driver that "always
outputs exactly 1 SQL query," making it lightweight and **serverless/edge-ready**.

- **Two query APIs**: a **SQL-like** builder (`db.select().from(users).where(...)`,
  reads like SQL) and an opt-in **relational queries** API (`db.query.users.
  findMany({ with: { posts: true } })`) for nested data without manual joins.
- **drizzle-kit** is the CLI: `generate` (emit SQL migrations from schema diff),
  `migrate` (apply them), `push` (prototype: push schema straight to DB),
  `pull` (introspect), `studio` (GUI), plus `check`/`up`.
- **Transactions**: `await db.transaction(async (tx) => { ... })`.
- **Fits**: edge/serverless (Cloudflare Workers, Vercel Edge, Neon/Turso), teams
  who *want* to see the SQL, bundle-size-sensitive deploys. **Trade-off**: less
  hand-holding than Prisma; you own more of the modeling.

### 3. Kysely — a type-safe query *builder* (not an ORM)

Kysely is a **type-safe SQL query builder** inspired by Knex. It is explicitly
**NOT an ORM and has no concept of relations** — you write SQL semantics
(`selectFrom`, `innerJoin`, `where`, CTEs, window functions) and get full
compile-time checking and autocomplete derived from a **`Database` interface**
you declare (table → column-type map).

- **Type inference**: column names, aliases, and result types are inferred from
  subqueries, joins, and `with` (CTE) statements — the result type has exactly
  the selected columns with correct types.
- **Composability**: everything is an **Expression**; `SelectQueryBuilder` and
  raw builders are themselves expressions, so you build **reusable query
  fragments** and helpers. Query *building* and *execution* can be split.
- **The `Database` type** is usually generated by **kysely-codegen** (official),
  **prisma-kysely**, or introspection — keeping types in sync with the real DB.
- Ships **transactions** (`db.transaction().execute(...)`), a **migration**
  framework, and an `sql` template-tag escape hatch. Compiles to one statement.
- **When a builder beats an ORM**: complex analytical SQL (window functions,
  recursive CTEs, set operations), reporting, or when you want the DB schema —
  not an object graph — to be the mental model, with zero hidden queries.

### 4. TypeORM, Sequelize & MikroORM — entities, decorators, the AR/DM split

These three are the mature, entity-based ORMs.

- **Active Record vs Data Mapper** (the defining axis): in **Active Record** the
  entity carries its own persistence methods (`user.save()`, `User.find()`); the
  model extends a base class. In **Data Mapper** entities are "dumb" property bags
  and persistence lives in separate **repository** classes (`repo.save(user)`),
  which scales better in large apps. **TypeORM uniquely supports both**;
  **MikroORM is Data Mapper**; **Sequelize is Active Record**.
- **TypeORM**: `@Entity`/`@Column`/`@OneToMany`/`@ManyToOne` decorators (needs
  `experimentalDecorators`/`reflect-metadata`); `DataSource` config; `Repository`
  + `QueryBuilder`. Broad DB support; the de-facto NestJS default.
- **Sequelize**: the oldest, most battle-tested (v6 mature, v7 modernizing TS).
  `Model` classes, `init`/`define`, associations, `include`-based eager loading,
  strong transactions, read replication, migrations via `sequelize-cli`.
- **MikroORM**: implements **Data Mapper + Unit of Work + Identity Map**. The
  **Identity Map** guarantees one in-memory instance per DB row within a request
  (an in-request cache enabling cheap identity comparison and **batched** ops).
  The **Unit of Work** tracks all changes via snapshot diffing and persists them
  in one implicit transaction on **`em.flush()`** — you mutate entities and flush
  once. Never share an `EntityManager` across requests; use `RequestContext`
  (backed by `AsyncLocalStorage`) for request-scoped EMs.
- **Legacy note**: TypeORM and Sequelize predate Prisma/Drizzle and carry larger
  APIs and historically weaker end-to-end type-safety; choose them for ecosystem
  maturity (Sequelize) or AR/DM flexibility & Nest integration (TypeORM).

### 5. Migrations strategy (cross-cutting)

A **migration** is a versioned, committed, ordered change to the DB schema.
Across all tools the same discipline applies:

- **Generate from a schema diff, commit the SQL, apply forward in CI/prod.**
  Prisma: `migrate dev` (gen+apply locally) → `migrate deploy` (apply in prod).
  Drizzle: `drizzle-kit generate` → `migrate`. Kysely/TypeORM/Sequelize ship
  their own runners. MikroORM has `@mikro-orm/migrations`.
- **`push` is not a migration.** `prisma db push` / `drizzle-kit push` sync the
  schema directly with no history — fine for prototyping, **never** for shared/
  prod environments (no rollback, no audit, easy to drift).
- **Migration maturity** is a real selection factor: Prisma's shadow-DB-backed
  drift detection and `migrate deploy` are the most opinionated/mature; Drizzle
  and Kysely are lighter and give you raw SQL files you fully own.

### 6. The N+1 problem, eager/lazy loading & DataLoader (cross-cutting)

**N+1** is the canonical data-layer performance bug: one query fetches N parent
rows, then the code triggers **one query per parent** for a relation (N more) —
`1 + N` round-trips where 1–2 would do. It explodes silently under ORMs whose
**lazy loading** fetches a relation on property access, and under GraphQL
resolvers (one resolver per field per item).

- **Eager loading** is the primary fix: tell the ORM to load the relation up
  front in one query or a small fixed number — Prisma `include`, Drizzle `with`,
  Sequelize `include`, TypeORM `relations`/`leftJoinAndSelect`, MikroORM
  `populate`. **Lazy loading** fetches on demand (less memory, but the N+1 trap).
- **DataLoader** is the batching fix when eager loading isn't structurally
  possible (e.g. GraphQL): it **coalesces** the per-item key lookups within a tick
  into **one batched query** and caches within the request. Create a **new
  DataLoader per request** to avoid cross-user cache bleed. MikroORM has built-in
  dataloaders. This is the standard GraphQL N+1 remedy.

### 7. Transactions, pooling, raw SQL & repositories (cross-cutting)

- **Transactions**: every tool wraps a callback in a DB transaction — Prisma
  `$transaction` (array form for batched independent ops, **interactive** form
  for a callback with `tx`), Drizzle/Kysely `db.transaction(...)`, TypeORM
  `dataSource.transaction` / `QueryRunner`, MikroORM `em.transactional` (or the
  implicit transaction `em.flush()` already provides).
- **Connection pooling at the data layer**: the app holds a pool of DB
  connections; **size it to the database's connection ceiling**, not to traffic.
  In **serverless**, each function instance opens its own pool, so concurrent
  invocations can exhaust DB limits — front the DB with an external pooler
  (**PgBouncer** in transaction mode, Prisma Accelerate, Neon/Supabase poolers).
  Prisma historically managed its own pool (`connection_limit`, `pool_timeout`);
  with v7 driver adapters, pooling defaults come from the underlying driver. For
  the **driver-internal** pool mechanics of one DB, see that driver's docs.
- **Raw-SQL escape hatch**: keep one even with an ORM. Prisma `$queryRaw` /
  `$executeRaw` (tagged-template, parameterized) and **TypedSQL**; Drizzle/Kysely
  `sql\`...\`` template tag; Sequelize `sequelize.query`; TypeORM `query()`.
  **Always parameterize** — string-concatenated raw SQL is SQL injection.
- **Repository pattern**: wrap data access behind a repository interface so call
  sites depend on a method (`users.findActive()`), not the ORM. TypeORM/MikroORM
  ship `Repository` objects; with Prisma/Drizzle/Kysely you write thin repo
  modules. This isolates the ORM choice and keeps it swappable.
- **Seeding**: scripted insertion of baseline/dev data (Prisma `prisma db seed`
  via a `seed` script; others run a plain script against the client) — keep it
  idempotent and separate from migrations.

## Library comparison & selection

| Library | Kind | Schema source | Type-safety | Migrations | Edge / serverless | Best fit |
| --- | --- | --- | --- | --- | --- | --- |
| **Prisma** | ORM (schema-first) | `schema.prisma` DSL | Excellent (generated client) | Mature (`migrate dev`/`deploy`, drift) | Good (v7 Rust-free) | Max DX & type-safety; managed migration story |
| **Drizzle** | ORM-ish / SQL-first builder | TS schema | Excellent | Light, you-own-SQL (`drizzle-kit`) | Excellent (no engine, 1 query) | Edge/serverless, bundle-size, want-to-see-SQL |
| **Kysely** | Query **builder** (no relations) | TS `Database` type (codegen) | Excellent (inferred) | Built-in runner | Excellent | Complex/analytical SQL, full control + types |
| **TypeORM** | ORM (AR **and** DM) | Decorated entities | Good | Built-in | OK | NestJS apps; AR/DM flexibility |
| **Sequelize** | ORM (Active Record) | `Model` classes | Moderate (improving in v7) | `sequelize-cli` | OK | Mature ecosystem, legacy/broad DB support |
| **MikroORM** | ORM (DM + UoW + Identity Map) | Decorated entities | Good | Built-in | OK | DDD/Unit-of-Work, identity guarantees, batching |

**Selection guidance**

- **ORM vs builder vs raw driver**: rich object graph, change tracking, fast CRUD
  DX → **ORM**. Complex/analytical SQL with type-safety and no hidden queries →
  **query builder** (Kysely / Drizzle SQL-API). One hot, perf-critical path or a
  tiny script → **raw driver**. Most apps mix: an ORM for CRUD + a builder/raw
  for the few heavy queries.
- **Prisma vs Drizzle vs Kysely vs TypeORM**:
  - **Best end-to-end DX + migration maturity** → **Prisma**.
  - **Edge/serverless, minimal bundle, SQL-first, no codegen** → **Drizzle**.
  - **You think in SQL, want builder ergonomics + types, no ORM magic** →
    **Kysely**.
  - **NestJS, or you specifically want Active-Record or Data-Mapper choice** →
    **TypeORM**; **classic battle-tested ecosystem** → **Sequelize**;
    **Unit-of-Work / DDD identity semantics** → **MikroORM**.

## Practical patterns

- **Prefer eager loading by default; reach for DataLoader only where you can't
  eager-load** (GraphQL resolvers). Both beat lazy loading in a request hot path.
- **Use `migrate deploy` / `drizzle-kit migrate` in CI**, never `db push` /
  `kit push`, against shared environments — commit the generated SQL.
- **One pooler in serverless.** Point the app at PgBouncer (transaction mode) or
  Accelerate/Neon pooling so N function instances don't exhaust DB connections.
- **Keep a parameterized raw-SQL escape hatch** for the queries the ORM models
  awkwardly; don't fight the ORM for a window function — drop to `sql\`...\``.
- **Wrap the ORM in a repository module** so the data layer stays swappable and
  call sites don't import the client everywhere.
- **Make seeds idempotent** (upsert, not blind insert) so re-running is safe.
- **Pin to interactive transactions** when later writes depend on earlier reads
  within the same atomic unit (Prisma `$transaction(async tx => …)`).

## Anti-patterns

- **N+1 queries.** Iterating parents and touching a lazy relation per item.
  Symptom: a flood of near-identical single-row `SELECT`s in the query log. Fix:
  eager-load the relation (`include`/`with`/`relations`/`populate`) or batch with
  **DataLoader**. The cardinal data-layer performance bug.
- **`db push` / `kit push` to production.** No history, no rollback, silent drift.
  Use generated, committed migrations everywhere shared.
- **String-concatenated raw SQL.** `queryRaw("... " + userInput)` is SQL
  injection — always use the parameterized tagged-template form.
- **A pool per serverless invocation with no external pooler** — exhausts the
  DB's `max_connections` under concurrency. Front it with PgBouncer/Accelerate.
- **`SELECT *` via the ORM when you need three columns** — fetch only what you
  project (`select`) to cut payload and avoid over-fetching.
- **Sharing one long-lived `EntityManager`/identity-mapped context across
  requests** (MikroORM/TypeORM) — leaks state between users; use request-scoped
  contexts (`RequestContext` / `AsyncLocalStorage`).
- **Treating Kysely or Drizzle's SQL API like an ORM** — there's no relation
  graph or identity map; you compose SQL, you don't navigate objects.

## Troubleshooting

- **Mysterious burst of identical `SELECT`s** → N+1; turn on query logging,
  eager-load or add DataLoader.
- **"too many connections" / pool timeout under load (esp. serverless)** → pool
  sized above the DB ceiling × instance count; reduce per-instance limit and add
  an external transaction-mode pooler.
- **Prisma types out of date after a schema edit** → re-run `prisma generate`
  (it's a generated client; the build won't pick up changes otherwise).
- **PgBouncer transaction mode breaking prepared statements / Prisma** → set
  `pgbouncer=true` on the connection string and follow the pooler-mode guidance;
  prepared-statement caching conflicts with transaction-pooling.
- **Kysely/Drizzle "column doesn't exist" only at runtime** → the generated
  `Database` type / TS schema drifted from the DB; re-introspect / re-run
  kysely-codegen / `drizzle-kit pull`.
- **MikroORM changes not saved** → you forgot `em.flush()`; the Unit of Work
  persists on flush, not on mutation.
- **Migration "drift detected" (Prisma)** → the DB diverged from migration
  history (a manual change or a `db push`); resolve with `migrate diff` /
  baselining rather than another `push`.

## References

- Prisma — Prisma Client overview (generated client, type-safe queries): https://www.prisma.io/docs/orm/prisma-client
- Prisma — Prisma Migrate (`migrate dev` / `deploy`, db push): https://www.prisma.io/docs/orm/prisma-migrate
- Prisma — Connection pool (`connection_limit`, serverless, PgBouncer, v7 driver adapters): https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections/connection-pool
- Prisma — Relation mode (`prisma` vs `foreignKeys`): https://www.prisma.io/docs/orm/prisma-schema/data-model/relations/relation-mode
- Prisma — Release notes / changelog (v7 Rust-free client): https://www.prisma.io/changelog
- Drizzle ORM — Why Drizzle / overview (no codegen, no runtime engine, 1 query, serverless): https://orm.drizzle.team/docs/overview
- Drizzle ORM — Migrations & drizzle-kit (generate/migrate/push/pull): https://orm.drizzle.team/docs/migrations ; https://orm.drizzle.team/docs/kit-overview
- Drizzle ORM — Query data & relational queries (`with`): https://orm.drizzle.team/docs/data-querying ; https://orm.drizzle.team/docs/rqb-v2
- Kysely — Introduction (type-safe builder, not an ORM, no relations): https://kysely.dev/docs/intro
- Kysely — Expressions (composable query building blocks) & Relations recipe: https://kysely.dev/docs/recipes/expressions ; https://kysely.dev/docs/recipes/relations
- TypeORM — Active Record vs Data Mapper: https://typeorm.io/docs/guides/active-record-data-mapper/
- TypeORM — Entities & decorators; Repository: https://typeorm.io/docs/entity/entities/ ; https://typeorm.io/docs/working-with-entity-manager/working-with-repository/
- Sequelize — Eager loading (`include`) & Associations: https://sequelize.org/docs/v6/advanced-association-concepts/eager-loading/ ; https://sequelize.org/docs/v6/core-concepts/assocs/
- MikroORM — Unit of Work & transactions; Identity Map & request context: https://mikro-orm.io/docs/unit-of-work ; https://mikro-orm.io/docs/identity-map
- MikroORM — Dataloaders (built-in N+1 batching): https://mikro-orm.io/docs/dataloaders
- DataLoader — Solving the N+1 problem (GraphQL.js guide): https://www.graphql-js.org/docs/n1-dataloader/
