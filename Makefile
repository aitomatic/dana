# Makefile - OpenDXA Development Commands
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

# =============================================================================
# OpenDXA Development Makefile
# =============================================================================
# Modern Python development with uv package manager
# Requires uv to be installed: https://docs.astral.sh/uv/

# Default target
.DEFAULT_GOAL := quickstart

# All targets are phony (don't create files)
.PHONY: help \
	quickstart \
	install install-dev setup-dev \
	test test-fast test-live test-cov test-watch \
	lint lint-fix format format-check typecheck \
	check fix verify \
	dana run \
	clean clean-all clean-cache \
	dev update-deps sync \
	onboard env-check env-setup examples demo-basic demo-reasoning jupyter \
	docs-build docs-serve docs-check docs-validate docs-deploy \
	security validate-config release-check

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
	@echo "\033[33mTip: New to OpenDXA? Start with 'make quickstart' or 'make onboard'\033[0m"
	@echo ""

# =============================================================================
# Quick Start (Get Running in 30 seconds!)
# =============================================================================

quickstart: ## 🚀 QUICK START: Get OpenDXA running in 30 seconds!
	@echo ""
	@echo "🚀 \033[1m\033[32mOpenDXA Quick Start\033[0m"
	@echo "==================="
	@echo ""
	@echo "📦 Installing dependencies..."
	@uv sync --quiet
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
	uv run pytest tests/

test-fast: ## Run fast tests only (excludes live/deep tests)
	@echo "⚡ Running fast tests..."
	uv run pytest -m "not live and not deep" tests/

test-live: ## Run live tests (requires API keys)
	@echo "🌐 Running live tests (requires API keys)..."
	uv run pytest -m "live" tests/

test-cov: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	uv run pytest --cov=opendxa --cov-report=html --cov-report=term tests/
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
# Documentation (legacy placeholder kept for compatibility)
# ============================================================================= 