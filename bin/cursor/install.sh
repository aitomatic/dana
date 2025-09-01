#!/bin/bash
# Install Dana Language Support for Cursor
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# This calls the VSCode installer with --cursor flag

set -e

# Colors for output
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Installing Dana Language Support for Cursor...${NC}"

# Get the directory of this script and find the VSCode install script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VSCODE_SCRIPT="$SCRIPT_DIR/../vscode/install.sh"

# Check if VSCode install script exists
if [[ ! -f "$VSCODE_SCRIPT" ]]; then
    echo -e "${RED}❌ Error: VSCode install script not found at $VSCODE_SCRIPT${NC}"
    exit 1
fi

# Call the VSCode install script with --cursor flag
exec "$VSCODE_SCRIPT" --cursor
