from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    booking_url: str
    country: str
    location: str
    category: str | None
    debug: bool
    use_playwright: bool
    vfs_email: str | None
    vfs_password: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    gmail_address: str | None
    gmail_app_password: str | None
    alert_email_to: str | None
    state_file: str
    heartbeat_file: str


def load_settings() -> Settings:
    return Settings(
        booking_url=os.getenv(
            "VFS_BOOKING_URL",
            "https://visa.vfsglobal.com/pak/en/swe/book-an-appointment",
        ),
        country=os.getenv("VFS_COUNTRY", "Sweden"),
        location=os.getenv("VFS_LOCATION", "Islamabad"),
        category=os.getenv("VFS_CATEGORY"),
        debug=_as_bool(os.getenv("DEBUG"), default=False),
        use_playwright=_as_bool(os.getenv("VFS_USE_PLAYWRIGHT"), default=False),
        vfs_email=os.getenv("VFS_EMAIL"),
        vfs_password=os.getenv("VFS_PASSWORD"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        gmail_address=os.getenv("GMAIL_ADDRESS"),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD"),
        alert_email_to=os.getenv("ALERT_EMAIL_TO"),
        state_file=os.getenv("VFS_STATE_FILE", "state/status.json"),
        heartbeat_file=os.getenv("VFS_HEARTBEAT_FILE", "state/heartbeat.txt"),
    )

