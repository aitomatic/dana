#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$DIR/../../../" && pwd)"

echo "[check-archive-links] Scanning for links to .archive from active docs..."

# Look for any references to .archive in Markdown files outside maintenance and archive directories
if grep -RIn --include "*.md" --exclude-dir ".archive" --exclude-dir ".ai" --exclude-dir ".ai-only" "\.archive/" "$REPO/docs" >/dev/null 2>&1; then
  echo "[check-archive-links] ERROR: Found references to .archive in active docs."
  grep -RIn --include "*.md" --exclude-dir ".archive" --exclude-dir ".ai" --exclude-dir ".ai-only" "\.archive/" "$REPO/docs" || true
  exit 1
fi

echo "[check-archive-links] OK: No active docs reference .archive."


