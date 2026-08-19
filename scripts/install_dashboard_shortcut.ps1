param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ShortcutName = "Plant Energy Monitor.lnk"
)

$ErrorActionPreference = "Stop"

$dashboardLauncher = Join-Path $ProjectRoot "scripts\launch_dashboard.vbs"
if (-not (Test-Path $dashboardLauncher)) {
    throw "Dashboard launcher not found: $dashboardLauncher"
}

$desktopFolder = [Environment]::GetFolderPath("Desktop")
if (-not $desktopFolder) {
    throw "Unable to resolve the current user's Desktop folder."
}

$shortcutPath = Join-Path $desktopFolder $ShortcutName
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$dashboardLauncher`""
$shortcut.WorkingDirectory = $ProjectRoot
$shortcut.Description = "Open the Plant Energy Monitor dashboard viewer."
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$shortcut.WindowStyle = 1
$shortcut.Save()

Write-Host "Dashboard viewer shortcut installed: $shortcutPath"
Write-Host "This shortcut only opens http://127.0.0.1:5000 and does not manage backend processes."
