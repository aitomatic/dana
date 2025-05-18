#!/bin/bash
# Run with "source ./VENV.sh"

# Activate the virtual environment
source .venv/bin/activate

# Install opendxa library in dev mode
pip install -e ".[dev]"
