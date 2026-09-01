# api/tests/test_skills.py
"""The showcase skills surface: the only place this service spends model credit.

Every test here is written from the money's side rather than the feature's:

* an unauthenticated caller must not be able to spend a cent — there is no
  public tier on this surface, unlike the MCP gateway's read tools,
* a `read` key must not be able to spend either; `run` is the scope that costs,
* the demo's input ceiling must hold, because an unbounded paste is a cost
  incident and not a use case,
* a run with **no price in force for the model** must be refused *before* the
  provider is called, never after — `ledger.DEFAULT_PRICES` omits the Claude
  rows on purpose, so this is the default state of a fresh deployment,
* a successful run writes exactly two ledger rows (input and output) and no
  more, and a failed one writes none while still leaving the attempt on record.

The provider is faked. A test that called the real API would bill the owner to
assert a string, which is the exact failure mode this surface exists to bound.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from explorer_api import gateway as gw
from explorer_api import keys, models as m
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.skills import (
    MAX_INPUT_CHARS,
    MODEL,
    Completion,
    get_llm_client,
)
from explorer_api.settings import Settings

NOTES = "Met with Acme Tue. They want SSO by Q3. TODO: send pricing. Bob is out."


@dataclass(frozen=True)
class Caller:
    raw: str
    user: m.User


class FakeLlm:
    """Stands in for Anthropic. Records what it was asked, never calls out."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.raise_on_call: Exception | None = None
        self.reply = "# llms.txt\n\n- [Acme](#acme): SSO by Q3\n"

    async def complete(self, *, system: str, prompt: str,
                       max_tokens: int) -> Completion:
        self.calls.append({"system": system, "prompt": prompt,
                           "max_tokens": max_tokens})
        if self.raise_on_call is not None:
            raise self.raise_on_call
        return Completion(text=self.reply, input_tokens=120, output_tokens=340)


@pytest_asyncio.fixture
async def llm() -> FakeLlm:
    return FakeLlm()


@pytest_asyncio.fixture
async def priced(session) -> None:
    """A price in force for the model, which a fresh deployment does not have.

    Most tests want to exercise the surface rather than the refusal, so they
    depend on this; :func:`test_a_model_with_no_price_is_refused_before_spending`
    deliberately does not.
    """
    for kind in ("input", "output"):
        session.add(m.Price(model=MODEL, kind=kind,
                            unit_cost_usd=Decimal("3.00"),
                            price_usd=Decimal("9.00"),
                            note="test fixture"))
    await session.flush()


@pytest_asyncio.fixture
async def client(session, llm, database_url: str, tmp_path) -> AsyncIterator[AsyncClient]:
    settings = Settings.load({
        "DATABASE_URL": database_url,
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
        "STORES_ROOT": str(tmp_path / "stores"),
    })
    app = create_app(settings)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_llm_client] = lambda: llm

    gw.reset_rate_limits()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def _caller(session, scopes: list[str], plan_id: str = "pro") -> Caller:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test", plan_id=plan_id)
    session.add(user)
    await session.flush()
    raw, _row = await keys.create(session, user, scopes)
    await session.flush()
    return Caller(raw=raw, user=user)


@pytest_asyncio.fixture
async def key_run(session) -> Caller:
    return await _caller(session, ["read", "run"])


@pytest_asyncio.fixture
async def key_read(session) -> Caller:
    return await _caller(session, ["read"])


