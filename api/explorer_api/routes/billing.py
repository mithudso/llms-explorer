"""`/api/billing` — the Customer Portal and the Stripe webhook.

Thin by design: every rule about money lives in `explorer_api.billing`. What
is decided here is who may call what, and what each refusal looks like:

* **The webhook takes no session and no key.** It authenticates by signature
  alone (`explorer_api.billing.verify_event`), because Stripe is the only
  caller and it has no cookie. A failed verification is a 400 with nothing
  written.
* **A 2xx is Stripe's "stop retrying".** So a duplicate and an event we do not
  act on both answer 200 with a `status` saying which; only a signature
  failure and a genuine server fault are non-2xx.
* **The Portal is account-only.** The customer id is read from a row that
  belongs to the signed-in user, never from the request.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .. import billing, models as m
from ..db import get_session
from ..settings import Settings
from .auth import current_user
from .donate import Gateway, get_gateway

router = APIRouter(prefix="/api/billing", tags=["billing"])

CurrentUser = Annotated[m.User, Depends(current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def _settings(request: Request) -> Settings:
    return request.app.state.settings


class PortalOut(BaseModel):
    url: str


class WebhookOut(BaseModel):
    received: bool
    status: str
    detail: str | None = None


@router.get("/portal", response_model=PortalOut, summary="Open the Customer Portal")
async def open_portal(user: CurrentUser, session: DbSession, gateway: Gateway) -> PortalOut:
    try:
        url = await billing.open_portal(session, user, gateway)
    except billing.NoCustomer as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "no billing account yet — donate once to open a portal",
        ) from exc
    return PortalOut(url=url)


@router.post("/webhook", response_model=WebhookOut, summary="Stripe events (Stripe only)")
async def webhook(request: Request, session: DbSession) -> WebhookOut:
    """Verify, then apply exactly once. Nothing is written before verification."""
    payload = await request.body()
    settings = _settings(request)
    try:
        event = billing.verify_event(
            payload,
            request.headers.get("stripe-signature"),
            secret=settings.stripe_webhook_secret.get_secret_value(),
        )
    except billing.SignatureInvalid as exc:
        # Deliberately terse: the reason goes to our logs, not to whoever sent
        # this, so a forger learns nothing about why their attempt failed.
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "signature verification failed") from exc
    outcome = await billing.handle_event(session, event)
    await session.commit()
    return WebhookOut(received=True, status=outcome.status, detail=outcome.detail)


__all__ = ["PortalOut", "WebhookOut", "get_gateway", "router"]
