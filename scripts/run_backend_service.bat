@echo off
setlocal EnableExtensions

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"
set "PYTHON=%APP_ROOT%\.venv\Scripts\python.exe"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "RUNNER_LOG=%APP_ROOT%\logs\backend_runner.log"

if not exist "%APP_ROOT%\logs" mkdir "%APP_ROOT%\logs"

echo [%DATE% %TIME%] Runner invoked from %APP_ROOT%>> "%RUNNER_LOG%"

if not exist "%PYTHON%" (
	echo Missing project Python at %PYTHON%
	echo [%DATE% %TIME%] Missing Python runtime at %PYTHON%>> "%RUNNER_LOG%"
	exit /b 1
)

if not exist "%APP_ROOT%\.env" (
	echo Warning: %APP_ROOT%\.env not found. Backend will rely on machine environment variables or built-in defaults.
	echo [%DATE% %TIME%] Warning: .env not found, backend will use machine environment/defaults.>> "%RUNNER_LOG%"
)

"%PYTHON%" -u main.py
set "EXIT_CODE=%ERRORLEVEL%"
echo [%DATE% %TIME%] Backend process exited with code %EXIT_CODE%.>> "%RUNNER_LOG%"
exit /b %EXIT_CODE%
