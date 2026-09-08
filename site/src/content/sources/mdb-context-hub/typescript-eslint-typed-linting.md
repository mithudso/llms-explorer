---
title: "TypeScript ESLint Typed Linting"
description: "A lang-js-ts reference for linting TypeScript with typescript-eslint v8: stand up an"
---

# typescript-eslint & Type-Aware Linting — flat config, `projectService`, typed rules

A `lang-js-ts` reference for **linting TypeScript with `typescript-eslint` v8**: stand up an
`eslint.config.js` flat config, turn on *type-aware* (typed) linting via
`parserOptions.projectService`, pick the right shared config, and know which high-value rules need
type information versus which are purely syntactic. The goal: a correct, version-appropriate ESLint
setup the first time, with the typed-linting performance cost understood and scoped. Defer the
TypeScript compiler API / `parserServices` internals, general bundler/linter *choice*, `tsconfig`
strictness, and non-TS ESLint config to the siblings listed below.

## Overview

`typescript-eslint` is the toolkit that lets ESLint understand TypeScript. Two packages do the work,
both re-exported from the umbrella **`typescript-eslint`** package:

- **`@typescript-eslint/parser`** — replaces ESLint's default (Espree) parser so ESLint can read TS
  syntax (types, generics, decorators) into an AST.
- **`@typescript-eslint/eslint-plugin`** — the rules themselves (~100+), including the typed rules.

**Linting is not type-checking.** ESLint + typescript-eslint finds *bad practices and likely bugs*
(floating promises, unsafe `any`, dead conditions). It does **not** replace `tsc`: you still run
`tsc --noEmit` as the type gate. The two are complementary — `tsc` proves the program type-checks;
typed linting enforces opinions the compiler doesn't (e.g. "you ignored this promise").

**Version anchor (memorize — these drive "is this available / how do I configure it" questions):**

| Thing | State (as of 2026) | Note |
| --- | --- | --- |
| **typescript-eslint** | **v8** (8.x) | Conventions below are stable across all of 8.x. |
| Flat config (`eslint.config.js`) | **ESLint 9 default** | Legacy `.eslintrc` is end-of-life; v8 docs are flat-config-first. |
| `parserOptions.projectService: true` | **current recommendation** | Promoted from `EXPERIMENTAL_useProjectService` → stable `projectService` in **v8.0**. |
| `parserOptions.project` | older alternative | Still works; `projectService` is easier and usually faster. |
| `tseslint.config()` helper | stable | Spreads configs positionally. |
| `defineConfig` from `eslint/config` | newer | What the current Getting Started uses; takes `extends:` arrays. |
| Biome 2.0 typed rules / oxlint + `tsgolint` | type-aware *gap closing* (2025+) | Rust/Go linters reached ~partial typed coverage; typescript-eslint still the reference. |

> **Flat config only.** This reference uses `eslint.config.js`/`.mjs`. If you're on a legacy
> `.eslintrc`, migrate first — ESLint 9 made flat config the default and v8 of typescript-eslint
> documents it exclusively.

## Core Concepts

### The two config helpers (and the one thing that breaks copy-paste)

typescript-eslint ships shared configs as **arrays of flat-config objects**. How you splice them in
depends on which helper you use, and the spread (`...`) is **load-bearing**:

- **`tseslint.config(...)`** — typescript-eslint's own helper. Takes config objects as positional
  arguments, so array-valued configs **must be spread**: `...tseslint.configs.recommendedTypeChecked`.
  Forgetting the spread passes an array where an object is expected → broken config.
- **`defineConfig(...)`** from `eslint/config` (ESLint 9.x) — the newer, framework-native helper.
  It flattens arrays for you, so you do **not** spread: pass `tseslint.configs.recommendedTypeChecked`
  directly, either positionally or inside an `extends: [...]` array.

Both are valid in v8. Lead with whichever your project already uses; the rules and `parserOptions`
are identical between them.

### Enabling type-aware (typed) linting

