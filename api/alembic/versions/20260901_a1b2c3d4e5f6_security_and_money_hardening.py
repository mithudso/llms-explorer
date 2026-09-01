"""security and money hardening

What this migration exists for, one item per confirmed defect:

* ``users.pending_email`` — a passkey sign-up types an address into an
  *unauthenticated* request body. Storing that in ``users.email`` made it a row
  a later, genuinely verified OAuth sign-in would merge into, handing the
  attacker the victim's account. Claimed addresses now live here and are never
  merged on.
* ``users.session_epoch`` — the session cookie is a stateless signature, so
  before this there was no way to revoke one. The epoch is signed into the
  token; bumping it logs every device out.
* ``users.overage_opt_in`` — 15 §5 makes overage "opt-in", which needs somewhere
  to store the opt. Without it "opt-in" read as "always yes".
* ``ledger.api_key_id`` — 15 §10's per-key ``max_usd_day`` cap cannot be summed
  without knowing which key spent a row.
* ``ledger.client_ip`` — 15 §9 enforces the free-tier ceilings "per user **and**
  per IP".
* ``credit_grants`` — invoice-level idempotency for the monthly included credit.
  ``stripe_events`` only dedupes an event id, so a resent invoice under a new
  event id granted the credit twice.
* the ``BEFORE TRUNCATE`` trigger — a row-level trigger cannot fire for
  TRUNCATE, so "append-only" was erasable in one statement.

Revision ID: a1b2c3d4e5f6
Revises: 23eeb106db35
Create Date: 2026-09-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from explorer_api.models import LEDGER_APPEND_ONLY_SQL

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "23eeb106db35"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("pending_email", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("session_epoch", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("overage_opt_in", sa.Boolean(), server_default="false", nullable=False),
    )

    op.add_column("ledger", sa.Column("api_key_id", sa.Text(), nullable=True))
    op.add_column("ledger", sa.Column("client_ip", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_ledger_api_key_id_api_keys"),
        "ledger", "api_keys", ["api_key_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_ledger_api_key_id_at", "ledger", ["api_key_id", "at"])
    op.create_index("ix_ledger_client_ip_at", "ledger", ["client_ip", "at"])
    op.create_index(op.f("ix_ledger_api_key_id"), "ledger", ["api_key_id"])

    op.create_table(
        "credit_grants",
        sa.Column("invoice_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("subscription_id", sa.Text(), nullable=True),
        sa.Column("amount_usd", sa.Numeric(12, 6), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"],
                                name=op.f("fk_credit_grants_subscription_id_subscriptions"),
                                ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name=op.f("fk_credit_grants_user_id_users"),
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("invoice_id", name=op.f("pk_credit_grants")),
    )
    op.create_index(op.f("ix_credit_grants_user_id"), "credit_grants", ["user_id"])

    # Re-run the whole append-only block: it is CREATE OR REPLACE / DROP IF
    # EXISTS throughout, so replaying it is what installs the TRUNCATE guard
    # alongside the row-level one without the two definitions ever drifting.
    for statement in LEDGER_APPEND_ONLY_SQL:
        op.execute(statement)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS ledger_append_only_truncate ON ledger")
    op.drop_index(op.f("ix_credit_grants_user_id"), table_name="credit_grants")
    op.drop_table("credit_grants")
    op.drop_index(op.f("ix_ledger_api_key_id"), table_name="ledger")
    op.drop_index("ix_ledger_client_ip_at", table_name="ledger")
    op.drop_index("ix_ledger_api_key_id_at", table_name="ledger")
    op.drop_constraint(op.f("fk_ledger_api_key_id_api_keys"), "ledger", type_="foreignkey")
    op.drop_column("ledger", "client_ip")
    op.drop_column("ledger", "api_key_id")
    op.drop_column("users", "overage_opt_in")
    op.drop_column("users", "session_epoch")
    op.drop_column("users", "pending_email")
