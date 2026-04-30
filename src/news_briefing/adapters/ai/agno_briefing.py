"""BriefingGenerator implementation using Agno and provider from settings."""

from __future__ import annotations

import textwrap

from agno.agent import Agent

from news_briefing.adapters.ai.model_factory import build_chat_model
from news_briefing.config.settings import Settings
from news_briefing.domain.briefing import BriefingContent
from news_briefing.domain.fetched_article import FetchedArticle
from news_briefing.domain.preferences import UserPreferences


def _build_prompt(
    preferences: UserPreferences,
    articles_by_topic: dict[str, tuple[FetchedArticle, ...]],
) -> str:
    lines: list[str] = [
        "Create a concise daily news briefing in Markdown.",
        "Structure:",
        "# <short title with date>",
        "For each topic, use ## Topic name, then bullet points with headline, one-line summary, and source link.",
        "Prioritize clarity. Use pt-BR.",
        "",
        "Topics configured:",
    ]
    for t in preferences.topics:
        lines.append(f"- {t.name} (keywords: {', '.join(t.priority_keywords)})")
    lines.append("")
    lines.append("Articles by topic:")
    for name, arts in articles_by_topic.items():
        lines.append(f"## Data for topic: {name}")
        if not arts:
            lines.append("- (no articles returned)")
        for a in arts:
            lines.append(f"- Title: {a.title}")
            lines.append(f"  URL: {a.url}")
            if a.summary:
                lines.append(f"  Snippet: {a.summary[:400]}")
    return "\n".join(lines)


class AgnoBriefingGenerator:
    """Uses an Agno Agent to produce markdown briefings."""

    def __init__(self, settings: Settings) -> None:
        self._agent = Agent(
            model=build_chat_model(settings),
            name="BriefingWriter",
            description="Writes structured news briefings in Brazilian Portuguese.",
            instructions=textwrap.dedent(
                """
                You are a news editor. Output only the briefing in Markdown.
                Do not include chatty preambles. No emojis unless necessary.
                """
            ).strip(),
        )

    def generate(
        self,
        preferences: UserPreferences,
        articles_by_topic: dict[str, tuple[FetchedArticle, ...]],
    ) -> BriefingContent:
        """Return a title and markdown body for Discord and e-mail."""
        prompt = _build_prompt(preferences, articles_by_topic)
        result = self._agent.run(prompt)
        body = (getattr(result, "content", None) or "").strip()
        if not body:
            body = "_Empty briefing (model returned no text)._"
        title_line = "Daily briefing"
        if body.startswith("#"):
            first = body.splitlines()[0].lstrip("# ").strip()
            if first:
                title_line = first[:200]
        return BriefingContent(title=title_line, body_markdown=body)
