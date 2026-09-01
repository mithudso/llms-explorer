# api/tests/test_keys.py
"""Scoped API keys: Argon2id-hashed, prefix-looked-up, shown exactly once.

The plan's two tests (Task 4 Step 1) come first, verbatim in intent; the rest
are written from the attacker's side, because this is the module where a bug
hands somebody else's key away:

* the plaintext must not be recoverable from anything we store or return,
* a tampered or malformed key must be refused without raising,
* a revoked key must stop working the instant it is revoked,
* another user's key must be neither listable nor revocable — and must 404,
  not 403, so the id space cannot be enumerated.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from explorer_api import keys, models as m
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.keys import current_user, router as keys_router
from explorer_api.settings import Settings


async def _user(session) -> m.User:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test")
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def user(session) -> m.User:
    return await _user(session)


@pytest_asyncio.fixture
async def client(session, user, database_url: str) -> AsyncIterator[AsyncClient]:
    """The keys router, mounted on the real app, signed in as ``user``.

    ``get_session`` is pinned to the test's own session so an assertion made
    straight afterwards sees the same rows the route wrote, and ``current_user``
    stands in for Task 3's session cookie, which does not exist yet.
    """
    settings = Settings.load(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_x",
        }
    )
    app = create_app(settings)
    # Wiring the router into `main.create_app` belongs to the task that owns
    # `main.py`; mounting it here keeps this task to its three files.
    app.include_router(keys_router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


# --- the plan's two tests ----------------------------------------------------


async def test_the_plaintext_key_is_shown_once_and_never_stored(session, client):
    r = await client.post("/api/keys", json={"scopes": ["read"]})
    assert r.status_code == 201
    raw = r.json()["key"]
    assert raw.startswith("llmsx_")
    row = (await session.execute(select(m.ApiKey))).scalar_one()
    assert raw not in (row.hash + row.prefix)          # the secret half is not recoverable
    assert (await client.get("/api/keys")).json()[0].get("key") is None
    assert await keys.authenticate(session, raw) is not None
    assert await keys.authenticate(session, _tamper(raw)) is None


async def test_a_revoked_key_stops_working_immediately(session, client):
    raw = (await client.post("/api/keys", json={"scopes": ["read"]})).json()["key"]
    kid = (await client.get("/api/keys")).json()[0]["id"]
    assert (await client.delete(f"/api/keys/{kid}")).status_code == 204
    assert await keys.authenticate(session, raw) is None


# --- the secret really is one-way -------------------------------------------


def _tamper(raw: str) -> str:
    """``raw`` with its last character changed — never equal to ``raw``."""
    return raw[:-1] + ("x" if raw[-1] != "x" else "y")


async def test_storage_is_argon2id_over_the_secret_half_only(session, user):
    raw, row = await keys.create(session, user, ["read"])
    await session.flush()
    _, prefix, secret = raw.split("_", 2)
    assert row.prefix == prefix
    assert row.hash.startswith("$argon2id$")           # not argon2i, not a plain digest
    assert secret not in row.hash and prefix not in row.hash
    assert keys.PLAINTEXT_FIELD not in {c.name for c in m.ApiKey.__table__.columns}


async def test_every_key_is_distinct(session, user):
    raws = [(await keys.create(session, user, ["read"]))[0] for _ in range(3)]
    await session.flush()
    assert len(set(raws)) == 3
    rows = (await session.execute(select(m.ApiKey))).scalars().all()
    assert len({r.prefix for r in rows}) == 3
    assert len({r.hash for r in rows}) == 3            # a per-key salt, not a bare hash


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "llmsx_",
        "llmsx_deadbeef",
        "lx_deadbeefcafe_secret",                      # the spoke's older prefix
        "llmsx__secret",
        "llmsx_NOTHEX!!!!!!!!_secret",
        "Bearer llmsx_deadbeefcafe_secret",
        "llmsx_deadbeefcafe_" + "x" * 5000,
    ],
)
async def test_a_malformed_key_is_refused_and_never_raises(session, bad):
    assert await keys.authenticate(session, bad) is None


async def test_a_key_from_a_different_prefix_cannot_borrow_another_secret(session, user):
    raw_a, _ = await keys.create(session, user, ["read"])
    _raw_b, row_b = await keys.create(session, user, ["read"])
    await session.flush()
    secret_a = raw_a.split("_", 2)[2]
    assert await keys.authenticate(session, f"llmsx_{row_b.prefix}_{secret_a}") is None


# --- lifecycle ---------------------------------------------------------------


async def test_authenticate_stamps_last_used(session, user):
    raw, row = await keys.create(session, user, ["read"])
    # Committed, because the stamp is deliberately written on its own connection
    # (so a long request cannot hold a lock on `api_keys` for its whole
    # duration) and that connection can only see committed rows.
    await session.commit()
    assert row.last_used_at is None
    found = await keys.authenticate(session, raw)
    assert found is not None and found.id == row.id
    assert found.last_used_at is not None


async def test_a_soft_deleted_users_key_stops_working(session, user):
    raw, _ = await keys.create(session, user, ["read"])
    await session.flush()
    assert await keys.authenticate(session, raw) is not None
    user.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
    assert await keys.authenticate(session, raw) is None


# --- scopes ------------------------------------------------------------------


async def test_scopes_must_be_a_non_empty_subset_of_the_three(client):
    assert (await client.post("/api/keys", json={"scopes": []})).status_code == 422
    assert (await client.post("/api/keys", json={"scopes": ["admin"]})).status_code == 422
    assert (await client.post("/api/keys", json={"scopes": ["read", "read"]})).status_code == 422
    ok = await client.post("/api/keys", json={"scopes": ["read", "run", "publish"]})
    assert ok.status_code == 201
    assert ok.json()["scopes"] == ["read", "run", "publish"]


# --- one user's keys are not another's ---------------------------------------


async def test_another_users_key_is_invisible_and_unrevocable(session, user, client):
    stranger = await _user(session)
    _, theirs = await keys.create(session, stranger, ["read"])
    await session.flush()

    mine = (await client.post("/api/keys", json={"scopes": ["read"]})).json()
    listed = (await client.get("/api/keys")).json()
    assert [k["id"] for k in listed] == [mine["id"]]        # never the stranger's

    # 404, not 403: the response must not confirm that the id exists at all.
    assert (await client.delete(f"/api/keys/{theirs.id}")).status_code == 404
    await session.refresh(theirs)
    assert theirs.revoked_at is None


async def test_revoking_twice_is_a_404_the_second_time(client):
    kid = (await client.post("/api/keys", json={"scopes": ["read"]})).json()["id"]
    assert (await client.delete(f"/api/keys/{kid}")).status_code == 204
    assert (await client.delete(f"/api/keys/{kid}")).status_code == 404


async def test_a_revoked_key_is_still_listed_so_its_history_is_visible(client):
    kid = (await client.post("/api/keys", json={"scopes": ["read"]})).json()["id"]
    await client.delete(f"/api/keys/{kid}")
    listed = (await client.get("/api/keys")).json()
    assert len(listed) == 1 and listed[0]["revoked_at"] is not None


async def test_signed_out_callers_get_401(session, database_url):
    """With no ``current_user`` override the router refuses every method."""
    settings = Settings.load(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_x",
        }
    )
    app = create_app(settings)
    app.include_router(keys_router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        assert (await http.get("/api/keys")).status_code == 401
        assert (await http.post("/api/keys", json={"scopes": ["read"]})).status_code == 401
        assert (await http.delete("/api/keys/key_whatever")).status_code == 401
