@echo off
rem Uninstall vLLM for Windows
rem Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
rem Usage: bin\vllm\uninstall.bat [--env-name ENV_NAME] [--yes] [--wsl|--native|--pip]

setlocal enabledelayedexpansion

rem Default values
set ENV_NAME=vllm_env
set AUTO_CONFIRM=false
set INSTALL_TYPE=auto

rem Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="--env-name" (
    set ENV_NAME=%~2
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--yes" (
    set AUTO_CONFIRM=true
    shift
    goto parse_args
)
if /i "%~1"=="-y" (
    set AUTO_CONFIRM=true
    shift
    goto parse_args
)
if /i "%~1"=="--wsl" (
    set INSTALL_TYPE=wsl
    shift
    goto parse_args
)
if /i "%~1"=="--native" (
    set INSTALL_TYPE=native
    shift
    goto parse_args
)
if /i "%~1"=="--pip" (
    set INSTALL_TYPE=pip
    shift
    goto parse_args
)
if /i "%~1"=="--help" goto show_help
if /i "%~1"=="-h" goto show_help
echo ERROR: Unknown option: %~1
echo Use --help for usage information
exit /b 1

:end_parse

echo.
echo 🗑️  vLLM Uninstaller for Windows
echo.

rem Auto-detect installation type if not specified
if /i "%INSTALL_TYPE%"=="auto" (
    echo 🔍 Auto-detecting vLLM installation type...
    
    rem Check for WSL installation
    wsl --status >nul 2>&1
    if !errorlevel! equ 0 (
        wsl test -d ~/!ENV_NAME! >nul 2>&1
        if !errorlevel! equ 0 (
            set INSTALL_TYPE=wsl
            echo    📁 Found WSL installation
        )
    )
    
    rem Check for native installation
    if exist "%USERPROFILE%\!ENV_NAME!" (
        if /i "!INSTALL_TYPE!"=="auto" (
            set INSTALL_TYPE=native
            echo    📁 Found native installation
        )
    )
    
    rem Check for pip installation
    python -c "import vllm" >nul 2>&1
    if !errorlevel! equ 0 (
        if /i "!INSTALL_TYPE!"=="auto" (
            set INSTALL_TYPE=pip
            echo    📦 Found pip installation
        )
    )
    
    if /i "!INSTALL_TYPE!"=="auto" (
        echo ✅ No vLLM installation found to remove
        echo.
        echo Checked for:
        echo   • WSL installation: ~/!ENV_NAME!/
        echo   • Native installation: %USERPROFILE%\!ENV_NAME!\
        echo   • Pip installation: Python packages
        echo.
        echo 💡 If vLLM was installed with a different method or name, specify:
        echo    %~nx0 --wsl --env-name YOUR_ENV_NAME
        echo    %~nx0 --native --env-name YOUR_ENV_NAME
        echo    %~nx0 --pip
        pause
        exit /b 0
    )
)

echo 📋 Installation type: !INSTALL_TYPE!
echo.

rem Handle different installation types
if /i "%INSTALL_TYPE%"=="wsl" goto uninstall_wsl
if /i "%INSTALL_TYPE%"=="native" goto uninstall_native
if /i "%INSTALL_TYPE%"=="pip" goto uninstall_pip

:uninstall_wsl
echo 🐧 Uninstalling WSL vLLM installation...
echo.

rem Check WSL availability
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: WSL is not available
    echo    WSL installation detected but WSL is not running
    echo    Please start WSL and try again
    pause
    exit /b 1
)

rem Check what exists in WSL
set items_found=0

wsl test -d ~/!ENV_NAME! >nul 2>&1
if !errorlevel! equ 0 (
    set /a items_found+=1
    echo 📁 Found WSL virtual environment: ~/!ENV_NAME!/
    for /f "delims=" %%i in ('wsl du -sh ~/!ENV_NAME! 2^>^/dev^/null ^| cut -f1 2^>nul') do set venv_size=%%i
    if defined venv_size echo    Size: !venv_size!
)

wsl test -d ~/vllm >nul 2>&1
if !errorlevel! equ 0 (
    set /a items_found+=1
    echo 📁 Found WSL vLLM source: ~/vllm/
    for /f "delims=" %%i in ('wsl du -sh ~/vllm 2^>^/dev^/null ^| cut -f1 2^>nul') do set vllm_size=%%i
    if defined vllm_size echo    Size: !vllm_size!
)

if exist "bin\start_vllm.bat" (
    set /a items_found+=1
    echo 📄 Found start script: bin\start_vllm.bat
)

if !items_found! equ 0 (
    echo ✅ No WSL vLLM installation found to remove
    pause
    exit /b 0
)

echo.
if /i "%AUTO_CONFIRM%"=="false" (
    echo ⚠️  WARNING: This will permanently delete the above items in WSL!
    set /p confirm="Are you sure you want to continue? (y/N): "
    if /i not "!confirm!"=="y" (
        echo ℹ️  Uninstall cancelled
        pause
        exit /b 0
    )
    echo.
)

echo 🗑️  Removing WSL vLLM installation...

rem Remove WSL virtual environment
wsl test -d ~/!ENV_NAME! >nul 2>&1
if !errorlevel! equ 0 (
    echo 🔸 Removing WSL virtual environment...
    wsl rm -rf ~/!ENV_NAME!
    if !errorlevel! equ 0 (
        echo   ✅ WSL virtual environment removed
    ) else (
        echo   ❌ Failed to remove WSL virtual environment
        pause
        exit /b 1
    )
)

rem Remove WSL vLLM source
wsl test -d ~/vllm >nul 2>&1
if !errorlevel! equ 0 (
    echo 🔸 Removing WSL vLLM source...
    wsl rm -rf ~/vllm
    if !errorlevel! equ 0 (
        echo   ✅ WSL vLLM source removed
    ) else (
        echo   ❌ Failed to remove WSL vLLM source
        pause
        exit /b 1
    )
)

