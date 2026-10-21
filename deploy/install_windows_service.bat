@echo off
rem ============================================================================
rem KELVRA Device Lab — Windows Service Installation Script (via NSSM)
rem Service Port: :8098 (Loopback / Host interface)
rem Zero Emoji Prohibition Enforced
rem ============================================================================

set SERVICE_NAME=KelvraDeviceLab
set DISPLAY_NAME=KELVRA Device Lab Service
set DESCRIPTION=Autonomous mobile device teleoperation, streaming, and testing engine.
set APP_DIR=%~dp0..
set PYTHON_EXE=python

rem Check administrative privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges.
    echo Please right-click and select "Run as administrator".
    pause
    exit /b 1
)

echo ========================================================
echo  KELVRA Device Lab - Windows Service Setup
echo ========================================================
echo Target Directory: %APP_DIR%
echo Service Name:     %SERVICE_NAME%
echo Service Port:     8098
echo.

rem Check if NSSM is available
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo [NOTICE] NSSM was not found in PATH.
    echo To install as an automatic background service:
    echo   1. Download NSSM from https://nssm.cc/download
    echo   2. Place nssm.exe in C:\Windows\System32 or in this directory.
    echo.
    echo Alternatively, run in background via standard standalone launcher:
    echo   run_standalone.bat
    echo.
    pause
    exit /b 1
)

rem Check if service already exists
nssm status %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo [INFO] Existing service %SERVICE_NAME% found. Stopping and reconfiguring...
    nssm stop %SERVICE_NAME%
    nssm remove %SERVICE_NAME% confirm
)

echo [INFO] Registering %SERVICE_NAME% with NSSM...
nssm install %SERVICE_NAME% "%PYTHON_EXE%" "-m src.server"
nssm set %SERVICE_NAME% AppDirectory "%APP_DIR%"
nssm set %SERVICE_NAME% DisplayName "%DISPLAY_NAME%"
nssm set %SERVICE_NAME% Description "%DESCRIPTION%"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

rem Configure environment variables
nssm set %SERVICE_NAME% AppEnvironmentExtra KELVRA_DEVICE_LAB_HOST=127.0.0.1 KELVRA_DEVICE_LAB_PORT=8098 LOG_LEVEL=info

rem Configure output logs
if not exist "%APP_DIR%\logs" mkdir "%APP_DIR%\logs"
nssm set %SERVICE_NAME% AppStdout "%APP_DIR%\logs\service_stdout.log"
nssm set %SERVICE_NAME% AppStderr "%APP_DIR%\logs\service_stderr.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateOnline 1
nssm set %SERVICE_NAME% AppRotateSeconds 86400
nssm set %SERVICE_NAME% AppRotateBytes 10485760

rem Configure failure restart (restart after 5 seconds)
nssm set %SERVICE_NAME% AppRestartDelay 5000

echo [INFO] Starting %SERVICE_NAME%...
nssm start %SERVICE_NAME%

echo.
echo ========================================================
echo  Service installation complete.
echo  Port: 8098
echo  Logs: %APP_DIR%\logs\service_stdout.log
echo ========================================================
pause
