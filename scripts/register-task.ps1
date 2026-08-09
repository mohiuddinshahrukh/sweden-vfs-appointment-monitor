param(
    [string]$TaskName = "Sweden VFS Monitor",
    [int]$IntervalMinutes = 5,
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

$scriptPath = (Resolve-Path (Join-Path $PSScriptRoot "run-monitor.ps1")).Path
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -RepoRoot `"$RepoRoot`""

$startTime = (Get-Date).AddMinutes(1)
$trigger = New-ScheduledTaskTrigger -Once -At $startTime
$trigger.Repetition = New-ScheduledTaskRepetitionSettingsSet `
    -Interval (New-TimeSpan -Minutes $IntervalMinutes) `
    -Duration (New-TimeSpan -Days 3650)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Checks Sweden VFS appointment availability locally every $IntervalMinutes minutes using a persistent browser profile." `
    -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
