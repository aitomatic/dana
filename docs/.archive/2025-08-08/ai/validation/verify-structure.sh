#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$DIR/../../../" && pwd)"

echo "[verify-structure] Verifying documentation structure..."

required_paths=(
  "$REPO/docs/.ai/README.md"
  "$REPO/docs/.ai/quickstart-guide.md"
  "$REPO/docs/.ai/cookbook-guide.md"
  "$REPO/docs/.ai/language-reference-guide.md"
  "$REPO/docs/.ai/examples-guide.md"
  "$REPO/docs/.ai/templates/cookbook-recipe.md"
  "$REPO/docs/.ai/templates/migration-guide.md"
  "$REPO/docs/.ai/templates/archive-reason.md"
  "$REPO/docs/.ai/templates/primer-section.md"
  "$REPO/docs/.ai/validation/validate-examples.sh"
  "$REPO/docs/.ai/validation/check-archive-links.sh"
  "$REPO/docs/.ai/validation/test-quickstart.sh"
  "$REPO/docs/.ai/validation/verify-structure.sh"
  "$REPO/docs/.ai/validation/verify-public-features.sh"
  "$REPO/docs/.archive/INDEX.md"
)

missing=()
for p in "${required_paths[@]}"; do
  if [[ ! -e "$p" ]]; then
    missing+=("$p")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "[verify-structure] Missing required paths:" >&2
  printf ' - %s\n' "${missing[@]}" >&2
  exit 1
fi

echo "[verify-structure] OK: All required files and directories exist."



