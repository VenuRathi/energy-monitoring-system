@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "APP_ROOT=%CD%"
set "LAUNCHER=%APP_ROOT%\scripts\launch_dashboard.vbs"

if not exist "%LAUNCHER%" (
	echo Missing dashboard launcher:
	echo %LAUNCHER%
	exit /b 1
)

wscript.exe "%LAUNCHER%"

exit /b 0
