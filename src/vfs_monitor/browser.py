from __future__ import annotations

from pathlib import Path

from vfs_monitor.detector import classify_visible_text
from vfs_monitor.models import AppointmentStatus, DetectionResult


def _import_playwright():
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        return None, None, exc
    return sync_playwright, PlaywrightTimeoutError, None


def _playwright_error_result(
    *,
    booking_url: str,
    location: str,
    category: str | None,
    subcategory: str | None,
    checked_at: str,
    message: str,
) -> DetectionResult:
    return DetectionResult(
        status=AppointmentStatus.ERROR,
        location=location,
        category=category,
        subcategory=subcategory,
        available_dates=[],
        available_times=[],
        signals=[message],
        fingerprint=f"playwright-error:{message}",
        method="Playwright persistent browser",
        checked_at=checked_at,
        source_url=booking_url,
    )


def _launch_persistent_context(
    *,
    playwright,
    browser_user_data_dir: str,
    browser_channel: str | None,
    browser_executable_path: str | None,
    headless: bool,
):
    launch_kwargs = {
        "user_data_dir": str(Path(browser_user_data_dir).resolve()),
        "headless": headless,
    }
    if browser_channel:
        launch_kwargs["channel"] = browser_channel
    if browser_executable_path:
        launch_kwargs["executable_path"] = browser_executable_path
    return playwright.chromium.launch_persistent_context(**launch_kwargs)


def detect_with_playwright(
    *,
    booking_url: str,
    location: str,
    category: str | None,
    subcategory: str | None,
    checked_at: str,
    browser_user_data_dir: str,
    browser_channel: str | None,
    browser_executable_path: str | None,
    browser_headless: bool,
    browser_timeout_ms: int,
) -> DetectionResult:
    sync_playwright, playwright_timeout_error, import_error = _import_playwright()
    if import_error:
        return _playwright_error_result(
            booking_url=booking_url,
            location=location,
            category=category,
            subcategory=subcategory,
            checked_at=checked_at,
            message=f"playwright not installed: {import_error}",
        )

    with sync_playwright() as playwright:  # pragma: no cover
        context = _launch_persistent_context(
            playwright=playwright,
            browser_user_data_dir=browser_user_data_dir,
            browser_channel=browser_channel,
            browser_executable_path=browser_executable_path,
            headless=browser_headless,
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(booking_url, wait_until="domcontentloaded", timeout=browser_timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=min(browser_timeout_ms, 15000))
            except playwright_timeout_error:
                pass
            page.wait_for_timeout(3000)
            visible_text = page.locator("body").inner_text(timeout=5000)
            title = page.title()
            current_url = page.url
            signals: list[str] = []
            lowered = visible_text.lower()
            if location and location.lower() in lowered:
                signals.append("expected centre label found")
            if category and category.lower() in lowered:
                signals.append("expected category label found")
            if subcategory and subcategory.lower() in lowered:
                signals.append("expected sub-category label found")
            return classify_visible_text(
                visible_text=" ".join(item for item in [title, visible_text] if item),
                method="Playwright persistent browser",
                location=location,
                category=category,
                subcategory=subcategory,
                checked_at=checked_at,
                source_url=booking_url,
                current_url=current_url,
                extra_signals=signals,
            )
        except playwright_timeout_error as exc:
            return _playwright_error_result(
                booking_url=booking_url,
                location=location,
                category=category,
                subcategory=subcategory,
                checked_at=checked_at,
                message=f"browser timeout: {exc}",
            )
        except Exception as exc:  # pragma: no cover
            return _playwright_error_result(
                booking_url=booking_url,
                location=location,
                category=category,
                subcategory=subcategory,
                checked_at=checked_at,
                message=f"browser error: {type(exc).__name__}: {exc}",
            )
        finally:
            context.close()


def open_persistent_browser_for_manual_login(
    *,
    booking_url: str,
    browser_user_data_dir: str,
    browser_channel: str | None,
    browser_executable_path: str | None,
    timeout_ms: int,
    headless: bool,
) -> None:
    sync_playwright, playwright_timeout_error, import_error = _import_playwright()
    if import_error:
        raise RuntimeError(f"playwright not installed: {import_error}") from import_error

    with sync_playwright() as playwright:  # pragma: no cover
        context = _launch_persistent_context(
            playwright=playwright,
            browser_user_data_dir=browser_user_data_dir,
            browser_channel=browser_channel,
            browser_executable_path=browser_executable_path,
            headless=headless,
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(booking_url, wait_until="domcontentloaded", timeout=timeout_ms)
            print(f"Persistent profile: {Path(browser_user_data_dir).resolve()}")
            print("Complete the VFS login manually in this browser window.")
            print("Leave the terminal running. Press Ctrl+C after you have reached the appointment page.")
            while True:
                try:
                    page.wait_for_timeout(1000)
                except playwright_timeout_error:
                    continue
        finally:
            context.close()
