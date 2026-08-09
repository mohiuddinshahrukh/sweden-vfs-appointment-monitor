from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    check_method: str
    booking_url: str
    country: str
    location: str
    category: str | None
    subcategory: str | None
    debug: bool
    vfs_email: str | None
    vfs_password: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    gmail_address: str | None
    gmail_app_password: str | None
    alert_email_to: str | None
    state_file: str
    heartbeat_file: str
    browser_user_data_dir: str
    browser_channel: str | None
    browser_executable_path: str | None
    browser_headless: bool
    browser_timeout_ms: int


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        check_method=os.getenv("VFS_CHECK_METHOD", "browser").strip().lower(),
        booking_url=os.getenv(
            "VFS_BOOKING_URL",
            "https://visa.vfsglobal.com/pak/en/swe/book-an-appointment",
        ),
        country=os.getenv("VFS_COUNTRY", "Sweden"),
        location=os.getenv("VFS_LOCATION", "Sweden Visa Application Centre - Islamabad"),
        category=os.getenv("VFS_CATEGORY", "Default_Sweden_Pakistan"),
        subcategory=os.getenv("VFS_SUBCATEGORY", "Family Visit"),
        debug=_as_bool(os.getenv("DEBUG"), default=False),
        vfs_email=os.getenv("VFS_EMAIL"),
        vfs_password=os.getenv("VFS_PASSWORD"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        gmail_address=os.getenv("GMAIL_ADDRESS"),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD"),
        alert_email_to=os.getenv("ALERT_EMAIL_TO"),
        state_file=os.getenv("VFS_STATE_FILE", "state/status.json"),
        heartbeat_file=os.getenv("VFS_HEARTBEAT_FILE", "state/heartbeat.txt"),
        browser_user_data_dir=os.getenv("VFS_BROWSER_USER_DATA_DIR", "browser-profile"),
        browser_channel=os.getenv("VFS_BROWSER_CHANNEL", "chrome"),
        browser_executable_path=os.getenv("VFS_BROWSER_EXECUTABLE_PATH"),
        browser_headless=_as_bool(os.getenv("VFS_BROWSER_HEADLESS"), default=True),
        browser_timeout_ms=int(os.getenv("VFS_BROWSER_TIMEOUT_MS", "90000")),
    )

