# api/tests/test_ledger.py
"""The ledger and the one place a quota is enforced.

Every test here is written from the side that costs something: a row that
silently became a float, a model with no price that gets billed anyway, a
failed verify gate the user is charged for, a quota that lets one more through
than the plan sold. Component 15 §9's acceptance bar is these, not a smoke test.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy import select

from explorer_api import ledger, models as m, plans
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes import usage as usage_routes
from explorer_api.settings import Settings

MILLION = 1_000_000


async def _user(session, plan_id: str = "free") -> m.User:
    u = m.User(email=f"u-{uuid4().hex[:10]}@example.test", plan_id=plan_id)
    session.add(u)
    await session.flush()
    return u


# --- record() ----------------------------------------------------------------


async def test_record_prices_a_row_off_the_published_price_list(session):
    """15 §3: mxbai embeddings cost ≈$0.02/1M and are sold at $0.10/1M."""
    user = await _user(session)
    row = await ledger.record(session, user, component="17", kind="embedding",
                              model="mxbai-embed-large", units=MILLION)
    await session.commit()
    assert row.unit_cost_usd == Decimal("0.02")
    assert row.price_usd == Decimal("0.10")
    assert row.billable is True


async def test_money_is_decimal_at_six_places_never_float(session):
    user = await _user(session)
    await ledger.record(session, user, component="02", kind="input",
                        model="qwen3.5:35b", units=123_456)
    await session.commit()
    got = (await session.execute(select(m.LedgerEntry))).scalar_one()
    for value in (got.unit_cost_usd, got.price_usd):
        assert isinstance(value, Decimal) and not isinstance(value, float)
        assert -value.as_tuple().exponent <= 6
    # 123,456 tokens at $0.50/1M, exactly, with no binary-float residue.
    assert got.price_usd == Decimal("0.061728")


async def test_a_price_row_in_postgres_overrides_the_default(session):
    """15 §3: the price list is "owner-tunable in Postgres" — data, not a deploy."""
    user = await _user(session)
    session.add(m.Price(model="mxbai-embed-large", kind="embedding",
                        unit_cost_usd=Decimal("0.03"), price_usd=Decimal("0.30")))
    await session.flush()
    row = await ledger.record(session, user, component="17", kind="embedding",
                              model="mxbai-embed-large", units=MILLION)
    await session.commit()
    assert row.price_usd == Decimal("0.30")


async def test_only_the_price_in_force_is_used(session):
    """A future price does not apply today; the newest past one does."""
    user = await _user(session)
    today = dt.date.today()
    session.add_all([
        m.Price(model="qwen3.5:35b", kind="input", unit_cost_usd=Decimal("0.10"),
                price_usd=Decimal("0.40"), effective_from=today - dt.timedelta(days=30)),
        m.Price(model="qwen3.5:35b", kind="input", unit_cost_usd=Decimal("0.10"),
                price_usd=Decimal("0.60"), effective_from=today - dt.timedelta(days=1)),
        m.Price(model="qwen3.5:35b", kind="input", unit_cost_usd=Decimal("0.10"),
                price_usd=Decimal("9.99"), effective_from=today + dt.timedelta(days=7)),
    ])
    await session.flush()
    row = await ledger.record(session, user, component="02", kind="input",
                              model="qwen3.5:35b", units=MILLION)
    assert row.price_usd == Decimal("0.60")


async def test_an_unpriced_model_refuses_to_write_a_row(session):
    """Better a loud failure than a job billed at zero, or at a guess."""
    user = await _user(session)
    with pytest.raises(ledger.UnknownPrice) as exc:
        await ledger.record(session, user, component="01", kind="input",
                            model="claude-opus-4-8", units=1000)
    assert "claude-opus-4-8" in str(exc.value)
    assert (await session.execute(select(m.LedgerEntry))).first() is None


async def test_a_failed_verify_gate_is_recorded_and_not_billed(session):
    """15 §8 / master §5: the user does not pay for work they cannot use."""
    user = await _user(session)
    row = await ledger.record(session, user, component="01", kind="output",
                              model="qwen3.5:35b", units=MILLION,
                              billable=False, reason="verify")
    await session.commit()
    assert row.billable is False and row.reason == "verify"
    assert row.price_usd == Decimal("0.50")          # the cost is still recorded…
    summary = await ledger.usage(session, user)
    assert summary.billable_usd == Decimal("0")      # …it is simply not charged
    assert summary.total_usd == Decimal("0.50")


async def test_a_row_can_be_tied_to_the_job_or_the_call_that_caused_it(session):
    user = await _user(session)
    job = m.Job(user_id=user.id, kind="index", status="running")
    session.add(job)
    await session.flush()
    row = await ledger.record(session, user, component="13", kind="embedding",
                              model="mxbai-embed-large", units=10_000,
                              job=job, call_id="mcp_abc", reason="query")
    await session.commit()
    assert row.job_id == job.id and row.call_id == "mcp_abc"


# --- check_quota() -----------------------------------------------------------


async def test_a_counter_at_its_limit_stops_with_an_upgrade_url(session):
    """Free gets one private tree (15 §5). The second is refused, not billed."""
    user = await _user(session)
    session.add(m.Tree(user_id=user.id, slug="me", forked_from_sha="a" * 40,
                       path=f"trees/{user.id}/tree.json"))
    await session.flush()
    verdict = await ledger.check_quota(session, user, "private_trees")
    assert verdict.allowed is False
    assert verdict.tier == "free" and verdict.limit == 1 and verdict.remaining == 0
    assert verdict.upgrade_url and "starter" in verdict.upgrade_url


async def test_a_counter_below_its_limit_allows_and_reports_what_is_left(session):
    user = await _user(session)
    verdict = await ledger.check_quota(session, user, "private_trees")
    assert verdict.allowed is True and verdict.remaining == 1


async def test_an_unlimited_quota_allows_without_counting(session):
    user = await _user(session, plan_id="starter")
    verdict = await ledger.check_quota(session, user, "lint_per_day", amount=10_000)
    assert verdict.allowed is True
    assert verdict.limit is None and verdict.remaining is None
    assert verdict.upgrade_url is None


async def test_a_daily_counter_only_counts_today(session):
    """200 keyword queries/day on free — yesterday's are not today's problem."""
    user = await _user(session)
    now = dt.datetime.now(dt.UTC)
    for at in (now - dt.timedelta(days=1), now):
        await ledger.record(session, user, component="13", kind="input",
                            model="qwen3.5:35b", units=0, reason="query", at=at)
    await session.flush()
    verdict = await ledger.check_quota(session, user, "keyword_queries_per_day")
    assert verdict.used == 1 and verdict.remaining == 199 and verdict.allowed is True


async def test_a_flag_feature_is_refused_on_the_plan_that_lacks_it(session):
    free = await _user(session)
    starter = await _user(session, plan_id="starter")
    refused = await ledger.check_quota(session, free, "publish")
    assert refused.allowed is False and "starter" in (refused.upgrade_url or "")
    assert (await ledger.check_quota(session, starter, "publish")).allowed is True


async def test_the_free_tier_semantic_demo_is_not_a_metered_allowance(session):
    """D7: free semantic search is the 16-doc demo, rate-limited and not billed."""
    user = await _user(session)
    verdict = await ledger.check_quota(session, user, "semantic_queries")
    assert verdict.allowed is False and verdict.limit == "demo-only"
    assert (await ledger.check_quota(
        session, await _user(session, plan_id="pro"), "semantic_queries")).allowed is True


async def test_a_size_cap_is_checked_against_the_amount_asked_for(session):
    """Free lints files ≤ 64 KB; the 65th kilobyte is a 402, not a truncation."""
    user = await _user(session)
    assert (await ledger.check_quota(session, user, "lint_max_bytes",
                                     amount=64 * 1024)).allowed is True
    over = await ledger.check_quota(session, user, "lint_max_bytes", amount=64 * 1024 + 1)
    assert over.allowed is False and over.limit == 65536


async def test_a_feature_postgres_cannot_count_refuses_to_guess(session):
    """Docset counts live in the per-user store, not here (master §5). Asking
    without the count must fail loudly rather than allow everything."""
    user = await _user(session)
    with pytest.raises(ledger.UncountableFeature):
        await ledger.check_quota(session, user, "indexes")
    ok = await ledger.check_quota(session, user, "indexes", used=0)
    assert ok.allowed is True and ok.remaining == 1


async def test_an_unknown_feature_is_an_error(session):
    user = await _user(session)
    with pytest.raises(plans.UnknownFeature):
        await ledger.check_quota(session, user, "free_lunch")


# --- aggregates --------------------------------------------------------------


async def test_usage_aggregates_by_day_component_and_model(session):
    user = await _user(session)
    now = dt.datetime.now(dt.UTC)
    yesterday = now - dt.timedelta(days=1)
    await ledger.record(session, user, component="17", kind="embedding",
                        model="mxbai-embed-large", units=MILLION, at=yesterday)
    await ledger.record(session, user, component="17", kind="embedding",
                        model="mxbai-embed-large", units=MILLION, at=now)
    await ledger.record(session, user, component="02", kind="input",
                        model="qwen3.5:35b", units=MILLION, at=now)
    await session.commit()

    summary = await ledger.usage(session, user)
    assert len(summary.rows) == 3
    assert {(r.component, r.model) for r in summary.rows} == {
        ("17", "mxbai-embed-large"), ("02", "qwen3.5:35b")}
    assert summary.total_usd == Decimal("0.70")

    today_only = await ledger.usage(session, user, since=now.date())
    assert len(today_only.rows) == 2 and today_only.total_usd == Decimal("0.60")


async def test_usage_only_ever_sees_one_users_rows(session):
    mine, theirs = await _user(session), await _user(session)
    await ledger.record(session, theirs, component="17", kind="embedding",
                        model="mxbai-embed-large", units=MILLION)
    await session.commit()
    assert (await ledger.usage(session, mine)).rows == []


async def test_the_credit_balance_is_zero_until_stripe_says_otherwise(session):
    user = await _user(session)
    assert await ledger.credit_balance(session, user) == Decimal("0")
    session.add(m.Credit(user_id=user.id, balance_usd=Decimal("10")))
    await session.flush()
    assert await ledger.credit_balance(session, user) == Decimal("10")


# --- GET /api/usage ----------------------------------------------------------


@pytest_asyncio.fixture
async def app_and_user(session, database_url):
    settings = Settings(
        database_url=SecretStr(database_url),
        session_secret=SecretStr("s" * 32),
        stripe_secret_key=SecretStr("sk_test_x"),
        stripe_webhook_secret=SecretStr("whsec_x"),
    )
    app = create_app(settings)
    app.include_router(usage_routes.router)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    user = await _user(session)
    yield app, user


@pytest_asyncio.fixture
async def client(app_and_user):
    app, user = app_and_user
    app.dependency_overrides[usage_routes.get_current_user] = lambda: user
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_usage_endpoint_returns_the_aggregate_and_the_balance(
    session, app_and_user, client
):
    _, user = app_and_user
    await ledger.record(session, user, component="17", kind="embedding",
                        model="mxbai-embed-large", units=MILLION)
    await session.commit()
    body = (await client.get("/api/usage")).json()
    assert body["total_usd"] == "0.100000"
    assert body["credit_balance_usd"] == "-0.100000"
    assert body["rows"][0]["component"] == "17"
    assert body["rows"][0]["units"] == MILLION


async def test_usage_endpoint_honours_the_from_and_to_window(
    session, app_and_user, client
):
    _, user = app_and_user
    old = dt.datetime.now(dt.UTC) - dt.timedelta(days=10)
    await ledger.record(session, user, component="17", kind="embedding",
                        model="mxbai-embed-large", units=MILLION, at=old)
    await session.commit()
    today = dt.date.today().isoformat()
    assert (await client.get(f"/api/usage?from={today}")).json()["rows"] == []
    windowed = await client.get(f"/api/usage?from={old.date()}&to={old.date()}")
    assert len(windowed.json()["rows"]) == 1


async def test_usage_endpoint_is_401_without_a_signed_in_user(app_and_user):
    app, _ = app_and_user
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        assert (await c.get("/api/usage")).status_code == 401