def _auth(caller: Caller | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {caller.raw}"} if caller else {}


async def _run(client, skill: str, caller: Caller | None = None, **body):
    return await client.post(f"/api/skills/{skill}/run",
                             json={"input": NOTES, **body},
                             headers=_auth(caller))


# --- nobody spends without a key --------------------------------------------


async def test_an_anonymous_caller_cannot_spend(client, llm):
    """No public tier here: every call costs money the owner pays for."""
    r = await _run(client, "notes-to-llms")
    assert r.status_code == 401
    assert llm.calls == []          # the provider was never reached


async def test_a_read_key_cannot_spend(client, llm, key_read):
    """`run` is the scope that costs; `read` reads. `keys.astro` says so."""
    r = await _run(client, "notes-to-llms", key_read)
    assert r.status_code == 403
    assert "run" in r.json()["detail"]
    assert llm.calls == []


async def test_an_unknown_skill_is_not_hosted(client, key_run, llm):
    r = await _run(client, "make-me-a-sandwich", key_run)
    assert r.status_code == 404
    assert llm.calls == []


# --- the demo's own bounds ---------------------------------------------------


async def test_input_over_the_showcase_cap_is_refused(client, key_run, llm, priced):
    r = await client.post("/api/skills/notes-to-llms/run",
                          json={"input": "x" * (MAX_INPUT_CHARS + 1)},
                          headers=_auth(key_run))
    assert r.status_code == 400
    body = r.json()
    assert body["limit"] == MAX_INPUT_CHARS
    assert llm.calls == []          # refused before any spend


async def test_input_at_the_cap_is_allowed(client, key_run, llm, priced):
    r = await client.post("/api/skills/notes-to-llms/run",
                          json={"input": "x" * MAX_INPUT_CHARS},
                          headers=_auth(key_run))
    assert r.status_code == 200
    assert len(llm.calls) == 1


async def test_concept_abstract_requires_a_concept(client, key_run, llm, priced):
    r = await _run(client, "concept-abstract-mini", key_run)
    assert r.status_code == 400
    assert "concept" in r.json()["detail"]
    assert llm.calls == []


async def test_the_free_plan_has_no_model_passes(client, session, llm, priced):
    """15 §5: `lint_model_passes` is False on free. The 402 says what to buy."""
    caller = await _caller(session, ["read", "run"], plan_id="free")
    r = await _run(client, "notes-to-llms", caller)
    assert r.status_code == 402
    body = r.json()
    assert body["code"] == "quota"
    assert body["tier"] == "free"
    assert body["upgrade_url"] and "starter" in body["upgrade_url"]
    assert llm.calls == []


# --- money -------------------------------------------------------------------


async def test_a_model_with_no_price_is_refused_before_spending(
    client, key_run, llm
):
    """A fresh deployment has no Claude price: `DEFAULT_PRICES` omits it.

    The refusal has to come *before* the provider call, or the owner has paid
    for tokens the ledger cannot record at any rate.
    """
    r = await _run(client, "notes-to-llms", key_run)
    assert r.status_code == 502
    assert MODEL in r.json()["detail"]
    assert llm.calls == []


async def test_a_successful_run_writes_exactly_two_ledger_rows(
    client, session, key_run, llm, priced
):
    r = await _run(client, "notes-to-llms", key_run)
    assert r.status_code == 200
    body = r.json()
    assert body["skill"] == "notes-to-llms"
    assert body["bounded"] is True
    assert body["passes"] == 1
    assert body["output"] == llm.reply
    assert body["input_tokens"] == 120 and body["output_tokens"] == 340

    rows = (await session.execute(
        select(m.LedgerEntry).where(m.LedgerEntry.user_id == key_run.user.id)
    )).scalars().all()
    assert sorted(row.kind for row in rows) == ["input", "output"]
    assert {row.model for row in rows} == {MODEL}
    assert sorted(row.units for row in rows) == [120, 340]

    job = (await session.execute(
        select(m.Job).where(m.Job.user_id == key_run.user.id)
    )).scalars().one()
    assert job.kind == "notes" and job.status == "done"
    assert job.cost_tokens == 460


async def test_a_failed_provider_call_bills_nothing(
    client, session, key_run, llm, priced
):
    """Gateway rule 5, on this surface: never bill for work that did not happen."""
    llm.raise_on_call = RuntimeError("connection reset by peer")
    r = await _run(client, "notes-to-llms", key_run)
    assert r.status_code == 502

    rows = (await session.execute(
        select(m.LedgerEntry).where(m.LedgerEntry.user_id == key_run.user.id)
    )).scalars().all()
    assert rows == []

    job = (await session.execute(
        select(m.Job).where(m.Job.user_id == key_run.user.id)
    )).scalars().one()
    assert job.status == "failed"           # the attempt is still on the record


async def test_the_providers_own_error_text_never_reaches_the_caller(
    client, key_run, llm, priced
):
    """An auth failure's message can carry the request URL and part of the key."""
    llm.raise_on_call = RuntimeError(
        "401 unauthorized for https://api.anthropic.com/v1/messages "
        "key sk-ant-secret-value"
    )
    r = await _run(client, "notes-to-llms", key_run)
    assert r.status_code == 502
    assert "sk-ant-secret-value" not in r.text
    assert "api.anthropic.com" not in r.text


# --- the two-pass skill ------------------------------------------------------


async def test_the_optimizer_runs_exactly_two_passes(
    client, session, key_run, llm, priced
):
    """Audit then fix — and the fix pass is given the audit's findings."""
    r = await _run(client, "optimizer-pass", key_run)
    assert r.status_code == 200
    assert r.json()["passes"] == 2
    assert len(llm.calls) == 2
    assert "audit" in llm.calls[0]["system"].lower()
    assert llm.reply in llm.calls[1]["prompt"]      # findings carried forward

    rows = (await session.execute(
        select(m.LedgerEntry).where(m.LedgerEntry.user_id == key_run.user.id)
    )).scalars().all()
    # Still two rows: one input total, one output total, both passes summed.
    assert sorted(row.kind for row in rows) == ["input", "output"]
    assert sorted(row.units for row in rows) == [240, 680]


# --- the catalogue -----------------------------------------------------------


@pytest_asyncio.fixture
async def keyless_client(tmp_path) -> AsyncIterator[AsyncClient]:
    """A client with no database behind it.

    `GET /api/skills` reads a module-level table and touches no session, so
    requiring Postgres to test it would skip the one check that can run on a
    machine without a server — which is every machine the site is developed on.
    """
    settings = Settings.load({
        "DATABASE_URL": "postgresql+asyncpg://unused@127.0.0.1/unused",
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
        "STORES_ROOT": str(tmp_path / "stores"),
    })
    transport = ASGITransport(app=create_app(settings))
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def test_the_skill_list_needs_no_key(keyless_client):
    """A playground page renders itself before the visitor has pasted a key."""
    r = await keyless_client.get("/api/skills")
    assert r.status_code == 200
    body = r.json()
    assert {s["name"] for s in body["skills"]} == {
        "notes-to-llms", "optimizer-pass", "concept-abstract-mini"
    }
    assert all(s["bounded"] is True for s in body["skills"])
    assert all(s["scope"] == "run" for s in body["skills"])
