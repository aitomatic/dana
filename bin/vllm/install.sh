#!/bin/bash
# Install vLLM for macOS and Linux (Ubuntu/Debian-based)
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/vllm/install.sh [--env-name ENV_NAME]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment name
ENV_NAME="vllm_env"

# Check for custom environment name
if [[ "$1" == "--env-name" && -n "$2" ]]; then
    ENV_NAME="$2"
fi

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            echo "ubuntu"
        elif command -v yum &> /dev/null; then
            echo "rhel"
        else
            echo "linux"
        fi
    else
        echo "unknown"
    fi
}

OS_TYPE=$(detect_os)

case "$OS_TYPE" in
    "macos")
        echo -e "${BLUE}🚀 Installing vLLM for macOS...${NC}"
        echo -e "${YELLOW}⚠️  Note: vLLM on macOS runs CPU-only (no GPU acceleration yet)${NC}"
        ;;
    "ubuntu"|"linux")
        echo -e "${BLUE}🚀 Installing vLLM for Linux...${NC}"
        echo -e "${GREEN}✅ GPU acceleration available if CUDA is properly configured${NC}"
        ;;
    "rhel")
        echo -e "${BLUE}🚀 Installing vLLM for Linux (RHEL/CentOS)...${NC}"
        echo -e "${GREEN}✅ GPU acceleration available if CUDA is properly configured${NC}"
        ;;
    *)
        echo -e "${RED}❌ Error: Unsupported operating system: $OSTYPE${NC}"
        echo -e "${YELLOW}💡 Supported systems: macOS, Ubuntu/Debian, RHEL/CentOS${NC}"
        exit 1
        ;;
esac
echo ""

# OS-specific system checks
check_system_requirements() {
    case "$OS_TYPE" in
        "macos")
            # Check macOS version
            MACOS_VERSION=$(sw_vers -productVersion)
            MAJOR_VERSION=$(echo "$MACOS_VERSION" | cut -d '.' -f 1)
            MINOR_VERSION=$(echo "$MACOS_VERSION" | cut -d '.' -f 2)
            
            echo -e "${BLUE}🖥️  macOS Version: ${MACOS_VERSION}${NC}"
            
            if [[ "$MAJOR_VERSION" -lt 14 || ("$MAJOR_VERSION" -eq 14 && "$MINOR_VERSION" -lt 4) ]]; then
                echo -e "${RED}❌ Error: macOS Sonoma (14.4) or later is required for vLLM${NC}"
                echo -e "${YELLOW}💡 Current version: ${MACOS_VERSION}, Required: 14.4+${NC}"
                exit 1
            fi
            ;;
        "ubuntu"|"linux")
            # Check Ubuntu/Debian version
            if command -v lsb_release &> /dev/null; then
                LINUX_VERSION=$(lsb_release -rs)
                LINUX_DISTRO=$(lsb_release -is)
                echo -e "${BLUE}🐧 Linux Distribution: ${LINUX_DISTRO} ${LINUX_VERSION}${NC}"
            else
                echo -e "${BLUE}🐧 Linux Distribution: Detected${NC}"
            fi
            
            # Check for CUDA (optional but recommended)
            if command -v nvidia-smi &> /dev/null; then
                CUDA_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -1)
                echo -e "${GREEN}🚀 NVIDIA GPU detected (Driver: ${CUDA_VERSION})${NC}"
                echo -e "${GREEN}💡 GPU acceleration will be available${NC}"
            else
                echo -e "${YELLOW}⚠️  No NVIDIA GPU detected - vLLM will run on CPU${NC}"
                echo -e "${YELLOW}💡 For GPU acceleration, install NVIDIA drivers and CUDA toolkit${NC}"
            fi
            ;;
        "rhel")
            # Check RHEL/CentOS version
            if [[ -f /etc/redhat-release ]]; then
                RHEL_VERSION=$(cat /etc/redhat-release)
                echo -e "${BLUE}🔴 Red Hat Distribution: ${RHEL_VERSION}${NC}"
            fi
            
            # Check for CUDA (optional but recommended)
            if command -v nvidia-smi &> /dev/null; then
                CUDA_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -1)
                echo -e "${GREEN}🚀 NVIDIA GPU detected (Driver: ${CUDA_VERSION})${NC}"
                echo -e "${GREEN}💡 GPU acceleration will be available${NC}"
            else
                echo -e "${YELLOW}⚠️  No NVIDIA GPU detected - vLLM will run on CPU${NC}"
                echo -e "${YELLOW}💡 For GPU acceleration, install NVIDIA drivers and CUDA toolkit${NC}"
            fi
            ;;
    esac
}

