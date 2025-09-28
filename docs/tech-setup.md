# Dana Technical Setup Guide

Use this guide to set up your development environment for running and contributing to Dana

## Navigation
- [Quick Start](#quick-start)
- [Python Installation](#python-installation)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [Create and Activate a Virtual Environment](#create-and-activate-a-virtual-environment)
- [Configure API Keys](#configure-api-keys)
- [Install Dana](#install-dana)
- [Troubleshooting](#troubleshooting)
- [Contributor Setup (Optional)](#contributor-setup-optional)
- [IDE Extension](#ide-extension)

---

## Quick Start

### Prerequisites
- Python **3.12 or above**
```bash
python3 # Linux/macOS
```
```bash
python # Windows  
```
**For contributors:**  
- Git  
- Node.js **18+** (only if building/modifying Agent Studio UI; install via nvm or from `https://nodejs.org`)  
- GNU Make (optional; you can run npm/uv commands directly)  

---

## Python Installation

### Linux

**Option 1: Ubuntu/Debian (recommended)**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-pip
```
Verify:
```bash
python3.12 --version
```

**Option 2: All distros (advanced, pyenv)**
```bash
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

# Add to ~/.bashrc (or ~/.zshrc)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Restart shell, then install Python
pyenv install 3.12.0
pyenv global 3.12.0
```
Verify:
```bash
python3 --version
```

**Optional PATH for --user installs**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

### macOS

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Apple Silicon
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# For Intel Macs, replace /opt/homebrew with /usr/local
brew install python@3.13
```
Verify:
```bash
python3 --version
```

**Optional PATH for --user installs**
```bash
echo 'export PATH="$(python3 -m site --user-base)/bin:$PATH"' >> ~/.zprofile
```

---

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/).  
   - Check **Add Python to PATH**  
   - Check **Disable path length limit**  

2. Verify:
```powershell
python --version
```

3. Virtual environment activation:
```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1
# If blocked:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
```cmd
:: Command Prompt
.venv\Scripts\activate.bat
```

**Alternative (if multiple Python installs):**
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## Create and Activate a Virtual Environment

From your project directory:
```bash
python3 -m venv .venv        # Linux/macOS
python -m venv .venv         # Windows
```

Activate it (in every new shell):
```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt
.\.venv\Scripts\activate.bat
```

Verify:
```bash
which python   # Linux/macOS
where python   # Windows
```

---

## Configure API Keys

Dana requires an API key for a model provider.

Use the starter file at the repo root: `.env.template` (same as `.env.example`).

```bash
cp .env.template .env
```

Edit `.env` and uncomment **one** provider:
- OpenAI → `OPENAI_API_KEY=...`
- Azure OpenAI → `AZURE_OPENAI_API_KEY=...` (+ related vars)
- Anthropic Claude → `ANTHROPIC_API_KEY=...`
- Local models (Ollama, vLLM) → `LOCAL_API_KEY`, `LOCAL_BASE_URL`, `LOCAL_MODEL_NAME`

Dana looks for `.env` in this order:
1. `./.env` (project root) — recommended
2. `~/.dana/.env`
3. `~/.env`

---

## Install Dana

### Quick install (users)
```bash
python -m pip install --upgrade pip
pip install dana
```

Verify:
```bash
# CLI
dana --version              # macOS/Linux
python -m dana --version    # Cross-platform

# Python one-liner
python -c "import dana; print(dana.__version__)"

# Via package manager
pip show dana | grep Version         # macOS/Linux
pip show dana | Select-String Version  # Windows PowerShell
```
Optional REPL smoke test:
```bash
dana repl
```
At the prompt, type:
```dana
help()
```

### Development install (contributors)
```bash
git clone https://github.com/aitomatic/dana.git
cd dana
uv sync --extra dev

# Build Dana Agent Studio (frontend) — required to serve the local UI or when modifying UI
make build-frontend

# Serve UI + API locally at http://127.0.0.1:12345
make local-server
# or
uv run python -m dana.api.server
```

Verify:
```bash
# Check Dana version
uv run dana --version

# Confirm Agent Studio launches in browser
open http://127.0.0.1:12345    # macOS
xdg-open http://127.0.0.1:12345  # Linux
# Windows: manually open browser at http://127.0.0.1:12345
```

**Notes for contributors:**  
- Repo clones must build the frontend at least once with `make build-frontend`.  
- If you modify UI code, rebuild (`make build-frontend`) or run dev mode (`npm run dev` in `dana/contrib/ui`).  
- For editing `.na` files, install the [Dana VS Code extension](#ide-extension).

---

## Troubleshooting

- Dana not found: activate the virtual environment.  
- Wrong Python version: `python3 --version` should be 3.12 or above.  
- API key errors: check `.env` exists with a valid key.  
- Windows PowerShell: if activation fails, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.  
- UI build: check Node.js 18+ (`node -v`) and GNU Make (`make -v`); rebuild with `make build-frontend`.  

---

## Contributor Setup (Optional)

Install uv:
- macOS: `brew install uv`
- Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `winget install astral-sh.uv`

Check:
```bash
uv --version
```

Git config:
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## IDE Extension

We recommend the Dana Language Extension for VS Code:
- Syntax highlighting for `.na` files  
- Code snippets and REPL integration  
- Easier agent workflow editing  

Search **“Dana”** in the VS Code Extensions Marketplace, or install from Open VSX (`aitomatic.dana-language`).