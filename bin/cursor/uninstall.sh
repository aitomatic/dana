#!/bin/bash
# Uninstall Dana Language Support from Cursor
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# This calls the VSCode uninstaller with --cursor flag

set -e

# Colors for output
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️ Uninstalling Dana Language Support from Cursor...${NC}"

# Get the directory of this script and find the VSCode uninstall script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VSCODE_SCRIPT="$SCRIPT_DIR/../vscode/uninstall.sh"

# Check if VSCode uninstall script exists
if [[ ! -f "$VSCODE_SCRIPT" ]]; then
    echo -e "${RED}❌ Error: VSCode uninstall script not found at $VSCODE_SCRIPT${NC}"
    exit 1
fi

# Call the VSCode uninstall script with --cursor flag
exec "$VSCODE_SCRIPT" --cursor
