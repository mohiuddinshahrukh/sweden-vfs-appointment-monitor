from __future__ import annotations

from vfs_monitor.models import AppointmentStatus, DetectionResult
from vfs_monitor.notifications import format_notification_message


def test_notification_contains_dates_when_present() -> None:
    result = DetectionResult(
        status=AppointmentStatus.AVAILABLE,
        location="Islamabad",
        category="Visit Family/Friends",
        subcategory="Family Visit",
        available_dates=["2026-08-21"],
        available_times=["09:30"],
        signals=["selectable appointment date found"],
        fingerprint="abc",
        method="HTTP",
        checked_at="2026-08-08T17:00:00Z",
        source_url="https://example.test",
    )
    message = format_notification_message(result, "availability_detected")
    assert "2026-08-21" in message
    assert "09:30" in message
    assert "Islamabad" in message
    assert "Family Visit" in message

