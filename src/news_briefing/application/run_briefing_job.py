"""Scheduled job: fetch news, generate briefing, deliver."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import TypeVar

from news_briefing.domain.briefing import BriefingContent
from news_briefing.domain.fetched_article import FetchedArticle
from news_briefing.domain.preferences import UserPreferences
from news_briefing.ports.briefing_generator import BriefingGenerator
from news_briefing.ports.delivery import BriefingDelivery
from news_briefing.ports.news_source import NewsSource

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def _run_cpu_bound(loop: asyncio.AbstractEventLoop, fn: Callable[[], T]) -> T:
    """Run a blocking function off the event loop thread."""
    return await loop.run_in_executor(None, fn)


async def run_briefing_job(
    preferences: UserPreferences,
    news: NewsSource,
    generator: BriefingGenerator,
    delivery: BriefingDelivery,
) -> None:
    """Execute one full briefing cycle for a single user configuration."""
    loop = asyncio.get_running_loop()
    try:

        def _build_articles() -> dict[str, tuple[FetchedArticle, ...]]:
            return {t.name: news.fetch(t) for t in preferences.topics}

        articles = await _run_cpu_bound(loop, _build_articles)

        def _build_briefing() -> BriefingContent:
            return generator.generate(preferences, articles)

        content = await _run_cpu_bound(loop, _build_briefing)
        await delivery.send_discord(preferences, content)
        await delivery.send_email(preferences, content)
    except Exception:
        logger.exception("Briefing job failed for channel %s", preferences.discord_channel_id)
        raise
