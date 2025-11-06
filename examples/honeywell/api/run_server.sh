#!/bin/bash
# Run the HVAC Agent API server
#
# This script uses 'uv run' to ensure all dependencies are available.
# The dana_agent package requires structlog and other dependencies that
# are installed in the uv-managed .venv environment.
#
# Alternative: Activate the venv manually:
#   source .venv/bin/activate
#   python3 server.py

cd "$(dirname "$0")/../.."
uv run python3 honeywell/api/server.py

