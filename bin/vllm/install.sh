#!/bin/bash
# Install vLLM for macOS (Apple Silicon and Intel)
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

echo -e "${BLUE}🚀 Installing vLLM for macOS...${NC}"
echo -e "${YELLOW}⚠️  Note: vLLM on macOS runs CPU-only (no GPU acceleration yet)${NC}"
echo ""

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
if [[ -d "$VLLM_DIR" ]]; then
    echo -e "${YELLOW}⚠️  vLLM repository already exists at ${VLLM_DIR}${NC}"
    read -p "Do you want to update it? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}📥 Updating vLLM repository...${NC}"
        cd "$VLLM_DIR"
        git pull origin main
    else
        cd "$VLLM_DIR"
    fi
else
    echo -e "${BLUE}📥 Cloning vLLM repository...${NC}"
    git clone https://github.com/vllm-project/vllm.git "$VLLM_DIR"
    cd "$VLLM_DIR"
fi

# Install CPU requirements
echo -e "${BLUE}📦 Installing CPU requirements...${NC}"
if [[ -f "requirements-cpu.txt" ]]; then
    pip install -r requirements-cpu.txt
else
    echo -e "${YELLOW}⚠️  requirements-cpu.txt not found, installing basic requirements...${NC}"
    pip install torch torchvision torchaudio
fi

# Install vLLM in editable mode
echo -e "${BLUE}🔨 Building and installing vLLM (this may take several minutes)...${NC}"
VLLM_TARGET_DEVICE=cpu pip install -e .

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
START_SCRIPT="$PROJECT_ROOT/bin/start_vllm.sh"

cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
# Start vLLM Server for OpenDXA
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/start_vllm.sh [OPTIONS]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_MODEL="facebook/opt-125m"
DEFAULT_HOST="localhost"
DEFAULT_PORT="8000"
DEFAULT_ENV_NAME="ENV_NAME_PLACEHOLDER"

# Parse command line arguments
MODEL="$DEFAULT_MODEL"
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
ENV_NAME="$DEFAULT_ENV_NAME"

show_help() {
    echo "Start vLLM Server for OpenDXA"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --model MODEL        Model to serve (default: $DEFAULT_MODEL)"
    echo "  --host HOST          Host to bind to (default: $DEFAULT_HOST)"
    echo "  --port PORT          Port to listen on (default: $DEFAULT_PORT)"
    echo "  --env-name NAME      vLLM environment name (default: $DEFAULT_ENV_NAME)"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with defaults"
    echo "  $0 --model microsoft/DialoGPT-medium  # Use different model"
    echo "  $0 --port 8080                       # Use different port"
    echo ""
    echo "Environment:"
    echo "  The script will look for vLLM installation at: ~/\$ENV_NAME/"
    echo "  Default: ~/vllm_env/"
}

# Parse arguments
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

echo -e "${BLUE}🚀 Starting vLLM Server for OpenDXA...${NC}"
echo -e "${BLUE}📋 Configuration:${NC}"
echo "  • Model: $MODEL"
echo "  • Host: $HOST"
echo "  • Port: $PORT"
echo "  • Environment: $ENV_NAME"
echo ""

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

# Start vLLM server
exec python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host "$HOST" \
    --port "$PORT" \
    --dtype float16 \
    --max-model-len 2048
EOF

# Replace placeholder with actual environment name
sed -i.bak "s/ENV_NAME_PLACEHOLDER/$ENV_NAME/g" "$START_SCRIPT"
rm -f "$START_SCRIPT.bak"

# Make the start script executable
chmod +x "$START_SCRIPT"
echo -e "${GREEN}✅ Created start script: $START_SCRIPT${NC}"
echo -e "${BLUE}   Environment: $ENV_NAME${NC}"

echo ""
echo -e "${GREEN}🎉 vLLM installation completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Start vLLM server (recommended):"
echo "   ./bin/start_vllm.sh"
echo ""
echo "2. Or start with custom options:"
echo "   ./bin/start_vllm.sh --model microsoft/DialoGPT-medium --port 8080"
echo ""
echo "3. Test vLLM with a simple example:"
echo "   source $VENV_PATH/bin/activate"
echo "   python -c \"from vllm import LLM; print('vLLM is ready!')\""
echo ""
echo "4. Manual activation (if needed):"
echo "   source $VENV_PATH/bin/activate"
echo ""
echo -e "${BLUE}💡 Important Notes:${NC}"
echo "• vLLM on macOS runs CPU-only (no GPU acceleration)"
echo "• Only FP32 and FP16 data types are supported"
echo "• Performance will be slower than CUDA-enabled systems"
echo "• Consider alternatives like MLX or llama.cpp for Apple Silicon GPU acceleration"
echo ""
echo -e "${YELLOW}📚 For more information:${NC}"
echo "• vLLM Documentation: https://docs.vllm.ai/"
echo "• macOS Installation Guide: https://docs.vllm.ai/en/latest/getting_started/installation/cpu-apple.html"
echo ""
echo -e "${BLUE}🗂️  Installation Details:${NC}"
echo "• Virtual Environment: $VENV_PATH"
echo "• vLLM Source: $VLLM_DIR"
echo "• Start Script: ./bin/start_vllm.sh"
echo "• Python Version: $PYTHON_VERSION"
echo "• macOS Version: $MACOS_VERSION" 