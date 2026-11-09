import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger("moods.email")


def send_email(to: str, subject: str, body: str) -> None:
    """لو SMTP مش متظبط بيطبع الإيميل في الكونسول (مفيد في التطوير)."""
    if not settings.SMTP_HOST:
        log.warning("EMAIL (console) -> %s | %s\n%s", to, subject, body)
        return
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.SMTP_FROM, to, subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
    except Exception:  # noqa: BLE001
        log.exception("Failed to send email to %s", to)