"Typed linting" means rules can call into the TypeScript type checker (`parserServices` /
`getTypeChecker()`) to reason about the *types* of expressions, not just their syntax. That's what
makes `no-floating-promises` (is this expression a `Promise`?) possible at all.

To turn it on you (1) extend a `*TypeChecked` config and (2) tell the parser how to find type info via
`parserOptions.projectService`:

```js
// eslint.config.mjs — typed linting with tseslint.config() (note the SPREAD on the array config)
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname, // __dirname in a CommonJS config
      },
    },
  },
);
```

The same setup with the newer `defineConfig` helper (no spread; `extends:` arrays):

```js
// eslint.config.mjs — typed linting with defineConfig (NO spread; arrays flatten)
import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';

export default defineConfig({
  files: ['**/*.{js,ts,mts,cts}'],
  extends: [js.configs.recommended, tseslint.configs.recommendedTypeChecked],
  languageOptions: {
    parserOptions: {
      projectService: true,
      tsconfigRootDir: import.meta.dirname,
    },
  },
});
```

**`tsconfigRootDir`** anchors relative tsconfig lookups to the config file's directory. Pair
`projectService: true` with `tsconfigRootDir: import.meta.dirname` (ESM) or `__dirname` (CJS) — omit
it and the parser resolves tsconfigs relative to the CWD, a real "works on my machine" footgun.

### `projectService` vs `project` (and the `EXPERIMENTAL_` history)

| Option | What it is |
| --- | --- |
| **`projectService: true`** | The **modern, recommended** way (v8). Internally uses the same TypeScript **Project Service** APIs that editors like VS Code use to build Programs — so lint types match editor types. Auto-discovers the nearest `tsconfig.json` per file. Generally easier to configure and faster at scale than `project`. |
| `project: true` / `project: ['./tsconfig.json', …]` | The **older** mechanism. typescript-eslint creates Programs itself from the tsconfig path(s) you list. Works, but more config (often a dedicated `tsconfig.eslint.json`) and historically slower / memory-heavy on big monorepos. |
| `EXPERIMENTAL_useProjectService` | The **pre-v8 name** for the project service. In v8 it was promoted to stable `projectService`; rename it if you see it in an old config. |

For files **outside** any tsconfig (root config files, scripts), `projectService` takes an options
object instead of `true`:

```js
parserOptions: {
  projectService: {
    allowDefaultProject: ['*.js', '*.config.js'], // lint these out-of-project files WITH types
    defaultProject: 'tsconfig.json',
  },
  tsconfigRootDir: import.meta.dirname,
},
```

`allowDefaultProject` is a glob of out-of-project files to lint with type information — no extra
tsconfig or compiler options needed. (Mechanics of `parserServices`/the checker API itself →
`typescript-compiler-api`.)

### Shared configs (which require type info)

Extend a preset rather than enabling rules one by one. The **`*TypeChecked`** variants require typed
linting (`projectService`/`project`); the plain ones do not.

| Config | Type info? | What it is |
| --- | --- | --- |
| `recommended` | No | Almost-always-a-bug rules. Disables conflicting core ESLint rules. The baseline. |
| `recommendedTypeChecked` | **Yes** | `recommended` **plus** type-aware correctness rules. The default for typed projects. |
| `strict` | No | `recommended` + more opinionated bug-catchers. Not semver-stable (rules added in minors). |
| `strictTypeChecked` | **Yes** | `strict` + `recommendedTypeChecked` + extra typed rules. Most thorough; noisiest. |
| `stylistic` | No | Best-practice consistency rules (formatting-adjacent, not formatting). |
| `stylisticTypeChecked` | **Yes** | `stylistic` + typed stylistic rules (e.g. `consistent-type-exports`). |
| `*TypeCheckedOnly` (`recommendedTypeCheckedOnly`, …) | **Yes** | **Only** the typed rules from that tier — pair with the non-typed base if you compose manually. `recommended` + `recommendedTypeCheckedOnly` ≡ `recommendedTypeChecked`. |
| `disableTypeChecked` | n/a | Turns **off** all type-aware rules for a set of files (see Performance). |
| `eslintRecommended` | No | Just the "disable core rules TS already covers" slice; auto-included by the `recommended*` configs. |
| `all` | mixed | Every rule on. **Don't** use it — many rules conflict; not semver-stable. |
| `base` | n/a | Bare parser/plugin wiring; auto-included, not for direct use. |

