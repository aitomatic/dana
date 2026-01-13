# Dana Language Support for VS Code & Cursor

Language support for Dana AI Agent Language (.na files) in Visual Studio Code and Cursor.

## Features

- ✅ **File Association**: `.na` files are recognized as Dana language
- ✅ **Syntax Highlighting**: Keywords, strings, comments, operators, and Dana-specific constructs
- ✅ **Run Command**: Press F5 or right-click → "Run Dana File" to execute

## Installation

### Option 1: Install from VSIX (Recommended)

1. Build the extension:
   ```bash
   cd opendxa/dana/integration/vscode
   npm install
   npm run compile
   npx vsce package
   ```

2. Install in VS Code:
   ```bash
   code --install-extension dana-language-0.1.0.vsix
   ```

### Option 2: Development Mode

1. Open VS Code
2. Go to `File > Open Folder`
3. Open the `opendxa/dana/integration/vscode` folder
4. Press `F5` to launch a new VS Code window with the extension loaded

## Usage

1. **Open a Dana file**: Create or open any `.na` file
2. **Syntax highlighting**: Keywords, strings, and comments will be highlighted automatically
3. **Run Dana code**: 
   - Press `F5` while editing a `.na` file, OR
   - Right-click in the editor → "Run Dana File", OR
   - Open Command Palette (`Cmd/Ctrl+Shift+P`) → "Dana: Run Dana File"

## Requirements

- Dana CLI must be installed and available in PATH (`dana` command)
- VS Code 1.60.0 or higher

## Syntax Highlighting

The extension highlights:
- **Keywords**: `if`, `else`, `while`, `for`, `def`, `return`, etc.
- **Dana built-ins**: `reason`, `print`, `len`, `str`, etc.
- **Scopes**: `local:`, `private:`, `public:`, `system:`
- **Strings**: Single, double, and triple-quoted strings
- **Comments**: Lines starting with `#`
- **Numbers**: Integers and floats
- **Operators**: `+`, `-`, `*`, `/`, `|`, `^`, etc.

## Development

### Building

```bash
npm install
npm run compile
```

### Packaging

```bash
npm install -g vsce
vsce package
```

### Testing

1. Open this folder in VS Code
2. Press F5 to launch Extension Development Host
3. Open a `.na` file to test the extension

## Troubleshooting

**"dana command not found"**: Make sure Dana CLI is installed and in your PATH.

**Syntax highlighting not working**: Reload VS Code window (`Cmd/Ctrl+Shift+P` → "Developer: Reload Window").

**F5 not working**: Make sure you have a `.na` file open and focused in the editor.

## What's Next?

This is the minimal viable extension. Future features (only if users request):
- Error diagnostics
- Auto-completion
- Go to definition
- Debugger integration 