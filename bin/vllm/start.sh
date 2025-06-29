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
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_MODEL="facebook/opt-125m"
DEFAULT_HOST="localhost"
DEFAULT_PORT="8000"
DEFAULT_ENV_NAME="vllm_env"

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
    echo "Start vLLM Server for OpenDXA"
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
    echo -e "${BLUE}🤖 vLLM Model Selection for OpenDXA${NC}"
    echo -e "${BLUE}════════════════════════════════════${NC}"
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

echo -e "${BLUE}🚀 Starting vLLM Server for OpenDXA...${NC}"
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
