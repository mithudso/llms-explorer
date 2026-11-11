"""Recoverable coordination of a public tree file and a caller-owned SQL transaction.

Cooperating API writers share one advisory lock. Publication precedes commit,
so readers may briefly see staged bytes. A private fsynced journal allows the
next writer to resolve interrupted or ambiguous commits against PostgreSQL.
This does not make the filesystem and database one atomic transaction.
"""
from __future__ import annotations

import asyncio
import base64
import fcntl
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from . import models as m
from .settings import TREE_PUBLICATION_LOCK_POLL_SECONDS


class PublicationError(RuntimeError):
    """Publication cannot proceed without resolving its existing journal."""


class PublicationBusy(PublicationError):
    """Another cooperating writer owns the file lock."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_nodes(nodes) -> bytes:
    """The hub's JSON format, without its external website-refresh hook."""
    return (json.dumps(nodes, indent=2, ensure_ascii=False) + "\n").encode()


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_replace(path: Path, data: bytes, *, mode: int | None = None) -> None:
    """Unique temporary inode, fsync, replace, then fsync the directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    permissions = mode if mode is not None else (path.stat().st_mode & 0o777
                                                if path.exists() else 0o644)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), permissions)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        _sync_directory(path.parent)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class TreeLock:
    """A stable advisory-lock inode; async waiters remain cancellable."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = self.path.with_name(f".{self.path.name}.lock")
        self.fd = os.open(name, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)

    def try_acquire(self) -> bool:
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False

    async def acquire(self) -> None:
        try:
            while not self.try_acquire():
                await asyncio.sleep(TREE_PUBLICATION_LOCK_POLL_SECONDS)
        except BaseException:
            self.release()
            raise

    def acquire_nowait(self) -> None:
        if not self.try_acquire():
            self.release()
            raise PublicationBusy("another tree publication is in progress")

    def release(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


def journal_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.publication.json")


@dataclass
class Journal:
    path: Path
    proposal_id: str
    before: bytes
    after: bytes

    def save(self) -> None:
        body = {"version": 1, "proposal_id": self.proposal_id,
                "before": base64.b64encode(self.before).decode(),
                "after": base64.b64encode(self.after).decode(),
                "before_sha": digest(self.before), "after_sha": digest(self.after)}
        atomic_replace(journal_path(self.path), json.dumps(body).encode(), mode=0o600)

    @classmethod
    def load(cls, path: Path) -> Journal | None:
        record = journal_path(path)
        if not record.exists():
            return None
        try:
            body = json.loads(record.read_bytes())
            before = base64.b64decode(body["before"], validate=True)
            after = base64.b64decode(body["after"], validate=True)
            if (body["version"] != 1 or not isinstance(body["proposal_id"], str)
                    or digest(before) != body["before_sha"] or digest(after) != body["after_sha"]):
                raise ValueError
            return cls(path, body["proposal_id"], before, after)
        except (ValueError, KeyError, TypeError) as exc:
            raise PublicationError("invalid tree publication journal") from exc

    def finish(self, *, committed: bool) -> None:
        current = self.path.read_bytes()
        if current not in (self.before, self.after):
            raise PublicationError(
                "tree changed outside its pending publication; recovery required")
        target = self.after if committed else self.before
        if current != target:
            atomic_replace(self.path, target)
        journal_path(self.path).unlink()
        _sync_directory(self.path.parent)


async def recover(session: AsyncSession, path: Path) -> None:
    """Resolve a journal under the caller's file lock using an independent DB read."""
    journal = Journal.load(path)
    if journal is None:
        return
    factory = async_sessionmaker(session.bind, expire_on_commit=False)
    async with factory() as fresh:
        # Wait for an interrupted connection's transaction to settle. The
        # requesting session must not lock this proposal before recovery.
        result = await fresh.execute(select(m.Proposal.status)
                                     .where(m.Proposal.id == journal.proposal_id).with_for_update())
        status = result.scalar_one_or_none()
    if status not in ("merged", "proposed", "rejected"):
        raise PublicationError("publication decision is unknown; recovery required")
    journal.finish(committed=status == "merged")


@dataclass
class Pending:
    lock: TreeLock
    journal: Journal
    scope: object
    attempted: bool = False
    committed: bool = False
    scope_rolled_back: bool = False


_PENDING = "explorer_tree_publication"


def _install_events(session: AsyncSession) -> None:
    sync = session.sync_session
    if sync.info.get("explorer_publication_events"):
        return
    sync.info["explorer_publication_events"] = True

    @event.listens_for(sync, "before_commit")
    def before_commit(current):
        if not current.in_nested_transaction() and (pending := current.info.get(_PENDING)):
            pending.attempted = True

    @event.listens_for(sync, "after_commit")
    def after_commit(current):
        if not current.in_nested_transaction() and (pending := current.info.get(_PENDING)):
            pending.committed = True

    @event.listens_for(sync, "after_soft_rollback")
    def after_soft_rollback(current, previous):
        pending = current.info.get(_PENDING)
        scope = pending.scope if pending else None
        while scope is not None:
            if scope is previous:
                pending.scope_rolled_back = True
                break
            scope = scope.parent

    @event.listens_for(sync, "after_transaction_end")
    def after_transaction_end(current, transaction):
        if transaction.parent is not None:
            return
        pending = current.info.pop(_PENDING, None)
        if pending is None:
            return
        try:
            if pending.committed:
                pending.journal.finish(committed=not pending.scope_rolled_back)
            elif not pending.attempted:
                pending.journal.finish(committed=False)
            # A failed commit may have reached the database. Keep the journal
            # until a fresh async read can determine its actual outcome.
        finally:
            pending.lock.release()


def stage(session: AsyncSession, lock: TreeLock, journal: Journal) -> None:
    """Persist recovery evidence before exposing new bytes; transfer lock ownership."""
    if session.sync_session.info.get(_PENDING):
        raise PublicationBusy("one public tree publication is already pending in this transaction")
    _install_events(session)
    journal.save()
    scope = (session.sync_session.get_nested_transaction()
             or session.sync_session.get_transaction())
    session.sync_session.info[_PENDING] = Pending(lock, journal, scope)
    atomic_replace(journal.path, journal.after)


def owns_lock(session: AsyncSession, lock: TreeLock) -> bool:
    pending = session.sync_session.info.get(_PENDING)
    return pending is not None and pending.lock is lock


async def commit_decision(session: AsyncSession) -> None:
    """Commit, or resolve any failed/ambiguous commit using a fresh DB session."""
    pending = session.sync_session.info.get(_PENDING)
    try:
        await session.commit()
    except BaseException:
        await session.rollback()
        if pending is not None:
            lock = TreeLock(pending.journal.path)
            await lock.acquire()
            try:
                await recover(session, lock.path)
            finally:
                lock.release()
        raise
