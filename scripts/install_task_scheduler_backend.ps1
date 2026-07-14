param(
    [string]$TaskName = "EnergyMonitoringBackend",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$RunAsUser = $env:USERNAME
)

$runner = Join-Path $ProjectRoot "scripts\run_backend_service.bat"

if (-not (Test-Path $runner)) {
    throw "Backend runner not found: $runner"
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$runner`"" -WorkingDirectory $ProjectRoot
$triggerStartup = New-ScheduledTaskTrigger -AtStartup
$triggerLogin = New-ScheduledTaskTrigger -AtLogOn -User $RunAsUser
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger @($triggerStartup, $triggerLogin) `
    -Settings $settings `
    -Description "Runs the Energy Monitoring backend continuously on the plant PC."

Write-Host "Scheduled task '$TaskName' registered."
