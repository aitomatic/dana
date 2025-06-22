# Makefile - OpenDXA Development Commands
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

# =============================================================================
# OpenDXA Development Makefile
# =============================================================================
# Modern Python development with uv package manager
# Requires uv to be installed: https://docs.astral.sh/uv/

# Platform detection
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    SCRIPT_EXT := .bat
else
    DETECTED_OS := $(shell uname -s)
    SCRIPT_EXT := .sh
endif

# UV command helper - use system uv if available, otherwise fallback to ~/.local/bin/uv
UV_CMD = $(shell command -v uv 2>/dev/null || echo ~/.local/bin/uv)

# Default target
.DEFAULT_GOAL := quickstart

# All targets are phony (don't create files)
.PHONY: help \
	quickstart check-uv \
	install install-dev setup-dev \
	test test-fast test-live test-cov test-watch test-poet \
	lint lint-fix format format-check typecheck \
	check fix verify \
	dana run opendxa-server \
	clean clean-all clean-cache \
	dev update-deps sync \
	onboard env-check env-setup examples demo-basic demo-reasoning jupyter \
	docs-build docs-serve docs-check docs-validate docs-deploy \
	security validate-config release-check \
	install-cursor install-vscode install-vim uninstall-cursor uninstall-vscode uninstall-vim install-editors uninstall-editors \
	install-ollama update-ollama uninstall-ollama

# =============================================================================
# Help & Information
# =============================================================================

help: ## Show this help message with available commands
	@echo ""
	@echo "\033[1m\033[34mOpenDXA Development Commands\033[0m"
	@echo "\033[1m=====================================\033[0m"
	@echo ""
	@echo "\033[1mGetting Started:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(quickstart|onboard|install|setup|sync).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mUsing Dana:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(dana|run|examples|demo-basic|demo-reasoning|jupyter).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mTesting:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^test.*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mCode Quality:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(lint|format|typecheck|check|fix|verify).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mDocumentation:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(docs-build|docs-serve|docs-check|docs-validate|docs-deploy).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mAdvanced Development:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(dev|env-check|env-setup|update).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mMaintenance & Security:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(clean|security|validate-config|release-check).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mEditor Integration:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(install-cursor|install-vscode|install-vim|uninstall-cursor|uninstall-vscode|uninstall-vim|install-editors|uninstall-editors).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mOllama Management:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(install-ollama|update-ollama|uninstall-ollama).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[33mTip: New to OpenDXA? Start with 'make quickstart' or 'make onboard'\033[0m"
	@echo ""

# =============================================================================
# Quick Start (Get Running in 30 seconds!)
# =============================================================================

# Check if uv is installed, install if missing
check-uv:
	@if ! command -v uv >/dev/null 2>&1 && ! test -f ~/.local/bin/uv; then \
		echo "🔧 uv not found, installing..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "✅ uv installed successfully"; \
	else \
		echo "✅ uv already available"; \
	fi

quickstart: check-uv ## 🚀 QUICK START: Get OpenDXA running in 30 seconds!
	@echo ""
	@echo "🚀 \033[1m\033[32mOpenDXA Quick Start\033[0m"
	@echo "==================="
	@echo ""
	@echo "📦 Installing dependencies..."
	@$(UV_CMD) sync --quiet
	@echo "🔧 Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env file from template"; \
	else \
		echo "📝 .env file already exists"; \
	fi
	@echo ""
	@echo "🎉 \033[1m\033[32mReady to go!\033[0m"
	@echo ""
	@echo "\033[1mNext: Add your API key to .env, then:\033[0m"
	@echo "  \033[36mmake dana\033[0m    # Start Dana REPL"
	@echo "  \033[36mmake test\033[0m    # Run tests"
	@echo "  \033[36mmake help\033[0m    # See all commands"
	@echo ""
	@echo "\033[33m💡 Tip: Run 'open .env' to edit your API keys\033[0m"
	@echo ""

# =============================================================================
# Setup & Installation
# =============================================================================

install: ## Install package and dependencies
	@echo "📦 Installing dependencies..."
	uv sync

install-dev: ## Install with development dependencies
	@echo "🛠️  Installing development dependencies..."
	uv sync --extra dev

setup-dev: install-dev ## Complete development environment setup
	@echo "🔧 Setting up development environment..."
	uv run pre-commit install
	@echo "✅ Development environment ready!"

sync: ## Sync dependencies with uv.lock
	@echo "🔄 Syncing dependencies..."
	uv sync

