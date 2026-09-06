# api/alembic/versions/20260906_d4e5f6a7b8c9_backfill_free_plan_corpus_quotas.py
"""backfill free plan corpus quotas

The original seed migration (20260831_23eeb106db35) never included
`corpus_max_tokens`/`corpus_per_day` in the `free` plan's `quotas` JSONB —
those keys were added to `explorer_api.plans.QUOTA_FEATURES` for corpus
synthesis (component 19) after that migration was written, and nothing ever
backfilled the seeded row. `plans.quota()` reads the in-memory `PLANS` dict,
not the DB row, so this never broke production; it was caught by
`tests/test_plans.py::test_the_seeded_row_matches_the_module`, which compares
the two directly.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-06 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE plans SET quotas = quotas || "
        "'{\"corpus_max_tokens\": 25000, \"corpus_per_day\": 5}'::jsonb "
        "WHERE id = 'free'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE plans SET quotas = quotas - 'corpus_max_tokens' - 'corpus_per_day' "
        "WHERE id = 'free'"
    )
