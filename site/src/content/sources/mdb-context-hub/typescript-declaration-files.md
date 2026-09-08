---
title: "TypeScript Declaration Files"
description: "A lang-js-ts hub reference for producing and shipping TypeScript type information: how .d.ts"
---

# TypeScript Declaration Files (.d.ts Authoring & Type Distribution)

A `lang-js-ts` hub reference for **producing and shipping TypeScript type information**: how `.d.ts`
files are emitted, how to hand-author ambient declarations and augment other people's types, and how
to distribute types from an npm package so downstream consumers (and `tsc`, `attw`, editors) resolve
them correctly across ESM and CJS.

A `.d.ts` is **types only** — no runtime code, no JS output. It is the contract `tsc` reads when it
can't see a library's source. Scope discipline: declaration **emit** compiler options live here (not in
`typescript-compiler-config`); the **runtime** resolution algorithm that finds the file lives in
`nodejs-module-resolution`; the **bundler** that produces the file lives in
`nodejs-build-tooling-bundlers`; advanced **type operators** used inside a `.d.ts` live in
`typescript-advanced-types`.

## Overview

There are two ways a `.d.ts` comes into existence: **emitted** by the compiler from `.ts` source
(`declaration: true`), or **hand-authored** as an ambient declaration for code TypeScript can't analyze
(plain JS libs, globals injected by a `<script>`, env vars). Distribution is the third axis: a package
points consumers at its types via the `types` field and the `exports` map, or — if it ships no types —
the community publishes them under `@types/*` via DefinitelyTyped.

**Version anchors (memorize — these drive "does my TS have X" questions):**

| Feature | Compiler option / syntax | Since |
| --- | --- | --- |
| Declaration emit | `declaration: true` | long-standing |
| Declaration source maps (`.d.ts.map`) | `declarationMap: true` | TS 2.9 |
| Emit only `.d.ts` (no `.js`) | `emitDeclarationOnly: true` | TS 2.8 |
| Separate output root for `.d.ts` | `declarationDir` | TS 2.0 |
| **Isolated declarations** (per-file d.ts emit) | `isolatedDeclarations: true` | **TS 5.5** |
| `${configDir}` in tsconfig paths | `"${configDir}"` | TS 5.5 |
| `types` condition in `exports` | `package.json` `exports` | TS 4.7 (`node16`/`nodenext`) |
| UMD global | `export as namespace Foo;` | TS 2.x |

## Core Concepts

### 1. Declaration emit — turning `.ts` into `.d.ts`

With `declaration: true`, `tsc` emits a `.d.ts` next to each `.js` it produces. The four knobs:

| Option | Effect |
| --- | --- |
| `declaration` | Emit `.d.ts` alongside the `.js`. |
| `declarationMap` | Also emit `.d.ts.map` so editors **go-to-definition jumps to the `.ts` source**, not the generated `.d.ts`. Essential in monorepos with project references; ship the maps (and the source) only if you want consumers to navigate into your `.ts`. |
| `emitDeclarationOnly` | Emit `.d.ts` but **no `.js`**. Use when another tool (esbuild, Babel, swc, oxc) emits the JavaScript and `tsc` is reduced to "the types compiler." |
| `declarationDir` | Write all `.d.ts` under a separate root (e.g. `./dist/types`) instead of interleaved with JS. |

```jsonc
// tsconfig.json — library that emits its own types
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true,
    "emitDeclarationOnly": false,
    "outDir": "./dist",
    "module": "nodenext",
    "moduleResolution": "nodenext"
  }
}
```

**Why explicit return types help emit (this is load-bearing).** When a function lacks an annotated
return type, the emitter must *infer* the type and write it into the `.d.ts`. Inference can be slow on
complex code, and worse, it can produce a declaration that **references a symbol the consumer can't
name** — TS then errors with `TS2742` ("inferred type cannot be named without a reference to …") or
`TS4082` ("default export of the module has or is using private name …"). Annotating the public surface
(exported function/method return types, exported `const` types) makes emit a near-mechanical copy and
sidesteps the un-nameable-symbol class of failures entirely. This is exactly what isolated declarations
formalizes.

### 2. `--isolatedDeclarations` (TS 5.5)

`isolatedDeclarations: true` forces the public API to be **explicitly typed enough that a `.d.ts` can be
generated from a single file without consulting any other file**. That one-in/one-out property lets
non-`tsc` tools (oxc, swc, esbuild's experimental path) emit declarations **in parallel, per file**,
which `tsc`'s whole-program declaration emit can't do.

- **Requires `declaration: true` (or `composite: true`)** — it's a stricter mode *of* declaration emit,
  so the compiler errors if neither is set. (`isolatedModules` is a recommended companion for the same
  "per-file" philosophy, but it is **not** the enforced prerequisite — `declaration`/`composite` is.)
- **What it enforces (representative error: `TS9007`, "Function must have an explicit return type
  annotation with --isolatedDeclarations"; the `TS900x`/`TS903x` family covers the other
  inference-blocking cases):**
  - Every exported function / arrow / function-expression assigned to an exported binding needs an
    explicit return type.
  - Exported `let`/`const`/`var` need an annotation or a trivially-inferable literal initializer.
  - Public and protected class members (fields, accessors, method return types) need annotations.
  - Constructs whose emitted type can't be computed locally are rejected (e.g. spreading a value whose
    type comes from another file, computed property keys whose type needs inference).

