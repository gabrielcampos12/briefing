"""Asynchronous e-mail send via :mod:`smtplib` in a thread pool."""

from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

from news_briefing.config.settings import Settings

logger = logging.getLogger(__name__)


def _build_message(mail_from: str, to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body, subtype="plain", charset="utf-8")
    return msg


def _send_sync(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    mail_from: str,
    to: str,
    subject: str,
    body: str,
) -> None:
    message = _build_message(mail_from, to, subject, body)
    context = ssl.create_default_context()
    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as s:
            if smtp_user and smtp_password:
                s.login(smtp_user, smtp_password)
            s.send_message(message)
        return
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.ehlo()
        tls_enabled = False
        try:
            s.starttls(context=context)
            s.ehlo()
            tls_enabled = True
        except smtplib.SMTPException:
            # Local dev servers (e.g. MailHog) may not advertise TLS.
            logger.warning(
                "SMTP server did not accept STARTTLS on %s:%s",
                smtp_host,
                smtp_port,
            )
        if smtp_user and smtp_password:
            if not tls_enabled and smtp_host.endswith("sendgrid.net"):
                raise smtplib.SMTPException(
                    "SendGrid requires STARTTLS on port 587/2525 or SSL on port 465."
                )
            s.login(smtp_user, smtp_password)
        s.send_message(message)


def _send_with_sendgrid_fallback(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    mail_from: str,
    to: str,
    subject: str,
    body: str,
) -> None:
    """Retry with implicit TLS for SendGrid when AUTH fails on STARTTLS port."""
    try:
        _send_sync(
            smtp_host,
            smtp_port,
            smtp_user,
            smtp_password,
            mail_from,
            to,
            subject,
            body,
        )
    except (smtplib.SMTPException, OSError):
        if smtp_host.endswith("sendgrid.net") and smtp_port in {587, 2525}:
            logger.warning(
                "Retrying SendGrid e-mail using SMTP SSL on port 465 after SMTP failure."
            )
            _send_sync(
                smtp_host,
                465,
                smtp_user,
                smtp_password,
                mail_from,
                to,
                subject,
                body,
            )
            return
        raise


async def send_plaintext_email(
    settings: Settings,
    to: str,
    subject: str,
    body: str,
) -> None:
    """Send a plaintext e-mail using project SMTP settings."""
    if not settings.smtp_host or not settings.mail_from:
        return
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: _send_with_sendgrid_fallback(
            settings.smtp_host,
            settings.smtp_port,
            settings.smtp_user,
            settings.smtp_password,
            settings.mail_from,
            to,
            subject,
            body,
        ),
    )
