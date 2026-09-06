"""`/api/donate` — a Stripe Checkout session for a one-time or monthly donation.

Thin, like every route module: `explorer_api.billing` owns the money rule
(build the inline price, record the `Donation` row), this file owns who may
call it and what a bad amount looks like over HTTP. Unlike the old
plan-checkout route, no sign-in is required — `user` is `optional_user`, so an
anonymous visitor can donate and a signed-in one gets the donation attached to
their account.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from .. import billing, models as m
from ..db import get_session
from ..settings import Settings
from .auth import optional_user

router = APIRouter(prefix="/api/donate", tags=["donate"])

OptionalUser = Annotated[m.User | None, Depends(optional_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def get_gateway(request: Request) -> billing.StripeGateway:
    """The Stripe client, built once per process and cached on the app.

    A dependency rather than a module global so a test can override it with a
    double and never open a socket. `routes.billing` imports this rather than
    defining its own, so the process holds one Stripe client, not two.
    """
    gateway = getattr(request.app.state, "stripe_gateway", None)
    if gateway is None:
        settings = _settings(request)
        gateway = billing.LiveStripe(settings.stripe_secret_key.get_secret_value())
        request.app.state.stripe_gateway = gateway
    return gateway


Gateway = Annotated[billing.StripeGateway, Depends(get_gateway)]


class CheckoutIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_usd: Decimal
    interval: str

    @field_validator("amount_usd")
    @classmethod
    def _positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount_usd must be positive")
        return value

    @field_validator("interval")
    @classmethod
    def _known_interval(cls, value: str) -> str:
        if value not in billing.DONATION_INTERVALS:
            raise ValueError(f"interval must be one of {billing.DONATION_INTERVALS}")
        return value


class CheckoutOut(BaseModel):
    url: str
    session_id: str


@router.post("/checkout", response_model=CheckoutOut, summary="Start a donation Checkout session")
async def start_checkout(
    body: CheckoutIn, user: OptionalUser, session: DbSession, gateway: Gateway,
) -> CheckoutOut:
    try:
        checkout = await billing.create_donation_checkout(
            session, gateway,
            amount_usd=body.amount_usd, interval=body.interval, user=user,
            success_url=billing.CHECKOUT_SUCCESS_URL,
            cancel_url=billing.CHECKOUT_CANCEL_URL,
        )
    except billing.InvalidDonationAmount as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    return CheckoutOut(url=checkout.url, session_id=checkout.id)


__all__ = ["CheckoutIn", "CheckoutOut", "get_gateway", "router"]
