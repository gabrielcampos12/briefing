"""Abstraction over Agno/LLM to turn articles into a structured briefing."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from news_briefing.domain.briefing import BriefingContent
from news_briefing.domain.fetched_article import FetchedArticle
from news_briefing.domain.preferences import UserPreferences


@runtime_checkable
class BriefingGenerator(Protocol):
    """Produces final briefing text from user preferences and raw articles."""

    def generate(
        self,
        preferences: UserPreferences,
        articles_by_topic: dict[str, tuple[FetchedArticle, ...]],
    ) -> BriefingContent:
        """Build markdown briefing from grouped articles."""
        ...
