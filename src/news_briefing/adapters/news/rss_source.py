"""RSS-backed news source (Google News search feed)."""

from __future__ import annotations

import logging
import urllib.parse

import feedparser
import httpx

from news_briefing.domain.fetched_article import FetchedArticle
from news_briefing.domain.preferences import TopicPreferences

logger = logging.getLogger(__name__)


def _parse_feed_payload(payload: str) -> list[FetchedArticle]:
    parsed = feedparser.parse(payload)
    if getattr(parsed, "bozo", False):
        logger.warning("Feed may be ill-formed: %s", getattr(parsed, "bozo_exception", None))
    out: list[FetchedArticle] = []
    for entry in getattr(parsed, "entries", []):
        title = (entry.get("title") or "").strip() or "(no title)"
        link = (entry.get("link") or "").strip()
        summary = (entry.get("summary") or entry.get("description") or "")
        summary = summary[:2000]
        out.append(FetchedArticle(title=title, url=link, summary=summary))
    return out


def _google_news_rss_url(topic: TopicPreferences) -> str:
    q = f"{topic.name} {' '.join(topic.priority_keywords)}"
    return (
        "https://news.google.com/rss/search?"
        + urllib.parse.urlencode({"q": q, "hl": "pt", "gl": "BR", "ceid": "BR:pt"})
    )


class RssNewsSource:
    """Fetches a Google News RSS feed and trims to ``max_articles``."""

    def __init__(self, timeout: float = 20.0) -> None:
        self._timeout = timeout

    def fetch(self, topic: TopicPreferences) -> tuple[FetchedArticle, ...]:
        """Return recent articles for the given topic (limited by max_articles)."""
        url = _google_news_rss_url(topic)
        with httpx.Client(
            follow_redirects=True,
            timeout=self._timeout,
            headers={"User-Agent": "news-briefing-bot/0.1"},
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
        articles = _parse_feed_payload(resp.text)[: max(1, topic.max_articles)]
        return tuple(articles)
