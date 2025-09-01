#!/bin/bash
# Install Dana Language Support for VS Code/Cursor
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/install-vscode-extension.sh [--cursor]
# This script delegates to the new Linux installer for better reliability

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to VS Code
EDITOR="code"
EDITOR_NAME="VS Code"

# Check for --cursor flag
if [[ "$1" == "--cursor" ]]; then
    EDITOR="cursor"
    EDITOR_NAME="Cursor"
fi

echo -e "${BLUE}🚀 Installing Dana Language Support for ${EDITOR_NAME}...${NC}"

# Check if editor is installed
if ! command -v $EDITOR &> /dev/null; then
    echo -e "${RED}❌ Error: ${EDITOR_NAME} is not installed or not in PATH${NC}"
    echo -e "${YELLOW}💡 Please install ${EDITOR_NAME} first:${NC}"
    if [[ "$EDITOR" == "code" ]]; then
        echo "   - Download from: https://code.visualstudio.com/"
        echo "   - Or install via snap: sudo snap install code --classic"
    else
        echo "   - Download from: https://cursor.sh/"
        echo "   - Or install via snap: sudo snap install cursor --classic"
    fi
    exit 1
fi

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NEW_INSTALLER="$PROJECT_ROOT/dana/integrations/vscode/bin/install-on-linux"

echo -e "${BLUE}📁 Using new Linux installer: ${NEW_INSTALLER}${NC}"

# Check if new installer exists
if [[ ! -f "$NEW_INSTALLER" ]]; then
    echo -e "${RED}❌ Error: New Linux installer not found at ${NEW_INSTALLER}${NC}"
    echo -e "${YELLOW}💡 This suggests the Dana repository structure has changed${NC}"
    exit 1
fi

# Make sure the new installer is executable
chmod +x "$NEW_INSTALLER"

# Delegate to the new installer
echo -e "${BLUE}🔄 Delegating to new Linux installer...${NC}"
echo ""

# Call the new installer with appropriate arguments
if [[ "$EDITOR" == "cursor" ]]; then
    "$NEW_INSTALLER" cursor
else
    "$NEW_INSTALLER" code
fi
