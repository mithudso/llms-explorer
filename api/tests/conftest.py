"""Test database plumbing.

Task 2's tables are Postgres-shaped — `numeric(12,6)` money that must not become
float, a `BEFORE UPDATE` trigger that makes `ledger` append-only, jsonb payloads
and array scopes — so the tests run against a real PostgreSQL, never SQLite.

Where that server comes from, in order:

1. ``EXPLORER_TEST_DATABASE_URL`` — a server you already run (CI, a container).
   It must point at a *maintenance* database (``.../postgres``); the fixtures
   create and drop their own databases beside it.
2. Otherwise a throwaway cluster is booted for the session from the ``initdb``
   and ``pg_ctl`` on ``PATH`` (or a Homebrew ``postgresql@NN``), on a free port,
   and torn down at the end. Nothing outside the temporary data directory is
   touched.
3. If neither is available every test here skips with the reason, rather than
   silently degrading to a backend that cannot enforce the guarantees.

Isolation model (plan Task 2): the schema is built **once** per session by
``alembic upgrade head`` into a template database; every test then gets a fresh
copy of it via ``CREATE DATABASE … TEMPLATE …``. Tests are therefore
order-independent and none of them has to clean up after itself.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

API_DIR = Path(__file__).resolve().parents[1]

#: Homebrew keeps versioned Postgres out of PATH; look there before giving up.
_BREW_GLOBS = ("/opt/homebrew/opt/postgresql@*/bin", "/usr/local/opt/postgresql@*/bin")

TEMPLATE_DB = "explorer_test_template"


def _find_pg_bin() -> Path | None:
    """Directory holding ``initdb``/``pg_ctl``, or ``None`` when there is none."""
    initdb = shutil.which("initdb")
    if initdb:
        return Path(initdb).parent
    for pattern in _BREW_GLOBS:
        base = Path(pattern)
        for candidate in sorted(base.parent.parent.glob(base.parent.name), reverse=True):
            if (candidate / "bin" / "initdb").exists():
                return candidate / "bin"
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="session")
def postgres_dsn(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Base DSN (``postgresql://…``, no driver, maintenance database) for the session."""
    external = os.environ.get("EXPLORER_TEST_DATABASE_URL")
    if external:
        yield external.rstrip("/")
        return

    bindir = _find_pg_bin()
    if bindir is None:
        pytest.skip(
            "no PostgreSQL available: set EXPLORER_TEST_DATABASE_URL or install "
            "postgresql (initdb/pg_ctl must be on PATH). These tests refuse to "
            "run on SQLite because they assert Postgres-specific guarantees."
        )

    data_dir = tmp_path_factory.mktemp("pgdata") / "db"
    # The unix socket path has a hard ~103-byte limit on macOS and pytest's tmp
    # tree is already most of that, so the socket directory gets its own short
    # path even though every connection here is over TCP.
    sock_dir = Path(tempfile.mkdtemp(prefix="pgs"))
    port = _free_port()
    _run([str(bindir / "initdb"), "-D", str(data_dir), "-U", "postgres",
          "--auth=trust", "-E", "UTF8", "--no-sync"])
    log = data_dir.parent / "server.log"
    _run([str(bindir / "pg_ctl"), "-D", str(data_dir), "-l", str(log), "-w", "start",
          "-o", f"-p {port} -k {sock_dir} -h 127.0.0.1 -F"], log=log)
    dsn = f"postgresql://postgres@127.0.0.1:{port}/postgres"
    try:
        _wait_ready(bindir, port)
        yield dsn
    finally:
        subprocess.run(
            [str(bindir / "pg_ctl"), "-D", str(data_dir), "-m", "immediate", "stop"],
            check=False, capture_output=True,
        )
        shutil.rmtree(sock_dir, ignore_errors=True)


def _run(argv: list[str], log: Path | None = None) -> None:
    """Run a Postgres tool, and on failure say what it actually printed."""
    done = subprocess.run(argv, capture_output=True, text=True)
    if done.returncode != 0:
        tail = ""
        if log is not None and log.exists():
            tail = f"\nserver log:\n{log.read_text()[-2000:]}"
        raise RuntimeError(
            f"{argv[0]} failed ({done.returncode})\n"
            f"stdout:\n{done.stdout}\nstderr:\n{done.stderr}{tail}"
        )


def _wait_ready(bindir: Path, port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        done = subprocess.run(
            [str(bindir / "pg_isready"), "-h", "127.0.0.1", "-p", str(port)],
            capture_output=True,
        )
        if done.returncode == 0:
            return
        time.sleep(0.2)
    raise RuntimeError(f"postgres on port {port} never became ready")


def _async_url(dsn: str, database: str) -> str:
    head, _, _ = dsn.rpartition("/")
    return f"{head}/{database}".replace("postgresql://", "postgresql+asyncpg://", 1)


def _psql_url(dsn: str, database: str) -> str:
    head, _, _ = dsn.rpartition("/")
    return f"{head}/{database}"


@pytest.fixture(scope="session")
def template_database(postgres_dsn: str) -> Iterator[str]:
    """Build the schema **once** with alembic, into a template other tests copy."""
    import asyncio

    import asyncpg

    async def _admin(sql: str) -> None:
        conn = await asyncpg.connect(_psql_url(postgres_dsn, "postgres"))
        try:
            await conn.execute(sql)
        finally:
            await conn.close()

    asyncio.run(_admin(f'DROP DATABASE IF EXISTS "{TEMPLATE_DB}"'))
    asyncio.run(_admin(f'CREATE DATABASE "{TEMPLATE_DB}"'))

    env = dict(os.environ)
    env["DATABASE_URL"] = _async_url(postgres_dsn, TEMPLATE_DB)
    done = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_DIR, env=env, capture_output=True, text=True,
    )
    if done.returncode != 0:
        raise AssertionError(
            "alembic upgrade head failed\n"
            f"stdout:\n{done.stdout}\nstderr:\n{done.stderr}"
        )
    yield TEMPLATE_DB


@pytest_asyncio.fixture
async def database_url(postgres_dsn: str, template_database: str) -> AsyncIterator[str]:
    """A private, freshly copied database for one test."""
    import asyncpg

    name = f"t_{uuid.uuid4().hex[:16]}"
    admin = await asyncpg.connect(_psql_url(postgres_dsn, "postgres"))
    try:
        await admin.execute(f'CREATE DATABASE "{name}" TEMPLATE "{template_database}"')
    finally:
        await admin.close()
    try:
        yield _async_url(postgres_dsn, name)
    finally:
        admin = await asyncpg.connect(_psql_url(postgres_dsn, "postgres"))
        try:
            await admin.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = $1 AND pid <> pg_backend_pid()",
                name,
            )
            await admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
        finally:
            await admin.close()


@pytest_asyncio.fixture
async def engine(database_url: str):
    eng = create_async_engine(database_url, future=True)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
