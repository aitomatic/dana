<!--
⚠️ IMPORTANT FOR AI CODE GENERATORS:
Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
NEVER use dot notation: `private.x`, `public.x`, etc.
Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.
-->

<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# vLLM Installation Scripts

Quick installation scripts for **vLLM** (Very Large Language Models) inference engine on macOS and Windows.

⚠️ **Important**: vLLM on macOS runs **CPU-only** with no GPU acceleration. For Apple Silicon GPU acceleration, consider alternatives like [MLX](https://github.com/ml-explore/mlx) or [llama.cpp](https://github.com/ggerganov/llama.cpp).

✅ **Stability**: The installation script now uses stable vLLM version v0.9.1 and includes multiprocessing fixes to prevent common import errors on macOS.

## 🚀 Quick Install

### macOS (Apple Silicon & Intel)
```bash
./bin/vllm/install.sh
```

**Custom environment name:**
```bash
./bin/vllm/install.sh --env-name my_vllm_env
```

### Windows
```cmd
bin\vllm\install.bat
```

**Interactive mode (recommended):**
```cmd
bin\vllm\install.bat
```

**Direct installation methods:**
```cmd
bin\vllm\install.bat --wsl        # WSL installation (recommended)
bin\vllm\install.bat --native     # Native Windows (experimental)
bin\vllm\install.bat --pip        # pip installation (limited)
```

## 🗑️ Quick Uninstall

### macOS/Linux
```bash
./bin/vllm/uninstall.sh           # Interactive uninstall
./bin/vllm/uninstall.sh --yes     # Auto-confirm uninstall
```

### Windows
```cmd
bin\vllm\uninstall.bat            # Auto-detect and remove
bin\vllm\uninstall.bat --wsl      # Remove WSL installation
bin\vllm\uninstall.bat --native   # Remove native installation
```

## 📋 Prerequisites

### macOS
- **macOS Sonoma 14.4+** (required)
- **Xcode 15.4+** and Command Line Tools (required)
- **Python 3.8+** (Python 3.10+ recommended)
- **Git** (for cloning repository)

### Install Prerequisites (macOS)
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Python via Homebrew (recommended)
brew install python

# Or download from python.org
# https://www.python.org/downloads/
```

### Windows
**Note**: vLLM does not officially support native Windows. Multiple installation methods available:

#### WSL Installation (Recommended):
- **Windows 10 version 2004+ or Windows 11** (required)
- **WSL (Windows Subsystem for Linux)** (auto-installed by script)
- **Ubuntu in WSL** (auto-configured)
- **Administrator access** (for WSL installation)

#### Native Windows (Experimental):
- **Visual Studio 2019+ with C++ build tools** (required)
- **CUDA Toolkit** (for GPU support)
- **Python 3.12** (recommended for community fork)
- **Git for Windows** (required)
- **Advanced development knowledge** (troubleshooting required)

#### pip Installation (Limited):
- **Python 3.8+** (required)
- **Windows 10/11** (required)
- **No GPU support** (CPU-only)
- **May fail** (not officially supported)

### Install Prerequisites (Windows)

#### For WSL Installation (Recommended):
```cmd
# The install script will handle WSL installation automatically
# Just run: bin\vllm\install.bat --wsl
```

#### For Native Windows (Advanced):
```cmd
# Install Visual Studio Community with C++ build tools
# Download from: https://visualstudio.microsoft.com/vs/community/

# Install CUDA Toolkit (for GPU support)  
# Download from: https://developer.nvidia.com/cuda-downloads

# Install Python 3.12
# Download from: https://www.python.org/downloads/

# Install Git for Windows
# Download from: https://git-scm.com/download/win
```

#### For pip Installation:
```cmd
# Install Python 3.8+ with pip
# Download from: https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation
```

## ✨ What You Get

After installation:
- ✅ Complete vLLM installation from source (or WSL/community fork on Windows)
- ✅ Isolated Python virtual environment
- ✅ CPU-optimized build (macOS/Linux) or WSL environment (Windows)
- ✅ All required dependencies
- ✅ Installation verification
- ✅ **Convenience start script** (`bin/start_vllm.sh` / `bin/start_vllm.bat`)
- ✅ Helpful usage instructions

### 🛠️ Convenience Start Script Features

The `bin/start_vllm.sh` / `bin/start_vllm.bat` scripts provide:
- **🚀 One-command startup**: No need to remember activation commands
- **⚙️ Configurable options**: Model, host, port, environment name
- **🔍 Environment validation**: Checks vLLM installation and dependencies  
- **📋 Port conflict detection**: Warns if port is already in use
- **💡 Helpful error messages**: Clear guidance when things go wrong
- **📖 Built-in help**: `--help` flag shows all options
- **🔌 Auto-activation**: Handles environment activation automatically
- **🛡️ Stability fixes**: Uses stable vLLM version and prevents import errors
- **🖼️ Interactive Model Selection**: 19 curated models organized by use case (CPU, GPU, coding, vision)
- **🐧 Smart Platform Detection**: Windows script auto-detects WSL vs native installation

## 🔧 Installation Details

The script performs these steps:
1. **System Checks**: Verifies macOS version, Python, and Xcode requirements
2. **Environment Setup**: Creates isolated Python virtual environment
3. **Source Download**: Clones vLLM repository and switches to stable version
4. **Dependency Installation**: Installs CPU-specific requirements
5. **Build Process**: Compiles vLLM with CPU target and stability fixes
6. **Verification**: Tests installation success
7. **Start Script**: Creates convenience script with multiprocessing fixes

## 📁 Installation Locations

### Default Paths
- **Virtual Environment**: `~/vllm_env/`
- **vLLM Source**: `~/vllm/`
- **Dependencies**: Installed in virtual environment

### Custom Environment
```bash
./bin/vllm/install.sh --env-name custom_name
# Creates: ~/custom_name/
```

## 🚀 Usage After Installation

### 1. Quick Start (Recommended)

**macOS/Linux:**
```bash
# Start vLLM server with interactive model selection
./bin/start_vllm.sh

# Start with custom model and port
./bin/start_vllm.sh --model microsoft/Phi-4 --port 8080

# See all options
./bin/start_vllm.sh --help
```

**Windows:**
```cmd
REM Start vLLM server with interactive model selection (19 curated models)
bin\start_vllm.bat

REM Start with custom model and port
bin\start_vllm.bat --model microsoft/Phi-4 --port 8080

REM See all options
bin\start_vllm.bat --help
```

### 2. Manual Activation

**macOS/Linux:**
```bash
source ~/vllm_env/bin/activate
```

**Windows (WSL):**
```bash
wsl bash -c "source ~/vllm_env/bin/activate && python -c 'import vllm; print(\"vLLM ready!\")'"
```

**Windows (Native):**
```cmd
call %USERPROFILE%\vllm_env\Scripts\activate.bat
```

### 3. Basic vLLM Usage
```python
from vllm import LLM, SamplingParams

# Create LLM instance
llm = LLM(model="facebook/opt-125m")  # Small model for testing

# Define sampling parameters
sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

# Generate text
prompts = ["Hello, my name is", "The capital of France is"]
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
```

### 4. Command Line Usage

**Using the convenience script (recommended):**

**macOS/Linux:**
```bash
# Start server with defaults (facebook/opt-125m on localhost:8000)
./bin/start_vllm.sh

# Start with different model
./bin/start_vllm.sh --model microsoft/DialoGPT-medium

# Start on different port
./bin/start_vllm.sh --port 8080

# Combine options
./bin/start_vllm.sh --model huggingface/CodeBERTa-small-v1 --port 8080 --host 0.0.0.0
```

**Windows (WSL/Native):**
```cmd
# Start server with defaults (facebook/opt-125m on localhost:8000)
bin\start_vllm.bat

# Start with different model  
bin\start_vllm.bat --model microsoft/DialoGPT-medium

# Start on different port
bin\start_vllm.bat --port 8080

# Combine options
bin\start_vllm.bat --model huggingface/CodeBERTa-small-v1 --port 8080 --host 0.0.0.0
```

**Manual server startup:**
```bash
# Activate environment first
source ~/vllm_env/bin/activate

# Run vLLM server manually
python -m vllm.entrypoints.openai.api_server \
    --model facebook/opt-125m \
    --host localhost \
    --port 8000
```

## ⚠️ Important Limitations

### macOS Specific
- **CPU-Only**: No GPU acceleration available
- **Performance**: Slower than CUDA-enabled systems
- **Memory**: May require significant RAM for larger models
- **Data Types**: Only FP32 and FP16 supported

### Windows Specific
- **WSL Required**: Recommended installation runs in WSL (Linux subsystem)
- **Native Build**: Experimental, community-maintained, may not support latest features  
- **GPU Support**: Available in WSL with proper CUDA setup
- **Performance**: WSL performance close to native Linux

### Recommended Alternatives for Apple Silicon
- **[MLX](https://github.com/ml-explore/mlx)**: Native Apple Silicon GPU support
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)**: Optimized for Apple Silicon
- **[Ollama](https://ollama.com/)**: Easy local LLM management

### Recommended Alternatives for Windows
- **[Ollama](https://ollama.com/)**: Native Windows support with easy management
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)**: Good Windows compatibility
- **[Text Generation WebUI](https://github.com/oobabooga/text-generation-webui)**: Windows-friendly interface

## 🐛 Troubleshooting

### Common Issues

**"macOS version too old"**:
- Upgrade to macOS Sonoma 14.4 or later
- vLLM requires modern macOS for compilation

**"Xcode version incompatible"**:
- Update Xcode to 15.4+ from App Store
- Run `xcode-select --install` for Command Line Tools

**"Python version too old"**:
- Install Python 3.8+ (3.10+ recommended)
- Use Homebrew: `brew install python`

**"Build fails with compiler errors"**:
- Ensure Xcode Command Line Tools are installed
- Try updating Xcode and macOS
- Check available disk space (build requires several GB)

**"Import vllm fails"**:
- Ensure virtual environment is activated
- Check installation logs for errors
- Try reinstalling in clean environment

**"ImportError: cannot import name 'PoolingParams'"**:
- This error occurs with unstable vLLM versions
- The install script now uses stable version v0.9.1 to prevent this
- If you have an older installation, reinstall: `./bin/vllm/install.sh`
- The start script includes `--disable-frontend-multiprocessing` to prevent import errors

### Windows-Specific Issues

**"WSL not found/installation failed"**:
- Ensure Windows 10 version 2004+ or Windows 11
- Run PowerShell as Administrator
- Manually run: `wsl --install`
- Restart computer after installation

**"vLLM not found in WSL"**:
- Open WSL terminal: `wsl`
- Check if environment exists: `ls ~/vllm_env/`
- Re-run installation if needed
- Ensure Ubuntu/Linux packages are installed

**"start_vllm.bat fails"**:
- Ensure WSL is running: `wsl --status`
- Check vLLM installation in WSL
- Try manual WSL command execution
- Verify port is not in use on Windows

**"Native Windows build fails"**:
- This is expected - use WSL instead
- If persisting, ensure all Visual Studio components installed
- Check CUDA toolkit compatibility
- Review community fork documentation

### Getting Help

1. **Check Logs**: Installation script provides detailed output
2. **vLLM Documentation**: https://docs.vllm.ai/
3. **GitHub Issues**: https://github.com/vllm-project/vllm/issues
4. **macOS Guide**: https://docs.vllm.ai/en/latest/getting_started/installation/cpu-apple.html

## 🔄 Updates

### Update vLLM
```bash
# Activate environment
source ~/vllm_env/bin/activate

# Update source
cd ~/vllm
git pull origin main

# Reinstall
VLLM_TARGET_DEVICE=cpu pip install -e .
```

### Reinstall from Scratch
```bash
# Remove old installation
rm -rf ~/vllm_env ~/vllm

# Run install script again
./bin/vllm/install.sh
```

## 🧪 Testing Your Installation

### Quick Test
```bash
source ~/vllm_env/bin/activate
python -c "from vllm import LLM; print('vLLM is ready!')"
```

### Model Test
```python
# test_vllm.py
from vllm import LLM

# Use a small model for testing
model_name = "facebook/opt-125m"
llm = LLM(model=model_name)

prompts = ["The future of AI is"]
outputs = llm.generate(prompts)

for output in outputs:
    print(f"Generated: {output.outputs[0].text}")
```

## 📊 Performance Expectations

### Apple Silicon (M1/M2/M3)
- **Small Models (< 1B params)**: Usable performance
- **Medium Models (1B-7B params)**: Slow but functional
- **Large Models (> 7B params)**: Very slow, may require lots of RAM

### Intel Mac
- **Performance**: Generally slower than Apple Silicon
- **Compatibility**: Full vLLM feature support
- **Memory**: May need 16GB+ RAM for decent performance

## 🗑️ Uninstallation

### Quick Uninstall (Recommended)

**macOS/Linux:**
```bash
./bin/vllm/uninstall.sh
```

**Custom environment:**
```bash
./bin/vllm/uninstall.sh --env-name my_vllm_env
```

**Auto-confirm (no prompts):**
```bash
./bin/vllm/uninstall.sh --yes
```

**Windows:**
```cmd
bin\vllm\uninstall.bat
bin\vllm\uninstall.bat --wsl --yes            # Remove WSL installation
bin\vllm\uninstall.bat --native --yes         # Remove native installation  
bin\vllm\uninstall.bat --pip                  # Remove pip installation
```

### 🛠️ Uninstall Script Features

The uninstall scripts provide:
- **🔍 Auto-detection**: Automatically finds vLLM installations
- **📋 Safe removal**: Shows what will be deleted before proceeding
- **💾 Size reporting**: Displays disk space that will be freed
- **⚠️ Confirmation prompts**: Prevents accidental deletion (unless --yes used)
- **🎯 Selective removal**: Only removes vLLM-related files
- **📝 Clear feedback**: Shows progress and results of each step
- **🔧 Reinstall guidance**: Provides commands to reinstall if needed

### Manual Uninstallation (Alternative)

If you prefer manual removal:

```bash
# Remove virtual environment
rm -rf ~/vllm_env

# Remove source code
rm -rf ~/vllm

# Remove start script
rm -f ./bin/start_vllm.sh

# That's it! No other system modifications were made
```

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 