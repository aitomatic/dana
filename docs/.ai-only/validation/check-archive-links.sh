#!/usr/bin/env bash
set -euo pipefail
if grep -R "\.archive/" docs --include "*.md" --exclude-dir ".archive" --exclude-dir ".ai-only" -n | cat; then
  echo "Error: Active docs must not reference .archive/" >&2
  exit 1
fi
echo "No references to .archive/ found in active docs."
