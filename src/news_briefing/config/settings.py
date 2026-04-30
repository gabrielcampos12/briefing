"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration; extend fields as you add integrations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    discord_bot_token: str = Field(default="", description="Discord bot token")
    discord_guild_id: int = Field(
        default=0,
        description="If set, sync slash commands to this guild immediately (dev).",
    )
    llm_provider: str = Field(
        default="groq",
        description="LLM provider for Agno (supported: groq)",
    )
    llm_model_id: str = Field(
        default="llama-3.3-70b-versatile",
        description="Chat model id used by the selected provider",
    )
    llm_api_key: str = Field(
        default="",
        description="Generic API key for selected provider (preferred, Groq).",
    )
    groq_api_key: str = Field(
        default="",
        description="Groq API key (legacy compatibility).",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://news:news@localhost:5432/news_briefing",
        description="Async SQLAlchemy URL (asyncpg driver)",
    )

    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    mail_from: str = Field(default="")

    briefing_schedule_hour: int = Field(default=7, ge=0, le=23)
    briefing_schedule_minute: int = Field(default=0, ge=0, le=59)
    schedule_timezone: str = Field(
        default="America/Sao_Paulo",
        description="IANA timezone for the daily briefing",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def convert_psycopg_to_asyncpg(cls, v: str) -> str:
        """Support plain 'postgresql://' in .env by coercing to asyncpg if missing."""
        if not isinstance(v, str):
            return v
        if v.startswith("postgresql+asyncpg://"):
            return v
        if v.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v.removeprefix("postgresql://")
        return v

    @field_validator("llm_model_id")
    @classmethod
    def validate_llm_model_for_groq(cls, v: str) -> str:
        """Avoid accidental OpenAI model ids when provider is Groq-only."""
        model = v.strip()
        if not model:
            raise ValueError("LLM_MODEL_ID cannot be empty.")
        if model.startswith("gpt-"):
            raise ValueError(
                "Invalid LLM_MODEL_ID for Groq-only setup. "
                "Use a Groq model such as 'llama-3.3-70b-versatile'."
            )
        return model

    @property
    def normalized_llm_provider(self) -> str:
        """Return lowercase provider id."""
        return self.llm_provider.strip().lower()

    @property
    def resolved_llm_api_key(self) -> str:
        """Return LLM API key based on provider with compatibility fallbacks."""
        if self.llm_api_key.strip():
            return self.llm_api_key.strip()
        if self.normalized_llm_provider == "groq":
            return self.groq_api_key.strip()
        return ""