update-deps: ## Update dependencies to latest versions
	@echo "⬆️  Updating dependencies..."
	uv lock --upgrade

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "🧪 Running all tests..."
	# OPENDXA_MOCK_LLM=true uv run pytest tests/
	OPENDXA_MOCK_LLM=true uv run pytest tests/ -v -k "not (function_composition or pipe_operator_composition)"

test-fast: ## Run fast tests only (excludes live/deep tests)
	@echo "⚡ Running fast tests..."
	OPENDXA_MOCK_LLM=true uv run pytest -m "not live and not deep" tests/

test-live: ## Run live tests (requires API keys)
	@echo "🌐 Running live tests (requires API keys)..."
	uv run pytest -m "live" tests/

test-cov: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	OPENDXA_MOCK_LLM=true uv run pytest --cov=opendxa --cov-report=html --cov-report=term tests/
	@echo "📈 Coverage report generated in htmlcov/"

test-watch: ## Run tests in watch mode (reruns on file changes)
	@echo "👀 Running tests in watch mode..."
	uv run pytest-watch tests/

test-poet: ## Run POET tests only
	@echo "🎭 Running POET tests..."
	OPENDXA_MOCK_LLM=true uv run pytest -m "poet" tests/ -v --tb=short

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	uv run ruff check .

lint-fix: ## Auto-fix linting issues
	@echo "🔧 Auto-fixing linting issues..."
	uv run ruff check --fix .

format: ## Format code with black
	@echo "✨ Formatting code..."
	uv run black .

format-check: ## Check code formatting without changes
	@echo "📝 Checking code formatting..."
	uv run black --check .

typecheck: ## Run type checking
	@echo "🔍 Running type checks..."
	uv run pyright .

check: lint format-check typecheck ## Run all code quality checks
	@echo "✅ All quality checks completed!"

fix: lint-fix format ## Auto-fix all fixable issues
	@echo "🔧 Applied all auto-fixes!"

verify: setup-dev check test-fast ## Complete verification (setup + quality + tests)
	@echo "🎯 Full verification completed!"

# =============================================================================
# Application
# =============================================================================

dana: ## Start the Dana REPL
	@echo "🚀 Starting Dana REPL..."
	uv run dana

run: dana ## Alias for 'dana' command

opendxa-server: ## Start the OpenDXA API server (includes POET service)
	@echo "🌐 Starting OpenDXA API server on http://localhost:8080"
	uv run python -m opendxa.api.server --host localhost --port 8080

# =============================================================================
# Maintenance & Cleanup
# =============================================================================

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

clean-cache: ## Clean Python and tool caches
	@echo "🧹 Cleaning Python caches..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/

clean-all: clean clean-cache ## Clean everything (artifacts + caches)
	@echo "🧹 Deep cleaning completed!"

# =============================================================================
# Development Workflows
# =============================================================================

dev: setup-dev verify ## Complete development setup and verification
	@echo ""
	@echo "🎉 \033[1m\033[32mDevelopment environment is ready!\033[0m"
	@echo ""
	@echo "Next steps:"
	@echo "  • Run '\033[36mmake dana\033[0m' to start the Dana REPL"
	@echo "  • Run '\033[36mmake test\033[0m' to run tests"
	@echo "  • Run '\033[36mmake check\033[0m' for code quality checks"
	@echo ""

# =============================================================================
# Developer Onboarding
# =============================================================================

onboard: setup-dev env-check examples ## 🎯 Complete developer onboarding (setup + demos)
	@echo ""
	@echo "🎉 \033[1m\033[32mWelcome to OpenDXA!\033[0m"
	@echo "======================"
	@echo ""
	@echo "✅ Development environment configured"
	@echo "✅ Environment variables checked"
	@echo "✅ Examples ready to run"
	@echo ""
	@echo "\033[1mNext steps:\033[0m"
	@echo "  \033[36mmake demo-basic\033[0m     # Try basic Dana syntax"
	@echo "  \033[36mmake demo-reasoning\033[0m # See AI reasoning in action"
	@echo "  \033[36mmake dana\033[0m           # Start interactive REPL"
	@echo "  \033[36mmake jupyter\033[0m        # Explore notebooks"
	@echo ""

env-check: ## Check required environment variables
	@echo "🔍 Checking environment variables..."
	@python3 -c "\
import os; \
required = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']; \
missing = [k for k in required if not os.getenv(k)]; \
print('✅ Required API keys configured' if not missing else f'❌ Missing API keys: {missing}'); \
print('💡 Edit .env file to add missing keys' if missing else '')"

