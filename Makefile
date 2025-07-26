# Makefile - Dana Development Commands
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

# =============================================================================
# Dana Development Makefile - Essential Commands Only
# =============================================================================

# UV command helper - use system uv if available, otherwise fallback to ~/.local/bin/uv
UV_CMD = $(shell command -v uv 2>/dev/null || echo ~/.local/bin/uv)

# Default target
.DEFAULT_GOAL := help

# All targets are phony (don't create files)
.PHONY: help help-more quickstart install setup-dev sync test dana clean lint format fix check mypy \
	install-ollama start-ollama install-vllm start-vllm install-vscode install-cursor install-vim install-emacs \
	docs-serve docs-build docs-deps test-fast test-cov update-deps dev security validate-config release-check

# =============================================================================
# Help & Quick Start
# =============================================================================

help: ## Show essential Dana commands
	@echo ""
	@echo "\033[1m\033[34mDana Development Commands\033[0m"
	@echo "\033[1m=====================================\033[0m"
	@echo ""
	@echo "\033[1mGetting Started:\033[0m"
	@echo "  \033[36mquickstart\033[0m      🚀 Get Dana running in 30 seconds!"
	@echo "  \033[36minstall\033[0m         📦 Install package and dependencies"
	@echo "  \033[36msetup-dev\033[0m       🛠️  Install with development dependencies"
	@echo ""
	@echo "\033[1mUsing Dana:\033[0m"
	@echo "  \033[36mdana\033[0m            🚀 Start the Dana REPL"
	@echo "  \033[36mtest\033[0m            🧪 Run all tests"
	@echo ""
	@echo "\033[1mCode Quality:\033[0m"
	@echo "  \033[36mlint\033[0m            🔍 Check code style and quality"
	@echo "  \033[36mlint-critical\033[0m   🚫 Critical checks (matches CI)"
	@echo "  \033[36mformat\033[0m          ✨ Format code automatically"
	@echo "  \033[36mfix\033[0m             🔧 Auto-fix all fixable code issues"
	@echo "  \033[36mci-check\033[0m        🎯 Run same checks as GitHub CI"
	@echo ""
	@echo "\033[1mLLM Integration:\033[0m"
	@echo "  \033[36minstall-ollama\033[0m  🦙 Install Ollama for local inference"
	@echo "  \033[36minstall-vllm\033[0m    ⚡ Install vLLM for local inference"
	@echo ""
	@echo "\033[1mEditor Support:\033[0m"
	@echo "  \033[36minstall-vscode\033[0m  📝 Install VS Code extension with LSP"
	@echo "  \033[36minstall-cursor\033[0m  🎯 Install Cursor extension with LSP"
	@echo "  \033[36minstall-vim\033[0m     ⚡ Install Vim/Neovim support with LSP"
	@echo "  \033[36minstall-emacs\033[0m   🌟 Install Emacs support with LSP"
	@echo ""
	@echo "\033[1mMaintenance:\033[0m"
	@echo "  \033[36mclean\033[0m           🧹 Clean build artifacts and caches"
	@echo ""
	@echo "\033[33mTip: Run 'make help-more' for additional commands\033[0m"
	@echo ""

help-more: ## Show all available commands including advanced ones
	@echo ""
	@echo "\033[1m\033[34mDana Development Commands (Complete)\033[0m"
	@echo "\033[1m==========================================\033[0m"
	@echo ""
	@echo "\033[1mGetting Started:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(quickstart|install|setup-dev|sync).*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mUsing Dana:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(dana|test|run).*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mAdvanced Testing:\033[0m"
	@awk 'BEGIN {FS = ":.*?## MORE: "} /^test.*:.*?## MORE:/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mCode Quality:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(lint|format|check|fix|mypy).*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mLLM Integration:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(install-ollama|start-ollama|install-vllm|start-vllm).*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mEditor Support:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(install-vscode|install-cursor|install-vim|install-emacs).*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mDevelopment & Release:\033[0m"
	@awk 'BEGIN {FS = ":.*?## MORE: "} /^(update-deps|dev|security|validate-config|release-check|docs-build|docs-deps).*:.*?## MORE:/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mMaintenance:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(clean|docs-serve).*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# Check if uv is installed, install if missing
check-uv:
	@if ! command -v uv >/dev/null 2>&1 && ! test -f ~/.local/bin/uv; then \
		echo "🔧 uv not found, installing..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "✅ uv installed successfully"; \
	else \
		echo "✅ uv already available"; \
	fi

quickstart: check-uv ## 🚀 QUICK START: Get Dana running in 30 seconds!
	@echo ""
	@echo "🚀 \033[1m\033[32mDana Quick Start\033[0m"
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
	@echo ""
	@echo "\033[33m💡 Tip: Run 'open .env' to edit your API keys\033[0m"
	@echo ""

