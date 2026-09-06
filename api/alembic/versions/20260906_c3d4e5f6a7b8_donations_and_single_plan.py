# api/alembic/versions/20260906_c3d4e5f6a7b8_donations_and_single_plan.py
"""donations and single plan

Collapses the plan table to `free` only (donations design §1) and adds
`donations` for Stripe-recorded one-time/monthly support.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-06 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Any account still on starter/pro moves to free before the rows they
    # reference are deleted — plan_id is `ForeignKey("plans.id", ondelete="RESTRICT")`,
    # so deleting a referenced row would fail outright rather than silently orphan one.
    op.execute("UPDATE users SET plan_id = 'free' WHERE plan_id != 'free'")
    op.execute("DELETE FROM plans WHERE id != 'free'")

    op.drop_constraint(op.f("ck_plans_plans_id"), "plans", type_="check")
    op.create_check_constraint(op.f("ck_plans_plans_id"), "plans", "id IN ('free')")

    op.create_table(
        "donations",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_usd", sa.Numeric(12, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="usd"),
        sa.Column("interval", sa.String(8), nullable=False),
        sa.Column("stripe_checkout_session_id", sa.Text(), nullable=True),
        sa.Column("stripe_subscription_id", sa.Text(), nullable=True, unique=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint("interval IN ('once', 'month')", name="donations_interval"),
        sa.CheckConstraint(
            "status IN ('pending', 'paid', 'active', 'lapsed', 'canceled')",
            name="donations_status",
        ),
    )
    op.create_index("ix_donations_user_id", "donations", ["user_id"])
    op.create_index(
        "ix_donations_stripe_checkout_session_id", "donations",
        ["stripe_checkout_session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_donations_stripe_checkout_session_id", table_name="donations")
    op.drop_index("ix_donations_user_id", table_name="donations")
    op.drop_table("donations")
    op.drop_constraint(op.f("ck_plans_plans_id"), "plans", type_="check")
    op.create_check_constraint(
        op.f("ck_plans_plans_id"), "plans", "id IN ('free', 'starter', 'pro')"
    )
    # starter/pro rows are not re-seeded on downgrade — a downgrade here is for
    # rolling back a broken deploy within minutes, not for restoring commercial
    # plan data, which lives in the original migration if that is ever needed.
