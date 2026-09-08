---
title: "Node.js Build Tooling & Bundlers"
description: "This reference is about **turning Node.js + TypeScript source into a production"
---

# Node.js Build Tooling & Bundlers

## Overview

This reference is about **turning Node.js + TypeScript source into a production
artifact** — a bundled server, a single-file CLI, a Lambda zip, or a publishable
library — and picking the tool that fits each shape. It is the *build-time* companion
to three sibling references that own adjacent layers:

- **`nodejs-typescript-and-runtime-features`** — *runtime* TypeScript: native
  type-stripping and dev runners (`tsx`, `ts-node`) that execute `.ts` directly. This
  file covers `tsx` only at the boundary — "dev runner vs prod bundler."
- **`nodejs-module-resolution`** — the resolution algorithm and `package.json`
  `"exports"`/conditions. This file *reads* those fields but does not re-derive them.
- **`nodejs-package-management-supply-chain`** / **`devops-containers-cicd`** —
  `npm`/`pnpm` install, lockfiles, publishing/provenance. This file produces the
  artifact; those own how it is installed and shipped.

The mental model: **most Node backends do not need a bundler at all.** Reach for one
only when single-file packaging, startup-time/cold-start, or library output quality
justifies it. Then choose by *output shape*: **esbuild/swc** to transpile fast,
**tsup** for a dual-format library with types, **Rollup** for the cleanest library
bundle, **@vercel/ncc** to collapse everything into one file.

## Core concepts

### 1. The bundle-vs-ship-source decision for Node backends

Unlike the browser (where every byte is downloaded), a Node backend already has the
files on disk, so bundling is **optional and situational**. Ship **source +
`node_modules`** for a normal long-lived server in a container: simplest path, honest
stack traces, native addons resolve normally. **Bundle** when you need:

- **A single distributable file** — a CLI published to npm (smaller install, fewer
  files), a GitHub Action, or a Lambda/Edge artifact that must be self-contained.
- **Faster cold starts** — serverless functions pay per-file I/O at init; one
  pre-resolved file with **dead-code elimination** (DCE) reduces parse/resolve cost.
- **A library with multiple output formats** (ESM + CJS) and bundled internal modules.

**Tree-shaking / DCE** statically drop unused exports; they work on **ES module**
syntax (`import`/`export`), not CommonJS `require`, which is why ESM input matters.
**Minification** (whitespace + identifier renaming + syntax compression) shrinks bytes
— useful for libraries and Lambda size limits, rarely worth the debugging cost for a
plain server. Key caveat: keep **native addons** (`.node`), workers, and dynamic
`require` paths **external** — bundlers can't trace them.

### 2. esbuild — the fast default

