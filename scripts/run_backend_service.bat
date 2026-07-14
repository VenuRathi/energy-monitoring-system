@echo off
setlocal EnableExtensions

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"
set "PYTHON=%APP_ROOT%\.venv\Scripts\python.exe"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"

if not exist "%APP_ROOT%\logs" mkdir "%APP_ROOT%\logs"

if not exist "%PYTHON%" (
	echo Missing project Python at %PYTHON%
	exit /b 1
)

if not exist "%APP_ROOT%\.env" (
	echo Warning: %APP_ROOT%\.env not found. Backend will rely on machine environment variables or built-in defaults.
)

"%PYTHON%" -u main.py
