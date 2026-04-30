"""Postgres implementation of :class:`PreferenceRepository`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from news_briefing.adapters.persistence.models import UserPreferenceModel
from news_briefing.domain.preferences import TopicPreferences, UserPreferences


@asynccontextmanager
async def _session_ctx(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def _prefs_to_row(owner_key: str, prefs: UserPreferences) -> UserPreferenceModel:
    topics: list[dict[str, object]] = []
    for t in prefs.topics:
        topics.append(
            {
                "name": t.name,
                "priority_keywords": list(t.priority_keywords),
                "max_articles": t.max_articles,
            }
        )
    return UserPreferenceModel(
        owner_key=owner_key,
        email_to=prefs.email_to,
        discord_channel_id=prefs.discord_channel_id,
        topics=topics,
    )


def _row_to_prefs(row: UserPreferenceModel) -> UserPreferences:
    topics: list[TopicPreferences] = []
    for item in row.topics:
        topics.append(
            TopicPreferences(
                name=str(item["name"]),
                priority_keywords=tuple(str(k) for k in item.get("priority_keywords", [])),
                max_articles=int(item.get("max_articles", 3)),
            )
        )
    return UserPreferences(
        topics=tuple(topics),
        email_to=row.email_to,
        discord_channel_id=row.discord_channel_id,
    )


class PostgresPreferenceRepository:
    """Persists :class:`UserPreferences` using JSONB for topic definitions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def load(self, owner_key: str) -> UserPreferences | None:
        """Return saved preferences for this owner, or None if not configured."""
        async with _session_ctx(self._session_factory) as s:
            row = await s.get(UserPreferenceModel, owner_key)
            if row is None:
                return None
            return _row_to_prefs(row)

    async def save(self, owner_key: str, preferences: UserPreferences) -> None:
        """Persist preferences after the collection flow completes."""
        async with _session_ctx(self._session_factory) as s:
            existing = await s.get(UserPreferenceModel, owner_key)
            if existing is None:
                s.add(_prefs_to_row(owner_key, preferences))
            else:
                new_row = _prefs_to_row(owner_key, preferences)
                existing.email_to = new_row.email_to
                existing.discord_channel_id = new_row.discord_channel_id
                existing.topics = new_row.topics

    async def list_owner_keys(self) -> tuple[str, ...]:
        """List every owner that has a saved row."""
        async with _session_ctx(self._session_factory) as s:
            res = await s.execute(select(UserPreferenceModel.owner_key))
            return tuple(str(x) for x in res.scalars().all())
