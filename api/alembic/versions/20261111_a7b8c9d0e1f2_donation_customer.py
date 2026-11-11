"""Persist donation-owned Stripe customers for the Customer Portal.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("donations", sa.Column("stripe_customer_id", sa.Text(), nullable=True))
    # The webhook stored verified events before the old handler lost customer
    # IDs. Recover only an exact checkout-session match with a single customer.
    # Conflicting metadata, malformed customers and ambiguous matches stay NULL;
    # anonymous donations keep their existing NULL user_id.
    op.execute("""
        WITH customer_matches AS (
            SELECT d.id, min(e.payload #>> '{data,object,customer}') AS customer_id
            FROM donations AS d
            JOIN stripe_events AS e
              ON e.payload #>> '{data,object,id}' = d.stripe_checkout_session_id
            WHERE e.type = 'checkout.session.completed'
              AND e.processed_at IS NOT NULL
              AND jsonb_typeof(e.payload #> '{data,object,id}') = 'string'
              AND jsonb_typeof(e.payload #> '{data,object,customer}') = 'string'
              AND e.payload #>> '{data,object,customer}' <> ''
              AND (e.payload #>> '{data,object,metadata,donation_id}' IS NULL
                   OR e.payload #>> '{data,object,metadata,donation_id}' = d.id)
            GROUP BY d.id
            HAVING count(DISTINCT e.payload #>> '{data,object,customer}') = 1
        )
        UPDATE donations AS d
        SET stripe_customer_id = matches.customer_id
        FROM customer_matches AS matches
        WHERE d.id = matches.id AND d.stripe_customer_id IS NULL
    """)


def downgrade() -> None:
    op.drop_column("donations", "stripe_customer_id")
