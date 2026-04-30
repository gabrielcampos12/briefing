"""Minimal article data returned from news sources."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FetchedArticle:
    """A single item used when generating a briefing."""

    title: str
    url: str
    summary: str = ""
