from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AppointmentStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    AUTH_REQUIRED = "auth_required"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass(slots=True)
class DetectionResult:
    status: AppointmentStatus
    location: str
    category: str | None
    available_dates: list[str]
    available_times: list[str]
    signals: list[str]
    fingerprint: str
    method: str
    checked_at: str
    source_url: str


@dataclass(slots=True)
class MonitorState:
    status: str
    fingerprint: str
    last_change: str | None
    last_success: str | None
    last_alert_fingerprint: str
    consecutive_errors: int = 0


@dataclass(slots=True)
class TransitionDecision:
    send_notification: bool
    event_type: str
    reason: str
    recovery: bool = False

