---
title: "Node.js Package Management & Supply-Chain"
description: "This reference is the consumer side of the npm ecosystem: how you *install,"
---

# Node.js Package Management & Supply-Chain

## Overview

This reference is the **consumer side** of the npm ecosystem: how you *install,
resolve, lock, and secure* the dependencies a Node.js project pulls in. It covers the
four mainstream package managers (npm, pnpm, Yarn Berry, bun), the lockfile +
reproducible-install contract, workspaces/monorepos, semver resolution and override
mechanics, npm scripts/lifecycle, and the supply-chain hardening surface (audit,
provenance, install-script defenses, PM pinning).

It deliberately stops at three boundaries owned by sibling references:

- **`nodejs-module-resolution`** — owns *how Node finds a module at runtime*
  (`require`/CJS, `ESM_RESOLVE`, the `exports`/`imports` fields, conditional exports).
  This file gets the bytes onto disk; that file resolves a specifier against them.
- **`devops-containers-cicd` (library packaging)** — owns *publishing a library*:
  `npm publish`, `files`/`exports` for distribution, ESM↔CJS dual builds,
  `semantic-release`. This file consumes the registry; that one ships to it. (Provenance
  here is covered only as a *consumer* verification + the `--provenance` publish flag.)
- **`nodejs-typescript-and-runtime-features`** — owns native TS loading, SEA, and the
  full `node --run` runtime story. This file references `node --run` only for its
  lifecycle-script behavior.

The mental model: **manifest (`package.json`) declares intent → resolver picks concrete
versions → lockfile freezes them → installer materializes `node_modules` (or a PnP map) →
lifecycle scripts run → audit/provenance/pinning guard the supply chain.**

## Core concepts

### 1. The package managers — install models that differ at the layout layer

All four read `package.json`, but they materialize dependencies very differently:

- **npm** — the default. Builds a **flat, hoisted `node_modules`**: transitive deps are
  pulled up to the top level when versions allow. Simple and maximally compatible, but
  hoisting exposes **phantom dependencies** — your code can `require` a package you never
  declared (because a *transitive* dep hoisted it), and the import silently breaks the day
  that transitive dep drops it.
- **pnpm** — a **content-addressable global store** (`~/.pnpm-store`/`~/.local/share/pnpm`):
  every file of every package version is stored once and **hard-linked** into projects, so
  N projects sharing a version cost ~one copy on disk. `node_modules` is **symlinked and
  isolated**: only packages you *actually declared* are reachable at the top level (the rest
  live under `node_modules/.pnpm/`), which **eliminates phantom deps by construction**.
  Fastest on large/monorepo installs.
- **Yarn (Berry, v2+) with Plug'n'Play (PnP)** — eliminates `node_modules` entirely.
  Resolution lives in a generated **`.pnp.cjs`** loader that maps every package to its
  location inside zipped caches; Node loads it via a runtime hook. Strict ("semantic
  erroring" on undeclared deps), fast, low storage, and supports **zero-installs**
  (commit the cache + `.pnp.cjs`). Fallback to a classic layout via
  `nodeLinker: node-modules` in `.yarnrc.yml` for tools that can't speak PnP (e.g. some
  React Native setups).
- **bun install** — Bun's installer is a drop-in for `npm install` that uses a **global
  cache** (`~/.bun/install/cache/`) with **hardlinks / copy-on-write**, parallel downloads,
  and platform-tuned syscalls (`hardlink` backend on Linux). Materializes a normal
  `node_modules`; markedly faster than npm on cold and warm installs.

### 2. Lockfiles — the reproducibility contract

A lockfile pins the **entire resolved tree** (exact versions + resolved URLs +
**integrity** hashes, typically SHA-512 / SRI) so a second install reproduces the first
bit-for-bit. Each PM has its own:

