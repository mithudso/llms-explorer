# LLMS-Explorer site — Step 3 (accounts, metering, hosted MCP, governance) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build-order step 3 of `docs/site/00-platform-design.md` §10: `explorer-api` — the FastAPI service with accounts, API keys, a token ledger, the hosted MCP gateway over the hub's read tools, per-user artifacts at `/u/<user>/<slug>.llms/`, private tree forks, and the moderation queue for merge-back proposals.

**Architecture:** One FastAPI app under `api/`, run on the M5 behind a Cloudflare Tunnel. Postgres (Neon) holds accounts, keys, ledger, jobs and governance; the hub's SQLite/Chroma stores stay where they are and stay single-writer. The MCP gateway terminates the hosted session, authenticates the key, applies tier policy, and forwards to `hub_mcp_server.py` on 127.0.0.1 — the hub server itself never faces the tunnel. Everything is built and tested against a local Postgres and a Stripe *test* key; provisioning the real Neon/Stripe/tunnel is a separate, owner-run task (Task 12) because it needs credentials only the owner has.

**Tech Stack:** FastAPI + uvicorn, SQLAlchemy 2 + Alembic, `asyncpg`, `argon2-cffi` (key hashing), `webauthn` (passkeys), `authlib` (OAuth), `stripe`, `pytest` + `httpx` + `testcontainers`-style local Postgres (or `pytest-postgresql`), all on `hub/.venv`.

## Global Constraints

- Design authority: `docs/site/00-platform-design.md` §§3–9 and D1–D9, plus components `13`, `15`, `05`, `09`. **Decisions D1–D9 are settled; do not re-decide them in code or comments.**
- **The hub is not modified by this step.** `explorer-api` imports `~/.global-ai-hub/scripts` read-only on the box and the vendored `hub/` in CI. Any hub change needed is a BLOCKED row in the task's report, not an edit.
- **One writer per store** (master principle 5): per-user docsets live at `stores/<user_id>/docsets.db` on the M5, outside `.chroma-docsets/`, excluded from `replicate_docsets.py`'s push. Requests touching them pin to the M5 (master §5 Box routing).
- **The hub MCP server never faces the tunnel.** It binds 127.0.0.1; only the gateway may call it (`hub/docs/MCP.md`: "do not expose off-box without adding auth").
- Secrets come from the environment, never from a file in the repo: `DATABASE_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `OAUTH_GITHUB_*`, `OAUTH_GOOGLE_*`, `SESSION_SECRET`. A missing one fails fast at startup with the variable named. `.env.example` lists them with placeholder values; `.env` is gitignored.
- **API keys are stored as Argon2id hashes with a separate lookup prefix.** The plaintext key is shown once, at creation, and never again — not in a log, an error, or a job record.
- Money is `numeric(12,6)` in Postgres and `Decimal` in Python. Never float. The ledger is append-only: a correction is a new row, never an update.
- Tier numbers live in component 15 §5 and are loaded from `api/plans.py` as data — no tier threshold is written inline in a route.
- Tests never reach the network: Stripe is the `stripe-mock` container or a recorded fixture, OAuth providers are stubbed, and the hub MCP is a fake unless a test is explicitly marked `@pytest.mark.hub`.
- Python: `hub/.venv/bin/python`. Lint: `hub/.venv/bin/python -m ruff check api site/tools site/tests llmsx` (extend `site/ruff.toml`'s sibling `api/ruff.toml` with the same rule set).
- Commits: one per task, conventional prefix. Never commit `.env`, a Stripe key, or a database dump.

---

## File structure

```
api/
  pyproject.toml, ruff.toml, .env.example
  explorer_api/
    __init__.py, main.py            app factory, startup env check, health
    settings.py                     env → typed settings, fail-fast
    db.py                           engine, session dependency
    models.py                       SQLAlchemy: users, api_keys, plans, subscriptions,
                                    credits, ledger, jobs, job_events, artifacts,
                                    trees, proposals, moderation, stripe_events
    auth.py                         passkey + OAuth, session cookies
    keys.py                         create/list/revoke, Argon2 hash + prefix lookup
    plans.py                        the 15 §5 table as data; quota lookups
    ledger.py                       append-only rows, credit balance, quota checks
    billing.py                      Stripe checkout, portal, webhook (idempotent)
    gateway.py                      MCP gateway: key → user → scopes → tool policy → meter
    artifacts.py                    /u/<user>/<slug>.llms/… with llms_serve's headers
    trees.py                        fork, validate, propose
    moderation.py                   queue, decide, merge
    routes/                         one module per surface, thin
  alembic/                          migrations
  tests/                            one file per module, plus test_tier_policy.py
