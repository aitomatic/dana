#!/bin/bash
# Install Dana Language Support for VS Code/Cursor
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/install-vscode-extension.sh [--cursor]

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
        echo "   - Or install via brew: brew install --cask visual-studio-code"
    else
        echo "   - Download from: https://cursor.sh/"
        echo "   - Or install via brew: brew install --cask cursor"
    fi
    exit 1
fi

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EXTENSION_DIR="$PROJECT_ROOT/dana/integrations/vscode"

echo -e "${BLUE}📁 Extension directory: ${EXTENSION_DIR}${NC}"

# Check if extension directory exists
if [[ ! -d "$EXTENSION_DIR" ]]; then
    echo -e "${RED}❌ Error: Extension directory not found at ${EXTENSION_DIR}${NC}"
    exit 1
fi

# Change to extension directory
cd "$EXTENSION_DIR"

# Check if Node.js is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Error: Node.js/npm is not installed${NC}"
    echo -e "${YELLOW}💡 Please install Node.js first:${NC}"
    echo "   - Download from: https://nodejs.org/"
    echo "   - Or install via brew: brew install node"
    exit 1
fi

# Check for LSP dependencies
echo -e "${BLUE}🔍 Checking LSP dependencies...${NC}"
LSP_AVAILABLE=false
if python3 -c "import lsprotocol, pygls" 2>/dev/null; then
    LSP_AVAILABLE=true
    echo -e "${GREEN}✅ LSP dependencies available${NC}"
else
    echo -e "${YELLOW}⚠️  LSP dependencies not found. Install with: pip install lsprotocol pygls${NC}"
fi

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
npm install

# Check if vsce is installed globally
if ! command -v vsce &> /dev/null; then
    echo -e "${YELLOW}📦 Installing vsce (VS Code Extension Manager)...${NC}"
    npm install -g vsce
fi

# Compile TypeScript
echo -e "${BLUE}🔨 Compiling TypeScript...${NC}"
npm run compile

# Package extension
echo -e "${BLUE}📦 Packaging extension...${NC}"
vsce package --allow-missing-repository

# Find the generated .vsix file
VSIX_FILE=$(find . -name "*.vsix" -type f | head -n 1)

if [[ -z "$VSIX_FILE" ]]; then
    echo -e "${RED}❌ Error: No .vsix file found after packaging${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Extension packaged: ${VSIX_FILE}${NC}"

# Install the extension
echo -e "${BLUE}🔧 Installing extension in ${EDITOR_NAME}...${NC}"
$EDITOR --install-extension "$VSIX_FILE"

echo -e "${GREEN}🎉 Dana Language Support successfully installed in ${EDITOR_NAME}!${NC}"
echo ""

if [[ "$LSP_AVAILABLE" == "true" ]]; then
    echo -e "${GREEN}✅ LSP Features Enabled:${NC}"
    echo "  - Real-time syntax checking"
    echo "  - Hover documentation"
    echo "  - Auto-completion"
    echo "  - Error diagnostics"
    echo "  - Go-to-definition (coming soon)"
    echo ""
else
    echo -e "${YELLOW}⚠️  Basic Dana support installed (no LSP features)${NC}"
    echo -e "${BLUE}💡 To enable LSP features:${NC}"
    echo "  1. Install dependencies: pip install lsprotocol pygls"
    echo "  2. Restart ${EDITOR_NAME}"
    echo ""
fi

echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Open ${EDITOR_NAME}"
echo "2. Create or open a .na file"
echo "3. Press F5 to run Dana code"
echo ""
echo -e "${BLUE}💡 Dana Features in ${EDITOR_NAME}:${NC}"
echo "  - F5: Run current Dana file"
echo "  - Syntax highlighting for .na files"
if [[ "$LSP_AVAILABLE" == "true" ]]; then
    echo "  - Real-time error checking"
    echo "  - Hover help on Dana keywords"
    echo "  - Smart auto-completion"
fi
echo ""
echo -e "${BLUE}💡 Tip: Make sure 'dana' command is in your PATH${NC}"

# Check if local dana command is available
DANA_CLI="$PROJECT_ROOT/bin/dana"
if [[ -x "$DANA_CLI" ]]; then
    echo -e "${GREEN}✅ Dana CLI is available at ${DANA_CLI}${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Dana CLI not found at ${DANA_CLI}${NC}"
    echo -e "${YELLOW}   The extension will look for 'dana' in PATH when running files${NC}"
fi 
