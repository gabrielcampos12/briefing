"""Persistence for user preferences (per Discord user or guild)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from news_briefing.domain.preferences import UserPreferences


@runtime_checkable
class PreferenceRepository(Protocol):
    """Load/save configuration collected in Discord."""

    async def load(self, owner_key: str) -> UserPreferences | None:
        """Return saved preferences for this owner, or None if not configured."""
        ...

    async def save(self, owner_key: str, preferences: UserPreferences) -> None:
        """Persist preferences after the collection flow completes."""
        ...

    async def list_owner_keys(self) -> tuple[str, ...]:
        """List every owner that has at least one saved configuration (for batch jobs)."""
        ...