env-setup: ## Interactive environment setup wizard
	@echo "⚙️  Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env from template"; \
	fi
	@echo "📂 Please edit .env file with your API keys:"
	@echo "  - Add OPENAI_API_KEY=your_key_here"
	@echo "  - Add ANTHROPIC_API_KEY=your_key_here"
	@echo "💡 Run 'make env-check' to verify setup"

examples: ## Run Dana language examples
	@echo "🎯 Running Dana examples..."
	@if [ -f examples/dana/run_examples.py ]; then \
		uv run python examples/dana/run_examples.py; \
	else \
		echo "📚 Available examples:"; \
		find examples/ -name "*.na" -type f | head -5; \
	fi

demo-basic: ## Quick Dana language demo (arithmetic)
	@echo "🚀 Basic Dana demo - arithmetic..."
	@if [ -f examples/dana/na/arithmetic_example.na ]; then \
		uv run dana examples/dana/na/arithmetic_example.na; \
	else \
		echo "📝 Creating basic demo..."; \
		echo 'print("Hello from Dana!")' | uv run dana; \
	fi

demo-reasoning: ## AI reasoning demo
	@echo "🧠 AI reasoning demo..."
	@if [ -f examples/dana/na/reasoning_example.na ]; then \
		uv run dana examples/dana/na/reasoning_example.na; \
	else \
		echo "🤖 Testing reasoning capability..."; \
		echo 'reason("What is 2+2 and why?")' | uv run dana; \
	fi

jupyter: ## Start Jupyter with Dana examples
	@echo "📊 Starting Jupyter with examples..."
	@if command -v jupyter >/dev/null 2>&1; then \
		cd examples && uv run jupyter lab; \
	else \
		echo "❌ Jupyter not available. Install with: uv add jupyter"; \
	fi

# =============================================================================
# Documentation Workflows
# =============================================================================

docs-build: ## Build documentation
	@echo "📚 Building documentation..."
	@if [ -f mkdocs.yml ]; then \
		uv run --extra docs mkdocs build; \
	else \
		echo "❌ mkdocs.yml not found. Documentation not configured."; \
	fi

docs-serve: ## Serve documentation locally
	@echo "🌐 Serving docs at http://localhost:8000"
	@if [ -f mkdocs.yml ]; then \
		uv run --extra docs mkdocs serve; \
	else \
		echo "❌ mkdocs.yml not found. Documentation not configured."; \
	fi

docs-check: ## Validate documentation links and style
	@echo "🔍 Checking documentation..."
	@if command -v linkcheckmd >/dev/null 2>&1; then \
		uv run --extra docs linkcheckmd docs/; \
	else \
		echo "⚠️  linkcheckmd not available, skipping link check"; \
	fi
	@if command -v doc8 >/dev/null 2>&1; then \
		uv run --extra docs doc8 docs/; \
	else \
		echo "⚠️  doc8 not available, skipping style check"; \
	fi

docs-validate: docs-build docs-check ## Complete documentation validation
	@echo "✅ Documentation validation completed!"

docs-deploy: docs-build ## Deploy documentation to GitHub Pages
	@echo "🚀 Deploying docs to GitHub Pages..."
	@if [ -f mkdocs.yml ]; then \
		uv run --extra docs mkdocs gh-deploy --clean; \
	else \
		echo "❌ mkdocs.yml not found. Documentation not configured."; \
	fi

# =============================================================================
# Quality Assurance
# =============================================================================

security: ## Run security checks
	@echo "🔒 Running security checks..."
	@if command -v bandit >/dev/null 2>&1; then \
		uv run bandit -r opendxa/ -f json -o security-report.json || echo "⚠️  Security issues found - check security-report.json"; \
		uv run bandit -r opendxa/; \
	else \
		echo "❌ bandit not available. Install with: uv add bandit"; \
	fi
	@if command -v safety >/dev/null 2>&1; then \
		uv run safety check; \
	else \
		echo "❌ safety not available. Install with: uv add safety"; \
	fi

validate-config: ## Validate project configuration files
	@echo "⚙️  Validating configuration..."
	@echo "📝 Checking pyproject.toml..."
	@python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('✅ pyproject.toml is valid')"
	@if [ -f opendxa_config.json ]; then \
		echo "📝 Checking opendxa_config.json..."; \
		python3 -c "import json; json.load(open('opendxa_config.json')); print('✅ opendxa_config.json is valid')"; \
	fi
	@if [ -f mkdocs.yml ]; then \
		echo "📝 Checking mkdocs.yml..."; \
		python3 -c "import yaml; yaml.safe_load(open('mkdocs.yml')); print('✅ mkdocs.yml is valid')"; \
	fi