# =============================================================================
# Setup & Installation
# =============================================================================

install: ## Install package and dependencies
	@echo "📦 Installing dependencies..."
	$(UV_CMD) sync --extra dev

setup-dev: ## Install with development dependencies and setup tools
	@echo "🛠️  Installing development dependencies..."
	$(UV_CMD) sync --extra dev
	@echo "🔧 Setting up development tools..."
	$(UV_CMD) run pre-commit install
	@echo "✅ Development environment ready!"

sync: ## Sync dependencies with uv.lock
	@echo "🔄 Syncing dependencies..."
	$(UV_CMD) sync

# =============================================================================
# Usage
# =============================================================================

dana: ## Start the Dana REPL
	@echo "🚀 Starting Dana REPL..."
	$(UV_CMD) run dana

test: ## Run all tests (matches CI)
	@echo "🧪 Running tests (matching CI)..."
	DANA_MOCK_LLM=true DANA_USE_REAL_LLM=false $(UV_CMD) run pytest -m "not live and not deep" tests/ --tb=short -v

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Check code style and quality (matches CI)
	@echo "🔍 Running linting checks (matching CI)..."
	@echo "🚫 Critical checks (E722, F821)..."
	$(UV_CMD) run ruff check dana/ tests/ --select E722,F821 --exclude dana/contrib
	@echo "⚠️ Important checks (F841, B017)..."
	$(UV_CMD) run ruff check dana/ tests/ --select F841,B017
	@echo "✨ Style checks..."
	$(UV_CMD) run ruff check dana/ tests/ --select UP038,B026,E712,E721,B024,B007

lint-critical: ## Run only critical lint checks (BLOCKING)
	@echo "🚫 Running critical lint checks (BLOCKING)..."
	$(UV_CMD) run ruff check dana/ tests/ --select E722,F821 --exclude dana/contrib

lint-important: ## Run important lint checks (WARNING)
	@echo "⚠️ Running important lint checks (WARNING)..."
	$(UV_CMD) run ruff check dana/ tests/ --select F841,B017

lint-style: ## Run style and formatting checks (INFO)
	@echo "✨ Running style and formatting checks (INFO)..."
	$(UV_CMD) run ruff format --check dana/ tests/
	$(UV_CMD) run ruff check dana/ tests/ --select UP038,B026,E712,E721,B024,B007

format: ## Format code automatically
	@echo "✨ Formatting code..."
	$(UV_CMD) run ruff format dana/ tests/

check: lint format-check ## Run all code quality checks
	@echo "✅ All quality checks completed!"

format-check: ## Check code formatting (matches CI)
	@echo "📝 Checking code formatting..."
	$(UV_CMD) run ruff format --check dana/ tests/

fix: ## Auto-fix all fixable code issues
	@echo "🔧 Auto-fixing code issues..."
	$(UV_CMD) run ruff check --fix dana/ tests/
	$(UV_CMD) run ruff format dana/ tests/
	@echo "🔧 Applied all auto-fixes!"

mypy: ## Run type checking
	@echo "🔍 Running type checks..."
	$(UV_CMD) run mypy .

# =============================================================================
# LLM Integration
# =============================================================================

install-ollama: ## Install Ollama for local model inference
	@echo "🦙 Installing Ollama for Dana..."
	@./bin/ollama/install.sh

start-ollama: ## Start Ollama with Dana configuration
	@echo "🚀 Starting Ollama for Dana..."
	@./bin/ollama/start.sh

install-vllm: ## Install vLLM for local model inference
	@echo "⚡ Installing vLLM for Dana..."
	@./bin/vllm/install.sh

start-vllm: ## Start vLLM server with interactive model selection
	@echo "🚀 Starting vLLM for Dana..."
	@./bin/vllm/start.sh

install-vscode: ## Install VS Code extension with LSP support
	@echo "📝 Installing Dana VS Code extension..."
	@./bin/vscode/install.sh

install-cursor: ## Install Cursor extension with LSP support
	@echo "🎯 Installing Dana Cursor extension..."
	@./bin/cursor/install.sh

install-vim: ## Install Vim/Neovim support with LSP
	@echo "⚡ Installing Dana Vim/Neovim support..."
	@./bin/vim/install.sh

install-emacs: ## Install Emacs support with LSP
	@echo "🌟 Installing Dana Emacs support..."
	@./bin/emacs/install.sh

# =============================================================================
# Maintenance & Documentation
# =============================================================================

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache/ .mypy_cache/

