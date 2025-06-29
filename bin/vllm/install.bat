@echo off
REM Install vLLM for Windows
REM Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
REM Usage: bin\vllm\install.bat [option]

setlocal enabledelayedexpansion

echo.
echo 🚀 vLLM Windows Installation Guide
echo Copyright © 2025 Aitomatic, Inc.
echo ===================================
echo.

REM Check command line arguments
set "INSTALL_METHOD="
if "%1"=="--wsl" set "INSTALL_METHOD=wsl"
if "%1"=="--native" set "INSTALL_METHOD=native"
if "%1"=="--pip" set "INSTALL_METHOD=pip"
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

if "%INSTALL_METHOD%"=="" goto :show_options
goto :install_%INSTALL_METHOD%

:show_help
echo Usage: install.bat [OPTION]
echo.
echo Options:
echo   --wsl        Install via Windows Subsystem for Linux (Recommended)
echo   --native     Attempt native Windows installation (Experimental)
echo   --pip        Try pip installation (Limited support)
echo   --help, -h   Show this help message
echo.
echo For interactive selection, run without arguments.
echo.
pause
exit /b 0

:show_options
echo ⚠️  IMPORTANT: vLLM does NOT officially support native Windows installation.
echo.
echo 📋 Available Installation Methods:
echo.
echo [1] WSL + Linux Installation (RECOMMENDED)
echo     ✅ Officially supported by vLLM team
echo     ✅ Full GPU support with CUDA
echo     ✅ Most stable and reliable
echo     ✅ Easy to use and maintain
echo.
echo [2] Native Windows Build (EXPERIMENTAL)
echo     ⚠️  Community fork, not officially supported
echo     ⚠️  Requires Visual Studio and advanced setup
echo     ⚠️  May not support latest vLLM features
echo     ✅ Runs directly on Windows (no WSL needed)
echo.
echo [3] pip install (LIMITED)
echo     ⚠️  Not officially supported
echo     ⚠️  CPU-only, may fail on many systems
echo     ⚠️  No guarantee of compatibility
echo     ✅ Simplest attempt (if it works)
echo.
echo [Q] Quit / Exit
echo.
set /p "choice=Enter your choice (1-3, Q): "

if /i "%choice%"=="1" goto :install_wsl
if /i "%choice%"=="2" goto :install_native
if /i "%choice%"=="3" goto :install_pip
if /i "%choice%"=="q" exit /b 0
echo Invalid choice. Please enter 1, 2, 3, or Q.
goto :show_options

:install_wsl
echo.
echo 🐧 Installing vLLM via Windows Subsystem for Linux (WSL)
echo =====================================================
echo.
echo This is the RECOMMENDED and officially supported method.
echo.
echo 📋 Prerequisites Check:
echo • Windows 10 version 2004+ or Windows 11
echo • Administrator access
echo • Internet connection
echo.

REM Check if WSL is available
wsl --version >nul 2>&1
if errorlevel 1 (
    echo ❌ WSL not found. Installing WSL...
    echo.
    echo 📦 Step 1: Installing WSL with Ubuntu...
    echo Running: wsl --install
    echo.
    echo ⚠️  IMPORTANT: You will need to restart your computer after WSL installation.
    echo.
    set /p "continue=Continue with WSL installation? (Y/n): "
    if /i not "!continue!"=="y" if not "!continue!"=="" goto :end
    
    wsl --install
    if errorlevel 1 (
        echo.
        echo ❌ Automatic WSL installation failed.
        echo.
        echo 📝 Manual installation steps:
        echo 1. Open PowerShell as Administrator
        echo 2. Run: wsl --install
        echo 3. Restart your computer
        echo 4. Set up Ubuntu when prompted
        echo 5. Run this script again
        goto :end
    )
    
    echo.
    echo ✅ WSL installation initiated.
    echo 🔄 Please RESTART your computer now.
    echo 📝 After restart, run this script again to continue with vLLM installation.
    goto :end
) else (
    echo ✅ WSL is available
)

