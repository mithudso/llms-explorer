---
title: "TypeScript Migration and Adoption"
description: "A lang-js-ts reference for taking an existing JavaScript codebase to TypeScript incrementally, without a stop-the-world rewrite and without a red CI. The goal: keep the app shipping while types arrive"
---

# JS→TS Migration & Incremental Adoption

A `lang-js-ts` reference for taking an existing **JavaScript codebase to TypeScript incrementally**, without a stop-the-world rewrite and without a red CI. The goal: keep the app shipping while types arrive file-by-file, get type *checking* before you change a single extension, sequence the strictness flags so each one is a bounded chunk of work, and treat suppressions as debt you can count and burn down. This is the **journey** — ordering, decisions, and debt management. It is **not** the flag catalog: every `compilerOptions` flag's exact semantics, defaults, and the module quartet live in `typescript-compiler-config`; this doc names a flag and links there rather than re-documenting it.

## Overview

A successful migration has four phases that overlap, not a single switch:

1. **Enable TS over the JS** — `allowJs: true` so `.js` compiles alongside `.ts`; optionally `checkJs`/`// @ts-check` to start *checking* the JS in place. No renames yet. The build still produces the same output.
2. **Get types onto the JS via JSDoc** — annotate hot/leaf modules with JSDoc so you catch real bugs and design the types *before* converting. JSDoc has limits (below); where it can't express a type, that file is a rename candidate.
3. **Rename incrementally** — `.js`→`.ts` (`.jsx`→`.tsx`) a module or directory at a time, fixing the errors that surface, keeping CI green after each batch.
4. **Ramp strictness** — start loose, turn on one flag at a time (lead with `strictNullChecks`), drive `noImplicitAny` to `true` as the milestone, and burn down the `any`/`@ts-expect-error` debt accumulated along the way.

The throughline: **`tsc --noEmit` is the type gate, your existing bundler/transpiler keeps doing the build.** You never block shipping on the type-checker until you choose to.

> **Version anchor (TS 5.x vs 6.0 — this changes your starting point).** Through TS 5.x the *compiler* default is `strict: false`, so a fresh `tsconfig.json` is permissive and you opt *into* strictness. **TS 6.0 (released 2026) flips `strict` to default `true`** — the release notes are explicit: *"If you were relying on the previous default of `false`, you'll need to explicitly set `"strict": false` in your `tsconfig.json`."* For a JS codebase adopting TS *on 6.0*, that means: **write `"strict": false` explicitly in step 1**, or your very first `tsc` run buries you under `strictNullChecks` + `noImplicitAny` errors across the whole tree at once — the exact all-at-once trap this skill exists to avoid. 6.0 also defaults `module: esnext`, `target` to a floating current-year spec (currently `es2025`), `types: []`, and makes `esModuleInterop`/`allowSyntheticDefaultImports` undisablable. **Pin `strict`, `target`, `module`, and `lib` explicitly** so a 5.x and a 6.0 toolchain give the same migration baseline. (Flag defaults table → `typescript-compiler-config`.)

## Core Concepts

### Phase 1 — Enable TS over a mixed codebase (`allowJs` + `checkJs`)

`allowJs: true` lets `.js`/`.jsx` files into the program so TypeScript and JavaScript coexist and import each other. On its own it gives you nothing but co-compilation. Add checking in one of two granularities:

- **Whole-project:** `checkJs: true` type-checks *every* `.js` file (using whatever JSDoc/inference is present). Escape hatch per file: `// @ts-nocheck` at the top opts a noisy file out.
- **Per-file opt-in:** leave `checkJs: false` and put `// @ts-check` at the top of individual files you're ready to harden. This is the safer default on a large codebase — you choose which files start failing the build.

> **The official "Migrating from JavaScript" handbook page predates this workflow** — it leads with `target: es5` + `noEmitOnError` and never mentions `checkJs`/`@ts-check`. The current practice is **checkJs-first**: check the JS in place, fix and annotate, *then* rename. Ground the `checkJs`/`@ts-check` mechanics in the handbook's "Type Checking JavaScript Files" page instead. (Flagging this because the most-linked guide is stale on exactly this point.)

