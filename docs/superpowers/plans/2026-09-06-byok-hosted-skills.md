# Bring-your-own-API-key for Hosted Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a signed-in account store its own Anthropic API key, encrypted at rest, and use it — instead of a plan-granted quota that no longer exists — to unlock the three hosted showcase skills (`notes-to-llms`, `optimizer-pass`, `concept-abstract-mini`).

**Architecture:** A new `explorer_api.secrets_crypto` module wraps `cryptography.fernet.Fernet` for generic at-rest encryption. A new `explorer_api.anthropic_keys` domain module owns save/clear, validating a key with one free Anthropic call before ever encrypting it. `routes/anthropic_key.py` exposes that as `PUT`/`DELETE /api/account/anthropic-key`. `routes/skills.py`'s `_check_plan` drops its dead `lint_model_passes` quota check for a "does this account have a stored key" check, and `get_llm_client` becomes a factory built per-request from the caller's own decrypted key rather than one process-wide client built from the site's key — because the caller now pays Anthropic directly, `_quote()` and the two `ledger.record()` calls are skipped for this surface entirely.

**Tech Stack:** FastAPI, SQLAlchemy 2 + Alembic, `cryptography` (new dependency), the existing `anthropic` SDK.

**Authority:** `docs/superpowers/specs/2026-09-06-byok-hosted-skills-design.md`.

---

## Global notes for every task

- Python: `.venv/bin/python`/`.venv/bin/pytest`/`.venv/bin/alembic`, run from `api/`. Load env first: `set -a && . ./.env && set +a`.
- One commit per task. Never commit `api/.env`.
- **Deviation from the design spec, decided during this plan's research:** the spec says `ANTHROPIC_KEY_ENCRYPTION_SECRET` is "required at startup." Reading `explorer_api/settings.py`, the sibling secret this feature depends on — `anthropic_api_key` (the *site's* key, used before this plan existed) — is deliberately **optional**, with the comment "absent means that one surface refuses with 'not configured', rather than the whole app failing to boot over a feature most deployments do not run." That is exactly this feature's situation too, so Task 1 makes `anthropic_key_encryption_secret` optional, matching the established convention, not a new `REQUIRED_VARS` entry.

---

### Task 1: `secrets_crypto.py` and the new setting

**Files:**
- Create: `api/explorer_api/secrets_crypto.py`
- Modify: `api/explorer_api/settings.py`
- Modify: `api/pyproject.toml`
- Test: `api/tests/test_secrets_crypto.py`

- [ ] **Step 1: Add the dependency**