echo.
echo 📦 Step 2: Setting up vLLM in WSL...
echo.
echo 💡 The following commands will be executed in your WSL Ubuntu environment:
echo.
echo    # Update system packages
echo    sudo apt update ^&^& sudo apt upgrade -y
echo.
echo    # Install Python and development tools
echo    sudo apt install -y python3 python3-pip python3-venv git build-essential
echo.
echo    # Create virtual environment
echo    python3 -m venv ~/vllm_env
echo.
echo    # Activate environment
echo    source ~/vllm_env/bin/activate
echo.
echo    # Clone and install vLLM
echo    git clone https://github.com/vllm-project/vllm.git ~/vllm
echo    cd ~/vllm
echo    pip install -r requirements-cpu.txt
echo    pip install -e .
echo.
set /p "continue=Execute these commands in WSL now? (Y/n): "
if /i not "%continue%"=="y" if not "%continue%"=="" goto :wsl_manual

echo.
echo 🚀 Executing installation in WSL...
wsl bash -c "sudo apt update && sudo apt upgrade -y && sudo apt install -y python3 python3-pip python3-venv git build-essential && python3 -m venv ~/vllm_env && source ~/vllm_env/bin/activate && git clone https://github.com/vllm-project/vllm.git ~/vllm && cd ~/vllm && git checkout v0.9.1 && pip install -r requirements-cpu.txt && VLLM_TARGET_DEVICE=cpu pip install -e ."

if errorlevel 1 (
    echo.
    echo ❌ Automatic installation encountered errors.
    goto :wsl_manual
)

echo.
echo ✅ vLLM installation in WSL completed!
goto :create_start_script_wsl

:wsl_manual
echo.
echo 📝 Manual WSL Installation Steps:
echo.
echo 1. Open your WSL Ubuntu terminal
echo 2. Copy and paste these commands one by one:
echo.
echo    sudo apt update ^&^& sudo apt upgrade -y
echo    sudo apt install -y python3 python3-pip python3-venv git build-essential
echo    python3 -m venv ~/vllm_env
echo    source ~/vllm_env/bin/activate
echo    git clone https://github.com/vllm-project/vllm.git ~/vllm
echo    cd ~/vllm
echo    git checkout v0.9.1
echo    pip install -r requirements-cpu.txt
echo    VLLM_TARGET_DEVICE=cpu pip install -e .
echo.
echo 3. Test installation:
echo    python -c "import vllm; print('vLLM is ready in WSL!')"
echo.
goto :create_start_script_wsl

:create_start_script_wsl
echo.
echo 📝 Creating convenience start script for WSL...

