# api/tests/test_migrations.py
"""The 2026-09-06 migration: exactly one plan row survives, and `donations` exists."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from explorer_api import models as m


async def test_only_the_free_plan_row_exists_after_migration(session):
    rows = (await session.execute(select(m.Plan.id))).scalars().all()
    assert rows == ["free"]


async def test_users_plan_id_check_constraint_only_allows_free(session):
    user = m.User(email="constraint-check@example.test", email_verified=True)
    session.add(user)
    await session.flush()
    with pytest.raises(Exception):  # IntegrityError, driver-specific text
        await session.execute(
            m.User.__table__.update().where(m.User.id == user.id).values(plan_id="starter")
        )


async def test_the_donations_table_accepts_a_one_time_row(session):
    donation = m.Donation(
        amount_usd="25.000000", currency="usd", interval="once",
        stripe_checkout_session_id="cs_test_migration_check", status="pending",
    )
    session.add(donation)
    await session.flush()
    assert donation.id.startswith("don_")
