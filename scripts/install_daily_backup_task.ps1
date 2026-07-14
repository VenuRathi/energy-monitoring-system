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

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Creates a daily PostgreSQL backup for the Energy Monitoring System."

Write-Host "Scheduled backup task '$TaskName' registered for $RunTime."
