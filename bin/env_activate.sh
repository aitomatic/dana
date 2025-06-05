#!/bin/bash
# =============================================================================
# OpenDXA Virtual Environment Activation Script
# =============================================================================
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
#
# This script activates the Python virtual environment for OpenDXA development.
# It provides a convenient way to enter the project's isolated Python environment
# with all dependencies properly configured.
#
# Usage:
#   source bin/activate_venv.sh        # Activate the virtual environment
#   . bin/activate_venv.sh             # Alternative activation syntax
#
# Prerequisites:
#   - Virtual environment must exist at .venv/
#   - Run 'uv sync' or 'uv sync --extra dev' first to create the environment
#
# Note: This script must be sourced (not executed) to modify the current shell
# environment. If executed directly, it won't activate the environment in your
# current shell session.
#
# Environment Check:
#   After sourcing, your prompt should show (.venv) prefix indicating the
#   virtual environment is active. Use 'deactivate' command to exit.
# =============================================================================

# Activate the OpenDXA virtual environment
source .venv/bin/activate
