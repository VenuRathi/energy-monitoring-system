Set-StrictMode -Version 2.0

$script:DeploymentChecks = @()
$script:DeploymentReportRoot = $null

function New-SafeName {
    param([string]$Value)
    return (($Value -replace "[^A-Za-z0-9_.-]", "_").Trim("_")).ToLowerInvariant()
}

function Initialize-DeploymentReport {
    param(
        [string]$ProjectRoot,
        [string]$Mode
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
    $safeMode = New-SafeName -Value $Mode
    $reportsRoot = Join-Path $ProjectRoot "deployment\reports"
    $script:DeploymentReportRoot = Join-Path $reportsRoot "${timestamp}_${safeMode}"
    New-Item -ItemType Directory -Path $script:DeploymentReportRoot -Force | Out-Null
    $script:DeploymentChecks = @()
    return $script:DeploymentReportRoot
}

function Add-DeploymentCheck {
    param(
        [ValidateSet("PASS", "WARN", "FAIL", "INFO")]
        [string]$Status,
        [string]$Label,
        [string]$Detail = "",
        [string]$Category = "general"
    )

    $line = "{0}: {1}" -f $Status, $Label
    if ($Detail) {
        $line = "$line - $Detail"
    }

    switch ($Status) {
        "PASS" { Write-Host $line -ForegroundColor Green }
        "WARN" { Write-Host $line -ForegroundColor Yellow }
        "FAIL" { Write-Host $line -ForegroundColor Red }
        default { Write-Host $line }
    }

    $script:DeploymentChecks += [pscustomobject]@{
        status = $Status
        category = $Category
        label = $Label
        detail = $Detail
        checkedAt = (Get-Date).ToString("o")
    }
}

function Complete-DeploymentReport {
    param(
        [string]$ProjectRoot,
        [string]$Mode
    )

    $checksPath = Join-Path $script:DeploymentReportRoot "checks.json"
    $summaryPath = Join-Path $script:DeploymentReportRoot "summary.txt"
    $script:DeploymentChecks | ConvertTo-Json -Depth 10 | Set-Content -Path $checksPath -Encoding UTF8

    $passCount = @($script:DeploymentChecks | Where-Object { $_.status -eq "PASS" }).Count
    $warnCount = @($script:DeploymentChecks | Where-Object { $_.status -eq "WARN" }).Count
    $failCount = @($script:DeploymentChecks | Where-Object { $_.status -eq "FAIL" }).Count

    $summary = New-Object System.Collections.Generic.List[string]
    $summary.Add("Energy Monitoring Deployment Report")
    $summary.Add("===================================")
    $summary.Add("")
    $summary.Add("Mode: $Mode")
    $summary.Add("Project root: $ProjectRoot")
    $summary.Add("Report folder: $script:DeploymentReportRoot")
    $summary.Add("Generated at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")")
    $summary.Add("")
    $summary.Add("Result counts: PASS=$passCount WARN=$warnCount FAIL=$failCount")
    $summary.Add("")
    foreach ($check in $script:DeploymentChecks) {
        $detail = if ($check.detail) { " - $($check.detail)" } else { "" }
        $summary.Add(("{0}: {1}{2}" -f $check.status, $check.label, $detail))
    }

    $summary | Set-Content -Path $summaryPath -Encoding UTF8
    return @{
        ReportRoot = $script:DeploymentReportRoot
        SummaryPath = $summaryPath
        ChecksPath = $checksPath
        FailCount = $failCount
        WarnCount = $warnCount
        PassCount = $passCount
    }
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-DetectedComPorts {
    try {
        return @([System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object)
    }
    catch {
        return @()
    }
}

function Get-MeterConnectionPort {
    param($Connection)

    if (-not $Connection) {
        return ""
    }

    $comPort = ""
    if ($Connection.PSObject.Properties.Name -contains "com_port") {
        $comPort = [string]$Connection.com_port
    }
    if ($comPort) {
        return $comPort
    }
    if ($Connection.PSObject.Properties.Name -contains "port") {
        return [string]$Connection.port
    }
    return ""
}

function Get-ObjectPropertyValue {
    param(
        $Object,
        [string]$Name,
        $DefaultValue
    )

    if ($Object -and $Object.PSObject.Properties.Name -contains $Name) {
        $value = $Object.$Name
        if ($null -ne $value -and [string]$value -ne "") {
            return $value
        }
    }
    return $DefaultValue
}

function Save-DetectedComPorts {
    param([string]$ReportRoot)

    $ports = Get-DetectedComPorts
    $path = Join-Path $ReportRoot "com-ports.txt"
    if ($ports.Count -gt 0) {
        $ports | Set-Content -Path $path -Encoding UTF8
        Add-DeploymentCheck -Status "PASS" -Label "COM ports detected" -Detail ($ports -join ", ") -Category "meters"
    }
    else {
        "No COM ports detected." | Set-Content -Path $path -Encoding UTF8
        Add-DeploymentCheck -Status "WARN" -Label "COM ports detected" -Detail "Windows reported no COM ports" -Category "meters"
    }
}

function Read-DotEnvFile {
    param([string]$Path)

    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $separatorIndex = $trimmed.IndexOf("=")
        if ($separatorIndex -lt 1) {
            continue
        }

        $key = $trimmed.Substring(0, $separatorIndex).Trim()
        $value = $trimmed.Substring($separatorIndex + 1).Trim()
        $values[$key] = $value
    }

    return $values
}

function Save-SanitizedEnv {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot
    )

    $envPath = Join-Path $ProjectRoot ".env"
    $outputPath = Join-Path $ReportRoot "sanitized-env.txt"
    if (-not (Test-Path $envPath)) {
        "Missing .env at $envPath" | Set-Content -Path $outputPath -Encoding UTF8
        Add-DeploymentCheck -Status "WARN" -Label ".env" -Detail ".env is missing" -Category "environment"
        return
    }

    $sanitized = foreach ($line in Get-Content -Path $envPath) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or $trimmed.IndexOf("=") -lt 1) {
            $line
            continue
        }

        $separatorIndex = $line.IndexOf("=")
        $key = $line.Substring(0, $separatorIndex).Trim()
        if ($key -match "(?i)(PASSWORD|SECRET|TOKEN|KEY)") {
            "$key=***REDACTED***"
        }
        else {
            $line
        }
    }

    $sanitized | Set-Content -Path $outputPath -Encoding UTF8
    Add-DeploymentCheck -Status "PASS" -Label ".env" -Detail "sanitized copy written" -Category "environment"
}