[esbuild](https://esbuild.github.io/) is a Go-based bundler/transpiler whose draw is
raw speed. Two entry points:

- **Transform API** (`esbuild.transform(code, opts)`) — processes a single in-memory
  string "in an isolated environment that's completely disconnected from any other
  files." No bundling, no plugins. Use it to transpile one file (TS→JS) in a pipeline.
- **Build API** (`esbuild.build(opts)`) — the primary interface: reads `entryPoints`,
  follows imports, writes to `outfile`/`outdir`. Supports `bundle`, plugins, watch/rebuild.

Node-relevant options:

- **`platform: 'node'`** — sets `format` to `cjs`, marks Node built-ins external, and
  adds the `node` export condition. (`'browser'` → `iife`; `'neutral'` → `esm`.)
- **`format`** — `'esm'` | `'cjs'` | `'iife'`. Override the platform default explicitly
  for ESM output on Node (`.mjs` or `"type":"module"`).
- **`bundle: true`** — inline imported deps (off by default).
- **`external: ['pg', '*.node']`** and **`packages: 'external'`** — the latter marks
  *all* dependencies external (the common server recipe: bundle your code, leave
  `node_modules` on disk).
- **`minify`**, **`treeShaking`** (on by default when bundling; honors `package.json`
  `sideEffects`), **`target: 'node20'`**, **`sourcemap`** (`true`/`'inline'`/`'external'`).
- **Hard limit — no type-checking.** esbuild strips types; per the docs, *"esbuild does
  not do any type checking so you will still need to run `tsc --noEmit` in parallel."*
  It also never emits `.d.ts`. Enable `isolatedModules` in `tsconfig.json` because each
  file is compiled independently. It honors `experimentalDecorators` but **not**
  `emitDecoratorMetadata` (that needs the type system).

### 3. swc — Rust-speed transpilation

[SWC](https://swc.rs/) ("Speedy Web Compiler") is a Rust-based platform for compiling
TS/JS. `@swc/core` exposes `transform` / `transformSync` / `transformFile` (plus
`minify` and `parse`); it is "mainly useful for build-tool authors." Configured by
**`.swcrc`** (or inline `jsc`):

- **`jsc.parser.syntax`** = `"typescript"` | `"ecmascript"`, with `tsx`/`jsx` and
  **`decorators`** flags.
- **`jsc.target`** (e.g. `"es2022"`), **`jsc.transform.legacyDecorator`** /
  **`decoratorMetadata`** — the SWC equivalents that **do** support
  `emitDecoratorMetadata`, which is why **NestJS/TypeORM stacks favor swc** over esbuild.
- **`module.type`** = `"commonjs"` | `"es6"` | `"umd"` | `"amd"`; **`minify: true`**.

**swc vs esbuild:** both are far faster than Babel/`tsc` and both skip type-checking.
esbuild is also a *bundler*; swc is primarily a *compiler/transform* (bundling via the
separate, less-used `@swc/pack`). Pick **swc** for decorator metadata or its ecosystem
(Next.js, Jest via `@swc/jest`); pick **esbuild** when you want one tool that also
bundles. The dev-time runtime loader `@swc-node/register` belongs to
`nodejs-typescript-and-runtime-features`.

### 4. tsup — the library-build sweet spot

[tsup](https://tsup.egoist.dev/) is "the simplest and fastest way to bundle your
TypeScript libraries," an **esbuild wrapper** that adds the two things esbuild lacks for
libraries: easy **dual-format output** and **`.d.ts` generation**. Zero-config defaults
plus `tsup.config.ts`:

- **`entry`** (entry points), **`format: ['esm', 'cjs']`** (or `--format esm,cjs`) →
  emits both `.js`/`.mjs` + `.cjs` so one package serves ESM and CJS consumers.
- **`dts: true`** (or `--dts`) → generates a bundled `.d.ts` (delegates to the TS
  compiler) — the feature that makes it a *library* tool, not just a transpiler.
- **`target`**, **`minify`**, **`sourcemap`**, **`splitting`** (code-splitting, ESM
  only), **`treeshake`**, **`--watch`**, **`--no-bundle`** (transpile-only mode).

Note: tsup's README now points to **`tsdown`** (a Rolldown-based successor) as the
recommended direction with a migration guide; tsup remains widely used and the patterns
here transfer. Use tsup (or tsdown) for a **publishable package**; for an *application*
you usually want a plain esbuild build or no bundle at all.

### 5. Rollup — when output quality and plugins matter

[Rollup](https://rollupjs.org/) "compiles small pieces of code into something larger,
such as a library or application," and it pioneered **tree-shaking** ("statically
analyzes the code you are importing, and will exclude anything that isn't actually
used" — "more effective than simply running an automated minifier"). Reach for Rollup
over esbuild when:

- You want the **cleanest library bundle** — Rollup's output is famously readable and
  flat, with the best tree-shaking; many published packages are built with it.
- You need **output formats** beyond esbuild's set: **`es`**, **`cjs`**, **`umd`**,
  **`iife`**, **`amd`**, **`system`** (UMD/AMD/SystemJS matter for some consumers).
- You need its **plugin ecosystem** (`@rollup/plugin-node-resolve`,
  `@rollup/plugin-commonjs`, `@rollup/plugin-typescript`) or **code-splitting** with
  precise control. The trade-off is speed: Rollup is slower than esbuild/swc.

(Rolldown — a Rust port of Rollup — and tsdown are the emerging fast successors.)

### 6. @vercel/ncc — single-file compilation

[`@vercel/ncc`](https://github.com/vercel/ncc) compiles "a Node.js module into a single
file, together with all its dependencies, gcc-style." Built on webpack under the hood,
it does static analysis to **relocate assets** and handles binary addons and dynamic
requires better than a naive bundle. The canonical use cases are exactly the
self-contained ones: **CLIs, GitHub Actions** (a committed `dist/index.js`), and
**Lambda**. CLI:

```bash
ncc build src/index.ts -o dist   # -m minify, -s source-map, -e <pkg> external, -w watch
```

It handles TypeScript natively. Choose ncc when the deliverable is *"one file, drop it
anywhere, no `node_modules`"*; choose esbuild/tsup when you want speed or library
formats and are willing to keep some deps external.

### 7. Source maps for Node + tsconfig path-alias resolution

Two production-correctness concerns that bite bundled/transpiled Node code:

- **Source maps.** Generate them in the bundler (`sourcemap: true` / `--sourcemap` /
  `-s`), then run Node with **`--enable-source-maps`** (or `NODE_OPTIONS`) so traces
  "report stack traces relative to the original source file." Caveat from the docs: it
  "can introduce latency... when `Error.stack` is accessed" — fine for most servers,
  note it for hot error paths. If you override `Error.prepareStackTrace`, call the
  original to preserve mapping.
- **TS path aliases (`compilerOptions.paths`) in bundles.** `tsc` rewrites nothing at
  runtime, so `@app/*` aliases break unless the bundler resolves them. esbuild reads
  `paths` from `tsconfig.json` — **but only when `--bundle` is set** (in transpile-only
  mode the alias survives into output and fails at runtime). For non-bundling builds use
  esbuild's `alias` option, a plugin (`esbuild-plugin-tsconfig-paths`), or a runtime
  resolver. Rollup uses `@rollup/plugin-alias` / `rollup-plugin-typescript-paths`.

### 8. tsx / native TS for dev vs a bundler for prod

`tsx` ("TypeScript Execute") runs `.ts` directly in Node, **powered by esbuild** as a
*transpiler, not a bundler*. It is a **dev/script runner** (watch mode, zero-config,
no installation via `npx tsx`) and, like esbuild, **does not type-check** — it lets you
run code without being blocked by type errors. The decision rule: **`tsx` (or Node's
native type-stripping) for development and one-off scripts; a real bundler/build step
for production.** Don't ship a server by running `tsx` in prod — produce a built
artifact and run plain `node`. (Deep runtime-loader internals → the runtime-features
reference.)

## Tool comparison

| Tool | Engine | Bundles? | Type-checks? | Emits `.d.ts`? | Best for |
| --- | --- | --- | --- | --- | --- |
| **esbuild** | Go | Yes | No (`tsc --noEmit`) | No | Fast app/server builds; the default transpiler+bundler |
| **swc** | Rust | Mostly transpile | No | No | Fast transpile; decorator metadata (Nest/TypeORM); Jest/Next |
| **tsup** | esbuild wrapper | Yes | No (runs tsc for dts) | Yes (`--dts`) | Publishable libraries needing dual ESM+CJS + types |
| **Rollup** | JS | Yes | Via plugin | Via plugin | Highest-quality library bundle; many output formats; plugins |
| **@vercel/ncc** | webpack | Yes (single file) | No | No | One-file CLIs, GitHub Actions, Lambda |
| **tsx** | esbuild | No (runner) | No | No | Dev/scripts only — not a production build tool |

## Practical patterns

- **Server recipe (esbuild):** `bundle: true, platform: 'node', format: 'esm',
  target: 'node20', packages: 'external', sourcemap: true` → one entry file, deps stay
  in `node_modules`; run with `node --enable-source-maps dist/index.js`.
- **Lambda / single-file recipe:** drop `packages: 'external'` so deps are inlined (or
  use `ncc build`), add `minify: true`, keep only true natives external. Smaller cold
  start, self-contained zip.
- **Library recipe (tsup):** `entry: ['src/index.ts'], format: ['esm','cjs'],
  dts: true, sourcemap: true, treeshake: true`, and wire `package.json` `exports` to
  the emitted ESM/CJS/`.d.ts` (resolution details → `nodejs-module-resolution`).
- **Always pair a fast transpiler with a type gate** — esbuild/swc/tsx skip types, so
  run `tsc --noEmit` (or `tsc -p tsconfig.build.json --emitDeclarationOnly` for types)
  in CI alongside the build. Speed for builds, `tsc` for correctness.
- **Set `isolatedModules: true`** in any project transpiled file-by-file (esbuild/swc/
  tsx/Babel) so you catch unsafe cross-file `type` re-exports at design time.

## Anti-patterns

- **Bundling a normal long-lived server "for performance."** A containerized server
  rarely benefits; you trade simpler stack traces and native-addon resolution for
  little. Bundle for *packaging* (CLI/Lambda/Action) or *cold start*, not by reflex.
- **Trusting a fast transpiler to catch type errors.** esbuild/swc/tsx emit happily on
  broken types. No `tsc --noEmit` in CI = type safety lost.
- **Shipping a bundle with no source maps**, or generating maps but forgetting
  `--enable-source-maps` — every prod stack trace points at minified output.
- **Inlining native addons / dynamic `require` targets.** Bundlers can't trace `.node`
  files or runtime-computed paths; mark them `external` or the artifact crashes at load.
- **Expecting `tsconfig` `paths` to "just work."** They only resolve when the bundler
  is told to (esbuild needs `--bundle`; otherwise add a plugin/alias) — easy silent
  `ERR_MODULE_NOT_FOUND` in production.
- **Running `tsx`/`ts-node` as your production process.** Per-request transpile cost and
  no build artifact; build once, run `node`.

## Troubleshooting

- **`ERR_REQUIRE_ESM` / "exports is not defined" at runtime** → format mismatch. The
  bundle is ESM but loaded as CJS (or vice-versa); set `format` to match `package.json`
  `"type"` and the file extension (`.mjs`/`.cjs`).
- **Stack traces point at bundled/minified code** → you didn't run with
  `--enable-source-maps`, or the bundler didn't emit a map (`sourcemap: true`).
- **`Cannot find module '@app/...'`** → `tsconfig` `paths` weren't resolved at build;
  enable `--bundle` (esbuild), add a paths plugin, or use `alias`.
- **Decorator metadata missing (DI fails in Nest/TypeORM)** → esbuild ignores
  `emitDecoratorMetadata`; switch that build to **swc** (`decoratorMetadata: true`) or `tsc`.
- **No `.d.ts` in the published package** → esbuild/swc never emit declarations; use
  **tsup `--dts`** or run `tsc --emitDeclarationOnly`.
- **Bundle crashes loading a native addon** → mark it (and `*.node`) `external`; native
  binaries can't be inlined.
- **Type error slipped to production** → the fast transpiler doesn't type-check; add a
  `tsc --noEmit` step to CI.

## References

**Bundle-vs-ship-source, tree-shaking & DCE (Node backends)**
- esbuild — bundling & the `bundle`/`packages` options: https://esbuild.github.io/api/
- Rollup — what it is + tree-shaking definition: https://rollupjs.org/introduction/
- Node.js — CLI (`--enable-source-maps`, runtime flags for built artifacts): https://nodejs.org/api/cli.html

**esbuild**
- esbuild — API (transform vs build, platform, format, external, packages, minify, sourcemap, tree shaking): https://esbuild.github.io/api/
- esbuild — Getting started (build/transform examples): https://esbuild.github.io/getting-started/
- esbuild — Content types / TypeScript (no type-checking → `tsc --noEmit`, isolatedModules, decorators): https://esbuild.github.io/content-types/

**swc**
- SWC — Getting started & overview: https://swc.rs/docs/getting-started
- SWC — `.swcrc` configuration (jsc.parser, target, transform, module, minify): https://swc.rs/docs/configuration/swcrc
- SWC — `@swc/core` usage (transform/transformSync/transformFile): https://swc.rs/docs/usage/core

**tsup**
- tsup — docs (esbuild-powered, format, dts, entry, watch): https://tsup.egoist.dev/
- tsup — README / repo (dual ESM+CJS, `--dts`, tsdown successor note): https://github.com/egoist/tsup
- esbuild — API (the engine tsup wraps): https://esbuild.github.io/api/

**Rollup**
- Rollup — Introduction (output formats es/cjs/umd/iife/amd/system, tree-shaking, libraries): https://rollupjs.org/introduction/
- Rollup — Configuration options (`output.format`, code-splitting): https://rollupjs.org/configuration-options/
- esbuild — API (speed/feature contrast for the when-Rollup-over-esbuild call): https://esbuild.github.io/api/

**@vercel/ncc**
- @vercel/ncc — repo (single-file compile, `ncc build`, `-m`/`-s`/`-e`/`-w`, assets/addons): https://github.com/vercel/ncc
- Node.js — CLI (running the produced single file): https://nodejs.org/api/cli.html
- esbuild — API (alternative bundler for the same single-file goal): https://esbuild.github.io/api/

**Source maps for Node + tsconfig path-alias resolution**
- Node.js — `--enable-source-maps` (stack traces to original source, `Error.stack` latency): https://nodejs.org/api/cli.html#--enable-source-maps
- esbuild — API (`sourcemap`, `alias`, reading tsconfig `paths` under `--bundle`): https://esbuild.github.io/api/
- esbuild-plugin-tsconfig-paths (alias resolution when not bundling): https://www.npmjs.com/package/esbuild-plugin-tsconfig-paths

**tsx / native TS for dev vs bundler for prod**
- tsx — site (run TS directly, esbuild-powered, dev runner): https://tsx.is/
- tsx — FAQ / TypeScript (no type-checking; transpiler not bundler): https://tsx.is/faq
- esbuild — Content types (the no-type-check engine behavior tsx inherits): https://esbuild.github.io/content-types/
