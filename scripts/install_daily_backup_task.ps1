param(
    [string]$TaskName = "EnergyMonitoringDailyBackup",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$RunTime = "23:30"
)

$backupScript = Join-Path $ProjectRoot "scripts\backup_postgres.ps1"

if (-not (Test-Path $backupScript)) {
    throw "Backup script not found: $backupScript"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$backupScript`""

$trigger = New-ScheduledTaskTrigger -Daily -At $RunTime
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Creates a daily PostgreSQL backup for the Energy Monitoring System." `
        -ErrorAction Stop | Out-Null
}
catch {
    throw "Failed to register scheduled backup task '$TaskName'. Run PowerShell as Administrator or ask IT to register it. $($_.Exception.Message)"
}

$registeredTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $registeredTask) {
    throw "Scheduled backup task '$TaskName' was not found after registration."
}

Write-Host "Scheduled backup task '$TaskName' registered for $RunTime."