function Ensure-EnvFile {
    param(
        [string]$ProjectRoot,
        [bool]$Modify
    )

    $envPath = Join-Path $ProjectRoot ".env"
    $examplePath = Join-Path $ProjectRoot ".env.example"
    if (Test-Path $envPath) {
        Add-DeploymentCheck -Status "PASS" -Label ".env exists" -Detail $envPath -Category "environment"
        return
    }

    if (-not $Modify) {
        Add-DeploymentCheck -Status "WARN" -Label ".env exists" -Detail ".env is missing; read-only mode will not create it" -Category "environment"
        return
    }

    if (-not (Test-Path $examplePath)) {
        Add-DeploymentCheck -Status "FAIL" -Label ".env create" -Detail ".env.example is missing" -Category "environment"
        return
    }

    Copy-Item -Path $examplePath -Destination $envPath -Force
    Add-DeploymentCheck -Status "PASS" -Label ".env create" -Detail "created .env from .env.example" -Category "environment"
}

function Backup-FileIfExists {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
    $backupPath = "$Path.bak_$timestamp"
    Copy-Item -Path $Path -Destination $backupPath -Force
    Add-DeploymentCheck -Status "PASS" -Label "$Label backup" -Detail $backupPath -Category "backup"
    return $backupPath
}

function Invoke-LoggedCommand {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$LogPath,
        [string]$Label,
        [bool]$Required = $true
    )

    Push-Location $WorkingDirectory
    try {
        $output = & $FilePath @Arguments 2>&1
        $exitCode = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
        $output | Set-Content -Path $LogPath -Encoding UTF8
        if ($exitCode -eq 0) {
            Add-DeploymentCheck -Status "PASS" -Label $Label -Detail "exit code 0" -Category "command"
            return $true
        }

        $status = if ($Required) { "FAIL" } else { "WARN" }
        Add-DeploymentCheck -Status $status -Label $Label -Detail "exit code $exitCode; see $LogPath" -Category "command"
        return $false
    }
    catch {
        $_.Exception.Message | Set-Content -Path $LogPath -Encoding UTF8
        $status = if ($Required) { "FAIL" } else { "WARN" }
        Add-DeploymentCheck -Status $status -Label $Label -Detail $_.Exception.Message -Category "command"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Test-Prerequisites {
    param(
        [bool]$IncludeFrontend = $true,
        [bool]$IncludeDatabase = $true
    )

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        Add-DeploymentCheck -Status "PASS" -Label "Python on PATH" -Detail $python.Source -Category "prerequisite"
    }
    else {
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) {
            Add-DeploymentCheck -Status "PASS" -Label "Python launcher" -Detail $py.Source -Category "prerequisite"
        }
        else {
            Add-DeploymentCheck -Status "FAIL" -Label "Python" -Detail "Python was not found; install Python manually first" -Category "prerequisite"
        }
    }

    if ($IncludeFrontend) {
        $node = Get-Command node -ErrorAction SilentlyContinue
        $npm = Get-Command npm -ErrorAction SilentlyContinue
        if ($node) {
            Add-DeploymentCheck -Status "PASS" -Label "Node.js" -Detail $node.Source -Category "prerequisite"
        }
        else {
            Add-DeploymentCheck -Status "FAIL" -Label "Node.js" -Detail "node was not found; install Node.js manually first" -Category "prerequisite"
        }
        if ($npm) {
            Add-DeploymentCheck -Status "PASS" -Label "npm" -Detail $npm.Source -Category "prerequisite"
        }
        else {
            Add-DeploymentCheck -Status "FAIL" -Label "npm" -Detail "npm was not found; install Node.js/npm manually first" -Category "prerequisite"
        }
    }

    if ($IncludeDatabase) {
        $services = @(Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue)
        if ($services.Count -gt 0) {
            $running = @($services | Where-Object { $_.Status -eq "Running" })
            $detail = ($services | ForEach-Object { "$($_.Name)=$($_.Status)" }) -join ", "
            if ($running.Count -gt 0) {
                Add-DeploymentCheck -Status "PASS" -Label "PostgreSQL service" -Detail $detail -Category "database"
            }
            else {
                Add-DeploymentCheck -Status "FAIL" -Label "PostgreSQL service" -Detail $detail -Category "database"
            }
        }
        else {
            Add-DeploymentCheck -Status "WARN" -Label "PostgreSQL service" -Detail "no postgresql* Windows service found; database connection check may still work" -Category "database"
        }
    }
}

