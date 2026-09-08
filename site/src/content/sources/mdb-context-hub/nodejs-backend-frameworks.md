---
title: "Node.js Backend Frameworks (Fastify, NestJS, Hono)"
description: "Three post-Express Node.js/TypeScript backend frameworks. They share the HTTP-handler foundation captured in the express-patterns hub reference (middleware chains, routing, error handling, graceful sh"
---

# Node.js Backend Frameworks: Fastify, NestJS, and Hono

Three post-Express Node.js/TypeScript backend frameworks. They share the HTTP-handler foundation captured in the `express-patterns` hub reference (middleware chains, routing, error handling, graceful shutdown, security hardening) — read that first; this reference covers what each framework does *differently*.

> Full reference: `~/.claude/skills/software-engineering-patterns/references/nodejs-backend-frameworks.md`. Cross-refs: Express baseline → express-patterns; API surface design → api-design-patterns; backend architecture → backend-patterns; auth flows → web-auth-patterns; Zod/TypeBox depth → zod-schema-validation; edge/Bun/Deno runtimes → programming-languages/javascript-runtimes-deno-bun-edge.

## The spectrum
- **NestJS** — heavyweight, opinionated architecture + DI container + enterprise modules (decorator/Angular-style). Node only; uses Express OR Fastify as the HTTP adapter; no edge runtimes.
- **Fastify** — mid-weight, Express-like ergonomics + raw speed + built-in JSON-Schema validation/serialization; minimal opinions. Node only.
- **Hono** — lightweight (~14KB), Web-Standards (Request/Response) based, edge-native, tight type inference. Runs on Cloudflare Workers, Deno, Bun, Lambda, Fastly, Node.

Synthetic JSON throughput: Hono ~78k req/s, Fastify ~62k req/s. Raw speed rarely decides real apps — DB/business logic dominate. Choose on architecture, runtime target, team conventions.

## Fastify
- **Plugins + encapsulation context** governs which decorators/hooks/schemas a route sees; child contexts are isolated. **`fastify-plugin` (`fp`)** breaks encapsulation on purpose — wrap shared capabilities (DB, auth decorator) so parent/siblings see them. "Decorator not defined on parent" = missing `fp`.
- **Lifecycle hooks** (all encapsulated except onClose): onRequest → preParsing → preValidation → preHandler → handler → preSerialization → onSend → onResponse. `onError` is read-only; change error responses via `setErrorHandler()`.
- **JSON Schema** on a route validates input AND compiles response serialization (fast-json-stringify) — a big speed source. `addSchema()` registers reusable schemas (encapsulated). **TypeBox + @fastify/type-provider-typebox** = one schema is both runtime validator and TS type. Async custom validators must return `{error}`, not throw (thrown → unhandled rejection → crash).
- **Decorators**: `decorateRequest('x', {})` shares ONE object across requests — init `null`, assign in `onRequest`.
- **Gotchas**: returning `undefined` from async handler = "no response"; mixing `return value` + `reply.send()` discards the second; after async `reply.send()` do `return reply`; arrow-function handlers don't bind `this`.

## NestJS
- **Modules + hierarchical DI**: providers encapsulated by default; `exports` is the public API; other modules access via `imports`. `@Global()` sparingly.
- **Providers + scopes**: default singleton; `Scope.REQUEST` (per request, perf cost, bubbles up injection chain); `Scope.TRANSIENT` (per injection site). Custom providers: useClass/useValue/useFactory/useExisting.
- **Request pipeline (fixed order)**: Middleware → Guards → Interceptors(pre) → Pipes → Handler → Interceptors(post) → Exception Filters. Guards = authZ; Interceptors = wrap handler (RxJS, transform req/resp); Pipes = validate/transform input; Filters = shape error responses.
- **Dynamic modules** (`forRoot`/`forFeature` → DynamicModule) for configurable infra. **Circular deps** → `forwardRef()` on both sides; treat as a smell, prefer refactor.
- **HTTP adapter**: swap `@nestjs/platform-express` for `@nestjs/platform-fastify` for Fastify throughput under Nest's architecture.

## Hono
- **Web-Standards core + Context `c`**: built on WHATWG Request/Response → runs everywhere. Middleware is `async (c, next) => {...}` (Koa onion model), no separate req/res.
- **Routing + typed generics**: default `RegExpRouter` is fastest on Workers. `new Hono<{ Variables, Bindings }>()` makes `c.get('user')` and `c.env.DB` typed end-to-end.
- **Validation + RPC**: `@hono/zod-validator` (+ Valibot/Typia/ArkType) gives typed `c.req.valid()`. RPC mode: export app type, `hc<typeof app>(url)` infers paths/args/returns — type-safe client, no codegen.
- **Batteries**: JWT, basic/bearer auth, CORS, CSRF, secure-headers, ETag, cache, compression, body-limit, IP restriction, timing, timeout, SSE, WebSockets, JSX SSR. Edge wins are mostly geography (Workers at nearest PoP) + low overhead. Recommended for Node→Bun migration.

## Choosing
- **NestJS** — enterprise architecture, 3+ team, long-lived backend, first-party modules, Angular/.NET background, edge not required.
- **Fastify** — standalone Node API, Express-shaped + faster + built-in validation, pick-your-own ORM/auth.
- **Hono** — Cloudflare Workers/Vercel Edge/Deno/Bun/Lambda, smallest/fastest/most-inferred, serverless/edge, Node→Bun.
- **Express** — max middleware ecosystem/familiarity, no strong perf/validation/edge need.
- **NestJS + Fastify adapter** = Nest architecture + Fastify speed. NestJS does NOT run on edge runtimes.

## Sources
Fastify docs (Encapsulation, Plugins, Hooks, Validation-and-Serialization, Decorators, Errors); Nearform Fastify plugin guide; Strapi Fastify APIs; NestJS docs (Modules, Circular dependency, Performance/Fastify); DeepWiki NestJS request pipeline; LogRocket circular deps; Hono docs (Concepts, RPC, Validation, Benchmarks, Stacks); Cloudflare Hono story; freeCodeCamp Hono; Encore NestJS-vs-Fastify-vs-Hono (2026); Better Stack Hono-vs-Fastify; HireNodeJS frameworks 2026.
