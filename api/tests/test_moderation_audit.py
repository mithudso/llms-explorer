"""Publication boundary regressions using temporary trees only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from explorer_api import moderation, trees


@pytest.mark.parametrize("wrapped", [False, True])
def test_snapshot_hash_describes_exactly_the_returned_nodes(tmp_path, monkeypatch, wrapped):
    path = tmp_path / "tree.json"
    old = [{"concept": "Old", "parentConcept": None, "childConcepts": []}]
    new = [{"concept": "New", "parentConcept": None, "childConcepts": []}]
    original_bytes = json.dumps({"nodes": old} if wrapped else old).encode()
    replacement = json.dumps(new).encode()
    path.write_bytes(original_bytes)
    read_bytes = Path.read_bytes
    read_nodes = trees.read_nodes

    def read_then_publish(candidate):
        result = read_bytes(candidate)
        if candidate == path:
            path.write_bytes(replacement)
        return result

    def legacy_read_then_publish(candidate):
        result = read_nodes(candidate)
        path.write_bytes(replacement)
        return result

    monkeypatch.setattr(Path, "read_bytes", read_then_publish)
    monkeypatch.setattr(trees, "read_nodes", legacy_read_then_publish)
    loaded, sha = moderation.read_tree(path)
    assert loaded == old
    assert sha == hashlib.sha256(original_bytes).hexdigest()
    assert read_bytes(path) == replacement

# The remaining cases exercise real database dispositions and temporary tree
# files. No test calls the live hub refresh hook or a real public-tree path.
import asyncio
import os
import stat
import sys
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

from explorer_api import models as m, tree_publication as publication


@pytest_asyncio.fixture
async def decision(session, tmp_path, monkeypatch):
    path = tmp_path / "tree.json"
    before = publication.encode_nodes([{"concept": "Root", "slug": "root",
                                        "parentConcept": None, "childConcepts": []}])
    path.write_bytes(before)
    monkeypatch.setenv("EXPLORER_PUBLIC_TREE", str(path))
    moderator = m.User(email="moderator-audit@example.test", email_verified=True)
    author = m.User(email="author-audit@example.test")
    session.add_all([moderator, author])
    await session.flush()
    monkeypatch.setenv(moderation.MODERATOR_ENV, moderator.email)
    proposal = m.Proposal(user_id=author.id, tree_sha=publication.digest(before), status="proposed",
                         patch_json={"ops": [{"op": "update", "concept": "Root",
                                             "node": {"description": "accepted é"}}]})
    session.add(proposal)
    await session.commit()
    return SimpleNamespace(path=path, before=before, moderator=moderator, proposal=proposal,
                           proposal_id=proposal.id)


def test_same_sha_writers_have_exactly_one_winner(tmp_path):
    path = tmp_path / "tree.json"
    path.write_bytes(b"[]")
    expected = publication.digest(path.read_bytes())
    from threading import Event

    entered, release = Event(), Event()
    original = publication.atomic_replace

    def controlled_write(target, data, **kwargs):
        entered.set()
        assert release.wait(timeout=3)
        original(target, data, **kwargs)

    from unittest.mock import patch

    with (patch.object(publication, "atomic_replace", controlled_write),
          ThreadPoolExecutor(max_workers=1) as pool):
        winner = pool.submit(moderation.write_tree, path, [{"concept": "First"}],
                             expected_sha=expected)
        try:
            assert entered.wait(timeout=3)
            with pytest.raises(moderation.PublicationBusy):
                moderation.write_tree(path, [{"concept": "Second"}], expected_sha=expected)
        finally:
            release.set()
        winner.result(timeout=3)
    with pytest.raises(moderation.TreeMoved):
        moderation.write_tree(path, [{"concept": "Second"}], expected_sha=expected)
    assert json.loads(path.read_bytes()) == [{"concept": "First"}]


async def test_commit_keeps_publication_and_private_journal_is_removed(session, decision,
                                                                      monkeypatch):
    # The hub's serializer now includes an external publication hook. API
    # persistence must use its identical format without invoking that hook.
    monkeypatch.setattr(trees.concept_tree(), "save_nodes", lambda *args: pytest.fail("hub write"))
    await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)
    record = publication.journal_path(decision.path)
    assert stat.S_IMODE(record.stat().st_mode) == 0o600
    after = decision.path.read_bytes()
    assert b"accepted \xc3\xa9" in after
    await moderation.commit_decision(session)
    assert decision.path.read_bytes() == after
    assert not record.exists()
    await session.refresh(decision.proposal)
    assert decision.proposal.status == "merged"
    lock = publication.TreeLock(decision.path)
    lock.acquire_nowait()
    lock.release()


async def test_rollback_restores_public_file_and_proposed_record(session, decision):
    await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)
    assert decision.path.read_bytes() != decision.before
    await session.rollback()
    assert decision.path.read_bytes() == decision.before
    assert not publication.journal_path(decision.path).exists()
    await session.refresh(decision.proposal)
    assert decision.proposal.status == "proposed"


async def test_flush_failure_restores_on_rollback(session, decision, monkeypatch):
    error = OperationalError("controlled flush", {}, RuntimeError("temporary DB fault"))
    monkeypatch.setattr(session, "flush", AsyncMock(side_effect=error))
    with pytest.raises(OperationalError):
        await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)
    await session.rollback()
    assert decision.path.read_bytes() == decision.before
    assert not publication.journal_path(decision.path).exists()


async def test_commit_failure_resolves_using_fresh_database_status(session, decision):
    await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)

    def fail_commit(_):
        raise OperationalError("controlled commit", {}, RuntimeError("temporary DB fault"))

    event.listen(session.sync_session, "before_commit", fail_commit)
    with pytest.raises(OperationalError):
        await moderation.commit_decision(session)
    assert decision.path.read_bytes() == decision.before
    assert not publication.journal_path(decision.path).exists()
    await session.refresh(decision.proposal)
    assert decision.proposal.status == "proposed"


@pytest.mark.parametrize("savepoint_rollback", [False, True])
async def test_savepoint_does_not_finalize_outer_publication(session, decision, savepoint_rollback):
    nested = await session.begin_nested()
    await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)
    staged = decision.path.read_bytes()
    if savepoint_rollback:
        await nested.rollback()
    else:
        await nested.commit()
    assert decision.path.read_bytes() == staged
    assert publication.journal_path(decision.path).exists()
    lock = publication.TreeLock(decision.path)
    with pytest.raises(publication.PublicationBusy):
        lock.acquire_nowait()
    if savepoint_rollback:
        # Releasing an enclosing transaction after a rolled-back SAVEPOINT
        # must not preserve that SAVEPOINT's discarded moderation decision.
        await moderation.commit_decision(session)
    else:
        await session.rollback()
    assert decision.path.read_bytes() == decision.before
    assert not publication.journal_path(decision.path).exists()


async def test_canceling_async_lock_waiter_releases_its_descriptor(tmp_path):
    path = tmp_path / "tree.json"
    held = publication.TreeLock(path)
    held.acquire_nowait()
    waiting = publication.TreeLock(path)
    task = asyncio.create_task(waiting.acquire())
    await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert waiting.fd is None
    held.release()
    next_lock = publication.TreeLock(path)
    next_lock.acquire_nowait()
    next_lock.release()


@pytest.mark.parametrize("status,third_party,expected_exit", [
    ("merged", False, 0), ("proposed", False, 0), ("rejected", False, 0),
    ("missing", False, 12), ("merged", True, 12),
])
async def test_fresh_process_recovers_or_refuses_pending_journal(session, database_url, decision,
                                                               status, third_party, expected_exit):
    proposal_id = decision.proposal_id
    if status == "missing":
        proposal_id = "prop_missing"
    else:
        decision.proposal.status = status
        await session.commit()
    after = publication.encode_nodes([{"concept": "Staged"}])
    publication.Journal(decision.path, proposal_id, decision.before, after).save()
    published = b'[{"concept":"External"}]' if third_party else after
    publication.atomic_replace(decision.path, published)
    script = '''import asyncio, os, sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from explorer_api import tree_publication as p
async def run():
    engine = create_async_engine(os.environ["EXPLORER_RECOVERY_TEST_DATABASE_URL"])
    lock = p.TreeLock(Path(sys.argv[1]))
    try:
        await lock.acquire()
        async with async_sessionmaker(engine)() as session:
            await p.recover(session, lock.path)
    except p.PublicationError:
        return 12
    finally:
        lock.release()
        await engine.dispose()
    return 0
sys.exit(asyncio.run(run()))
'''
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-c", script, str(decision.path),
        env={**os.environ, "EXPLORER_RECOVERY_TEST_DATABASE_URL": database_url},
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await asyncio.wait_for(process.communicate(), timeout=10)
    assert process.returncode == expected_exit, (out + err).decode()
    if expected_exit:
        assert decision.path.read_bytes() == published
        assert publication.journal_path(decision.path).exists()
    else:
        assert decision.path.read_bytes() == (after if status == "merged" else decision.before)
        assert not publication.journal_path(decision.path).exists()


async def test_filesystem_failure_after_replace_restores_on_rollback(session, decision,
                                                                   monkeypatch):
    original = publication.atomic_replace
    failed = False

    def fail_after_publish(path, data, **kwargs):
        nonlocal failed
        original(path, data, **kwargs)
        if path == decision.path and not failed:
            failed = True
            raise OSError("controlled post-replace failure")

    monkeypatch.setattr(publication, "atomic_replace", fail_after_publish)
    with pytest.raises(OSError, match="controlled post-replace"):
        await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)
    await session.rollback()
    assert failed
    assert decision.path.read_bytes() == decision.before
    assert not publication.journal_path(decision.path).exists()


async def test_other_process_cannot_publish_while_decision_is_uncommitted(session, decision):
    await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)
    script = '''import sys
from pathlib import Path
from explorer_api import moderation as m
path = Path(sys.argv[1])
try:
    m.write_tree(path, [], expected_sha=m.read_tree(path)[1])
except m.PublicationBusy:
    sys.exit(17)
sys.exit(0)
'''
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-c", script, str(decision.path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await asyncio.wait_for(process.communicate(), timeout=10)
    assert process.returncode == 17, (out + err).decode()
    await moderation.commit_decision(session)
    assert json.loads(decision.path.read_bytes())[0]["concept"] == "Root"


async def test_reject_cannot_overwrite_concurrent_acceptance(session, engine, decision):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    moderator_id = decision.moderator.id
    async with async_sessionmaker(engine, expire_on_commit=False)() as rejecting:
        moderator = await rejecting.get(m.User, moderator_id)
        stale = await rejecting.get(m.Proposal, decision.proposal_id)
        assert stale.status == "proposed"
        await moderation.decide(session, decision.moderator, decision.proposal_id, accept=True)
        task = asyncio.create_task(moderation.decide(
            rejecting, moderator, decision.proposal_id, accept=False))
        try:
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(task), timeout=0.05)
            await moderation.commit_decision(session)
            with pytest.raises(moderation.AlreadyDecided):
                await asyncio.wait_for(task, timeout=3)
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            await rejecting.rollback()
    await session.refresh(decision.proposal)
    assert decision.proposal.status == "merged"
    assert json.loads(decision.path.read_bytes())[0]["description"] == "accepted é"
