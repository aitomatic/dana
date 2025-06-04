<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA Development Tools

This directory contains development tools and utilities for OpenDXA.

## 📂 Directory Structure

```
bin/
├── dana*              # Main Dana CLI executable
├── dana-cat*          # View Dana files with syntax highlighting
├── dana-less*         # Page through Dana files with syntax highlighting
├── cursor/            # Cursor editor integration
│   ├── install.sh     # Install Dana extension for Cursor (macOS/Linux)
│   ├── install.bat    # Install Dana extension for Cursor (Windows)
│   ├── uninstall.sh   # Uninstall Dana extension from Cursor (macOS/Linux)
│   ├── uninstall.bat  # Uninstall Dana extension from Cursor (Windows)
│   └── README.md      # Cursor-specific documentation
├── vim/               # Vim/Neovim editor integration
│   ├── install.sh     # Install Dana support for Vim/Neovim (macOS/Linux)
│   ├── uninstall.sh   # Uninstall Dana support from Vim/Neovim (macOS/Linux)
│   ├── dana.vim       # Dana language syntax file
│   └── README.md      # Vim-specific documentation
└── vscode/            # VS Code editor integration
    ├── install.sh     # Install Dana extension for VS Code (macOS/Linux)
    ├── install.bat    # Install Dana extension for VS Code (Windows)
    ├── uninstall.sh   # Uninstall Dana extension from VS Code (macOS/Linux)
    └── README.md      # VS Code-specific documentation
```

## 🚀 Quick Start

### Dana CLI
```bash
# Run Dana REPL
./bin/dana

# Run a Dana file
./bin/dana path/to/file.na

# View Dana files with syntax highlighting
./bin/dana-cat path/to/file.na

# Page through Dana files with syntax highlighting
./bin/dana-less path/to/file.na
```

### Editor Extensions

**For Cursor users (recommended for AI-powered development):**
```bash
# macOS/Linux
./bin/cursor/install.sh

# Windows
bin\cursor\install.bat
```

**For Vim/Neovim users (terminal-based editing):**
```bash
# macOS/Linux (auto-detects Vim vs Neovim)
./bin/vim/install.sh
```

**For VS Code users:**
```bash
# macOS/Linux
./bin/vscode/install.sh

# Windows
bin\vscode\install.bat
```

## 📚 Documentation

- **Cursor Integration**: See [`cursor/README.md`](cursor/README.md)
- **Vim/Neovim Integration**: See [`vim/README.md`](vim/README.md)
- **VS Code Integration**: See [`vscode/README.md`](vscode/README.md)
- **Dana CLI**: See main project documentation

## 🔧 What's Included

### Dana CLI (`dana`)
- Interactive REPL for Dana language
- File execution and debugging
- Integration with OpenDXA framework

### Command-Line Tools
- **`dana-cat`** - View Dana files with syntax highlighting (uses bat/pygments)
- **`dana-less`** - Page through Dana files with syntax highlighting

### Editor Extensions
Both Cursor and VS Code extensions provide:
- ✅ Dana language syntax highlighting
- ✅ F5 to run Dana files
- ✅ Right-click "Run Dana File" command
- ✅ Smart CLI detection (local `bin/dana` or PATH)

Vim/Neovim integration provides:
- ✅ Complete syntax highlighting for Dana language
- ✅ File type detection for `.na` files
- ✅ F5 and leader key mappings to run Dana code
- ✅ Smart abbreviations for common Dana patterns
- ✅ Proper indentation and folding

### Why Separate Directories?

We've organized editor tools into separate directories for:
- **Clarity**: Each editor has its own focused documentation and scripts
- **Maintenance**: Easier to update editor-specific features
- **User Experience**: Simpler installation commands without flags
- **Organization**: Clean separation of concerns

## 💡 Migration from Old Structure

If you previously used scripts from `bin/vscode-cursor/`, the new equivalent commands are:

| Old Command | New Command |
|-------------|-------------|
| `./bin/vscode-cursor/install-vscode-extension.sh` | `./bin/vscode/install.sh` |
| `./bin/vscode-cursor/install-vscode-extension.sh --cursor` | `./bin/cursor/install.sh` |
| `./bin/vscode-cursor/install-cursor-extension.sh` | `./bin/cursor/install.sh` |

The old directory is deprecated and will be removed in a future version.

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 
