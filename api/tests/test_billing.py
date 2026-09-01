# api/tests/test_billing.py
"""Stripe: Checkout, the Customer Portal, and webhooks that cannot be replayed.

This is the module where a bug either charges somebody twice or hands them a
plan they did not buy, so the tests are written from the attacker's side and
from Stripe's — a delivery service that retries, duplicates and reorders.

The plan's three tests (Task 6 Step 1) come first:

* a replayed webhook with the same event id changes nothing the second time,
* an invalid signature is 400 and writes nothing,
* `customer.subscription.deleted` downgrades **at period end**, not immediately.

Nothing here reaches Stripe. The two calls that would (Checkout and Portal
session creation) go through :class:`explorer_api.billing.StripeGateway`, which
the fake below stands in for; signature verification is local HMAC by
construction, so it is exercised for real against the real library.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from explorer_api import billing, models as m
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.auth import current_user
from explorer_api.routes.billing import get_gateway, router as billing_router
from explorer_api.settings import Settings

WEBHOOK_SECRET = "whsec_test_secret"
UTC = dt.UTC


# --- doubles -----------------------------------------------------------------


@dataclass
class FakeStripe:
    """The two network calls, recorded instead of made."""

    checkout_url: str = "https://checkout.stripe.test/c/pay/cs_test_1"
    portal_url: str = "https://billing.stripe.test/p/session/live_1"
    checkout_calls: list[dict[str, Any]] = field(default_factory=list)
    portal_calls: list[dict[str, Any]] = field(default_factory=list)

    async def create_checkout_session(self, **kwargs: Any) -> billing.CheckoutSession:
        self.checkout_calls.append(kwargs)
        return billing.CheckoutSession(id="cs_test_1", url=self.checkout_url)

    async def create_portal_session(self, **kwargs: Any) -> str:
        self.portal_calls.append(kwargs)
        return self.portal_url


def _sign(body: bytes, *, secret: str = WEBHOOK_SECRET, timestamp: int | None = None,
          signature: str | None = None) -> str:
    """Stripe's `Stripe-Signature` header, computed the way Stripe computes it."""
    ts = timestamp if timestamp is not None else int(time.time())
    mac = signature or hmac.new(
        secret.encode(), f"{ts}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return f"t={ts},v1={mac}"


def _epoch(when: dt.datetime) -> int:
    return int(when.timestamp())


def subscription_event(
    event_type: str,
    *,
    customer: str,
    subscription: str = "sub_test_1",
    status: str = "active",
    price_id: str = "price_starter",
    plan_id: str | None = None,
    user_id: str | None = None,
    period_end: dt.datetime | None = None,
    cancel_at_period_end: bool = False,
    event_id: str | None = None,
) -> dict[str, Any]:
    period_end = period_end or dt.datetime.now(UTC) + dt.timedelta(days=20)
    # Checkout puts `{user_id, plan_id}` on `subscription_data.metadata`, so the
    # subscription events carry it even when they arrive before the session one.
    metadata = {k: v for k, v in (("plan_id", plan_id), ("user_id", user_id)) if v}
    return {
        "id": event_id or f"evt_{uuid4().hex[:16]}",
        "type": event_type,
        "data": {
            "object": {
                "id": subscription,
                "object": "subscription",
                "customer": customer,
                "status": status,
                "cancel_at_period_end": cancel_at_period_end,
                "current_period_start": _epoch(period_end - dt.timedelta(days=30)),
                "current_period_end": _epoch(period_end),
                "metadata": metadata,
                "items": {"data": [{"price": {"id": price_id}}]},
            }
        },
    }


def invoice_paid_event(
    *,
    customer: str,
    subscription: str = "sub_test_1",
    billing_reason: str = "subscription_cycle",
    event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id or f"evt_{uuid4().hex[:16]}",
        "type": "invoice.paid",
        "data": {
            "object": {
                "id": f"in_{uuid4().hex[:12]}",
                "object": "invoice",
                "customer": customer,
                "subscription": subscription,
                "billing_reason": billing_reason,
                "amount_paid": 900,
                "currency": "usd",
            }
        },
    }


# --- fixtures ----------------------------------------------------------------


async def _user(session, *, plan_id: str = "free") -> m.User:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test", email_verified=True,
                  plan_id=plan_id)
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def user(session) -> m.User:
    return await _user(session)


