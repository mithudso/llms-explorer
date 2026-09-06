"""Saving, validating and clearing an account's own Anthropic API key.

Validation is one real call before anything is ever encrypted or stored — a
bad key is a clear, immediate error rather than a confusing failure the next
time a hosted skill runs. The validator is injected (`Validator` protocol)
so these tests never make a real network call, the same pattern
`billing.StripeGateway` uses for Checkout/Portal calls.
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from explorer_api import anthropic_keys, models as m, secrets_crypto
from explorer_api.settings import Settings


def _settings() -> Settings:
    return Settings.load({
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/x",
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
        "ANTHROPIC_KEY_ENCRYPTION_SECRET": secrets_crypto.generate_key(),
    })


class FakeValidator:
    def __init__(self, *, accept: bool = True) -> None:
        self.accept = accept
        self.calls: list[str] = []

    async def __call__(self, api_key: str) -> None:
        self.calls.append(api_key)
        if not self.accept:
            raise anthropic_keys.InvalidApiKey("the model provider rejected this key")


@pytest_asyncio.fixture
async def user(session) -> m.User:
    u = m.User(email="byok@example.test", email_verified=True)
    session.add(u)
    await session.flush()
    return u


async def test_saving_a_valid_key_stores_ciphertext_and_a_hint(session, user):
    settings = _settings()
    validator = FakeValidator(accept=True)
    hint = await anthropic_keys.save(
        session, user, "sk-ant-api03-abcXYZ1234", settings, validate=validator
    )
    assert hint == "1234"
    assert validator.calls == ["sk-ant-api03-abcXYZ1234"]
    assert user.anthropic_api_key_hint == "1234"
    assert user.anthropic_api_key_ciphertext is not None
    assert user.anthropic_api_key_ciphertext != "sk-ant-api03-abcXYZ1234"
    assert secrets_crypto.decrypt(user.anthropic_api_key_ciphertext, settings) == \
        "sk-ant-api03-abcXYZ1234"


async def test_saving_an_invalid_key_stores_nothing(session, user):
    settings = _settings()
    validator = FakeValidator(accept=False)
    with pytest.raises(anthropic_keys.InvalidApiKey):
        await anthropic_keys.save(
            session, user, "sk-ant-bad-key", settings, validate=validator
        )
    assert user.anthropic_api_key_ciphertext is None
    assert user.anthropic_api_key_hint is None


async def test_clearing_removes_both_columns(session, user):
    settings = _settings()
    await anthropic_keys.save(
        session, user, "sk-ant-api03-abcXYZ1234", settings, validate=FakeValidator()
    )
    await anthropic_keys.clear(user)
    assert user.anthropic_api_key_ciphertext is None
    assert user.anthropic_api_key_hint is None


async def test_saving_without_encryption_configured_refuses(session, user):
    settings = Settings.load({
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/x",
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
    })
    with pytest.raises(anthropic_keys.NotConfigured):
        await anthropic_keys.save(
            session, user, "sk-ant-api03-abcXYZ1234", settings, validate=FakeValidator()
        )
