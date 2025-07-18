#!/bin/bash
# Install Dana Language Support for Vim/Neovim
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# This script sets up syntax highlighting, file type detection, and key mappings

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing Dana Language Support for Vim...${NC}"

# Detect vim vs neovim
VIM_TYPE=""
VIM_DIR=""

if command -v nvim &> /dev/null; then
    VIM_TYPE="Neovim"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        VIM_DIR="$HOME/.config/nvim"
    else
        VIM_DIR="$HOME/.config/nvim"
    fi
elif command -v vim &> /dev/null; then
    VIM_TYPE="Vim"
    VIM_DIR="$HOME/.vim"
else
    echo -e "${RED}❌ Error: Neither Vim nor Neovim is installed${NC}"
    echo -e "${YELLOW}💡 Please install one of them first:${NC}"
    echo "   - Vim: https://www.vim.org/"
    echo "   - Neovim: https://neovim.io/"
    echo "   - Or install via package manager:"
    echo "     - macOS: brew install vim or brew install neovim"
    echo "     - Ubuntu: apt install vim or apt install neovim"
    exit 1
fi

echo -e "${BLUE}📝 Detected: ${VIM_TYPE}${NC}"
echo -e "${BLUE}📁 Config directory: ${VIM_DIR}${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DANA_VIM_FILE="$SCRIPT_DIR/dana.vim"

# Check if Dana vim file exists
if [[ ! -f "$DANA_VIM_FILE" ]]; then
    echo -e "${RED}❌ Error: Dana vim file not found at $DANA_VIM_FILE${NC}"
    exit 1
fi

# Create necessary directories
mkdir -p "$VIM_DIR/syntax"
mkdir -p "$VIM_DIR/ftdetect"

# Copy syntax file
echo -e "${BLUE}📦 Installing syntax highlighting...${NC}"
cp "$DANA_VIM_FILE" "$VIM_DIR/syntax/dana.vim"

# Create file type detection
echo -e "${BLUE}🔍 Setting up file type detection...${NC}"
cat > "$VIM_DIR/ftdetect/dana.vim" << 'EOF'
" File type detection for Dana language
autocmd BufRead,BufNewFile *.na setfiletype dana
EOF

# Create backup of existing vimrc if it exists
VIMRC_FILE=""
if [[ "$VIM_TYPE" == "Neovim" ]]; then
    VIMRC_FILE="$VIM_DIR/init.vim"
else
    VIMRC_FILE="$HOME/.vimrc"
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

# Add Dana configuration to vimrc
echo -e "${BLUE}⚙️  Configuring ${VIM_TYPE}...${NC}"

# Check if Dana configuration already exists
if [[ -f "$VIMRC_FILE" ]] && grep -q "OpenDXA Dana Language Support" "$VIMRC_FILE"; then
    echo -e "${YELLOW}⚠️  Dana configuration already exists in $VIMRC_FILE${NC}"
    echo -e "${YELLOW}   Skipping vimrc modification. Remove manually if needed.${NC}"
else
    # Create backup
    if [[ -f "$VIMRC_FILE" ]]; then
        cp "$VIMRC_FILE" "$VIMRC_FILE.dana-backup"
        echo -e "${BLUE}📋 Created backup: $VIMRC_FILE.dana-backup${NC}"
    fi
    
    # Add Dana configuration
    if [[ "$LSP_AVAILABLE" == "true" ]]; then
        if [[ "$VIM_TYPE" == "Neovim" ]]; then
            # Neovim with built-in LSP
            cat >> "$VIMRC_FILE" << 'EOF'

" ===== OpenDXA Dana Language Support =====
" Auto-installed by bin/vim/install.sh

" Dana file type detection
augroup dana_filetype
  autocmd!
  autocmd BufRead,BufNewFile *.na setfiletype dana
augroup END

" Dana LSP setup (Neovim built-in LSP)
lua << LUAEOF
-- Configure Dana Language Server
require('lspconfig').configs.dana = {
  default_config = {
    cmd = {'dana-ls'},
    filetypes = {'dana'},
    root_dir = require('lspconfig.util').root_pattern('.git', 'pyproject.toml', 'setup.py'),
    settings = {},
  }
}

-- Setup Dana LSP
require('lspconfig').dana.setup{
  on_attach = function(client, bufnr)
    -- Enable completion triggered by <c-x><c-o>
    vim.api.nvim_buf_set_option(bufnr, 'omnifunc', 'v:lua.vim.lsp.omnifunc')
    
    -- LSP key mappings
    local opts = { noremap=true, silent=true }
    vim.api.nvim_buf_set_keymap(bufnr, 'n', 'gd', '<cmd>lua vim.lsp.buf.definition()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', 'K', '<cmd>lua vim.lsp.buf.hover()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<C-k>', '<cmd>lua vim.lsp.buf.signature_help()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<space>e', '<cmd>lua vim.lsp.diagnostic.show_line_diagnostics()<CR>', opts)
    
    print('Dana LSP attached successfully!')
  end,
  capabilities = require('cmp_nvim_lsp').default_capabilities(vim.lsp.protocol.make_client_capabilities()),
}
LUAEOF
EOF
        else
            # Regular Vim with vim-lsp
            cat >> "$VIMRC_FILE" << 'EOF'

" ===== OpenDXA Dana Language Support =====
" Auto-installed by bin/vim/install.sh

" Dana file type detection
augroup dana_filetype
  autocmd!
  autocmd BufRead,BufNewFile *.na setfiletype dana