@pytest_asyncio.fixture
async def sellable_plans(session) -> Mapping[str, str]:
    """Give the paid plans a Stripe price id, as Task 12's runbook does live."""
    ids = {"starter": "price_starter", "pro": "price_pro"}
    for plan_id, price_id in ids.items():
        plan = await session.get(m.Plan, plan_id)
        plan.stripe_price_id = price_id
    await session.flush()
    return ids


@pytest.fixture
def gateway() -> FakeStripe:
    return FakeStripe()


@pytest_asyncio.fixture
async def client(session, user, gateway, database_url: str) -> AsyncIterator[AsyncClient]:
    """The billing router on the real app, signed in as ``user``."""
    settings = Settings.load(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": "s" * 32,
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET,
        }
    )
    app = create_app(settings)
    # Wiring the router into `main.create_app` belongs to the task that owns
    # `main.py`; mounting it here keeps this task to its three files.
    app.include_router(billing_router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[get_gateway] = lambda: gateway

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def _post_webhook(client: AsyncClient, event: dict[str, Any], **sign: Any):
    body = json.dumps(event).encode()
    return await client.post(
        "/api/billing/webhook",
        content=body,
        headers={"stripe-signature": _sign(body, **sign),
                 "content-type": "application/json"},
    )


async def _count(session, model) -> int:
    return int((await session.execute(select(func.count()).select_from(model))).scalar_one())


async def _balance(session, user: m.User) -> Decimal:
    row = (await session.execute(
        select(m.Credit.balance_usd).where(m.Credit.user_id == user.id)
    )).scalars().first()
    return Decimal("0") if row is None else row


# --- the plan's three tests --------------------------------------------------


async def test_a_replayed_webhook_changes_nothing_the_second_time(
    session, client, user, sellable_plans
):
    """Stripe retries. The second delivery of an event id must be a no-op."""
    session.add(m.Subscription(user_id=user.id, plan_id="starter",
                               stripe_customer_id="cus_1",
                               stripe_subscription_id="sub_test_1", state="active"))
    await session.flush()
    event = invoice_paid_event(customer="cus_1", event_id="evt_replay")

    first = await _post_webhook(client, event)
    assert first.status_code == 200 and first.json()["status"] == "applied"
    credited = await _balance(session, user)
    assert credited == Decimal("10.000000")        # starter's included credit, once

    second = await _post_webhook(client, event)
    assert second.status_code == 200               # a 4xx would make Stripe retry forever
    assert second.json()["status"] == "duplicate"
    assert await _balance(session, user) == credited
    assert await _count(session, m.StripeEvent) == 1


async def test_an_invalid_signature_is_400_and_writes_nothing(session, client, user):
    event = invoice_paid_event(customer="cus_1", event_id="evt_forged")
    body = json.dumps(event).encode()

    forged = await client.post(
        "/api/billing/webhook",
        content=body,
        headers={"stripe-signature": _sign(body, secret="whsec_not_ours")},
    )
    assert forged.status_code == 400
    assert await _count(session, m.StripeEvent) == 0
    assert await _balance(session, user) == Decimal("0")

    # A missing header is the same refusal — never an unsigned fast path.
    assert (await client.post("/api/billing/webhook", content=body)).status_code == 400
    assert await _count(session, m.StripeEvent) == 0


async def test_subscription_deleted_downgrades_at_period_end_not_immediately(
    session, client, user, sellable_plans
):
    user.plan_id = "pro"
    period_end = dt.datetime.now(UTC) + dt.timedelta(days=9)
    session.add(m.Subscription(user_id=user.id, plan_id="pro",
                               stripe_customer_id="cus_2",
                               stripe_subscription_id="sub_pro", state="active",
                               period_end=period_end))
    await session.flush()

    r = await _post_webhook(client, subscription_event(
        "customer.subscription.deleted", customer="cus_2", subscription="sub_pro",
        status="canceled", price_id="price_pro", period_end=period_end,
    ))
    assert r.status_code == 200
    await session.refresh(user)
    assert user.plan_id == "pro"                   # still paid for, still Pro

    sub = (await session.execute(select(m.Subscription))).scalar_one()
    assert sub.state == "canceled" and sub.cancel_at_period_end is True

    # …and the sweep that runs after the period does the downgrade.
    moved = await billing.apply_expired_downgrades(
        session, now=period_end + dt.timedelta(seconds=1)
    )
    await session.flush()
    await session.refresh(user)
    assert moved == 1 and user.plan_id == "free"


# --- checkout ----------------------------------------------------------------


async def test_checkout_returns_a_session_url_for_the_named_plan(
    client, user, gateway, sellable_plans
):
    r = await client.post("/api/billing/checkout", json={"plan": "starter"})
    assert r.status_code == 200
    assert r.json()["url"] == gateway.checkout_url

    (call,) = gateway.checkout_calls
    assert call["price_id"] == "price_starter"
    # The caller is identified to Stripe by our id, so the webhook can find them
    # again without trusting an email in the payload.
    assert call["client_reference_id"] == user.id
    assert call["metadata"]["plan_id"] == "starter"


async def test_checkout_refuses_what_cannot_be_sold(client, user, gateway):
    # The free plan is not a purchase.
    assert (await client.post("/api/billing/checkout",
                              json={"plan": "free"})).status_code == 400
    # An unknown plan is a validation error, never a silent fallback to free.
    assert (await client.post("/api/billing/checkout",
                              json={"plan": "enterprise"})).status_code == 422
    # A real plan with no Stripe price configured yet (the state Task 12 fixes)
    # fails loudly rather than charging for the wrong thing.
    assert (await client.post("/api/billing/checkout",
                              json={"plan": "pro"})).status_code == 503
    assert gateway.checkout_calls == []


async def test_checkout_reuses_the_customer_this_account_already_has(
    session, client, user, gateway, sellable_plans
):
    session.add(m.Subscription(user_id=user.id, plan_id="starter",
                               stripe_customer_id="cus_existing", state="canceled"))
    await session.flush()
    await client.post("/api/billing/checkout", json={"plan": "pro"})
    (call,) = gateway.checkout_calls
    assert call["customer_id"] == "cus_existing"   # never a second customer per user


async def test_billing_needs_a_session(session, database_url, gateway, user):
    """Every surface but the webhook is account-only; the webhook is Stripe-only."""
    settings = Settings.load({"DATABASE_URL": database_url, "SESSION_SECRET": "s" * 32,
                              "STRIPE_SECRET_KEY": "sk_test_x",
                              "STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET})
    app = create_app(settings)
    app.include_router(billing_router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_gateway] = lambda: gateway
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as http:
        assert (await http.post("/api/billing/checkout",
                                json={"plan": "starter"})).status_code == 401
        assert (await http.get("/api/billing/portal")).status_code == 401
        assert (await http.get("/api/billing/plans")).status_code == 200


# --- portal ------------------------------------------------------------------


async def test_the_portal_needs_a_customer_and_is_that_customer_only(
    session, client, user, gateway
):
    # Nothing bought yet: there is no customer to open a portal for.
    assert (await client.get("/api/billing/portal")).status_code == 409
    assert gateway.portal_calls == []

    session.add(m.Subscription(user_id=user.id, plan_id="starter",
                               stripe_customer_id="cus_mine", state="active"))
    # …and somebody else's customer, which must never be reachable from here.
    other = await _user(session)
    session.add(m.Subscription(user_id=other.id, plan_id="pro",
                               stripe_customer_id="cus_theirs", state="active"))
    await session.flush()

    r = await client.get("/api/billing/portal")
    assert r.status_code == 200 and r.json()["url"] == gateway.portal_url
    (call,) = gateway.portal_calls
    assert call["customer_id"] == "cus_mine"


# --- subscription lifecycle --------------------------------------------------


async def test_subscription_created_puts_the_account_on_the_paid_plan(
    session, client, user, sellable_plans
):
    assert user.plan_id == "free"
    r = await _post_webhook(client, subscription_event(
        "customer.subscription.created", customer="cus_3", price_id="price_pro",
        user_id=user.id))
    assert r.status_code == 200 and r.json()["status"] == "applied"

    await session.refresh(user, ["plan_id"])
    sub = (await session.execute(select(m.Subscription))).scalar_one()
    assert sub.user_id == user.id and sub.plan_id == "pro" and sub.state == "active"
    assert sub.period_end is not None
    assert user.plan_id == "pro"


async def test_a_past_due_subscription_keeps_the_plan_during_grace(
    session, client, user, sellable_plans
):
    user.plan_id = "starter"
    session.add(m.Subscription(user_id=user.id, plan_id="starter",
                               stripe_customer_id="cus_4",
                               stripe_subscription_id="sub_4", state="active"))
    await session.flush()

    await _post_webhook(client, subscription_event(
        "customer.subscription.updated", customer="cus_4", subscription="sub_4",
        status="past_due", price_id="price_starter"))
    await session.refresh(user, ["plan_id"])
    sub = (await session.execute(select(m.Subscription))).scalar_one()
    assert sub.state == "past_due"
    assert user.plan_id == "starter"        # 15 §6: a grace period, not a cut-off


async def test_checkout_completed_links_the_customer_to_the_account(
    session, client, user, sellable_plans
):
    event = {
        "id": "evt_checkout_done",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test_1", "object": "checkout.session",
            "client_reference_id": user.id, "customer": "cus_new",
            "subscription": "sub_new", "payment_status": "paid",
            "status": "complete", "metadata": {"plan_id": "starter"},
        }},
    }
    assert (await _post_webhook(client, event)).status_code == 200
    sub = (await session.execute(select(m.Subscription))).scalar_one()
    assert sub.user_id == user.id and sub.stripe_customer_id == "cus_new"
    assert sub.stripe_subscription_id == "sub_new"


# --- credits -----------------------------------------------------------------


async def test_only_a_subscription_invoice_grants_the_monthly_credit(
    session, client, user, sellable_plans
):
    session.add(m.Subscription(user_id=user.id, plan_id="pro",
                               stripe_customer_id="cus_5",
                               stripe_subscription_id="sub_5", state="active"))
    await session.flush()

    r = await _post_webhook(client, invoice_paid_event(
        customer="cus_5", subscription="sub_5", billing_reason="manual"))
    assert r.json()["status"] == "ignored"
    assert await _balance(session, user) == Decimal("0")

    await _post_webhook(client, invoice_paid_event(
        customer="cus_5", subscription="sub_5", billing_reason="subscription_create"))
    balance = await _balance(session, user)
    assert balance == Decimal("50.000000")        # pro's included credit
    assert isinstance(balance, Decimal)           # money is never a float

    await _post_webhook(client, invoice_paid_event(
        customer="cus_5", subscription="sub_5", billing_reason="subscription_cycle"))
    assert await _balance(session, user) == Decimal("100.000000")


async def test_payment_failed_starts_the_grace_period(session, client, user):
    session.add(m.Subscription(user_id=user.id, plan_id="starter",
                               stripe_customer_id="cus_6",
                               stripe_subscription_id="sub_6", state="active"))
    await session.flush()
    event = {
        "id": "evt_failed",
        "type": "invoice.payment_failed",
        "data": {"object": {"id": "in_x", "object": "invoice", "customer": "cus_6",
                            "subscription": "sub_6", "billing_reason": "subscription_cycle"}},
    }
    assert (await _post_webhook(client, event)).status_code == 200
    sub = (await session.execute(select(m.Subscription))).scalar_one()
    assert sub.state == "past_due"


# --- events we do not act on -------------------------------------------------


async def test_an_unhandled_event_is_recorded_and_ignored(session, client):
    event = {"id": "evt_other", "type": "payment_intent.succeeded",
             "data": {"object": {"id": "pi_1"}}}
    r = await _post_webhook(client, event)
    assert r.status_code == 200 and r.json()["status"] == "ignored"
    row = (await session.execute(select(m.StripeEvent))).scalar_one()
    assert row.id == "evt_other" and row.processed_at is not None


async def test_an_event_for_an_unknown_customer_is_ignored_not_fatal(session, client):
    """A test-mode event, or one for a deleted account: never a 500 loop."""
    r = await _post_webhook(client, invoice_paid_event(customer="cus_nobody",
                                                       subscription="sub_nobody"))
    assert r.status_code == 200 and r.json()["status"] == "ignored"


async def test_a_stale_timestamp_is_refused(session, client):
    """Replay protection: an old signature must not be accepted forever."""
    event = invoice_paid_event(customer="cus_1", event_id="evt_stale")
    body = json.dumps(event).encode()
    old = int(time.time()) - 3600
    r = await client.post(
        "/api/billing/webhook", content=body,
        headers={"stripe-signature": _sign(body, timestamp=old)},
    )
    assert r.status_code == 400
    assert await _count(session, m.StripeEvent) == 0


# --- the public price table --------------------------------------------------


async def test_the_public_plan_table_is_the_plans_module(client):
    body = (await client.get("/api/billing/plans")).json()
    assert [p["id"] for p in body] == ["free", "starter", "pro"]
    starter = body[1]
    # Money crosses the wire as a string, at the ledger's six places.
    assert starter["price_usd"] == "9.000000"
    assert starter["included_credit_usd"] == "10.000000"
    assert starter["quotas"]["private_trees"] == 3


async def test_a_second_subscription_does_not_clobber_the_live_one(
    session, client, user, sellable_plans
):
    """A customer can hold two subscriptions; the second must get its own row.

    Overwriting the first row's `stripe_subscription_id` would make the live
    subscription unfindable and leave the old one looking current — a silent
    way to bill for one thing and entitle another.
    """
    session.add(m.Subscription(user_id=user.id, plan_id="starter",
                               stripe_customer_id="cus_7",
                               stripe_subscription_id="sub_first", state="active"))
    await session.flush()

    r = await _post_webhook(client, subscription_event(
        "customer.subscription.created", customer="cus_7", subscription="sub_second",
        price_id="price_pro"))
    assert r.status_code == 200 and r.json()["status"] == "applied"

    rows = {s.stripe_subscription_id: s for s in
            (await session.execute(select(m.Subscription))).scalars().all()}
    assert set(rows) == {"sub_first", "sub_second"}
    assert rows["sub_first"].plan_id == "starter"      # untouched
    assert rows["sub_second"].user_id == user.id       # owner found via the customer


async def test_cancelling_an_old_subscription_does_not_strip_the_live_plan(
    session, client, user, sellable_plans
):
    """One account, two subscriptions: ending the old one must not downgrade."""
    user.plan_id = "pro"
    stale = dt.datetime.now(UTC) - dt.timedelta(days=1)
    session.add_all([
        m.Subscription(user_id=user.id, plan_id="starter", stripe_customer_id="cus_8",
                       stripe_subscription_id="sub_old", state="active",
                       period_end=stale),
        m.Subscription(user_id=user.id, plan_id="pro", stripe_customer_id="cus_8",
                       stripe_subscription_id="sub_new", state="active"),
    ])
    await session.flush()

    await _post_webhook(client, subscription_event(
        "customer.subscription.deleted", customer="cus_8", subscription="sub_old",
        status="canceled", price_id="price_starter", period_end=stale))
    await session.refresh(user, ["plan_id"])
    assert user.plan_id == "pro"

    # …and the sweep leaves them alone too, for the same reason.
    assert await billing.apply_expired_downgrades(session) == 0
    await session.refresh(user, ["plan_id"])
    assert user.plan_id == "pro"
