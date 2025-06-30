@echo off
setlocal enabledelayedexpansion

rem
rem start.bat: Starts the Ollama service, pulls a model, and configures environment variables.
rem
rem Usage:
rem   .\bin\ollama\start.bat [--model <model_name>]
rem

rem --- Configuration ---
set "DEFAULT_MODEL=phi3:mini"
set "OLLAMA_HOST=localhost"
set "OLLAMA_PORT=11434"
set "MODEL_SELECTED="

rem --- Helper Functions ---
:check_ollama_installed
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: 'ollama' command not found.
    echo Please install Ollama first by running: .\bin\ollama\install.bat
    goto :eof
)
goto :eof

:ensure_service_running
echo 🔄 Checking Ollama service status...
ollama ps >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ Ollama service is already running.
) else (
    echo 🟡 Ollama service is not running.
    echo On Windows, Ollama should start automatically. Please check the system tray icon.
    echo If the issue persists, try reinstalling.
    pause
    goto :eof
)
goto :eof

:show_model_menu
echo.
echo 🤖 Select a model to run:
echo    1) Phi-3 Mini (3.8B) - Microsoft's efficient model (default)
echo    2) Llama 3 (8B) - Meta's powerful model
echo    3) Qwen (4B) - Alibaba's compact powerhouse
echo    4) Gemma (2B) - Google's lightweight model
echo    5) Mistral (7B) - Mistral AI's popular model
echo    ---
echo    6) Enter custom model name
echo    0) Exit
goto :eof

:pull_model
set "model_name=%~1"
echo.
echo 🔍 Checking for model '%model_name%'...
ollama list | findstr /B /I /C:"%model_name%" >nul
if %errorlevel% equ 0 (
    echo ✅ Model '%model_name%' is already available locally.
) else (
    echo 🟡 Model '%model_name%' not found locally. Pulling from Ollama Hub...
    ollama pull %model_name%
    if %errorlevel% neq 0 (
        echo ❌ Failed to pull model '%model_name%'.
        echo Please check the model name and your internet connection.
        pause
        goto :eof
    )
    echo ✅ Successfully pulled model '%model_name%'.
)
set "MODEL_SELECTED=%model_name%"
goto :eof

rem --- Main Script ---

rem Parse arguments
:arg_loop
if "%1"=="" goto :args_done
if /i "%1"=="--model" (
    set "MODEL_SELECTED=%2"
    shift
)
shift
goto arg_loop
:args_done

call :check_ollama_installed
call :ensure_service_running

if not defined MODEL_SELECTED (
    :menu_loop
    call :show_model_menu
    set /p "choice=Enter your choice (1-6): "
    if "%choice%"=="1" (call :pull_model "phi3:mini") & goto :menu_done
    if "%choice%"=="2" (call :pull_model "llama3") & goto :menu_done
    if "%choice%"=="3" (call :pull_model "qwen:4b") & goto :menu_done
    if "%choice%"=="4" (call :pull_model "gemma:2b") & goto :menu_done
    if "%choice%"=="5" (call :pull_model "mistral") & goto :menu_done
    if "%choice%"=="6" (
        set /p "custom_model=Enter custom model name (e.g., codellama:7b): "
        if defined custom_model (
            call :pull_model "!custom_model!"
            goto :menu_done
        ) else (
            echo Invalid name. Please try again.
            goto menu_loop
        )
    )
    if "%choice%"=="0" (echo 👋 Exiting.) & goto :eof
    echo Invalid choice. Please try again.
    goto menu_loop
    :menu_done
) else (
    call :pull_model "%MODEL_SELECTED%"
)

rem --- Configure Environment for OpenDXA ---
set "LOCAL_LLM_URL=http://%OLLAMA_HOST%:%OLLAMA_PORT%/v1"
set "LOCAL_LLM_NAME=%MODEL_SELECTED%"

echo.
echo ✅ Configuration complete!
echo Ollama is running with model: %MODEL_SELECTED%
echo.
echo Environment variables have been set for this command prompt session:
echo   - LOCAL_LLM_URL=%LOCAL_LLM_URL%
echo   - LOCAL_LLM_NAME=%LOCAL_LLM_NAME%
echo.
echo These variables allow OpenDXA to connect to the local Ollama server.
echo To start an interactive chat session, run: .\bin\ollama\chat.bat --model %MODEL_SELECTED%
echo.
echo You can now run your OpenDXA applications in this command prompt.

rem Keep the window open and environment variables active by starting a new cmd instance
cmd /k 