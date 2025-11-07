#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting HVAC Agent Application${NC}"

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: OPENAI_API_KEY not set${NC}"
    echo -e "${YELLOW}   The application requires an OpenAI API key to function.${NC}"
    echo -e "${YELLOW}   Set it via: export OPENAI_API_KEY=your-key${NC}"
    echo -e "${YELLOW}   Or create a .env file in the project root with OPENAI_API_KEY${NC}"
fi

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo -e "${YELLOW}   Run './install.sh' first to set up the environment${NC}"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    # Kill all background jobs
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start LlamaStack server in background
echo -e "${GREEN}📦 Starting LlamaStack server...${NC}"
uv run --with llama-stack llama stack run starter > /tmp/llamastack.log 2>&1 &
LLAMASTACK_PID=$!

# Wait for LlamaStack to be ready
echo -e "${YELLOW}⏳ Waiting for LlamaStack server to start...${NC}"
sleep 5

# Check if LlamaStack is running
if ! kill -0 $LLAMASTACK_PID 2>/dev/null; then
    echo -e "${RED}❌ LlamaStack server failed to start${NC}"
    echo -e "${YELLOW}   Check logs: tail -f /tmp/llamastack.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ LlamaStack server started (PID: $LLAMASTACK_PID)${NC}"
echo -e "${BLUE}   Logs: tail -f /tmp/llamastack.log${NC}"

# Start HVAC API server in background
echo -e "${GREEN}🌐 Starting HVAC API server...${NC}"
cd "$SCRIPT_DIR"
uv run python3 api/server.py > /tmp/hvac-api.log 2>&1 &
API_PID=$!

# Wait for API to be ready
echo -e "${YELLOW}⏳ Waiting for HVAC API server to start...${NC}"
sleep 3

# Check if API is running
if ! kill -0 $API_PID 2>/dev/null; then
    echo -e "${RED}❌ HVAC API server failed to start${NC}"
    echo -e "${YELLOW}   Check logs: tail -f /tmp/hvac-api.log${NC}"
    kill $LLAMASTACK_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ HVAC API server started (PID: $API_PID) on http://localhost:8081${NC}"
echo -e "${BLUE}   Logs: tail -f /tmp/hvac-api.log${NC}"

# Start UI dev server in background
echo -e "${GREEN}🎨 Starting UI dev server...${NC}"
cd "$SCRIPT_DIR/ui"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found, running npm install...${NC}"
    npm install
fi

npm run dev > /tmp/hvac-ui.log 2>&1 &
UI_PID=$!

# Wait for UI to be ready
echo -e "${YELLOW}⏳ Waiting for UI dev server to start...${NC}"
sleep 3

# Check if UI is running
if ! kill -0 $UI_PID 2>/dev/null; then
    echo -e "${RED}❌ UI dev server failed to start${NC}"
    echo -e "${YELLOW}   Check logs: tail -f /tmp/hvac-ui.log${NC}"
    kill $LLAMASTACK_PID $API_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ UI dev server started (PID: $UI_PID) on http://localhost:5173${NC}"
echo -e "${BLUE}   Logs: tail -f /tmp/hvac-ui.log${NC}"

# Summary
echo -e "\n${GREEN}✨ All services started successfully!${NC}"
echo -e "${GREEN}   - LlamaStack: http://localhost:8080${NC}"
echo -e "${GREEN}   - HVAC API: http://localhost:8081${NC}"
echo -e "${GREEN}   - UI: http://localhost:5173${NC}"
if [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}   - OpenAI API: Configured${NC}"
else
    echo -e "${YELLOW}   - OpenAI API: Not configured (set OPENAI_API_KEY)${NC}"
fi
echo -e "\n${BLUE}💡 Press Ctrl+C to stop all services${NC}"

# Wait for all background processes
wait