check_system_requirements

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed${NC}"
    echo -e "${YELLOW}💡 Please install Python 3.8+ (Python 3.10+ recommended):${NC}"
    echo "   - Download from: https://www.python.org/downloads/"
    echo "   - Or install via brew: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${BLUE}🐍 Python Version: ${PYTHON_VERSION}${NC}"

# Check Python version
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d '.' -f 1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d '.' -f 2)

if [[ "$PYTHON_MAJOR" -lt 3 || ("$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 8) ]]; then
    echo -e "${RED}❌ Error: Python 3.8+ is required for vLLM${NC}"
    echo -e "${YELLOW}💡 Current version: ${PYTHON_VERSION}, Required: 3.8+${NC}"
    exit 1
fi

# OS-specific build tools check
check_build_tools() {
    case "$OS_TYPE" in
        "macos")
            # Check if Xcode Command Line Tools are installed
            echo -e "${BLUE}🔧 Checking Xcode Command Line Tools...${NC}"
            if ! xcode-select -p &> /dev/null; then
                echo -e "${YELLOW}📦 Installing Xcode Command Line Tools...${NC}"
                xcode-select --install
                echo -e "${YELLOW}⏳ Please complete the Xcode Command Line Tools installation and run this script again${NC}"
                exit 0
            fi
            
            # Check Xcode version
            if command -v xcodebuild &> /dev/null; then
                XCODE_VERSION=$(xcodebuild -version | head -n1 | cut -d ' ' -f2)
                echo -e "${BLUE}🛠️  Xcode Version: ${XCODE_VERSION}${NC}"
                
                # Check if Xcode version is 15.4+
                XCODE_MAJOR=$(echo "$XCODE_VERSION" | cut -d '.' -f 1)
                XCODE_MINOR=$(echo "$XCODE_VERSION" | cut -d '.' -f 2)
                
                if [[ "$XCODE_MAJOR" -lt 15 || ("$XCODE_MAJOR" -eq 15 && "$XCODE_MINOR" -lt 4) ]]; then
                    echo -e "${YELLOW}⚠️  Warning: Xcode 15.4+ is recommended for vLLM${NC}"
                    echo -e "${YELLOW}   Current version: ${XCODE_VERSION}, Recommended: 15.4+${NC}"
                    echo -e "${YELLOW}   Please update Xcode from the App Store if you encounter build issues${NC}"
                fi
            fi
            ;;
        "ubuntu"|"linux")
            # Check for essential build tools
            echo -e "${BLUE}🔧 Checking build tools...${NC}"
            
            # Check for basic build tools
            missing_tools=()
            if ! command -v make &> /dev/null; then missing_tools+=("make"); fi
            if ! command -v gcc &> /dev/null; then missing_tools+=("gcc"); fi
            if ! command -v g++ &> /dev/null; then missing_tools+=("g++"); fi
            
            if [[ ${#missing_tools[@]} -gt 0 ]]; then
                echo -e "${YELLOW}📦 Installing build-essential...${NC}"
                sudo apt-get update
                sudo apt-get install -y build-essential
            else
                echo -e "${GREEN}✅ Build tools available${NC}"
            fi
            
            # Optional: Check for CUDA development tools
            if command -v nvidia-smi &> /dev/null && ! command -v nvcc &> /dev/null; then
                echo -e "${YELLOW}💡 NVIDIA GPU detected but CUDA toolkit not found${NC}"
                echo -e "${YELLOW}   For GPU acceleration, consider installing CUDA toolkit:${NC}"
                echo -e "${YELLOW}   sudo apt-get install nvidia-cuda-toolkit${NC}"
            fi
            ;;
        "rhel")
            # Check for essential build tools on RHEL/CentOS
            echo -e "${BLUE}🔧 Checking build tools...${NC}"
            
            # Check for Development Tools group
            if ! command -v make &> /dev/null || ! command -v gcc &> /dev/null; then
                echo -e "${YELLOW}📦 Installing Development Tools...${NC}"
                sudo yum groupinstall -y "Development Tools"
            else
                echo -e "${GREEN}✅ Build tools available${NC}"
            fi
            
            # Optional: Check for CUDA development tools
            if command -v nvidia-smi &> /dev/null && ! command -v nvcc &> /dev/null; then
                echo -e "${YELLOW}💡 NVIDIA GPU detected but CUDA toolkit not found${NC}"
                echo -e "${YELLOW}   For GPU acceleration, consider installing CUDA toolkit${NC}"
            fi
            ;;
    esac
}

check_build_tools

# Check if virtual environment already exists
VENV_PATH="$HOME/${ENV_NAME}"
if [[ -d "$VENV_PATH" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment '${ENV_NAME}' already exists at ${VENV_PATH}${NC}"
    read -p "Do you want to remove it and create a new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🗑️  Removing existing environment...${NC}"
        rm -rf "$VENV_PATH"
    else
        echo -e "${YELLOW}💡 You can specify a different environment name with: --env-name MY_ENV${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${BLUE}🐍 Creating Python virtual environment: ${ENV_NAME}${NC}"
python3 -m venv "$VENV_PATH"

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Upgrade pip, setuptools, and wheel
echo -e "${BLUE}📦 Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel

# Clone vLLM repository
VLLM_DIR="$HOME/vllm"
STABLE_VERSION="v0.9.1"

if [[ -d "$VLLM_DIR" ]]; then
    echo -e "${YELLOW}⚠️  vLLM repository already exists at ${VLLM_DIR}${NC}"
    read -p "Do you want to update it? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}📥 Updating vLLM repository...${NC}"
        cd "$VLLM_DIR"
        git fetch --all --tags
        git pull origin main
    else
        cd "$VLLM_DIR"
    fi
else
    echo -e "${BLUE}📥 Cloning vLLM repository...${NC}"
    git clone https://github.com/vllm-project/vllm.git "$VLLM_DIR"
    cd "$VLLM_DIR"
fi

# Switch to stable version for better reliability
echo -e "${BLUE}🏷️  Switching to stable version ${STABLE_VERSION}...${NC}"
echo -e "${YELLOW}💡 Using stable version instead of main branch for better reliability${NC}"
git checkout "$STABLE_VERSION"

# OS-specific vLLM installation
install_vllm() {
    case "$OS_TYPE" in
        "macos")
            # Install CPU requirements for macOS
            echo -e "${BLUE}📦 Installing CPU requirements for macOS...${NC}"
            if [[ -f "requirements-cpu.txt" ]]; then
                pip install -r requirements-cpu.txt
            else
                echo -e "${YELLOW}⚠️  requirements-cpu.txt not found, installing basic requirements...${NC}"
                pip install torch torchvision torchaudio
            fi
            
            # Install vLLM in CPU-only mode for macOS
            echo -e "${BLUE}🔨 Building and installing vLLM for macOS (CPU-only)...${NC}"
            VLLM_TARGET_DEVICE=cpu pip install -e .
            ;;
        "ubuntu"|"linux"|"rhel")
            # Install requirements for Linux (GPU support if available)
            if command -v nvidia-smi &> /dev/null; then
                echo -e "${BLUE}📦 Installing GPU requirements for Linux...${NC}"
                # Install PyTorch with CUDA support
                pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
                
                # Install other requirements
                if [[ -f "requirements.txt" ]]; then
                    pip install -r requirements.txt
                fi
                
                # Install vLLM with GPU support
                echo -e "${BLUE}🔨 Building and installing vLLM with GPU support...${NC}"
                pip install -e .
            else
                echo -e "${BLUE}📦 Installing CPU requirements for Linux...${NC}"
                # Install CPU-only PyTorch
                pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
                
                # Install CPU requirements if available
                if [[ -f "requirements-cpu.txt" ]]; then
                    pip install -r requirements-cpu.txt
                elif [[ -f "requirements.txt" ]]; then
                    pip install -r requirements.txt
                fi
                
                # Install vLLM in CPU mode
                echo -e "${BLUE}🔨 Building and installing vLLM (CPU-only)...${NC}"
                VLLM_TARGET_DEVICE=cpu pip install -e .
            fi
            ;;
    esac
}

install_vllm

# Verify installation
echo -e "${BLUE}✅ Verifying vLLM installation...${NC}"
if python -c "import vllm; print(f'vLLM version: {vllm.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}🎉 vLLM successfully installed!${NC}"
else
    echo -e "${RED}❌ Error: vLLM installation verification failed${NC}"
    exit 1
fi

# Create convenience start script
echo -e "${BLUE}📝 Creating convenience start script...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
START_SCRIPT="$PROJECT_ROOT/bin/vllm/start.sh"

cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
# Start vLLM Server for Dana
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/vllm/start.sh [OPTIONS]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_MODEL="facebook/opt-125m"
DEFAULT_HOST="localhost"
DEFAULT_PORT="8000"
DEFAULT_ENV_NAME="ENV_NAME_PLACEHOLDER"

# Model selection variables
MODEL_SELECTED=""
INTERACTIVE_MODE=true

# Parse command line arguments first to check if model was specified
for arg in "$@"; do
    if [[ "$arg" == "--model" ]]; then
        INTERACTIVE_MODE=false
        break
    fi
done

show_help() {
    echo "Start vLLM Server for Dana"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --model MODEL        Model to serve (default: interactive selection)"
    echo "  --host HOST          Host to bind to (default: $DEFAULT_HOST)"
    echo "  --port PORT          Port to listen on (default: $DEFAULT_PORT)"
    echo "  --env-name NAME      vLLM environment name (default: $DEFAULT_ENV_NAME)"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Interactive Mode:"
    echo "  If no --model is specified, an interactive menu will appear"
    echo "  with curated model recommendations for different use cases."
    echo ""
    echo "Examples:"
    echo "  $0                                    # Interactive model selection"
    echo "  $0 --model microsoft/Phi-4           # Direct model specification"
    echo "  $0 --port 8080                       # Interactive + custom port"
    echo ""
    echo "Environment:"
    echo "  The script will look for vLLM installation at: ~/\$ENV_NAME/"
    echo "  Default: ~/vllm_env/"
}

show_model_menu() {
    clear
    echo -e "${BLUE}🤖 vLLM Model Selection for Dana${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo ""
    echo "Select a model category optimized for your hardware and use case:"
    echo ""
    echo -e "${GREEN}📱 macOS/CPU Optimized Models${NC}"
    echo "   1) Phi-3.5-mini (3.8B) - Microsoft's efficient model"
    echo "   2) Qwen2.5-3B - Alibaba's compact powerhouse"
    echo "   3) Gemma-2-2B - Google's lightweight model" 
    echo "   4) Llama-3.2-3B - Meta's small but capable"
    echo ""
    echo -e "${PURPLE}🚀 GPU High-Performance Models${NC}"
    echo "   5) Qwen2.5-7B-Instruct - Excellent balance (14GB VRAM)"
    echo "   6) Llama-3.1-8B-Instruct - Meta's solid choice (16GB VRAM)"
    echo "   7) Phi-4 (15B) - Microsoft's latest (30GB VRAM)"
    echo "   8) Mistral-7B-Instruct - Fast and efficient (14GB VRAM)"
    echo ""
    echo -e "${CYAN}💻 Coding Specialized Models${NC}"
    echo "   9) microsoft/Phi-4 - Excellent at code generation"
    echo "  10) bigcode/starcoder2-7b - Dedicated coding model"
    echo "  11) deepseek-ai/deepseek-coder-6.7b-instruct - Code specialist"
    echo ""
    echo -e "${YELLOW}🖼️  Vision/Multimodal Models${NC}"
    echo "  12) meta-llama/Llama-4-Scout-17B-16E-Instruct - Latest multimodal"
    echo "  13) microsoft/Phi-3.5-vision-instruct - Compact vision model"
    echo "  14) Qwen/Qwen2-VL-7B-Instruct - Excellent vision understanding"
    echo ""
    echo -e "${GREEN}🎯 Popular Recommended Models${NC}"
    echo "  15) Qwen/Qwen2.5-7B-Instruct - Best overall balance"
    echo "  16) microsoft/Phi-4 - Latest and efficient"
    echo "  17) meta-llama/Llama-3.1-8B-Instruct - Reliable choice"
    echo ""
    echo -e "${BLUE}⚙️  Custom Options${NC}"
    echo "  18) Enter custom model name"
    echo "  19) Use default (facebook/opt-125m - testing only)"
    echo ""
    echo -e "${RED}❌ Exit${NC}"
    echo "   0) Exit without starting"
    echo ""
}

get_model_selection() {
    while true; do
        show_model_menu
        echo -ne "${CYAN}Please select a model (0-19): ${NC}"
        read -r choice
        
        case $choice in
            1) MODEL_SELECTED="microsoft/Phi-3.5-mini-instruct"; break ;;
            2) MODEL_SELECTED="Qwen/Qwen2.5-3B-Instruct"; break ;;
            3) MODEL_SELECTED="google/gemma-2-2b-it"; break ;;
            4) MODEL_SELECTED="meta-llama/Llama-3.2-3B-Instruct"; break ;;
            5) MODEL_SELECTED="Qwen/Qwen2.5-7B-Instruct"; break ;;
            6) MODEL_SELECTED="meta-llama/Llama-3.1-8B-Instruct"; break ;;
            7) MODEL_SELECTED="microsoft/Phi-4"; break ;;
            8) MODEL_SELECTED="mistralai/Mistral-7B-Instruct-v0.3"; break ;;
            9) MODEL_SELECTED="microsoft/Phi-4"; break ;;
            10) MODEL_SELECTED="bigcode/starcoder2-7b"; break ;;
            11) MODEL_SELECTED="deepseek-ai/deepseek-coder-6.7b-instruct"; break ;;
            12) MODEL_SELECTED="meta-llama/Llama-4-Scout-17B-16E-Instruct"; break ;;
            13) MODEL_SELECTED="microsoft/Phi-3.5-vision-instruct"; break ;;
            14) MODEL_SELECTED="Qwen/Qwen2-VL-7B-Instruct"; break ;;
            15) MODEL_SELECTED="Qwen/Qwen2.5-7B-Instruct"; break ;;
            16) MODEL_SELECTED="microsoft/Phi-4"; break ;;
            17) MODEL_SELECTED="meta-llama/Llama-3.1-8B-Instruct"; break ;;
            18) 
                echo -ne "${CYAN}Enter custom model name (e.g., microsoft/Phi-4): ${NC}"
                read -r custom_model
                if [[ -n "$custom_model" ]]; then
                    MODEL_SELECTED="$custom_model"
                    break
                else
                    echo -e "${RED}❌ Please enter a valid model name${NC}"
                    sleep 2
                fi
                ;;
            19) MODEL_SELECTED="$DEFAULT_MODEL"; break ;;
            0) 
                echo -e "${YELLOW}👋 Goodbye!${NC}"
                exit 0 
                ;;
            *)
                echo -e "${RED}❌ Invalid selection. Please choose 0-19.${NC}"
                sleep 2
                ;;
        esac
    done
    
    echo ""
    echo -e "${GREEN}✅ Selected model: $MODEL_SELECTED${NC}"
    echo ""
}

