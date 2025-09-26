@echo off
setlocal ENABLEDELAYEDEXPANSION

echo 🚀 Starting Ollama for Dana (Windows)...

where ollama >nul 2>nul
if errorlevel 1 (
	echo ❌ Ollama CLI not found in PATH. Run .\bin\ollama\setup.bat first.
	exit /b 1
)

REM Attempt to start Windows service if present
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$svc = Get-Service -Name 'Ollama' -ErrorAction SilentlyContinue;" ^
  "if ($svc) {" ^
  "  if ($svc.Status -ne 'Running') {" ^
  "    Start-Service -InputObject $svc;" ^
  "    try { $svc.WaitForStatus('Running','00:00:15') } catch {}" ^
  "  }" ^
  "  if ($svc.Status -eq 'Running') { exit 0 } else { exit 3 }" ^
  "} else { exit 2 }" >nul
set "ERR=%ERRORLEVEL%"

if "%ERR%"=="0" (
	echo ✅ Ollama Windows service is running.
	goto :WAIT_READY
)

if "%ERR%"=="2" (
	echo ℹ️  Ollama Windows service not found. Launching foreground 'ollama serve'...
	start "Ollama Serve" /b cmd /c "ollama serve"
	goto :WAIT_READY
)

echo ❌ Failed to start the Ollama service (code %ERR%).
echo    Try starting the Ollama desktop app manually.
exit /b %ERR%

:WAIT_READY
REM Wait for API to respond
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$uri = 'http://127.0.0.1:11434/api/version';" ^
  "for ($i = 0; $i -lt 30; $i++) {" ^
  "  try {" ^
  "    Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 2 | Out-Null;" ^
  "    exit 0" ^
  "  } catch {" ^
  "    Start-Sleep -Seconds 1" ^
  "  }" ^
  "}" ^
  "exit 1" >nul
if errorlevel 1 (
	echo ⚠️  Ollama did not respond at http://127.0.0.1:11434 within 30s.
	echo    Run "ollama serve" manually or launch the Ollama desktop app.
	exit /b 1
)

echo 🎉 Ollama is ready at http://127.0.0.1:11434
exit /b 0
