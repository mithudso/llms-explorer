---
title: "Node.js Modern Batteries-Included Built-ins"
description: "Between Node.js v20 and v26 (2024-2026) the runtime absorbed a wave of capabilities that"
---

# Node.js Modern Batteries-Included Built-ins

## Overview

Between Node.js v20 and v26 (2024-2026) the runtime absorbed a wave of capabilities that
historically required an npm dependency. A SQLite driver, a WebSocket *client*, `.env`
parsing, a task runner, file watching, glob matching, terminal colors, deep cloning, and a
V8 startup cache now all ship in core. The practical upshot: many small projects can drop
`better-sqlite3`, `ws`, `dotenv`, `nodemon`, `chalk`, `glob`, and `lodash.cloneDeep`
entirely.

The catch — and the reason this reference exists — is **stability is per-feature and
recent**. Some of these are fully Stable (2), several are Release Candidate (1.2), and a
few are still Experimental (1) or "Active development" (1.1). Shipping an Experimental API
to production without pinning the Node version is the cardinal sin here. Every concept
below states its **added-in version and current stability index explicitly**; treat those
as the load-bearing facts, because an API that is RC today may change a method signature in
the next minor.

Scope boundaries (owned by sibling references in this family): Single-Executable
Applications, the `--permission` model, and native TypeScript stripping live in
`nodejs-typescript-and-runtime-features`; the **deep** `node:test` runner (mocking,
coverage, reporters, snapshots) lives in `nodejs-test-runner` — `node:test` is mentioned
here only as "it exists, it replaces Jest/Mocha for many projects, see the sibling";
Bun/Deno/edge equivalents live in `javascript-runtimes-deno-bun-edge`.

A note on reading stability: index **2** = Stable; **1.2** = Release Candidate (API frozen,
shipping unflagged, final polish); **1.1** = Active development (unflagged but may change);
**1** = Experimental; **1.0** = Early development. Anything below 2 deserves a pinned
`engines.node` and a changelog read on upgrade.

## Core concepts

### 1. `node:sqlite` — a built-in synchronous SQLite driver

Added in **v22.5.0**, unflagged since **v23.4.0 / v22.13.0** (was behind
`--experimental-sqlite`), currently **Stability 1.2 - Release Candidate**. Available only
under the `node:` scheme. It is the in-core analogue of **`better-sqlite3`**: synchronous,
prepared-statement-centric, fast.

```js
import { DatabaseSync } from 'node:sqlite';

const db = new DatabaseSync(':memory:');               // or a path, or a Buffer/URL
db.exec('CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT) STRICT');

const insert = db.prepare('INSERT INTO users (id, name) VALUES (?, ?)');
insert.run(1, 'Ada');                                  // { changes: 1, lastInsertRowid: 1 }

const byId = db.prepare('SELECT * FROM users WHERE id = ?');
byId.get(1);                                           // { id: 1, name: 'Ada' } | undefined
db.prepare('SELECT * FROM users').all();               // [{ id, name }, ...]
for (const row of byId.iterate(1)) { /* streaming */ } // iterate added v23.4.0/v22.13.0
```

- **`DatabaseSync(path[, options])`** options: `open` (default `true`), `readOnly`,
  `enableForeignKeyConstraints` (default `true`), `allowExtension`, `timeout` (busy timeout
  ms), `readBigInts`, `returnArrays`, `allowBareNamedParameters` (default `true`),
  `allowUnknownNamedParameters`. `:memory:` is an in-memory DB.
- **`StatementSync`** (from `db.prepare(sql)`): `get()` → first row or `undefined`;
  `all()` → array; `run()` → `{ changes, lastInsertRowid }`; `iterate()` → row iterator.
  Config methods: `setReadBigInts(true)` (read `INTEGER` as `BigInt`),
  `setReturnArrays(true)`, `setAllowBareNamedParameters(true)`,
  `setAllowUnknownNamedParameters(true)`. Introspection: `columns()`, `sourceSQL`,
  `expandedSQL`.
