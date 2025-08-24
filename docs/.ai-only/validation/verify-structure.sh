#!/usr/bin/env bash
set -euo pipefail
required_dirs=(
  "docs/.ai-only/templates"
  "docs/.ai-only/validation"
  "docs/.ai-only/migrations"
  "docs/.archive"
  "docs/cookbook"
  "docs/examples"
  "docs/primers"
)
for d in "${required_dirs[@]}"; do
  [ -d "$d" ] || { echo "Missing directory: $d" >&2; exit 1; }
done
required_files=(
  "docs/index.md"
  "docs/quickstart.md"
  "docs/core-concepts.md"
  "docs/cookbook/multi-agent-chat.md"
  "docs/cookbook/data-pipeline.md"
  "docs/cookbook/api-orchestration.md"
  "docs/cookbook/error-recovery.md"
  "docs/examples/local_agent.na"
  "docs/examples/chatbot.na"
  "docs/examples/data_processor.na"
  "docs/examples/multi_agent.na"
  "docs/examples/production.na"
)
for f in "${required_files[@]}"; do
  [ -f "$f" ] || { echo "Missing file: $f" >&2; exit 1; }
done
echo "Documentation structure verified."
