@echo off
REM Uninstall Dana Language Support from Cursor
REM Copyright (C) 2025 Aitomatic, Inc. Licensed under the MIT License.
REM This calls the VSCode uninstaller with --cursor flag

echo Uninstalling Dana Language Support from Cursor...

REM Get the directory of this script and find the VSCode uninstall script
set "SCRIPT_DIR=%~dp0"
set "VSCODE_SCRIPT=%SCRIPT_DIR%..\vscode\uninstall.sh"

REM Check if VSCode uninstall script exists
if not exist "%VSCODE_SCRIPT%" (
    echo Error: VSCode uninstall script not found at %VSCODE_SCRIPT%
    exit /b 1
)

REM Call the VSCode uninstall script with --cursor flag
call "%VSCODE_SCRIPT%" --cursor 