- **Parameter binding** — three styles: anonymous `?` (positional varargs), and named
  `:name` / `@name` / `$name` (pass an object keyed by the prefixed name, e.g.
  `{ ':id': 1 }`; bare keys `{ id: 1 }` work when `allowBareNamedParameters` is on).
- **`db.aggregate(name, { start, step, result, inverse })`** registers custom SQL aggregate
  / window functions; **`backup(sourceDb, destPath, { rate, progress })`** does an online
  backup; `db.loadExtension()` requires `allowExtension: true`. `constants` (v23.5.0)
  exposes `SQLITE_CHANGESET_*`, authorizer codes, etc. (serialize/deserialize landed later,
  ~v26).
- **Type map**: `NULL↔null`, `INTEGER↔number|bigint`, `REAL↔number`, `TEXT↔string`,
  `BLOB↔Uint8Array`/TypedArray.

### 2. The global `WebSocket` client (undici-backed)

A spec-compliant, browser-compatible **`WebSocket`** is exposed on the global scope, backed
by undici. Timeline: experimental behind `--experimental-websocket` in **v21**, **on by
default in v22.0.0** (disable with `--no-experimental-websocket`), and **no longer
experimental as of v22.4.0**. No import needed.

```js
const ws = new WebSocket('wss://example.com/feed');
ws.addEventListener('open',   () => ws.send('hello'));
ws.addEventListener('message', (e) => console.log(e.data));
ws.addEventListener('error',  (e) => console.error(e));
ws.addEventListener('close',  () => {});
```

It replaces the **`ws`** package **for client use only**. Critically, there is **no
built-in WebSocket *server*** — to accept connections you still need `ws` (or another
library). The API is the WHATWG/browser `WebSocket`, not the `ws` EventEmitter API, so it
is portable to browsers but is *not* a drop-in for `ws`'s `.on('message')` server-side
idioms.

### 3. Environment files — `--env-file`, `loadEnvFile()`, `util.parseEnv()`

The in-core replacement for **`dotenv`**. Three surfaces:

- **`--env-file=.env`** (CLI) — added **v20.6.0**, **Stable** since **v24.10.0 / v22.21.0**.
  Loads the file into `process.env` before the app runs; Node-config vars like
  `NODE_OPTIONS` are honored. Multiple `--env-file` flags stack (later overrides earlier).
  Real `process.env` values take precedence over file values. **Throws if the file is
  missing.**
- **`--env-file-if-exists=.env`** — added **v22.9.0**. Identical, but silently no-ops if the
  file is absent (use for optional local overrides).
- **`process.loadEnvFile([path])`** — programmatic load (defaults to `./.env`), added
  v20.12.0/v21.7.0. **`util.parseEnv(content)`** (added **v21.6.0 / v20.12.0**) parses a
  `.env`-format **string** and returns a plain object without mutating `process.env`.

**`.env` parsing rules**: `KEY=value` per line; text after `#` is a comment; values may be
quoted with `` ` ``, `"`, or `'` (quotes stripped); **multi-line** quoted values supported
(v21.7.0/v20.12.0); a leading `export ` is ignored. **There is NO variable expansion** —
`PASSWORD=${SECRET}` is the literal string `${SECRET}`, unlike `dotenv-expand`. This is the
single most common migration surprise.

### 4. Task running (`node --run`) and watch mode (`--watch`)

**`node --run <script>`** (added **v22.0.0**, **Stability 1.1 - Active development**) runs a
`scripts` entry from `package.json` — the in-core, faster alternative to `npm run` and a
partial replacement for `nodemon`-style wrappers when combined with `--watch`.

```bash
node --run build              # runs package.json scripts.build
node --run test -- --watch    # everything after -- is forwarded to the script
```

- Sets **`NODE_RUN_SCRIPT_NAME`** (the script name) and **`NODE_RUN_PACKAGE_JSON_PATH`**
  (resolved package.json path) in the child env; prepends `node_modules/.bin` to `PATH`.
