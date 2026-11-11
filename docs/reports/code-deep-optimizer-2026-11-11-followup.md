---
title: Repository code optimizer follow-up
type: history
created: 2026-11-11
updated: 2026-11-11
sources:
  - code: api/explorer_api/gateway.py
  - code: api/explorer_api/tree_publication.py
  - code: api/pyproject.toml
verified_at: c458299c
---

# Code deep optimizer follow-up

Version:1.0.0. Delta: extend the earlier17-file lifecycle audit to a risk-selected
account/API and skill-registry scope. Profile:default; mode:full. **Status:
BLIND-AUDIT-DISSENT.** The verified repairs are ready for delivery; three confirmed
residuals remain. This is not a whole-repository clean claim.

## Per-iteration severity

| Round | Critical | High | Medium | Disposition |
| --- | ---: | ---: | ---: | --- |
| Main review + bootstrap/repo passes |0|10|35|45 findings repaired |
| First blind gate + accounting corroboration |0|0|4|3 blind findings plus1 financial-contract correction repaired in the one extra iteration |
| Second blind gate + minimum SDK corroboration |0|1|2|3 residuals listed below; no third gate or further repair loop |

Applied total:49 (10High/39Medium), including44 source findings and5 dependency/tooling
findings. The known malformed-non-ASCII ciphertext normalization observation remains
Low and does not gate this run. Earlier retractions and the prior audit's14 fixes and
BLIND-AUDIT-DISSENT boundary remain intact; they were not rewritten as clean.

## Findings

The table caps descriptions and fixes and shows30 applied rows. The other19 applied
rows and every per-file pass disposition are retained in
[code-deep-optimizer-2026-11-11-followup-coverage.json](code-deep-optimizer-2026-11-11-followup-coverage.json).

| Pass | File/anchor | Severity | Finding | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| S2 | `api/explorer_api/anthropic_keys.py` [46, 54] | Medium | A per-request AsyncAnthropic client has no deterministic close path | Own client in async context manager; actual SDK1.3.0 __aexit__ awaits close; fake success/auth/service cases verify release | fixed |
| S5 | `api/explorer_api/anthropic_keys.py` [42, 54] | Medium | External key-validation attempt/outcome has no audit event | Sanitized outcome events tested to exclude key and upstream body | fixed |
| C1,C3,S1,S2,P2 | `api/explorer_api/artifacts.py` api/explorer_api/artifacts.py:245-271 in initial292line source | High | write mutates filesystem before following symlinks and checking containment; planted leaf/section links overwrite outside content even when NotFound follows, while aliase | No-follow descriptor traversal anchored at configured store before any owned mkdir/write; atomic owner-private stage+replace and regular-file checks. Root alias | fixed |
| per-file passes | `api/explorer_api/artifacts.py` api/explorer_api/artifacts.py:199-204 in initial312line reviewed patch | High | read resolved and checked a pathname, then reopened it; a swapped leaf or ancestor follows a symlink outside the private jail. | Parent changed read to pinned directory descriptors, leaf O_NOFOLLOW/O_NONBLOCK and fstat regular check. Independent active-boundary race assertions pass. | fixed |
| per-file passes | `api/explorer_api/artifacts.py` api/explorer_api/artifacts.py:273-275 in initial312line reviewed patch | Medium | If fdopen raises before wrapping staging fd, unlink runs but raw descriptor remains open. | Register raw fd with ExitStack before fdopen, use closefd=False. Injected wrapper failures prove read/write close their owned descriptor. | fixed |
| C1,C3,S1,S3 | `api/explorer_api/auth.py` api/explorer_api/auth.py:575-578 | High | An existing-account registration ceremony rehydrates its owner even when current authenticated user is absent. Logout/revocation does not retire the10minute ceremony, so  | Existing-account enrollment now requires active matching current user. Cookie owner is never reloaded as substitute for authentication; anonymous registration i | fixed |
| C1,C2,C3,S2,S3,T1 | `api/explorer_api/auth.py` api/explorer_api/auth.py:257-258 | Medium | HTTP200 OAuth token responses are parsed without JSON/type validation. Invalid JSON or a JSON list escapes as JSONDecodeError/AttributeError rather than OAuthError; route | Shared provider object decoder converts malformed/non-object token/profile payloads into safe OAuthError; tokens must be nonempty strings. | fixed |
| S5,T1 | `api/explorer_api/auth.py` api/explorer_api/auth.py:147-155,233-261,434-474,594-609 | Medium | Important authentication state transitions and OAuth failure branches emit no semantic audit events, contrary to docs/logging.md. Uvicorn access logs cannot identify acco | Safe account resolution, passkey enrollment, revocation-request and token exchange outcome events added. Requested revocation explicitly remains pending caller  | fixed |
| C1,C2,C3,M4,T1 | `api/explorer_api/billing.py` [174, 188, 416, 428] | Medium | The donation becomes active but the customer ID is lost: the handler updates only an already-existing Subscription by its new Stripe subscription ID, while donation check | Donation owns nullable stripe_customer_id; own-user lookup prefers donations and falls back to legacy Subscription. No manufactured plan rows. Payment-mode SDK  | fixed |
| C1,C2,C3,T1 | `api/explorer_api/billing.py` [67, 74, 402, 415] | Medium | The donation is marked paid/active immediately. checkout.session.async_payment_failed is not handled, so a one-time failed payment remains permanently recorded as paid. T | Checkout completion stores IDs but confirms paid/active only for explicit payment_status=paid. Async success uses the same paid-gated handler; async failure kee | fixed |
| C1,C3,P2,T1 | `api/explorer_api/billing.py` [433, 449, 485, 494] | Medium | The first event stores canceled; the second unconditionally sets active. Event-id deduplication does not protect against these distinct events, so canceled recurring dona | Donation rows are selected FOR UPDATE with populate_existing so preloaded stale identities refresh after lock acquisition. Canceled remains terminal across invo | fixed |
| C1,C2,C3,S3,T1 | `api/explorer_api/billing.py` api/explorer_api/billing.py:218-233 in first-gate source | Medium | Fractional cents persist a different donation amount from the integer cents requested from Stripe (1.999USD versus199cents); sub-cent input reaches zero provider amount. | Reject nonfinite/nonpositive and fractional-cent amounts through existing InvalidDonationAmount before row insertion or provider invocation. Exact-cent inputs i | fixed |
| C3,S2,S3,T1 | `api/explorer_api/checkouts.py` api/explorer_api/checkouts.py:95,121,158 | Medium | A truthy non-list concepts field in a single valid JSON run file raises uncaught TypeError, taking down the aggregate snapshot and all held_by callers, including status/q | Validate concepts list shape per record before iteration. Reject only malformed run/batch records and retain valid sibling reservations. Emit bounded WARNING so | fixed |
| C1,C2,C3,S2,T1 | `api/explorer_api/gateway.py` [1091, 1101] | Medium | Failed keyword queries consume the free daily query allowance and write success-shaped ledger rows. The real hub reports failure strings at hub/mcp-server/hub_mcp_server. | call_hub recognizes standard MCP isError and exact legacy ERROR:/nonzero EXIT conventions, returns sanitized isError result; _tools_call rolls back and skips me | fixed |
| C1,C3,P2,S3,T1 | `api/explorer_api/gateway.py` [1088, 1101] | Medium | Both index operations start and succeed although free indexes limit is1. Daily query counters have the same check-then-await structure; exact witness covers free index ca | Lock account User row transactionally before quota read and hold through operation/meter commit. Invalidate index catalogue under lock, including separately cac | fixed |
| S2,S5,M4,T1 | `api/explorer_api/gateway.py` [542, 551, 633, 638, 644, 651] | Medium | Operators see generic502 without the gateway tool operation or safe failure class. Comments claim chained detail reaches logs, but that catch path never logs. | Single upstream wrapper boundary emits known bounded operation and exception class (64chars maximum), no args, raw provider text or traceback. | fixed |
| C3,S2,P2,T1 | `api/explorer_api/keys.py` api/explorer_api/keys.py:113-119 | High | The semaphore token is held by the awaiting coroutine, not the running hash worker. Coroutine cancellation releases it immediately while the thread continues, allowing ac | Keep a permit owned by the running worker until completion. Shield worker lifetime or use a completion callback that releases the permit exactly once and consum | fixed |
| S5,T1 | `api/explorer_api/keys.py` api/explorer_api/keys.py:205-218,336-341 | Medium | The module emits no semantic issuance/revocation audit events despite the documented critical-transition logging policy. Access logs do not identify key lifecycle operati | Emit safe key issuance/revocation request events with non-secret key ID/prefix and user ID. Because these helpers flush and caller commits, event wording must n | fixed |
| C3,S2,P2,S5,T1 | `api/explorer_api/keys.py` api/explorer_api/keys.py:309 in first-gate source | Medium | Authentication holds its request SELECT connection while optional last-use metadata awaits a second connection. A full shared pool stalls every such request until the poo | A central100ms best-effort deadline includes checkout, UPDATE and commit; failure keeps authentication alive and records safe exception class only. | fixed |
| C1,C3,S2,P2,T1 | `api/explorer_api/ledger.py` api/explorer_api/ledger.py:259-267 (original) | Medium | Read-then-create cannot lock an absent credit row; simultaneous first spends collide. SELECT FOR UPDATE also retains an already-loaded ORM Credit balance unless refreshed | PostgreSQL INSERT ON CONFLICT UPDATE uses current database balance minus exact money(amount), sets updated_at and returns refreshed Credit with populate_existin | fixed |
| S5,T1 | `api/explorer_api/ledger.py` api/explorer_api/ledger.py:255-256 (original) | Medium | Ledger writes emit no semantic event although docs/logging.md explicitly requires critical ledger transitions be logged. | Safe INFO ledger_append_staged after flush with ledger/user IDs, bounded component/kind, units and billable flag; no raw call,IP,email or transaction commit cla | fixed |
| C1,C3 | `api/explorer_api/main.py` [86] | High | Allowed site browser cannot preflight PUT for saving BYOK key | Allow PUT in explicit CORS method list | fixed |
| S1,S5 | `api/explorer_api/main.py` [140, 143] | High | DBAPIError traceback logs SQL statement, bound private account fields and driver text | Retain method, path and exception class only; regression uses synthetic private markers | fixed |
| C1,C3,P2,M4,T1 | `api/explorer_api/moderation.py` [204, 220] | Medium | The expected-SHA check and file replacement are not serialized; the snapshot nodes and SHA also come from separate file reads. | One immutable byte buffer binds nodes/hash and fork hash/copy. Stable advisory lock covers expected-SHA check and unique atomic replacement; sync contenders fai | fixed |
| C1,C3,S2,P2,M4,T1 | `api/explorer_api/moderation.py` [786, 810] | Medium | Public tree publication precedes the durable moderation decision and has no rollback/recovery coordination with the caller-owned database transaction. | Fsynced0600 journal preserves before/after bytes and proposal identity. Lock is retained to outer transaction end; known rollback restores, commit retains, ambi | fixed |
| S1,S5 | `api/explorer_api/notify.py` [30, 31] | High | Default no-SMTP path logs full recipient address and subject | Log bounded delivery state, not recipient/subject/body | fixed |
| S2,P2,S5 | `api/explorer_api/notify.py` [38, 42, 68] | Medium | SMTP uses unbounded socket timeout and synchronous sends inside async publisher; no transport outcome audit | Central positive SMTP timeout, to_thread offload, success/failure events with exception class only | fixed |
| M4 | `api/explorer_api/notify.py` [50, 52] | Medium | Docstring directs user to nonexistent scripts/notify_new_post.py | Document explicit function call and absence of automatic publishing hook | fixed |
| C1,C3,S2,P2,T1 | `api/explorer_api/research.py`  | High | Caller cancellation exits proc.wait and discards the live child from _PROCS without killing or reaping it; shutdown can no longer find it. Cancellation during asynchronou | Strongly reference and shield process creation; keep a shielded referenced cleanup task through repeated cancellation; kill the process group, await reaping, th | fixed |
| S1,S2,T1 | `api/explorer_api/research.py`  | High | Raw worker stdout/stderr uses default directory/file permissions. Under ordinary umask022 the log is0644, and an already-permissive file stays readable by other local acc | New log leaf directories0700, current log descriptor0600 even for existing file, no-follow regular-file open and unconditional descriptor cleanup. Historical un | fixed |

