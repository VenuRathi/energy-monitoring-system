param(
    [string]$TaskName = "EnergyMonitoringBackend",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$RunAsUser = $env:USERNAME,
    [switch]$RunAsCurrentUser
)

$watchdog = Join-Path $ProjectRoot "scripts\run_backend_watchdog.ps1"

if (-not (Test-Path $watchdog)) {
    throw "Backend watchdog not found: $watchdog"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$watchdog`" -ProjectRoot `"$ProjectRoot`"" `
    -WorkingDirectory $ProjectRoot
$triggerStartup = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Days 3650)

$principal = if ($RunAsCurrentUser) {
    New-ScheduledTaskPrincipal -UserId $RunAsUser -LogonType InteractiveOrPassword -RunLevel Highest
}
else {
    New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
}

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $triggerStartup `
        -Settings $settings `
        -Principal $principal `
        -Description "Runs the Energy Monitoring backend continuously on the plant PC." `
        -Force `
        -ErrorAction Stop | Out-Null
}
catch {
    throw "Failed to register scheduled task '$TaskName'. Run PowerShell as Administrator or ask IT to register it. $($_.Exception.Message)"
}

$registeredTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $registeredTask) {
    throw "Scheduled task '$TaskName' was not found after registration."
}

$context = if ($RunAsCurrentUser) { $RunAsUser } else { "SYSTEM" }
Write-Host "Scheduled task '$TaskName' registered."
Write-Host "Run context: $context"
Write-Host "Project root: $ProjectRoot"