docs-serve: ## Serve documentation locally
	@echo "📚 Serving docs at http://localhost:8000"
	@if [ -f mkdocs.yml ]; then \
		$(UV_CMD) run --extra docs mkdocs serve; \
	else \
		echo "❌ mkdocs.yml not found. Documentation not configured."; \
	fi

docs-build: ## MORE: Build documentation with strict validation
	@echo "📖 Building documentation with strict validation..."
	@if [ -f mkdocs.yml ]; then \
		$(UV_CMD) run --extra docs mkdocs build --strict; \
	else \
		echo "❌ mkdocs.yml not found. Documentation not configured."; \
	fi

docs-deps: ## MORE: Install documentation dependencies
	@echo "📚 Installing documentation dependencies..."
	$(UV_CMD) sync --extra docs

# =============================================================================
# Advanced/Comprehensive Targets (shown in help-more)
# =============================================================================

test-fast: ## MORE: Run fast tests only (excludes live/deep tests)
	@echo "⚡ Running fast tests..."
	DANA_MOCK_LLM=true $(UV_CMD) run pytest -m "not live and not deep" tests/

test-cov: ## MORE: Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	DANA_MOCK_LLM=true $(UV_CMD) run pytest --cov=dana --cov-report=html --cov-report=term tests/
	@echo "📈 Coverage report generated in htmlcov/"

update-deps: ## MORE: Update dependencies to latest versions
	@echo "⬆️  Updating dependencies..."
	$(UV_CMD) lock --upgrade

ci-check: lint-critical test ## Run the same checks as GitHub CI
	@echo ""
	@echo "🎯 \033[1m\033[32mCI checks completed!\033[0m"
	@echo "=================================="
	@echo "✅ Critical lint checks passed"
	@echo "✅ Tests passed"
	@echo ""
	@echo "\033[33m💡 This matches what GitHub CI will run\033[0m"
	@echo ""

dev: setup-dev check test-fast ## MORE: Complete development setup and verification
	@echo ""
	@echo "🎉 \033[1m\033[32mDevelopment environment is ready!\033[0m"
	@echo ""
	@echo "Next steps:"
	@echo "  • Run '\033[36mmake dana\033[0m' to start the Dana REPL"
	@echo "  • Run '\033[36mmake test\033[0m' to run tests"
	@echo "  • Run '\033[36mmake check\033[0m' for code quality checks"
	@echo ""

security: ## MORE: Run security checks on codebase
	@echo "🔒 Running security checks..."
	@if command -v bandit >/dev/null 2>&1; then \
		$(UV_CMD) run bandit -r dana/ -f json -o security-report.json || echo "⚠️  Security issues found - check security-report.json"; \
		$(UV_CMD) run bandit -r dana/; \
	else \
		echo "❌ bandit not available. Install with: uv add bandit"; \
	fi

validate-config: ## MORE: Validate project configuration files
	@echo "⚙️  Validating configuration..."
	@echo "📝 Checking pyproject.toml..."
	@python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('✅ pyproject.toml is valid')"
	@if [ -f dana_config.json ]; then \
		echo "📝 Checking dana_config.json..."; \
		python3 -c "import json; json.load(open('dana_config.json')); print('✅ dana_config.json is valid')"; \
	fi
	@if [ -f mkdocs.yml ]; then \
		echo "📝 Checking mkdocs.yml..."; \
		python3 -c "import yaml; yaml.safe_load(open('mkdocs.yml')); print('✅ mkdocs.yml is valid')"; \
	fi

release-check: clean check test-fast security validate-config ## MORE: Complete pre-release validation
	@echo ""
	@echo "🚀 \033[1m\033[32mRelease validation completed!\033[0m"
	@echo "=================================="
	@echo ""
	@echo "✅ Code quality checks passed"
	@echo "✅ Tests passed"
	@echo "✅ Security checks completed"
	@echo "✅ Configuration validated"
	@echo ""
	@echo "\033[33m🎯 Ready for release!\033[0m"
	@echo ""

# =============================================================================
# Package Building & Publishing
# =============================================================================

build: ## Build package distribution files
	@echo "📦 Building package..."
	$(UV_CMD) run python -m build

dist: clean build ## Clean and build distribution files
	@echo "✅ Distribution files ready in dist/"

check-dist: ## Validate built distribution files
	@echo "🔍 Checking distribution files..."
	$(UV_CMD) run twine check dist/*

publish: check-dist ## Upload to PyPI
	@echo "🚀 Publishing to PyPI..."
	$(UV_CMD) run twine upload --verbose dist/*
run: dana ## Alias for 'dana' command 

build-frontend: ## Build the frontend (Vite React app) and copy to backend static
	cd dana/contrib/ui && npm i && npm run build

build-all: ## Build frontend and Python package
	build-frontend & uv run python -m build

local-server: ## Start the local server
	uv run python -m dana.api.server
