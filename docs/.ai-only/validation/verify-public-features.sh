#!/usr/bin/env bash
set -euo pipefail
# Ensure docs do not mention non-public preview flags
if grep -R "PREVIEW" docs --include "*.md" --exclude-dir ".archive" --exclude-dir ".ai-only" -n | cat; then
  echo "Warning: Preview markers found; ensure these are not in production docs" >&2
  exit 1
fi
# Basic check that version badge points to PyPI
if ! grep -R "https://img.shields.io/pypi/v/dana" docs --include "*.md" -n | cat; then
  echo "Note: Consider adding version badges to pages." >&2
fi
echo "Public feature check completed."
