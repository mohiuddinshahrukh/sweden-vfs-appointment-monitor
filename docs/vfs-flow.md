# VFS Flow Discovery

Date of discovery: 2026-08-08

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

## What is still unconfirmed

The following items remain unconfirmed from this environment because the public entry is blocked before the appointment UI becomes visible:

1. exact `Book now` click path for Pakistan -> Sweden
2. whether login is required before location/category selectors
3. exact Islamabad category label for short-stay family/friends visit
4. exact text for no-availability state
5. exact text or structure for positive availability state
6. whether actual date/time data is exposed in HTML or JSON after legitimate navigation

## Provisional category choice

For a planned stay of up to 90 days, current official public VFS Sweden Pakistan pages show the label:

- `Tourist / Visit Family Or Friends`

That is the best provisional `VFS_CATEGORY` value for this repository until the live appointment selector can be inspected directly without bypassing protections.

## Current implementation decision

Given the observed `403` protection, repository implementation uses:

- HTTP-first probing
- explicit `BLOCKED` classification on Cloudflare/access-denied signals
- optional Playwright fallback only if a legitimate browser-visible public path can be used without bypassing CAPTCHA/OTP/security challenges

## Operational consequence

As of 2026-08-08, a reliable unattended five-minute slot checker may not be technically possible from GitHub Actions without defeating site protections. This project therefore implements best-effort legitimate monitoring and warns clearly when the system is blocked or changed.
