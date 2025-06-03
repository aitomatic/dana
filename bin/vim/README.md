<!--
⚠️ IMPORTANT FOR AI CODE GENERATORS:
Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
NEVER use dot notation: `private.x`, `public.x`, etc.
Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.
-->

<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# Dana Language Support for Vim/Neovim

Complete Dana language integration for Vim and Neovim with syntax highlighting, file type detection, key mappings, and intelligent abbreviations.

## 🚀 Quick Install

### Automatic Installation
```bash
./bin/vim/install.sh
```

This script automatically:
- ✅ Detects Vim vs Neovim
- ✅ Installs syntax highlighting
- ✅ Sets up file type detection
- ✅ Configures key mappings
- ✅ Adds helpful abbreviations
- ✅ Creates backups of existing config

## 🗑️ Uninstall

### Complete Removal
```bash
./bin/vim/uninstall.sh
```

This safely removes all Dana configuration while preserving backups.

## 📋 Prerequisites

**One of these editors:**
- **Vim** - Download from [vim.org](https://www.vim.org/) 
- **Neovim** - Download from [neovim.io](https://neovim.io/) ⭐ *Recommended*

**Installation options:**
```bash
# macOS
brew install vim        # or brew install neovim
brew install neovim     # Recommended

# Ubuntu/Debian
apt install vim         # or apt install neovim
apt install neovim      # Recommended

# Other platforms
# See respective websites for installation instructions
```

## ✨ Features

- **🎨 Syntax Highlighting**: Complete syntax highlighting for Dana language
  - Keywords: `if`, `elif`, `else`, `while`, `for`, `def`, `try`, `except`, `finally`, `import`, `from`, `as`, etc.
  - Scope prefixes: `private:`, `public:`, `local:`, `system:`
  - Built-in types: `int`, `float`, `str`, `bool`, `list`, `dict`, `tuple`, `set`, `any`
  - Python built-ins: `len`, `sum`, `max`, `min`, `abs`, `round`, `sorted`, `type`, etc.
  - String literals: regular strings, f-strings, raw strings, multiline strings
  - Numbers, operators, comments, and more

- **🗂️ File Type Detection**: Automatic `.na` file recognition
- **⌨️ Key Mappings**: Convenient shortcuts for Dana development
  - `F5`: Run current Dana file
  - `<leader>dr`: Run current Dana file
  - `<leader>dc`: Check current Dana file with validation
  - `<leader>dd`: Debug current Dana file
- **⚡ Smart Abbreviations**: Quick typing shortcuts
  - `pub:` → `public:`
  - `priv:` → `private:`
  - `loc:` → `local:`
  - `sys:` → `system:`
- **📝 Proper Indentation**: 4-space indentation with smart auto-indent
- **📁 Code Folding**: Indent-based folding for better code organization

## 🔧 Manual Installation

If the automatic script doesn't work:

### 1. Copy Syntax File
```bash
# For Vim
mkdir -p ~/.vim/syntax
cp bin/vim/dana.vim ~/.vim/syntax/

# For Neovim  
mkdir -p ~/.config/nvim/syntax
cp bin/vim/dana.vim ~/.config/nvim/syntax/
```

### 2. Set Up File Type Detection
```bash
# For Vim
mkdir -p ~/.vim/ftdetect
echo 'autocmd BufRead,BufNewFile *.na setfiletype dana' > ~/.vim/ftdetect/dana.vim

# For Neovim
mkdir -p ~/.config/nvim/ftdetect  
echo 'autocmd BufRead,BufNewFile *.na setfiletype dana' > ~/.config/nvim/ftdetect/dana.vim
```

### 3. Add Configuration
Add the Dana configuration block from `install.sh` to your `.vimrc` or `init.vim`.

## 🐛 Troubleshooting

**"dana command not found"**:
- Make sure you're running from the OpenDXA project root
- Or ensure `dana` is in your PATH
- The key mappings use `bin/dana` relative to current directory

**"Syntax highlighting not working"**:
- Check file type with `:set filetype?` - should show `dana`
- Manually set with `:set filetype=dana`
- Ensure `.na` file extension is being used

**"Key mappings not working"**:
- Mappings only work for `.na` files with Dana filetype
- Check your leader key setting (default is `\`)
- Try `:map <F5>` to see current F5 mapping

**"Installation script fails"**:
- Ensure you have write permissions to vim config directories
- Check if vim/neovim is properly installed: `vim --version` or `nvim --version`

**"Neovim vs Vim detection issues"**:
- Script prioritizes Neovim if both are installed
- Uses `~/.config/nvim/init.vim` for Neovim
- Uses `~/.vimrc` for Vim

## 📁 Files Created/Modified

**Syntax & Detection:**
- `~/.vim/syntax/dana.vim` or `~/.config/nvim/syntax/dana.vim`
- `~/.vim/ftdetect/dana.vim` or `~/.config/nvim/ftdetect/dana.vim`

**Configuration:**
- `~/.vimrc` (Vim) or `~/.config/nvim/init.vim` (Neovim)

**Backups:**
- `~/.vimrc.dana-backup` or `~/.config/nvim/init.vim.dana-backup`

## 🔄 Updates

To update Dana language support:
1. Pull latest changes from repository
2. Run `./bin/vim/install.sh` again
3. Existing configuration will be updated automatically

## 💡 Tips & Best Practices

**Leader Key:**
- Default leader is `\` - consider setting to `,` or `<space>`:
  ```vim
  let mapleader = ","      " or let mapleader = "\<space>"
  ```

**Enhanced Dana Development:**
- Use `:set number` for line numbers
- Enable `:set cursorline` for current line highlighting  
- Consider `:set list` to see whitespace characters

**Working with Multiple Files:**
- Use `:args *.na` to load all Dana files
- Use `:bufdo %s/pattern/replacement/g` for project-wide replacements
- Use tags or LSP for code navigation (future enhancement)

## 🚀 What's Next?

Future enhancements planned:
- LSP integration for code completion and navigation
- Better indentation rules specific to Dana constructs
- Snippet support for common Dana patterns
- Integration with Dana REPL for interactive development

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 