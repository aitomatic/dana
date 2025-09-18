# Dana Technical Setup Guide

This guide will help you set up Dana for development and contribution.

## 🚀 Quick Start

### Prerequisites

- **Python**: Version 3.12 or 3.13 required
- **Command Line**: `python3` must be accessible from your terminal

## 📦 Python Installation by Platform

#### 🐧 Linux

1. **Install Python**: Use your package manager to install Python 3.12 or 3.13
2. **Update PATH**: Add to your `~/.bashrc`:
   ```bash
   export PATH=$PATH:/usr/.local/bin
   ```
   *(Adjust path if your Python scripts are installed elsewhere)*

#### 🍎 macOS

1. **Install Homebrew**: Visit [brew.sh](https://brew.sh) and follow installation instructions
2. **Verify Homebrew**: Ensure `brew` is in your PATH (follow post-installation instructions)
3. **Install Python**: 
   ```bash
   brew install python
   ```
4. **Verify Installation**:
   ```bash
   which python3
   ```
5. **Update PATH**: Add to your `~/.zprofile`:
   ```bash
   export PATH=$PATH:~/Library/Python/3.13/bin
   ```
   *(Replace `3.13` with your installed Python version)*

#### 🪟 Windows

1. **Install Python**:  
   - **Recommended:** Download Python 3.12 or 3.13 from [python.org](https://python.org).  
     The python.org installer will automatically update your `PATH` and enable long path support if you check the boxes during installation.  
     - During setup, make sure to check **"Add Python to PATH"** and **"Enable long path length limit"** (if available).
   - **Alternative:** If you have issues with the python.org installer, you can also install Python from the [Microsoft Store](https://apps.microsoft.com/store/detail/python-313/9NRWMJP3717K).

2. **Verify Installation**:  
   Open a new Command Prompt and run:
   ```
   python --version
   ```

3. *(If you used the Microsoft Store and encounter issues with long paths or PATH settings, you may need to manually enable long paths and update your environment variables. See these guides: [Autodesk](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/The-Windows-10-default-path-length-limitation-MAX-PATH-is-256-characters.html) | [Geek Rewind](https://geekrewind.com/how-to-enable-win32-long-paths-in-windows-11). Reboot after enabling long paths.)*

## 📚 Install Dana

Before installing Dana, it's recommended to use a Python virtual environment to avoid conflicts with other packages.

1. **Create a virtual environment** (if you haven't already):

   ```bash
   python3 -m venv .venv
   ```

2. **Activate the virtual environment**:

   ```bash
   source .venv/bin/activate
   ```

3. **Install Dana inside the virtual environment**:

   ```bash
   pip install dana
   ```

> 💡 **Tip:** Always activate your virtual environment with `source .venv/bin/activate` before running or installing anything for Dana.

### ⚙️ Environment Variable Setup for Dana

Dana searches for environment files in this priority order:

| Priority | Location | Use Case |
|----------|----------|----------|
| 🥇 **Highest** | `./.env` (project root) | Development projects |
| 🥈 **Medium** | `~/.dana/.env` | User-wide settings |
| 🥉 **Lowest** | `~/.env` | System-wide settings |

#### 🔧 Setup Options

**🎯 Option 1: Project-specific (Recommended)**
```bash
# In your project directory
curl -o .env https://raw.githubusercontent.com/aitomatic/dana/main/.env.example
# Edit .env with your API keys
```

**👤 Option 2: User-wide**
```bash
# Create Dana config directory
mkdir -p ~/.dana
# Download template
curl -o ~/.dana/.env https://raw.githubusercontent.com/aitomatic/dana/main/.env.example
# Edit with your credentials
```

**🌐 Option 3: System-wide**
```bash
# Download to home directory
curl -o ~/.env https://raw.githubusercontent.com/aitomatic/dana/main/.env.example
# Edit with your credentials
```

> 💡 **Tip**: Project-specific `.env` files override user/system settings, making them perfect for development.

### ✅ Verify Installation

1. **Start Dana REPL**:
   ```bash
   dana repl
   ```

2. **Test LLM Connection**:
   ```dana
   llm('Hello, Dana!')
   ```

   If successful, you'll see a response from your configured LLM provider.

## 🛠️ Contributor Setup

> **Prerequisites**: Complete the [Quick Start](#-quick-start-typical-developer) section first.

### 📦 Additional Tools

**Install `uv` (Python package manager)**:
```bash
pip install uv
```

**Configure Git**:
```bash
# Install Git (if not already installed)
# Windows: Download from git-scm.com
# macOS: brew install git
# Linux: Use your package manager

# Enable long paths on Windows
git config --global core.longpaths true
```

### 🚀 Development Environment

1. **Clone the Repository**:
   ```bash
   # HTTPS
   git clone https://github.com/aitomatic/dana.git
   
   # SSH (if you have SSH keys set up)
   git clone git@github.com:aitomatic/dana.git
   ```

2. **Setup Development Environment**:
   ```bash
   cd dana
   uv sync --extra dev
   ```

   This creates a virtual environment and installs all development dependencies.

3. **Activate Virtual Environment**:
   ```bash
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

🎉 **You're ready to contribute to Dana!**

## 🔌 IDE Extension

**Install Dana Language Extension**:
- **VSCode**: Search for `aitomatic.dana-language` in extensions
- **Direct Link**: [open-vsx.org/extension/aitomatic/dana-language](https://open-vsx.org/extension/aitomatic/dana-language)

**Auto-install for Projects**:
Create `.vscode/extensions.json` in your project:
```json
{
  "recommendations": [
    "aitomatic.dana-language",
    
    ...  // other extensions you want to install
  ]
}
```

