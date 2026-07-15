@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "APP_ROOT=%CD%"
set "LAUNCHER=%APP_ROOT%\scripts\launch_app.ps1"

if not exist "%LAUNCHER%" (
	echo Missing launcher script:
	echo %LAUNCHER%
	pause
	exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%LAUNCHER%" -ProjectRoot "%APP_ROOT%"
if errorlevel 1 (
	echo.
	echo Launch failed. Review the message above, then run post-install checks if needed.
	pause
	exit /b 1
)

exit /b 0