```

---

### Task 1: The app skeleton that fails fast

**Files:** Create `api/pyproject.toml`, `api/ruff.toml`, `api/.env.example`, `api/explorer_api/{__init__,settings,main}.py`, `api/tests/test_settings.py`

**Interfaces:**
- Produces `Settings` (pydantic-settings) with `database_url`, `session_secret`, `stripe_secret_key`, `stripe_webhook_secret`, `oauth_github_id/secret`, `oauth_google_id/secret`, `hub_mcp_url` (default `http://127.0.0.1:8787`), `stores_root`, `environment`.
- `create_app() -> FastAPI` with `GET /health` → `{"status":"ok","environment":…}` and a startup hook that raises on any missing required setting, naming every one.

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_settings.py
import pytest
from explorer_api.settings import Settings, MissingSettings


def test_missing_settings_are_named_all_at_once(monkeypatch):
    for var in ("DATABASE_URL", "SESSION_SECRET", "STRIPE_SECRET_KEY"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(MissingSettings) as e:
        Settings.load()
    msg = str(e.value)
    assert "DATABASE_URL" in msg and "SESSION_SECRET" in msg and "STRIPE_SECRET_KEY" in msg


def test_loads_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/x")
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    s = Settings.load()
    assert s.hub_mcp_url == "http://127.0.0.1:8787"     # localhost by default, never public
    assert s.environment in ("dev", "prod")


def test_no_secret_is_ever_repr_ed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:hunter2@localhost/x")
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_supersecret")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    s = Settings.load()
    assert "hunter2" not in repr(s) and "supersecret" not in repr(s)
```

- [ ] **Step 2: Run it** — `cd api && ../hub/.venv/bin/python -m pytest tests/test_settings.py -q` → FAIL (no module).
- [ ] **Step 3: Implement** the package, `Settings.load()` collecting *every* missing variable before raising, `SecretStr` for anything sensitive, and `create_app()`.
- [ ] **Step 4: Run** the tests and `uvicorn explorer_api.main:app --port 8790` with a dummy env; `curl localhost:8790/health` → 200.
- [ ] **Step 5: Commit** — `feat(api): FastAPI skeleton with fail-fast settings`.

---

### Task 2: Schema and migrations

**Files:** Create `api/explorer_api/{db,models}.py`, `api/alembic/…`, `api/tests/conftest.py`, `api/tests/test_models.py`

**Interfaces:**
- The tables named in 15 §7 and master §4, with money as `numeric(12,6)`, `ledger` append-only (no `updated_at`), `jobs` carrying `worker/lease_expires/attempts/last_heartbeat` (master §4), and `job_events(job_id, seq, ts, kind, payload)` with `unique(job_id, seq)` for `Last-Event-ID` resume.
- `conftest.py` gives every test a clean database (a template database created once per session, copied per test) so tests are order-independent.

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_models.py
from decimal import Decimal
import pytest
from sqlalchemy import select
from explorer_api import models as m


async def test_ledger_is_append_only(session):
    u = await _user(session)
    row = m.LedgerEntry(user_id=u.id, component="01", kind="input", model="claude-opus-4-8",
                        units=1000, unit_cost_usd=Decimal("0.000015"),
                        price_usd=Decimal("0.000045"), billable=True)
    session.add(row); await session.commit()
    with pytest.raises(Exception):                 # the trigger/constraint refuses it
        row.price_usd = Decimal("0")
        await session.commit()


async def test_money_keeps_six_decimals(session):
    u = await _user(session)
    session.add(m.LedgerEntry(user_id=u.id, component="17", kind="embedding", model="mxbai-embed-large",
                              units=1, unit_cost_usd=Decimal("0.000001"),
                              price_usd=Decimal("0.000003"), billable=True))
    await session.commit()
    got = (await session.execute(select(m.LedgerEntry))).scalar_one()
    assert got.price_usd == Decimal("0.000003")     # not 3e-06 float noise


async def test_job_events_are_ordered_and_unique(session):
    j = await _job(session)
    session.add_all([m.JobEvent(job_id=j.id, seq=1, kind="stage", payload={"s": "clean"}),
                     m.JobEvent(job_id=j.id, seq=2, kind="tokens", payload={"n": 10})])
    await session.commit()
    with pytest.raises(Exception):
        session.add(m.JobEvent(job_id=j.id, seq=2, kind="stage", payload={}))
        await session.commit()
```

- [ ] **Step 2: Run it** → FAIL. — [ ] **Step 3: Implement** models + the initial Alembic revision; enforce append-only with a `BEFORE UPDATE` trigger on `ledger` that raises. — [ ] **Step 4:** `alembic upgrade head` on a scratch database, then the tests. — [ ] **Step 5: Commit** — `feat(api): schema for accounts, ledger, jobs and governance`.

---

### Task 3: Accounts and sessions

**Files:** `api/explorer_api/auth.py`, `api/explorer_api/routes/auth.py`, `api/tests/test_auth.py`

**Interfaces:** `POST /api/auth/passkey/register|authenticate` (WebAuthn ceremonies), `GET /api/auth/oauth/{github,google}` + `/callback`, `POST /api/auth/logout`, `GET /api/me`. Session = signed, `HttpOnly`, `Secure`, `SameSite=Lax` cookie; 30-day rolling expiry.

- [ ] **Step 1: Write the failing test** — a stubbed OAuth provider returns a fixed profile; assert a user row is created on first sign-in and reused on the second (matched on verified email), that the cookie is `HttpOnly`+`Secure`, that `/api/me` is 401 without it, and that two providers with the same verified email land on **one** user.
- [ ] **Step 2: Run it** → FAIL. — [ ] **Step 3: Implement.** — [ ] **Step 4: Run.** — [ ] **Step 5: Commit** — `feat(api): passkey and OAuth sign-in with session cookies`.

---

### Task 4: API keys

**Files:** `api/explorer_api/keys.py`, `api/explorer_api/routes/keys.py`, `api/tests/test_keys.py`

**Interfaces:** `create(user, scopes) -> (plaintext, ApiKey)` where plaintext is `llmsx_<prefix>_<secret>`; storage is `prefix` (indexed, non-secret) + Argon2id hash of the secret. `authenticate(raw) -> ApiKey | None`. `GET/POST/DELETE /api/keys`. Scopes: `read`, `run`, `publish`.

- [ ] **Step 1: Write the failing test**

```python
async def test_the_plaintext_key_is_shown_once_and_never_stored(session, client):
    r = await client.post("/api/keys", json={"scopes": ["read"]})
    raw = r.json()["key"]
    assert raw.startswith("llmsx_")
    row = (await session.execute(select(m.ApiKey))).scalar_one()
    assert raw not in (row.hash + row.prefix)          # the secret half is not recoverable
    assert (await client.get("/api/keys")).json()[0].get("key") is None
    assert await keys.authenticate(session, raw) is not None
    assert await keys.authenticate(session, raw[:-1] + "x") is None


async def test_a_revoked_key_stops_working_immediately(session, client):
    raw = (await client.post("/api/keys", json={"scopes": ["read"]})).json()["key"]
    kid = (await client.get("/api/keys")).json()[0]["id"]
    await client.delete(f"/api/keys/{kid}")
    assert await keys.authenticate(session, raw) is None
```

- [ ] **Step 2–5** as above. Commit — `feat(api): scoped API keys, Argon2-hashed, shown once`.

---

### Task 5: Plans, quotas and the ledger

**Files:** `api/explorer_api/{plans,ledger}.py`, `api/explorer_api/routes/usage.py`, `api/tests/{test_plans,test_ledger}.py`

**Interfaces:**
- `plans.PLANS` mirrors 15 §5 exactly (free/starter/pro: price, included credit, and the quota dict — lint size and daily count, keyword/day, indexes, storage GB, private trees, publish).
- `ledger.record(session, user, component, kind, model, units, *, job=None, billable=True, reason=None) -> LedgerEntry` computing `unit_cost_usd` from `prices` and `price_usd` at the plan's margin.
- `ledger.check_quota(session, user, feature, amount=1) -> QuotaVerdict{allowed, remaining, tier, upgrade_url}` — **the single place** a limit is enforced.
- `GET /api/usage?from&to` aggregates by component/model/day.

- [ ] **Step 1: Write the failing test** — assert the free tier's numbers come from `PLANS` and match 15 §5 (parse the spoke's table in the test, so drift between doc and code fails CI); a metered call at quota returns `allowed=False` with `upgrade_url`; `record()` never writes a float; billing a failed verify-gate stage writes `billable=False` with a reason (master §5).
- [ ] **Step 2–5.** Commit — `feat(api): plans, quota checks and the append-only ledger`.

