---
title: "JavaScript Build Tooling and Bundlers"
description: "programming-languages hub reference for the JavaScript/TypeScript build toolchain: bundlers, parsers/transpilers, minifiers, linters, and formatters — and the 2025-2026 Rust/Go rewrite wave reshaping"
---

# JavaScript Build Tooling & Bundlers

programming-languages hub reference for the JavaScript/TypeScript **build toolchain**: bundlers, parsers/transpilers, minifiers, linters, and formatters — and the 2025-2026 **Rust/Go rewrite wave** reshaping all of them. Sibling to `javascript-nodejs` (language/runtime), `javascript-runtimes-deno-bun-edge` (non-Node runtimes), and `typescript-expert` (type system).

**TRIGGER:** choosing or migrating a bundler/build tool; Vite/Rolldown/VoidZero questions; Rspack↔webpack or Turbopack↔Next.js decisions; Oxc/oxlint/Biome vs ESLint/Prettier; "why is my build slow"; configuring tree-shaking, code-splitting, HMR, or source maps.
**SKIP:** Node/Deno/Bun *runtime* semantics → `javascript-runtimes-deno-bun-edge` / `javascript-nodejs`; TypeScript *type-system* → `typescript-expert`; package install / workspaces / monorepo task-orchestration → package-management (concept-tree gap, not yet built).

## The 2026 landscape: Rust is eating the toolchain

The fastest tool in every toolchain category is now written in **Rust or Go**. The pivotal driver is **VoidZero** (Evan You's company, founded late 2024) building a unified Rust toolchain under one parser.

- **Rolldown** — Rust bundler, drop-in replacement for *both* esbuild (dev) and Rollup (prod) inside Vite. Hit **1.0 Release Candidate in Jan 2026**; API stable, production-ready for early adopters.
- **Oxc** (Oxidation Compiler) — the Rust parser/transformer/resolver *underneath* Rolldown. **oxlint** is ~50-100× ESLint; Oxc formatting ~30× Prettier.
- **Vite 8** — runs on Rolldown by default, replacing the historical esbuild+Rollup two-engine split (which caused dev/prod output divergence bugs).

> Single-parser convergence (Oxc) under one bundler (Rolldown) inside one dev tool (Vite) is the structural story: it removes the class of bugs where dev (esbuild) and prod (Rollup) disagreed.

## Bundlers

| Tool | Lang | Niche | Pick it when |
|---|---|---|---|
| **Vite** (8, on Rolldown) | Rust core | Default app dev tool; framework-agnostic (Vue, React non-Next, Svelte, Solid…) | Greenfield apps; anything not locked to Next.js or webpack |
| **Rolldown** | Rust | The bundler inside Vite; Rollup-compatible plugin API | You need Rollup output semantics at Rust speed |
| **esbuild** | Go | Ultra-fast dev transforms; simple library bundling | Quick library builds, dev-server transforms, no complex code-splitting needs |
| **Rollup** | JS | Library bundling, cleanest ESM output, mature plugin ecosystem | Publishing a library where output quality > build speed |
| **Webpack** | JS | Legacy/enterprise; richest loader+plugin ecosystem; Module Federation | Existing webpack apps not worth migrating yet |
| **Rspack** | Rust | Tencent's webpack-API-compatible replacement | **Migrating** a webpack app — prioritizes webpack compat over peak speed |
| **Turbopack** | Rust | Vercel's bundler, tightly coupled to Next.js | You're a **Next.js** shop |
| **Parcel** | Rust (SWC) | Zero-config | Prototyping with no config tolerance |
| **Bun** (bundler) | Zig | All-in-one runtime + bundler | Already on the Bun runtime |

**Migration rule of thumb:** Rspack for webpack migrations (compat) · Turbopack for Next.js · **Vite for everything else**.

## Parsers / transpilers / minifiers

- **Oxc** — Rust parser/transformer/minifier/resolver; the new substrate.
- **SWC** — Rust; powers Next.js compilation and many transforms; Parcel's transformer.
- **esbuild** — Go; transpile + minify, extremely fast, the prior speed king.
- **Babel** — JS; still the most plugin-extensible transpiler (custom syntax, legacy targets), but slow — being displaced for plain transpilation.
- **tsc** — TypeScript's own compiler; use for **type-checking** (`--noEmit`), not bundling. The transpile-vs-typecheck split matters: bundlers strip types fast but don't type-check (see `javascript-nodejs` native-TS notes).
- **Terser** — JS minifier; legacy default, now outpaced by esbuild/Oxc minify.

## Linters & formatters

| Tool | Lang | Replaces | Note |
|---|---|---|---|
| **Biome** | Rust | ESLint **and** Prettier | One tool, ~25× faster; strong defaults; growing rule parity |
| **oxlint** | Rust | ESLint | ~50-100× ESLint; great as a fast pre-commit/CI gate alongside ESLint |
| **ESLint** (flat config) | JS | — | Still the ecosystem standard for deep custom rules + `typescript-eslint`; `eslint.config.js` flat config is now the default |
| **Prettier** | JS | — | Still the most widely-adopted formatter; Biome/Oxc are the fast challengers |

Common 2026 pattern: **oxlint or Biome for the fast 90%** in CI/pre-commit, **ESLint + typescript-eslint** retained for type-aware rules the Rust linters don't yet implement.

## Mental model: dev server vs production build

- **Dev** optimizes for *startup + HMR latency*: native ESM, on-demand transform, no full bundle (Vite's historical esbuild role; now Rolldown).
- **Prod** optimizes for *output*: tree-shaking, code-splitting, chunking, minification, source maps, asset hashing (historically Rollup; now Rolldown).
- Keeping **one engine for both** (Rolldown) is why Vite 8 matters — it ends dev/prod output drift.

## Decision checklist

1. **Framework lock-in?** Next.js → Turbopack. Otherwise → Vite.
2. **Migrating webpack?** → Rspack (compat) before considering a rewrite to Vite.
3. **Library, not app?** → Rollup/Rolldown (clean ESM) or `tsup`/esbuild for speed.
4. **Lint/format speed pain?** → add oxlint/Biome to CI; keep ESLint for type-aware rules.
5. **"Build is slow"** → identify the stage (transpile vs bundle vs typecheck vs lint); move transpile to esbuild/SWC/Oxc, move typecheck to a separate `tsc --noEmit` job, parallelize.

## Anti-patterns

- Running Babel for plain TS/JS transpile when esbuild/SWC/Oxc do it 20-100× faster.
- Treating the bundler as a type-checker — bundlers strip types, they don't verify them.
- Adopting a bleeding-edge RC (e.g. Rolldown 1.0 RC) for a critical legacy app without a fallback path.
- Mixing ESLint legacy `.eslintrc` and flat `eslint.config.js` — pick flat config.

## Sources

- "Rust Is Eating the JavaScript Toolchain: Rolldown, Oxc, Rspack" — dev.to (2026)
- "Vite 8, Rolldown, and Oxc: Rust Is Taking Over the JavaScript Toolchain" — dev.to / alexcloudstar (2026)
- "The Current State of JavaScript Bundlers" — blog.openreplay.com
- "Vite vs Turbopack vs Rspack Benchmark [2026]" — kunalganglani.com
- State of JavaScript 2024 — Build Tools — 2024.stateofjs.com
- rstackjs/build-tools-performance benchmarks — github.com
