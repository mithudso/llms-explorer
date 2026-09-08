---
title: "Node.js Native TypeScript, Permission Model & Single Executable Applications"
description: "PROVENANCE: Authored by /dr (deep-research-and-build) on 2026-05-31."
---

<!--
PROVENANCE: Authored by /dr (deep-research-and-build) on 2026-05-31.
HUB: programming-languages (reference spoke). NOT a standalone top-level skill.
SCOPE: Node.js-native TypeScript execution (type stripping, --experimental-transform-types
history, erasableSyntaxOnly), the tsx and ts-node third-party runners and when each is still
needed, the Node 24.x stable Permission Model (--permission / --allow-*), and Single Executable
Applications (sea-config, --build-sea, postject, node:sea). Cross-references the sibling
references javascript-nodejs.md (Node runtime APIs), typescript-expert.md (tsconfig/type system),
and javascript-runtimes-deno-bun-edge.md (Deno/Bun secure-by-default perms parallel) — this file
assumes that foundation and focuses on the Node-24/25/26 toolchain + runtime-feature layer.
SOURCES: Node.js official docs — Modules: TypeScript (nodejs.org/api/typescript.html),
Permissions (nodejs.org/docs/latest-v24.x/api/permissions.html), Single executable applications
(nodejs.org/api/single-executable-applications.html), Running TypeScript Natively learn guide
(nodejs.org/learn/typescript/run-natively); Joyee Cheung core-maintainer blog on moving SEA build
into core (joyeecheung.github.io, 2026-01-26); DEV "Node.js 24 Ships Native TypeScript";
Better Stack "tsx vs ts-node"; tsx docs (npmjs.com/package/tsx); nodejs/typescript roadmap issue #24.
-->

# Node.js Native TypeScript, tsx/ts-node, the 24.x Permission Model & Single Executable Applications

A `programming-languages` hub reference for the **Node.js 24/25/26 LTS toolchain + runtime-security
feature layer**: running `.ts` files with no build step, the third-party runners that fill the gaps,
locking a process down with the Permission Model, and shipping a single self-contained binary. For
generic TypeScript type-system / tsconfig work defer to `typescript-expert.md` and
`typescript-advanced-types.md`; for Node runtime APIs and the event loop defer to `javascript-nodejs.md`
and `nodejs-concurrency-internals.md`; the Deno/Bun secure-by-default permission model is the parallel
covered in `javascript-runtimes-deno-bun-edge.md`.

## Overview

Node.js 24 (the 2025 "Krypton" LTS line) turned three previously experimental capabilities into
default-or-stable features: it **runs TypeScript directly** by stripping types, ships a **stable
Permission Model** for restricting what a process can touch, and supports **Single Executable
Applications (SEA)** for distributing a CLI as one binary. These features share one premise — reduce
the toolchain around a Node app: fewer build steps (type stripping), fewer ambient privileges
(permissions), fewer install prerequisites (SEA). They do **not** replace a type checker, a bundler,
or OS-level sandboxing; each has a sharp, documented boundary.

**Version anchors (memorize these — they drive most "does my Node have X" questions):**

| Feature | Flag/since | Stable/default |
| --- | --- | --- |
| Type stripping behind flag | `--experimental-strip-types` (v22.6.0) | — |
| Type stripping **on by default** | v23.6.0 / v22.18.0 | default for `.ts` |
| Type stripping **stable** | v25.2.0 / v24.12.0 | stable |
| `--experimental-transform-types` (enum/namespace via codegen) | added v22.7.0 | **removed in v26.0.0** |
| Permission Model | `--experimental-permission` (v20.0.0) | `--permission` stable in v24.x (no longer experimental since v23.5.0 / v22.13.0) |
| SEA two-step (config + postject) | `--experimental-sea-config` (v19.7.0+) | experimental |
| SEA single-step in core | `--build-sea` (v25.5.0) | experimental, may backport to LTS |

## Core Concepts

### 1. Native TypeScript via type stripping

Node executes `.ts` by **erasing** type syntax and running the remaining JavaScript — it does *not*
compile or downlevel. Erased syntax (type annotations, `interface`, `type`, `import type`, type-only
`namespace`) is replaced **in place with whitespace**, so line/column numbers are preserved and no
source map is needed.

- **No type checking happens.** Type errors silently pass at runtime. Run `tsc --noEmit` separately
  in CI/editor for safety. This is the single most important caveat.
- **Unsupported (throws `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`):** `enum`, parameter properties
  (`constructor(private x: number)`), runtime `namespace` (with executable code), and (legacy
  TS) `import =`/`export =` aliases — these all require *emitting* JS, not just erasing.
- **Decorators / JSX:** `.tsx` is **not** supported by type stripping; legacy experimental decorators
  need a transform. Use a runner (tsx) or a real compile step.
- **Extensions:** `.ts` (module type from nearest `package.json` `"type"`), `.mts` (always ESM),
  `.cts` (always CJS). Relative imports **must carry the extension** (`import './x.ts'`) — there is no
  extensionless resolution. `node_modules` `.ts` files are refused (libraries must ship `.js`+`.d.ts`).
