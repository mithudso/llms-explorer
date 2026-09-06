# api/tests/test_secrets_crypto.py
"""Symmetric at-rest encryption for third-party secrets this service stores
on a caller's behalf (today: their own Anthropic API key)."""
from __future__ import annotations

import pytest

from explorer_api import secrets_crypto
from explorer_api.settings import Settings


def _settings(**overrides: str) -> Settings:
    values = {
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/x",
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_x",
        **overrides,
    }
    return Settings.load(values)


def test_a_round_trip_returns_the_original_plaintext():
    settings = _settings(
        ANTHROPIC_KEY_ENCRYPTION_SECRET=secrets_crypto.generate_key()
    )
    ciphertext = secrets_crypto.encrypt("sk-ant-api03-abc123", settings)
    assert ciphertext != "sk-ant-api03-abc123"
    assert secrets_crypto.decrypt(ciphertext, settings) == "sk-ant-api03-abc123"


def test_encrypting_without_the_setting_configured_is_a_clear_error():
    settings = _settings()  # no ANTHROPIC_KEY_ENCRYPTION_SECRET
    with pytest.raises(secrets_crypto.EncryptionNotConfigured):
        secrets_crypto.encrypt("sk-ant-api03-abc123", settings)


def test_generate_key_produces_a_valid_fernet_key():
    from cryptography.fernet import Fernet

    key = secrets_crypto.generate_key()
    Fernet(key.encode())  # raises ValueError if malformed
