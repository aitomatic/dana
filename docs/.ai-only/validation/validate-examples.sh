#!/usr/bin/env bash
set -euo pipefail

# Install public PyPI version
python3 -m pip install --upgrade dana || pip install --upgrade dana

# Test all examples against public version
find docs -name "*.na" -type f | while read -r file; do
  echo "Testing $file..."
  if command -v dana >/dev/null 2>&1; then
    dana validate "$file" || exit 1
  else
    echo "dana CLI not found; skipping validate for $file" >&2
  fi
done
