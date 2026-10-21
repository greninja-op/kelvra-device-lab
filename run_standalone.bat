@echo off
REM =========================================================================
REM KELVRA Device Lab — Standalone Server Windows Launcher
REM Dedicated Port: 8098
REM =========================================================================

setlocal
cd /d "%~dp0"

echo [KELVRA Device Lab] Initializing standalone service on port 8098...
python run_standalone.py

if errorlevel 1 (
    echo [KELVRA Device Lab] Service exited with error code %errorlevel%.
    pause
)
endlocal
