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
	test test-fast test-live test-cov test-watch \
	lint lint-fix format format-check typecheck \
	check fix verify \
	dana run opendxa-server \
	clean clean-all clean-cache \
	dev update-deps sync \
	onboard env-check env-setup examples demo-basic demo-reasoning jupyter \
	docs-build docs-serve docs-check docs-validate docs-deploy \
	security validate-config release-check \
	install-cursor install-vscode install-vim uninstall-cursor uninstall-vscode uninstall-vim install-editors uninstall-editors \
	install-ollama update-ollama uninstall-ollama start-ollama chat-ollama stop-ollama \
	install-vllm update-vllm uninstall-vllm start-vllm chat-vllm stop-vllm status-vllm test-vllm vllm-models

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
	@awk 'BEGIN {FS = ":.*?## "} /^(install-ollama|update-ollama|uninstall-ollama|start-ollama|chat-ollama|stop-ollama).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mvLLM Management:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(install-vllm|update-vllm|uninstall-vllm|start-vllm|chat-vllm|stop-vllm|status-vllm|test-vllm|vllm-models).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
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
	@#OPENDXA_MOCK_LLM=true uv run pytest tests/ -v -k "not (function_composition or pipe_operator_composition)"
	OPENDXA_MOCK_LLM=true uv run pytest tests/

test-fast: ## Run fast tests only (excludes live/deep tests)
	@echo "⚡ Running fast tests..."
	OPENDXA_MOCK_LLM=true uv run pytest -m "not live and not deep" tests/

test-live: ## Run live tests (requires API keys)
	@echo "🌐 Running live tests (requires API keys)..."
	uv run pytest -m "live" tests/

test-cov: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	OPENDXA_MOCK_LLM=true uv run pytest --cov=opendxa --cov=dana --cov-report=html --cov-report=term tests/
	@echo "📈 Coverage report generated in htmlcov/"

test-watch: ## Run tests in watch mode (reruns on file changes)
	@echo "👀 Running tests in watch mode..."
	uv run pytest-watch tests/

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	uv run ruff check .

lint-fix: ## Auto-fix linting issues
	@echo "🔧 Auto-fixing linting issues..."
	uv run ruff check --fix .

format: ## Format code with ruff
	@echo "✨ Formatting code..."
	uv run ruff format .

format-check: ## Check code formatting without changes
	@echo "📝 Checking code formatting..."
	uv run ruff format --check .

typecheck: ## Run type checking
	@echo "🔍 Running type checks..."
	uv run mypy .

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
	uv run python -m dana.api.server --host localhost --port 8080

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
		uv run bandit -r opendxa/ dana/ -f json -o security-report.json || echo "⚠️  Security issues found - check security-report.json"; \
		uv run bandit -r opendxa/ dana/; \
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
# Editor & Local LLM Integration
# =============================================================================

# --- Editor Integration ---

install-editors: install-cursor install-vscode install-vim ## Install all editor integrations
uninstall-editors: uninstall-cursor uninstall-vscode uninstall-vim ## Uninstall all editor integrations

install-cursor: ## Install Cursor.sh integration
	@./bin/cursor/install$(SCRIPT_EXT)
uninstall-cursor: ## Uninstall Cursor.sh integration
	@echo "Uninstall not yet implemented for Cursor"

install-vscode: ## Install VSCode integration
	@./bin/vscode/install$(SCRIPT_EXT)
uninstall-vscode: ## Uninstall VSCode integration
	@echo "Uninstall not yet implemented for VSCode"

install-vim: ## Install Vim/Neovim integration
	@./bin/vim/install$(SCRIPT_EXT)
uninstall-vim: ## Uninstall Vim/Neovim integration
	@echo "Uninstall not yet implemented for Vim"

# --- Ollama Management ---

install-ollama: ## Install Ollama for local model inference
	@./bin/ollama/install$(SCRIPT_EXT)

start-ollama: ## Start Ollama and configure environment for OpenDXA
ifeq ($(DETECTED_OS),Windows)
	@start cmd /k "bin\ollama\start.bat"
else
	@echo "source ./bin/ollama/start.sh"
	@echo "You must 'source' this script to apply environment variables to your shell."
endif

chat-ollama: ## Start an interactive chat session with Ollama
	@./bin/ollama/chat$(SCRIPT_EXT)