function Ensure-PythonEnvironment {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot
    )

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    $bootstrap = Join-Path $ProjectRoot "scripts\bootstrap_python_env.ps1"
    if (-not (Test-Path $venvPython)) {
        if (-not (Test-Path $bootstrap)) {
            Add-DeploymentCheck -Status "FAIL" -Label "Python environment" -Detail "bootstrap script missing" -Category "python"
            return $false
        }
        Invoke-LoggedCommand -FilePath "powershell.exe" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $bootstrap, "-ProjectRoot", $ProjectRoot) -WorkingDirectory $ProjectRoot -LogPath (Join-Path $ReportRoot "python-bootstrap.txt") -Label "create .venv" | Out-Null
    }
    else {
        Add-DeploymentCheck -Status "PASS" -Label ".venv python" -Detail $venvPython -Category "python"
    }

    if (-not (Test-Path $venvPython)) {
        Add-DeploymentCheck -Status "FAIL" -Label "Python environment" -Detail ".venv python is still missing" -Category "python"
        return $false
    }

    $requirementsPath = Join-Path $ProjectRoot "requirements.txt"
    if (Test-Path $requirementsPath) {
        Invoke-LoggedCommand -FilePath $venvPython -Arguments @("-m", "pip", "install", "-r", $requirementsPath) -WorkingDirectory $ProjectRoot -LogPath (Join-Path $ReportRoot "python-requirements.txt") -Label "Python dependencies" | Out-Null
    }
    else {
        Add-DeploymentCheck -Status "WARN" -Label "Python dependencies" -Detail "requirements.txt missing" -Category "python"
    }

    return $true
}

