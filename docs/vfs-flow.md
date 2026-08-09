# VFS Flow Discovery

Date of discovery: 2026-08-09

Target:

- VFS Global
- Pakistan -> Sweden
- Short-stay Schengen visa
- Booking entry page: `https://visa.vfsglobal.com/pak/en/swe/book-an-appointment`

## Observed facts

### Public HTTP access

Direct public HTTP access from this environment returns:

- HTTP status: `403`
- Response body:

```json
{
  "code": "403201",
  "description": ""
}
```

This is consistent with anti-bot or access protection and must be classified as `BLOCKED`, not `AVAILABLE`, `UNAVAILABLE`, or `AUTH_REQUIRED`.

### Search-engine-visible public structure

Search results for the Pakistan/Sweden VFS site show that public pages exist for:

- welcome page
- apply for a visa
- attend centre pages
- booking entry page

The indexed snippets are not enough to confirm slot availability or exact visa category labels.

### JavaScript/login pattern on VFS

VFS login pages on the same platform expose a JavaScript-heavy sign-in flow and search-engine snapshots show:

- `Sign in`
- `Email`
- `Password`
- `This website requires JavaScript`

That indicates the platform uses client-side rendering for at least part of the booking flow.

## Confirmed from user-validated screenshots

- exact application centre label:
  `Sweden Visa Application Centre - Islamabad`
- exact appointment category label:
  `Default_Sweden_Pakistan`
- exact appointment sub-category label:
  `Tourist Visit`
- exact unavailable message:
  `We are sorry but no appointment slots are currently available. New slots open at regular intervals, please try again later`

## What is still unconfirmed

The following items still require direct validation from a legitimate local browser session on the Windows laptop:

1. exact positive availability DOM/text structure when a date becomes bookable
2. whether date/time values appear as visible text, button labels, or hidden JSON
3. whether session expiry lands on login, OTP, or another intermediate challenge first

## Current implementation decision

Given the observed `403` protection and the confirmed manual-browser success, repository implementation now uses:

- Windows-local browser-first probing via Playwright persistent context
- a dedicated reusable local Chrome profile
- exact unavailable-text detection
- explicit `AUTH_REQUIRED` and `BLOCKED` classification without bypass attempts

## Operational consequence

As of 2026-08-08, a reliable unattended five-minute slot checker may not be technically possible from GitHub Actions without defeating site protections. This project therefore implements best-effort legitimate monitoring and warns clearly when the system is blocked or changed.
