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
EDITOR_CMD="code" # Renamed to avoid conflict if EDITOR env var is set
EDITOR_NAME="VS Code"

# Check for --cursor flag
if [[ "$1" == "--cursor" ]]; then
    EDITOR_CMD="cursor"
    EDITOR_NAME="Cursor"
fi

echo -e "${BLUE}🗑️  Uninstalling Dana Language Support from ${EDITOR_NAME}...${NC}"

# Check if editor is installed
if ! command -v "$EDITOR_CMD" &> /dev/null; then
    echo -e "${RED}❌ Error: ${EDITOR_NAME} command ('${EDITOR_CMD}') is not installed or not in PATH${NC}"
    exit 1
fi

# Expected extension ID (publisher.name)
# Publisher in package.json: "Aitomatic, Inc." (likely sanitized to 'aitomatic' or similar by vsce/vscode)
# Name in package.json: "dana-language"
EXTENSION_ID="aitomatic, inc..dana-language" # This is the most common assumed ID

echo -e "${BLUE}🔧 Attempting to remove extension '$EXTENSION_ID' from ${EDITOR_NAME}...${NC}"

# Attempt to uninstall. The `if` statement handles the exit code.
if "$EDITOR_CMD" --uninstall-extension "$EXTENSION_ID"; then
    echo -e "${GREEN}✅ Dana Language Support ('$EXTENSION_ID') successfully uninstalled from ${EDITOR_NAME}!${NC}"
else
    # The command failed (returned non-zero exit code).
    echo -e "${YELLOW}⚠️  Failed to uninstall '$EXTENSION_ID'.${NC}"
    echo -e "${YELLOW}   This can happen if the extension was not installed with this exact ID, or was already removed.${NC}"
    echo -e "${YELLOW}💡 To find the correct extension ID, please list your installed extensions:${NC}"
    echo -e "   ${EDITOR_CMD} --list-extensions | grep -i dana"
    echo -e "${YELLOW}💡 If you find it under a different ID (e.g., SomePublisher.dana-language), uninstall manually:${NC}"
    echo -e "   ${EDITOR_CMD} --uninstall-extension ACTUAL_PUBLISHER.dana-language"
    # We don't exit with an error here, as the goal is to guide the user.
    # The script will still complete.
fi

echo -e "${BLUE}💡 Note: You may need to restart ${EDITOR_NAME} for changes to take effect${NC}" 