augroup END

" Dana LSP setup (vim-lsp)
if executable('dana-ls')
    au User lsp_setup call lsp#register_server({
        \ 'name': 'dana-ls',
        \ 'cmd': {server_info->['dana-ls']},
        \ 'allowlist': ['dana'],
        \ })
    
    " LSP settings for Dana files
    augroup dana_lsp
        autocmd!
        autocmd FileType dana setlocal omnifunc=lsp#complete
        autocmd FileType dana nnoremap <buffer> gd <plug>(lsp-definition)
        autocmd FileType dana nnoremap <buffer> K <plug>(lsp-hover)
        autocmd FileType dana nnoremap <buffer> <C-k> <plug>(lsp-signature-help)
        autocmd FileType dana nnoremap <buffer> <space>e <plug>(lsp-document-diagnostics)
    augroup END
endif
EOF
        fi
    else
        # No LSP - basic configuration only
        cat >> "$VIMRC_FILE" << 'EOF'

" ===== OpenDXA Dana Language Support =====
" Auto-installed by bin/vim/install.sh

" Dana file type detection
augroup dana_filetype
  autocmd!
  autocmd BufRead,BufNewFile *.na setfiletype dana
augroup END
EOF
    fi

    # Common configuration for all setups
    cat >> "$VIMRC_FILE" << 'EOF'

" Dana key mappings (only for .na files)
augroup dana_mappings
  autocmd!
  autocmd FileType dana nnoremap <buffer> <F5> :!bin/dana %<CR>
  autocmd FileType dana nnoremap <buffer> <leader>dr :!bin/dana %<CR>
  autocmd FileType dana nnoremap <buffer> <leader>dc :!bin/dana --check %<CR>
  autocmd FileType dana nnoremap <buffer> <leader>dd :!bin/dana --debug %<CR>
augroup END

" Dana abbreviations (only for .na files)
augroup dana_abbreviations
  autocmd!
  autocmd FileType dana iabbrev <buffer> pub: public:
  autocmd FileType dana iabbrev <buffer> priv: private:
  autocmd FileType dana iabbrev <buffer> loc: local:
  autocmd FileType dana iabbrev <buffer> sys: system:
augroup END

" Dana settings (only for .na files)
augroup dana_settings
  autocmd!
  autocmd FileType dana setlocal expandtab tabstop=4 shiftwidth=4 softtabstop=4
  autocmd FileType dana setlocal autoindent smartindent
  autocmd FileType dana setlocal foldmethod=indent foldlevelstart=99
  autocmd FileType dana setlocal commentstring=#\ %s
augroup END

" ===== End OpenDXA Dana Language Support =====
EOF

    echo -e "${GREEN}✅ Added Dana configuration to $VIMRC_FILE${NC}"
fi

# Check if local dana CLI exists
DANA_CLI="$(cd "$SCRIPT_DIR/../.." && pwd)/bin/dana"
if [[ -x "$DANA_CLI" ]]; then
    echo -e "${GREEN}✅ Dana CLI found at $DANA_CLI${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Dana CLI not found at $DANA_CLI${NC}"
    echo -e "${YELLOW}   Make sure to run from project root or have 'dana' in PATH${NC}"
fi

echo -e "${GREEN}🎉 Dana Language Support successfully installed for ${VIM_TYPE}!${NC}"
echo ""

if [[ "$LSP_AVAILABLE" == "true" ]]; then
    echo -e "${GREEN}✅ LSP Features Enabled:${NC}"
    echo "  - Real-time syntax checking"
    echo "  - Hover documentation (K)"
    echo "  - Go-to-definition (gd)"
    echo "  - Auto-completion (<C-x><C-o>)"
    echo "  - Error diagnostics (<space>e)"
    echo ""
    if [[ "$VIM_TYPE" == "Neovim" ]]; then
        echo -e "${BLUE}💡 Neovim LSP Requirements:${NC}"
        echo "  - nvim-lspconfig plugin"
        echo "  - Optional: nvim-cmp for enhanced completion"
    else
        echo -e "${BLUE}💡 Vim LSP Requirements:${NC}"
        echo "  - vim-lsp plugin"
        echo "  - Install with: :PlugInstall prabirshrestha/vim-lsp"
    fi
else
    echo -e "${YELLOW}⚠️  Basic Dana support installed (no LSP features)${NC}"
    echo -e "${BLUE}💡 To enable LSP features:${NC}"
    echo "  1. Install dependencies: pip install lsprotocol pygls"
    echo "  2. Re-run this installer"
fi

echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Open ${VIM_TYPE}: vim or nvim"
echo "2. Create or open a .na file"
echo "3. Use F5 to run Dana code"
echo ""
echo -e "${BLUE}💡 Dana Key Mappings:${NC}"
echo "  - F5: Run current file with Dana"
echo "  - <leader>dr: Run current file with Dana"
echo "  - <leader>dc: Check current file with Dana"
echo "  - <leader>dd: Debug current file with Dana"
if [[ "$LSP_AVAILABLE" == "true" ]]; then
    echo "  - K: Hover documentation"
    echo "  - gd: Go to definition"
    echo "  - <space>e: Show diagnostics"
fi
echo ""
echo -e "${BLUE}💡 Dana Abbreviations:${NC}"
echo "  - pub: → public:"
echo "  - priv: → private:"
echo "  - loc: → local:"
echo "  - sys: → system:" 