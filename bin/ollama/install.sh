#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
	cat <<'EOF'
Install Ollama for Dana

Usage: ./bin/ollama/install.sh [--force]

Options:
  --force   Reinstall even if Ollama is already detected
  -h, --help  Show this help message

The script installs Ollama using the recommended method for your OS:
  • macOS   → Homebrew formula `ollama`
  • Linux   → Official install script from https://ollama.com

After installation, run the guided setup (`make install-ollama`) if you need to update
Dana environment variables, then start the daemon with `make start-ollama`.
EOF
}

has_command() {
	command -v "$1" >/dev/null 2>&1
}

FORCE=false

while [[ $# -gt 0 ]]; do
	case "$1" in
		--force)
			FORCE=true
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			usage >&2
			exit 1
			;;
	esac
done

require_curl() {
	if ! has_command curl; then
		echo "curl is required to install Ollama." >&2
		echo "Please install curl (e.g. apt-get install curl) and retry." >&2
		exit 1
	fi
}

install_linux() {
	require_curl
	echo "📦 Installing Ollama (Linux)..."
	if [[ "$FORCE" == true ]]; then
		echo "ℹ️  Forcing reinstall via official script."
	elif has_command ollama; then
		echo "✅ Ollama already installed. Re-run with --force to reinstall."
		return
	fi

	if curl -fsSL https://ollama.com/install.sh | sh; then
		echo "✅ Ollama install script finished."
	else
		echo "❌ Failed to execute Ollama install script." >&2
		exit 1
	fi
}

install_macos() {
	if ! has_command brew; then
		echo "❌ Homebrew is required to install Ollama on macOS." >&2
		echo "Install Homebrew from https://brew.sh/ and retry." >&2
		exit 1
	fi

	echo "📦 Installing Ollama (macOS via Homebrew)..."
	if brew list --formula | grep -q '^ollama$'; then
		if [[ "$FORCE" == true ]]; then
			echo "ℹ️  Reinstalling Homebrew formula 'ollama'."
			brew reinstall ollama
		else
			echo "✅ Ollama already installed. Re-run with --force to reinstall."
			return
		fi
	else
		brew install ollama
	fi

	echo "✅ Homebrew completed the Ollama installation."
}

verify_install() {
	if ! has_command ollama; then
		echo "❌ Ollama command not found after installation." >&2
		echo "Please review the output above for errors." >&2
		exit 1
	fi

	local version
	version="$(ollama --version 2>/dev/null || true)"
	if [[ -z "$version" ]]; then
		echo "⚠️  Ollama installed but version check failed." >&2
	else
		echo "🎉 Ollama detected: $version"
	fi
}

main() {
	case "$(uname -s)" in
		Linux)
			install_linux
			;;
		Darwin)
			install_macos
			;;
		*)
			echo "❌ Unsupported operating system: $(uname -s)" >&2
			exit 1
			;;
	esac

	verify_install

	echo
	echo "Next steps:"
	echo "  • (Optional) run 'make install-ollama' to configure Dana environment files"
	echo "  • Start the daemon with 'make start-ollama'"
}

main "$@"