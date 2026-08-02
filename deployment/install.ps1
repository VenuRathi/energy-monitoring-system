param(
    [ValidateSet("Menu", "HealthCheck", "Evidence", "MeterSetup", "StartupFallback", "AdminTask", "Full")]
    [string]$Mode = "Menu",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ApiBaseUrl = "http://127.0.0.1:5000"
)

$ErrorActionPreference = "Stop"

function New-ReportRoot {
    param([string]$Label)

    $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
    $safeLabel = ($Label -replace "[^A-Za-z0-9_.-]", "_").Trim("_")
    $root = Join-Path $ProjectRoot "deployment-reports\$timestamp`_$safeLabel"
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    return $root
}

function Write-Result {
    param(
        [string]$Status,
        [string]$Label,
        [string]$Message,
        [string]$SummaryPath
    )

    $line = "[{0}] {1}: {2}" -f $Status, $Label, $Message
    Write-Host $line
    if ($SummaryPath) {
        Add-Content -Path $SummaryPath -Value $line -Encoding UTF8
    }
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal] $identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
}

function Read-DotEnv {
    $envPath = Join-Path $ProjectRoot ".env"
    $values = @{}
    if (-not (Test-Path $envPath)) {
        return $values
    }

    foreach ($line in Get-Content $envPath) {
        if ($line -match "^\s*#" -or $line -notmatch "=") {
            continue
        }
        $parts = $line -split "=", 2
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $values
}

function Copy-SanitizedEnv {
    param([string]$ReportRoot)

    $envPath = Join-Path $ProjectRoot ".env"
    $target = Join-Path $ReportRoot "sanitized-env.txt"
    if (-not (Test-Path $envPath)) {
        "MISSING: $envPath" | Set-Content -Path $target -Encoding UTF8
        return
    }

    Get-Content $envPath | ForEach-Object {
        if ($_ -match "(?i)PASSWORD|API_KEY|SMTP") {
            $_ -replace "=.*", "=REDACTED"
        }
        else {
            $_
        }
    } | Set-Content -Path $target -Encoding UTF8
}

function Get-ComPorts {
    try {
        return @([System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object)
    }
    catch {
        return @()
    }
}

function Get-MeterConfig {
    $configPath = Join-Path $ProjectRoot "config\meter_config.json"
    if (-not (Test-Path $configPath)) {
        return $null
    }
    return Get-Content $configPath -Raw | ConvertFrom-Json
}

function Test-MeterConfiguration {
    param(
        [string]$SummaryPath,
        [string]$ReportRoot
    )

    $ports = @(Get-ComPorts)
    $portsText = if ($ports.Count -gt 0) { $ports -join ", " } else { "none detected" }
    $portsText | Set-Content -Path (Join-Path $ReportRoot "com-ports.txt") -Encoding UTF8
    Write-Result "INFO" "Detected COM ports" $portsText $SummaryPath

    $config = Get-MeterConfig
    if (-not $config) {
        Write-Result "FAIL" "Meter config" "config\meter_config.json is missing or unreadable" $SummaryPath
        return
    }

    Copy-Item -Path (Join-Path $ProjectRoot "config\meter_config.json") -Destination (Join-Path $ReportRoot "meter-config.json") -Force

    $enabledMeters = @($config.meters | Where-Object { $_.enabled -eq $true })
    foreach ($meter in $enabledMeters) {
        $port = [string]$meter.connection.port
        $slaveId = [string]$meter.connection.slave_id
        $label = "$($meter.meter_id) COM/slave"
        if ($ports -contains $port) {
            Write-Result "PASS" $label "$port slave $slaveId is configured on a detected COM port" $SummaryPath
        }
        else {
            Write-Result "FAIL" $label "$port slave $slaveId is configured, but Windows does not detect $port" $SummaryPath
        }
    }

    $groups = $enabledMeters | Group-Object { $_.connection.port }
    foreach ($group in $groups) {
        $serialSignatures = @{}
        $slaveIds = @{}
        foreach ($meter in $group.Group) {
            $signature = "{0}|{1}|{2}|{3}|{4}" -f `
                $meter.connection.baud_rate,
                $meter.connection.parity,
                $meter.connection.stop_bits,
                $meter.connection.byte_size,
                $meter.connection.timeout
            $serialSignatures[$signature] = $true
            $slaveKey = [string]$meter.connection.slave_id
            if ($slaveIds.ContainsKey($slaveKey)) {
                Write-Result "FAIL" "Duplicate slave ID" "$($meter.meter_id) duplicates slave $slaveKey on $($group.Name)" $SummaryPath
            }
            $slaveIds[$slaveKey] = $true
        }

        if ($serialSignatures.Count -gt 1) {
            Write-Result "FAIL" "Serial settings conflict" "Enabled meters sharing $($group.Name) do not share the same serial settings" $SummaryPath
        }
    }
}

function Invoke-ApiCapture {
    param(
        [string]$ReportRoot,
        [string]$SummaryPath
    )

    try {
        $health = Invoke-RestMethod -Uri "$ApiBaseUrl/api/health" -Method Get -TimeoutSec 10
        $health | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $ReportRoot "api-health.json") -Encoding UTF8
        Write-Result "PASS" "API health" "reachable, status=$($health.status)" $SummaryPath
    }
    catch {
        $_.Exception.Message | Set-Content -Path (Join-Path $ReportRoot "api-health.txt") -Encoding UTF8
        Write-Result "FAIL" "API health" "not reachable at $ApiBaseUrl" $SummaryPath
    }

    try {
        $status = Invoke-RestMethod -Uri "$ApiBaseUrl/api/status" -Method Get -TimeoutSec 10
        $status | ConvertTo-Json -Depth 30 | Set-Content -Path (Join-Path $ReportRoot "api-status.json") -Encoding UTF8
        Write-Result "INFO" "Runtime status" "overall=$($status.status), database=$($status.databaseStatus), polling=$($status.polling.running)" $SummaryPath
        if ($status.checks.databaseHardening) {
            Write-Result "INFO" "Database hardening" "$($status.checks.databaseHardening.status): $($status.checks.databaseHardening.message)" $SummaryPath
        }
        foreach ($meter in $status.summary.meters) {
            Write-Result "INFO" "$($meter.meterId)" "$($meter.communicationStatus), $($meter.diagnosticCode): $($meter.diagnosticMessage)" $SummaryPath
        }
    }
    catch {
        $_.Exception.Message | Set-Content -Path (Join-Path $ReportRoot "api-status.txt") -Encoding UTF8
        Write-Result "WARN" "API status" "not captured because /api/status is unavailable" $SummaryPath
    }
}

function Invoke-PostgresCapture {
    param(
        [string]$ReportRoot,
        [string]$SummaryPath
    )

    $target = Join-Path $ReportRoot "postgres-check.txt"
    $settings = Read-DotEnv
    $serviceLines = Get-Service *postgres* -ErrorAction SilentlyContinue | Format-Table Name, Status, StartType | Out-String
    $serviceLines | Set-Content -Path $target -Encoding UTF8

    if ($serviceLines.Trim()) {
        Write-Result "INFO" "PostgreSQL service" ($serviceLines.Trim() -replace "\r?\n", " | ") $SummaryPath
    }
    else {
        Write-Result "WARN" "PostgreSQL service" "no postgres service visible to this user" $SummaryPath
    }

    $psql = Get-Command psql -ErrorAction SilentlyContinue
    if (-not $psql) {
        Write-Result "WARN" "psql" "not found on PATH; service check only" $SummaryPath
        return
    }

    $required = @("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    foreach ($key in $required) {
        if (-not $settings.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($settings[$key])) {
            Write-Result "FAIL" "Database config" "$key is missing from .env" $SummaryPath
            return
        }
    }

    $env:PGPASSWORD = $settings["DB_PASSWORD"]
    try {
        $output = & $psql.Source `
            -h $settings["DB_HOST"] `
            -p $settings["DB_PORT"] `
            -U $settings["DB_USER"] `
            -d $settings["DB_NAME"] `
            -c "SELECT 1 AS db_connection_test;" 2>&1
        Add-Content -Path $target -Value "`nConnection test:`n$output" -Encoding UTF8
        if ($LASTEXITCODE -eq 0) {
            Write-Result "PASS" "Database connection" "psql connected to $($settings["DB_NAME"])" $SummaryPath
        }
        else {
            Write-Result "FAIL" "Database connection" (($output | Out-String).Trim()) $SummaryPath
        }
    }
    finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
}

function Copy-LogTails {
    param([string]$ReportRoot)

    $target = Join-Path $ReportRoot "logs-tail.txt"
    $logNames = @("energy_monitoring.log", "backend_watchdog.log", "backend_runner.log")
    foreach ($logName in $logNames) {
        $path = Join-Path $ProjectRoot "logs\$logName"
        Add-Content -Path $target -Value "`n===== $logName =====" -Encoding UTF8
        if (Test-Path $path) {
            Get-Content $path -Tail 160 | Add-Content -Path $target -Encoding UTF8
        }
        else {
            Add-Content -Path $target -Value "MISSING: $path" -Encoding UTF8
        }
    }
}

function Invoke-HealthCheck {
    param([string]$Label = "health_check")

    $reportRoot = New-ReportRoot -Label $Label
    $summaryPath = Join-Path $reportRoot "summary.txt"
    "Energy Monitoring Deployment Report" | Set-Content -Path $summaryPath -Encoding UTF8
    "Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")" | Add-Content -Path $summaryPath -Encoding UTF8
    "Project: $ProjectRoot" | Add-Content -Path $summaryPath -Encoding UTF8
    "" | Add-Content -Path $summaryPath -Encoding UTF8

    Write-Result "INFO" "Administrator" (Test-IsAdministrator) $summaryPath
    Write-Result "INFO" "Project root" $ProjectRoot $summaryPath
    Copy-SanitizedEnv -ReportRoot $reportRoot
    Test-MeterConfiguration -SummaryPath $summaryPath -ReportRoot $reportRoot
    Invoke-PostgresCapture -ReportRoot $reportRoot -SummaryPath $summaryPath
    Invoke-ApiCapture -ReportRoot $reportRoot -SummaryPath $summaryPath
    Copy-LogTails -ReportRoot $reportRoot

    Write-Host ""
    Write-Host "Report folder:"
    Write-Host $reportRoot
}

function Install-StartupFallback {
    $script = Join-Path $ProjectRoot "scripts\install_user_startup_backend.ps1"
    if (-not (Test-Path $script)) {
        throw "Missing script: $script"
    }
    & powershell -ExecutionPolicy Bypass -File $script -ProjectRoot $ProjectRoot
}

function Install-AdminTask {
    if (-not (Test-IsAdministrator)) {
        throw "This mode needs Administrator PowerShell. Use StartupFallback until IT/admin access is available."
    }
    $script = Join-Path $ProjectRoot "scripts\install_task_scheduler_backend.ps1"
    & powershell -ExecutionPolicy Bypass -File $script -ProjectRoot $ProjectRoot
}

function Show-Menu {
    while ($true) {
        Write-Host ""
        Write-Host "Energy Monitoring Deployment Tool"
        Write-Host "1. Health Check"
        Write-Host "2. Collect Evidence"
        Write-Host "3. Meter/COM Setup Check"
        Write-Host "4. Install User Startup Fallback"
        Write-Host "5. Install Admin Scheduled Task"
        Write-Host "6. Full Non-Destructive Check"
        Write-Host "7. Exit"
        $choice = Read-Host "Choose an option"

        switch ($choice) {
            "1" { Invoke-HealthCheck -Label "health_check" }
            "2" { Invoke-HealthCheck -Label "evidence" }
            "3" { Invoke-HealthCheck -Label "meter_setup" }
            "4" { Install-StartupFallback }
            "5" { Install-AdminTask }
            "6" { Install-StartupFallback; Invoke-HealthCheck -Label "full_check" }
            "7" { return }
            default { Write-Host "Choose 1-7." }
        }
    }
}

switch ($Mode) {
    "Menu" { Show-Menu }
    "HealthCheck" { Invoke-HealthCheck -Label "health_check" }
    "Evidence" { Invoke-HealthCheck -Label "evidence" }
    "MeterSetup" { Invoke-HealthCheck -Label "meter_setup" }
    "StartupFallback" { Install-StartupFallback }
    "AdminTask" { Install-AdminTask }
    "Full" { Install-StartupFallback; Invoke-HealthCheck -Label "full_check" }
}
