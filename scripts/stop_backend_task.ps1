param(
    [string]$TaskName = "EnergyMonitoringBackend",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$logPath = Join-Path $ProjectRoot "logs\backend_watchdog.log"
New-Item -ItemType Directory -Path (Split-Path $logPath) -Force | Out-Null
Add-Content -LiteralPath $logPath -Value ("{0} | STOP REQUESTED: scheduled task {1}." -f (Get-Date).ToString("o"), $TaskName) -Encoding UTF8
Stop-ScheduledTask -TaskName $TaskName -ErrorAction Stop
Write-Host "Stop requested for scheduled task '$TaskName'."