function Test-PythonEnvironment {
    param([string]$ProjectRoot)

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Add-DeploymentCheck -Status "PASS" -Label ".venv python" -Detail $venvPython -Category "python"
    }
    else {
        Add-DeploymentCheck -Status "WARN" -Label ".venv python" -Detail ".venv is missing" -Category "python"
    }
}

function Invoke-FrontendStep {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot,
        [bool]$Build
    )

    $frontendRoot = Join-Path $ProjectRoot "frontend"
    $distIndex = Join-Path $frontendRoot "dist\index.html"
    if (-not (Test-Path $frontendRoot)) {
        Add-DeploymentCheck -Status "FAIL" -Label "frontend folder" -Detail "frontend folder missing" -Category "frontend"
        return
    }

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) {
        Add-DeploymentCheck -Status "FAIL" -Label "frontend npm" -Detail "npm not found" -Category "frontend"
        return
    }

    $nodeModules = Join-Path $frontendRoot "node_modules"
    if ($Build -and -not (Test-Path $nodeModules)) {
        Invoke-LoggedCommand -FilePath $npm.Source -Arguments @("ci") -WorkingDirectory $frontendRoot -LogPath (Join-Path $ReportRoot "frontend-npm-ci.txt") -Label "frontend npm ci" | Out-Null
    }
    elseif (Test-Path $nodeModules) {
        Add-DeploymentCheck -Status "PASS" -Label "frontend dependencies" -Detail "node_modules exists" -Category "frontend"
    }
    else {
        Add-DeploymentCheck -Status "WARN" -Label "frontend dependencies" -Detail "node_modules missing; read-only mode will not run npm ci" -Category "frontend"
    }

    if ($Build) {
        Invoke-LoggedCommand -FilePath $npm.Source -Arguments @("run", "build") -WorkingDirectory $frontendRoot -LogPath (Join-Path $ReportRoot "frontend-build.txt") -Label "frontend build" | Out-Null
    }

    if (Test-Path $distIndex) {
        Add-DeploymentCheck -Status "PASS" -Label "frontend/dist/index.html" -Detail $distIndex -Category "frontend"
    }
    else {
        $status = if ($Build) { "FAIL" } else { "WARN" }
        Add-DeploymentCheck -Status $status -Label "frontend/dist/index.html" -Detail "production build missing" -Category "frontend"
    }
}

function Invoke-DatabaseSetup {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot,
        [bool]$ApplySchema,
        [bool]$CreateDatabase
    )

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Add-DeploymentCheck -Status "FAIL" -Label "database setup" -Detail ".venv python is missing; cannot run deployment DB helper" -Category "database"
        return
    }

    $outputPath = Join-Path $ReportRoot "postgres-check.json"
    $logPath = Join-Path $ReportRoot "postgres-check.txt"
    $helperPath = Join-Path $ProjectRoot "deployment\db_setup.py"
    $arguments = @($helperPath, "--project-root", $ProjectRoot, "--output", $outputPath)
    if ($ApplySchema) {
        $arguments += "--apply-schema"
    }
    if ($CreateDatabase) {
        $arguments += "--create-database"
    }

    Invoke-LoggedCommand -FilePath $venvPython -Arguments $arguments -WorkingDirectory $ProjectRoot -LogPath $logPath -Label "database setup/check" -Required:$ApplySchema | Out-Null

    if (Test-Path $outputPath) {
        try {
            $payload = Get-Content -Path $outputPath -Raw | ConvertFrom-Json
            foreach ($check in $payload.checks) {
                Add-DeploymentCheck -Status $check.status -Label $check.label -Detail $check.detail -Category "database"
            }
        }
        catch {
            Add-DeploymentCheck -Status "WARN" -Label "database check parse" -Detail $_.Exception.Message -Category "database"
        }
    }
}

function Copy-DeploymentArtifacts {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot
    )

    $meterConfigPath = Join-Path $ProjectRoot "config\meter_config.json"
    if (Test-Path $meterConfigPath) {
        Copy-Item -Path $meterConfigPath -Destination (Join-Path $ReportRoot "meter-config.json") -Force
        Add-DeploymentCheck -Status "PASS" -Label "meter config artifact" -Detail "copied meter-config.json" -Category "evidence"
    }
    else {
        Add-DeploymentCheck -Status "FAIL" -Label "meter config artifact" -Detail "config\meter_config.json missing" -Category "evidence"
    }
}

