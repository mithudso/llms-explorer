"""`/api/keys` — list, create, revoke (component 15 §5).

Thin by design: request shape and authorisation live here, every rule about what
a key *is* lives in `explorer_api.keys`.

Two choices worth stating, because both are security decisions rather than
style:

* **The plaintext appears in exactly one response** — the 201 from `POST`. The
  list response is built by `keys.public_view`, an allow-list that has no field
  for it, so no later column can leak into a listing by accident.
* **Another user's key id is a 404, not a 403.** A 403 would confirm that the id
  exists, turning `DELETE /api/keys/<id>` into an enumeration oracle over every
  key on the service.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .. import keys as keys_module
from ..db import get_session
from ..models import KEY_SCOPES, User
# The one session dependency. There is deliberately no second definition here:
# the local one this replaces read `request.state.user`, which *nothing* in the
# codebase ever set, so every `/api/keys` request 401'd once the router was
# actually mounted — while its docstring asserted a session mechanism that did
# not exist. `billing.py`, `trees.py` and `proposals.py` already import this one.
from .auth import current_user

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/keys", tags=["keys"])

Scope = Literal["read", "run", "publish"]

MAX_NAME_LEN = 64


CurrentUser = Annotated[User, Depends(current_user)]
Session = Annotated["AsyncSession", Depends(get_session)]


class KeyCreate(BaseModel):
    """`POST /api/keys` body."""

    model_config = ConfigDict(extra="forbid")

    #: `min_length=1` is 15 §2's rule that a key always carries some power; the
    #: `Literal` is what turns an unknown scope into a 422 rather than a row the
    #: gateway would later have to interpret.
    scopes: list[Scope] = Field(min_length=1)
    name: str | None = Field(default=None, max_length=MAX_NAME_LEN)
    #: 15 §10's per-key spend cap. `Decimal`, never float — money always is.
    max_usd_day: Decimal | None = Field(default=None, ge=0)

    @field_validator("scopes")
    @classmethod
    def _no_repeats(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("scopes must not repeat")
        # Canonical order, so two keys with the same powers look the same.
        return [scope for scope in KEY_SCOPES if scope in set(value)]

    @field_validator("name")
    @classmethod
    def _blank_name_is_no_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class KeyPublic(BaseModel):
    """A key as anyone may see it — no secret material, ever."""

    id: str
    name: str | None
    prefix: str
    scopes: list[str]
    max_usd_day: Decimal | None
    created_at: dt.datetime
    last_used_at: dt.datetime | None
    revoked_at: dt.datetime | None


class KeyCreated(KeyPublic):
    """The one response that carries the plaintext. It is never stored or logged."""

    key: str


@router.get("", response_model=list[KeyPublic], summary="List this account's keys")
async def list_keys(user: CurrentUser, session: Session) -> list[KeyPublic]:
    rows = await keys_module.list_for_user(session, user)
    return [KeyPublic(**keys_module.public_view(row)) for row in rows]


@router.post(
    "",
    response_model=KeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create a key (the plaintext is shown once, here, and never again)",
)
async def create_key(body: KeyCreate, user: CurrentUser, session: Session) -> KeyCreated:
    try:
        plaintext, row = await keys_module.create(
            session,
            user,
            body.scopes,
            name=body.name,
            max_usd_day=body.max_usd_day,
        )
    except keys_module.InvalidScopes as exc:
        # Unreachable through the model above; kept so a future caller that
        # bypasses the schema still gets a 422 rather than a 500.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    await session.commit()
    return KeyCreated(**keys_module.public_view(row), key=plaintext)


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a key",
)
async def revoke_key(key_id: str, user: CurrentUser, session: Session) -> None:
    row = await keys_module.revoke(session, user, key_id)
    if row is None:
        # Covers "not yours", "no such key" and "already revoked" with one
        # answer, so none of the three can be told apart from outside.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such key")
    await session.commit()


__all__ = ["KeyCreate", "KeyCreated", "KeyPublic", "current_user", "router"]
