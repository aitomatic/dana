#!/bin/bash
#
# install.sh: Installs Ollama on macOS using Homebrew.
#
# Usage:
#   ./bin/ollama/install.sh
#
# The script performs the following actions:
# 1. Checks for Homebrew.
# 2. Installs Ollama using 'brew install ollama'.
# 3. Verifies the installation.
#

set -e
set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Ollama Installation for macOS...${NC}"

# --- Check for Homebrew ---
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Error: Homebrew is not installed.${NC}"
    echo -e "${YELLOW}Please install Homebrew first by following the instructions at https://brew.sh/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Homebrew is installed.${NC}"

# --- Install Ollama ---
echo -e "${BLUE}📦 Installing Ollama via Homebrew...${NC}"
if brew list ollama &>/dev/null; then
    echo -e "${YELLOW}Ollama is already installed. If you face issues, consider running 'brew reinstall ollama'.${NC}"
else
    if ! brew install ollama; then
        echo -e "${RED}❌ Ollama installation failed.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Ollama installed successfully.${NC}"
fi

# --- Verify Installation ---
echo -e "${BLUE}🔍 Verifying Ollama installation...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Verification failed. 'ollama' command not found in PATH.${NC}"
    exit 1
fi

OLLAMA_VERSION=$(ollama --version)
echo -e "${GREEN}✅ Verification successful. ${OLLAMA_VERSION} is ready.${NC}"

# --- Post-installation instructions ---
echo -e "\n${BLUE}🎉 Ollama setup is complete!${NC}"
echo -e "Ollama will now run as a background service."
echo -e "You can start using it with the following commands:"
echo -e "  - To start the server and run a model: ${YELLOW}ollama run phi3${NC}"
echo -e "  - To see a list of downloaded models: ${YELLOW}ollama list${NC}"
echo -e "  - To use the custom start script: ${YELLOW}./bin/ollama/start.sh${NC}"

exit 0 