# Parse command line arguments
MODEL="$DEFAULT_MODEL"
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
ENV_NAME="$DEFAULT_ENV_NAME"

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --env-name)
            ENV_NAME="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Show interactive model selection if no model specified
if [[ "$INTERACTIVE_MODE" == true ]]; then
    get_model_selection
    MODEL="$MODEL_SELECTED"
fi

echo -e "${BLUE}🚀 Starting vLLM Server for Dana...${NC}"
echo -e "${BLUE}📋 Configuration:${NC}"
echo "  • Model: $MODEL"
echo "  • Host: $HOST"
echo "  • Port: $PORT"
echo "  • Environment: $ENV_NAME"
echo ""

# Hardware recommendations
case $MODEL in
    *"Phi-3.5-mini"*|*"gemma-2-2b"*|*"Qwen2.5-3B"*|*"Llama-3.2-3B"*)
        echo -e "${GREEN}💡 This model is optimized for CPU/macOS and lower memory systems${NC}"
        ;;
    *"Phi-4"*|*"Qwen2.5-7B"*|*"Mistral-7B"*|*"Llama-3.1-8B"*)
        echo -e "${PURPLE}💡 This model works best with GPU (14-30GB VRAM recommended)${NC}"
        ;;
    *"vision"*|*"VL"*|*"Scout"*)
        echo -e "${YELLOW}💡 This is a multimodal model - supports both text and images${NC}"
        ;;
    *"coder"*|*"starcoder"*)
        echo -e "${CYAN}💡 This model is specialized for code generation and programming${NC}"
        ;;