uninstall-ollama: ## Uninstall Ollama and clean up
	@./bin/ollama/uninstall$(SCRIPT_EXT)

stop-ollama: uninstall-ollama ## Alias to stop and uninstall Ollama

update-ollama: ## Check for Ollama updates
	@echo "Checking for Ollama updates..."
	@ollama pull ollama/ollama

# --- vLLM Management ---

install-vllm: ## Install vLLM for local model inference
	@./bin/vllm/install$(SCRIPT_EXT)

update-vllm: ## Update vLLM on current platform
ifeq ($(DETECTED_OS),Darwin)
	@$(MAKE) update-vllm-macos
else ifeq ($(DETECTED_OS),Linux)
	@$(MAKE) update-vllm-linux
else ifeq ($(DETECTED_OS),Windows)
	@$(MAKE) update-vllm-windows
else
	@echo "❌ Unsupported platform: $(DETECTED_OS)"
	@echo "Please visit https://docs.vllm.ai/ for manual update"
endif

uninstall-vllm: ## Uninstall vLLM on current platform
ifeq ($(DETECTED_OS),Darwin)
	@$(MAKE) uninstall-vllm-macos
else ifeq ($(DETECTED_OS),Linux)
	@$(MAKE) uninstall-vllm-linux
else ifeq ($(DETECTED_OS),Windows)
	@$(MAKE) uninstall-vllm-windows
else
	@echo "❌ Unsupported platform: $(DETECTED_OS)"
endif

# Platform-specific vLLM targets

install-vllm-macos: # Install vLLM on macOS using our custom script
	@echo "🦄 Installing vLLM on macOS..."
	@if [ -f ./bin/vllm/install.sh ]; then \
		./bin/vllm/install.sh; \
		echo "✅ vLLM installed successfully"; \
	else \
		echo "❌ vLLM install script not found at ./bin/vllm/install.sh"; \
		echo "Please ensure the script exists and is executable"; \
	fi

update-vllm-macos: # Update vLLM on macOS
	@echo "⬆️  Updating vLLM on macOS..."
	@if [ -d ~/vllm ]; then \
		echo "📥 Updating vLLM source repository..."; \
		cd ~/vllm && git pull origin main; \
		if [ -d ~/vllm_env ]; then \
			echo "🔨 Rebuilding vLLM..."; \
			source ~/vllm_env/bin/activate; \
			VLLM_TARGET_DEVICE=cpu pip install -e .; \
			echo "✅ vLLM updated successfully"; \
		else \
			echo "❌ vLLM virtual environment not found at ~/vllm_env"; \
			echo "Please run 'make install-vllm' to install vLLM first"; \
		fi; \
	else \
		echo "❌ vLLM source not found at ~/vllm"; \
		echo "Please run 'make install-vllm' to install vLLM first"; \
	fi

uninstall-vllm-macos: # Uninstall vLLM on macOS
	@echo "🗑️  Uninstalling vLLM on macOS..."
	@echo "🗂️  Removing vLLM virtual environment..."
	@rm -rf ~/vllm_env || true
	@echo "🗂️  Removing vLLM source code..."
	@rm -rf ~/vllm || true
	@echo "✅ vLLM uninstalled successfully"
	@echo "💡 Note: Any custom environments with different names need manual removal"

install-vllm-linux: # Install vLLM on Linux using custom script
	@echo "🐧 Installing vLLM on Linux..."
	@if [ -f ./bin/vllm/install.sh ]; then \
		./bin/vllm/install.sh; \
		echo "✅ vLLM installed successfully"; \
	else \
		echo "❌ vLLM install script not found at ./bin/vllm/install.sh"; \
		echo "Please ensure the script exists and is executable"; \
	fi

update-vllm-linux: update-vllm-macos # Update vLLM on Linux (same process as macOS)

uninstall-vllm-linux: uninstall-vllm-macos # Uninstall vLLM on Linux (same process as macOS)

