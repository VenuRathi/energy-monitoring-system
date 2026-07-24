param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$BundleRoot = "",
    [switch]$RequireZip
)

function Resolve-BundleFolder {
    param([string]$ReleaseRoot)

    $latestBundle = Get-ChildItem -Path $ReleaseRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "energy-monitoring-system-pilot_*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1

    if (-not $latestBundle) {
        throw "No release bundle folder was found under $ReleaseRoot. Run scripts\prepare_release_bundle.ps1 first."
    }

    return $latestBundle.FullName
}

function Write-Check {
    param(
        [string]$Label,
        [bool]$Ok,
        [string]$Details
    )

    $status = if ($Ok) { "OK" } else { "FAIL" }
    Write-Host ("[{0}] {1}: {2}" -f $status, $Label, $Details)
}

$releaseRoot = Join-Path $ProjectRoot "release"
$bundleFolder = ""

if (-not $BundleRoot) {
    $bundleFolder = Resolve-BundleFolder -ReleaseRoot $releaseRoot
    $BundleRoot = Join-Path $bundleFolder "energy-monitoring-system"
}
elseif ((Split-Path $BundleRoot -Leaf) -eq "energy-monitoring-system") {
    $bundleFolder = Split-Path $BundleRoot -Parent
}
else {
    $bundleFolder = $BundleRoot
    $BundleRoot = Join-Path $bundleFolder "energy-monitoring-system"
}

if (-not (Test-Path $BundleRoot)) {
    throw "Bundle application root not found: $BundleRoot"
}

$checks = @(
    @{ Label = "Bundle app root"; Path = $BundleRoot },
    @{ Label = "main.py"; Path = (Join-Path $BundleRoot "main.py") },
    @{ Label = "run_app.bat"; Path = (Join-Path $BundleRoot "run_app.bat") },
    @{ Label = "requirements.txt"; Path = (Join-Path $BundleRoot "requirements.txt") },
    @{ Label = "README.md"; Path = (Join-Path $BundleRoot "README.md") },
    @{ Label = "LICENSE"; Path = (Join-Path $BundleRoot "LICENSE") },
    @{ Label = ".env.example"; Path = (Join-Path $BundleRoot ".env.example") },
    @{ Label = "frontend build"; Path = (Join-Path $BundleRoot "frontend\dist\index.html") },
    @{ Label = "launch_app.ps1"; Path = (Join-Path $BundleRoot "scripts\launch_app.ps1") },
    @{ Label = "run_backend_service.bat"; Path = (Join-Path $BundleRoot "scripts\run_backend_service.bat") },
    @{ Label = "run_backend_watchdog.ps1"; Path = (Join-Path $BundleRoot "scripts\run_backend_watchdog.ps1") },
    @{ Label = "install_task_scheduler_backend.ps1"; Path = (Join-Path $BundleRoot "scripts\install_task_scheduler_backend.ps1") },
    @{ Label = "stop_backend_task.ps1"; Path = (Join-Path $BundleRoot "scripts\stop_backend_task.ps1") },
    @{ Label = "first_run_setup.ps1"; Path = (Join-Path $BundleRoot "scripts\first_run_setup.ps1") },
    @{ Label = "bootstrap_python_env.ps1"; Path = (Join-Path $BundleRoot "scripts\bootstrap_python_env.ps1") },
    @{ Label = "post_install_check.ps1"; Path = (Join-Path $BundleRoot "scripts\post_install_check.ps1") },
    @{ Label = "collect_pilot_evidence.ps1"; Path = (Join-Path $BundleRoot "scripts\collect_pilot_evidence.ps1") },
    @{ Label = "install_user_startup_backend.ps1"; Path = (Join-Path $BundleRoot "scripts\install_user_startup_backend.ps1") },
    @{ Label = "plant-pc-deployment.md"; Path = (Join-Path $BundleRoot "docs\plant-pc-deployment.md") },
    @{ Label = "release-bundle.md"; Path = (Join-Path $BundleRoot "docs\release-bundle.md") },
    @{ Label = "pilot-evidence-log.md"; Path = (Join-Path $BundleRoot "docs\pilot-evidence-log.md") }
)

$allOk = $true
foreach ($check in $checks) {
    $exists = Test-Path $check.Path
    Write-Check -Label $check.Label -Ok $exists -Details $check.Path
    if (-not $exists) {
        $allOk = $false
    }
}

$startHerePath = Join-Path $bundleFolder "START_HERE.txt"
$startHereExists = Test-Path $startHerePath
Write-Check -Label "START_HERE.txt" -Ok $startHereExists -Details $startHerePath
if (-not $startHereExists) {
    $allOk = $false
}

$releaseInfoPath = Join-Path $bundleFolder "RELEASE_INFO.txt"
$releaseInfoExists = Test-Path $releaseInfoPath
Write-Check -Label "RELEASE_INFO.txt" -Ok $releaseInfoExists -Details $releaseInfoPath
if (-not $releaseInfoExists) {
    $allOk = $false
}

if ($RequireZip) {
    $zipPath = "$bundleFolder.zip"
    $zipExists = Test-Path $zipPath
    Write-Check -Label "Bundle zip" -Ok $zipExists -Details $zipPath
    if (-not $zipExists) {
        $allOk = $false
    }
}

if (-not $allOk) {
    throw "Release bundle validation failed."
}

Write-Host ""
Write-Host "Release bundle validation passed for: $BundleRoot"
