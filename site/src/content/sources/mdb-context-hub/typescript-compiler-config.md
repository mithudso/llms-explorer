---
title: "TypeScript Compiler Configuration"
description: "A lang-js-ts reference for the tsconfig.json file and the full compilerOptions surface. The"
---

# TypeScript Compiler Configuration — `tsconfig.json` & `compilerOptions`

A `lang-js-ts` reference for the **`tsconfig.json` file and the full `compilerOptions` surface**. The
goal: pick a correct, version-appropriate config the first time, know what each strictness flag costs,
and copy a sane baseline for a Node app, a bundler/web app, or a published library. Defer module
*resolution algorithm* internals, project references / `tsc -b`, and external bundler config to the
siblings listed in the provenance block.

## Overview

`tsconfig.json` marks a directory as the **root of a TypeScript project** and tells `tsc` (and every
editor, bundler plugin, and `ts-node`/`tsx`) what files to compile and under what rules. Running `tsc`
with no input files makes it search up from the CWD for the nearest `tsconfig.json`; `tsc -p ./path`
points at a specific one. The shape is two halves: a small set of **top-level fields** (which files,
what to extend) and the large **`compilerOptions`** object (how to type-check, resolve, and emit).

**Version anchor (memorize — these drive "is this flag available / on" questions):**

| Flag / change | Landed in | Note |
| --- | --- | --- |
| `noUncheckedIndexedAccess`, `jsxImportSource` | TS 4.1 | |
| `noImplicitOverride` | TS 4.3 | |
| `useUnknownInCatchVariables`, `exactOptionalPropertyTypes` | TS 4.4 | `useUnknownInCatch…` is in the `strict` family |
| `moduleResolution: "bundler"`, `verbatimModuleSyntax`, `allowImportingTsExtensions`, `allowArbitraryExtensions` | **TS 5.0** | `verbatimModuleSyntax` replaces `importsNotUsedAsValues` + `preserveValueImports` |
| `module: "preserve"` | TS 5.4 | implies `moduleResolution: bundler`; emits ESM imports as-is and `import …= require()` as `require()` |
| `noUncheckedSideEffectImports` | TS 5.6 | defaults `true` |
| `erasableSyntaxOnly`, `rewriteRelativeImportExtensions` | TS 5.8 | aligns `tsc` with Node's native type-stripping |
| Default flips (`strict`, `module`, `target`, `types`, `rootDir`), big deprecations | **TS 6.0** (Mar 2026) | last JS-based release before the Go-based TS 7.0; see "TS 6.0 delta" |

> **Defaults vs `tsc --init`.** Through TS 5.x the *compiler* defaults are permissive (`strict: false`,
> `target: ES5`, `module` keyed off `target`), even though `tsc --init` *scaffolds* a strict-on file —
> "default" in this doc means the compiler default for the stated version line, not what a generated
> file shows. **TS 6.0 changes the compiler defaults themselves** (see the TS 6.0 delta). The robust
> habit either way: set `strict`, `target`, `module`, and `lib` explicitly so behavior doesn't shift
> under you across versions.

## Core Concepts

### Top-level fields (brief — deep dives are deferred)

- **`extends`** — inherit another config: a relative path or a package, e.g. `"@tsconfig/node20/tsconfig.json"`. Accepts an **array** (TS 5.0+) merged left→right. The child wins on conflicts; `files`/`include`/`exclude` from the parent are overwritten (not merged) if redefined. Relative `paths`/`outDir` in the parent resolve against the **parent's** location.
- **`files`** — an explicit allowlist of files. No globs. Best for tiny projects; otherwise use `include`.
- **`include`** — glob patterns (`"src/**/*"`). If omitted, defaults to everything under the config dir (minus `exclude`). `*`/`?`/`**` supported; patterns without an extension match `.ts/.tsx/.d.ts` (and `.js/.jsx` when `allowJs`).
- **`exclude`** — globs removed from `include` (defaults to `node_modules`, `bower_components`, `jspm_packages`, and `outDir`). `exclude` only filters `include`; it does **not** stop a file pulled in by an `import` or a `/// <reference>`.
- **`references`** — array of `{ "path": "../pkg" }` for **project references** (composite builds). *Deep coverage → `typescript-project-references-monorepo`.*

