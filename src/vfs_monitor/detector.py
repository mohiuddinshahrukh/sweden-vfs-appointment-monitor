from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable

from bs4 import BeautifulSoup

from vfs_monitor.http_client import HttpFetchResult
from vfs_monitor.models import AppointmentStatus, DetectionResult

EXACT_UNAVAILABLE_MESSAGE = (
    "We are sorry but no appointment slots are currently available. "
    "New slots open at regular intervals, please try again later"
)

_UNAVAILABLE_PATTERNS = (
    EXACT_UNAVAILABLE_MESSAGE.lower(),
    "no appointment slots",
    "no available dates",
    "fully booked",
    "no slots available",
    "currently no appointments available",
)
_BLOCKED_PATTERNS = (
    "captcha",
    "recaptcha",
    "cloudflare",
    "access denied",
    "bot verification",
    "security challenge",
    "are you human",
    "verify you are human",
    '"code": "403201"',
)
_AUTH_PATTERNS = (
    "sign in",
    "log in",
    "login",
    "email",
    "password",
    "forgot password",
    "one time password",
    "otp",
    "verification code",
)
_AVAILABILITY_PATTERNS = (
    "appointment slot",
    "available slot",
    "available appointment",
    "select date",
    "select time",
    "time slot",
)
_LONG_DATE_PATTERN = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{1,2},\s+20\d{2}\b",
    re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def _hash_parts(parts: Iterable[str]) -> str:
    joined = "||".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _extract_dates(text: str) -> list[str]:
    iso_matches = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    long_matches = _LONG_DATE_PATTERN.findall(text)
    return sorted(set([*iso_matches, *long_matches]))