install-vllm-windows: # Install vLLM on Windows using custom script
	@echo "🪟 Installing vLLM on Windows..."
	@if [ -f ./bin/vllm/install.bat ]; then \
		./bin/vllm/install.bat; \
	else \
		echo "❌ vLLM install script not found at ./bin/vllm/install.bat"; \
		echo "Please ensure the script exists"; \
		echo ""; \
		echo "📝 Manual installation steps for Windows:"; \
		echo "   1. Install Python 3.8+ from https://www.python.org/downloads/"; \
		echo "   2. Install Git from https://git-scm.com/download/win"; \
		echo "   3. Install Visual Studio Build Tools"; \
		echo "   4. Run: python -m venv vllm_env"; \
		echo "   5. Run: vllm_env\\Scripts\\activate"; \
		echo "   6. Run: git clone https://github.com/vllm-project/vllm.git"; \
		echo "   7. Run: cd vllm && pip install -e ."; \
	fi

update-vllm-windows: # Update vLLM on Windows
	@echo "⬆️  Updating vLLM on Windows..."
	@echo "📝 Manual update steps for Windows:"
	@echo "   1. Activate environment: vllm_env\\Scripts\\activate"
	@echo "   2. Update source: cd vllm && git pull origin main"
	@echo "   3. Reinstall: pip install -e ."
	@echo "   4. Test: python -c \"import vllm; print('vLLM updated!')\""

uninstall-vllm-windows: # Uninstall vLLM on Windows
	@echo "🗑️  Uninstalling vLLM on Windows..."
	@echo "📝 Manual uninstall steps for Windows:"
	@echo "   1. Remove virtual environment: rmdir /s vllm_env"
	@echo "   2. Remove source code: rmdir /s vllm"
	@echo "   3. That's it! No other system modifications were made"

start-vllm: ## Start vLLM server with interactive model selection
	@echo "🚀 Starting vLLM server..."
	@./bin/vllm/start$(SCRIPT_EXT)

chat-vllm: ## Start interactive chat with vLLM server
	@echo "💬 Starting vLLM chat interface..."
	@./bin/vllm/chat$(SCRIPT_EXT)

stop-vllm: ## Stop running vLLM server
	@echo "🛑 Stopping vLLM server..."
	@if pgrep -f "vllm.entrypoints.openai.api_server" >/dev/null 2>&1; then \
		pkill -f "vllm.entrypoints.openai.api_server"; \
		echo "✅ vLLM server stopped"; \
	else \
		echo "⚠️  No vLLM server process found"; \
	fi

status-vllm: ## Check vLLM server status
	@echo "🔍 Checking vLLM server status..."
	@if pgrep -f "vllm.entrypoints.openai.api_server" >/dev/null 2>&1; then \
		echo "✅ vLLM server is running"; \
		echo "📊 Process details:"; \
		ps aux | grep -E "vllm.entrypoints.openai.api_server" | grep -v grep; \
	else \
		echo "❌ vLLM server is not running"; \
		echo "💡 Run 'make start-vllm' to start the server"; \
	fi

test-vllm: ## Test vLLM server with a sample request
	@echo "🧪 Testing vLLM server..."
	@if curl -s http://localhost:8000/v1/models >/dev/null 2>&1; then \
		echo "✅ vLLM server is responding"; \
		echo "📋 Available models:"; \
		curl -s http://localhost:8000/v1/models | python3 -m json.tool; \
	else \
		echo "❌ vLLM server is not responding"; \
		echo "💡 Make sure the server is running with 'make start-vllm'"; \
	fi

vllm-models: ## List available models for vLLM
	@echo "🤖 Popular vLLM-compatible models:"
	@echo ""
	@echo "Small models (< 3GB):"
	@echo "  • microsoft/phi-2                    (2.7B parameters)"
	@echo "  • stabilityai/stablelm-2-1_6b        (1.6B parameters)"
	@echo ""
	@echo "Medium models (3-10GB):"
	@echo "  • mistralai/Mistral-7B-Instruct-v0.2 (7B parameters)"
	@echo "  • meta-llama/Llama-2-7b-chat-hf      (7B parameters)"
	@echo "  • google/gemma-7b                     (7B parameters)"
	@echo ""
	@echo "Large models (> 10GB):"
	@echo "  • meta-llama/Llama-2-13b-chat-hf     (13B parameters)"
	@echo "  • mistralai/Mixtral-8x7B-Instruct-v0.1 (46.7B parameters)"
	@echo ""
	@echo "💡 To use a model, start vLLM with:"
	@echo "   make start-vllm"
	@echo "   Then select your model from the interactive menu"

# =============================================================================
# Documentation (legacy placeholder kept for compatibility)
# ============================================================================= 
