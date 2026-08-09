param(
    [string]$TaskName = "SwedenVFSMonitor",
    [int]$IntervalMinutes = 15,
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

$scriptPath = (Resolve-Path (Join-Path $PSScriptRoot "run-monitor.ps1")).Path
$powershellPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$startBoundary = (Get-Date).AddMinutes(1).ToString("s")
$taskArguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $scriptPath + '" -RepoRoot "' + $RepoRoot + '"'

$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$startBoundary</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
      <Repetition>
        <Interval>PT${IntervalMinutes}M</Interval>
        <Duration>P3650D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$powershellPath</Command>
      <Arguments>$taskArguments</Arguments>
      <WorkingDirectory>$RepoRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$tempXml = Join-Path $env:TEMP "sweden-vfs-monitor-task.xml"
[System.IO.File]::WriteAllText($tempXml, $xml, [System.Text.Encoding]::Unicode)

$process = Start-Process -FilePath "schtasks.exe" -ArgumentList @("/Create", "/TN", $TaskName, "/XML", $tempXml, "/F") -Wait -PassThru -NoNewWindow
if ($process.ExitCode -ne 0) {
    throw "schtasks.exe exited with code $($process.ExitCode)"
}

Write-Host "Registered scheduled task: $TaskName"