### Type-checking / strictness

`strict` is a **bundle switch**. Setting `"strict": true` turns on all eight family members at once;
you can then re-disable any single one (`"strict": true, "strictNullChecks": false`) — the explicit
flag overrides the bundle. The **eight `strict`-family flags**:

| Flag | What it does |
| --- | --- |
| `noImplicitAny` | Error when an expression/declaration falls back to an inferred `any` (e.g. an untyped parameter). |
| `strictNullChecks` | `null`/`undefined` are distinct types, not assignable to everything. The single most valuable flag — enable it before the others if migrating. |
| `strictFunctionTypes` | Function **parameters** checked contravariantly (sound) instead of bivariantly. Does not apply to method syntax on interfaces/classes. |
| `strictBindCallApply` | `.call`/`.apply`/`.bind` are type-checked against the function's real parameters. |
| `strictPropertyInitialization` | Class fields must be initialized in the constructor or marked `?`/`!`. Requires `strictNullChecks` to take effect. |
| `noImplicitThis` | Error on a `this` whose type is an implied `any`. |
| `useUnknownInCatchVariables` | `catch (e)` types `e` as `unknown` instead of `any`, forcing a narrowing check (TS 4.4). |
| `alwaysStrict` | Parse every file in ECMAScript strict mode and emit `"use strict"`. |

> The exact membership of the `strict` family is these eight per the TSConfig reference. Newer TS
> lines have floated additional `strict`-gated checks; verify against the reference for your version
> before relying on one beyond these eight.

**Standalone checks** (NOT enabled by `strict` — opt in individually):

| Flag | Since | What it does / cost |
| --- | --- | --- |
| `noUncheckedIndexedAccess` | 4.1 | Adds `\| undefined` to any index-signature/array access (`arr[i]`, `rec[key]`). High value, high friction — forces a guard or `!` on every dynamic access. |
| `exactOptionalPropertyTypes` | 4.4 | `{ x?: T }` means "absent or `T`" — assigning `undefined` explicitly is an error. Surfaces real present-vs-absent bugs; noisy with libraries that pass `undefined`. |
| `noImplicitOverride` | 4.3 | Require the `override` keyword when a subclass method overrides a base method. Prevents silent signature drift. |
| `noFallthroughCasesInSwitch` | — | Error on a non-empty `case` that falls through without `break`/`return`/`throw`. |
| `noUncheckedSideEffectImports` | 5.6 | Error if a **side-effect-only** import (`import "./x"`) doesn't resolve to a real file. Defaults **`true`** (low-risk: only affects bare side-effect imports). |
| `noPropertyAccessFromIndexSignature` | — | Force bracket access (`obj["key"]`) for properties that only exist via an index signature; reserve dot access for declared properties. |
| `noImplicitReturns` | — | Every code path in a function with a return type must return a value. |
| `allowUnreachableCode` | — | `false` errors on unreachable code; `undefined` (default) warns; `true` silences. (`allowUnusedLabels` is the sibling for labels.) |

The **`@tsconfig/strictest`** preset enables the full set above (plus `noUnusedLocals`,
`noUnusedParameters`, `noImplicitReturns`, etc.) for green-field projects that can afford it.

### Modules

These four options are interdependent — set them as a group, not piecemeal.

**`module`** — the module format `tsc` *emits* and the import syntax it understands:

- `"commonjs"` — `require`/`module.exports` output. Legacy Node / CJS packages.
- `"node16"` / `"nodenext"` — emit format is chosen **per file** from the nearest `package.json` `"type"` (and `.mts`/`.cts` extension). The correct choice for code that runs in modern Node. `nodenext` tracks the latest Node behavior; `node16` pins to the Node 16 semantics.
- `"esnext"` / `"es2015"`/`"es2020"`/`"es2022"` — pure ESM output at the stated level. Use for code a bundler will consume, or pure-ESM libraries.
- `"preserve"` (TS 5.4) — leave imports/`import()` exactly as written, no rewriting. Implies `moduleResolution: bundler`. The modern "I'm handing this to a bundler" choice.
- (Deprecated/legacy: `amd`, `umd`, `system`, `none`.)

