from __future__ import annotations

import smtplib
from email.message import EmailMessage

import httpx

from vfs_monitor.config import Settings
from vfs_monitor.models import DetectionResult


def format_notification_message(result: DetectionResult, event_type: str) -> str:
    lines = [
        "SWEDEN VISA APPOINTMENT ALERT" if result.status.value == "available" else "VFS MONITOR NOTICE",
        "",
        f"Event: {event_type}",
        f"Status: {result.status.value.upper()}",
        f"Centre: {result.location}",
        f"Category: {result.category or 'unknown'}",
        f"Sub-category: {result.subcategory or 'unknown'}",
        f"Method: {result.method}",
        f"Checked: {result.checked_at}",
        f"Booking URL: {result.source_url}",
    ]
    if result.available_dates:
        lines.append("Available dates: " + ", ".join(result.available_dates))
    if result.available_times:
        lines.append("Available times: " + ", ".join(result.available_times))
    if result.signals:
        lines.append("Signals: " + "; ".join(result.signals))
    return "\n".join(lines)


def send_telegram_message(settings: Settings, text: str) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise ValueError("telegram secrets missing")
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
            },
        )
        response.raise_for_status()


def send_email_message(settings: Settings, subject: str, text: str) -> None:
    if not settings.gmail_address or not settings.gmail_app_password or not settings.alert_email_to:
        raise ValueError("gmail secrets missing")
    message = EmailMessage()
    message["From"] = settings.gmail_address
    message["To"] = settings.alert_email_to
    message["Subject"] = subject
    message.set_content(text)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(settings.gmail_address, settings.gmail_app_password)
        smtp.send_message(message)