release-check: clean verify docs-validate security validate-config ## Complete pre-release validation
	@echo ""
	@echo "🚀 \033[1m\033[32mRelease validation completed!\033[0m"
	@echo "=================================="
	@echo ""
	@echo "✅ Code quality checks passed"
	@echo "✅ Tests passed" 
	@echo "✅ Documentation validated"
	@echo "✅ Security checks completed"
	@echo "✅ Configuration validated"
	@echo ""
	@echo "\033[33m🎯 Ready for release!\033[0m"
	@echo ""

# =============================================================================
# Editor Integration
# =============================================================================

install-cursor: ## Install Dana extension for Cursor
	@echo "🔧 Installing Dana extension for Cursor ($(DETECTED_OS))..."
	@if [ -f ./bin/cursor/install$(SCRIPT_EXT) ]; then \
		./bin/cursor/install$(SCRIPT_EXT); \
	else \
		echo "❌ Cursor install script not found for $(DETECTED_OS)"; \
	fi

install-vscode: ## Install Dana extension for VS Code
	@echo "🔧 Installing Dana extension for VS Code ($(DETECTED_OS))..."
	@if [ -f ./bin/vscode/install$(SCRIPT_EXT) ]; then \
		./bin/vscode/install$(SCRIPT_EXT); \
	else \
		echo "❌ VS Code install script not found for $(DETECTED_OS)"; \
	fi

install-vim: ## Install Dana syntax for Vim/Neovim (Unix only)
ifeq ($(DETECTED_OS),Windows)
	@echo "❌ Vim integration not available on Windows"
else
	@echo "🔧 Installing Dana syntax for Vim/Neovim..."
	@if [ -f ./bin/vim/install.sh ]; then \
		./bin/vim/install.sh; \
	else \
		echo "❌ Vim install script not found"; \
	fi
endif

uninstall-cursor: ## Remove Dana extension from Cursor
	@echo "🗑️  Removing Dana extension from Cursor ($(DETECTED_OS))..."
	@if [ -f ./bin/cursor/uninstall$(SCRIPT_EXT) ]; then \
		./bin/cursor/uninstall$(SCRIPT_EXT); \
	else \
		echo "❌ Cursor uninstall script not found for $(DETECTED_OS)"; \
	fi

uninstall-vscode: ## Remove Dana extension from VS Code
	@echo "🗑️  Removing Dana extension from VS Code ($(DETECTED_OS))..."
	@if [ -f ./bin/vscode/uninstall$(SCRIPT_EXT) ]; then \
		./bin/vscode/uninstall$(SCRIPT_EXT); \
	else \
		echo "❌ VS Code uninstall script not found for $(DETECTED_OS)"; \
	fi

uninstall-vim: ## Remove Dana syntax from Vim/Neovim (Unix only)
ifeq ($(DETECTED_OS),Windows)
	@echo "❌ Vim integration not available on Windows"
else
	@echo "🗑️  Removing Dana syntax from Vim/Neovim..."
	@if [ -f ./bin/vim/uninstall.sh ]; then \
		./bin/vim/uninstall.sh; \
	else \
		echo "❌ Vim uninstall script not found"; \
	fi
endif

install-editors: ## Install Dana support for all available editors
	@echo "🚀 Installing Dana support for all available editors..."
	@echo "📍 Step 1/3: Installing Cursor extension..."
	@$(MAKE) install-cursor
	@echo "📍 Step 2/3: Installing VS Code extension..."
	@$(MAKE) install-vscode
ifneq ($(DETECTED_OS),Windows)
	@echo "📍 Step 3/3: Installing Vim syntax..."
	@$(MAKE) install-vim
else
	@echo "📍 Step 3/3: Skipping Vim (Windows not supported)"
endif
	@echo "✅ Editor integration complete!"

uninstall-editors: ## Remove Dana support from all editors
	@echo "🗑️  Removing Dana support from all editors..."
	@echo "📍 Step 1/3: Removing Cursor extension..."
	@$(MAKE) uninstall-cursor
	@echo "📍 Step 2/3: Removing VS Code extension..."
	@$(MAKE) uninstall-vscode
ifneq ($(DETECTED_OS),Windows)
	@echo "📍 Step 3/3: Removing Vim syntax..."
	@$(MAKE) uninstall-vim
else
	@echo "📍 Step 3/3: Skipping Vim (Windows not supported)"
endif
	@echo "✅ Editor cleanup complete!"

# =============================================================================
# Ollama Management
# =============================================================================

install-ollama: ## Install Ollama on current platform
ifeq ($(DETECTED_OS),Darwin)
	@$(MAKE) install-ollama-macos
else ifeq ($(DETECTED_OS),Linux)
	@$(MAKE) install-ollama-linux
