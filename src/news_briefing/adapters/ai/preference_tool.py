"""Factory for the interview tool that writes :class:`UserPreferences` to storage."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable

import pydantic

from news_briefing.adapters.persistence.postgres_repository import (
    PostgresPreferenceRepository,
)
from news_briefing.domain.preferences import TopicPreferences, UserPreferences

logger = logging.getLogger(__name__)


class _TopicItem(pydantic.BaseModel):
    name: str
    priority_keywords: list[str]
    max_articles: int = pydantic.Field(ge=1, le=50)


def _parse_preferences(
    email: str,
    discord_channel_id: int,
    topics_json: str,
) -> UserPreferences:
    """Parse and validate the JSON list from the LLM tool call."""
    payload = json.loads(topics_json)
    if not isinstance(payload, list):
        raise TypeError("topics_json must be a JSON array")
    topic_models = [_TopicItem.model_validate(x) for x in payload]
    if not topic_models:
        raise ValueError("At least one topic is required")
    topics = tuple(
        TopicPreferences(
            name=tm.name.strip(),
            priority_keywords=tuple(
                k.strip() for k in tm.priority_keywords if k and k.strip()
            ),
            max_articles=tm.max_articles,
        )
        for tm in topic_models
    )
    return UserPreferences(
        topics=topics,
        email_to=email.strip(),
        discord_channel_id=int(discord_channel_id),
    )


def build_record_user_preferences(
    owner_key: str,
    repository: PostgresPreferenceRepository,
    main_loop: asyncio.AbstractEventLoop,
) -> Callable[[str, int, str], str]:
    """
    Return a sync tool callable. When the tool runs in a worker thread, the coroutine
    is scheduled on ``main_loop`` (the bot loop).
    """

    def record_user_preferences(email: str, discord_channel_id: int, topics_json: str) -> str:
        """
        Persist the user's preferences after explicit confirmation in chat.

        Args:
            email: inbox that receives the daily briefing
            discord_channel_id: text channel id (snowflake) for Discord posts
            topics_json: JSON list of {name, priority_keywords, max_articles}
        """
        try:
            prefs = _parse_preferences(email, discord_channel_id, topics_json)
        except (ValueError, TypeError, json.JSONDecodeError, pydantic.ValidationError) as e:
            return f"Validation error: {e!s}. Re-ask the user for corrected values."
        try:
            fut = asyncio.run_coroutine_threadsafe(
                repository.save(owner_key, prefs), main_loop
            )
            fut.result(120)
        except Exception as e:
            logger.exception("Failed to store preferences for %s", owner_key)
            return f"Database error: {e!s}"
        return (
            "Preferences saved successfully. "
            "The first automated briefing will follow the server schedule (default 07:00 local)."
        )

    return record_user_preferences