function Test-MeterConfiguration {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot
    )

    $meterConfigPath = Join-Path $ProjectRoot "config\meter_config.json"
    if (-not (Test-Path $meterConfigPath)) {
        Add-DeploymentCheck -Status "FAIL" -Label "meter config" -Detail "config\meter_config.json missing" -Category "meters"
        return
    }

    try {
        $config = Get-Content -Path $meterConfigPath -Raw | ConvertFrom-Json
    }
    catch {
        Add-DeploymentCheck -Status "FAIL" -Label "meter config JSON" -Detail $_.Exception.Message -Category "meters"
        return
    }

    $detectedPorts = @(Get-DetectedComPorts | ForEach-Object { $_.ToUpperInvariant() })
    $connectionDefaults = Get-ObjectPropertyValue -Object $config -Name "connection_defaults" -DefaultValue ([pscustomobject]@{})
    $enabledMeters = @($config.meters | Where-Object {
        -not ($_.PSObject.Properties.Name -contains "enabled") -or [bool]$_.enabled
    })
    if ($enabledMeters.Count -gt 0) {
        Add-DeploymentCheck -Status "PASS" -Label "enabled meters" -Detail "$($enabledMeters.Count) enabled meter(s) configured" -Category "meters"
    }
    else {
        Add-DeploymentCheck -Status "WARN" -Label "enabled meters" -Detail "no enabled meters configured" -Category "meters"
    }

    $seenPortSlave = @{}
    $settingsByPort = @{}
    foreach ($meter in $enabledMeters) {
        $connection = $meter.connection
        $port = ""
        $port = Get-MeterConnectionPort -Connection $connection
        $port = $port.ToUpperInvariant()
        $slaveId = [int](Get-ObjectPropertyValue -Object $connection -Name "slave_id" -DefaultValue 1)

        if (-not $port) {
            Add-DeploymentCheck -Status "FAIL" -Label "$($meter.meter_id) COM port" -Detail "enabled meter has no COM port configured" -Category "meters"
            continue
        }

        if ($detectedPorts.Count -gt 0 -and $detectedPorts -notcontains $port) {
            Add-DeploymentCheck -Status "FAIL" -Label "$($meter.meter_id) COM port" -Detail "configured $port but Windows detects $($detectedPorts -join ', ')" -Category "meters"
        }
        elseif ($detectedPorts.Count -eq 0) {
            Add-DeploymentCheck -Status "WARN" -Label "$($meter.meter_id) COM port" -Detail "configured $port but no COM ports were detected" -Category "meters"
        }
        else {
            Add-DeploymentCheck -Status "PASS" -Label "$($meter.meter_id) COM port" -Detail "$port detected" -Category "meters"
        }

        $portSlaveKey = "$port|$slaveId"
        if ($seenPortSlave.ContainsKey($portSlaveKey)) {
            Add-DeploymentCheck -Status "FAIL" -Label "$($meter.meter_id) slave ID" -Detail "duplicates slave $slaveId on $port with $($seenPortSlave[$portSlaveKey])" -Category "meters"
        }
        else {
            $seenPortSlave[$portSlaveKey] = [string]$meter.meter_id
        }

        $baudRate = Get-ObjectPropertyValue -Object $connection -Name "baud_rate" -DefaultValue (Get-ObjectPropertyValue -Object $connectionDefaults -Name "baud_rate" -DefaultValue 9600)
        $parity = Get-ObjectPropertyValue -Object $connection -Name "parity" -DefaultValue (Get-ObjectPropertyValue -Object $connectionDefaults -Name "parity" -DefaultValue "N")
        $stopBits = Get-ObjectPropertyValue -Object $connection -Name "stop_bits" -DefaultValue (Get-ObjectPropertyValue -Object $connectionDefaults -Name "stop_bits" -DefaultValue 1)
        $byteSize = Get-ObjectPropertyValue -Object $connection -Name "byte_size" -DefaultValue (Get-ObjectPropertyValue -Object $connectionDefaults -Name "byte_size" -DefaultValue 8)
        $timeout = Get-ObjectPropertyValue -Object $connection -Name "timeout" -DefaultValue (Get-ObjectPropertyValue -Object $connectionDefaults -Name "timeout" -DefaultValue 2.0)
        $serialSettings = "baud=$baudRate,parity=$parity,stop_bits=$stopBits,byte_size=$byteSize,timeout=$timeout"
        if ($settingsByPort.ContainsKey($port) -and $settingsByPort[$port] -ne $serialSettings) {
            Add-DeploymentCheck -Status "FAIL" -Label "$($meter.meter_id) serial settings" -Detail "conflicts on $port; expected $($settingsByPort[$port]) but meter has $serialSettings" -Category "meters"
        }
        elseif (-not $settingsByPort.ContainsKey($port)) {
            $settingsByPort[$port] = $serialSettings
        }
    }

    foreach ($port in $settingsByPort.Keys) {
        $metersOnPort = @($enabledMeters | Where-Object {
            $connection = $_.connection
            $configuredPort = Get-MeterConnectionPort -Connection $connection
            $configuredPort.ToUpperInvariant() -eq $port
        })
        if ($metersOnPort.Count -gt 1) {
            Add-DeploymentCheck -Status "PASS" -Label "$port shared bus" -Detail "$($metersOnPort.Count) enabled meter(s) share $port with checked slave IDs" -Category "meters"
        }
    }
}

