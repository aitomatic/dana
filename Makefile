# Makefile - Dana Monorepo
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

# =============================================================================
# Dana Monorepo Makefile
# =============================================================================
#
# This monorepo uses uv workspace (configured in pyproject.toml):
#   - ONE shared .venv at the root level
#   - All 3 packages (dana_agent, dana_lang, dana_studio) installed together
#   - Running 'make setup' or 'uv sync' installs everything in editable mode
#
# Sub-packages have their own Makefiles for package-specific operations:
#   - Testing (unit, integration, live)
#   - Code quality (lint, format, fix)
#   - Package-specific tasks
#
# =============================================================================

# UV command helper - use system uv if available, otherwise fallback to ~/.local/bin/uv
UV_CMD = $(shell command -v uv 2>/dev/null || echo ~/.local/bin/uv)

# Sub-packages
PACKAGES = dana_agent dana_lang dana_studio

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# Meta Target Helper - Propagate targets to all sub-packages
# =============================================================================
# Usage: $(call run-in-packages,target-name)
# This will run 'make target-name' in each package directory
define run-in-packages
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "📦 Running '$(1)' in $$pkg..."; \
		cd $$pkg && $(MAKE) $(1) || exit 1; \
		cd ..; \
	done
endef

# All targets are phony (don't create files)
.PHONY: help list packages quickstart setup sync test test-agent test-lang test-studio clean dana studio-server \
	install-ollama start-ollama install-vllm start-vllm

# =============================================================================
# Help & Info
# =============================================================================

help: ## Show available commands
	@echo ""
	@echo "\033[1m\033[34mDana Monorepo\033[0m"
	@echo "\033[1m==============\033[0m"
	@echo ""
	@echo "\033[1mInfo:\033[0m"
	@echo "  \033[36mlist\033[0m            📦 List packages and installation status"
	@echo "  \033[36mpackages\033[0m        📋 Show installed Dana packages"
	@echo ""
	@echo "\033[1mGetting Started:\033[0m"
	@echo "  \033[36mquickstart\033[0m      🚀 Get Dana running in 30 seconds"
	@echo "  \033[36msetup\033[0m           🔧 Setup all packages (installs to .venv)"
	@echo "  \033[36msync\033[0m            🔄 Sync dependencies"
	@echo ""
	@echo "\033[1mDevelopment:\033[0m"
	@echo "  \033[36mtest\033[0m            🧪 Run all tests"
	@echo "  \033[36mtest-agent\033[0m      🤖 Run dana-agent tests only"
	@echo "  \033[36mtest-lang\033[0m       📝 Run dana-lang tests only"
	@echo "  \033[36mtest-studio\033[0m     🎨 Run dana-studio tests only"
	@echo "  \033[36mclean\033[0m           🧹 Clean artifacts and remove .venv"
	@echo ""
	@echo "\033[1mRun:\033[0m"
	@echo "  \033[36mdana\033[0m            🚀 Start the Dana REPL"
	@echo "  \033[36mstudio-server\033[0m   🎨 Start Dana Studio server"
	@echo ""
	@echo "\033[1mLLM Infrastructure:\033[0m"
	@echo "  \033[36minstall-ollama\033[0m  🦙 Install Ollama for local inference"
	@echo "  \033[36mstart-ollama\033[0m    🚀 Start Ollama server"
	@echo "  \033[36minstall-vllm\033[0m    ⚡ Install vLLM for local inference"
	@echo "  \033[36mstart-vllm\033[0m      🚀 Start vLLM server"
	@echo ""
	@echo "\033[33m💡 Tip: Each package has its own Makefile with additional targets\033[0m"
	@echo "   • cd dana_agent && make help"
	@echo "   • cd dana_lang && make help"
	@echo "   • cd dana_studio && make help"
	@echo ""

