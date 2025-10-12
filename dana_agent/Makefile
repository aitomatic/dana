# Makefile - Dana Agent Development Commands
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

# UV command helper - use system uv if available, otherwise fallback to ~/.local/bin/uv
UV_CMD = $(shell command -v uv 2>/dev/null || echo ~/.local/bin/uv)

.PHONY: help test test-unit test-integration test-live test-cov lint format fix clean

# Default target
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo ""
	@echo "\033[1m\033[34mDana Agent - Development Commands\033[0m"
	@echo "\033[1m======================================\033[0m"
	@echo ""
	@echo "\033[33m💡 Run 'cd .. && make setup' to install all packages\033[0m"
	@echo ""
	@echo "\033[1mTesting:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^test.*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mCode Quality:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(lint|format|fix|clean).*:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Testing
# =============================================================================
# Note: Run 'make setup' from the monorepo root to install all packages

test: ## Run all tests (excludes live/deep/windows_console)
	@echo "🤖 Running dana_agent tests..."
	DANA_MOCK_LLM=true DANA_USE_REAL_LLM=false $(UV_CMD) run pytest tests/ -v --maxfail=10

test-unit: ## Run only unit tests
	@echo "🧪 Running unit tests..."
	DANA_MOCK_LLM=true $(UV_CMD) run pytest tests/ -m unit -v

test-integration: ## Run only integration tests
	@echo "🔗 Running integration tests..."
	DANA_MOCK_LLM=true $(UV_CMD) run pytest tests/ -m integration -v

test-live: ## Run live tests (requires API keys)
	@echo "🌐 Running live tests..."
	$(UV_CMD) run pytest tests/ -m live -v

test-cov: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	DANA_MOCK_LLM=true $(UV_CMD) run pytest tests/ --cov=dana_agent --cov-report=html --cov-report=term
	@echo "📈 Coverage report: htmlcov/index.html"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Check code style and quality
	@echo "🔍 Linting dana_agent..."
	$(UV_CMD) run ruff check .

format: ## Format code automatically
	@echo "✨ Formatting dana_agent..."
	$(UV_CMD) run ruff format .

fix: ## Auto-fix code issues
	@echo "🔧 Auto-fixing dana_agent..."
	$(UV_CMD) run ruff check --fix .
	$(UV_CMD) run ruff format .

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning dana_agent..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache/ .mypy_cache/
