---
title: "Node.js Built-in Test Runner (node:test deep features)"
description: "This reference is about using node:test as a real test framework — the depth"
---

# Node.js Built-in Test Runner — Deep Feature Surface

## Overview

This reference is about using **`node:test` as a real test framework** — the depth
that lets it stand in for Jest or Mocha: nested subtests, lifecycle hooks, a full
mocking system (functions, methods, properties, timers, modules), built-in coverage
with failing thresholds, pluggable reporters, a CLI filtering/sharding/isolation
model, and snapshot testing. It assumes you already know how to write one
`test(name, fn)`.

It is the "now build a suite" companion to three siblings that own neighbouring layers:

- **`javascript-nodejs`** — owns the *intro*: your first `test()`, `assert.strict`
  basics, ESM/CJS module syntax. This file does **not** re-teach the first test or the
  primitives of `assert`.
- **`software-engineering-patterns`** — owns the *third-party* runners **Vitest** and
  **Jest** (Vitest's `vi` mocks, Jest matchers, Jest→Vitest migration). This file is
  the *built-in* runner only; reach there if the project uses a framework.
- **`nodejs-builtin-modules-modern`** — owns the *generic* `--watch` flag and the rest
  of the batteries-included surface (`node:util` `parseArgs`, etc.). This file covers
  `--watch` only as a test re-run mode.

The mental model: `node:test` is **TAP-emitting and isolation-by-default**. The
`test()` function and the `TestContext`/`MockTracker` objects are the API; the `--test*`
CLI flags are the *runner* that discovers files, isolates them in child processes,
filters by name, and aggregates reporters — both halves matter. Two `import` surfaces:
functions come from `node:test` (`test`, `describe`, `it`, `before`, `mock`, …); reporter
classes from `node:test/reporters` (`spec`, `tap`, `lcov`, …). The runner is **stable
since Node.js 20** (coverage thresholds and snapshots stabilized later — noted per feature).

## Core concepts

### 1. Test structure: test / describe / it, subtests, and the `TestContext`

`test(name, options?, fn)` registers a test; `fn` receives a `TestContext` named `t`
(and may be `async`, or use the second `done` callback for callback-style). `describe()`
(alias `suite()`) groups tests and `it()` (alias of `test`) reads naturally inside it —
`describe`/`it` is the BDD style, bare `test()` the flat style. Both compose.

- **Subtests**: call **`t.test(name, fn)`** to nest a test *inside* a parent test. The
  parent **must `await`** its subtests (or `await Promise.all([...])`) — an un-awaited
  subtest is cancelled when the parent finishes and reported as failing. This is the
  single most common node:test mistake.
- **The `TestContext` `t`** exposes:
  - `t.diagnostic(message)` — emit a TAP diagnostic line (not an assertion).
  - `t.plan(count, options?)` — assert that exactly `count` assertions/subtests run;
    `{ wait }` can wait for asynchronous assertions. The test fails if the count is off.
  - `t.skip(message?)` / `t.todo(message?)` — mark the running test skipped/todo at
    runtime; `t.runOnly(bool)` enables only-mode for *this context's* subtests.
  - `t.signal` — an `AbortSignal` aborted on timeout/cancellation; pass it into
    `fetch`/timers so work cancels with the test. `t.name`, `t.fullName`, `t.filePath`
    identify the test.
  - `t.waitFor(fn, options?)` — poll `fn` until it stops throwing (for eventually-true
    conditions), with `interval`/`timeout`.
  - `t.assert` — per-test assertion methods (see §7); `t.mock` — a per-test
    `MockTracker` (see §2) that auto-restores after the test.
- `describe`/`suite` callbacks get a `SuiteContext` (`signal`, `name`) rather than a
  `TestContext`.

### 2. Lifecycle hooks: before / after / beforeEach / afterEach

Four hooks, importable as top-level functions or callable as `t.before*`:

- `before(fn, options?)` / `after(fn, options?)` — run **once** per suite (file or
  `describe` block), around all its tests. `after` runs even if tests fail.
- `beforeEach(fn, options?)` / `afterEach(fn, options?)` — run around **each** test in
  the current suite; `afterEach` runs even when the test fails (use it for teardown).
- **`HookOptions`**: `{ signal, timeout }` — abort/limit a slow hook independently of
  the tests. Hooks receive the test/suite context as their argument.
- Hooks **nest**: an outer `describe`'s `beforeEach` runs before each test in nested
  `describe`s too. Scope hooks to a block by declaring them inside that `describe`, or
  per-test via `t.beforeEach()`.

### 3. Mocking functions, methods, getters/setters, and properties

The `MockTracker` (`import { mock } from 'node:test'`, or per-test `t.mock`) creates
spies/stubs and tracks calls. Top-level `mock` persists across tests — call
`mock.reset()`/`mock.restoreAll()` (or prefer `t.mock`, which auto-restores).

- **`mock.fn(original?, implementation?, options?)`** — a mock function; without args
  it's a no-op spy. `options.times` lets `implementation` apply for the first N calls
  then fall back to `original`.
- **`mock.method(object, methodName, implementation?, options?)`** — replace a method
  in place while spying; restored on `restore()`. `mock.getter()` / `mock.setter()`
  mock an accessor; **`mock.property(object, propertyName, value?)`** (Node 24+) mocks a
  plain data property's reads/writes.
- **Introspection — the `MockFunctionContext` at `someMock.mock`**:
  - `mock.calls` — array of call records (`{ arguments, result, error, this, stack }`).
  - `mock.callCount()` — number of invocations.
  - `mock.mockImplementation(fn)` / `mock.mockImplementationOnce(fn, onCall?)` — swap the
    implementation, permanently or for one (specific) call.
  - `mock.resetCalls()` — clear recorded calls; `mock.restore()` — undo this one mock.

### 4. Mocking time: `mock.timers`

`mock.timers` fakes timers and `Date` so time-dependent code is deterministic and fast.

- **`mock.timers.enable({ apis, now })`** — turn on faking for the chosen `apis`:
  `setTimeout`, `setInterval`, `setImmediate`, `Date`, and `scheduler.wait`. Faked APIs
  cover the globals **and** `node:timers` + `node:timers/promises`. `now` seeds the
  starting time (number or `Date`).
- **`mock.timers.tick(ms)`** — advance fake time by `ms`, synchronously firing every
  timer that would have elapsed (and moving the faked `Date`). `runAll()` fires all
  pending timers and jumps to the last one's time. **`setTime(ms)`** sets the current
  faked `Date` without running timers.
- **`mock.timers.reset()`** — clear scheduled timers and restore real ones (also done by
  `mock.reset()` / disable). Faking `Date` makes `Date.now()` / `new Date()` follow the
  mock clock.

### 5. Module mocking: `mock.module()` (experimental)

**`mock.module(specifier, options?)`** replaces a module's exports for code imported
*after* the mock is installed — covering ESM, CommonJS, JSON, and builtin modules.
**Requires the `--experimental-test-module-mocks` flag** (and the API is experimental).

- `options`: `namedExports` (object of named exports), `defaultExport` (the default),
  and `cache` (default `false` — by default the module is freshly evaluated and the
  real cache is untouched; references obtained *before* mocking are not affected).
- Because mocks apply to subsequent loads, the module under test must be brought in via
  **dynamic `import()` after** the `mock.module()` call (static top-level imports are
  already resolved). The mock is reverted by `restore()` / `restoreAll()`.

### 6. Coverage, reporters, and the filtering / execution model

**Coverage.** Start with **`--experimental-test-coverage`** to collect and print line/
branch/function coverage after the run. **Thresholds are stable (Node 22.8+)**:
`--test-coverage-lines=<pct>`, `--test-coverage-branches=<pct>`,
`--test-coverage-functions=<pct>` make the process **exit non-zero** when coverage is
below target. `--test-coverage-exclude=<glob>` / `--test-coverage-include=<glob>` tune
scope; `node_modules/`, core modules, and the matched **test files themselves are
excluded by default**. Emit a real report with the **lcov** reporter (below) for CI.

**Reporters** (`node:test/reporters`): **`spec`** (human-readable, the CLI default on a
TTY), **`tap`** (TAP, the default when piped), **`dot`** (compact `.`/`X`), **`junit`**
(JUnit XML for CI), and **`lcov`** (an `lcov.info` file, only meaningful with
`--experimental-test-coverage`). Select with **`--test-reporter`** and route output with
**`--test-reporter-destination`** (`stdout` or a file). The two flags pair positionally,
so you can run **several at once** — e.g. spec to the terminal and junit to a file.
A **custom reporter** is any module default-exporting a function/stream that consumes the
`TestsStream` events (`test:pass`, `test:fail`, `test:diagnostic`, `test:coverage`, …).

**Filtering & execution.** `node --test` discovers files by default globs: `*.test.*`,
`*-test.*`, `*_test.*`, files named `test.*`, files starting with `test-`, and **any
`.js/.cjs/.mjs` under a `test/` directory** (recursively). You can instead pass quoted
glob args. Filter by name with **`--test-name-pattern`** (regex; tests whose name
matches run) and **`--test-skip-pattern`** (regex; matches are skipped) — supply both
and a test must satisfy both. **`only`-mode**: mark `test('x', { only: true }, …)` (or
`t.runOnly(true)`) and run with **`--test-only`** to execute just those.
**`--test-concurrency`** caps parallel *files* (default `availableParallelism() - 1`).
**`--test-isolation`** chooses `process` (default — each file in its own child process,
crash-isolated) or `none` (all files in one process; faster, shares state, forces
concurrency 1). **`--test-shard=<i>/<n>`** runs only the i-th of n shards for splitting
across machines (incompatible with watch). **`--watch`** with `--test` re-runs affected
tests on file change (generic `--watch` semantics live in
`nodejs-builtin-modules-modern`).

### 7. Snapshots and assertions

- **Snapshot testing (stable, Node 22.3+ / marked stable later):** `t.assert.snapshot(value, options?)`
  compares `value` to a stored snapshot. Generate/update snapshots by running with
  **`--test-update-snapshots`**; the snapshot file defaults to `<testfile>.snapshot`.
  Customize **serializers** via `options.serializers` (array of `value => string`
  functions, applied in order) and relocate files with
  `snapshot.setResolveSnapshotPath()` / set global serializers with
  `snapshot.setDefaultSnapshotSerializers()`.
- **Assertions:** `node:test` integrates **`node:assert/strict`** — use
  `assert.strictEqual`, `assert.deepStrictEqual`, `assert.throws`, `assert.rejects`,
  `assert.match`, etc. Inside a test, prefer **`t.assert.*`** (the same `assert` methods,
  plus `t.assert.snapshot`): assertions made through `t.assert` are counted by `t.plan()`
  and attributed to the test in the reporter output.

## Key APIs / flags

| API / flag | Purpose | Notes |
| --- | --- | --- |
| `test` / `it` / `describe`(`suite`) | Register tests / suites | `it`=alias of `test`; `describe` groups |
| `t.test(name, fn)` | Subtest | **must be awaited** by the parent |
| `before`/`after`/`beforeEach`/`afterEach` | Lifecycle hooks | options `{ signal, timeout }`; `afterEach`/`after` run on failure |
| `t.plan` / `t.diagnostic` / `t.signal` | Assertion count / log / cancel | `t.signal` aborts on timeout |
| `skip` / `todo` / `only` (option or `t.*`) | Per-test control | `only` needs `--test-only` |
| `mock.fn` / `mock.method` / `mock.getter`/`setter` / `mock.property` | Spies & stubs | `mock.property` Node 24+ |
| `<m>.mock.calls` / `callCount()` / `mockImplementation(Once)` / `resetCalls()` / `restore()` | Mock introspection | `MockFunctionContext` |
| `mock.timers.enable({apis,now})` / `tick` / `runAll` / `setTime` / `reset` | Fake timers + Date | apis: setTimeout/Interval/Immediate, Date, scheduler.wait |
| `mock.module(spec, {namedExports,defaultExport,cache})` | Module mocking | `--experimental-test-module-mocks`; load target via dynamic `import()` after |
| `--experimental-test-coverage` | Collect coverage | print after run |
| `--test-coverage-lines/-branches/-functions=<pct>` | Failing thresholds | stable (≥22.8); non-zero exit below target |
| `--test-coverage-exclude` / `-include` | Coverage scope | node_modules + test files excluded by default |
| `--test-reporter` / `--test-reporter-destination` | Pick + route reporter | pair positionally → multiple reporters |
| `spec` / `tap` / `dot` / `junit` / `lcov` | Built-in reporters | from `node:test/reporters` |
| `--test-name-pattern` / `--test-skip-pattern` | Filter by name | regex; both = AND |
| `--test-concurrency` / `--test-isolation` | Parallelism / isolation | isolation `process`(default)\|`none` |
| `--test-shard=<i>/<n>` / `--watch` | Shard / re-run | shard ⊥ watch |
| `t.assert.snapshot` / `--test-update-snapshots` | Snapshots | `<file>.snapshot`; custom serializers |

## Practical patterns

- **Always `await` subtests** (`await t.test(...)`, or `await Promise.all([...])` for
  parallel siblings) so they're counted and not orphaned.
- **Prefer `t.mock` over the global `mock`** — per-test mocks auto-restore at test end,
  so you never leak a stub into the next test.
- **Pass `t.signal` into async work** (`fetch(url, { signal: t.signal })`, timers) so a
  timeout actually cancels the in-flight operation instead of leaking it.
- **Fake timers for time-logic**: `t.mock.timers.enable({ apis: ['setTimeout','Date'] })`
  then `tick()` to drive debounce/retry/TTL code deterministically — no real waiting.
- **CI reporter combo**: `node --test --experimental-test-coverage
  --test-reporter=spec --test-reporter-destination=stdout
  --test-reporter=junit --test-reporter-destination=junit.xml
  --test-reporter=lcov --test-reporter-destination=lcov.info` — human output, a JUnit
  artifact, and an lcov file in one run.
- **Gate merges on coverage**: add `--test-coverage-lines=80 --test-coverage-branches=75
  --test-coverage-functions=80`; the non-zero exit fails the job.
- **Shard wide suites across CI machines**: `--test-shard=1/4 … 4/4` on four runners.

## Anti-patterns

- **Un-awaited subtests** — the parent finishes, the subtest is cancelled and reported
  as failing. The #1 node:test footgun.
- **Reusing the global `mock` without restoring** — stubs bleed across tests; use
  `t.mock` or call `mock.restoreAll()` in `afterEach`.
- **Static-importing the module you intend to `mock.module()`** — the import already
  resolved before the mock installed; import it dynamically *after* mocking.
- **Forgetting `--experimental-test-module-mocks`** — `mock.module()` silently does
  nothing (or throws) without the flag.
- **Treating `--experimental-test-coverage` as a gate** — collection alone never fails
  the build; you need the `--test-coverage-*` *threshold* flags for that.
- **Real timers / real sleeps in tests** — slow and flaky; fake them with `mock.timers`.
- **`--test-isolation=none` while expecting per-file isolation** — all files share one
  process and global state; a leak in one file corrupts others.
- **Reaching for Jest/Vitest mocking idioms** (`jest.fn`, `vi.mock`) here — wrong API;
  those frameworks are a `software-engineering-patterns` concern.

## Troubleshooting

- **Subtest "was cancelled" / counts wrong** → `await` the `t.test()` call (or the
  `Promise.all` of them); check `t.plan()` matches the real assertion count.
- **`mock.module()` has no effect** → confirm `--experimental-test-module-mocks` is set
  *and* the target is loaded by dynamic `import()` after the mock.
- **Timer mocks don't fire** → you didn't `tick()`/`runAll()`, or the API wasn't in the
  `enable({ apis })` list; remember faking covers `node:timers/promises` too.
- **Coverage report empty / not failing** → `--experimental-test-coverage` only prints;
  add `--test-coverage-lines/-branches/-functions` to fail, and check
  `--test-coverage-exclude` didn't exclude your sources (test files are excluded by
  default).