def _extract_times(text: str) -> list[str]:
    matches = re.findall(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", text)
    return sorted(set(matches))


def _build_detection(
    *,
    status: AppointmentStatus,
    location: str,
    category: str | None,
    subcategory: str | None,
    available_dates: list[str],
    available_times: list[str],
    signals: list[str],
    fingerprint_parts: list[str],
    method: str,
    checked_at: str,
    source_url: str,
) -> DetectionResult:
    return DetectionResult(
        status=status,
        location=location,
        category=category,
        subcategory=subcategory,
        available_dates=available_dates,
        available_times=available_times,
        signals=signals,
        fingerprint=_hash_parts(fingerprint_parts),
        method=method,
        checked_at=checked_at,
        source_url=source_url,
    )


def classify_visible_text(
    *,
    visible_text: str,
    method: str,
    location: str,
    category: str | None,
    subcategory: str | None,
    checked_at: str,
    source_url: str,
    status_code: int | None = None,
    current_url: str | None = None,
    extra_signals: list[str] | None = None,
) -> DetectionResult:
    normalized = _normalize_text(visible_text)
    lowered = normalized.lower()
    signals = list(extra_signals or [])
    dates = _extract_dates(normalized)
    times = _extract_times(normalized)

    if status_code == 403 or any(pattern in lowered for pattern in _BLOCKED_PATTERNS):
        if status_code is not None:
            signals.append(f"http_status={status_code}")
        if "403201" in lowered:
            signals.append("cloudflare_code=403201")
        return _build_detection(
            status=AppointmentStatus.BLOCKED,
            location=location,
            category=category,
            subcategory=subcategory,
            available_dates=[],
            available_times=[],
            signals=signals,
            fingerprint_parts=["blocked", *signals, source_url, current_url or ""],
            method=method,
            checked_at=checked_at,
            source_url=source_url,
        )

    if EXACT_UNAVAILABLE_MESSAGE.lower() in lowered:
        signals.append("exact unavailable message found")
        return _build_detection(
            status=AppointmentStatus.UNAVAILABLE,
            location=location,
            category=category,
            subcategory=subcategory,
            available_dates=[],
            available_times=[],
            signals=signals,
            fingerprint_parts=["unavailable", EXACT_UNAVAILABLE_MESSAGE],
            method=method,
            checked_at=checked_at,
            source_url=source_url,
        )

    if any(pattern in lowered for pattern in _AUTH_PATTERNS):
        signals.append("manual authentication step detected")
        if current_url:
            signals.append(f"current_url={current_url}")
        return _build_detection(
            status=AppointmentStatus.AUTH_REQUIRED,
            location=location,
            category=category,
            subcategory=subcategory,
            available_dates=[],
            available_times=[],
            signals=signals,
            fingerprint_parts=["auth_required", normalized[:500], current_url or ""],
            method=method,
            checked_at=checked_at,
            source_url=source_url,
        )

    if dates or times or any(pattern in lowered for pattern in _AVAILABILITY_PATTERNS):
        signals.append("potential selectable appointment signal found")
        return _build_detection(
            status=AppointmentStatus.AVAILABLE,
            location=location,
            category=category,
            subcategory=subcategory,
            available_dates=dates,
            available_times=times,
            signals=signals,
            fingerprint_parts=["available", *dates, *times, normalized[:500]],
            method=method,
            checked_at=checked_at,
            source_url=source_url,
        )

    if any(pattern in lowered for pattern in _UNAVAILABLE_PATTERNS):
        signals.append("confirmed no-slot message found")
        return _build_detection(
            status=AppointmentStatus.UNAVAILABLE,
            location=location,
            category=category,
            subcategory=subcategory,
            available_dates=[],
            available_times=[],
            signals=signals,
            fingerprint_parts=["unavailable", normalized[:500]],
            method=method,
            checked_at=checked_at,
            source_url=source_url,
        )

    return _build_detection(
        status=AppointmentStatus.UNKNOWN,
        location=location,
        category=category,
        subcategory=subcategory,
        available_dates=[],
        available_times=[],
        signals=signals or ["unable to classify safely"],
        fingerprint_parts=["unknown", normalized[:1500], current_url or ""],
        method=method,
        checked_at=checked_at,
        source_url=source_url,
    )


def detect_from_http(
    fetch_result: HttpFetchResult,
    *,
    location: str,
    category: str | None,
    subcategory: str | None,
    checked_at: str,
    source_url: str,
) -> DetectionResult:
    if fetch_result.error:
        return _build_detection(
            status=AppointmentStatus.ERROR,
            location=location,
            category=category,
            subcategory=subcategory,
            available_dates=[],
            available_times=[],
            signals=[fetch_result.error],
            fingerprint_parts=["error", fetch_result.error, source_url],
            method="HTTP",
            checked_at=checked_at,
            source_url=source_url,
        )

    raw_text = fetch_result.text
    lowered = raw_text.lower()

    if fetch_result.status_code == 403 or any(pattern in lowered for pattern in _BLOCKED_PATTERNS):
        return classify_visible_text(
            visible_text=raw_text,
            method="HTTP",
            location=location,
            category=category,
            subcategory=subcategory,
            checked_at=checked_at,
            source_url=source_url,
            status_code=fetch_result.status_code,
            current_url=fetch_result.url,
        )

    content_type = fetch_result.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = json.loads(raw_text)
            return _build_detection(
                status=AppointmentStatus.UNKNOWN,
                location=location,
                category=category,
                subcategory=subcategory,
                available_dates=[],
                available_times=[],
                signals=[f"unexpected_json_status={fetch_result.status_code}"],
                fingerprint_parts=[
                    "unknown",
                    str(fetch_result.status_code),
                    json.dumps(payload, sort_keys=True),
                ],
                method="HTTP",
                checked_at=checked_at,
                source_url=source_url,
            )
        except json.JSONDecodeError:
            pass

    soup = BeautifulSoup(raw_text, "html.parser")
    visible_text = _normalize_text(soup.get_text(" ", strip=True))
    semantic_text = " ".join(item for item in [soup.title.get_text(" ", strip=True) if soup.title else "", visible_text] if item)
    result = classify_visible_text(
        visible_text=semantic_text,
        method="HTTP",
        location=location,
        category=category,
        subcategory=subcategory,
        checked_at=checked_at,
        source_url=source_url,
        status_code=fetch_result.status_code,
        current_url=fetch_result.url,
    )
    if result.status is AppointmentStatus.UNKNOWN and not result.signals:
        result.signals.append("unable to classify safely")
    return result

