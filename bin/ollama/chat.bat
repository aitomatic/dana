@echo off
rem
rem chat.bat: Starts an interactive chat session with a specified Ollama model.
rem
rem Usage:
rem   .\bin\ollama\chat.bat --model <model_name>
rem

set "MODEL_NAME=phi3:mini"

:arg_loop
if "%1"=="" goto :args_done
if /i "%1"=="--model" (
    set "MODEL_NAME=%2"
    shift
)
shift
goto arg_loop
:args_done

if not defined MODEL_NAME (
    echo ❌ Error: Model name not specified.
    echo Usage: .\bin\ollama\chat.bat --model ^<model_name^>
    exit /b 1
)

echo 💬 Starting chat with model: %MODEL_NAME%
echo    (Type '/bye' to exit)
echo ---

ollama run "%MODEL_NAME%" 