**Picking:** no type info → `recommended` (+ `stylistic`). Type info → `recommendedTypeChecked`
(+ `stylisticTypeChecked`). Reach for `strict*` only if a real share of the team is highly
TS-proficient and will tolerate the friction.

### High-value typed rules (and the one syntactic exception)

These are the rules that *justify* paying the typed-linting cost. All but the last **require type
information**:

| Rule | Type info? | Catches |
| --- | --- | --- |
| `no-floating-promises` | **Yes** | A `Promise` whose result is never awaited/handled (silent unhandled rejection). The flagship typed rule. |
| `no-misused-promises` | **Yes** | Passing an `async`/promise-returning fn where a `void`/boolean is expected (e.g. `if (asyncFn())`, a promise in a `forEach`). |
| `await-thenable` | **Yes** | `await` on a non-thenable (a no-op `await`), or detecting a missing one. |
| `no-unsafe-assignment` / `-call` / `-member-access` / `-argument` / `-return` | **Yes** | The `any` firewall: assigning/calling/reading/passing/returning an `any`-typed value, which silently defeats the type system. |
| `restrict-template-expressions` | **Yes** | Interpolating a non-string-safe value (object → `[object Object]`, `any`, nullable) into a template literal. |
| `no-unnecessary-condition` | **Yes** | A condition that's always truthy/falsy given its type (dead branch, redundant `?.`). |
| `strict-boolean-expressions` | **Yes** | Non-boolean values used in a boolean position without an explicit check (nullable strings/numbers in `if`). Opinionated. |
| `require-await` | **Yes** | An `async` function with no `await` inside (probably shouldn't be async). |
| `switch-exhaustiveness-check` | **Yes** | A `switch` over a union/enum that misses a member — the exhaustiveness guard for discriminated unions. |
| **`consistent-type-imports`** | **No** | **Syntactic, not typed.** Enforces `import type { T }` for type-only imports. Needs no `projectService`. |

`consistent-type-imports` is the exception worth calling out: it's purely about *import syntax*, so it
runs without type info. It pairs with TypeScript's `verbatimModuleSyntax` / `isolatedModules` to make
type-only imports explicit and prevent a single-file transpiler from emitting a broken value import.
(The tsconfig flags themselves → `typescript-compiler-config`.)

### Turning off ESLint rules that conflict with TypeScript

Several core ESLint rules are wrong or redundant under TypeScript — the compiler already covers them,
or they false-positive on TS syntax. The classic is **`no-undef`**: TS already errors on undefined
identifiers, and `no-undef` flags valid TS (global types, ambient declarations). **You don't disable
these by hand** — `typescript-eslint`'s `recommended*` configs include `eslintRecommended`, which
turns off the core rules TS subsumes (`no-undef`, `no-dupe-class-members`, `no-redeclare`, etc.).
Likewise, prefer the typescript-eslint *extension rules* (e.g. `@typescript-eslint/no-unused-vars`,
`@typescript-eslint/no-shadow`) over the core versions, and disable the core one when you enable the
TS variant.

## Tools / Frameworks

- **`typescript-eslint` (umbrella package)** — install `eslint typescript typescript-eslint` (plus
  `@eslint/js` for `js.configs.recommended`). Exposes `tseslint.config`, `tseslint.parser`,
  `tseslint.plugin`, and `tseslint.configs.*`.
- **`@eslint/js`** — provides ESLint's own `js.configs.recommended` base.
- **`defineConfig` / `eslint/config`** (ESLint 9) — the framework-native flat-config helper; the
  alternative to `tseslint.config()`.
- **`tsgolint`** — a Go-based engine running typescript-eslint's *typed* rules natively, used as the
  backend for **oxlint**'s type-aware preview. The fast-typed-linting frontier.
- **Biome / oxlint** — Rust-based all-in-one lint/format tools. Fast, but see Anti-Patterns for the
  typed-linting gap. *Choosing between them and ESLint is out of scope →
  `javascript-build-tooling-bundlers`.*

## Methodology

1. **Start from a preset, not hand-rolled rules.** Extend `recommended` (no types) or
   `recommendedTypeChecked` (types) and only add/override specific rules afterward.
2. **Decide if you want typed linting.** If yes, set `parserOptions.projectService: true` +
   `tsconfigRootDir: import.meta.dirname` and extend a `*TypeChecked` config. If you only want fast
   syntactic linting, stay on `recommended` and skip `projectService` entirely.
3. **Get the helper/spread right.** `tseslint.config(...)` → spread array configs
   (`...tseslint.configs.recommendedTypeChecked`). `defineConfig(...)` → no spread.
4. **Scope out non-TS files.** Add a `{ files: ['**/*.js'], extends: [tseslint.configs.disableTypeChecked] }`
   block so plain JS / config files don't trip typed rules (or error for lacking a Program).
5. **Enable the flagship typed rules deliberately** if the preset doesn't already: at minimum
   `no-floating-promises` and `no-misused-promises` — they catch real production bugs.
6. **Keep `tsc --noEmit` in CI.** Lint and type-check are separate gates; run both.
7. **Verify** by running `eslint .` and confirming typed rules fire on a known floating promise.

## Practical Patterns

**Recommended typed setup (most TS projects), `tseslint.config()` form:**

```js
// eslint.config.mjs
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist/**', 'coverage/**'] }, // flat-config replacement for .eslintignore
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // tighten beyond the preset:
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
      '@typescript-eslint/consistent-type-imports': 'error', // syntactic; no type info needed
    },
  },
  {
    // typed rules can't run on plain JS — turn them off there
    files: ['**/*.js', '**/*.cjs', '**/*.mjs'],
    extends: [tseslint.configs.disableTypeChecked],
  },
);
```

**Multi-plugin config (Jest on tests), typed linting off on JS — `defineConfig` form:**

```js
// @ts-check
import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import jestPlugin from 'eslint-plugin-jest';
import tseslint from 'typescript-eslint';

export default defineConfig(
  { ignores: ['**/build/**', '**/dist/**'] },
  js.configs.recommended,
  {
    plugins: { '@typescript-eslint': tseslint.plugin, jest: jestPlugin },
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: { '@typescript-eslint/no-floating-promises': 'error' },
  },
  {
    files: ['**/*.js'],
    extends: [tseslint.configs.disableTypeChecked], // disable type-aware linting on JS files
  },
  {
    files: ['test/**'],
    extends: [jestPlugin.configs['flat/recommended']],
  },
);
```

**Linting out-of-project files (root config files) without a dedicated tsconfig:**

```js
parserOptions: {
  projectService: {
    allowDefaultProject: ['*.js', '*.config.*'],
    defaultProject: 'tsconfig.json',
  },
  tsconfigRootDir: import.meta.dirname,
},
```

**Migrating off the old `project` option:**

```js
parserOptions: {
  // project: true,            // ← remove (older mechanism)
  projectService: true,        // ← v8 recommendation: easier + usually faster
  tsconfigRootDir: import.meta.dirname,
},
```

## Anti-Patterns

- **Forgetting the spread under `tseslint.config()`.** `tseslint.configs.recommendedTypeChecked`
  (no `...`) passes an array where a config object is expected → silent misconfiguration or a crash.
  Spread it. (Under `defineConfig`, do the opposite: don't spread.)
- **Enabling `*TypeChecked` without `projectService`/`project`.** Typed rules need a Program; without
  one you get "parserOptions.project has been set … but … was not found" or the rules simply don't
  run. Set `projectService: true`.
- **Running typed rules over plain JS / config files.** They error (no Program) or noise.
  `disableTypeChecked` on a `**/*.js` block.
- **Omitting `tsconfigRootDir`.** Relative tsconfig resolution then depends on the CWD — flaky across
  editor vs CLI vs CI. Always set `import.meta.dirname` / `__dirname`.
- **Treating `eslint` as the type-checker.** Linting ≠ `tsc`. Typed linting catches *practices*, not
  type *errors*; you still run `tsc --noEmit`.
- **Hand-disabling `no-undef` and friends.** The `recommended*` configs already do this via
  `eslintRecommended`. Manually toggling core rules that conflict with TS just duplicates that.
- **Expecting Biome/oxlint to fully replace typed linting.** As of 2025–26, Biome 2.0 added type
  inference (~85% of typescript-eslint's typed coverage) and oxlint added a `tsgolint`-backed
  type-aware *preview* — but the flagship typed rules (`no-floating-promises`, the `no-unsafe-*`
  family) are exactly the guarantees a purely-syntactic Rust linter loses. If those rules matter,
  keep typescript-eslint. *(Picking a toolchain overall → `javascript-build-tooling-bundlers`.)*
- **Using the `all` config.** Many rules conflict; it's not semver-stable. Extend a `recommended*` or
  `strict*` preset instead.
- **`consistent-type-imports` "needs type info."** It doesn't — it's syntactic. Don't gate it behind
  `projectService`.

## Troubleshooting

- **"You have used a rule which requires type information, but … parserOptions … not set"** → you
  extended a `*TypeChecked` config without `projectService`/`project`. Add `projectService: true`.
- **"… was not found by the project service. Consider … allowDefaultProject"** → an out-of-project
  file (a root config) hit a typed rule. Add it to `allowDefaultProject`, or `disableTypeChecked` for
  that glob.
- **Lint is very slow / high memory** → typed linting builds the TS program. Levers: prefer
  `projectService` over `project`; narrow `files`; `disableTypeChecked` on non-source globs; run
  typed lint as its own CI step; ensure `tsconfig` `include` isn't pulling in the world.
- **Rules don't fire / config seems ignored** → flat config resolution. Confirm the file is
  `eslint.config.js`/`.mjs`, that you're on ESLint 9 (flat-config default), and (under
  `tseslint.config`) that array configs are spread.
- **`no-undef` flags valid TS (global types, ambient decls)** → you re-enabled it manually; the
  `recommended*` configs disable it on purpose. Remove the override.
- **`EXPERIMENTAL_useProjectService` errors / deprecation** → renamed to `projectService` in v8;
  update the key.
- **`import type` rule won't activate** → that's `consistent-type-imports`, which is syntactic; it
  needs no `projectService`. Make sure it's actually enabled in `rules`, not assumed via a preset.
- **Editor and CLI disagree on types** → divergent tsconfigs. `projectService` uses the editor's
  Project Service APIs, which helps; ensure both resolve the same `tsconfig.json` via
  `tsconfigRootDir`.

## References

- typescript-eslint — Getting Started (flat config quick start): https://typescript-eslint.io/getting-started/
- typescript-eslint — Typed Linting (`projectService`, `recommendedTypeChecked`): https://typescript-eslint.io/getting-started/typed-linting/
- typescript-eslint — Shared Configs (every preset, type-info matrix): https://typescript-eslint.io/users/configs/
- typescript-eslint — Rules (the 💭 "requires type information" marker): https://typescript-eslint.io/rules/
- typescript-eslint — `@typescript-eslint/parser` (`projectService`, `project`, `tsconfigRootDir`): https://typescript-eslint.io/packages/parser/
- typescript-eslint — "Typed Linting with Project Service" blog: https://typescript-eslint.io/blog/project-service/
- typescript-eslint — Announcing v8 (`EXPERIMENTAL_useProjectService` → `projectService`): https://typescript-eslint.io/blog/announcing-typescript-eslint-v8/
- ESLint — Configuration Files (flat config, `defineConfig`): https://eslint.org/docs/latest/use/configure/configuration-files
- Biome 2.0 — type inference / type-aware rules: https://biomejs.dev/blog/biome-v2-0-0/
- oxc — Oxlint Type-Aware Preview (`tsgolint`): https://oxc.rs/blog/2025-08-17-oxlint-type-aware
