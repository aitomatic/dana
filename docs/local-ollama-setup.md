# Quick Ollama Setup for Dana

Want Dana to run fully local? Follow these essentials. For deeper explanations, troubleshooting, and Windows screenshots, open `bin/ollama/README.md`—this page just keeps the basics handy.

## 1. Use the Makefile helpers
- **Install & configure (guided wizard):**
  ```bash
  make install-ollama
  ```
- **Start the service for local inference:**
  ```bash
  make start-ollama
  ```

`make install-ollama` wraps the OS-specific setup script. It detects macOS vs. Linux, installs the Ollama daemon with the recommended package source, then walks you through where to save `.env` values (project, `~/.dana/.env`, or both), which chat and embedding models to pull, and finally runs quick curl checks to confirm the API is live. Run it any time you want to tweak settings.

> 💡 Prefer the Makefile commands so the workflow stays consistent with the other local LLM integrations. The raw scripts still live in `bin/ollama/` if you need them.

## 2. Keep the Ollama service running
- macOS: `make start-ollama` will wake the launchctl service; you can still launch the Ollama desktop app if you prefer.
- Linux: `make start-ollama` attempts to use systemd when available, otherwise it runs `ollama serve` in the foreground.
- Windows: Use the Ollama desktop app or `bin\ollama\setup.bat` to install/configure; the tray icon confirms the service is running.

## 3. Launch Dana and verify
```bash
dana repl
```
```dana
set_model("local:phi3:mini")
agent Neo
Neo.chat("What was The Oracle's best advice?")
```
That’s it—you’re now running Dana with your local Ollama models. See `bin/ollama/README.md` any time you need the full playbook or troubleshooting tips.