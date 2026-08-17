param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ShortcutName = "PlantEnergyMonitorWatchdog.lnk",
    [string]$LegacyShortcutName = "EnergyMonitoringBackend.cmd",
    [string]$LegacyVbsName = "PlantEnergyMonitorWatchdog.vbs",
    [switch]$SkipDesktopShortcut
)

$watchdogLauncher = Join-Path $ProjectRoot "scripts\run_backend_watchdog.vbs"
$dashboardLauncher = Join-Path $ProjectRoot "scripts\launch_dashboard.vbs"
if (-not (Test-Path $watchdogLauncher)) {
    throw "Watchdog launcher not found: $watchdogLauncher"
}
if (-not (Test-Path $dashboardLauncher)) {
    throw "Dashboard launcher not found: $dashboardLauncher"
}

$startupFolder = [Environment]::GetFolderPath("Startup")
if (-not $startupFolder) {
    throw "Unable to resolve the current user's Startup folder."
}

$shortcutPath = Join-Path $startupFolder $ShortcutName
$shell = New-Object -ComObject WScript.Shell
$startupShortcut = $shell.CreateShortcut($shortcutPath)
$startupShortcut.TargetPath = "wscript.exe"
$startupShortcut.Arguments = "`"$watchdogLauncher`""
$startupShortcut.WorkingDirectory = $ProjectRoot
$startupShortcut.Description = "Start the Plant Energy Monitor watchdog after user logon."
$startupShortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$startupShortcut.WindowStyle = 7
$startupShortcut.Save()

$legacyVbsPath = Join-Path $startupFolder $LegacyVbsName
if (Test-Path $legacyVbsPath) {
    $disabledVbsPath = "$legacyVbsPath.disabled"
    if (Test-Path $disabledVbsPath) {
        $disabledVbsPath = "$legacyVbsPath.disabled_$((Get-Date).ToString('yyyyMMdd_HHmmss'))"
    }
    Move-Item -LiteralPath $legacyVbsPath -Destination $disabledVbsPath -Force
    Write-Host "Disabled previous copied VBS launcher: $disabledVbsPath"
}

$legacyPath = Join-Path $startupFolder $LegacyShortcutName
if (Test-Path $legacyPath) {
    $legacyContent = Get-Content -LiteralPath $legacyPath -Raw -ErrorAction SilentlyContinue
    if ($legacyContent -match "run_backend_service\.bat") {
        $disabledPath = "$legacyPath.disabled"
        if (Test-Path $disabledPath) {
            $disabledPath = "$legacyPath.disabled_$((Get-Date).ToString('yyyyMMdd_HHmmss'))"
        }
        Move-Item -LiteralPath $legacyPath -Destination $disabledPath -Force
        Write-Host "Disabled legacy direct backend launcher: $disabledPath"
    }
    else {
        Write-Warning "Existing startup file was not changed because it is not the known legacy backend launcher: $legacyPath"
    }
}

if (-not $SkipDesktopShortcut) {
    $desktopFolder = [Environment]::GetFolderPath("Desktop")
    if (-not $desktopFolder) {
        throw "Unable to resolve the current user's Desktop folder."
    }

    $desktopShortcutPath = Join-Path $desktopFolder "Plant Energy Monitor.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $desktopShortcut = $shell.CreateShortcut($desktopShortcutPath)
    $desktopShortcut.TargetPath = "wscript.exe"
    $desktopShortcut.Arguments = "`"$dashboardLauncher`""
    $desktopShortcut.WorkingDirectory = $ProjectRoot
    $desktopShortcut.Description = "Open the Plant Energy Monitor live dashboard."
    $desktopShortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
    $desktopShortcut.WindowStyle = 1
    $desktopShortcut.Save()
    Write-Host "Desktop shortcut installed: $desktopShortcutPath"
}

Write-Host "Hidden user startup watchdog launcher installed:"
Write-Host $shortcutPath
Write-Host "This starts the watchdog after the current Windows user logs in."
Write-Host "The watchdog starts and monitors main.py independently of the browser."
