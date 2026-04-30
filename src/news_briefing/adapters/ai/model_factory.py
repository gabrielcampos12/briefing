"""Factory for Groq chat model used by Agno agents."""

from __future__ import annotations

from agno.models.base import Model
from agno.models.groq import Groq

from news_briefing.config.settings import Settings


def build_chat_model(settings: Settings) -> Model:
    """Create a Groq model instance from ``LLM_MODEL_ID`` and API key."""
    provider = settings.normalized_llm_provider
    if provider != "groq":
        raise ValueError("Unsupported LLM_PROVIDER. Use 'groq'.")
    return Groq(id=settings.llm_model_id, api_key=settings.resolved_llm_api_key)
