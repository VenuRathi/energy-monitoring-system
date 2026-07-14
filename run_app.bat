@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "APP_ROOT=%CD%"
set "PYTHON=%APP_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
	echo Project virtual environment was not found at:
	echo %PYTHON%
	echo.
	echo Restore or create .venv before starting the service.
	pause
	exit /b 1
)

echo Starting energy monitoring service...
echo Using Python: %PYTHON%
"%PYTHON%" -u main.py

echo.
echo Service stopped.
pause
