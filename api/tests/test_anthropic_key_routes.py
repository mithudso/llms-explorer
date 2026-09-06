"""`PUT`/`DELETE /api/account/anthropic-key` — an account's own stored key."""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from explorer_api import anthropic_keys, models as m, secrets_crypto
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.anthropic_key import get_validator
from explorer_api.routes.auth import current_user
from explorer_api.settings import Settings


async def _user(session) -> m.User:
    u = m.User(email="byok-route@example.test", email_verified=True)
    session.add(u)
    await session.flush()
    return u


class FakeValidator:
    def __init__(self, *, accept: bool = True) -> None:
        self.accept = accept

    async def __call__(self, api_key: str) -> None:
        if not self.accept:
            raise anthropic_keys.InvalidApiKey("rejected")


@pytest_asyncio.fixture
async def user(session) -> m.User:
    return await _user(session)


@pytest_asyncio.fixture
async def client(session, user, database_url: str) -> AsyncIterator[AsyncClient]:
    settings = Settings.load({
        "DATABASE_URL": database_url,
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
        "ANTHROPIC_KEY_ENCRYPTION_SECRET": secrets_crypto.generate_key(),
    })
    app = create_app(settings)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[get_validator] = lambda: FakeValidator(accept=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        http.app = app  # so a test can change dependency overrides mid-test
        yield http


async def test_saving_a_valid_key_returns_its_hint(client, session, user):
    r = await client.put("/api/account/anthropic-key",
                         json={"api_key": "sk-ant-api03-abcXYZ1234"})
    assert r.status_code == 200, r.text
    assert r.json() == {"hint": "1234"}
    await session.refresh(user)
    assert user.anthropic_api_key_ciphertext is not None


async def test_saving_an_invalid_key_is_422_and_stores_nothing(
    client, session, user
):
    client.app.dependency_overrides[get_validator] = lambda: FakeValidator(accept=False)
    r = await client.put("/api/account/anthropic-key",
                         json={"api_key": "sk-ant-bad"})
    assert r.status_code == 422
    await session.refresh(user)
    assert user.anthropic_api_key_ciphertext is None


async def test_deleting_clears_a_stored_key(client, session, user):
    await client.put("/api/account/anthropic-key",
                     json={"api_key": "sk-ant-api03-abcXYZ1234"})
    r = await client.delete("/api/account/anthropic-key")
    assert r.status_code == 204
    await session.refresh(user)
    assert user.anthropic_api_key_ciphertext is None