- **Intentionally minimal**: it **does NOT run `pre`/`post` lifecycle scripts**
  (`prebuild`/`postbuild` are skipped), unlike `npm run`. This is the chief footgun when
  migrating from npm — chained build steps silently stop running. It also doesn't read npm
  config or run arbitrary shell features npm provides.

**Watch mode** restarts the process on file changes — the in-core **`nodemon`**:

- **`--watch`** — restart on changes to the entry file and its imported module graph.
- **`--watch-path=<dir>`** — watch explicit paths instead of the dependency graph (repeatable).
- **`--watch-preserve-output`** — don't clear the terminal on restart (keep prior logs).
- Combine with `--run`: `node --run dev` where `scripts.dev` is `node --watch --env-file=.env server.js`.

### 5. Filesystem & utility built-ins: `fs.glob`, `util.styleText`, `structuredClone`, `navigator`

- **`fs.glob` / `fs.globSync` / `fsPromises.glob`** — added **v22.0.0** (unflagged
  v22.2.0), **Stability 1 - Experimental** (the least-mature item here). Replaces
  **`glob`** / **`fast-glob`**. Options: `cwd`, `exclude` (a predicate `(p) => boolean` or
  an array of glob patterns — note **negation `!pattern` is not supported**),
  `withFileTypes` (return `Dirent` objects instead of path strings).
  ```js
  import { globSync } from 'node:fs';
  const files = globSync('src/**/*.js', { exclude: ['**/*.test.js'] });
  ```
- **`util.styleText(format, text[, options])`** — terminal ANSI styling; replaces **`chalk`**
  / `colors` / `kleur`. Added **v21.7.0 / v20.12.0**, since stabilized to **2 - Stable**.
  `format` is a style name or an array of them (e.g. `['bold', 'red']`); colors and
  modifiers like `bold`, `italic`, `underline`, `dim`, `bgGreen` are supported. It honors
  **`NO_COLOR`** / **`FORCE_COLOR`** and falls back to `tty.hasColors()` auto-detection;
  pass `{ stream: process.stdout }` so it decides based on the actual output target.
  ```js
  import { styleText } from 'node:util';
  console.log(styleText(['bold', 'green'], 'OK'));
  ```
- **`structuredClone(value)`** — global, added **v17.0.0** (precisely v17.6.0 / v16.15.0),
  **Stable** (WHATWG standard). Deep-clones via the structured-clone algorithm (handles
  `Map`/`Set`/`Date`/`ArrayBuffer`/typed arrays/circular refs), replacing
  **`lodash.cloneDeep`** for clonable data. Caveat: it **cannot clone functions, DOM-less
  class prototypes (methods are dropped → plain objects), or symbols** — it throws
  `DataCloneError` on functions.
- **`navigator`** — global Web-interop object, added **v21.0.0**, **Stability 1.1 - Active
  development** (disable with `--no-experimental-global-navigator`).
  `navigator.hardwareConcurrency` (v21.0.0) returns the logical-CPU count — a cleaner
  replacement for `os.cpus().length` when sizing worker pools; `navigator.userAgent`
  (v21.1.0) is `Node.js/<major>`; `navigator.language` / `navigator.languages` (v21.2.0)
  report the runtime locale.

### 6. Module compile cache — `module.enableCompileCache()` / `NODE_COMPILE_CACHE`

Persists V8's **code cache** for CommonJS, ESM, **and** TypeScript modules to disk so
subsequent process starts skip recompilation — a meaningful startup-time win for CLIs and
serverless cold starts. Added **v22.8.0**; **no longer experimental as of v25.4.0**
(**Stability 1.2 - Release Candidate**).

```js
// Best placed at the very top of the entry module, before other requires/imports
import { enableCompileCache } from 'node:module';
enableCompileCache(); // → { status, message?, directory? }
```

