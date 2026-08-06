Option Explicit

Dim shell
Dim dashboardUrl

Set shell = CreateObject("WScript.Shell")

dashboardUrl = "http://127.0.0.1:5000"

shell.Run dashboardUrl, 1, False

Set shell = Nothing
