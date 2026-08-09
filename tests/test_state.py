from __future__ import annotations

from vfs_monitor.models import AppointmentStatus, DetectionResult, MonitorState
from vfs_monitor.state import build_alert_fingerprint, decide_transition, next_state


def make_result(
    status: AppointmentStatus,
    *,
    fingerprint: str,
    dates: list[str] | None = None,
) -> DetectionResult:
    return DetectionResult(
        status=status,
        location="Islamabad",
        category="Visit Family/Friends",
        subcategory="Tourist Visit",
        available_dates=dates or [],
        available_times=[],
        signals=[],
        fingerprint=fingerprint,
        method="HTTP",
        checked_at="2026-08-08T17:00:00Z",
        source_url="https://example.test",
    )


def test_same_available_state_with_new_dates_triggers_notification() -> None:
    previous = MonitorState(
        status="available",
        fingerprint="old",
        last_change=None,
        last_success=None,
        last_alert_fingerprint="",
        consecutive_errors=0,
    )
    decision = decide_transition(
        previous,
        make_result(AppointmentStatus.AVAILABLE, fingerprint="new", dates=["2026-08-21", "2026-08-22"]),
    )
    assert decision.send_notification is True
    assert decision.event_type == "availability_changed"


def test_first_error_triggers_technical_alert() -> None:
    previous = MonitorState(
        status="unavailable",
        fingerprint="old-ok",
        last_change=None,
        last_success=None,
        last_alert_fingerprint="",
        consecutive_errors=0,
    )
    decision = decide_transition(
        previous,
        make_result(AppointmentStatus.ERROR, fingerprint="err"),
    )
    assert decision.send_notification is True
    assert decision.event_type == "technical_error"


def test_recovery_after_errors_sends_recovery() -> None:
    previous = MonitorState(
        status="error",
        fingerprint="old",
        last_change=None,
        last_success=None,
        last_alert_fingerprint="",
        consecutive_errors=1,
    )
    decision = decide_transition(
        previous,
        make_result(AppointmentStatus.UNAVAILABLE, fingerprint="ok"),
    )
    assert decision.send_notification is True
    assert decision.recovery is True


def test_next_state_resets_error_counter_on_success() -> None:
    previous = MonitorState(
        status="error",
        fingerprint="old",
        last_change=None,
        last_success=None,
        last_alert_fingerprint="",
        consecutive_errors=3,
    )
    result = make_result(AppointmentStatus.UNAVAILABLE, fingerprint="ok")
    state = next_state(previous, result, build_alert_fingerprint(result, "recovery"))
    assert state.consecutive_errors == 0
    assert state.status == "unavailable"

