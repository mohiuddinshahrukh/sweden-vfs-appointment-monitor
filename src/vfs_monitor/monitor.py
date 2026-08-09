from __future__ import annotations

from dataclasses import dataclass

from vfs_monitor.browser import detect_with_attached_browser, detect_with_playwright
from vfs_monitor.config import Settings
from vfs_monitor.detector import detect_from_http
from vfs_monitor.http_client import fetch_booking_page
from vfs_monitor.models import DetectionResult
from vfs_monitor.notifications import (
    format_notification_message,
    send_email_message,
    send_telegram_message,
)
from vfs_monitor.state import (
    build_alert_fingerprint,
    decide_transition,
    load_state,
    next_state,
    save_state,
    update_heartbeat,
    utc_now_iso,
)


@dataclass(slots=True)
class MonitorRunResult:
    detection: DetectionResult
    notification_sent: bool
    heartbeat_updated: bool
    decision_reason: str
    event_type: str


def perform_check(settings: Settings) -> DetectionResult:
    checked_at = utc_now_iso()
    if settings.check_method == "attach":
        return detect_with_attached_browser(
            booking_url=settings.booking_url,
            location=settings.location,
            category=settings.category,
            subcategory=settings.subcategory,
            checked_at=checked_at,
            browser_attach_url=settings.browser_attach_url,
            browser_timeout_ms=settings.browser_timeout_ms,
            vfs_email=settings.vfs_email,
            vfs_password=settings.vfs_password,
        )
    if settings.check_method == "browser":
        return detect_with_playwright(
            booking_url=settings.booking_url,
            location=settings.location,
            category=settings.category,
            subcategory=settings.subcategory,
            checked_at=checked_at,
            browser_user_data_dir=settings.browser_user_data_dir,
            browser_profile_directory=settings.browser_profile_directory,
            browser_channel=settings.browser_channel,
            browser_executable_path=settings.browser_executable_path,
            browser_headless=settings.browser_headless,
            browser_timeout_ms=settings.browser_timeout_ms,
        )
    fetch_result = fetch_booking_page(settings.booking_url)
    detection = detect_from_http(
        fetch_result,
        location=settings.location,
        category=settings.category,
        subcategory=settings.subcategory,
        checked_at=checked_at,
        source_url=settings.booking_url,
    )
    if settings.check_method == "auto" and detection.status.value in {"unknown", "blocked"}:
        return detect_with_playwright(
            booking_url=settings.booking_url,
            location=settings.location,
            category=settings.category,
            subcategory=settings.subcategory,
            checked_at=checked_at,
            browser_user_data_dir=settings.browser_user_data_dir,
            browser_profile_directory=settings.browser_profile_directory,
            browser_channel=settings.browser_channel,
            browser_executable_path=settings.browser_executable_path,
            browser_headless=settings.browser_headless,
            browser_timeout_ms=settings.browser_timeout_ms,
        )
    return detection


def run_monitor(
    settings: Settings,
    *,
    notify: bool,
    persist_state: bool,
    update_daily_heartbeat: bool,
) -> MonitorRunResult:
    previous = load_state(settings.state_file)
    detection = perform_check(settings)
    decision = decide_transition(previous, detection)
    alert_fingerprint = build_alert_fingerprint(detection, decision.event_type)
    should_send = notify and decision.send_notification and previous.last_alert_fingerprint != alert_fingerprint

    if should_send:
        body = format_notification_message(detection, decision.event_type)
        sent_any = False
        if settings.telegram_bot_token and settings.telegram_chat_id:
            send_telegram_message(settings, body)
            sent_any = True
        if settings.gmail_address and settings.gmail_app_password and settings.alert_email_to:
            send_email_message(
                settings,
                subject="URGENT: Sweden VFS appointment availability detected"
                if detection.status.value == "available"
                else "VFS monitor notice",
                text=body,
            )
            sent_any = True
        if not sent_any:
            should_send = False

    new_state = next_state(
        previous,
        detection,
        alert_fingerprint if should_send else None,
    )
    heartbeat_updated = False
    if persist_state:
        save_state(settings.state_file, new_state)
        if update_daily_heartbeat:
            heartbeat_updated = update_heartbeat(settings.heartbeat_file, detection.checked_at)

    return MonitorRunResult(
        detection=detection,
        notification_sent=should_send,
        heartbeat_updated=heartbeat_updated,
        decision_reason=decision.reason,
        event_type=decision.event_type,
    )
