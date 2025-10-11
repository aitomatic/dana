# Makefile - Dana Lang Development Commands
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

.PHONY: help test test-unit test-integration test-functional test-live test-cov lint format fix clean

# Default target
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo ""
	@echo "\033[1m\033[34mDana Lang - Development Commands\033[0m"
	@echo "\033[1m=====================================\033[0m"
	@echo ""
	@echo "\033[1mTesting:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^test.*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "\033[1mCode Quality:\033[0m"
	@awk 'BEGIN {FS = ":.*?## "} /^(lint|format|fix|clean).*:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests (excludes live/deep/real_api)
	@echo "📝 Running dana-lang tests..."
	DANA_MOCK_LLM=true DANA_USE_REAL_LLM=false pytest tests/ -v --maxfail=10

test-unit: ## Run only unit tests
	@echo "🧪 Running unit tests..."
	DANA_MOCK_LLM=true pytest tests/ -m unit -v

test-integration: ## Run only integration tests
	@echo "🔗 Running integration tests..."
	DANA_MOCK_LLM=true pytest tests/ -m integration -v

test-functional: ## Run only functional tests
	@echo "⚙️  Running functional tests..."
	DANA_MOCK_LLM=true pytest tests/functional/ -v

test-live: ## Run live tests (requires API keys)
	@echo "🌐 Running live tests..."
	pytest tests/ -m live -v

test-deep: ## Run deep/comprehensive tests
	@echo "🔬 Running deep tests..."
	pytest tests/ -m deep -v

test-cov: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	DANA_MOCK_LLM=true pytest tests/ --cov=dana_lang --cov-report=html --cov-report=term
	@echo "📈 Coverage report: htmlcov/index.html"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Check code style and quality
	@echo "🔍 Linting dana-lang..."
	ruff check . --exclude contrib

format: ## Format code automatically
	@echo "✨ Formatting dana-lang..."
	ruff format . --exclude contrib

fix: ## Auto-fix code issues
	@echo "🔧 Auto-fixing dana-lang..."
	ruff check --fix . --exclude contrib
	ruff format . --exclude contrib

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning dana-lang..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache/ .mypy_cache/

