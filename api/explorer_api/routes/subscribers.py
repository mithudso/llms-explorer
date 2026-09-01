"""`/api/subscribers` — opt in to blog change notices, confirm, unsubscribe.

Public by design: no session, no API key — anyone reading the blog can sign up.
Double opt-in, three steps:

* ``POST /api/subscribers`` stores the address unconfirmed and mails a confirm
  link. The response never says whether the address was already on the list —
  the same enumeration concern ``keys.py`` names for key ids applies here to
  addresses.
* ``GET /api/subscribers/confirm`` flips ``confirmed_at``; only confirmed rows
  are ever mailed a notice (``notify.notify_new_post``).
* ``GET /api/subscribers/unsubscribe`` flips ``unsubscribed_at``, from the
  token mailed with every notice. Re-subscribing the same address afterwards
  mints a fresh confirm token rather than silently reviving the old one.
"""

from __future__ import annotations

import re
import secrets
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from .. import notify
from ..db import get_session
from ..models import Subscriber
from ..settings import Settings

router = APIRouter(prefix="/api/subscribers", tags=["subscribers"])

Session = Annotated[AsyncSession, Depends(get_session)]

#: Deliberately loose — this is "reject obvious garbage before a mail attempt",
#: not RFC 5322 validation; the confirm-link round trip is the real check.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_EMAIL_LEN = 254


def _settings(request: Request) -> Settings:
    return request.app.state.settings


class SubscribeIn(BaseModel):
    """`POST /api/subscribers` body."""

    model_config = ConfigDict(extra="forbid")

    email: str

    @field_validator("email")
    @classmethod
    def _looks_like_an_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not value or len(value) > MAX_EMAIL_LEN or not _EMAIL_RE.match(value):
            raise ValueError("not a valid email address")
        return value


class StatusOut(BaseModel):
    status: str


@router.post(
    "",
    response_model=StatusOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Opt in to blog change notices (mails a confirm link)",
)
async def subscribe(
    body: SubscribeIn, session: Session, background: BackgroundTasks, settings: Annotated[Settings, Depends(_settings)]
) -> StatusOut:
    row = (
        await session.execute(select(Subscriber).where(Subscriber.email == body.email))
    ).scalar_one_or_none()
    if row is None:
        row = Subscriber(
            email=body.email,
            confirm_token=secrets.token_urlsafe(24),
            unsubscribe_token=secrets.token_urlsafe(24),
        )
        session.add(row)
        await session.flush()
    elif row.unsubscribed_at is not None:
        row.unsubscribed_at = None
        row.confirmed_at = None
        row.confirm_token = secrets.token_urlsafe(24)

    if row.confirmed_at is None:
        confirm_url = (
            f"{settings.api_public_url}/api/subscribers/confirm?token={row.confirm_token}"
        )
        background.add_task(
            notify.send_email,
            row.email,
            "Confirm your subscription",
            f"Confirm your subscription to blog change notices: {confirm_url}",
            settings,
        )
    await session.commit()
    return StatusOut(status="ok")


@router.get(
    "/confirm",
    response_model=StatusOut,
    summary="Confirm a subscription from the mailed link",
)
async def confirm(token: str, session: Session) -> StatusOut:
    result = await session.execute(
        update(Subscriber)
        .where(Subscriber.confirm_token == token, Subscriber.confirmed_at.is_(None))
        .values(confirmed_at=func.now())
    )
    await session.commit()
    # A stale, already-used or unknown token gets the same answer as success:
    # confirming twice is idempotent, and the alternative (a 404) would let a
    # token be brute-forced by distinguishing "wrong" from "already redeemed".
    del result
    return StatusOut(status="confirmed")


@router.get(
    "/unsubscribe",
    response_model=StatusOut,
    summary="Unsubscribe from the mailed link",
)
async def unsubscribe(token: str, session: Session) -> StatusOut:
    await session.execute(
        update(Subscriber)
        .where(Subscriber.unsubscribe_token == token, Subscriber.unsubscribed_at.is_(None))
        .values(unsubscribed_at=func.now())
    )
    await session.commit()
    return StatusOut(status="unsubscribed")


__all__ = ["StatusOut", "SubscribeIn", "router"]
