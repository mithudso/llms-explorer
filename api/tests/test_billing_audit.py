"""Donation lifecycle regressions, using real PostgreSQL and a fake Stripe seam."""
from __future__ import annotations

import asyncio
import datetime as dt
import os
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from explorer_api import billing, models as m


@pytest.mark.parametrize("amount", ["1.999", "0.009"])
async def test_checkout_rejects_fractional_cents_before_recording_or_provider(session, amount):
    gateway = SimpleNamespace(create_checkout_session=AsyncMock(
        return_value=billing.CheckoutSession("cs_precision", "https://checkout.test")))
    with pytest.raises(billing.InvalidDonationAmount, match="whole cents"):
        await billing.create_donation_checkout(
            session, gateway, amount_usd=Decimal(amount), interval="once", user=None,
            success_url=billing.CHECKOUT_SUCCESS_URL, cancel_url=billing.CHECKOUT_CANCEL_URL)
    gateway.create_checkout_session.assert_not_awaited()
    assert (await session.execute(select(m.Donation))).scalars().all() == []


async def test_exact_cents_match_the_recorded_checkout_amount(session):
    gateway = SimpleNamespace(create_checkout_session=AsyncMock(
        return_value=billing.CheckoutSession("cs_exact", "https://checkout.test")))
    await billing.create_donation_checkout(
        session, gateway, amount_usd=Decimal("1.2300"), interval="once", user=None,
        success_url=billing.CHECKOUT_SUCCESS_URL, cancel_url=billing.CHECKOUT_CANCEL_URL)
    row = (await session.execute(select(m.Donation))).scalars().one()
    assert row.amount_usd == Decimal("1.23")
    assert gateway.create_checkout_session.call_args.kwargs["price_data"]["unit_amount"] == 123


def event(kind, donation, **overrides):
    obj = {"id": donation.stripe_checkout_session_id, "mode": "subscription",
           "subscription": donation.stripe_subscription_id or "sub_audit",
           "customer": "cus_audit", "payment_status": "paid",
           "metadata": {"donation_id": donation.id}}
    if kind == "customer.subscription.deleted":
        obj["id"] = donation.stripe_subscription_id
    obj.update(overrides)
    return {"id": "evt_" + uuid4().hex, "type": kind, "data": {"object": obj}}


async def donation_for(session, *, interval="month", status="pending", user=None):
    row = m.Donation(amount_usd=Decimal("10"), interval=interval, status=status,
                     user_id=user.id if user else None,
                     stripe_checkout_session_id="cs_" + uuid4().hex,
                     stripe_subscription_id="sub_" + uuid4().hex if interval == "month" else None)
    session.add(row)
    await session.flush()
    return row


async def test_new_donor_can_open_only_their_own_portal(session):
    owner = m.User(email="donor@example.test", email_verified=True)
    other = m.User(email="other@example.test", email_verified=True)
    session.add_all([owner, other])
    await session.flush()
    donation = await donation_for(session, user=owner)
    await billing.handle_event(session, event("checkout.session.completed", donation))
    await session.commit()
    gateway = SimpleNamespace(create_portal_session=AsyncMock(return_value="https://portal.test"))
    assert await billing.open_portal(session, owner, gateway) == "https://portal.test"
    gateway.create_portal_session.assert_awaited_once_with(
        customer_id="cus_audit", return_url=billing.PORTAL_RETURN_URL)
    assert donation.stripe_customer_id == "cus_audit"
    with pytest.raises(billing.NoCustomer):
        await billing.open_portal(session, other, gateway)
    assert gateway.create_portal_session.await_count == 1
    assert (await session.execute(select(m.Subscription))).scalars().all() == []


async def test_anonymous_donation_customer_is_not_claimed_by_an_account(session):
    user = m.User(email="visitor@example.test", email_verified=True)
    session.add(user)
    await session.flush()
    donation = await donation_for(session)
    await billing.handle_event(session, event("checkout.session.completed", donation))
    assert donation.stripe_customer_id == "cus_audit"
    assert await billing.customer_id_for(session, user) is None


async def test_legacy_subscription_customer_still_opens_portal(session):
    user = m.User(email="legacy@example.test", email_verified=True)
    session.add(user)
    await session.flush()
    session.add(m.Subscription(user_id=user.id, plan_id="free", state="active",
                               stripe_customer_id="cus_legacy"))
    await session.flush()
    assert await billing.customer_id_for(session, user) == "cus_legacy"


@pytest.mark.parametrize("interval", ["once", "month"])
async def test_unpaid_completion_stays_pending_until_async_success(session, interval):
    donation = await donation_for(session, interval=interval)
    completed = event("checkout.session.completed", donation, payment_status="unpaid")
    await billing.handle_event(session, completed)
    assert donation.status == "pending"
    assert donation.stripe_customer_id == "cus_audit"
    succeeded = event("checkout.session.async_payment_succeeded", donation)
    assert (await billing.handle_event(session, succeeded)).status == "applied"
    assert donation.status == ("active" if interval == "month" else "paid")
    assert (await billing.handle_event(session, succeeded)).status == "duplicate"
    await session.commit()


@pytest.mark.parametrize("interval,expected", [("once", "pending"), ("month", "lapsed")])
async def test_async_failure_never_marks_unpaid_donation_paid(session, interval, expected):
    donation = await donation_for(session, interval=interval)
    await billing.handle_event(session, event("checkout.session.completed", donation,
                                              payment_status="unpaid"))
    failed = event("checkout.session.async_payment_failed", donation, payment_status="unpaid")
    assert (await billing.handle_event(session, failed)).status == "applied"
    assert donation.status == expected
    assert (await billing.handle_event(session, failed)).status == "duplicate"


