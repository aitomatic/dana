@echo off
REM Start vLLM Server for OpenDXA (Windows)
REM Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
REM Usage: bin\start_vllm.bat [OPTIONS]

setlocal enabledelayedexpansion

REM Default configuration
set "DEFAULT_MODEL=facebook/opt-125m"
set "DEFAULT_HOST=localhost"
set "DEFAULT_PORT=8000"
set "DEFAULT_ENV_NAME=vllm_env"

REM Model selection variables
set "MODEL_SELECTED="
set "INTERACTIVE_MODE=true"

REM Check if model is specified in arguments
for %%i in (%*) do (
    if "%%i"=="--model" set "INTERACTIVE_MODE=false"
)

REM Initialize variables
set "MODEL=%DEFAULT_MODEL%"
set "HOST=%DEFAULT_HOST%"
set "PORT=%DEFAULT_PORT%"
set "ENV_NAME=%DEFAULT_ENV_NAME%"

if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

goto :parse_args

:show_help
echo Start vLLM Server for OpenDXA (Windows)
echo.
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   --model MODEL        Model to serve (default: interactive selection)
echo   --host HOST          Host to bind to (default: %DEFAULT_HOST%)
echo   --port PORT          Port to listen on (default: %DEFAULT_PORT%)
echo   --env-name NAME      vLLM environment name (default: %DEFAULT_ENV_NAME%)
echo   --help, -h           Show this help message
echo.
echo Interactive Mode:
echo   If no --model is specified, an interactive menu will appear
echo   with curated model recommendations for different use cases.
echo.
echo Examples:
echo   %0                                    # Interactive model selection
echo   %0 --model microsoft/Phi-4           # Direct model specification
echo   %0 --port 8080                       # Interactive + custom port
echo.
echo Environment:
echo   WSL: The script will use WSL vLLM installation
echo   Native: The script will use Windows vLLM installation
goto :eof

:show_model_menu
cls
echo.
echo 🤖 vLLM Model Selection for OpenDXA (Windows)
echo ════════════════════════════════════════════
echo.
echo Select a model category optimized for your hardware and use case:
echo.
echo 📱 Windows/CPU Optimized Models
echo    1) Phi-3.5-mini (3.8B) - Microsoft's efficient model
echo    2) Qwen2.5-3B - Alibaba's compact powerhouse
echo    3) Gemma-2-2B - Google's lightweight model
echo    4) Llama-3.2-3B - Meta's small but capable
echo.
echo 🚀 GPU High-Performance Models
echo    5) Qwen2.5-7B-Instruct - Excellent balance (14GB VRAM)
echo    6) Llama-3.1-8B-Instruct - Meta's solid choice (16GB VRAM)
echo    7) Phi-4 (15B) - Microsoft's latest (30GB VRAM)
echo    8) Mistral-7B-Instruct - Fast and efficient (14GB VRAM)
echo.
echo 💻 Coding Specialized Models
echo    9) microsoft/Phi-4 - Excellent at code generation
echo   10) bigcode/starcoder2-7b - Dedicated coding model
echo   11) deepseek-ai/deepseek-coder-6.7b-instruct - Code specialist
echo.
echo 🖼️  Vision/Multimodal Models
echo   12) meta-llama/Llama-4-Scout-17B-16E-Instruct - Latest multimodal
echo   13) microsoft/Phi-3.5-vision-instruct - Compact vision model
echo   14) Qwen/Qwen2-VL-7B-Instruct - Excellent vision understanding
echo.
echo 🎯 Popular Recommended Models
echo   15) Qwen/Qwen2.5-7B-Instruct - Best overall balance
echo   16) microsoft/Phi-4 - Latest and efficient
echo   17) meta-llama/Llama-3.1-8B-Instruct - Reliable choice
echo.
echo ⚙️  Custom Options
echo   18) Enter custom model name
echo   19) Use default (facebook/opt-125m - testing only)
echo.
echo ❌ Exit
echo    0) Exit without starting
echo.
goto :eof

:get_model_selection
:selection_loop
call :show_model_menu
set /p "choice=Please select a model (0-19): "

if "%choice%"=="1" set "MODEL_SELECTED=microsoft/Phi-3.5-mini-instruct" && goto :selection_done
if "%choice%"=="2" set "MODEL_SELECTED=Qwen/Qwen2.5-3B-Instruct" && goto :selection_done
if "%choice%"=="3" set "MODEL_SELECTED=google/gemma-2-2b-it" && goto :selection_done
if "%choice%"=="4" set "MODEL_SELECTED=meta-llama/Llama-3.2-3B-Instruct" && goto :selection_done
if "%choice%"=="5" set "MODEL_SELECTED=Qwen/Qwen2.5-7B-Instruct" && goto :selection_done
if "%choice%"=="6" set "MODEL_SELECTED=meta-llama/Llama-3.1-8B-Instruct" && goto :selection_done
if "%choice%"=="7" set "MODEL_SELECTED=microsoft/Phi-4" && goto :selection_done
if "%choice%"=="8" set "MODEL_SELECTED=mistralai/Mistral-7B-Instruct-v0.3" && goto :selection_done
if "%choice%"=="9" set "MODEL_SELECTED=microsoft/Phi-4" && goto :selection_done
if "%choice%"=="10" set "MODEL_SELECTED=bigcode/starcoder2-7b" && goto :selection_done
if "%choice%"=="11" set "MODEL_SELECTED=deepseek-ai/deepseek-coder-6.7b-instruct" && goto :selection_done
if "%choice%"=="12" set "MODEL_SELECTED=meta-llama/Llama-4-Scout-17B-16E-Instruct" && goto :selection_done
if "%choice%"=="13" set "MODEL_SELECTED=microsoft/Phi-3.5-vision-instruct" && goto :selection_done
if "%choice%"=="14" set "MODEL_SELECTED=Qwen/Qwen2-VL-7B-Instruct" && goto :selection_done
if "%choice%"=="15" set "MODEL_SELECTED=Qwen/Qwen2.5-7B-Instruct" && goto :selection_done
if "%choice%"=="16" set "MODEL_SELECTED=microsoft/Phi-4" && goto :selection_done
if "%choice%"=="17" set "MODEL_SELECTED=meta-llama/Llama-3.1-8B-Instruct" && goto :selection_done
if "%choice%"=="18" goto :custom_model
if "%choice%"=="19" set "MODEL_SELECTED=%DEFAULT_MODEL%" && goto :selection_done
if "%choice%"=="0" echo 👋 Goodbye! && exit /b 0

