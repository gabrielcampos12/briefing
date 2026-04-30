"""Agno interview agent for collecting user preferences in Discord."""

from __future__ import annotations

import logging
from collections.abc import Callable

from agno.agent import Agent

from news_briefing.adapters.ai.model_factory import build_chat_model
from news_briefing.adapters.ai.prompts import INTERVIEW_AGENT_INSTRUCTIONS
from news_briefing.config.settings import Settings

logger = logging.getLogger(__name__)


def build_interview_agent(
    settings: Settings,
    record_tool: Callable[[str, int, str], str],
) -> Agent:
    """Build an :class:`Agent` that guides the user and can persist with ``record_tool``."""
    return Agent(
        model=build_chat_model(settings),
        name="PreferenceInterview",
        description="Interviews the user in Brazilian Portuguese to configure briefings.",
        instructions=INTERVIEW_AGENT_INSTRUCTIONS,
        tools=[record_tool],
        add_history_to_context=True,
        num_history_runs=8,
    )


def run_agent_turn(
    agent: Agent,
    user_message: str,
    user_id: str,
    session_id: str,
) -> str:
    """Run one synchronous model turn; returns assistant text and/or tool result summary."""
    out = agent.run(
        user_message,
        user_id=user_id,
        session_id=session_id,
        stream=False,
    )
    return (out.content or "").strip() or "_(empty response)_"
