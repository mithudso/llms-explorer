---
title: "Node.js Application Security Hardening"
description: "This reference is the consolidated Node.js security playbook: the threats that"
---

# Node.js Application Security Hardening

## Overview

This reference is the **consolidated Node.js security playbook**: the threats that
are specific to running JavaScript on a server with full OS access, and the
defenses Node ships for them. It is organized threat → defense so you can go from
a symptom ("untrusted JSON reaches a merge", "user input reaches `child_process`")
straight to the mitigation.

Node's own **threat model** sets the boundary: Node trusts the code it is asked to
run and the OS environment it runs in. Everything here is about defending the line
between **trusted application code** and **untrusted external input** — request
bodies, query strings, JSON, transcripts, file paths, third-party packages. It is
*not* about sandboxing untrusted code (Node explicitly does not do that).

This file owns the *application-layer* attack surface. Several adjacent concerns
live in sibling references and are deferred, not duplicated:

- **Permission-Model mechanics** (the full `--allow-fs-read`/`--allow-net`/SEA
  flag matrix) → `nodejs-typescript-and-runtime-features`. Here we cover only
  *why* the model is defense-in-depth, not a sandbox.
- **Package-manager workflows** (lockfile/audit/workspace mechanics) →
  `nodejs-package-management-supply-chain`. Here we cover supply chain as *risk*.
- **HTTP security headers** (Helmet, CSP, HSTS, CORS) → `http-security-headers`.
- **Web Crypto / vault / encryption-at-rest** → `webcrypto-vault-reviewer`.
- **OAuth/OIDC/session auth flows** → `web-auth-patterns`.
- **Event-loop / ReDoS-*blocking* mechanics** → `nodejs-concurrency-internals`.
  Here we cover ReDoS only from the *defense* angle.

The mental model: **validate untrusted input at the boundary, deny shells and
dynamic eval, freeze what should be immutable, and treat every dependency as
untrusted code.** Defense-in-depth — no single flag makes a Node app safe.

## Core concepts

### 1. Prototype pollution (CWE-1321)

JavaScript objects inherit from `Object.prototype`. If an attacker can write a key
named `__proto__`, `constructor`, or `prototype` into an object built from
untrusted data, they mutate that shared prototype — and every object in the
process suddenly carries the injected property. The classic sink is an **insecure
recursive merge / deep-clone / `extend`** (CVE-2018-16487 in lodash) or a
**query-string parser** that auto-vivifies nested keys (`?__proto__[isAdmin]=1`).

```js
const data = JSON.parse('{"__proto__": { "polluted": true }}');
const c = Object.assign({}, { a: 1 }, data);
console.log(({}).polluted); // true  — every object is now polluted
```

**Impact:** ranges from logic corruption and DoS to privilege escalation and, via
a *gadget*, full RCE (a polluted `.env`/`.shell` property read by a later
`child_process` call — see concept 6).

**Defenses (layer them):**
- **Validate against a schema** (Ajv/zod) at the boundary — the strongest fix;
  reject unexpected keys with `additionalProperties: false`.
- Use **null-prototype objects** for dictionaries: `Object.create(null)` (no
  `__proto__` to pollute) or a **`Map`** instead of an object-as-dictionary.
- **`Object.freeze(MyClass.prototype)`** / `Object.freeze(Object.prototype)` to
  block writes to a specific prototype.
- **`--disable-proto=throw`** (or `=delete`) removes the `Object.prototype.__proto__`
  accessor process-wide — `throw` raises `ERR_PROTO_ACCESS` on access, `delete`
  removes it entirely.
- A **`JSON.parse` reviver** that drops `__proto__`/`constructor` keys; check
  ownership with `Object.hasOwn(obj, key)`, never inherited lookups.
- Avoid hand-rolled recursive merges on untrusted data; if unavoidable, skip the
  three magic keys explicitly.

### 2. Injection (command, path, eval, SQL/NoSQL)

**Command injection** is the highest-severity Node-specific sink.
`child_process.exec()` / `execSync()` **spawn a shell** (`/bin/sh`) and the Node
docs warn verbatim: *"Never pass unsanitized user input to this function. Any
input containing shell metacharacters may be used to trigger arbitrary command
execution."* Defense: prefer **`execFile()` or `spawn()`**, which run the binary
directly **without a shell by default**, and pass arguments as a **separate
array** (`spawn('git', ['log', userRef])`) so metacharacters are never parsed.
Keep **`shell: false`** (the default) — enabling `shell: true` re-introduces the
exact `exec` vulnerability. Never build a command string by concatenating input.

