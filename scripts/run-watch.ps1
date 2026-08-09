param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [int]$IntervalMinutes = 15
)

$ErrorActionPreference = "Stop"

Set-Location $RepoRoot

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment not found at $venvPython"
}

& $venvPython -m vfs_monitor.cli watch --notify --persist-state --heartbeat --json --interval-minutes $IntervalMinutes