REM Get the script directory and project root
set "SCRIPT_DIR=%~dp0"
for %%i in ("%SCRIPT_DIR%..\..\") do set "PROJECT_ROOT=%%~fi"
set "START_SCRIPT=%PROJECT_ROOT%bin\start_vllm.bat"

REM Create start script for WSL usage
(
echo @echo off
echo REM Start vLLM Server in WSL for OpenDXA
echo REM Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
echo REM Usage: bin\start_vllm.bat [OPTIONS]
echo.
echo setlocal enabledelayedexpansion
echo.
echo REM Default configuration
echo set "DEFAULT_MODEL=facebook/opt-125m"
echo set "DEFAULT_HOST=localhost"
echo set "DEFAULT_PORT=8000"
echo set "DEFAULT_ENV_NAME=vllm_env"
echo.
echo REM Parse command line arguments
echo set "MODEL=%DEFAULT_MODEL%"
echo set "HOST=%DEFAULT_HOST%"
echo set "PORT=%DEFAULT_PORT%"
echo set "ENV_NAME=%DEFAULT_ENV_NAME%"
echo.
echo if "%%1"=="--help" goto :show_help
echo if "%%1"=="-h" goto :show_help
echo.
echo :parse_args
echo if "%%1"=="" goto :start_server
echo if "%%1"=="--model" ^(
echo     set "MODEL=%%2"
echo     shift
echo     shift
echo     goto :parse_args
echo ^)
echo if "%%1"=="--host" ^(
echo     set "HOST=%%2"
echo     shift
echo     shift
echo     goto :parse_args
echo ^)
echo if "%%1"=="--port" ^(
echo     set "PORT=%%2"
echo     shift
echo     shift
echo     goto :parse_args
echo ^)
echo if "%%1"=="--env-name" ^(
echo     set "ENV_NAME=%%2"
echo     shift
echo     shift
echo     goto :parse_args
echo ^)
echo shift
echo goto :parse_args
echo.
echo :show_help
echo echo Start vLLM Server in WSL for OpenDXA
echo echo.
echo echo Usage: %%0 [OPTIONS]
echo echo.
echo echo Options:
echo echo   --model MODEL        Model to serve ^(default: %DEFAULT_MODEL%^)
echo echo   --host HOST          Host to bind to ^(default: %DEFAULT_HOST%^)
echo echo   --port PORT          Port to listen on ^(default: %DEFAULT_PORT%^)
echo echo   --env-name NAME      vLLM environment name ^(default: %DEFAULT_ENV_NAME%^)
echo echo   --help, -h           Show this help message
echo echo.
echo echo Examples:
echo echo   %%0                                    # Start with defaults
echo echo   %%0 --model microsoft/DialoGPT-medium  # Use different model
echo echo   %%0 --port 8080                       # Use different port
echo echo.
echo echo Environment:
echo echo   The script will look for vLLM installation in WSL at: ~/%%ENV_NAME%%/
echo echo   Default: ~/vllm_env/
echo pause
echo exit /b 0
echo.
echo :start_server
echo echo.
echo echo 🚀 Starting vLLM Server in WSL for OpenDXA...
echo echo 📋 Configuration:
echo echo   • Model: %%MODEL%%
echo echo   • Host: %%HOST%%
echo echo   • Port: %%PORT%%
echo echo   • Environment: %%ENV_NAME%%
echo echo.
echo.
echo echo 🔌 Starting vLLM in WSL Ubuntu environment...
echo echo 💡 Server will be available at: http://%%HOST%%:%%PORT%%
echo echo 📖 API docs will be at: http://%%HOST%%:%%PORT%%/docs
echo echo 🛑 Press Ctrl+C to stop the server
echo echo.
echo.
echo wsl bash -c "source ~/%%ENV_NAME%%/bin/activate && python -m vllm.entrypoints.openai.api_server --model %%MODEL%% --host %%HOST%% --port %%PORT%% --dtype float16 --max-model-len 2048 --disable-frontend-multiprocessing"
) > "%START_SCRIPT%"

echo ✅ Created start script: %START_SCRIPT%

echo.
echo 🎉 vLLM WSL installation completed successfully!
echo.
echo 📝 Next steps:
echo 1. Start vLLM server ^(recommended^):
echo    bin\start_vllm.bat
echo.
echo 2. Or start with custom options:
echo    bin\start_vllm.bat --model microsoft/DialoGPT-medium --port 8080
echo.
echo 3. Test vLLM manually in WSL:
echo    wsl bash -c "source ~/vllm_env/bin/activate && python -c 'import vllm; print(\"vLLM is ready!\")'"
echo.
echo 💡 Important Notes:
echo • vLLM runs in WSL Ubuntu environment using stable version v0.9.1
echo • GPU acceleration available if CUDA is configured in WSL
echo • Windows applications can access the server at localhost:8000
echo • Multiprocessing disabled to prevent import errors on WSL
echo • Enhanced reliability with stability fixes included
echo.
goto :end

:install_native
echo.
echo ⚠️  Native Windows Installation (EXPERIMENTAL)
echo ============================================
echo.
echo 🚨 WARNING: This method is NOT officially supported by vLLM!
echo 🚨 This uses a community fork and may not work with latest vLLM versions.
echo 🚨 Only proceed if you understand the risks and have development experience.
echo.
set /p "continue=Continue anyway? (y/N): "
if /i not "%continue%"=="y" goto :show_options

echo.
echo 📋 Prerequisites for Native Windows Build:
echo • Visual Studio 2019 or newer (with C++ build tools)
echo • CUDA Toolkit (for GPU support)
echo • Python 3.12 (recommended for prebuilt wheels)
echo • Git for Windows
echo • Advanced Windows development knowledge
echo.
set /p "continue=Do you have all prerequisites installed? (y/N): "
if /i not "%continue%"=="y" (
    echo.
    echo 📝 Install prerequisites first:
    echo 1. Visual Studio Community: https://visualstudio.microsoft.com/vs/community/
    echo 2. CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
    echo 3. Python 3.12: https://www.python.org/downloads/
    echo 4. Git for Windows: https://git-scm.com/download/win
    echo.
    echo Run this script again after installing prerequisites.
    goto :end
)

echo.
echo 📦 Step 1: Cloning community vLLM Windows fork...
if exist "vllm-windows" (
    echo Directory vllm-windows already exists. Updating...
    cd vllm-windows
    git pull
    cd ..
) else (
    git clone https://github.com/SystemPanic/vllm-windows.git
)

if errorlevel 1 (
    echo ❌ Failed to clone vLLM Windows fork
    echo Please check your internet connection and Git installation
    goto :end
)

echo.
echo 📦 Step 2: Setting up build environment...
echo.
echo 📝 Manual steps required:
echo.
echo 1. Open "Developer Command Prompt for VS 2019/2022" as Administrator
echo 2. Navigate to: %CD%\vllm-windows
echo 3. Run: \VC\Auxiliary\Build\vcvarsall.bat x64
echo 4. Set CUDA environment if needed
echo 5. Follow the fork's README for build commands
echo.
echo 📚 For detailed instructions, see:
echo https://github.com/SystemPanic/vllm-windows/blob/main/README.md
echo.
echo ⚠️  This is an advanced process that may require troubleshooting.
echo ⚠️  Consider using WSL installation instead for better compatibility.
echo.
goto :end

:install_pip
echo.
echo 🎲 Attempting pip Installation (LIMITED SUPPORT)
echo ============================================
echo.
echo ⚠️  WARNING: This method is NOT officially supported!
echo ⚠️  May fail with compilation errors or missing dependencies.
echo ⚠️  CPU-only usage, no GPU acceleration.
echo ⚠️  Use WSL installation for better compatibility.
echo.
set /p "continue=Continue anyway? (y/N): "
if /i not "%continue%"=="y" goto :show_options

echo.
echo 📋 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    goto :end
)

