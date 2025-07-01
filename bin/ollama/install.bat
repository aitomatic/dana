@echo off
rem
rem install.bat: Installs Ollama on Windows using winget.
rem
rem Usage:
rem   .\bin\ollama\install.bat
rem
rem The script performs the following actions:
rem 1. Checks for winget.
rem 2. Installs Ollama using 'winget install Ollama.Ollama'.
rem 3. Verifies the installation.
rem
setlocal

echo 🚀 Starting Ollama Installation for Windows...

rem --- Check for winget ---
where winget >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: winget is not installed or not in PATH.
    echo Please install the "App Installer" from the Microsoft Store.
    echo You can find it here: ms-windows-store://pdp/?productid=9NBLGGH4NNS1
    pause
    exit /b 1
)

echo ✅ winget is available.

rem --- Install Ollama ---
echo 📦 Installing Ollama via winget...
ollama --version >nul 2>nul
if %errorlevel% equ 0 (
    echo Ollama is already installed.
) else (
    winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo ❌ Ollama installation failed.
        pause
        exit /b 1
    )
    echo ✅ Ollama installed successfully.
)

rem --- Verify Installation ---
echo 🔍 Verifying Ollama installation...
ollama --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Verification failed. 'ollama' command not found in PATH after installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('ollama --version') do set OLLAMA_VERSION=%%i
echo ✅ Verification successful. %OLLAMA_VERSION% is ready.

rem --- Post-installation instructions ---
echo.
echo 🎉 Ollama setup is complete!
echo Ollama will now run as a background service.
echo You can start using it with the following commands in a new terminal:
echo   - To start the server and run a model: ollama run phi3
echo   - To see a list of downloaded models: ollama list
echo   - To use the custom start script: .\bin\ollama\start.bat

pause
exit /b 0 