**`eval()` / `new Function()` / `vm` with untrusted strings** is direct RCE — OWASP
calls it inherently a remote-code-execution vulnerability. Don't evaluate user
input; use a parser/lookup table instead. `vm` is **not** a security sandbox.

**Path traversal:** untrusted input flowing into `fs.*` enables `../../etc/passwd`
file inclusion. Normalize with `path.resolve()`, then assert the result
`startsWith` the intended base directory; reject otherwise. Decode and strip
`..`/null bytes before use.

**SQL/NoSQL injection** lives at the app layer: always use **parameterized
queries / prepared statements** (driver placeholders), never string-built SQL. For
MongoDB, reject object-typed values where a scalar is expected (`{$gt:''}`
operator injection from query strings) and cast inputs to their expected type.

### 3. Hardening flags & runtime defenses

Node ships process-level flags that shrink the attack surface as **defense-in-depth**:

| Flag | Effect | Note |
| --- | --- | --- |
| `--frozen-intrinsics` | Recursively freezes built-ins (`Array`, `Object`, prototypes) so monkey-patching (CWE-349) fails with a `TypeError`. | Experimental; root context only; `--require`/`--import` run *before* freezing so polyfills can load. |
| `--disable-proto=throw\|delete` | Removes/poisons `Object.prototype.__proto__` (see concept 1). | `throw` → `ERR_PROTO_ACCESS`. |
| `--secure-heap=n` | Allocates an OpenSSL secure heap (size `n`) for key material, guarding against some memory-disclosure reads (CWE-284). | Not on Windows; `--secure-heap-min` sets the min allocation. |
| `--permission` | Enables the **Permission Model** — denies fs/net/child-process/etc. unless explicitly granted. | See below — *seat belt, not sandbox*. |

The **Permission Model is defense-in-depth, not a security boundary.** The Node
docs are explicit: *"The permission model implements a 'seat belt' approach …
It does not provide security guarantees in the presence of malicious code.
Malicious code can bypass the permission model and execute arbitrary code."* It
*"trusts any code it is asked to run."* So `--permission` is useful to prevent
*trusted* code (and its dependencies) from *accidentally* touching the filesystem
or network — a containment layer, not a jail for untrusted code. (The
`--allow-*` flag matrix, scoping, and SEA mechanics are deferred to
`nodejs-typescript-and-runtime-features`.) Also: don't enable experimental
features in production unless you accept the breaking-change risk.

### 4. Secrets & configuration hygiene

- **Keep secrets in the environment, not in source.** Read from `process.env`;
  never commit `.env` files or hard-coded API keys/tokens (CWE-552). Add `.env` to
  `.gitignore` and use an allowlist (`files` in `package.json`, `.npmignore`) so a
  `npm publish` doesn't leak them — verify with `npm publish --dry-run`.
- **`--env-file` caveat:** `--env-file=.env` loads vars into `process.env`, *and it
  also parses Node-configuring vars like `NODE_OPTIONS`*. The docs warn Node *"will
  not sanitize or perform validation on the user-provided configuration, so NEVER
  use untrusted configuration files."* A writable `.env` is therefore a code-exec
  vector (it can inject `NODE_OPTIONS`). `--env-file` is also **not** subject to
  Permission-Model restrictions. Use a real secrets manager for production.
- **Never put secrets in logs or error responses.** Redact tokens/passwords/keys
  before logging; don't echo stack traces or `err.message` containing connection
  strings to clients. Centralize redaction in the logger.
- **`process.env` hygiene:** read each secret once at startup into a typed config
  object; don't pass the whole `process.env` into child processes or templates
  (a prototype-pollution gadget can poison it — concept 6).

### 5. Dependency & supply-chain risk (CWE-1357)

Most of a Node app's code is third-party and runs with full privilege. Treat the
dependency tree as an attack surface:

- **`npm audit` + CVE response:** scan regularly; for a flagged CVE, upgrade to the
  fixed version (or apply an override) and re-test. Don't ignore transitive
  advisories.
- **Install-script risk:** `postinstall`/`preinstall` scripts run arbitrary code at
  install time. For untrusted or audited installs use **`npm install
  --ignore-scripts`** (or `npm config set ignore-scripts true`) and allowlist the
  few packages that legitimately need a build step.
