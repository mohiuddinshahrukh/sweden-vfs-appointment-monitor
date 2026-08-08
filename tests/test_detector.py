from __future__ import annotations

from pathlib import Path

from vfs_monitor.detector import detect_from_http
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

