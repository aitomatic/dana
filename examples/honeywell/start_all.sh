#!/bin/bash

# This script starts:
# 1. LlamaStack server (port 8321) - inference orchestration
# 2. Dana API server (port 8081) - agent API and demo UI
# 3. Frontend UI (port 5173) - React development server

# Get script directory (works when executed or sourced)
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
if command -v realpath >/dev/null 2>&1; then
    SCRIPT_DIR="$(dirname "$(realpath "$SCRIPT_PATH")")"
else
    SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
fi

PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load .env from project root
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}Loading environment variables from .env file...${NC}"
    # Export all variables from .env file
    set -a
    source "$ENV_FILE"
    set +a
    echo -e "${GREEN}✓ Loaded .env file${NC}\n"
else
    echo -e "${YELLOW}No .env file found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Create one with your OPENAI_API_KEY and other variables${NC}\n"
fi

# List everything in the env file
echo -e "${YELLOW}Variables from .env file:${NC}"
while IFS='=' read -r key value; do
    # Skip empty lines and lines beginning with #
    if [[ -z "$key" ]] || [[ "$key" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    # Hide secrets (heuristic: key contains "KEY" or "SECRET")
    if [[ "$key" =~ (KEY|SECRET) ]]; then
        echo -e "  $key=${YELLOW}[hidden]${NC}"
    else
        echo -e "  $key=$value"
    fi
done < "$ENV_FILE"
echo ""

# Create log files
LLAMASTACK_LOG="/tmp/hvac-llamastack.log"
API_LOG="/tmp/hvac-api.log"
UI_LOG="/tmp/hvac-ui.log"

# Clean up old log files
> "$LLAMASTACK_LOG"
> "$API_LOG"
> "$UI_LOG"

echo -e "${GREEN}Starting services...${NC}"
echo -e "  LlamaStack log: ${YELLOW}$LLAMASTACK_LOG${NC}"
echo -e "  API log: ${YELLOW}$API_LOG${NC}"
echo -e "  UI log: ${YELLOW}$UI_LOG${NC}"
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Initialize PID variables
LLAMASTACK_PID=""
API_PID=""
UI_PID=""

# Start LlamaStack server in background
echo -e "${GREEN}Starting LlamaStack server (port 8321)...${NC}"
if check_port 8321; then
    echo -e "${YELLOW}  Warning: Port 8321 is already in use${NC}"
else
    cd "$SCRIPT_DIR"
    nohup uv run --with llama-stack llama stack run starter > "$LLAMASTACK_LOG" 2>&1 &
    LLAMASTACK_PID=$!
    echo -e "${GREEN}  ✓ Started (PID: $LLAMASTACK_PID)${NC}"
fi

# Wait a moment for LlamaStack to initialize
sleep 2

# Start API server in background
echo -e "${GREEN}Starting API server (port 8081)...${NC}"
if check_port 8081; then
    echo -e "${YELLOW}  Warning: Port 8081 is already in use${NC}"
else
    cd "$PROJECT_ROOT"
    nohup uv run python3 examples/honeywell/api/server.py > "$API_LOG" 2>&1 &
    API_PID=$!
    echo -e "${GREEN}  ✓ Started (PID: $API_PID)${NC}"
fi

# Wait a moment for API to initialize
sleep 2

# Start UI server in background
echo -e "${GREEN}Starting UI server (port 5173)...${NC}"
if check_port 5173; then
    echo -e "${YELLOW}  Warning: Port 5173 is already in use${NC}"
else
    cd "$SCRIPT_DIR/ui"
    # Check if node_modules exists, if not, run npm install
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}  Installing UI dependencies...${NC}"
        npm install > /dev/null 2>&1
    fi
    nohup npm run dev > "$UI_LOG" 2>&1 &
    UI_PID=$!
    echo -e "${GREEN}  ✓ Started (PID: $UI_PID)${NC}"
fi

echo ""
echo -e "${GREEN}All services started!${NC}"
echo ""
echo -e "Services:"
echo -e "  ${GREEN}LlamaStack:${NC} http://localhost:8321"
echo -e "  ${GREEN}API:${NC}        http://localhost:8081"
echo -e "  ${GREEN}UI:${NC}         http://localhost:5173"
echo ""
echo -e "Log files:"
echo -e "  ${YELLOW}tail -f $LLAMASTACK_LOG${NC}"
echo -e "  ${YELLOW}tail -f $API_LOG${NC}"
echo -e "  ${YELLOW}tail -f $UI_LOG${NC}"
echo ""
if [ -n "$LLAMASTACK_PID" ] || [ -n "$API_PID" ] || [ -n "$UI_PID" ]; then
    echo -e "To stop services, run:"
    [ -n "$LLAMASTACK_PID" ] && echo -e "  ${YELLOW}kill $LLAMASTACK_PID${NC}  # LlamaStack"
    [ -n "$API_PID" ] && echo -e "  ${YELLOW}kill $API_PID${NC}  # API"
    [ -n "$UI_PID" ] && echo -e "  ${YELLOW}kill $UI_PID${NC}  # UI"
fi