esac

# Check if vLLM environment exists
VENV_PATH="$HOME/$ENV_NAME"
if [[ ! -d "$VENV_PATH" ]]; then
    echo -e "${RED}❌ Error: vLLM environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}💡 Please install vLLM first:${NC}"
    echo "   ./bin/vllm/install.sh"
    if [[ "$ENV_NAME" != "$DEFAULT_ENV_NAME" ]]; then
        echo "   ./bin/vllm/install.sh --env-name $ENV_NAME"
    fi
    exit 1
fi

# Check if activation script exists
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
if [[ ! -f "$ACTIVATE_SCRIPT" ]]; then
    echo -e "${RED}❌ Error: vLLM activation script not found at $ACTIVATE_SCRIPT${NC}"
    echo -e "${YELLOW}💡 The vLLM environment may be corrupted. Try reinstalling:${NC}"
    echo "   ./bin/vllm/install.sh"
    exit 1
fi

echo -e "${BLUE}🔌 Activating vLLM environment...${NC}"
source "$ACTIVATE_SCRIPT"

# Verify vLLM is available
if ! python -c "import vllm" 2>/dev/null; then
    echo -e "${RED}❌ Error: vLLM not found in environment${NC}"
    echo -e "${YELLOW}💡 Try reinstalling vLLM:${NC}"
    echo "   ./bin/vllm/install.sh"
    exit 1