### Confirmed residuals

| ID | Severity | Anchor | Finding | Disposition |
| --- | --- | --- | --- | --- |
| FINAL-F1 | High | `{'path': 'api/explorer_api/gateway.py', 'start': 1155, 'end': 1169}` | Billable indexing bypasses account and per-key spend limits | unmodified after second dissent |
| FINAL-F2 | Medium | `{'path': 'api/explorer_api/routes/contribute.py', 'start': 129, 'end': 169}` | Colliding contribution slugs overwrite bytes behind an earlier passing proposal | unmodified after second dissent |
| T2-ANTHROPIC-FLOOR | Medium | `anthropic>=0.40; api/explorer_api/anthropic_keys.py models.list call` | AllowedAnthropic0.40.0 has messages but no AsyncAnthropic.models; validator requires models.list. | unmodified after second dissent |

- FINAL-F1: actual gateway/quota/meter/ledger functions accepted a billable index
  under the free plan with owned count0, initial credit0, overage disabled and
  per-key daily cap0. The fake provider was reached; generated debit was$0.100000,
  and ledger key/IP fields were absent. This used fake database/provider seams;
  it is a code-flow counterexample, not a production transaction.
- FINAL-F2: `A B` and `A-B` produced the same artifact slug. Actual lint passed the
  first bytes and rejected the replacement. The earlier proposal still reached
  merged state without another lint. Database/provider/publication seams were
  fake; only temporary fixture bytes changed. No public tree was modified.
- T2-ANTHROPIC-FLOOR: an isolated0.40.0 SDK has `messages` but no `models` attribute;
  current validator calls `models.list`. Final no-network capability probe exited0.
  Current locked SDK behavior passing tests does not establish the allowed minimum.

The missing-CSRF-header candidate was rejected: hostile same-site Origin with no
Content-Type received422 before provider execution. It is not a vulnerability finding.
The two-gate skill contract ends on corroborated second dissent; residuals were not
silently fixed through an unreported third loop.

## Verify gate

| Command/surface | Baseline | After iteration2 | Verdict |
| --- | --- | --- | --- |
| Isolated API pytest with actual temporary PostgreSQL |307passed/exit0|442passed,3existing warnings,67.23s/exit0|PASS;51source hashes identical before/after |
| Standalone registry `uv run --directory hub/skill-registry --frozen pytest -q` |72passed/exit0|72passed/exit0|PASS; no registry source behavior change |
| `uvx ruff check api hub/skill-registry` |exit0|exit0|PASS |
| `api/.venv/bin/python -m pytest scripts/tests -q` |affected script baseline|112passed/exit0|PASS |
| Site workflow contract test |existing contract|13passed/exit0|PASS |
| `npm run check` in site |owning locked setup|exit0;0errors/0warnings,19existing hints|PASS |
| `python3 scripts/check_doc_indexes.py` |22paths|31paths/exit0|PASS |
| Registry drift checker |existing metadata|exit0|PASS |
| API dependency audit |exit1;8unique advisories|exit0;zero known vulnerabilities after3 targeted upgrades|PASS within installed audited packages |
| Registry installed audit/site npm lock audit |exit0|exit0;zero known vulnerabilities|PASS within those scopes |
| Minimum compatibility smoke |old floors lack APIs|Settings2.15.0 CSV/NoDecode + Stripe12.5.0.v1 methods/exit0|PASS; no provider calls |
| Repeat unchanged ledger plan |614pending/68unchanged|identical plan;0 of51 selected files replanned|PASS;614 still genuinely unreviewed |

Final API command (cwd `api/` in the isolated worktree):

```sh
env -u EXPLORER_TEST_DATABASE_URL PYTHONPATH=/Users/mitch/dev/llms-explorer-wt-01a1ca5e/hub/skill-registry/src RESEARCH_SITE_SYNC_DISABLED=1 /Users/mitch/dev/llms-explorer-wt-01a1ca5e/api/.venv/bin/python -m pytest -q
```

Real PostgreSQL fixtures create/drop their own databases. Regression witnesses cover
cancellation, concurrent debits/quota admissions, payment ordering, artifact symlink
races, resource cleanup, logs and migration upgrade/downgrade. Red results are retained:
iteration2 regressions initially3failed/1passed (exit1), then62 affected tests passed.
The first shared-environment setup attempts failed collection (missing llms_txt/PyYAML);
they were replaced with isolated frozen environments, never counted as passing baselines.

The API lock changed only certifi2026.7.22→2026.10.23, pyasn1 0.6.4→0.6.5 and urllib3
2.7.0→2.8.0. Raising two minimum constraints changed no package versions. First-party
`llms-txt` is not available to the PyPI advisory audit, editable packages were excluded,
and other requirements/manifests were not comprehensively scanned. Dependency-reviewer
package-risk fallback found no Endor MCP and `endorctl` exited127; Endor risk remains
UNKNOWN, not approved. Source/compatibility evidence and pip-audit are separately named.

No genuine held-out optimizer benchmark/eval set exists for this selection. Empirical
mode was not engaged; regression tests are not an optimization benchmark, and no
champion, efficacy or performance improvement is claimed.

### Delivery checks after the capped audit

The first PR head `622040f4` received three CodeQL path-expression alerts at the
new descriptor-relative artifact operations. Delivery stopped for this required
check. The follow-up separates the trusted configured root from relative child
names, passes explicit validated basenames to file operations, and uses fullmatch
to reject final-newline components. It retains no-follow descriptor traversal,
201-character slugs, safe punctuation and existing slash normalization.

The basename-only follow-up `d7eb70ee` still triggered CodeQL. Inspection of
GitHub's current path-injection model showed that it tracks normalization plus
an explicit prefix check. The final helper now normalizes each child against
its intended parent, checks the separator-terminated parent prefix, then returns
the basename. Directory descriptors and no-follow checks remain authoritative
for filesystem races. No CodeQL suppression, dismissal or weakened rule was used.
The full451-test API suite passed again with exit0 in51.52s; Ruff passed.

Nine added regressions produced six failures and three positive passes before
the guard change (exit1). All41 artifact tests and the full451-test API suite
then passed with exit0; Ruff passed. Independent focused inspection and20 pure
validation probes passed. The precise delivery file hashes/read ranges are in
the coverage JSON. CodeQL must pass the final pushed head before merge.

This is required CI delivery remediation after the completed two-gate audit,
not a third blind gate or a new convergence claim. The three residuals and the
49-finding audit accounting remain unchanged. A separate one-file ledger refresh
records14 file passes and explicit N/A for repo-only/entrypoint passes; it does
not inflate the parent audit's57 record events or51 distinct reviewed files.