---

### Task 6: Stripe

**Files:** `api/explorer_api/billing.py`, `api/explorer_api/routes/billing.py`, `api/tests/test_billing.py`

**Interfaces:** `POST /api/billing/checkout {plan}` → session URL; `GET /api/billing/portal`; `POST /api/billing/webhook` verifying the signature, recording `stripe_events.id` **before** acting (idempotency), and applying `checkout.session.completed`, `customer.subscription.{created,updated,deleted}`, `invoice.paid` → credits.

- [ ] **Step 1: Write the failing test** — a replayed webhook with the same event id changes nothing the second time; an invalid signature is 400 and writes nothing; a `subscription.deleted` downgrades the plan at period end, not immediately.
- [ ] **Step 2–5.** Commit — `feat(api): Stripe checkout, portal and idempotent webhooks`.

---

### Task 7: The MCP gateway

**Files:** `api/explorer_api/gateway.py`, `api/explorer_api/routes/mcp.py`, `api/tests/test_gateway.py`

**Interfaces:**
- `POST /mcp` (Streamable HTTP) — authenticate the key, resolve the user, apply `TOOL_POLICY`, forward to `settings.hub_mcp_url`, record a ledger row for metered tools.
- `TOOL_POLICY` names every tool with its tier and scope, from 13 §5: public read tools (`hub_list_docsets`, `hub_query_docset`, `hub_docset_index`, `hub_llms_full_list`, the four `hub_concept_*`, `hub_directory_score`), `run`-scoped (`hub_index_docset`, `hub_delete_docset` — both scoped to the caller's own `u_<user>__*` keys, D5), and **absent hosted**: `hub_ask`, `hub_distill_run`, `hub_memory_*` (D5).
- Namespacing: a docset argument not prefixed `u_<user>__` and not in the public catalogue is rejected before the call reaches the hub.

- [ ] **Step 1: Write the failing test**

```python
async def test_absent_tools_are_not_reachable_however_the_key_is_scoped(gateway, key_all_scopes):
    for tool in ("hub_ask", "hub_distill_run", "hub_memory_search"):
        r = await gateway.call(tool, {}, key=key_all_scopes)
        assert r.status_code == 404 and "not hosted" in r.text          # D5

async def test_a_user_cannot_touch_another_users_docset(gateway, key_a):
    r = await gateway.call("hub_query_docset", {"docset": "u_bob__notes", "question": "x"}, key=key_a)
    assert r.status_code == 403
    assert (await gateway.call("hub_query_docset",
                               {"docset": "codeclaudecom__codeclaudecom", "question": "x"},
                               key=key_a)).status_code == 200           # public is fine

async def test_a_metered_tool_writes_exactly_one_ledger_row(gateway, key_run, session):
    await gateway.call("hub_index_docset", {"mirror": "…", "name": "u_a__x"}, key=key_run)
    rows = (await session.execute(select(m.LedgerEntry))).scalars().all()
    assert len(rows) == 1 and rows[0].component == "13"

async def test_read_scope_cannot_run(gateway, key_read):
    assert (await gateway.call("hub_index_docset", {}, key=key_read)).status_code == 403
```

- [ ] **Step 2–5.** Commit — `feat(api): hosted MCP gateway with per-tool tier policy and namespacing`.

---

### Task 8: Per-user artifacts

**Files:** `api/explorer_api/artifacts.py`, `api/explorer_api/routes/artifacts.py`, `api/tests/test_artifacts.py`

**Interfaces:** `GET /u/<user>/<slug>.llms/<file>` serving the same headers as `llms_serve.py` (`text/markdown; charset=utf-8`, `X-Markdown-Tokens`, `Link rel=describedby`) **plus** `Cache-Control: private, no-store` and a cache key including the session/key (master §6). 404 (not 403) for another user's artifact, so the path does not leak existence.

- [ ] **Step 1: Write the failing test** — owner gets 200 with the headers; a signed-in stranger gets 404; anonymous gets 401; the response is never edge-cacheable (`private, no-store` present, no `public`).
- [ ] **Step 2–5.** Commit — `feat(api): per-user artifact route, private and never edge-cached`.

---

### Task 9: Private trees and forks

**Files:** `api/explorer_api/trees.py`, `api/explorer_api/routes/trees.py`, `api/tests/test_trees.py`

**Interfaces:** `POST /api/trees/fork` copies the public `tree.json` to `trees/<user_id>/tree.json` and records `trees(user_id, forked_from_sha, updated_at)` (master §4 — a file copy, not a patch model); `GET /api/tree?tree=public|me`; `POST /api/trees/me/validate` running `concept_tree.py validate`; quota from `PLANS` (free 1, starter 3, pro 20).

- [ ] **Step 1: Write the failing test** — fork records the source sha; a second fork past quota is 402 with `upgrade_url`; `?tree=me` differs from `?tree=public` after an edit; validate reports dangling parents.
- [ ] **Step 2–5.** Commit — `feat(api): private tree forks with per-plan quota`.

---

### Task 10: Proposals and moderation (05)

**Files:** `api/explorer_api/{moderation}.py`, `api/explorer_api/routes/proposals.py`, `api/tests/test_moderation.py`

**Interfaces:** `POST /api/proposals` (a diff from a private tree against the public sha) → runs the **lint gate** and the 05 §4 precedence ladder, then queues; `GET /api/proposals` (moderator); `POST /api/proposals/<id>/{accept,reject}`; accept merges into the public tree and records who decided. A proposal whose artifacts fail the lint gate is rejected automatically with the findings attached (master §9).

- [ ] **Step 1: Write the failing test** — a proposal from a stale sha is 409; one with a High lint finding is auto-rejected with the finding text; accept updates the public tree and writes the moderator and timestamp; a non-moderator cannot accept.
- [ ] **Step 2–5.** Commit — `feat(api): merge-back proposals through the lint gate and moderation queue`.

---

### Task 11: Wire the site to the API

**Files:** `site/src/pages/{login,account,keys,usage}.astro`, `site/src/components/AccountNav.astro`, `site/tests/test_account_pages.py`, `site/README.md`

**Interfaces:** The account pages are islands calling the API with the session cookie; the site stays static, so a signed-out visitor sees exactly what step 2 shipped. `PUBLIC_API_URL` env (default `https://api.llms-explorer.com`).

- [ ] **Step 1: Write the failing test** — the pages build; signed-out markup contains no user data; every account route is behind an island, not server-rendered; the pages have `.md` twins like every other page and the family still lints 0 High.
- [ ] **Step 2–5.** Commit — `feat(site): account, keys and usage pages`.

---

### Task 12: Provisioning (OWNER-RUN — not for an agent)

This task needs credentials no agent should hold. It is written as a runbook for the owner.

- [ ] Create the Neon project; copy the pooled connection string to `DATABASE_URL` on the M5. Run `alembic upgrade head`.
- [ ] Create the Stripe products/prices for Starter and Pro (15 §5), copy `STRIPE_SECRET_KEY` and the webhook signing secret; point the webhook at `https://api.llms-explorer.com/api/billing/webhook`.
- [ ] Register the GitHub and Google OAuth apps; callback `https://api.llms-explorer.com/api/auth/oauth/<provider>/callback`.
- [ ] `cloudflared tunnel create explorer-api`; route `api.llms-explorer.com` → `http://127.0.0.1:8790`; run two replicas (master §8).
- [ ] launchd units for uvicorn and the tunnel; both must run under a binary approved for macOS Local Network privacy if they touch LAN Ollama (master §8).
- [ ] Smoke: `curl https://api.llms-explorer.com/health`, sign in, create a key, call a public MCP tool, check `/api/usage`.

---

### Task 13: Step-3 acceptance

- [ ] `cd api && ../hub/.venv/bin/python -m pytest tests -q` and the site + llmsx suites → all green; `ruff check api site/tools site/tests llmsx` clean.
- [ ] The §10 row-3 bar, proven: **a paid key calls every hosted read tool within tier limits** (a script that walks `TOOL_POLICY` and asserts each public tool answers and each absent tool 404s), and **a proposal round-trips through moderation** (create → lint gate → queue → accept → public tree updated).
- [ ] Record the acceptance in `00-platform-design.md` §10 row 3 with the date and the evidence, as rows 1 and 2 carry.
- [ ] Commit.

---

## Self-review

- **Spec coverage.** §10 row 3 names 15 (Tasks 1–6, 11), 13 (Task 7) and 05 (Tasks 9–10); the deliverables — sign-in, keys, ledger, hosted MCP reads, private trees, `/u/…` — map to Tasks 3, 4, 5, 7, 9, 8. D5's tool list is Task 7's policy table; D7's allowances are Task 5's `PLANS`; master §4's job/ledger shapes are Task 2.
- **Placeholders.** None. The one genuinely unknowable part — real credentials — is isolated in Task 12 and marked owner-run rather than faked.
- **Type consistency.** `Settings.load()`, `keys.create/authenticate`, `ledger.record/check_quota`, `plans.PLANS`, `gateway.TOOL_POLICY` are used with the same names and signatures across Tasks 1–11; money is `Decimal` everywhere it appears.
- **Risk the plan accepts:** this is the first step where a bug costs money or leaks data. Every task that touches keys, money or another user's data has a test written from the attacker's side (revoked key still works? another user's docset reachable? webhook replayed? artifact enumerable?), and those tests are the acceptance bar, not an afterthought.