- **`--experimental-transform-types`** historically *emitted* the unsupported constructs (enums etc.)
  and enabled source maps — but it was **removed in v26.0.0**. On v26+, code using enums/namespaces
  must move to erasable patterns or use an external tool.
- **`--no-strip-types`** disables the behavior (e.g. to force a loader to handle `.ts`).

Recommended `tsconfig.json` for the native path (TS 5.8+):

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

`erasableSyntaxOnly` is the key alignment knob: it makes `tsc` reject exactly what Node refuses, so
the editor catches the mismatch instead of a runtime crash. `tsconfig` `paths` are **not** honored by
the runtime — use Node subpath imports (`#alias` in `package.json` `imports`) instead.

### 2. tsx and ts-node — when native stripping is not enough

Native stripping covers dev scripts and simple services; the third-party runners remain necessary for
the constructs Node refuses or for full type checking.

- **tsx** — esbuild-powered runner. Transpiles (does **not** type-check, like `ts-node --swc`),
  supports enums, decorators, JSX/`.tsx`, `tsconfig` `paths`, CJS+ESM transparently, and has a fast
  integrated watch mode. Invoke as `tsx file.ts`, `tsx watch file.ts`, or as a loader:
  `node --import tsx file.ts`. Best default for "I want it to just run everything."
- **ts-node** — uses the real `tsc` (or `--swc`). Its draw is **type checking during execution** and
  full language fidelity; its pain is fiddly ESM setup and slower starts. Use `ts-node --esm` for ESM.
- **Decision rule:** dev script / simple service with erasable code → **native** `node file.ts`
  (zero deps). Need enums/decorators/JSX/path-aliases but not runtime type-checking → **tsx**. Want
  type errors to *halt* execution → **ts-node** (or just gate with `tsc --noEmit` in CI and use native).
- **Production:** none of these replace a real build. For shipping, still run `tsc`/`esbuild`/a
  bundler with optimization, tree-shaking, and minification.

### 3. The Permission Model (stable in 24.x)

`node --permission app.js` denies, by default, access to: the filesystem (`fs`), child processes,
worker threads, native addons, WASI, and the inspector. It is a **trusted-code seatbelt** (prevent a
dependency from *unintentionally* reaching resources), **not** a sandbox against malicious code.

Grant flags (each can repeat; comma lists also work):

| Flag | Grants |
| --- | --- |
| `--allow-fs-read=<path\|*>` | filesystem read |
| `--allow-fs-write=<path\|*>` | filesystem write |
| `--allow-child-process` | `child_process` spawn/exec/fork |
| `--allow-worker` | `worker_threads` |
| `--allow-addons` | native N-API addons |
| `--allow-wasi` | WASI |
| `--allow-inspector` | inspector / debugging |

Path syntax: `*` = all; absolute or CWD-relative paths; a trailing `/` on an existing directory auto-
adds `/*`; `*` mid/end is a wildcard (`/home/test*`). The entrypoint (and `-r` preloads) are
auto-added to `--allow-fs-read`. Declarable in `node.config.json` under a `"permission"` object and
loaded with `--experimental-default-config-file`.

Runtime API: `process.permission.has('fs.write')` and `process.permission.has('fs.read', '/path')`
return booleans. Denials throw `Error … code: 'ERR_ACCESS_DENIED', permission: 'FileSystemRead', …`.

**Documented limitations (cite these — they are common gotchas):** permissions **do not inherit to
worker threads** (grant per-worker); **symlinks are followed** even to unauthorized targets (traversal
bypass); pre-init flags (`--env-file`, `--openssl-config`) run before the model initializes; existing
**file descriptors via `node:fs` bypass** the model; `sqlite` loadable extensions and OpenSSL engines
can't be requested at runtime; `process._debugProcess()` is not gated.

### 4. Single Executable Applications (SEA)

Distribute a Node app as one binary to machines without Node installed, by injecting a blob into a copy
of the `node` binary. **CommonJS or ESM** main, single entrypoint per app.

`sea-config.json` fields: `main`, `mainFormat` (`"commonjs"` default | `"module"`), `output`,
`disableExperimentalSEAWarning`, `useSnapshot`, `useCodeCache`, `execArgv` + `execArgvExtension`
(`"none"`|`"env"`|`"cli"`), and `assets` (key→path map).

**New single-step build (v25.5.0+, recommended):**

```bash
node --build-sea sea-config.json   # generates blob AND injects it; no postject, no LIEF knowledge
```

`--build-sea` ported postject's injection logic into core (`src/node_sea_bin.cc`, statically links
LIEF, ~5 MB binary growth). Joyee Cheung landed it in v25.5.0; may backport to LTS.