**`moduleResolution`** — *how* a specifier maps to a file:

- `"node10"` (the option formerly named `"node"`) — classic Node CJS resolution. No `exports`/`imports` field support. Legacy only.
- `"node16"` / `"nodenext"` — modern Node resolution honoring `package.json` `"exports"`/`"imports"`, conditional exports, and `.mts`/`.cts`. Pair with `module: node16`/`nodenext`. **Required** for correctly typing dual-format packages.
- `"bundler"` (TS 5.0) — models esbuild/Vite/webpack/Parcel: extensionless imports allowed (like CJS) but prefers `import` conditions in `exports` (like ESM). For app code consumed by a bundler. **Not for published libraries** — it hides resolution problems your consumers (who may not bundle) would hit; ship with `node16`/`nodenext` instead.
- `"classic"` — pre-Node TS resolution. Effectively never use it. *(Resolution **algorithm** internals + `exports`/`imports` mechanics → `nodejs-module-resolution`.)*

**`target`** — the ECMAScript version `tsc` downlevels syntax to (e.g. `es2015`…`es2023`, `esnext`).
Drives the default `lib` and the default `module`. Through 5.x the default is `ES5`; pick at least
`es2022` for modern runtimes (top-level await, class fields, `Error.cause`).

**`lib`** — which built-in type declarations to include (e.g. `["es2022", "dom", "dom.iterable"]`).
Omitting it derives a set from `target`. Set it explicitly to control DOM availability: include `dom`
for browser code, omit it for pure Node/server code so `document`/`window` don't type-check.

**Path mapping & related:**