## Activated skills and method

- Migrated CDO1.17.1 supplied the pass/ledger contract; canonical body differs only
  in routing lines and used references/helper are identical.
- Migrated bootstrapper5.4.2 lagged canonical5.7.2; the canonical checklist and current
  bootstrap prompt governed source-backed documentation/setup repairs. Both are pinned
  in [code-deep-optimizer-2026-11-11-followup-skill-pins.json](code-deep-optimizer-2026-11-11-followup-skill-pins.json).
- Python, security and software-engineering reviewer references informed runtime,
  trust-boundary and test checks. Context7 supplied current Python cancellation,
  SQLAlchemy transaction and Stripe/Pydantic API documentation; installed SDK source
  and isolated capability tests verified the actual used interfaces.
- The subprocess lifecycle specialist repaired research cancellation and owner-private
  output. Postman's API-engineer workflow reused pytest contracts; uninitialized
  Postman account/workspace state was recorded, not initialized gratuitously.
- Dependency-reviewer ran read-only package-risk fallback with explicit unavailable
  Endor evidence. No Endor approval, risk verdict or package policy was fabricated.

**Method deviation:** root/coordinator completed many separate bounded per-file reads
in reused orchestration contexts; follow-up file workers also reused contexts. This
is not51freshper-file agents and does not satisfy the strict fanout shape retroactively.
Two distinct fresh-context blind agents independently read all assigned source. The
second gate read13,737lines in89slices≤220 and its hashes match final files. Per-file
coverage is full for51 selected/repair files; canonical workflow and whole-repository
coverage remain partial. Large cohesive existing modules were reviewed rather than
split without a supported reason. CLI stdout/protocol output and documented expected
best-effort catches were assessed in context, not counted as debug/silent-error bugs.

## Unified diff excerpts

Each file is capped at16 diff lines; further lines are explicitly omitted. The
complete task diff remains in Git. Mechanical ledger/generated report artifacts and
parent-owned prompt/memory history are excluded from recursive diff rendering.

### `.env.example`

```diff
diff --git a/.env.example b/.env.example
index de92f4de..f26849f5 100644
--- a/.env.example
+++ b/.env.example
@@ -47,2 +47,21 @@ HUB_REFINE_LLM_MODEL=qwen3.5:35b
 # be billed is refused rather than run.
 ANTHROPIC_API_KEY=
+
+# --- Hosted private skill releases and candidate broker -----------------------
+# Per-account immutable release count and stored archive bytes.
+SKILL_RELEASE_LIMIT=500
+SKILL_STORAGE_LIMIT_BYTES=104857600
+# Maximum streamed JSON body for the private release adapter (bytes).
+SKILL_REGISTRY_REQUEST_BYTES=8650752
+# Maximum streamed JSON body for candidate-job submissions (bytes).
+OPTIMIZER_JOB_REQUEST_BYTES=1048576
... 10 further diff lines omitted; full change is in Git.
```

### `.github/dependabot.yml`

```diff
diff --git a/.github/dependabot.yml b/.github/dependabot.yml
index 59014809..51cb3c7c 100644
--- a/.github/dependabot.yml
+++ b/.github/dependabot.yml
@@ -13,4 +13,8 @@ updates:
     schedule:
       interval: "weekly"
+  - package-ecosystem: "pip"
+    directory: "/hub/skill-registry"
+    schedule:
+      interval: "weekly"
   - package-ecosystem: "npm"
     directory: "/site"
```

### `.github/workflows/site.yml`

```diff
diff --git a/.github/workflows/site.yml b/.github/workflows/site.yml
index 53431f0e..bea73fb2 100644
--- a/.github/workflows/site.yml
+++ b/.github/workflows/site.yml
@@ -69,4 +69,7 @@ jobs:
           SITE_URL: https://llmsx.org

+      - name: Site type check
+        run: cd site && npm run check
+
       - name: site tests
         run: hub/.venv/bin/python -m pytest site/tests -q
```

### `.gitignore`

```diff
diff --git a/.gitignore b/.gitignore
index a005955d..d13d4eb5 100644
--- a/.gitignore
+++ b/.gitignore
@@ -103,4 +103,8 @@ outputs/llms-full/files/support.quo.com.txt
 # Local scratch and vendor mirrors previously rejected by secret protection.
 tmp/
+
+# API public-tree transaction sidecars contain pending publication snapshots.
+.tree.json.lock
+.tree.json.publication.json
 outputs/llms-full/files/docs.cloudbase.net.txt
 outputs/llms-full/files/prismatic.io__docs.txt
```

### `CLAUDE.md`

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index 5819d949..9dfbfffe 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -6,7 +6,8 @@ Monorepo for the LLMS-Explorer platform: accounts, metering, hosted MCP gateway,

 - `api/`: FastAPI backend with PostgreSQL ledger, WebAuthn/OAuth auth, API keys (Argon2id), Stripe subscriptions, and quota enforcement.
-- `site/`: Astro + TypeScript static & SSR website styled with plain CSS (`site/src/styles/`, no CSS framework), 3D concept graph, and account pages.
+- `site/`: Astro + TypeScript static website with browser account islands styled with plain CSS (`site/src/styles/`, no CSS framework), 3D concept graph, and account pages.
 - `hub/`: Global AI Hub semantic ops, ChromaDB/SQLite docsets, Ollama embedding pools, MCP server (`global_ai_hub`).
 - `hub/research-expertise/`: Standalone Neo4j graph/CPU semantic projection and source-grounded research capture; see its `README.md` and `MCP.md`. Canonical packs remain authoritative.
+- `hub/skill-registry/`: Independently locked local skill router, immutable resource bundles, private/team hosted releases and opt-in candidate workers. See its `README.md`.
 - `llmsx/`: Python library and CLI for the llms.txt standard v2.
 - `.claude/commands/` & `.claude/skills/`: Agent commands and workflows (`/ldo`, `/lca`). Both live under `.claude/` so Claude Code (local and cloud sessions) loads them as project commands and skills.
@@ -35,4 +36,10 @@ Monorepo for the LLMS-Explorer platform: accounts, metering, hosted MCP gateway,
 - Existing legacy indexing/embedding/Ollama pauses are separate from this standalone CPU projection.
... 9 further diff lines omitted; full change is in Git.
```

### `GEMINI.md`

```diff
diff --git a/GEMINI.md b/GEMINI.md
index b8c013f2..58871f35 100644
--- a/GEMINI.md
+++ b/GEMINI.md
@@ -3,4 +3,4 @@
 Adhere to the following repo rules:
 1. **Caveman Mode**: Extreme brevity, technical density, diffs only for code changes, no conversational filler.
-2. **Verify Always**: Run `uv run --directory api --extra test pytest`, `uv run --directory hub pytest`, and `cd site && npm run build` to verify changes.
+2. **Verify Always**: Run `uv run --directory api --extra test pytest`, `HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests`, and `cd site && npm run build` to verify changes.
 3. **Ledger Guarantees**: Preserve Postgres `Numeric(12,6)` precision and append-only database triggers.
```

### `README.md`

```diff
diff --git a/README.md b/README.md
index 52194a93..9714001c 100644
--- a/README.md
+++ b/README.md
@@ -27,9 +27,11 @@ integration with separate repository access.
 |---|---|
 | `api/` | FastAPI backend handling PostgreSQL ledger, WebAuthn/OAuth auth, API keys, and metering. |
-| `site/` | Astro + TypeScript frontend (plain CSS): directory, 3D concept graph, and account portals. |
+| `site/` | Astro + TypeScript frontend (plain CSS): directory, 3D concept graph, and browser account portals. |
 | `hub/` | Global AI Hub semantic operations, docset refiner, vector/keyword indexing, and MCP server. |
 | `hub/research-expertise/` | Standalone canonical research capture, Neo4j graph and CPU semantic retrieval through a bounded MCP interface. |
+| `hub/skill-registry/` | Standalone source-bound skill lookup, immutable private/team releases and bounded optional optimizer workers. |
 | `llmsx/` | Python library and CLI for parsing, validating, and generating `llms.txt` standard v2 files. |
 | `concept-tree/` | Canonical hierarchical topic data (`tree.json`) that powers the 3D graph and topical navigation. |
+| `native/speculative-mlx/` | Optional Apple Silicon/CGO verifier sidecar; separate hardware/runtime prerequisites and qualification limits. |
 | `scripts/` | Python and shell utilities for tasks like tree merging, indexing, and snapshot refreshing. |
... 7 further diff lines omitted; full change is in Git.
```

### `api/.env.example`

```diff
diff --git a/api/.env.example b/api/.env.example
index 6e1e3582..d91c2f76 100644
--- a/api/.env.example
+++ b/api/.env.example
@@ -3,5 +3,5 @@
 #
 #     set -a && . ./.env && set +a
-#     ../hub/.venv/bin/python -m uvicorn explorer_api.main:app --port 8790
+#     uv run --frozen --extra test uvicorn explorer_api.main:app --port 8790
 #
 # The app never reads this file itself — secrets come from the environment only,
@@ -52,4 +52,6 @@ OAUTH_GOOGLE_SECRET=
 SMTP_HOST=
 SMTP_PORT=587
