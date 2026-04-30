"""SQLAlchemy table definitions."""

from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


class UserPreferenceModel(Base):
    """Persisted end-user configuration keyed by a stable string (e.g. Discord user id)."""

    __tablename__ = "user_preferences"

    owner_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    email_to: Mapped[str] = mapped_column(String(320), nullable=False)
    discord_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    topics: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
