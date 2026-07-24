param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [int]$RestartDelaySeconds = 10
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
    while ($true) {
        Write-WatchdogLog "BACKEND STARTING: executable=$pythonPath."
        $backendProcess = Start-Process `
            -FilePath $pythonPath `
            -ArgumentList @("-u", "main.py") `
            -WorkingDirectory $ProjectRoot `
            -PassThru

        $backendProcess.WaitForExit()
        $exitCode = $backendProcess.ExitCode
        if ($exitCode -eq 0) {
            Write-WatchdogLog "BACKEND STOPPED: exit_code=$exitCode. Watchdog will not restart a clean exit."
            break
        }

        Write-WatchdogLog "BACKEND CRASHED: exit_code=$exitCode. Restarting in $RestartDelaySeconds second(s)."
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
