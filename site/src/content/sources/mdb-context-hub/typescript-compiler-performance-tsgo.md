---
title: "TypeScript Compiler Performance and tsgo"
description: "A lang-js-ts reference for why tsc and the editor get slow, how to measure and fix it, and what the Go-based native port (TypeScript 7 / 'Corsa' / tsgo) changes. Three jobs: (1) instrument a slow type"
---

# TypeScript Type-Checking Performance & the Go Compiler (TS 7 "Corsa" / tsgo)

A `lang-js-ts` reference for **why `tsc` and the editor get slow, how to measure and fix it, and what the Go-based native port (TypeScript 7 / "Corsa" / `tsgo`) changes**. Three jobs: (1) instrument a slow type-check and read the numbers, (2) apply the build-level levers that cut type-check and editor latency, (3) understand the native-port preview accurately — version-precise, honest about preview status, no fabricated feature claims.

Scope boundary up front: this skill tells you **where the type cost is and how to reduce it at the build/config level**. It is *not* a tutorial on writing conditional/mapped/template-literal types — when the fix is to refactor the type operator itself, that's `typescript-advanced-types`. General `compilerOptions` reference is `typescript-compiler-config`; the programmatic compiler/transformer/LS-plugin API is `typescript-compiler-api`; bundler/transpiler throughput (esbuild/swc/Vite) is the `*-build-tooling-bundlers` siblings.

## Overview

Type-checking cost is dominated by **how many types the checker has to create and compare**, not by lines of code. A handful of recursive conditional types, a 200-member union, or an unannotated export that forces whole-program inference can cost more than thousands of plain statements. The editor (tsserver) runs the same checker, so a slow `tsc --noEmit` and a laggy "go to definition" share a root cause.

The workflow is always: **measure first** (`--extendedDiagnostics`, then `--generateTrace` if you need a per-construct breakdown) → **find the hot spot** (the file/type that dominates `Instantiations` or `checkTime`) → **apply the cheapest lever that moves it** (annotate a return type, cap a union, split into project references, `skipLibCheck`). Guessing at fixes without a trace wastes effort on cold paths.

Separately, Microsoft is rewriting the entire compiler + language service in **Go** ("Project Corsa", shipping as **TypeScript 7**). It is in **public nightly preview** as `@typescript/native-preview` (binary `tsgo`) and reports ~10× faster type-checking and ~8× faster editor load on Microsoft's own benchmarks. It is **not yet feature-complete** and **drops the existing programmatic API** — details and current flux are in the "Native Go port" section.

## Core Concepts

### Diagnosing a slow type-check — `--extendedDiagnostics`

`tsc --extendedDiagnostics --noEmit` prints the timing + size breakdown. Run it first; it's cheap and tells you whether you have a *type-system* problem or an *I/O/program-graph* problem. The numbers that matter:

| Metric | Meaning | What a high value points at |
| --- | --- | --- |
| **Instantiations** | Count of type instantiations the checker created (generics/conditional/mapped types expanded). **The single most useful number for finding expensive types.** | Heavy generics, recursive conditional types, large unions being distributed. Millions = a type blowup. |
| **Types** | Distinct types created across the program. | Same culprits as Instantiations, plus large `.d.ts` surface. |
| **Check time** | Time in the type-checker itself. | Expensive types (correlate with Instantiations). |
| **Program time** | I/O + scanning + parsing + building the file graph. | Too many files in the program (`include` too broad, `node_modules` pulled in). |
| **Parse / Bind time** | Front-end phases. | Sheer file count / huge generated files. |
| **I/O Read / I/O Write time** | Filesystem. | Slow disk, network FS, huge `.tsbuildinfo`. |
| **Memory used** | Peak heap. | Large program; correlate with Types. |

Heuristic: **high Check time + high Instantiations → a type problem** (go to a trace, fix the types). **High Program time with low Check time → a file-graph problem** (tighten `include`/`exclude`, add project references, `skipLibCheck`). `--diagnostics` is the shorter legacy subset of the same output.

### Pinpointing the cost — `--generateTrace` + Perfetto + analyze-trace

When `--extendedDiagnostics` says "types are expensive" but not *which*, capture an event trace:

```bash
tsc --noEmit --generateTrace ./trace-out
```