A minimal **phase-1 `tsconfig.json`** that compiles a mixed tree and checks nothing yet (you turn `checkJs` on, or sprinkle `// @ts-check`, when ready):

```json
{
  "compilerOptions": {
    "allowJs": true,
    "checkJs": false,
    "strict": false,
    "noImplicitAny": false,
    "target": "es2022",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "lib": ["es2022"],
    "esModuleInterop": true,
    "skipLibCheck": true,
    "noEmit": true,
    "outDir": "dist"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

`noEmit: true` makes `tsc` a pure checker — your bundler/swc/Babel/`tsx` still builds. (If you want `tsc` itself to emit during migration, drop `noEmit` and set `outDir`; pair with `noEmitOnError: false` early so type errors don't block the JS output you already shipped.)

### Phase 2 — JSDoc-as-types (and its limits)

Before renaming, you can express real types in `.js` with JSDoc and get full checking under `// @ts-check`/`checkJs`. This is high-leverage: you find bugs and *design the type surface* with zero syntax churn, and a clean JSDoc'd file renames to `.ts` almost trivially.

```js
// @ts-check

/**
 * @param {string} id
 * @param {{ retries?: number; signal?: AbortSignal }} [opts]
 * @returns {Promise<User>}
 */
async function fetchUser(id, opts) { /* ... */ }

/**
 * @typedef {Object} User
 * @property {string} id
 * @property {string} name
 * @property {number} [age]   // optional
 */

/** @type {User[]} */
const users = [];

/** @template T @param {T} x @returns {T} */
const identity = (x) => x;

// Import a type from another module (TS 5.5+ `@import`, or inline `import()`):
/** @import { Config } from "./config.js" */
/** @type {Config} */
let cfg;
/** @param {import("./db.js").Client} client */
function withClient(client) {}

// Cast (parenthesize the expression):
const el = /** @type {HTMLInputElement} */ (document.getElementById("email"));
```

Supported tags worth knowing: `@type`, `@param`, `@returns`, `@typedef` + `@property`, `@callback`, `@template` (with constraints `@template {string} K` and defaults `@template [T=object]`), `@satisfies` (TS 4.9+), `@enum`, `@this`, `@extends`/`@implements`/`@override`, and `@import`/`import()` for cross-file types.

**Limits — where JSDoc can't reach (these files are your rename candidates):**

- **Non-nullable `!T` is ignored**; nullable `?T` only behaves once `strictNullChecks` is on.
- No JSDoc syntax for many **advanced type operators** — conditional types, mapped types, `infer`, complex generic gymnastics are awkward or impossible in comments. (Those operators themselves → `typescript-advanced-types`.)
- Optional-with-default uses the bracket form `[prop=42]`, not postfix `=`; some tags (`@yields`, `@member`, `@memberof`) aren't supported.
- It's verbose: once a file needs generics-heavy or operator-heavy types, **stop annotating and rename it** — `.ts` syntax is cheaper than fighting JSDoc.

### Phase 3 — Renaming: leaf-first vs entry-first

Renaming a file from `.js` to `.ts` flips it from "checked only if `// @ts-check`" to "always checked, with full TS rules." Two orderings:

- **Leaf-first (bottom-up) — the default.** Convert modules with **no internal dependencies** first (utils, types, constants), then work up the import graph. Each converted leaf gives accurate types to everything that imports it, so upstream conversions get *easier*. Errors stay local and small. Best for keeping CI green.
- **Entry-first (top-down).** Start at entry points / shared interfaces. Surfaces the *shape* of the whole system early and forces key boundary types to exist, but every unconverted dependency below is still `any`-ish, so you lean on stubs and provisional types. Use when the architecture is the risk, not the leaves.

Most migrations are **leaf-first with a few entry-first interface files** drawn early to anchor the domain model. Convert in **small batches that each keep `tsc --noEmit` passing** (or only adding *tracked* suppressions); a batch should be a reviewable PR, not a 400-file flag day.

### Phase 4 — The strictness ramp

Turn flags on **one at a time**, each as its own PR-sized chunk, instead of `strict: true` in one commit (which dumps every category of error simultaneously).

