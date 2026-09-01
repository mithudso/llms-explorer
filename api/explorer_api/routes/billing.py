"""`/api/billing` — Checkout, the Customer Portal, the price table, the webhook.

Thin by design: every rule about money lives in `explorer_api.billing`, every
number lives in `explorer_api.plans`. What is decided *here* is who may call
what, and what each refusal looks like:

* **The webhook takes no session and no key.** It authenticates by signature
  alone (`explorer_api.billing.verify_event`), because Stripe is the only caller
  and it has no cookie. A failed verification is a 400 with nothing written.
* **A 2xx is Stripe's "stop retrying".** So a duplicate and an event we do not
  act on both answer 200 with a `status` saying which; only a signature failure
  and a genuine server fault are non-2xx.
* **Every other route is account-only.** The customer id is read from a row that
  belongs to the signed-in user, never from the request, so no parameter can
  point this service at somebody else's billing.

Money leaves as a **string** at six decimal places, exactly as `/api/usage`
does: JSON numbers are IEEE doubles and a price rendered by a double is the
float bug the ledger exists to avoid.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, field_serializer
from sqlalchemy.ext.asyncio import AsyncSession

from .. import billing, ledger, models as m, plans
from ..db import get_session
from ..settings import Settings
from .auth import current_user

router = APIRouter(prefix="/api/billing", tags=["billing"])

PlanId = Literal["free", "starter", "pro"]

CurrentUser = Annotated[m.User, Depends(current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def get_gateway(request: Request) -> billing.StripeGateway:
    """The Stripe client, built once per process and cached on the app.

    A dependency rather than a module global so a test can override it with a
    double and never open a socket.
    """
    gateway = getattr(request.app.state, "stripe_gateway", None)
    if gateway is None:
        settings = _settings(request)
        gateway = billing.LiveStripe(settings.stripe_secret_key.get_secret_value())
        request.app.state.stripe_gateway = gateway
    return gateway


Gateway = Annotated[billing.StripeGateway, Depends(get_gateway)]


# --- responses ---------------------------------------------------------------


class MoneyModel(BaseModel):
    """Base for responses carrying money: every `Decimal` leaves as a string."""

    @field_serializer("*", when_used="json", check_fields=False)
    def _money_as_string(self, value: object) -> object:
        return str(ledger.money(value)) if isinstance(value, Decimal) else value


class PlanOut(MoneyModel):
    id: str
    name: str
    price_usd: Decimal
    included_credit_usd: Decimal
    quotas: dict[str, Any]


class CheckoutOut(BaseModel):
    url: str
    session_id: str


class PortalOut(BaseModel):
    url: str


class WebhookOut(BaseModel):
    received: bool
    status: str
    detail: str | None = None


class CheckoutIn(BaseModel):
    """`POST /api/billing/checkout` body. An unknown plan is a 422, not a guess."""

    model_config = ConfigDict(extra="forbid")

    plan: PlanId


# --- routes ------------------------------------------------------------------


@router.get("/plans", response_model=list[PlanOut], summary="Public price table")
async def list_plans() -> list[PlanOut]:
    """15 §5's price table, straight from `plans.PLANS`. No sign-in needed."""
    return [
        PlanOut(id=plan.id, name=plan.name, price_usd=plan.price_usd,
                included_credit_usd=plan.included_credit_usd, quotas=dict(plan.quotas))
        for plan in plans.PLANS.values()
    ]


@router.post("/checkout", response_model=CheckoutOut, summary="Start a Checkout session")
async def start_checkout(
    body: CheckoutIn, user: CurrentUser, session: DbSession, gateway: Gateway
) -> CheckoutOut:
    try:
        checkout = await billing.start_checkout(session, user, body.plan, gateway)
    except billing.PlanNotPurchasable as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except billing.PlanNotSellable as exc:
        # Configuration, not the caller's fault: 503 says "come back later"
        # rather than blaming a request that was perfectly valid.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "this plan is not available for purchase yet") from exc
    return CheckoutOut(url=checkout.url, session_id=checkout.id)


@router.get("/portal", response_model=PortalOut, summary="Open the Customer Portal")
async def open_portal(user: CurrentUser, session: DbSession, gateway: Gateway) -> PortalOut:
    try:
        url = await billing.open_portal(session, user, gateway)
    except billing.NoCustomer as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "no billing account yet — subscribe to a plan first",
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


__all__ = ["CheckoutIn", "CheckoutOut", "PlanOut", "PortalOut", "WebhookOut",
           "get_gateway", "router"]
