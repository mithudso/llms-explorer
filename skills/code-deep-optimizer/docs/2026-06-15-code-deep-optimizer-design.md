> **SUPERSEDED — historical planning artifact, not current behavior.**
> Written 2026-06-15 against a 12-then-16-pass design. The shipped skill has run **18 passes**
> (C1–C3, S1–S5, P1–P2, M1–M4, T1–T4) since v1.7.0 (2026-07-20), and since v1.9.0 (2026-09-09)
> also carries a Stage 0.5 injection gate, streaming-checkpoint crash recovery, a flag-interaction
> table, and the `--quick` triage mode. Neither this document nor its amendment describes S5
> (logging/observability), T4 (test-suite performance), empirical mode, or `--quick`.
> **SKILL.md is the only source of truth.** Kept for design rationale only.

# Code Deep Optimizer — Design Spec

- **Date:** 2026-06-15
- **Status:** Approved (design); pending spec review → implementation plan
- **Author:** Claude (brainstorming session with mitch)
- **Artifact under design:** a new skill `code-deep-optimizer` + `/cdo` command, the code-facing
  sibling of the existing iterative-optimizer family.

---

## 1. Context & motivation

The skill ecosystem already has three iterative "deep optimizer" siblings, each a multi-pass
review-and-fix loop that runs to convergence and cites one shared contract:

| Artifact | Skill | Command |
| --- | --- | --- |
| Prose documents | `document-critique` | `/ddo` |
| Production prompts | `prompt-deep-optimizer` | `/pdo` |
| Skill files | `skill-optimizer` | `/sko` |
| **Source code** | **`code-deep-optimizer` (this spec)** | **`/cdo`** |

Code is the missing fourth corner. The user asked for a deep code optimizer that "does a
multi-stage review of a code file or repo, automatically detects and loads the language-specific
skills, and repeats until all medium and higher findings are resolved."

**Shared infrastructure that already exists and must be reused (cite, never restate):**

- `~/.claude/skill-consolidation/convergence-and-severity.md` — canonical severity ladder, the 7
  exit conditions, and the guardrails (blocked findings, intent-drift guard, injection guard,
  evidence rule, demotion guard, blind re-audit gate, pre-write snapshot, cross-model gate).
- `~/.claude/skill-consolidation/convergence_check.py` — computes no-progress / stable-rewrite /
  loop-instability verdicts from two artifact versions + model-counted severity totals.
- `~/.claude/skill-consolidation/cross-model-gate.md` — optional `--cross-model` independence gate.
- `~/.claude/skill-consolidation/backups/<target>-<ts>/` — central pre-write snapshot directory.
- `~/.claude/skill-consolidation/optimizer-telemetry.jsonl` — per-pass telemetry sink.

**Distinct from the built-in `/code-review` command.** `/code-review` reviews a *git diff* once
(with an `ultra` cloud multi-agent mode). `code-deep-optimizer` is a *file/repo* deep optimizer
with a convergence loop, automatic language/domain skill loading, and a build/lint/test verify
gate. They compose; the skill's `SKIP:` clause points quick one-shot diff reviews to `/code-review`.

---

## 2. Goals / non-goals

**Goals**

1. Multi-stage static review of a single file or a whole repo, in the same structural style as the
   three sibling optimizers.
2. Automatically detect the languages/frameworks/domains present and activate the matching reviewer
   skills, feeding them into the relevant passes.
3. Apply every Medium-or-higher fix in place, then verify by running the project's build/lint/tests,
   backing out any fix that regresses the suite.
4. Loop to convergence using the canonical contract (cap, exit conditions, blind re-audit,
   optional cross-model gate).
5. Ship as a full family member: shared contract + reused infra + `/cdo` command + peer-deferral
   edges + hub/registry sync.

**Non-goals**

- Not a replacement for `/code-review` (one-shot diff review stays there).
- Not a linter/formatter reimplementation — it *runs* the project's existing tools, it doesn't
  reimplement them.
