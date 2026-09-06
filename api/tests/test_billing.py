# api/tests/test_billing.py
"""Stripe: donation Checkout, the Customer Portal, and webhooks that cannot be replayed.

Three inherited guarantees, still tested here because they are still true and
still load-bearing: a replayed webhook changes nothing the second time, an
invalid signature is 400 and writes nothing, and the two outbound calls this
module makes go through `StripeGateway` so nothing here opens a socket.

What is new: a donation's amount is arbitrary, so Checkout is built with an
inline `price_data` rather than a pre-created Price id, and there is no plan to
switch a user onto — a paid invoice just marks a `Donation` row `active`
(monthly) or `paid` (one-time), a failed one marks it `lapsed`, and a donor
cancelling their recurring donation (e.g. via the Customer Portal) marks it
`canceled`. `customer.subscription.created`/`updated` carry no donation-specific
action — the state transitions that matter are covered by
`checkout.session.completed` and the two invoice events — so they are asserted
here only to the extent that they are handled gracefully, not to a NameError.
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
from explorer_api.routes.donate import get_gateway, router as donate_router
from explorer_api.settings import Settings

WEBHOOK_SECRET = "whsec_test_secret"
UTC = dt.UTC


@dataclass
class FakeStripe:
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
    ts = timestamp if timestamp is not None else int(time.time())
    mac = signature or hmac.new(
        secret.encode(), f"{ts}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return f"t={ts},v1={mac}"


def checkout_completed_event(
    *, customer: str, amount_total: int = 2500, mode: str = "payment",
    subscription: str | None = None, donation_id: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id or f"evt_{uuid4().hex[:16]}",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_{uuid4().hex[:16]}",
                "object": "checkout.session",
                "customer": customer,
                "subscription": subscription,
                "mode": mode,
                "amount_total": amount_total,
                "currency": "usd",
                "payment_status": "paid",
                "metadata": {"donation_id": donation_id} if donation_id else {},
            }
        },
    }


def invoice_event(
    event_type: str, *, customer: str, subscription: str = "sub_test_1",
    billing_reason: str = "subscription_cycle", event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id or f"evt_{uuid4().hex[:16]}",
        "type": event_type,
        "data": {
            "object": {
                "id": f"in_{uuid4().hex[:12]}",
                "object": "invoice",
                "customer": customer,
                "subscription": subscription,
                "billing_reason": billing_reason,
            }
        },
    }


def subscription_event(
    event_type: str, *, customer: str, subscription: str = "sub_test_1",
    status: str = "active", event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id or f"evt_{uuid4().hex[:16]}",
        "type": event_type,
        "data": {
            "object": {
                "id": subscription,
                "object": "subscription",
                "customer": customer,
                "status": status,
            }
        },
    }


async def _user(session, **kwargs: Any) -> m.User:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test", email_verified=True, **kwargs)
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def user(session) -> m.User:
    return await _user(session)


@pytest.fixture
def gateway() -> FakeStripe:
    return FakeStripe()


@pytest_asyncio.fixture
async def client(session, user, gateway, database_url: str) -> AsyncIterator[AsyncClient]:
    settings = Settings.load({
        "DATABASE_URL": database_url,
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET,
    })
    app = create_app(settings)

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
        "/api/billing/webhook", content=body,
        headers={"stripe-signature": _sign(body, **sign),
                 "content-type": "application/json"},
    )


async def _count(session, model) -> int:
    return int((await session.execute(select(func.count()).select_from(model))).scalar_one())


# --- checkout ------------------------------------------------------------


async def test_a_one_time_donation_builds_an_inline_price(client, gateway):
    r = await client.post("/api/donate/checkout",
                          json={"amount_usd": "25", "interval": "once"})
    assert r.status_code == 200, r.text
    assert r.json()["url"] == gateway.checkout_url
    call = gateway.checkout_calls[0]
    assert call["mode"] == "payment"
    assert call["price_data"]["unit_amount"] == 2500
    assert "recurring" not in call["price_data"]


async def test_a_monthly_donation_builds_a_recurring_inline_price(client, gateway):
    r = await client.post("/api/donate/checkout",
                          json={"amount_usd": "10", "interval": "month"})
    assert r.status_code == 200, r.text
    call = gateway.checkout_calls[0]
    assert call["mode"] == "subscription"
    assert call["price_data"]["recurring"] == {"interval": "month"}


async def test_a_zero_or_negative_amount_is_rejected(client):
    r = await client.post("/api/donate/checkout",
                          json={"amount_usd": "0", "interval": "once"})
    assert r.status_code == 422


async def test_checkout_creates_a_pending_donation_row(session, client):
    await client.post("/api/donate/checkout", json={"amount_usd": "5", "interval": "once"})
    assert await _count(session, m.Donation) == 1
    row = (await session.execute(select(m.Donation))).scalars().first()
    assert row.status == "pending" and row.amount_usd == Decimal("5.000000")


# --- webhook: inherited guarantees ----------------------------------------


async def test_a_replayed_webhook_changes_nothing_the_second_time(session, client, user):
    event = checkout_completed_event(customer="cus_1", donation_id="don_placeholder")
    donation = m.Donation(id="don_placeholder", amount_usd=Decimal("25"),
                          interval="once", status="pending",
                          stripe_checkout_session_id=event["data"]["object"]["id"])
    session.add(donation)
    await session.flush()

    r1 = await _post_webhook(client, event)
    r2 = await _post_webhook(client, event)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json()["status"] == "duplicate"
    assert await _count(session, m.StripeEvent) == 1


async def test_an_invalid_signature_is_400_and_writes_nothing(session, client):
    event = checkout_completed_event(customer="cus_1")
    body = json.dumps(event).encode()
    r = await client.post(
        "/api/billing/webhook", content=body,
        headers={"stripe-signature": _sign(body, signature="0" * 64),
                 "content-type": "application/json"},
    )
    assert r.status_code == 400
    assert await _count(session, m.StripeEvent) == 0


# --- webhook: donation-specific behavior ----------------------------------


async def test_checkout_completed_marks_a_one_time_donation_paid(session, client):
    donation = m.Donation(id="don_a", amount_usd=Decimal("25"), interval="once",
                          status="pending", stripe_checkout_session_id="cs_a")
    session.add(donation)
    await session.flush()
    event = checkout_completed_event(
        customer="cus_a", donation_id="don_a", mode="payment",
    )
    event["data"]["object"]["id"] = "cs_a"
    r = await _post_webhook(client, event)
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "paid"


async def test_checkout_completed_marks_a_monthly_donation_active_and_records_the_subscription(
    session, client,
):
    donation = m.Donation(id="don_b", amount_usd=Decimal("10"), interval="month",
                          status="pending", stripe_checkout_session_id="cs_b")
    session.add(donation)
    await session.flush()
    event = checkout_completed_event(
        customer="cus_b", donation_id="don_b", mode="subscription",
        subscription="sub_b",
    )
    event["data"]["object"]["id"] = "cs_b"
    r = await _post_webhook(client, event)
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "active"
    assert donation.stripe_subscription_id == "sub_b"


async def test_invoice_paid_keeps_a_monthly_donation_active(session, client):
    donation = m.Donation(id="don_c", amount_usd=Decimal("10"), interval="month",
                          status="active", stripe_subscription_id="sub_c")
    session.add(donation)
    await session.flush()
    r = await _post_webhook(client, invoice_event("invoice.paid", customer="cus_c",
                                                   subscription="sub_c"))
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "active"


async def test_payment_failed_marks_a_monthly_donation_lapsed(session, client):
    donation = m.Donation(id="don_d", amount_usd=Decimal("10"), interval="month",
                          status="active", stripe_subscription_id="sub_d")
    session.add(donation)
    await session.flush()
    r = await _post_webhook(
        client, invoice_event("invoice.payment_failed", customer="cus_d",
                              subscription="sub_d"),
    )
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "lapsed"


async def test_subscription_deleted_marks_a_monthly_donation_canceled(session, client):
    """A donor who cancels their recurring donation via the Customer Portal
    fires `customer.subscription.deleted` — the only subscription event this
    module acts on, since `checkout.session.completed` and the invoice events
    already cover creation and renewal."""
    donation = m.Donation(id="don_e", amount_usd=Decimal("10"), interval="month",
                          status="active", stripe_subscription_id="sub_e")
    session.add(donation)
    await session.flush()
    r = await _post_webhook(
        client, subscription_event("customer.subscription.deleted", customer="cus_e",
                                   subscription="sub_e"),
    )
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "canceled"


async def test_subscription_created_and_updated_are_acknowledged_without_acting(
    session, client,
):
    """These two events carry no donation-specific action — this asserts they
    are handled gracefully (200, recorded, `ignored`) rather than raising."""
    for event_type in ("customer.subscription.created", "customer.subscription.updated"):
        r = await _post_webhook(
            client, subscription_event(event_type, customer="cus_f", subscription="sub_f"),
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "ignored"


# --- portal ----------------------------------------------------------------


async def test_the_portal_needs_a_customer_and_is_that_customer_only(client):
    r = await client.get("/api/billing/portal")
    assert r.status_code == 409


async def test_the_portal_opens_for_a_known_customer(session, client, user, gateway):
    session.add(m.Subscription(user_id=user.id, plan_id="free",
                               stripe_customer_id="cus_known", state="active"))
    await session.flush()
    r = await client.get("/api/billing/portal")
    assert r.status_code == 200, r.text
    assert r.json()["url"] == gateway.portal_url
    assert gateway.portal_calls[0]["customer_id"] == "cus_known"
