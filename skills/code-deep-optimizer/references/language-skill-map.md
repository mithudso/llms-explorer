> Reference for the code-deep-optimizer skill's Stage 0. Full language/framework/domain → reviewer-skill activation matrix. See SKILL.md "## Stage 0".

This is the authoritative lookup behind Stage 0's compact table (SKILL.md § 0.2). Stage 0 detects the languages, frameworks, and domains in the code under review and activates the matching reviewer skills, scoped to what was actually detected. Run detection once at repo scope, then per file scoped to that file's stack.

**Citation form matters.** Some activation targets are **top-level skills** — cite them by their bare kebab-case id (e.g. `lang-js-ts`), and they activate via the Skill tool when present in the session. Others are **reference files folded under a hub** — cite them as `hub-id (references/<file>.md)` (e.g. `software-engineering-patterns (references/code-reviewer.md)`), because a bare file name would not resolve at activation time. The matrix below uses the correct form per row; preserve it when editing.

## Detection signals

Priority-ordered (SKILL.md § 0.1, spec § 5.1). Earlier signals are more authoritative; later ones disambiguate or catch special shapes. Stop widening once the stack is unambiguous.

1. **File extensions and shebangs** — the fastest stack read.
   - JS/TS: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`
   - Python: `.py`; shebang `#!/usr/bin/env python3`
   - Go: `.go`
   - Kotlin: `.kt`, `.kts`
   - Rust: `.rs`
   - Node CLI scripts: shebang `#!/usr/bin/env node`

2. **Project manifests** — pin the language *and* its toolchain (the verify-gate commands key off these too).
   - JS/TS: `package.json`, `tsconfig.json`
   - Python: `pyproject.toml`, `requirements.txt`, `setup.cfg`, `setup.py`
   - Go: `go.mod`
   - Rust: `Cargo.toml`
   - JVM: `pom.xml`, `build.gradle(.kts)`
   - Ruby: `Gemfile`

3. **Framework / library imports in source** — promote a generic language to a domain.
   - React/JSX: `import React`, `.jsx`/`.tsx` markup, `from "react"`
   - Angular: `@Component`/`@Injectable`/`@NgModule` decorators, `@angular/*` imports
   - Node web frameworks: `express`, `fastify`, `@nestjs/*`, `hono`
   - Python web frameworks: `fastapi`, `django`, `flask`
   - MongoDB: `mongodb`, `mongoose`
   - AWS: `@aws-sdk/*`, `boto3`
   - Web Crypto: `crypto.subtle`

4. **Infra / config files** — non-source surfaces that still get reviewed.
   - Containers: `Dockerfile`, `docker-compose.yml`
   - Kubernetes: `*.yaml` manifests with `apiVersion:`/`kind:` (Deployment, Service, Ingress, etc.)
   - Terraform: `*.tf`
   - CI: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`

5. **Content sniffing for special shapes** — patterns no extension reveals.
   - Tampermonkey/Greasemonkey userscript: `// ==UserScript==` metadata header
   - Chrome MV3 extension: `manifest.json` containing `"manifest_version": 3`
   - Concurrency surfaces: `WebSocket`, `Worker`, `worker_threads`, `SharedArrayBuffer`
   - Crypto surfaces: `crypto.subtle`, `AES-GCM`, `PBKDF2`, `wrapKey`/`unwrapKey`

## Activation matrix

The **Feeds passes** column names which of the 18 fix-track passes the activated skill informs — `C1` correctness, `C2` interface/contract & types, `C3` adversarial bug-hunt, `S1` security, `S2` error/resources, `S3` input/trust, `S4` portability/runtime-compat, `S5` logging/observability, `P1` performance, `P2` concurrency/async, `M1` readability/standards, `M2` duplication, `M3` architecture, `M4` doc-correctness, `T1` tests, `T2` supply-chain, `T3` tooling-gap, `T4` test-suite performance. An activated reviewer sharpens those passes; it does not gate the others. (Advisory passes `A1`/`A2`/`A3` run only under `--suggest` — see the Advisory track section below.)

