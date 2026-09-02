param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

if (-not $OutputPath) {
    $reportRoot = Join-Path $ProjectRoot "deployment-reports"
    $OutputPath = Join-Path $reportRoot ("pc-inventory_{0}.json" -f (Get-Date -Format "yyyy-MM-dd_HHmmss"))
}

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

function New-Check {
    param(
        [string]$Name,
        [bool]$Present,
        [string]$Details
    )

    [ordered]@{
        name = $Name
        status = if ($Present) { "PASS" } else { "WARN" }
        details = $Details
    }
}

$manifestPath = Join-Path $ProjectRoot "config\deployment-manifest.json"
$manifest = if (Test-Path -LiteralPath $manifestPath) {
    Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
}
else {
    $null
}

$requiredPaths = @(
    "main.py",
    "app",
    "config",
    "frontend\dist\index.html",
    "scripts",
    "docs\handover\plant-pc-deployment.md",
    ".env"
)
$pathChecks = foreach ($relativePath in $requiredPaths) {
    $fullPath = Join-Path $ProjectRoot $relativePath
    New-Check -Name "path:$relativePath" -Present (Test-Path -LiteralPath $fullPath) -Details $fullPath
}

$pythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$pythonVersion = "not available"
if (Test-Path -LiteralPath $pythonPath) {
    try {
        $pythonVersion = (& $pythonPath --version 2>&1 | Out-String).Trim()
    }
    catch {
        $pythonVersion = "present but could not execute: $($_.Exception.Message)"
    }
}

$postgresServices = @(Get-Service -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match "(?i)^postgres" -or $_.DisplayName -match "(?i)postgres"
})
$postgresDetails = if ($postgresServices.Count -eq 0) {
    "No PostgreSQL Windows service detected."
}
else {
    ($postgresServices | ForEach-Object { "$($_.Name)=$($_.Status); startup=$($_.StartType)" }) -join "; "
}

$taskNames = @("EnergyMonitoringBackend", "EnergyMonitoringDailyBackup")
$taskChecks = foreach ($taskName in $taskNames) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    $details = if ($task) { "$($task.TaskName)=$($task.State)" } else { "Task not found" }
    New-Check -Name "scheduled-task:$taskName" -Present ($null -ne $task) -Details $details
}

$gitCommit = "not a Git checkout"
try {
    $gitCommit = (& git -C $ProjectRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
    if (-not $gitCommit) { $gitCommit = "unavailable" }
}
catch {
    $gitCommit = "unavailable"
}

$report = [ordered]@{
    schemaVersion = 1
    capturedAt = (Get-Date).ToUniversalTime().ToString("o")
    computerName = $env:COMPUTERNAME
    userName = $env:USERNAME
    projectRoot = $ProjectRoot
    deploymentMode = if (Test-Path -LiteralPath (Join-Path $ProjectRoot ".git")) { "source-checkout" } else { "release-or-installer" }
    gitCommit = $gitCommit
    manifestVersion = if ($manifest) { $manifest.manifestVersion } else { $null }
    python = [ordered]@{
        executable = $pythonPath
        version = $pythonVersion
    }
    paths = @($pathChecks)
    services = @($postgresDetails)
    scheduledTasks = @($taskChecks)
    notes = @(
        "This report intentionally excludes .env contents, credentials, database contents, and log contents.",
        "WARN means the item needs review on this PC; it is not an automatic failure."
    )
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host "PC inventory written to: $OutputPath"
