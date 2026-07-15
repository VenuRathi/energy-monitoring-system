param(
    [string]$ApiBaseUrl = "http://127.0.0.1:5000"
)

function Format-Value {
    param($Value)
    if ($null -eq $Value -or $Value -eq "") {
        return "n/a"
    }
    return [string]$Value
}

$healthUrl = "$ApiBaseUrl/api/health"
$statusUrl = "$ApiBaseUrl/api/status"

try {
    $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 10
}
catch {
    throw "Unable to reach $healthUrl. $($_.Exception.Message)"
}

try {
    $status = Invoke-RestMethod -Uri $statusUrl -Method Get -TimeoutSec 10
}
catch {
    throw "Unable to reach $statusUrl. $($_.Exception.Message)"
}

Write-Host "API Health"
Write-Host "----------"
Write-Host ("status              : {0}" -f (Format-Value $health.status))
Write-Host ("database            : {0}" -f (Format-Value $status.databaseStatus))
Write-Host ("overall runtime     : {0}" -f (Format-Value $status.status))
Write-Host ("timestamp           : {0}" -f (Format-Value $status.timestamp))
Write-Host ""

Write-Host "Polling"
Write-Host "-------"
Write-Host ("running             : {0}" -f (Format-Value $status.polling.running))
Write-Host ("cycle in progress   : {0}" -f (Format-Value $status.polling.cycleInProgress))
Write-Host ("total cycles        : {0}" -f (Format-Value $status.polling.totalCyclesCompleted))
Write-Host ("last cycle start    : {0}" -f (Format-Value $status.polling.lastCycleStartTime))
Write-Host ("last cycle end      : {0}" -f (Format-Value $status.polling.lastCycleEndTime))
Write-Host ("last cycle duration : {0}" -f (Format-Value $status.polling.lastCycleDurationSeconds))
Write-Host ("uptime seconds      : {0}" -f (Format-Value $status.polling.uptimeSeconds))
Write-Host ("last polling error  : {0}" -f (Format-Value $status.polling.lastGlobalPollingError))
Write-Host ("polling check       : {0}" -f (Format-Value $status.checks.polling.message))
Write-Host ""

Write-Host "Meters"
Write-Host "------"
Write-Host ("meter count         : {0}" -f (Format-Value $status.summary.meterCount))
Write-Host ("enabled meters      : {0}" -f (Format-Value $status.summary.enabledMeterCount))
Write-Host ("stale meters        : {0}" -f (Format-Value $status.summary.staleMeterCount))
Write-Host ("meter check         : {0}" -f (Format-Value $status.checks.meters.message))
Write-Host ""

foreach ($meter in $status.summary.meters) {
    Write-Host ("{0}" -f $meter.meterId)
    Write-Host ("  enabled                 : {0}" -f (Format-Value $meter.enabled))
    Write-Host ("  communication status    : {0}" -f (Format-Value $meter.communicationStatus))
    Write-Host ("  status                  : {0}" -f (Format-Value $meter.status))
    Write-Host ("  stale warning           : {0}" -f (Format-Value $meter.staleWarning))
    Write-Host ("  consecutive failures    : {0}" -f (Format-Value $meter.consecutiveFailureCount))
    Write-Host ("  last success            : {0}" -f (Format-Value $meter.lastSuccessfulReadingTime))
    Write-Host ("  latest reading          : {0}" -f (Format-Value $meter.latestReadingTimestamp))
    Write-Host ("  last error              : {0}" -f (Format-Value $meter.lastErrorMessage))
    Write-Host ""
}
