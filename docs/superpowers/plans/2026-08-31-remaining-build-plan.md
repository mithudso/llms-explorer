# LLMS-Explorer — the rest of the build (steps 3–6)

**Written:** 2026-08-31 · **Authority:** `docs/site/00-platform-design.md` §10 (build order) and its decisions D1–D9 · **Status:** step 3 in flight, steps 4–6 not started

This is the whole remaining plan in one file, so the work survives any single
session. Steps 1 and 2 are done and live at https://llms-explorer.com. Step 3
has a detailed per-task plan of its own
(`2026-08-31-site-step3-accounts-mcp-governance.md`); the step-3 section here
summarises it and records progress. Steps 4–6 are planned to the level a fresh
session could pick up and expand into task plans of their own.

---

## YOU ARE HERE

```
step 1  content + dog food + CI gate ................ SHIPPED  (accepted 2026-08-31, live)
step 2  tree + directory + demo ..................... SHIPPED  (accepted 2026-08-31, live)
step 3  accounts, metering, hosted MCP, governance .. IN PROGRESS  ◀── you are here
          tasks 1-11  building now (workflow wf_857c706b-a7e)
          task 12     provisioning: prerequisites done, rest blocked on tasks 1-11
          task 13     acceptance: not started
step 4  metered jobs: optimize, notes→llms, indexes .. NOT STARTED
step 5  concept-axis jobs: abstraction, family, deepen NOT STARTED
step 6  contribute flow, owner claims, CLI GA ........ NOT STARTED
```

**Immediately next, in order**

1. Land workflow `wf_857c706b-a7e` (step-3 tasks 1–11 + adversarial review), fix
   what the review confirms, commit.
2. Step 3 Task 12 — provisioning. Prerequisites are already done on the M5:
   Postgres 16 running with `explorer_dev` and `explorer_test`, `cloudflared
   2026.8.2` and the Stripe CLI installed. What remains needs the owner's
   sign-ins (see the split below).
3. Step 3 Task 13 — acceptance against §10 row 3, stamp the row, commit.
4. Then step 4.

**Who does what in provisioning.** I can create the Neon project, create Stripe
products and prices, register the OAuth apps, create and route the tunnel, write
the launchd units and run the smoke tests. The owner does: signing in to Neon and
Stripe (and any card entry), `stripe login`'s pairing confirmation, and the final
switch from Stripe test keys to live keys. Secrets land in the environment on the
M5, never in the repo.

---

## Constraints that hold for every remaining step

These are settled; a task that appears to need one changed should stop and say so
rather than change it.

- **The hub is the runtime and the single writer.** `~/.global-ai-hub` owns the
  public stores; the site and API read them. Per-user stores live at
  `stores/<user_id>/docsets.db` on the M5, outside `.chroma-docsets/`, excluded
  from `replicate_docsets.py`'s push. Requests touching them pin to the M5.
- **The hub MCP server never faces the tunnel.** It binds 127.0.0.1; only the
  gateway calls it.
- **Decisions D1–D9** in `00-platform-design.md` §12 are not re-litigated. D5 fixes
  the hosted tool set, D6 the plan caps, D7 the free embedding/storage allowances,
  D8 that third-party full text is never served publicly, D9 that step-2 payloads
  are build-time JSON.
- **Money is `Decimal`/`numeric(12,6)`, the ledger is append-only**, and a
  correction is a new row.
- **Every artifact published anywhere passes the lint gate at 0 High.**
- **Generated, not hand-edited**: artifacts come from a generator; hand inputs go
  into `manifest.overrides` or `llms.overrides.json`.
- **Tests for anything touching keys, money or another user's data are written
  from the attacker's side**, and they are the acceptance bar.
- Python is `hub/.venv/bin/python`; lint is `ruff check api site/tools site/tests llmsx`.
- No agent commits during a workflow; the orchestrator commits at phase
  boundaries. Hub commits go through a detached worktree on `origin/main`, and the
  suite runs *in the worktree* before pushing.

---

## Step 3 — accounts, metering, hosted MCP, governance (IN PROGRESS)

Full detail: `2026-08-31-site-step3-accounts-mcp-governance.md`. Summary and state:

| Task | What | State |
|---|---|---|
| 1 | `api/` skeleton, fail-fast settings | building |
| 2 | Schema + Alembic (users … stripe_events) | building |
| 3 | Passkey + OAuth sign-in, session cookies | building |
| 4 | Scoped API keys, Argon2id, shown once | building |
| 5 | `PLANS` from 15 §5, quota checks, append-only ledger | building |
| 6 | Stripe checkout, portal, idempotent webhooks | building |
| 7 | MCP gateway: key → user → scope → tool policy → meter | building |
| 8 | `/u/<user>/<slug>.llms/…`, private, never edge-cached | building |
| 9 | Private tree forks with per-plan quota | building |
| 10 | Proposals through the lint gate + moderation queue | building |
| 11 | Site account/keys/usage pages | building |
| 12 | Provisioning (Neon, Stripe, OAuth, tunnel, launchd) | prerequisites done; rest blocked on 1–11 |
| 13 | Acceptance: a paid key calls every hosted read tool; a proposal round-trips | not started |

