from __future__ import annotations

from vfs_monitor.models import AppointmentStatus, DetectionResult


def detect_with_playwright(
    *,
    booking_url: str,
    location: str,
    category: str | None,
    checked_at: str,
) -> DetectionResult:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        return DetectionResult(
            status=AppointmentStatus.ERROR,
            location=location,
            category=category,
            available_dates=[],
            available_times=[],
            signals=[f"playwright not installed: {exc}"],
            fingerprint=f"playwright-import-error:{type(exc).__name__}",
            method="Playwright",
            checked_at=checked_at,
            source_url=booking_url,
        )

    with sync_playwright() as playwright:  # pragma: no cover
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            response = page.goto(booking_url, wait_until="networkidle", timeout=90000)
            text = page.locator("body").inner_text()
            lowered = text.lower()
            signals = [f"http_status={response.status if response else 'unknown'}"]
            if any(token in lowered for token in ("captcha", "cloudflare", "access denied")):
                status = AppointmentStatus.BLOCKED
                signals.append("challenge text found in browser")
            elif any(token in lowered for token in ("sign in", "password", "forgot password")):
                status = AppointmentStatus.AUTH_REQUIRED
                signals.append("login text found in browser")
            else:
                status = AppointmentStatus.UNKNOWN
                signals.append("browser flow loaded but no safe classifier implemented")
            return DetectionResult(
                status=status,
                location=location,
                category=category,
                available_dates=[],
                available_times=[],
                signals=signals,
                fingerprint=f"playwright:{status.value}:{hash(text[:1000])}",
                method="Playwright",
                checked_at=checked_at,
                source_url=booking_url,
            )
        finally:
            browser.close()