In `api/pyproject.toml`, in `[project].dependencies`, add (`cryptography` is already pulled in transitively by `httpx`/`anthropic`'s TLS stack, but this module imports it directly, so it must be declared):

```toml
    "anthropic>=0.40",
    "cryptography>=42",
```

- [ ] **Step 2: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_secrets_crypto.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'explorer_api.secrets_crypto'`.

- [ ] **Step 3: Add the setting**

In `api/explorer_api/settings.py`, immediately after the existing `anthropic_api_key` field (line 142):

```python
    #: Encrypts a caller's own stored Anthropic key (`secrets_crypto.py`) —
    #: a different secret from `anthropic_api_key` above, which is this
    #: server's own key. Optional for the same reason `anthropic_api_key` is:
    #: absent means the one feature that needs it refuses cleanly, not that
    #: the whole app fails to boot over a feature most deployments do not run.
    anthropic_key_encryption_secret: SecretStr | None = None
```

- [ ] **Step 4: Write `secrets_crypto.py`**

```python
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
```

- [ ] **Step 5: Run test to verify it passes, then commit**

```bash
.venv/bin/python -m pytest tests/test_secrets_crypto.py -q
```
Expected: PASS, 3 tests.

```bash
git add api/explorer_api/secrets_crypto.py api/explorer_api/settings.py api/pyproject.toml api/tests/test_secrets_crypto.py
git commit -m "feat(api): secrets_crypto — at-rest encryption for stored third-party keys"
```

---

### Task 2: `User` gets two new columns

**Files:**
- Create: `api/alembic/versions/20260906_e5f6a7b8c9d0_anthropic_api_key.py`
- Modify: `api/explorer_api/models.py`
- Test: `api/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Add to `api/tests/test_models.py` (near the other `User`-focused tests):

```python
async def test_a_user_can_store_an_encrypted_anthropic_key_and_a_hint(session):
    u = await _user(session)
    assert u.anthropic_api_key_ciphertext is None
    assert u.anthropic_api_key_hint is None
    u.anthropic_api_key_ciphertext = "gAAAAA...ciphertext..."
    u.anthropic_api_key_hint = "aB3f"
    await session.commit()
    await session.refresh(u)
    assert u.anthropic_api_key_ciphertext == "gAAAAA...ciphertext..."
    assert u.anthropic_api_key_hint == "aB3f"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_models.py::test_a_user_can_store_an_encrypted_anthropic_key_and_a_hint -q`
Expected: FAIL — `AttributeError: 'User' object has no attribute 'anthropic_api_key_ciphertext'`.

- [ ] **Step 3: Add the columns**

In `api/explorer_api/models.py`, in the `User` class, immediately after `plan_id` (after line 148, before the `org_id` comment):

```python
    #: This account's own Anthropic key, Fernet-encrypted (`secrets_crypto.py`)
    #: — never the site's own key, which lives only in `Settings`. `NULL` means
    #: the account has not set one, which is what `routes/skills.py`'s
    #: `_check_plan` refuses on.
    anthropic_api_key_ciphertext: Mapped[str | None] = mapped_column(Text)
    #: Last 4 characters of the plaintext key, unencrypted. Not a secret — a
    #: high-entropy key's last 4 characters are not guessable-useful — it
    #: exists purely so account settings can show "key ending in …aB3f"
    #: without ever redisplaying the key itself, mirroring `ApiKey.prefix`.
    anthropic_api_key_hint: Mapped[str | None] = mapped_column(String(4))
```

- [ ] **Step 4: Write the migration**

```python
# api/alembic/versions/20260906_e5f6a7b8c9d0_anthropic_api_key.py
"""anthropic api key

Adds the two columns a caller's own, encrypted Anthropic key lives in
(donations design follow-up: bring-your-own-key for the hosted skills).

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-06 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("anthropic_api_key_ciphertext", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("anthropic_api_key_hint", sa.String(4), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "anthropic_api_key_hint")
    op.drop_column("users", "anthropic_api_key_ciphertext")
```

- [ ] **Step 5: Run migration and tests, then commit**

```bash
set -a && . ./.env && set +a
.venv/bin/alembic upgrade head
.venv/bin/python -m pytest tests/test_models.py::test_a_user_can_store_an_encrypted_anthropic_key_and_a_hint tests/test_models.py::test_the_migration_and_the_models_have_not_drifted -q
```
Expected: migration applies cleanly, both tests PASS.

```bash
git add api/alembic/versions/20260906_e5f6a7b8c9d0_anthropic_api_key.py api/explorer_api/models.py api/tests/test_models.py
git commit -m "feat(api): User gains anthropic_api_key_ciphertext/_hint columns"
```

---

### Task 3: `anthropic_keys.py` — save, validate, clear

**Files:**
- Create: `api/explorer_api/anthropic_keys.py`
- Test: `api/tests/test_anthropic_keys.py`

**Files this task does NOT touch:** `routes/anthropic_key.py` (Task 4) and `routes/skills.py` (Task 5) — this task is the domain module only, matching this repo's "routes are thin, a domain module owns the rule" convention (`explorer_api/keys.py`, `explorer_api/billing.py`).

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_anthropic_keys.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_anthropic_keys.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'explorer_api.anthropic_keys'`.

- [ ] **Step 3: Write `anthropic_keys.py`**

```python
# api/explorer_api/anthropic_keys.py
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
```

- [ ] **Step 4: Run test to verify it passes, then commit**

```bash
.venv/bin/python -m pytest tests/test_anthropic_keys.py -q
```
Expected: PASS, 4 tests.

```bash
git add api/explorer_api/anthropic_keys.py api/tests/test_anthropic_keys.py
git commit -m "feat(api): anthropic_keys — validate, encrypt, store an account's own key"
```

---

### Task 4: `routes/anthropic_key.py`

**Files:**
- Create: `api/explorer_api/routes/anthropic_key.py`
- Modify: `api/explorer_api/routes/__init__.py`
- Test: `api/tests/test_anthropic_key_routes.py`

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_anthropic_key_routes.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_anthropic_key_routes.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'explorer_api.routes.anthropic_key'`.

- [ ] **Step 3: Write `routes/anthropic_key.py`**

```python
# api/explorer_api/routes/anthropic_key.py
"""`/api/account/anthropic-key` — an account's own stored Anthropic key.

Kept separate from `routes/keys.py`, which manages this app's *own* platform
API keys — a different concept: this file is about a third-party secret this
service stores on the caller's behalf, not a credential that authenticates
*to* this service.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from .. import anthropic_keys
from ..db import get_session
from ..models import User
from .auth import current_user

router = APIRouter(prefix="/api/account/anthropic-key", tags=["account"])

CurrentUser = Annotated[User, Depends(current_user)]
Session = Annotated["object", Depends(get_session)]


def get_validator(request: Request) -> anthropic_keys.Validator:
    """The real validator by default; a test overrides this dependency."""
    return anthropic_keys.real_validator


Validator = Annotated[anthropic_keys.Validator, Depends(get_validator)]


class KeyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key: str = Field(min_length=1)


class KeyOut(BaseModel):
    hint: str


@router.put("", response_model=KeyOut, summary="Save (and validate) this account's Anthropic key")
async def save_key(
    body: KeyIn, user: CurrentUser, session: Session, validate: Validator,
    request: Request,
) -> KeyOut:
    settings = request.app.state.settings
    try:
        hint = await anthropic_keys.save(
            session, user, body.api_key, settings, validate=validate
        )
    except anthropic_keys.NotConfigured as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except anthropic_keys.InvalidApiKey as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    return KeyOut(hint=hint)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Remove the stored key")
async def delete_key(user: CurrentUser, session: Session) -> None:
    await anthropic_keys.clear(user)
    await session.commit()


__all__ = ["KeyIn", "KeyOut", "get_validator", "router"]
```

- [ ] **Step 4: Wire the router**

In `api/explorer_api/routes/__init__.py`, add the import and mount (alongside `donate_routes`, before `mcp_routes`):

```python
from . import anthropic_key as anthropic_key_routes
```

```python
ROUTER_MODULES = (
    auth_routes,
    keys_routes,
    usage_routes,
    billing_routes,
    donate_routes,
    anthropic_key_routes,
    mcp_routes,
```

Run:
```bash
.venv/bin/python -m pytest tests/test_anthropic_key_routes.py -q
```
Expected: PASS, 3 tests.

- [ ] **Step 5: Commit**

```bash
git add api/explorer_api/routes/anthropic_key.py api/explorer_api/routes/__init__.py api/tests/test_anthropic_key_routes.py
git commit -m "feat(api): mount PUT/DELETE /api/account/anthropic-key"
```

---

### Task 5: `routes/skills.py` — the gate and the per-caller client

**Files:**
- Modify: `api/explorer_api/routes/skills.py`
- Modify: `api/explorer_api/plans.py`
- Modify: `api/explorer_api/ledger.py` (docstring only — see Step 3)
- Test: `api/tests/test_skills.py`

This is the task that actually makes the three skills reachable again. Read all of Step 3 before starting — several pieces move together.

- [ ] **Step 1: Write the failing test**

Add to `api/tests/test_skills.py`, replacing `test_the_free_plan_has_no_model_passes` (delete it — the whole premise of "which plan" is gone):

```python
async def test_a_run_without_a_stored_key_is_refused(client, session, llm, priced):
    caller = await _caller(session, ["read", "run"])
    r = await _run(client, "notes-to-llms", caller)
    assert r.status_code == 403
    body = r.json()
    assert body["code"] == "missing_api_key"
    assert llm.calls == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_skills.py::test_a_run_without_a_stored_key_is_refused -q`
Expected: FAIL — `AssertionError` (still refuses via the old `lint_model_passes` path, so `body["code"] == "quota"`, not `"missing_api_key"`; the field doesn't exist yet as a distinct refusal type).

- [ ] **Step 3: Rewrite `_check_plan`, `get_llm_client`, and the run body**

In `api/explorer_api/plans.py`, delete `lint_model_passes` from `QUOTA_FEATURES`, from `FEATURE_KINDS`, and from the free plan's `quotas=` call in `PLANS` — it is no longer a plan-granted quota:

```python
# QUOTA_FEATURES: remove "lint_model_passes" from the tuple
# FEATURE_KINDS: remove the "lint_model_passes": "flag" entry
# The free _plan(...) call: remove the lint_model_passes=False keyword argument
```

In `api/explorer_api/routes/skills.py`:

Add a new exception near the top, after the module's other imports settle (place it right before `_check_plan`'s current location, since that is where it is raised):

```python
class MissingApiKey(gw.GatewayRefusal):
    """This account has not stored an Anthropic key — required to run any
    hosted skill now that there is no plan-granted allowance to spend instead.
    """

    status_code = 403
    code = "missing_api_key"
```

Replace `_check_plan` (the whole function) with:

```python
async def _check_plan(session: AsyncSession, principal: gw.Principal,
                      text: str) -> None:
    """Every prerequisite, in the order that refuses most cheaply first."""
    user = principal.user
    assert user is not None  # the caller checks anonymity before this runs

    if user.anthropic_api_key_ciphertext is None:
        raise MissingApiKey(
            "this skill needs your own Anthropic API key — add one in "
            "account settings"
        )

    size = await ledger.check_quota(session, user, "lint_max_bytes",
                                    amount=len(text.encode("utf-8")))
    if not size.allowed:
        raise gw.QuotaExceeded(
            f"that input is larger than the {size.tier} plan allows",
            **size.as_error(),
        )

    daily = await ledger.check_quota(
        session, user, "lint_per_day",
        used=await _count_model_passes_today(session, user),
    )
    if not daily.allowed:
        raise gw.QuotaExceeded(
            f"today's model-pass allowance on the {daily.tier} plan is used up",
            **daily.as_error(),
        )
```

Replace `get_llm_client` with a factory (keep `LlmClient`/`Completion`/`AnthropicClient`/`LlmUnavailable` exactly as they are — only the injection point changes):

```python
LlmClientFactory = Callable[["m.User"], LlmClient]


def get_llm_client_factory(request: Request) -> LlmClientFactory:
    """A factory, not a client: which key to use is only known once the
    caller's account is resolved, inside the route body — this dependency
    still resolves eagerly (before the body runs), so it cannot itself
    decide the key. Building fresh per call also means a decrypted key is
    never cached anywhere beyond the one request that needed it.
    """
    settings = request.app.state.settings

    def build(user: "m.User") -> LlmClient:
        ciphertext = user.anthropic_api_key_ciphertext
        assert ciphertext is not None  # _check_plan already refused otherwise
        api_key = secrets_crypto.decrypt(ciphertext, settings)
        return AnthropicClient(api_key)

    return build
```

Add the import this needs, alongside the module's existing `from .. import` lines:

```python
from .. import secrets_crypto
```

Add `from collections.abc import Callable` to the existing `from collections.abc import Mapping` line:

```python
from collections.abc import Callable, Mapping
```

In `run_skill`'s signature, replace:

```python
    llm: Llm,
```

with:

```python
    llm_factory: Annotated[LlmClientFactory, Depends(get_llm_client_factory)],
```

and delete the now-unused `Llm = Annotated[LlmClient, Depends(get_llm_client)]` type alias.

In `run_skill`'s body, the caller now pays Anthropic directly, so `_quote()` and the two `ledger.record()` calls are skipped — replace:

```python
        await _check_plan(session, principal, body.input)
        await _quote(session)

        user = principal.user
        assert user is not None
        job = m.Job(user_id=user.id, kind=policy.job_kind, status="running",
                    params={"skill": policy.name, "passes": policy.passes,
                            "bounded": True})
        job.started_at = dt.datetime.now(dt.UTC)
        session.add(job)
        await session.flush()

        try:
            output, in_tokens, out_tokens = await _run_passes(llm, policy, body)
        except gw.GatewayRefusal:
            # The work did not happen, so no ledger row is written — but the
            # attempt stays on the record, committed on its own.
            job.status = "failed"
            job.finished_at = dt.datetime.now(dt.UTC)
            await session.commit()
            raise

        for kind, units in (("input", in_tokens), ("output", out_tokens)):
            await ledger.record(session, user, COMPONENT, kind, MODEL, units,
                                job=job, api_key_id=principal.key.id
                                if principal.key else None,
                                client_ip=principal.ip)
        job.status = "done"
        job.finished_at = dt.datetime.now(dt.UTC)
        job.cost_tokens = in_tokens + out_tokens
        await session.commit()
```

with:

```python
        await _check_plan(session, principal, body.input)

        user = principal.user
        assert user is not None
        llm = llm_factory(user)
        job = m.Job(user_id=user.id, kind=policy.job_kind, status="running",
                    params={"skill": policy.name, "passes": policy.passes,
                            "bounded": True})
        job.started_at = dt.datetime.now(dt.UTC)
        session.add(job)
        await session.flush()

        try:
            output, in_tokens, out_tokens = await _run_passes(llm, policy, body)
        except gw.GatewayRefusal:
            # The work did not happen — the attempt stays on the record.
            job.status = "failed"
            job.finished_at = dt.datetime.now(dt.UTC)
            await session.commit()
            raise

        # No ledger row: the caller's own Anthropic key pays for this call,
        # not this service, so there is no spend of *ours* to record.
        job.status = "done"
        job.finished_at = dt.datetime.now(dt.UTC)
        job.cost_tokens = in_tokens + out_tokens
        await session.commit()
```

Update the module docstring's rules 1 and 3 (currently lines 21-33) to match:

```python
1. **Nothing here is public.** Every call needs the caller's own Anthropic
   key, so the anonymous tier that `hub_query_docset` enjoys does not exist
   here: no key is a 401, and a key without ``run`` is a 403.
2. **One limit, one place** (gateway rule 4). ``lint_max_bytes`` /
   ``lint_per_day`` are abuse-prevention caps, not cost control — the caller
   pays Anthropic directly, not this service.
3. **This service never spends its own credit here.** A caller with no
   stored Anthropic key is refused (`MissingApiKey`) before any model call;
   `explorer_api.anthropic_keys` is where a key is validated once, at save
   time, so a run never discovers a bad key mid-request.
4. **A run's outcome is always on the record.** Every attempt writes a `Job`
   row — status, timing — regardless of who paid for the tokens.
```

`_quote` (the function) becomes unused by `run_skill` — leave its definition in place only if something else calls it; grep to check:

```bash
grep -rn "_quote(" explorer_api/ tests/
```
If `run_skill` was its only caller, delete the `_quote` function definition entirely (dead code) — do not leave an unused function behind.

- [ ] **Step 4: Run the tests, fix the fallout, run the full suite**

```bash
.venv/bin/python -m pytest tests/test_skills.py -q 2>&1 | tail -60
```

This will show several more failures — the tests that give a `key_run`-style caller *no* stored key now hit `MissingApiKey` instead of running. Fix `tests/test_skills.py`:

Remove the `_bypass_model_pass_gate` helper entirely (it existed only to work around the now-deleted `lint_model_passes` gate) and every test that called it. In its place, give `_caller` an optional stored key:

```python
async def _caller(session, scopes: list[str], plan_id: str = "free",
                  with_key: bool = False) -> Caller:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test", plan_id=plan_id)
    if with_key:
        user.anthropic_api_key_ciphertext = "gAAAAA...test-ciphertext..."
        user.anthropic_api_key_hint = "test"
    session.add(user)
    await session.flush()
    raw, _row = await keys.create(session, user, scopes)
    await session.flush()
    return Caller(raw=raw, user=user)
```

Update `key_run` to carry a key (every test that expects a *successful* run uses this fixture):

```python
@pytest_asyncio.fixture
async def key_run(session) -> Caller:
    return await _caller(session, ["read", "run"], with_key=True)
```

Then, since the client's `get_llm_client_factory` dependency needs overriding (not `get_llm_client`, which no longer exists), fix the `client` fixture:

```python
    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_llm_client_factory] = lambda: (lambda user: llm)
```

(Update the import at the top of the file from `get_llm_client` to `get_llm_client_factory`.)

Delete the `priced` fixture and every `priced` parameter from every test signature — `_quote()` no longer runs on this path, so a `Price` row is never consulted here. Delete `test_a_model_with_no_price_is_refused_before_spending` entirely — its premise (refuse before spending because no price is configured) cannot happen anymore, since this surface never spends the site's own money.

In `test_a_successful_run_writes_exactly_two_ledger_rows`, rename it and drop the ledger-row assertions (no rows are written now — only `Job`):

```python
async def test_a_successful_run_writes_no_ledger_rows_only_a_job(
    client, session, key_run, llm
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
    assert rows == []

    job = (await session.execute(
        select(m.Job).where(m.Job.user_id == key_run.user.id)
    )).scalars().one()
    assert job.kind == "notes" and job.status == "done"
    assert job.cost_tokens == 460
```

Remove the `priced` parameter (and the now-dead `monkeypatch`/`_bypass_model_pass_gate` calls) from `test_a_failed_provider_call_bills_nothing`, `test_the_providers_own_error_text_never_reaches_the_caller`, `test_the_optimizer_runs_exactly_two_passes`, and `test_input_at_the_cap_is_allowed` — they keep their existing bodies otherwise (they already use `key_run`, which now carries a key by construction).

Run the full file, then the full suite:

```bash
.venv/bin/python -m pytest tests/test_skills.py -q
.venv/bin/python -m pytest tests -q 2>&1 | tail -60
```
Expected: every test in `test_skills.py` PASSES; the only other files that might need a look are `tests/test_plans.py` (if it enumerated `lint_model_passes` anywhere — grep it) and `tests/test_gateway.py` (unaffected — that surface's `_check_plan`-equivalent is `gateway.check_quota`, which never touched `lint_model_passes`; confirm with the grep, don't assume).

```bash
grep -rn "lint_model_passes" api/ --include="*.py"
```
Expected after this task: no hits anywhere in `api/` except historical comments explaining its removal, if any were added.

- [ ] **Step 5: Commit**

```bash
git add api/explorer_api/routes/skills.py api/explorer_api/plans.py api/tests/test_skills.py
git commit -m "feat(api): hosted skills require a stored Anthropic key, not a plan quota"
```

---

### Task 6: The spoke doc

**Files:**
- Modify: `docs/site/components/15-accounts-and-billing.md`

- [ ] **Step 1: No test — documentation only**

- [ ] **Step 2: Edit the doc**

In the §5 table (already collapsed to one column by the donations plan), find the row:

```markdown
| Lint model passes P4/P8/P12 (01) | — | — |
```

Replace with:

```markdown
| Lint model passes P4/P8/P12 (01) | requires your own Anthropic API key (account settings) | — |
```

- [ ] **Step 3: Verify by reading the diff**

```bash
git diff docs/site/components/15-accounts-and-billing.md
```
Expected: exactly the one row changed.

- [ ] **Step 4: N/A**

- [ ] **Step 5: Commit**

```bash
git add docs/site/components/15-accounts-and-billing.md
git commit -m "docs(site): 15-accounts-and-billing reflects BYOK for model passes"
```

---

### Task 7: Site — an Anthropic key field on `account.astro`

**Files:**
- Modify: `site/src/pages/account.astro`

- [ ] **Step 1: Read the current file before writing anything**

```bash
cat site/src/pages/account.astro
```
Find the existing pattern this page uses for an island-fetch form (it almost certainly already has one, e.g. for display name or the OAuth-provider list) — match that pattern exactly rather than inventing a new fetch/error-handling convention. Do not guess its structure from this plan; read it.

- [ ] **Step 2: No automated test** — this is a static-site island with no `site/tests` fixture that inspects form behavior for the existing account page sections either (confirm with `grep -n "account" site/tests/test_account_pages.py`); this task's own verification is the manual browser check in Step 4.

- [ ] **Step 3: Add the section**

Add a section (placed after whatever the page's last existing account-settings section is) that:
- Shows "No Anthropic key stored" or "Key ending in …`{hint}`" based on a `GET` that returns whether one is set (if `account.astro`'s existing pattern already fetches an account-summary endpoint on load, extend that response's shape rather than adding a second fetch — read `routes/auth.py`'s or wherever `/api/account` (or equivalent) is served from first, via `grep -rn "current_user" api/explorer_api/routes/*.py` to find the right existing endpoint to extend, and add `anthropic_key_hint: str | None` to its response model rather than creating a new GET route this plan didn't design).
- A text input + Save button that `PUT`s to `/api/donate/checkout`'s sibling, `/api/account/anthropic-key`, with `{"api_key": <value>}`, `credentials: "include"`.
- A Remove button that `DELETE`s the same path, when a key is currently stored.
- On a 422 from Save, show the response's `detail` field as an inline error (matching whatever error-display convention the page's existing forms use).

Since this step depends on reading the actual current file (Step 1), the exact HTML/script is not prescribed here — follow the page's own existing conventions for island scripts, error elements, and styling, the same way Plan 1's `donate.astro` followed `billing.astro`'s existing conventions rather than inventing new ones.

- [ ] **Step 4: Manual verification**

```bash
cd site && npm run build 2>&1 | tail -15
```
Expected: build succeeds, no broken links (`test_internal_links_resolve` still passes: `hub/.venv/bin/python -m pytest site/tests -q` from repo root).

Then, with the API running locally (`set -a && . api/.env && set +a && api/.venv/bin/python -m uvicorn explorer_api.main:app --reload --port 8790` from `api/`) and the site dev server pointed at it, sign in, paste a real (or throwaway) Anthropic key, confirm Save shows the hint and Remove clears it. This step cannot be scripted — say explicitly in your task report that this was checked in a browser, not merely built.

- [ ] **Step 5: Commit**

```bash
git add site/src/pages/account.astro
git commit -m "feat(site): account settings gains an Anthropic API key field"
```

---

## Self-review notes (already applied above)

- **Spec coverage:** §1 encryption (Task 1), §2 data model (Task 2), §3 save/validate/clear (Tasks 3-4), §4 the gate (Task 5), §5 per-caller client (Task 5), §6 billing/ledger (Task 5), §7 out-of-scope items — untouched by any task, correctly. §8 testing — covered across Tasks 1-5's own test steps.
- **Deviation flagged up front:** `anthropic_key_encryption_secret` is optional, not required-at-startup, correcting the spec's literal wording against the codebase's own established convention for the sibling `anthropic_api_key` setting (discovered reading `settings.py` at plan-writing time, not assumed).
- **Type/name consistency checked:** `anthropic_keys.save()`'s signature (`session, user, api_key, settings, *, validate=`) is called identically in Task 3's own tests and Task 4's route. `MissingApiKey`'s `code = "missing_api_key"` matches Task 5's own test assertion. `get_llm_client_factory` is the one and only name used for the new dependency across Task 5's production code and test fixture — the old `get_llm_client` name is fully retired, not left as a dangling alias.