- **`module.enableCompileCache([directory])`** returns `{ status, message?, directory? }`
  where `status` is one of `module.constants.compileCacheStatus`: `ENABLED`,
  `ALREADY_ENABLED`, `FAILED` (with `message`), or `DISABLED` (when
  `NODE_DISABLE_COMPILE_CACHE=1`). Without an argument it uses the `NODE_COMPILE_CACHE`
  env var, else `os.tmpdir()/node-compile-cache`.
- **`module.getCompileCacheDir()`** returns the active cache dir (or `undefined`);
  **`module.flushCompileCache()`** (v22.10.0+) writes accumulated cache to disk immediately
  rather than waiting for process exit — useful before spawning children that should reuse it.
- **`NODE_COMPILE_CACHE=<dir>`** enables it without code changes (set it once, no
  `enableCompileCache()` call needed). `NODE_COMPILE_CACHE_PORTABLE=1` (or
  `{ portable: true }`) lets the cache survive the project being moved. Caches are
  **Node-version-specific**; first run is slightly slower (cache is generated then), and
  code coverage is slightly less precise on deserialized functions.

### 7. (Pointer) `node:test` — the built-in test runner

Node ships a full test runner (`node --test`, `node:test`, `node:assert`) that replaces
Jest/Mocha for many projects. **Deep coverage is deferred** to the `nodejs-test-runner`
sibling (mocking, code coverage, reporters, snapshot testing, watch integration). Listed
here only so the "what's built-in now" inventory is complete.

### 8. CLI app building with built-ins (`util.parseArgs`, `readline/promises`, signals, exit codes)

A small CLI no longer needs `minimist`/`yargs` for arg parsing or `inquirer` for simple
prompts — `util.parseArgs`, `node:readline/promises`, and the `process`/`tty` globals cover
the common cases. Combine with the shebang + `node --run` story from §4 (a `scripts.cli`
entry, or a `#!/usr/bin/env node` file made executable) to ship a dependency-free tool.

- **`util.parseArgs([config])`** — added **v18.3.0 / v16.17.0**, **Stability 2 - Stable**
  since v20.0.0; the in-core replacement for **`minimist`** / **`yargs`** (for non-trivial
  arg parsing). `config.options` keys are long names; each value is `{ type: 'string' |
  'boolean' (required), short, multiple, default }`. Parser flags: `args` (defaults to
  `process.argv` minus execPath+filename), `strict` (default `true` — throws on unknown
  args / type mismatch), `allowPositionals` (default `false` when `strict`), `allowNegative`
  (`--no-foo` sets a boolean `false`; added **v22.4.0 / v20.16.0**), and `tokens` (return a
  parsed-token stream to extend behavior). Returns `{ values, positionals, tokens? }`.
  Defaults landed in **v18.11.0 / v16.19.0**.
  ```js
  import { parseArgs } from 'node:util';
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      output: { type: 'string', short: 'o', default: 'out.txt' },
      verbose: { type: 'boolean', short: 'v' },
      include: { type: 'string', multiple: true },   // repeatable → string[]
    },
  });
  // node cli.js -v -o build.txt --include a --include b file1 file2
  // values → { output: 'build.txt', verbose: true, include: ['a','b'] }
  // positionals → ['file1', 'file2']
  ```
- **`node:readline/promises`** — added **v17.0.0**, **Stability 2 - Stable** since
  **v24.0.0 / v22.17.0**; the async/await prompt API (replaces `inquirer`/`prompts` for
  simple questions). `createInterface({ input, output })` then `await rl.question(query)`
  resolves to the typed line; `rl.close()` when done. `question` accepts `{ signal }` (e.g.
  `AbortSignal.timeout(10_000)`) to cancel a hung prompt.
  ```js
  import * as readline from 'node:readline/promises';
  import { stdin as input, stdout as output } from 'node:process';
  const rl = readline.createInterface({ input, output });
  const name = await rl.question('Name? ');
  rl.close();
  ```