```ts
// FAILS isolatedDeclarations
export function load(name) { return readJson(name); }   // TS9007: needs : Config
export const PORT = process.env.PORT ?? 3000;            // ok (literal-ish), but annotate to be safe

// PASSES
export function load(name: string): Config { return readJson(name); }
export const PORT: number = Number(process.env.PORT ?? 3000);
```

### 3. Hand-authoring `.d.ts` — the global-vs-module rule

The single most important authoring fact: **a `.d.ts` with any top-level `import` or `export` is a
*module* — its declarations are scoped, not global.** A `.d.ts` with **no** top-level `import`/`export`
is a *script*: every `declare`d name lands in the **global scope**. `moduleDetection` is always `auto`
for `.d.ts`, so you cannot force this with config — it's purely structural.

```ts
// global.d.ts — SCRIPT (no top-level import/export) → adds to global scope
declare const APP_VERSION: string;
declare function gtag(...args: unknown[]): void;
interface Window {            // merges into the built-in lib Window (see merging below)
  myWidget?: { open(): void };
}
```

```ts
// ambient module declaration — for an untyped JS package or a non-code import
declare module "untyped-lib" {
  export function doThing(x: number): string;
  export default function (): void;
}
declare module "*.svg" {       // asset import (bundler magic)
  const url: string;
  export default url;
}
```

To put global types in a file that *is* a module (has imports/exports), wrap them in `declare global`:

```ts
import type { Logger } from "./logger.js";   // this import makes the file a module
declare global {
  interface Window { logger: Logger }
  var __DEV__: boolean;        // `var`, not `let/const`, to declare a global variable
}
export {};                     // ensures module-ness if there were no other export
```

**Triple-slash directives** (must be at the very top, before any statement):

```ts
/// <reference types="node" />          // depend on another @types package's globals
/// <reference lib="es2022.array" />    // pull in a specific built-in lib slice
/// <reference path="./other.d.ts" />   // legacy file include — AVOID in published types
```

In **published** declaration files, use `/// <reference types="..." />` to declare a dependency on
another package's types; **do not** use `/// <reference path="..." />` (the TS team explicitly flags it
as a red flag — it bakes in a relative file layout). Prefer real `import`s where the file is a module.

### 4. Declaration merging & module augmentation

TypeScript **merges** multiple declarations of the same name in the same scope. This is the mechanism
behind extending types you don't own.

**Interface merging** — same-named interfaces combine their members:

```ts
interface Box { height: number; }
interface Box { width: number; }      // Box now has BOTH height and width
```

**Namespace + function/class/enum merging** — a `namespace` merges with a same-named function, class, or
enum, letting you hang static-like members off a callable/constructable:

```ts
function buildLabel(name: string): string { return buildLabel.prefix + name; }
namespace buildLabel { export let prefix = "Hello, "; }   // buildLabel.prefix is typed
```

**Module augmentation** — re-open another package's module from **a file that is itself a module** and
`declare module "their-pkg"`. The augmenting declarations merge into the original; you cannot add
*new top-level* exports this way, only augment existing shapes.

```ts
// augment a third-party module's interface
import "express";                                  // make this file a module + load the target
declare module "express" {
  interface Request { userId?: string; }           // adds req.userId everywhere
}
```

**Augmenting globals from inside a module** uses `declare global`. The two canonical Node patterns:

```ts
// 1. Strongly type process.env  (NodeJS.ProcessEnv is itself an interface you merge into)
export {};
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      DATABASE_URL: string;
      NODE_ENV: "development" | "production" | "test";
    }
  }
}

// 2. Add a property to the DOM Window
export {};
declare global {
  interface Window { dataLayer: unknown[]; }
}
```

### 5. Shipping types from a package

**Bundled (most common):** emit `.d.ts` with your build and point at the entry declaration.

```jsonc
{
  "name": "awesome",
  "version": "1.0.0",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts"   // "typings" is an exact synonym
}
```

**With an `exports` map (modern, and `node16`/`nodenext` resolution requires it):** add a `types`
condition. **It MUST appear first in each condition block** — TypeScript reads conditions top-to-bottom
and stops at the first match, so a `types` placed after `import`/`require`/`default` is silently
ignored.

