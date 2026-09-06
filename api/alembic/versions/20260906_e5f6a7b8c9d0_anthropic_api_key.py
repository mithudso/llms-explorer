# api/alembic/versions/20260906_e5f6a7b8c9d0_anthropic_api_key.py
"""anthropic api key

Adds the two columns a caller's own, encrypted Anthropic key lives in
(donations design follow-up: bring-your-own-key for the hosted skills).

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-06 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("anthropic_api_key_ciphertext", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("anthropic_api_key_hint", sa.String(4), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "anthropic_api_key_hint")
    op.drop_column("users", "anthropic_api_key_ciphertext")