- **Line processing via async iteration** — the interface is an async iterable
  (`Symbol.asyncIterator`, added **v11.4.0 / v10.16.0**), so a CLI can stream stdin or a file
  line-by-line; `break`/`return`/`throw` out of the loop auto-calls `rl.close()`. Use
  `crlfDelay: Infinity` to treat `\r\n` as one break. (For perf-critical bulk reads the
  `'line'` event is faster than iteration.)
  ```js
  import { createInterface } from 'node:readline';
  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of rl) process.stdout.write(line.toUpperCase() + '\n');
  ```
- **`process.argv` / `argv0` / `execPath`** — `process.argv` is `[execPath, scriptPath,
  ...args]`; `parseArgs` already strips the first two by default, so reach for raw `argv`
  only when you need the script path or a passthrough tail. `process.argv0` (v6.4.0) is the
  original `argv[0]` even if `argv` was rewritten; `process.execPath` (v0.1.100) is the
  resolved `node` binary path (handy for re-spawning the same runtime).
- **Exit codes — prefer `process.exitCode` over `process.exit()`.** Set
  `process.exitCode = 1` and let the event loop drain; calling `process.exit()` terminates
  **synchronously** and can **truncate async stdout/stderr writes** (they may span multiple
  ticks), so a usage message printed right before `exit(1)` can be lost. Convention: `0` =
  success, non-zero = failure; an unhandled `SIGINT`/`SIGTERM` exits with `128 + signal`.
- **Signal handling for graceful shutdown** — `process.on('SIGINT', …)` (Ctrl-C, all
  platforms) and `process.on('SIGTERM', …)` (all except Windows) let a long-running CLI flush
  buffers, close handles, then set `process.exitCode` and return. Installing a listener
  overrides the default `128 + n` exit, so set the code yourself.
  ```js
  for (const sig of ['SIGINT', 'SIGTERM']) {
    process.on(sig, () => { cleanup(); process.exitCode = sig === 'SIGINT' ? 130 : 143; });
  }
  ```
- **Detect interactive vs piped, and color.** `process.stdout.isTTY` (the `stream.isTTY`
  flag, v0.5.8) / `tty.isatty(fd)` tell you whether output is a terminal or a pipe — gate
  spinners/prompts/ANSI on it. For the colors themselves, use **`util.styleText` (see §5)**
  rather than hand-rolling escapes; it already honors `NO_COLOR`/`FORCE_COLOR` and
  `tty.hasColors()` (added **v11.13.0 / v10.16.0**) when passed `{ stream }`.

## Replaces (dep → built-in)

| Third-party dep | Built-in replacement | Added / current stability | Caveat |
| --- | --- | --- | --- |
| `better-sqlite3` | `node:sqlite` (`DatabaseSync`) | v22.5.0 / **1.2 RC** | Synchronous-only; don't block a hot request path |
| `ws` (client) | global `WebSocket` | v21 → default v22.0.0 / **stable v22.4.0** | **Client only** — no built-in server |
| `dotenv` | `--env-file` / `process.loadEnvFile()` / `util.parseEnv()` | v20.6.0 / **Stable** (v24.10.0/v22.21.0) | **No `${var}` expansion** |
| `nodemon` | `--watch` / `--watch-path` / `--watch-preserve-output` | v18.11+ (watch) | Restarts whole process |
| `npm run` (speed) | `node --run` | v22.0.0 / **1.1** | **Skips pre/post scripts** |
| `chalk` / `colors` | `util.styleText()` | v21.7.0/v20.12.0 / **Stable** | Respects `NO_COLOR`/`FORCE_COLOR` |
| `glob` / `fast-glob` | `fs.glob` / `fs.globSync` | v22.0.0 / **1 Experimental** | No `!` negation in `exclude` |
| `lodash.cloneDeep` | `structuredClone()` | v17 / **Stable** | Can't clone functions/methods |
| `os.cpus().length` | `navigator.hardwareConcurrency` | v21.0.0 / **1.1** | navigator still Active-development |
| build-time compile caches | `module.enableCompileCache()` / `NODE_COMPILE_CACHE` | v22.8.0 / **1.2 RC** | Cache is Node-version-specific |
| `jest` / `mocha` | `node:test` (see `nodejs-test-runner`) | v18+ / Stable | Deferred to sibling reference |

