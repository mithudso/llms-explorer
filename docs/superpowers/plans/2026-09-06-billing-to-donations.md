# Billing → Donations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the three-tier plan/billing system (Free/Starter/Pro) to a single free plan for every account, and replace paid checkout with a Stripe-powered one-time-or-monthly donation.

**Architecture:** `api/explorer_api/plans.py` keeps exactly one `Plan` row (`free`) with today's Free-tier quotas, applied to every account. `api/explorer_api/billing.py` keeps its webhook idempotency/signature machinery and the Customer Portal (a donor can still manage/cancel a recurring donation there) but loses all plan-entitlement logic (nothing is a "plan you're on" anymore) and gains a `Donation` record + a checkout function that builds its Stripe price inline (`price_data`), since a donation amount is never one of a fixed set of pre-created Prices. A new `routes/donate.py` replaces the plan-purchasing half of `routes/billing.py`; the webhook route stays where it is since it isn't donation-specific. On the site, `/billing/` is deleted and a new `/donate/` page takes its place in the nav.

**Tech Stack:** FastAPI, SQLAlchemy 2 + Alembic (existing `api/` stack, unchanged), Astro (existing `site/` stack, unchanged).

**Authority:** `docs/superpowers/plans/2026-09-06-donations-and-community-directory-design.md` §1 (Part A).

---

## Global notes for every task

- Python: `hub/.venv/bin/python`, run from `api/` unless noted. Tests: `hub/.venv/bin/python -m pytest tests/<file> -q` from `api/`.
- Site: `npm run build` from `site/`, tests via `hub/.venv/bin/python -m pytest site/tests -q` from the repo root.
- Never commit `api/.env`. Never run `git push --force`. One commit per task.
- `Credit`, `CreditGrant`, and `explorer_api.ledger`'s spend-tracking are **out of scope** — they're separable from the tier system per the design doc and untouched here. Only the plan-*entitlement* machinery (which subscription state maps to which `user.plan_id`) is removed, because with one plan there is nothing to switch to.

---

### Task 1: Migration — one plan, plus the `donations` table

**Files:**
- Create: `api/alembic/versions/20260906_c3d4e5f6a7b8_donations_and_single_plan.py`
- Test: `api/tests/test_migrations.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_migrations.py
"""The 2026-09-06 migration: exactly one plan row survives, and `donations` exists."""
from __future__ import annotations

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
```