```jsonc
{
  "name": "awesome",
  "type": "module",
  "exports": {
    ".": {
      "import": {
        "types": "./dist/index.d.mts",   // types BEFORE the runtime target
        "default": "./dist/index.mjs"
      },
      "require": {
        "types": "./dist/index.d.cts",
        "default": "./dist/index.cjs"
      }
    },
    "./package.json": "./package.json"
  }
}
```

**Dual-package types (the gotcha):** when you ship both ESM and CJS, a *single* `index.d.ts` is wrong if
your package is `"type": "module"` — under `require`, the consumer's compiler sees the `.d.ts` as ESM
syntax describing a CJS file. Ship **two** declaration files: `.d.mts` for the `import` condition and
`.d.cts` for the `require` condition (or `index.d.ts` + `index.d.cts`). This is precisely what
`@arethetypeswrong/cli` flags as **"Masquerading as CJS/ESM."**

**`typesVersions`** — serve different declarations to older TypeScript versions, or remap subpaths:

```jsonc
{
  "types": "./index.d.ts",
  "typesVersions": {
    ">=4.0": { "*": ["ts4.0/*"] },          // TS ≥4.0 reads ./ts4.0/*.d.ts
    "<4.0":  { "index.d.ts": ["index.v3.d.ts"] }
  }
}
```

**UMD global (`export as namespace`)** — for a library usable both as a module and as a `<script>` global:

```ts
// index.d.ts for a UMD library "myLib"
export as namespace myLib;     // exposes global `myLib` when loaded via <script>
export function greet(name: string): string;
export interface Options { loud?: boolean }
```

`export as namespace id` is **only legal in a `.d.ts`** that also has other top-level exports; placing it
in a `.ts` errors with `TS1315`. It only takes effect when the file enters compilation via a
triple-slash reference or as a top-level input — it's a no-op when the package is `import`ed.

## Tools / Frameworks

- **`tsc`** — `tsc --emitDeclarationOnly` (types-only build), `tsc -b` (project references; needs
  `composite: true`, which implies `declaration: true`).
- **`@arethetypeswrong/cli` (`attw`)** — `attw --pack .` or `attw <tarball>` validates that published
  types resolve under every module/condition combination. Flags "Masquerading as CJS/ESM,"
  "Fallback Condition," "No types," "missing `package.json` `exports`." Run in CI before publish.
- **`tsd`** — type-level test runner (uses `expect-type` under the hood). Write `*.test-d.ts` files with
  `expectType<T>(value)` and `expectError(...)`; `tsd` runs the compiler and asserts. Configure via a
  `tsd` block in `package.json`.
- **Vitest type testing** — alternative to `tsd`: `*.test-d.ts` with `expectTypeOf(x).toEqualTypeOf<T>()`
  or the simpler `assertType<T>(x)`; gated behind `typecheck` config (statically analyzed, never run).
- **`@types/*` + DefinitelyTyped (DT)** — the community type registry, auto-published to the `@types`
  npm org from the DT monorepo.

## Methodology

1. **Emit vs. hand-author.** If you own the `.ts` source, prefer **emitted** `.d.ts` (`declaration:
   true`) — never hand-maintain types that duplicate your source. Hand-author only for untyped JS deps,
   ambient globals, or non-code imports.
2. **Annotate the public surface** (exported return types, exported `const` types). Consider turning on
   `isolatedDeclarations: true` to *enforce* it and unlock parallel/third-party d.ts emit.
3. **Decide global vs. module per file** by the top-level import/export rule; reach for `declare global`
   only inside module files; reach for `declare module "x"` to augment a dependency.
4. **Wire distribution:** `types` field for the simple case; an `exports` map with a leading `types`
   condition for `node16`/`nodenext`; split `.d.mts`/`.d.cts` for dual packages.
5. **Validate before publish:** `attw --pack .` for resolution correctness, `tsd`/Vitest for the type
   contract.

## Consuming & contributing `@types` / DefinitelyTyped

**Consuming.** `tsc` auto-includes every `@types/*` package found under `node_modules/@types` (and parent
`node_modules`). Two `tsconfig` knobs scope this:

- `typeRoots` — which folders hold ambient type packages (default `["./node_modules/@types"]`).
- `types` — an **allow-list**; `"types": ["node", "jest"]` includes *only* those, excluding all other
  `@types/*` from the global scope. Use it to stop unrelated global types (e.g. a stray `@types/mocha`)
  from polluting a project. (Package-scoped, `import`ed types are unaffected — this gates only the
  automatically-included ambient packages.)

**Contributing a NEW types package to DefinitelyTyped.** Create `types/foo/` with these files (the old
triple-slash header comment is gone — metadata now lives in a `package.json`):

```
types/foo/
  index.d.ts        // the declarations for module "foo"
  foo-tests.ts      // type-checked (never executed) usage tests
  tsconfig.json     // per-package config (usually leave as generated)
  package.json      // metadata (below)
```

