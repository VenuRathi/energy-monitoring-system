param(
    [string]$TaskName = "EnergyMonitoringBackend",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [int]$GraceSeconds = 10
)

$logPath = Join-Path $ProjectRoot "logs\backend_watchdog.log"
$lockPath = Join-Path $ProjectRoot "data\energy-monitoring-system-main.lock"
$pidPath = Join-Path $ProjectRoot "data\energy-monitoring-system-main.pid"
$expectedPythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$apiPort = if ($env:API_PORT) { [int]$env:API_PORT } else { 5000 }

New-Item -ItemType Directory -Path (Split-Path $logPath) -Force | Out-Null

function Write-StopLog {
    param([string]$Message)

    Add-Content -LiteralPath $logPath -Value ("{0} | {1}" -f (Get-Date).ToString("o"), $Message) -Encoding UTF8
}

function Read-PidFromFile {
    param(
        [string]$Path,
        [string]$Description
    )

    if (-not (Test-Path $Path)) {
        Write-StopLog "BACKEND PID NOT FOUND: $Description does not exist at $Path."
        return $null
    }

    try {
        $rawPid = (Get-Content -LiteralPath $Path -Raw -ErrorAction Stop).Trim()
    }
    catch {
        Write-StopLog "BACKEND PID READ FAILED: unable to read $Description at $Path. $($_.Exception.Message)"
        return $null
    }

    if (-not $rawPid) {
        Write-StopLog "BACKEND PID NOT FOUND: $Description is empty at $Path."
        return $null
    }

    $backendPid = 0
    if (-not [int]::TryParse($rawPid, [ref]$backendPid) -or $backendPid -le 0) {
        Write-StopLog "BACKEND PID INVALID: $Description value '$rawPid' is not a positive integer."
        return $null
    }

    Write-StopLog "BACKEND PID READ: pid=$backendPid from $Description at $Path."
    return $backendPid
}

function Read-BackendPid {
    $backendPid = Read-PidFromFile -Path $pidPath -Description "pid file"
    if ($null -ne $backendPid) {
        return $backendPid
    }

    Write-StopLog "BACKEND PID FALLBACK: trying legacy lock file at $lockPath."
    return Read-PidFromFile -Path $lockPath -Description "legacy lock file"
}

function Get-VerifiedBackendProcess {
    param([int]$BackendPid)

    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $BackendPid" -ErrorAction SilentlyContinue
    if (-not $process) {
        Write-StopLog "BACKEND PROCESS NOT RUNNING: pid=$BackendPid from lock file."
        return $null
    }

    $actualExecutable = [string]$process.ExecutablePath
    $commandLine = [string]$process.CommandLine
    $expectedExecutable = (Resolve-Path $expectedPythonPath -ErrorAction SilentlyContinue).Path
    if (-not $expectedExecutable) {
        Write-StopLog "BACKEND VERIFY FAILED: expected Python runtime missing at $expectedPythonPath."
        return $null
    }

    $executableMatches = $actualExecutable -ieq $expectedExecutable
    $commandUsesExpectedPython = $commandLine -like "*$expectedExecutable*"
    $runsMainPy = $commandLine -match '(^|[\s"''\\/])main\.py(["''\s]|$)'
    if (-not (($executableMatches -or $commandUsesExpectedPython) -and $runsMainPy)) {
        $ownsApiPort = $false
        if (-not $actualExecutable -and -not $commandLine) {
            $apiListener = Get-NetTCPConnection -LocalPort $apiPort -State Listen -ErrorAction SilentlyContinue |
                Where-Object { [int]$_.OwningProcess -eq $BackendPid } |
                Select-Object -First 1
            $ownsApiPort = $null -ne $apiListener
        }

        if ($ownsApiPort) {
            Write-StopLog (
                "BACKEND VERIFY OK: pid=$BackendPid owns API port $apiPort but Windows did not expose executable/commandLine metadata. " +
                "Using project PID file and API port ownership fallback."
            )
            return $process
        }

        Write-StopLog (
            "BACKEND VERIFY FAILED: pid=$BackendPid executable='$actualExecutable' commandLine='$commandLine'. " +
            "Expected executable or command line to include '$expectedExecutable' and script main.py."
        )
        return $null
    }

    Write-StopLog "BACKEND VERIFY OK: pid=$BackendPid executable='$actualExecutable' commandLine='$commandLine'."
    return $process
}

