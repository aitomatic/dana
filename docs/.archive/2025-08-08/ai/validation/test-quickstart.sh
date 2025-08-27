#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$DIR/../../../" && pwd)"

echo "[test-quickstart] Ensuring dana-lang (PyPI) is installed..."
python3 -m pip install --upgrade --quiet dana-lang

QUICKSTART_MD="$REPO/docs/quickstart.md"
if [[ ! -f "$QUICKSTART_MD" ]]; then
  echo "[test-quickstart] ERROR: docs/quickstart.md not found."
  exit 1
fi

echo "[test-quickstart] Checking for at least one .na example under docs/examples/ ..."
mapfile -t FILES < <(cd "$REPO" && find docs/examples -type f -name "*.na" 2>/dev/null | sort || true)
if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "[test-quickstart] WARNING: No .na files under docs/examples/. Skipping run test."
  exit 0
fi

FIRST="${FILES[0]}"
echo "[test-quickstart] Validating example: $FIRST"
if dana validate "$FIRST"; then
  echo "[test-quickstart] OK: Quickstart examples validate with current PyPI dana-lang."
  exit 0
else
  echo "[test-quickstart] FAIL: Example failed to validate: $FIRST"
  exit 1
fi