rem Remove start script
if exist "bin\start_vllm.bat" (
    echo 🔸 Removing start script...
    del "bin\start_vllm.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Start script removed
    ) else (
        echo   ❌ Failed to remove start script
        pause
        exit /b 1
    )
)

goto uninstall_complete

:uninstall_native
echo 🪟 Uninstalling native Windows vLLM installation...
echo.

rem Check what exists
set items_found=0

if exist "%USERPROFILE%\!ENV_NAME!" (
    set /a items_found+=1
    echo 📁 Found virtual environment: %USERPROFILE%\!ENV_NAME!\
)

if exist "%USERPROFILE%\vllm" (
    set /a items_found+=1
    echo 📁 Found vLLM source: %USERPROFILE%\vllm\
)

if exist "bin\start_vllm.bat" (
    set /a items_found+=1
    echo 📄 Found start script: bin\start_vllm.bat
)

if !items_found! equ 0 (
    echo ✅ No native vLLM installation found to remove
    pause
    exit /b 0
)

echo.
if /i "%AUTO_CONFIRM%"=="false" (
    echo ⚠️  WARNING: This will permanently delete the above items!
    set /p confirm="Are you sure you want to continue? (y/N): "
    if /i not "!confirm!"=="y" (
        echo ℹ️  Uninstall cancelled
        pause
        exit /b 0
    )
    echo.
)

echo 🗑️  Removing native vLLM installation...

rem Remove virtual environment
if exist "%USERPROFILE%\!ENV_NAME!" (
    echo 🔸 Removing virtual environment...
    rmdir /s /q "%USERPROFILE%\!ENV_NAME!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Virtual environment removed
    ) else (
        echo   ❌ Failed to remove virtual environment
        pause
        exit /b 1
    )
)

rem Remove vLLM source
if exist "%USERPROFILE%\vllm" (
    echo 🔸 Removing vLLM source...
    rmdir /s /q "%USERPROFILE%\vllm" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ vLLM source removed
    ) else (
        echo   ❌ Failed to remove vLLM source
        pause
        exit /b 1
    )
)

rem Remove start script
if exist "bin\start_vllm.bat" (
    echo 🔸 Removing start script...
    del "bin\start_vllm.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Start script removed
    ) else (
        echo   ❌ Failed to remove start script
        pause
        exit /b 1
    )
)

goto uninstall_complete

:uninstall_pip
echo 📦 Uninstalling pip vLLM installation...
echo.

rem Check if vllm is installed
python -c "import vllm" >nul 2>&1
if %errorlevel% neq 0 (
    echo ✅ No pip vLLM installation found to remove
    pause
    exit /b 0
)

echo 📦 Found pip vLLM installation
for /f "delims=" %%i in ('python -c "import vllm; print(vllm.__version__)" 2^>nul') do set vllm_version=%%i
if defined vllm_version echo    Version: !vllm_version!

if exist "bin\start_vllm.bat" (
    echo 📄 Found start script: bin\start_vllm.bat
)

echo.
if /i "%AUTO_CONFIRM%"=="false" (
    echo ⚠️  WARNING: This will uninstall vLLM from your Python environment!
    set /p confirm="Are you sure you want to continue? (y/N): "
    if /i not "!confirm!"=="y" (
        echo ℹ️  Uninstall cancelled
        pause
        exit /b 0
    )
    echo.
)

echo 🗑️  Removing pip vLLM installation...

echo 🔸 Uninstalling vLLM package...
pip uninstall vllm -y >nul 2>&1
if !errorlevel! equ 0 (
    echo   ✅ vLLM package uninstalled
) else (
    echo   ❌ Failed to uninstall vLLM package
    pause
    exit /b 1
)

rem Remove start script
if exist "bin\start_vllm.bat" (
    echo 🔸 Removing start script...
    del "bin\start_vllm.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Start script removed
    ) else (
        echo   ❌ Failed to remove start script
        pause
        exit /b 1
    )
)

goto uninstall_complete

:uninstall_complete
echo.
echo 🎉 vLLM uninstallation completed successfully!
echo.
echo 💡 To reinstall vLLM:
if /i "%INSTALL_TYPE%"=="wsl" echo    bin\vllm\install.bat --wsl
if /i "%INSTALL_TYPE%"=="native" echo    bin\vllm\install.bat --native
if /i "%INSTALL_TYPE%"=="pip" echo    bin\vllm\install.bat --pip
if not "%ENV_NAME%"=="vllm_env" echo    Add --env-name !ENV_NAME! for custom environment name
echo.
echo ℹ️  No system packages were modified during uninstallation
pause
exit /b 0

:show_help
echo Uninstall vLLM for Windows
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --wsl              Remove WSL installation
echo   --native           Remove native Windows installation  
echo   --pip              Remove pip installation
echo   --env-name NAME    Environment name to remove (default: vllm_env)
echo   --yes, -y          Skip confirmation prompts
echo   --help, -h         Show this help message
echo.
echo Examples:
echo   %~nx0                              # Auto-detect and remove
echo   %~nx0 --wsl --yes                  # Remove WSL installation automatically
echo   %~nx0 --native --env-name my_env   # Remove custom native installation
echo   %~nx0 --pip                        # Remove pip installation
echo.
echo What will be removed:
echo   WSL: ~/ENV_NAME/, ~/vllm/, bin\start_vllm.bat
echo   Native: %%USERPROFILE%%\ENV_NAME\, %%USERPROFILE%%\vllm\, bin\start_vllm.bat
echo   Pip: vllm package, bin\start_vllm.bat
exit /b 0 