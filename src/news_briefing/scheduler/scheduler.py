"""APScheduler async wrapper for the daily briefing job."""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from news_briefing.adapters.ai.agno_briefing import AgnoBriefingGenerator
from news_briefing.adapters.delivery.composite_delivery import (
    CompositeBriefingDelivery,
)
from news_briefing.adapters.news.rss_source import RssNewsSource
from news_briefing.adapters.persistence.postgres_repository import (
    PostgresPreferenceRepository,
)
from news_briefing.application.run_briefing_job import run_briefing_job
from news_briefing.config.settings import Settings

logger = logging.getLogger(__name__)


def register_briefing_scheduler(
    client: discord.Client,
    settings: Settings,
    repository: PostgresPreferenceRepository,
) -> AsyncIOScheduler:
    """
    Create and start a scheduler that runs each day at the configured local time.
    The job reuses the :class:`RssNewsSource`, the Agno generator, and
    :class:`CompositeBriefingDelivery`.
    """
    zone = ZoneInfo(settings.schedule_timezone)
    sched = AsyncIOScheduler(timezone=zone)
    news = RssNewsSource()
    gen = AgnoBriefingGenerator(settings)
    delivery = CompositeBriefingDelivery(client, settings)

    async def _run_all() -> None:
        keys = await repository.list_owner_keys()
        for owner in keys:
            prefs = await repository.load(owner)
            if not prefs or not prefs.topics:
                continue
            try:
                await run_briefing_job(prefs, news, gen, delivery)
            except Exception:
                logger.exception("Scheduled briefing failed for %s", owner)

    sched.add_job(
        _run_all,
        CronTrigger(
            hour=settings.briefing_schedule_hour,
            minute=settings.briefing_schedule_minute,
            timezone=zone,
        ),
    )
    sched.start()
    return sched
