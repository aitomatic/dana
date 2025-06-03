@echo off
REM Install Dana Language Support for VS Code/Cursor
REM Copyright (C) 2025 Aitomatic, Inc. Licensed under the MIT License.
REM Usage: bin\install-vscode-extension.bat [--cursor]

setlocal enabledelayedexpansion

REM Default to VS Code
set "EDITOR=code"
set "EDITOR_NAME=VS Code"

REM Check for --cursor flag
if "%1"=="--cursor" (
    set "EDITOR=cursor"
    set "EDITOR_NAME=Cursor"
)

echo Installing Dana Language Support for %EDITOR_NAME%...

REM Check if editor is installed
where %EDITOR% >nul 2>&1
if errorlevel 1 (
    echo Error: %EDITOR_NAME% is not installed or not in PATH
    echo Please install %EDITOR_NAME% first:
    if "%EDITOR%"=="code" (
        echo    - Download from: https://code.visualstudio.com/
        echo    - Or install via winget: winget install Microsoft.VisualStudioCode
    ) else (
        echo    - Download from: https://cursor.sh/
    )
    exit /b 1
)

REM Get the project root directory
set "PROJECT_ROOT=%~dp0.."
set "EXTENSION_DIR=%PROJECT_ROOT%\opendxa\dana\integration\vscode"

echo Extension directory: %EXTENSION_DIR%

REM Check if extension directory exists
if not exist "%EXTENSION_DIR%" (
    echo Error: Extension directory not found at %EXTENSION_DIR%
    exit /b 1
)

REM Change to extension directory
cd /d "%EXTENSION_DIR%"

REM Check if Node.js is installed
where npm >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js/npm is not installed
    echo Please install Node.js first:
    echo    - Download from: https://nodejs.org/
    echo    - Or install via winget: winget install OpenJS.NodeJS
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
call npm install
if errorlevel 1 (
    echo Error: Failed to install dependencies
    exit /b 1
)

REM Check if vsce is installed globally
where vsce >nul 2>&1
if errorlevel 1 (
    echo Installing vsce VS Code Extension Manager...
    call npm install -g vsce
    if errorlevel 1 (
        echo Error: Failed to install vsce
        exit /b 1
    )
)

REM Compile TypeScript
echo Compiling TypeScript...
call npm run compile
if errorlevel 1 (
    echo Error: Failed to compile TypeScript
    exit /b 1
)

REM Package extension
echo Packaging extension...
call vsce package --allow-missing-repository
if errorlevel 1 (
    echo Error: Failed to package extension
    exit /b 1
)

REM Find the generated .vsix file
for %%f in (*.vsix) do set "VSIX_FILE=%%f"

if not defined VSIX_FILE (
    echo Error: No .vsix file found after packaging
    exit /b 1
)

echo Extension packaged: %VSIX_FILE%

REM Install the extension
echo Installing extension in %EDITOR_NAME%...
%EDITOR% --install-extension "%VSIX_FILE%"
if errorlevel 1 (
    echo Error: Failed to install extension
    exit /b 1
)

echo Dana Language Support successfully installed in %EDITOR_NAME%!
echo.
echo Next steps:
echo 1. Open %EDITOR_NAME%
echo 2. Create or open a .na file
echo 3. Press F5 to run Dana code
echo.
echo Tip: Make sure dana command is in your PATH

REM Check if local dana command is available
set "DANA_CLI=%PROJECT_ROOT%\bin\dana"
if exist "%DANA_CLI%" (
    echo Dana CLI is available at %DANA_CLI%
) else (
    echo Warning: Dana CLI not found at %DANA_CLI%
    echo The extension will look for dana in PATH when running files
)

pause 