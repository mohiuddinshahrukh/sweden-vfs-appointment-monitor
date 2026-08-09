param(
    [string]$ChromePath = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    [string]$UserDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data",
    [string]$ProfileDirectory = "Default",
    [int]$RemoteDebuggingPort = 9222
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ChromePath)) {
    $chromePathX86 = "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    if (Test-Path $chromePathX86) {
        $ChromePath = $chromePathX86
    } else {
        throw "Chrome executable not found."
    }
}

Start-Process -FilePath $ChromePath -ArgumentList @(
    "--remote-debugging-port=$RemoteDebuggingPort",
    "--user-data-dir=$UserDataDir",
    "--profile-directory=$ProfileDirectory"
)