## Practical patterns

- **Gate on the Node version.** Set `"engines": { "node": ">=22.13" }` (or whatever each
  feature you use requires) in `package.json` and verify in CI. These APIs simply don't
  exist on older runtimes, and Experimental/RC ones can change between minors.
- **Dependency-free local dev script.** `"dev": "node --watch --env-file-if-exists=.env.local --env-file=.env src/server.js"`,
  launched via `node --run dev` — replaces the `nodemon` + `dotenv-cli` + `npm run` stack
  with zero `node_modules`.
- **`node:sqlite` for embedded/test data.** Use `:memory:` databases as fast, disposable
  fixtures in tests; prepared statements are reusable — `prepare()` once at module scope,
  `run/get/all` many times.
- **Right-size worker pools with `navigator.hardwareConcurrency`** instead of importing
  `os` — `const pool = Math.max(1, navigator.hardwareConcurrency - 1)`.
- **Compile cache for CLIs/cold starts.** Either call `enableCompileCache()` as the first
  line of the entry file, or ship a launcher that sets `NODE_COMPILE_CACHE`; for processes
  that spawn workers, `flushCompileCache()` then pass `NODE_COMPILE_CACHE` down so children
  reuse it.
- **`util.styleText({ stream })`** so color is decided by the real output target (pipe vs
  TTY), and let `NO_COLOR` work for free instead of hand-rolling a `supportsColor` check.

## Anti-patterns

- **Shipping an Experimental/RC API to prod without pinning Node.** `fs.glob` (1),
  `navigator`/`node --run` (1.1), and `node:sqlite`/compile-cache (1.2) can change. Pin
  `engines.node` and read the changelog on upgrade — don't assume "it's in core so it's
  frozen."
- **Treating the global `WebSocket` as a server.** It's a client. Reaching for it to
  *accept* connections fails; you still need `ws` server-side.
- **Blocking the event loop with `node:sqlite`.** It is synchronous by design; a large
  query or write inside an HTTP handler stalls every other request. Keep heavy SQLite work
  off the main thread (worker thread) or out of hot paths.
- **Expecting `${VAR}` expansion in `--env-file`.** Core `.env` parsing does no
  interpolation; configs that relied on `dotenv-expand` break silently.
- **Assuming `node --run` runs pre/post scripts.** Migrating a `prebuild`/`postbuild`
  chain to `node --run build` silently drops those steps.
- **Using `structuredClone` on objects with methods/functions.** Methods are lost (you get
  a plain object) and a function value throws `DataCloneError` — it clones *data*, not
  behavior.
- **Negation patterns in `fs.glob` `exclude`.** `'!keep.js'` is not supported; use a
  predicate function or a positive pattern set.

## Troubleshooting

- **`ERR_UNKNOWN_BUILTIN_MODULE` / "Cannot find module 'node:sqlite'"** → the Node version
  predates v22.5.0, or it's v22.5.0-v22.12 and you didn't pass `--experimental-sqlite`
  (unflagged only from v23.4.0/v22.13.0). Check `node -v`.
- **`WebSocket is not defined`** → Node < v22 (need `--experimental-websocket` on v21), or
  someone passed `--no-experimental-websocket`. On supported versions it's a global; no
  import.
- **`--env-file` throws on missing file** → expected; switch to `--env-file-if-exists` for
  optional files. If a variable is "ignored," remember real `process.env` overrides file
  values, and that there is no `${}` expansion.
- **`node --run` "command not found" for a tool that works under `npm run`** → it's a
  pre/post script or relies on npm-injected env/PATH behavior `node --run` doesn't
  replicate. Run the underlying binary directly (it is on `node_modules/.bin`).
