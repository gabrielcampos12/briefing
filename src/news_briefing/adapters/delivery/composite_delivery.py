"""Discord + SMTP delivery for generated briefings."""

from __future__ import annotations

import logging

import discord

from news_briefing.adapters.email.smtp_mailer import send_plaintext_email
from news_briefing.config.settings import Settings
from news_briefing.domain.briefing import BriefingContent
from news_briefing.domain.preferences import UserPreferences

logger = logging.getLogger(__name__)

_MAX_DISCORD: int = 2000


def _chunk_text(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


class CompositeBriefingDelivery:
    """Sends the briefing to a Discord channel and to the user inbox."""

    def __init__(self, client: discord.Client, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def send_discord(
        self,
        preferences: UserPreferences,
        content: BriefingContent,
    ) -> None:
        """Post the markdown briefing to the configured channel."""
        channel = self._client.get_channel(preferences.discord_channel_id)
        if channel is None:
            try:
                channel = await self._client.fetch_channel(preferences.discord_channel_id)
            except discord.HTTPException as e:
                logger.error("Could not access Discord channel: %s", e)
                return
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            logger.error("Target is not a text channel: %s", type(channel))
            return
        text = f"**{content.title}**\n\n{content.body_markdown}"
        for part in _chunk_text(text, _MAX_DISCORD):
            await channel.send(part)

    async def send_email(
        self,
        preferences: UserPreferences,
        content: BriefingContent,
    ) -> None:
        """Send a plaintext e-mail (same substance as the briefing)."""
        if not self._settings.smtp_host or not self._settings.mail_from:
            logger.info("Skipping e-mail: SMTP or MAIL_FROM not configured.")
            return
        body = f"{content.title}\n\n{content.body_markdown}"
        await send_plaintext_email(
            self._settings,
            preferences.email_to,
            content.title[:78],
            body,
        )