- Not a test generator (it flags missing tests; authoring net-new suites is a downstream task).
- No new convergence/severity model — it inherits the canonical one.

---

## 3. Decisions (locked with the user)

| # | Decision | Choice |
| --- | --- | --- |
| D1 | Default apply mode | **Apply + verify in place** (snapshot → apply Medium+ → run tests → back out regressions → loop). Report-only available via `--read-only`/`--report`. |
| D2 | Verify gate | **Auto-detect & run build/lint/tests each iteration**; graceful N/A when none exist. `--no-verify` / `--verify-end` available. |
| D3 | Repo scope | **Whole repo, triaged** (index all sources, prioritize by risk × size, fan out per file up to a cap). `--scope=changed|<paths>` overrides. |
| D4 | Integration depth | **Full family member** — shared contract, reused infra, `/cdo`, peer-edge seeding, hub sync. |
| D5 | Name | `code-deep-optimizer` skill, `/cdo` command (parallels `prompt-deep-optimizer`/`/pdo`). |

**Defaults chosen for the three open questions raised at design review** (user said "go ahead",
leaving these to sensible defaults — stated here explicitly per the spec ambiguity check):

- **(a) Pass set:** 12 passes in 5 groups (§6). Accessibility and i18n are *not* standalone passes;
  they ride along when `frontend-ui` activates in Stage 0 (YAGNI — promotable to passes later).
- **(b) Repo triage cap:** default **soft cap 50 files per run**, overridable via `--max-files=N`;
  truncation is always disclosed and the dropped-but-prioritized remainder is emitted as a
  ready-to-run follow-up (`/cdo <path> --scope=<next-batch>`). No silent caps.
- **(c) Verify-gate backout:** **bounded bisect** — back out the highest-risk / most-recently-applied
  fix first, re-run; escalate to backing out the iteration's batch only if a small bisect budget
  (default 3 probes) is exhausted (§7).

---

## 4. Deliverables & file layout

```
~/.claude/skills/code-deep-optimizer/
  SKILL.md                          # lean (< ~6k-token soft budget); the procedure + calibration table
  references/
    language-skill-map.md           # full language/framework/domain → reviewer-skill activation matrix
    worked-example.md               # one end-to-end run (single JS/TS file) showing the output format
  docs/
    2026-06-15-code-deep-optimizer-design.md   # this spec
~/.claude/commands/cdo.md           # thin shim: invoke the skill against $ARGUMENTS, flags included
```

