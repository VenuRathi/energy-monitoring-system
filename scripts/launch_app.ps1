param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$NoBrowser
)

function Get-EnvMap {
    param([string]$Path)

    $map = @{}
    if (-not (Test-Path $Path)) {
        return $map
    }

    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed -split "=", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $map[$parts[0].Trim()] = $parts[1].Trim()
    }

    return $map
}

function Resolve-AppUrl {
    param([hashtable]$EnvMap)

    $hostValue = "$($EnvMap["API_HOST"])".Trim()
    $portValue = "$($EnvMap["API_PORT"])".Trim()

    if (-not $portValue) {
        $portValue = "5000"
    }

    if (-not $hostValue -or $hostValue -in @("0.0.0.0", "::", "*")) {
        $hostValue = "127.0.0.1"
    }

    return "http://{0}:{1}" -f $hostValue, $portValue
}

function Test-BackendHealth {
    param([string]$BaseUrl)

    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/health" -Method Get -TimeoutSec 4
        return $response -and $response.status
    }
    catch {
        return $false
    }
}

$envPath = Join-Path $ProjectRoot ".env"
$watchdogPath = Join-Path $ProjectRoot "scripts\run_backend_watchdog.ps1"
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$envMap = Get-EnvMap -Path $envPath
$appUrl = Resolve-AppUrl -EnvMap $envMap

if (-not (Test-Path $venvPython)) {
    Write-Host "Project virtual environment was not found at:" -ForegroundColor Yellow
    Write-Host $venvPython
    Write-Host ""
    Write-Host "Run this first:" -ForegroundColor Yellow
    Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_python_env.ps1"
    exit 1
}

if (-not (Test-Path $watchdogPath)) {
    throw "Backend watchdog not found: $watchdogPath"
}

function Test-BackendHourlyEnergyRoute {
    param([string]$BaseUrl)

    try {
        # Probe a meter id that does not need to exist. A current backend returns
        # an empty JSON array; a pre-hourly-history backend returns 404.
        $response = Invoke-WebRequest `
            -Uri "$BaseUrl/api/meters/__startup_probe__/hourly-energy?hours=1" `
            -Method Get `
            -TimeoutSec 4 `
            -UseBasicParsing
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

$backendReady = (Test-BackendHealth -BaseUrl $appUrl) -and (Test-BackendHourlyEnergyRoute -BaseUrl $appUrl)

if (-not $backendReady) {
    Write-Host "Backend is not reachable at $appUrl. Starting hidden backend watchdog..." -ForegroundColor Cyan
    Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden",
            "-File", $watchdogPath,
            "-ProjectRoot", $ProjectRoot
        ) `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden

    $deadline = (Get-Date).AddSeconds(25)
    do {
        Start-Sleep -Seconds 2
        $backendReady = Test-BackendHealth -BaseUrl $appUrl
    } while (-not $backendReady -and (Get-Date) -lt $deadline)
}

if ($backendReady) {
    Write-Host "Backend is ready at $appUrl" -ForegroundColor Green
    if (-not $NoBrowser) {
        Start-Process $appUrl | Out-Null
    }
    exit 0
}

Write-Host "Backend did not become ready at $appUrl." -ForegroundColor Yellow
Write-Host "Check .env, PostgreSQL, COM port availability, and backend logs before retrying." -ForegroundColor Yellow
Write-Host "You can also run scripts\post_install_check.ps1 for a quick environment check."
exit 1
