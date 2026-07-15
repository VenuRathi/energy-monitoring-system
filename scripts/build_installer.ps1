param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$BundleRoot = "",
    [string]$OutputDir = "",
    [switch]$SkipBundleValidation
)

function Resolve-IsccPath {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $commonCandidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $commonCandidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "ISCC.exe was not found. Install Inno Setup 6 first or add ISCC.exe to PATH."
}

if (-not $BundleRoot) {
    $releaseRoot = Join-Path $ProjectRoot "release"
    $latestBundle = Get-ChildItem -Path $releaseRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "energy-monitoring-system-pilot_*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1

    if (-not $latestBundle) {
        throw "No release bundle folder was found under $releaseRoot. Run scripts\prepare_release_bundle.ps1 first."
    }

    $BundleRoot = Join-Path $latestBundle.FullName "energy-monitoring-system"
}

if (-not (Test-Path $BundleRoot)) {
    throw "Bundle root not found: $BundleRoot"
}

$bundleValidator = Join-Path $ProjectRoot "scripts\validate_release_bundle.ps1"
if ((-not $SkipBundleValidation) -and (Test-Path $bundleValidator)) {
    Write-Host "Validating release bundle before installer build..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File $bundleValidator -ProjectRoot $ProjectRoot -BundleRoot $BundleRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Release bundle validation failed. Fix the bundle before compiling the installer."
    }
}

$installerScript = Join-Path $ProjectRoot "installer\energy_monitoring_system.iss"
if (-not (Test-Path $installerScript)) {
    throw "Installer script not found: $installerScript"
}

$iscc = Resolve-IsccPath
Write-Host "Using Inno Setup compiler: $iscc"
Write-Host "Using release bundle: $BundleRoot"

$arguments = @("/DSourceRoot=$BundleRoot")
if ($OutputDir) {
    $arguments += "/O$OutputDir"
}
$arguments += $installerScript

& $iscc @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed."
}

Write-Host "Installer build completed successfully."
