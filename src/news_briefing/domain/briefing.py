"""Structured output of the briefing generation step."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BriefingContent:
    """Final text (or sections) to send to Discord and e-mail."""

    title: str
    body_markdown: str
