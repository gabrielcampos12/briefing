"""Manual trigger for briefing delivery without waiting scheduler."""

from __future__ import annotations

import asyncio
import logging

import discord

from news_briefing.adapters.ai.agno_briefing import AgnoBriefingGenerator
from news_briefing.adapters.delivery.composite_delivery import CompositeBriefingDelivery
from news_briefing.adapters.news.rss_source import RssNewsSource
from news_briefing.adapters.persistence.db import (
    build_engine,
    close_engine,
    get_session_factory,
)
from news_briefing.adapters.persistence.postgres_repository import (
    PostgresPreferenceRepository,
)
from news_briefing.application.run_briefing_job import run_briefing_job
from news_briefing.config.settings import Settings


async def _run() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings()
    if not settings.discord_bot_token.strip():
        raise SystemExit("DISCORD_BOT_TOKEN is required.")
    if not settings.resolved_llm_api_key:
        raise SystemExit("Set LLM_API_KEY (or GROQ_API_KEY).")

    build_engine(settings.database_url)
    repo = PostgresPreferenceRepository(get_session_factory())

    intents = discord.Intents.none()
    intents.guilds = True
    client = discord.Client(intents=intents)

    await client.login(settings.discord_bot_token)
    try:
        news = RssNewsSource()
        generator = AgnoBriefingGenerator(settings)
        delivery = CompositeBriefingDelivery(client, settings)

        owners = await repo.list_owner_keys()
        if not owners:
            logging.info("No configured users in database.")
            return 0

        sent = 0
        failed = 0
        for owner in owners:
            prefs = await repo.load(owner)
            if prefs is None or not prefs.topics:
                continue
            try:
                await run_briefing_job(prefs, news, generator, delivery)
                sent += 1
                logging.info("Triggered briefing for owner_key=%s", owner)
            except Exception:
                failed += 1
                logging.exception("Manual trigger failed for owner_key=%s", owner)
        logging.info("Done. Triggered jobs: %s, failed jobs: %s", sent, failed)
        return 0 if failed == 0 else 2
    finally:
        await client.close()
        await close_engine()


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
