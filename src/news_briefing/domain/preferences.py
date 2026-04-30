"""User-configurable briefing preferences."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicPreferences:
    """Interest area and how to filter news for it."""

    name: str
    priority_keywords: tuple[str, ...]
    max_articles: int


@dataclass(frozen=True)
class UserPreferences:
    """Everything the agent must collect before running scheduled jobs."""

    topics: tuple[TopicPreferences, ...]
    email_to: str
    discord_channel_id: int