```jsonc
// types/foo/package.json
{
  "private": true,
  "name": "@types/foo",
  "version": "1.2.9999",                 // match foo's major.minor; patch is 9999
  "projects": ["https://github.com/org/foo"],
  "dependencies": { "@types/node": "*" },
  "devDependencies": { "@types/foo": "workspace:." },
  "owners": [{ "name": "Your Name", "githubUsername": "you" }],
  "minimumTypeScriptVersion": "5.0"      // if the types need a newer TS
}
```

Tests use **dtslint** assertions inside `foo-tests.ts`: `// $ExpectType string` on the line above an
expression, and `// @ts-expect-error` for code that must fail to compile. Validate locally with
`pnpm test` (DT runs dtslint + `attw`); after merge, the `@types/foo` package publishes automatically
within a few hours. Declare runtime-type dependencies in `dependencies` (not `devDependencies`) so
consumers pull them transitively.

## Anti-Patterns

- Putting the `types` condition **after** `import`/`require`/`default` in `exports` — TS stops at the
  first match and never sees it. `types` goes **first**.
- Shipping one `index.d.ts` for a dual ESM+CJS `"type": "module"` package — "Masquerading as CJS." Ship
  `.d.mts` + `.d.cts`.
- Hand-maintaining `.d.ts` that mirror your own `.ts` source instead of emitting them — they drift.
- `/// <reference path="..." />` in published types — bakes in a file layout; use
  `/// <reference types="..." />` or real imports.
- Exporting un-annotated functions from a library entry and being surprised by `TS2742`/`TS4082`
  ("cannot be named") on emit — annotate the public surface.
- Expecting `declare module "x"` (module augmentation) to add *new* top-level exports — it can only
  augment existing shapes; the augmenting file must itself be a module.
- Using `let`/`const` to declare a *global variable* in a `declare global` block — use `var`.
- Relying on `tsconfig` `paths` to be honored in *published* types — consumers don't share your `paths`;
  emit fully-resolved specifiers (the Node-native runner ignores `paths` too, per the sibling
  native-strip-types reference).

## Troubleshooting

- **`error TS9007` (or `TS900x`)** under `isolatedDeclarations` → add the explicit return type /
  annotation it points at.
- **`isolatedDeclarations can only be used when … declaration … is enabled`** → set `declaration: true`
  or `composite: true`.
- **`TS2742` / `TS4082` "cannot be named" on emit** → annotate the export, or export the referenced
  symbol so it's nameable.
- **Consumer "Could not find a declaration file for module 'foo'"** → ship a `types` field / `types`
  condition, or `npm i -D @types/foo`, or write a local `declare module "foo"` stub.
- **`attw` "Masquerading as CJS/ESM" / "Fallback Condition"** → fix the `exports` conditions; provide the
  matching `.d.mts`/`.d.cts` for each runtime entry.
- **`declare global` "Augmentations for the global scope can only be nested in … modules"** → the file
  isn't a module; add `export {};`.
- **`TS1315` "Global module exports may only appear in declaration files"** → `export as namespace` is in
  a `.ts`; move it to a `.d.ts`.
- **Global types from a `.d.ts` don't appear** → the file has a top-level `import`/`export`, so it's a
  module; either remove them or wrap the globals in `declare global`.

## References

- TS Handbook — Declaration Files (Introduction / Library Structures / Templates: module, global,
  global-plugin, module-plugin): https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html
- TS Handbook — Declaration Merging: https://www.typescriptlang.org/docs/handbook/declaration-merging.html
- TS Handbook — Modules (module vs. script rule): https://www.typescriptlang.org/docs/handbook/2/modules.html
- TS Handbook — Publishing: https://www.typescriptlang.org/docs/handbook/declaration-files/publishing.html
- TSConfig — isolatedDeclarations / declaration / declarationMap / emitDeclarationOnly / declarationDir:
  https://www.typescriptlang.org/tsconfig/#isolatedDeclarations
- TS 5.5 release notes (isolatedDeclarations): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html
- microsoft/TypeScript #58944 — Isolated Declarations: state of the feature: https://github.com/microsoft/TypeScript/issues/58944
- DefinitelyTyped README + contribution guide: https://github.com/DefinitelyTyped/DefinitelyTyped / https://definitelytyped.org/guides/contributing.html
- @arethetypeswrong/cli (problem kinds: FalseCJS/FalseESM/FallbackCondition): https://github.com/arethetypeswrong/arethetypeswrong.github.io
- tsd: https://github.com/tsdjs/tsd ; Vitest "Testing Types": https://vitest.dev/guide/testing-types
- microsoft/TypeScript #26532 — `export as namespace` (UMD): https://github.com/microsoft/TypeScript/issues/26532