fi

# Check if port is already in use
if command -v lsof >/dev/null && lsof -i ":$PORT" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Port $PORT is already in use${NC}"
    echo -e "${YELLOW}💡 You may want to use a different port with --port XXXX${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo -e "${GREEN}🌐 Starting vLLM OpenAI-compatible API server...${NC}"
echo -e "${BLUE}💡 Server will be available at: http://$HOST:$PORT${NC}"
echo -e "${YELLOW}📖 API docs will be at: http://$HOST:$PORT/docs${NC}"
echo -e "${YELLOW}🛑 Press Ctrl+C to stop the server${NC}"
echo ""

# Adjust parameters based on model type
EXTRA_ARGS=""
if [[ "$MODEL" == *"vision"* || "$MODEL" == *"VL"* || "$MODEL" == *"Scout"* ]]; then
    EXTRA_ARGS="--limit-mm-per-prompt '{\"image\": 5}'"
fi

# Start vLLM server with model-specific optimizations
exec python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host "$HOST" \
    --port "$PORT" \
    --dtype float16 \
    --max-model-len 2048 \
    --disable-frontend-multiprocessing \
    $EXTRA_ARGS
EOF

# Replace placeholder with actual environment name
sed -i.bak "s/ENV_NAME_PLACEHOLDER/$ENV_NAME/g" "$START_SCRIPT"
rm -f "$START_SCRIPT.bak"

