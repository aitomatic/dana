#!/bin/bash
#
# uninstall.sh: Uninstalls Ollama on macOS.
#
# Usage:
#   ./bin/ollama/uninstall.sh [--yes]
#
# The script performs the following actions:
# 1. Uninstalls Ollama using 'brew uninstall ollama'.
# 2. Stops the Ollama background service.
# 3. Provides instructions to remove downloaded models.
#

set -e
set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

AUTO_CONFIRM=false
if [[ "$1" == "--yes" ]]; then
    AUTO_CONFIRM=true
fi

echo -e "${BLUE}🚀 Starting Ollama Uninstallation for macOS...${NC}"

# --- Check if Ollama is installed ---
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama is not installed. Nothing to do.${NC}"
    exit 0
fi

# --- Confirm Uninstallation ---
if [ "$AUTO_CONFIRM" = false ]; then
    read -p "Are you sure you want to uninstall Ollama? This will stop the service. (y/N): " choice
    case "$choice" in
        y|Y ) echo "Proceeding with uninstallation...";;
        * ) echo "Uninstallation cancelled."; exit 0;;
    esac
fi

# --- Stop and Uninstall Ollama Service ---
echo -e "${BLUE}🛑 Stopping and uninstalling Ollama...${NC}"
if brew list ollama &>/dev/null; then
    if ! brew uninstall ollama; then
        echo -e "${RED}❌ Failed to uninstall Ollama via Homebrew.${NC}"
        exit 1
    fi
    # On macOS, brew uninstall should handle the launchd service.
    echo -e "${GREEN}✅ Ollama uninstalled successfully.${NC}"
else
    echo -e "${YELLOW}Ollama was not installed via Homebrew. Please uninstall it manually from the Applications folder.${NC}"
fi


# --- Instruct on Model Removal ---
echo -e "\n${YELLOW}⚠️ Note on Models:${NC}"
echo -e "The uninstallation does not remove the models you have downloaded."
echo -e "To remove the models and free up disk space, delete the Ollama models directory:"
echo -e "  ${RED}rm -rf ~/.ollama/models${NC}"
echo ""
echo -e "${GREEN}🎉 Uninstallation complete.${NC}"

exit 0 