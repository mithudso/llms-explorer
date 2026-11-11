"""Isolated PostgreSQL regression probes for ledger debits and audit events."""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from explorer_api import ledger, models as m


async def _user(session):
    user = m.User(email=f"ledger-audit-{uuid4().hex}@example.test", plan_id="free")
    session.add(user)
    await session.commit()
    return user


async def _charge(session, user):
    row = await ledger.record(session, user, component="17", kind="embedding",
                              model="mxbai-embed-large", units=1_000_000)
    await session.commit()
    return row.id


async def test_concurrent_first_debits_both_persist(engine, session):
    user_id = (await _user(session)).id
    reached = 0
    both_missing = asyncio.Event()

    class FirstDebitSession(AsyncSession):
        async def get(self, entity, ident, **kwargs):
            nonlocal reached
            row = await super().get(entity, ident, **kwargs)
            if entity is m.Credit and row is None:
                # Hold both actual READ COMMITTED misses before either inserts.
                # An atomic insert/update implementation needs no missing-row read.
                reached += 1
                if reached == 2:
                    both_missing.set()
                await asyncio.wait_for(both_missing.wait(), 2)
            return row

    factory = async_sessionmaker(engine, class_=FirstDebitSession, expire_on_commit=False)
    async with factory() as first, factory() as second:
        users = await asyncio.gather(first.get(m.User, user_id), second.get(m.User, user_id))
        results = await asyncio.wait_for(asyncio.gather(
            _charge(first, users[0]), _charge(second, users[1]), return_exceptions=True,
        ), 5)
    assert all(isinstance(result, str) for result in results), [type(r).__name__ for r in results]
    user = await session.get(m.User, user_id)
    assert await ledger.credit_balance(session, user) == Decimal("-.20")
    assert await session.scalar(select(func.count()).select_from(m.LedgerEntry)) == 2


async def test_debit_uses_current_balance_even_when_identity_map_is_stale(engine, session):
    user = await _user(session)
    session.add(m.Credit(user_id=user.id, balance_usd=Decimal("10")))
    await session.commit()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as stale, factory() as fresh:
        stale_user = await stale.get(m.User, user.id)
        cached = await stale.get(m.Credit, user.id)
        fresh_user = await fresh.get(m.User, user.id)
        await _charge(fresh, fresh_user)
        assert cached.balance_usd == Decimal("10")
        await _charge(stale, stale_user)
        assert cached.balance_usd == Decimal("9.80")
    assert await ledger.credit_balance(session, user) == Decimal("9.80")
    assert await session.scalar(select(func.count()).select_from(m.LedgerEntry)) == 2


async def test_ledger_append_has_safe_staged_audit_event(session, caplog):
    user = await _user(session)
    caplog.set_level(logging.INFO, logger="explorer_api.ledger")
    row = await ledger.record(session, user, component="17", kind="embedding",
                              model="mxbai-embed-large", units=1_000_000,
                              call_id="private-call-body-not-for-logs")
    assert "ledger_append_staged" in caplog.text
    assert row.id in caplog.text and user.id in caplog.text
    assert user.email not in caplog.text
    assert "private-call-body-not-for-logs" not in caplog.text


async def test_rollback_discards_both_the_append_and_debit(session):
    user = await _user(session)
    user_id = user.id
    await ledger.record(session, user, component="17", kind="embedding",
                        model="mxbai-embed-large", units=1_000_000)
    await session.rollback()
    assert await session.get(m.Credit, user_id) is None
    assert await session.scalar(select(func.count()).select_from(m.LedgerEntry)) == 0
