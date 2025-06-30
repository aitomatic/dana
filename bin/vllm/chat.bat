@echo off
REM bin\vllm\chat.bat - Wrapper to run the Python chat client
REM Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

REM Find the project root directory
set "SCRIPT_DIR=%~dp0"
for %%i in ("%SCRIPT_DIR%..\..\") do set "PROJECT_ROOT=%%~fi"

REM Path to the python script
set "PYTHON_SCRIPT=%PROJECT_ROOT%bin\vllm\chat"

REM Check if python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: 'python' is not found in your PATH.
    echo Please ensure Python is installed and accessible.
    pause
    exit /b 1
)

REM Run the python script, passing all arguments
python "%PYTHON_SCRIPT%" %* 