Add the missing `import pytest` at the top of the new test file alongside the existing imports.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && hub/../.venv/bin/python -m pytest tests/test_migrations.py -q` (use `.venv/bin/python -m pytest tests/test_migrations.py -q` from `api/`)
Expected: FAIL — `AttributeError: module 'explorer_api.models' has no attribute 'Donation'` (Task 2 hasn't run yet) and the migration doesn't exist yet either. This step exists to record the target behavior before Task 2's model and this task's migration are written; it will only truly pass once both are in place, so don't chase a clean fail message here — just confirm it errors, not passes.

- [ ] **Step 3: Write the migration**

```python
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

    op.drop_constraint("ck_plans_plans_id", "plans", type_="check")
    op.create_check_constraint("ck_plans_plans_id", "plans", "id IN ('free')")

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
        sa.CheckConstraint("interval IN ('once', 'month')", name="ck_donations_interval"),
        sa.CheckConstraint(
            "status IN ('pending', 'paid', 'active', 'lapsed', 'canceled')",
            name="ck_donations_status",
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
    op.drop_constraint("ck_plans_plans_id", "plans", type_="check")
    op.create_check_constraint(
        "ck_plans_plans_id", "plans", "id IN ('free', 'starter', 'pro')"
    )
    # starter/pro rows are not re-seeded on downgrade — a downgrade here is for
    # rolling back a broken deploy within minutes, not for restoring commercial
    # plan data, which lives in the original migration if that is ever needed.
```

- [ ] **Step 4: Run the migration and the test**

```bash
cd api
set -a && . ./.env && set +a
.venv/bin/alembic upgrade head
.venv/bin/python -m pytest tests/test_migrations.py -q
```
Expected: `alembic upgrade head` runs cleanly (still fails at Step 2's `test_the_donations_table_accepts_a_one_time_row` until Task 2 adds the `Donation` model — that's expected here; re-run this exact command again after Task 2). `test_only_the_free_plan_row_exists_after_migration` and `test_users_plan_id_check_constraint_only_allows_free` should PASS now.

- [ ] **Step 5: Commit**

```bash
git add api/alembic/versions/20260906_c3d4e5f6a7b8_donations_and_single_plan.py api/tests/test_migrations.py
git commit -m "feat(api): migration collapsing plans to free-only, adding donations table"
```

---

### Task 2: `models.py` — `PLAN_IDS`, the `Donation` model

**Files:**
- Modify: `api/explorer_api/models.py:82` (`PLAN_IDS`), and near `api/explorer_api/models.py:315` (after `Price`, before the ledger section — `Donation` belongs with the other money-adjacent tables)
- Test: `api/tests/test_migrations.py` (already written in Task 1 — this task makes it pass)

- [ ] **Step 1: The failing test already exists**

`test_the_donations_table_accepts_a_one_time_row` from Task 1 currently fails with `AttributeError: module 'explorer_api.models' has no attribute 'Donation'`. Confirm:

```bash
cd api && .venv/bin/python -m pytest tests/test_migrations.py::test_the_donations_table_accepts_a_one_time_row -q
```
Expected: FAIL, `AttributeError`.

- [ ] **Step 2: Change `PLAN_IDS`**

In `api/explorer_api/models.py`, line 82:

```python
# before
PLAN_IDS = ("free", "starter", "pro")
# after
PLAN_IDS = ("free",)
```

- [ ] **Step 3: Add the `Donation` model**

Insert immediately after the `Price` class (after line 337, before the `# --- the ledger --------` comment) in `api/explorer_api/models.py`:

```python
DONATION_INTERVALS = ("once", "month")
DONATION_STATUSES = ("pending", "paid", "active", "lapsed", "canceled")


class Donation(Base):
    """A Stripe-recorded donation — one-time or monthly, account optional.

    `user_id` is nullable: a donation does not require signing in. `status`
    tracks the Stripe lifecycle (`pending` until `checkout.session.completed`,
    `active` while a monthly donation's subscription renews, `lapsed` on a
    failed renewal, `canceled` when the donor cancels via the Portal).
    """

    __tablename__ = "donations"
    __table_args__ = (
        _one_of("interval", DONATION_INTERVALS, "donations_interval"),
        _one_of("status", DONATION_STATUSES, "donations_status"),
    )

    id: Mapped[str] = _id("don")
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    amount_usd: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(String(3), default="usd", server_default="usd")
    interval: Mapped[str] = mapped_column(String(8))
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(Text, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(Text, unique=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending")
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )
```

Add `"Donation"`, `"DONATION_INTERVALS"`, `"DONATION_STATUSES"` to the `__all__` list at the bottom of the file (alphabetical, alongside the existing entries — `"Donation"` goes after `"Credit"`/`"CreditGrant"`, `"DONATION_INTERVALS"`/`"DONATION_STATUSES"` go near `"JOB_EVENT_KINDS"` alphabetically).

- [ ] **Step 4: Run the tests**

```bash
cd api
set -a && . ./.env && set +a
.venv/bin/alembic upgrade head   # re-run: Task 1's migration + this model must agree
.venv/bin/python -m pytest tests/test_migrations.py -q
```
Expected: all three tests in `test_migrations.py` PASS.

- [ ] **Step 5: Commit**

```bash
git add api/explorer_api/models.py
git commit -m "feat(api): Donation model, single-plan PLAN_IDS"
```

---

### Task 3: `plans.py` — collapse to one plan

**Files:**
- Modify: `api/explorer_api/plans.py` (wholesale rewrite of the seed table and removal of upgrade logic)
- Test: `api/tests/test_plans.py` (wholesale rewrite — the existing file parses a 3-column markdown table that no longer exists after Task 4)

This task and Task 4 (the spoke doc) must land together: `test_plans.py` reads `docs/site/components/15-accounts-and-billing.md` directly, so changing one without the other leaves the test unable to parse the file at all (not just wrong values — a `AssertionError: no table headed ... in ...` from `_table_rows`).

- [ ] **Step 1: Replace `plans.py`'s seed table and delete upgrade logic**

In `api/explorer_api/plans.py`:

```python
# before (lines 33-39)
#: Where a refused request sends the user. Path only up to the plan: the site
#: owns the page, this module owns which plan to name.
BILLING_URL = "https://llms-explorer.com/billing"

#: 15 §5 column order — also cheapest-first, which is what makes
#: :func:`upgrade_target` "the *cheapest* plan that lifts the limit".
PLAN_ORDER: tuple[str, ...] = ("free", "starter", "pro")

# after
#: One plan. The comment on `PLAN_ORDER` used to explain why order mattered
#: (cheapest-first, for `upgrade_target`); with one plan there is no order to
#: keep, and no upgrade target to find — the site is free, supported by
#: donations (`explorer_api.billing`), not a paid tier ladder.
PLAN_ORDER: tuple[str, ...] = ("free",)
```

```python
# before (lines 143-200, the PLANS mapping) — delete the "starter" and "pro"
# _plan(...) calls entirely, keeping only "free":
PLANS: Mapping[str, Plan] = {
    plan.id: plan
    for plan in (
        _plan(
            "free", "Free", price="0", credit="0",
            lint_max_bytes=65536,
            lint_per_day=20,
            lint_model_passes=False,
            keyword_queries_per_day=200,
            semantic_queries="demo-only",
            indexes=1,
            index_max_units=20000,
            storage_gb=Decimal("0.2"),
            corpus_max_tokens=25000,
            corpus_per_day=5,
            private_trees=1,
            publish=False,
            overage=False,
        ),
    )
}
```

```python
# delete entirely (lines 218-252): _is_better, upgrade_target, upgrade_url —
# nothing calls them once there is one plan.
```

Update `__all__` at the bottom: remove `"BILLING_URL"`, `"upgrade_target"`, `"upgrade_url"`.

- [ ] **Step 2: Rewrite `test_plans.py`**

Replace the entire file. The markdown-table parser (`_table_rows`, `_plan_header`, `_count`, `_bytes`, `_gigabytes`, `_flag`, `_lint_deterministic`, `_index_a_docset`, `_corpus`, and the tests built on them: `test_the_spoke_still_has_the_table_this_test_reads`, `test_the_plans_match_the_spoke`, `test_the_prices_match_the_spoke`, `test_the_margin_multiple_is_the_one_the_spoke_states`) existed to keep three plans' many numbers in sync with prose across two files. With one plan whose numbers change rarely and are reviewed as a diff either way, a direct assertion against the known values is simpler and no less safe — the drift the parser guarded against (a spoke edit landing without a code edit, or the reverse) still fails a review, it just fails as a wrong-looking diff instead of a parsed-table mismatch.

```python
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
```

- [ ] **Step 3: Run the test to verify it fails first, then passes**

```bash
cd api
.venv/bin/python -m pytest tests/test_plans.py -q
```
Before touching `plans.py` this would fail on `test_the_free_plan_has_todays_free_tier_quotas` (extra `starter`/`pro` keys in `PLANS`) — since Step 1 already made the code change, run this now and expect PASS on every test. If anything fails, the mismatch is between this file's hardcoded expectations and `plans.py`'s actual `PLANS["free"]` — compare them directly, don't guess.

- [ ] **Step 4: Run the full API test suite to catch every other caller of the deleted names**

```bash
cd api && .venv/bin/python -m pytest tests -q 2>&1 | tail -40
```
Expected: failures naming `plans.BILLING_URL`, `plans.upgrade_target`, or `plans.upgrade_url` — these are Task 6 (billing.py) and Task 7 (routes/billing.py)'s job to fix, not this task's. Confirm the *only* new failures are import/attribute errors in `billing.py`/`routes/billing.py`/their tests; anything else is a regression this task introduced and must be fixed before moving on.

- [ ] **Step 5: Commit**

```bash
git add api/explorer_api/plans.py api/tests/test_plans.py
git commit -m "feat(api): collapse plans.py to the single free plan"
```

---

### Task 4: The spoke doc — `15-accounts-and-billing.md` §5's table

**Files:**
- Modify: `docs/site/components/15-accounts-and-billing.md` (the §5 feature table, and §1's purpose statement)

Task 3's `test_plans.py` no longer parses this file, but the doc is still the design record referenced everywhere (`plans.py`'s own docstring, `docs/superpowers/plans/2026-09-06-donations-and-community-directory-design.md`'s "Authority" line) — leaving it describing three paid tiers after the code no longer has them is exactly the kind of doc/code drift this repo's own conventions (`docs/site/00-platform-design.md`) treat as a defect, not a nit.

- [ ] **Step 1: No test — this is a documentation-only change with no assertion to write**

(Per "No Placeholders," this is stated explicitly rather than silently skipped: some tasks genuinely have no test because there's no runtime behavior to assert against. Step 2 below is the whole task.)

- [ ] **Step 2: Edit the doc**

In `docs/site/components/15-accounts-and-billing.md`, replace the §5 feature table (the one starting `| Feature | Free | Starter ($9/mo) | Pro ($39/mo) | Metered unit |`) with a single-column version:

```markdown
| Feature | Free (every account) | Metered unit |
|---|---|---|
| Reference, blog, directory, public tree, 3D view | ✓ | — |
| Served llms files (`/d/ /m/ /t/`) | ✓ (public by design) | — |
| Lint, deterministic passes (01) | files ≤ 64 KB, 20/day | — |
| Lint, model passes P4/P8/P12 (01) | — | — |
| Keyword queries (13/17) | 200/day | — |
| Semantic / hybrid queries (13/17) | 16 demo only, rate-limited, not billed (D7) | — |
| Index a docset (13/17) | 1 index ≤ 20k units, 200 MB | — |
| Corpus synthesis (19) | 25k tokens/run, 5/day | — |
| Private trees (09) | 1 (fork) | — |
| Publish to shared catalogue (13) | — | — |
| Support the project | via donation, one-time or monthly — `/donate/` | — |
```

Also update §1's purpose paragraph. Replace:

```markdown
Let anyone read everything that is already public (reference, blog, tree, directory, served
llms files) for free, and charge — profitably — for the things that spend model tokens or GPU
time on the user's behalf: lint with model passes, notes→llms, concept packs, deepen runs,
semantic queries, indexing. One ledger records every token; Stripe turns the ledger into money.
```

with:

```markdown
The site is free — every account gets the same limits (§5's one column). It is supported by
voluntary donations (`/donate/`), one-time or monthly via Stripe, not by metered access. The
ledger still records every token spent (it is what makes usage visible on `/usage/`), but nothing
in this document gates a feature behind payment anymore.
```

- [ ] **Step 3: No command to run — verify by reading the diff**

```bash
git diff docs/site/components/15-accounts-and-billing.md
```
Expected: the table has one data column plus "Metered unit" (now always `—`, since nothing charges per-unit anymore — kept as a column rather than deleted so a future metered feature has somewhere to land without another table restructure), and §1 no longer says "charge — profitably."

- [ ] **Step 4: N/A**

- [ ] **Step 5: Commit**

```bash
git add docs/site/components/15-accounts-and-billing.md
git commit -m "docs(site): 15-accounts-and-billing reflects the single free plan"
```

---

### Task 5: `billing.py` — remove plan entitlement, add donation checkout + webhook handling

**Files:**
- Modify: `api/explorer_api/billing.py` (large — see the itemized deletions/additions below)
- Test: `api/tests/test_billing.py` (large rewrite)

This is the biggest task in the plan. Read it fully before starting — the deletions and additions are interdependent (e.g. `_bindable_subscription` is deleted because only `_handle_subscription` called it, and `_handle_subscription` is deleted because there is no plan to switch to).

**Delete entirely** (each is either plan-entitlement logic with nothing left to entitle, or was only called by something else being deleted):
`PlanNotPurchasable`, `PlanNotSellable`, `start_checkout`, `ACTIVE_STATES`, `TERMINAL_STATES`, `GRACE_STATES`, `CREDIT_GRANTING_BILLING_REASONS`, `FREE_PLAN`, `_subscription_by_ids` (kept, see below — not deleted), `_bindable_subscription`, `_plan_for_price`, `_price_id`, `_period_end` (kept, see below), `_has_live_subscription`, `_apply_plan`, `_handle_subscription`, `_grant_credit`, `apply_expired_downgrades`. Remove `from . import ... plans` (nothing left in this file reads `plans`).

**Keep unchanged:** `BillingError`, `SignatureInvalid`, `NoCustomer`, `CheckoutSession`, `StripeGateway` (protocol — but see the changed `create_checkout_session` signature below), `LiveStripe.create_portal_session`, `customer_id_for`, `open_portal`, `verify_event`, `EventOutcome`, `_object`, `_epoch_to_utc`, `_claim`, `handle_event`, `SIGNATURE_TOLERANCE_SECONDS`. `_period_end` is kept because a monthly donation's renewal still needs it.

**Change:** `StripeGateway.create_checkout_session` and `LiveStripe.create_checkout_session` — the only caller left (the new `create_donation_checkout`) builds an inline price, not a pre-created `price_id`.

**Add:** `Donation`-facing constants, `create_donation_checkout`, rewritten `_handle_checkout_completed`, `_handle_invoice_paid`, `_handle_payment_failed`.

- [ ] **Step 1: Write the failing tests**

Replace `api/tests/test_billing.py` in full:

```python
# api/tests/test_billing.py
"""Stripe: donation Checkout, the Customer Portal, and webhooks that cannot be replayed.

Three inherited guarantees, still tested here because they are still true and
still load-bearing: a replayed webhook changes nothing the second time, an
invalid signature is 400 and writes nothing, and the two outbound calls this
module makes go through `StripeGateway` so nothing here opens a socket.

What is new: a donation's amount is arbitrary, so Checkout is built with an
inline `price_data` rather than a pre-created Price id, and there is no plan to
switch a user onto — a paid invoice just marks a `Donation` row `active`
(monthly) or `paid` (one-time), and a failed one marks it `lapsed`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from explorer_api import billing, models as m
from explorer_api.db import get_session
from explorer_api.main import create_app
from explorer_api.routes.auth import current_user
from explorer_api.routes.donate import get_gateway, router as donate_router
from explorer_api.settings import Settings

WEBHOOK_SECRET = "whsec_test_secret"
UTC = dt.UTC


@dataclass
class FakeStripe:
    checkout_url: str = "https://checkout.stripe.test/c/pay/cs_test_1"
    portal_url: str = "https://billing.stripe.test/p/session/live_1"
    checkout_calls: list[dict[str, Any]] = field(default_factory=list)
    portal_calls: list[dict[str, Any]] = field(default_factory=list)

    async def create_checkout_session(self, **kwargs: Any) -> billing.CheckoutSession:
        self.checkout_calls.append(kwargs)
        return billing.CheckoutSession(id="cs_test_1", url=self.checkout_url)

    async def create_portal_session(self, **kwargs: Any) -> str:
        self.portal_calls.append(kwargs)
        return self.portal_url


def _sign(body: bytes, *, secret: str = WEBHOOK_SECRET, timestamp: int | None = None,
          signature: str | None = None) -> str:
    ts = timestamp if timestamp is not None else int(time.time())
    mac = signature or hmac.new(
        secret.encode(), f"{ts}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return f"t={ts},v1={mac}"


def _epoch(when: dt.datetime) -> int:
    return int(when.timestamp())


def checkout_completed_event(
    *, customer: str, amount_total: int = 2500, mode: str = "payment",
    subscription: str | None = None, donation_id: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id or f"evt_{uuid4().hex[:16]}",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_{uuid4().hex[:16]}",
                "object": "checkout.session",
                "customer": customer,
                "subscription": subscription,
                "mode": mode,
                "amount_total": amount_total,
                "currency": "usd",
                "payment_status": "paid",
                "metadata": {"donation_id": donation_id} if donation_id else {},
            }
        },
    }


def invoice_event(
    event_type: str, *, customer: str, subscription: str = "sub_test_1",
    billing_reason: str = "subscription_cycle", event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id or f"evt_{uuid4().hex[:16]}",
        "type": event_type,
        "data": {
            "object": {
                "id": f"in_{uuid4().hex[:12]}",
                "object": "invoice",
                "customer": customer,
                "subscription": subscription,
                "billing_reason": billing_reason,
            }
        },
    }


async def _user(session, **kwargs: Any) -> m.User:
    user = m.User(email=f"u-{uuid4().hex[:10]}@example.test", email_verified=True, **kwargs)
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def user(session) -> m.User:
    return await _user(session)


@pytest.fixture
def gateway() -> FakeStripe:
    return FakeStripe()


@pytest_asyncio.fixture
async def client(session, user, gateway, database_url: str) -> AsyncIterator[AsyncClient]:
    settings = Settings.load({
        "DATABASE_URL": database_url,
        "SESSION_SECRET": "s" * 32,
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET,
    })
    app = create_app(settings)

    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[get_gateway] = lambda: gateway

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def _post_webhook(client: AsyncClient, event: dict[str, Any], **sign: Any):
    body = json.dumps(event).encode()
    return await client.post(
        "/api/billing/webhook", content=body,
        headers={"stripe-signature": _sign(body, **sign),
                 "content-type": "application/json"},
    )


async def _count(session, model) -> int:
    return int((await session.execute(select(func.count()).select_from(model))).scalar_one())


# --- checkout ------------------------------------------------------------


async def test_a_one_time_donation_builds_an_inline_price(client, gateway):
    r = await client.post("/api/donate/checkout",
                          json={"amount_usd": "25", "interval": "once"})
    assert r.status_code == 200, r.text
    assert r.json()["url"] == gateway.checkout_url
    call = gateway.checkout_calls[0]
    assert call["mode"] == "payment"
    assert call["price_data"]["unit_amount"] == 2500
    assert "recurring" not in call["price_data"]


async def test_a_monthly_donation_builds_a_recurring_inline_price(client, gateway):
    r = await client.post("/api/donate/checkout",
                          json={"amount_usd": "10", "interval": "month"})
    assert r.status_code == 200, r.text
    call = gateway.checkout_calls[0]
    assert call["mode"] == "subscription"
    assert call["price_data"]["recurring"] == {"interval": "month"}


async def test_a_zero_or_negative_amount_is_rejected(client):
    r = await client.post("/api/donate/checkout",
                          json={"amount_usd": "0", "interval": "once"})
    assert r.status_code == 422


async def test_checkout_creates_a_pending_donation_row(session, client):
    await client.post("/api/donate/checkout", json={"amount_usd": "5", "interval": "once"})
    assert await _count(session, m.Donation) == 1
    row = (await session.execute(select(m.Donation))).scalars().first()
    assert row.status == "pending" and row.amount_usd == Decimal("5.000000")


# --- webhook: inherited guarantees ----------------------------------------


async def test_a_replayed_webhook_changes_nothing_the_second_time(session, client, user):
    event = checkout_completed_event(customer="cus_1", donation_id="don_placeholder")
    donation = m.Donation(id="don_placeholder", amount_usd=Decimal("25"),
                          interval="once", status="pending",
                          stripe_checkout_session_id=event["data"]["object"]["id"])
    session.add(donation)
    await session.flush()

    r1 = await _post_webhook(client, event)
    r2 = await _post_webhook(client, event)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json()["status"] == "duplicate"
    assert await _count(session, m.StripeEvent) == 1


async def test_an_invalid_signature_is_400_and_writes_nothing(session, client):
    event = checkout_completed_event(customer="cus_1")
    body = json.dumps(event).encode()
    r = await client.post(
        "/api/billing/webhook", content=body,
        headers={"stripe-signature": _sign(body, signature="0" * 64),
                 "content-type": "application/json"},
    )
    assert r.status_code == 400
    assert await _count(session, m.StripeEvent) == 0


# --- webhook: donation-specific behavior ----------------------------------


async def test_checkout_completed_marks_a_one_time_donation_paid(session, client):
    donation = m.Donation(id="don_a", amount_usd=Decimal("25"), interval="once",
                          status="pending", stripe_checkout_session_id="cs_a")
    session.add(donation)
    await session.flush()
    event = checkout_completed_event(
        customer="cus_a", donation_id="don_a", mode="payment",
    )
    event["data"]["object"]["id"] = "cs_a"
    r = await _post_webhook(client, event)
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "paid"


async def test_checkout_completed_marks_a_monthly_donation_active_and_records_the_subscription(
    session, client,
):
    donation = m.Donation(id="don_b", amount_usd=Decimal("10"), interval="month",
                          status="pending", stripe_checkout_session_id="cs_b")
    session.add(donation)
    await session.flush()
    event = checkout_completed_event(
        customer="cus_b", donation_id="don_b", mode="subscription",
        subscription="sub_b",
    )
    event["data"]["object"]["id"] = "cs_b"
    r = await _post_webhook(client, event)
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "active"
    assert donation.stripe_subscription_id == "sub_b"


async def test_invoice_paid_keeps_a_monthly_donation_active(session, client):
    donation = m.Donation(id="don_c", amount_usd=Decimal("10"), interval="month",
                          status="active", stripe_subscription_id="sub_c")
    session.add(donation)
    await session.flush()
    r = await _post_webhook(client, invoice_event("invoice.paid", customer="cus_c",
                                                   subscription="sub_c"))
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "active"


async def test_payment_failed_marks_a_monthly_donation_lapsed(session, client):
    donation = m.Donation(id="don_d", amount_usd=Decimal("10"), interval="month",
                          status="active", stripe_subscription_id="sub_d")
    session.add(donation)
    await session.flush()
    r = await _post_webhook(
        client, invoice_event("invoice.payment_failed", customer="cus_d",
                              subscription="sub_d"),
    )
    assert r.status_code == 200
    await session.refresh(donation)
    assert donation.status == "lapsed"
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd api && .venv/bin/python -m pytest tests/test_billing.py -q
```
Expected: FAIL — `ModuleNotFoundError: No module named 'explorer_api.routes.donate'` (Task 6 hasn't run yet). This is expected; Steps 3-4 add `billing.py`'s side of this, Task 6 adds the route module the test imports.

- [ ] **Step 3: Rewrite `billing.py`**

Apply the deletions listed above. Then, right after the `NoCustomer` class (around the old line 129), add:

```python
DONATION_INTERVALS = ("once", "month")


class InvalidDonationAmount(BillingError):
    """A donation of zero or less — Stripe would reject it anyway, but this is
    the clearer message and it avoids a round trip to find out."""
```

Replace `StripeGateway.create_checkout_session` and `LiveStripe.create_checkout_session` (the protocol and the one implementation) — the only caller is the new `create_donation_checkout`, which needs an inline price, not a pre-created one:

```python
class StripeGateway(Protocol):
    """The only two calls this service makes to Stripe."""

    async def create_checkout_session(
        self,
        *,
        mode: str,
        price_data: Mapping[str, Any],
        client_reference_id: str | None,
        customer_email: str | None,
        success_url: str,
        cancel_url: str,
        metadata: Mapping[str, str],
    ) -> CheckoutSession: ...

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> str: ...


class LiveStripe:
    """The real gateway. Constructed once per process from the secret key."""

    def __init__(self, api_key: str) -> None:
        self._client = stripe.StripeClient(api_key)

    async def create_checkout_session(
        self,
        *,
        mode: str,
        price_data: Mapping[str, Any],
        client_reference_id: str | None,
        customer_email: str | None,
        success_url: str,
        cancel_url: str,
        metadata: Mapping[str, str],
    ) -> CheckoutSession:
        params: dict[str, Any] = {
            "mode": mode,
            "line_items": [{"price_data": dict(price_data), "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": dict(metadata),
        }
        if client_reference_id:
            params["client_reference_id"] = client_reference_id
        if customer_email:
            params["customer_email"] = customer_email
        if mode == "subscription":
            params["subscription_data"] = {"metadata": dict(metadata)}
        session = await self._client.v1.checkout.sessions.create_async(params=params)
        return CheckoutSession(id=session.id, url=session.url or "")

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> str:
        session = await self._client.v1.billing_portal.sessions.create_async(
            params={"customer": customer_id, "return_url": return_url}
        )
        return session.url
```

Replace `start_checkout` (deleted) with `create_donation_checkout`, placed where `start_checkout` used to be:

```python
async def create_donation_checkout(
    session: AsyncSession,
    gateway: StripeGateway,
    *,
    amount_usd: Decimal,
    interval: str,
    user: m.User | None,
    success_url: str,
    cancel_url: str,
) -> CheckoutSession:
    """A Stripe Checkout session for a donation of ``amount_usd``.

    Builds `price_data` inline rather than referencing a pre-created Price:
    a donation amount is chosen by the donor, so there is no fixed catalogue
    of prices to have created ahead of time the way a subscription tier needs.
    """
    if interval not in DONATION_INTERVALS:
        raise BillingError(f"interval must be one of {DONATION_INTERVALS}, got {interval!r}")
    if amount_usd <= 0:
        raise InvalidDonationAmount(f"amount_usd must be positive, got {amount_usd}")

    donation = m.Donation(
        user_id=user.id if user else None,
        amount_usd=amount_usd,
        interval=interval,
        status="pending",
    )
    session.add(donation)
    await session.flush()

    price_data: dict[str, Any] = {
        "currency": "usd",
        "unit_amount": int(amount_usd * 100),
        "product_data": {"name": "Donation to LLMS-Explorer"},
    }
    mode = "payment"
    if interval == "month":
        mode = "subscription"
        price_data["recurring"] = {"interval": "month"}

    checkout = await gateway.create_checkout_session(
        mode=mode,
        price_data=price_data,
        client_reference_id=user.id if user else None,
        customer_email=user.email if user else None,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"donation_id": donation.id},
    )
    donation.stripe_checkout_session_id = checkout.id
    await session.flush()
    return checkout
```

Replace the three webhook handlers (`_handle_checkout_completed`, `_handle_invoice_paid`, `_handle_payment_failed`) with donation-aware versions, and add one lookup helper. Keep `_subscription_by_ids` deleted (nothing calls it once subscriptions aren't plan-tied) but add its donation equivalent:

```python
async def _donation_by_ids(
    session: AsyncSession, *, donation_id: str | None = None,
    checkout_session_id: str | None = None, subscription_id: str | None = None,
) -> m.Donation | None:
    """The donation an event is about, tried in the order the event's own
    fields are most to least specific."""
    for column, value in (
        (m.Donation.id, donation_id),
        (m.Donation.stripe_checkout_session_id, checkout_session_id),
        (m.Donation.stripe_subscription_id, subscription_id),
    ):
        if not value:
            continue
        row = (await session.execute(
            select(m.Donation).where(column == value)
        )).scalars().first()
        if row is not None:
            return row
    return None


async def _handle_checkout_completed(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    metadata = obj.get("metadata") or {}
    donation = await _donation_by_ids(
        session, donation_id=metadata.get("donation_id"),
        checkout_session_id=obj.get("id"),
    )
    if donation is None:
        return f"no donation for checkout session {obj.get('id')!r}"
    donation.status = "active" if obj.get("mode") == "subscription" else "paid"
    subscription_id = obj.get("subscription")
    if subscription_id:
        donation.stripe_subscription_id = str(subscription_id)
    await session.flush()
    return None


async def _handle_invoice_paid(session: AsyncSession, obj: Mapping[str, Any]) -> str | None:
    donation = await _donation_by_ids(session, subscription_id=obj.get("subscription"))
    if donation is None:
        return f"no donation for subscription {obj.get('subscription')!r}"
    donation.status = "active"
    await session.flush()
    return None


async def _handle_payment_failed(
    session: AsyncSession, obj: Mapping[str, Any]
) -> str | None:
    donation = await _donation_by_ids(session, subscription_id=obj.get("subscription"))
    if donation is None:
        return f"no donation for subscription {obj.get('subscription')!r}"
    donation.status = "lapsed"
    await session.flush()
    return None
```

The `_HANDLERS` dict and its `assert set(_HANDLERS) == HANDLED_EVENTS` line stay exactly as they are — the event *names* don't change, only what each handler does.

Finally, fix the module-level URL constants (they built off the deleted `plans.BILLING_URL`):

```python
# before
CHECKOUT_SUCCESS_URL = f"{plans.BILLING_URL}?checkout=success"
CHECKOUT_CANCEL_URL = f"{plans.BILLING_URL}?checkout=cancelled"
PORTAL_RETURN_URL = plans.BILLING_URL

# after
DONATE_URL = "https://llms-explorer.com/donate"
CHECKOUT_SUCCESS_URL = f"{DONATE_URL}?checkout=success"
CHECKOUT_CANCEL_URL = f"{DONATE_URL}?checkout=cancelled"
PORTAL_RETURN_URL = DONATE_URL
```

Update `__all__`: remove `"PlanNotPurchasable"`, `"PlanNotSellable"`, `"ACTIVE_STATES"`, `"TERMINAL_STATES"`, `"GRACE_STATES"`, `"CREDIT_GRANTING_BILLING_REASONS"`, `"apply_expired_downgrades"`, `"start_checkout"`; add `"DONATE_URL"`, `"DONATION_INTERVALS"`, `"InvalidDonationAmount"`, `"create_donation_checkout"`.

- [ ] **Step 4: Run the tests**

```bash
cd api && .venv/bin/python -m pytest tests/test_billing.py -q
```
Expected: still FAIL on the same `ModuleNotFoundError` until Task 6 exists — this is the expected state at the end of this task. Do not attempt to make this fully green yet.

- [ ] **Step 5: Commit**

```bash
git add api/explorer_api/billing.py api/tests/test_billing.py
git commit -m "feat(api): billing.py drops plan entitlement, gains donation checkout+webhooks"
```

---

### Task 6: `routes/donate.py` (new) and `routes/billing.py` (trimmed to the webhook)

**Files:**
- Create: `api/explorer_api/routes/donate.py`
- Modify: `api/explorer_api/routes/billing.py` (remove `/plans` and `/checkout`, keep `/webhook` and `/portal`)
- Modify: `api/explorer_api/routes/__init__.py` (mount the new router)

- [ ] **Step 1: The failing tests already exist**

Task 5's `test_billing.py` is the test suite for this task too (it imports `from explorer_api.routes.donate import get_gateway, router as donate_router` and posts to `/api/donate/checkout`). Confirm the current failure:

```bash
cd api && .venv/bin/python -m pytest tests/test_billing.py -q 2>&1 | head -5
```
Expected: `ModuleNotFoundError: No module named 'explorer_api.routes.donate'`.

- [ ] **Step 2: Create `routes/donate.py`**

```python
# api/explorer_api/routes/donate.py
"""`/api/donate` — a Stripe Checkout session for a one-time or monthly donation.

Thin, like every route module: `explorer_api.billing` owns the money rule
(build the inline price, record the `Donation` row), this file owns who may
call it and what a bad amount looks like over HTTP. Unlike the old
plan-checkout route, no sign-in is required — `user` is `optional_user`, so an
anonymous visitor can donate and a signed-in one gets the donation attached to
their account.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from .. import billing, models as m
from ..db import get_session
from .auth import optional_user

router = APIRouter(prefix="/api/donate", tags=["donate"])

OptionalUser = Annotated[m.User | None, Depends(optional_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def _settings(request: Request):
    return request.app.state.settings


def get_gateway(request: Request) -> billing.StripeGateway:
    gateway = getattr(request.app.state, "stripe_gateway", None)
    if gateway is None:
        settings = _settings(request)
        gateway = billing.LiveStripe(settings.stripe_secret_key.get_secret_value())
        request.app.state.stripe_gateway = gateway
    return gateway


Gateway = Annotated[billing.StripeGateway, Depends(get_gateway)]


class CheckoutIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_usd: Decimal
    interval: str

    @field_validator("amount_usd")
    @classmethod
    def _positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount_usd must be positive")
        return value

    @field_validator("interval")
    @classmethod
    def _known_interval(cls, value: str) -> str:
        if value not in billing.DONATION_INTERVALS:
            raise ValueError(f"interval must be one of {billing.DONATION_INTERVALS}")
        return value


class CheckoutOut(BaseModel):
    url: str
    session_id: str


@router.post("/checkout", response_model=CheckoutOut, summary="Start a donation Checkout session")
async def start_checkout(
    body: CheckoutIn, user: OptionalUser, session: DbSession, gateway: Gateway, request: Request,
) -> CheckoutOut:
    try:
        checkout = await billing.create_donation_checkout(
            session, gateway,
            amount_usd=body.amount_usd, interval=body.interval, user=user,
            success_url=billing.CHECKOUT_SUCCESS_URL,
            cancel_url=billing.CHECKOUT_CANCEL_URL,
        )
    except billing.InvalidDonationAmount as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    return CheckoutOut(url=checkout.url, session_id=checkout.id)


__all__ = ["CheckoutIn", "CheckoutOut", "get_gateway", "router"]
```

`optional_user` must already exist in `explorer_api/routes/auth.py` (it's what `artifacts.py` uses — confirm with `grep -n "def optional_user" api/explorer_api/routes/auth.py` before writing this step's code for real; if the name differs, use the actual one).

- [ ] **Step 3: Trim `routes/billing.py`**

Delete `PlanId`, `PlanOut`, `CheckoutIn`, `CheckoutOut`, the `/plans` route, and the `/checkout` route from `api/explorer_api/routes/billing.py`. Delete the now-unused `from .. import ... plans` and `from typing import ... Literal` if nothing else in the file needs them. What remains:

```python
# api/explorer_api/routes/billing.py
"""`/api/billing` — the Customer Portal and the Stripe webhook.

Thin by design: every rule about money lives in `explorer_api.billing`. What
is decided here is who may call what, and what each refusal looks like:

* **The webhook takes no session and no key.** It authenticates by signature
  alone (`explorer_api.billing.verify_event`), because Stripe is the only
  caller and it has no cookie. A failed verification is a 400 with nothing
  written.
* **A 2xx is Stripe's "stop retrying".** So a duplicate and an event we do not
  act on both answer 200 with a `status` saying which; only a signature
  failure and a genuine server fault are non-2xx.
* **The Portal is account-only.** The customer id is read from a row that
  belongs to the signed-in user, never from the request.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .. import billing, models as m
from ..db import get_session
from ..settings import Settings
from .auth import current_user
from .donate import Gateway, get_gateway

router = APIRouter(prefix="/api/billing", tags=["billing"])

CurrentUser = Annotated[m.User, Depends(current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def _settings(request: Request) -> Settings:
    return request.app.state.settings


class PortalOut(BaseModel):
    url: str


class WebhookOut(BaseModel):
    received: bool
    status: str
    detail: str | None = None


@router.get("/portal", response_model=PortalOut, summary="Open the Customer Portal")
async def open_portal(user: CurrentUser, session: DbSession, gateway: Gateway) -> PortalOut:
    try:
        url = await billing.open_portal(session, user, gateway)
    except billing.NoCustomer as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "no billing account yet — donate once to open a portal",
        ) from exc
    return PortalOut(url=url)


@router.post("/webhook", response_model=WebhookOut, summary="Stripe events (Stripe only)")
async def webhook(request: Request, session: DbSession) -> WebhookOut:
    payload = await request.body()
    settings = _settings(request)
    try:
        event = billing.verify_event(
            payload,
            request.headers.get("stripe-signature"),
            secret=settings.stripe_webhook_secret.get_secret_value(),
        )
    except billing.SignatureInvalid as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "signature verification failed") from exc
    outcome = await billing.handle_event(session, event)
    await session.commit()
    return WebhookOut(received=True, status=outcome.status, detail=outcome.detail)


__all__ = ["PortalOut", "WebhookOut", "get_gateway", "router"]
```

Note this file now imports its `Gateway`/`get_gateway` from `routes/donate.py` rather than defining its own — one Stripe client per process, not two.

- [ ] **Step 4: Wire the new router and run the tests**

In `api/explorer_api/routes/__init__.py`, add the import and mount it (donate before billing, since donate's checkout is the more commonly hit path and ordering within `ROUTER_MODULES` doesn't otherwise matter here — no path overlaps):

```python
# add to the import block
from . import donate as donate_routes

# add to ROUTER_MODULES, after billing_routes
ROUTER_MODULES = (
    auth_routes,
    keys_routes,
    usage_routes,
    billing_routes,
    donate_routes,
    mcp_routes,
    skill_routes,
    tree_routes,
    proposal_routes,
    subscriber_routes,
    artifact_routes,
)
```

Run:
```bash
cd api && .venv/bin/python -m pytest tests/test_billing.py tests/test_plans.py tests/test_migrations.py -q
```
Expected: all PASS.

Then run the full suite to find every remaining reference to deleted names (old `test_main.py` route-set assertions, anything importing `routes.billing.CheckoutIn`/`PlanOut`, etc.):
```bash
cd api && .venv/bin/python -m pytest tests -q 2>&1 | tail -60
```
Fix every failure named here before moving to Task 7 — likely `test_main.py` (asserts the mounted path set; add `/api/donate/checkout` and remove `/api/billing/plans`, `/api/billing/checkout` from whatever list it checks — read that test's actual assertion first, don't guess its shape).

- [ ] **Step 5: Commit**

```bash
git add api/explorer_api/routes/donate.py api/explorer_api/routes/billing.py api/explorer_api/routes/__init__.py
git commit -m "feat(api): mount /api/donate/checkout, trim /api/billing to portal+webhook"
```

---

### Task 7: Site — delete the pricing page, add `/donate/`

**Files:**
- Delete: `site/src/pages/billing.astro`, `site/tools/gen_plans.py`, `site/src/data/plans.json`
- Modify: `.github/workflows/site.yml` (remove the `plans.json` staleness check added earlier)
- Modify: `site/tools/twins.py` (remove the `/billing/` `STATIC_PAGES` entry added earlier)
- Create: `site/src/pages/donate.astro`
- Modify: `site/src/layouts/Base.astro:8-14` (nav: remove "Pricing", add "Donate")
- Test: `site/tests/test_scaffold.py`, `site/tests/test_account_pages.py` (both reference `/billing/`; retarget to `/donate/`)

- [ ] **Step 1: Write the failing test**

Add to `site/tests/test_scaffold.py` (near the existing `test_internal_links_resolve`):

```python
def test_billing_page_is_gone_and_donate_exists():
    dist = SITE / "dist"
    assert not (dist / "billing").exists(), "/billing/ should be deleted, not just unlinked"
    assert (dist / "donate" / "index.html").is_file()
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd site && npm run build > /tmp/build.log 2>&1; tail -5 /tmp/build.log
cd .. && hub/.venv/bin/python -m pytest site/tests/test_scaffold.py::test_billing_page_is_gone_and_donate_exists -q
```
Expected: FAIL — `/donate/` doesn't exist yet (and `/billing/` still does).

- [ ] **Step 3: Delete the old page, create the new one**

```bash
git rm site/src/pages/billing.astro site/tools/gen_plans.py site/src/data/plans.json
```

Create `site/src/pages/donate.astro`:

```astro
---
import Base from "../layouts/Base.astro";

const API_DEFAULT = "https://api.llms-explorer.com";
const api = String(import.meta.env.PUBLIC_API_URL || API_DEFAULT).replace(/\/+$/, "");

const title = "Donate";
const description =
  "LLMS-Explorer is free — reading, the tree, every served llms file, no account needed. If it's useful, a one-time or monthly donation keeps it running.";

const PRESETS = [5, 10, 25, 50];
---
<Base title={title} description={description} route="/donate/">
  <p class="lede">{description}</p>

  <div class="donate-form" data-api={api}>
    <fieldset>
      <legend>Amount (USD)</legend>
      {PRESETS.map((n) => (
        <label class="preset">
          <input type="radio" name="preset" value={n} /> ${n}
        </label>
      ))}
      <label class="preset">
        <input type="radio" name="preset" value="custom" checked /> Other:
        <input type="number" id="custom-amount" min="1" step="1" value="10" />
      </label>
    </fieldset>
    <fieldset>
      <legend>Frequency</legend>
      <label><input type="radio" name="interval" value="once" checked /> One-time</label>
      <label><input type="radio" name="interval" value="month" /> Monthly</label>
    </fieldset>
    <button type="button" id="donate-button">Donate</button>
    <p class="donate-error" id="donate-error" hidden></p>
  </div>

  <noscript>
    <p>Donating starts a Stripe Checkout session, which needs JavaScript.</p>
  </noscript>

  <script>
    const form = document.querySelector(".donate-form");
    const api = form ? form.getAttribute("data-api") : "";
    const errorEl = document.getElementById("donate-error");
    const button = document.getElementById("donate-button") as HTMLButtonElement;

    function amount(): string {
      const preset = (document.querySelector('input[name="preset"]:checked') as HTMLInputElement)?.value;
      if (preset && preset !== "custom") return preset;
      return (document.getElementById("custom-amount") as HTMLInputElement).value;
    }

    function interval(): string {
      return (document.querySelector('input[name="interval"]:checked') as HTMLInputElement).value;
    }

    button?.addEventListener("click", async () => {
      errorEl.hidden = true;
      button.disabled = true;
      try {
        const r = await fetch(api + "/api/donate/checkout", {
          method: "POST",
          credentials: "include",
          headers: { accept: "application/json", "content-type": "application/json" },
          body: JSON.stringify({ amount_usd: amount(), interval: interval() }),
        });
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          errorEl.textContent = body.detail || "Could not start checkout.";
          errorEl.hidden = false;
          return;
        }
        const { url } = await r.json();
        window.location.href = url;
      } catch {
        errorEl.textContent = "Could not reach the API. Try again in a moment.";
        errorEl.hidden = false;
      } finally {
        button.disabled = false;
      }
    });
  </script>
</Base>

<style>
  .donate-form fieldset { border: 1px solid var(--rule); margin: var(--sp-3) 0; padding: var(--sp-2); }
  .donate-form .preset { display: inline-block; margin-right: var(--sp-2); }
  .donate-error { color: var(--accent); font-size: var(--step--1); }
</style>
```

- [ ] **Step 4: Nav, the `gen_plans.py` CI check, and the `twins.py` `STATIC_PAGES` entry**

In `site/src/layouts/Base.astro`, in the `NAV` array:

```javascript
// before
const NAV = [
  ["/reference/", "Reference"],
  ["/examples/", "Examples"],
  ["/downloads/", "Download"],
  ["/blog/", "Blog"],
  ["/billing/", "Pricing"],
];
// after
const NAV = [
  ["/reference/", "Reference"],
  ["/examples/", "Examples"],
  ["/downloads/", "Download"],
  ["/blog/", "Blog"],
  ["/donate/", "Donate"],
];
```

In `.github/workflows/site.yml`, delete the `"committed data is current (src/data/plans.json)"` step added earlier this session (it runs `site/tools/gen_plans.py`, which Step 3 deleted).

In `site/tools/twins.py`'s `STATIC_PAGES` list, replace the `/billing/` entry with a `/donate/` one:

```python
    {"route": "/donate/", "title": "Donate", "page": "src/pages/donate.astro",
     "description": "LLMS-Explorer is free — reading, the tree, every served llms "
                    "file, no account needed. If it's useful, a one-time or "
                    "monthly donation keeps it running.",
     "body": "The amount and frequency are chosen on the page; Checkout is "
             "Stripe-hosted, so no card detail ever reaches this site's own "
             "server.\n\n"
             "## What happens after paying\n\n"
             "A one-time donation is done. A monthly one can be managed or "
             "cancelled from the Stripe Customer Portal, reachable from your "
             "account once you've made one.\n"},
```

(Verify the `description` string above is ≤180 characters and a single sentence before using it — this session's own memory notes that the site's index generator truncates anything longer; count it with `python3 -c "print(len('...'))"` and shorten if needed.)

Also update `site/src/pages/[...slug].astro` and any other file that still lists `"billing"` — there shouldn't be any (`/billing/` was never a content-collection page), but grep to confirm: `grep -rln "billing" site/src --include="*.astro" --include="*.ts"`.

- [ ] **Step 5: Rebuild, retest, commit**

```bash
cd site && rm -rf dist && npm run build 2>&1 | tail -15
cd .. && hub/.venv/bin/python -m pytest site/tests -q 2>&1 | tail -20
```
Expected: `test_billing_page_is_gone_and_donate_exists` PASSES. Fix any other failing test that references `/billing/` before committing (`test_account_pages.py`'s `PAGES` tuple does not include `billing`/`donate` today — it's scoped to the four account routes — so it should be unaffected; confirm with the full run rather than assuming).

```bash
git add site/src/pages/donate.astro site/src/layouts/Base.astro site/tools/twins.py site/tests/test_scaffold.py .github/workflows/site.yml
git commit -m "feat(site): replace /billing/ with /donate/"
```

---

## Self-review notes (already applied above, kept here for the reviewer)

- **Spec coverage:** every bullet in the design doc's §1.1/§1.2 has a task — migration (Task 1), model (Task 2), plan collapse (Task 3), spoke doc (Task 4), billing.py + webhook behavior (Task 5), routes (Task 6), site (Task 7). The design doc's "Stripe test-mode Products/Prices... left in place, unused" bullet needs no task — it's an explicit non-action.
- **Type consistency checked:** `Donation.status` values (`pending/paid/active/lapsed/canceled`) are the same set in the model's `DONATION_STATUSES`, the migration's CHECK constraint, and every test's assertions. `create_donation_checkout`'s keyword names match `routes/donate.py`'s call to it exactly.
- **One thing intentionally deferred, not forgotten:** `apply_expired_downgrades` was scheduled to run periodically before this change (grep for it in a cron/launchd config before assuming it's unused elsewhere — if something schedules it, that scheduling entry needs removing too, which isn't captured as its own task above because it depends on what's found).