function Invoke-MeterWizard {
    param(
        [string]$ProjectRoot,
        [bool]$Interactive
    )

    if (-not $Interactive) {
        Add-DeploymentCheck -Status "INFO" -Label "meter wizard" -Detail "skipped in non-interactive mode" -Category "meters"
        return
    }

    $ports = @(Get-DetectedComPorts)
    if ($ports.Count -eq 0) {
        Add-DeploymentCheck -Status "WARN" -Label "meter wizard" -Detail "no COM ports detected, so no guided update was offered" -Category "meters"
        return
    }

    $answer = Read-Host "Update enabled meter COM ports now? Type YES to continue"
    if ($answer -ne "YES") {
        Add-DeploymentCheck -Status "INFO" -Label "meter wizard" -Detail "operator skipped guided update" -Category "meters"
        return
    }

    $meterConfigPath = Join-Path $ProjectRoot "config\meter_config.json"
    $config = Get-Content -Path $meterConfigPath -Raw | ConvertFrom-Json
    Backup-FileIfExists -Path $meterConfigPath -Label "meter_config.json" | Out-Null

    Write-Host "Detected COM ports:"
    for ($index = 0; $index -lt $ports.Count; $index++) {
        Write-Host ("{0}. {1}" -f ($index + 1), $ports[$index])
    }

    $changed = $false
    foreach ($meter in $config.meters) {
        if ($null -ne $meter.enabled -and -not [bool]$meter.enabled) {
            continue
        }
        $currentPort = Get-MeterConnectionPort -Connection $meter.connection
        $currentSlaveId = if ($meter.connection) {
            [int](Get-ObjectPropertyValue -Object $meter.connection -Name "slave_id" -DefaultValue 1)
        }
        else {
            1
        }
        $selection = Read-Host "COM port number for $($meter.meter_id) [$currentPort], blank to keep"

        if (-not $meter.connection) {
            $meter | Add-Member -NotePropertyName "connection" -NotePropertyValue ([pscustomobject]@{}) -Force
        }

        if ($selection) {
            $selectedIndex = 0
            if (-not [int]::TryParse($selection, [ref]$selectedIndex) -or $selectedIndex -lt 1 -or $selectedIndex -gt $ports.Count) {
                Add-DeploymentCheck -Status "WARN" -Label "$($meter.meter_id) COM selection" -Detail "invalid selection '$selection'; kept $currentPort" -Category "meters"
            }
            else {
                $selectedPort = $ports[$selectedIndex - 1]
                $meter.connection | Add-Member -NotePropertyName "port" -NotePropertyValue $selectedPort -Force
                $changed = $true
                Add-DeploymentCheck -Status "PASS" -Label "$($meter.meter_id) COM update" -Detail "$currentPort -> $selectedPort" -Category "meters"
            }
        }

        $slaveSelection = Read-Host "Slave ID for $($meter.meter_id) [$currentSlaveId], blank to keep"
        if ($slaveSelection) {
            $selectedSlaveId = 0
            if (-not [int]::TryParse($slaveSelection, [ref]$selectedSlaveId) -or $selectedSlaveId -lt 1 -or $selectedSlaveId -gt 247) {
                Add-DeploymentCheck -Status "WARN" -Label "$($meter.meter_id) slave selection" -Detail "invalid slave ID '$slaveSelection'; kept $currentSlaveId" -Category "meters"
            }
            else {
                $meter.connection | Add-Member -NotePropertyName "slave_id" -NotePropertyValue $selectedSlaveId -Force
                $changed = $true
                Add-DeploymentCheck -Status "PASS" -Label "$($meter.meter_id) slave update" -Detail "$currentSlaveId -> $selectedSlaveId" -Category "meters"
            }
        }
    }

    if ($changed) {
        $config | ConvertTo-Json -Depth 40 | Set-Content -Path $meterConfigPath -Encoding UTF8
        Add-DeploymentCheck -Status "PASS" -Label "meter config update" -Detail "config\meter_config.json updated with backup" -Category "meters"
    }
    else {
        Add-DeploymentCheck -Status "INFO" -Label "meter config update" -Detail "no changes made" -Category "meters"
    }
}

