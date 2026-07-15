param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$BundleRoot = "",
    [string]$OutputDir = "",
    [string]$IsccPath = "",
    [switch]$SkipBundleValidation
)

function Resolve-IsccPath {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        if (Test-Path $ExplicitPath) {
            return (Resolve-Path $ExplicitPath).Path
        }

        throw "Provided ISCC path was not found: $ExplicitPath"
    }

    $envCandidates = @(
        $env:ISCC_PATH,
        $(if ($env:INNO_SETUP_HOME) { Join-Path $env:INNO_SETUP_HOME "ISCC.exe" } else { $null }),
        $(if ($env:INNO_SETUP_HOME) { Join-Path $env:INNO_SETUP_HOME "Compiler\ISCC.exe" } else { $null })
    ) | Where-Object { $_ }

    foreach ($candidate in $envCandidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $registryCandidates = @()
    $registryRoots = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    foreach ($registryRoot in $registryRoots) {
        try {
            $matches = Get-ItemProperty $registryRoot -ErrorAction SilentlyContinue |
                Where-Object { $_.DisplayName -like "*Inno Setup*" }

            foreach ($match in $matches) {
                if ($match.InstallLocation) {
                    $registryCandidates += (Join-Path $match.InstallLocation "ISCC.exe")
                    $registryCandidates += (Join-Path $match.InstallLocation "Compiler\ISCC.exe")
                }

                if ($match.DisplayIcon) {
                    $registryCandidates += (($match.DisplayIcon -split ",")[0].Trim('"'))
                }
            }
        }
        catch {
        }
    }

    $commonCandidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\Compiler\ISCC.exe",
        "C:\Program Files\Inno Setup 6\Compiler\ISCC.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\Compiler\ISCC.exe")
    ) + $registryCandidates

    foreach ($candidate in $commonCandidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $message = @"
ISCC.exe was not found.

How to fix:
1. Install Inno Setup 6 on this machine
   - common path: C:\Program Files (x86)\Inno Setup 6\ISCC.exe
2. Or add ISCC.exe to PATH
3. Or rerun with:
   powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1 -IsccPath "C:\path\to\ISCC.exe"
4. Or set one of these environment variables before running:
   - ISCC_PATH
   - INNO_SETUP_HOME

This project can already produce a release bundle zip without Inno Setup:
   powershell -ExecutionPolicy Bypass -File .\scripts\prepare_release_bundle.ps1
"@

    throw $message
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

$iscc = Resolve-IsccPath -ExplicitPath $IsccPath
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
if ($OutputDir) {
    Write-Host "Installer output directory: $OutputDir"
}
