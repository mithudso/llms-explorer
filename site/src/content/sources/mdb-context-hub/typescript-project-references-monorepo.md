---
title: "TypeScript Project References"
description: "A lang-js-ts reference for splitting a TypeScript codebase into multiple referenced projects and building them as a graph with tsc --build. The goal: structure a monorepo (or any multi-tsconfig repo)"
---

# TypeScript Project References & Monorepo Builds — `composite`, `tsc -b`, Solution Configs

A `lang-js-ts` reference for **splitting a TypeScript codebase into multiple referenced projects and building them as a graph** with `tsc --build`. The goal: structure a monorepo (or any multi-`tsconfig` repo) so each package type-checks against its dependencies' emitted `.d.ts`, builds in dependency order, skips up-to-date work, and gives editors cross-package "go to definition." Defer single-project `compilerOptions`/strictness, the module-resolution *algorithm*, package-manager workspace plumbing, and bundler/task-runner orchestration to the siblings in the SKIP line.

## Overview

A **project reference** lets one `tsconfig.json` declare that it depends on another via a `references` array. This does three things at once: it tells the editor and `tsc` to treat the referenced project as a **prebuilt unit** (consumers load its emitted `.d.ts`, not its source), it lets the **build mode** (`tsc -b`) order and cache compilations across the whole graph, and — with `declarationMap` — it keeps editor navigation jumping to the original `.ts` source across package boundaries.

The feature has three moving parts:

1. **`composite: true`** on every *referenced* project — the opt-in that makes a project safely consumable as a dependency (forces `.d.ts` emit, enables incremental info, fixes the input-file set).
2. **`references: [{ path }]`** on every *consuming* project — the dependency edges.
3. **`tsc -b` / `tsc --build`** — a build *orchestrator* (distinct from the single-project `tsc -p`) that walks those edges topologically and uses `.tsbuildinfo` to skip up-to-date projects.

**Version anchors (these drive "is this available?" questions):**

| Feature | Landed in | Note |
| --- | --- | --- |
| `composite`, `references`, `tsc -b`, solution-style empty `files: []` | **TS 3.0** | the whole project-references system |
| `incremental` + `.tsbuildinfo` as a standalone flag | TS 3.4 | `composite` implies it |
| `declarationMap` cross-project navigation | TS 3.x | optional companion, recommended |
| `disableReferencedProjectLoad`, `disableSolutionSearching`, `disableSourceOfProjectReferenceRedirect` | TS 3.8 | large-monorepo editor-perf knobs |
| **`${configDir}`** template variable in `extends` bases | **TS 5.5** | makes a shared base's `outDir`/`rootDir`/`paths` resolve to the *extending* config's dir |
| `prepend`, `out` deprecated (no effect from 5.5, **error in 6.0**) | TS 5.0 → 6.0 | legacy `outFile` bundling — do not use |

> **`tsc -b` vs `tsc -p` in one line:** `tsc -p ./x` type-checks/emits **one** project and does *not* build its dependencies; `tsc -b ./x` finds the referenced projects, checks which are out of date, and **builds the out-of-date ones in dependency order first**. In a referenced setup you almost always want `-b`.

## Core Concepts

### `composite: true` — the consumable-project contract

Setting `"composite": true` (default `false`, since TS 3.0) is mandatory on any project that appears in another project's `references`. The handbook is explicit: *"Referenced projects must have the new `composite` setting enabled."* Enabling it **forces several options**:

- **`declaration` is set to `true`.** A referenced project *must* emit `.d.ts` — consumers type-check against that output, never the source. This is the single load-bearing reason composite exists.
- **`incremental` is set to `true`**, so the project writes a `.tsbuildinfo` and participates in up-to-date checks. (Corollary: `tsc -b` is **inherently incremental** for composite projects — you do *not* add `--incremental`; that flag is for standalone non-composite builds.)
- **`rootDir` default changes** to the directory containing `tsconfig.json` (rather than the inferred longest-common-path of the inputs). This is **not** a hard "you must set `rootDir`" requirement — but if your sources live under `src/`, set `"rootDir": "src"` explicitly so emitted paths mirror `src/**` into `outDir` cleanly instead of including the config dir.
- **All input files must be covered by `include`/`files`.** *"All implementation files must be matched by an `include` pattern or listed in the `files` array. If this constraint is violated, `tsc` will inform you which files weren't specified."* A file pulled in only by an `import` but excluded from the glob is an error under composite (see Anti-Patterns: composite-requires-all-files).

