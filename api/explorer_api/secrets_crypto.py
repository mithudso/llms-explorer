# api/explorer_api/secrets_crypto.py
"""At-rest encryption for third-party secrets this service stores on a
caller's behalf — today, an account's own Anthropic API key
(`explorer_api.anthropic_keys`).

Symmetric, via `cryptography.fernet.Fernet`, keyed by
`Settings.anthropic_key_encryption_secret`. Deliberately not the same secret
as `Settings.session_secret` or any other: a secret with one job is a secret
that can be rotated without touching what else depends on it.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from .settings import Settings


class EncryptionNotConfigured(RuntimeError):
    """`ANTHROPIC_KEY_ENCRYPTION_SECRET` is not set on this server."""


class DecryptionFailed(RuntimeError):
    """The ciphertext does not decrypt under the configured key.

    Only ever means the key changed since this row was written, or the row is
    corrupt — never a normal runtime outcome, so callers should treat it as a
    configuration or data-integrity problem, not a per-request refusal.
    """


def generate_key() -> str:
    """A fresh Fernet key, suitable for `ANTHROPIC_KEY_ENCRYPTION_SECRET`."""
    return Fernet.generate_key().decode("ascii")


def _fernet(settings: Settings) -> Fernet:
    secret = settings.anthropic_key_encryption_secret
    if secret is None:
        raise EncryptionNotConfigured(
            "ANTHROPIC_KEY_ENCRYPTION_SECRET is not set on this server"
        )
    return Fernet(secret.get_secret_value().encode("ascii"))


def encrypt(plaintext: str, settings: Settings) -> str:
    return _fernet(settings).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(ciphertext: str, settings: Settings) -> str:
    try:
        return _fernet(settings).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise DecryptionFailed(
            "stored ciphertext does not decrypt under the configured key"
        ) from exc


__all__ = [
    "DecryptionFailed",
    "EncryptionNotConfigured",
    "decrypt",
    "encrypt",
    "generate_key",
]