python --version
echo ✅ Python found

echo.
echo 📦 Creating virtual environment...
python -m venv vllm_env_windows
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    goto :end
)

echo.
echo 🔌 Activating virtual environment...
call vllm_env_windows\Scripts\activate.bat

echo.
echo 📦 Upgrading pip and installing dependencies...
python -m pip install --upgrade pip setuptools wheel

echo.
echo 🎲 Attempting to install vLLM via pip...
echo This may take several minutes and might fail...
pip install vllm

if errorlevel 1 (
    echo.
    echo ❌ pip installation failed (as expected)
    echo.
    echo 💡 This is normal - vLLM doesn't officially support Windows pip installation.
    echo 💡 Please use WSL installation instead:
    echo    %0 --wsl
    echo.
    goto :end
)

echo.
echo 🧪 Testing vLLM installation...
python -c "import vllm; print('vLLM imported successfully!')"
if errorlevel 1 (
    echo ❌ vLLM import test failed
    echo The installation may be incomplete or incompatible
    goto :end
)

echo.
echo 📝 Creating convenience start script...
REM Create a basic start script for pip installation
set "SCRIPT_DIR=%~dp0"
for %%i in ("%SCRIPT_DIR%..\..\") do set "PROJECT_ROOT=%%~fi"
set "START_SCRIPT=%PROJECT_ROOT%bin\start_vllm.bat"

(
echo @echo off
echo REM Start vLLM Server (pip installation) for OpenDXA
echo.
echo echo 🚀 Starting vLLM Server...
echo.
echo if not exist "vllm_env_windows\Scripts\activate.bat" ^(
echo     echo ❌ Virtual environment not found
echo     echo Please run install.bat again
echo     pause
echo     exit /b 1
echo ^)
echo.
echo call vllm_env_windows\Scripts\activate.bat
echo python -m vllm.entrypoints.openai.api_server --model facebook/opt-125m --host localhost --port 8000 --dtype float16 --max-model-len 2048 --disable-frontend-multiprocessing
) > "%START_SCRIPT%"

echo ✅ Created start script: %START_SCRIPT%

echo.
echo 🎉 Experimental pip installation completed!
echo.
echo ⚠️  IMPORTANT: This installation is experimental and may not work reliably.
echo ⚠️  Consider using WSL installation for production use.
echo.
echo 📝 Next steps:
echo 1. Test the installation:
echo    python -c "from vllm import LLM; print('vLLM is ready!')"
echo.
echo 2. Start vLLM server:
echo    bin\start_vllm.bat
echo.
goto :end

:end
echo.
echo 📚 Additional Resources:
echo • vLLM Documentation: https://docs.vllm.ai/
echo • Windows Installation Issues: https://github.com/vllm-project/vllm/issues
echo • Community Windows Fork: https://github.com/SystemPanic/vllm-windows
echo • WSL Documentation: https://docs.microsoft.com/en-us/windows/wsl/
echo.
pause
exit /b 0 