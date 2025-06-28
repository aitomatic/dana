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
DEFAULT_ENV_NAME="vllm_env"

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
