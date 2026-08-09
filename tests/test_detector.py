from __future__ import annotations

from pathlib import Path

from vfs_monitor.detector import EXACT_UNAVAILABLE_MESSAGE, classify_visible_text, detect_from_http
from vfs_monitor.http_client import HttpFetchResult
from vfs_monitor.models import AppointmentStatus


def fixture_text(name: str) -> str:
    return Path("tests/fixtures", name).read_text(encoding="utf-8")


def detect(name: str, *, status_code: int = 200, content_type: str = "text/html") -> AppointmentStatus:
    result = detect_from_http(
        HttpFetchResult(
            status_code=status_code,
            url="https://example.test",
            text=fixture_text(name),
            headers={"content-type": content_type},
        ),
        location="Islamabad",
        category="Visit Family/Friends",
        subcategory="Tourist Visit",
        checked_at="2026-08-08T17:00:00Z",
        source_url="https://example.test",
    )
    return result.status


def test_available_fixture_is_available() -> None:
    assert detect("available.html") is AppointmentStatus.AVAILABLE


def test_unavailable_fixture_is_unavailable() -> None:
    assert detect("unavailable.html") is AppointmentStatus.UNAVAILABLE


def test_changed_fixture_is_unknown() -> None:
    assert detect("changed.html") is AppointmentStatus.UNKNOWN


def test_blocked_fixture_is_blocked() -> None:
    assert detect("blocked.html", status_code=403) is AppointmentStatus.BLOCKED


def test_exact_unavailable_message_is_unavailable() -> None:
    result = classify_visible_text(
        visible_text=EXACT_UNAVAILABLE_MESSAGE,
        method="Playwright persistent browser",
        location="Sweden Visa Application Centre - Islamabad",
        category="Default_Sweden_Pakistan",
        subcategory="Tourist Visit",
        checked_at="2026-08-09T10:00:00Z",
        source_url="https://example.test",
    )
    assert result.status is AppointmentStatus.UNAVAILABLE


def test_otp_text_is_auth_required() -> None:
    result = classify_visible_text(
        visible_text="Enter the OTP verification code sent to your email address.",
        method="Playwright persistent browser",
        location="Sweden Visa Application Centre - Islamabad",
        category="Default_Sweden_Pakistan",
        subcategory="Tourist Visit",
        checked_at="2026-08-09T10:00:00Z",
        source_url="https://example.test",
        current_url="https://visa.vfsglobal.com/login",
    )
    assert result.status is AppointmentStatus.AUTH_REQUIRED