- **`baseUrl`** — base directory for resolving **bare** specifiers. (Deprecated in TS 6.0; prefer `paths` without it, or package `imports`.)
- **`paths`** — remap import specifiers to locations, e.g. `{ "@app/*": ["./src/*"] }`. **`tsc` and editors honor these for type-checking only — they do not rewrite emitted paths.** A bundler, `tsc-alias`, or `package.json` `"imports"` must make them work at runtime. Node's native runner ignores `paths`.
- **`rootDir`** — the input root that mirrors into `outDir` (controls output folder structure). `rootDirs` merges multiple virtual roots into one.
- **`outDir`** — where emitted `.js`/`.d.ts` go.
- **`resolveJsonModule`** — allow `import data from "./x.json"` with an inferred type. Requires a `module` that supports it (most do except some legacy modes).
- **`allowImportingTsExtensions`** (5.0) — permit `import "./x.ts"` (explicit TS extension). Only allowed with `noEmit` **or** `emitDeclarationOnly` (since `tsc` can't emit a `.ts` import). Needed for Node's native type-stripping workflow.
- **`moduleDetection`** — `"auto"` (default; a file with any `import`/`export`, or under `module: node16`/`nodenext` with `"type":"module"`, is a module), `"force"` (treat **every** file as a module — recommended to avoid global-scope surprises), `"legacy"`.
- **`resolvePackageJsonExports` / `resolvePackageJsonImports`** — consult the `package.json` `"exports"`/`"imports"` fields. Default **`true`** under `node16`/`nodenext`/`bundler`. *(Field mechanics → `nodejs-module-resolution`.)*

### Emit & interop

- **`declaration`** — emit `.d.ts` files. **Mandatory for a published library.** Defaults `true` when `composite` is on, else `false`.
- **`declarationMap`** — emit `.d.ts.map` so consumers' "go to definition" jumps to your `.ts` source, not the `.d.ts`. Ship for libraries with source.
- **`sourceMap`** — emit `.js.map` for runtime debugging.
- **`noEmit`** — type-check only, produce no files. The standard setting when a **bundler** (or Node's strip-types) does the actual transpile and `tsc` is the type gate.
- **`isolatedModules`** — guarantee every file can be transpiled **alone**, without cross-file type info (which is exactly how esbuild/swc/Babel/Node-strip operate). It bans constructs needing whole-program knowledge — re-exporting a type without `export type`, `const enum`, certain namespace patterns. Turn it on whenever a single-file transpiler is in the pipeline.
- **`verbatimModuleSyntax`** (5.0) — leave any import/export **without** a `type` modifier exactly as written, and **drop** anything with `type`. Replaces the deprecated `importsNotUsedAsValues` + `preserveValueImports`. Makes value-vs-type imports explicit and prevents accidental elision — pair it with `isolatedModules`/`erasableSyntaxOnly`. Caveat: it won't rewrite ESM syntax to `require`, so don't combine it with `module: commonjs` if you write `import`/`export`.
- **`esModuleInterop`** — generate interop helpers so `import express from "express"` works against a CJS module without a real default export. Implies `allowSyntheticDefaultImports`. Effectively always-on in modern configs (and undisablable in TS 6.0).
- **`allowSyntheticDefaultImports`** — allow default-style imports from modules lacking a default export, for **type-checking** only (no emit change). Implied by `esModuleInterop`.
- **`erasableSyntaxOnly`** (5.8) — error on TS constructs that **emit runtime code**: `enum`, `namespace` with runtime members, parameter properties (`constructor(private x)`), `import =`. Mirrors exactly what Node's native type-stripping refuses, so the editor catches the mismatch instead of a runtime crash. Pair with `verbatimModuleSyntax`. *(Node runtime side → `nodejs-typescript-and-runtime-features`.)*

### JS interop & JSX

- **`allowJs`** — let `.js`/`.jsx` files into the program (imported by, or alongside, `.ts`). Needed for incremental migration and for emitting from a JS codebase.
- **`checkJs`** — type-check those `.js` files (using JSDoc annotations). Per-file opt-in/out via `// @ts-check` / `// @ts-nocheck`. Requires `allowJs`.
- **`jsx`** — JSX transform: `"preserve"` (emit `.jsx`, leave JSX for a bundler), `"react"` (classic `React.createElement`), `"react-jsx"` (the automatic runtime — no `import React` needed; **the modern default for React 17+**), `"react-jsxdev"`, `"react-native"`.
- **`jsxImportSource`** (4.1) — the module the automatic runtime imports `jsx`/`jsxs` from (default `"react"`); set to `"preact"`, `"@emotion/react"`, etc. Only meaningful with `jsx: react-jsx`/`react-jsxdev`.

### The TS 6.0 delta (current as of June 2026)

TypeScript **6.0** (released March 2026) is the **last JavaScript-based release** before the Go-based
**TS 7.0** ("native"). Per the official handbook release notes it **changes compiler defaults** —
relevant to this skill:

- `strict` now defaults **`true`** (was `false`). The notes are explicit: *"If you were relying on the previous default of `false`, you'll need to explicitly set `"strict": false` in your `tsconfig.json`."*
- `module` defaults **`esnext`** (ESM is now the dominant format).
- `target` defaults to the **most recent supported ECMAScript spec** — a floating target, currently **`es2025`**.
- `types` defaults **`[]`** (no longer auto-pulls every installed `@types` package — declare what you need).
- `rootDir` defaults to the **directory containing `tsconfig.json`**.
- `noUncheckedSideEffectImports` defaults `true` (already true on the 5.6+ reference); `libReplacement` now defaults `false` for performance.

It also adds `--stableTypeOrdering` (to diff 6.0 vs 7.0 output) and **deprecates/removes** legacy
surface (`target: es5` + `--downlevelIteration`, `moduleResolution: node10`/`classic`,
`module: amd/umd/system/none`, `--outFile`, `baseUrl`). **Practical takeaway:** explicitly set
`strict`, `target`, `module`, and `lib` in your config so behavior is identical across 5.x and 6.0
instead of relying on defaults that shifted.

## Tools / Frameworks

- **`tsc --init`** — scaffold a commented `tsconfig.json`. The generated defaults have grown stricter over versions; treat the output as a starting point, not gospel — prune comments and pin the four module/target options.
- **`@tsconfig/bases`** — official community base configs you `extends`: `@tsconfig/node20`, `@tsconfig/node22`, `@tsconfig/strictest`, `@tsconfig/recommended`, framework bases (`@tsconfig/vite-react`, etc.). Inherit one and override the few project-specific keys.
- **`tsc --showConfig`** — print the fully-resolved config (after `extends` merging and defaults). The fastest way to answer "what is actually in effect here?"
- **`tsc --explainFiles` / `--listFilesOnly`** — show why each file is in the program (which `include`/`import`/`reference` pulled it in). Use when `include`/`exclude` isn't behaving.
- **`tsc --noEmit`** — the type-check gate to run in CI when a bundler or Node strip-types does the real build.
- **`tsc-alias` / bundler `resolve.alias`** — make `paths` work at runtime (since `tsc` doesn't rewrite them).

## Methodology

1. **Inherit, don't hand-roll.** Start from `@tsconfig/node22` (or a framework base) via `extends`, then override only what's project-specific.
2. **Set the module quartet together** by runtime target: Node → `module: nodenext` + `moduleResolution: nodenext`; bundler/web → `module: preserve` (implies `bundler`) + `noEmit`; library → `module: nodenext` (or `esnext`) + `declaration: true`.
3. **Turn on `strict`** (default in 6.0) and, for new code, the high-value standalone checks `noUncheckedIndexedAccess` + `noImplicitOverride`. Add `exactOptionalPropertyTypes`/`@tsconfig/strictest` only if the team will pay the friction.
4. **Pin `target` and `lib` explicitly** (e.g. `es2022`; `["es2022"]` server vs `["es2022","dom","dom.iterable"]` web) so the 6.0 default flips don't silently change behavior.
5. **If a single-file transpiler is in the pipeline** (esbuild/swc/Vite/Node strip-types), set `isolatedModules: true` + `verbatimModuleSyntax: true` (+ `erasableSyntaxOnly` for the native-Node path).
6. **Verify with `tsc --showConfig`** and a `tsc --noEmit` run before trusting the file.

## Practical Patterns

**Node app (TS 5.x/6.0, transpiled by `tsc`):**

```json
{
  "extends": "@tsconfig/node22/tsconfig.json",
  "compilerOptions": {
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "target": "es2023",
    "lib": ["es2023"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "resolveJsonModule": true,
    "moduleDetection": "force",
    "skipLibCheck": true,
    "rootDir": "src",
    "outDir": "dist",
    "sourceMap": true,
    "declaration": false
  },
  "include": ["src/**/*"],
  "exclude": ["dist", "node_modules"]
}
```

**Bundler / web app (Vite/esbuild/webpack do the transpile; `tsc` is the type gate):**

```json
{
  "compilerOptions": {
    "module": "preserve",
    "noEmit": true,
    "target": "es2022",
    "lib": ["es2022", "dom", "dom.iterable"],
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "resolveJsonModule": true,
    "moduleDetection": "force",
    "skipLibCheck": true,
    "allowImportingTsExtensions": true,
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"]
}
```

**Published library (dual-friendly types, source-mapped declarations):**

```json
{
  "extends": "@tsconfig/node20/tsconfig.json",
  "compilerOptions": {
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "target": "es2021",
    "lib": ["es2021"],
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "rootDir": "src",
    "outDir": "dist",
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["**/*.test.ts"]
}
```

**Node native type-stripping (zero build; `tsc --noEmit` only validates):**

```json
{
  "compilerOptions": {
    "noEmit": true,
    "module": "nodenext",
    "target": "esnext",
    "erasableSyntaxOnly": true,
    "verbatimModuleSyntax": true,
    "rewriteRelativeImportExtensions": true,
    "allowImportingTsExtensions": true
  }
}
```

(*Native-runtime behavior itself → `nodejs-typescript-and-runtime-features`.*)

## Anti-Patterns

- **Mixing module modes.** `module: esnext` with `moduleResolution: node10` (or `bundler` with `module: commonjs`) gives wrong resolution/emit. Keep `module`/`moduleResolution` consistent with the runtime.
- **`moduleResolution: bundler` in a published package.** It validates only the bundler case and hides breakage for consumers using plain Node resolution. Libraries → `node16`/`nodenext`.
- **Expecting `paths` to work at runtime.** `tsc` never rewrites them; without a bundler/`tsc-alias`/package `imports`, the emitted JS has unresolved bare specifiers.
- **Leaving `target: ES5` (5.x default) unset on a modern runtime** — bloated downlevel output and missing lib types. Always pin `target`.
- **`enum`/`namespace`/parameter-properties under `isolatedModules` or a strip-types runtime** — they need whole-program emit; use `erasableSyntaxOnly` to catch them at author time.
- **`skipLibCheck` everywhere as a crutch** — it's a performance win, but it can mask genuine conflicts between `@types` packages; don't reach for it to silence a real type error.
- **Re-exporting a type without `export type` when `isolatedModules`/`verbatimModuleSyntax` is on** — a single-file transpiler can't tell it's type-only and may emit a broken value import.
- **Relying on TS 6.0's default flips.** Be explicit about `strict`/`target`/`module`/`lib` so a 5.x and a 6.0 toolchain produce identical results.

## Troubleshooting

- **"Cannot use import statement outside a module" / wrong require-vs-import emit** → `module`/`moduleResolution` don't match the runtime; switch to `nodenext` and check the package's `"type"`.
- **`paths` import fails at runtime** (works in editor) → expected; wire `tsc-alias`, a bundler alias, or `package.json` `"imports"`.
- **"This import path can only be used with allowImportingTsExtensions"** → you imported `./x.ts`; set `allowImportingTsExtensions: true` (and `noEmit`/`emitDeclarationOnly`).
- **"`X` is declared but never used" / unexpected unused errors** → a `@tsconfig/strictest` base enabled `noUnusedLocals`/`noUnusedParameters`; relax or prefix with `_`.
- **`enum`/parameter-property errors under a no-emit setup** → `erasableSyntaxOnly` is on (or the runtime strips types); rewrite to erasable constructs.
- **Config changes seem ignored** → run `tsc --showConfig`; an `extends` parent or an editor pinning a different `tsconfig` is overriding you.
- **A file you expected isn't compiled** → it's outside `files`/`include` or hit `exclude`; `exclude` can't remove a file reached via `import`. Use `tsc --explainFiles`.
- **New type errors after a TS upgrade** → `strict` may gate additional checks in the new line (and 6.0 flips defaults); pin versions and read that release's notes.
- **DOM globals (`document`, `window`) missing or unexpectedly present** → set `lib` explicitly (include/exclude `dom`).

## References

- TypeScript — TSConfig Reference (every option, defaults): https://www.typescriptlang.org/tsconfig/
- TypeScript Handbook — What is a tsconfig.json: https://www.typescriptlang.org/docs/handbook/tsconfig-json.html
- TypeScript Handbook — Modules: Choosing Compiler Options: https://www.typescriptlang.org/docs/handbook/modules/guides/choosing-compiler-options.html
- TypeScript 5.0 release notes (`verbatimModuleSyntax`, `bundler`, `allowImportingTsExtensions`): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html
- TypeScript 5.4 release notes (`module: preserve`): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-4.html
- TypeScript 5.6 release notes (`noUncheckedSideEffectImports`): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-6.html
- TypeScript 5.8 release notes (`erasableSyntaxOnly`, `rewriteRelativeImportExtensions`): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html
- TypeScript 6.0 release notes (default flips, deprecations, last JS-based release): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html
- `@tsconfig/bases` (community base configs): https://github.com/tsconfig/bases
- Total TypeScript — The TSConfig Cheat Sheet (Matt Pocock baselines): https://www.totaltypescript.com/tsconfig-cheat-sheet
