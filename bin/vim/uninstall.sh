#!/bin/bash
# Uninstall Dana Language Support from Vim/Neovim
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# This script removes syntax files, file type detection, and configuration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️ Uninstalling Dana Language Support from Vim...${NC}"

# Detect vim vs neovim
VIM_TYPE=""
VIM_DIR=""

if command -v nvim &> /dev/null; then
    VIM_TYPE="Neovim"
    VIM_DIR="$HOME/.config/nvim"
elif command -v vim &> /dev/null; then
    VIM_TYPE="Vim"
    VIM_DIR="$HOME/.vim"
else
    echo -e "${YELLOW}⚠️  Neither Vim nor Neovim detected${NC}"
    echo -e "${BLUE}   Checking common configuration locations anyway...${NC}"
    VIM_TYPE="Unknown"
    VIM_DIR="$HOME/.vim"
fi

echo -e "${BLUE}📝 Target: ${VIM_TYPE}${NC}"
echo -e "${BLUE}📁 Config directory: ${VIM_DIR}${NC}"

# Remove syntax file
SYNTAX_FILE="$VIM_DIR/syntax/dana.vim"
if [[ -f "$SYNTAX_FILE" ]]; then
    echo -e "${BLUE}🗑️ Removing syntax file: $SYNTAX_FILE${NC}"
    rm "$SYNTAX_FILE"
    echo -e "${GREEN}✅ Removed syntax file${NC}"
else
    echo -e "${YELLOW}⚠️  Syntax file not found: $SYNTAX_FILE${NC}"
fi

# Remove file type detection
FTDETECT_FILE="$VIM_DIR/ftdetect/dana.vim"
if [[ -f "$FTDETECT_FILE" ]]; then
    echo -e "${BLUE}🗑️ Removing file type detection: $FTDETECT_FILE${NC}"
    rm "$FTDETECT_FILE"
    echo -e "${GREEN}✅ Removed file type detection${NC}"
else
    echo -e "${YELLOW}⚠️  File type detection not found: $FTDETECT_FILE${NC}"
fi

# Remove configuration from vimrc
VIMRC_FILE=""
VIMRC_NEOVIM="$HOME/.config/nvim/init.vim"
VIMRC_VIM="$HOME/.vimrc"

# Check both possible locations
for VIMRC_CANDIDATE in "$VIMRC_NEOVIM" "$VIMRC_VIM"; do
    if [[ -f "$VIMRC_CANDIDATE" ]] && grep -q "OpenDXA Dana Language Support" "$VIMRC_CANDIDATE"; then
        VIMRC_FILE="$VIMRC_CANDIDATE"
        break
    fi
done

if [[ -n "$VIMRC_FILE" ]]; then
    echo -e "${BLUE}🗑️ Removing Dana configuration from: $VIMRC_FILE${NC}"
    
    # Create backup before modification
    cp "$VIMRC_FILE" "$VIMRC_FILE.pre-dana-uninstall"
    echo -e "${BLUE}📋 Created backup: $VIMRC_FILE.pre-dana-uninstall${NC}"
    
    # Remove Dana configuration block
    sed -i.bak '/^" ===== OpenDXA Dana Language Support =====/,/^" ===== End OpenDXA Dana Language Support =====/d' "$VIMRC_FILE"
    
    # Remove the backup file created by sed
    rm "$VIMRC_FILE.bak" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Removed Dana configuration from $VIMRC_FILE${NC}"
    
    # Check if there's a backup available for restoration
    BACKUP_FILE="$VIMRC_FILE.dana-backup"
    if [[ -f "$BACKUP_FILE" ]]; then
        echo -e "${BLUE}📋 Original backup found: $BACKUP_FILE${NC}"
        echo -e "${YELLOW}   You can restore it manually if needed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No Dana configuration found in vimrc files${NC}"
    echo -e "${BLUE}   Checked: $VIMRC_NEOVIM and $VIMRC_VIM${NC}"
fi

# Check for empty directories and remove them
for DIR in "$VIM_DIR/syntax" "$VIM_DIR/ftdetect"; do
    if [[ -d "$DIR" ]] && [[ -z "$(ls -A "$DIR" 2>/dev/null)" ]]; then
        echo -e "${BLUE}🗑️ Removing empty directory: $DIR${NC}"
        rmdir "$DIR" 2>/dev/null || true
    fi
done

echo -e "${GREEN}🎉 Dana Language Support successfully uninstalled!${NC}"
echo ""
echo -e "${YELLOW}📝 What was removed:${NC}"
echo "  - Syntax highlighting file"
echo "  - File type detection"
echo "  - Key mappings and abbreviations"
echo "  - Dana-specific settings"
echo ""
echo -e "${BLUE}💡 Backups created:${NC}"
if [[ -n "$VIMRC_FILE" ]]; then
    echo "  - $VIMRC_FILE.pre-dana-uninstall"
fi
if [[ -f "$VIMRC_FILE.dana-backup" ]]; then
    echo "  - $VIMRC_FILE.dana-backup (from installation)"
fi
echo ""
echo -e "${BLUE}💡 To completely clean up, you can remove backup files manually${NC}" 