This emits **`trace.json`** (a Chrome-tracing/`about:tracing` event stream — `checkSourceFile`, `checkExpression`, `checkVariableDeclaration`, `structuredTypeRelatedTo` spans) and **`types.json`** (the types referenced by the trace). View `trace.json` in **[ui.perfetto.dev](https://ui.perfetto.dev)**, `chrome://tracing`, or `edge://tracing`. Wide bars = the files/checks eating the time; click a span to see the source position.

For an automated readout, run the official analyzer:

```bash
npx @typescript/analyze-trace ./trace-out          # ranks hot spots
npx @typescript/analyze-trace ./trace-out --forceMillis 200   # lower the report threshold
```

`analyze-trace` prints the slow files and the specific expensive types (with `types.json` IDs) so you don't have to read the raw trace by hand. This is *diagnosis* — the **fix** (rewriting a conditional type, capping a union) belongs to `typescript-advanced-types`; this skill just gets you to the offending construct and applies the build-level mitigations below.

### Speed levers — configuration

| Lever | Since | Effect / when |
| --- | --- | --- |
| **`skipLibCheck: true`** | — | Skip type-checking inside `.d.ts` files. Usually the **biggest single config win** — cuts a large chunk of Check time. Caveat: can mask genuine conflicts between mismatched `@types` packages; it's a perf trade, not a free win. |
| **`incremental: true`** | 3.4 | Persist a `.tsbuildinfo` so the next `tsc` only re-checks what changed. Standard for repeated local/CI runs. |
| **`assumeChangesOnlyAffectDirectDependencies: true`** | 3.8 | On a rebuild, re-check only changed files **and their direct importers**, not the full transitive closure. Faster watch/incremental at the cost of occasionally missing a deep-transitive error — a deliberate soundness-for-speed trade. |
| **Project references** (`composite` + `references`) | 3.0 | Split a big program into smaller projects so `tsc -b` builds them **in parallel and incrementally**, and the editor loads only the relevant project. The structural lever for large monorepos (Microsoft suggests ~5–20 projects). *Deep setup → `typescript-project-references-monorepo` / `typescript-compiler-config`.* |
| **`isolatedDeclarations: true`** | 5.5 | Require exported declarations to be fully annotated so a `.d.ts` can be produced **per file without the type-checker** — enabling parallel/tool-driven declaration emit (`transpileDeclaration` API; esbuild/swc DTS). Reported ~3× faster declaration builds in a sample monorepo. Cost: you must annotate public API return types. |
| **`isolatedModules: true`** | — | Guarantee each file transpiles **alone** (no cross-file type info) — the contract every single-file transpiler (esbuild/swc/Babel/Node strip-types) relies on. Doesn't speed `tsc` itself, but unlocks the fast-emit architecture below. |

### Speed levers — code patterns

These reduce the work the checker does. Keep them **diagnostic/build-level**; the deep "how to author the type" treatment is `typescript-advanced-types`.

- **Add explicit return-type annotations on exported functions.** Without them the checker must *infer* the return type — often the largest source of Instantiations in a hot file. Annotating cuts the inference and improves editor responsiveness. (This is also what `isolatedDeclarations` enforces.)
- **Prefer `interface extends` over large intersection (`&`) types.** Interfaces are cached and compared by reference; a big intersection is recomputed structurally on every comparison. Same shape, far cheaper.
- **Cap union size.** Unions with many members (≈10+, and pathologically 100s) cost quadratically in assignability and *distribute* across conditional types. Replace giant unions with a base type + discriminant where possible.
- **Avoid recursive/deeply-nested conditional & template-literal blowups.** A single recursive conditional or a template-literal type over a large union can generate millions of instantiations. Find it via the trace; the *rewrite* is `typescript-advanced-types`' job.
- **`import type` / type-only imports.** Make value-vs-type imports explicit (`import type { T }`) so the type graph and the runtime graph stay separate; pairs with `verbatimModuleSyntax`/`isolatedModules` and avoids dragging value modules into type-only paths.

### `tsc --noEmit` as the type-gate (decouple checking from emit)

The dominant modern build splits the two jobs `tsc` historically did:

- **A fast single-file transpiler emits JS** — `esbuild` / `swc` / Vite / Node's native type-stripping. Milliseconds, no type-checking.
- **`tsc --noEmit` is the type-checker gate** — run in CI and in the editor, produces no files.

This is faster because emit no longer waits on the checker, and it parallelizes. It **requires** `isolatedModules: true` (and `verbatimModuleSyntax`/`erasableSyntaxOnly` for the native-Node path) so the per-file transpiler can't mis-handle constructs that need whole-program info (`const enum`, type-only re-exports, parameter properties). *The transpiler/bundler config itself → the `*-build-tooling-bundlers` siblings; the tsconfig flags → `typescript-compiler-config`.*

### The native Go port — TypeScript 7 / "Corsa" / `tsgo`

**What it is.** A from-scratch **port of the TypeScript compiler *and* language service to Go** — codename **"Corsa"** (the existing JavaScript-based compiler is **"Strada"**). It ships as **TypeScript 7**. Staging repo: **`microsoft/typescript-go`**. Go was chosen for native compilation plus **shared-memory parallelism / concurrency** (the checker fans work across cores), which the single-threaded JS implementation can't do.

**The speed claim (Microsoft's own benchmarks — not a universal guarantee).** ~**10×** faster type-checking on real projects: VS Code (~1.5M LOC) 77.8s → 7.5s (**10.4×**), Playwright 11.1s → 1.1s (**10.1×**), TypeORM 17.5s → 1.3s (**13.5×**). Editor **project-load** ~9.6s → ~1.2s (**~8×**). Peak **memory ~half** of the JS implementation. Treat as "order-of-magnitude on large codebases," verify on your own repo.

**Status (as of the December 2025 "Progress on TypeScript 7" post — currency-sensitive, confirm before quoting).** Stable enough to try daily; **not yet at full parity**. What now **works**: command-line type-checking at high compatibility (in a 6,000-error test corpus, only ~74 cases diverge); JSX checking; JS-via-JSDoc checking; **`--incremental` + `.tsbuildinfo`**; **project references**; **`--build` (`tsc -b`)**; **parallel multi-project compilation**; a real **LSP language service** in the editor (completions + auto-imports, go-to-definition/implementation/type-definition, find-all-references, rename, hover, signature help, formatting, code lens, call hierarchy). *(Note: the earlier May-2025 announcement listed no project refs / no `--build` / no declaration emit — that is **superseded**; the Dec-2025 state above is current.)*

**Still in flux — flag these explicitly:**
- **JS emit pipeline is incomplete.** Downlevel emit "realistically only goes as far back as the **`es2021`** target," and there is **no decorator emit** yet.
- **`--watch`** exists but "may be less-efficient than the existing TypeScript compiler in some scenarios."
- **The Strada compiler API is gone.** "Corsa / TypeScript 7.0 will not support the existing Strada API." This breaks **custom transformers, programmatic `ts.*` consumers, and language-service plugins**. "The Corsa API is still a work in progress, and no stable tooling integration exists for it." (Tools like ts-loader, ESLint type-aware rules, ts-jest, API-extractor must wait for / migrate to the new API.) *The Strada API surface itself → `typescript-compiler-api`.*
- **JSDoc was rewritten** with reduced backward compatibility (dropped `@enum`/`@constructor` recognition, stricter `Object` handling) — JS-heavy codebases may see new errors.

**Versioning & how to try it.** Published as **nightly `7.0.0-dev.*`** builds on npm under **`@typescript/native-preview`** (a moving dev tag — don't pin one nightly as "the version"). Binary is **`tsgo`**, a drop-in for `tsc`:

```bash
npm i -D @typescript/native-preview
npx tsgo --noEmit -p ./tsconfig.json   # use like tsc
```

**Editor:** install the **"TypeScript (Native Preview)"** extension (`TypeScriptTeam.native-preview`), then run the command-palette action **"TypeScript Native Preview: Enable (Experimental)"** (equivalently the `typescript.experimental.useTsgo` setting). It swaps the editor's language service to the `tsgo` LSP.

**Release line.** **TypeScript 6.0 (March 2026) is the last JavaScript-based release** (no 6.1 planned); 6.x carries deprecations that pre-align with the native codebase. **TS 7.0 is the native compiler** and ships when parity is reached (no firm public date in the Dec-2025 post). *(Version anchors here match the `typescript-compiler-config` skill — keep them in sync.)*

## Tools / Frameworks

- **`tsc --extendedDiagnostics` / `--diagnostics`** — the first-look timing + size report (Instantiations, Types, Check/Program time, Memory).
- **`tsc --generateTrace <dir>`** — emit `trace.json` + `types.json` for Perfetto / `chrome://tracing` / `edge://tracing`.
- **`@typescript/analyze-trace`** — `npx @typescript/analyze-trace <dir>` (`--forceMillis N`) ranks the hot files/types automatically.
- **`tsc --explainFiles` / `--listFilesOnly`** — *why* is this file in the program? (catches an over-broad `include` inflating Program time).
- **`tsc -b --verbose` / `--dry`** — see what project references actually rebuild.
- **`@typescript/native-preview` (`tsgo`)** — the native-port nightly; benchmark it against your `tsc` baseline.
- **esbuild / swc / Vite / Node `--experimental-strip-types`** — the fast emitters paired with `tsc --noEmit` (config → the bundler siblings).
- **`@arethetypeswrong/cli`** — orthogonal but adjacent: validates a published package's `.d.ts`/`exports` (correctness, not speed).

## Methodology

1. **Reproduce with a number, not a vibe.** `tsc --extendedDiagnostics --noEmit`. Record Instantiations, Check time, Program time, Memory.
2. **Classify.** High Check time + high Instantiations → **type problem** (step 3). High Program time / low Check time → **file-graph problem** (jump to step 5).
3. **Trace the type problem.** `tsc --noEmit --generateTrace ./trace-out`; run `analyze-trace` (or open `trace.json` in Perfetto) to name the offending file/type.
4. **Fix at the cheapest level.** Annotate the exported return type; swap a big intersection for an `interface extends`; cap/​discriminate a giant union. If the fix is *inside* the type operator, hand off to `typescript-advanced-types`.
5. **Fix the file-graph / build.** `skipLibCheck: true`; tighten `include`/`exclude`; add `incremental`; split into **project references** for parallel/partial builds; consider `assumeChangesOnlyAffectDirectDependencies` for watch.
6. **Decouple emit from checking** if not already: fast transpiler emits JS, `tsc --noEmit` is the gate (`isolatedModules: true`). Add `isolatedDeclarations: true` if you publish `.d.ts` and want parallel declaration emit.
7. **Re-measure.** Confirm Instantiations/Check time actually dropped — don't trust the fix without the second `--extendedDiagnostics`.
8. **Consider `tsgo` for the worst cases.** For a large slow repo, benchmark `npx tsgo --noEmit` against your `tsc` baseline — but **only as a non-authoritative second checker** until TS 7 is stable, and verify your emit target/decorators and any compiler-API tooling aren't on the unsupported list.

## Practical Patterns

**Measure, then trace, then auto-analyze:**

```bash
tsc --noEmit --extendedDiagnostics
tsc --noEmit --generateTrace ./trace-out
npx @typescript/analyze-trace ./trace-out --forceMillis 200
# open ./trace-out/trace.json in https://ui.perfetto.dev for the visual flame view
```

**Fast-build config (transpiler emits, `tsc` gates):**

```json
{
  "compilerOptions": {
    "noEmit": true,
    "skipLibCheck": true,
    "incremental": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "module": "preserve",
    "target": "es2022",
    "strict": true
  }
}
```

(esbuild/swc/Vite does the JS emit; this `tsconfig` is the type-gate only. Flag reference → `typescript-compiler-config`.)

**Library with parallel declaration emit:**

```json
{
  "compilerOptions": {
    "declaration": true,
    "isolatedDeclarations": true,
    "skipLibCheck": true,
    "composite": true,
    "incremental": true
  }
}
```

(Annotate every exported return type; a downstream tool or `transpileDeclaration` can now emit `.d.ts` per file in parallel.)

**Try the native port without committing your build to it:**

```bash
npm i -D @typescript/native-preview
npx tsgo --noEmit -p ./tsconfig.json        # compare wall-clock vs `tsc --noEmit`
# editor: install "TypeScript (Native Preview)" → palette "TypeScript Native Preview: Enable (Experimental)"
```

## Anti-Patterns

- **Optimizing without a trace.** Refactoring types you *guess* are slow. Always let `--extendedDiagnostics` → `--generateTrace`/`analyze-trace` name the hot spot first.
- **Treating `skipLibCheck` as the whole answer.** It's the biggest easy win but can hide real `@types` conflicts; pair it with a periodic full check, and don't use it to silence a genuine error.
- **Unannotated exported return types in hot modules.** Forces whole-program inference and inflates Instantiations; it also blocks `isolatedDeclarations` and slows the editor.
- **Giant unions / unconstrained recursive conditionals as a "clever" API.** They blow up Instantiations quadratically and distribute through conditionals. (Rewrite belongs to `typescript-advanced-types`, but *spotting the cost* is here.)
- **One monolithic project for a huge monorepo.** No parallelism, full re-checks, slow editor load. Split into project references.
- **Assuming `tsgo` is a finished drop-in.** As of Dec-2025 it has **incomplete emit (downlevel only ~es2021, no decorators)**, a **less-efficient `--watch`**, and **no Strada API** — so transformers, type-aware ESLint, ts-loader, ts-jest, API-extractor and similar tooling may not run against it yet. Use it as a fast second checker, not your authoritative emit/CI gate, until TS 7 is stable.
- **Pinning a specific `7.0.0-dev.*` nightly as "the TS 7 version."** It's a moving tag; describe the channel (`@typescript/native-preview`, `tsgo`) instead.
- **Quoting the old May-2025 announcement's limitations as current.** Project references, `tsc -b`, incremental, and the LSP all work as of the Dec-2025 progress post — cite the dated status.

## Troubleshooting

- **`tsc --noEmit` takes minutes** → `--extendedDiagnostics`; if Check time + Instantiations dominate, trace it; if Program time dominates, tighten `include`/`exclude` and add `skipLibCheck`.
- **Editor "loading…"/laggy IntelliSense but `tsc` is okay** → tsserver loads the whole project; split into project references, add return-type annotations, and/or try the `tsgo` Native Preview language service.
- **Instantiations in the millions** → a recursive conditional or large distributed union; find it with `analyze-trace`, then refactor (→ `typescript-advanced-types`).
- **`analyze-trace` reports nothing useful** → lower `--forceMillis`, or open `trace.json` directly in Perfetto and look for the widest `checkSourceFile`/`structuredTypeRelatedTo` bars.
- **Incremental build re-checks everything** → ensure `incremental`/`composite` is on and `.tsbuildinfo` isn't being deleted between runs; for watch, try `assumeChangesOnlyAffectDirectDependencies` (accept the soundness trade).
- **`isolatedDeclarations` errors flood in** → exported symbols lack explicit type annotations; annotate the public return/value types (that's the contract that enables fast DTS).
- **`tsgo` emits nothing / wrong JS for old targets or decorators** → expected; the native emit pipeline only downlevels to ~`es2021` and doesn't emit decorators yet — keep `tsc`/esbuild for emit and use `tsgo` for checking.
- **A transformer / type-aware lint rule / build plugin breaks under TS 7** → the Strada compiler API is dropped and the Corsa API is still WIP with no stable integration; stay on TS 6.x/`tsc` for that tooling until it migrates (→ `typescript-compiler-api`).
- **New type/JSDoc errors only under `tsgo`** → JSDoc was rewritten with reduced compat (`@enum`/`@constructor` dropped, stricter `Object`); reconcile against the TS 7 notes before assuming a bug.

## References

- TypeScript DevBlog — Announcing TypeScript Native Previews (`tsgo`, `@typescript/native-preview`, VS Code extension): https://devblogs.microsoft.com/typescript/announcing-typescript-native-previews/
- TypeScript DevBlog — Progress on TypeScript 7 (December 2025; current parity/flux status): https://devblogs.microsoft.com/typescript/progress-on-typescript-7-december-2025/
- TypeScript DevBlog — A 10x Faster TypeScript / the native port announcement (Strada vs Corsa, why Go, 10x benchmarks): https://devblogs.microsoft.com/typescript/typescript-native-port/
- microsoft/typescript-go (staging repo for the native port): https://github.com/microsoft/typescript-go
- `@typescript/native-preview` on npm (nightly `7.0.0-dev.*`, `tsgo`): https://www.npmjs.com/package/@typescript/native-preview
- TypeScript Wiki — Performance (extendedDiagnostics, generateTrace, recommendations): https://github.com/microsoft/TypeScript/wiki/Performance
- `@typescript/analyze-trace` on npm: https://www.npmjs.com/package/@typescript/analyze-trace
- Perfetto UI (trace viewer): https://ui.perfetto.dev
- TypeScript 5.5 release notes — Isolated Declarations + `transpileDeclaration`: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html
- TSConfig — `isolatedDeclarations`: https://www.typescriptlang.org/tsconfig/isolatedDeclarations.html
- TSConfig — `assumeChangesOnlyAffectDirectDependencies`: https://www.typescriptlang.org/tsconfig/assumeChangesOnlyAffectDirectDependencies.html
- VS Code Marketplace — TypeScript (Native Preview) extension: https://marketplace.visualstudio.com/items?itemName=TypeScriptTeam.native-preview