### `references` — declaring the edges

In a *consuming* project:

```json
{
  "compilerOptions": { "composite": true /* if this project is itself referenced */ },
  "references": [{ "path": "../core" }, { "path": "../utils" }]
}
```

- Each `path` "can point to a directory containing a `tsconfig.json` file, or to the config file itself (which may have any name)" — e.g. `"../core"` or `"../core/tsconfig.build.json"`.
- The edge changes resolution: *"Importing modules from a referenced project will instead load its output declaration file (`.d.ts`)."* So `import { x } from "@scope/core"` is type-checked against `../core/dist/*.d.ts`, not `../core/src`.
- Edges must form a **DAG** — the dependency graph must be acyclic. `tsc -b` rejects cycles.

### Solution-style root `tsconfig.json`

A repo-root config that builds the whole graph but compiles nothing itself:

```json
{
  "files": [],
  "references": [
    { "path": "packages/core" },
    { "path": "packages/utils" },
    { "path": "packages/api" }
  ]
}
```

The handbook's exact guidance: *"have a 'solution' `tsconfig.json` file that simply has `references` to all of your leaf-node projects and sets `files` to an empty array (otherwise the solution file will cause double compilation of files)."* The empty array is legal: *"starting with 3.0, it is no longer an error to have an empty `files` array if you have at least one `reference`."* `tsc -b` (from the repo root) then builds every package in dependency order. List **all** leaf projects here, not just the top-level app, or unreferenced packages won't build.

### `declarationMap` — cross-project go-to-definition

Without it, "go to definition" on a symbol from a referenced package lands in the generated `.d.ts`. With `"declarationMap": true` (emits `.d.ts.map`), *"you'll be able to use editor features like 'Go to Definition' and Rename to transparently navigate and edit code across project boundaries."* It is **not** forced by `composite` — it's the recommended optional companion for any package whose source you have locally. Pair it with `sourceMap` for runtime debugging. (Ship the `.d.ts.map` and the `.ts` source if you want consumers of a *published* package to navigate too.)

### Build mode internals: up-to-date checks & `.tsbuildinfo`

`tsc -b` *"will: find all referenced projects, detect if they are up-to-date, build out-of-date projects in the correct order."* It decides up-to-date-ness from each project's **`.tsbuildinfo`** file — written when `incremental`/`composite` is on, it stores *"information about the project graph from the last compilation"* so the next run can *"detect the least number of files to re-check and re-emit."*

- **`tsBuildInfoFile`** controls where that file goes; the default name is `.tsbuildinfo`, *"stored alongside the output files."* Under `outDir: dist` you'll see `dist/tsconfig.tsbuildinfo`. Pin it (e.g. into a cache dir) when you want it out of the publishable output.
- **`noEmitOnError` is implied across the build:** *"`tsc -b` effectively acts as if `noEmitOnError` is enabled for all projects"* — otherwise a broken upstream dep would emit once, then be skipped as "up to date" and you'd never see the error again.

### `${configDir}` (TS 5.5) — shareable bases

Before 5.5, relative paths in an `extends` base resolved against the *base* file's location — so a shared `tsconfig.base.json` (especially one in `node_modules`) couldn't set a useful `outDir`/`rootDir`. `${configDir}` resolves to *"the directory that the tsconfig is contained in"* — i.e. the **extending** config's dir. This makes one base reusable across every package:

```json
// tsconfig.base.json (shared)
{
  "compilerOptions": {
    "composite": true,
    "declaration": true,
    "declarationMap": true,
    "rootDir": "${configDir}/src",
    "outDir": "${configDir}/dist",
    "tsBuildInfoFile": "${configDir}/dist/.tsbuildinfo"
  }
}
```

Each package's `tsconfig.json` does `"extends": "../../tsconfig.base.json"` and `outDir`/`rootDir` land relative to *that* package, not the base. Requires TS 5.5+.