@pytest.mark.parametrize("payment_status", [None, "no_payment_required", "unpaid"])
async def test_only_explicit_paid_status_confirms_payment(session, payment_status):
    donation = await donation_for(session, interval="once")
    completed = event("checkout.session.completed", donation, mode="payment", subscription=None,
                      payment_status=payment_status)
    if payment_status is None:
        completed["data"]["object"].pop("payment_status")
    await billing.handle_event(session, completed)
    assert donation.status == "pending"


@pytest.mark.parametrize("kind", ["invoice.paid", "invoice.payment_failed",
                                  "checkout.session.completed",
                                  "checkout.session.async_payment_succeeded",
                                  "checkout.session.async_payment_failed"])
async def test_canceled_subscription_is_terminal_for_late_events(session, kind):
    donation = await donation_for(session, status="active")
    await billing.handle_event(session, event("customer.subscription.deleted", donation))
    assert donation.status == "canceled"
    await billing.handle_event(session, event(kind, donation))
    assert donation.status == "canceled"


async def test_concurrent_late_invoice_cannot_overwrite_cancellation(session, engine):
    donation = await donation_for(session, status="lapsed")
    await session.commit()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as deleting, factory() as late:
        # A preloaded identity must also be refreshed after acquiring the lock.
        stale = await late.get(m.Donation, donation.id)
        assert stale.status == "lapsed"
        await billing.handle_event(deleting, event("customer.subscription.deleted", donation))
        paid = event("invoice.paid", donation)

        async def deliver_late():
            await billing.handle_event(late, paid)
            await late.commit()

        pending = asyncio.create_task(deliver_late())
        try:
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(pending), timeout=0.05)
            await deleting.commit()
            await asyncio.wait_for(pending, timeout=3)
        finally:
            if not pending.done():
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
    await session.refresh(donation)
    assert donation.status == "canceled"


async def test_failed_event_transaction_can_be_retried(session, engine):
    donation = await donation_for(session)
    await session.commit()
    incoming = event("checkout.session.completed", donation)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as failed:
        assert (await billing.handle_event(failed, incoming)).status == "applied"
        await failed.rollback()
    async with factory() as retry:
        assert (await billing.handle_event(retry, incoming)).status == "applied"
        await retry.commit()


@pytest.mark.parametrize("mode", ["payment", "subscription"])
async def test_live_checkout_customer_creation_parameter_without_network(monkeypatch, mode):
    create = AsyncMock(return_value=SimpleNamespace(id="cs_fake", url="https://checkout.test"))
    fake_client = SimpleNamespace(v1=SimpleNamespace(
        checkout=SimpleNamespace(sessions=SimpleNamespace(create_async=create))))
    monkeypatch.setattr(billing.stripe, "StripeClient", lambda _: fake_client)
    gateway = billing.LiveStripe("not-a-real-key")
    await gateway.create_checkout_session(
        mode=mode, price_data={"currency": "usd", "unit_amount": 1000},
        client_reference_id="usr_own", customer_email="donor@example.test",
        success_url=billing.CHECKOUT_SUCCESS_URL, cancel_url=billing.CHECKOUT_CANCEL_URL,
        metadata={"donation_id": "don_fake"})
    params = create.await_args.kwargs["params"]
    if mode == "payment":
        assert params["customer_creation"] == "always"
    else:
        assert "customer_creation" not in params
        assert params["subscription_data"]["metadata"]["donation_id"] == "don_fake"


async def test_donation_customer_migration_round_trip_preserves_donation(session, database_url):
    donation = await donation_for(session)
    malformed = await donation_for(session)
    ambiguous = await donation_for(session)
    unrelated = await donation_for(session)
    anonymous = await donation_for(session)
    for row, customer in [(donation, "cus_historical"), (malformed, {"id": "cus_expanded"}),
                          (ambiguous, "cus_one"), (ambiguous, "cus_two"),
                          (unrelated, "cus_wrong"), (anonymous, "cus_anonymous")]:
        incoming = event("checkout.session.completed", row, customer=customer)
        if row is unrelated:
            incoming["data"]["object"]["metadata"]["donation_id"] = "don_other"
        session.add(m.StripeEvent(id=incoming["id"], type=incoming["type"], payload=incoming,
                                  processed_at=dt.datetime.now(dt.UTC)))
    # Arbitrary or incomplete historical JSON must not make migration fail.
    session.add(m.StripeEvent(id="evt_malformed", type="checkout.session.completed",
                              payload={"data": ["unexpected"]},
                              processed_at=dt.datetime.now(dt.UTC)))
    await session.commit()
    api_dir = Path(__file__).resolve().parents[1]
    env = {**os.environ, "DATABASE_URL": database_url}

    async def migrate(*args):
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "alembic", *args, cwd=api_dir, env=env,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await process.communicate()
        assert process.returncode == 0, (out + err).decode()

    await migrate("downgrade", "f6a7b8c9d0e1")
    columns = (await session.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='donations'"
    ))).scalars().all()
    assert "stripe_customer_id" not in columns
    assert (await session.execute(text("SELECT amount_usd FROM donations WHERE id=:id"),
                                  {"id": donation.id})).scalar_one() == Decimal("10")
    await session.rollback()
    await migrate("upgrade", "head")
    await session.refresh(donation)
    assert donation.amount_usd == Decimal("10")
    assert donation.stripe_customer_id == "cus_historical"
    for row in (malformed, ambiguous, unrelated):
        await session.refresh(row)
        assert row.stripe_customer_id is None
    await session.refresh(anonymous)
    assert anonymous.stripe_customer_id == "cus_anonymous"
    assert anonymous.user_id is None
    version = (await session.execute(text("SELECT version_num FROM alembic_version"))).scalar_one()
    assert version == "a7b8c9d0e1f2"
