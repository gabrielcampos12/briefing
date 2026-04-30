"""Outbound channels for the generated briefing."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from news_briefing.domain.briefing import BriefingContent
from news_briefing.domain.preferences import UserPreferences


@runtime_checkable
class BriefingDelivery(Protocol):
    """Sends the same briefing to Discord and e-mail as required by the assignment."""

    async def send_discord(
        self,
        preferences: UserPreferences,
        content: BriefingContent,
    ) -> None:
        """Post briefing to the configured Discord channel."""
        ...

    async def send_email(
        self,
        preferences: UserPreferences,
        content: BriefingContent,
    ) -> None:
        """Send briefing body to the configured address."""
        ...
