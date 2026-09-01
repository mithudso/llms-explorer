"""subscribers

Adds the ``subscribers`` table for the blog change-notice mailing list: an
email address, a double opt-in confirmation token, and a one-click unsubscribe
token. Not part of the master plan's numbered components — a small standalone
subsystem alongside it.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscribers",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("confirm_token", sa.Text(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unsubscribe_token", sa.Text(), nullable=False),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscribers")),
    )
    op.create_index(op.f("ix_subscribers_email"), "subscribers", ["email"], unique=True)
    op.create_index(op.f("ix_subscribers_confirm_token"), "subscribers",
                     ["confirm_token"], unique=True)
    op.create_index(op.f("ix_subscribers_unsubscribe_token"), "subscribers",
                     ["unsubscribe_token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_subscribers_unsubscribe_token"), table_name="subscribers")
    op.drop_index(op.f("ix_subscribers_confirm_token"), table_name="subscribers")
    op.drop_index(op.f("ix_subscribers_email"), table_name="subscribers")
    op.drop_table("subscribers")