**Legacy two-step (still valid, needed where `--build-sea` isn't available):**

```bash
node --experimental-sea-config sea-config.json           # writes sea-prep.blob
cp $(command -v node) myapp                               # copy the runtime
codesign --remove-signature myapp                         # macOS/Windows: strip sig first
npx postject myapp NODE_SEA_BLOB sea-prep.blob \
  --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2 \
  [--macho-segment-name NODE_SEA]                          # macOS only
codesign --sign - myapp                                   # macOS: re-sign (required to run)
```

Blob placement is format-specific: PE resource (Windows), Mach-O `NODE_SEA_BLOB` section in segment
`NODE_SEA` (macOS), ELF note (Linux). The fuse sentinel marks the binary as carrying a blob.

**`node:sea` API** (call from inside the app): `isSea()`, `getAsset(key[, encoding])`,
`getAssetAsBlob(key)`, `getRawAsset(key)` (no-copy reference), `getAssetKeys()`. Inside a SEA,
`__filename`/`module.filename` equal `process.execPath` and `__dirname` is its directory; use
`module.createRequire()` to load files off disk (built-ins always work).

## Tools / Frameworks

- **Node 24+ runtime** — `node file.ts` (strip), `--permission` + `--allow-*`, `--build-sea`.
- **tsx** — `tsx file.ts`, `tsx watch`, `node --import tsx file.ts` (transpile-only, full TS feature set).
- **ts-node** — `ts-node`, `ts-node --esm`, `ts-node --swc` (type-checking runner).
- **tsc** — `tsc --noEmit` for the type-check gate that native stripping omits; full build for prod.
- **postject** — `npx postject` blob injection (legacy SEA path / pre-25.5 runtimes).
- **codesign / signtool** — macOS/Windows binary (re)signing around postject.

## Methodology

1. **Pick the run path.** Erasable code + dev → native `node`. Enums/decorators/JSX/aliases → tsx.
   Need runtime type enforcement → ts-node. Always pair native/tsx with a separate `tsc --noEmit`.
2. **Align tsconfig** with `erasableSyntaxOnly` + `verbatimModuleSyntax` so the editor mirrors Node.
3. **Lock down** long-running or third-party-heavy processes with `--permission` and the minimal
   `--allow-*` set; verify at runtime via `process.permission.has(...)`; remember workers need their own.
4. **Ship a binary** with `node --build-sea sea-config.json` on v25.5+, else the config+postject+codesign
   chain. Disable `useCodeCache`/`useSnapshot` for cross-platform reproducibility.

## Practical Patterns

- **Zero-build CLI:** ship `.ts` directly; `node bin.ts`; gate types with `tsc --noEmit` in CI.
- **Subpath aliases without a bundler:** `package.json` `"imports": { "#db/*": "./src/db/*.ts" }` — Node
  honors these where it ignores `tsconfig` `paths`.
- **Least-privilege service:** `node --permission --allow-fs-read=./config --allow-net app.js` (network
  is open unless a build gates it; today fs/child/worker/addon/wasi/inspector are the gated axes).
- **Asset-bundled SEA:** put templates/migrations in `assets`, read with `sea.getAsset('schema.sql','utf8')`.

## Anti-Patterns

- Treating native stripping as a type checker — it never validates types; CI must run `tsc`.
- Writing `enum`/`namespace`/parameter-properties expecting native to run them (use `const` objects,
  union types, plain assignment, or switch to tsx).
- Relying on `--experimental-transform-types` going forward — **removed in v26**.
- Importing without extensions under native execution — resolution will fail.
- Assuming `--permission` sandboxes malicious code or inherits to workers/symlink targets — it does not.
- Combining `useSnapshot: true` with `mainFormat: "module"`, or `import()` with `useCodeCache: true` — unsupported.

## Troubleshooting

- `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` → erase the offending construct or run via tsx.
- `Cannot find module './x'` under native TS → add the explicit `.ts` extension.
- A `.ts` dependency under `node_modules` won't run → libraries must publish compiled `.js` + `.d.ts`.
- `ERR_ACCESS_DENIED` with `permission: 'FileSystemRead'` → add `--allow-fs-read=<path>`; check the
  worker is granted separately.
- SEA "is experimental" warning → set `disableExperimentalSEAWarning: true` in the config.
- SEA binary won't launch on macOS → you must `codesign --sign -` after injection.

## References

- Node.js Docs — Modules: TypeScript: https://nodejs.org/api/typescript.html
- Node.js Learn — Running TypeScript Natively: https://nodejs.org/learn/typescript/run-natively
- Node.js Docs — Permissions (v24.x): https://nodejs.org/docs/latest-v24.x/api/permissions.html
- Node.js Docs — Single executable applications: https://nodejs.org/api/single-executable-applications.html
- Joyee Cheung — Improving SEA Building for Node.js (--build-sea, 2026-01-26): https://joyeecheung.github.io/blog/2026/01/26/improving-single-executable-application-building-for-node-js/
- DEV — Node.js 24 Ships Native TypeScript: https://dev.to/benriemer/nodejs-24-ships-native-typescript-the-end-of-build-steps-440f
- Better Stack — tsx vs ts-node: https://betterstack.com/community/guides/scaling-nodejs/tsx-vs-ts-node/
- tsx (npm): https://www.npmjs.com/package/tsx
- nodejs/typescript — Roadmap to stable strip-types (issue #24): https://github.com/nodejs/typescript/issues/24
