"""Stripe: Checkout, the Customer Portal, and webhooks that cannot be replayed.

Authority: component 15 §5 (the three billing routes and the public price
table), §7 (`subscriptions`, `credits`, `stripe_events`) and §8 ("`invoice.paid`
→ credit top-up, `customer.subscription.updated/deleted` → plan change,
`invoice.payment_failed` → grace"). 15 §9's bar is one sentence — *"replaying
any event changes nothing"* — and this module is built around it.

Four decisions worth stating, because each is a correctness rule rather than a
style preference:

**1. The event id is claimed before anything is applied.** :func:`handle_event`
inserts the row into ``stripe_events`` with ``ON CONFLICT DO NOTHING``; if the
insert claimed nothing, the event has already been seen and the function stops.
Because that INSERT and the effects share one transaction, a concurrent second
delivery blocks on the primary key rather than double-crediting, and a failure
half-way rolls the claim back so Stripe's next retry is a real retry.

**2. Signature verification happens before the database is touched at all.**
:func:`verify_event` is local HMAC (`stripe.Webhook.construct_event` makes no
network call), so a forged or stale delivery is refused without a write — which
is what makes "an invalid signature writes nothing" true rather than merely
likely.

**3. A cancellation downgrades at period end, never on the event.** The user
paid through ``period_end``; :func:`_apply_plan` keeps the plan until then and
:func:`apply_expired_downgrades` is the sweep that finally moves them. Same rule
for ``past_due``: 15 §6's grace period, not a cut-off.

**4. The two calls that reach Stripe go through :class:`StripeGateway`.**
Checkout and Portal session creation are the only outbound calls in the module;
behind a protocol they can be faked in a test without a network stub, and the
webhook path — which is where the money logic lives — has no outbound call at
all.

No card data ever reaches this service (15 §10): Checkout and the Portal are
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

from . import ledger, models as m, plans

UTC = dt.UTC

#: 15 §5's billing pages live on the site; this module only decides which plan
#: to name and where to come back to.
CHECKOUT_SUCCESS_URL = f"{plans.BILLING_URL}?checkout=success"
CHECKOUT_CANCEL_URL = f"{plans.BILLING_URL}?checkout=cancelled"
PORTAL_RETURN_URL = plans.BILLING_URL

#: Stripe's own default: a signature older than this is refused, so a captured
#: delivery cannot be replayed at leisure.
SIGNATURE_TOLERANCE_SECONDS = 300

#: The events 15 §8 names. Anything else is recorded and ignored — recorded so
#: an operator can see what Stripe is sending, ignored so an unknown type can
#: never be a 500 that makes Stripe retry forever.
HANDLED_EVENTS: frozenset[str] = frozenset({
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
})

#: States where the subscription entitles the account to its paid plan.
ACTIVE_STATES: frozenset[str] = frozenset({"active", "trialing"})
#: States where the subscription is over — the downgrade is due at period end.
TERMINAL_STATES: frozenset[str] = frozenset({"canceled", "incomplete_expired", "unpaid"})
#: 15 §6: seven days read-only on paid features, not an instant downgrade.
GRACE_STATES: frozenset[str] = frozenset({"past_due"})

#: Only a subscription's own invoices carry the monthly included credit. An
#: overage or a one-off invoice is paid *from* credit; granting more for it
#: would hand the bundle out twice a month.
CREDIT_GRANTING_BILLING_REASONS: frozenset[str] = frozenset({
    "subscription_create", "subscription_cycle",
})

FREE_PLAN = "free"


# --- errors ------------------------------------------------------------------


class BillingError(RuntimeError):
    """Base for everything this module refuses to do."""


class SignatureInvalid(BillingError):
    """The delivery is not from Stripe, or is too old to still be honoured."""


class PlanNotPurchasable(BillingError):
    """A plan that is not for sale — the free tier has nothing to check out."""


class PlanNotSellable(BillingError):
    """A paid plan with no Stripe price configured yet (Task 12's runbook).

    Deliberately fatal rather than "pick something": a checkout at a guessed
    price would charge a real card the wrong amount.
    """

    def __init__(self, plan_id: str) -> None:
        self.plan_id = plan_id
        super().__init__(
            f"plan {plan_id!r} has no stripe_price_id. Create the Stripe price and "
            "set it on the `plans` row before selling this plan."
        )


class NoCustomer(BillingError):
    """The account has never checked out, so it has no Stripe customer."""


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
        price_id: str,
        client_reference_id: str,
        customer_id: str | None,
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
        price_id: str,
        client_reference_id: str,
        customer_id: str | None,
        customer_email: str | None,
        success_url: str,
        cancel_url: str,
        metadata: Mapping[str, str],
    ) -> CheckoutSession:
        params: dict[str, Any] = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "client_reference_id": client_reference_id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": dict(metadata),
            # Carried onto the subscription itself, so `customer.subscription.*`
            # can find the account even if it arrives before the session event.
            "subscription_data": {"metadata": dict(metadata)},
        }
        if customer_id:
            params["customer"] = customer_id
        elif customer_email:
            params["customer_email"] = customer_email
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


async def start_checkout(
    session: AsyncSession,
    user: m.User,
    plan_id: str,
    gateway: StripeGateway,
    *,
    success_url: str = CHECKOUT_SUCCESS_URL,
    cancel_url: str = CHECKOUT_CANCEL_URL,
) -> CheckoutSession:
    """A Stripe Checkout session for ``plan_id``, for this user only."""
    plan = plans.get(plan_id)                    # UnknownPlan for anything else
    if not plan.is_paid:
        raise PlanNotPurchasable(
            f"{plan.id} is free; there is nothing to check out"
        )
    row = await session.get(m.Plan, plan.id)
    price_id = row.stripe_price_id if row is not None else None
    if not price_id:
        raise PlanNotSellable(plan.id)
    return await gateway.create_checkout_session(
        price_id=price_id,
        client_reference_id=user.id,
        customer_id=await customer_id_for(session, user),
        customer_email=user.email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user.id, "plan_id": plan.id},
    )


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
        detail = f"{event_type} is not one of 15 §8's events"
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


async def _subscription_by_ids(
    session: AsyncSession,
    *,
    subscription_id: str | None = None,
    customer_id: str | None = None,
) -> m.Subscription | None:
    """The row this event is *about*: by subscription id, then by customer.

    Read-oriented — good enough to answer "whose plan is this, and what state is
    the customer in". Anything that is about to write an id onto the row uses
    :func:`_bindable_subscription` instead.
    """
    for column, value in ((m.Subscription.stripe_subscription_id, subscription_id),
                          (m.Subscription.stripe_customer_id, customer_id)):
        if not value:
            continue
        row = (await session.execute(
            select(m.Subscription).where(column == value)
            .order_by(m.Subscription.updated_at.desc()).limit(1)
        )).scalars().first()
        if row is not None:
            return row
    return None


async def _bindable_subscription(
    session: AsyncSession,
    *,
    subscription_id: str | None,
    customer_id: str | None,
    user_id: str | None = None,
) -> m.Subscription | None:
    """The row ``subscription_id`` may be written onto, or ``None`` for a new one.

    A customer can hold more than one subscription over time, and the second
    one's events must not overwrite the first one's id — that would make the
    live subscription unfindable and leave the old one looking current. So a
    row is bindable only when it is the same subscription, or when it carries no
    subscription id yet.
    """
    if subscription_id:
        row = (await session.execute(
            select(m.Subscription)
            .where(m.Subscription.stripe_subscription_id == subscription_id)
        )).scalars().first()
        if row is not None:
            return row
    clauses = []
    if customer_id:
        clauses.append(m.Subscription.stripe_customer_id == customer_id)
    if user_id:
        clauses.append(m.Subscription.user_id == user_id)
    for clause in clauses:
        row = (await session.execute(
            select(m.Subscription)
            .where(clause, m.Subscription.stripe_subscription_id.is_(None))
            .order_by(m.Subscription.updated_at.desc()).limit(1)
        )).scalars().first()
        if row is not None:
            return row
    return None


async def _plan_for_price(session: AsyncSession, price_id: str | None) -> str | None:
    if not price_id:
        return None
    return (await session.execute(
        select(m.Plan.id).where(m.Plan.stripe_price_id == price_id).limit(1)
    )).scalars().first()


def _price_id(obj: Mapping[str, Any]) -> str | None:
    items = (obj.get("items") or {}).get("data") or []
    if not items:
        return None
    price = items[0].get("price") or {}
    return price.get("id") if isinstance(price, Mapping) else None


def _period_end(obj: Mapping[str, Any]) -> dt.datetime | None:
    end = _epoch_to_utc(obj.get("current_period_end"))
    if end is not None:
        return end
    # 2025-era API: the period moved onto the subscription item.
    items = (obj.get("items") or {}).get("data") or []
    return _epoch_to_utc(items[0].get("current_period_end")) if items else None


async def _has_live_subscription(
    session: AsyncSession, user: m.User, *, excluding: str | None = None
) -> bool:
    """Is anything else still paying for this account?"""
    stmt = select(m.Subscription.id).where(
        m.Subscription.user_id == user.id,
        m.Subscription.state.in_(sorted(ACTIVE_STATES | GRACE_STATES)),
    )
    if excluding:
        stmt = stmt.where(m.Subscription.id != excluding)
    return (await session.execute(stmt.limit(1))).first() is not None


async def _apply_plan(
    session: AsyncSession, user: m.User, sub: m.Subscription,
    *, now: dt.datetime | None = None,
) -> None:
    """Move ``user`` onto (or off) the subscription's plan.

    Two rules, and nothing else:

    * A subscription that has ended still entitles the user to the plan until
      ``period_end``. Nothing here downgrades early —
      :func:`apply_expired_downgrades` does that, later, when the time is up.
    * A user may hold more than one subscription, so an ended one only
      downgrades them if no other is still live. Otherwise cancelling an old
      subscription would strip the plan the new one is paying for.

    ``GRACE_STATES`` and the ``incomplete`` states leave the plan exactly as it
    is (15 §6's grace period).
    """
    now = now or dt.datetime.now(UTC)
    if sub.state in ACTIVE_STATES:
        user.plan_id = sub.plan_id
        return
    over = sub.state in TERMINAL_STATES and (
        sub.period_end is None or sub.period_end <= now
    )
    if over and not await _has_live_subscription(session, user, excluding=sub.id):
        user.plan_id = FREE_PLAN


async def _handle_subscription(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    subscription_id = obj.get("id")
    customer_id = obj.get("customer")
    metadata = obj.get("metadata") or {}
    sub = await _bindable_subscription(session, subscription_id=subscription_id,
                                       customer_id=customer_id)

    user: m.User | None = None
    if sub is not None:
        user = await session.get(m.User, sub.user_id)
    elif metadata.get("user_id"):
        user = await session.get(m.User, str(metadata["user_id"]))
    if user is None and customer_id:
        # A second subscription for a customer we already know: find the owner
        # from any of their rows, without writing this id onto that row.
        owner = await _subscription_by_ids(session, customer_id=customer_id)
        if owner is not None:
            user = await session.get(m.User, owner.user_id)
    if user is None:
        return f"no account for customer {customer_id!r}"

    plan_id = (
        await _plan_for_price(session, _price_id(obj))
        or (str(metadata["plan_id"]) if metadata.get("plan_id") in plans.PLANS else None)
        or (sub.plan_id if sub is not None else None)
    )
    if plan_id is None:
        return f"no plan matches price {_price_id(obj)!r}"

    if sub is None:
        sub = m.Subscription(user_id=user.id, plan_id=plan_id, state="incomplete")
        session.add(sub)
    sub.plan_id = plan_id
    if customer_id:
        sub.stripe_customer_id = str(customer_id)
    if subscription_id:
        sub.stripe_subscription_id = str(subscription_id)
    state = str(obj.get("status") or sub.state)
    sub.state = state if state in m.SUBSCRIPTION_STATES else sub.state
    sub.period_start = _epoch_to_utc(obj.get("current_period_start")) or sub.period_start
    sub.period_end = _period_end(obj) or sub.period_end
    # A deleted subscription is, by definition, not renewing — say so explicitly
    # so the downgrade sweep and the UI agree on what is about to happen.
    sub.cancel_at_period_end = bool(obj.get("cancel_at_period_end")) or (
        sub.state in TERMINAL_STATES
    )
    await session.flush()
    await _apply_plan(session, user, sub)
    await session.flush()
    return None


async def _handle_checkout_completed(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    metadata = obj.get("metadata") or {}
    user_id = obj.get("client_reference_id") or metadata.get("user_id")
    user = await session.get(m.User, str(user_id)) if user_id else None
    if user is None:
        return f"no account for client_reference_id {user_id!r}"

    customer_id = obj.get("customer")
    subscription_id = obj.get("subscription")
    plan_id = str(metadata.get("plan_id") or "")
    sub = await _bindable_subscription(session, subscription_id=subscription_id,
                                       customer_id=customer_id, user_id=user.id)
    if sub is None:
        sub = m.Subscription(user_id=user.id,
                             plan_id=plan_id if plan_id in plans.PLANS else FREE_PLAN,
                             state="incomplete")
        session.add(sub)
    if plan_id in plans.PLANS:
        sub.plan_id = plan_id
    if customer_id:
        sub.stripe_customer_id = str(customer_id)
    if subscription_id:
        sub.stripe_subscription_id = str(subscription_id)
    # `customer.subscription.created` carries the authoritative state and period;
    # this event only establishes who the customer belongs to, plus enough state
    # that a user who paid is not left on free if that event is delayed.
    if obj.get("payment_status") == "paid" and sub.state not in TERMINAL_STATES:
        sub.state = "active"
    await session.flush()
    await _apply_plan(session, user, sub)
    await session.flush()
    return None


async def _grant_credit(session: AsyncSession, user: m.User, amount: Decimal) -> None:
    """Add ``amount`` to the account's credit balance, creating the row if needed."""
    credit = await session.get(m.Credit, user.id, with_for_update=True)
    if credit is None:
        credit = m.Credit(user_id=user.id, balance_usd=Decimal("0"))
        session.add(credit)
        await session.flush()
    credit.balance_usd = ledger.money(Decimal(credit.balance_usd) + amount)
    await session.flush()


async def _handle_invoice_paid(session: AsyncSession, obj: Mapping[str, Any]) -> str | None:
    reason = str(obj.get("billing_reason") or "")
    sub = await _subscription_by_ids(session, subscription_id=obj.get("subscription"),
                                     customer_id=obj.get("customer"))
    if sub is None:
        return f"no subscription for customer {obj.get('customer')!r}"
    if reason not in CREDIT_GRANTING_BILLING_REASONS:
        return f"billing_reason {reason!r} carries no included credit"
    user = await session.get(m.User, sub.user_id)
    if user is None:  # pragma: no cover - FK makes this unreachable
        return f"no account for subscription {sub.id!r}"
    amount = plans.get(sub.plan_id).included_credit_usd
    if amount <= 0:
        return f"plan {sub.plan_id!r} includes no credit"
    await _grant_credit(session, user, amount)
    return None


async def _handle_payment_failed(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    sub = await _subscription_by_ids(session, subscription_id=obj.get("subscription"),
                                     customer_id=obj.get("customer"))
    if sub is None:
        return f"no subscription for customer {obj.get('customer')!r}"
    # 15 §6: seven days read-only on paid features. The plan does not change
    # here; `customer.subscription.deleted` is what ends it, at period end.
    sub.state = "past_due"
    await session.flush()
    return None


_HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "customer.subscription.created": _handle_subscription,
    "customer.subscription.updated": _handle_subscription,
    "customer.subscription.deleted": _handle_subscription,
    "invoice.paid": _handle_invoice_paid,
    "invoice.payment_failed": _handle_payment_failed,
}

assert set(_HANDLERS) == HANDLED_EVENTS, "HANDLED_EVENTS and _HANDLERS must agree"


# --- the downgrade sweep -----------------------------------------------------


async def apply_expired_downgrades(
    session: AsyncSession, *, now: dt.datetime | None = None
) -> int:
    """Move accounts whose ended subscription has now run out onto the free plan.

    This is the other half of "downgrade at period end": the webhook records
    that the subscription ended, this decides that the paid period is over.
    Run it on a schedule; it is idempotent, and returns how many it moved.
    """
    now = now or dt.datetime.now(UTC)
    stmt = (
        select(m.User, m.Subscription)
        .join(m.Subscription, m.Subscription.user_id == m.User.id)
        .where(
            m.Subscription.state.in_(sorted(TERMINAL_STATES)),
            m.User.plan_id != FREE_PLAN,
            (m.Subscription.period_end.is_(None)) | (m.Subscription.period_end <= now),
        )
    )
    moved = 0
    for user, sub in (await session.execute(stmt)).all():
        # Only if nothing else is still paying for them.
        if await _has_live_subscription(session, user):
            continue
        user.plan_id = FREE_PLAN
        sub.cancel_at_period_end = True
        moved += 1
    await session.flush()
    return moved


__all__ = [
    "ACTIVE_STATES",
    "CHECKOUT_CANCEL_URL",
    "CHECKOUT_SUCCESS_URL",
    "CREDIT_GRANTING_BILLING_REASONS",
    "GRACE_STATES",
    "HANDLED_EVENTS",
    "PORTAL_RETURN_URL",
    "SIGNATURE_TOLERANCE_SECONDS",
    "TERMINAL_STATES",
    "BillingError",
    "CheckoutSession",
    "EventOutcome",
    "LiveStripe",
    "NoCustomer",
    "PlanNotPurchasable",
    "PlanNotSellable",
    "SignatureInvalid",
    "StripeGateway",
    "apply_expired_downgrades",
    "customer_id_for",
    "handle_event",
    "open_portal",
    "start_checkout",
    "verify_event",
]
