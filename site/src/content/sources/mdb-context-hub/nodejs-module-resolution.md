---
title: "Node.js Module Resolution & ESM/CJS Interop"
description: "This reference is about HOW Node.js turns a specifier into a loaded module — the two"
---

# Node.js Module Resolution & ESM/CJS Interop

## Overview

This reference is about **HOW Node.js turns a specifier into a loaded module** — the two
resolution algorithms (CommonJS `require` and ESM) and the interop seam between them. It
assumes you already know *what* a module is and *how to write one*; that intro is owned by
the **`javascript-nodejs`** reference. Two other siblings own adjacent layers and are
explicitly out of scope here:

- **`nodejs-typescript-and-runtime-features`** — TypeScript native type-stripping, the
  `--experimental-strip-types` / `--experimental-transform-types` flags, and the
  `.ts`/`.mts` import-extension rules. This file covers JS/JSON/Wasm resolution only.
- **Bundlers/transpilers** (esbuild, webpack, Vite, `tsc`'s `moduleResolution`) — they
  reimplement resolution with their own rules. This file is the **Node runtime** resolver.

The two mental models you must hold separately: **CommonJS resolution is synchronous,
filesystem-probing, and extension-tolerant** (`require('./util')` tries `util`, `util.js`,
`util.json`, `util.node`, then `util/index.js`…). **ESM resolution is URL-based, mostly
specifier-exact, and requires file extensions** (`import './util.js'` — no extension
guessing, no directory index). The `"exports"`/`"imports"` package.json fields, the
condition system, and the dual-package hazard are the shared machinery that both algorithms
now route through, and `require(esm)` (stable since the v20.19/v22.12 LTS lines) is the
bridge that finally lets CommonJS load ES modules synchronously.

## Core concepts

### 1. The CommonJS `require(X)` resolution algorithm

`require(X)` from a module at path `Y` runs a fixed, synchronous sequence (the
spec-pseudocode names are load-bearing — they appear in errors and docs):

1. **Core / `node:` builtin** → return it and STOP. The `node:` prefix always hits the
   builtin and bypasses `require.cache`.
2. **`/`, `./`, `../`** (relative/absolute) → `LOAD_AS_FILE(Y+X)` then `LOAD_AS_DIRECTORY(Y+X)`.
3. **`#`-prefixed** → `LOAD_PACKAGE_IMPORTS` (private internal specifiers, concept 4).
4. `LOAD_PACKAGE_SELF` (self-reference by package name), then
5. `LOAD_NODE_MODULES(X, dirname(Y))` — the `node_modules` walk.
6. Else THROW `MODULE_NOT_FOUND`.

The sub-routines:

- **`LOAD_AS_FILE(X)`** probes extensions in order: `X` (verbatim) → `X.js` → `X.json` →
  `X.node` (native addon). The `.js` case consults the **closest `package.json` `"type"`**
  to decide ESM vs CJS (and otherwise detects module syntax).
- **`LOAD_INDEX(X)`** probes `X/index.js` → `X/index.json` → `X/index.node`.
- **`LOAD_AS_DIRECTORY(X)`** reads `X/package.json`'s `"main"`, runs `LOAD_AS_FILE` then
  `LOAD_INDEX` on it, and falls back to `LOAD_INDEX(X)`.
- **`LOAD_NODE_MODULES(X, START)`** iterates `NODE_MODULES_PATHS(START)`, trying
  `LOAD_PACKAGE_EXPORTS` then `LOAD_AS_FILE` then `LOAD_AS_DIRECTORY` in each dir.
- **`NODE_MODULES_PATHS(START)`** generates the walk: append `node_modules` at every
  ancestor directory up to the filesystem root, then `GLOBAL_FOLDERS`. So
  `/home/ry/projects/foo.js` requiring `bar` searches
  `/home/ry/projects/node_modules/bar` → `/home/ry/node_modules/bar` →
  `/home/node_modules/bar` → `/node_modules/bar`. This array is exposed as `module.paths`.

`require.cache` keys loaded modules by resolved filename (delete a key to force reload).
`require.resolve(req[, {paths}])` runs the machinery without loading; `require.resolve.paths(req)`
returns the search list (or `null` for a core module). `require.main` is the entry module —
`require.main === module` is the CJS "am I the entry point?" idiom. `NODE_PATH` (colon-/
semicolon-delimited absolute paths) is a legacy prepend to the walk; prefer `"exports"` over it.

### 2. The ESM resolution algorithm

ESM resolution is URL-based and specified as **`ESM_RESOLVE(specifier, parentURL)` → `{ format, resolved }`**:

1. Valid URL → parse and reserialize.
2. `/`, `./`, `../` → resolve relative to `parentURL` (a `file:` URL).
3. `#…` → `PACKAGE_IMPORTS_RESOLVE`.
4. Bare specifier → **`PACKAGE_RESOLVE`**: if it's a builtin, return `node:` + name; else walk
   `node_modules`, read `package.json`, and if `"exports"` exists call
   **`PACKAGE_EXPORTS_RESOLVE`**, else resolve `"main"`/subpath directly.
5. For `file:` URLs: reject percent-encoded `/` or `\`; **throw `ERR_UNSUPPORTED_DIR_IMPORT`
   for a directory** (no index lookup); **throw `ERR_MODULE_NOT_FOUND` if absent**; then set
   format via `ESM_FILE_FORMAT`.

**`PACKAGE_EXPORTS_RESOLVE`** and **`PACKAGE_TARGET_RESOLVE`** evaluate the `"exports"` map:
target objects are walked **in insertion order**, returning the first key that is `"default"`
or present in the active condition set; arrays try each entry; `null` blocks. **`ESM_FILE_FORMAT`**
maps extension → format: `.mjs`→`module`, `.cjs`→`commonjs`, `.json`→`json`, `.wasm`→`wasm`,
`.js`→`"type"`-driven (or syntax-detected), no-extension→`"type"` or detection.

The consequences that bite developers: **file extensions are mandatory** (`import './x'`
fails — use `'./x.js'`), **directory indexes don't work** (`import './lib'` fails — use
`'./lib/index.js'`), and a package with `"exports"` is **encapsulated** (concept 3).

### 3. `package.json` `"exports"` — conditional exports, subpaths, patterns, encapsulation

`"exports"` is the modern public-API surface for a package. Three powers:

- **Conditional exports** — map the same specifier to different files by environment. The
  condition keys, in the documented **most-specific-to-least order**: `"types"` (MUST be
  first, for type systems), `"node-addons"` (Node with native addons; off under
  `--no-addons`), `"node"` (any Node), `"import"` (loaded via `import`/`import()`),
  `"require"` (loaded via `require()`), `"module-sync"` (via `import`/`import()`/`require()` —
  a synchronous ESM with no top-level await), `"default"` (MUST be last). **Key order is
  significant** — the resolver returns the first match, so an `"import"` listed after
  `"default"` is dead. `"import"` and `"require"` are mutually exclusive at resolve time.
  Custom community conditions are matched via `node --conditions=<name>` (`-C`).

  ```json
  { "exports": { "types": "./index.d.ts", "import": "./index.mjs", "require": "./index.cjs" } }
  ```

- **Subpath exports** — expose specific deep entry points: `{ ".": "./index.js",
  "./feature": "./src/feature.js" }`. **Subpath patterns** use `*` as a **flexible string
  substitution (NOT a glob)**: `"./features/*.js": "./src/features/*.js"` maps
  `pkg/features/x.js` → `./src/features/x.js`, and `*` spans `/`. Map a target to `null` to
  block a private subtree (`"./features/internal/*": null`).

- **Encapsulation** — once `"exports"` exists, **only listed subpaths are importable**;
  everything else throws **`ERR_PACKAGE_PATH_NOT_EXPORTED`**. Add `"./package.json":
  "./package.json"` if consumers need it. (Encapsulation is not "strong" — an absolute path
  `require('/abs/node_modules/pkg/secret.js')` still works.) **Exports sugar**: when only
  `"."` exists, `"exports": "./index.js"` is shorthand for `{ ".": "./index.js" }`.

### 4. `package.json` `"imports"` — private `#` internal specifiers

`"imports"` defines specifiers **only resolvable from inside the same package**. Keys MUST
start with `#` (to disambiguate from bare external specifiers). Targets can be **internal
files OR external packages**, and support the **same conditions and `*` patterns** as
`"exports"`:

```json
{ "imports": { "#dep": { "node": "dep-node-native", "default": "./dep-polyfill.js" },
               "#internal/*.js": "./src/internal/*.js" } }
```

Then `import dep from '#dep'` / `import x from '#internal/util.js'` resolve per condition.
Unlisted `#` specifiers throw **`ERR_PACKAGE_IMPORT_NOT_DEFINED`**. This is the standard
replacement for fragile `../../..` relative paths and for swapping implementations by env.

### 5. The dual-package hazard

When one package ships **both** a CJS and an ESM build (via `import`/`require` conditions), an
app can end up loading **both copies** — once through each entry. The hazard:

- **Two instances** of the module exist simultaneously; **module-level state diverges**
  (caches, registries, singletons are not shared).
- **`instanceof` breaks** — a class from the ESM copy is not the same identity as the class
  from the CJS copy, so `x instanceof Pkg.Thing` fails across the seam.

Two documented cures: **(a) ESM-first with a thin CJS wrapper** — author in ESM and make the
`"require"` target a `.cjs` that does `module.exports = require('./index.js')` (now viable
because `require(esm)` works, concept 6); or **(b) isolate all stateful logic into a single
CJS file** that *both* the ESM and CJS entry points load (the ESM entry uses `createRequire`),
so there is exactly one state object. With `require(esm)` unflagged, shipping a **single ESM
build** consumable by both `import` and `require` is increasingly the simplest answer.

### 6. ESM ↔ CJS interop: `require(esm)`, importing CJS, `createRequire`

- **`require(esm)` — synchronous require of ES modules.** Timeline: added behind
  `--experimental-require-module` in **v22.0.0** (backported to v20.17), **unflagged/default
  in v23** and across the LTS lines (**v20.19.0+, v22.12.0+**), now marked stable. With it,
  `require()` of an ES module no longer throws `ERR_REQUIRE_ESM`. **Constraint:** the target
  must be unambiguously ESM (`.mjs` or `"type":"module"`) and **fully synchronous** — a
  top-level `await` anywhere in its graph throws **`ERR_REQUIRE_ASYNC_MODULE`**. Disable with
  `--no-experimental-require-module`. The returned object is the module namespace: the ESM
  default is on `.default`, and (v23+) a `'module.exports'` key mirrors the CJS-interop view.
- **Importing CommonJS from ESM.** `module.exports` is exposed as the **default export**;
  Node additionally runs **`cjs-module-lexer`** to statically detect named exports so
  `import { name } from './cjs.cjs'` works. Detection is a **heuristic** — dynamically
  assigned or computed exports are not seen; fall back to the default import and destructure.
- **`module.createRequire(filename)`** builds a `require` scoped to an ESM file:
  `const require = createRequire(import.meta.url)` — the standard way to pull a CJS-only
  package (or JSON) into ESM. (Requires created this way are not affected by async hooks.)
- **`import.meta`** (ESM only): `import.meta.url` (the module's `file:` URL);
  `import.meta.resolve(specifier)` — **synchronous since v20** (returns a URL **string**, not
  a Promise; honors `"exports"`); `import.meta.dirname` and `import.meta.filename` (stable
  v22/v24; the ESM equivalents of `__dirname`/`__filename`, `file:` modules only);
  `import.meta.main` (newer) ≈ `require.main === module`.

### 7. Module customization (loader) hooks

Node lets you intercept resolution and loading with **hooks**, registered before app code via
`--import ./register-hooks.js`:

- **`module.registerHooks({ resolve, load })`** (v23.5+, release candidate) — **synchronous,
  in-thread** hooks. The recommended default: simpler, no inter-thread overhead, and works
  cleanly for CommonJS in the graph. Returns `{ deregister() }`. Registration is **LIFO** —
  the last-registered hook runs first, then chains toward Node's default.
- **`module.register(specifier[, parentURL][, options])`** (v20.6+) — registers a hooks
  module that runs **asynchronously on a separate loader thread**. Use it when a hook must do
  async work and you want Node to own the worker/atomics plumbing; `options.data` +
  `options.transferList` (e.g. a `MessagePort`) pass data to `initialize`. (It carries
  documentation-only deprecation **DEP0205** steering most users to `registerHooks`, but it is
  **not** runtime-deprecated and remains the off-thread API.)
- **The hooks.** `initialize(data)` runs once at registration. **`resolve(specifier, context,
  nextResolve)`** receives `context.{conditions, importAttributes, parentURL}` and returns
  `{ url, format?, importAttributes?, shortCircuit? }`. **`load(url, context, nextLoad)`**
  returns `{ format, source, shortCircuit? }` where `format` ∈ `'builtin' | 'commonjs' |
  'json' | 'module' | 'wasm'` (+ addon/typescript variants). Each hook must either call
  `next…()` (to chain) or set `shortCircuit: true`.
- **History.** The old `--experimental-loader ./loader.mjs` flag (v8.8) was the original API;
  its `getFormat`/`getSource`/`transformSource`/`globalPreload` hooks were removed in v16.12
  and the whole flag superseded by `register`/`registerHooks`. `module.builtinModules`,
  `module.isBuiltin(name)`, and `module.syncBuiltinESMExports()` round out the introspection.

### 8. Import attributes, JSON modules, and import maps

- **Import attributes** — `import data from './x.json' with { type: 'json' }` (and the dynamic
  `import('./x.json', { with: { type: 'json' } })`). No longer experimental (v20.18/v22.12+).
  They **replaced** the older `assert { type: ... }` "import assertions" syntax (deprecated).
- **JSON modules** require `with { type: 'json' }`, expose **only a default export** (no named
  exports), and share a cache entry with the CJS JSON cache.
- **`data:` and `node:` imports** — `data:text/javascript,…` / `data:application/json,…` (no
  relative resolution) and `node:fs` builtins.
- **Import maps** are a **browser/HTML** standard (`<script type="importmap">`) for remapping
  bare specifiers in the browser; Node has **no built-in import-map support** — the Node
  equivalent of "remap a bare specifier" is `"imports"` (concept 4) or a `resolve` hook.

## Key APIs

| API / flag | Surface | Use it for |
| --- | --- | --- |
| `require.resolve(req[, {paths}])` / `.paths(req)` | CJS | Resolve without loading; inspect the search path. |
| `require.cache` | CJS | Inspect/evict the module cache (keyed by resolved filename). |
| `module.createRequire(import.meta.url)` | ESM→CJS | Get a `require` inside an ES module. |
| `import.meta.resolve(spec)` | ESM | Synchronous specifier → URL string (honors `"exports"`). |
| `import.meta.dirname` / `.filename` / `.url` | ESM | ESM replacements for `__dirname`/`__filename`. |
| `module.register(spec, parentURL, {data, transferList})` | hooks | Async, **off-thread** resolve/load hooks. |
| `module.registerHooks({resolve, load})` | hooks | Sync, **in-thread** hooks (recommended; returns `deregister`). |
| `module.isBuiltin(name)` / `module.builtinModules` | introspection | Detect/enumerate core modules. |
| `node --conditions=<name>` (`-C`) | CLI | Activate a custom export/import condition. |
| `node --import ./hooks.js app.js` | CLI | Preload hook registration before app code (inherited by workers). |
| `--experimental-require-module` / `--no-experimental-require-module` | CLI | Toggle `require(esm)` (default on in current/LTS). |

## Methodology — practical patterns

1. **Authoring a package's public API: lead with `"exports"`.** List every supported entry
   point; rely on encapsulation to keep deep imports private; put `"types"` first and
   `"default"` last in every condition object.
2. **Ship dual packages only when forced.** Prefer a single ESM build now that `require(esm)`
   is unflagged. If you must ship both, use the ESM-source + `.cjs`-wrapper pattern, or
   isolate state into one shared CJS file — never let both builds carry independent state.
3. **Pull CJS-only deps / JSON into ESM with `createRequire`** rather than fighting named-export
   detection; pull pure data with `with { type: 'json' }`.
4. **Use `"imports"` (`#…`) for internal aliases and env-swapped implementations** instead of
   `../../..` chains or build-time aliasing.
5. **Prefer `module.registerHooks` (in-thread)** for transforms/instrumentation; reach for
   `module.register` (off-thread) only when a hook genuinely needs async I/O.
6. **Register hooks via `--import`**, not inside app code, so they affect the entry module and
   worker threads too.

## Anti-patterns

- **Relying on extensionless / directory imports in ESM.** `import './util'` and
  `import './lib'` fail — ESM needs `'./util.js'` and `'./lib/index.js'`. Only CJS guesses.
- **Mis-ordering conditions.** Putting `"default"` (or `"require"`) before `"import"` makes
  the later, more specific branch unreachable — the first match wins.
- **Forgetting that `"exports"` blocks deep imports.** Adding `"exports"` silently breaks
  `pkg/lib/internal.js` consumers with `ERR_PACKAGE_PATH_NOT_EXPORTED`; list (or deliberately
  withhold) every subpath, and re-add `"./package.json"` if needed.
- **A dual package with shared mutable state in both builds** → divergent singletons and
  `instanceof` failures (the dual-package hazard).
- **`require()`-ing an ESM with top-level await** → `ERR_REQUIRE_ASYNC_MODULE`; use dynamic
  `import()`, or remove the top-level `await`.
- **Treating `*` in `"exports"` as a glob.** It is a plain string substitution; `./*` exposes
  *everything*, including dotfiles, unless narrowed or blocked with `null`.
- **`assert { type: 'json' }`** — the deprecated assertion syntax; use `with { type: 'json' }`.

## Troubleshooting

- **`ERR_MODULE_NOT_FOUND`** → ESM couldn't find the `file:` URL: missing extension, wrong
  relative base, or a bare specifier not exported. Check the exact specifier string;
  `import.meta.resolve` shows what Node computes.
- **`ERR_REQUIRE_ESM`** → you're on an old Node (or `--no-experimental-require-module`), or the
  target isn't unambiguously ESM. Upgrade to a current LTS, or use dynamic `import()`.
- **`ERR_REQUIRE_ASYNC_MODULE`** → the required ESM (or a transitive dep) uses top-level await.
- **`ERR_PACKAGE_PATH_NOT_EXPORTED`** → the subpath isn't in the dependency's `"exports"`; use
  a listed entry point, or (last resort) an absolute path past `node_modules`.
- **`ERR_UNSUPPORTED_DIR_IMPORT`** → ESM import of a directory; point at the index file.
- **`ERR_PACKAGE_IMPORT_NOT_DEFINED`** → a `#…` specifier with no `"imports"` entry (or no
  matching condition).
- **Named import from a CJS module is `undefined`** → `cjs-module-lexer` couldn't statically
  see it (dynamic/computed `exports`); import the default and destructure at runtime.
- **A loader hook isn't applied to the entry file** → register it with `--import` (preload),
  not from within application code, which runs too late.

## References

- Node.js — Modules: CommonJS modules (`require(X)`, `LOAD_AS_FILE`/`LOAD_INDEX`/`LOAD_AS_DIRECTORY`/`LOAD_NODE_MODULES`/`NODE_MODULES_PATHS`, `LOAD_PACKAGE_EXPORTS`/`LOAD_PACKAGE_IMPORTS`, `require.cache`/`require.resolve`, `NODE_PATH`): https://nodejs.org/api/modules.html
- Node.js — Modules: ECMAScript modules (specifiers, mandatory extensions, `import.meta.*`, CJS interop, `require(esm)`, import attributes, `ESM_RESOLVE`/`PACKAGE_RESOLVE`/`PACKAGE_EXPORTS_RESOLVE`/`PACKAGE_TARGET_RESOLVE`/`ESM_FILE_FORMAT`): https://nodejs.org/api/esm.html
- Node.js — Modules: Packages (`"type"`, `"exports"` conditional/subpath/pattern/encapsulation, `"imports"`, the dual-package hazard, conditions & `--conditions`): https://nodejs.org/api/packages.html
- Node.js — Modules: `node:module` API (`module.register`, `module.registerHooks`, `resolve`/`load`/`initialize` hooks, `createRequire`, `builtinModules`/`isBuiltin`, `--import`): https://nodejs.org/api/module.html
- Node.js — Deprecations (DEP0205 `module.register()`, documentation-only): https://nodejs.org/api/deprecations.html
- Joyee Cheung — "require(esm) in Node.js: from experiment to stability" (flag timeline, `ERR_REQUIRE_ASYNC_MODULE`, sync-graph constraint): https://joyeecheung.github.io/blog/2025/12/30/require-esm-in-node-js-from-experiment-to-stability/
- Node.js v23.0.0 release notes (`require(esm)` unflagged by default): https://nodejs.org/en/blog/release/v23.0.0