- **Dependency confusion:** if your build resolves from both a private and the
  public registry, an attacker can publish a public package with your *internal*
  name and win. Defense: **publish internal packages under an `@your-scope/`**,
  register that scope publicly even if unused, and pin the scope to the private
  registry in `.npmrc` (`@your-scope:registry=…`).
- **Lockfile integrity:** commit `package-lock.json` (it records exact versions
  *and* the resolved registry + integrity hash) and install with **`npm ci`**,
  which fails on any lockfile/`package.json` mismatch. Guard against lockfile
  poisoning in review. (Lockfile/workspace *workflow* mechanics →
  `nodejs-package-management-supply-chain`.)
- **Keep Node patched:** track Node.js **security releases** and run a supported
  (Active LTS or Maintenance) line; EOL versions get no security fixes.

### 6. Request-layer risks (SSRF, ReDoS, smuggling, deserialization)

- **SSRF (server-side request forgery):** any server-side `fetch`/`undici`/`http`
  call to a **user-controlled URL** can be steered at internal services or the
  cloud **metadata endpoint `169.254.169.254`** to steal credentials. Node's
  built-in fetch has no SSRF guard. Defense: **allowlist** permitted hosts/schemes;
  **resolve the hostname to IP and reject private/reserved ranges**
  (loopback/private/link-local/ULA/IPv4-mapped) *before* connecting; **disable or
  re-validate redirects** (a 302 can point inward); beware DNS-rebinding/TOCTOU —
  validate at connect time (libraries: `request-filtering-agent`, `ssrf-req-filter`).
- **ReDoS (regex denial-of-service):** a regex with catastrophic backtracking
  (nested quantifiers like `(a+)+$`, overlapping alternations) hangs on a crafted
  input. *Defense angle:* avoid such patterns, **cap input length**, prefer a
  linear engine (**RE2** / `node:re2`), and screen patterns with `safe-regex` /
  `vuln-regex-detector`. (*Why* it stalls the whole process — the event-loop
  blocking mechanics — is in `nodejs-concurrency-internals`.)
- **HTTP request smuggling (CWE-444):** ambiguous `Content-Length`/`Transfer-Encoding`
  framing lets a request slip past a front-end. Don't set
  **`insecureHTTPParser: true`**; normalize at the proxy; prefer end-to-end HTTP/2.
- **Unsafe deserialization:** `JSON.parse` is safe for data, but libraries that
  deserialize *functions* (e.g. **`node-serialize` ≤0.0.4** `unserialize()`) execute
  attacker-supplied **IIFE** payloads → RCE. Never deserialize untrusted input with a
  function-capable format; restrict to JSON + schema validation.

## Threat → defense table

| Threat | Node-specific sink | Primary defense |
| --- | --- | --- |
| Prototype pollution | recursive merge / clone, query parser, `JSON.parse` | schema validation; `Object.create(null)` / `Map`; `--disable-proto=throw`; `Object.freeze`; reviver |
| Command injection | `child_process.exec`/`execSync`, `shell:true` | `execFile`/`spawn` with arg array, `shell:false`; never concatenate |
| Eval/code injection | `eval`, `new Function`, `vm` | never eval input; parser/lookup; `vm` ≠ sandbox |
| Path traversal | `fs.*` with user path | `path.resolve` + base-dir `startsWith` check |
| SQL/NoSQL injection | string-built queries, object operators | parameterized queries; type-cast/reject operator objects |
| Monkey-patching | mutated intrinsics | `--frozen-intrinsics`; `Object.freeze(globalThis)` |
| Secret leakage | source, logs, `--env-file` | env-only secrets; `.gitignore`/`files`; redact logs; no untrusted `.env` |
| Supply chain | install scripts, dep confusion, stale deps | `--ignore-scripts`, scoped pkgs, `npm ci` + lockfile, `npm audit`, patch Node |
| SSRF | server-side `fetch`/`undici` to user URL | host allowlist; block private IPs; validate redirects/DNS |
| ReDoS | catastrophic-backtracking regex | RE2/linear engine; input-length cap; `safe-regex` |
| Request smuggling | `insecureHTTPParser`, ambiguous framing | leave parser strict; normalize at proxy; HTTP/2 |
| Unsafe deserialization | `node-serialize` `unserialize()` | JSON + schema only; no function-capable formats |

## Practical patterns

- **Validate at the boundary, once.** Run every external payload through an Ajv/zod
  schema with `additionalProperties:false` *before* it touches business logic — this
  closes prototype pollution, type-confusion NoSQL injection, and oversized-field
  abuse in one place.
