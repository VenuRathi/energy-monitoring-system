param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputRoot = "",
    [string]$BundleName = "energy-monitoring-system-pilot"
)

function Resolve-GitCommit {
    param([string]$RootPath)

    try {
        $commit = git -C $RootPath rev-parse --short HEAD 2>$null
        if ($LASTEXITCODE -eq 0 -and $commit) {
            return ($commit | Select-Object -First 1).Trim()
        }
    }
    catch {
    }

    return "unknown"
}

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $ProjectRoot "release"
}

$frontendDist = Join-Path $ProjectRoot "frontend\dist"
if (-not (Test-Path $frontendDist)) {
    throw "Frontend production build not found at $frontendDist. Run 'cd frontend && npm run build' before preparing a release bundle."
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$bundleCreatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$sourceCommit = Resolve-GitCommit -RootPath $ProjectRoot
$bundleRoot = Join-Path $OutputRoot "${BundleName}_${timestamp}"
$bundleAppRoot = Join-Path $bundleRoot "energy-monitoring-system"
New-Item -ItemType Directory -Path $bundleAppRoot -Force | Out-Null

$itemsToCopy = @(
    "main.py",
    "run_app.bat",
    "requirements.txt",
    "README.md",
    "LICENSE",
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

Bundle created: $bundleCreatedAt
Source commit: $sourceCommit

Contents:
- energy-monitoring-system\  -> application files

Recommended first steps on a new PC:
1. Read energy-monitoring-system\docs\plant-pc-deployment.md
2. Copy energy-monitoring-system\.env.example to .env and fill real values
3. Create .venv and run: pip install -r requirements.txt
4. Run energy-monitoring-system\scripts\post_install_check.ps1
5. Confirm PostgreSQL and COM port settings
6. Launch with energy-monitoring-system\run_app.bat, then set up Task Scheduler

Important:
- This bundle does not include a Python virtual environment
- This bundle does not include PostgreSQL binaries
- This bundle does include the built frontend from frontend\dist
"@ | Set-Content -Path $startHerePath -Encoding UTF8

$releaseInfoPath = Join-Path $bundleRoot "RELEASE_INFO.txt"
@"
Energy Monitoring System - Release Metadata

Bundle created: $bundleCreatedAt
Bundle name: ${BundleName}_${timestamp}
Source commit: $sourceCommit
Project root: $ProjectRoot
Application folder: $bundleAppRoot
"@ | Set-Content -Path $releaseInfoPath -Encoding UTF8

$zipPath = Join-Path $OutputRoot "${BundleName}_${timestamp}.zip"
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path $bundleRoot -DestinationPath $zipPath -Force

Write-Host "Release bundle folder: $bundleRoot"
Write-Host "Release bundle archive: $zipPath"
Write-Host "Next check: powershell -ExecutionPolicy Bypass -File .\scripts\validate_release_bundle.ps1 -BundleRoot `"$bundleAppRoot`" -RequireZip"
