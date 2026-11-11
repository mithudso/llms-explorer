"""Bound actual hash-worker concurrency, including cancelled request waiters."""

from __future__ import annotations

import asyncio
import logging
import threading

import pytest
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from explorer_api import keys
from explorer_api import models as m
from test_keys import user

__all__ = ["user"]


async def test_optional_stamp_does_not_wait_for_a_saturated_request_pool(database_url, caplog):
    engine = create_async_engine(database_url, pool_size=1, max_overflow=0, pool_timeout=1)
    caplog.set_level(logging.WARNING, logger="explorer_api.keys")
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            account = m.User()
            session.add(account)
            await session.flush()
            row = m.ApiKey(user_id=account.id, prefix="stamp_fixture", hash="unused",
                           scopes=["read"])
            session.add(row)
            await session.commit()
            # Authentication already holds its request's pooled SELECT connection.
            row = await session.scalar(select(m.ApiKey).where(m.ApiKey.id == row.id))
            async with asyncio.timeout(.5):
                await keys._touch(session, row)
            assert row.last_used_at is None
            assert "key_last_used_stamp_failed" in caplog.text
            assert "TimeoutError" in caplog.text
            assert "UPDATE api_keys" not in caplog.text
    finally:
        await engine.dispose()


class BlockingHasher:
    def __init__(self, loop, *, failure=False):
        self.loop = loop
        self.failure = failure
        self.entered = asyncio.Queue()
        self.release = threading.Event()
        self.lock = threading.Lock()
        self.active = self.peak = 0

    def verify(self, stored, secret):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.loop.call_soon_threadsafe(self.entered.put_nowait, self.active)
        try:
            if not self.release.wait(3):
                raise RuntimeError("hash test release watchdog expired")
            if self.failure:
                raise VerifyMismatchError("controlled mismatch")
            return True
        finally:
            with self.lock:
                self.active -= 1


@pytest.mark.parametrize("cancellations", [1, 2])
async def test_cancelled_waiter_does_not_release_a_running_hash_slot(monkeypatch, cancellations):
    fake = BlockingHasher(asyncio.get_running_loop())
    monkeypatch.setattr(keys, "HASHER", fake)
    monkeypatch.setattr(keys, "_hash_gate", asyncio.Semaphore(1))
    first = asyncio.create_task(keys._verify("hash", "dummy"))
    second = None
    try:
        assert await asyncio.wait_for(fake.entered.get(), 1) == 1
        for _ in range(cancellations):
            first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        second = asyncio.create_task(keys._verify("hash", "dummy"))
        # A negative event assertion is intentional: a cancelled coroutine must
        # not admit a second real worker while the first remains behind its gate.
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(fake.entered.get(), .05)
        fake.release.set()
        assert await asyncio.wait_for(second, 1) is True
        assert fake.peak == 1
        # A later request proves both completed workers returned their permits.
        assert await asyncio.wait_for(keys._verify("hash", "dummy"), 1) is True
    finally:
        fake.release.set()
        await asyncio.gather(first, *([second] if second is not None else []),
                             return_exceptions=True)


async def test_mismatch_releases_the_hash_slot(monkeypatch):
    fake = BlockingHasher(asyncio.get_running_loop(), failure=True)
    fake.release.set()
    monkeypatch.setattr(keys, "HASHER", fake)
    monkeypatch.setattr(keys, "_hash_gate", asyncio.Semaphore(1))
    assert await asyncio.wait_for(keys._verify("hash", "dummy"), 1) is False
    fake.failure = False
    assert await asyncio.wait_for(keys._verify("hash", "dummy"), 1) is True
    assert fake.peak == 1


async def test_key_mutation_events_are_staged_and_do_not_include_secrets(session, user, caplog):
    caplog.set_level(logging.INFO, logger="explorer_api.keys")
    raw, row = await keys.create(session, user, ["read"])
    assert await keys.revoke(session, user, row.id) is row
    assert "api_key_create_staged" in caplog.text
    assert "api_key_revoke_staged" in caplog.text
    assert row.id in caplog.text and row.prefix in caplog.text
    assert raw not in caplog.text
    assert raw.split("_", 2)[2] not in caplog.text
    assert row.hash not in caplog.text
    assert user.email not in caplog.text
