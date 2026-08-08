from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable

from bs4 import BeautifulSoup

from vfs_monitor.http_client import HttpFetchResult
from vfs_monitor.models import AppointmentStatus, DetectionResult

_UNAVAILABLE_PATTERNS = (
    "no appointment slots",
    "no available dates",
    "fully booked",
    "no slots available",
    "currently no appointments available",
)
_BLOCKED_PATTERNS = (
    "captcha",
    "cloudflare",
    "access denied",
    "bot verification",
    "security challenge",
    '"code": "403201"',
)
_AUTH_PATTERNS = (
    "sign in",
    "log in",
    "email",
    "password",
    "forgot password",
)


def _normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def _hash_parts(parts: Iterable[str]) -> str:
    joined = "||".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _extract_dates(text: str) -> list[str]:
    matches = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    return sorted(set(matches))


def _extract_times(text: str) -> list[str]:
    matches = re.findall(r"\b(?:[01]\d|2[0-3]):[0-5]\d\b", text)
    return sorted(set(matches))


def detect_from_http(
    fetch_result: HttpFetchResult,
    *,
    location: str,
    category: str | None,
    checked_at: str,
    source_url: str,
) -> DetectionResult:
    if fetch_result.error:
        fingerprint = _hash_parts(["error", fetch_result.error, source_url])
        return DetectionResult(
            status=AppointmentStatus.ERROR,
            location=location,
            category=category,
            available_dates=[],
            available_times=[],
            signals=[fetch_result.error],
            fingerprint=fingerprint,
            method="HTTP",
            checked_at=checked_at,
            source_url=source_url,
        )

    raw_text = fetch_result.text
    lowered = raw_text.lower()
    signals: list[str] = []

    if fetch_result.status_code == 403 or any(pattern in lowered for pattern in _BLOCKED_PATTERNS):
        signals.append(f"http_status={fetch_result.status_code}")
        if '"code": "403201"' in lowered:
            signals.append("cloudflare_code=403201")
        fingerprint = _hash_parts(["blocked", *signals, source_url])
        return DetectionResult(
            status=AppointmentStatus.BLOCKED,
            location=location,
            category=category,
            available_dates=[],
            available_times=[],
            signals=signals,
            fingerprint=fingerprint,
            method="HTTP",
            checked_at=checked_at,
            source_url=source_url,
        )

    content_type = fetch_result.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = json.loads(raw_text)
            fingerprint = _hash_parts(
                ["unknown", str(fetch_result.status_code), json.dumps(payload, sort_keys=True)]
            )
            return DetectionResult(
                status=AppointmentStatus.UNKNOWN,
                location=location,
                category=category,
                available_dates=[],
                available_times=[],
                signals=[f"unexpected_json_status={fetch_result.status_code}"],
                fingerprint=fingerprint,
                method="HTTP",
                checked_at=checked_at,
                source_url=source_url,
            )
        except json.JSONDecodeError:
            pass

    soup = BeautifulSoup(raw_text, "html.parser")
    visible_text = _normalize_text(soup.get_text(" ", strip=True))
    visible_lower = visible_text.lower()
    dates = _extract_dates(visible_text)
    times = _extract_times(visible_text)

    if dates or times:
        signals.append("selectable date or time pattern found")
        fingerprint = _hash_parts(["available", *dates, *times, visible_text[:500]])
        return DetectionResult(
            status=AppointmentStatus.AVAILABLE,
            location=location,
            category=category,
            available_dates=dates,
            available_times=times,
            signals=signals,
            fingerprint=fingerprint,
            method="HTTP",
            checked_at=checked_at,
            source_url=source_url,
        )

    if any(pattern in visible_lower for pattern in _UNAVAILABLE_PATTERNS):
        signals.append("confirmed no-slot message found")
        fingerprint = _hash_parts(["unavailable", visible_text[:500]])
        return DetectionResult(
            status=AppointmentStatus.UNAVAILABLE,
            location=location,
            category=category,
            available_dates=[],
            available_times=[],
            signals=signals,
            fingerprint=fingerprint,
            method="HTTP",
            checked_at=checked_at,
            source_url=source_url,
        )

    if any(pattern in visible_lower for pattern in _AUTH_PATTERNS):
        signals.append("login form text found")
        fingerprint = _hash_parts(["auth_required", visible_text[:500]])
        return DetectionResult(
            status=AppointmentStatus.AUTH_REQUIRED,
            location=location,
            category=category,
            available_dates=[],
            available_times=[],
            signals=signals,
            fingerprint=fingerprint,
            method="HTTP",
            checked_at=checked_at,
            source_url=source_url,
        )

    semantic_text = " ".join(
        item
        for item in [
            soup.title.get_text(" ", strip=True) if soup.title else "",
            visible_text[:1500],
        ]
        if item
    )
    fingerprint = _hash_parts(["unknown", semantic_text])
    return DetectionResult(
        status=AppointmentStatus.UNKNOWN,
        location=location,
        category=category,
        available_dates=[],
        available_times=[],
        signals=["unable to classify safely"],
        fingerprint=fingerprint,
        method="HTTP",
        checked_at=checked_at,
        source_url=source_url,
    )

