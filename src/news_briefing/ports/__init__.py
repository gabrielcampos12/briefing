"""Abstract interfaces (depend on these from application layer)."""

from news_briefing.ports.briefing_generator import BriefingGenerator
from news_briefing.ports.delivery import BriefingDelivery
from news_briefing.ports.news_source import NewsSource
from news_briefing.ports.preference_repository import PreferenceRepository

__all__ = [
    "BriefingDelivery",
    "BriefingGenerator",
    "NewsSource",
    "PreferenceRepository",
]
