<!--
⚠️ IMPORTANT FOR AI CODE GENERATORS:
Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
NEVER use dot notation: `private.x`, `public.x`, etc.
Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.
-->

<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# Dana Language Extension for VS Code

Quick installation scripts for Dana Language Support in **VS Code**.

## 🚀 Quick Install

### macOS/Linux
```bash
./bin/vscode/install.sh
```

### Windows
```cmd
bin\vscode\install.bat
```

## 🗑️ Uninstall

### macOS/Linux
```bash
./bin/vscode/uninstall.sh
```

## 📋 Prerequisites

- **Node.js** - Download from [nodejs.org](https://nodejs.org/)
- **VS Code** - Download from [code.visualstudio.com](https://code.visualstudio.com/)

**Note**: The extension automatically detects and uses the local `bin/dana` CLI when you're in the Dana project, otherwise it looks for `dana` in your PATH.

## ✨ What You Get

After installation:
- ✅ `.na` files recognized as Dana language
- ✅ Syntax highlighting for Dana code (keywords, strings, comments)
- ✅ **F5** to run Dana files instantly
- ✅ Right-click **"Run Dana File"** command
- ✅ Smart Dana CLI detection (local `bin/dana` or PATH)
- ✅ Welcome messages and helpful tips

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
   code --install-extension dana-language-*.vsix
   ```

## 🐛 Troubleshooting

**"dana command not found"**: 
- If working in the Dana project: Make sure `bin/dana` exists and is executable
- If working elsewhere: Make sure Dana CLI is installed and in your PATH

**"npm not found"**: Install Node.js from [nodejs.org](https://nodejs.org/).

**"code not found"**: Install command line tools via Command Palette → "Shell Command: Install 'code' command in PATH"

**Extension not working**: Try restarting VS Code after installation.

**F5 runs wrong Dana**: The extension prioritizes `bin/dana` in the workspace root, then falls back to PATH.

## 📁 Files Created

The installation creates extension files in `~/.vscode/extensions/aitomatic.dana-language-*`

No other system modifications are made.

## 🔄 Updates

To update the extension:
1. Pull latest changes from the repository
2. Run the install script again
3. The new version will replace the old one

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 