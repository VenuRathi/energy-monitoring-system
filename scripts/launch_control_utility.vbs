Option Explicit

Dim shell
Dim fileSystem
Dim scriptDirectory
Dim projectRoot
Dim controlPath
Dim powershellPath
Dim command

Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

scriptDirectory = fileSystem.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fileSystem.GetParentFolderName(scriptDirectory)
controlPath = scriptDirectory & "\plant_energy_monitor_control.ps1"
powershellPath = shell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\WindowsPowerShell\v1.0\powershell.exe"

shell.CurrentDirectory = projectRoot
command = Chr(34) & powershellPath & Chr(34) & " -NoProfile -ExecutionPolicy Bypass -STA -File " & _
    Chr(34) & controlPath & Chr(34) & " -ProjectRoot " & Chr(34) & projectRoot & Chr(34)
shell.Run command, 1, False

Set fileSystem = Nothing
Set shell = Nothing
