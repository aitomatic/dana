#!/bin/bash

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install opendxa library in dev mode
pip install -e ".[dev]"

# Install pre-commit
pip install pre-commit
pre-commit install --hook-type post-checkout --hook-type post-merge --hook-type post-rewrite

# Install dependencies
pip install -r requirements.txt

echo "Installation & environment setup complete."