echo ❌ Invalid selection. Please choose 0-19.
timeout /t 2 /nobreak >nul
goto :selection_loop

:custom_model
set /p "custom_model=Enter custom model name (e.g., microsoft/Phi-4): "
if "%custom_model%"=="" (
    echo ❌ Please enter a valid model name
    timeout /t 2 /nobreak >nul
    goto :selection_loop
)
set "MODEL_SELECTED=%custom_model%"
goto :selection_done

:selection_done
echo.
echo ✅ Selected model: %MODEL_SELECTED%
echo.
goto :eof

:parse_args
REM Parse command line arguments
:arg_loop
if "%1"=="" goto :args_done
if "%1"=="--model" (
    set "MODEL=%2"
    shift
    shift
    goto :arg_loop
)
if "%1"=="--host" (
    set "HOST=%2"
    shift
    shift
    goto :arg_loop
)
if "%1"=="--port" (
    set "PORT=%2"
    shift
    shift
    goto :arg_loop
)
if "%1"=="--env-name" (
    set "ENV_NAME=%2"
    shift
    shift
    goto :arg_loop
)
echo ❌ Unknown option: %1
echo Use --help for usage information
exit /b 1

:args_done

REM Show interactive model selection if no model specified
if "%INTERACTIVE_MODE%"=="true" (
    call :get_model_selection
    set "MODEL=%MODEL_SELECTED%"
)

echo.
echo 🚀 Starting vLLM Server for OpenDXA (Windows)...
echo 📋 Configuration:
echo   • Model: %MODEL%
echo   • Host: %HOST%
echo   • Port: %PORT%
echo   • Environment: %ENV_NAME%
echo.

REM Hardware recommendations
echo %MODEL% | findstr /C:"Phi-3.5-mini" /C:"gemma-2-2b" /C:"Qwen2.5-3B" /C:"Llama-3.2-3B" >nul
if not errorlevel 1 echo 💡 This model is optimized for CPU/Windows and lower memory systems

echo %MODEL% | findstr /C:"Phi-4" /C:"Qwen2.5-7B" /C:"Mistral-7B" /C:"Llama-3.1-8B" >nul
if not errorlevel 1 echo 💡 This model works best with GPU (14-30GB VRAM recommended)

echo %MODEL% | findstr /C:"vision" /C:"VL" /C:"Scout" >nul
if not errorlevel 1 echo 💡 This is a multimodal model - supports both text and images

echo %MODEL% | findstr /C:"coder" /C:"starcoder" >nul
if not errorlevel 1 echo 💡 This model is specialized for code generation and programming

REM Check if running in WSL
wsl --status >nul 2>&1
if not errorlevel 1 (
    echo 🔌 Using WSL vLLM installation...
    echo 🌐 Starting vLLM OpenAI-compatible API server in WSL...
    echo 💡 Server will be available at: http://%HOST%:%PORT%
    echo 📖 API docs will be at: http://%HOST%:%PORT%/docs
    echo 🛑 Press Ctrl+C to stop the server
    echo.
    
    REM Adjust parameters for multimodal models
    set "EXTRA_ARGS="
    echo %MODEL% | findstr /C:"vision" /C:"VL" /C:"Scout" >nul
    if not errorlevel 1 set "EXTRA_ARGS=--limit-mm-per-prompt {\"image\": 5}"
    
    wsl bash -c "source ~/vllm_env/bin/activate && python -m vllm.entrypoints.openai.api_server --model '%MODEL%' --host '%HOST%' --port '%PORT%' --dtype float16 --max-model-len 2048 --disable-frontend-multiprocessing %EXTRA_ARGS%"
) else (
    echo 🔌 Using Native Windows vLLM installation...
    
    REM Check if Python vLLM environment exists
    if not exist "%USERPROFILE%\%ENV_NAME%" (
        echo ❌ Error: vLLM environment not found
        echo 💡 Please install vLLM first using: bin\vllm\install.bat
        pause
        exit /b 1
    )
    
    echo 🌐 Starting vLLM OpenAI-compatible API server...
    echo 💡 Server will be available at: http://%HOST%:%PORT%
    echo 📖 API docs will be at: http://%HOST%:%PORT%/docs
    echo 🛑 Press Ctrl+C to stop the server
    echo.
    
    REM Activate environment and start server
    call "%USERPROFILE%\%ENV_NAME%\Scripts\activate.bat"
    
    REM Adjust parameters for multimodal models
    set "EXTRA_ARGS="
    echo %MODEL% | findstr /C:"vision" /C:"VL" /C:"Scout" >nul
    if not errorlevel 1 set "EXTRA_ARGS=--limit-mm-per-prompt {\"image\": 5}"
    
    python -m vllm.entrypoints.openai.api_server --model "%MODEL%" --host "%HOST%" --port "%PORT%" --dtype float16 --max-model-len 2048 --disable-frontend-multiprocessing %EXTRA_ARGS%
) 