## Tools / Frameworks

- **`tsc -b` / `tsc --build`** — the build orchestrator. Accepts multiple config paths (`tsc -b src test`); *"don't worry about ordering the files… `tsc` will re-order them so that dependencies are always built first."* Build-mode flags:
  - `--verbose` — log what's being built and why (combine with any flag).
  - `--dry` — show what *would* build without building (combine with `--clean`).
  - `--clean` — delete the outputs of the specified projects.
  - `--force` — *"act as if all projects are out of date"* (ignore `.tsbuildinfo`).
  - `--watch` / `-w` — watch mode (*"may not be combined with any flag except `--verbose`"*).
- **`disableReferencedProjectLoad`** — stop the editor eagerly loading the *entire* reference graph in a huge monorepo (load on demand instead).
- **`disableSolutionSearching`** — exclude a project from "find all references"/"go to definition" solution-wide searches when it's only there to be built.
- **`disableSourceOfProjectReferenceRedirect`** — make the editor read a referenced project's `.d.ts` output instead of redirecting into its source (rarely needed; helps perf when source is huge).
- **Workspace managers (pnpm/npm/yarn)** — provide the *runtime* symlink so `@scope/core` resolves to the sibling package; project references provide the *build ordering and types*. The two are orthogonal — see Methodology.

## Methodology

1. **Mark every leaf package `composite: true`** (via a shared `${configDir}` base) so each emits `.d.ts` + `.tsbuildinfo`. Add `declarationMap` for in-repo navigation.
2. **Add `references` edges** from each consumer to its direct dependencies (point `path` at the dependency's dir/config). Keep the graph acyclic.
3. **Create a solution root** with `files: []` + `references` to *all* leaf packages.
4. **Build with `tsc -b` from the root** (`tsc -b --watch` in dev). Never `tsc -p` a referenced project expecting its deps to build.
5. **In a workspace monorepo, layer the two systems:** let the package manager's symlinks resolve package names at runtime; use `references` for build order + types. **Prefer this over `paths`** — `paths` are type-only and don't create build edges (next point).
6. **Use `paths` only as a fallback** when you can't rely on workspace symlinks, and remember a bundler/`tsc-alias`/package `imports` must make them work at runtime. Set them in the shared base with `${configDir}`.
7. **Verify** with `tsc -b --dry --verbose` (what would build, in what order) and `tsc -b --force` to rule out a stale `.tsbuildinfo`.

## Practical Patterns

**Referenced (leaf) package — `packages/core/tsconfig.json`:**

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "declaration": true,
    "declarationMap": true,
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src/**/*"]
}
```

**Consuming package that depends on it — `packages/api/tsconfig.json`:**

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src/**/*"],
  "references": [{ "path": "../core" }, { "path": "../utils" }]
}
```

**Solution root — `tsconfig.json` (builds the whole graph, compiles nothing itself):**

```json
{
  "files": [],
  "references": [
    { "path": "packages/utils" },
    { "path": "packages/core" },
    { "path": "packages/api" }
  ]
}
```

**`tsc -b` invocations:**

```shell
tsc -b                       # build the solution in ./tsconfig.json (whole graph, in order)
tsc -b --verbose             # ...and explain which projects build and why
tsc -b --watch               # incremental rebuild on change (dev loop)
tsc -b --dry --verbose       # preview the build plan without writing anything
tsc -b --clean               # delete all emitted outputs (.js/.d.ts/.tsbuildinfo)
tsc -b --force               # ignore .tsbuildinfo; rebuild everything
tsc -b packages/api          # build just api + its (out-of-date) dependencies
```

**Workspace + references together (the recommended monorepo shape):**

```jsonc
// package.json (pnpm/npm/yarn workspace) gives RUNTIME resolution:
//   "@scope/api" → symlink to packages/api
// tsconfig references give BUILD ORDER + TYPES.
// In packages/api/src/index.ts:
import { thing } from "@scope/core"; // resolves via workspace symlink at runtime,
                                     // and is type-checked via the ../core reference's .d.ts
```

## Anti-Patterns

