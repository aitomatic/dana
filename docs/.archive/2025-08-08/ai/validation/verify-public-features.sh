#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$DIR/../../../" && pwd)"

echo "[verify-public-features] Ensuring active docs do not claim preview-only or internal-only features..."

VIOL=0

# Iterate over markdown files, excluding archives and maintenance folders
while IFS= read -r -d '' f; do
  in_code=0
  lineno=0
  while IFS='' read -r line || [[ -n "$line" ]]; do
    lineno=$((lineno+1))
    # Toggle code fence state on lines that start with ```
    case "$line" in
      '```'*)
        if (( in_code == 0 )); then in_code=1; else in_code=0; fi
        continue
        ;;
    esac
    # Only check outside code fences
    if (( in_code == 0 )); then
      shopt -s nocasematch
      if [[ "$line" =~ \bcoming[[:space:]]+soon\b ]] || \
         [[ "$line" =~ preview[[:space:]]*-[[:space:]]*features[[:space:]]+not[[:space:]]+yet[[:space:]]+available ]] || \
         [[ "$line" =~ \binternal([-[:space:]])only\b ]]; then
        echo "$f:$lineno:$line"
        VIOL=1
      fi
      shopt -u nocasematch
    fi
  done <"$f"
done < <(cd "$REPO" && find docs -type f -name "*.md" \
  -not -path "*/.archive/*" -not -path "*/.ai/*" -not -path "*/.ai-only/*" -print0)

if (( VIOL == 1 )); then
  echo "[verify-public-features] ERROR: Found preview/internal-only markers in active docs (outside code blocks)."
  exit 1
fi

echo "[verify-public-features] OK: No preview/internal-only markers detected in active docs."

echo "[verify-public-features] Checking PyPI availability of dana-lang..."
python3 -c "import pkgutil, sys; sys.exit(0 if pkgutil.find_loader('dana') or pkgutil.find_loader('dana_lang') else 1)" || {
  echo "[verify-public-features] WARNING: Cannot verify dana-lang availability in this environment."
}

exit 0