+# Positive socket timeout in seconds, including connection and TLS operations.
+SMTP_TIMEOUT_SECONDS=15
... 20 further diff lines omitted; full change is in Git.
```

### `api/alembic/versions/20261111_a7b8c9d0e1f2_donation_customer.py`

```diff
--- /dev/null
+++ api/alembic/versions/20261111_a7b8c9d0e1f2_donation_customer.py
@@ -0,0 +1,47 @@
+"""Persist donation-owned Stripe customers for the Customer Portal.
+
+Revision ID: a7b8c9d0e1f2
+Revises: f6a7b8c9d0e1
+"""
+from __future__ import annotations
+
+import sqlalchemy as sa
+from alembic import op
+
+revision = "a7b8c9d0e1f2"
+down_revision = "f6a7b8c9d0e1"
+branch_labels = None
... 34 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/anthropic_keys.py`

```diff
diff --git a/api/explorer_api/anthropic_keys.py b/api/explorer_api/anthropic_keys.py
index cb0340ff..c10c88a1 100644
--- a/api/explorer_api/anthropic_keys.py
+++ b/api/explorer_api/anthropic_keys.py
@@ -13,4 +13,5 @@ forces a test to reach the real network, and a route can wire in the real one.
 from __future__ import annotations

+import logging
 from typing import Protocol

@@ -20,4 +21,5 @@ from .settings import Settings

 HINT_LEN = 4
+log = logging.getLogger(__name__)


... 21 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/artifacts.py`

```diff
diff --git a/api/explorer_api/artifacts.py b/api/explorer_api/artifacts.py
index acf0cee3..f3ecdfda 100644
--- a/api/explorer_api/artifacts.py
+++ b/api/explorer_api/artifacts.py
@@ -32,5 +32,9 @@ here runs; this module never sees a request and never decides who anybody is.
 from __future__ import annotations

+import os
 import re
+import secrets
+import stat
+from contextlib import ExitStack, contextmanager
 from dataclasses import dataclass
 from pathlib import Path
@@ -169,5 +173,5 @@ def resolve(stores_root: Path | str, user_id: str, slug: str, relative: str) ->
     """
... 128 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/auth.py`

```diff
diff --git a/api/explorer_api/auth.py b/api/explorer_api/auth.py
index 966efc90..8212b2f8 100644
--- a/api/explorer_api/auth.py
+++ b/api/explorer_api/auth.py
@@ -27,4 +27,5 @@ from __future__ import annotations
 import base64
 import datetime as dt
+import logging
 import secrets
 from collections.abc import Mapping
@@ -53,4 +54,6 @@ from . import models as m
 from .settings import Settings

+_LOG = logging.getLogger(__name__)
+
 # --- cookie names and lifetimes ----------------------------------------------
... 103 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/billing.py`

```diff
diff --git a/api/explorer_api/billing.py b/api/explorer_api/billing.py
index b52c9655..8b5ee965 100644
--- a/api/explorer_api/billing.py
+++ b/api/explorer_api/billing.py
@@ -67,4 +67,6 @@ SIGNATURE_TOLERANCE_SECONDS = 300
 HANDLED_EVENTS: frozenset[str] = frozenset({
     "checkout.session.completed",
+    "checkout.session.async_payment_succeeded",
+    "checkout.session.async_payment_failed",
     "customer.subscription.created",
     "customer.subscription.updated",
@@ -94,6 +96,5 @@ DONATION_INTERVALS = ("once", "month")

 class InvalidDonationAmount(BillingError):
-    """A donation of zero or less — Stripe would reject it anyway, but this is
-    the clearer message and it avoids a round trip to find out."""
... 141 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/checkouts.py`

```diff
diff --git a/api/explorer_api/checkouts.py b/api/explorer_api/checkouts.py
index 8bdc2a03..fd93fe6f 100644
--- a/api/explorer_api/checkouts.py
+++ b/api/explorer_api/checkouts.py
@@ -30,4 +30,5 @@ import datetime as dt
 import importlib.util
 import json
+import logging
 import os
 import re
@@ -36,4 +37,6 @@ from pathlib import Path
 from typing import Any

+log = logging.getLogger(__name__)
+
 CACHE_SECONDS = 60
... 49 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/gateway.py`

```diff
diff --git a/api/explorer_api/gateway.py b/api/explorer_api/gateway.py
index 45338c2f..4626d458 100644
--- a/api/explorer_api/gateway.py
+++ b/api/explorer_api/gateway.py
@@ -35,4 +35,5 @@ from __future__ import annotations

 import json
+import logging
 import math
 import re
@@ -46,4 +47,5 @@ from typing import TYPE_CHECKING, Any, Protocol

 import httpx
+from sqlalchemy import select

 from . import ledger
... 144 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/keys.py`

```diff
diff --git a/api/explorer_api/keys.py b/api/explorer_api/keys.py
index 5cb87635..3f7676f0 100644
--- a/api/explorer_api/keys.py
+++ b/api/explorer_api/keys.py
@@ -48,4 +48,5 @@ from sqlalchemy.orm.attributes import set_committed_value

 from .models import KEY_SCOPES, ApiKey, User
+from .settings import DEFAULT_API_KEY_STAMP_TIMEOUT_SECONDS

 log = logging.getLogger(__name__)
@@ -103,4 +104,7 @@ _DUMMY_HASH: str | None = None
 ARGON2_CONCURRENCY = max(1, int(os.environ.get("EXPLORER_ARGON2_CONCURRENCY", "4")))
 _hash_gate = asyncio.Semaphore(ARGON2_CONCURRENCY)
+# Keep shielded workers alive until their threads finish, even after the request
+# waiting for them has been cancelled.
+_verification_tasks: set[asyncio.Task[bool]] = set()
... 66 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/ledger.py`

```diff
diff --git a/api/explorer_api/ledger.py b/api/explorer_api/ledger.py
index 707cbe60..476af050 100644
--- a/api/explorer_api/ledger.py
+++ b/api/explorer_api/ledger.py
@@ -31,4 +31,5 @@ from __future__ import annotations

 import datetime as dt
+import logging
 from collections.abc import Awaitable, Callable, Mapping
 from dataclasses import dataclass, field
@@ -37,4 +38,5 @@ from typing import Any

 from sqlalchemy import Date, Integer, cast, func, select
+from sqlalchemy.dialects.postgresql import insert
 from sqlalchemy.ext.asyncio import AsyncSession

... 38 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/main.py`

```diff
diff --git a/api/explorer_api/main.py b/api/explorer_api/main.py
index 26bd7623..3e35b036 100644
--- a/api/explorer_api/main.py
+++ b/api/explorer_api/main.py
@@ -84,5 +84,5 @@ def create_app(settings: Settings | None = None) -> FastAPI:
         allow_origins=list(settings.site_origins),
         allow_credentials=True,
-        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
+        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["authorization", "content-type", "accept", "x-requested-with"],
         max_age=600,
@@ -138,6 +138,8 @@ def create_app(settings: Settings | None = None) -> FastAPI:
         from an application bug.
         """
-        log.warning("database unavailable for %s %s", request.method,
-                    request.url.path, exc_info=exc)
... 6 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/models.py`

```diff
diff --git a/api/explorer_api/models.py b/api/explorer_api/models.py
index 7d744c72..e898fcd2 100644
--- a/api/explorer_api/models.py
+++ b/api/explorer_api/models.py
@@ -357,7 +357,10 @@ class Donation(Base):

     `user_id` is nullable: a donation does not require signing in. `status`
