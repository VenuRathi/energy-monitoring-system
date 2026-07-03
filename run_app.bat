@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "APP_ROOT=%CD%"
set "PYTHON=%APP_ROOT%\.venv\Scripts\python.exe"
set "PYVENV_CFG=%APP_ROOT%\.venv\pyvenv.cfg"
set "BASE_PYTHON="
set "SITE_PACKAGES=%APP_ROOT%\.venv\Lib\site-packages"

if exist "%PYVENV_CFG%" (
	for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"executable =" "%PYVENV_CFG%"`) do (
		set "BASE_PYTHON=%%B"
	)
)

if defined BASE_PYTHON (
	if "!BASE_PYTHON:~0,1!"==" " set "BASE_PYTHON=!BASE_PYTHON:~1!"
	if exist "!BASE_PYTHON!" (
		set "PYTHON=!BASE_PYTHON!"
	)
)

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
if exist "%SITE_PACKAGES%" (
	if defined PYTHONPATH (
		set "PYTHONPATH=%APP_ROOT%;%SITE_PACKAGES%;%PYTHONPATH%"
	) else (
		set "PYTHONPATH=%APP_ROOT%;%SITE_PACKAGES%"
	)
)
"%PYTHON%" -u main.py

echo.
echo Service stopped.
pause
