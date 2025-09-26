# Ollama Management Scripts

This directory contains a suite of scripts to install, manage, and use [Ollama](https://ollama.com/) for local large language model (LLM) and embedding inference within the Dana runtime. These scripts provide a consistent experience on both macOS and Windows.

## Quick Start

| Action | macOS | Linux | Windows |
| :--- | :--- | :--- | :--- |
| **Install & Configure** | `bash ./bin/ollama/setup_macos.sh` | `bash ./bin/ollama/setup.sh` | `.\bin\ollama\setup.bat` |
| **Chat with Model** | `./bin/ollama/chat.sh --model <name>` | `./bin/ollama/chat.sh --model <name>` | `.\bin\ollama\chat.bat --model <name>` |
| **Uninstall** | `./bin/ollama/uninstall.sh` | `./bin/ollama/uninstall.sh` | `.\bin\ollama\uninstall.bat` |

---

## Scripts Overview


### `setup.sh` (Linux) & `setup_macos.sh` (macOS)
End-to-end assistants that:

1. Check whether Ollama is installed (and offer to install via the official script or Homebrew).
2. Ask where to store configuration (`.env` in the project, `~/.dana/.env`, or both).
3. Let you select language and/or embedding models, including pulling new models from the Ollama Hub.
4. Write all `LOCAL_*` and embedding-specific variables to your chosen `.env` files via a Python helper.
5. Run quick smoke tests against the OpenAI-compatible `/chat/completions` and native `/api/embed` endpoints to confirm the setup.

### `setup.bat` (Windows)
Delegates to `setup_windows.ps1` to deliver the same guided experience using Winget for installation, environment updates, and validation tests.

### `chat.sh` / `chat.bat`
Starts an interactive chat session with any downloaded model.

```bash
./bin/ollama/chat.sh --model llama3
```

### `uninstall.sh` / `uninstall.bat`
Removes Ollama using the appropriate package manager and reminds you to delete cached models under `~/.ollama/models` if you want to reclaim disk space.

## Environment updates & Dana integration

During the guided setup the script asks where you want Ollama settings stored—either the project’s `.env`, your user-level `~/.dana/.env`, or both. It then populates the relevant `LOCAL_*` and embedding-related variables so Dana can discover your local models without any manual editing.

If you skip configuration, nothing on disk changes. You can still export the same variables in your shell before launching Dana to test things temporarily, and re-run the setup script later to make the changes persistent.

Either way, Dana’s `LLMResource` and `EmbeddingResource` immediately understand the `local` / `ollama:<model>` handles, so switching between local Ollama and hosted providers (OpenAI, Azure, etc.) stays frictionless.