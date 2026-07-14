param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputRoot = "",
    [string]$BundleName = "energy-monitoring-system-pilot"
)

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $ProjectRoot "release"
}

$frontendDist = Join-Path $ProjectRoot "frontend\dist"
if (-not (Test-Path $frontendDist)) {
    throw "Frontend production build not found at $frontendDist. Run 'cd frontend && npm run build' before preparing a release bundle."
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$bundleRoot = Join-Path $OutputRoot "${BundleName}_${timestamp}"
$bundleAppRoot = Join-Path $bundleRoot "energy-monitoring-system"
New-Item -ItemType Directory -Path $bundleAppRoot -Force | Out-Null

$itemsToCopy = @(
    "main.py",
    "requirements.txt",
    "README.md",
    ".env.example",
    "app",
    "config",
    "docs",
    "scripts",
    "utils",
    "frontend\dist"
)

foreach ($relativePath in $itemsToCopy) {
    $sourcePath = Join-Path $ProjectRoot $relativePath
    if (-not (Test-Path $sourcePath)) {
        continue
    }

    $destinationPath = Join-Path $bundleAppRoot $relativePath
    $destinationParent = Split-Path $destinationPath -Parent
    if ($destinationParent) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }

    Copy-Item -Path $sourcePath -Destination $destinationPath -Recurse -Force
}

$startHerePath = Join-Path $bundleRoot "START_HERE.txt"
@"
Energy Monitoring System - Pilot Release Bundle

Bundle created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Contents:
- energy-monitoring-system\  -> application files

Recommended first steps on a new PC:
1. Read energy-monitoring-system\docs\plant-pc-deployment.md
2. Copy energy-monitoring-system\.env.example to .env and fill real values
3. Create .venv and run: pip install -r requirements.txt
4. Confirm PostgreSQL and COM port settings
5. Run backend once manually, then set up Task Scheduler

Important:
- This bundle does not include a Python virtual environment
- This bundle does not include PostgreSQL binaries
- This bundle does include the built frontend from frontend\dist
"@ | Set-Content -Path $startHerePath -Encoding UTF8

$zipPath = Join-Path $OutputRoot "${BundleName}_${timestamp}.zip"
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path $bundleRoot -DestinationPath $zipPath -Force

Write-Host "Release bundle folder: $bundleRoot"
Write-Host "Release bundle archive: $zipPath"
