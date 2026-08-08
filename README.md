# Sweden VFS Appointment Monitor

Python monitor for Sweden Schengen visa appointment availability through VFS Global Pakistan, with Telegram and email alerts.

## What it does

This project checks the official VFS Global Pakistan booking flow for Sweden short-stay Schengen appointments and classifies the result as `available`, `unavailable`, `unknown`, `auth_required`, `blocked`, or `error`.

## What it does not do

This project does not:

- book appointments
- reserve appointments
- bypass CAPTCHA, OTP, anti-bot checks, or rate limits

## Current limitation

As of August 8, 2026, direct public HTTP access to `https://visa.vfsglobal.com/pak/en/swe/book-an-appointment` from this environment returns Cloudflare `403` with code `403201`. That means unattended availability detection may be limited to `BLOCKED` or other public-state monitoring unless VFS exposes a legitimate machine-readable path or a reusable authenticated session without CAPTCHA/OTP.

See [docs/vfs-flow.md](/Users/shahrukh/Documents/ChatGPT/Private%20stuff/docs/vfs-flow.md) for discovery notes.

## Setup

1. Install Python 3.13.
2. Create virtual environment.
3. Install package and dev dependencies: `pip install -e .[dev]`
4. Run tests: `pytest`
5. Copy `.env.example` values into GitHub Actions secrets or local shell env.
6. Set `VFS_CATEGORY` only after you confirm the exact VFS label from a legitimate visible flow. Leave it blank otherwise.
7. Run manual check: `python -m vfs_monitor.cli check`
8. Run manual check with notifications: `python -m vfs_monitor.cli check --notify`
9. Trigger GitHub workflow manually with `workflow_dispatch`
10. Verify Telegram delivery
11. Optionally verify email delivery if Gmail secrets are configured
12. Leave schedule enabled once behavior is validated

## Local commands

```bash
python -m vfs_monitor.cli check
python -m vfs_monitor.cli check --notify
python -m vfs_monitor.cli check --persist-state
```

## Troubleshooting

- `BLOCKED`: VFS returned CAPTCHA, Cloudflare, access denied, or similar protection
- `AUTH_REQUIRED`: appointment visibility requires manual login
- `UNKNOWN`: page changed and detector can no longer classify safely
- Telegram failed: verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Gmail failed: verify `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, and `ALERT_EMAIL_TO`, or leave them unset to run Telegram-only
- Workflow stopped: confirm repository still has recent activity and scheduled workflows remain enabled

## Security

Public repository must never contain personal details, VFS credentials, cookies, or tokens. Use GitHub Actions secrets only.
