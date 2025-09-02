# Dana Language Plugin Installation on Linux - Technical Notes

## Problem Analysis

### Current Issues Discovered
1. **Permission Error**: npm global installation fails with `EACCES: permission denied` for `/usr/local/lib/node_modules/`
2. **Node.js Version Incompatibility**: Node.js 18.x is incompatible with modern VS Code extension tooling
3. **Deprecated Tools**: Old `vsce` package is deprecated and replaced by `@vscode/vsce`
4. **Missing Dependencies**: LSP dependencies may not be available

### Root Causes
- **Permission Issue**: npm tries to install globally to system directories requiring root access
- **Version Mismatch**: Modern VS Code extension ecosystem requires Node.js 20+ due to:
  - `File` API introduced in Node.js 20
  - Dependencies like `undici`, `@azure/*`, `@secretlint/*` require Node.js 20+
  - `@vscode/vsce` and related tooling built for Node.js 20+

## Dependencies and Versions

### Required System Dependencies
```bash
# Node.js (REQUIRED: 20.x or higher)
node >= 20.0.0
npm >= 10.0.0

# Python 3 (for LSP features)
python3 >= 3.8
pip3

# LSP Python packages
lsprotocol
pygls
```

### Ubuntu Package Management Advantages
```bash
# One-command installation for most dependencies
sudo apt update
sudo apt install -y nodejs npm python3 python3-pip

# Python packages via apt (more stable than pip)
sudo apt install -y python3-lsprotocol python3-pygls

# Development tools
sudo apt install -y build-essential git curl wget

# VS Code/Cursor (if not already installed)
sudo snap install code --classic  # VS Code
sudo snap install cursor --classic # Cursor
```

### Required npm Packages
```json
{
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/vscode": "^1.85.0",
    "typescript": "^5.0.0"
  }
}
```

### Extension Tooling
```bash
# Modern VS Code Extension Manager (REQUIRED)
@vscode/vsce >= 3.0.0

# Legacy (DEPRECATED - DO NOT USE)
vsce < 3.0.0
```

## Installation Flow

### Ubuntu Quick Start (Simplified)
```bash
# Complete environment setup in 3 commands
sudo apt update
sudo apt install -y nodejs npm python3 python3-pip build-essential git
pip3 install lsprotocol pygls

# Verify installation
node --version  # Should be >= 20.0.0
npm --version   # Should be >= 10.0.0
python3 --version
```

### Phase 1: Environment Setup (Ubuntu Optimized)
1. **Install Node.js 20+**
   ```bash
   # Option A: Ubuntu official packages (RECOMMENDED for Ubuntu)
   sudo apt update
   sudo apt install -y nodejs npm

   # Option B: NodeSource repository (for latest versions)
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs

   # Option C: Using nvm (for development flexibility)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   source ~/.bashrc
   nvm install 20
   nvm use 20
   ```

2. **Configure npm for user installation**
   ```bash
   mkdir -p ~/.npm-global
   npm config set prefix '~/.npm-global'
   echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Install Python LSP dependencies**
   ```bash
   pip3 install lsprotocol pygls
   ```

### Phase 2: Extension Development
1. **Install project dependencies**
   ```bash
   cd dana/integrations/vscode
   npm install
   ```

2. **Compile TypeScript**
   ```bash
   npm run compile
   ```

### Phase 3: Extension Packaging
1. **Package extension using modern tooling**
   ```bash
   # Use npx to avoid global installation issues
   npx @vscode/vsce package --allow-missing-repository
   ```

2. **Verify package creation**
   ```bash
   # Should create .vsix file
   ls -la *.vsix
   ```

### Phase 4: Extension Installation
1. **Install in target editor**
   ```bash
   # For Cursor
   cursor --install-extension dana-language-0.1.1.vsix

   # For VS Code
   code --install-extension dana-language-0.1.1.vsix
   ```

## Implementation Strategy

### Clean Installation Script Requirements
1. **Environment Validation**
   - Check Node.js version (must be >= 20)
   - Check npm availability and configuration
   - Check Python LSP dependencies
   - Validate editor installation

2. **Dependency Management**
   - Use `npx` instead of global npm installations
   - Prefer `@vscode/vsce` over deprecated `vsce`
   - Handle LSP dependency installation gracefully

3. **Error Handling**
   - Clear error messages for version mismatches
   - Graceful fallbacks for missing dependencies
   - User-friendly installation instructions

### Script Structure
```bash
#!/bin/bash
# 1. Environment checks
# 2. Dependency validation
# 3. Extension compilation
# 4. Extension packaging
# 5. Extension installation
# 6. Post-installation verification
```

## Testing Requirements

### Pre-Installation Tests
- [ ] Node.js version >= 20
- [ ] npm accessible and configured
- [ ] Python 3 available
- [ ] LSP packages installable
- [ ] Target editor (Cursor/VS Code) installed

### Post-Installation Tests
- [ ] Extension loads without errors
- [ ] Syntax highlighting works for .na files
- [ ] LSP features functional (if dependencies available)
- [ ] F5 execution works
- [ ] No permission errors in logs

## Future Improvements

### Short-term
1. **Fix current installer** to use modern tooling
2. **Add comprehensive error handling**
3. **Implement dependency auto-installation**

### Long-term
1. **Create Linux-specific installer package**
2. **Add automated testing for Linux environments**
3. **Implement CI/CD for Linux extension builds**
4. **Create Docker development environment**

## Notes
- **Never use global npm installations** for development tools
- **Always use npx** for one-off tool execution
- **Node.js 20+ is mandatory** for modern VS Code extension development
- **LSP features are optional** but highly recommended for user experience

## Ubuntu-Specific Optimizations

### Package Manager Benefits
- **Stability**: Ubuntu packages are tested and stable
- **Security**: Automatic security updates via `apt`
- **Dependencies**: Automatic dependency resolution
- **Version Management**: Consistent versions across system

### Ubuntu vs Manual Installation
| Method | Pros | Cons |
|--------|------|------|
| **apt** | Stable, secure, easy updates | May have older versions |
| **NodeSource** | Latest versions, official | Requires adding repository |
| **nvm** | Version flexibility, user-level | More complex setup |

### Recommended Ubuntu Workflow
1. **Use apt for system packages** (nodejs, npm, python3, build tools)
2. **Use pip for Python packages** (lsprotocol, pygls) - more up-to-date
3. **Use npx for Node.js tools** (avoid global installations)
4. **Use snap for editors** (VS Code, Cursor) - auto-updates, sandboxed
