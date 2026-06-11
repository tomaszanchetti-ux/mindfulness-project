"""Envío de email (WS20). Espejo del patrón storage/auth: un modo por entorno.

  off  → no manda nada (default; dev y tests no tocan la red).
  log  → imprime a stdout (debug local del contenido).
  smtp → envío real por relay SMTP (SendGrid: host smtp.sendgrid.net,
         user literal "apikey", pass = la API key).

Una sola función pública. Quien llama no sabe ni le importa el modo.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..config import settings


def enviar_email(destino: str, asunto: str, texto: str, html: str) -> bool:
    """Manda un email. Devuelve True si se envió (o se simuló), False si falló.

    Nunca levanta: un email caído no debe tumbar el barrido del aviso diario.
    """
    if settings.email_mode == "off":
        return False
    if settings.email_mode == "log":
        print(f"[email:log] para={destino} asunto={asunto!r}", flush=True)
        return True

    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.set_content(texto)
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001 — el barrido sigue con el resto
        print(f"[email:error] para={destino}: {exc}", flush=True)
        return False
