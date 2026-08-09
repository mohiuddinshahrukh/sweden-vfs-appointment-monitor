# Sweden VFS Appointment Monitor

Windows-local monitor for Sweden VFS Pakistan appointment availability, designed to run from a real home-user laptop with a legitimate VFS browser session.

## Status

This repository is now local-runner-first.

- Primary path: Windows laptop + persistent Chrome profile + Task Scheduler every 5 minutes
- Notifications: Telegram first
- Email: optional and disabled by default
- Safety: no booking, no reservation, no CAPTCHA/OTP bypass, no anti-bot bypass

## Confirmed live labels

These values are now the repo defaults and should only be changed if the live VFS UI changes.

- Application centre: `Sweden Visa Application Centre - Islamabad`
- Appointment category: `Default_Sweden_Pakistan`
- Sub-category: `Tourist Visit`
- Exact unavailable text:
  `We are sorry but no appointment slots are currently available. New slots open at regular intervals, please try again later`

## Monitor states

- `AVAILABLE`: clear appointment availability signal detected
- `UNAVAILABLE`: exact no-slot message or equivalent unavailable signal detected
- `UNKNOWN`: page loaded but can no longer be classified safely
- `AUTH_REQUIRED`: login, OTP, verification code, or manual re-auth step detected
- `BLOCKED`: CAPTCHA, Cloudflare, access denied, or anti-bot page detected
- `ERROR`: technical failure in the monitor itself

Repeated identical states do not alert every 5 minutes. Telegram is only sent on meaningful state changes or availability changes.

## Setup

1. Install Python 3.11 or newer on Windows.
2. Install Google Chrome on the same laptop that can reach the VFS appointment page normally.
3. Create a virtual environment:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

4. Install the package and browser dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .[dev,browser]
python -m playwright install chromium
```

5. Copy `.env.example` to `.env` and set:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - optionally `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`
6. Rotate the VFS password before deployment if it was previously exposed in chat history.
7. Bootstrap a dedicated persistent browser profile for this monitor:

```powershell
python -m vfs_monitor.cli open-browser --headed
```

8. In that browser window, log in manually to VFS and reach the appointment page.
9. Leave the browser profile closed after login setup. Scheduled checks will reuse the same profile directory.
10. Run a local check:

```powershell
python -m vfs_monitor.cli check --notify --persist-state --heartbeat --json
```

## Windows operation

The monitor defaults to browser mode through a persistent local profile:

- `VFS_CHECK_METHOD=browser`
- `VFS_BROWSER_USER_DATA_DIR=browser-profile`
- `VFS_BROWSER_PROFILE_DIRECTORY=Default` when reusing real Chrome profile root
- `VFS_BROWSER_ATTACH_URL=http://127.0.0.1:9222` for attach mode
- `VFS_BROWSER_CHANNEL=chrome`

Recommended approach:

- Use the dedicated `browser-profile` directory in this repo
- Log into VFS manually once using `open-browser --headed`
- Let scheduled checks run headless every 5 minutes against that same profile

This avoids GitHub Actions and datacenter IPs while still staying inside a legitimate local browser session.

## Attach Mode

If VFS blocks automation-launched Chrome but allows your manually opened local Chrome tab, use attach mode.

1. Close Chrome.
2. Launch Chrome with remote debugging enabled:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\open-debug-chrome.ps1
```

3. In that Chrome window, log in manually and reach appointment page.
4. Set `VFS_CHECK_METHOD=attach`.
5. Run:

```powershell
python -m vfs_monitor.cli check --notify --persist-state --heartbeat --json
python -m vfs_monitor.cli watch --notify --persist-state --heartbeat --json --interval-minutes 15
```

Attach mode will connect to your already-open VFS tab, refresh it, and classify visible state. It still may be blocked by VFS after repeated automated refreshes.

## Commands

```powershell
python -m vfs_monitor.cli open-browser --headed
python -m vfs_monitor.cli check
python -m vfs_monitor.cli check --notify
python -m vfs_monitor.cli check --notify --persist-state --heartbeat --json
python -m vfs_monitor.cli watch --notify --persist-state --heartbeat --json --interval-minutes 15
```

## Task Scheduler

Helper scripts are in [scripts](/Users/mohiu/OneDrive/Documents/Swedish%20Embassy%20Checker/scripts).

- Run once manually: [scripts/run-monitor.ps1](/Users/mohiu/OneDrive/Documents/Swedish%20Embassy%20Checker/scripts/run-monitor.ps1)
- Run continuous 15-minute watch loop: [scripts/run-watch.ps1](/Users/mohiu/OneDrive/Documents/Swedish%20Embassy%20Checker/scripts/run-watch.ps1)
- Register the repeating task: [scripts/register-task.ps1](/Users/mohiu/OneDrive/Documents/Swedish%20Embassy%20Checker/scripts/register-task.ps1)
- Open debug-enabled Chrome for attach mode: [scripts/open-debug-chrome.ps1](/Users/mohiu/OneDrive/Documents/Swedish%20Embassy%20Checker/scripts/open-debug-chrome.ps1)

Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register-task.ps1
```

Full setup guide: [docs/windows-local-runner.md](/Users/mohiu/OneDrive/Documents/Swedish%20Embassy%20Checker/docs/windows-local-runner.md)

## Local validation

Run tests:

```powershell
pytest
```

Run one live local check:

```powershell
python -m vfs_monitor.cli check --json
```

Expected behavior:

- If the stored session is still valid and the no-slot text is visible, the result should be `UNAVAILABLE`
- If login, OTP, verification code, or password is shown, the result should be `AUTH_REQUIRED`
- If CAPTCHA, Cloudflare, or access denied is shown, the result should be `BLOCKED`
- If dates/times or a clear slot-selection signal appears, the result should be `AVAILABLE`

## Notes

- GitHub Actions no longer acts as the primary monitor.
- The GitHub workflow now runs tests only.
- Runtime state and the persistent browser profile are ignored by git.
- The monitor never attempts to submit forms, reserve slots, or bypass security controls.
