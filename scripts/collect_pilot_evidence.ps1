param(
    [string]$ApiBaseUrl = "http://127.0.0.1:5000",
    [string]$OutputRoot = (Join-Path (Resolve-Path "$PSScriptRoot\..").Path "pilot-evidence"),
    [string]$Label = "baseline"
)

function New-SafeName {
    param([string]$Value)
    return ($Value -replace "[^A-Za-z0-9_.-]", "_").Trim("_")
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$safeLabel = New-SafeName -Value $Label
$evidenceRoot = Join-Path $OutputRoot "${timestamp}_${safeLabel}"
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$summaryPath = Join-Path $evidenceRoot "summary.txt"
$healthPath = Join-Path $evidenceRoot "api-health.json"
$statusPath = Join-Path $evidenceRoot "api-status.json"
$environmentPath = Join-Path $evidenceRoot "environment.txt"

$healthUrl = "$ApiBaseUrl/api/health"
$statusUrl = "$ApiBaseUrl/api/status"

try {
    $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 10
    $health | ConvertTo-Json -Depth 20 | Set-Content -Path $healthPath -Encoding UTF8
}
catch {
    "Unable to reach $healthUrl. $($_.Exception.Message)" | Set-Content -Path $healthPath -Encoding UTF8
    throw "Pilot evidence collection failed while reading /api/health."
}

try {
    $status = Invoke-RestMethod -Uri $statusUrl -Method Get -TimeoutSec 10
    $status | ConvertTo-Json -Depth 20 | Set-Content -Path $statusPath -Encoding UTF8
}
catch {
    "Unable to reach $statusUrl. $($_.Exception.Message)" | Set-Content -Path $statusPath -Encoding UTF8
    throw "Pilot evidence collection failed while reading /api/status."
}

$ports = @()
try {
    $ports = [System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object
}
catch {
}

$environmentLines = @(
    "Collected at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")",
    "Computer: $env:COMPUTERNAME",
    "User: $env:USERNAME",
    "API base URL: $ApiBaseUrl",
    "COM ports: $(if ($ports.Count -gt 0) { $ports -join ", " } else { "none detected" })"
)
$environmentLines | Set-Content -Path $environmentPath -Encoding UTF8

$meterRows = @()
if ($status.summary -and $status.summary.meters) {
    foreach ($meter in $status.summary.meters) {
        $meterRows += "{0}: enabled={1}, communication={2}, stale={3}, failures={4}, lastSuccess={5}, latestReading={6}" -f `
            $meter.meterId,
            $meter.enabled,
            $meter.communicationStatus,
            $meter.staleWarning,
            $meter.consecutiveFailureCount,
            $meter.lastSuccessfulReadingTime,
            $meter.latestReadingTimestamp
    }
}

$summaryLines = @(
    "Pilot Evidence Summary",
    "======================",
    "",
    "Label: $Label",
    "Collected at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")",
    "API health: $($health.status)",
    "Overall runtime: $($status.status)",
    "Database: $($status.databaseStatus)",
    "Polling running: $($status.polling.running)",
    "Polling cycles: $($status.polling.totalCyclesCompleted)",
    "Stale meters: $($status.summary.staleMeterCount)",
    "",
    "Meters",
    "------"
) + $meterRows

$summaryLines | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "Pilot evidence collected: $evidenceRoot"
Write-Host "Summary: $summaryPath"
