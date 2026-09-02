"""`/api/subscribers`: double opt-in, one-click unsubscribe, no enumeration.

Three properties worth a test each, because a mailing list is where a bug leaks
whether an address is on the list, or lets someone else unsubscribe it:

* subscribing twice, or with garbage, never reveals which happened,
* a notice only ever reaches a confirmed, still-subscribed address,
* an unsubscribe token works exactly once and needs no other credential.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from explorer_api import models as m
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.settings import Settings


@pytest_asyncio.fixture
async def client(session, database_url: str) -> AsyncIterator[AsyncClient]:
    settings = Settings.load(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_x",
        }
    )
    app = create_app(settings)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def test_subscribe_stores_an_unconfirmed_row(session, client):
    r = await client.post("/api/subscribers", json={"email": "reader@example.test"})
    assert r.status_code == 202
    row = (
        await session.execute(
            select(m.Subscriber).where(m.Subscriber.email == "reader@example.test"))
    ).scalar_one()
    assert row.confirmed_at is None
    assert row.unsubscribed_at is None


async def test_subscribing_twice_answers_identically(session, client):
    first = await client.post("/api/subscribers", json={"email": "twice@example.test"})
    second = await client.post("/api/subscribers", json={"email": "twice@example.test"})
    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    rows = (
        await session.execute(
            select(m.Subscriber).where(m.Subscriber.email == "twice@example.test"))
    ).scalars().all()
    assert len(rows) == 1


async def test_garbage_email_is_rejected(client):
    r = await client.post("/api/subscribers", json={"email": "not-an-email"})
    assert r.status_code == 422


async def test_confirm_flips_confirmed_at_and_is_idempotent(session, client):
    await client.post("/api/subscribers", json={"email": "confirm@example.test"})
    row = (
        await session.execute(
            select(m.Subscriber).where(m.Subscriber.email == "confirm@example.test"))
    ).scalar_one()
    token = row.confirm_token

    r1 = await client.get("/api/subscribers/confirm", params={"token": token})
    assert r1.status_code == 200
    await session.refresh(row)
    assert row.confirmed_at is not None

    # A second redemption of the same token is a no-op, not an error — the
    # alternative (404 on an already-used token) would let a token be
    # distinguished from an unknown one.
    r2 = await client.get("/api/subscribers/confirm", params={"token": token})
    assert r2.status_code == 200


async def test_unsubscribe_flips_unsubscribed_at_and_stops_notice(session, client):
    from explorer_api import notify
    from explorer_api.settings import Settings as S

    await client.post("/api/subscribers", json={"email": "bye@example.test"})
    row = (
        await session.execute(select(m.Subscriber).where(m.Subscriber.email == "bye@example.test"))
    ).scalar_one()
    await client.get("/api/subscribers/confirm", params={"token": row.confirm_token})
    await session.refresh(row)

    r = await client.get("/api/subscribers/unsubscribe", params={"token": row.unsubscribe_token})
    assert r.status_code == 200
    await session.refresh(row)
    assert row.unsubscribed_at is not None

    settings = S.load(
        {
            "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/x",
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_x",
        }
    )
    count = await notify.notify_new_post(session, settings, title="t", url="https://x/t")
    assert count == 0