**Acceptance (§10 row 3):** a paid key can call every hosted read tool within tier
limits, and a proposal round-trips through moderation.

---

## Step 4 — metered jobs (NOT STARTED)

**Components:** 01 optimize, 02 notes→llms, 17 hosted indexes; plus 03's keyword
search over the reference and 14's playground.
**Deliverable:** the first jobs that spend model tokens, end to end, with real
metering.
**Acceptance (§10 row 4):** estimate → actual within ±20 % on a pilot set, and the
refund rule verified on a forced gate failure.

### What it builds

1. **The job runner.** The `Job`/`JobEvent` tables exist from step 3; step 4 adds
   the worker: lease + heartbeat + reaper (`attempts` ≤ 3), SSE at
   `/api/jobs/<id>/events` with a keepalive every ≤ 20 s and `Last-Event-ID`
   resume, `GET /api/jobs/<id>` as the authoritative state. Enqueues through the
   hub's `BoxPool` with a `site` priority class; an admission controller over the
   Ollama pool reserves a floor for site jobs and for the hub's own pipeline.
2. **Cost estimates before spending.** Every job kind gets an estimator (input
   size × stage plan). The estimate is shown, the quota hold is taken against it,
   and the ±20 % acceptance is measured on a pilot set of ~20 real runs.
3. **`/ldo` optimize as a job** (01): the deterministic passes already run in
   milliseconds; this adds the model passes (P4 navigation, P8 facts truth, P12
   agent usability) through the Claude Agent SDK with the SKILL.md as the run
   spec and read-only hub MCP tools. Findings stream as `JobEvent`s; the report is
   the artifact.
4. **Notes → llms as a job** (02): upload (private, virus-scanned, size-capped) →
   ingest-time P9 scan for steering and secrets **before** any agent stage → the
   `docset_refine` chain with `clean.FIRST_PARTY` → export → lint gate → artifact
   at `/u/<user>/<slug>.llms/`.
5. **Hosted indexes** (17): `POST /api/index` creating a per-user docset in
   `stores/<user_id>/`, vector + FTS5, with the model allowlist and cross-model
   refusal; the downloadable single-SQLite bundle.
6. **Refunds.** A stage that fails a verify gate writes its polish/judgment tokens
   `billable=false` with a reason. Forced-failure test is the acceptance.

### Risks to design against

- A job that dies mid-stage must release its quota hold — the reaper's job.
- Ollama contention with the hub's own timers; quiet hours remove the M3 on
  weekdays 09:00–17:00 (pool weight 8 → 5).
- The Claude circuit breaker: when open, jobs needing a judgment pass are **held**
  with a `waiting-for-claude` event for at most 24 h, then cancelled with the hold
  released — never silently skipped.

---

## Step 5 — concept-axis jobs (NOT STARTED)

**Components:** 06 abstraction (`/lca`), 08 family map, 07 deepen (`/dr`).
**Deliverable:** a concept pack that passes the lint gate and lands on its tree node.
**Acceptance (§10 row 5):** exactly that.

### What it builds

1. **Abstraction** (06): concept + scope → the `/lca` pipeline (lexicon expansion,
   keyword harvest, semantic pass with cached embeddings, model classification of
   borderline units, verification) → a concept pack directory. UI: scope picker,
   the lexicon proposal to edit and approve, the harvest report, then the pack with
   facet tabs, disagreements, and the concept graph in the 3D renderer.
2. **Family map** (08): a concept → proposed neighbours with relation, novelty and
   evidence; shown as dashed nodes in the 3D view; the user picks which gaps to
   research, which hands to 07.
3. **Deepen** (07): `/dr` as a job from a node or a pack. Free tier gets the
   plan-only preview; a run fans out ≤ 4 research agents per batch with bounded
   briefs, lands as an updated spoke or a new skill under the user's namespace,
   regenerates the topical llms and refreshes the vocabulary, and shows a diff
   (new facts, re-verified stamps, new frontier nodes) the user accepts or reverts.

### Notes carried forward from the hub work

- `docset_refine topical` and `vocabulary` already exist and are the generators;
  step 5 is the service around them, not a reimplementation.
- The abstractor's output contract (`~/.claude/skills/llms-concept-abstractor/references/output-contract.md`)
  is the pack shape — do not invent a second one.
- Two hub bugs found during step 2 are fixed (`vocabulary.render()` sourcing,
  `clean.classify` policy); the site's `_classify_twin` monkeypatch **stays** until
  the hub grows a route-based classifier hook, because a threshold policy cannot
  express a rule keyed on the first path segment.

---

## Step 6 — contribute, claims, CLI GA (NOT STARTED)

**Components:** 13 contribute flow (§2 M4), 10 owner claims + rescoring, `llmsx` GA.
**Deliverable:** community publishing.
**Acceptance (§10 row 6):** a first external contribution merged through the ladder.

### What it builds

