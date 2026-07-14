@echo off
setlocal EnableExtensions

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"
set "PYTHON=%APP_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
	echo Missing project Python at %PYTHON%
	exit /b 1
)

"%PYTHON%" -u main.py
