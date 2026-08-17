Option Explicit

Dim shell
Dim fileSystem
Dim scriptDirectory
Dim projectRoot
Dim watchdogPath
Dim command

Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

scriptDirectory = fileSystem.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fileSystem.GetParentFolderName(scriptDirectory)
watchdogPath = scriptDirectory & "\run_backend_watchdog.ps1"

shell.CurrentDirectory = projectRoot
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " & _
    Chr(34) & watchdogPath & Chr(34) & " -ProjectRoot " & Chr(34) & projectRoot & Chr(34)
shell.Run command, 0, False

Set fileSystem = Nothing
Set shell = Nothing
