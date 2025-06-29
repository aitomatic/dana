@echo off
REM Chat with vLLM Server (Windows)
REM Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
REM Usage: bin\vllm\chat.bat [OPTIONS]

setlocal enabledelayedexpansion

REM Default configuration
set "DEFAULT_HOST=localhost"
set "DEFAULT_PORT=8000"
set "DEFAULT_TIMEOUT=30"

REM Initialize variables
set "HOST=%DEFAULT_HOST%"
set "PORT=%DEFAULT_PORT%"
set "TIMEOUT=%DEFAULT_TIMEOUT%"
set "MODEL="

if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

goto :parse_args

:show_help
echo Chat with vLLM Server (Windows)
echo.
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   --host HOST          vLLM server host (default: %DEFAULT_HOST%)
echo   --port PORT          vLLM server port (default: %DEFAULT_PORT%)
echo   --timeout TIMEOUT    Request timeout in seconds (default: %DEFAULT_TIMEOUT%)
echo   --model MODEL        Specific model to use (default: first available)
echo   --help, -h           Show this help message
echo.
echo Examples:
echo   %0                                    # Chat with default server
echo   %0 --port 8080                       # Chat with server on port 8080
echo   %0 --model microsoft/Phi-4           # Chat with specific model
echo.
echo Chat Commands:
echo   quit, exit, bye      Exit chat
echo   clear               Clear conversation history
echo   help                Show chat help
goto :eof

:parse_args
REM Parse command line arguments
:arg_loop
if "%1"=="" goto :args_done
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
if "%1"=="--timeout" (
    set "TIMEOUT=%2"
    shift
    shift
    goto :arg_loop
)
if "%1"=="--model" (
    set "MODEL=%2"
    shift
    shift
    goto :arg_loop
)
echo ❌ Unknown option: %1
echo Use --help for usage information
exit /b 1

:args_done

set "BASE_URL=http://%HOST%:%PORT%"
set "COMPLETIONS_URL=%BASE_URL%/v1/chat/completions"
set "MODELS_URL=%BASE_URL%/v1/models"

echo.
echo 💬 vLLM Chat Interface (Windows)
echo Server: %BASE_URL%
echo.

REM Check if server is responding
echo 🔍 Checking server connection...
curl -s --max-time 5 "%BASE_URL%/health" >nul 2>&1
if not errorlevel 1 goto :server_ok

curl -s --max-time 5 "%MODELS_URL%" >nul 2>&1
if not errorlevel 1 goto :server_ok

echo ❌ Cannot connect to vLLM server at %BASE_URL%
echo 💡 Make sure vLLM server is running:
echo    bin\vllm\start.bat
exit /b 1

:server_ok
echo ✅ Connected to server

REM Get available models and select one
echo 📋 Getting available models...
if "%MODEL%"=="" (
    for /f "delims=" %%i in ('curl -s --max-time %TIMEOUT% "%MODELS_URL%" 2^>nul ^| python -c "import json,sys;data=json.load(sys.stdin);models=data.get('data',[]);print(models[0]['id'] if models else 'facebook/opt-125m')" 2^>nul') do set "MODEL=%%i"
    if "!MODEL!"=="" set "MODEL=facebook/opt-125m"
)

echo 🤖 Using model: %MODEL%
echo.
echo 💡 Chat Commands:
echo   • Type naturally to chat with the AI
echo   • 'quit', 'exit', or 'bye' to stop
echo   • 'clear' to clear conversation history
echo   • 'help' for more commands
echo ==================================================

REM Initialize conversation file
set "CONVERSATION_FILE=%TEMP%\vllm_chat_%RANDOM%.json"
echo [] > "%CONVERSATION_FILE%"

REM Chat loop
:chat_loop
echo.
set /p "user_input=🧑 You: "

if "%user_input%"=="" goto :chat_loop

REM Convert to lowercase for comparison
set "input_lower=%user_input%"
for %%i in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do call set "input_lower=%%input_lower:%%i=%%i%%"

if "%input_lower%"=="quit" goto :chat_end
if "%input_lower%"=="exit" goto :chat_end
if "%input_lower%"=="bye" goto :chat_end

if "%input_lower%"=="clear" (
    echo [] > "%CONVERSATION_FILE%"
    echo 🧹 Conversation history cleared
    goto :chat_loop
)

if "%input_lower%"=="help" (
    echo 🆘 Available commands:
    echo    quit/exit/bye - Exit chat
    echo    clear - Clear conversation history
    echo    help - Show this help
    echo    Just type naturally to chat!
    goto :chat_loop
)

REM Add user message to conversation
echo 🤖 AI is thinking...

REM Create a temporary Python script for JSON handling
set "TEMP_PY=%TEMP%\vllm_chat_%RANDOM%.py"
(
echo import json, sys, time
echo.
echo # Load conversation
echo with open(r'%CONVERSATION_FILE%', 'r') as f:
echo     conversation = json.load(f)
echo.
echo # Add user message
echo conversation.append({'role': 'user', 'content': r'''%user_input%'''})
echo.
echo # Create request
echo request = {
echo     'model': r'%MODEL%',
echo     'messages': conversation,
echo     'temperature': 0.7,
echo     'max_tokens': 300,
echo     'stream': False
echo }
echo.
echo # Send request and handle response
echo import subprocess
echo import json
echo.
echo try:
echo     result = subprocess.run([
echo         'curl', '-s', '--max-time', '%TIMEOUT%', '-X', 'POST',
echo         '%COMPLETIONS_URL%',
echo         '-H', 'Content-Type: application/json',
echo         '-d', json.dumps(request)
echo     ], capture_output=True, text=True, timeout=%TIMEOUT%)
echo     
echo     if result.returncode == 0:
echo         response_data = json.loads(result.stdout)
echo         if 'choices' in response_data and len(response_data['choices']) > 0:
echo             ai_response = response_data['choices'][0]['message']['content']
echo             print(f'AI_RESPONSE:{ai_response}')
echo             
echo             # Add AI response to conversation
echo             conversation.append({'role': 'assistant', 'content': ai_response})
echo             with open(r'%CONVERSATION_FILE%', 'w') as f:
echo                 json.dump(conversation, f)
echo         else:
echo             print('ERROR:No response content received')
echo     else:
echo         print('ERROR:Request failed')
echo except Exception as e:
echo     print(f'ERROR:{str(e)}')
) > "%TEMP_PY%"

REM Execute the Python script and parse output
for /f "tokens=1,* delims=:" %%a in ('python "%TEMP_PY%" 2^>nul') do (
    if "%%a"=="AI_RESPONSE" (
        echo 🤖 AI: %%b
    ) else if "%%a"=="ERROR" (
        echo ❌ %%b
    )
)

REM Cleanup temp Python script
del "%TEMP_PY%" 2>nul

goto :chat_loop

:chat_end
echo 👋 Goodbye!

REM Cleanup
del "%CONVERSATION_FILE%" 2>nul 