- **Ban the shell.** Lint for `child_process.exec`/`execSync` and `shell:true`;
  standardize on `execFile`/`spawn` with argument arrays.
- **Run with `--disable-proto=throw`** (cheap, high-value) and consider
  `--frozen-intrinsics` once you've confirmed your polyfills load via `--require`.
- **Wrap untrusted text** (transcripts, Slack, case bodies, anything fed to an LLM
  or template) in an escaped envelope so it can't be interpreted as control input —
  the same discipline as parameterizing a query.
- **Gate outbound URLs** through a single SSRF-filtering agent so no code path can
  fetch an arbitrary user URL directly.
- **`npm ci` in CI**, `--ignore-scripts` for untrusted installs, and a scheduled
  `npm audit` + Node-version check so patch cadence isn't manual.

## Anti-patterns

- **Deep-merging untrusted JSON** with a hand-rolled or old-lodash `merge` and no
  schema — the #1 prototype-pollution foothold.
- **`child_process.exec('cmd ' + userInput)`** or flipping `shell:true` "to make it
  work" — arbitrary command execution.
- **`eval`/`new Function` on request data**, or trusting `vm` as a sandbox.
- **Committing `.env`**, logging full error objects with secrets, or loading an
  **untrusted `--env-file`** (it can inject `NODE_OPTIONS`).
- **Treating `--permission` as a sandbox** for untrusted code — it is a seat belt
  for *trusted* code; malicious code bypasses it.
- **Fetching a user-supplied URL** server-side with no allowlist / private-range
  block — SSRF to `169.254.169.254`.
- **`node-serialize.unserialize()`** (or any function-deserializing format) on
  untrusted input — instant RCE.
- **Running an EOL Node version** or ignoring `npm audit` advisories.

## Troubleshooting

- **Prototype pollution slipped through schema validation** → the validator ran
  *after* the merge, or allowed `additionalProperties`; validate first and set
  `additionalProperties:false`. Confirm with `({}).polluted === undefined` after the
  request.
- **`--frozen-intrinsics` breaks a dependency** → a library mutates a built-in; load
  required polyfills via `--require`/`--import` (they run before the freeze) or drop
  the flag for that service — it's experimental and root-context only.
- **`execFile` still runs a shell** → you passed `shell:true` or a single
  command-line string; pass the binary + an args array with `shell:false`.
- **SSRF filter bypassed** → likely DNS rebinding (TOCTOU) or an IPv6-mapped/redirect
  bypass; re-validate the resolved IP at connect time and disallow redirects to new
  hosts.
- **Regex still hangs after switching libraries** → the pattern is still
  backtracking-prone; move to RE2 (linear) and cap input length. For *why* one
  blocked regex freezes all requests, see `nodejs-concurrency-internals`.
- **`npm audit` flags a transitive dep with no direct fix** → use an `overrides`
  entry to force the patched version, then re-audit and test.

## References

- Node.js — Security best practices (prototype pollution, monkey-patching, secure heap, HTTP smuggling, supply chain, permission model, secrets): https://nodejs.org/en/learn/getting-started/security-best-practices
- Node.js — CLI flags (`--frozen-intrinsics`, `--disable-proto`, `--secure-heap`, `--permission`, `--env-file`): https://nodejs.org/api/cli.html
- Node.js — Permission Model ("seat belt" / not-a-sandbox, threat model, limitations): https://nodejs.org/api/permissions.html
- Node.js — `child_process` (exec vs execFile/spawn, `shell` option, shell-injection warning): https://nodejs.org/api/child_process.html
- OWASP — Node.js Security Cheat Sheet (command injection, eval, path traversal, ReDoS, request-size limits): https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html
- OWASP — SSRF Prevention in Node.js (allowlist, private-range block, metadata endpoint): https://owasp.org/www-community/pages/controls/SSRF_Prevention_in_Nodejs
- Snyk — Preventing insecure deserialization in Node.js (`node-serialize`, IIFE RCE): https://snyk.io/blog/preventing-insecure-deserialization-node-js/
- Snyk — Detect and prevent dependency confusion attacks on npm: https://snyk.io/blog/detect-prevent-dependency-confusion-attacks-npm-supply-chain-security/
- nodejs/undici — SSRF protection in undici / native fetch (no built-in guard): https://github.com/nodejs/undici/issues/2019
- OWASP — Prototype Pollution Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html
