@echo off
rem
rem uninstall.bat: Uninstalls Ollama on Windows.
rem
rem Usage:
rem   .\bin\ollama\uninstall.bat [--yes]
rem

setlocal

set "AUTO_CONFIRM="
if /i "%1"=="--yes" set "AUTO_CONFIRM=true"

echo 🚀 Starting Ollama Uninstallation for Windows...

rem --- Check if Ollama is installed ---
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo Ollama is not installed. Nothing to do.
    exit /b 0
)

rem --- Confirm Uninstallation ---
if not defined AUTO_CONFIRM (
    choice /c YN /m "Are you sure you want to uninstall Ollama?"
    if errorlevel 2 (
        echo Uninstallation cancelled.
        exit /b 0
    )
)

rem --- Uninstall Ollama ---
echo 🛑 Uninstalling Ollama...
winget uninstall -e --id Ollama.Ollama --accept-source-agreements
if %errorlevel% neq 0 (
    echo ❌ Failed to uninstall Ollama using winget.
    echo You may need to uninstall it manually from 'Add or remove programs'.
    pause
    exit /b 1
)
echo ✅ Ollama uninstalled successfully.

rem --- Instruct on Model Removal ---
echo.
echo ⚠️ Note on Models:
echo The uninstallation does not remove the models you have downloaded.
echo To remove the models and free up disk space, delete the Ollama models directory.
echo By default, it is located at:
echo   C:\Users\%USERNAME%\.ollama\models
echo You can delete it by running:
echo   rmdir /s /q "%USERPROFILE%\.ollama\models"
echo.
echo 🎉 Uninstallation complete.

pause
exit /b 0 