# Make the start script executable
chmod +x "$START_SCRIPT"
echo -e "${GREEN}✅ Created start script: ./bin/vllm/start.sh${NC}"
echo -e "${BLUE}   Environment: $ENV_NAME${NC}"

echo ""
echo -e "${GREEN}🎉 vLLM installation completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Start vLLM server with interactive model selection (recommended):"
echo "   ./bin/vllm/start.sh"
echo "   ⭐ Choose from 19 curated models optimized for different use cases!"
echo ""
echo "2. Or start with direct model specification:"
echo "   ./bin/vllm/start.sh --model microsoft/Phi-4 --port 8080"
echo ""
echo "3. Recommended models for your system:"
echo "   • For macOS/CPU: microsoft/Phi-3.5-mini-instruct (fast & efficient)"
echo "   • For coding: microsoft/Phi-4 or deepseek-ai/deepseek-coder-6.7b-instruct"
echo "   • For vision: microsoft/Phi-3.5-vision-instruct (images + text)"
echo ""
echo "4. Test vLLM with a simple example:"
echo "   source $VENV_PATH/bin/activate"
echo "   python -c \"from vllm import LLM; print('vLLM is ready!')\""
echo ""
echo "5. Manual activation (if needed):"
echo "   source $VENV_PATH/bin/activate"
echo ""
# OS-specific installation notes
show_installation_notes() {
    echo -e "${BLUE}💡 Important Notes:${NC}"
    case "$OS_TYPE" in
        "macos")
            echo "• vLLM on macOS runs CPU-only (no GPU acceleration)"
            echo "• Only FP32 and FP16 data types are supported"
            echo "• Performance will be slower than CUDA-enabled systems"
            echo "• Multiprocessing disabled to prevent import errors on macOS"
            echo "• Consider alternatives like MLX or llama.cpp for Apple Silicon GPU acceleration"
            ;;
        "ubuntu"|"linux"|"rhel")
            if command -v nvidia-smi &> /dev/null; then
                echo "• vLLM installed with GPU support"
                echo "• CUDA acceleration available for faster inference"
                echo "• Performance will be significantly faster than CPU-only"
                echo "• Monitor GPU memory usage during inference"
            else
                echo "• vLLM installed in CPU-only mode"
                echo "• For GPU acceleration, install NVIDIA drivers and CUDA toolkit"
                echo "• Performance will be slower than GPU-enabled systems"
            fi
            echo "• FP32, FP16, and other optimizations available"
            ;;
    esac
    echo "• Installed stable version ${STABLE_VERSION} for better reliability"
}

