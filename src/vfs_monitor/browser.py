from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

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
    method: str = "Playwright persistent browser",
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
        method=method,
        checked_at=checked_at,
        source_url=booking_url,
    )


def _build_browser_detection(
    *,
    page,
    booking_url: str,
    location: str,
    category: str | None,
    subcategory: str | None,
    checked_at: str,
    method: str,
    extra_signals: list[str] | None = None,
) -> DetectionResult:
    visible_text = page.locator("body").inner_text(timeout=5000)
    title = page.title()
    current_url = page.url
    signals = list(extra_signals or [])
    lowered = visible_text.lower()
    if location and location.lower() in lowered:
        signals.append("expected centre label found")
    if category and category.lower() in lowered:
        signals.append("expected category label found")
    if subcategory and subcategory.lower() in lowered:
        signals.append("expected sub-category label found")
    return classify_visible_text(
        visible_text=" ".join(item for item in [title, visible_text] if item),
        method=method,
        location=location,
        category=category,
        subcategory=subcategory,
        checked_at=checked_at,
        source_url=booking_url,
        current_url=current_url,
        extra_signals=signals,
    )


def _login_url_from_booking_url(booking_url: str) -> str:
    parts = urlsplit(booking_url)
    path = parts.path.rstrip("/")
    if path.endswith("/book-an-appointment"):
        path = path[: -len("/book-an-appointment")] + "/login"
    else:
        path = "/login"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _launch_persistent_context(
    *,
    playwright,
    browser_user_data_dir: str,
    browser_profile_directory: str | None,
    browser_channel: str | None,
    browser_executable_path: str | None,
    headless: bool,
):
    launch_kwargs = {
        "user_data_dir": str(Path(browser_user_data_dir).resolve()),
        "headless": headless,
    }
    args: list[str] = []
    if browser_profile_directory:
        args.append(f"--profile-directory={browser_profile_directory}")
    if args:
        launch_kwargs["args"] = args
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
    browser_profile_directory: str | None,
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
            method="Playwright attached browser",
        )

    with sync_playwright() as playwright:  # pragma: no cover
        context = _launch_persistent_context(
            playwright=playwright,
            browser_user_data_dir=browser_user_data_dir,
            browser_profile_directory=browser_profile_directory,
            browser_channel=browser_channel,
            browser_executable_path=browser_executable_path,
            headless=browser_headless,
        )
        for existing_page in list(context.pages):
            try:
                if existing_page.url in {"about:blank", "chrome://newtab/"}:
                    existing_page.close()
            except Exception:
                pass
        page = context.new_page()
        try:
            page.goto(booking_url, wait_until="domcontentloaded", timeout=browser_timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=min(browser_timeout_ms, 15000))
            except playwright_timeout_error:
                pass
            page.wait_for_timeout(3000)
            return _build_browser_detection(
                page=page,
                booking_url=booking_url,
                location=location,
                category=category,
                subcategory=subcategory,
                checked_at=checked_at,
                method="Playwright persistent browser",
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


def detect_with_attached_browser(
    *,
    booking_url: str,
    location: str,
    category: str | None,
    subcategory: str | None,
    checked_at: str,
    browser_attach_url: str | None,
    browser_timeout_ms: int,
    vfs_email: str | None,
    vfs_password: str | None,
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
    if not browser_attach_url:
        return _playwright_error_result(
            booking_url=booking_url,
            location=location,
            category=category,
            subcategory=subcategory,
            checked_at=checked_at,
            message="browser attach url missing",
            method="Playwright attached browser",
        )

    with sync_playwright() as playwright:  # pragma: no cover
        browser = None
        try:
            browser = playwright.chromium.connect_over_cdp(browser_attach_url, timeout=browser_timeout_ms)
            contexts = browser.contexts
            if not contexts:
                return _playwright_error_result(
                    booking_url=booking_url,
                    location=location,
                    category=category,
                    subcategory=subcategory,
                    checked_at=checked_at,
                    message="no browser context found in attached Chrome session",
                    method="Playwright attached browser",
                )
            target_host = booking_url.split("/")[2]
            page = None
            for context in contexts:
                for existing_page in context.pages:
                    if target_host in existing_page.url:
                        page = existing_page
                        break
                if page:
                    break
            if page is None:
                return _playwright_error_result(
                    booking_url=booking_url,
                    location=location,
                    category=category,
                    subcategory=subcategory,
                    checked_at=checked_at,
                    message="no matching VFS tab found in attached Chrome session",
                    method="Playwright attached browser",
                )
            page.bring_to_front()
            signals = ["attached_to_existing_chrome_tab"]
            login_url = _login_url_from_booking_url(booking_url)
            if "/login" not in page.url:
                page.goto(login_url, wait_until="domcontentloaded", timeout=browser_timeout_ms)
                signals.append("navigated_to_login")
                try:
                    page.wait_for_load_state("networkidle", timeout=min(browser_timeout_ms, 15000))
                except playwright_timeout_error:
                    pass
                page.wait_for_timeout(3000)

            if "/login" in page.url:
                signals.append("login_page_found")
                if vfs_email:
                    page.locator("input#email").fill(vfs_email, timeout=10000)
                    signals.append("filled_email")
                if vfs_password:
                    page.locator("input#password").fill(vfs_password, timeout=10000)
                    signals.append("filled_password")
                sign_in_button = page.get_by_role("button", name="Sign In")
                page.wait_for_timeout(1000)
                if sign_in_button.is_visible():
                    sign_in_button.click(timeout=10000)
                    signals.append("clicked_sign_in")
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=browser_timeout_ms)
                    except playwright_timeout_error:
                        pass
                    page.wait_for_timeout(5000)

            if "/dashboard" in page.url:
                start_booking_button = page.get_by_role("button", name="Start New Booking")
                start_booking_button.click(timeout=10000)
                signals.append("clicked_start_new_booking")
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=browser_timeout_ms)
                except playwright_timeout_error:
                    pass
                page.wait_for_timeout(5000)

            if "/application-detail" in page.url and subcategory:
                mat_selects = page.locator("mat-select")
                if mat_selects.count() >= 3:
                    subcategory_locator = mat_selects.nth(2)
                    selected_text = subcategory_locator.inner_text(timeout=5000).strip().lower()
                    if subcategory.lower() not in selected_text:
                        subcategory_locator.click(timeout=10000)
                        page.get_by_role("option", name=subcategory).click(timeout=10000)
                        signals.append("selected_sub_category")
                        page.wait_for_timeout(4000)
                else:
                    signals.append("sub_category_control_missing")

            if "/application-detail" in page.url:
                return _build_browser_detection(
                    page=page,
                    booking_url=booking_url,
                    location=location,
                    category=category,
                    subcategory=subcategory,
                    checked_at=checked_at,
                    method="Playwright attached browser",
                    extra_signals=signals,
                )

            return _build_browser_detection(
                page=page,
                booking_url=booking_url,
                location=location,
                category=category,
                subcategory=subcategory,
                checked_at=checked_at,
                method="Playwright attached browser",
                extra_signals=signals,
            )
        except playwright_timeout_error as exc:
            return _playwright_error_result(
                booking_url=booking_url,
                location=location,
                category=category,
                subcategory=subcategory,
                checked_at=checked_at,
                message=f"attached browser timeout: {exc}",
                method="Playwright attached browser",
            )
        except Exception as exc:  # pragma: no cover
            return _playwright_error_result(
                booking_url=booking_url,
                location=location,
                category=category,
                subcategory=subcategory,
                checked_at=checked_at,
                message=f"attached browser error: {type(exc).__name__}: {exc}",
                method="Playwright attached browser",
            )
        finally:
            if browser is not None:
                browser.close()


def open_persistent_browser_for_manual_login(
    *,
    booking_url: str,
    browser_user_data_dir: str,
    browser_profile_directory: str | None,
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
            browser_profile_directory=browser_profile_directory,
            browser_channel=browser_channel,
            browser_executable_path=browser_executable_path,
            headless=headless,
        )
        for existing_page in list(context.pages):
            try:
                if existing_page.url in {"about:blank", "chrome://newtab/"}:
                    existing_page.close()
            except Exception:
                pass
        page = context.new_page()
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
