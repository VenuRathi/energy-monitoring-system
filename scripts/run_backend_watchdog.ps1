param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [int]$RestartDelaySeconds = 10,
    [string]$HealthUrl = "http://127.0.0.1:5000/api/status",
    [int]$HealthCheckIntervalSeconds = 30,
    [int]$StartupGraceSeconds = 60,
    [int]$MaxConsecutiveHealthFailures = 3,
    [int]$MaxPollingSilenceSeconds = 0,
    [int]$MaxRestartsInWindow = 5,
    [int]$RestartWindowMinutes = 10,
    [int]$RestartLoopPauseSeconds = 300
)

$logDirectory = Join-Path $ProjectRoot "logs"
$logPath = Join-Path $logDirectory "backend_watchdog.log"
$pythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$maxLogBytes = 5MB
$backupCount = 7

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

function Rotate-WatchdogLog {
    if (-not (Test-Path $logPath)) {
        return
    }

    if ((Get-Item $logPath).Length -lt $maxLogBytes) {
        return
    }

    for ($index = $backupCount; $index -ge 1; $index--) {
        $source = if ($index -eq 1) { $logPath } else { "$logPath.$($index - 1)" }
        $destination = "$logPath.$index"
        if (Test-Path $destination) {
            Remove-Item -LiteralPath $destination -Force
        }
        if (Test-Path $source) {
            Move-Item -LiteralPath $source -Destination $destination -Force
        }
    }
}

function Write-WatchdogLog {
    param([string]$Message)

    Rotate-WatchdogLog
    Add-Content -LiteralPath $logPath -Value ("{0} | {1}" -f (Get-Date).ToString("o"), $Message) -Encoding UTF8
}

function Test-BackendHealth {
    param(
        [System.Diagnostics.Process]$Process,
        [datetime]$StartedAt
    )

    if ((Get-Date) -lt $StartedAt.AddSeconds([Math]::Max(0, $StartupGraceSeconds))) {
        return $true
    }

    try {
        $status = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 5
        if (-not $status.polling.running) {
            Write-WatchdogLog "HEALTH WARNING: polling loop is not running."
            return $false
        }

        $lastCycleEnd = [datetimeoffset]::MinValue
        if (-not [datetimeoffset]::TryParse([string]$status.polling.lastCycleEndTime, [ref]$lastCycleEnd)) {
            Write-WatchdogLog "HEALTH WARNING: polling lastCycleEndTime is missing or invalid."
            return $false
        }

        $pollIntervalSeconds = 180
        $reportedPollInterval = 0
        if ([int]::TryParse([string]$status.polling.pollIntervalSeconds, [ref]$reportedPollInterval) -and $reportedPollInterval -gt 0) {
            $pollIntervalSeconds = $reportedPollInterval
        }
        $silenceLimitSeconds = if ($MaxPollingSilenceSeconds -gt 0) {
            [Math]::Max(60, $MaxPollingSilenceSeconds)
        } else {
            # Allow one configured polling interval plus bounded startup/DB tolerance.
            [Math]::Max(420, $pollIntervalSeconds + 120)
        }
        $silenceSeconds = ([datetimeoffset]::UtcNow - $lastCycleEnd.ToUniversalTime()).TotalSeconds
        if ($silenceSeconds -gt $silenceLimitSeconds) {
            Write-WatchdogLog "HEALTH WARNING: polling heartbeat is $([Math]::Round($silenceSeconds)) second(s) old (limit=$silenceLimitSeconds, poll_interval=$pollIntervalSeconds)."
            return $false
        }

        return $true
    }
    catch {
        Write-WatchdogLog "HEALTH WARNING: backend status request failed: $($_.Exception.Message)"
        return $false
    }
}

$mutex = New-Object System.Threading.Mutex($false, "Global\EnergyMonitoringBackendWatchdog")
$ownsMutex = $false
try {
    $ownsMutex = $mutex.WaitOne(0)
    if (-not $ownsMutex) {
        Write-WatchdogLog "Watchdog instance already exists; exiting duplicate launcher."
        exit 0
    }

    if (-not (Test-Path $pythonPath)) {
        Write-WatchdogLog "STARTUP FAILED: project Python not found at $pythonPath."
        exit 1
    }

    Write-WatchdogLog "WATCHDOG STARTED: project=$ProjectRoot pid=$PID."
    $restartHistory = New-Object System.Collections.Generic.List[datetime]
    while ($true) {
        $windowStart = (Get-Date).AddMinutes(-[Math]::Max(1, $RestartWindowMinutes))
        for ($index = $restartHistory.Count - 1; $index -ge 0; $index--) {
            if ($restartHistory[$index] -lt $windowStart) {
                $restartHistory.RemoveAt($index)
            }
        }
        if ($restartHistory.Count -ge [Math]::Max(1, $MaxRestartsInWindow)) {
            Write-WatchdogLog "RESTART LOOP PROTECTION: $($restartHistory.Count) restart(s) in $RestartWindowMinutes minute(s). Pausing for $RestartLoopPauseSeconds second(s)."
            Start-Sleep -Seconds ([Math]::Max(30, $RestartLoopPauseSeconds))
            $restartHistory.Clear()
        }

        Write-WatchdogLog "BACKEND STARTING: executable=$pythonPath."
        $backendProcess = Start-Process `
            -FilePath $pythonPath `
            -ArgumentList @("-u", "main.py") `
            -WorkingDirectory $ProjectRoot `
            -WindowStyle Hidden `
            -PassThru
        Write-WatchdogLog "BACKEND STARTED: pid=$($backendProcess.Id) executable=$pythonPath script=main.py."

        $startedAt = Get-Date
        $consecutiveHealthFailures = 0
        while (-not $backendProcess.HasExited) {
            Start-Sleep -Seconds ([Math]::Max(5, $HealthCheckIntervalSeconds))
            if ($backendProcess.HasExited) {
                break
            }

            if (Test-BackendHealth -Process $backendProcess -StartedAt $startedAt) {
                if ($consecutiveHealthFailures -gt 0) {
                    Write-WatchdogLog "HEALTH RECOVERED: backend status and polling heartbeat are healthy."
                }
                $consecutiveHealthFailures = 0
                continue
            }

            $consecutiveHealthFailures++
            Write-WatchdogLog "HEALTH FAILURE: consecutive_count=$consecutiveHealthFailures/$MaxConsecutiveHealthFailures."
            if ($consecutiveHealthFailures -ge [Math]::Max(1, $MaxConsecutiveHealthFailures)) {
                Write-WatchdogLog "BACKEND HUNG: stopping pid=$($backendProcess.Id) after failed health checks."
                Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
                break
            }
        }

        $backendProcess.WaitForExit()
        $exitCode = $backendProcess.ExitCode
        if ($exitCode -eq 0) {
            Write-WatchdogLog "BACKEND STOPPED: exit_code=$exitCode. Watchdog will not restart a clean exit."
            break
        }

        Write-WatchdogLog "BACKEND CRASHED: exit_code=$exitCode. Restarting in $RestartDelaySeconds second(s)."
        $restartHistory.Add((Get-Date))
        Start-Sleep -Seconds ([Math]::Max(1, $RestartDelaySeconds))
        Write-WatchdogLog "BACKEND RESTARTING after exit_code=$exitCode."
    }
}
catch {
    Write-WatchdogLog ("WATCHDOG FAILED: {0}" -f $_.Exception.Message)
    exit 1
}
finally {
    if ($ownsMutex) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
    Write-WatchdogLog "WATCHDOG STOPPED."
}