- **`fs.glob` results differ from the `glob` package** → core glob has its own semantics
  (no `!` negation in `exclude`; `withFileTypes` returns `Dirent`s). It's also Experimental,
  so behavior can shift between minors — pin Node.
- **`styleText` prints raw escape codes / no color** → output isn't a TTY (auto-detection),
  or `NO_COLOR` is set, or `FORCE_COLOR` is needed; pass `{ stream }` and check the env vars.
- **Compile cache "doesn't help" / `status: DISABLED`** → `NODE_DISABLE_COMPILE_CACHE=1` is
  set, or you upgraded Node (caches are version-specific and regenerate), or the cache dir
  isn't writable (`status: FAILED`, check `.message`). First run is always slower.
- **`navigator` is `undefined`** → Node < v21, or `--no-experimental-global-navigator` was
  passed; it's still Stability 1.1.

## References

- Node.js — `node:sqlite` (DatabaseSync/StatementSync, params, aggregate, backup, stability): https://nodejs.org/api/sqlite.html
- Node.js — Node 22 release announcement (node:sqlite, node --run, WebSocket default, fs.glob): https://nodejs.org/en/blog/announcements/v22-release-announce
- Node.js — global `WebSocket` (history: v21 flag → v22.0.0 default → v22.4.0 stable): https://nodejs.org/api/globals.html
- Node.js — Native WebSocket Client guide (undici-backed, client-only): https://nodejs.org/learn/getting-started/websocket
- Node.js v21.0.0 release (initial `--experimental-websocket`): https://github.com/nodejs/node/releases/tag/v21.0.0
- Node.js — CLI (`--env-file`, `--env-file-if-exists`, `--run`, `--watch`, `--watch-path`, `--watch-preserve-output`, `NODE_COMPILE_CACHE`): https://nodejs.org/api/cli.html
- Node.js — `util.parseEnv` & `util.styleText` (formats, NO_COLOR/FORCE_COLOR, versions): https://nodejs.org/api/util.html
- Node.js — `util.parseArgs` (options type/short/multiple/default, positionals, strict, allowNegative, tokens; Stable since v20.0.0): https://nodejs.org/api/util.html#utilparseargsconfig
- Node.js — `node:readline` / `node:readline/promises` (createInterface, rl.question, async line iteration; promises Stable v24.0.0/v22.17.0): https://nodejs.org/api/readline.html
- Node.js — `tty` module (`tty.isatty`, `stream.isTTY`, `writeStream.hasColors`/`getColorDepth`): https://nodejs.org/api/tty.html
- Node.js — `process` (argv/argv0/execPath, exitCode vs exit(), stdin/stdout/stderr, SIGINT/SIGTERM signal events): https://nodejs.org/api/process.html
- Node.js — `process.loadEnvFile()`: https://nodejs.org/api/process.html#processloadenvfilepath
- Node.js — Node 22.10.0 release (node --run env vars, flushCompileCache): https://nodejs.org/en/blog/release/v22.10.0
- Node.js — `fs.glob` / `globSync` / `fsPromises.glob` (cwd/exclude/withFileTypes, Stability 1): https://nodejs.org/api/fs.html
- Node.js — global objects: `structuredClone`, `navigator` (hardwareConcurrency/userAgent/language, Stability 1.1): https://nodejs.org/api/globals.html
- Node.js — `module.enableCompileCache` / `getCompileCacheDir` / `flushCompileCache` (v22.8.0, stable v25.4.0): https://nodejs.org/api/module.html
- Node.js — V8 code caching background ("Code caching for JavaScript developers"): https://v8.dev/blog/code-caching-for-devs
- Node.js — GitHub CHANGELOG (per-version "added/unflagged/stabilized" notes for all of the above): https://github.com/nodejs/node/blob/main/doc/changelogs/CHANGELOG_V22.md
- Node.js — `node:test` runner (deferred — deep coverage in the nodejs-test-runner sibling): https://nodejs.org/api/test.html