- **Using `tsc -p` (or bare `tsc`) on a referenced project.** It won't build dependencies; you'll get stale or missing `.d.ts`. Use `tsc -b`.
- **`paths` instead of `references` for cross-package imports.** `paths` are **type-only** and create **no build edge** — `tsc -b` won't build a sibling just because a `paths` entry points at it, and the emitted JS has unresolved bare specifiers without a bundler/`tsc-alias`/package `imports`. Use workspace symlinks + `references`; reserve `paths` for fallback resolution.
- **Forgetting `composite` on a referenced project.** Error: the referenced project must be composite. Add `composite: true` (which also forces `declaration`).
- **`include`/`files` that miss an imported file under composite** (composite-requires-all-files). A file reached only by `import` but outside the glob errors — widen `include` or add it to `files`.
- **Omitting `files: []` in the solution root.** The root then compiles its own inputs *and* builds the references → double compilation. Keep it empty.
- **Circular references.** The graph must be a DAG; break the cycle (extract shared types into a third leaf package).
- **Expecting "go to definition" to reach source without `declarationMap`.** It lands in `.d.ts`. Enable `declarationMap` on the referenced package.
- **`prepend: true` / `outFile` bundling.** Legacy concat-output project references — deprecated since 5.0, no effect from 5.5, and an **error in 6.0**. Don't adopt them; use a real bundler for single-file output.
- **A stale `.tsbuildinfo` masking changes** (e.g. after a git operation that rewrites mtimes). Symptom: "nothing to build" when there clearly is. Fix: `tsc -b --force` (or `--clean` then rebuild).
- **`tsc -b` over a huge graph in the editor feeling slow.** Reach for `disableReferencedProjectLoad` (lazy graph load) and `disableSolutionSearching` rather than collapsing packages back into one.

## Troubleshooting

- **"Referenced project '…' must have setting `composite: true`"** → add `composite: true` to that project's `tsconfig.json`.
- **"Output file '…/x.d.ts' has not been built from source file '…/x.ts'"** → a downstream project references an upstream one whose outputs are stale/missing; build with `tsc -b` (which orders deps) instead of `tsc -p`, or run `tsc -b --force`.
- **"File '…' is not listed within the file list of project '…'. Projects must list all files or use an `include` pattern."** → composite-requires-all-files; widen `include` or add to `files`.
- **"Cannot find module '@scope/core' or its type declarations"** → the `references` edge is missing *or* the referenced project hasn't emitted `.d.ts` yet; add the edge and run `tsc -b`. Runtime resolution is a separate concern (workspace symlink / `paths` + bundler).
- **`tsc -b` says everything is up to date but it isn't** → stale `.tsbuildinfo`; `tsc -b --force` or delete the `.tsbuildinfo`. Confirm the plan with `tsc -b --dry --verbose`.
- **Go-to-definition lands in `.d.ts`, not `.ts`** → enable `declarationMap` on the referenced package and rebuild.
- **Editor slow / high memory in a large monorepo** → `disableReferencedProjectLoad: true` (load referenced projects lazily); consider `disableSolutionSearching` on build-only projects.
- **Shared base's `outDir` resolves to the wrong (base) directory** → you're on TS < 5.5 or didn't use `${configDir}`; upgrade to 5.5+ and wrap paths as `"${configDir}/dist"`.
- **Deprecation error on `prepend`/`out` after upgrading toward 6.0** → remove them; they no longer function and error in 6.0.

## References

- TypeScript Handbook — Project References (composite, references, solution config, declarationMap, build mode): https://www.typescriptlang.org/docs/handbook/project-references.html
- TypeScript — TSConfig Reference (`composite`, `incremental`, `tsBuildInfoFile`, `declarationMap`, `disableReferencedProjectLoad`, `disableSolutionSearching`): https://www.typescriptlang.org/tsconfig/
- TypeScript 5.5 release notes (`${configDir}` template variable): https://devblogs.microsoft.com/typescript/announcing-typescript-5-5/
- TypeScript 5.0 release notes (deprecation of `prepend`/`out`): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html
- TypeScript 6.0 release notes (deprecated options become errors): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html
- Total TypeScript — TSConfig Cheat Sheet (monorepo/project-references baselines): https://www.totaltypescript.com/tsconfig-cheat-sheet
