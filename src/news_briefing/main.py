"""Process bootstrap: settings, database, bot, and scheduler."""

from __future__ import annotations

import asyncio
import logging
import sys
from logging import getLogger

import discord
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.base import BaseScheduler
from discord.ext import commands

from news_briefing.adapters.discord.bot import build_bot
from news_briefing.adapters.persistence.db import (
    build_engine,
    close_engine,
    get_session_factory,
    init_db_schema,
)
from news_briefing.adapters.persistence.postgres_repository import (
    PostgresPreferenceRepository,
)
from news_briefing.config.settings import Settings
from news_briefing.scheduler.scheduler import register_briefing_scheduler

logger = getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("discord").setLevel(logging.INFO)


def _require_env(s: Settings) -> None:
    if not s.discord_bot_token.strip():
        raise SystemExit("DISCORD_BOT_TOKEN is required in the environment or .env")
    provider = s.normalized_llm_provider
    if provider != "groq":
        raise SystemExit("LLM_PROVIDER must be 'groq'.")
    if not s.resolved_llm_api_key:
        raise SystemExit(
            "Missing LLM API key. Set LLM_API_KEY or GROQ_API_KEY."
        )


async def _wait_for_db(max_attempts: int = 15) -> None:
    """Apply schema, retrying until PostgreSQL is reachable (Docker start order)."""
    for attempt in range(1, max_attempts + 1):
        try:
            await init_db_schema()
            logger.info("Database schema is ready (attempt %s).", attempt)
            return
        except Exception as e:
            logger.warning("DB not ready (attempt %s): %s", attempt, e)
            await asyncio.sleep(2.0)
    raise RuntimeError("Database did not become ready in time.")


async def _async_main() -> int:
    _setup_logging()
    settings = Settings()
    _require_env(settings)
    logger.info(
        "LLM configured: provider=%s model=%s",
        settings.normalized_llm_provider,
        settings.llm_model_id,
    )
    build_engine(settings.database_url)
    try:
        await _wait_for_db()
    except RuntimeError as e:
        logger.error("%s", e)
        await close_engine()
        return 1
    repo = PostgresPreferenceRepository(get_session_factory())
    bot: commands.Bot = build_bot(settings, repo)
    sched: BaseScheduler | None = None
    scheduler_started: bool = False

    @bot.event
    async def on_ready() -> None:
        nonlocal sched, scheduler_started
        u = bot.user
        if u is not None:
            logger.info("Bot connected as %s", u)
        if scheduler_started:
            return
        sched = register_briefing_scheduler(bot, settings, repo)  # type: ignore[assignment]
        scheduler_started = True
        logger.info("Daily briefing scheduler registered.")

    try:
        await bot.start(settings.discord_bot_token)
    except discord.LoginFailure as e:
        logger.error("Invalid Discord token: %s", e)
        return 1
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, closing.")
    finally:
        if sched is not None:
            try:
                sched.shutdown(wait=False)
            except SchedulerNotRunningError:
                pass
        await close_engine()
    return 0


def main() -> None:
    """Entry point: run the async Discord + scheduler process."""
    code = asyncio.run(_async_main())
    if code:
        raise SystemExit(code)