1. **`strictNullChecks` first.** The single highest-value flag — `null`/`undefined` become distinct types. Biggest bug-catch, and it *unlocks* JSDoc nullability and `strictPropertyInitialization`. Do this before the rest of the `strict` family.
2. **The rest of the `strict` family**, roughly cheapest-first: `noImplicitThis`, `alwaysStrict`, `strictBindCallApply`, `strictFunctionTypes`, `strictPropertyInitialization`, `useUnknownInCatchVariables`. (Membership/semantics → `typescript-compiler-config`.)
3. **`noImplicitAny: true` is the milestone**, not the starting gun. Keep it **`false`** during phases 1–3 — flip it early and your still-untyped `.js`/freshly-renamed `.ts` files erupt in implicit-`any` errors everywhere at once. Reaching `noImplicitAny: true` *means* "there is no silent `any` left in the codebase" — it's the line that certifies the migration's core is done. *(Alternative framing: the handbook suggests turning `noImplicitAny` on early **if** the team will annotate aggressively from day one. On a checkJs/JSDoc-first migration, milestone-not-gate is the calmer path.)*
4. **`any` → `unknown` cleanup.** The provisional `any`s you and `ts-migrate` scattered are unsafe (they disable checking and propagate). Replace deliberate escape hatches with `unknown`, which forces a narrowing check at the use site before the value is touched. Track the count of remaining `any` (grep, or `typescript-eslint`'s `no-explicit-any`) and drive it down.
5. **High-value standalone checks last** (optional): `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride` — only when the team will pay the friction.

**Per-directory `tsconfig` overrides** let different parts of the tree sit at different strictness during the ramp. A migrated subtree can be strict while the rest stays loose:

```jsonc
// src/payments/tsconfig.json  — this subtree is fully migrated, hold it to a higher bar
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true
  },
  "include": ["./**/*"]
}
```

This **ratchets**: once a directory is strict, new code there can't regress. (Project references / `tsc -b` wiring for multi-config builds → `typescript-project-references-monorepo`.)

### Suppressions as tracked debt: `@ts-expect-error` vs `@ts-ignore`

Both silence the error on the next line. The difference is what happens when the underlying error goes away:

- **`// @ts-expect-error` (TS 3.9+) — prefer this.** If the next line has **no** error, TypeScript reports *"Unused '@ts-expect-error' directive."* It **self-removes**: once you fix the real problem, the suppression becomes a build error and forces its own deletion. This makes debt **self-cleaning** and countable.
- **`// @ts-ignore` — silent.** Does nothing when the line is error-free, so it rots — stays in the code long after the error it hid is gone.

**Burn-down practice:** standardize on `@ts-expect-error` with a reason comment (`// @ts-expect-error TODO(#1234): widen Config type`); ban `@ts-ignore` via `typescript-eslint` `ban-ts-comment` (`{ "ts-ignore": true, "ts-expect-error": "allow-with-description" }`). Track the count over time (`grep -rc "@ts-expect-error" src | ...`) as a burn-down metric — a migration is "done" when both the `@ts-expect-error` count and the `any` count trend to zero. (Typed-lint rules to enforce this → `typescript-eslint-typed-linting`.)

## Tools / Frameworks

- **`ts-migrate`** (Airbnb) — automates the bulk conversion. `npx -p ts-migrate -c "ts-migrate-full <folder>"` runs the whole pipeline (and git-commits after each major step). Or run the stages individually: `npx ts-migrate -- init <folder>` (scaffold `tsconfig.json`), `... rename <folder>` (`.js`/`.jsx`→`.ts`/`.tsx`), `... migrate <folder>` (codemods that fix what they can), `... reignore <folder>` (re-apply suppressions). Scope with `--sources "path/**/*"`. **Set expectations:** per its own README the output *"will pass the build, but a followup is required to improve type safety. There will be lots of `// @ts-expect-error`, and `any` that will need to be fixed over time."* So `ts-migrate` gets you to *compiling* fast; phase 4 (strictness ramp + debt burn-down) is the real work it leaves behind. Best on large, uniform codebases; for a small one, manual leaf-first is often cleaner.
- **`tsc --noEmit`** — the **type gate** for CI while a bundler/swc/`tsx`/Node strip-types does the actual build. This is what keeps the migration from blocking shipping.
- **`@types/*`** — install community declarations for untyped deps: `npm i -D @types/lodash`. First stop when "Could not find a declaration file for module 'x'."
- **`declare module` quick stub** — when no `@types` exists, unblock with a one-liner so the import type-checks as `any` instead of erroring:

  ```ts
  // src/types/shims.d.ts
  declare module "untyped-legacy-pkg";          // whole module → any
  declare module "csv-parse/sync" {             // or a minimal real shape
    export function parse(input: string, opts?: unknown): unknown[];
  }
  ```

  This is **migration survival**, not declaration authoring — keep stubs minimal and replace with real `@types` when available. Proper `.d.ts` authoring, `declare global`, and module augmentation depth → `typescript-declaration-files`.
- **arethetypeswrong (`@arethetypeswrong/cli`)** — if you *publish* a package, run `npx @arethetypeswrong/cli` against your packed tarball/published package to catch shipped-types problems (masquerading CJS/ESM, missing types, `export`-map/resolution failures across `node10`/`node16`/`bundler`). Relevant once your migrated library's `.d.ts` output goes out the door.
- **Editor "infer from usage" quick-fixes** — TS language-service codemods (VS Code lightbulb) that infer parameter/return types from call sites and add JSDoc or TS annotations. Cheap way to knock out implicit-`any` errors after a rename.
- **`typescript-eslint`** — enforce the burn-down: `no-explicit-any`, `ban-ts-comment` (force descriptions, ban `@ts-ignore`). Setup → `typescript-eslint-typed-linting`.

## Methodology

1. **Add `tsconfig.json` with `allowJs: true`, `noEmit: true`, `strict: false`, `noImplicitAny: false`** — and on TS 6.0 write `"strict": false` *explicitly*. Pin `target`/`module`/`lib`. Wire `tsc --noEmit` into CI as **non-blocking** first (report, don't fail).
2. **Turn on checking gradually** — `// @ts-check` on a handful of leaf files (or `checkJs: true` if the tree is small). Fix what surfaces.
3. **Annotate with JSDoc** the modules you check, designing the type surface in place. When a file needs types JSDoc can't express, mark it for rename.
4. **Rename leaf-first** in PR-sized batches, drawing a few entry-level interface files early. Keep each batch green (or adding only tracked `@ts-expect-error`s).
5. **Make `tsc --noEmit` blocking in CI** once the tree compiles.
6. **Ramp strictness one flag at a time:** `strictNullChecks` → rest of `strict` family → `any`→`unknown` → **`noImplicitAny: true` (milestone)** → optional standalone checks. Use per-directory overrides to ratchet finished subtrees.
7. **Burn down debt:** track `@ts-expect-error` and `any` counts to zero; replace `declare module` stubs with real `@types`.
8. **Run `attw`** before publishing if it's a library.

## Practical Patterns

**CI: type gate that doesn't block the build (early), then does (later).**

```yaml
# .github/workflows/ci.yml (excerpt)
jobs:
  build:
    steps:
      - run: npm ci
      - run: npm run build          # bundler / swc / tsx — the real artifact
  typecheck:
    continue-on-error: true         # PHASE 1-3: report, don't block. Flip to false once green.
    steps:
      - run: npm ci
      - run: npx tsc --noEmit       # the type gate
```

**Tracking the debt (drop in a script or CI step):**

```bash
echo "any:          $(grep -rIn --include=*.ts -e ': any' -e '<any>' src | wc -l)"
echo "ts-expect:    $(grep -rIn --include=*.ts '@ts-expect-error' src | wc -l)"
echo "ts-ignore:    $(grep -rIn --include=*.ts '@ts-ignore' src | wc -l)   # target: 0"
echo "remaining js: $(find src -name '*.js' | wc -l)"
```

**One file mid-migration, JSDoc → soon-to-be-`.ts`:**

```js
// @ts-check
/** @typedef {import("./types.js").Invoice} Invoice */

/**
 * @param {Invoice} inv
 * @returns {number}
 */
export function total(inv) {
  // @ts-expect-error TODO(#88): lineItems untyped until billing/ is migrated
  return inv.lineItems.reduce((s, li) => s + li.amount, 0);
}
```

## Anti-Patterns

- **`strict: true` (or all flags) in one commit.** Dumps every error category across the whole codebase simultaneously — unreviewable, demoralizing, and it stalls the migration. Ramp one flag at a time. On **TS 6.0 this is the *default*** unless you write `"strict": false` — the single most common 6.0 migration faceplant.
- **Reaching for `any` as the migration tool.** `any` disables checking *and* spreads through every value it touches, silently defeating the migration. Use `unknown` for genuine escape hatches (forces narrowing), and treat each `any` as debt to remove.
- **Mass `@ts-ignore`.** Silent and permanent — it rots in place long after the error is gone. Use `@ts-expect-error` (self-removing) with a reason, and ban `@ts-ignore` in lint.
- **Flipping `noImplicitAny: true` too early.** Before the JS is annotated/renamed, every untyped parameter erupts at once. It's the *milestone* that certifies "no silent any," not the opening move.
- **Blocking CI on `tsc` before the tree compiles.** Halts shipping during a multi-week migration. Keep `tsc --noEmit` non-blocking until the codebase is green, then make it required.
- **Annotating a generics/operator-heavy file in JSDoc instead of renaming it.** JSDoc can't express conditional/mapped/`infer` types; you'll waste hours. Rename to `.ts` and write real syntax.
- **Treating `ts-migrate` output as "done."** It produces *compiling* code studded with `any` and `@ts-expect-error` — that's the starting line for phase 4, not the finish.
- **Letting per-directory strict subtrees regress.** Once a directory is strict, keep it strict (ratchet) — don't relax it to land a quick change.
- **Relying on TS 6.0 default flips.** Pin `strict`/`target`/`module`/`lib` so 5.x and 6.0 toolchains produce identical results.

## Troubleshooting

- **First `tsc` run on TS 6.0 shows thousands of strict errors** → `strict` now defaults `true`; set `"strict": false` explicitly to restart the loose-baseline migration.
- **"Could not find a declaration file for module 'x'"** → `npm i -D @types/x`; if none exists, add `declare module "x";` to a `.d.ts` shim (→ `typescript-declaration-files` for real authoring).
- **A `.js` file isn't being checked despite `checkJs`/`@ts-check`** → confirm `allowJs: true`, the file is inside `include`, and there's no `// @ts-nocheck` at the top.
- **JSDoc `?Type` (nullable) seems ignored** → it only takes effect under `strictNullChecks`; `!Type` (non-nullable) is always ignored.
- **"Unused '@ts-expect-error' directive."** → the underlying error is fixed; delete the directive. This is the feature working — debt self-cleaning. (`@ts-ignore` would have rotted silently.)
- **Renaming a file to `.ts` produced a flood of errors** → expected; `.ts` is always fully checked. Convert leaf-first so dependencies are typed before their importers, and land small batches.
- **`paths`/alias imports resolve in the editor but fail at build** → `tsc` doesn't rewrite `paths`; this is a resolution concern, not a migration one → `typescript-compiler-config`.
- **CI build is fine but `tsc --noEmit` fails (or vice-versa)** → they're separate steps by design (bundler builds, `tsc` checks). Keep `tsc` non-blocking until the migration is green, then make it required.
- **`ts-migrate` left the project compiling but full of `any`/`@ts-expect-error`** → by design; proceed to the strictness ramp and debt burn-down.

## References

- TypeScript Handbook — Migrating from JavaScript (note: predates the checkJs/JSDoc-first workflow): https://www.typescriptlang.org/docs/handbook/migrating-from-javascript.html
- TypeScript Handbook — Type Checking JavaScript Files (`checkJs`, `// @ts-check`, `// @ts-nocheck`): https://www.typescriptlang.org/docs/handbook/type-checking-javascript-files.html
- TypeScript Handbook — JSDoc Reference (supported tags + limits): https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html
- TypeScript 3.9 release notes (`@ts-expect-error`): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-9.html
- TypeScript 6.0 release notes (`strict`/`module`/`target`/`types` default flips; `esModuleInterop` undisablable): https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html
- `ts-migrate` (Airbnb): https://github.com/airbnb/ts-migrate
- Are the Types Wrong? (`@arethetypeswrong/cli`): https://github.com/arethetypeswrong/arethetypeswrong.github.io
- TSConfig Reference (full flag semantics — deferred to `typescript-compiler-config`): https://www.typescriptlang.org/tsconfig/