show_installation_notes
echo ""
echo -e "${YELLOW}📚 For more information:${NC}"
echo "• vLLM Documentation: https://docs.vllm.ai/"
case "$OS_TYPE" in
    "macos")
        echo "• macOS Installation Guide: https://docs.vllm.ai/en/latest/getting_started/installation/cpu-apple.html"
        ;;
    "ubuntu"|"linux"|"rhel")
        echo "• Linux Installation Guide: https://docs.vllm.ai/en/latest/getting_started/installation.html"
        if command -v nvidia-smi &> /dev/null; then
            echo "• GPU Installation Guide: https://docs.vllm.ai/en/latest/getting_started/installation/cuda.html"
        fi
        ;;
esac
echo ""
# OS-specific installation summary
show_installation_summary() {
    echo -e "${BLUE}🗂️  Installation Details:${NC}"
    echo "• Virtual Environment: $VENV_PATH"
    echo "• vLLM Source: $VLLM_DIR"
    echo "• vLLM Version: $STABLE_VERSION (stable)"
    echo "• Start Script: ./bin/vllm/start.sh"
    echo "• Python Version: $PYTHON_VERSION"
    
    case "$OS_TYPE" in
        "macos")
            echo "• macOS Version: $MACOS_VERSION"
            ;;
        "ubuntu"|"linux")
            if [[ -n "${LINUX_DISTRO:-}" && -n "${LINUX_VERSION:-}" ]]; then
                echo "• Linux Distribution: $LINUX_DISTRO $LINUX_VERSION"
            else
                echo "• Operating System: Linux"
            fi
            if command -v nvidia-smi &> /dev/null; then
                echo "• GPU Support: Available (NVIDIA)"
            else
                echo "• GPU Support: Not available (CPU-only)"
            fi
            ;;
        "rhel")
            if [[ -n "${RHEL_VERSION:-}" ]]; then
                echo "• System: $RHEL_VERSION"
            else
                echo "• Operating System: RHEL/CentOS"
            fi
            if command -v nvidia-smi &> /dev/null; then
                echo "• GPU Support: Available (NVIDIA)"
            else
                echo "• GPU Support: Not available (CPU-only)"
            fi
            ;;
    esac
}

show_installation_summary 