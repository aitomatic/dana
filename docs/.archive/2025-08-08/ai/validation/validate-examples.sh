#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$DIR/../../../" && pwd)"

echo "[validate-examples] Using repository at: $REPO"

echo "[validate-examples] Ensuring dana-lang (PyPI) is installed..."
python3 -m pip install --upgrade --quiet dana-lang

if ! command -v dana >/dev/null 2>&1; then
  echo "Error: 'dana' CLI not found after installation. Ensure dana-lang provides the CLI and PATH is set."
  exit 1
fi

echo "[validate-examples] Searching for .na examples under docs/ (excluding .archive)..."
mapfile -t FILES < <(cd "$REPO" && \
  find docs -type f -name "*.na" -not -path "*/.archive/*" | sort)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No .na files found in docs/. Nothing to validate."
  exit 0
fi

FAIL=0
for file in "${FILES[@]}"; do
  echo "[validate-examples] Validating $file ..."
  if ! dana validate "$file"; then
    echo "[validate-examples] FAILED: $file"
    FAIL=1
    break
  fi
done

if [[ $FAIL -eq 0 ]]; then
  echo "[validate-examples] All examples validated successfully against PyPI dana-lang."
else
  echo "[validate-examples] Validation failed. See errors above."
  exit 1
fi



