from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from vfs_monitor.models import AppointmentStatus, DetectionResult, MonitorState, TransitionDecision


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_state(path: str) -> MonitorState:
    file_path = Path(path)
    if not file_path.exists():
        return MonitorState(
            status=AppointmentStatus.UNKNOWN.value,
            fingerprint="",
            last_change=None,
            last_success=None,
            last_alert_fingerprint="",
            consecutive_errors=0,
        )
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return MonitorState(**data)


def save_state(path: str, state: MonitorState) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")


def update_heartbeat(path: str, checked_at: str) -> bool:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    day = checked_at[:10]
    old = file_path.read_text(encoding="utf-8").strip() if file_path.exists() else ""
    if old == day:
        return False
    file_path.write_text(day + "\n", encoding="utf-8")
    return True


def build_alert_fingerprint(result: DetectionResult, event_type: str) -> str:
    parts = [
        event_type,
        result.status.value,
        ",".join(result.available_dates),
        ",".join(result.available_times),
        result.fingerprint,
    ]
    return "|".join(parts)


def decide_transition(previous: MonitorState, result: DetectionResult) -> TransitionDecision:
    if result.status is AppointmentStatus.ERROR:
        return TransitionDecision(
            send_notification=True,
            event_type="technical_error",
            reason="technical error detected",
        )

    if previous.consecutive_errors >= 1:
        return TransitionDecision(
            send_notification=True,
            event_type="recovery",
            reason="monitor recovered after error",
            recovery=True,
        )

    previous_status = previous.status
    current_status = result.status.value

    if previous_status == current_status:
        if result.status is AppointmentStatus.AVAILABLE and previous.fingerprint != result.fingerprint:
            return TransitionDecision(
                send_notification=True,
                event_type="availability_changed",
                reason="available slots changed",
            )
        return TransitionDecision(
            send_notification=False,
            event_type="no_change",
            reason="no meaningful change",
        )

    if result.status is AppointmentStatus.AVAILABLE:
        return TransitionDecision(
            send_notification=True,
            event_type="availability_detected",
            reason="availability detected",
        )

    if result.status is AppointmentStatus.UNAVAILABLE and previous_status == AppointmentStatus.AVAILABLE.value:
        return TransitionDecision(
            send_notification=True,
            event_type="availability_closed",
            reason="availability disappeared",
        )

    if result.status is AppointmentStatus.UNKNOWN:
        return TransitionDecision(
            send_notification=True,
            event_type="warning_unknown",
            reason="page changed or no longer classifiable",
        )

    if result.status is AppointmentStatus.BLOCKED:
        return TransitionDecision(
            send_notification=True,
            event_type="warning_blocked",
            reason="anti-bot or access block detected",
        )

    if result.status is AppointmentStatus.AUTH_REQUIRED:
        return TransitionDecision(
            send_notification=True,
            event_type="auth_required",
            reason="manual authentication required",
        )

    return TransitionDecision(
        send_notification=False,
        event_type="state_change",
        reason="state changed without alert rule",
    )


def next_state(previous: MonitorState, result: DetectionResult, alert_fingerprint: str | None) -> MonitorState:
    consecutive_errors = previous.consecutive_errors + 1 if result.status is AppointmentStatus.ERROR else 0
    last_change = previous.last_change
    if previous.status != result.status.value or previous.fingerprint != result.fingerprint:
        last_change = result.checked_at
    last_success = previous.last_success
    if result.status is not AppointmentStatus.ERROR:
        last_success = result.checked_at
    return MonitorState(
        status=result.status.value,
        fingerprint=result.fingerprint,
        last_change=last_change,
        last_success=last_success,
        last_alert_fingerprint=alert_fingerprint or previous.last_alert_fingerprint,
        consecutive_errors=consecutive_errors,
    )

