# Makefile - Dana Studio Development Commands
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

# UV command helper - use system uv if available, otherwise fallback to ~/.local/bin/uv
UV_CMD = $(shell command -v uv 2>/dev/null || echo ~/.local/bin/uv)

.PHONY: help test test-unit test-integration test-cov lint format fix clean server

# Default target
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo ""
	@echo "\033[1m\033[34mDana Studio - Development Commands\033[0m"
	@echo "\033[1m=======================================\033[0m"
	@echo ""
	@echo "\033[33m💡 Run 'cd .. && make setup' to install all packages\033[0m"
	@echo ""
	@echo "\033[1mServer:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^server.*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mTesting:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^test.*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mCode Quality:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(lint|format|fix|clean).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Server
# =============================================================================
# Note: Run 'make setup' from the monorepo root to install all packages

server: ## Start Dana Studio server
	@echo "🎨 Starting Dana Studio server..."
	$(UV_CMD) run python -m dana_studio.server

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "🎨 Running dana-studio tests..."
	$(UV_CMD) run pytest tests/ -v --maxfail=10 || echo "⚠️  No tests found yet"

test-unit: ## Run only unit tests
	@echo "🧪 Running unit tests..."
	$(UV_CMD) run pytest tests/ -m unit -v || echo "⚠️  No tests found yet"

test-integration: ## Run only integration tests
	@echo "🔗 Running integration tests..."
	$(UV_CMD) run pytest tests/ -m integration -v || echo "⚠️  No tests found yet"

test-cov: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	$(UV_CMD) run pytest tests/ --cov=dana_studio --cov-report=html --cov-report=term || echo "⚠️  No tests found yet"
	@echo "📈 Coverage report: htmlcov/index.html"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Check code style and quality
	@echo "🔍 Linting dana-studio..."
	$(UV_CMD) run ruff check .

format: ## Format code automatically
	@echo "✨ Formatting dana-studio..."
	$(UV_CMD) run ruff format .

fix: ## Auto-fix code issues
	@echo "🔧 Auto-fixing dana-studio..."
	$(UV_CMD) run ruff check --fix .
	$(UV_CMD) run ruff format .

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning dana-studio..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache/ .mypy_cache/
