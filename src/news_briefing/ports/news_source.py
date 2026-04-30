"""Abstraction for fetching recent news by topic."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from news_briefing.domain.fetched_article import FetchedArticle
from news_briefing.domain.preferences import TopicPreferences


@runtime_checkable
class NewsSource(Protocol):
    """Fetches recent items for a configured topic."""

    def fetch(self, topic: TopicPreferences) -> tuple[FetchedArticle, ...]:
        """Return recent articles matching the topic and keywords."""
        ...
