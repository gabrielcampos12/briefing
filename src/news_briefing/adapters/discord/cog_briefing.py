"""Slash commands and DM handler for deterministic preference interview."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from news_briefing.adapters.persistence.postgres_repository import (
    PostgresPreferenceRepository,
)
from news_briefing.config.settings import Settings
from news_briefing.domain.preferences import TopicPreferences, UserPreferences

logger = logging.getLogger(__name__)


@dataclass
class InterviewState:
    """Per-user interview state machine."""

    stage: str = "topics"
    topics: list[str] = field(default_factory=list)
    topic_details: dict[str, TopicPreferences] = field(default_factory=dict)
    email: str = ""
    channel_id: int = 0
    pending_topic_index: int = 0


class BriefingCog(commands.Cog):
    """Registers `/briefing` and handles DM replies with deterministic flow."""

    def __init__(
        self,
        bot: commands.Bot,
        settings: Settings,
        repository: PostgresPreferenceRepository,
    ) -> None:
        self._bot = bot
        self._settings = settings
        self._repo = repository
        self._sessions: dict[int, InterviewState] = {}

    @app_commands.command(
        name="briefing",
        description="Inicia a configuração do briefing por DM.",
    )
    async def briefing(self, interaction: discord.Interaction) -> None:
        """Start or restart private interview to collect preferences."""
        if interaction.user is None:
            return
        await interaction.response.defer(ephemeral=True)
        uid = interaction.user.id
        logger.info("Received /briefing from user_id=%s", uid)
        self._sessions[uid] = InterviewState()

        first = (
            "Vamos configurar seu briefing.\n\n"
            "1) Envie os topicos separados por virgula.\n"
            "Exemplo: jogos, tecnologia, futebol"
        )
        try:
            await interaction.user.send(first[:2000])
        except discord.HTTPException:
            logger.warning("Could not DM user_id=%s", uid)
            await interaction.followup.send(
                "Nao consigo enviar DM. Habilite DMs do servidor e tente novamente.",
            )
            return
        await interaction.followup.send(
            "Mensagem enviada no seu privado. Vamos configurar por etapas.",
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handle DM replies for active interview sessions."""
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.DMChannel):
            return
        uid = message.author.id
        state = self._sessions.get(uid)
        if state is None:
            return
        text = (message.content or "").strip()
        if not text:
            return
        reply = await self._handle_stateful_reply(state, text, str(uid))
        await message.channel.send(reply[:2000])

    async def _handle_stateful_reply(
        self, state: InterviewState, text: str, owner_key: str
    ) -> str:
        """Advance deterministic interview flow and return next prompt."""
        if state.stage == "topics":
            topics = [t.strip() for t in text.split(",") if t.strip()]
            if not topics:
                return "Nao entendi os topicos. Envie separados por virgula."
            state.topics = topics
            state.stage = "topic_details"
            topic = state.topics[state.pending_topic_index]
            return (
                f"Topico **{topic}**.\n"
                "Envie no formato: `palavra1, palavra2; 5`\n"
                "No final, numero maximo de noticias (1 a 20)."
            )

        if state.stage == "topic_details":
            topic = state.topics[state.pending_topic_index]
            parsed = _parse_topic_detail(topic, text)
            if parsed is None:
                return (
                    "Formato invalido. Exemplo: `xbox, bf6; 5` "
                    "(palavras-chave; maximo de noticias)."
                )
            state.topic_details[topic] = parsed
            state.pending_topic_index += 1
            if state.pending_topic_index < len(state.topics):
                next_topic = state.topics[state.pending_topic_index]
                return (
                    f"Agora topico **{next_topic}**.\n"
                    "Envie no formato: `palavra1, palavra2; 5`."
                )
            state.stage = "email"
            return "Agora envie o e-mail de destino do briefing."

        if state.stage == "email":
            if not _looks_like_email(text):
                return "E-mail invalido. Envie um e-mail valido."
            state.email = text.strip()
            state.stage = "channel"
            return "Perfeito. Agora envie o ID numerico do canal do Discord."

        if state.stage == "channel":
            digits = "".join(ch for ch in text if ch.isdigit())
            if not digits:
                return "ID invalido. Envie apenas numeros."
            state.channel_id = int(digits)
            prefs = UserPreferences(
                topics=tuple(state.topic_details[t] for t in state.topics),
                email_to=state.email,
                discord_channel_id=state.channel_id,
            )
            await self._repo.save(owner_key, prefs)
            state.stage = "done"
            return (
                "Configuracao salva com sucesso.\n"
                "O briefing sera enviado no horario agendado."
            )

        return "Entrevista ja concluida. Se quiser reiniciar, rode `/briefing` novamente."


def _parse_topic_detail(topic: str, text: str) -> TopicPreferences | None:
    """Parse `keywords; max` format."""
    parts = text.split(";")
    if len(parts) != 2:
        return None
    keywords = tuple(k.strip() for k in parts[0].split(",") if k.strip())
    if not keywords:
        return None
    m = re.search(r"\d+", parts[1])
    if not m:
        return None
    maximum = int(m.group(0))
    if maximum < 1 or maximum > 20:
        return None
    return TopicPreferences(
        name=topic,
        priority_keywords=keywords,
        max_articles=maximum,
    )


def _looks_like_email(value: str) -> bool:
    """Simple email format check."""
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))
