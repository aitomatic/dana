#!/bin/bash
# Install all dependencies for LlamaStack server, Dana API server, and Frontend UI
#
# This script installs:
# 1. Python dependencies via uv sync
# 2. API server dependencies from api/requirements.txt
# 3. LlamaStack dependencies
# 4. Frontend UI dependencies via npm install
#
# Run this before start_all.sh

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
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installing all dependencies${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Install API server dependencies
echo -e "${GREEN}[1/3] Installing API server dependencies...${NC}"
cd "$PROJECT_ROOT"
API_REQUIREMENTS="$SCRIPT_DIR/api/requirements.txt"
if [ -f "$API_REQUIREMENTS" ]; then
    if ! uv pip install -r "$API_REQUIREMENTS"; then
        echo -e "${RED}✗ Failed to install API server dependencies${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ API server dependencies installed${NC}\n"
else
    echo -e "${YELLOW}⚠ API requirements file not found at $API_REQUIREMENTS${NC}\n"
fi

# Step 3: Install LlamaStack dependencies
echo -e "${GREEN}[2/3] Installing LlamaStack dependencies...${NC}"
cd "$PROJECT_ROOT"
if ! uv run --with llama-stack llama stack list-deps starter | xargs -L1 uv pip install; then
    echo -e "${RED}✗ Failed to install LlamaStack dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ LlamaStack dependencies installed${NC}\n"

# Step 4: Install UI dependencies
echo -e "${GREEN}[3/3] Installing UI dependencies...${NC}"
cd "$SCRIPT_DIR/ui"
if ! npm install; then
    echo -e "${RED}✗ Failed to install UI dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ UI dependencies installed${NC}\n"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All dependencies installed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "You can now run ${YELLOW}./start_all.sh${NC} to start all services."

