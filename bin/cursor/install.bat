@echo off
REM Install Dana Language Support for Cursor
REM Copyright (C) 2025 Aitomatic, Inc. Licensed under the MIT License.
REM This calls the VSCode installer with --cursor flag

echo Installing Dana Language Support for Cursor...

REM Get the directory of this script and find the VSCode install script
set "SCRIPT_DIR=%~dp0"
set "VSCODE_SCRIPT=%SCRIPT_DIR%..\vscode\install.bat"

REM Check if VSCode install script exists
if not exist "%VSCODE_SCRIPT%" (
    echo Error: VSCode install script not found at %VSCODE_SCRIPT%
    exit /b 1
)

REM Call the VSCode install script with --cursor flag
call "%VSCODE_SCRIPT%" --cursor
