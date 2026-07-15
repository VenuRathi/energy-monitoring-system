param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ApiBaseUrl = "http://127.0.0.1:5000"
)

function Write-Check {
    param(
        [string]$Label,
        [bool]$Ok,
        [string]$Details
    )

    $status = if ($Ok) { "OK" } else { "CHECK" }
    Write-Host ("[{0}] {1}: {2}" -f $status, $Label, $Details)
}

function Resolve-PgDumpPath {
    $command = Get-Command pg_dump -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $commonRoots = @(
        "C:\Program Files\PostgreSQL",
        "C:\Program Files (x86)\PostgreSQL"
    )

    foreach ($root in $commonRoots) {
        if (-not (Test-Path $root)) {
            continue
        }

        $candidate = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "bin\pg_dump.exe" } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1

        if ($candidate) {
            return $candidate
        }
    }

    return $null
}

$envPath = Join-Path $ProjectRoot ".env"
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$frontendIndex = Join-Path $ProjectRoot "frontend\dist\index.html"
$runnerPath = Join-Path $ProjectRoot "scripts\run_backend_service.bat"
$launcherPath = Join-Path $ProjectRoot "run_app.bat"

Write-Check "Project root" (Test-Path $ProjectRoot) $ProjectRoot
Write-Check ".env" (Test-Path $envPath) $envPath
Write-Check "Frontend build" (Test-Path $frontendIndex) $frontendIndex
Write-Check "Backend runner" (Test-Path $runnerPath) $runnerPath
Write-Check "App launcher" (Test-Path $launcherPath) $launcherPath

if (Test-Path $venvPython) {
    try {
        $pythonVersion = & $venvPython --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Check ".venv python" $true ($pythonVersion | Out-String).Trim()
        }
        else {
            Write-Check ".venv python" $false (($pythonVersion | Out-String).Trim())
        }
    }
    catch {
        Write-Check ".venv python" $false $_.Exception.Message
    }
}
else {
    Write-Check ".venv python" $false $venvPython
}

$pythonOnPath = Get-Command python -ErrorAction SilentlyContinue
Write-Check "Python on PATH" ($null -ne $pythonOnPath) ($(if ($pythonOnPath) { $pythonOnPath.Source } else { "python not found on PATH" }))

$pgDumpPath = Resolve-PgDumpPath
Write-Check "pg_dump available" ($null -ne $pgDumpPath) ($(if ($pgDumpPath) { $pgDumpPath } else { "pg_dump not found on PATH or standard PostgreSQL locations" }))

if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    $hasPlaceholderSecrets = $envContent -match "replace_me" -or $envContent -match "replace_with_strong_random_secret"
    Write-Check ".env placeholder values" (-not $hasPlaceholderSecrets) ($(if ($hasPlaceholderSecrets) { "replace_me-style placeholders still present" } else { "no obvious placeholder secrets detected" }))
}

try {
    $ports = [System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object
    $portText = if ($ports.Count -gt 0) { $ports -join ", " } else { "no COM ports detected" }
    Write-Check "COM ports" ($ports.Count -gt 0) $portText
}
catch {
    Write-Check "COM ports" $false $_.Exception.Message
}

try {
    $health = Invoke-RestMethod -Uri "$ApiBaseUrl/api/health" -Method Get -TimeoutSec 5
    Write-Check "API health" $true ($health.status | Out-String).Trim()
}
catch {
    Write-Check "API health" $false "backend not reachable at $ApiBaseUrl"
}
