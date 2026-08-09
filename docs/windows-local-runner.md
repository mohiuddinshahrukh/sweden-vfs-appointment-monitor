# Windows Local Runner

This guide is for running the monitor on a real Windows laptop as of August 9, 2026.

## Why local browser mode

Direct public HTTP checks from hosted environments have already hit:

- `HTTP 403`
- `{"code":"403201","description":""}`

The intended deployment is therefore:

- a normal Windows laptop
- a legitimate local browser session
- a persistent browser profile
- Task Scheduler every 5 minutes
- Telegram alerts on meaningful changes only

## Recommended profile strategy

Use a dedicated Chrome profile directory for the monitor instead of your day-to-day browser profile.

Reason:

- avoids profile locking when your normal Chrome is open
- keeps VFS session cookies separate
- still uses a legitimate local browser session from the same laptop

Default profile directory:

- `browser-profile`

## First-time setup

1. Create `.env` from `.env.example`.
2. Fill in Telegram secrets.
3. Install dependencies:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev,browser]
python -m playwright install chromium
```

4. Open the persistent profile visibly:

```powershell
python -m vfs_monitor.cli open-browser --headed
```

5. Log into VFS manually.
6. Navigate until you can see the Sweden Pakistan appointment page.
7. Confirm the page shows:
   - `Sweden Visa Application Centre - Islamabad`
   - `Default_Sweden_Pakistan`
   - `Family Visit`
8. Stop the helper once the session is ready by pressing `Ctrl+C`.

## First validation run

Run:

```powershell
python -m vfs_monitor.cli check --notify --persist-state --heartbeat --json
```

Interpretation:

- `UNAVAILABLE`: the exact no-slot message was found
- `AVAILABLE`: clear slot-selection signal was found
- `AUTH_REQUIRED`: login, OTP, password, or verification step appeared
- `BLOCKED`: CAPTCHA, Cloudflare, access denied, or anti-bot page appeared
- `UNKNOWN`: page loaded but changed enough that the monitor stayed conservative
- `ERROR`: local runtime problem, usually Python/Playwright/browser related

## Scheduling every 5 minutes

Register the task once:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register-task.ps1
```

This creates a user-level scheduled task that runs:

- [scripts/run-monitor.ps1](/Users/mohiu/OneDrive/Documents/Swedish%20Embassy%20Checker/scripts/run-monitor.ps1)

Default repetition interval:

- 5 minutes

## Operational guidance

- Do not leave the dedicated automation profile open in regular Chrome while the scheduled task runs.
- If VFS forces re-login, OTP, CAPTCHA, or another manual check, the monitor will classify it as `AUTH_REQUIRED` or `BLOCKED` and alert once.
- The monitor does not try to bypass or solve that challenge.
- After manual re-authentication, the next successful run will recover automatically.
