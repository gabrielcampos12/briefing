"""Standalone SMTP test script (no project imports, stdlib only)."""

from __future__ import annotations

import argparse
from datetime import datetime
from email.message import EmailMessage
import smtplib
import ssl
from pathlib import Path
import traceback


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal .env file (KEY=VALUE lines)."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def get_cfg(args: argparse.Namespace) -> dict[str, str]:
    env_data = parse_env_file(Path(args.env_file))
    return {
        "host": args.host or env_data.get("SMTP_HOST", ""),
        "port": str(args.port if args.port is not None else env_data.get("SMTP_PORT", "587")),
        "user": args.user or env_data.get("SMTP_USER", ""),
        "password": args.password or env_data.get("SMTP_PASSWORD", ""),
        "mail_from": args.mail_from or env_data.get("MAIL_FROM", ""),
    }


def build_message(mail_from: str, to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body, subtype="plain", charset="utf-8")
    return msg


def _mask_secret(secret: str) -> str:
    if not secret:
        return "(empty)"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


def send_smtp(
    host: str,
    port: int,
    user: str,
    password: str,
    mail_from: str,
    to: str,
    subject: str,
    body: str,
    debug: bool = False,
) -> None:
    msg = build_message(mail_from, to, subject, body)
    context = ssl.create_default_context()
    if port == 465:
        if debug:
            print("[DEBUG] Mode: SMTP_SSL (implicit TLS)")
        with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as s:
            if debug:
                s.set_debuglevel(1)
                print("[DEBUG] Connected. Attempting AUTH/login...")
            if user and password:
                s.login(user, password)
            if debug:
                print("[DEBUG] AUTH succeeded. Sending message...")
            s.send_message(msg)
            if debug:
                print("[DEBUG] Message sent.")
        return

    if debug:
        print("[DEBUG] Mode: SMTP + STARTTLS")
    with smtplib.SMTP(host, port, timeout=20) as s:
        if debug:
            s.set_debuglevel(1)
            print("[DEBUG] Connected. Running EHLO...")
        s.ehlo()
        if debug:
            print("[DEBUG] Starting TLS...")
        s.starttls(context=context)
        if debug:
            print("[DEBUG] TLS established. Running EHLO again...")
        s.ehlo()
        if debug:
            print("[DEBUG] Attempting AUTH/login...")
        if user and password:
            s.login(user, password)
        if debug:
            print("[DEBUG] AUTH succeeded. Sending message...")
        s.send_message(msg)
        if debug:
            print("[DEBUG] Message sent.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone SMTP e-mail test")
    parser.add_argument("--to", required=True, help="Destination e-mail")
    parser.add_argument("--subject", default="Teste SMTP standalone")
    parser.add_argument("--message", default="Teste de SMTP standalone.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--host", default="")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--user", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--mail-from", default="")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose SMTP diagnostics and traceback on failure.",
    )
    args = parser.parse_args()

    cfg = get_cfg(args)
    host = cfg["host"].strip()
    mail_from = cfg["mail_from"].strip()
    user = cfg["user"].strip()
    password = cfg["password"].strip()
    try:
        port = int(cfg["port"])
    except ValueError as exc:
        raise SystemExit(f"SMTP_PORT invalida: {cfg['port']!r}") from exc

    if not host:
        raise SystemExit("SMTP_HOST nao informado (--host ou .env).")
    if not mail_from:
        raise SystemExit("MAIL_FROM nao informado (--mail-from ou .env).")

    print("=== SMTP test config ===")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"From: {mail_from}")
    print(f"To: {args.to.strip()}")
    print(f"User: {user or '(empty)'}")
    print(f"Password: {_mask_secret(password)}")
    print("========================")

    body = (
        f"{args.message}\n\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
        f"Host: {host}\nPort: {port}\nUser: {user or '(empty)'}\n"
    )

    try:
        send_smtp(
            host=host,
            port=port,
            user=user,
            password=password,
            mail_from=mail_from,
            to=args.to.strip(),
            subject=args.subject,
            body=body,
            debug=args.debug,
        )
    except Exception as exc:  # noqa: BLE001
        if args.debug:
            print("\n[DEBUG] Full traceback:")
            traceback.print_exc()
        raise SystemExit(f"Falha ao enviar e-mail: {type(exc).__name__}: {exc}") from exc

    print(f"E-mail enviado com sucesso para {args.to.strip()}")


if __name__ == "__main__":
    main()
