@echo off
REM Uninstall Dana Language Support from VS Code/Cursor
REM Copyright (C) 2025 Aitomatic, Inc. Licensed under the MIT License.
REM Usage: uninstall.bat [--cursor]

setlocal enabledelayedexpansion

REM Default to VS Code
set "EDITOR_CMD=code"
set "EDITOR_NAME=VS Code"

REM Check for --cursor flag
if "%1"=="--cursor" (
    set "EDITOR_CMD=cursor"
    set "EDITOR_NAME=Cursor"
)

echo Uninstalling Dana Language Support from %EDITOR_NAME%...

REM Check if editor is installed
where "%EDITOR_CMD%" >nul 2>&1
if errorlevel 1 (
    echo Error: %EDITOR_NAME% command '%EDITOR_CMD%' is not installed or not in PATH
    exit /b 1
)

REM Expected extension IDs (publisher.name)
REM Publisher in package.json: "Aitomatic, Inc." (likely sanitized to 'aitomatic' or similar by vsce/vscode)
REM Name in package.json: "dana-language"
set "EXTENSION_ID_1=aitomatic.dana-language"
set "EXTENSION_ID_2=aitomatic, inc..dana-language"

echo Attempting to remove extension '%EXTENSION_ID_1%' from %EDITOR_NAME%...

REM Attempt to uninstall first extension ID
"%EDITOR_CMD%" --uninstall-extension "%EXTENSION_ID_1%" >nul 2>&1
if not errorlevel 1 (
    echo Dana Language Support '%EXTENSION_ID_1%' successfully uninstalled from %EDITOR_NAME%!
    goto :success
)

REM If first ID failed, try second ID
echo Trying alternative extension ID '%EXTENSION_ID_2%'...
"%EDITOR_CMD%" --uninstall-extension "%EXTENSION_ID_2%" >nul 2>&1
if not errorlevel 1 (
    echo Dana Language Support '%EXTENSION_ID_2%' successfully uninstalled from %EDITOR_NAME%!
    goto :success
)

REM Both IDs failed
echo Warning: Failed to uninstall '%EXTENSION_ID_1%' or '%EXTENSION_ID_2%'.
echo This can happen if the extension was not installed with this exact ID, or was already removed.
echo.
echo To find the correct extension ID, please list your installed extensions:
echo    %EDITOR_CMD% --list-extensions ^| findstr /i dana
echo.
echo If you find it under a different ID (e.g., SomePublisher.dana-language), uninstall manually:
echo    %EDITOR_CMD% --uninstall-extension ACTUAL_PUBLISHER.dana-language
goto :end

:success
echo Note: You may need to restart %EDITOR_NAME% for changes to take effect

:end
endlocal