| Detected signal | Activate (skill or reference) | Feeds passes |
| --- | --- | --- |
| JavaScript / TypeScript (`.ts`/`.tsx`/`.js`/`.jsx`/`.mjs`/`.cjs`, `package.json`, `tsconfig.json`) | `lang-js-ts` | C1, C2, S2, P1, M1 |
| Heavy TS generics / conditional types (`infer`, mapped types, branded types, variadic tuples) | `lang-js-ts (references/typescript-advanced-types.md)` | C2 |
| Python (`.py`, `#!/usr/bin/env python3`, `pyproject.toml`/`requirements.txt`/`setup.cfg`) | `lang-python` | C1, C2, S2, P1, M1 |
| Go / Kotlin (`.go`+`go.mod`; `.kt`/`.kts`+Gradle) | `lang-go-and-mobile` | C1, C2, P2, M1 |
| Frontend / HTML / CSS / React markup (JSX/TSX, `@angular/*`, `.html`/`.css`) | `frontend-ui` | M1 (+ a11y, responsive) |
| Node async / streams / workers / event loop (`worker_threads`, `Worker`, streams, `WebSocket`) | `lang-js-ts (references/nodejs-concurrency-internals.md)` | P2, S2, C3 |
| Chrome extension — MV3 (`manifest.json` with `"manifest_version": 3`, content scripts, `chrome.*` APIs) | `chrome-extension-expert` | S1, S3, C1 |
| `crypto.subtle` / AES / PBKDF2 / key-wrapping (`wrapKey`/`unwrapKey`, IV/nonce handling) | `misc-catch-all (references/webcrypto-vault-reviewer.md)` | S1 |
| Auth / untrusted input / web app surface (sessions, login flows, external request handlers) | `security-review` | S1, S3, C3 |
| MongoDB / Atlas data-plane (`mongodb`/`mongoose`, MQL, aggregation, index design) | `mongodb-expert` (+ `mongodb-atlas-expert` for platform/control-plane) | C1, P1 |
| REST / GraphQL / gRPC API surface (route handlers, schemas, `.proto`, OpenAPI) | `software-engineering-patterns (references/api-design-patterns.md)` | C2, S3 |
| Kubernetes / Docker / CI (`Dockerfile`, k8s manifests, `.github/workflows/*.yml`) | `devops-containers-cicd` (+ its `references/kubernetes-networking.md` for k8s manifests) | S1, M3 |
| AWS SDK / IAM / Lambda (`@aws-sdk/*`, `boto3`, IAM policy JSON, SAM/CDK) | `aws-cloud` | S1, C1 |
| Dependency manifests & lockfiles (`package.json`/`package-lock.json`, `requirements.txt`/`poetry.lock`, `go.sum`, `Cargo.lock`) | `security-review` (supply-chain / compliance) | T2 |
| Test files / test runners (`*.test.*`, `*.spec.*`, `__tests__/`, vitest/jest/pytest config) | `software-engineering-patterns (references/testing-and-vitest-expert.md)` | T1, T4 |
| Logging / observability surfaces (logger calls, error/catch branches, external-call sites, state transitions) | `devops-observability` | S5 |
| Repo-level architecture (any multi-file repo — layering, module boundaries, dependency cycles) | `software-engineering-patterns (references/software-architect.md)` | M3 |
| Performance-critical paths (hot loops, N+1 queries, large-data processing, sync-blocking) | `software-engineering-patterns (references/performance-profiling-expert.md)` | P1 |
| Runtime/version constraints (`package.json` `engines`, browserslist, `// ==UserScript==` sandbox, SES/lockdown, CSP) | the matching language/runtime skill (e.g. `lang-js-ts`, `chrome-extension-expert`) | S4 |
| Documented public API / JSDoc / docstrings (or notably absent on exported symbols) | `technical-writing-craft` | M4 |
| Missing tooling config (no `eslint`/`tsconfig`/CI workflow/formatter/`pre-commit`/dependency pinning) | `repo-bootstrapper`, `devops-containers-cicd` (CI) | T3 |
| **Always-on baseline (every run)** | `software-engineering-patterns (references/code-reviewer.md + references/coding-standards.md)` | all passes incl. C3 |

**Optional reinforcements** (cite the same way; activate only when the row's signal is genuinely present):

- Backend service decomposition / framework selection (Express/Fastify/Nest/Hono, FastAPI/Django/Flask) → `software-engineering-patterns (references/backend-patterns.md)` → feeds C2, M3.
- Browser OAuth / OIDC / session-login flow design → `software-engineering-patterns (references/web-auth-patterns.md)` → feeds S1, S3.
- Hard-to-reproduce runtime defects / root-cause work uncovered mid-review → `software-engineering-patterns (references/debugging.md)` → feeds C1, S2.

## Advisory track (`--suggest`) — pass → skill

Advisory passes run only under `--suggest` (report-only; see SKILL.md § Advisory track and `references/advisory-track.md`):

- **A1 Feature / latent-intent** (per-file) — no fixed skill; grounds on in-code signals (TODO, missing `switch` case, stub, ignored arg). Pull a domain skill only when the signal is domain-specific (e.g. `api-design-patterns` for an API gap).
- **A2 Architecture & design recommendations** (repo) → `software-engineering-patterns (references/software-architect.md)`.
- **A3 Migration & deprecation roadmap** (repo) → the domain's operations skill (e.g. `mongodb-operations-expert` for MongoDB driver/server migrations, `devops-containers-cicd` for base-image/runtime EOL).

## Guardrails

- **Don't over-activate.** Scope activation to what was actually detected — six reviewers on a 40-line file is noise (the ddo guard, SKILL.md § 0.4). Activate a row only when its detection signal is present in the code under review, not because the language *could* host that domain.
- **Activation status feeds the Stage 0 block.** Record which skills activated and why; that block becomes the report's activated-skills list.
- **Status is blocking** when a security, crypto, or otherwise regulated domain is detected but no matching reviewer skill is available to load — the run must not silently skip a security review of security-sensitive code.
- **Status is minor** when a domain is detected but no skill exists for it at all — note the gap and proceed with the always-on baseline (`software-engineering-patterns (references/code-reviewer.md + references/coding-standards.md)`).
- **Status is pass/clean** when every detected domain has its reviewer activated.
