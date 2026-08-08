from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class HttpFetchResult:
    status_code: int | None
    url: str
    text: str
    headers: dict[str, str]
    error: str | None = None


def fetch_booking_page(url: str, timeout_seconds: float = 30.0) -> HttpFetchResult:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/json",
    }
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout_seconds,
            headers=headers,
        ) as client:
            response = client.get(url)
            return HttpFetchResult(
                status_code=response.status_code,
                url=str(response.url),
                text=response.text,
                headers={k.lower(): v for k, v in response.headers.items()},
            )
    except httpx.HTTPError as exc:
        return HttpFetchResult(
            status_code=None,
            url=url,
            text="",
            headers={},
            error=str(exc),
        )

