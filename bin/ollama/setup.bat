@echo off
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%setup_windows.ps1"

if not exist "%PS_SCRIPT%" (
    echo Could not locate %PS_SCRIPT%
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
exit /b %ERRORLEVEL%
