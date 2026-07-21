param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ShortcutName = "EnergyMonitoringBackend.cmd"
)

$runner = Join-Path $ProjectRoot "scripts\run_backend_service.bat"
if (-not (Test-Path $runner)) {
    throw "Backend runner not found: $runner"
}

$startupFolder = [Environment]::GetFolderPath("Startup")
if (-not $startupFolder) {
    throw "Unable to resolve the current user's Startup folder."
}

$shortcutPath = Join-Path $startupFolder $ShortcutName
$lines = @(
    "@echo off",
    "cd /d `"$ProjectRoot`"",
    "call `"$runner`""
)

$lines | Set-Content -Path $shortcutPath -Encoding ASCII

Write-Host "User startup backend launcher installed:"
Write-Host $shortcutPath
Write-Host "This starts the backend when the current Windows user logs in."