-    tracks the Stripe lifecycle (`pending` until `checkout.session.completed`,
+    tracks the Stripe lifecycle (`pending` until Stripe confirms payment,
     `active` while a monthly donation's subscription renews, `lapsed` on a
-    failed renewal, `canceled` when the donor cancels via the Portal).
+    failed renewal, `canceled` when the donor cancels via the Portal). A
+    canceled subscription stays canceled when older events arrive late.
+    `stripe_customer_id` keeps the owning donor's Portal reachable without a
+    legacy paid-plan Subscription.
     """
... 7 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/moderation.py`

```diff
diff --git a/api/explorer_api/moderation.py b/api/explorer_api/moderation.py
index e2d12f9e..5c0f19b9 100644
--- a/api/explorer_api/moderation.py
+++ b/api/explorer_api/moderation.py
@@ -62,5 +62,5 @@ from sqlalchemy import select
 from sqlalchemy.ext.asyncio import AsyncSession

-from . import models as m, trees
+from . import models as m, tree_publication, trees

 # --- the hub, imported read-only ---------------------------------------------
@@ -162,4 +162,12 @@ class NotAModerator(ModerationError):


+class PublicationBusy(ModerationError):
+    """A cooperating writer currently owns the public tree (409)."""
... 163 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/notify.py`

```diff
diff --git a/api/explorer_api/notify.py b/api/explorer_api/notify.py
index 716f3df1..b74177e1 100644
--- a/api/explorer_api/notify.py
+++ b/api/explorer_api/notify.py
@@ -2,5 +2,5 @@

 No provider is wired in by default: with ``smtp_host`` unset (the default),
-:func:`send_email` logs the message instead of sending it, so a dev environment
+:func:`send_email` records a skipped-delivery event instead of sending, so a dev environment
 or a deploy that has not configured SMTP still runs — it just does not mail
 anyone. Set ``SMTP_HOST``/``SMTP_PORT``/``SMTP_USER``/``SMTP_PASSWORD``/
@@ -10,4 +10,5 @@ anyone. Set ``SMTP_HOST``/``SMTP_PORT``/``SMTP_USER``/``SMTP_PASSWORD``/
 from __future__ import annotations

+import asyncio
 import logging
... 51 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/research.py`

```diff
diff --git a/api/explorer_api/research.py b/api/explorer_api/research.py
index b46794d8..2866a7c2 100644
--- a/api/explorer_api/research.py
+++ b/api/explorer_api/research.py
@@ -13,7 +13,7 @@ hub, the repo and the ``claude`` CLI, so the run is a child process of the API.

 There is no job worker in this service. The run is an asyncio task that owns
-its Job row: queued, then running, then done or failed. If the API restarts
-mid-run the task dies with it, and :func:`expire_stale` marks the orphaned row
-failed the next time anyone asks, so a dead run never reads as in progress.
+its Job row: queued, running, then done, failed or cancelled. Cancellation kills
+and reaps its process group before returning. If the API restarts mid-run,
+:func:`expire_stale` fails the orphaned row on the next write path.

 Only the concept and parent names enter the prompt, and only after
@@ -30,6 +30,8 @@ import re
... 175 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/routes/auth.py`

```diff
diff --git a/api/explorer_api/routes/auth.py b/api/explorer_api/routes/auth.py
index b1003779..44d6f71b 100644
--- a/api/explorer_api/routes/auth.py
+++ b/api/explorer_api/routes/auth.py
@@ -219,5 +219,6 @@ async def oauth_callback(provider: str, request: Request, session: SessionDep,
     # Both halves must be present, equal, and *ours*. Equality alone proves
     # nothing — an attacker who can set a cookie can set the query string too.
-    if not code or not state or not cookie_state or not hmac.compare_digest(state, cookie_state):
+    if (not code or not state or not cookie_state or not state.isascii()
+            or not cookie_state.isascii() or not hmac.compare_digest(state, cookie_state)):
         raise HTTPException(status.HTTP_400_BAD_REQUEST, "the sign-in did not check out")
     try:
```

### `api/explorer_api/routes/contribute.py`

```diff
diff --git a/api/explorer_api/routes/contribute.py b/api/explorer_api/routes/contribute.py
index 9c6118b6..f55c16f4 100644
--- a/api/explorer_api/routes/contribute.py
+++ b/api/explorer_api/routes/contribute.py
@@ -133,4 +133,5 @@ async def contribute(
     skill_policy = skills.SKILL_POLICY["concept-abstract-mini"]
     run_request = skills.RunRequest(input=text, concept=concept)
+    job = await skills._reserve_job(session, principal, text, skill_policy)
     try:
         pass_output, in_tokens, out_tokens = await skills._run_passes(
@@ -138,25 +139,19 @@ async def contribute(
         )
     except gw.GatewayRefusal:
+        job.status = "failed"
+        job.finished_at = dt.datetime.now(dt.UTC)
+        await session.commit()
... 29 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/routes/mcp.py`

```diff
diff --git a/api/explorer_api/routes/mcp.py b/api/explorer_api/routes/mcp.py
index d5897794..f97c4e22 100644
--- a/api/explorer_api/routes/mcp.py
+++ b/api/explorer_api/routes/mcp.py
@@ -95,5 +95,5 @@ async def _read_message(request: Request) -> Any:
     try:
         return json.loads(raw)
-    except json.JSONDecodeError as exc:
+    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
         raise gw.BadRequest("the request body is not JSON") from exc

```

### `api/explorer_api/routes/proposals.py`

```diff
diff --git a/api/explorer_api/routes/proposals.py b/api/explorer_api/routes/proposals.py
index bea6f6df..87657c8c 100644
--- a/api/explorer_api/routes/proposals.py
+++ b/api/explorer_api/routes/proposals.py
@@ -180,5 +180,5 @@ async def _decide(
         await session.rollback()
         raise _http(exc) from exc
-    await session.commit()
+    await moderation.commit_decision(session)
     return ProposalPublic(**moderation.public_view(proposal))

```

### `api/explorer_api/routes/skills.py`

```diff
diff --git a/api/explorer_api/routes/skills.py b/api/explorer_api/routes/skills.py
index b0e7ea09..c5f3b433 100644
--- a/api/explorer_api/routes/skills.py
+++ b/api/explorer_api/routes/skills.py
@@ -35,4 +35,5 @@ otherwise leak money:
 from __future__ import annotations

+import asyncio
 import datetime as dt
 from collections.abc import Callable, Mapping
@@ -51,4 +52,10 @@ from .. import models as m
 from .. import secrets_crypto
 from ..db import get_session
+from ..settings import (
+    SHOWCASE_LLM_TIMEOUT_SECONDS,
+    SHOWCASE_MAX_INPUT_CHARS,
... 112 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/settings.py`

```diff
diff --git a/api/explorer_api/settings.py b/api/explorer_api/settings.py
index 90667401..68988d9b 100644
--- a/api/explorer_api/settings.py
+++ b/api/explorer_api/settings.py
@@ -43,4 +43,19 @@ DEFAULT_STORES_ROOT = Path.home() / ".llms-explorer" / "stores"
 MIN_SESSION_SECRET_LEN = 32

+# Public operating defaults share this module even where a compatibility
+# constant is exported by a route/helper. Protocol and cryptographic format
+# invariants remain owned by their libraries.
+SHOWCASE_MODEL = "claude-sonnet-5"
+SHOWCASE_MAX_INPUT_CHARS = 4000
+SHOWCASE_MAX_OUTPUT_TOKENS = 4000
+SHOWCASE_LLM_TIMEOUT_SECONDS = 120.0
+DEFAULT_RESEARCH_MAX_RUNNING = 2
+DEFAULT_RESEARCH_TIMEOUT_SECONDS = 3600
... 14 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/tree_publication.py`

```diff
--- /dev/null
+++ api/explorer_api/tree_publication.py
@@ -0,0 +1,259 @@
+"""Recoverable coordination of a public tree file and a caller-owned SQL transaction.
+
+Cooperating API writers share one advisory lock. Publication precedes commit,
+so readers may briefly see staged bytes. A private fsynced journal allows the
+next writer to resolve interrupted or ambiguous commits against PostgreSQL.
+This does not make the filesystem and database one atomic transaction.
+"""
+from __future__ import annotations
+
+import asyncio
+import base64
+import fcntl
+import hashlib
... 246 further diff lines omitted; full change is in Git.
```

### `api/explorer_api/trees.py`

```diff
diff --git a/api/explorer_api/trees.py b/api/explorer_api/trees.py
index 6ae95d78..c107cac2 100644
--- a/api/explorer_api/trees.py
+++ b/api/explorer_api/trees.py
@@ -50,5 +50,5 @@ from sqlalchemy import select
 from sqlalchemy.ext.asyncio import AsyncSession

-from . import ledger, models as m
+from . import ledger, models as m, tree_publication

 if TYPE_CHECKING:  # pragma: no cover - typing only
@@ -219,7 +219,13 @@ def read_nodes(path: Path) -> list[dict[str, Any]]:

 def write_nodes(path: Path, nodes: list[dict[str, Any]]) -> None:
-    """Write ``nodes`` atomically, in the hub's own format."""
-    path.parent.mkdir(parents=True, exist_ok=True)
... 30 further diff lines omitted; full change is in Git.
```

### `api/pyproject.toml`

```diff
diff --git a/api/pyproject.toml b/api/pyproject.toml
index 162f373e..1719c87a 100644
--- a/api/pyproject.toml
+++ b/api/pyproject.toml
@@ -13,5 +13,6 @@ dependencies = [
     "uvicorn>=0.30",
     "pydantic>=2.7",
-    "pydantic-settings>=2.2",
+    # Verified supported baseline exporting the NoDecode annotation we import.
+    "pydantic-settings>=2.15.0",
     "sqlalchemy[asyncio]>=2.0.30",
     "alembic>=1.13",
@@ -22,5 +23,6 @@ dependencies = [
     "httpx>=0.27",
     "argon2-cffi>=23.1.0",
-    "stripe>=10.0.0",
... 4 further diff lines omitted; full change is in Git.
```

### `api/tests/test_anthropic_key_validator_lifecycle.py`

```diff
--- /dev/null
+++ api/tests/test_anthropic_key_validator_lifecycle.py
@@ -0,0 +1,56 @@
+"""BYOK validation must close its owned HTTP client on every result."""
+import logging
+from types import SimpleNamespace
+
+import anthropic
+import httpx
+import pytest
+
+from explorer_api import anthropic_keys
+
+
+class FakeClient:
+    def __init__(self, outcome):
... 43 further diff lines omitted; full change is in Git.
```

### `api/tests/test_artifacts_audit.py`

```diff
--- /dev/null
+++ api/tests/test_artifacts_audit.py
@@ -0,0 +1,144 @@
+"""Private artifact writes cannot follow a planted link before rejecting it."""
+
+from pathlib import Path
+
+import pytest
+
+from explorer_api import artifacts
+
+
+@pytest.mark.parametrize("link_at", ["leaf", "section", "artifact", "user"])
+def test_write_refuses_symlinks_without_touching_outside(tmp_path, link_at):
+    stores = tmp_path / "stores"
+    outside = tmp_path / "outside"
... 131 further diff lines omitted; full change is in Git.
```

### `api/tests/test_auth_audit.py`

```diff
--- /dev/null
+++ api/tests/test_auth_audit.py
@@ -0,0 +1,104 @@
+"""Regression cases for authentication trust boundaries and safe diagnostics."""
+
+from __future__ import annotations
+
+import logging
+
+import httpx
+import pytest
+from sqlalchemy import func, select
+
+from explorer_api import auth, models as m
+from test_auth import SoftAuthenticator, app, client, settings, sign_in
+
... 91 further diff lines omitted; full change is in Git.
```

### `api/tests/test_billing_audit.py`

```diff
--- /dev/null
+++ api/tests/test_billing_audit.py
@@ -0,0 +1,262 @@
+"""Donation lifecycle regressions, using real PostgreSQL and a fake Stripe seam."""
+from __future__ import annotations
+
+import asyncio
+import datetime as dt
+import os
+import sys
+from decimal import Decimal
+from pathlib import Path
+from types import SimpleNamespace
+from unittest.mock import AsyncMock
+from uuid import uuid4
+
... 249 further diff lines omitted; full change is in Git.
```

### `api/tests/test_checkouts_audit.py`

```diff
--- /dev/null
+++ api/tests/test_checkouts_audit.py
@@ -0,0 +1,50 @@
+"""Malformed local metadata cannot hide valid sibling research reservations."""
+
+from __future__ import annotations
+
+import json
+import logging
+from pathlib import Path
+
+import pytest
+
+from explorer_api import checkouts
+
+
... 37 further diff lines omitted; full change is in Git.
```

### `api/tests/test_gateway_audit.py`

```diff
--- /dev/null
+++ api/tests/test_gateway_audit.py
@@ -0,0 +1,240 @@
+"""Gateway error accounting and concurrent admission against real PostgreSQL.
+
+The remote hub is controlled; the account locks, quota reads and ledger writes
+use this repository's ephemeral database fixture, with one session per caller.
+"""
+
+from __future__ import annotations
+
+import asyncio
+import json
+import logging
+from pathlib import Path
+from types import SimpleNamespace
... 227 further diff lines omitted; full change is in Git.
```

### `api/tests/test_hosted_skill_lifecycle.py`

```diff
--- /dev/null
+++ api/tests/test_hosted_skill_lifecycle.py
@@ -0,0 +1,81 @@
+"""Owned model transports close even when a showcase pass fails or is cancelled."""
+import asyncio
+from types import SimpleNamespace
+
+import anthropic
+import pytest
+
+from explorer_api.routes.skills import AnthropicClient, LlmUnavailable
+
+
+@pytest.mark.parametrize("outcome", ["success", "error", "empty", "cancel"])
+async def test_owned_provider_transport_closes(monkeypatch, outcome):
+    clients = []
... 68 further diff lines omitted; full change is in Git.
```

### `api/tests/test_hosted_skill_quota_atomicity.py`

```diff
--- /dev/null
+++ api/tests/test_hosted_skill_quota_atomicity.py
@@ -0,0 +1,112 @@
+"""Daily model allowances are reserved before provider work across both entrypoints."""
+import asyncio
+from types import SimpleNamespace
+
+import pytest
+from sqlalchemy import func, select
+from sqlalchemy.ext.asyncio import async_sessionmaker
+from starlette.requests import Request
+
+from explorer_api import gateway, models as m, plans
+from explorer_api.routes import contribute, skills
+
+
... 99 further diff lines omitted; full change is in Git.
```

### `api/tests/test_keys_audit.py`

```diff
--- /dev/null
+++ api/tests/test_keys_audit.py
@@ -0,0 +1,120 @@
+"""Bound actual hash-worker concurrency, including cancelled request waiters."""
+
+from __future__ import annotations
+
+import asyncio
+import logging
+import threading
+
+import pytest
+from argon2.exceptions import VerifyMismatchError
+from sqlalchemy import select
+from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
+
... 107 further diff lines omitted; full change is in Git.
```

### `api/tests/test_ledger_audit.py`

```diff
--- /dev/null
+++ api/tests/test_ledger_audit.py
@@ -0,0 +1,96 @@
+"""Isolated PostgreSQL regression probes for ledger debits and audit events."""
+
+from __future__ import annotations
+
+import asyncio
+import logging
+from decimal import Decimal
+from uuid import uuid4
+
+from sqlalchemy import func, select
+from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
+
+from explorer_api import ledger, models as m
... 83 further diff lines omitted; full change is in Git.
```

### `api/tests/test_moderation_audit.py`

```diff
--- /dev/null
+++ api/tests/test_moderation_audit.py
@@ -0,0 +1,323 @@
+"""Publication boundary regressions using temporary trees only."""
+from __future__ import annotations
+
+import hashlib
+import json
+from pathlib import Path
+
+import pytest
+
+from explorer_api import moderation, trees
+
+
+@pytest.mark.parametrize("wrapped", [False, True])
... 310 further diff lines omitted; full change is in Git.
```

### `api/tests/test_notify_hardening.py`

```diff
--- /dev/null
+++ api/tests/test_notify_hardening.py
@@ -0,0 +1,103 @@
+"""Mail transport stays bounded and logs outcomes without subscriber identifiers."""
+import asyncio
+import logging
+from types import SimpleNamespace
+
+import pytest
+
+from explorer_api import notify
+
+
+class FakeSMTP:
+    def __init__(self, host, port, *, timeout=None):
+        self.host, self.port, self.timeout = host, port, timeout
... 90 further diff lines omitted; full change is in Git.
```

### `api/tests/test_research_audit.py`

```diff
--- /dev/null
+++ api/tests/test_research_audit.py
@@ -0,0 +1,272 @@
+"""Research process ownership survives cancellation of its asyncio waiter."""
+
+import asyncio
+import os
+import signal
+import stat
+import sys
+
+import pytest
+
+from explorer_api import research
+
+
... 259 further diff lines omitted; full change is in Git.
```

### `api/tests/test_route_boundary_audit.py`

```diff
--- /dev/null
+++ api/tests/test_route_boundary_audit.py
@@ -0,0 +1,90 @@
+"""Malformed public inputs remain client errors and browser API methods work."""
+from types import SimpleNamespace
+
+import httpx
+import pytest
+from fastapi import HTTPException
+from pydantic import SecretStr
+from starlette.requests import Request
+
+from explorer_api import auth, gateway
+from explorer_api.main import create_app
+from explorer_api.routes import auth as auth_routes
+from explorer_api.routes.mcp import _read_message
... 77 further diff lines omitted; full change is in Git.
```

### `api/tests/test_trees_audit.py`

```diff
--- /dev/null
+++ api/tests/test_trees_audit.py
@@ -0,0 +1,38 @@
+"""Fork snapshot regression using temporary storage and actual PostgreSQL."""
+from __future__ import annotations
+
+import hashlib
+import json
+from pathlib import Path
+
+from explorer_api import models as m, trees
+from explorer_api.settings import Settings
+
+
+async def test_fork_copies_the_same_snapshot_that_it_hashes(session, database_url, tmp_path,
+                                                          monkeypatch):
... 25 further diff lines omitted; full change is in Git.
```

### `api/uv.lock`

```diff
diff --git a/api/uv.lock b/api/uv.lock
index 19edba57..09ec75e6 100644
--- a/api/uv.lock
+++ b/api/uv.lock
@@ -228,9 +228,9 @@ wheels = [
 [[package]]
 name = "certifi"
-version = "2026.7.22"
+version = "2026.10.23"
 source = { registry = "https://pypi.org/simple" }
-sdist = { url = "https://files.pythonhosted.org/packages/a3/c2/24167ea9858356b47a87a50d39908bfdb72ceeefe0041586e704e5376b3a/certifi-2026.7.22.tar.gz", hash = "sha256:741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55", size = 138112, upload-time = "2026-07-22T03:35:12.644Z" }
+sdist = { url = "https://files.pythonhosted.org/packages/fd/11/b524cbd9bbdaca58608e4cf4053fd463417549e1959fa8d3aa18319f9555/certifi-2026.10.23.tar.gz", hash = "sha256:a9895e6e2758b371e0545e321a3a8fd1fcfd9829ada8824a936dfb16aaaf36cd", size = 136225, upload-time = "2026-10-23T11:36:16.478Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/0b/a7/71ac2cff56fec219ed242bb11b8efb69fcc4bec75db06fb7bfe35de520e6/certifi-2026.7.22-py3-none-any.whl", hash = "sha256:62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775", size = 136983, upload-time = "2026-07-22T03:35:11.276Z" },
+    { url = "https://files.pythonhosted.org/packages/32/d1/a3652fe2c19134d0d15922177821d863cbd7e842d53a21bbe7e8e3a1b5ac/certifi-2026.10.23-py3-none-any.whl", hash = "sha256:e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1", size = 135082, upload-time = "2026-10-23T11:36:14.763Z" },
 ]
... 40 further diff lines omitted; full change is in Git.
```

### `docs/ARCHITECTURE.md`

```diff
diff --git a/docs/ARCHITECTURE.md b/docs/ARCHITECTURE.md
index 7ee1fe77..7dd76945 100644
--- a/docs/ARCHITECTURE.md
+++ b/docs/ARCHITECTURE.md
@@ -24,5 +24,5 @@ graph TD

 1. **Frontend (`site/`)**:
-   - Built with Astro (SSR + Static generation) and TypeScript, styled with plain CSS (`site/src/styles/`).
+   - Built with Astro static generation and TypeScript, styled with plain CSS (`site/src/styles/`).
    - Hosts the directory of llms.txt sources, 3D force-directed concept graph, documentation viewers, and account islands.
    - Postbuild tools generate twin format endpoints and llms.txt indexes.
@@ -67,2 +67,18 @@ checks grant no native evidence qualification. Search rechecks canonical hashes
 and returns unreviewed status explicitly. See [the package guide](../hub/research-expertise/README.md)
 and [the native concept contracts](architecture/concept-knowledge-contracts.md).
+
+## Skill source and immutable release decision
... 14 further diff lines omitted; full change is in Git.
```

### `docs/COMPONENTS.md`

```diff
diff --git a/docs/COMPONENTS.md b/docs/COMPONENTS.md
index fae0bb7e..a2ba91d8 100644
--- a/docs/COMPONENTS.md
+++ b/docs/COMPONENTS.md
@@ -5,5 +5,7 @@
 - **Entrypoint**: `explorer_api/main.py` (`create_app()`)
 - **Database Layer**: `explorer_api/models.py`, `explorer_api/db.py`
-  - Models: `User`, `Passkey`, `OAuthAccount`, `ApiKey`, `Plan`, `Subscription`, `Credit`, `CreditGrant`, `Price`, `LedgerEntry`, `Job`, `JobEvent`, `Artifact`, `Proposal`, `Tree`, `Moderation`.
+  - Models cover accounts, keys, the single free plan, donations, legacy subscriptions,
+    credits/ledger, jobs/events, artifacts/trees, proposals/moderation and private skill releases/grants.
+    `models.py` owns the exact table definitions.
 - **Authentication**: `explorer_api/auth.py`
   - Signed session cookies (`itsdangerous`), WebAuthn ceremony handling (`webauthn`), OAuth flow.
@@ -13,5 +15,9 @@
   - Atomic debiting, unit conversions, immutable spend history.
 - **Stripe Billing**: `explorer_api/billing.py`
... 44 further diff lines omitted; full change is in Git.
```

### `docs/DEVELOPMENT.md`

```diff
diff --git a/docs/DEVELOPMENT.md b/docs/DEVELOPMENT.md
index 085b71f2..b3f633f3 100644
--- a/docs/DEVELOPMENT.md
+++ b/docs/DEVELOPMENT.md
@@ -94,2 +94,16 @@ downloads and production corpus writes are not prerequisites. Installation,
 capture, reingestion and model migration are separate operations documented in
 [the package guide](../hub/research-expertise/README.md).
+
+## Standalone skill registry
+
+```sh
+uv sync --directory hub/skill-registry --frozen --all-extras
+uv run --directory hub/skill-registry --frozen pytest -q
+uv run --directory hub/skill-registry --frozen ruff check src tests
+```
+
... 5 further diff lines omitted; full change is in Git.
```

### `docs/MCP.md`

```diff
diff --git a/docs/MCP.md b/docs/MCP.md
index 68e4a5d5..7beb0f07 100644
--- a/docs/MCP.md
+++ b/docs/MCP.md
@@ -43,2 +43,16 @@ point at the stable installed entrypoint; reload the client to discover new
 tools. Keep credentials in the private connection file. Arbitrary reads through
 the separate official Neo4j MCP bypass application freshness checks.
+
+## 4. Local skill registry (`skill-registry`)
+
+`hub/skill-registry/src/skill_registry/mcp_server.py` registers the source lookup,
+release and candidate-job tools. Its decorators are authoritative for the current
+names and mutation annotations. `skills_status` and `skill_load` read metadata
+and bounded source spans. `skill_lookup` may refresh the derived lexical catalog.
+Release packaging, remote fetch/publication and optimizer queue/policy operations
+are explicitly mutating; neither lookup nor HTTP upload runs an optimizer.
... 5 further diff lines omitted; full change is in Git.
```

### `docs/TESTING.md`

```diff
diff --git a/docs/TESTING.md b/docs/TESTING.md
index 21e38ce5..497790a7 100644
--- a/docs/TESTING.md
+++ b/docs/TESTING.md
@@ -12,5 +12,5 @@ The test suite enforces the following principles:
 1. **API Tests (`api/tests/`)**:
    - `test_auth.py`: OAuth, passkey registration/authentication, session security.
-   - `test_billing.py`: Stripe webhooks, subscription sync, invoice idempotency.
+   - `test_billing.py`: Donation webhooks, Customer Portal and event idempotency.
    - `test_gateway.py`: API key authentication, rate limiting, ledger spend tracking.
    - `test_keys.py`: Argon2id key generation, verification, and revocation.
@@ -72,2 +72,20 @@ errors and logs. Passing unit tests does not measure research answer quality,
 retrieval recall or semantic entailment. Those require separate datasets and
 independent evidence review.
+
+## Skill registry and hosted optimizer broker
... 16 further diff lines omitted; full change is in Git.
```

### `docs/codebase-overview.md`

```diff
diff --git a/docs/codebase-overview.md b/docs/codebase-overview.md
index 4c2ede72..11fa965a 100644
--- a/docs/codebase-overview.md
+++ b/docs/codebase-overview.md
@@ -39,5 +39,5 @@ This document maps the entire repository structure by directory and module.

 - `src/pages/`: Astro routing pages (`index.astro`, `directory/`, `tree/`, `account.astro`, `keys.astro`, `login.astro`, `usage.astro`, `contribute.astro`, `proposals.astro`, `moderate.astro`, `/api/contribute` reader).
-- `src/components/`: Reusable Astro/React components (Account navigation, 3D Canvas, Search).
+- `src/components/`: Reusable Astro components (Account navigation, 3D Canvas, Search).
 - `src/layouts/`: Base HTML page layouts.
 - `tools/`: Build scripts (`twins.py`, `build_llms.py`).
@@ -86,2 +86,30 @@ This document maps the entire repository structure by directory and module.
 The package guide and [wiki entry](subsystems/research-expertise.md) describe
 command ownership and preserve the distinction between capture and validation.
+
+## Skill registry and optimizer broker
... 26 further diff lines omitted; full change is in Git.
```

### `docs/high_signal_file_index.json`

```diff
diff --git a/docs/high_signal_file_index.json b/docs/high_signal_file_index.json
index 00ca8900..cf19214c 100644
--- a/docs/high_signal_file_index.json
+++ b/docs/high_signal_file_index.json
@@ -1,5 +1,5 @@
 {
-  "version": "1.1.0",
-  "generated_at": "2026-11-11T12:40:00Z",
+  "version": "1.3.0",
+  "generated_at": "2026-11-11T17:29:16Z",
   "files": [
     {
@@ -31,5 +31,5 @@
       "path": "api/explorer_api/billing.py",
       "component": "api",
-      "summary": "Stripe checkout session creation, customer portal links, webhook processing, and invoice credit grants."
... 63 further diff lines omitted; full change is in Git.
```

### `docs/index.md`

```diff
diff --git a/docs/index.md b/docs/index.md
index 7b8b68c1..58326cea 100644
--- a/docs/index.md
+++ b/docs/index.md
@@ -9,4 +9,5 @@ repository. The rules are in [`CLAUDE.md`](CLAUDE.md).

 - Research capture, evidence boundaries and local Neo4j retrieval: [[research-expertise]]
+- Skill sources, private releases and optional optimizer jobs: [[skill-registry]]
 - Site styling, the logo or the concept tree page: [[site-design-tokens]]
 - Everything else: the older flat documents in this folder (`ARCHITECTURE.md`, `COMPONENTS.md`, `DEVELOPMENT.md`) until pages cover it.
@@ -23,4 +24,6 @@ repository. The rules are in [`CLAUDE.md`](CLAUDE.md).

 - [[research-expertise]] -- canonical capture, projection, retrieval and validation boundaries
+- [[skill-registry]] -- source lookup, private releases and candidate-worker boundaries
+- [[tree-publication]] -- API proposal commits, file journals and recovery limits

... 1 further diff lines omitted; full change is in Git.
```

### `docs/logging.md`

```diff
diff --git a/docs/logging.md b/docs/logging.md
index 08fb5bb0..8db7b28c 100644
--- a/docs/logging.md
+++ b/docs/logging.md
@@ -9,5 +9,5 @@
 ## Log Levels

-- `DEBUG`: Detailed execution tracing, SQL statement inspection in dev.
+- `DEBUG`: Detailed execution tracing without SQL parameters or private content.
 - `INFO`: Lifecycle milestones (app startup, job dispatched, invoice paid).
 - `WARNING`: Recoverable errors, database reconnect attempts, quota limits hit, unknown webhook events.
@@ -20,4 +20,16 @@
 - `hub/`: `logs/pipeline_manager.log`, launchd agent stdout/stderr.

+## API event safety
+
... 12 further diff lines omitted; full change is in Git.
```

### `docs/onboarding.md`

```diff
diff --git a/docs/onboarding.md b/docs/onboarding.md
index 497ddb34..a1d61c38 100644
--- a/docs/onboarding.md
+++ b/docs/onboarding.md
@@ -1,5 +1,5 @@
 # Contributor Onboarding

-Welcome to LLMS-Explorer! Follow this guide to set up your environment in under 10 minutes.
+Welcome to LLMS-Explorer! Use the owning package setup below; private library access and optional runtimes have separate prerequisites.

 ## 1. Install Tools
@@ -8,5 +8,5 @@ Ensure you have installed:
 - [uv](https://docs.astral.sh/uv/) (Python package manager)
 - [Node.js 22.18+](https://nodejs.org/) & npm
-- [PostgreSQL](https://www.postgresql.org/) (optional if running tests, `conftest.py` locates `initdb`)
+- [PostgreSQL](https://www.postgresql.org/) (required for real database tests; fixtures locate installed `initdb`/`pg_ctl` or use an explicit test maintenance DSN)
... 2 further diff lines omitted; full change is in Git.
```

### `docs/subsystems/skill-registry.md`

```diff
--- /dev/null
+++ docs/subsystems/skill-registry.md
@@ -0,0 +1,36 @@
+---
+title: Skill sources and private releases
+type: subsystem
+created: 2026-11-11
+updated: 2026-11-11
+sources:
+  - code: hub/skill-registry/src/skill_registry/catalog.py
+  - code: hub/skill-registry/src/skill_registry/bundles.py
+  - code: hub/skill-registry/src/skill_registry/worker.py
+  - code: api/explorer_api/routes/skill_registry.py
+  - code: api/explorer_api/optimizer_jobs.py
+verified_at: c458299c
+---
... 23 further diff lines omitted; full change is in Git.
```

### `docs/subsystems/tree-publication.md`

```diff
--- /dev/null
+++ docs/subsystems/tree-publication.md
@@ -0,0 +1,48 @@
+---
+title: API tree publication
+type: subsystem
+created: 2026-11-11
+updated: 2026-11-11
+sources:
+  - code: api/explorer_api/tree_publication.py
+  - code: api/explorer_api/moderation.py
+  - code: api/explorer_api/trees.py
+  - code: api/explorer_api/routes/proposals.py
+verified_at: c458299c
+---
+
... 35 further diff lines omitted; full change is in Git.
```

### `scripts/rotate_workflow_logs.py`

```diff
diff --git a/scripts/rotate_workflow_logs.py b/scripts/rotate_workflow_logs.py
index 15894794..eb9881b1 100755
--- a/scripts/rotate_workflow_logs.py
+++ b/scripts/rotate_workflow_logs.py
@@ -1,31 +1,128 @@
 #!/usr/bin/env python3
-"""Rotate memory.md and prompts.md if they exceed 200KB."""
+"""Archive oversized workflow logs and retain their newest complete version sections."""

-import shutil
-from datetime import datetime, UTC
+import argparse
+import logging
+import os
+import re
+import stat
... 133 further diff lines omitted; full change is in Git.
```

### `scripts/tests/test_rotate_workflow_logs.py`

```diff
--- /dev/null
+++ scripts/tests/test_rotate_workflow_logs.py
@@ -0,0 +1,207 @@
+"""Workflow-log rotation must shorten current logs without losing their history."""
+import importlib.util
+from pathlib import Path
+
+import pytest
+
+SOURCE = Path(__file__).resolve().parents[1] / "rotate_workflow_logs.py"
+spec = importlib.util.spec_from_file_location("rotate_workflow_logs", SOURCE)
+rotation = importlib.util.module_from_spec(spec)
+spec.loader.exec_module(rotation)
+
+
+@pytest.fixture
... 194 further diff lines omitted; full change is in Git.
```

### `site/tests/test_ci_config.py`

```diff
diff --git a/site/tests/test_ci_config.py b/site/tests/test_ci_config.py
index ecb71ae4..0796d74f 100644
--- a/site/tests/test_ci_config.py
+++ b/site/tests/test_ci_config.py
@@ -19,4 +19,5 @@ def test_workflow_runs_build_tests_and_lint_gate():
     steps = _run_steps(wf)
     assert "sh hub/bootstrap.sh" in steps and "npm run build" in steps
+    assert "cd site && npm run check" in steps, "Astro build does not type-check TypeScript"
     assert "pytest site/tests" in steps
     assert "llms_lint.py check site/dist/llms.txt" in steps and "--json" in steps
```

## Blind re-audit result

First gate:51 files/13,729lines,3 corroborated Medium findings (optional timestamp
pool wait, NoDecode floor, Stripe floor). They were fixed in the one extra iteration.
Accounting precision was also corrected after coordinator/owner corroboration of
observable persisted-versus-charged mismatch; the independent reviewer had graded it Low.
Second gate:51 files/13,737lines, High FINAL-F1 and Medium FINAL-F2 remained. The additional
minimum-Anthropic check corroborated one Medium residual. No CLEAN claim is made.

## Summary

2iterations ·18fix-track passes +conditional M5 ·default profile ·Final C/H/M/L:0/1/2/1 ·Verify:PASS ·Status:BLIND-AUDIT-DISSENT

## Snapshot and rollback

Preimages are under
`/Users/mitch/.claude/skill-consolidation/backups/llms-explorer-cdo-20261111T163600Z/`.
The initial50 source files were copied before writes. Example literal source restore:

```sh
cp /Users/mitch/.claude/skill-consolidation/backups/llms-explorer-cdo-20261111T163600Z/api/explorer_api/gateway.py /Users/mitch/dev/llms-explorer-wt-01a1ca5e/api/explorer_api/gateway.py
```

The complete explicit preimage restore/removal manifest is
[code-deep-optimizer-2026-11-11-followup-rollback.txt](code-deep-optimizer-2026-11-11-followup-rollback.txt). Newly created files have no preimage;
its single-file removal commands are for a deliberate rollback, not cleanup. The
new donation migration must be downgraded only after checking retained customer data;
its reversible upgrade/downgrade was tested on temporary databases. Shipping rollback
and installed-state acceptance are owned by delivery and recorded separately.

## Index and memory-central

index:skipped (--no-sync; paused semantic/indexing/Ollama work preserved).
Static navigation and31-source path index were updated and checked. Hub semantic
lookup was unavailable (`No module named numpy`); direct bounded source reads were used.

memory-central: bounded lessons/conventions intake returned no task-changing record;
source and prior audit evidence governed. No model-backed refresh or memory store
rewrite ran; parent owns versioned prompt/memory continuation and tracker closure.

## Coverage and continuation

Initial inventory664:17 unchanged prior reviews,50 selected and597 deferred. A new
necessary publication helper raises this run to51 unique source files. Current inventory
682 includes newly added tests/migration/helper; ledger covers68 and leaves614 pending.
The helper counts57 record operations because6 final source hashes were refreshed;
it is not57 unique reviewed files. Matching ledger hashes prove review coverage,
not absence of findings. The residual paths must be explicitly selected first because
the unchanged-file planner otherwise skips their reviewed hashes.

[code-deep-optimizer-2026-11-11-followup-next-plan.json](code-deep-optimizer-2026-11-11-followup-next-plan.json) contains the full614-path remainder,
known residuals first, and actual `.astro`/`.css` enumeration omissions. Snapshot/archive
copies are not relabeled as live production risk. The prior17-file audit remains dated
history with its own accepted fixes, retractions and dissent; this run does not certify
it or the rest of the monorepo clean.

Follow-up task: close three corroborated residuals, TASK-1346:
https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/TASK-1346

Bootstrap48-path existence inventory and its accuracy/coverage limits are documented
in [the bootstrap follow-up](../repo-bootstrap-audit-2026-11-11-followup.md). Publication
coordinates cooperating API writers through a recoverable journal; staged bytes may
briefly be visible before SQL commit and external noncooperating writers remain outside
the advisory lock. Offline tests do not establish deployed behavior; delivery records
must verify the actual merged revision and live behavior before completion.

The verbatim helper receipt below counts **57 record operations**, including six
hash refreshes. This run reviewed **51 distinct files**, with **68 of 682** files
covered cumulatively and **614** still pending. The per-pass `Files:57` counters
do not establish 57 distinct reviewed files.

## Passes that ran (receipt)

| Pass | State | Files | Note |
|---|---|---|---|
| C1 | ran | 57 |  |
| C2 | ran | 57 |  |
| C3 | ran | 57 |  |
| S1 | ran | 57 |  |
| S2 | ran | 57 |  |
| S3 | ran | 57 |  |
| S4 | ran | 57 |  |
| S5 | ran | 57 |  |
| P1 | ran | 57 |  |
| P2 | ran | 57 |  |
| M1 | ran | 57 |  |
| M2 | ran | 57 |  |
| M3 | ran | 0 | Reviewed account/API versus standalone registry boundaries, canonical files versus derived catalogs, central typed settings and reusable importable packages. Existing environment/config equivalents retained; broad unreviewed runtime/UI settings and operations registry are not certified. |
| M4 | ran | 57 |  |
| T1 | ran | 57 |  |
| T2 | ran | 0 | Isolated installed API/registry and site lock vulnerability scans reviewed; API three transitive pins repaired for eight unique advisories. Minimum-version NoDecode/Stripe contracts repaired without further version changes; isolated minimum compatibility smoke passed. Anthropic0.40 allowed floor lacks validator.models API: confirmed Medium residual after second blind round, not repaired under gate cap. llms-txt/editables/other manifests and Endor risk tools remain unavailable or outside scan coverage. |
| T3 | ran | 0 | Existing Python owning-package frozen environments, Ruff, pytest, CI and static doc index checked. Added existing Astro check to full site CI and standalone registry Dependabot; no duplicate framework/scaffolding. Broader tooling inventory remains partial. |
| T4 | ran | 0 | Reviewed suite eligibility and observed owning-package timings. Temporary PostgreSQL plus global fixtures and real subprocess cancellation witnesses require isolation; no equivalence-backed parallel runner change or performance claim made. No assertions removed or coverage thresholds invented. |
| M5 | ran | 0 | Actual registry CLI help and protocol input-error/signal fixtures, workflow-log CLI help/bad-argument/swap/concurrency/temp-directory tests exercised in owned environments. No real optimizer/model, SMTP, hosted-account or private research launch. |

Fix-track passes that ran: 18 of 18 (+1 conditional)
Mode: incremental   Status: BLIND-AUDIT-DISSENT
Files reviewed this run: 57
Source files covered by the ledger now: 68 of 682
Still unreviewed or changed since review: 614