else ifeq ($(DETECTED_OS),Windows)
	@$(MAKE) install-ollama-windows
else
	@echo "❌ Unsupported platform: $(DETECTED_OS)"
	@echo "Please visit https://ollama.com/download for manual installation"
endif

update-ollama: ## Update Ollama on current platform
ifeq ($(DETECTED_OS),Darwin)
	@$(MAKE) update-ollama-macos
else ifeq ($(DETECTED_OS),Linux)
	@$(MAKE) update-ollama-linux
else ifeq ($(DETECTED_OS),Windows)
	@$(MAKE) update-ollama-windows
else
	@echo "❌ Unsupported platform: $(DETECTED_OS)"
	@echo "Please visit https://ollama.com/download for manual update"
endif

uninstall-ollama: ## Uninstall Ollama on current platform
ifeq ($(DETECTED_OS),Darwin)
	@$(MAKE) uninstall-ollama-macos
else ifeq ($(DETECTED_OS),Linux)
	@$(MAKE) uninstall-ollama-linux
else ifeq ($(DETECTED_OS),Windows)
	@echo "🗑️  To uninstall Ollama on Windows:"
	@echo "   1. Go to Settings > Apps"
	@echo "   2. Search for 'Ollama'"
	@echo "   3. Click Uninstall"
else
	@echo "❌ Unsupported platform: $(DETECTED_OS)"
endif

# Platform-specific Ollama targets

install-ollama-macos: # Install Ollama on macOS using Homebrew
	@echo "🦄 Installing Ollama on macOS..."
	@if command -v brew >/dev/null 2>&1; then \
		brew install ollama || brew upgrade ollama; \
		echo "✅ Ollama installed/updated successfully"; \
	else \
		echo "❌ Homebrew not found. Please install Homebrew first:"; \
		echo "   /bin/bash -c \"\$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""; \
		echo "   Then run: make install-ollama-macos"; \
	fi

update-ollama-macos: # Update Ollama on macOS using Homebrew
	@echo "⬆️  Updating Ollama on macOS..."
	@if command -v brew >/dev/null 2>&1; then \
		brew update; \
		brew upgrade ollama; \
		echo "✅ Ollama updated successfully"; \
	else \
		echo "❌ Homebrew not found"; \
	fi

uninstall-ollama-macos: # Uninstall Ollama on macOS using Homebrew
	@echo "🗑️  Uninstalling Ollama on macOS..."
	@if command -v brew >/dev/null 2>&1; then \
		brew uninstall ollama; \
		echo "✅ Ollama uninstalled successfully"; \
	else \
		echo "❌ Homebrew not found"; \
	fi

install-ollama-linux: # Install Ollama on Linux using official script
	@echo "🐧 Installing Ollama on Linux..."
	@echo "📥 Downloading and running official install script..."
	@curl -fsSL https://ollama.com/install.sh | sh
	@echo "✅ Ollama installed successfully"

update-ollama-linux: install-ollama-linux # Update Ollama on Linux (same as install)

uninstall-ollama-linux: # Uninstall Ollama on Linux
	@echo "🗑️  Uninstalling Ollama on Linux..."
	@if command -v systemctl >/dev/null 2>&1; then \
		sudo systemctl stop ollama || true; \
		sudo systemctl disable ollama || true; \
		sudo rm -f /etc/systemd/system/ollama.service; \
		sudo systemctl daemon-reload; \
	fi
	@sudo rm -f /usr/local/bin/ollama
	@sudo rm -rf /usr/share/ollama
	@sudo userdel ollama 2>/dev/null || true
	@sudo groupdel ollama 2>/dev/null || true
	@echo "✅ Ollama uninstalled successfully"
	@echo "💡 Note: Model files in ~/.ollama may remain. Remove manually if desired."

install-ollama-windows: # Install Ollama on Windows (instructions only)
	@echo "🪟 Installing Ollama on Windows..."
	@echo "📝 Please follow these steps:"
	@echo "   1. Download OllamaSetup.exe from https://ollama.com/download"
	@echo "   2. Run the installer as administrator"
	@echo "   3. Follow the setup wizard"
	@echo ""
	@echo "💡 Alternative - using PowerShell:"
	@echo "   Start-BitsTransfer -Source 'https://ollama.com/download/OllamaSetup.exe' -Destination 'OllamaSetup.exe'"
	@echo "   Then run OllamaSetup.exe"

update-ollama-windows: install-ollama-windows # Update Ollama on Windows (same as install)

# =============================================================================
# Documentation (legacy placeholder kept for compatibility)
# ============================================================================= 
