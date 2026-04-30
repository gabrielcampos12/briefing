"""Discord :class:`commands.Bot` construction."""

from __future__ import annotations

import logging

import discord
from discord import Object
from discord.ext import commands

from news_briefing.adapters.discord.cog_briefing import BriefingCog
from news_briefing.adapters.persistence.postgres_repository import (
    PostgresPreferenceRepository,
)
from news_briefing.config.settings import Settings

logger = logging.getLogger(__name__)


def build_bot(
    settings: Settings,
    repository: PostgresPreferenceRepository,
) -> commands.Bot:
    """Build a :class:`commands.Bot` with DM intents and the briefing cog."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.dm_messages = True
    intents.guilds = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def setup_hook() -> None:
        await bot.add_cog(BriefingCog(bot, settings, repository))
        tree = bot.tree
        if settings.discord_guild_id and settings.discord_guild_id > 0:
            g = Object(id=settings.discord_guild_id)
            tree.copy_global_to(guild=g)
            await tree.sync(guild=g)
        else:
            await tree.sync()
        logger.info("Slash command tree synced (guild_id=%s)", settings.discord_guild_id)

    return bot
