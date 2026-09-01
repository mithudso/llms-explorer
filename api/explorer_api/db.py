"""Engine, session factory and the FastAPI session dependency.

Deliberately holds no table definitions — those are ``models.py``, which imports
:class:`Base` from here. Keeping the declarative base beside the engine means
``alembic/env.py`` can reach the metadata without importing the app.

Connection budget (master §8): "≤ 5 connections per worker and ≤ 20 per API
process", against Neon's *pooled* endpoint. ``pool_size=5`` with
``max_overflow=15`` is that ceiling exactly.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from fastapi import Request
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .settings import Settings

#: Deterministic constraint names, so an Alembic autogenerate diff is stable and
#: a migration can drop a constraint it did not name itself.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

POOL_SIZE = 5
MAX_OVERFLOW = 15


class Base(DeclarativeBase):
    """Declarative base for every table in ``models.py``."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_engine(settings: Settings, **kwargs: Any) -> AsyncEngine:
    """Build the async engine. Does not connect — the first query does that."""
    options: dict[str, Any] = {
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_pre_ping": True,
        "future": True,
    }
    options.update(kwargs)
    return create_async_engine(settings.database_url.get_secret_value(), **options)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, rolled back on an exception."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
