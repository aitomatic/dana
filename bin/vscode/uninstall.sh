#!/bin/bash
# Uninstall Dana Language Support from VS Code/Cursor
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/uninstall-vscode-extension.sh [--cursor]

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

echo -e "${BLUE}🗑️  Uninstalling Dana Language Support from ${EDITOR_NAME}...${NC}"

# Check if editor is installed
if ! command -v $EDITOR &> /dev/null; then
    echo -e "${RED}❌ Error: ${EDITOR_NAME} is not installed or not in PATH${NC}"
    exit 1
fi

# Uninstall the extension
echo -e "${BLUE}🔧 Removing extension from ${EDITOR_NAME}...${NC}"
$EDITOR --uninstall-extension aitomatic.dana-language

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Dana Language Support successfully uninstalled from ${EDITOR_NAME}!${NC}"
else
    echo -e "${YELLOW}⚠️  Extension may not have been installed or already removed${NC}"
fi

echo -e "${BLUE}💡 Note: You may need to restart ${EDITOR_NAME} for changes to take effect${NC}" 