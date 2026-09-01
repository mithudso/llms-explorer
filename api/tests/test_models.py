# api/tests/test_models.py
"""The schema's guarantees, asserted against a real PostgreSQL.

Three of these come verbatim from the plan (Task 2 Step 1); the rest hold the
lines the plan's Global Constraints draw — money never becomes a float, the
ledger cannot be rewritten, `job_events` can be replayed by `Last-Event-ID`,
and the whole table set the later tasks import actually exists.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DatabaseError

from explorer_api import models as m

# Every table Tasks 3–10 import. Named here so a missing one fails now, loudly,
# instead of at import time three tasks later.
EXPECTED_TABLES = {
    "users", "auth_passkeys", "auth_oauth", "api_keys", "plans", "subscriptions",
    "credits", "ledger", "jobs", "job_events", "artifacts", "trees", "proposals",
    "moderation", "stripe_events", "prices",
}


async def _user(session):
    u = m.User(email=f"u-{uuid4().hex[:10]}@example.test")
    session.add(u)
    await session.flush()
    return u


async def _job(session):
    u = await _user(session)
    j = m.Job(user_id=u.id, kind="lint", status="queued", input_ref="mirror.md")
    session.add(j)
    await session.flush()
    return j


# --- the plan's three tests --------------------------------------------------

async def test_ledger_is_append_only(session):
    u = await _user(session)
    row = m.LedgerEntry(user_id=u.id, component="01", kind="input", model="claude-opus-4-8",
                        units=1000, unit_cost_usd=Decimal("0.000015"),
                        price_usd=Decimal("0.000045"), billable=True)
    session.add(row)
    await session.commit()
    with pytest.raises(DatabaseError):                 # the trigger/constraint refuses it
        row.price_usd = Decimal("0")
        await session.commit()


async def test_money_keeps_six_decimals(session):
    u = await _user(session)
    session.add(m.LedgerEntry(user_id=u.id, component="17", kind="embedding",
                              model="mxbai-embed-large",
                              units=1, unit_cost_usd=Decimal("0.000001"),
                              price_usd=Decimal("0.000003"), billable=True))
    await session.commit()
    got = (await session.execute(select(m.LedgerEntry))).scalar_one()
    assert got.price_usd == Decimal("0.000003")     # not 3e-06 float noise


async def test_job_events_are_ordered_and_unique(session):
    j = await _job(session)
    session.add_all([m.JobEvent(job_id=j.id, seq=1, kind="stage", payload={"s": "clean"}),
                     m.JobEvent(job_id=j.id, seq=2, kind="tokens", payload={"n": 10})])
    await session.commit()
    with pytest.raises(DatabaseError):
        session.add(m.JobEvent(job_id=j.id, seq=2, kind="stage", payload={}))
        await session.commit()


# --- the rest of the contract ------------------------------------------------

async def test_the_migration_creates_every_table_the_later_tasks_import(session):
    rows = await session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    )
    present = {r[0] for r in rows}
    assert present >= EXPECTED_TABLES, f"missing: {sorted(EXPECTED_TABLES - present)}"


async def test_every_money_column_is_numeric_12_6_never_float(session):
    rows = await session.execute(text("""
        SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND (column_name LIKE '%%_usd' OR column_name LIKE '%%_usd_%%')
    """))
    found = list(rows)
    assert found, "no money columns found — the schema is not what the ledger needs"
    for table, column, data_type, precision, scale in found:
        assert data_type == "numeric", f"{table}.{column} is {data_type}, not numeric"
        assert (precision, scale) == (12, 6), f"{table}.{column} is numeric({precision},{scale})"


async def test_the_ledger_cannot_be_deleted_either(session):
    u = await _user(session)
    row = m.LedgerEntry(user_id=u.id, component="13", kind="input", model="qwen3.5:35b",
                        units=5, unit_cost_usd=Decimal("0.000100"),
                        price_usd=Decimal("0.000500"), billable=True)
    session.add(row)
    await session.commit()
    with pytest.raises(DatabaseError):
        await session.delete(row)
        await session.commit()


async def test_the_ledger_has_no_updated_at_column(session):
    rows = await session.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='ledger'"
    ))
    assert "updated_at" not in {r[0] for r in rows}   # append-only rows are never touched


async def test_a_ledger_row_records_a_non_billable_reason(session):
    """Master §5: a failed verify gate bills nothing for that iteration."""
    u = await _user(session)
    session.add(m.LedgerEntry(user_id=u.id, component="01", kind="output",
                              model="claude-sonnet-5", units=4000,
                              unit_cost_usd=Decimal("0.000015"),
                              price_usd=Decimal("0.000045"),
                              billable=False, reason="polish"))
    await session.commit()
    got = (await session.execute(select(m.LedgerEntry))).scalar_one()
    assert got.billable is False and got.reason == "polish"


async def test_an_unknown_component_is_refused(session):
    """15 §3 fixes the component list; 10 spends nothing and is not on it."""
    u = await _user(session)
    session.add(m.LedgerEntry(user_id=u.id, component="10", kind="input", model="x",
                              units=1, unit_cost_usd=Decimal("0"), price_usd=Decimal("0")))
    with pytest.raises(DatabaseError):
        await session.commit()


async def test_jobs_carry_the_lease_fields_the_reaper_needs(session):
    """Master §4/§5: worker, lease_expires, attempts, last_heartbeat."""
    j = await _job(session)
    for field in ("worker", "lease_expires", "attempts", "last_heartbeat"):
        assert hasattr(j, field)
    assert j.attempts == 0


async def test_job_events_replay_in_sequence_for_last_event_id(session):
    j = await _job(session)
    session.add_all([m.JobEvent(job_id=j.id, seq=n, kind="stage", payload={"n": n})
                     for n in (3, 1, 2)])
    await session.commit()
    rows = (await session.execute(
        select(m.JobEvent).where(m.JobEvent.job_id == j.id,
                                 m.JobEvent.seq > 1).order_by(m.JobEvent.seq)
    )).scalars().all()
    assert [r.seq for r in rows] == [2, 3]


async def test_an_api_key_prefix_is_unique_and_the_hash_is_separate(session):
    u = await _user(session)
    session.add(m.ApiKey(user_id=u.id, prefix="abc123", hash="$argon2id$...",
                         scopes=["read"]))
    await session.commit()
    session.add(m.ApiKey(user_id=u.id, prefix="abc123", hash="$argon2id$other",
                         scopes=["run"]))
    with pytest.raises(DatabaseError):
        await session.commit()


async def test_two_accounts_cannot_share_one_verified_email(session):
    await _user(session)
    got = (await session.execute(select(m.User))).scalar_one()
    session.add(m.User(email=got.email))
    with pytest.raises(DatabaseError):
        await session.commit()


async def test_one_oauth_account_maps_to_one_user(session):
    u = await _user(session)
    session.add(m.OAuthAccount(user_id=u.id, provider="github", provider_account_id="1"))
    await session.commit()
    session.add(m.OAuthAccount(user_id=u.id, provider="github", provider_account_id="1"))
    with pytest.raises(DatabaseError):
        await session.commit()


async def test_a_stripe_event_id_can_only_be_recorded_once(session):
    """Task 6 leans on this for webhook idempotency."""
    session.add(m.StripeEvent(id="evt_1", type="invoice.paid", payload={"a": 1}))
    await session.commit()
    session.add(m.StripeEvent(id="evt_1", type="invoice.paid", payload={"a": 1}))
    with pytest.raises(DatabaseError):
        await session.commit()


async def test_the_three_plans_are_seeded_with_their_quotas(session):
    plans = (await session.execute(select(m.Plan).order_by(m.Plan.sort_order))).scalars().all()
    assert [p.id for p in plans] == ["free", "starter", "pro"]
    free, starter, pro = plans
    assert free.price_usd == Decimal("0") and starter.price_usd == Decimal("9")
    assert pro.included_credit_usd == Decimal("50")
    assert free.quotas["private_trees"] == 1 and pro.quotas["private_trees"] == 20


async def test_a_private_tree_records_the_sha_it_forked_from(session):
    u = await _user(session)
    session.add(m.Tree(user_id=u.id, slug="me", forked_from_sha="a" * 40,
                       path=f"trees/{u.id}/tree.json"))
    await session.commit()
    got = (await session.execute(select(m.Tree))).scalar_one()
    assert got.forked_from_sha == "a" * 40 and got.updated_at is not None


async def test_a_proposal_starts_proposed_and_names_its_source_sha(session):
    u = await _user(session)
    session.add(m.Proposal(user_id=u.id, tree_sha="b" * 40, patch_json={"add": []}))
    await session.commit()
    got = (await session.execute(select(m.Proposal))).scalar_one()
    assert got.status == "proposed" and got.moderator_user_id is None


async def test_a_moderation_row_points_at_what_it_is_deciding(session):
    u = await _user(session)
    p = m.Proposal(user_id=u.id, tree_sha="c" * 40, patch_json={})
    session.add(p)
    await session.flush()
    session.add(m.ModerationItem(subject_kind="proposal", subject_id=p.id, state="pending"))
    await session.commit()
    got = (await session.execute(select(m.ModerationItem))).scalar_one()
    assert got.subject_id == p.id and got.decided_at is None


async def test_a_price_row_is_effective_from_a_date(session):
    session.add(m.Price(model="qwen3.5:35b", kind="input",
                        unit_cost_usd=Decimal("0.000000"), price_usd=Decimal("0.000001")))
    await session.commit()
    got = (await session.execute(select(m.Price))).scalar_one()
    assert got.effective_from is not None


async def test_credits_start_at_zero_and_are_one_row_per_user(session):
    u = await _user(session)
    session.add(m.Credit(user_id=u.id))
    await session.commit()
    got = (await session.execute(select(m.Credit))).scalar_one()
    assert got.balance_usd == Decimal("0")
    # A second row for the same user is refused by the database, not merely by
    # the ORM identity map — so a raw INSERT is the honest way to ask.
    with pytest.raises(DatabaseError):
        await session.execute(
            text("INSERT INTO credits (user_id, balance_usd) VALUES (:u, 0)"),
            {"u": u.id},
        )
        await session.commit()


async def test_an_artifact_can_be_public_or_owned(session):
    u = await _user(session)
    session.add_all([
        m.Artifact(kind="facts", visibility="public", slug="x", path="/d/x/llms-facts.txt"),
        m.Artifact(kind="concept-pack", visibility="private", owner_user_id=u.id,
                   slug="y", path=f"/u/{u.id}/y.llms/llms.txt"),
    ])
    await session.commit()
    rows = (await session.execute(select(m.Artifact))).scalars().all()
    assert {r.visibility for r in rows} == {"public", "private"}


async def test_a_private_artifact_must_have_an_owner(session):
    session.add(m.Artifact(kind="facts", visibility="private", slug="z", path="/u/?/z"))
    with pytest.raises(DatabaseError):
        await session.commit()


async def test_a_passkey_credential_id_is_unique(session):
    u = await _user(session)
    session.add(m.Passkey(user_id=u.id, credential_id=b"cred-1", public_key=b"pk",
                          sign_count=0))
    await session.commit()
    u2 = await _user(session)
    session.add(m.Passkey(user_id=u2.id, credential_id=b"cred-1", public_key=b"pk2",
                          sign_count=0))
    with pytest.raises(DatabaseError):
        await session.commit()


async def test_a_subscription_maps_a_user_to_a_plan_and_a_stripe_id(session):
    u = await _user(session)
    session.add(m.Subscription(user_id=u.id, plan_id="starter",
                               stripe_customer_id="cus_1", stripe_subscription_id="sub_1",
                               state="active"))
    await session.commit()
    got = (await session.execute(select(m.Subscription))).scalar_one()
    assert got.plan_id == "starter" and got.cancel_at_period_end is False


async def test_deleting_a_user_takes_their_keys_with_them(session):
    u = await _user(session)
    session.add(m.ApiKey(user_id=u.id, prefix="p1", hash="h", scopes=["read"]))
    await session.commit()
    await session.delete(u)
    await session.commit()
    assert not (await session.execute(select(m.ApiKey))).scalars().all()


async def test_the_migration_and_the_models_have_not_drifted(database_url):
    """`alembic check` on a freshly migrated database: no pending diff.

    This is the guard that stops a column being added to `models.py` without a
    migration — the failure would otherwise only appear on the box, at deploy.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    api_dir = Path(__file__).resolve().parents[1]
    env = dict(os.environ, DATABASE_URL=database_url)
    done = subprocess.run(
        [sys.executable, "-m", "alembic", "check"],
        cwd=api_dir, env=env, capture_output=True, text=True,
    )
    assert done.returncode == 0, f"{done.stdout}\n{done.stderr}"