1. **Publish to the shared catalogue**: a user's export, topical file, concept pack
   or vocabulary passes the lint gate at 0 High, carries a provenance banner, and
   enters the moderation queue. Rights: index + facts + the contributor's own words
   are publishable; third-party full text is not (D8).
2. **Claimed-site owners** (10): verify a site with a claim token (an `llms.txt`
   comment, a `Link` header, or a DNS TXT record) → lint-on-push, rescoring, a
   badge, and hosted access to that site's own full text.
3. **`llmsx` GA**: the CLI gains the metered verbs behind a key (`lint`, `optimize`,
   `notes`, `abstract`, `deepen`, `index`, `publish`), keeps `--local` for the
   deterministic paths, and ships to PyPI with the version pinned in the docs.
4. **The directory becomes self-maintaining**: the weekly refresh rescoring claimed
   sites, retiring dead ones, and recording score history.

---

## Cross-cutting work that has no step of its own

Do these when the step they block arrives, not before:

- **`/u/` route in `llms_serve.py` vs explorer-api** — master §3a assigns it to
  explorer-api; component 13 §7 still says `llms_serve.py`. The master wins; 13 was
  edited. No code change outstanding.
- **`hub_ask` hosted** — absent in v1 per D5. Revisit only when metering is proven.
- **The site's `_classify_twin` monkeypatch** — removable once the hub grows a
  pluggable classifier hook or a `route_sections` field. Logged, not scheduled.
- **Stale generated vocabularies in the estate** — files written before the
  `vocabulary.render()` fix still carry unsourced term lines and will not lint clean
  until regenerated. Regenerate with the next estate refresh.
- **`llms-concepts/*.llms/llms-vocabulary.txt`** — written by the concept
  abstractor (a separate skill, nested repo), still violating the same contract the
  hub generator now honours. Upstream fix belongs to that skill.

---

## Provisioning runbook (step 3 Task 12) — the detail, so it is not lost

Prerequisites already done on the M5: PostgreSQL 16 running (`explorer_dev`,
`explorer_test`), `cloudflared 2026.8.2`, Stripe CLI.

1. **Neon** — owner signs in; create the project; copy the **pooled** connection
   string into `DATABASE_URL` on the M5; `alembic upgrade head`. Pool limits:
   ≤ 5 connections per worker, ≤ 20 per API process, 5 s statement timeout on
   job-status writes.
2. **Stripe** — owner signs in and confirms `stripe login` pairing. Create the
   Starter ($9/mo) and Pro ($39/mo) products and prices per 15 §5. Copy
   `STRIPE_SECRET_KEY` (test) and the webhook signing secret; point the webhook at
   `https://api.llms-explorer.com/api/billing/webhook`. **The live-key switch is
   the owner's, separately.**
3. **OAuth apps** — GitHub and Google; callback
   `https://api.llms-explorer.com/api/auth/oauth/<provider>/callback`.
4. **Tunnel** — `cloudflared tunnel create explorer-api`; route
   `api.llms-explorer.com` → `http://127.0.0.1:8790`; run two replicas.
5. **launchd** — units for uvicorn and the tunnel. Any unit that touches LAN Ollama
   must run under a binary approved for macOS Local Network privacy (granted per
   binary — the reason `replicate_docsets.py` runs on `/usr/bin/python3`).
6. **Smoke** — `curl https://api.llms-explorer.com/health`; sign in; create a key;
   call a public MCP tool; check `/api/usage`.

---

## Hard-won facts a fresh session would otherwise relearn

- **Cloudflare Pages merges matching `_headers` rules** and concatenates repeated
  header names — it does not override. A committed `site/public/_headers` is copied
  into `dist/` during `astro build`, which runs *before* `postbuild`, so locally the
  generated file wins and the stale one looks inert while shipping in production.
  The file must not exist; a test enforces that.
- **Cloudflare shallow-clones**, so the repo's 846 MB `outputs/` costs ~14 s in a
  Pages build, not a timeout.
- **`SITE_URL` is load-bearing**: it is baked into twin banners, the mirror's `URL:`
  lines and every absolute link in `llms.txt`. Changing the domain requires a rebuild.
- **`*.pages.dev` is not a choice** — every Pages project gets one; a custom domain
  is attached afterwards, and attaching `www` alone *serves* both hosts, so a
  redirect rule is what makes the apex canonical.
- **The snapshot timer's `git add -A`** sweeps up any uncommitted work in the
  explorer repo at 04:30 and commits it under a "snapshot" message. Land work before
  then or expect to re-label the commit.
- **Astro 5, not 7**: `npm create astro@latest` installs 7, whose collections API
  differs from what this site uses. Pin `astro ^5`.
- **The shared checkout hazard**: copying a whole file from `~/.global-ai-hub` into a
  worktree can carry another session's half-finished work onto main. Run the suite
  *in the worktree* before pushing — a green shared checkout only proves the two
  sessions' changes work together.
- **`llms_lint` attributes that judge a file's neighbourhood** (`S2` wants an
  `llms-small` sibling, `H8` a manifest) are unanswerable for a flat mirror and are
  excluded from directory scoring; a High still caps the grade at D.
