# Ollama Management Scripts

This directory contains a suite of scripts to install, manage, and use [Ollama](https://ollama.com/) for local large language model (LLM) inference within the OpenDXA framework. These scripts provide a consistent experience on both macOS and Windows.

## Quick Start

| Action | macOS / Linux | Windows |
| :--- | :--- | :--- |
| **Install** | `./bin/ollama/install.sh` | `.\bin\ollama\install.bat` |
| **Start & Configure** | `source ./bin/ollama/start.sh` | `.\bin\ollama\start.bat` |
| **Chat with Model** | `./bin/ollama/chat.sh --model <name>` | `.\bin\ollama\chat.bat --model <name>` |
| **Uninstall** | `./bin/ollama/uninstall.sh` | `.\bin\ollama\uninstall.bat` |

---

##  Scripts Overview

### `install.sh` / `install.bat`
This script handles the installation of Ollama.
- **On macOS**: It uses [Homebrew](https://brew.sh/) to install the `ollama` package.
- **On Windows**: It uses [Winget](https://docs.microsoft.com/en-us/windows/package-manager/winget/) to install the `Ollama.Ollama` package.

The script checks for the required package manager and verifies the installation.

### `start.sh` / `start.bat`
This is the main script for integrating Ollama with the OpenDXA framework.

**Key Features:**
1.  **Service Check**: Ensures the Ollama background service is running. On macOS, it will attempt to start the service if it's not active.
2.  **Interactive Model Selection**: Presents a menu of popular and recommended models to download and run. It also allows you to specify a custom model.
3.  **Automatic Model Pull**: If the selected model is not found locally, the script will automatically pull it from the Ollama Hub.
4.  **Environment Configuration**: **Crucially, it sets the `LOCAL_LLM_URL` and `LOCAL_LLM_NAME` environment variables.** This allows the OpenDXA `LLMResource` to automatically connect to the local Ollama server when `"local"` is specified in the `preferred_models` configuration.

**Usage:**
-   **macOS/Linux**: You must `source` the script for the environment variables to be applied to your current shell session:
    ```bash
    source ./bin/ollama/start.sh
    ```
-   **Windows**: The script automatically starts a new `cmd` session where the environment variables are active:
    ```bash
    .\bin\ollama\start.bat
    ```

### `chat.sh` / `chat.bat`
A simple utility to quickly start an interactive chat session with any model you have downloaded.

**Usage:**
```bash
# Chat with the default model (phi3:mini)
./bin/ollama/chat.sh

# Chat with a specific model
./bin/ollama/chat.sh --model llama3
```

### `uninstall.sh` / `uninstall.bat`
This script removes Ollama from your system.

- It uses the same package managers (`brew` or `winget`) to perform the uninstallation.
- It provides a warning and instructions on how to manually delete the downloaded models, which are not removed by the uninstaller, to free up disk space. The model cache is typically located at `~/.ollama/models`.

---
## Integration with OpenDXA

The `start.sh` and `start.bat` scripts are designed for seamless integration. By setting the `LOCAL_LLM_URL` and `LOCAL_LLM_NAME` variables, they configure your environment to match what the `LLMResource` expects when it finds `"local"` in your list of preferred models in `opendxa_config.json`.

This allows you to easily switch between a local Ollama instance and other remote services like OpenAI without changing any code. 