- **No JUnit/lcov file written** → each `--test-reporter` needs its own paired
  `--test-reporter-destination`; lcov also requires `--experimental-test-coverage`.
- **Tests not discovered** → the file doesn't match the default globs and isn't under a
  `test/` dir; rename to `*.test.js` or pass a quoted glob to `--test`.
- **`--test-name-pattern` skips everything** → it's a regex over the *full* test name;
  with `--test-skip-pattern` both must pass. Anchor/escape as needed.
- **Snapshot always fails** → first run needs `--test-update-snapshots` to create the
  baseline; non-deterministic values (dates, ids) need a custom `serializers` entry.

## References

- Node.js — Test runner (`node:test`: test/describe/it, hooks, TestContext, MockTracker, mock.timers, mock.module, snapshots, coverage, reporters): https://nodejs.org/api/test.html
- Node.js — Command-line API (`--test`, `--test-name-pattern`, `--test-skip-pattern`, `--test-only`, `--test-concurrency`, `--test-isolation`, `--test-shard`, `--experimental-test-coverage`, `--test-coverage-lines/-branches/-functions`, `--test-coverage-exclude/-include`, `--test-reporter`, `--test-reporter-destination`, `--experimental-test-module-mocks`, `--test-update-snapshots`): https://nodejs.org/api/cli.html
- Node.js Learn — Using Node.js's test runner (structure, file discovery, watch, only): https://nodejs.org/learn/test-runner/using-test-runner
- Node.js Learn — Mocking in tests (mock.fn/method/getter/setter, mock.timers, mock.module): https://nodejs.org/learn/test-runner/mocking
- Node.js Learn — Collecting code coverage (flags, thresholds, lcov): https://nodejs.org/learn/test-runner/collecting-code-coverage
- Node.js — `node:test/reporters` (spec, tap, dot, junit, lcov, custom reporters): https://nodejs.org/api/test.html#test-reporters
