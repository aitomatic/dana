#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Installing HVAC Agent Application${NC}"

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo -e "${BLUE}📁 Project root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}📁 Script directory: $SCRIPT_DIR${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed${NC}"
    echo -e "${YELLOW}   Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ uv found${NC}"

# Step 1: Set up uv environment from root
echo -e "\n${GREEN}📦 Step 1: Setting up uv environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}   Creating virtual environment...${NC}"
    uv venv
fi

echo -e "${YELLOW}   Syncing dependencies...${NC}"
uv sync

echo -e "${GREEN}✅ uv environment ready${NC}"

# Step 2: Install llamastack starter dependencies
echo -e "\n${GREEN}📦 Step 2: Installing LlamaStack starter dependencies...${NC}"

# First ensure llama-stack is installed
echo -e "${YELLOW}   Installing llama-stack and dana...${NC}"
uv pip install llama-stack dana

# Install llamastack starter dependencies
echo -e "${YELLOW}   Installing LlamaStack starter distribution...${NC}"
if llama stack list-deps starter 2>/dev/null | xargs -L1 uv pip install; then
    echo -e "${GREEN}✅ LlamaStack starter dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Some LlamaStack dependencies may not be available${NC}"
fi

# Step 3: Install UI requirements
echo -e "\n${GREEN}📦 Step 3: Installing UI requirements...${NC}"

UI_DIR="$SCRIPT_DIR/ui"
if [ ! -d "$UI_DIR" ]; then
    echo -e "${RED}❌ UI directory not found: $UI_DIR${NC}"
    exit 1
fi

cd "$UI_DIR"

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo -e "${YELLOW}   Please install Node.js 18+ to continue${NC}"
    exit 1
fi

echo -e "${YELLOW}   Installing npm dependencies...${NC}"
npm install

echo -e "${GREEN}✅ UI dependencies installed${NC}"

# Summary
echo -e "\n${GREEN}✨ Installation complete!${NC}"
echo -e "${BLUE}   Run './start.sh' to start all services${NC}"

