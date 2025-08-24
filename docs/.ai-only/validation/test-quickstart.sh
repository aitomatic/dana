#!/usr/bin/env bash
set -euo pipefail
START_TIME=$(date +%s)
python3 -m pip install --upgrade dana || pip install --upgrade dana
# Basic smoke test: ensure CLI is invokable
if command -v dana >/dev/null 2>&1; then
  dana --version | cat
else
  echo "Error: dana CLI not available after install" >&2
  exit 1
fi
END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))
echo "Quickstart smoke test completed in ${ELAPSED}s"
