#!/bin/bash
# Uninstall vLLM for macOS/Linux
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# Usage: ./bin/vllm/uninstall.sh [--env-name ENV_NAME] [--yes]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment name
ENV_NAME="vllm_env"
AUTO_CONFIRM=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env-name)
            ENV_NAME="$2"
            shift 2
            ;;
        --yes|-y)
            AUTO_CONFIRM=true
            shift
            ;;
        --help|-h)
            echo "Uninstall vLLM for macOS/Linux"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --env-name NAME    vLLM environment name to remove (default: vllm_env)"
            echo "  --yes, -y          Skip confirmation prompts (auto-confirm all)"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Interactive uninstall"
            echo "  $0 --yes                     # Auto-confirm uninstall"
            echo "  $0 --env-name my_vllm_env    # Remove custom environment"
            echo ""
            echo "What will be removed:"
            echo "  • Virtual environment: ~/\$ENV_NAME/"
            echo "  • vLLM source code: ~/vllm/"
            echo "  • Start script: ./bin/start_vllm.sh"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🗑️  vLLM Uninstaller${NC}"
echo ""

# Define paths
VENV_PATH="$HOME/$ENV_NAME"
VLLM_DIR="$HOME/vllm"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
START_SCRIPT="$PROJECT_ROOT/bin/start_vllm.sh"

# Check what exists
items_to_remove=()
total_size=0

if [[ -d "$VENV_PATH" ]]; then
    items_to_remove+=("Virtual environment: $VENV_PATH")
    if command -v du >/dev/null; then
        size=$(du -sh "$VENV_PATH" 2>/dev/null | cut -f1)
        echo -e "${YELLOW}📁 Found virtual environment: $VENV_PATH ($size)${NC}"
    else
        echo -e "${YELLOW}📁 Found virtual environment: $VENV_PATH${NC}"
    fi
fi

if [[ -d "$VLLM_DIR" ]]; then
    items_to_remove+=("vLLM source code: $VLLM_DIR")
    if command -v du >/dev/null; then
        size=$(du -sh "$VLLM_DIR" 2>/dev/null | cut -f1)
        echo -e "${YELLOW}📁 Found vLLM source: $VLLM_DIR ($size)${NC}"
    else
        echo -e "${YELLOW}📁 Found vLLM source: $VLLM_DIR${NC}"
    fi
fi

if [[ -f "$START_SCRIPT" ]]; then
    items_to_remove+=("Start script: $START_SCRIPT")
    echo -e "${YELLOW}📄 Found start script: $START_SCRIPT${NC}"
fi

# Check if anything was found
if [[ ${#items_to_remove[@]} -eq 0 ]]; then
    echo -e "${GREEN}✅ No vLLM installation found to remove${NC}"
    echo ""
    echo "Checked locations:"
    echo "  • Virtual environment: $VENV_PATH"
    echo "  • vLLM source: $VLLM_DIR"  
    echo "  • Start script: $START_SCRIPT"
    echo ""
    echo -e "${BLUE}💡 If vLLM was installed with a different environment name, use:${NC}"
    echo "   $0 --env-name YOUR_ENV_NAME"
    exit 0
fi

echo ""
echo -e "${BLUE}📋 Items to be removed:${NC}"
for item in "${items_to_remove[@]}"; do
    echo "  • $item"
done

echo ""

# Confirmation prompt
if [[ "$AUTO_CONFIRM" == false ]]; then
    echo -e "${RED}⚠️  WARNING: This will permanently delete the above items!${NC}"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Uninstall cancelled${NC}"
        exit 0
    fi
    echo ""
fi

# Remove items
echo -e "${BLUE}🗑️  Removing vLLM installation...${NC}"

# Remove virtual environment
if [[ -d "$VENV_PATH" ]]; then
    echo -e "${BLUE}🔸 Removing virtual environment...${NC}"
    rm -rf "$VENV_PATH"
    if [[ ! -d "$VENV_PATH" ]]; then
        echo -e "${GREEN}  ✅ Virtual environment removed${NC}"
    else
        echo -e "${RED}  ❌ Failed to remove virtual environment${NC}"
        exit 1
    fi
fi

# Remove vLLM source
if [[ -d "$VLLM_DIR" ]]; then
    echo -e "${BLUE}🔸 Removing vLLM source code...${NC}"
    rm -rf "$VLLM_DIR"
    if [[ ! -d "$VLLM_DIR" ]]; then
        echo -e "${GREEN}  ✅ vLLM source removed${NC}"
    else
        echo -e "${RED}  ❌ Failed to remove vLLM source${NC}"
        exit 1
    fi
fi

# Remove start script
if [[ -f "$START_SCRIPT" ]]; then
    echo -e "${BLUE}🔸 Removing start script...${NC}"
    rm -f "$START_SCRIPT"
    if [[ ! -f "$START_SCRIPT" ]]; then
        echo -e "${GREEN}  ✅ Start script removed${NC}"
    else
        echo -e "${RED}  ❌ Failed to remove start script${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}🎉 vLLM uninstallation completed successfully!${NC}"
echo ""
echo -e "${BLUE}📝 Summary:${NC}"
echo "  • Removed virtual environment: $VENV_PATH"
echo "  • Removed vLLM source: $VLLM_DIR"
echo "  • Removed start script: $START_SCRIPT"
echo ""
echo -e "${YELLOW}💡 To reinstall vLLM:${NC}"
echo "   ./bin/vllm/install.sh"
if [[ "$ENV_NAME" != "vllm_env" ]]; then
    echo "   ./bin/vllm/install.sh --env-name $ENV_NAME"
fi
echo ""
echo -e "${BLUE}ℹ️  No system packages were modified during uninstallation${NC}" 