| PM | Lockfile | Notes |
| --- | --- | --- |
| npm | `package-lock.json` | JSON; `integrity` field is the SRI hash verified on install. |
| pnpm | `pnpm-lock.yaml` | YAML; encodes the isolated layout + peer resolution. |
| Yarn | `yarn.lock` | Berry uses a YAML-ish format; Classic a custom one. |
| bun | `bun.lock` (text) | Replaced the binary `bun.lockb` in Bun 1.2; text diffs cleanly. |

- **Always commit the lockfile** for apps (libraries usually publish without dictating
  consumers' trees). It is the single source of truth for what actually ran in CI/prod.
- **`npm ci` vs `npm install`**: `npm install` *reconciles* — if a range in
  `package.json` no longer matches the lock, it re-resolves and **rewrites the lock**.
  `npm ci` is **strict and reproducible**: it requires an existing lock that matches
  `package.json`, wipes `node_modules`, installs **exactly** the locked versions, and
  **errors** on any mismatch (it never edits the lock). Use `npm ci` in CI/CD and
  post-clone. The frozen equivalents: `yarn install --frozen-lockfile` (Classic) /
  `--immutable` (Berry), `pnpm install --frozen-lockfile`, `bun install --frozen-lockfile`.

### 3. Workspaces / monorepos

A workspace is a repo of multiple packages sharing one install + one lock, with local
packages linked to each other instead of being fetched from the registry.

- **Declaration**: npm and Yarn use a `"workspaces": [...]` array in the root
  `package.json`; **pnpm uses a dedicated `pnpm-workspace.yaml`** (`packages:` globs).
- **The `workspace:` protocol** (originated in pnpm; supported by Yarn Berry and npm 7+):
  a dependency written `"pkg-a": "workspace:*"` (or `workspace:^`) **must** resolve to the
  local workspace package, never the registry. On publish, the PM rewrites `workspace:*`
  to the concrete version so external consumers get a normal range.
- **Hoisting vs isolation**: npm/Yarn-classic hoist shared deps to the root (re-exposing
  phantom-dep risk across the monorepo); pnpm keeps each package isolated by default.
- **Running scripts across packages**: npm `--workspace=<name>` / `--workspaces`; Yarn
  `yarn workspace <name> <cmd>` / `yarn workspaces foreach`; pnpm `--filter <name>` and
  **`-r`** (recursive). pnpm/Yarn order execution by the **dependency graph** (build a
  package's local deps first); this topological awareness is a major monorepo win.

### 4. Dependency resolution & semver

Ranges in `package.json` are **semver** (`MAJOR.MINOR.PATCH`); the resolver picks the
highest published version satisfying every constraint, then **dedupes** shared transitive
deps.

- **Range operators**: `^1.2.3` allows the **leftmost-non-zero** to stay fixed → `>=1.2.3
  <2.0.0` (npm/Yarn/pnpm default on `add`); `~1.2.3` allows only patch bumps → `>=1.2.3
  <1.3.0`. Beware `^0.x`: `^0.2.3` means `>=0.2.3 <0.3.0` (minor is treated as breaking
  while major is 0). Also `1.2.x`, `*`, `>=`, `||`, hyphen ranges.
- **`peerDependencies`** — "the host must provide this" (e.g. a React plugin peers
  `react`). Auto-install behavior **differs per PM** — state it precisely:
  - **npm 7+**: auto-installs missing peers by default (npm ≤6 only *warned*).
  - **pnpm 8+**: `auto-install-peers` defaults to **true** (it was `false` in v7).
  - **Yarn Berry**: does **not** auto-install peers — it warns and you add them yourself.
  On a *conflicting* peer requirement, PMs decline to auto-install and warn.
- **`optionalDependencies`** — install failure is non-fatal (used for platform-specific
  native binaries); guard usage with try/catch since they may be absent.
- **Overriding a transitive version** (force a patched nested dep) — the field name
  **differs per PM**: npm `"overrides"`, **Yarn `"resolutions"`**, pnpm `"pnpm.overrides"`.
  The primary lever for fast supply-chain remediation when a deep dep is vulnerable but its
  parent hasn't bumped.
- **`engines`** — declares supported `node`/PM versions; advisory by default, enforced with
  `engine-strict` (npm) / `engineStrict`. Pair with the `packageManager` field (concept 6).

### 5. npm scripts & lifecycle

`"scripts"` in `package.json` defines named commands run via `npm run <name>`. npm
**auto-wraps** any script with hooks: running `<name>` executes `pre<name>` → `<name>` →
`post<name>` in sequence (e.g. `prebuild`/`build`/`postbuild`).

- **Install lifecycle**: `preinstall` → `install` → `postinstall` run during
  `npm install`. **`postinstall` is the most-abused hook** — it's how a malicious dependency
  gets arbitrary code execution on `npm install` (see concept 6).
- **`prepare`** runs on local install (no package args) and before `npm pack`/`npm publish`;
  npm guidance is to **use `prepare` for build steps, not `install`/`preinstall`** — the only
  legitimate use of `install`/`preinstall` is native compilation that must happen on the
  target architecture.
- **Security note — `node --run` skips pre/post hooks.** Node's built-in `node --run <script>`
  executes *only* the named script and, by **intentional design, does NOT run `pre`/`post`
  lifecycle scripts** (and ignores `NODE_OPTIONS`). That makes it faster and more predictable,
  but means a `predeploy`/`postdeploy` you *rely on* will silently not run. For the full
  `node --run` runtime semantics see **`nodejs-builtin-modules-modern`** (or
  `nodejs-typescript-and-runtime-features`).

### 6. Supply-chain security

The dependency graph is the largest untrusted attack surface in a Node app. The defenses:

- **`npm audit`** cross-checks the installed tree against the advisory DB; `npm audit fix`
  remediates within ranges, `--force` may bump majors (review the diff). **`npm audit
  signatures`** verifies registry signatures **and provenance attestations** — tying audit
  to concept-6 provenance.
- **Provenance & trusted publishing** (GA 2023, via **Sigstore**): publishing with
  **`npm publish --provenance`** from a supported CI (GitHub Actions, GitLab) creates a
  cryptographically signed, publicly logged (Rekor transparency log) link between the
  published tarball, the **source commit**, and the **build**. **Trusted publishing** uses
  short-lived CI **OIDC** tokens instead of long-lived npm tokens, so a leaked token can't
  publish. As a *consumer*, you verify with `npm audit signatures` / the package's
  provenance badge. (Authoring/publishing detail lives in `devops-containers-cicd`.)
- **Install-scripts attack surface**: a compromised package's `postinstall` runs on
  `npm install`. **`--ignore-scripts`** (or `npm config set ignore-scripts true`) blocks all
  lifecycle scripts — OWASP calls it the single most effective mitigation; re-enable per-package
  only for deps that genuinely need native compilation. **`--omit=dev`** / **`--omit=optional`**
  trims the prod install surface (replaces the old `--production`/`--no-optional`).
- **Dependency confusion** (a.k.a. substitution): if a build pulls from a private *and* the
  public registry, an attacker publishes a public package with your **internal name** at a
  **higher version**, and the resolver grabs the malicious one. Mitigate by **scoping**
  internal packages (`@org/...`) and pinning that scope's registry in `.npmrc`, and never
  letting a public range win over an internal name.
- **Lockfile injection**: a malicious PR edits the lockfile to point a name at a different
  tarball/URL while leaving `package.json` innocent-looking. Mitigate by **reviewing lockfile
  diffs**, using `npm ci`/frozen installs (which honor the lock's integrity hash), and
  version/cooldown policies (rejecting versions published in the last N days blunts
  fast-moving compromise windows).
- **Pinning the package manager** — **corepack** + the **`packageManager` field**:
  `"packageManager": "pnpm@9.1.0+sha224.<hash>"` (name@version, optional but recommended
  hash). Corepack (shipped with Node) reads it and transparently runs *that exact* PM
  version, so every contributor and CI uses the same tool — closing a reproducibility/trust
  gap the lockfile alone can't (the lock pins deps, not the resolver). `npm`, `pnpm`, `yarn`
  are the permitted values; explicit pinning beats `COREPACK_ENABLE_AUTO_PIN`.

## Package-manager comparison

| Dimension | npm | pnpm | Yarn Berry (PnP) | bun |
| --- | --- | --- | --- | --- |
| Install model / layout | Flat hoisted `node_modules` | Content-addressable store + **symlinked, isolated** `node_modules` | **No `node_modules`** — `.pnp.cjs` resolution map (or `nodeLinker: node-modules`) | Flat `node_modules` from a global cache |
| Store / cache | Per-project copy (global cache `_cacache`) | Global store, **hard-linked** (one copy/version on disk) | Zipped caches; supports zero-installs | Global cache w/ hardlink / copy-on-write |
| Lockfile | `package-lock.json` | `pnpm-lock.yaml` | `yarn.lock` | `bun.lock` (text) |
| Workspace config | `workspaces` in `package.json` | **`pnpm-workspace.yaml`** | `workspaces` in `package.json` | `workspaces` in `package.json` |
| Run across packages | `--workspace` / `--workspaces` | `--filter` / `-r` (graph-ordered) | `yarn workspace(s)` / `foreach` | `--filter` |
| peerDeps auto-install | **On** (npm 7+) | **On** (pnpm 8+, `auto-install-peers`) | **Off** (warns) | On (npm-compatible) |
| Override field | `overrides` | `pnpm.overrides` | **`resolutions`** | `overrides` (npm-compatible) |
| Phantom-dep strictness | Loose (hoist exposes undeclared) | **Strict by construction** | **Strict** ("semantic erroring") | Loose (flat layout) |
| Frozen/CI install | `npm ci` | `--frozen-lockfile` | `--immutable` | `--frozen-lockfile` |

## Practical patterns

- **CI/CD always uses the frozen install** — `npm ci` / `pnpm i --frozen-lockfile` /
  `yarn install --immutable` / `bun install --frozen-lockfile`. It's faster (skips
  re-resolution), reproducible, and fails loudly on lock drift.
- **Pin the PM with `packageManager` + corepack** so "works on my machine" can't be a
  resolver-version difference. Commit the field; let corepack enforce it.
- **Default to `--ignore-scripts` org-wide**, then allowlist the handful of deps that need
  native builds. Combine with `--omit=dev`/`--omit=optional` for prod images.
- **Remediate deep CVEs with the override field** (`overrides`/`resolutions`/`pnpm.overrides`)
  to force a patched transitive version while you wait for the parent to bump.
- **Reach for pnpm on monorepos** — graph-ordered `--filter -r` runs and the isolated store
  are the biggest practical wins; reach for Yarn PnP for strictness + zero-installs, and bun
  install for raw speed.
- **Verify provenance on critical deps** (`npm audit signatures`) and prefer packages
  published with provenance/trusted publishing.

## Anti-patterns

- **Not committing the lockfile** (or `.gitignore`-ing it) — you forfeit reproducibility and
  can't audit what actually shipped.
- **`npm install` in CI** instead of `npm ci` — lets a stale/mismatched lock silently
  re-resolve and rewrite, defeating the whole point of locking.
- **Relying on a phantom dependency** — importing a package you never declared because it
  hoisted; it breaks the day a transitive dep drops it. (pnpm/PnP make this an immediate
  error — a feature, not a nuisance.)
- **Running `npm install` untrusted with scripts enabled** — a single `postinstall` is RCE.
  Audit new deps and default to `--ignore-scripts`.
- **`audit fix --force` without reading the diff** — it can pull a breaking major and quietly
  change your tree.
- **Mixing package managers in one repo** (an `npm install` over a pnpm project) — produces a
  conflicting/second lockfile and an inconsistent tree. Pin one PM via `packageManager`.
- **Wide-open `*` / `latest` ranges or `^0.x` blindness** — surrenders control over what
  resolves and widens the compromise window.

## Troubleshooting

- **`npm ci` fails: "lock file's ... does not satisfy ... in package.json"** → the lock is
  out of sync; run `npm install` locally to reconcile and **commit the updated lock**, then
  `npm ci` passes. Never hand-edit the lock to fix this.
- **`ERESOLVE` peer-dependency conflict (npm 7+)** → a peer range can't be satisfied across
  the tree. Fix the real version, or use `overrides`; `--legacy-peer-deps` *suppresses* the
  check (last resort — it ships a tree npm considers invalid).
- **"Cannot find module X" after switching to pnpm/Yarn PnP** → X was a phantom dependency;
  **declare it** in `package.json` (PnP: or add via `packageExtensions`). This is the strict
  layout doing its job.
- **Integrity / `EINTEGRITY` checksum mismatch** → the downloaded tarball's hash ≠ the lock's
  `integrity`. Clear the cache (`npm cache clean --force`), confirm the registry, and treat an
  unexplained mismatch as a possible tampering/lockfile-injection signal.
- **Different results local vs CI** → almost always a **PM-version** drift (pin via corepack)
  or `npm install` vs `npm ci`. Lock the resolver, not just the deps.
- **`postinstall`/build step not running under `node --run`** → expected: `node --run` skips
  pre/post hooks by design. Use `npm run` (or call the script explicitly) when you need the
  hooks.

## References

- npm Docs — `npm ci` (reproducible install, strict lock match): https://docs.npmjs.com/cli/v11/commands/npm-ci/
- npm Docs — package-locks (`package-lock.json`, `integrity`/SRI): https://docs.npmjs.com/cli/v6/configuring-npm/package-locks/
- npm Docs — scripts (lifecycle, pre/post hooks, `prepare` vs `install`): https://docs.npmjs.com/cli/v11/using-npm/scripts
- npm Docs — semver / version ranges (`^`, `~`): https://docs.npmjs.com/cli/v6/using-npm/semver/
- npm Docs — Generating provenance statements & Trusted publishers: https://docs.npmjs.com/generating-provenance-statements/ ; https://docs.npmjs.com/trusted-publishers/
- pnpm — Motivation, symlinked `node_modules`, store (content-addressable + hard links): https://pnpm.io/motivation ; https://pnpm.io/symlinked-node-modules-structure
- pnpm — Workspaces & the `workspace:` protocol: https://pnpm.io/workspaces ; Settings (`auto-install-peers`, `overrides`): https://pnpm.io/settings
- Yarn — Plug'n'Play (`.pnp.cjs`, strict deps, `nodeLinker` fallback): https://yarnpkg.com/features/pnp ; Workspaces (`workspace:` protocol): https://yarnpkg.com/features/workspaces
- Yarn (Classic) — dependency versions / `resolutions`: https://classic.yarnpkg.com/lang/en/docs/dependency-versions/
- Bun — `bun install` (global cache, hardlink backend) & text lockfile: https://bun.com/docs/pm/cli/install ; https://bun.com/blog/bun-lock-text-lockfile
- Node.js — `--run` (skips pre/post lifecycle scripts; ignores `NODE_OPTIONS`): https://nodejs.org/api/cli.html#--run
- Node.js — Corepack & the `packageManager` field (PM pinning): https://nodejs.org/api/corepack.html ; https://github.com/nodejs/corepack
- GitHub Blog — Introducing npm package provenance (Sigstore): https://github.blog/security/supply-chain-security/introducing-npm-package-provenance/ ; Sigstore Blog — provenance GA: https://blog.sigstore.dev/npm-provenance-ga/
- OWASP / Snyk — dependency confusion & `--ignore-scripts` mitigations: https://snyk.io/blog/detect-prevent-dependency-confusion-attacks-npm-supply-chain-security/ ; https://github.com/lirantal/npm-security-best-practices