`SKILL.md` carries the procedure, the small severity *calibration table* (citing the contract),
the pass-group summaries, the verify-gate logic, the convergence-loop boundary, and the report
format. The full detection matrix and the worked example live in `references/` for progressive
disclosure (Pass J budget discipline — same as `prompt-deep-optimizer`'s `references/`).

**`cdo.md` shim** mirrors `pdo.md`/`sko.md`: frontmatter (`description`, `argument-hint`), a body
that says "invoke the `code-deep-optimizer` skill via the Skill tool and follow its SKILL.md
exactly; SKILL.md is the single source of truth; if `$ARGUMENTS` is empty, ask once for a file or
repo path."

---

## 5. Stage 0 — language/domain detection & reviewer-skill activation (headline feature)

Mechanism specialized from `document-critique` Pass 0 ("identify domains → activate matching
reviewer skills → record what activated and why → don't over-activate").

**5.1 Detect** the stack from, in priority order:

1. File extensions and shebangs (`.ts/.tsx/.js/.mjs`, `.py`, `.go`, `.kt`, `.rs`, `#!/usr/bin/env python`).
2. Project manifests: `package.json`, `tsconfig.json`, `pyproject.toml`/`requirements.txt`,
   `go.mod`, `Cargo.toml`, `Gemfile`, `pom.xml`.
3. Framework/library imports in the source (React/JSX, Angular decorators, Express/Fastify/Nest,
   FastAPI/Django/Flask, `mongodb`/`mongoose`, `@aws-sdk`, `crypto.subtle`).
4. Infra/config files: `Dockerfile`, k8s manifests, `*.tf`, CI workflow YAML.
5. Content sniffing for special shapes: `// ==UserScript==` (Tampermonkey), MV3 `manifest.json`
   (Chrome extension), WebSocket/Worker usage, etc.

**5.2 Map → reviewer skills** via the matrix in `references/language-skill-map.md`. Seed rows:

| Detected | Activate |
| --- | --- |
| JS / TS | `lang-js-ts` (+ `typescript-advanced-types` for heavy generics/conditional types) |
| Python | `lang-python` |
| Go / Kotlin | `lang-go-and-mobile` |
| Frontend / HTML / CSS / React markup | `frontend-ui` (carries a11y + responsive lenses) |
| Node async / streams / workers | `nodejs-concurrency-internals` |
| Chrome extension (MV3, content scripts, manifest.json) | `chrome-extension-expert` |
| `crypto.subtle` / AES / PBKDF2 / key-wrapping | `webcrypto-vault-reviewer` |
| Auth / untrusted input / web app surface | `security-review` |
| MongoDB / Atlas data-plane code | `mongodb-expert` (+ `mongodb-atlas-expert` for platform) |
| REST / GraphQL / gRPC API surface | `api-design-patterns` |
| Kubernetes / Docker / CI pipelines | `kubernetes-networking`, `devops-containers-cicd` |
| AWS SDK / IAM / Lambda | `aws-cloud` |
| **Always-on baseline** | `software-engineering-patterns` (references/code-reviewer.md), `coding-standards` |

**5.3 Activate.** If a skill is in the session's available-skills list, invoke it via the Skill
tool; otherwise Read its `references/<name>.md` (or `SKILL.md`) path directly — the exact ddo
fallback. Record which activated and why in the Stage 0 status block.

**5.4 Guardrails.**
- Don't over-activate (six reviewers on a 40-line file is noise — the ddo guard).
- Status is **blocking** if a security/crypto/regulated domain is detected but no reviewer skill is
  available; `pass` when coverage is complete; `minor` if a domain is detected but no skill exists.
- Activated domain skills are injected into the relevant passes (§6) — e.g. `security-review`
  informs Pass S1, `coding-standards` informs Pass M1, `nodejs-concurrency-internals` informs P2.

This is the literal "automatically detects and loads the language-specific skills" requirement,
grounded in the real installed ecosystem.

---

## 6. Multi-stage passes (5 parallel-dispatch groups, 12 passes)

Grouped by semantic affinity, dispatched as parallel subagent bundles in a single batch when an
Agent tool exists (family pattern); otherwise sequential. **Collect all findings from all passes
before any write.** Each pass emits a row even when `N/A`.

**Group 1 — Correctness & Contract**
- **C1 Correctness/logic** — control-flow errors, off-by-one, null/undefined deref, type coercion,
  wrong API usage, incorrect conditionals, unreachable code, broken error propagation.
- **C2 Interface/contract** — function signatures vs call sites, return-shape consistency, public
  API stability, exported-symbol/typing accuracy.

**Group 2 — Safety & Robustness**
- **S1 Security** — injection (SQL/command/XSS/path), unsafe deserialization, secrets in source,
  authn/authz gaps, SSRF, unsafe crypto. Delegates to `security-review` / `webcrypto-vault-reviewer`.
- **S2 Error handling & resources** — swallowed errors, missing try/catch around I/O, unhandled
  promise rejections, resource/handle leaks, missing timeouts/retries/backoff on network calls.
- **S3 Input validation & trust boundaries** — untrusted input treated as data not code, bounds
  checks, sanitization, encoding.

**Group 3 — Performance & Concurrency**
- **P1 Performance** — algorithmic complexity, N+1 queries, redundant computation/allocation,
  sync-blocking on hot/async paths, missing caching/memoization where clearly warranted.
- **P2 Concurrency & async** — data races, deadlocks, event-loop blocking, `await`-in-loop,
  unsynchronized shared-state mutation. Delegates to `nodejs-concurrency-internals`.

**Group 4 — Maintainability & Structure**
- **M1 Readability & standards** — naming, dead code, magic numbers, comment density vs the
  surrounding file, over-long functions, cyclomatic complexity. Delegates to `coding-standards`.
- **M2 Duplication & simplification** — copy-paste, reinvented utilities, DRY/KISS/YAGNI
  simplification opportunities.
- **M3 Architecture (repo scope only; `N/A` for a single file)** — layering, dependency cycles,
  module boundaries, dead modules. Delegates to `software-engineering-patterns` (software-architect).

**Group 5 — Tests & Supply chain**
- **T1 Test coverage & quality** — untested branches for changed/risky code, missing edge-case
  tests, flaky patterns. Delegates to `testing-and-vitest-expert`.
- **T2 Dependency & supply chain** — outdated/known-vulnerable deps, unused deps, obvious license
  flags (lightweight; deep audit handed to security-review's compliance reference).

**Skip protocol:** any pass may be `N/A`/`partial` with a reason; never silently dropped. The
report Summary names the active pass count (e.g. `11 of 12 passes active`).

---

## 7. Architecture — one repo-level convergence loop, per-file fan-out

The contract forbids a *second nested* convergence loop. So a repo is **one loop** whose iteration
fans out per-file diagnostic+fix bundles (files are dispatch units, not their own loops). A single
file degenerates to the same loop with one file.

**One repo-level iteration:**

1. **(iteration 1 only) Discover & triage.** Enumerate source files honoring `.gitignore`; skip
   vendored/generated dirs (`node_modules`, `dist`, `build`, `vendor`), lockfiles, minified/bundled
   files, and binaries. Prioritize by **risk × size**: security-sensitive files and entrypoints
   first, then large/complex, then recently changed (when in git). Apply the **soft cap (50,
   `--max-files`)** with disclosed truncation.
2. **(iteration 1 only) Verify-gate baseline.** Run detected build/lint/tests once and record the
   baseline pass/fail set, so later regressions are distinguishable from pre-existing failures.
3. **Repo-scope cross-file passes** (M3 architecture, T2 dependencies, cross-file M2 duplication)
   run once per iteration at repo scope.
4. **Per-file fan-out.** Dispatch a bounded subagent per in-scope file running Stage 0 (scoped to
   that file's stack) + the file-level passes (G1–G2–G3, M1–M2, T1). Concurrency-capped
   (`min(16, cores−2)`, family default). One round-trip each; error/empty → `N/A` row, no
   mid-iteration retry.
5. **Triage & dedup** all findings (cross-file + per-file) against the calibration table; merge
   duplicates; keep higher severity.
6. **Apply** every Medium+ fix (default mode) after snapshotting. `--read-only`/`--report` skip
   writes (and the snapshot).
7. **Verify gate** (§8): re-run the suite; back out regressions via bounded bisect.
8. **Convergence check** (§9): stop or continue.

---

## 8. Verify gate (code-specific; D2)

- **Detect** commands per stack: JS/TS — `package.json` scripts (`build`/`lint`/`test`/`typecheck`),
  `tsc --noEmit`, `eslint`, `vitest`/`jest`, `node --check`; Python — `pytest`, `ruff`/`flake8`,
  `mypy`, `python -m py_compile`; Go — `go build ./...`, `go vet`, `go test ./...`; plus
  `Makefile` targets and `pre-commit`. *(This repo specifically: `node --check` on a copy +
  `npm test` (vitest), per its CLAUDE.md.)*
- **Baseline first** (iteration 1) → separates pre-existing failures from regressions. Pre-existing
  failures are reported but not chased unless a finding targets them.
- **After each apply:** re-run. A check green at baseline now red = **regression**. Back it out via
  **bounded bisect** (revert highest-risk/most-recent fix, re-run; up to 3 probes; then revert the
  iteration batch). The backed-out fix becomes a `BLOCKED (verify-gate regression)` row — counts as
  unsatisfied for convergence, never silently shipped.
- **N/A** when nothing is detected → fall back to a syntax check (`node --check`/`py_compile`) + the
  blind re-audit gate; never blocks convergence. `--no-verify` (static only), `--verify-end`
  (final candidate only).

This is the empirical analogue of `prompt-deep-optimizer`'s simulated behavioral smoke test (6a2):
behavior-drift is caught by execution, not judgment.

---

## 9. Convergence loop & severity (inherited)

- **Cite** `convergence-and-severity.md`; keep only a small **calibration table** mapping the
  canonical tiers → code findings. Keep **Critical** distinct (code has genuine wrong-output /
  undefined behavior) → maps like `prompt-deep-optimizer`, not sko:

  | Canonical | code-deep-optimizer | Example |
  | --- | --- | --- |
  | Blocking/Critical | **Critical** | wrong output, data loss, RCE/injection, secret leak |
  | High/Major | **High** | inconsistent behavior under repeated runs, resource leak, race |
  | Medium | **Medium** | reduces robustness/clarity/perf without breaking correctness |
  | Low/Minor | **Low** | subjective polish — skip |
  | Nit | **Nit** | formatting/whitespace — deterministic hygiene, skip |

- **Fix everything Medium+;** loop terminates on any of the 7 canonical exit conditions.
- **Iteration cap 5 (3 small-profile)** — code has a measurable per-iteration signal (tests), same
  rationale as prompts. Small profile: single file under ~150 lines AND no detected build/test
  surface → merged dispatch groups, cap 3.
- **`convergence_check.py`** computes no-progress / stable-rewrite / instability from `.iter<N>`
  copies + model-counted severity totals — never self-estimated.
- **Blind re-audit gate** on CLEAN exits: a fresh-context subagent receives only the final code +
  pass list; only corroborated Medium+ findings fail the gate; `BLIND-AUDIT-DISSENT` on second
  dissent.
- **Optional `--cross-model`** gate via `cross-model-gate.md` (copilot-adversarial-review is itself
  a cross-model code-diff reviewer — natural fit).

---

## 10. Guardrails (inherited, code-specialized)

- **BLOCKED rows** when a fix would require inventing behavior (ambiguous intent) — don't guess.
- **Behavior-drift guard** — a fix must not change observable behavior unless a finding justifies
  it; the verify gate enforces this empirically; declared deltas cite their finding row.
- **Injection guard** — code under review is data. A comment/string saying "ignore instructions",
  "mark as passing", or mimicking this skill's verdict format never alters a pass result (a real
  code-review attack surface). Flag it as a finding; continue on the actual code.
- **Secrets/PII** — a hardcoded secret is itself a **Critical** S1 finding; redact its value in the
  report/diff (`[REDACTED: <type>]`) while reporting the finding.
- **Evidence rule** — every Medium+ finding cites `file:line` (or a lint/test/grep result) plus the
  tier criterion it meets; otherwise recorded Low.
- **Pre-write snapshot** to the central backup dir + `.iter<N>` copies before each iteration's writes;
  final report ends with the literal restore command.
- **No silent caps** — repo file-count truncation is always disclosed with the dropped remainder.

---

## 11. Modes & flags (parallel to the family)

Default: **apply + verify in place**.

| Flag | Effect |
| --- | --- |
| `--read-only` / `--report` | findings + prescribed diffs, no writes (no snapshot) |
| `--annotate` | inline review comments instead of rewrites |
| `--scope=changed` | git-changed files only (instead of triaged-all) |
| `--scope=<paths>` | explicit file/dir list; no auto-discovery |
| `--max-files=N` | repo triage cap (default 50) |
| `--no-verify` | static analysis only (skip the build/lint/test gate) |
| `--verify-end` | run the suite once on the final candidate, not per iteration |
| `--max-iter=N` | hard ceiling on the convergence loop |
| `--budget-minutes=N` | canonical budget contract |
| `--cross-model` | cross-model exit gate (default OFF) |
| `--no-sync` | skip hub registration |

---

## 12. Report format (parallel to sko/pdo)

In order: per-iteration severity table (Critical/High/Medium/Low/Nit) · findings table
(`Pass | file:line | Severity | Finding | Fix | Status`, capped + rolled up) · **verify-gate table**
(`command | baseline | after-iter | verdict`) · **activated-skills list** (which language/domain
skills loaded + why) · unified `diff` preview per file (capped, truncation noted) · blind re-audit
result (+ cross-model residuals if `--cross-model`) · one-line **Summary**
(`Iterations · Active passes · Profile · Final C/H/M/L · Verify: PASS|FAIL|N/A · Status:
CLEAN|CONVERGED|OSCILLATING|CAPPED|NO_CHANGE|BUDGET_EXHAUSTED|BLIND-AUDIT-DISSENT`) · **Snapshot &
rollback** line with literal restore command.

**Telemetry:** append one JSONL row per executed pass to `optimizer-telemetry.jsonl` with
`artifact_type: "code"` per the canonical schema (fail-safe; a write error never blocks the run).

---

## 13. Integration / wiring as a full family member (D4)

Authoring produces the SKILL.md + references + command shim. Wiring then reuses existing machinery
rather than hand-editing the registry:

1. Run `/sko code-deep-optimizer` (skill-optimizer) to: audit quality (Pass A–O), run the **Pass H
   trigger-accuracy eval** (≥9/10 positives, ≤1/10 negatives), the **Pass I collision check**
   against `document-critique`, `prompt-deep-optimizer`, `skill-optimizer`, and
   `software-engineering-patterns`, and **Pass O peer-edge seeding**.
2. Seed the key routing edges:
   - `document-critique` Pass 11.5 "code embedded in document → software-engineering-patterns" gains
     a `→ code-deep-optimizer` handoff for whole-file/repo code review.
   - `software-engineering-patterns` (code-reviewer) defers deep convergence-loop optimization to
     `code-deep-optimizer`.
   - The optimizer family (`pdo`/`sko`/`ddo`) cross-reference the new sibling.
3. Hub/registry sync via skill-optimizer Step 7 (`tam_create_skill`/update or `/sync-skills`).

**Routing boundary (description SKIP clause):** one-shot diff review → `/code-review`; prose docs →
`document-critique`; prompts → `prompt-deep-optimizer`; skill files → `skill-optimizer`; pure
formatting → the language formatter.

---

## 14. Acceptance criteria

1. `/cdo <file>` and `/cdo <repo>` run the full pipeline: Stage 0 detection → multi-pass review →
   triage → apply Medium+ → verify gate → convergence loop → report.
2. Stage 0 detects the stack and activates the correct reviewer skills, logged in the report; a
   security/crypto domain with no available reviewer is reported `blocking`.
3. Loop applies all Medium+ fixes and terminates on a canonical exit condition; the report shows the
   per-iteration severity table and the chosen Status.
4. Verify gate runs the detected suite, backs out regressions as `BLOCKED (verify-gate regression)`,
   and reports `N/A` cleanly when no suite exists.
5. Repo mode triages, discloses any file-count truncation, runs repo-scope cross-file passes, and
   fans out per file.
6. The skill cites (does not restate) the canonical contract; reuses `convergence_check.py`,
   snapshots, blind re-audit gate, optional cross-model gate, and telemetry.
7. `SKILL.md` stays within the ~6k-token soft budget (detail in `references/`); `/sko
   code-deep-optimizer` passes Pass H/I and seeds peer edges.

---

## 15. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| Auto-applied fix breaks the build | Verify gate + bounded-bisect backout; pre-write snapshot + literal rollback line |
| Running an untrusted repo's test command is dangerous | Verify gate runs only detected, conventional commands; honor `--no-verify`; never run arbitrary scripts beyond build/lint/test entrypoints; surface the exact command before first run |
| Repo fan-out cost explosion | Triage cap (50, `--max-files`), concurrency cap, `--budget-minutes`, disclosed truncation |
| Over-activation of reviewer skills | ddo's "don't over-activate" guard; activation scoped to detected stack |
| Nested convergence loops | One repo-level loop; per-file work is dispatch units, not loops |
| Malicious code comments gaming the verdict | Injection guard — code is data, comments never alter pass results |

---

## 16. Open items deferred (YAGNI)

- Standalone accessibility / i18n passes (currently ride `frontend-ui` activation).
- Auto-generating net-new test suites (T1 only flags gaps).
- Language-server / AST-level deterministic checks beyond what the project's own tools provide.
- A `--explain` teaching mode (ddo has one; add later if wanted).

---

## 17. Amendment 2026-06-15 — fix/advisory two-track + new passes (v1.1.0)

Extends §3, §6, §8, §11, §12, §14. Driven by the question "what other passes help — features, architecture/tooling, bug-finding?" The key constraint: the convergence loop only works for **objective defects that can be applied + verified + converged**. Suggestions (features, redesigns, tooling you don't have) can't converge and must never be auto-applied (behavior-drift guard). So the catalog splits into two tracks.

### 17.1 Two tracks

- **Fix-track** — objective defects; applied in place, verified by the gate, gate convergence. The original 12 passes plus the new ones below: **16 passes** total.
- **Advisory-track** — recommendations; **report-only, never auto-applied, never gate convergence**, `--suggest`-gated (default OFF), and **evidence-grounded** (each suggestion cites a concrete signal in the code, or it is not raised). Output lands in a separate **Recommendations** report section, not the findings table; advisory items carry an *advisory* severity (Suggest/Consider) that never enters the Medium+ convergence count.

### 17.2 New fix-track passes (extends §6)

- **C2 (extended) — type safety.** Fold into the existing interface/contract pass: `any`/unsafe casts, missing null/undefined guards the type system would catch, unsound assertions. (No new pass id; C2 owns it.)
- **C3 Adversarial bug-hunt** (Group 1). Don't review by category — *try to break it*: boundary/edge inputs, error-path bugs, off-by-one, state-machine violations, resource exhaustion, plus **invariant/property checking** (what must always hold; find violating paths). **Counterexample mechanic:** when a build/test harness exists, C3 may write a *failing test* that reproduces a suspected bug, confirm it is red, then fix to green — turning a hypothesis into a verified, regression-guarded fix (the verify-gate-native bug-finding mode the prose/prompt siblings cannot do). With no harness, C3 reports the bug + a repro sketch. Delegates per Stage 0 (e.g. `security-review` for security-relevant breakage, `nodejs-concurrency-internals` for races).
- **S4 Portability & runtime-compat** (Group 2). Runtime/version/OS assumptions: Node/Deno/Bun version features, browser support targets, OS-specific paths, and hardened-runtime constraints (e.g. SES/lockdown frozen-intrinsics, CSP, no-eval). Delegates to the language/runtime skill.
- **M4 Documentation correctness** (Group 4). Comments/docstrings that contradict the code (a real bug source), stale references, undocumented public API. *Correctness* of docs, distinct from M1's density check. Delegates to `technical-writing-craft`.
- **T3 Tooling-gap** (Group 5). Missing linter config, type-checking on untyped JS, no CI, no test runner, no formatter, no pre-commit, unpinned deps. Mostly actionable — flag + scaffold, or hand the scaffolding to `repo-bootstrapper` (and `devops-containers-cicd` for CI). Detection grounds on the absence the verify gate already probes for.

Revised fix-track groups: **G1** C1, C2(+types), C3 · **G2** S1, S2, S3, S4 · **G3** P1, P2 · **G4** M1, M2, M3, M4 · **G5** T1, T2, T3 = **16**.

### 17.3 Advisory-track passes (`--suggest`)

- **A1 Feature / latent-intent enhancements** — only improvements the code *signals*: a `// TODO`, a `switch` missing a case the type permits, a `throw new Error("not implemented")` stub, a caller passing an argument the callee ignores. Each cites its evidence; no blue-sky.
- **A2 Architecture & design recommendations** — proposed extractions, boundary improvements, where a pattern would cut coupling (M3 *flags violations*; A2 *proposes redesigns*). Delegates to `software-engineering-patterns` (software-architect).
- **A3 Migration & deprecation roadmap** — deprecated APIs in use, EOL dependencies, next-major breaking changes. Delegates to the relevant domain skill (e.g. `mongodb-operations-expert` for MongoDB migrations).

### 17.4 Verify gate (extends §8)

C3's counterexample mechanic uses the gate: write failing test → confirm red (bug reproduced) → apply fix → confirm green. A bug C3 cannot reproduce as a red test (no harness, or non-deterministic) is reported with a repro sketch and **not** auto-fixed beyond an obvious correction, to avoid speculative edits.

### 17.5 Flags (extends §11)

Add **`--suggest`** — run the advisory track (A1/A2/A3) and emit the Recommendations section. Default OFF: the core run stays a tight, convergent fixer.

### 17.6 Report (extends §12)

Add a **Recommendations** section (only when `--suggest`): advisory items grouped A1/A2/A3, each with its grounding evidence (`file:line` / TODO / caller). Clearly separated from the findings table; never counted in the per-iteration severity table or the Status convergence math.

### 17.7 Acceptance (extends §14)

8. The 16 fix-track passes run and gate convergence; advisory passes run **only** under `--suggest`, never auto-apply, and never affect the Status/convergence count.
9. C3 produces, where a harness exists, at least a reproducing failing test for a confirmed bug before fixing; otherwise a repro sketch.
10. The Recommendations section appears only under `--suggest` and is evidence-grounded.

### 17.8 Deferred items now addressed

§16's "auto-generating net-new test suites" stays deferred as a *feature*; C3's counterexample test is a **bounded bug-repro test**, not full suite generation — a deliberate, narrow exception. Accessibility/i18n still ride `frontend-ui`.

### 17.9 Agent fan-out is the explicit dispatch model (extends §6, §7)

The review runs as a **parallel agent fan-out**, not a sequential walk — matching how `pdo`/`sko`/`document-critique` dispatch their pass bundles. Made explicit here so the new passes and the advisory track are covered:

- **Single-file / top-level mode:** dispatch **6 bundles in one batch** — the 5 fix-track groups (G1–G5) plus, when `--suggest` is set, a **6th advisory bundle** (A1/A2/A3). Sequential execution is only the fallback when no Agent tool exists.
- **Repo mode:** the top level fans out **one subagent per in-scope file** (concurrency-capped `min(16, cores−2)`); each per-file subagent runs its passes sequentially — it is the dispatch boundary and does **not** nest further (contract: no nested dispatch). Repo-scope passes (M3, T2, cross-file M2, and advisory A2/A3) run once at the top level; per-file passes (C1–C3, S1–S4, P1–P2, M1, M4, T1/T3, and advisory A1) run inside the file subagents.
- **Bundle budget rails (unchanged):** one round-trip per bundle; error/empty → `N/A` row, no mid-iteration retry; two consecutive failures → sequential fallback for that bundle; collect all findings before any write. An `N/A` bundle blocks the clean exit until re-run.
- The advisory bundle's results never gate convergence (§17.1); only the fix-track bundles' Medium+ findings do.
