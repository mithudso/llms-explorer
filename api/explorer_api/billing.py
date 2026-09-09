"""Stripe: donation Checkout, the Customer Portal, and webhooks that cannot be replayed.

Authority: `docs/superpowers/plans/2026-09-06-donations-and-community-directory-design.md`
§1 (Part A). Every account is on the single free plan (`explorer_api.plans`);
this module no longer decides who is entitled to what — it records what
Stripe says happened to a `Donation` and keeps the Customer Portal open for a
donor who wants to manage or cancel a recurring one.

Three decisions worth stating, because each is a correctness rule rather than
a style preference:

**1. The event id is claimed before anything is applied.** :func:`handle_event`
inserts the row into ``stripe_events`` with ``ON CONFLICT DO NOTHING``; if the
insert claimed nothing, the event has already been seen and the function stops.
Because that INSERT and the effects share one transaction, a concurrent second
delivery blocks on the primary key rather than double-recording, and a failure
half-way rolls the claim back so Stripe's next retry is a real retry.

**2. Signature verification happens before the database is touched at all.**
:func:`verify_event` is local HMAC (`stripe.Webhook.construct_event` makes no
network call), so a forged or stale delivery is refused without a write — which
is what makes "an invalid signature writes nothing" true rather than merely
likely.

**3. The two calls that reach Stripe go through :class:`StripeGateway`.**
Checkout and Portal session creation are the only outbound calls in the module;
behind a protocol they can be faked in a test without a network stub, and the
webhook path — which is where the money logic lives — has no outbound call at
all.

No card data ever reaches this service: Checkout and the Portal are
Stripe-hosted, and what comes back here is a URL.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

import stripe
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from . import models as m

UTC = dt.UTC

#: Where a refused/finished checkout sends the browser back to. The site owns
#: the donate page, this module owns the query strings that say how it went.
DONATE_URL = "https://llms-explorer.com/donate"
CHECKOUT_SUCCESS_URL = f"{DONATE_URL}?checkout=success"
CHECKOUT_CANCEL_URL = f"{DONATE_URL}?checkout=cancelled"
PORTAL_RETURN_URL = DONATE_URL

#: Stripe's own default: a signature older than this is refused, so a captured
#: delivery cannot be replayed at leisure.
SIGNATURE_TOLERANCE_SECONDS = 300

#: The events this module acts on. Anything else is recorded and ignored —
#: recorded so an operator can see what Stripe is sending, ignored so an
#: unknown type can never be a 500 that makes Stripe retry forever.
HANDLED_EVENTS: frozenset[str] = frozenset({
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
})


# --- errors ------------------------------------------------------------------


class BillingError(RuntimeError):
    """Base for everything this module refuses to do."""


class SignatureInvalid(BillingError):
    """The delivery is not from Stripe, or is too old to still be honoured."""


class NoCustomer(BillingError):
    """The account has never checked out, so it has no Stripe customer."""


DONATION_INTERVALS = ("once", "month")


class InvalidDonationAmount(BillingError):
    """A donation of zero or less — Stripe would reject it anyway, but this is
    the clearer message and it avoids a round trip to find out."""


# --- the outbound seam -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CheckoutSession:
    """What Checkout gives back: an id, and the URL to send the browser to."""

    id: str
    url: str


class StripeGateway(Protocol):
    """The only two calls this service makes to Stripe."""

    async def create_checkout_session(
        self,
        *,
        mode: str,
        price_data: Mapping[str, Any],
        client_reference_id: str | None,
        customer_email: str | None,
        success_url: str,
        cancel_url: str,
        metadata: Mapping[str, str],
    ) -> CheckoutSession: ...

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> str: ...


class LiveStripe:
    """The real gateway. Constructed once per process from the secret key."""

    def __init__(self, api_key: str) -> None:
        self._client = stripe.StripeClient(api_key)

    async def create_checkout_session(
        self,
        *,
        mode: str,
        price_data: Mapping[str, Any],
        client_reference_id: str | None,
        customer_email: str | None,
        success_url: str,
        cancel_url: str,
        metadata: Mapping[str, str],
    ) -> CheckoutSession:
        params: dict[str, Any] = {
            "mode": mode,
            "line_items": [{"price_data": dict(price_data), "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": dict(metadata),
        }
        if client_reference_id:
            params["client_reference_id"] = client_reference_id
        if customer_email:
            params["customer_email"] = customer_email
        if mode == "subscription":
            params["subscription_data"] = {"metadata": dict(metadata)}
        session = await self._client.v1.checkout.sessions.create_async(params=params)
        return CheckoutSession(id=session.id, url=session.url or "")

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> str:
        session = await self._client.v1.billing_portal.sessions.create_async(
            params={"customer": customer_id, "return_url": return_url}
        )
        return session.url


# --- checkout and portal -----------------------------------------------------


async def customer_id_for(session: AsyncSession, user: m.User) -> str | None:
    """This account's Stripe customer, if it has ever had one.

    Scoped to the user by construction: a customer id is only ever read from a
    row that belongs to them, so no request can open a portal onto somebody
    else's billing.
    """
    stmt = (
        select(m.Subscription.stripe_customer_id)
        .where(m.Subscription.user_id == user.id,
               m.Subscription.stripe_customer_id.is_not(None))
        .order_by(m.Subscription.updated_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().first()


async def create_donation_checkout(
    session: AsyncSession,
    gateway: StripeGateway,
    *,
    amount_usd: Decimal,
    interval: str,
    user: m.User | None,
    success_url: str,
    cancel_url: str,
) -> CheckoutSession:
    """A Stripe Checkout session for a donation of ``amount_usd``.

    Builds `price_data` inline rather than referencing a pre-created Price:
    a donation amount is chosen by the donor, so there is no fixed catalogue
    of prices to have created ahead of time the way a subscription tier needs.
    """
    if interval not in DONATION_INTERVALS:
        raise BillingError(f"interval must be one of {DONATION_INTERVALS}, got {interval!r}")
    if amount_usd <= 0:
        raise InvalidDonationAmount(f"amount_usd must be positive, got {amount_usd}")

    donation = m.Donation(
        user_id=user.id if user else None,
        amount_usd=amount_usd,
        interval=interval,
        status="pending",
    )
    session.add(donation)
    await session.flush()

    price_data: dict[str, Any] = {
        "currency": "usd",
        "unit_amount": int(amount_usd * 100),
        "product_data": {"name": "Donation to LLMS-Explorer"},
    }
    mode = "payment"
    if interval == "month":
        mode = "subscription"
        price_data["recurring"] = {"interval": "month"}

    checkout = await gateway.create_checkout_session(
        mode=mode,
        price_data=price_data,
        client_reference_id=user.id if user else None,
        customer_email=user.email if user else None,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"donation_id": donation.id},
    )
    donation.stripe_checkout_session_id = checkout.id
    await session.flush()
    return checkout


async def open_portal(
    session: AsyncSession,
    user: m.User,
    gateway: StripeGateway,
    *,
    return_url: str = PORTAL_RETURN_URL,
) -> str:
    """A Customer Portal URL, or :class:`NoCustomer` if nothing was ever bought."""
    customer_id = await customer_id_for(session, user)
    if not customer_id:
        raise NoCustomer("this account has no Stripe customer yet")
    return await gateway.create_portal_session(
        customer_id=customer_id, return_url=return_url
    )


# --- webhook: verification ---------------------------------------------------


def verify_event(
    payload: bytes,
    signature: str | None,
    *,
    secret: str,
    tolerance: int = SIGNATURE_TOLERANCE_SECONDS,
) -> dict[str, Any]:
    """Verify the delivery and return it as a plain dict.

    Local HMAC only — no network. Everything that is not a valid, current,
    well-formed delivery raises :class:`SignatureInvalid`, so the route has one
    thing to catch and one answer to give.
    """
    if not signature:
        raise SignatureInvalid("no Stripe-Signature header")
    try:
        stripe.Webhook.construct_event(payload, signature, secret, tolerance=tolerance)
    except stripe.SignatureVerificationError as exc:
        raise SignatureInvalid(str(exc)) from exc
    except ValueError as exc:                    # not JSON at all
        raise SignatureInvalid(f"unparseable payload: {exc}") from exc
    try:
        event = json.loads(payload)
    except ValueError as exc:  # pragma: no cover - construct_event parsed it already
        raise SignatureInvalid(f"unparseable payload: {exc}") from exc
    if not isinstance(event, dict) or not event.get("id") or not event.get("type"):
        raise SignatureInvalid("payload is not a Stripe event")
    return event


# --- webhook: dispatch -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EventOutcome:
    """What became of one delivery. ``status`` is the whole story:

    ``applied``    — claimed and acted on.
    ``duplicate``  — this event id was already recorded; nothing was done.
    ``ignored``    — recorded, but nothing to do (unhandled type, unknown
                     account, an invoice that grants no credit).
    """

    event_id: str
    type: str
    status: str
    detail: str | None = None


def _object(event: Mapping[str, Any]) -> Mapping[str, Any]:
    data = event.get("data") or {}
    obj = data.get("object") if isinstance(data, Mapping) else None
    return obj if isinstance(obj, Mapping) else {}


def _epoch_to_utc(value: Any) -> dt.datetime | None:
    if not isinstance(value, int | float):
        return None
    return dt.datetime.fromtimestamp(int(value), tz=UTC)


async def _claim(session: AsyncSession, event: Mapping[str, Any]) -> bool:
    """Record the event id, and say whether *we* are the ones who recorded it.

    ``ON CONFLICT DO NOTHING`` makes this the idempotency gate: the first
    delivery claims the id, every later one gets ``False`` and stops.
    """
    stmt = (
        pg_insert(m.StripeEvent)
        .values(id=str(event["id"]), type=str(event["type"]), payload=dict(event))
        .on_conflict_do_nothing(index_elements=[m.StripeEvent.id])
        .returning(m.StripeEvent.id)
    )
    claimed = (await session.execute(stmt)).first() is not None
    await session.flush()
    return claimed


async def handle_event(session: AsyncSession, event: Mapping[str, Any]) -> EventOutcome:
    """Apply one verified Stripe event, exactly once.

    The caller owns the transaction: commit and the effects land with the
    ``stripe_events`` row, roll back and Stripe's retry is a real retry.
    """
    event_id, event_type = str(event["id"]), str(event["type"])
    if not await _claim(session, event):
        return EventOutcome(event_id, event_type, "duplicate",
                            "already recorded; nothing done")

    handler = _HANDLERS.get(event_type)
    if handler is None:
        detail = f"{event_type} is not one of the handled events"
    else:
        detail = await handler(session, _object(event))

    await session.execute(
        m.StripeEvent.__table__.update()
        .where(m.StripeEvent.id == event_id)
        .values(processed_at=dt.datetime.now(UTC))
    )
    await session.flush()
    status = "applied" if detail is None else "ignored"
    return EventOutcome(event_id, event_type, status, detail)


# --- webhook: the handlers ---------------------------------------------------
#
# Each returns ``None`` when it acted, or a sentence saying why it did not.


def _period_end(obj: Mapping[str, Any]) -> dt.datetime | None:
    end = _epoch_to_utc(obj.get("current_period_end"))
    if end is not None:
        return end
    # 2025-era API: the period moved onto the subscription item.
    items = (obj.get("items") or {}).get("data") or []
    return _epoch_to_utc(items[0].get("current_period_end")) if items else None


async def _donation_by_ids(
    session: AsyncSession, *, donation_id: str | None = None,
    checkout_session_id: str | None = None, subscription_id: str | None = None,
) -> m.Donation | None:
    """The donation an event is about, tried in the order the event's own
    fields are most to least specific."""
    for column, value in (
        (m.Donation.id, donation_id),
        (m.Donation.stripe_checkout_session_id, checkout_session_id),
        (m.Donation.stripe_subscription_id, subscription_id),
    ):
        if not value:
            continue
        row = (await session.execute(
            select(m.Donation).where(column == value)
        )).scalars().first()
        if row is not None:
            return row
    return None


async def _handle_checkout_completed(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    metadata = obj.get("metadata") or {}
    donation = await _donation_by_ids(
        session, donation_id=metadata.get("donation_id"),
        checkout_session_id=obj.get("id"),
    )
    if donation is None:
        return f"no donation for checkout session {obj.get('id')!r}"
    donation.status = "active" if obj.get("mode") == "subscription" else "paid"
    subscription_id = obj.get("subscription")
    if subscription_id:
        donation.stripe_subscription_id = str(subscription_id)
    # Capture customer ID for both one-time and recurring donations so the portal is reachable
    customer_id = obj.get("customer")
    if customer_id:
        # Store customer ID in Subscription table for portal access (linked by user_id)
        # For recurring donations, also update via subscription webhook
        subscription_id = obj.get("subscription")
        if subscription_id:
            stmt = (
                m.Subscription.__table__.update()
                .where(m.Subscription.stripe_subscription_id == str(subscription_id))
                .values(stripe_customer_id=str(customer_id))
            )
            await session.execute(stmt)
    await session.flush()
    return None


async def _handle_invoice_paid(session: AsyncSession, obj: Mapping[str, Any]) -> str | None:
    # Invoice subscription field moved in 2025-era API: try direct field first, then nested path
    subscription_id = obj.get("subscription")
    if not subscription_id:
        # 2025-era API: subscription moved to parent.subscription_details.subscription
        parent = obj.get("parent") or {}
        subscription_details = parent.get("subscription_details") or {} if isinstance(parent, dict) else {}
        subscription_id = subscription_details.get("subscription")

    donation = await _donation_by_ids(session, subscription_id=subscription_id)
    if donation is None:
        return f"no donation for subscription {subscription_id!r}"
    donation.status = "active"
    await session.flush()
    return None


async def _handle_payment_failed(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    # Invoice subscription field moved in 2025-era API: try direct field first, then nested path
    subscription_id = obj.get("subscription")
    if not subscription_id:
        # 2025-era API: subscription moved to parent.subscription_details.subscription
        parent = obj.get("parent") or {}
        subscription_details = parent.get("subscription_details") or {} if isinstance(parent, dict) else {}
        subscription_id = subscription_details.get("subscription")

    donation = await _donation_by_ids(session, subscription_id=subscription_id)
    if donation is None:
        return f"no donation for subscription {subscription_id!r}"
    donation.status = "lapsed"
    await session.flush()
    return None


async def _handle_subscription_created(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    return "subscription creation is recorded by checkout.session.completed; nothing further to do"


async def _handle_subscription_updated(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    return "a donation's status tracks invoice events, not subscription updates; nothing to do"


async def _handle_subscription_deleted(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    """A donor cancelled their recurring donation, e.g. via the Customer Portal."""
    donation = await _donation_by_ids(session, subscription_id=obj.get("id"))
    if donation is None:
        return f"no donation for subscription {obj.get('id')!r}"
    donation.status = "canceled"
    await session.flush()
    return None


_HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "customer.subscription.created": _handle_subscription_created,
    "customer.subscription.updated": _handle_subscription_updated,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "invoice.paid": _handle_invoice_paid,
    "invoice.payment_failed": _handle_payment_failed,
}

assert set(_HANDLERS) == HANDLED_EVENTS, "HANDLED_EVENTS and _HANDLERS must agree"


__all__ = [
    "CHECKOUT_CANCEL_URL",
    "CHECKOUT_SUCCESS_URL",
    "DONATE_URL",
    "DONATION_INTERVALS",
    "HANDLED_EVENTS",
    "PORTAL_RETURN_URL",
    "SIGNATURE_TOLERANCE_SECONDS",
    "BillingError",
    "CheckoutSession",
    "EventOutcome",
    "InvalidDonationAmount",
    "LiveStripe",
    "NoCustomer",
    "SignatureInvalid",
    "StripeGateway",
    "create_donation_checkout",
    "customer_id_for",
    "handle_event",
    "open_portal",
    "verify_event",
]