function Invoke-MeterTrial {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot
    )

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Add-DeploymentCheck -Status "WARN" -Label "meter communication trial" -Detail ".venv python missing; direct Modbus trial skipped" -Category "meters"
        return
    }

    $outputPath = Join-Path $ReportRoot "meter-trial.json"
    $logPath = Join-Path $ReportRoot "meter-trial.txt"
    $helperPath = Join-Path $ProjectRoot "deployment\meter_trial.py"
    Invoke-LoggedCommand -FilePath $venvPython -Arguments @($helperPath, "--project-root", $ProjectRoot, "--output", $outputPath) -WorkingDirectory $ProjectRoot -LogPath $logPath -Label "meter communication trial" -Required:$false | Out-Null

    if (Test-Path $outputPath) {
        try {
            $payload = Get-Content -Path $outputPath -Raw | ConvertFrom-Json
            foreach ($trial in $payload.trials) {
                if ($trial.status -eq "SKIP") {
                    Add-DeploymentCheck -Status "INFO" -Label "$($trial.meter_id) Modbus trial" -Detail $trial.message -Category "meters"
                }
                else {
                    Add-DeploymentCheck -Status $trial.status -Label "$($trial.meter_id) Modbus trial" -Detail $trial.message -Category "meters"
                }
            }
        }
        catch {
            Add-DeploymentCheck -Status "WARN" -Label "meter trial parse" -Detail $_.Exception.Message -Category "meters"
        }
    }
}

function Invoke-ScheduledTaskSetup {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot,
        [string]$TaskName,
        [bool]$RunAsCurrentUser
    )

    if (-not (Test-Admin)) {
        Add-DeploymentCheck -Status "WARN" -Label "administrator privileges" -Detail "scheduled task registration may require Administrator" -Category "scheduler"
    }

    $scriptPath = Join-Path $ProjectRoot "scripts\install_task_scheduler_backend.ps1"
    if (-not (Test-Path $scriptPath)) {
        Add-DeploymentCheck -Status "FAIL" -Label "scheduled task script" -Detail "install_task_scheduler_backend.ps1 missing" -Category "scheduler"
        return
    }

    $arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath, "-TaskName", $TaskName, "-ProjectRoot", $ProjectRoot)
    if ($RunAsCurrentUser) {
        $arguments += "-RunAsCurrentUser"
    }
    Invoke-LoggedCommand -FilePath "powershell.exe" -Arguments $arguments -WorkingDirectory $ProjectRoot -LogPath (Join-Path $ReportRoot "scheduled-task-register.txt") -Label "scheduled task register/update" -Required:$false | Out-Null
}

