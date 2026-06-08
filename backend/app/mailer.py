"""Envío de correo con adjunto vía SMTP (smtplib)."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .config import settings


def send_email_with_pdf(to_email: str, subject: str, body: str, pdf_bytes: bytes, filename: str):
    if not settings.smtp_host or not to_email:
        raise RuntimeError("SMTP no configurado o destinatario vacío.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg.set_content(body)
    msg.add_attachment(
        pdf_bytes, maintype="application", subtype="pdf", filename=filename
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
