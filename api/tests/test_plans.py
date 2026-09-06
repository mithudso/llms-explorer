# api/tests/test_plans.py
"""`plans.PLANS` is the single free plan every account gets (donations design §1).

Numbers here must match `docs/site/components/15-accounts-and-billing.md` §5's
one remaining row exactly — there is one plan now, so this is a direct
assertion rather than a markdown-table parser (see git history before
2026-09-06 for the three-plan version, which this replaced)."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

from explorer_api import models as m
from explorer_api import plans


def test_the_free_plan_has_todays_free_tier_quotas():
    free = plans.get("free")
    assert free.price_usd == Decimal("0")
    assert free.included_credit_usd == Decimal("0")
    assert free.quotas == {
        "lint_max_bytes": 65536,
        "lint_per_day": 20,
        "lint_model_passes": False,
        "keyword_queries_per_day": 200,
        "semantic_queries": "demo-only",
        "indexes": 1,
        "index_max_units": 20000,
        "storage_gb": Decimal("0.2"),
        "corpus_max_tokens": 25000,
        "corpus_per_day": 5,
        "private_trees": 1,
        "publish": False,
        "overage": False,
    }


def test_plan_order_is_just_free():
    assert plans.PLAN_ORDER == ("free",)
    assert list(plans.PLANS) == ["free"]


def test_every_quota_feature_is_classified():
    assert set(plans.QUOTA_FEATURES) == set(plans.FEATURE_KINDS)


def test_an_unknown_plan_is_an_error_not_a_default():
    with pytest.raises(plans.UnknownPlan):
        plans.get("starter")


def test_quota_reads_a_feature_off_the_plan():
    assert plans.quota("free", "lint_per_day") == 20


def test_an_unknown_feature_is_an_error_not_none():
    with pytest.raises(plans.UnknownFeature):
        plans.quota("free", "not_a_real_feature")


async def test_the_seeded_row_matches_the_module(session):
    row = await session.get(m.Plan, "free")
    assert row is not None
    plan = plans.get("free")
    assert Decimal(row.price_usd) == plan.price_usd
    assert Decimal(row.included_credit_usd) == plan.included_credit_usd
    seeded = dict(row.quotas)
    for feature, value in plan.quotas.items():
        got = seeded[feature]
        if isinstance(value, Decimal):
            got = Decimal(str(got))
        assert got == value, f"free.{feature}: db {got!r} != code {value!r}"


async def test_no_other_plan_rows_exist(session):
    rows = (await session.execute(select(m.Plan.id))).scalars().all()
    assert rows == ["free"]
