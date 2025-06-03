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
	docs-serve

# =============================================================================
# Help & Information
# =============================================================================

help: ## Show this help message with available commands
	@echo ""
	@echo "\033[1m\033[34mOpenDXA Development Commands\033[0m"
	@echo "\033[1m=====================================\033[0m"
	@echo ""
	@echo "\033[1mSetup & Installation:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(install|setup|sync|update).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mTesting:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^test.*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mCode Quality:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(lint|format|typecheck|check|fix|verify).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mApplication:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(dana|run).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mMaintenance:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(clean|dev).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[33mTip: Run 'make dev' for complete setup + quality checks\033[0m"
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
# Documentation (if needed in future)
# =============================================================================

# docs-serve: ## Serve documentation locally (placeholder)
# 	@echo "📚 Serving documentation..."
# 	# Add documentation server command here when implemented 