param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"
$launcher = Join-Path $ProjectRoot "scripts\launch_control_utility.vbs"
if (-not (Test-Path $launcher)) {
    throw "Control utility launcher not found: $launcher"
}

$desktopFolder = [Environment]::GetFolderPath("Desktop")
if (-not $desktopFolder) {
    throw "Unable to resolve the current user's Desktop folder."
}

$shortcutPath = Join-Path $desktopFolder "Plant Energy Monitor Control.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$launcher`""
$shortcut.WorkingDirectory = $ProjectRoot
$shortcut.Description = "Temporary Plant Energy Monitor start/stop testing utility."
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$shortcut.WindowStyle = 1
$shortcut.Save()

Write-Host "Installed current-user control shortcut: $shortcutPath"
