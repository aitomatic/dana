# Dana Language Extension Installation

Quick installation scripts for Dana Language Support in **VS Code** and **Cursor**.

Both editors are fully supported with identical features!

## 🚀 Quick Install

### macOS/Linux

**Cursor** (recommended for AI-powered development):
```bash
./bin/install-vscode-extension.sh --cursor
```

**VS Code**:
```bash
./bin/install-vscode-extension.sh
```

### Windows

**Cursor**:
```cmd
bin\install-vscode-extension.bat --cursor
```

**VS Code**:
```cmd
bin\install-vscode-extension.bat
```

## 🗑️ Uninstall

### macOS/Linux
```bash
./bin/uninstall-vscode-extension.sh --cursor # Cursor
./bin/uninstall-vscode-extension.sh          # VS Code
```

## 📋 Prerequisites

- **Node.js** - Download from [nodejs.org](https://nodejs.org/)
- **Cursor** - Download from [cursor.sh](https://cursor.sh/) ⭐ *AI-powered editor*
- **VS Code** (alternative) - Download from [code.visualstudio.com](https://code.visualstudio.com/)

**💡 Why Cursor?** Cursor is built on VS Code but adds powerful AI features that work great with Dana's neurosymbolic approach!

**Note**: The extension automatically detects and uses the local `bin/dana` CLI when you're in the Dana project, otherwise it looks for `dana` in your PATH.

## ✨ What You Get

After installation in **both Cursor and VS Code**:
- ✅ `.na` files recognized as Dana language
- ✅ Syntax highlighting for Dana code (keywords, strings, comments)
- ✅ **F5** to run Dana files instantly
- ✅ Right-click **"Run Dana File"** command
- ✅ Smart Dana CLI detection (local `bin/dana` or PATH)
- ✅ Welcome messages and helpful tips

**🎯 Perfect for**: Dana development, neurosymbolic AI experiments, and rapid prototyping!

## 🔧 Manual Installation

If the scripts don't work, you can install manually:

1. Navigate to the extension directory:
   ```bash
   cd opendxa/dana/integration/vscode
   ```

2. Install dependencies and build:
   ```bash
   npm install
   npm run compile
   npx vsce package --allow-missing-repository
   ```

3. Install the generated .vsix file:
   ```bash
   # For Cursor
   cursor --install-extension dana-language-*.vsix
   
   # For VS Code
   code --install-extension dana-language-*.vsix
   ```

## 🐛 Troubleshooting

**"dana command not found"**: 
- If working in the Dana project: Make sure `bin/dana` exists and is executable
- If working elsewhere: Make sure Dana CLI is installed and in your PATH

**"npm not found"**: Install Node.js from [nodejs.org](https://nodejs.org/).

**"cursor/code not found"**: 
- **Cursor**: Make sure it's installed and command line tools are available
- **VS Code**: Install command line tools via Command Palette → "Shell Command: Install 'code' command in PATH"

**Extension not working**: Try restarting your editor after installation.

**F5 runs wrong Dana**: The extension prioritizes `bin/dana` in the workspace root, then falls back to PATH.

**Cursor vs VS Code**: Both editors work identically - choose based on your preference for AI features!

## 📁 Files Created

The installation creates these files in your editor:
- **Cursor**: Extension files in `~/.cursor/extensions/aitomatic.dana-language-*`
- **VS Code**: Extension files in `~/.vscode/extensions/aitomatic.dana-language-*`
- No other system modifications

## 🔄 Updates

To update the extension:
1. Pull latest changes from the repository
2. Run the install script again
3. The new version will replace the old one 