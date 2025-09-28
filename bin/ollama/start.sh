#!/bin/bash

set -euo pipefail

DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="11434"

usage() {
	cat <<'EOF'
Start the Ollama daemon for Dana usage.

Usage: ./bin/ollama/start.sh [--host HOST] [--port PORT] [--foreground]

Options:
  --host HOST      Host interface for Ollama serve (default: 127.0.0.1 when foreground)
  --port PORT      Port for Ollama serve (default: 11434 when foreground)
  --foreground     Run `ollama serve` in the foreground instead of using a system service
  -h, --help       Show this help message

If Ollama is managed by launchctl (macOS) or systemd (Linux), the script will
attempt to start those services. Otherwise it falls back to `ollama serve`.
EOF
}

has_command() {
	command -v "$1" >/dev/null 2>&1
}

HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
FORCE_FOREGROUND=false

while [[ $# -gt 0 ]]; do
	case "$1" in
		--host)
			HOST="$2"
			shift 2
			;;
		--port)
			PORT="$2"
			shift 2
			;;
		--foreground)
			FORCE_FOREGROUND=true
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

BASE_URL="http://${HOST}:${PORT}"

require_ollama() {
	if ! has_command ollama; then
		echo "❌ Ollama is not installed or not on PATH." >&2
		echo "Run 'make install-ollama' first." >&2
		exit 1
	fi
}

check_server_ready() {
	if has_command curl; then
		curl --silent --max-time 2 --fail "${BASE_URL}/api/version" >/dev/null 2>&1
		return $?
	fi

	# Fallback: use ollama ps (requires daemon) 
	ollama ps >/dev/null 2>&1
}

wait_for_server() {
	local attempts=0
	local max_attempts=30
	local sleep_seconds=1

	until check_server_ready; do
		attempts=$((attempts + 1))
		if [[ $attempts -ge $max_attempts ]]; then
			echo "❌ Ollama did not become ready at ${BASE_URL} within ${max_attempts}s." >&2
			return 1
		fi
		sleep "$sleep_seconds"
	done

	return 0
}

start_foreground() {
	echo "🚀 Starting ollama serve in the foreground..."
	echo "   Host: $HOST"
	echo "   Port: $PORT"
	echo "   Base URL: ${BASE_URL}/v1"
	export LOCAL_BASE_URL="${BASE_URL}/v1"
	export LOCAL_MODEL_NAME="${LOCAL_MODEL_NAME:-}"
	exec ollama serve --host "$HOST" --port "$PORT"
}

start_macos_service() {
	if ! has_command launchctl; then
		return 1
	fi

	local service_name="gui/$UID/com.ollama.ollama"
	echo "🔌 Activating Ollama launchctl service..."
	if launchctl kickstart -k "$service_name" >/dev/null 2>&1; then
		return 0
	fi

	# Fallback for older installs where service is in LaunchDaemon
	service_name="system/com.ollama.ollama"
	launchctl kickstart -k "$service_name" >/dev/null 2>&1
}

start_systemd_service() {
	if ! has_command systemctl; then
		return 1
	fi

	echo "🔌 Starting Ollama systemd service..."
	if sudo systemctl start ollama; then
		return 0
	fi

	return 1
}

main() {
	require_ollama

	if check_server_ready; then
		echo "✅ Ollama already responding at ${BASE_URL}."
		exit 0
	fi

	local os
	os="$(uname -s)"

	if [[ "$FORCE_FOREGROUND" == true ]]; then
		start_foreground
		return
	fi

	case "$os" in
		Darwin)
			if [[ "$HOST" != "$DEFAULT_HOST" || "$PORT" != "$DEFAULT_PORT" ]]; then
				echo "⚠️  Host/port overrides require --foreground on macOS. Using launchctl defaults." >&2
			fi
			if start_macos_service; then
				:
			else
				echo "⚠️  launchctl start failed; falling back to foreground serve." >&2
				start_foreground
				return
			fi
			;;
		Linux)
			if [[ "$HOST" != "$DEFAULT_HOST" || "$PORT" != "$DEFAULT_PORT" ]]; then
				echo "⚠️  Host/port overrides require --foreground on Linux when using systemd." >&2
			fi
			if start_systemd_service; then
				:
			else
				echo "⚠️  systemd start failed or not available; falling back to foreground serve." >&2
				start_foreground
				return
			fi
			;;
		*)
			echo "⚠️  Unknown OS (${os}); running ollama serve in foreground." >&2
			start_foreground
			return
			;;
	esac

	if wait_for_server; then
		echo "🎉 Ollama is now available at ${BASE_URL}."
		echo "   API endpoint: ${BASE_URL}/v1"
	else
		echo "❌ Ollama service failed to become ready. Try --foreground for more logs." >&2
		exit 1
	fi
}

main "$@"