list: ## List all sub-packages and their installation status
	@echo ""
	@echo "\033[1m\033[34mDana Sub-Packages\033[0m"
	@echo "\033[1m==================\033[0m"
	@echo ""
	@for pkg in $(PACKAGES); do \
		echo "📦 \033[36m$$pkg\033[0m"; \
		if [ -f $$pkg/pyproject.toml ]; then \
			desc=$$(grep '^description = ' $$pkg/pyproject.toml | head -1 | cut -d'"' -f2); \
			[ -n "$$desc" ] && echo "   $$desc"; \
		fi; \
		if [ -d $$pkg ] && [ -f $$pkg/pyproject.toml ]; then \
			echo "   ✅ Available in workspace"; \
		else \
			echo "   ❌ Missing"; \
		fi; \
		echo "   \033[33mcd $$pkg && make help\033[0m"; \
		echo ""; \
	done

packages: ## Show Dana packages installed in .venv
	@echo ""
	@echo "\033[1m\033[34mInstalled Editable Packages\033[0m"
	@echo "\033[1m========================\033[0m"
	@echo ""
	@if [ -d .venv ]; then \
		$(UV_CMD) pip list --editable 2>/dev/null || echo "⚠️  No Dana packages found - run 'make setup'"; \
	else \
		echo "⚠️  No .venv found - run 'make setup'"; \
	fi
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

# =============================================================================
# Quick Start
# =============================================================================

quickstart: check-uv ## Get Dana running in 30 seconds
	@echo ""
	@echo "🚀 \033[1m\033[32mDana Quick Start\033[0m"
	@echo "==================="
	@echo ""
	@echo "📦 Installing dependencies..."
	@$(UV_CMD) sync --quiet
	@echo "🔧 Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || echo "# Add your API keys here" > .env; \
		echo "📝 Created .env file"; \
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

# =============================================================================
# Development Setup
# =============================================================================

setup: ## Setup development environment (installs all packages in one venv)
	@echo "🔧 Setting up monorepo development environment..."
	@echo "📦 Syncing all workspace packages..."
	@$(UV_CMD) sync --extra dev
	@echo ""
	@echo "✅ \033[1m\033[32mAll packages installed in .venv!\033[0m"
	@echo ""
	@echo "Installed Dana packages:"
	@$(UV_CMD) pip list | grep -i "^dana" || true
	@echo ""
	@echo "💡 All packages share the same .venv at the root"

sync: ## Sync dependencies (uv workspace handles all packages)
	@echo "🔄 Syncing workspace dependencies..."
	@$(UV_CMD) sync
	@echo "✅ All dependencies synced!"

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "🧪 Running all tests..."
	$(call run-in-packages,test)
	@echo ""
	@echo "✅ \033[1m\033[32mAll tests passed!\033[0m"

test-agent: ## Run dana-agent tests only
	@cd dana_agent && $(MAKE) test

test-lang: ## Run dana-lang tests only
	@cd dana_lang && $(MAKE) test

test-studio: ## Run dana-studio tests only
	@cd dana_studio && $(MAKE) test

# =============================================================================
# Maintenance
# =============================================================================

clean: ## Clean build artifacts and remove .venv
	@echo "🧹 Cleaning build artifacts..."
	$(call run-in-packages,clean)
	@echo ""
	@echo "🧹 Cleaning root artifacts..."
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	@find . -maxdepth 1 -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -maxdepth 1 -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .ruff_cache/ .mypy_cache/
	@echo ""
	@echo "🗑️  Removing .venv..."
	@rm -rf .venv
	@echo "✅ Clean complete! Run 'make setup' to reinstall."

# =============================================================================
# Run Applications
# =============================================================================

dana: ## Start the Dana REPL
	@echo "🚀 Starting Dana REPL..."
	$(UV_CMD) run dana

studio-server: ## Start Dana Studio server
	@echo "🎨 Starting Dana Studio server..."
	$(UV_CMD) run python -m dana_lang.api.server

# =============================================================================
# LLM Infrastructure
# =============================================================================

install-ollama: ## Install Ollama for local model inference
	@echo "🦙 Installing Ollama for Dana..."
	@./bin/ollama/install.sh

start-ollama: ## Start Ollama server
	@echo "🚀 Starting Ollama for Dana..."
	@./bin/ollama/start.sh

install-vllm: ## Install vLLM for local model inference
	@echo "⚡ Installing vLLM for Dana..."
	@./bin/vllm/install.sh

start-vllm: ## Start vLLM server with interactive model selection
	@echo "🚀 Starting vLLM for Dana..."
	@./bin/vllm/start.sh
