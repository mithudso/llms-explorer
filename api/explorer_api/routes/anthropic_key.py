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
