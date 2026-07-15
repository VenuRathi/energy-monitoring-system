param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$requiredDirectories = @(
    "logs",
    "backups",
    "release"
)

foreach ($relativePath in $requiredDirectories) {
    $fullPath = Join-Path $ProjectRoot $relativePath
    New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    Write-Host "Ensured directory: $fullPath"
}

$envExamplePath = Join-Path $ProjectRoot ".env.example"
$envPath = Join-Path $ProjectRoot ".env"

if ((Test-Path $envExamplePath) -and (-not (Test-Path $envPath))) {
    Copy-Item -Path $envExamplePath -Destination $envPath -Force
    Write-Host "Created .env from .env.example at $envPath"
}
elseif (Test-Path $envPath) {
    Write-Host ".env already exists at $envPath"
}
else {
    Write-Warning ".env.example was not found. Create .env manually before running the backend."
}

$frontendIndex = Join-Path $ProjectRoot "frontend\dist\index.html"
if (Test-Path $frontendIndex) {
    Write-Host "Frontend build detected: $frontendIndex"
}
else {
    Write-Warning "Frontend build not found at $frontendIndex"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit .env with the real PostgreSQL, API, and meter settings"
Write-Host "2. Create or repair .venv if needed: powershell -ExecutionPolicy Bypass -File .\\scripts\\bootstrap_python_env.ps1"
Write-Host "3. If .venv already exists but is broken, rerun with -Recreate"
Write-Host "4. Run the environment check: powershell -ExecutionPolicy Bypass -File .\\scripts\\post_install_check.ps1"
Write-Host "5. Launch the app locally with run_app.bat or run the backend once manually"
Write-Host "6. Register scheduled startup if this is the plant PC"
