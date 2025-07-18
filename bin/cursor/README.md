<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# Dana Language Extension for Cursor

Quick installation scripts for Dana Language Support in **Cursor** - the AI-powered code editor.

## 🚀 Quick Install

### macOS/Linux
```bash
./bin/cursor/install.sh
```

### Windows
```cmd
bin\cursor\install.bat
```

## 🗑️ Uninstall

### macOS/Linux
```bash
./bin/cursor/uninstall.sh
```

### Windows
```cmd
bin\cursor\uninstall.bat
```

## 📋 Prerequisites

- **Node.js** - Download from [nodejs.org](https://nodejs.org/)
- **Cursor** - Download from [cursor.sh](https://cursor.sh/) ⭐ *AI-powered editor built on VS Code*

**💡 Why Cursor?** Cursor is built on VS Code but adds powerful AI features that work great with Dana's neurosymbolic approach!

**Note**: The extension automatically detects and uses the local `bin/dana` CLI when you're in the Dana project, otherwise it looks for `dana` in your PATH.

## ✨ What You Get

After installation in Cursor:
- ✅ `.na` files recognized as Dana language
- ✅ Syntax highlighting for Dana code (keywords, strings, comments)
- ✅ **F5** to run Dana files instantly
- ✅ Right-click **"Run Dana File"** command
- ✅ Smart Dana CLI detection (local `bin/dana` or PATH)
- ✅ Welcome messages and helpful tips
- ✅ **Perfect integration with Cursor's AI features** for Dana development!

**🎯 Perfect for**: Dana development, neurosymbolic AI experiments, and rapid prototyping with AI assistance!

## 🔧 Manual Installation

If the scripts don't work, you can install manually:

1. Navigate to the extension directory:
   ```bash
   cd dana/integrations/vscode
   ```

2. Install dependencies and build:
   ```bash
   npm install
   npm run compile
   npx vsce package --allow-missing-repository
   ```

3. Install the generated .vsix file:
   ```bash
   cursor --install-extension dana-language-*.vsix
   ```

## 🐛 Troubleshooting

**"dana command not found"**: 
- If working in the Dana project: Make sure `bin/dana` exists and is executable
- If working elsewhere: Make sure Dana CLI is installed and in your PATH

**"npm not found"**: Install Node.js from [nodejs.org](https://nodejs.org/).

**"cursor not found"**: 
- Make sure Cursor is installed and command line tools are available
- Download from [cursor.sh](https://cursor.sh/)

**Extension not working**: Try restarting Cursor after installation.

**F5 runs wrong Dana**: The extension prioritizes `bin/dana` in the workspace root, then falls back to PATH.

## 📁 Files Created

The installation creates extension files in `~/.cursor/extensions/aitomatic.dana-language-*`

No other system modifications are made.

## 🔄 Updates

To update the extension:
1. Pull latest changes from the repository
2. Run the install script again
3. The new version will replace the old one

## 🤖 AI-Powered Development

Cursor's AI features work great with Dana:
- **AI-assisted code completion** for Dana syntax
- **Context-aware suggestions** that understand neurosymbolic patterns
- **Natural language to Dana code** conversion
- **Intelligent debugging** assistance 

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 
