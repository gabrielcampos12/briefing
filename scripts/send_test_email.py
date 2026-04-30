"""Send a single SMTP test e-mail using project .env settings."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime

from news_briefing.adapters.email.smtp_mailer import send_plaintext_email
from news_briefing.config.settings import Settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a test e-mail using .env SMTP settings."
    )
    parser.add_argument(
        "--to",
        default="",
        help="Destination e-mail. If omitted, MAIL_FROM is used.",
    )
    parser.add_argument(
        "--subject",
        default="Teste SMTP - trabalho01",
        help="Subject of the test e-mail.",
    )
    parser.add_argument(
        "--message",
        default="Teste de envio SMTP do projeto trabalho01.",
        help="Body text of the test e-mail.",
    )
    return parser


async def _run(to: str, subject: str, message: str) -> int:
    settings = Settings()
    destination = to.strip() or settings.mail_from.strip()
    if not destination:
        raise SystemExit("Defina --to ou configure MAIL_FROM no .env.")
    if not settings.smtp_host.strip():
        raise SystemExit("SMTP_HOST nao configurado no .env.")

    body = (
        f"{message}\n\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
        f"SMTP_HOST: {settings.smtp_host}\n"
        f"SMTP_PORT: {settings.smtp_port}\n"
    )
    await send_plaintext_email(settings, destination, subject, body)
    print(f"E-mail de teste enviado para: {destination}")
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.to, args.subject, args.message)))


if __name__ == "__main__":
    main()
