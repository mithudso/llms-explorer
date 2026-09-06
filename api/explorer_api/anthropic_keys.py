"""An account's own Anthropic API key: save (validated, encrypted), clear.

Authority: `docs/superpowers/specs/2026-09-06-byok-hosted-skills-design.md` §3.

The key is validated with one real, free call (`models.list()` — no tokens
spent) *before* it is ever encrypted or written, so a typo or an expired key
is a clear 422 at save time, not a confusing failure the next time a hosted
skill runs. The validator is injected (`Validator` protocol) exactly the way
`billing.StripeGateway` injects Checkout/Portal calls — so this module never
forces a test to reach the real network, and a route can wire in the real one.
"""

from __future__ import annotations

from typing import Protocol

from . import models as m
from . import secrets_crypto
from .settings import Settings

HINT_LEN = 4


class AnthropicKeyError(RuntimeError):
    """Base for everything this module refuses to do."""


class InvalidApiKey(AnthropicKeyError):
    """The provider rejected this key, or it is obviously malformed."""


class NotConfigured(AnthropicKeyError):
    """This server has no `ANTHROPIC_KEY_ENCRYPTION_SECRET` set."""


class Validator(Protocol):
    """Confirms a key actually authenticates. Raises :class:`InvalidApiKey` if not."""

    async def __call__(self, api_key: str) -> None: ...


async def real_validator(api_key: str) -> None:
    """The real check: one free call, no tokens spent."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        await client.models.list()
    except anthropic.AuthenticationError as exc:
        raise InvalidApiKey("the model provider rejected this key") from exc
    except anthropic.APIError as exc:
        raise InvalidApiKey(
            "the model provider could not validate this key right now"
        ) from exc


async def save(
    session: object, user: m.User, api_key: str, settings: Settings,
    *, validate: Validator = real_validator,
) -> str:
    """Validate, encrypt and store ``api_key`` on ``user``. Returns the hint.

    Nothing is written to ``user`` unless validation succeeds — a bad key
    leaves the account's existing key (or lack of one) untouched.
    """
    if settings.anthropic_key_encryption_secret is None:
        raise NotConfigured("ANTHROPIC_KEY_ENCRYPTION_SECRET is not set on this server")
    await validate(api_key)
    ciphertext = secrets_crypto.encrypt(api_key, settings)
    user.anthropic_api_key_ciphertext = ciphertext
    user.anthropic_api_key_hint = api_key[-HINT_LEN:]
    return user.anthropic_api_key_hint


async def clear(user: m.User) -> None:
    """Remove the stored key, if any. Idempotent."""
    user.anthropic_api_key_ciphertext = None
    user.anthropic_api_key_hint = None


__all__ = [
    "AnthropicKeyError",
    "HINT_LEN",
    "InvalidApiKey",
    "NotConfigured",
    "Validator",
    "clear",
    "real_validator",
    "save",
]