function Stop-VerifiedWatchdogParent {
    param([object]$BackendProcess)

    $currentParentPid = [int]$BackendProcess.ParentProcessId
    for ($depth = 0; $depth -lt 8 -and $currentParentPid -gt 0; $depth++) {
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $currentParentPid" -ErrorAction SilentlyContinue
        if (-not $parent) {
            return
        }

        $parentCommandLine = [string]$parent.CommandLine
        $isProjectWatchdog = (
            [string]$parent.Name -in @("powershell.exe", "pwsh.exe") -and
            $parentCommandLine -like "*run_backend_watchdog.ps1*"
        )

        if ($isProjectWatchdog) {
            Write-StopLog "WATCHDOG PARENT STOP REQUESTED: pid=$($parent.ProcessId) commandLine='$parentCommandLine'."
            Stop-Process -Id ([int]$parent.ProcessId) -ErrorAction Stop
            Write-StopLog "WATCHDOG PARENT STOPPED: pid=$($parent.ProcessId)."
            return
        }

        $currentParentPid = [int]$parent.ParentProcessId
    }
}

function Wait-ScheduledTaskStopped {
    param([string]$Name)

    $deadline = (Get-Date).AddSeconds([Math]::Max(1, $GraceSeconds))
    while ((Get-Date) -lt $deadline) {
        $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
        if (-not $task -or [string]$task.State -ne "Running") {
            Write-StopLog "SCHEDULED TASK CONFIRMED STOPPED: $Name state=$($task.State)."
            return
        }
        Start-Sleep -Milliseconds 250
    }

    throw "Scheduled task '$Name' did not stop within $GraceSeconds second(s); refusing to stop backend child while watchdog may restart it."
}

function Stop-BackendProcess {
    param([object]$BackendProcess)

    $backendPid = [int]$BackendProcess.ProcessId
    Write-StopLog "BACKEND STOP REQUESTED: pid=$backendPid."
    try {
        Stop-Process -Id $backendPid -ErrorAction Stop
    }
    catch {
        Write-StopLog "BACKEND STOP-PROCESS FAILED: pid=$backendPid. $($_.Exception.Message)"
        $taskkill = Join-Path $env:SystemRoot "System32\taskkill.exe"
        if (-not (Test-Path $taskkill)) {
            throw
        }

        $output = & $taskkill /PID $backendPid /F 2>&1
        $exitCode = $LASTEXITCODE
        Write-StopLog "BACKEND TASKKILL RESULT: pid=$backendPid exit_code=$exitCode output=$($output -join ' ')"
        if ($exitCode -ne 0) {
            throw "taskkill failed for verified backend pid $backendPid with exit code $exitCode."
        }
    }

    $deadline = (Get-Date).AddSeconds([Math]::Max(1, $GraceSeconds))
    while ((Get-Date) -lt $deadline) {
        $stillRunning = Get-CimInstance Win32_Process -Filter "ProcessId = $backendPid" -ErrorAction SilentlyContinue
        if (-not $stillRunning) {
            Write-StopLog "BACKEND STOPPED: pid=$backendPid."
            Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue
            return
        }
        Start-Sleep -Milliseconds 250
    }

    $stillRunningAfterGrace = Get-CimInstance Win32_Process -Filter "ProcessId = $backendPid" -ErrorAction SilentlyContinue
    if ($stillRunningAfterGrace) {
        throw "Backend pid $backendPid did not exit within $GraceSeconds second(s)."
    }

    Write-StopLog "BACKEND STOPPED: pid=$backendPid."
    Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue
}

Write-StopLog "STOP REQUESTED: scheduled task $TaskName project=$ProjectRoot."

try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-StopLog "SCHEDULED TASK STOP REQUESTED: $TaskName."
        Wait-ScheduledTaskStopped -Name $TaskName
        Write-Host "Stop requested for scheduled task '$TaskName'."
    }
    else {
        Write-StopLog "SCHEDULED TASK NOT FOUND: $TaskName."
        Write-Warning "Scheduled task '$TaskName' was not found. Checking backend lock PID anyway."
    }

    $backendPid = Read-BackendPid
    if ($null -eq $backendPid) {
        Write-Host "No backend PID was available in the project PID or lock file."
        return
    }

    $backendProcess = Get-VerifiedBackendProcess -BackendPid $backendPid
    if ($null -eq $backendProcess) {
        Write-Warning "Backend PID $backendPid was not stopped because it did not verify as this project's python main.py process."
        return
    }

    if (-not $task) {
        Stop-VerifiedWatchdogParent -BackendProcess $backendProcess
    }

    Stop-BackendProcess -BackendProcess $backendProcess
    Write-Host "Stopped backend process pid $backendPid."
}
catch {
    Write-StopLog ("STOP FAILED: {0}" -f $_.Exception.Message)
    throw
}
