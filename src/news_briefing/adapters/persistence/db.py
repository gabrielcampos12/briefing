"""Async engine, session factory, and schema creation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from news_briefing.adapters.persistence.models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the lazy singleton engine."""
    if _engine is None:
        raise RuntimeError("Database engine is not initialised. Call build_engine() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Session factory is not initialised. Call build_engine() first.")
    return _session_factory


def build_engine(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Create the async engine and store the global session factory."""
    global _engine, _session_factory
    if _session_factory is not None:
        return _session_factory
    _engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
    )
    _session_factory = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return _session_factory  # type: ignore[return-value]


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Transaction scope (commit on success, rollback on error)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db_schema(engine: AsyncEngine | None = None) -> None:
    """Create tables if they do not exist (demo-friendly, not a migration replacement)."""
    target = engine or get_engine()
    async with target.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_engine() -> None:
    """Release database connections (call on process shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