function Test-ScheduledTaskState {
    param(
        [string]$ReportRoot,
        [string]$TaskName = "EnergyMonitoringBackend"
    )

    $outputPath = Join-Path $ReportRoot "scheduled-tasks.txt"
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
        $lastRunTime = if ($info) { $info.LastRunTime } else { "unavailable" }
        $lastTaskResult = if ($info) { $info.LastTaskResult } else { "unavailable" }
        $nextRunTime = if ($info) { $info.NextRunTime } else { "unavailable" }
        $lines = @(
            "TaskName: $($task.TaskName)",
            "State: $($task.State)",
            "Enabled: $($task.Settings.Enabled)",
            "LastRunTime: $lastRunTime",
            "LastTaskResult: $lastTaskResult",
            "NextRunTime: $nextRunTime"
        )
        $lines | Set-Content -Path $outputPath -Encoding UTF8
        if ($task.Settings.Enabled) {
            Add-DeploymentCheck -Status "PASS" -Label "scheduled task $TaskName" -Detail "state=$($task.State)" -Category "scheduler"
        }
        else {
            Add-DeploymentCheck -Status "FAIL" -Label "scheduled task $TaskName" -Detail "task exists but is disabled" -Category "scheduler"
        }
    }
    catch {
        $_.Exception.Message | Set-Content -Path $outputPath -Encoding UTF8
        Add-DeploymentCheck -Status "FAIL" -Label "scheduled task $TaskName" -Detail $_.Exception.Message -Category "scheduler"
    }
}

function Invoke-ApiChecks {
    param(
        [string]$ApiBaseUrl,
        [string]$ReportRoot,
        [bool]$Required = $false
    )

    $healthPath = Join-Path $ReportRoot "api-health.json"
    $statusPath = Join-Path $ReportRoot "api-status.json"
    try {
        $health = Invoke-RestMethod -Uri "$ApiBaseUrl/api/health" -Method Get -TimeoutSec 10
        $health | ConvertTo-Json -Depth 20 | Set-Content -Path $healthPath -Encoding UTF8
        Add-DeploymentCheck -Status "PASS" -Label "API health" -Detail "$ApiBaseUrl/api/health reachable" -Category "api"
    }
    catch {
        $_.Exception.Message | Set-Content -Path $healthPath -Encoding UTF8
        $status = if ($Required) { "FAIL" } else { "WARN" }
        Add-DeploymentCheck -Status $status -Label "API health" -Detail "backend not reachable at $ApiBaseUrl/api/health" -Category "api"
    }

    try {
        $statusPayload = Invoke-RestMethod -Uri "$ApiBaseUrl/api/status" -Method Get -TimeoutSec 10
        $statusPayload | ConvertTo-Json -Depth 20 | Set-Content -Path $statusPath -Encoding UTF8
        Add-DeploymentCheck -Status "PASS" -Label "API status" -Detail "runtime status reachable" -Category "api"
    }
    catch {
        $_.Exception.Message | Set-Content -Path $statusPath -Encoding UTF8
        $status = if ($Required) { "FAIL" } else { "WARN" }
        Add-DeploymentCheck -Status $status -Label "API status" -Detail "backend not reachable at $ApiBaseUrl/api/status" -Category "api"
    }
}

function Save-LogsTail {
    param(
        [string]$ProjectRoot,
        [string]$ReportRoot
    )

    $logsDir = Join-Path $ProjectRoot "logs"
    $outputPath = Join-Path $ReportRoot "logs-tail.txt"
    if (-not (Test-Path $logsDir)) {
        "logs folder missing" | Set-Content -Path $outputPath -Encoding UTF8
        Add-DeploymentCheck -Status "WARN" -Label "logs tail" -Detail "logs folder missing" -Category "evidence"
        return
    }

    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($file in Get-ChildItem -Path $logsDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 8) {
        $lines.Add("===== $($file.Name) =====")
        try {
            foreach ($line in Get-Content -Path $file.FullName -Tail 80 -ErrorAction Stop) {
                $lines.Add($line)
            }
        }
        catch {
            $lines.Add("Unable to read $($file.FullName): $($_.Exception.Message)")
        }
        $lines.Add("")
    }
    $lines | Set-Content -Path $outputPath -Encoding UTF8
    Add-DeploymentCheck -Status "PASS" -Label "logs tail" -Detail "recent logs collected" -Category "evidence"
}

function Compress-DeploymentReport {
    param([string]$ReportRoot)

    $zipPath = "$ReportRoot.zip"
    if (Test-Path $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $ReportRoot "*") -DestinationPath $zipPath -Force
    Add-DeploymentCheck -Status "PASS" -Label "evidence zip" -Detail $zipPath -Category "evidence"
    return $zipPath
}
