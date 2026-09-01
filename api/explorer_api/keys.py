"""Scoped API keys — minted once, stored as an Argon2id hash, looked up by prefix.

Authority: component 13 §7 (`api_keys(id, user_id, prefix, hash, scopes[], created,
last_used, revoked)`), component 15 §2 (the three scopes and "shown once") and §10
("keys hashed (argon2), prefix-searchable, scoped, revocable").

The shape of a key, and why:

    llmsx_<prefix>_<secret>
    ^^^^^ ^^^^^^^^ ^^^^^^^^
      |      |         └── 256 bits from `secrets`; only its Argon2id hash is stored
      |      └──────────── 48 bits, stored in the clear and indexed: the lookup half
      └─────────────────── a fixed label, so a leaked key is greppable in a log scan

Splitting the key in two is what keeps authentication to *one* indexed row read
plus *one* Argon2 verify. A single-part key would force either a scan over every
stored hash (unusable) or a fast unsalted digest (a rainbow table waiting to
happen). The prefix is deliberately non-secret — it is what `/api/keys` shows so a
user can tell two keys apart, and what an incident report can name without
printing a credential.

Two properties this module is responsible for, both asserted in `tests/test_keys.py`:

* **The plaintext is never recoverable.** It is returned exactly once, from
  :func:`create`, and after that only its hash exists. Nothing here logs it,
  stores it, or puts it in an exception.
* **A failed authentication costs the attacker the same either way.** An unknown
  prefix burns a verify against a dummy hash, so response time does not reveal
  whether a prefix exists.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import os
import re
import secrets
from collections.abc import Iterable, Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from argon2 import PasswordHasher, Type
from argon2.exceptions import Argon2Error, InvalidHashError
from sqlalchemy import select, update
from sqlalchemy.orm.attributes import set_committed_value

from .models import KEY_SCOPES, ApiKey, User

log = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.ext.asyncio import AsyncSession

# --- the wire format ---------------------------------------------------------

#: The label every key starts with. The step-3 plan (Task 4) fixes it as
#: `llmsx_…`; component 15 §2 still writes the older `lx_…` in prose. The plan
#: wins — it is the later document and the CLI is named `llmsx`.
KEY_LABEL = "llmsx"

PREFIX_BYTES = 6                       # → 12 hex characters, 48 bits
SECRET_BYTES = 32                      # → 43 url-safe characters, 256 bits
SECRET_MIN_LEN = 32
#: A hard ceiling before anything reaches Argon2: hashing is deliberately
#: expensive, so an unbounded input is a free denial-of-service.
SECRET_MAX_LEN = 256

#: The JSON field that carries the plaintext on the one response that has it.
#: Named here so a test can assert no *column* is called this.
PLAINTEXT_FIELD = "key"

_PREFIX_RE = re.compile(rf"\A[0-9a-f]{{{PREFIX_BYTES * 2}}}\Z")

#: How many times :func:`create` retries a prefix collision before giving up.
#: At 48 bits a collision is astronomically unlikely; the retry exists so that
#: if one ever happens it is a re-roll, not a 500.
PREFIX_ATTEMPTS = 5


# --- hashing -----------------------------------------------------------------

#: RFC 9106's second recommended profile (64 MiB, t=3, p=4). Argon2id — the
#: hybrid — because a key both sits in a database that could leak (wants memory
#: hardness) and is verified on a hot path (wants side-channel resistance).
HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)

_DUMMY_HASH: str | None = None

#: How many Argon2 verifies may be in flight at once, across the whole process.
#: The profile above costs 64 MiB *each*, so without a ceiling the peak memory
#: of this service is set by the number of open connections — an unauthenticated
#: client sending N concurrent bad keys pins N × 64 MiB. Four is the default
#: because it matches `parallelism` and keeps the worst case at 256 MiB.
ARGON2_CONCURRENCY = max(1, int(os.environ.get("EXPLORER_ARGON2_CONCURRENCY", "4")))
_hash_gate = asyncio.Semaphore(ARGON2_CONCURRENCY)

#: How stale ``last_used_at`` is allowed to get before a successful
#: authentication refreshes it. Every write is one row lock, and the request
#: that took it may then sit in a 30-minute upstream call, so writing on *every*
#: authentication serialised every concurrent call made with the same key.
TOUCH_INTERVAL = dt.timedelta(seconds=60)


async def _verify(stored: str, secret: str) -> bool:
    """One bounded, off-loop Argon2 verify."""
    async with _hash_gate:
        try:
            return bool(await asyncio.to_thread(HASHER.verify, stored, secret))
        except (Argon2Error, InvalidHashError):
            return False


async def _burn() -> None:
    """Spend the same work a real verify would, and discard the answer.

    Without this, "no such prefix" returns in microseconds while "wrong secret"
    takes ~50 ms, which is a free oracle for enumerating live prefixes.
    """
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(SECRET_BYTES))
    await _verify(_DUMMY_HASH, "")


# --- scopes ------------------------------------------------------------------


class InvalidScopes(ValueError):
    """Raised when the requested scopes are empty, duplicated or unknown."""


def normalise_scopes(scopes: Iterable[str]) -> list[str]:
    """Validate and put scopes in the canonical 15 §2 order.

    Canonical order makes two keys with the same powers compare equal, so the
    gateway's policy table (Task 7) can match on the list without sorting first.
    """
    given = list(scopes)
    if not given:
        raise InvalidScopes("a key needs at least one scope")
    unknown = [s for s in given if s not in KEY_SCOPES]
    if unknown:
        raise InvalidScopes(
            f"unknown scope(s) {', '.join(sorted(set(unknown)))}; "
            f"allowed: {', '.join(KEY_SCOPES)}"
        )
    if len(set(given)) != len(given):
        raise InvalidScopes("scopes must not repeat")
    return [scope for scope in KEY_SCOPES if scope in set(given)]


# --- parsing -----------------------------------------------------------------


def parse(raw: object) -> tuple[str, str] | None:
    """``llmsx_<prefix>_<secret>`` → ``(prefix, secret)``, or ``None``.

    Everything that is not exactly the expected shape is ``None`` — never an
    exception, because this runs on unauthenticated input on every request.
    """
    if not isinstance(raw, str):
        return None
    # `maxsplit=2` so a url-safe secret containing `_` survives intact.
    parts = raw.split("_", 2)
    if len(parts) != 3:
        return None
    label, prefix, secret = parts
    if label != KEY_LABEL or not _PREFIX_RE.match(prefix):
        return None
    if not (SECRET_MIN_LEN <= len(secret) <= SECRET_MAX_LEN):
        return None
    return prefix, secret


def format_key(prefix: str, secret: str) -> str:
    return f"{KEY_LABEL}_{prefix}_{secret}"


# --- create / authenticate / revoke -----------------------------------------


async def create(
    session: AsyncSession,
    user: User,
    scopes: Iterable[str],
    *,
    name: str | None = None,
    max_usd_day: Decimal | None = None,
) -> tuple[str, ApiKey]:
    """Mint a key. Returns ``(plaintext, row)`` — the only time the plaintext exists.

    The caller must hand the plaintext straight to the user and then drop it.
    `max_usd_day` is 15 §10's per-key spend cap; it is stored here and enforced
    by the ledger (Task 5).
    """
    resolved = normalise_scopes(scopes)
    prefix = await _free_prefix(session)
    secret = secrets.token_urlsafe(SECRET_BYTES)
    row = ApiKey(
        user_id=user.id,
        name=name,
        prefix=prefix,
        hash=HASHER.hash(secret),
        scopes=resolved,
        max_usd_day=max_usd_day,
    )
    session.add(row)
    await session.flush()
    return format_key(prefix, secret), row


async def _free_prefix(session: AsyncSession) -> str:
    for _ in range(PREFIX_ATTEMPTS):
        candidate = secrets.token_hex(PREFIX_BYTES)
        taken = await session.scalar(select(ApiKey.id).where(ApiKey.prefix == candidate))
        if taken is None:
            return candidate
    raise RuntimeError(
        f"could not find a free key prefix in {PREFIX_ATTEMPTS} attempts; "
        "PREFIX_BYTES is too small for the number of keys issued"
    )


async def authenticate(session: AsyncSession, raw: object) -> ApiKey | None:
    """Resolve a presented key to its live row, or ``None``.

    ``None`` covers every failure mode on purpose — malformed, unknown prefix,
    wrong secret, revoked, or belonging to a deleted account — so a caller
    cannot accidentally branch on *why* and leak the difference.
    """
    parsed = parse(raw)
    if parsed is None:
        return None
    prefix, secret = parsed

    row = await session.scalar(
        select(ApiKey)
        .join(User, User.id == ApiKey.user_id)
        .where(
            ApiKey.prefix == prefix,
            ApiKey.revoked_at.is_(None),
            User.deleted_at.is_(None),
        )
    )
    if row is None:
        await _burn()
        return None

    if not await _verify(row.hash, secret):
        return None

    # Parameters can be raised later without invalidating keys already issued:
    # the next successful use re-hashes at the current cost.
    if HASHER.check_needs_rehash(row.hash):
        row.hash = HASHER.hash(secret)

    await _touch(session, row)
    return row


async def _touch(session: AsyncSession, row: ApiKey) -> None:
    """Refresh ``last_used_at`` **outside** the caller's transaction.

    Writing it through ``session`` took a row lock on ``api_keys`` that was held
    until the request committed — and the request that just authenticated may be
    about to spend thirty minutes inside ``hub_index_docset``. Every other call
    made with the same key blocked behind it for the whole of that, holding a
    pool connection each, with no log line and no timeout of its own. So the
    stamp goes out on its own short-lived connection, is coalesced to
    :data:`TOUCH_INTERVAL`, and can never fail an authentication.
    """
    now = dt.datetime.now(dt.UTC)
    previous = row.last_used_at
    if previous is not None and now - previous < TOUCH_INTERVAL:
        return
    engine = getattr(session, "bind", None)
    if engine is None or not hasattr(engine, "connect"):  # pragma: no cover
        row.last_used_at = now
        await session.flush()
        return
    try:
        async with engine.connect() as connection:
            done = await connection.execute(
                update(ApiKey).where(ApiKey.id == row.id).values(last_used_at=now)
            )
            await connection.commit()
    except Exception as exc:  # noqa: BLE001 - a stamp must never fail a request
        log.warning("could not stamp last_used_at on key %s", row.prefix, exc_info=exc)
        return
    if not done.rowcount:
        # The row is not committed yet (a caller that minted the key in the same
        # still-open transaction). Nothing to reflect.
        return
    # Reflect what the other connection wrote *without* marking the attribute
    # dirty: a plain assignment would have the caller's transaction re-emit the
    # UPDATE on its next flush, reinstating the lock this function exists to avoid.
    set_committed_value(row, "last_used_at", now)


async def list_for_user(session: AsyncSession, user: User) -> Sequence[ApiKey]:
    """Every key this user owns, revoked ones included — newest first.

    Revoked keys stay listed so an owner can see when a key was retired; the
    row carries no secret, so showing it costs nothing.
    """
    result = await session.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user.id)
        .order_by(ApiKey.created_at.desc(), ApiKey.id.desc())
    )
    return result.scalars().all()


async def get_for_user(session: AsyncSession, user: User, key_id: str) -> ApiKey | None:
    """One of *this user's* keys. Another user's id resolves to ``None``."""
    return await session.scalar(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )


async def revoke(session: AsyncSession, user: User, key_id: str) -> ApiKey | None:
    """Retire a key. ``None`` when it is not this user's, or already revoked.

    Revocation is a stamp, not a delete: the ledger rows that reference the key
    must keep something to point at.
    """
    row = await get_for_user(session, user, key_id)
    if row is None or row.revoked_at is not None:
        return None
    row.revoked_at = dt.datetime.now(dt.UTC)
    await session.flush()
    return row


# --- serialisation -----------------------------------------------------------


def public_view(row: ApiKey) -> dict[str, Any]:
    """The safe projection of a key. Deliberately built field by field.

    An allow-list, never `row.__dict__` minus something: a column added later
    (another hash, a recovery token) then has to be added here on purpose
    before it can ever reach a response.
    """
    return {
        "id": row.id,
        "name": row.name,
        "prefix": row.prefix,
        "scopes": list(row.scopes),
        "max_usd_day": row.max_usd_day,
        "created_at": row.created_at,
        "last_used_at": row.last_used_at,
        "revoked_at": row.revoked_at,
    }


__all__ = [
    "HASHER",
    "KEY_LABEL",
    "PLAINTEXT_FIELD",
    "PREFIX_BYTES",
    "SECRET_BYTES",
    "ApiKey",
    "InvalidScopes",
    "authenticate",
    "create",
    "format_key",
    "get_for_user",
    "list_for_user",
    "normalise_scopes",
    "parse",
    "public_view",
    "revoke",
]
